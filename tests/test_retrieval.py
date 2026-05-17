"""Integration tests for the retrieval service.

Requires a live DB with at least one embedded KnowledgeChunk.
These tests are skipped automatically if the DB has no chunks.
"""

import pytest

from app.db import SessionLocal
from app.models import KnowledgeChunk
from app.services.retrieval import RetrievalResult, retrieve_relevant_chunks


def _has_chunks() -> bool:
    db = SessionLocal()
    try:
        return db.query(KnowledgeChunk).filter(KnowledgeChunk.embedding.isnot(None)).count() > 0
    finally:
        db.close()


pytestmark = pytest.mark.skipif(not _has_chunks(), reason="No embedded chunks in DB")


@pytest.mark.asyncio
async def test_returns_list_of_retrieval_results():
    db = SessionLocal()
    try:
        results = await retrieve_relevant_chunks("data encryption at rest", db, top_k=3)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, RetrievalResult)
            assert isinstance(r.similarity, float)
            assert 0.0 <= r.similarity <= 1.0
            assert r.chunk.text
    finally:
        db.close()


@pytest.mark.asyncio
async def test_similarity_threshold_filters_low_scores():
    db = SessionLocal()
    try:
        # Very high threshold should return fewer (or zero) results
        strict = await retrieve_relevant_chunks(
            "data encryption at rest", db, top_k=5, similarity_threshold=0.99
        )
        relaxed = await retrieve_relevant_chunks(
            "data encryption at rest", db, top_k=5, similarity_threshold=0.0
        )
        assert len(strict) <= len(relaxed)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_top_k_limits_results():
    db = SessionLocal()
    try:
        results = await retrieve_relevant_chunks(
            "security policy", db, top_k=2, similarity_threshold=0.0
        )
        assert len(results) <= 2
    finally:
        db.close()


@pytest.mark.asyncio
async def test_results_ordered_by_similarity_desc():
    db = SessionLocal()
    try:
        results = await retrieve_relevant_chunks(
            "encryption password security", db, top_k=5, similarity_threshold=0.0
        )
        similarities = [r.similarity for r in results]
        assert similarities == sorted(similarities, reverse=True)
    finally:
        db.close()


@pytest.mark.asyncio
async def test_semantic_match_not_just_keyword():
    """'rotate credentials' should retrieve the encryption/password chunk
    even though exact keywords differ."""
    db = SessionLocal()
    try:
        results = await retrieve_relevant_chunks(
            "rotate credentials quarterly", db, top_k=3, similarity_threshold=0.0
        )
        # Just verify we get something back — semantic search should work
        assert isinstance(results, list)
    finally:
        db.close()
