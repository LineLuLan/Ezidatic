"""LLM adapter — multi-provider with automatic fallback."""

import logging
from collections.abc import AsyncIterator
from typing import Any

from app.core.exceptions import AllProvidersFailedError
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)

log = logging.getLogger(__name__)


class LLMAdapter:
    """Try registered providers in priority order until one succeeds.

    After ``invoke()`` or ``stream()`` returns/exhausts, the adapter
    exposes ``last_provider`` (str) and ``last_usage`` (dict) reflecting
    the provider that actually answered. Persistence layers read these
    after the call.
    """

    def __init__(self) -> None:
        self.providers: list[LLMProvider] = [cls() for cls in ProviderRegistry.all()]
        self.last_provider: str | None = None
        self.last_usage: dict[str, Any] = {}

    async def invoke(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> LLMResponse:
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
                return resp
            except Exception as e:  # noqa: BLE001
                log.warning("provider %s failed: %s", provider.name, e)
                last_error = e
        raise AllProvidersFailedError(
            f"All LLM providers failed (skipped={skipped}). Last error: {last_error}"
        )

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        last_error: Exception | None = None
        skipped: list[str] = []
        for provider in self.providers:
            if not await provider.is_available():
                skipped.append(provider.name)
                continue
            try:
                self.last_provider = provider.name
                self.last_usage = {}
                async for chunk in provider.stream(messages, **kwargs):
                    yield chunk
                # After exhausting, the provider populates last_stream_usage.
                self.last_usage = getattr(provider, "last_stream_usage", {}) or {}
                return
            except Exception as e:  # noqa: BLE001
                log.warning("provider %s stream failed: %s", provider.name, e)
                last_error = e
        raise AllProvidersFailedError(
            f"All LLM providers failed for stream (skipped={skipped}). "
            f"Last error: {last_error}"
        )
