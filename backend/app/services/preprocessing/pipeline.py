"""Preprocessing pipeline — Chain of Responsibility runner."""

from typing import Any

import polars as pl

from app.services.preprocessing.steps.base import BaseStep


class Pipeline:
    """Run a list of preprocessing steps sequentially with audit log."""

    def __init__(self, steps: list[BaseStep]):
        self.steps = steps

    def run(self, df: pl.DataFrame) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
        logs: list[dict[str, Any]] = []
        current = df
        for step in self.steps:
            result = step.apply(current)
            current = result.df
            logs.append({"step": step.name, **result.log})
        return current, logs
