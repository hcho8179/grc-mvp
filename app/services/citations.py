"""Question ↔ knowledge chunk citation helpers."""

from sqlalchemy.orm import Session

from app.models import question_citations


def save_citation_scores(
    db: Session,
    question_id: int,
    chunks: list,
    cited_ids: list[int],
) -> dict[int, float]:
    """Write retrieval scores to question_citations and return {chunk_id: score} map."""
    score_map = {r.chunk.id: r.similarity for r in chunks}
    db.execute(question_citations.delete().where(question_citations.c.question_id == question_id))
    for cid in cited_ids:
        if cid in score_map:
            db.execute(
                question_citations.insert().values(
                    question_id=question_id,
                    chunk_id=cid,
                    retrieval_score=score_map[cid],
                )
            )
    return score_map
