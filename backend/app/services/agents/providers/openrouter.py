"""OpenRouter provider — fallback #2 (priority=3).

OpenRouter exposes an OpenAI-compatible endpoint at /api/v1/chat/completions.
We use httpx directly so we don't pull in the openai SDK just for one
provider.
"""

from collections.abc import AsyncIterator
from typing import Any

from app.config import settings
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)


_BASE_URL = "https://openrouter.ai/api/v1"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "Ezidatic",
    }


@ProviderRegistry.register
class OpenRouterProvider(LLMProvider):
    name = "openrouter"
    priority = 3

    def __init__(self) -> None:
        self.model = settings.openrouter_model
        self.last_stream_usage: dict[str, Any] = {}

    async def is_available(self) -> bool:
        return bool(settings.openrouter_api_key)

    async def invoke(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> LLMResponse:
        import httpx

        body = {
            "model": kwargs.pop("model_override", self.model),
            "messages": messages,
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{_BASE_URL}/chat/completions", headers=_headers(), json=body
            )
            resp.raise_for_status()
            data = resp.json()

        text = data["choices"][0]["message"].get("content", "") or ""
        usage_meta = data.get("usage") or {}
        usage = {
            "prompt_tokens": usage_meta.get("prompt_tokens", 0),
            "completion_tokens": usage_meta.get("completion_tokens", 0),
            "total_tokens": usage_meta.get("total_tokens", 0),
        }
        return LLMResponse(content=text, provider=self.name, usage=usage)

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        import httpx
        import json as _json

        self.last_stream_usage = {}
        body = {
            "model": kwargs.pop("model_override", self.model),
            "messages": messages,
            "stream": True,
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{_BASE_URL}/chat/completions",
                headers=_headers(),
                json=body,
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    chunk_text = line[len("data:") :].strip()
                    if chunk_text == "[DONE]":
                        break
                    try:
                        data = _json.loads(chunk_text)
                    except _json.JSONDecodeError:
                        continue
                    for choice in data.get("choices", []):
                        delta = choice.get("delta", {})
                        piece = delta.get("content")
                        if piece:
                            yield piece
                    if (usage_meta := data.get("usage")) is not None:
                        self.last_stream_usage = {
                            "prompt_tokens": usage_meta.get("prompt_tokens", 0),
                            "completion_tokens": usage_meta.get(
                                "completion_tokens", 0
                            ),
                            "total_tokens": usage_meta.get("total_tokens", 0),
                        }
