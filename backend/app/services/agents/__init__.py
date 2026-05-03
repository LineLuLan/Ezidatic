"""Agents subsystem — LLM adapter, router, workers, tools."""

from app.services.agents import providers, tools  # noqa: F401  (registers)
from app.services.agents.llm_adapter import LLMAdapter

__all__ = ["LLMAdapter"]
