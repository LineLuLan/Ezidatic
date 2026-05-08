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


# ----------------------------- Sprint 5 P1 EDA -------------------------------
# Q5-EDA-01 (datetime detection + line chart) +
# Q5-EDA-03 (auto-scatter for top-correlated pairs).

DATETIME_CSV = (
    "order_date,amount\n"
    "2024-01-05,120\n"
    "2024-01-06,150\n"
    "2024-01-07,90\n"
    "2024-01-08,200\n"
    "2024-01-09,180\n"
    "2024-01-10,140\n"
    "2024-01-11,160\n"
    "2024-01-12,210\n"
)


# Strong linear correlation between x and y so the corr cell is well above 0.5.
HIGH_CORR_CSV = (
    "x,y,noise\n"
    + "\n".join(
        f"{i},{2 * i + (i % 3)},{(i * 7) % 11}" for i in range(1, 25)
    )
    + "\n"
)


# Heavily right-skewed: cluster of small values + a long tail. Polars skew
# on this fixture is well above 1.0 so the picker auto-emits a boxplot.
SKEWED_CSV = (
    "amount\n"
    + "\n".join(
        str(v) for v in (
            1, 2, 2, 3, 3, 3, 4, 4, 4, 4,
            5, 5, 5, 5, 5, 5, 6, 7, 8, 50, 100, 250,
        )
    )
    + "\n"
)


@pytest.mark.asyncio
async def test_profile_includes_is_datetime_flag(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-EDA-01: profiler flags string-date columns as datetime."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("orders.csv", DATETIME_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.get(f"/api/v1/eda/{dataset_id}/profile")
    assert response.status_code == 200, response.text
    cols = {c["name"]: c for c in response.json()["columns"]}
    assert cols["order_date"]["is_datetime"] is True
    assert cols["amount"]["is_datetime"] is False


@pytest.mark.asyncio
async def test_charts_emit_line_for_datetime_column(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-EDA-01: a datetime column produces a line ChartSpec."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("orders.csv", DATETIME_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.get(f"/api/v1/eda/{dataset_id}/charts")
    assert response.status_code == 200, response.text
    specs = response.json()
    line_specs = [s for s in specs if s["type"] == "line"]
    assert len(line_specs) >= 1
    line = line_specs[0]
    # Line is grounded on the datetime column, x_axis labelled with column.
    assert line["x_axis"]["label"] == "order_date"
    assert line["x_axis"]["type"] == "time"
    assert line["y_axis"]["key"] == "count"
    # All 8 rows fall in Jan 2024 → 8 daily buckets when period=1d.
    data = line["series"][0]["data"]
    assert len(data) == 8
    # The datetime column must NOT also be rendered as a bar chart.
    bar_specs = [s for s in specs if s["type"] == "bar"]
    assert all(b["x_axis"]["label"] != "order_date" for b in bar_specs)


@pytest.mark.asyncio
async def test_charts_emit_scatter_for_top_correlated_pairs(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-EDA-03: high correlation produces at least one auto-scatter."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={
            "file": ("corr.csv", HIGH_CORR_CSV.encode("utf-8"), "text/csv")
        },
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.get(f"/api/v1/eda/{dataset_id}/charts")
    assert response.status_code == 200, response.text
    specs = response.json()
    scatters = [s for s in specs if s["type"] == "scatter"]
    assert len(scatters) >= 1
    # The strong x ↔ y pair should be among the auto-emitted scatters.
    pair_labels = {
        tuple(sorted((s["x_axis"]["label"], s["y_axis"]["label"])))
        for s in scatters
    }
    assert ("x", "y") in pair_labels


@pytest.mark.asyncio
async def test_charts_emit_boxplot_for_skewed_numeric(
    auth_client: AsyncClient, isolated_storage: Path
) -> None:
    """Q5-EDA-02: a heavily right-skewed numeric column emits a boxplot."""
    upload = await auth_client.post(
        "/api/v1/datasets",
        files={"file": ("skew.csv", SKEWED_CSV.encode("utf-8"), "text/csv")},
    )
    dataset_id = upload.json()["id"]

    response = await auth_client.get(f"/api/v1/eda/{dataset_id}/charts")
    assert response.status_code == 200, response.text
    specs = response.json()
    box_specs = [s for s in specs if s["type"] == "boxplot"]
    assert len(box_specs) >= 1
    box = box_specs[0]
    ChartSpec.model_validate(box)

    row = box["series"][0]["data"][0]
    assert row["q1"] <= row["median"] <= row["q3"]
    assert row["whisker_low"] <= row["q1"]
    assert row["whisker_high"] >= row["q3"]
    assert isinstance(row["outliers"], list)
    # The 50/100/250 tail should land outside the upper Tukey fence.
    assert any(v >= 50 for v in row["outliers"])
    assert box["metadata"]["outlier_count_total"] >= 2
    assert box["metadata"]["skew"] is not None
    # Histogram still co-emits — boxplot doesn't replace it.
    assert any(s["type"] == "histogram" for s in specs)


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
