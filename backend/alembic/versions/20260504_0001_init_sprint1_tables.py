"""init: sprint 1 tables (users, workspaces, datasets + columns/logs/experiments, chat)

Revision ID: 0001
Revises:
Create Date: 2026-05-04

Cross-DB notes:
- UUID columns use ``sa.Uuid(as_uuid=True)`` — Postgres compiles to UUID,
  SQLite stores as CHAR(32) hex. Both accept ``uuid.UUID`` round-trip.
- JSON columns use ``sa.JSON().with_variant(postgresql.JSONB(...), "postgresql")``
  so Postgres still gets JSONB while SQLite gets a plain JSON-encoded TEXT.
- ``sa.true()`` and ``sa.func.now()`` server defaults compile correctly on
  both dialects.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid() -> sa.types.TypeEngine:
    return sa.Uuid(as_uuid=True)


def _json() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(
        postgresql.JSONB(astext_type=sa.Text()), "postgresql"
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "workspaces",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("owner_id", _uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_workspaces_owner_id",
        ),
    )
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])

    op.create_table(
        "datasets",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("workspace_id", _uuid(), nullable=False),
        sa.Column("original_name", sa.String(length=512), nullable=False),
        sa.Column("storage_path", sa.String(length=1024), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("file_format", sa.String(length=32), nullable=True),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="pending"
        ),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("profile", _json(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
            name="fk_datasets_workspace_id",
        ),
    )
    op.create_index("ix_datasets_workspace_id", "datasets", ["workspace_id"])

    op.create_table(
        "dataset_columns",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("dataset_id", _uuid(), nullable=False),
        sa.Column("column_name", sa.String(length=255), nullable=False),
        sa.Column("data_type", sa.String(length=64), nullable=False),
        sa.Column(
            "is_nullable", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
        sa.Column("null_count", sa.Integer(), nullable=True),
        sa.Column("unique_count", sa.Integer(), nullable=True),
        sa.Column("sample_values", _json(), nullable=True),
        sa.Column("stats", _json(), nullable=True),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
            name="fk_dataset_columns_dataset_id",
        ),
    )
    op.create_index("ix_dataset_columns_dataset_id", "dataset_columns", ["dataset_id"])

    op.create_table(
        "pipeline_logs",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("dataset_id", _uuid(), nullable=False),
        sa.Column("step_name", sa.String(length=128), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("applied_changes", _json(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
            name="fk_pipeline_logs_dataset_id",
        ),
    )
    op.create_index("ix_pipeline_logs_dataset_id", "pipeline_logs", ["dataset_id"])

    op.create_table(
        "ml_experiments",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("dataset_id", _uuid(), nullable=False),
        sa.Column("target_column", sa.String(length=255), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("model_type", sa.String(length=64), nullable=False),
        sa.Column("metrics", _json(), nullable=True),
        sa.Column("hyperparams", _json(), nullable=True),
        sa.Column("artifact_path", sa.String(length=1024), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="CASCADE",
            name="fk_ml_experiments_dataset_id",
        ),
    )
    op.create_index("ix_ml_experiments_dataset_id", "ml_experiments", ["dataset_id"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("workspace_id", _uuid(), nullable=False),
        sa.Column("dataset_id", _uuid(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            ondelete="CASCADE",
            name="fk_chat_sessions_workspace_id",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            ondelete="SET NULL",
            name="fk_chat_sessions_dataset_id",
        ),
    )
    op.create_index("ix_chat_sessions_workspace_id", "chat_sessions", ["workspace_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", _uuid(), primary_key=True),
        sa.Column("session_id", _uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tool_calls", _json(), nullable=True),
        sa.Column("token_usage", _json(), nullable=True),
        sa.Column("provider_used", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["chat_sessions.id"],
            ondelete="CASCADE",
            name="fk_chat_messages_session_id",
        ),
    )
    op.create_index(
        "idx_chat_messages_session_created",
        "chat_messages",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_chat_messages_session_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index("ix_chat_sessions_workspace_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")
    op.drop_index("ix_ml_experiments_dataset_id", table_name="ml_experiments")
    op.drop_table("ml_experiments")
    op.drop_index("ix_pipeline_logs_dataset_id", table_name="pipeline_logs")
    op.drop_table("pipeline_logs")
    op.drop_index("ix_dataset_columns_dataset_id", table_name="dataset_columns")
    op.drop_table("dataset_columns")
    op.drop_index("ix_datasets_workspace_id", table_name="datasets")
    op.drop_table("datasets")
    op.drop_index("ix_workspaces_owner_id", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
