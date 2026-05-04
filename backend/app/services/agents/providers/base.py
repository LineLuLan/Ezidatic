"""LLMProvider interface + ProviderRegistry."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResponse:
    """Single response from an LLM provider — content + telemetry.

    `usage` is whatever the provider reports (typically prompt_tokens,
    completion_tokens, total_tokens). Stays a free-form dict so each
    provider can include extra fields without forcing the consumer to
    care.
    """

    content: str
    provider: str
    usage: dict[str, Any] = field(default_factory=dict)


class LLMProvider(ABC):
    name: str = "unnamed"
    priority: int = 100  # lower = tried first

    @abstractmethod
    async def is_available(self) -> bool:
        """Check API key + cached rate-limit state."""

    @abstractmethod
    async def invoke(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> LLMResponse:
        """One-shot generation. Returns content + telemetry."""

    @abstractmethod
    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        """Stream content as text deltas. Token usage (if any) should be
        recorded on the provider instance via ``self.last_stream_usage``
        once the stream finishes — adapters read it after exhausting the
        iterator.
        """


class ProviderRegistry:
    _registry: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, provider_cls: type[LLMProvider]) -> type[LLMProvider]:
        cls._registry[provider_cls.name] = provider_cls
        return provider_cls

    @classmethod
    def all(cls) -> list[type[LLMProvider]]:
        return sorted(cls._registry.values(), key=lambda c: c.priority)
