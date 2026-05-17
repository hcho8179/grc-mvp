"""Unit tests for the answer generation pipeline.

All LLM calls are mocked — no API keys required.
"""

import pytest

from app.services.generation import (
    AnswerResult,
    LLMProvider,
    _parse_json,
    generate_answer,
)
from app.services.retrieval import RetrievalResult


# ---------------------------------------------------------------------------
# Minimal stubs
# ---------------------------------------------------------------------------

class _FakeChunk:
    def __init__(self, id_: int, text: str):
        self.id = id_
        self.text = text
        self.source_document = "policy.pdf"


def _fake_result(chunk_id: int = 1, similarity: float = 0.85, text: str = "Policy text.") -> RetrievalResult:
    chunk = _FakeChunk(chunk_id, text)
    return RetrievalResult(chunk=chunk, similarity=similarity)  # type: ignore[arg-type]


class _MockLLM(LLMProvider):
    def __init__(self, responses: list[str]):
        self._responses = iter(responses)

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        return next(self._responses), 100, 50


# ---------------------------------------------------------------------------
# _parse_json
# ---------------------------------------------------------------------------

class TestParseJson:
    def test_parses_clean_json(self):
        raw = '{"answer": "yes", "confidence": "high", "cited_chunk_ids": [1], "reasoning": "clear", "insufficient_context": false}'
        result = _parse_json(raw)
        assert result["answer"] == "yes"
        assert result["confidence"] == "high"

    def test_strips_json_fences(self):
        raw = '```json\n{"answer": "x", "confidence": "low", "cited_chunk_ids": [], "reasoning": "r", "insufficient_context": false}\n```'
        result = _parse_json(raw)
        assert result is not None
        assert result["answer"] == "x"

    def test_strips_plain_fences(self):
        raw = '```\n{"answer": "x", "confidence": "low", "cited_chunk_ids": [], "reasoning": "", "insufficient_context": false}\n```'
        assert _parse_json(raw) is not None

    def test_returns_none_on_invalid_json(self):
        assert _parse_json("not json at all") is None
        assert _parse_json("```\nnot json\n```") is None


# ---------------------------------------------------------------------------
# generate_answer
# ---------------------------------------------------------------------------

VALID_JSON = '{"answer": "We use AES-256 encryption.", "confidence": "high", "cited_chunk_ids": [1, 2], "reasoning": "Direct policy match.", "insufficient_context": false}'


class TestGenerateAnswer:
    @pytest.mark.asyncio
    async def test_returns_answer_result_on_valid_response(self, monkeypatch):
        monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: _MockLLM([VALID_JSON]))
        result = await generate_answer("Do you encrypt data at rest?", [_fake_result(1), _fake_result(2)])
        assert isinstance(result, AnswerResult)
        assert result.answer == "We use AES-256 encryption."
        assert result.confidence == "high"
        assert result.cited_chunk_ids == [1, 2]
        assert not result.insufficient_context

    @pytest.mark.asyncio
    async def test_no_chunks_returns_insufficient(self, monkeypatch):
        monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: _MockLLM([]))
        result = await generate_answer("Any question?", [])
        assert result.insufficient_context
        assert result.answer == ""

    @pytest.mark.asyncio
    async def test_retries_once_on_bad_json(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.generation.get_llm_provider",
            lambda: _MockLLM(["not json", VALID_JSON]),
        )
        result = await generate_answer("Question?", [_fake_result()])
        assert result.answer == "We use AES-256 encryption."

    @pytest.mark.asyncio
    async def test_returns_insufficient_after_two_parse_failures(self, monkeypatch):
        monkeypatch.setattr(
            "app.services.generation.get_llm_provider",
            lambda: _MockLLM(["bad", "also bad"]),
        )
        result = await generate_answer("Question?", [_fake_result()])
        assert result.insufficient_context

    @pytest.mark.asyncio
    async def test_handles_markdown_fenced_response(self, monkeypatch):
        fenced = f"```json\n{VALID_JSON}\n```"
        monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: _MockLLM([fenced]))
        result = await generate_answer("Question?", [_fake_result()])
        assert not result.insufficient_context
        assert result.confidence == "high"

    @pytest.mark.asyncio
    async def test_invalid_confidence_defaults_to_low(self, monkeypatch):
        bad_conf = '{"answer": "x", "confidence": "very_high", "cited_chunk_ids": [], "reasoning": "", "insufficient_context": false}'
        monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: _MockLLM([bad_conf]))
        result = await generate_answer("Question?", [_fake_result()])
        assert result.confidence == "low"

    @pytest.mark.asyncio
    async def test_insufficient_context_flag_respected(self, monkeypatch):
        resp = '{"answer": "", "confidence": "low", "cited_chunk_ids": [], "reasoning": "no sources", "insufficient_context": true}'
        monkeypatch.setattr("app.services.generation.get_llm_provider", lambda: _MockLLM([resp]))
        result = await generate_answer("Question?", [_fake_result()])
        assert result.insufficient_context
