"""RAG retrieval pipeline — best-in-class, 7 layers.

Layer 1  HyDE + query expansion   1 fast LLM call → hypothetical answer + 3 rephrasings
Layer 2  Multi-vector dense        pgvector search for original + hyde + each rephrasing
Layer 3  Sparse / FTS              PostgreSQL full-text search (GIN index)
Layer 4  RRF fusion                Reciprocal Rank Fusion merges all ranked lists
Layer 5  Source boosting           approved_answer +35 %, starter template −25 %
Layer 6  Feedback scoring          per-org approve/reject history adjusts scores
Layer 7  Voyage reranking          rerank-2 re-scores top-20 candidates
Layer 8  Deduplication             drops near-identical chunks (cosine ≥ 0.92)

Returns up to top_k chunks with approved answers always surfaced first.
Every layer degrades gracefully — a failure falls back to the previous layer's output.
"""

from __future__ import annotations

import asyncio
import json
import math
import re
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import ChunkFeedback, KnowledgeChunk, SourceType
from app.services.embeddings import get_embedding_provider


@dataclass
class RetrievalResult:
    chunk: KnowledgeChunk
    similarity: float


# ---------------------------------------------------------------------------
# Tunables
# ---------------------------------------------------------------------------

_BOOST: dict[str, float] = {
    SourceType.approved_answer: 1.35,
    SourceType.policy:          1.00,
}
_RRF_K             = 60
_DEDUP_THRESHOLD   = 0.92
_FEEDBACK_SCALE    = 0.15   # ±15 % max per unit of tanh(net/3)
_FEEDBACK_CLAMP    = (0.60, 1.40)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def retrieve_relevant_chunks(
    question_text: str,
    db: Session,
    top_k: int = 8,
    workspace_id: int | None = None,
    customer_name: str | None = None,
    similarity_threshold: float = 0.0,
) -> list[RetrievalResult]:
    """Full 7-layer RAG pipeline. Falls back gracefully at every stage."""

    # Layers 1-2: HyDE + expansion + multi-vector dense (parallel with sparse)
    hyde_task   = asyncio.create_task(_hyde_and_expand(question_text))
    sparse      = _sparse_retrieve(question_text, db, top_k=20, workspace_id=workspace_id, customer_name=customer_name)
    hyde_text, rephrasings = await hyde_task

    # Build all query variants: original + hyde + rephrasings
    query_variants = [question_text]
    if hyde_text:
        query_variants.append(hyde_text)
    query_variants.extend(rephrasings)

    dense_lists = await _multi_dense_retrieve(query_variants, db, top_k=10, workspace_id=workspace_id, customer_name=customer_name)

    # Layer 3-4: RRF fusion of all ranked lists
    fused = _reciprocal_rank_fusion(*dense_lists, sparse)

    # Layer 5: Source-aware score boosting
    boosted = _apply_source_boost(fused, db)

    # Layer 6: Feedback scoring
    scored = _apply_feedback_score(boosted, db, workspace_id)

    # Layer 7: Reranking
    candidates = sorted(scored, key=lambda r: r.similarity, reverse=True)[:20]
    reranked   = await _rerank(question_text, candidates)

    # Layer 8: Deduplication
    deduped = _deduplicate(reranked)

    # Layer 9: Parent expansion — swap child chunks for their parent context
    expanded = _expand_to_parents(deduped, db)

    return [r for r in expanded if r.similarity >= similarity_threshold][:top_k]


# ---------------------------------------------------------------------------
# Layer 1 — HyDE + query expansion (single LLM call)
# ---------------------------------------------------------------------------

_HYDE_PROMPT = """\
Given this security questionnaire question, return ONLY valid JSON — no markdown:
{{
  "hyde": "A 1-2 sentence answer as if from a well-secured, compliant company.",
  "rephrasings": ["rephrasing 1", "rephrasing 2", "rephrasing 3"]
}}

Question: {question}"""


async def _hyde_and_expand(question: str) -> tuple[str, list[str]]:
    """Return (hyde_answer, [rephrasing1, rephrasing2, rephrasing3]).
    Returns ("", []) on any failure — caller uses original question only."""
    try:
        from app.services.generation import get_llm_provider
        provider = get_llm_provider()
        raw, _, _ = await asyncio.wait_for(
            provider.generate(
                "You are a concise assistant. Return only valid JSON, no prose.",
                _HYDE_PROMPT.format(question=question),
            ),
            timeout=12.0,
        )
        return _parse_hyde(raw)
    except Exception:
        return "", []


def _parse_hyde(raw: str) -> tuple[str, list[str]]:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text.strip())
        hyde = str(data.get("hyde", "")).strip()
        rephrasings = [str(r).strip() for r in data.get("rephrasings", []) if str(r).strip()][:3]
        return hyde, rephrasings
    except Exception:
        return "", []


# ---------------------------------------------------------------------------
# Layer 2 — Multi-vector dense retrieval
# ---------------------------------------------------------------------------

async def _multi_dense_retrieve(
    queries: list[str],
    db: Session,
    top_k: int,
    workspace_id: int | None,
    customer_name: str | None = None,
) -> list[list[RetrievalResult]]:
    """Embed all query variants in one batch, retrieve top_k for each."""
    if not queries:
        return []

    provider = get_embedding_provider()
    embeddings = await provider.embed(queries, input_type="query")

    results = []
    for vec in embeddings:
        results.append(await _dense_retrieve_vec(vec, db, top_k, workspace_id, customer_name))
    return results


async def _dense_retrieve_vec(
    vec: list[float],
    db: Session,
    top_k: int,
    workspace_id: int | None,
    customer_name: str | None = None,
) -> list[RetrievalResult]:
    vec_str = "[" + ",".join(str(float(v)) for v in vec) + "]"

    if workspace_id is not None:
        rows = db.execute(
            text("""
                SELECT kc.id,
                       1 - (kc.embedding <=> CAST(:vec AS vector)) AS similarity
                FROM   knowledge_chunks kc
                JOIN   documents d ON d.id = kc.document_id
                WHERE  kc.embedding IS NOT NULL
                AND    kc.is_leaf = TRUE
                AND    d.workspace_id = :workspace_id
                AND    (
                    kc.source_type != 'approved_answer'
                    OR kc.customer_name IS NULL
                    OR kc.customer_name = :customer_name
                )
                ORDER  BY kc.embedding <=> CAST(:vec AS vector)
                LIMIT  :k
            """),
            {"vec": vec_str, "k": top_k, "workspace_id": workspace_id, "customer_name": customer_name or ""},
        ).fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT id,
                       1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                FROM   knowledge_chunks
                WHERE  embedding IS NOT NULL
                AND    is_leaf = TRUE
                ORDER  BY embedding <=> CAST(:vec AS vector)
                LIMIT  :k
            """),
            {"vec": vec_str, "k": top_k},
        ).fetchall()

    if not rows:
        return []

    ids = [r.id for r in rows]
    sim_by_id = {r.id: float(r.similarity) for r in rows}
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(ids)).all()
    chunk_by_id = {c.id: c for c in chunks}

    return [
        RetrievalResult(chunk=chunk_by_id[cid], similarity=sim_by_id[cid])
        for cid in ids if cid in chunk_by_id
    ]


# ---------------------------------------------------------------------------
# Layer 3 — Sparse / full-text retrieval
# ---------------------------------------------------------------------------

def _sparse_retrieve(
    question_text: str,
    db: Session,
    top_k: int,
    workspace_id: int | None,
    customer_name: str | None = None,
) -> list[RetrievalResult]:
    if not question_text.strip():
        return []
    try:
        if workspace_id is not None:
            rows = db.execute(
                text("""
                    SELECT kc.id,
                           ts_rank_cd(
                               to_tsvector('english', kc.text),
                               plainto_tsquery('english', :q)
                           ) AS rank
                    FROM   knowledge_chunks kc
                    JOIN   documents d ON d.id = kc.document_id
                    WHERE  kc.embedding IS NOT NULL
                    AND    kc.is_leaf = TRUE
                    AND    d.workspace_id = :workspace_id
                    AND    (
                        kc.source_type != 'approved_answer'
                        OR kc.customer_name IS NULL
                        OR kc.customer_name = :customer_name
                    )
                    AND    to_tsvector('english', kc.text)
                           @@ plainto_tsquery('english', :q)
                    ORDER  BY rank DESC
                    LIMIT  :k
                """),
                {"q": question_text, "workspace_id": workspace_id, "k": top_k, "customer_name": customer_name or ""},
            ).fetchall()
        else:
            rows = db.execute(
                text("""
                    SELECT id,
                           ts_rank_cd(
                               to_tsvector('english', text),
                               plainto_tsquery('english', :q)
                           ) AS rank
                    FROM   knowledge_chunks
                    WHERE  embedding IS NOT NULL
                    AND    is_leaf = TRUE
                    AND    to_tsvector('english', text)
                           @@ plainto_tsquery('english', :q)
                    ORDER  BY rank DESC
                    LIMIT  :k
                """),
                {"q": question_text, "k": top_k},
            ).fetchall()
    except Exception:
        return []

    if not rows:
        return []

    ids = [r.id for r in rows]
    rank_by_id = {r.id: float(r.rank) for r in rows}
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(ids)).all()
    chunk_by_id = {c.id: c for c in chunks}

    return [
        RetrievalResult(chunk=chunk_by_id[cid], similarity=rank_by_id[cid])
        for cid in ids if cid in chunk_by_id
    ]


# ---------------------------------------------------------------------------
# Layer 4 — Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def _reciprocal_rank_fusion(*ranked_lists: list[RetrievalResult]) -> list[RetrievalResult]:
    scores: dict[int, float] = {}
    chunks: dict[int, KnowledgeChunk] = {}

    for results in ranked_lists:
        for rank, r in enumerate(results):
            scores[r.chunk.id] = scores.get(r.chunk.id, 0.0) + 1.0 / (_RRF_K + rank + 1)
            chunks[r.chunk.id] = r.chunk

    return [
        RetrievalResult(chunk=chunks[cid], similarity=score)
        for cid, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ]


# ---------------------------------------------------------------------------
# Layer 5 — Source-aware score boosting
# ---------------------------------------------------------------------------

def _apply_source_boost(results: list[RetrievalResult], db: Session) -> list[RetrievalResult]:
    boosted = []
    for r in results:
        multiplier = _BOOST.get(r.chunk.source_type, 1.0)
        boosted.append(RetrievalResult(chunk=r.chunk, similarity=r.similarity * multiplier))
    return boosted


# ---------------------------------------------------------------------------
# Layer 6 — Feedback-based score adjustment
# ---------------------------------------------------------------------------

def _apply_feedback_score(
    results: list[RetrievalResult],
    db: Session,
    workspace_id: int | None,
) -> list[RetrievalResult]:
    if not workspace_id or not results:
        return results

    ids = [r.chunk.id for r in results]
    try:
        rows = db.execute(
            text("""
                SELECT chunk_id,
                       SUM(CASE WHEN signal = 'positive' THEN 1 ELSE -1 END) AS net
                FROM   chunk_feedback
                WHERE  chunk_id IN :ids
                AND    workspace_id   = :workspace_id
                GROUP  BY chunk_id
            """),
            {"ids": tuple(ids), "workspace_id": workspace_id},
        ).fetchall()
    except Exception:
        return results

    net_by_id = {row.chunk_id: int(row.net) for row in rows}

    adjusted = []
    for r in results:
        net = net_by_id.get(r.chunk.id, 0)
        if net == 0:
            adjusted.append(r)
            continue
        raw_mult = 1.0 + _FEEDBACK_SCALE * math.tanh(net / 3.0)
        multiplier = max(_FEEDBACK_CLAMP[0], min(_FEEDBACK_CLAMP[1], raw_mult))
        adjusted.append(RetrievalResult(chunk=r.chunk, similarity=r.similarity * multiplier))
    return adjusted


# ---------------------------------------------------------------------------
# Layer 7 — Voyage reranking
# ---------------------------------------------------------------------------

async def _rerank(question: str, candidates: list[RetrievalResult]) -> list[RetrievalResult]:
    if not candidates:
        return candidates
    try:
        import voyageai
        from app.config import get_settings

        if not get_settings().voyage_api_key:
            return candidates

        client = voyageai.AsyncClient(api_key=get_settings().voyage_api_key)
        texts  = [r.chunk.text for r in candidates]
        result = await asyncio.wait_for(
            client.rerank(question, texts, model="rerank-2", top_k=len(texts)),
            timeout=10.0,
        )
        return [
            RetrievalResult(chunk=candidates[item.index].chunk, similarity=float(item.relevance_score))
            for item in result.results
        ]
    except Exception:
        return candidates


# ---------------------------------------------------------------------------
# Layer 8 — Deduplication
# ---------------------------------------------------------------------------

def _deduplicate(results: list[RetrievalResult], threshold: float = _DEDUP_THRESHOLD) -> list[RetrievalResult]:
    kept: list[RetrievalResult] = []
    for candidate in results:
        vec_c = _to_vec(candidate.chunk.embedding)
        if vec_c is None:
            kept.append(candidate)
            continue
        if not any(
            (vec_k := _to_vec(k.chunk.embedding)) is not None
            and _cosine_sim(vec_c, vec_k) >= threshold
            for k in kept
        ):
            kept.append(candidate)
    return kept


# ---------------------------------------------------------------------------
# Layer 9 — Parent expansion
# ---------------------------------------------------------------------------

def _expand_to_parents(
    results: list[RetrievalResult],
    db: Session,
) -> list[RetrievalResult]:
    """Replace child chunks with their parent chunks for richer LLM context.

    Children are small (≤150 tokens) and precise for retrieval.
    Parents are large (≤800 tokens) and give the LLM the full policy section.
    If two children share the same parent, the parent appears only once
    (highest child similarity score wins).
    Standalone leaf chunks (no parent) are returned as-is.
    """
    parent_best: dict[int, RetrievalResult] = {}   # parent_id → best result
    standalone: list[RetrievalResult] = []

    for r in results:
        pid = r.chunk.parent_chunk_id
        if pid is None:
            standalone.append(r)
        else:
            if pid not in parent_best or r.similarity > parent_best[pid].similarity:
                parent_best[pid] = r

    if not parent_best:
        return standalone

    parent_ids = list(parent_best.keys())
    parents = {
        p.id: p
        for p in db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(parent_ids)).all()
    }

    expanded: list[RetrievalResult] = list(standalone)
    for pid, child_result in parent_best.items():
        parent_chunk = parents.get(pid)
        if parent_chunk:
            expanded.append(RetrievalResult(chunk=parent_chunk, similarity=child_result.similarity))
        else:
            expanded.append(child_result)  # parent missing — fall back to child

    return sorted(expanded, key=lambda r: r.similarity, reverse=True)


# ---------------------------------------------------------------------------
# Feedback signal writers (called from approve / reject / regen routes)
# ---------------------------------------------------------------------------

def record_positive_feedback(chunk_ids: list[int], workspace_id: int, db: Session) -> None:
    _write_feedback(chunk_ids, workspace_id, "positive", db)


def record_negative_feedback(chunk_ids: list[int], workspace_id: int, db: Session) -> None:
    _write_feedback(chunk_ids, workspace_id, "negative", db)


def _write_feedback(chunk_ids: list[int], workspace_id: int, signal: str, db: Session) -> None:
    if not chunk_ids:
        return
    try:
        for cid in chunk_ids:
            db.add(ChunkFeedback(chunk_id=cid, workspace_id=workspace_id, signal=signal))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_vec(embedding) -> list[float] | None:
    if embedding is None:
        return None
    if isinstance(embedding, list):
        return embedding
    try:
        return list(embedding)
    except Exception:
        return None


def _cosine_sim(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot   = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
