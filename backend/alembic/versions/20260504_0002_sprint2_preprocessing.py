"""sprint 2: preprocessed_storage_path on datasets, params on pipeline_logs

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-04

Cross-DB: ``params`` uses sa.JSON with a Postgres JSONB variant so
``alembic upgrade head`` runs against both Postgres and SQLite.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json() -> sa.types.TypeEngine:
    return sa.JSON().with_variant(
        postgresql.JSONB(astext_type=sa.Text()), "postgresql"
    )


def upgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column("preprocessed_storage_path", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "pipeline_logs",
        sa.Column("params", _json(), nullable=True),
    )


def downgrade() -> None:
    # SQLite cannot drop columns before 3.35; in dev with SQLite we'd
    # nuke the file and re-upgrade. Postgres handles drop_column natively.
    with op.batch_alter_table("pipeline_logs") as batch_op:
        batch_op.drop_column("params")
    with op.batch_alter_table("datasets") as batch_op:
        batch_op.drop_column("preprocessed_storage_path")
