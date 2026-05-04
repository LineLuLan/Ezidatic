"""Preprocessing endpoints — Sprint 2 (M2)."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_workspace, db_session
from app.core.exceptions import NotFoundError, ValidationError
from app.models.dataset import Dataset, PipelineLog
from app.models.workspace import Workspace
from app.schemas.preprocessing import (
    PipelineLogOut,
    PreprocessingRunRequest,
    PreprocessingRunResponse,
)
from app.services.ingestion.base import ParserRegistry
from app.services.preprocessing.pipeline import Pipeline
from app.services.preprocessing.steps import build_step
from app.services.storage import get_storage

router = APIRouter()


@router.post("/{dataset_id}/run", response_model=PreprocessingRunResponse)
async def run_pipeline(
    dataset_id: UUID,
    body: PreprocessingRunRequest,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> PreprocessingRunResponse:
    if not body.steps:
        raise ValidationError("Pipeline must contain at least one step")

    dataset = await db.get(Dataset, dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise NotFoundError("Dataset not found")

    source_path = Path(dataset.storage_path)
    parser = ParserRegistry.get_parser(source_path)
    df = await parser.parse(source_path)

    step_objs = [build_step(s.step, s.params) for s in body.steps]
    transformed_df, step_logs = Pipeline(step_objs).run(df)

    storage = get_storage()
    target = storage.path_for_preprocessed(dataset.id)
    transformed_df.write_csv(target)
    dataset.preprocessed_storage_path = str(target)

    persisted_logs: list[PipelineLog] = []
    for index, (request_step, log_payload) in enumerate(zip(body.steps, step_logs)):
        log_without_step_name = {k: v for k, v in log_payload.items() if k != "step"}
        row = PipelineLog(
            dataset_id=dataset.id,
            step_name=request_step.step,
            step_order=index + 1,
            params=request_step.params or None,
            applied_changes=log_without_step_name or None,
        )
        db.add(row)
        persisted_logs.append(row)

    await db.commit()
    for row in persisted_logs:
        await db.refresh(row)

    return PreprocessingRunResponse(
        dataset_id=dataset.id,
        transformed_path=str(target),
        row_count=transformed_df.height,
        column_count=transformed_df.width,
        logs=[PipelineLogOut.model_validate(r) for r in persisted_logs],
    )


@router.get("/{dataset_id}/logs", response_model=list[PipelineLogOut])
async def list_logs(
    dataset_id: UUID,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> list[PipelineLogOut]:
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise NotFoundError("Dataset not found")

    stmt = (
        select(PipelineLog)
        .where(PipelineLog.dataset_id == dataset.id)
        .order_by(PipelineLog.created_at.asc(), PipelineLog.step_order.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [PipelineLogOut.model_validate(r) for r in rows]
