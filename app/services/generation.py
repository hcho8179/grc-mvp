"""
LLM provider abstraction + answer generation pipeline.

  get_llm_provider() → LLMProvider
  generate_answer(question_text, retrieved_chunks) → AnswerResult

LLMProvider.generate() now returns (text, input_tokens, output_tokens) so
the orchestration layer can log cost via LLMCall rows.
"""

import abc
import json
import re
from dataclasses import dataclass, field
from typing import Literal

import anthropic
import google.genai as genai
import google.genai.types as genai_types

from app.config import get_settings

# ---------------------------------------------------------------------------
# Cost table  (USD per 1 M tokens, as of 2026)
# ---------------------------------------------------------------------------

_COST_TABLE: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash": (0.15, 0.60),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-opus-4":     (15.00, 75.00),
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    for key, (in_c, out_c) in _COST_TABLE.items():
        if key in model:
            return (input_tokens * in_c + output_tokens * out_c) / 1_000_000
    return 0.0


# ---------------------------------------------------------------------------
# LLM provider abstraction
# ---------------------------------------------------------------------------

class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        """Return (response_text, input_tokens, output_tokens)."""
        ...


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return (
            message.content[0].text,
            message.usage.input_tokens,
            message.usage.output_tokens,
        )


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        config = genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1024,
        )
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=config,
        )
        usage = response.usage_metadata
        return (
            response.text,
            getattr(usage, "prompt_token_count", 0) or 0,
            getattr(usage, "candidates_token_count", 0) or 0,
        )


def get_llm_provider() -> LLMProvider:
    provider = get_settings().llm_provider
    if provider == "gemini":
        return GeminiProvider()
    if provider == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Must be 'anthropic' or 'gemini'.")


# ---------------------------------------------------------------------------
# Answer generation
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a security compliance expert helping a SaaS company answer \
a security questionnaire from their enterprise customer.

You will be given:
- A question being asked
- Relevant excerpts from the company's existing policies and previous \
questionnaire answers (each labeled with chunk_id)

Your job:
1. Write a clear, professional answer based ONLY on the provided context.
2. Match the formal tone and terminology of the source material.
3. If the context is insufficient, set insufficient_context to true \
and leave answer empty.
4. Do NOT invent facts, certifications, or capabilities not in sources.
5. Keep answers concise (2-4 sentences typical, longer only if needed).
6. Cite the chunk_ids you actually used.

Confidence levels:
- high: multiple strong source chunks directly answer the question
- medium: sources partially cover the question or require some inference
- low: weak retrieval, answer likely needs human review

Respond with ONLY valid JSON in this exact format (no markdown fences):
{
  "answer": "your answer text or empty string",
  "confidence": "high" | "medium" | "low",
  "cited_chunk_ids": [1, 5, 12],
  "reasoning": "brief explanation of confidence",
  "insufficient_context": false
}"""

RETRY_SUFFIX = (
    "\n\nYour previous response could not be parsed as JSON. "
    "Reply with ONLY the raw JSON object — no prose, no markdown fences."
)


@dataclass
class AnswerResult:
    answer: str
    confidence: Literal["high", "medium", "low"]
    cited_chunk_ids: list[int] = field(default_factory=list)
    reasoning: str = ""
    insufficient_context: bool = False
    input_tokens: int = 0
    output_tokens: int = 0


_INSUFFICIENT = AnswerResult(
    answer="",
    confidence="low",
    insufficient_context=True,
    reasoning="No relevant context found above similarity threshold.",
)


def _parse_json(raw: str) -> dict | None:
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return None


def _build_user_message(question_text: str, results: list) -> str:
    lines = [f"Question: {question_text}", "", "Available sources:"]
    for r in results:
        lines.append(f"[chunk_id {r.chunk.id}, similarity {r.similarity:.2f}]: {r.chunk.text}")
    return "\n".join(lines)


async def generate_answer(question_text: str, retrieved_chunks: list) -> AnswerResult:
    """Run retrieval results through the LLM and return a structured AnswerResult.

    Returns insufficient_context immediately if no chunks were retrieved.
    Token counts are accumulated across retries and stored on the result.
    """
    if not retrieved_chunks:
        return AnswerResult(
            answer="", confidence="low", insufficient_context=True,
            reasoning="No relevant context found above similarity threshold.",
        )

    provider = get_llm_provider()
    user_msg = _build_user_message(question_text, retrieved_chunks)
    total_in = total_out = 0

    raw, in_t, out_t = await provider.generate(SYSTEM_PROMPT, user_msg)
    total_in += in_t
    total_out += out_t
    parsed = _parse_json(raw)

    if parsed is None:
        raw, in_t, out_t = await provider.generate(SYSTEM_PROMPT, user_msg + RETRY_SUFFIX)
        total_in += in_t
        total_out += out_t
        parsed = _parse_json(raw)

    if parsed is None:
        result = AnswerResult(
            answer="", confidence="low", insufficient_context=True,
            reasoning="LLM returned unparseable response after retry.",
        )
    else:
        try:
            confidence = parsed.get("confidence", "low")
            if confidence not in ("high", "medium", "low"):
                confidence = "low"
            result = AnswerResult(
                answer=str(parsed.get("answer", "")),
                confidence=confidence,
                cited_chunk_ids=[int(i) for i in parsed.get("cited_chunk_ids", [])],
                reasoning=str(parsed.get("reasoning", "")),
                insufficient_context=bool(parsed.get("insufficient_context", False)),
            )
        except Exception:
            result = AnswerResult(
                answer="", confidence="low", insufficient_context=True,
                reasoning="LLM response parsing error.",
            )

    result.input_tokens = total_in
    result.output_tokens = total_out
    return result
