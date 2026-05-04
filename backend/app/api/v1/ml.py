"""ML endpoints — Sprint 3 (M4)."""

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

import joblib
import polars as pl
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_workspace, db_session
from app.core.exceptions import NotFoundError, ValidationError
from app.models.dataset import Dataset
from app.models.ml_experiment import MlExperiment
from app.models.workspace import Workspace
from app.schemas.ml import (
    ExperimentOut,
    LeaderboardEntry,
    TrainRequest,
    TrainResponse,
)
from app.services.ingestion.base import ParserRegistry
from app.services.ml.auto_train import auto_train
from app.services.storage import get_storage

router = APIRouter()

log = logging.getLogger(__name__)


def _build_xy(df: pl.DataFrame, target: str) -> tuple[Any, Any, dict[str, Any]]:
    """Drop rows with null target, drop non-numeric features, fillna(0)."""
    if target not in df.columns:
        raise ValidationError(
            f"Target column '{target}' not found in dataset",
            code="missing_target",
        )

    df = df.drop_nulls(subset=[target])
    pdf = df.to_pandas()
    y = pdf[target]
    X = pdf.drop(columns=[target])

    numeric = X.select_dtypes(include="number")
    dropped = [c for c in X.columns if c not in numeric.columns]
    X_clean = numeric.fillna(0)

    extras = {
        "dropped_non_numeric": dropped,
        "rows_used": len(pdf),
        "feature_count": X_clean.shape[1],
    }
    if X_clean.shape[1] == 0:
        raise ValidationError(
            "No numeric feature columns left after filtering. "
            "Run preprocessing (encode_categorical) first.",
            code="no_features",
        )
    return X_clean, y, extras


def _persist_experiments(
    db: AsyncSession,
    dataset: Dataset,
    payload: TrainRequest,
    leaderboard: list[dict[str, Any]],
    artifact_path: Path | None,
    best_name: str | None,
) -> list[MlExperiment]:
    rows: list[MlExperiment] = []
    for entry in leaderboard:
        row = MlExperiment(
            dataset_id=dataset.id,
            target_column=payload.target_column,
            task_type=payload.task_type,
            model_type=entry["name"],
            metrics={
                **entry["metrics"],
                "train_time_sec": entry["train_time_sec"],
                "feature_importance": entry.get("feature_importance"),
            },
            hyperparams=None,
            artifact_path=(
                str(artifact_path)
                if artifact_path is not None and entry["name"] == best_name
                else None
            ),
        )
        db.add(row)
        rows.append(row)
    return rows


def _save_artifact(
    storage_path: Path | None, dataset_id: UUID, name: str, model: Any
) -> Path | None:
    if model is None or storage_path is None:
        return None
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, storage_path)
    return storage_path


def _strip_models(leaderboard: list[dict[str, Any]]) -> list[LeaderboardEntry]:
    return [
        LeaderboardEntry(
            name=e["name"],
            metrics=e["metrics"],
            train_time_sec=e["train_time_sec"],
            feature_importance=e.get("feature_importance"),
        )
        for e in leaderboard
    ]


@router.post("/train", response_model=TrainResponse)
async def train(
    payload: TrainRequest,
    background_tasks: BackgroundTasks,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> TrainResponse:
    dataset = await db.get(Dataset, payload.dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise NotFoundError("Dataset not found")

    if payload.task_type not in ("classification", "regression"):
        raise ValidationError(
            f"Unsupported task_type: {payload.task_type}",
            code="bad_task_type",
        )

    source_path = Path(
        dataset.preprocessed_storage_path or dataset.storage_path
    )
    parser = ParserRegistry.get_parser(source_path)
    df = await parser.parse(source_path)

    X, y, extras = _build_xy(df, payload.target_column)

    if payload.background:
        # Snapshot data references the BackgroundTask will need.
        background_tasks.add_task(
            _run_and_persist_in_background,
            dataset_id=dataset.id,
            target_column=payload.target_column,
            task_type=payload.task_type,
            X=X,
            y=y,
            extras=extras,
        )
        return TrainResponse(
            dataset_id=dataset.id,
            task_type=payload.task_type,
            target_column=payload.target_column,
            leaderboard=[],
            best=None,
            artifact_path=None,
            extras={**extras, "status": "queued"},
        )

    leaderboard = auto_train(X, y, task=payload.task_type)
    if not leaderboard:
        raise ValidationError(
            "All estimators failed to fit. Check feature dtypes + target.",
            code="all_estimators_failed",
        )

    best = leaderboard[0]
    artifact_path = _save_artifact(
        get_storage().path_for_model(dataset.id, best["name"]),
        dataset.id,
        best["name"],
        best["model"],
    )
    _persist_experiments(db, dataset, payload, leaderboard, artifact_path, best["name"])
    await db.commit()

    return TrainResponse(
        dataset_id=dataset.id,
        task_type=payload.task_type,
        target_column=payload.target_column,
        leaderboard=_strip_models(leaderboard),
        best=_strip_models([best])[0],
        artifact_path=str(artifact_path) if artifact_path else None,
        extras=extras,
    )


@router.get(
    "/leaderboard/{dataset_id}", response_model=list[ExperimentOut]
)
async def leaderboard(
    dataset_id: UUID,
    workspace: Workspace = Depends(current_workspace),
    db: AsyncSession = Depends(db_session),
) -> list[ExperimentOut]:
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise NotFoundError("Dataset not found")

    stmt = (
        select(MlExperiment)
        .where(MlExperiment.dataset_id == dataset.id)
        .order_by(MlExperiment.created_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [ExperimentOut.model_validate(r) for r in rows]


async def _run_and_persist_in_background(
    dataset_id: UUID,
    target_column: str,
    task_type: str,
    X: Any,
    y: Any,
    extras: dict[str, Any],
) -> None:
    """Background task. Opens its own DB session because BackgroundTasks
    runs after the request response is sent and the request session is
    already closed."""
    from app.core.database import get_sessionmaker

    try:
        leaderboard_rows = auto_train(X, y, task=task_type)
        if not leaderboard_rows:
            log.warning("Background train: all estimators failed for %s", dataset_id)
            return

        best = leaderboard_rows[0]
        artifact_path = _save_artifact(
            get_storage().path_for_model(dataset_id, best["name"]),
            dataset_id,
            best["name"],
            best["model"],
        )

        Session = get_sessionmaker()
        async with Session() as session:
            for entry in leaderboard_rows:
                session.add(
                    MlExperiment(
                        dataset_id=dataset_id,
                        target_column=target_column,
                        task_type=task_type,
                        model_type=entry["name"],
                        metrics={
                            **entry["metrics"],
                            "train_time_sec": entry["train_time_sec"],
                            "feature_importance": entry.get("feature_importance"),
                        },
                        hyperparams=None,
                        artifact_path=(
                            str(artifact_path)
                            if artifact_path is not None and entry["name"] == best["name"]
                            else None
                        ),
                    )
                )
            await session.commit()
    except Exception:  # noqa: BLE001
        log.exception("Background training failed for dataset %s", dataset_id)
