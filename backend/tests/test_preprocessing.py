"""Preprocessing endpoint + step registry tests — M2."""

from pathlib import Path

import polars as pl
import pytest
from httpx import AsyncClient

from app.services.preprocessing.steps import STEP_REGISTRY, build_step
from app.services.preprocessing.steps.base import BaseStep, StepResult


# 8 numeric rows + 1 outlier (200) + 1 null + a categorical city column.
MESSY_CSV = (
    "age,salary,city\n"
    "30,50000,Hanoi\n"
    "25,45000,Saigon\n"
    "40,80000,Hanoi\n"
    "35,72000,Saigon\n"
    "28,48000,Danang\n"
    "32,55000,Hanoi\n"
    "29,49000,Saigon\n"
    "31,52000,Hanoi\n"
    ",60000,Danang\n"
    "200,1000000,Hanoi\n"
)


@pytest.mark.asyncio
async def test_run_three_steps_persists_logs_and_file(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("m.csv", MESSY_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        f"/api/v1/preprocessing/{dataset_id}/run",
        json={
            "steps": [
                {"step": "handle_missing", "params": {"strategy": "mean"}},
                {"step": "remove_outliers", "params": {"iqr_factor": 1.5}},
                {"step": "encode_categorical", "params": {"strategy": "one_hot"}},
            ]
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["dataset_id"] == dataset_id
    assert len(body["logs"]) == 3
    assert [log["step_order"] for log in body["logs"]] == [1, 2, 3]
    assert [log["step_name"] for log in body["logs"]] == [
        "handle_missing",
        "remove_outliers",
        "encode_categorical",
    ]
    # Outliers removed at least one row.
    assert body["row_count"] < 10
    # One-hot expanded city → at least 3 city_* columns.
    assert body["column_count"] >= 4

    # Transformed file exists on disk.
    pp_path = Path(body["transformed_path"])
    assert pp_path.exists()
    transformed = pl.read_csv(pp_path)
    assert "age" in transformed.columns
    # No nulls remain in age after handle_missing.
    assert transformed["age"].null_count() == 0
    # No raw `city` column left; one-hot encoded.
    assert "city" not in transformed.columns
    one_hot_cols = [c for c in transformed.columns if c.startswith("city_")]
    assert len(one_hot_cols) >= 3

    # Params persisted on each PipelineLog row.
    assert body["logs"][0]["params"] == {"strategy": "mean"}
    # applied_changes recorded for handle_missing.
    assert body["logs"][0]["applied_changes"]["strategy"] == "mean"


@pytest.mark.asyncio
async def test_get_logs_ordered_across_runs(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("m.csv", MESSY_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    await auth_client.post(
        f"/api/v1/preprocessing/{dataset_id}/run",
        json={"steps": [{"step": "handle_missing", "params": {}}]},
    )
    await auth_client.post(
        f"/api/v1/preprocessing/{dataset_id}/run",
        json={
            "steps": [
                {"step": "handle_missing", "params": {}},
                {"step": "remove_outliers", "params": {}},
            ]
        },
    )

    response = await auth_client.get(f"/api/v1/preprocessing/{dataset_id}/logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 3
    # First run (1 row) then second run (2 rows), insertion-ordered.
    assert [log["step_name"] for log in logs] == [
        "handle_missing",
        "handle_missing",
        "remove_outliers",
    ]
    assert [log["step_order"] for log in logs] == [1, 1, 2]


@pytest.mark.asyncio
async def test_unknown_step_returns_422(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("m.csv", MESSY_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        f"/api/v1/preprocessing/{dataset_id}/run",
        json={"steps": [{"step": "definitely_not_a_step", "params": {}}]},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "unknown_step"


@pytest.mark.asyncio
async def test_empty_steps_returns_422(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("m.csv", MESSY_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.post(
        f"/api/v1/preprocessing/{dataset_id}/run",
        json={"steps": []},
    )
    assert response.status_code == 422


def test_step_registry_extensibility() -> None:
    """Adding a step = subclass BaseStep + register a name. No core edits."""

    class Dummy(BaseStep):
        name = "dummy_test_only"

        def apply(self, df: pl.DataFrame) -> StepResult:  # pragma: no cover
            return StepResult(df=df, log={})

    STEP_REGISTRY[Dummy.name] = Dummy
    try:
        instance = build_step("dummy_test_only", {"any_param": 7})
        assert isinstance(instance, Dummy)
        assert instance.params == {"any_param": 7}
    finally:
        del STEP_REGISTRY[Dummy.name]
