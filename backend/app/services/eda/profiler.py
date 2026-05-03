"""Per-column profiling stats."""

from typing import Any

import polars as pl


def profile_column(df: pl.DataFrame, column: str) -> dict[str, Any]:
    series = df[column]
    base: dict[str, Any] = {
        "name": column,
        "dtype": str(series.dtype),
        "null_count": int(series.null_count()),
        "unique_count": int(series.n_unique()),
    }
    if series.dtype.is_numeric():
        non_null = series.drop_nulls()
        if non_null.len() > 0:
            base["stats"] = {
                "min": float(non_null.min()),
                "max": float(non_null.max()),
                "mean": float(non_null.mean()),
                "std": float(non_null.std() or 0.0),
            }
    return base


def profile_dataframe(df: pl.DataFrame) -> dict[str, Any]:
    return {
        "row_count": df.height,
        "column_count": df.width,
        "columns": [profile_column(df, c) for c in df.columns],
    }
