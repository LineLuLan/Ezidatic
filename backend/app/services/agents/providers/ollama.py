"""Ollama provider — fallback #3 (priority=4). Local, no API key required.

Ollama exposes both a native /api/chat endpoint and an OpenAI-compatible
/v1/chat/completions endpoint. We use the native one so we can detect
the local server's reachability via a fast /api/tags ping.
"""

from collections.abc import AsyncIterator
from typing import Any

from app.config import settings
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)


@ProviderRegistry.register
class OllamaProvider(LLMProvider):
    name = "ollama"
    priority = 4

    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.last_stream_usage: dict[str, Any] = {}

    async def is_available(self) -> bool:
        """Reachable only if the local Ollama daemon is up. Fast probe via
        /api/tags so we fail fast if the user never started Ollama.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                return resp.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    async def invoke(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> LLMResponse:
        import httpx

        kwargs.pop("response_format", None)
        body = {
            "model": kwargs.pop("model_override", self.model),
            "messages": messages,
            "stream": False,
        }
        if "temperature" in kwargs:
            body.setdefault("options", {})["temperature"] = kwargs.pop("temperature")
        if "max_tokens" in kwargs:
            body.setdefault("options", {})["num_predict"] = kwargs.pop("max_tokens")

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{self.base_url}/api/chat", json=body)
            resp.raise_for_status()
            data = resp.json()

        text = data.get("message", {}).get("content", "") or ""
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        }
        return LLMResponse(content=text, provider=self.name, usage=usage)

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        import httpx
        import json as _json

        self.last_stream_usage = {}
        kwargs.pop("response_format", None)
        body = {
            "model": kwargs.pop("model_override", self.model),
            "messages": messages,
            "stream": True,
        }
        if "temperature" in kwargs:
            body.setdefault("options", {})["temperature"] = kwargs.pop("temperature")
        if "max_tokens" in kwargs:
            body.setdefault("options", {})["num_predict"] = kwargs.pop("max_tokens")

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST", f"{self.base_url}/api/chat", json=body
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = _json.loads(line)
                    except _json.JSONDecodeError:
                        continue
                    piece = data.get("message", {}).get("content")
                    if piece:
                        yield piece
                    if data.get("done"):
                        self.last_stream_usage = {
                            "prompt_tokens": data.get("prompt_eval_count", 0),
                            "completion_tokens": data.get("eval_count", 0),
                            "total_tokens": (
                                data.get("prompt_eval_count", 0)
                                + data.get("eval_count", 0)
                            ),
                        }
