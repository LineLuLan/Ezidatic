"""Importing this triggers provider registry population."""

from app.services.agents.providers import groq  # noqa: F401  (registers)
from app.services.agents.providers.base import LLMProvider, ProviderRegistry

__all__ = ["LLMProvider", "ProviderRegistry"]
