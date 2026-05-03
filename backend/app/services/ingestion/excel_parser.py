"""Excel parser — sample showing how a single new file demos registry growth.

Adds .xlsx / .xls support without touching the upload endpoint, the
profiler, or the registry. Polars' `read_excel` is used; fall back to
pandas if the active polars install lacks the engine bindings.
"""

from pathlib import Path
from typing import Any

import polars as pl

from app.services.ingestion.base import DataParser, ParserRegistry


@ParserRegistry.register
class ExcelParser(DataParser):
    extensions = [".xlsx", ".xls"]

    async def parse(self, file_path: Path) -> pl.DataFrame:
        try:
            return pl.read_excel(file_path)
        except Exception:  # noqa: BLE001
            import pandas as pd

            return pl.from_pandas(pd.read_excel(file_path))

    def profile(self, df: pl.DataFrame) -> dict[str, Any]:
        return {
            "row_count": df.height,
            "column_count": df.width,
            "columns": [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "null_count": int(df[col].null_count()),
                    "unique_count": int(df[col].n_unique()),
                }
                for col in df.columns
            ],
        }
