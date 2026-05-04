"""EDA endpoints — Sprint 2 (M3)."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_workspace, db_session
from app.core.exceptions import NotFoundError
from app.models.dataset import Dataset
from app.models.workspace import Workspace
from app.services.eda.chart_spec import bar_spec, heatmap_spec, histogram_spec
from app.services.eda.profiler import profile_dataframe
from app.services.ingestion.base import ParserRegistry

router = APIRouter()

CATEGORICAL_TOP_K_LIMIT = 50


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
    for col in numeric_cols:
        if df[col].drop_nulls().n_unique() < 2:
            continue
        specs.append(histogram_spec(df, col))

    for col in df.columns:
        if col in numeric_cols:
            continue
        if df[col].n_unique() <= CATEGORICAL_TOP_K_LIMIT:
            specs.append(bar_spec(df, col))

    if len(numeric_cols) >= 2:
        specs.append(heatmap_spec(df, numeric_cols))

    return [spec.model_dump() for spec in specs]
