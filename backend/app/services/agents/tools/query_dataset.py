"""Query-dataset tool — sample BaseTool. Sprint 4 will wire to real exec."""

from typing import Any

from pydantic import BaseModel, Field

from app.services.agents.tools.base import BaseTool, ToolRegistry


class QueryDatasetArgs(BaseModel):
    dataset_id: str = Field(description="UUID of the dataset to query")
    polars_expr: str = Field(description="Polars expression string to evaluate")


class QueryDatasetTool(BaseTool):
    name = "query_dataset"
    description = "Run a Polars expression against a dataset and return rows."
    args_schema = QueryDatasetArgs

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        # Sprint 4 / M5: implement safe sandboxed eval
        raise NotImplementedError("Wire up in Sprint 4 / M5_AGENTIC_CHAT")


ToolRegistry.register(QueryDatasetTool())
