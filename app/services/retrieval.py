"""pgvector similarity search."""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import KnowledgeChunk
from app.services.embeddings import get_embedding_provider


@dataclass
class RetrievalResult:
    chunk: KnowledgeChunk
    similarity: float


async def retrieve_relevant_chunks(
    question_text: str,
    db: Session,
    top_k: int = 5,
    org_id: int | None = None,
) -> list[RetrievalResult]:
    """Embed *question_text* and return the top-K most similar KnowledgeChunks.

    No similarity threshold is applied — the best available chunks are always
    returned and every question always gets a draft. Confidence scoring
    communicates match quality to the human reviewer, who approves or rejects
    every answer before anything is exported. A bad draft is better than a
    silent skip.
    """
    provider = get_embedding_provider()
    embeddings = await provider.embed([question_text], input_type="query")
    query_vec = embeddings[0]

    vec_str = "[" + ",".join(str(float(v)) for v in query_vec) + "]"

    if org_id is not None:
        rows = db.execute(
            text("""
                SELECT kc.id,
                       1 - (kc.embedding <=> CAST(:vec AS vector)) AS similarity
                FROM   knowledge_chunks kc
                JOIN   documents d ON d.id = kc.document_id
                WHERE  kc.embedding IS NOT NULL
                AND    d.org_id = :org_id
                ORDER  BY kc.embedding <=> CAST(:vec AS vector)
                LIMIT  :k
            """),
            {"vec": vec_str, "k": top_k, "org_id": org_id},
        ).fetchall()
    else:
        rows = db.execute(
            text("""
                SELECT id,
                       1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                FROM   knowledge_chunks
                WHERE  embedding IS NOT NULL
                ORDER  BY embedding <=> CAST(:vec AS vector)
                LIMIT  :k
            """),
            {"vec": vec_str, "k": top_k},
        ).fetchall()

    if not rows:
        return []

    above = [(row.id, float(row.similarity)) for row in rows]
    ids = [r[0] for r in above]
    sim_by_id = {r[0]: r[1] for r in above}
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(ids)).all()
    chunk_by_id = {c.id: c for c in chunks}

    return [
        RetrievalResult(chunk=chunk_by_id[cid], similarity=sim)
        for cid, sim in above
        if cid in chunk_by_id
    ]
