"""query_dataset — run a Polars SQL SELECT against the dataset."""

from pathlib import Path
from typing import Any
from uuid import UUID

import polars as pl
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.services.agents.tools.base import BaseTool, ToolRegistry
from app.services.ingestion.base import ParserRegistry


MAX_PREVIEW_ROWS = 100


class QueryDatasetArgs(BaseModel):
    sql: str = Field(
        description=(
            "Polars SQL SELECT statement. The dataset is exposed as the "
            "table named 'data'. Only SELECT queries are allowed."
        )
    )


class QueryDatasetTool(BaseTool):
    name = "query_dataset"
    description = (
        "Run a SQL SELECT against the current dataset (table name = 'data'). "
        "Returns columns + up to 100 preview rows + the total row count."
    )
    args_schema = QueryDatasetArgs

    async def execute(
        self,
        *,
        sql: str,
        dataset_id: UUID,
        db: AsyncSession,
        **_: Any,
    ) -> dict[str, Any]:
        """Run the SQL.

        Safety: ``pl.SQLContext`` doesn't expose the host filesystem and
        we forbid non-SELECT statements at the prompt + parser level.
        Multi-statement payloads are rejected because Polars doesn't
        execute them as a batch anyway and a sneaky `;DROP` is moot.
        """
        cleaned = sql.strip().rstrip(";").strip()
        upper = cleaned.upper()
        if not upper.startswith(("SELECT", "WITH")):
            raise ValueError(
                "Only SELECT/WITH queries are allowed on the dataset."
            )
        if ";" in cleaned:
            raise ValueError("Multiple statements are not supported.")

        dataset = await db.get(Dataset, dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")

        path = Path(dataset.preprocessed_storage_path or dataset.storage_path)
        parser = ParserRegistry.get_parser(path)
        df = await parser.parse(path)

        ctx = pl.SQLContext({"data": df}, eager=True)
        result_df = ctx.execute(cleaned)
        return {
            "columns": result_df.columns,
            "rows": result_df.head(MAX_PREVIEW_ROWS).to_dicts(),
            "row_count": result_df.height,
            "truncated": result_df.height > MAX_PREVIEW_ROWS,
        }


ToolRegistry.register(QueryDatasetTool())
