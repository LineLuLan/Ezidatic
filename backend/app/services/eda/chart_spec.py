"""Chart spec generators — return frontend-agnostic JSON."""

import numpy as np
import polars as pl

from app.schemas.chart import AxisSpec, ChartSpec, SeriesSpec


def histogram_spec(df: pl.DataFrame, column: str, bins: int = 30) -> ChartSpec:
    values = df[column].drop_nulls().to_numpy()
    counts, edges = np.histogram(values, bins=bins)
    return ChartSpec(
        type="histogram",
        title=f"Distribution of {column}",
        x_axis=AxisSpec(key="bin", label=column, type="numeric"),
        y_axis=AxisSpec(key="count", label="Frequency", type="numeric"),
        series=[
            SeriesSpec(
                name=column,
                data=[
                    {"bin": float(edges[i]), "count": int(counts[i])}
                    for i in range(len(counts))
                ],
            )
        ],
    )


def bar_spec(df: pl.DataFrame, column: str, top_k: int = 20) -> ChartSpec:
    counts = (
        df.group_by(column)
        .agg(pl.len().alias("count"))
        .sort("count", descending=True)
        .head(top_k)
    )
    return ChartSpec(
        type="bar",
        title=f"Top {top_k} categories of {column}",
        x_axis=AxisSpec(key=column, label=column, type="category"),
        y_axis=AxisSpec(key="count", label="Count", type="numeric"),
        series=[
            SeriesSpec(
                name=column,
                data=counts.to_dicts(),
            )
        ],
    )
