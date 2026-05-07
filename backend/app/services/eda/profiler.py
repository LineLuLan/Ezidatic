"""Per-column profiling stats."""

from typing import Any

import polars as pl


_MAX_SAMPLE_VALUE_LEN = 50
_DATETIME_PARSE_THRESHOLD = 0.8  # ≥80% of sampled values must parse to mark as datetime


def is_datetime_series(series: pl.Series, sample_size: int = 50) -> bool:
    """Return True if ``series`` is a datetime column.

    Q5-EDA-01: a column is treated as datetime if its Polars dtype is
    temporal (Date / Datetime / Time) OR if it is a string column where
    at least ``_DATETIME_PARSE_THRESHOLD`` of a 50-sample parses to a
    datetime via ``str.to_datetime`` in non-strict mode.

    Used by both the EDA chart picker (to decide whether to emit a
    line chart) and the profiler (to surface ``is_datetime=True`` on
    the profile so future agent workers can read it).
    """
    if series.dtype.is_temporal():
        return True
    if series.dtype not in (pl.Utf8, pl.String):
        return False
    non_null = series.drop_nulls()
    if non_null.len() == 0:
        return False
    sample = non_null.head(sample_size)
    try:
        parsed = sample.str.to_datetime(strict=False)
    except Exception:  # noqa: BLE001
        return False
    parsed_non_null = parsed.drop_nulls().len()
    return parsed_non_null / sample.len() >= _DATETIME_PARSE_THRESHOLD


def _sample_values(series: pl.Series, k: int = 3) -> list[str]:
    """Return up to ``k`` distinct non-null values rendered as strings.

    Used by the SQL worker (Q5-AGENT-02) to ground the LLM in real values
    before generating a query. Each value is truncated to
    ``_MAX_SAMPLE_VALUE_LEN`` so a long-text column does not blow up the
    prompt context budget.
    """
    try:
        values = series.drop_nulls().unique().head(k).to_list()
    except Exception:  # noqa: BLE001
        return []
    out: list[str] = []
    for v in values:
        s = str(v)
        if len(s) > _MAX_SAMPLE_VALUE_LEN:
            s = s[: _MAX_SAMPLE_VALUE_LEN - 1] + "…"
        out.append(s)
    return out


def profile_column(df: pl.DataFrame, column: str) -> dict[str, Any]:
    series = df[column]
    base: dict[str, Any] = {
        "name": column,
        "dtype": str(series.dtype),
        "null_count": int(series.null_count()),
        "unique_count": int(series.n_unique()),
        "sample_values": _sample_values(series),
        "is_datetime": is_datetime_series(series),
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
