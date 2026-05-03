"""LLMProvider interface + ProviderRegistry."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class LLMProvider(ABC):
    name: str = "unnamed"
    priority: int = 100  # lower = tried first

    @abstractmethod
    async def is_available(self) -> bool:
        """Check API key + cached rate-limit state."""

    @abstractmethod
    async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        ...

    @abstractmethod
    async def stream(
        self, messages: list[dict[str, Any]], **kwargs: Any
    ) -> AsyncIterator[str]:
        ...


class ProviderRegistry:
    _registry: dict[str, type[LLMProvider]] = {}

    @classmethod
    def register(cls, provider_cls: type[LLMProvider]) -> type[LLMProvider]:
        cls._registry[provider_cls.name] = provider_cls
        return provider_cls

    @classmethod
    def all(cls) -> list[type[LLMProvider]]:
        return sorted(cls._registry.values(), key=lambda c: c.priority)
