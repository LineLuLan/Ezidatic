"""POL-05 — LLM response cache tests.

Uses fakeredis to provide an in-memory Redis without needing a docker
container in CI. Provider registry is cleaned around each test so the
LLMAdapter sees only the providers a given test cares about.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import fakeredis.aioredis
import pytest

from app.config import settings
from app.services.agents import cache as cache_mod
from app.services.agents.cache import LlmCache
from app.services.agents.llm_adapter import LLMAdapter
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)


@pytest.fixture
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> fakeredis.aioredis.FakeRedis:
    """Replace the lazy singleton with an in-memory fake."""
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(cache_mod, "_redis_client", fake)
    return fake


@pytest.fixture(autouse=True)
def clean_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test starts with an empty ProviderRegistry."""
    monkeypatch.setattr(ProviderRegistry, "_registry", {})


def _make_provider(
    provider_name: str = "fakeprov",
    invoke_content: str = "fresh response",
    stream_chunks: list[str] | None = None,
    stream_usage: dict[str, Any] | None = None,
    available: bool = True,
) -> type[LLMProvider]:
    """Build an ad-hoc provider class scripted with the supplied output."""
    _name = provider_name
    _chunks = stream_chunks or ["fresh ", "stream"]
    _usage = stream_usage or {"completion_tokens": 5}

    class _Fake(LLMProvider):
        name = _name
        priority = 1
        invoke_calls = 0
        stream_calls = 0

        async def is_available(self) -> bool:
            return available

        async def invoke(self, messages: list[dict[str, Any]], **kwargs: Any) -> LLMResponse:
            type(self).invoke_calls += 1
            return LLMResponse(
                content=invoke_content,
                provider=_name,
                usage={"prompt_tokens": 10, "completion_tokens": 20},
            )

        async def stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> AsyncIterator[str]:
            type(self).stream_calls += 1
            for chunk in _chunks:
                yield chunk
            self.last_stream_usage = _usage

    _Fake.__name__ = f"_Fake_{provider_name}"
    return _Fake


@pytest.fixture
def fake_messages() -> list[dict[str, Any]]:
    return [
        {"role": "system", "content": "You are a data analyst."},
        {"role": "user", "content": "Summarize this dataset."},
    ]


@pytest.mark.asyncio
async def test_invoke_cache_hit_skips_providers(
    fake_redis: fakeredis.aioredis.FakeRedis,
    fake_messages: list[dict[str, Any]],
) -> None:
    """A pre-seeded cache entry short-circuits the provider chain."""
    cached_payload = {
        "content": "from cache",
        "provider": "groq",
        "usage": {"prompt_tokens": 1, "completion_tokens": 2},
    }
    key = LlmCache.key_for(fake_messages, temperature=0.4, max_tokens=600)
    await fake_redis.setex(key, 60, json.dumps(cached_payload))

    adapter = LLMAdapter()  # no providers registered — would fail on miss
    resp = await adapter.invoke(fake_messages, temperature=0.4, max_tokens=600)

    assert resp.content == "from cache"
    assert resp.provider == "groq (cached)"
    assert adapter.last_provider == "groq (cached)"
    assert adapter.last_usage == cached_payload["usage"]


@pytest.mark.asyncio
async def test_invoke_cache_miss_calls_provider_and_persists(
    fake_redis: fakeredis.aioredis.FakeRedis,
    fake_messages: list[dict[str, Any]],
) -> None:
    """Cache miss: provider runs once, response then lives in Redis."""
    fake_cls = _make_provider(provider_name="groq", invoke_content="fresh answer")
    ProviderRegistry.register(fake_cls)

    adapter = LLMAdapter()
    resp = await adapter.invoke(fake_messages, temperature=0.4, max_tokens=600)

    assert resp.content == "fresh answer"
    assert resp.provider == "groq"
    assert fake_cls.invoke_calls == 1

    key = LlmCache.key_for(fake_messages, temperature=0.4, max_tokens=600)
    raw = await fake_redis.get(key)
    assert raw is not None
    stored = json.loads(raw)
    assert stored["content"] == "fresh answer"
    assert stored["provider"] == "groq"


@pytest.mark.asyncio
async def test_cache_disabled_bypasses_redis(
    fake_redis: fakeredis.aioredis.FakeRedis,
    fake_messages: list[dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Kill-switch path: cache layer becomes inert."""
    monkeypatch.setattr(settings, "llm_cache_enabled", False)

    fake_cls = _make_provider(provider_name="groq", invoke_content="fresh answer")
    ProviderRegistry.register(fake_cls)

    adapter = LLMAdapter()
    await adapter.invoke(fake_messages, temperature=0.4, max_tokens=600)

    assert fake_cls.invoke_calls == 1
    key = LlmCache.key_for(fake_messages, temperature=0.4, max_tokens=600)
    assert await fake_redis.get(key) is None  # nothing was stored


@pytest.mark.asyncio
async def test_stream_cache_hit_emits_single_chunk(
    fake_redis: fakeredis.aioredis.FakeRedis,
    fake_messages: list[dict[str, Any]],
) -> None:
    """Cache hit on stream: one delta with full content, no provider call."""
    cached_payload = {
        "content": "cached full text",
        "provider": "groq",
        "usage": {"completion_tokens": 7},
    }
    key = LlmCache.key_for(fake_messages, temperature=0.4, max_tokens=600)
    await fake_redis.setex(key, 60, json.dumps(cached_payload))

    adapter = LLMAdapter()  # no providers — would fail on miss
    chunks = []
    async for chunk in adapter.stream(fake_messages, temperature=0.4, max_tokens=600):
        chunks.append(chunk)

    assert chunks == ["cached full text"]
    assert adapter.last_provider == "groq (cached)"
    assert adapter.last_usage == cached_payload["usage"]


@pytest.mark.asyncio
async def test_stream_cache_miss_caches_after_completion(
    fake_redis: fakeredis.aioredis.FakeRedis,
    fake_messages: list[dict[str, Any]],
) -> None:
    """Cache miss on stream: chunks forwarded as-is, full text stored after."""
    fake_cls = _make_provider(
        provider_name="groq",
        stream_chunks=["alpha ", "beta ", "gamma"],
        stream_usage={"completion_tokens": 12},
    )
    ProviderRegistry.register(fake_cls)

    adapter = LLMAdapter()
    chunks = []
    async for chunk in adapter.stream(fake_messages, temperature=0.4, max_tokens=600):
        chunks.append(chunk)

    assert chunks == ["alpha ", "beta ", "gamma"]
    assert fake_cls.stream_calls == 1
    assert adapter.last_provider == "groq"
    assert adapter.last_usage == {"completion_tokens": 12}

    key = LlmCache.key_for(fake_messages, temperature=0.4, max_tokens=600)
    stored = json.loads(await fake_redis.get(key))
    assert stored["content"] == "alpha beta gamma"
    assert stored["provider"] == "groq"
    assert stored["usage"] == {"completion_tokens": 12}
