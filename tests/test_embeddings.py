"""Live embedding test — requires VOYAGE_API_KEY in .env."""

import pytest

from app.config import get_settings
from app.services.embeddings import VoyageProvider, get_embedding_provider


@pytest.mark.asyncio
async def test_voyage_embed_single_text():
    settings = get_settings()
    if not settings.voyage_api_key:
        pytest.skip("VOYAGE_API_KEY not set")

    provider = get_embedding_provider()
    assert isinstance(provider, VoyageProvider)

    embeddings = await provider.embed(["What is your data retention policy?"])

    assert len(embeddings) == 1
    assert len(embeddings[0]) == 1024
    assert all(isinstance(v, float) for v in embeddings[0])


@pytest.mark.asyncio
async def test_voyage_embed_batch():
    settings = get_settings()
    if not settings.voyage_api_key:
        pytest.skip("VOYAGE_API_KEY not set")

    provider = get_embedding_provider()
    texts = [f"Security policy statement number {i}." for i in range(5)]
    embeddings = await provider.embed(texts)

    assert len(embeddings) == 5
    for vec in embeddings:
        assert len(vec) == 1024
