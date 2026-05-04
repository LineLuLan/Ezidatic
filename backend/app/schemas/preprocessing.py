"""Preprocessing request/response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class StepRequest(BaseModel):
    """One step in a preprocessing pipeline."""

    step: str
    params: dict[str, Any] = Field(default_factory=dict)


class PreprocessingRunRequest(BaseModel):
    steps: list[StepRequest]


class PipelineLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    dataset_id: UUID
    step_name: str
    step_order: int
    params: dict[str, Any] | None = None
    applied_changes: dict[str, Any] | None = None
    created_at: datetime

    @field_serializer("id", "dataset_id")
    def _serialize_uuid(self, value: UUID) -> str:
        return str(value)


class PreprocessingRunResponse(BaseModel):
    dataset_id: UUID
    transformed_path: str
    row_count: int
    column_count: int
    logs: list[PipelineLogOut]

    @field_serializer("dataset_id")
    def _serialize_dataset_id(self, value: UUID) -> str:
        return str(value)
