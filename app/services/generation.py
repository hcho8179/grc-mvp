"""
LLM provider abstraction for answer generation.

  get_llm_provider() returns the correct provider based on settings.llm_provider.
  Callers only ever call:  text = await provider.generate(system_prompt, user_prompt)
"""

import abc

import anthropic
import google.genai as genai
import google.genai.types as genai_types

from app.config import get_settings


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class AnthropicProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self._model = settings.claude_model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text


class GeminiProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.gemini_model

    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        config = genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=1024,
        )
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=user_prompt,
            config=config,
        )
        return response.text


def get_llm_provider() -> LLMProvider:
    provider = get_settings().llm_provider
    if provider == "gemini":
        return GeminiProvider()
    if provider == "anthropic":
        return AnthropicProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r}. Must be 'anthropic' or 'gemini'.")
