"""
LLM provider abstraction + answer generation pipeline.

Priority order (best quality → most quota):
  1. Gemini 2.5 Flash          — best quality,  20 req/day  (Google AI Studio key)
  2. Gemma 3 27B               — great quality, 14,400/day  (same Google key, separate quota!)
  3. Groq  Llama 3.3 70B       — great quality, 1,000/day   (GROQ_API_KEY)
  4. Groq  Llama 4 Scout       — good quality,  1,000/day   (GROQ_API_KEY)
  5. Cerebras gpt-oss-120b     — good quality,  14,400/day  (CEREBRAS_API_KEY)
  6. Groq  Llama 3.1 8B        — decent,        14,400/day  (GROQ_API_KEY)
  7. OpenRouter Llama 3.3 70B  — great quality, 50/day      (OPENROUTER_API_KEY)
  8. OpenRouter DeepSeek Flash — good quality,  50/day      (OPENROUTER_API_KEY)

429 = quota exhausted → skip immediately, mark exhausted for this session
503 = overloaded     → retry same model up to 3× with 10s between, then skip
"""

import abc
import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Literal

import anthropic
import google.genai as genai
import google.genai.types as genai_types

from app.config import get_settings

# ---------------------------------------------------------------------------
# Cost table  (USD per 1 M tokens)
# ---------------------------------------------------------------------------

_COST_TABLE: dict[str, tuple[float, float]] = {
    "gemini-2.5-flash":  (0.15, 0.60),
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
# Exhaustion tracker — expires after 24 hours so quotas auto-restore
# ---------------------------------------------------------------------------

_exhausted: dict[str, float] = {}  # key → timestamp when it was marked exhausted
_EXHAUST_TTL = 24 * 60 * 60  # 24 hours in seconds


def _is_exhausted(key: str) -> bool:
    import time
    ts = _exhausted.get(key)
    if ts is None:
        return False
    if time.time() - ts > _EXHAUST_TTL:
        del _exhausted[key]  # quota restored, remove from list
        return False
    return True


def _mark_exhausted(key: str) -> None:
    import time
    _exhausted[key] = time.time()
    print(f"[LLM] {key} marked exhausted — will retry after 24h")


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class LLMProvider(abc.ABC):
    key: str  # unique identifier for exhaustion tracking

    @abc.abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        """Return (response_text, input_tokens, output_tokens)."""
        ...


# ---------------------------------------------------------------------------
# Gemini / Gemma  (Google AI Studio — google-genai SDK)
# ---------------------------------------------------------------------------

class GeminiModelProvider(LLMProvider):
    def __init__(self, model: str) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = model
        self.key = f"gemini:{model}"

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


# ---------------------------------------------------------------------------
# OpenAI-compatible providers (Groq, Cerebras, OpenRouter)
# ---------------------------------------------------------------------------

class OpenAICompatProvider(LLMProvider):
    def __init__(self, base_url: str, api_key: str, model: str, label: str) -> None:
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._model = model
        self.key = f"{label}:{model}"

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=1024,
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        in_t  = resp.usage.prompt_tokens     if resp.usage else 0
        out_t = resp.usage.completion_tokens if resp.usage else 0
        return text, in_t, out_t


# ---------------------------------------------------------------------------
# Anthropic  (kept for paid users)
# ---------------------------------------------------------------------------

class OllamaProvider(LLMProvider):
    """Local Ollama server — unlimited, offline, ultimate fallback.
    Install: brew install ollama && ollama pull llama3.2 && ollama serve
    """
    def __init__(self, model: str = "llama3.2") -> None:
        self._model = model
        self.key = f"ollama:{model}"

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # Ollama doesn't need a real key
        )
        resp = await client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=1024,
            temperature=0.2,
        )
        text = resp.choices[0].message.content or ""
        in_t  = resp.usage.prompt_tokens     if resp.usage else 0
        out_t = resp.usage.completion_tokens if resp.usage else 0
        return text, in_t, out_t


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model
        self.key = f"anthropic:{self._model}"

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


# ---------------------------------------------------------------------------
# Provider list builder — only includes providers with keys configured
# ---------------------------------------------------------------------------

def _build_provider_list() -> list[LLMProvider]:
    s = get_settings()
    providers: list[LLMProvider] = []

    # 1. Gemini 2.5 Flash ⭐⭐⭐⭐⭐ — best quality, 20 req/day
    if s.gemini_api_key:
        providers.append(GeminiModelProvider("gemini-2.5-flash"))

    # 2. Groq Llama 3.3 70B ⭐⭐⭐⭐⭐ — excellent, very fast, 1,000 req/day
    if s.groq_api_key:
        providers.append(OpenAICompatProvider(
            base_url="https://api.groq.com/openai/v1",
            api_key=s.groq_api_key,
            model="llama-3.3-70b-versatile",
            label="groq",
        ))

    # 3. Cerebras gpt-oss-120b ⭐⭐⭐⭐⭐ — 120B model, 14,400 req/day
    if s.cerebras_api_key:
        providers.append(OpenAICompatProvider(
            base_url="https://api.cerebras.ai/v1",
            api_key=s.cerebras_api_key,
            model="gpt-oss-120b",
            label="cerebras",
        ))

    # 4. Groq Llama 4 Scout ⭐⭐⭐⭐ — good reasoning, 1,000 req/day
    if s.groq_api_key:
        providers.append(OpenAICompatProvider(
            base_url="https://api.groq.com/openai/v1",
            api_key=s.groq_api_key,
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            label="groq",
        ))

    # 5. OpenRouter Llama 3.3 70B ⭐⭐⭐⭐ — same model as #2, separate quota, 50 req/day
    if s.openrouter_api_key:
        providers.append(OpenAICompatProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=s.openrouter_api_key,
            model="meta-llama/llama-3.3-70b-instruct:free",
            label="openrouter",
        ))

    # 6. OpenRouter DeepSeek V4 Flash ⭐⭐⭐⭐ — strong reasoning, 50 req/day
    if s.openrouter_api_key:
        providers.append(OpenAICompatProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=s.openrouter_api_key,
            model="deepseek/deepseek-v4-flash:free",
            label="openrouter",
        ))

    # 7. Gemini 3.1 Flash Lite ⭐⭐⭐ — reliable lite, 500 req/day
    if s.gemini_api_key:
        providers.append(GeminiModelProvider("gemini-3.1-flash-lite"))

    # 8. Gemma 4 31B ⭐⭐⭐ — separate quota pool, 14,400 req/day
    if s.gemini_api_key:
        providers.append(GeminiModelProvider("gemma-4-31b-it"))

    # 9. Gemma 4 26B ⭐⭐⭐ — another separate pool, 14,400 req/day
    if s.gemini_api_key:
        providers.append(GeminiModelProvider("gemma-4-26b-a4b-it"))

    # 10. Gemini 2.5 Flash Lite ⭐⭐ — 20 req/day
    if s.gemini_api_key:
        providers.append(GeminiModelProvider("gemini-2.5-flash-lite"))

    # 11. Gemini 3 Flash Preview ⭐⭐ — 20 req/day
    if s.gemini_api_key:
        providers.append(GeminiModelProvider("gemini-3-flash-preview"))

    # 12. Groq Llama 3.1 8B ⭐⭐ — only 8B but 14,400 req/day
    if s.groq_api_key:
        providers.append(OpenAICompatProvider(
            base_url="https://api.groq.com/openai/v1",
            api_key=s.groq_api_key,
            model="llama-3.1-8b-instant",
            label="groq",
        ))

    # 13. Anthropic Claude ⭐⭐⭐⭐⭐ — paid, ultimate cloud backup
    if s.anthropic_api_key:
        providers.append(AnthropicProvider())

    # 14. Local Ollama ⭐ — unlimited, offline, last resort
    # Install: brew install ollama && ollama pull llama3.2 && ollama serve
    providers.append(OllamaProvider(model=s.ollama_model))

    return providers


def get_llm_provider() -> "MultiProvider":
    return MultiProvider()


# ---------------------------------------------------------------------------
# MultiProvider — tries providers in order, handles 429/503 gracefully
# ---------------------------------------------------------------------------

class MultiProvider(LLMProvider):
    key = "multi"

    async def generate(self, system_prompt: str, user_prompt: str) -> tuple[str, int, int]:
        providers = _build_provider_list()

        if not providers:
            raise RuntimeError("No LLM providers configured. Add at least GEMINI_API_KEY to .env")

        last_err: Exception | None = None

        for provider in providers:
            if _is_exhausted(provider.key):
                continue

            for attempt in range(3):
                try:
                    result = await asyncio.wait_for(
                        provider.generate(system_prompt, user_prompt),
                        timeout=30.0,
                    )
                    if attempt > 0 or provider.key != "gemini:gemini-2.5-flash":
                        print(f"[LLM] used {provider.key}")
                    return result

                except asyncio.TimeoutError:
                    last_err = Exception(f"{provider.key} timed out after 30s")
                    print(f"[LLM] {provider.key} timed out, skipping")
                    break

                except Exception as e:
                    msg = str(e)

                    # 503 / overloaded — retry same model with short wait
                    if "503" in msg or "UNAVAILABLE" in msg or "high demand" in msg or "overloaded" in msg:
                        last_err = e
                        if attempt < 2:
                            await asyncio.sleep(10)
                            continue
                        print(f"[LLM] {provider.key} unavailable after 3 attempts, skipping")
                        break

                    # 429 / quota exhausted — skip this provider for the session
                    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "rate_limit" in msg.lower():
                        _mark_exhausted(provider.key)
                        print(f"[LLM] {provider.key} quota exhausted, switching provider")
                        last_err = e
                        break

                    # 404 / model not found — skip silently
                    if "404" in msg or "NOT_FOUND" in msg or "not found" in msg.lower():
                        last_err = e
                        break

                    # Ollama not running or model not pulled — skip gracefully
                    if "connection refused" in msg.lower() or "connection error" in msg.lower():
                        print(f"[LLM] Ollama not running. Start with: ollama serve")
                        last_err = e
                        break

                    # Any other error — surface it immediately
                    raise

        raise RuntimeError(
            "All LLM providers exhausted or unavailable.\n"
            "Options:\n"
            "  1. Run local Ollama: brew install ollama && ollama pull llama3.2 && ollama serve\n"
            "  2. Add cloud keys to .env: GROQ_API_KEY, CEREBRAS_API_KEY, OPENROUTER_API_KEY\n"
            "  3. Add billing at aistudio.google.com\n"
            f"Last error: {last_err}"
        )


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
7. Always set short_answer to exactly one of: "Yes", "No", "Partial", "N/A".
   This is used when the questionnaire has a separate Yes/No column.

Confidence levels:
- high: multiple strong source chunks directly answer the question
- medium: sources partially cover the question or require some inference
- low: weak retrieval, answer likely needs human review

Respond with ONLY valid JSON in this exact format (no markdown fences):
{
  "answer": "your answer text or empty string",
  "short_answer": "Yes" | "No" | "Partial" | "N/A",
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
    short_answer: str = "N/A"
    cited_chunk_ids: list[int] = field(default_factory=list)
    reasoning: str = ""
    insufficient_context: bool = False
    input_tokens: int = 0
    output_tokens: int = 0


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
    if not retrieved_chunks:
        return AnswerResult(
            answer="", confidence="low", insufficient_context=True,
            reasoning="No knowledge base documents found. Write this answer manually based on your company's actual policies.",
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
            short_answer = parsed.get("short_answer", "N/A")
            if short_answer not in ("Yes", "No", "Partial", "N/A"):
                short_answer = "N/A"
            result = AnswerResult(
                answer=str(parsed.get("answer", "")),
                short_answer=short_answer,
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
