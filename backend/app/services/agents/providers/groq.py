"""Groq provider — sample LLMProvider implementation (priority 1)."""

from collections.abc import AsyncIterator
from typing import Any

from app.config import settings
from app.services.agents.providers.base import LLMProvider, ProviderRegistry


@ProviderRegistry.register
class GroqProvider(LLMProvider):
    name = "groq"
    priority = 1

    def __init__(self) -> None:
        self.model = settings.groq_model

    async def is_available(self) -> bool:
        return bool(settings.groq_api_key)

    async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.groq_api_key)
        resp = await client.chat.completions.create(
            model=kwargs.pop("model_override", self.model),
            messages=messages,  # type: ignore[arg-type]
            **kwargs,
        )
        return resp.choices[0].message.content or ""

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.groq_api_key)
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
