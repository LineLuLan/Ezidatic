"""ML endpoints — Sprint 3 (M4) + Sprint 5 P0 quality (Q5-ML-01/02)."""

import logging
from pathlib import Path
from typing import Any
from uuid import UUID

import joblib
import pandas as pd
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
    ImputationStrategy,
    LeaderboardEntry,
    TrainRequest,
    TrainResponse,
)
from app.services.ingestion.base import ParserRegistry
from app.services.ml.auto_train import auto_train
from app.services.storage import get_storage

router = APIRouter()

log = logging.getLogger(__name__)

ONE_HOT_MAX_CARDINALITY = 20
LABEL_ENCODE_MAX_CARDINALITY = 200


def _impute_numeric(
    X: pd.DataFrame,
    cols: list[str],
    strategy: ImputationStrategy,
    log_dict: dict[str, str],
) -> pd.DataFrame:
    """Fill NaN per numeric column. Q5-ML-01.

    Imputation runs on the full X before train/val split. This is a
    minor leakage trade-off acceptable for free-tier workloads; Q5-ML-03
    (CV reporting) will move imputation inside each fold.
    """
    for col in cols:
        series = X[col]
        if series.notna().sum() == 0:
            X[col] = 0
            log_dict[col] = "all_null_zero_filled"
            continue
        if strategy == "median":
            value = float(series.median())
            X[col] = series.fillna(value)
            log_dict[col] = f"median({value:.4g})"
        elif strategy == "mean":
            value = float(series.mean())
            X[col] = series.fillna(value)
            log_dict[col] = f"mean({value:.4g})"
        else:  # "zero"
            X[col] = series.fillna(0)
            log_dict[col] = "zero"
    return X


def _impute_categorical(
    X: pd.DataFrame, cols: list[str], log_dict: dict[str, str]
) -> pd.DataFrame:
    """Fill NaN with mode (most frequent). Q5-ML-01."""
    for col in cols:
        series = X[col]
        modes = series.mode(dropna=True)
        if len(modes) == 0:
            X[col] = "missing"
            log_dict[col] = "mode(missing)"
        else:
            value = modes.iloc[0]
            X[col] = series.fillna(value)
            log_dict[col] = f"mode({value})"
    return X


def _encode_categorical(
    X: pd.DataFrame,
    cols: list[str],
    encoded_log: dict[str, str],
    dropped_high_card: list[str],
) -> pd.DataFrame:
    """Auto-encode by cardinality. Q5-ML-02.

    - cardinality <= ONE_HOT_MAX_CARDINALITY (20) → one-hot.
    - <= LABEL_ENCODE_MAX_CARDINALITY (200) → label encode.
    - > LABEL_ENCODE_MAX_CARDINALITY → drop (logged).
    """
    out = X.drop(columns=cols).copy()
    for col in cols:
        cardinality = X[col].nunique(dropna=False)
        if cardinality <= ONE_HOT_MAX_CARDINALITY:
            dummies = pd.get_dummies(X[col], prefix=col, drop_first=False)
            # Cast bool dummies to int8 so estimators that don't accept bool
            # (LightGBM with strict dtype check) stay happy.
            dummies = dummies.astype("int8")
            out = pd.concat([out, dummies], axis=1)
            encoded_log[col] = f"one_hot({cardinality})"
        elif cardinality <= LABEL_ENCODE_MAX_CARDINALITY:
            out[col] = X[col].astype("category").cat.codes.astype("int32")
            encoded_log[col] = f"label({cardinality})"
        else:
            dropped_high_card.append(col)
            encoded_log[col] = f"dropped_high_card({cardinality})"
    return out


CLASS_IMBALANCE_RATIO_THRESHOLD = 1.5


def _class_balance_summary(y: pd.Series) -> dict[str, Any]:
    """Q5-ML-04: report label frequency + an `imbalanced` boolean.

    Surfaces the hint via `extras["class_balance"]` so the FE can
    suggest a non-accuracy metric on imbalanced datasets.
    """
    counts = y.value_counts()
    if counts.empty:
        return {"counts": {}, "ratio": 1.0, "imbalanced": False}
    raw = {str(k): int(v) for k, v in counts.items()}
    max_c = float(counts.max())
    min_c = float(counts.min()) or 1.0
    ratio = max_c / min_c
    return {
        "counts": raw,
        "ratio": float(ratio),
        "imbalanced": ratio > CLASS_IMBALANCE_RATIO_THRESHOLD,
    }


def _build_xy(
    df: pl.DataFrame,
    target: str,
    imputation: ImputationStrategy = "median",
    task_type: str = "classification",
) -> tuple[Any, Any, dict[str, Any]]:
    """Build (X, y, extras) from the loaded dataframe.

    Sprint 5 P0 + P1 pipeline:
      1. Validate target.
      2. Drop rows with null target.
      3. Split numeric vs categorical (datetime cols dropped + logged).
      4. Impute per-column (Q5-ML-01).
      5. Auto-encode categoricals by cardinality (Q5-ML-02).
      6. For classification: report class balance / imbalance flag
         (Q5-ML-04).
      7. Final shape check; raise no_features if zero columns remain.
    """
    if target not in df.columns:
        raise ValidationError(
            f"Target column '{target}' not found in dataset",
            code="missing_target",
        )

    df = df.drop_nulls(subset=[target])
    pdf = df.to_pandas()
    y = pdf[target]
    X = pdf.drop(columns=[target])

    numeric_cols = list(X.select_dtypes(include="number").columns)
    datetime_cols = list(
        X.select_dtypes(include=["datetime", "datetimetz"]).columns
    )
    categorical_cols = [
        c for c in X.columns if c not in numeric_cols and c not in datetime_cols
    ]

    imputed_log: dict[str, str] = {}
    encoded_log: dict[str, str] = {}
    dropped_high_card: list[str] = []

    if datetime_cols:
        X = X.drop(columns=datetime_cols)

    X = _impute_numeric(X, numeric_cols, imputation, imputed_log)
    X = _impute_categorical(X, categorical_cols, imputed_log)
    X = _encode_categorical(
        X, categorical_cols, encoded_log, dropped_high_card
    )

    extras: dict[str, Any] = {
        "rows_used": len(pdf),
        "feature_count": X.shape[1],
        "imputation_strategy": imputation,
        "imputed_columns": imputed_log,
        "encoded_columns": encoded_log,
        "dropped_high_card": dropped_high_card,
        "dropped_datetime": datetime_cols,
        # Backward-compat key kept so any existing FE consumer can still
        # read it; now narrower since most categoricals get encoded.
        "dropped_non_numeric": dropped_high_card + datetime_cols,
    }
    if task_type == "classification":
        extras["class_balance"] = _class_balance_summary(y)
    if X.shape[1] == 0:
        raise ValidationError(
            "No usable feature columns after imputation + encoding. "
            "Check that the dataset has numeric or low-cardinality "
            "categorical columns.",
            code="no_features",
        )
    return X, y, extras


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

    X, y, extras = _build_xy(
        df,
        payload.target_column,
        payload.imputation,
        task_type=payload.task_type,
    )
    extras["metric"] = payload.metric or (
        "accuracy" if payload.task_type == "classification" else "r2"
    )

    if payload.background:
        # Snapshot data references the BackgroundTask will need.
        background_tasks.add_task(
            _run_and_persist_in_background,
            dataset_id=dataset.id,
            target_column=payload.target_column,
            task_type=payload.task_type,
            metric=payload.metric,
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

    leaderboard = auto_train(X, y, task=payload.task_type, metric=payload.metric)
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
    metric: str | None,
    X: Any,
    y: Any,
    extras: dict[str, Any],
) -> None:
    """Background task. Opens its own DB session because BackgroundTasks
    runs after the request response is sent and the request session is
    already closed."""
    from app.core.database import get_sessionmaker

    try:
        leaderboard_rows = auto_train(X, y, task=task_type, metric=metric)
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
