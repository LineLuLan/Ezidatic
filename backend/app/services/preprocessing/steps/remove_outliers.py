"""Remove outliers via IQR rule (Tukey fences)."""

from typing import Any

import polars as pl

from app.services.preprocessing.steps.base import BaseStep, StepResult


class RemoveOutliers(BaseStep):
    """Drop rows where any selected numeric column falls outside [q1-k*IQR, q3+k*IQR]."""

    name = "remove_outliers"

    def apply(self, df: pl.DataFrame) -> StepResult:
        iqr_factor = float(self.params.get("iqr_factor", 1.5))
        target_columns = self.params.get("columns")

        candidate_columns = [c for c in df.columns if df[c].dtype.is_numeric()]
        if target_columns is not None:
            candidate_columns = [c for c in candidate_columns if c in target_columns]

        before_rows = df.height
        bounds: list[dict[str, Any]] = []
        mask = pl.lit(True)

        for col in candidate_columns:
            non_null = df[col].drop_nulls()
            if non_null.len() < 4:
                continue
            q1 = float(non_null.quantile(0.25))
            q3 = float(non_null.quantile(0.75))
            iqr = q3 - q1
            if iqr == 0:
                continue
            low = q1 - iqr_factor * iqr
            high = q3 + iqr_factor * iqr
            mask = mask & ((pl.col(col) >= low) & (pl.col(col) <= high))
            bounds.append({"column": col, "low": low, "high": high})

        if bounds:
            df = df.filter(mask)

        return StepResult(
            df=df,
            log={
                "iqr_factor": iqr_factor,
                "removed_rows": before_rows - df.height,
                "bounds": bounds,
            },
        )
