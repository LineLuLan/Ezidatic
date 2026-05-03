"""Smoke test — health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "version" in payload


@pytest.mark.asyncio
async def test_csv_parser_registered() -> None:
    from app.services.ingestion import csv_parser  # noqa: F401
    from app.services.ingestion.base import ParserRegistry

    assert ".csv" in ParserRegistry._registry
    assert ".tsv" in ParserRegistry._registry


@pytest.mark.asyncio
async def test_lightgbm_registered() -> None:
    from app.services.ml import estimators  # noqa: F401
    from app.services.ml.base_estimator import ModelRegistry

    assert "lightgbm_classifier" in ModelRegistry._registry


@pytest.mark.asyncio
async def test_groq_provider_registered() -> None:
    from app.services.agents import providers  # noqa: F401
    from app.services.agents.providers.base import ProviderRegistry

    names = [p.name for p in ProviderRegistry.all()]
    assert "groq" in names
