"""Dataset upload + list + detail tests — M1."""

from pathlib import Path

import pytest
from httpx import AsyncClient


SAMPLE_CSV = (
    "name,age,city\n"
    "Alice,30,Hanoi\n"
    "Bob,25,Saigon\n"
    "Carol,,Hanoi\n"
    "Dave,40,Saigon\n"
)


@pytest.mark.asyncio
async def test_upload_csv_returns_ready_with_profile(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    response = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("people.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ready"
    assert body["row_count"] == 4
    assert body["column_count"] == 3
    assert body["original_name"] == "people.csv"
    assert body["file_format"] == "csv"

    # File was actually written to the isolated storage dir
    saved = list(isolated_storage.glob("*.csv"))
    assert len(saved) == 1


@pytest.mark.asyncio
async def test_upload_unsupported_format_rejected(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    response = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("data.unknown", b"random", "application/octet-stream")},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "unsupported_format"


@pytest.mark.asyncio
async def test_upload_requires_auth(client: AsyncClient, isolated_storage: Path) -> None:
    response = await client.post(
        "/api/v1/datasets",
        files={"file": ("people.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_datasets_returns_uploaded(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("a.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("b.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )

    response = await auth_client.get("/api/v1/datasets")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    names = {r["original_name"] for r in rows}
    assert names == {"a.csv", "b.csv"}


@pytest.mark.asyncio
async def test_dataset_detail_returns_columns(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("people.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    detail = await auth_client.get(f"/api/v1/datasets/{dataset_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == dataset_id
    assert len(body["columns"]) == 3
    column_names = {c["name"] for c in body["columns"]}
    assert column_names == {"name", "age", "city"}
    age_col = next(c for c in body["columns"] if c["name"] == "age")
    assert age_col["null_count"] == 1


@pytest.mark.asyncio
async def test_dataset_detail_404_for_other_workspace(
    auth_client: AsyncClient, client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("a.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    # Register a different user via the unauth client
    register = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "password": "supersecret"},
    )
    other_token = register.json()["access_token"]

    response = await client.get(
        f"/api/v1/datasets/{dataset_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404
