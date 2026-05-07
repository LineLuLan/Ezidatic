"""Chart spec generators — return frontend-agnostic JSON."""

import math
from typing import Any

import numpy as np
import polars as pl

from app.schemas.chart import AxisSpec, ChartSpec, SeriesSpec


def _clean(v: Any) -> Any:
    """Replace NaN/Inf with None so Pydantic + JSON serialization don't choke."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


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


def scatter_spec(
    df: pl.DataFrame, x: str, y: str, sample: int = 1000
) -> ChartSpec:
    """2D scatter of two numeric columns. Down-sample if dataset is large."""
    pairs = df.select([x, y]).drop_nulls()
    if pairs.height > sample:
        pairs = pairs.sample(n=sample, seed=42)
    points = [
        {"x": _clean(float(row[0])), "y": _clean(float(row[1]))}
        for row in pairs.iter_rows()
    ]
    return ChartSpec(
        type="scatter",
        title=f"{y} vs {x}",
        x_axis=AxisSpec(key="x", label=x, type="numeric"),
        y_axis=AxisSpec(key="y", label=y, type="numeric"),
        series=[SeriesSpec(name=f"{x} × {y}", data=points)],
        metadata={"sampled": pairs.height < df.height, "points": pairs.height},
    )


def _select_period(series: pl.Series) -> str:
    """Pick day / week / month bucket based on the datetime span.

    Q5-EDA-01 rule: < 90 days → 1d, < 2 years → 1w, else 1mo.
    """
    non_null = series.drop_nulls()
    if non_null.len() < 2:
        return "1d"
    try:
        span = non_null.max() - non_null.min()
        days = span.days if hasattr(span, "days") else int(span.total_seconds() / 86400)
    except Exception:  # noqa: BLE001
        return "1d"
    if days < 90:
        return "1d"
    if days < 730:
        return "1w"
    return "1mo"


def line_spec(
    df: pl.DataFrame, datetime_col: str, period: str | None = None
) -> ChartSpec:
    """Count records over time, bucketed by ``period``. Q5-EDA-01.

    If ``datetime_col`` is a string column it is parsed via
    ``str.to_datetime(strict=False)`` first. ``period`` defaults to a
    span-aware bucket (1d / 1w / 1mo).
    """
    series = df[datetime_col]
    if series.dtype in (pl.Utf8, pl.String):
        parsed = series.str.to_datetime(strict=False)
        df_use = df.with_columns(parsed.alias(datetime_col))
        series = df_use[datetime_col]
    else:
        df_use = df

    chosen = period or _select_period(series)

    grouped = (
        df_use.lazy()
        .filter(pl.col(datetime_col).is_not_null())
        .with_columns(pl.col(datetime_col).dt.truncate(chosen).alias("period"))
        .group_by("period")
        .agg(pl.len().alias("count"))
        .sort("period")
        .collect()
    )

    data: list[dict[str, Any]] = []
    for period_val, count in grouped.iter_rows():
        if hasattr(period_val, "isoformat"):
            label = period_val.isoformat()
        else:
            label = str(period_val)
        data.append({"period": label, "count": int(count)})

    return ChartSpec(
        type="line",
        title=f"Records over time ({datetime_col}, {chosen})",
        x_axis=AxisSpec(key="period", label=datetime_col, type="time"),
        y_axis=AxisSpec(key="count", label="count", type="numeric"),
        series=[SeriesSpec(name=datetime_col, data=data)],
        metadata={"period": chosen, "buckets": len(data)},
    )


def heatmap_spec(
    df: pl.DataFrame, columns: list[str] | None = None
) -> ChartSpec:
    """Pearson correlation matrix across numeric columns.

    Polars lacks a native full-matrix corr; we round-trip through pandas
    (compat layer per RULES §1) for this single computation.
    """
    if columns is None:
        columns = [c for c in df.columns if df[c].dtype.is_numeric()]
    if len(columns) < 2:
        raise ValueError("heatmap requires at least 2 numeric columns")

    pdf = df.select(columns).to_pandas()
    corr = pdf.corr(numeric_only=True)
    cells: list[dict[str, Any]] = []
    for row_col in corr.index:
        for col_col in corr.columns:
            cells.append(
                {
                    "x": col_col,
                    "y": row_col,
                    "value": _clean(float(corr.loc[row_col, col_col])),
                }
            )
    return ChartSpec(
        type="heatmap",
        title="Correlation matrix",
        x_axis=AxisSpec(key="x", label="column", type="category"),
        y_axis=AxisSpec(key="y", label="column", type="category"),
        series=[SeriesSpec(name="correlation", data=cells)],
        metadata={"columns": list(columns)},
    )
