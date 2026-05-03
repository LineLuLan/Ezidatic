"""Shared pytest fixtures.

Tests run against an in-memory SQLite via aiosqlite. We override the
`db_session` dependency so the app uses our test engine instead of the
real one configured by `Settings.database_url`.

`StaticPool` makes every connection share the same SQLite memory store,
which is required because each new aiosqlite connection would otherwise
start with an empty schema.
"""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.api.deps import db_session
from app.config import settings
from app.main import app
from app.models import Base
from app.services import ingestion  # noqa: F401  (populate ParserRegistry)


@pytest_asyncio.fixture
async def db_setup() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest_asyncio.fixture
async def client(
    db_setup: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncClient]:
    async def override_db_session() -> AsyncIterator[AsyncSession]:
        async with db_setup() as session:
            yield session

    app.dependency_overrides[db_session] = override_db_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """A client preloaded with an Authorization header for a fresh user."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "tester@example.com", "password": "supersecret"},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect file uploads to a tmp dir for the duration of the test."""
    monkeypatch.setattr(settings, "local_storage_dir", str(tmp_path))
    return tmp_path
