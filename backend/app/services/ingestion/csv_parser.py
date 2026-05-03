"""CSV / TSV parser — sample implementation of DataParser."""

from pathlib import Path
from typing import Any

import polars as pl

from app.services.ingestion.base import DataParser, ParserRegistry


@ParserRegistry.register
class CsvParser(DataParser):
    extensions = [".csv", ".tsv"]

    async def parse(self, file_path: Path) -> pl.DataFrame:
        sep = "\t" if file_path.suffix.lower() == ".tsv" else ","
        return pl.read_csv(file_path, separator=sep, infer_schema_length=10_000)

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
