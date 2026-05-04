"""Encode categorical columns via one-hot or label encoding."""

from typing import Any

import polars as pl

from app.services.preprocessing.steps.base import BaseStep, StepResult


class EncodeCategorical(BaseStep):
    """Encode non-numeric columns. strategy='one_hot' (default) or 'label'."""

    name = "encode_categorical"

    def apply(self, df: pl.DataFrame) -> StepResult:
        strategy = self.params.get("strategy", "one_hot")
        target_columns = self.params.get("columns")

        candidate_columns = [c for c in df.columns if not df[c].dtype.is_numeric()]
        if target_columns is not None:
            candidate_columns = [c for c in candidate_columns if c in target_columns]

        encoded: list[dict[str, Any]] = []

        for col in candidate_columns:
            before_cols = set(df.columns)
            if strategy == "one_hot":
                df = df.to_dummies(columns=[col])
                new_cols = [c for c in df.columns if c not in before_cols]
                encoded.append({"column": col, "new_columns": new_cols})
            elif strategy == "label":
                codes = df[col].cast(pl.Categorical).to_physical()
                df = df.with_columns(codes.alias(col))
                encoded.append({"column": col, "new_columns": [col]})
            else:
                raise ValueError(f"Unknown encode strategy: {strategy}")

        return StepResult(
            df=df,
            log={"strategy": strategy, "encoded": encoded},
        )
