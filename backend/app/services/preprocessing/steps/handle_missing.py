"""Handle missing values — sample BaseStep implementation."""

from typing import Any

import polars as pl

from app.services.preprocessing.steps.base import BaseStep, StepResult


class HandleMissingValues(BaseStep):
    name = "handle_missing"

    def apply(self, df: pl.DataFrame) -> StepResult:
        strategy = self.params.get("strategy", "mean")
        affected: list[dict[str, Any]] = []
        for col in df.columns:
            if df[col].null_count() == 0:
                continue
            if df[col].dtype.is_numeric():
                fill_value = (
                    df[col].mean() if strategy == "mean" else df[col].median()
                )
                df = df.with_columns(pl.col(col).fill_null(fill_value))
                affected.append({"column": col, "fill": float(fill_value)})
            else:
                df = df.with_columns(pl.col(col).fill_null("Unknown"))
                affected.append({"column": col, "fill": "Unknown"})
        return StepResult(df=df, log={"strategy": strategy, "affected": affected})
