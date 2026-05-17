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
    similarity_threshold: float = 0.5,
) -> list[RetrievalResult]:
    """Embed *question_text* and return the top-K most similar KnowledgeChunks.

    Chunks whose cosine similarity falls below *similarity_threshold* are
    excluded.  Results are ordered highest-similarity first.
    """
    provider = get_embedding_provider()
    embeddings = await provider.embed([question_text], input_type="query")
    query_vec = embeddings[0]

    # Inline the vector literal — values come from our own embedding service
    # so they are trusted floats; no SQL-injection risk.
    vec_str = "[" + ",".join(str(v) for v in query_vec) + "]"

    rows = db.execute(
        text(f"""
            SELECT id,
                   1 - (embedding <=> '{vec_str}'::vector) AS similarity
            FROM   knowledge_chunks
            WHERE  embedding IS NOT NULL
            ORDER  BY embedding <=> '{vec_str}'::vector
            LIMIT  :k
        """),
        {"k": top_k},
    ).fetchall()

    if not rows:
        return []

    # Bulk-load the matching chunks
    above = [(row.id, float(row.similarity)) for row in rows if float(row.similarity) >= similarity_threshold]
    if not above:
        return []

    ids = [r[0] for r in above]
    sim_by_id = {r[0]: r[1] for r in above}
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(ids)).all()
    chunk_by_id = {c.id: c for c in chunks}

    return [
        RetrievalResult(chunk=chunk_by_id[cid], similarity=sim)
        for cid, sim in above
        if cid in chunk_by_id
    ]
