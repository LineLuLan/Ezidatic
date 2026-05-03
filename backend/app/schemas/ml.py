"""ML schemas."""

from typing import Any

from pydantic import BaseModel


class TrainRequest(BaseModel):
    dataset_id: str
    target_column: str
    task_type: str  # "classification" | "regression"


class LeaderboardEntry(BaseModel):
    name: str
    metrics: dict[str, float]
    train_time_sec: float
    feature_importance: dict[str, float] | None = None


class TrainResponse(BaseModel):
    experiment_id: str
    leaderboard: list[LeaderboardEntry]
    best: LeaderboardEntry | None = None
    extras: dict[str, Any] = {}
