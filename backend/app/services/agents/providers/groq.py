"""Groq provider — primary LLM (priority=1)."""

from collections.abc import AsyncIterator
from typing import Any

from app.config import settings
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)


@ProviderRegistry.register
class GroqProvider(LLMProvider):
    name = "groq"
    priority = 1

    def __init__(self) -> None:
        self.model = settings.groq_model
        self.last_stream_usage: dict[str, Any] = {}

    async def is_available(self) -> bool:
        return bool(settings.groq_api_key)

    async def invoke(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> LLMResponse:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.groq_api_key)
        resp = await client.chat.completions.create(
            model=kwargs.pop("model_override", self.model),
            messages=messages,  # type: ignore[arg-type]
            **kwargs,
        )
        usage = {}
        if resp.usage is not None:
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
                "total_tokens": resp.usage.total_tokens,
            }
        return LLMResponse(
            content=resp.choices[0].message.content or "",
            provider=self.name,
            usage=usage,
        )

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.groq_api_key)
        self.last_stream_usage = {}
        stream = await client.chat.completions.create(
            model=kwargs.pop("model_override", self.model),
            messages=messages,  # type: ignore[arg-type]
            stream=True,
            **kwargs,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
            # Groq emits usage on the final chunk under x_groq.usage when
            # stream_options=include_usage is set; otherwise fall back to
            # top-level usage if present.
            if getattr(chunk, "usage", None) is not None:
                self.last_stream_usage = {
                    "prompt_tokens": chunk.usage.prompt_tokens,
                    "completion_tokens": chunk.usage.completion_tokens,
                    "total_tokens": chunk.usage.total_tokens,
                }
