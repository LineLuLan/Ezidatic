"""Chat session + SSE + provider-fallback + tool tests — M5."""

import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient

from app.services.agents.llm_adapter import LLMAdapter
from app.services.agents.providers.base import (
    LLMProvider,
    LLMResponse,
    ProviderRegistry,
)
from app.services.agents.tools import ToolRegistry


# ===========================================================================
# Fake providers + helpers
# ===========================================================================


class _BaseFakeProvider(LLMProvider):
    """Per-call scripted provider so tests are deterministic."""

    name = "fake"
    priority = 1
    available_flag = True
    invoke_responses: list[LLMResponse | Exception]
    stream_responses: list[list[str] | Exception]

    def __init__(self) -> None:
        self.last_stream_usage: dict[str, Any] = {}

    async def is_available(self) -> bool:
        return self.available_flag

    async def invoke(self, messages, **kwargs) -> LLMResponse:  # type: ignore[override]
        item = self.invoke_responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    async def stream(self, messages, **kwargs) -> AsyncIterator[str]:  # type: ignore[override]
        item = self.stream_responses.pop(0)
        if isinstance(item, Exception):
            raise item
        for chunk in item:
            yield chunk
        self.last_stream_usage = {"prompt_tokens": 5, "completion_tokens": 7, "total_tokens": 12}


@pytest.fixture
def fake_registry(monkeypatch):
    """Swap in a single-fake provider registry for the duration of a test."""

    saved = dict(ProviderRegistry._registry)
    ProviderRegistry._registry.clear()

    holder: dict[str, type[_BaseFakeProvider]] = {}

    def install(invoke_responses, stream_responses, *, name="fake_primary"):
        cls = type(
            name,
            (_BaseFakeProvider,),
            {
                "name": name,
                "priority": 1,
                "invoke_responses": list(invoke_responses),
                "stream_responses": list(stream_responses),
            },
        )
        ProviderRegistry.register(cls)
        holder[name] = cls
        return cls

    yield install

    ProviderRegistry._registry.clear()
    ProviderRegistry._registry.update(saved)


# ===========================================================================
# Provider fallback
# ===========================================================================


@pytest.mark.asyncio
async def test_provider_fallback_skips_failures(fake_registry) -> None:
    bad = type(
        "FakeBad",
        (_BaseFakeProvider,),
        {
            "name": "fake_bad",
            "priority": 1,
            "invoke_responses": [RuntimeError("upstream 500")],
            "stream_responses": [RuntimeError("upstream 500")],
        },
    )
    good = type(
        "FakeGood",
        (_BaseFakeProvider,),
        {
            "name": "fake_good",
            "priority": 2,
            "invoke_responses": [
                LLMResponse(content="hello from good", provider="fake_good", usage={"total_tokens": 3})
            ],
            "stream_responses": [["chunk1", "chunk2"]],
        },
    )
    ProviderRegistry.register(bad)
    ProviderRegistry.register(good)

    adapter = LLMAdapter()
    resp = await adapter.invoke([{"role": "user", "content": "ping"}])
    assert resp.content == "hello from good"
    assert resp.provider == "fake_good"
    assert adapter.last_provider == "fake_good"


@pytest.mark.asyncio
async def test_provider_fallback_all_fail(fake_registry) -> None:
    bad = fake_registry(
        invoke_responses=[RuntimeError("boom")],
        stream_responses=[RuntimeError("boom")],
        name="fake_only_bad",
    )
    bad.priority = 1
    from app.core.exceptions import AllProvidersFailedError

    adapter = LLMAdapter()
    with pytest.raises(AllProvidersFailedError):
        await adapter.invoke([{"role": "user", "content": "x"}])


# ===========================================================================
# Router
# ===========================================================================


@pytest.mark.asyncio
async def test_router_classifies_with_robust_parsing(fake_registry) -> None:
    fake_registry(
        invoke_responses=[
            LLMResponse(
                content='```json\n{"type": "sql", "reason": "filter request"}\n```',
                provider="fake_primary",
                usage={"total_tokens": 5},
            )
        ],
        stream_responses=[],
    )
    from app.services.agents.router import QueryType, route

    adapter = LLMAdapter()
    result = await route("how many rows?", adapter)
    assert result == QueryType.SQL


@pytest.mark.asyncio
async def test_router_falls_back_to_explain_on_garbage(fake_registry) -> None:
    fake_registry(
        invoke_responses=[
            LLMResponse(
                content="I think it's a SQL question, probably.",
                provider="fake_primary",
                usage={"total_tokens": 5},
            )
        ],
        stream_responses=[],
    )
    from app.services.agents.router import QueryType, route

    adapter = LLMAdapter()
    result = await route("what is this?", adapter)
    assert result == QueryType.EXPLAIN


# ===========================================================================
# query_dataset tool
# ===========================================================================


CHAT_CSV = (
    "name,age,city\n"
    "Alice,30,Hanoi\n"
    "Bob,25,Saigon\n"
    "Carol,40,Hanoi\n"
    "Dave,35,Saigon\n"
)


@pytest.mark.asyncio
async def test_query_dataset_runs_sql(
    auth_client: AsyncClient, isolated_storage: Path, db_setup
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("p.csv", CHAT_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]
    from uuid import UUID

    tool = ToolRegistry.get("query_dataset")
    async with db_setup() as session:
        result = await tool.execute(
            sql='SELECT city, COUNT(*) AS n FROM data GROUP BY city ORDER BY n DESC',
            dataset_id=UUID(dataset_id),
            db=session,
        )
    assert "city" in result["columns"]
    assert "n" in result["columns"]
    assert result["row_count"] == 2  # Hanoi + Saigon


@pytest.mark.asyncio
async def test_query_dataset_rejects_non_select(
    auth_client: AsyncClient, isolated_storage: Path, db_setup
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("p.csv", CHAT_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]
    from uuid import UUID

    tool = ToolRegistry.get("query_dataset")
    async with db_setup() as session:
        with pytest.raises(ValueError, match="SELECT"):
            await tool.execute(
                sql="DROP TABLE data",
                dataset_id=UUID(dataset_id),
                db=session,
            )


# ===========================================================================
# Session CRUD
# ===========================================================================


@pytest.mark.asyncio
async def test_create_and_list_sessions(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    create = await auth_client.post(
        "/api/v1/chat/sessions", json={"title": "First chat"}
    )
    assert create.status_code == 200, create.text
    body = create.json()
    assert body["title"] == "First chat"
    assert body["dataset_id"] is None

    listing = await auth_client.get("/api/v1/chat/sessions")
    assert listing.status_code == 200
    rows = listing.json()
    assert len(rows) == 1
    assert rows[0]["id"] == body["id"]


@pytest.mark.asyncio
async def test_session_with_dataset_404_for_missing(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    response = await auth_client.post(
        "/api/v1/chat/sessions",
        json={"dataset_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


# ===========================================================================
# SSE message flow
# ===========================================================================


def _parse_sse(payload: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in payload.splitlines():
        if line.startswith("data:"):
            blob = line[len("data:") :].strip()
            if blob:
                out.append(json.loads(blob))
    return out


@pytest.mark.asyncio
async def test_send_message_streams_and_persists(
    auth_client: AsyncClient, isolated_storage: Path, fake_registry
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("p.csv", CHAT_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    create = await auth_client.post(
        "/api/v1/chat/sessions",
        json={"title": "smoke", "dataset_id": dataset_id},
    )
    session_id = create.json()["id"]

    # Fake provider script: 1 invoke for router, then a streamed reply.
    # No tool dispatch — keep `intent=explain` so we exercise the
    # generic streaming branch.
    fake_registry(
        invoke_responses=[
            LLMResponse(
                content='{"type": "explain", "reason": "ok"}',
                provider="fake_primary",
                usage={"total_tokens": 3},
            )
        ],
        stream_responses=[
            ["Hi", " there", "!"],
        ],
    )

    response = await auth_client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        json={"content": "Hello"},
    )
    assert response.status_code == 200
    events = _parse_sse(response.text)
    types = [e["type"] for e in events]
    assert "intent" in types
    assert types.count("delta") == 3
    assert "done" in types
    assert "saved" in types

    done = next(e for e in events if e["type"] == "done")
    assert done["content"] == "Hi there!"
    assert done["provider_used"] == "fake_primary"
    assert done["intent"] == "explain"
    assert done["token_usage"]["total_tokens"] == 12

    history = await auth_client.get(
        f"/api/v1/chat/sessions/{session_id}/messages"
    )
    rows = history.json()
    assert len(rows) == 2
    assert rows[0]["role"] == "user" and rows[0]["content"] == "Hello"
    assert rows[1]["role"] == "assistant"
    assert rows[1]["content"] == "Hi there!"
    assert rows[1]["provider_used"] == "fake_primary"
    assert rows[1]["token_usage"] == {
        "prompt_tokens": 5,
        "completion_tokens": 7,
        "total_tokens": 12,
    }


@pytest.mark.asyncio
async def test_send_message_404_for_other_workspace(
    auth_client: AsyncClient, client: AsyncClient, isolated_storage: Path
) -> None:
    create = await auth_client.post(
        "/api/v1/chat/sessions", json={"title": "private"}
    )
    session_id = create.json()["id"]

    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "other-chat@example.com", "password": "supersecret"},
    )
    other_token = register.json()["access_token"]

    response = await client.post(
        f"/api/v1/chat/sessions/{session_id}/messages",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"content": "snoop"},
    )
    assert response.status_code == 404
