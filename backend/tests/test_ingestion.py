"""Ingestion registry tests — M1-BE-06."""

from app.services.ingestion.base import ParserRegistry


def test_registry_supports_csv_and_excel() -> None:
    extensions = ParserRegistry.supported_extensions()
    for ext in (".csv", ".tsv", ".xlsx", ".xls"):
        assert ext in extensions, f"{ext} should be registered"


def test_excel_parser_dispatched_for_xlsx(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from app.services.ingestion.excel_parser import ExcelParser

    fake = tmp_path / "x.xlsx"
    fake.write_bytes(b"")  # path-only check; content not parsed
    parser = ParserRegistry.get_parser(fake)
    assert isinstance(parser, ExcelParser)
