"""plot_chart — emit a ChartSpec by delegating to existing helpers."""

from pathlib import Path
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dataset import Dataset
from app.services.agents.tools.base import BaseTool, ToolRegistry
from app.services.eda.chart_spec import (
    bar_spec,
    heatmap_spec,
    histogram_spec,
    scatter_spec,
)
from app.services.ingestion.base import ParserRegistry


ChartTypeArg = Literal["histogram", "bar", "scatter", "heatmap"]


class PlotChartArgs(BaseModel):
    chart_type: ChartTypeArg = Field(description="One of: histogram, bar, scatter, heatmap")
    x_column: str | None = Field(
        default=None,
        description=(
            "Required for histogram/bar/scatter. Ignored for heatmap "
            "(which uses all numeric columns)."
        ),
    )
    y_column: str | None = Field(
        default=None,
        description="Required only for scatter (numeric Y axis).",
    )


class PlotChartTool(BaseTool):
    name = "plot_chart"
    description = (
        "Render one chart for the dataset. histogram + bar take an x_column; "
        "scatter takes both x_column and y_column; heatmap takes neither and "
        "produces a correlation matrix across all numeric columns."
    )
    args_schema = PlotChartArgs

    async def execute(
        self,
        *,
        chart_type: ChartTypeArg,
        x_column: str | None = None,
        y_column: str | None = None,
        dataset_id: UUID,
        db: AsyncSession,
        **_: Any,
    ) -> dict[str, Any]:
        dataset = await db.get(Dataset, dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")

        path = Path(dataset.preprocessed_storage_path or dataset.storage_path)
        parser = ParserRegistry.get_parser(path)
        df = await parser.parse(path)

        if chart_type == "heatmap":
            spec = heatmap_spec(df)
        else:
            if x_column is None:
                raise ValueError(f"{chart_type} requires x_column")
            if x_column not in df.columns:
                raise ValueError(
                    f"x_column '{x_column}' not in dataset columns: {df.columns}"
                )
            if chart_type == "histogram":
                spec = histogram_spec(df, x_column)
            elif chart_type == "bar":
                spec = bar_spec(df, x_column)
            elif chart_type == "scatter":
                if y_column is None or y_column not in df.columns:
                    raise ValueError(
                        f"scatter requires y_column in dataset columns: {df.columns}"
                    )
                spec = scatter_spec(df, x_column, y_column)
            else:
                raise ValueError(f"Unknown chart_type: {chart_type}")
        return spec.model_dump()


ToolRegistry.register(PlotChartTool())
