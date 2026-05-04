"""ML schemas."""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


TaskType = Literal["classification", "regression"]


class TrainRequest(BaseModel):
    dataset_id: UUID
    target_column: str
    task_type: TaskType
    background: bool = False


class LeaderboardEntry(BaseModel):
    name: str
    metrics: dict[str, float]
    train_time_sec: float
    feature_importance: dict[str, float] | None = None


class TrainResponse(BaseModel):
    dataset_id: UUID
    task_type: TaskType
    target_column: str
    leaderboard: list[LeaderboardEntry]
    best: LeaderboardEntry | None = None
    artifact_path: str | None = None
    extras: dict[str, Any] = Field(default_factory=dict)

    @field_serializer("dataset_id")
    def _serialize_dataset_id(self, value: UUID) -> str:
        return str(value)


class ExperimentOut(BaseModel):
    """One row of the persisted leaderboard (one model per row)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    target_column: str
    task_type: str
    model_type: str
    metrics: dict[str, Any] | None = None
    hyperparams: dict[str, Any] | None = None
    artifact_path: str | None = None
    created_at: datetime

    @field_serializer("id", "dataset_id")
    def _serialize_uuid(self, value: UUID) -> str:
        return str(value)
