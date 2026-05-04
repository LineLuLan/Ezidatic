"""sprint 2: preprocessed_storage_path on datasets, params on pipeline_logs

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column("preprocessed_storage_path", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "pipeline_logs",
        sa.Column(
            "params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("pipeline_logs", "params")
    op.drop_column("datasets", "preprocessed_storage_path")
