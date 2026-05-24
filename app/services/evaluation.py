"""RAG evaluation framework.

Measures retrieval quality against the org's own approved answer history —
no external labels needed.  For each approved question we already know which
chunks led to a good answer (cited_chunk_ids).  We run fresh retrieval and
check whether those chunks (or their parents) are recovered.

Metrics
-------
hit_rate_at_k   Fraction of questions where ≥1 originally-cited chunk
                (or its parent) appears in the top-k results.
mrr             Mean Reciprocal Rank — average of 1/rank for first hit.
avg_similarity  Average top-1 similarity score across all questions.
precision_at_1  Fraction of questions where the top-1 result is a cited chunk.
coverage        Fraction of approved questions that have at least one cited
                chunk still in the knowledge base (prerequisite for a fair eval).

Graceful degradation: every metric returns 0.0 on error rather than crashing.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from sqlalchemy.orm import Session


@dataclass
class EvalReport:
    questions_evaluated: int = 0
    coverage:            float = 0.0   # fraction with evaluable cited chunks
    hit_rate_at_k:       float = 0.0
    precision_at_1:      float = 0.0
    mrr:                 float = 0.0
    avg_top1_similarity: float = 0.0
    top_k:               int = 8
    warnings:            list[str] = field(default_factory=list)


async def evaluate_retrieval(
    workspace_id: int,
    db: Session,
    top_k: int = 8,
    sample_size: int = 50,
) -> EvalReport:
    """Run the evaluation pipeline and return an EvalReport.

    Pulls up to *sample_size* approved questions from the org, reruns
    retrieval for each, and scores the results.
    """
    from app.models import Question, QuestionStatus, Questionnaire, KnowledgeChunk
    from app.services.retrieval import retrieve_relevant_chunks

    report = EvalReport(top_k=top_k)

    # ── Fetch approved questions with cited chunks ──────────────────────────
    approved = (
        db.query(Question)
        .join(Questionnaire, Question.questionnaire_id == Questionnaire.id)
        .filter(
            Questionnaire.workspace_id == workspace_id,
            Question.status == QuestionStatus.approved,
            Question.cited_chunk_ids.isnot(None),
            Question.question_text.isnot(None),
        )
        .order_by(Question.id.desc())
        .limit(sample_size)
        .all()
    )

    if not approved:
        report.warnings.append("No approved questions with cited chunks found.")
        return report

    # ── Build set of all cited chunk IDs (and their parent IDs) ─────────────
    all_cited_ids: set[int] = set()
    for q in approved:
        all_cited_ids.update(q.cited_chunk_ids or [])

    # Fetch the chunks to also include their parent IDs as valid hits
    cited_chunks = (
        db.query(KnowledgeChunk)
        .filter(KnowledgeChunk.id.in_(all_cited_ids))
        .all()
    )
    parent_ids = {c.parent_chunk_id for c in cited_chunks if c.parent_chunk_id}
    all_valid_ids = all_cited_ids | parent_ids

    # Check how many questions still have evaluable chunks
    evaluable = [
        q for q in approved
        if any(cid in all_valid_ids for cid in (q.cited_chunk_ids or []))
    ]
    if not evaluable:
        report.questions_evaluated = len(approved)
        report.coverage = 0.0
        report.warnings.append(
            "All cited chunks have been deleted — coverage is 0. "
            "Re-upload documents to restore evaluation data."
        )
        return report

    report.coverage = round(len(evaluable) / len(approved), 3)

    # ── Run retrieval and score ──────────────────────────────────────────────
    hits_at_k    = 0
    hits_at_1    = 0
    reciprocal_ranks: list[float] = []
    top1_sims:        list[float] = []

    for q in evaluable:
        cited = set(q.cited_chunk_ids or [])
        # A hit can be a cited chunk OR its parent (parent-child aware)
        cited_and_parents = cited | {
            c.parent_chunk_id
            for c in cited_chunks
            if c.id in cited and c.parent_chunk_id
        }

        try:
            results = await retrieve_relevant_chunks(
                q.question_text, db, top_k=top_k, workspace_id=workspace_id
            )
        except Exception as exc:
            report.warnings.append(f"Retrieval failed for q.id={q.id}: {exc}")
            continue

        retrieved_ids = [r.chunk.id for r in results]

        if results:
            top1_sims.append(results[0].similarity)

        # Hit@k
        if any(cid in cited_and_parents for cid in retrieved_ids):
            hits_at_k += 1

        # Precision@1
        if retrieved_ids and retrieved_ids[0] in cited_and_parents:
            hits_at_1 += 1

        # MRR
        rr = 0.0
        for rank, cid in enumerate(retrieved_ids, 1):
            if cid in cited_and_parents:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    n = len(evaluable)
    report.questions_evaluated   = n
    report.hit_rate_at_k         = round(hits_at_k / n, 3)        if n else 0.0
    report.precision_at_1        = round(hits_at_1 / n, 3)        if n else 0.0
    report.mrr                   = round(sum(reciprocal_ranks) / n, 3) if n else 0.0
    report.avg_top1_similarity   = round(sum(top1_sims) / len(top1_sims), 3) if top1_sims else 0.0

    return report
