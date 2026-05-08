"""Redis-backed cache for LLM responses (POL-05).

Cache key is derived from the *input* envelope only — messages,
temperature, max_tokens, response_format. The provider that actually
answered is preserved inside the cached *value* so persistence layers
still surface provenance via `provider_used` (e.g. ``"groq (cached)"``
on a cache hit). This means a cached Groq answer is served even when
Groq is down on the next request — by design, the user gets a faster
response and we save a fallback round-trip.

Failure modes are non-fatal: if Redis is unreachable (dev without
docker, network blip, Upstash quota exhausted), `get` returns None
and `set` silently no-ops. The chat path then falls through to the
provider chain as if no cache existed.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from redis.asyncio import Redis

from app.config import settings

log = logging.getLogger(__name__)


_redis_client: Redis | None = None


def _get_client() -> Redis:
    """Lazy module-level singleton. Reads `settings.redis_url` once on
    first call. Tests monkeypatch `_redis_client` directly to inject
    fakeredis."""
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def _reset_client_for_tests() -> None:
    """Drop the singleton — used by tests when swapping in fakeredis."""
    global _redis_client
    _redis_client = None


class LlmCache:
    """Hash-keyed JSON cache for LLM responses.

    All methods are static — `LlmCache` is a namespace, not a stateful
    object. Holding state would couple the cache to a specific Redis
    instance and break the lazy singleton pattern.
    """

    KEY_PREFIX = "llm:"

    @staticmethod
    def key_for(messages: list[dict[str, Any]], **kwargs: Any) -> str:
        """Stable cache key fingerprint.

        `provider` is deliberately excluded so the same input shares a
        single cached response across the Groq/Gemini/OpenRouter/Ollama
        chain — saves cost on the demo's free-tier quotas. If a future
        feature needs provider-specific caching (e.g. comparing outputs
        across providers), include `provider` in the kwargs tuple here.
        """
        payload = {
            "messages": messages,
            "temperature": kwargs.get("temperature"),
            "max_tokens": kwargs.get("max_tokens"),
            "response_format": kwargs.get("response_format"),
        }
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return LlmCache.KEY_PREFIX + digest

    @staticmethod
    async def get(key: str) -> dict[str, Any] | None:
        """Return the cached payload (`{content, provider, usage}`) or
        None on miss / disabled / Redis error."""
        if not settings.llm_cache_enabled:
            return None
        try:
            raw = await _get_client().get(key)
        except Exception as exc:  # noqa: BLE001 — cache failure is non-fatal
            log.warning("llm_cache get failed: %s", exc)
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Stale / corrupted entry — treat as miss.
            return None

    @staticmethod
    async def set(key: str, value: dict[str, Any], ttl: int | None = None) -> None:
        """Persist with TTL. Silent no-op when disabled or on Redis error."""
        if not settings.llm_cache_enabled:
            return
        ttl = ttl or settings.llm_cache_ttl_seconds
        try:
            await _get_client().setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception as exc:  # noqa: BLE001 — cache failure is non-fatal
            log.warning("llm_cache set failed: %s", exc)
