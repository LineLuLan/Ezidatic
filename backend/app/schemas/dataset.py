"""Dataset schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


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

    id: str
    original_name: str
    file_format: str | None
    file_size: int | None
    status: str
    row_count: int | None
    column_count: int | None
    created_at: datetime
