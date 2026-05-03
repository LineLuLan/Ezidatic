"""Frontend-agnostic chart spec — frontend renders via adapter."""

from typing import Any, Literal

from pydantic import BaseModel, Field

ChartType = Literal["bar", "line", "scatter", "histogram", "heatmap", "pie"]


class AxisSpec(BaseModel):
    key: str
    label: str
    type: Literal["category", "numeric", "time"] = "category"


class SeriesSpec(BaseModel):
    name: str
    data: list[dict[str, Any]]


class ChartSpec(BaseModel):
    """Standardized chart spec — backend produces, frontend renders."""

    type: ChartType
    title: str
    x_axis: AxisSpec
    y_axis: AxisSpec
    series: list[SeriesSpec]
    metadata: dict[str, Any] = Field(default_factory=dict)
