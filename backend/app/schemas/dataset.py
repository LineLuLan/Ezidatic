"""Dataset schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_count: int
    unique_count: int
    sample_values: list[Any] | None = None
    stats: dict[str, Any] | None = None


class DatasetProfile(BaseModel):
    row_count: int
    column_count: int
    columns: list[ColumnProfile]


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    original_name: str
    file_format: str | None
    file_size: int | None
    status: str
    row_count: int | None
    column_count: int | None
    created_at: datetime

    @field_serializer("id")
    def _serialize_id(self, value: UUID) -> str:
        return str(value)


class DatasetDetail(DatasetOut):
    """List endpoint returns DatasetOut; detail adds columns + raw profile."""

    columns: list[ColumnProfile] = []
    profile: dict[str, Any] | None = None
