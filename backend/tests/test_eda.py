"""EDA endpoint tests — M3."""

from pathlib import Path

import pytest
from httpx import AsyncClient

from app.schemas.chart import ChartSpec


MIXED_CSV = (
    "age,salary,city\n"
    "30,50000,Hanoi\n"
    "25,45000,Saigon\n"
    "40,80000,Hanoi\n"
    "35,72000,Saigon\n"
    "28,48000,Danang\n"
    "50,120000,Hanoi\n"
)

CONSTANT_CSV = (
    "always_same,age,city\n"
    "1,30,Hanoi\n"
    "1,25,Saigon\n"
    "1,40,Hanoi\n"
    "1,,Saigon\n"
)


@pytest.mark.asyncio
async def test_profile_returns_persisted_blob(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("mixed.csv", MIXED_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.get(f"/api/v1/eda/{dataset_id}/profile")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["row_count"] == 6
    assert body["column_count"] == 3
    column_names = {c["name"] for c in body["columns"]}
    assert column_names == {"age", "salary", "city"}


@pytest.mark.asyncio
async def test_charts_auto_pick_histogram_bar_heatmap(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("mixed.csv", MIXED_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.get(f"/api/v1/eda/{dataset_id}/charts")
    assert response.status_code == 200, response.text
    specs = response.json()
    assert len(specs) >= 3

    # Validate every spec round-trips through the Pydantic schema.
    for s in specs:
        ChartSpec.model_validate(s)

    types = [s["type"] for s in specs]
    assert types.count("histogram") >= 2  # age + salary numeric
    assert types.count("bar") >= 1  # city categorical
    assert types.count("heatmap") == 1  # both numeric → 1 corr matrix


@pytest.mark.asyncio
async def test_charts_handle_constant_column_without_nan(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """A constant-value column produces NaN correlations; we replace with None."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("const.csv", CONSTANT_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.get(f"/api/v1/eda/{dataset_id}/charts")
    assert response.status_code == 200
    heatmap = next(s for s in response.json() if s["type"] == "heatmap")

    # No raw NaN/Inf strings should appear in the JSON response.
    raw = response.text
    assert "NaN" not in raw
    assert "Infinity" not in raw

    # Constant-column correlations land as null.
    cells = heatmap["series"][0]["data"]
    constant_cells = [c for c in cells if c["x"] == "always_same"]
    assert any(c["value"] is None for c in constant_cells)


@pytest.mark.asyncio
async def test_eda_404_for_other_workspace(
    auth_client: AsyncClient, client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("a.csv", MIXED_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "other-eda@example.com", "password": "supersecret"},
    )
    other_token = register.json()["access_token"]

    response = await client.get(
        f"/api/v1/eda/{dataset_id}/charts",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404
