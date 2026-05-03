"""LLM adapter — multi-provider with automatic fallback."""

import logging
from collections.abc import AsyncIterator
from typing import Any

from app.core.exceptions import AllProvidersFailedError
from app.services.agents.providers.base import LLMProvider, ProviderRegistry

log = logging.getLogger(__name__)


class LLMAdapter:
    """Try registered providers in priority order until one succeeds."""

    def __init__(self) -> None:
        self.providers: list[LLMProvider] = [cls() for cls in ProviderRegistry.all()]

    async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        last_error: Exception | None = None
        for provider in self.providers:
            if not await provider.is_available():
                continue
            try:
                return await provider.invoke(messages, **kwargs)
            except Exception as e:  # noqa: BLE001
                log.warning("provider %s failed: %s", provider.name, e)
                last_error = e
        raise AllProvidersFailedError(
            f"All LLM providers failed. Last: {last_error}"
        )

    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        last_error: Exception | None = None
        for provider in self.providers:
            if not await provider.is_available():
                continue
            try:
                async for chunk in provider.stream(messages, **kwargs):
                    yield chunk
                return
            except Exception as e:  # noqa: BLE001
                log.warning("provider %s stream failed: %s", provider.name, e)
                last_error = e
        raise AllProvidersFailedError(
            f"All LLM providers failed for stream. Last: {last_error}"
        )
