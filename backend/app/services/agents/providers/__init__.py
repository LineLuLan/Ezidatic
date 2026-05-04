"""Importing this triggers provider registry population.

Every provider file uses ``@ProviderRegistry.register``. Adding a new
one = write the file + import it here. The fallback chain inside
LLMAdapter is sorted by ``LLMProvider.priority``: Groq (1) → Gemini
(2) → OpenRouter (3) → Ollama (4).
"""

from app.services.agents.providers import (  # noqa: F401  (registers)
    gemini,
    groq,
    ollama,
    openrouter,
)
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)

__all__ = ["LLMProvider", "LLMResponse", "ProviderRegistry"]
