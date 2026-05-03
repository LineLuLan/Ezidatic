"""Ingestion subsystem — importing this triggers parser registry population."""

from app.services.ingestion import csv_parser  # noqa: F401  (registers .csv/.tsv)
from app.services.ingestion import excel_parser  # noqa: F401  (registers .xlsx/.xls)
from app.services.ingestion.base import DataParser, ParserRegistry

__all__ = ["DataParser", "ParserRegistry"]
