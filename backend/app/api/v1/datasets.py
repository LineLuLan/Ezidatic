"""Dataset endpoints — Sprint 1 (M1)."""

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_workspace, db_session
from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.dataset import Dataset, DatasetColumn
from app.models.workspace import Workspace
from app.schemas.dataset import ColumnProfile, DatasetDetail, DatasetOut
from app.services.eda.profiler import profile_dataframe
from app.services.ingestion.base import ParserRegistry
from app.services.storage import get_storage

router = APIRouter()


@router.post(
    "",
    response_model=DatasetOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    file: UploadFile,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> DatasetOut:
    """Save the uploaded file, parse via ParserRegistry, persist profile."""
    if not file.filename:
        raise ValidationError("Missing filename")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ParserRegistry.supported_extensions():
        raise ValidationError(
            f"Unsupported file format: {suffix}", code="unsupported_format"
        )

    raw = await file.read()
    size = len(raw)
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if size > max_bytes:
        raise ValidationError(
            f"File exceeds maximum size of {settings.max_file_size_mb} MB",
            code="file_too_large",
        )

    dataset_id = uuid4()
    storage_path = get_storage().write_bytes(dataset_id, suffix, raw)

    dataset = Dataset(
        id=dataset_id,
        workspace_id=workspace.id,
        original_name=file.filename,
        storage_path=str(storage_path),
        file_size=size,
        file_format=suffix.lstrip("."),
        status="pending",
    )
    db.add(dataset)
    await db.flush()

    try:
        parser = ParserRegistry.get_parser(storage_path)
        df = await parser.parse(storage_path)
        profile = profile_dataframe(df)

        dataset.row_count = profile["row_count"]
        dataset.column_count = profile["column_count"]
        dataset.profile = profile
        dataset.status = "ready"

        for column in profile["columns"]:
            db.add(
                DatasetColumn(
                    dataset_id=dataset.id,
                    column_name=column["name"],
                    data_type=column["dtype"],
                    null_count=column["null_count"],
                    unique_count=column["unique_count"],
                    stats=column.get("stats"),
                )
            )
    except Exception:  # noqa: BLE001
        dataset.status = "failed"
        await db.commit()
        await db.refresh(dataset)
        raise

    await db.commit()
    await db.refresh(dataset)
    return DatasetOut.model_validate(dataset)


@router.get("", response_model=list[DatasetOut])
async def list_datasets(
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> list[DatasetOut]:
    stmt = (
        select(Dataset)
        .where(Dataset.workspace_id == workspace.id)
        .order_by(Dataset.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [DatasetOut.model_validate(r) for r in rows]


@router.get("/{dataset_id}", response_model=DatasetDetail)
async def get_dataset(
    dataset_id: UUID,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> DatasetDetail:
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise NotFoundError("Dataset not found")

    cols_stmt = select(DatasetColumn).where(DatasetColumn.dataset_id == dataset.id)
    cols = (await db.execute(cols_stmt)).scalars().all()

    detail = DatasetDetail.model_validate(dataset)
    detail.columns = [
        ColumnProfile(
            name=c.column_name,
            dtype=c.data_type,
            null_count=c.null_count or 0,
            unique_count=c.unique_count or 0,
            sample_values=c.sample_values,
            stats=c.stats,
        )
        for c in cols
    ]
    detail.profile = dataset.profile
    return detail
