"""LLM adapter — multi-provider with automatic fallback + Redis cache."""

import logging
from collections.abc import AsyncIterator
from typing import Any

from app.core.exceptions import AllProvidersFailedError
from app.services.agents.cache import LlmCache
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)

log = logging.getLogger(__name__)


class LLMAdapter:
    """Try registered providers in priority order until one succeeds,
    with a Redis-backed response cache (POL-05) wrapped above the chain.

    After ``invoke()`` or ``stream()`` returns/exhausts, the adapter
    exposes ``last_provider`` (str) and ``last_usage`` (dict) reflecting
    the provider that actually answered. Persistence layers read these
    after the call. On a cache hit, ``last_provider`` is suffixed with
    ``" (cached)"`` so chat history surfaces provenance.
    """

    def __init__(self) -> None:
        self.providers: list[LLMProvider] = [cls() for cls in ProviderRegistry.all()]
        self.last_provider: str | None = None
        self.last_usage: dict[str, Any] = {}

    async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> LLMResponse:
        cache_key = LlmCache.key_for(messages, **kwargs)
        cached = await LlmCache.get(cache_key)
        if cached is not None:
            self.last_provider = f"{cached['provider']} (cached)"
            self.last_usage = cached.get("usage", {})
            return LLMResponse(
                content=cached["content"],
                provider=self.last_provider,
                usage=self.last_usage,
            )

        last_error: Exception | None = None
        skipped: list[str] = []
        for provider in self.providers:
            if not await provider.is_available():
                skipped.append(provider.name)
                continue
            try:
                resp = await provider.invoke(messages, **kwargs)
                self.last_provider = resp.provider
                self.last_usage = resp.usage
                await LlmCache.set(
                    cache_key,
                    {
                        "content": resp.content,
                        "provider": resp.provider,
                        "usage": resp.usage,
                    },
                )
                return resp
            except Exception as e:  # noqa: BLE001
                log.warning("provider %s failed: %s", provider.name, e)
                last_error = e
        raise AllProvidersFailedError(
            f"All LLM providers failed (skipped={skipped}). Last error: {last_error}"
        )

    async def stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> AsyncIterator[str]:
        cache_key = LlmCache.key_for(messages, **kwargs)
        cached = await LlmCache.get(cache_key)
        if cached is not None:
            self.last_provider = f"{cached['provider']} (cached)"
            self.last_usage = cached.get("usage", {})
            yield cached["content"]
            return

        last_error: Exception | None = None
        skipped: list[str] = []
        for provider in self.providers:
            if not await provider.is_available():
                skipped.append(provider.name)
                continue
            try:
                self.last_provider = provider.name
                self.last_usage = {}
                chunks: list[str] = []
                async for chunk in provider.stream(messages, **kwargs):
                    chunks.append(chunk)
                    yield chunk
                # After exhausting, the provider populates last_stream_usage.
                self.last_usage = getattr(provider, "last_stream_usage", {}) or {}
                await LlmCache.set(
                    cache_key,
                    {
                        "content": "".join(chunks),
                        "provider": provider.name,
                        "usage": self.last_usage,
                    },
                )
                return
            except Exception as e:  # noqa: BLE001
                log.warning("provider %s stream failed: %s", provider.name, e)
                last_error = e
        raise AllProvidersFailedError(
            f"All LLM providers failed for stream (skipped={skipped}). " f"Last error: {last_error}"
        )
