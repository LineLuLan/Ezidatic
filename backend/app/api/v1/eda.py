"""EDA endpoints — Sprint 2 (M3)."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_workspace, db_session
from app.core.exceptions import NotFoundError
from app.models.dataset import Dataset
from app.models.workspace import Workspace
from app.services.eda.chart_spec import (
    bar_spec,
    heatmap_spec,
    histogram_spec,
    line_spec,
    scatter_spec,
)
from app.services.eda.profiler import is_datetime_series, profile_dataframe
from app.services.ingestion.base import ParserRegistry

router = APIRouter()

CATEGORICAL_TOP_K_LIMIT = 50
SCATTER_CORR_THRESHOLD = 0.5  # Q5-EDA-03: only emit scatters above this |corr|.
SCATTER_TOP_PAIRS = 3  # Q5-EDA-03: cap auto-emitted scatters per dataset.


async def _load_dataset_df(dataset: Dataset):
    """Load the dataset's preprocessed CSV if available, else the raw upload."""
    raw_path = (
        dataset.preprocessed_storage_path
        if dataset.preprocessed_storage_path
        else dataset.storage_path
    )
    path = Path(raw_path)
    parser = ParserRegistry.get_parser(path)
    return await parser.parse(path)


@router.get("/{dataset_id}/profile")
async def get_profile(
    dataset_id: UUID,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> dict:
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise NotFoundError("Dataset not found")

    if dataset.profile is not None:
        return dataset.profile

    df = await _load_dataset_df(dataset)
    profile = profile_dataframe(df)
    dataset.profile = profile
    await db.commit()
    return profile


@router.get("/{dataset_id}/charts")
async def list_charts(
    dataset_id: UUID,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> list[dict]:
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise NotFoundError("Dataset not found")

    df = await _load_dataset_df(dataset)
    specs = []

    numeric_cols = [c for c in df.columns if df[c].dtype.is_numeric()]
    datetime_cols = [
        c for c in df.columns
        if c not in numeric_cols and is_datetime_series(df[c])
    ]

    for col in numeric_cols:
        if df[col].drop_nulls().n_unique() < 2:
            continue
        specs.append(histogram_spec(df, col))

    # Q5-EDA-01: line chart of count-over-period for every datetime column.
    for col in datetime_cols:
        try:
            specs.append(line_spec(df, col))
        except Exception:  # noqa: BLE001
            # If parse fails on real data, fall through to bar/skip rather
            # than 500 the whole charts response.
            pass

    for col in df.columns:
        if col in numeric_cols or col in datetime_cols:
            continue
        if df[col].n_unique() <= CATEGORICAL_TOP_K_LIMIT:
            specs.append(bar_spec(df, col))

    if len(numeric_cols) >= 2:
        heat = heatmap_spec(df, numeric_cols)
        specs.append(heat)

        # Q5-EDA-03: auto-scatter for top |corr| pairs above threshold.
        cells = heat.series[0].data
        seen: set[tuple[str, str]] = set()
        ranked: list[tuple[float, str, str]] = []
        for cell in cells:
            x, y, value = cell["x"], cell["y"], cell["value"]
            if x == y or value is None:
                continue
            key = tuple(sorted((x, y)))
            if key in seen:
                continue
            seen.add(key)
            ranked.append((abs(float(value)), key[0], key[1]))
        ranked.sort(key=lambda r: r[0], reverse=True)
        for abs_corr, x, y in ranked[:SCATTER_TOP_PAIRS]:
            if abs_corr < SCATTER_CORR_THRESHOLD:
                break
            specs.append(scatter_spec(df, x, y))

    return [spec.model_dump() for spec in specs]
