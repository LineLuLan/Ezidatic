"""DataParser interface + ParserRegistry (plug-in)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import polars as pl


class DataParser(ABC):
    """Interface every file format parser must implement."""

    extensions: list[str] = []

    @abstractmethod
    async def parse(self, file_path: Path) -> pl.DataFrame:
        """Read a file and return a Polars DataFrame."""

    @abstractmethod
    def profile(self, df: pl.DataFrame) -> dict[str, Any]:
        """Return metadata: row_count, column_count, columns[]."""


class ParserRegistry:
    """Maps file extensions to parser classes."""

    _registry: dict[str, type[DataParser]] = {}

    @classmethod
    def register(cls, parser_cls: type[DataParser]) -> type[DataParser]:
        for ext in parser_cls.extensions:
            cls._registry[ext.lower()] = parser_cls
        return parser_cls

    @classmethod
    def get_parser(cls, file_path: Path) -> DataParser:
        ext = file_path.suffix.lower()
        if ext not in cls._registry:
            raise ValueError(f"Unsupported file format: {ext}")
        return cls._registry[ext]()

    @classmethod
    def supported_extensions(cls) -> list[str]:
        return sorted(cls._registry.keys())
