"""Embedding generation service.

Two providers: VoyageProvider (default) and OpenAIProvider.
get_embedding_provider() returns a singleton keyed on settings.embedding_provider.
Both providers batch inputs in groups of 32 and sleep 0.5 s between batches
to respect free-tier rate limits.
"""

import abc
import asyncio
from typing import Optional

from app.config import get_settings


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    async def embed(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> list[list[float]]: ...


class VoyageProvider(EmbeddingProvider):
    def __init__(self) -> None:
        import voyageai

        settings = get_settings()
        self._client = voyageai.AsyncClient(api_key=settings.voyage_api_key)
        self._model = settings.embedding_model

    async def embed(
        self,
        texts: list[str],
        input_type: str = "document",
    ) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), 32):
            batch = texts[i : i + 32]
            response = await self._client.embed(
                batch, model=self._model, input_type=input_type
            )
            results.extend(response.embeddings)
            if i + 32 < len(texts):
                await asyncio.sleep(0.5)
        return results


class OpenAIProvider(EmbeddingProvider):
    _MODEL = "text-embedding-3-small"

    def __init__(self) -> None:
        from openai import AsyncOpenAI

        settings = get_settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed(
        self,
        texts: list[str],
        input_type: str = "document",  # unused by OpenAI, kept for interface parity
    ) -> list[list[float]]:
        results: list[list[float]] = []
        for i in range(0, len(texts), 32):
            batch = texts[i : i + 32]
            response = await self._client.embeddings.create(
                input=batch, model=self._MODEL
            )
            results.extend(item.embedding for item in response.data)
            if i + 32 < len(texts):
                await asyncio.sleep(0.5)
        return results


_provider_instance: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> EmbeddingProvider:
    global _provider_instance
    if _provider_instance is None:
        provider_name = get_settings().embedding_provider
        if provider_name == "voyage":
            _provider_instance = VoyageProvider()
        elif provider_name == "openai":
            _provider_instance = OpenAIProvider()
        else:
            raise ValueError(
                f"Unknown embedding_provider: {provider_name!r}. Must be 'voyage' or 'openai'."
            )
    return _provider_instance
