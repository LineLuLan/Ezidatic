"""Dataset, DatasetColumn, PipelineLog."""

from typing import Any
from uuid import UUID

from sqlalchemy import JSON, BigInteger, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPkMixin


class Dataset(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "datasets"

    workspace_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_name: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    profile: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class DatasetColumn(UUIDPkMixin, Base):
    __tablename__ = "dataset_columns"

    dataset_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(64), nullable=False)
    is_nullable: Mapped[bool] = mapped_column(default=True, nullable=False)
    null_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unique_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_values: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    stats: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


class PipelineLog(UUIDPkMixin, TimestampMixin, Base):
    __tablename__ = "pipeline_logs"

    dataset_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_name: Mapped[str] = mapped_column(String(128), nullable=False)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    applied_changes: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
