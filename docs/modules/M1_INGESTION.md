# M1 — Ingestion & Storage

**Goal**: Upload a file → parse via the right registered parser → persist
the dataset row + per-column profile. Adding a new format = one new file.

**Sprint**: 1 (with ExcelParser as a stretch goal to demo the registry).

## Files

### Backend

| Path | Responsibility |
|------|----------------|
| `backend/app/services/ingestion/base.py` | `DataParser` ABC + `ParserRegistry` (don't change shape after Sprint 1) |
| `backend/app/services/ingestion/csv_parser.py` | Sample CSV/TSV parser |
| `backend/app/services/ingestion/excel_parser.py` (new in Sprint 1 stretch) | `.xlsx`, `.xls` via `pl.read_excel` |
| `backend/app/services/ingestion/__init__.py` | Auto-import all parsers (registry side-effect) |
| `backend/app/models/dataset.py` | `Dataset`, `DatasetColumn`, `PipelineLog` |
| `backend/app/schemas/dataset.py` | `DatasetOut`, `ColumnProfile`, `DatasetProfile` |
| `backend/app/api/v1/datasets.py` | `POST` upload, `GET` list, `GET /{id}` detail |
| `backend/tests/test_ingestion.py` (new) | parser registry + upload happy path |

### Frontend

| Path | Responsibility |
|------|----------------|
| `frontend/components/upload/Dropzone.tsx` | File drop → POST multipart |
| `frontend/app/(dashboard)/datasets/page.tsx` | List w/ TanStack Query |
| `frontend/app/(dashboard)/datasets/[id]/page.tsx` (new) | Detail with profile table |
| `frontend/lib/types.ts` | `Dataset`, `DatasetProfile`, `ColumnProfile` (already drafted) |

## DB tables touched

`datasets`, `dataset_columns`. Both in migration `0001_init.py`.

## Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/v1/datasets` | multipart/form-data with `file` | `DatasetOut` |
| GET | `/api/v1/datasets` | – | `DatasetOut[]` (workspace-scoped) |
| GET | `/api/v1/datasets/{id}` | – | `DatasetOut` + `DatasetProfile` |

## Extension points

Adding a new format:

```python
# backend/app/services/ingestion/parquet_parser.py
@ParserRegistry.register
class ParquetParser(DataParser):
    extensions = [".parquet"]
    async def parse(self, file_path):  ...
    def profile(self, df):             ...
```

Then add `from app.services.ingestion import parquet_parser  # noqa: F401`
to the `__init__.py`. No changes to the upload endpoint.

## Tasks

- [ ] **M1-BE-01** Dataset + DatasetColumn migration 0001
- [ ] **M1-BE-02** POST /datasets upload (multipart, save to LOCAL_STORAGE_DIR)
- [ ] **M1-BE-03** Dispatch ParserRegistry, persist columns + profile, status=ready
- [ ] **M1-BE-04** GET /datasets workspace-scoped
- [ ] **M1-BE-05** GET /datasets/{id} detail
- [ ] **M1-BE-06** ExcelParser sample
- [ ] **M1-FE-01** Dropzone wire-up
- [ ] **M1-FE-02** Datasets list with TanStack Query
- [ ] **M1-FE-03** Status badges
- [ ] **M1-FE-04** Dataset detail page

## Acceptance criteria

- Upload a 10k-row CSV → list shows it within ≤2s, detail returns
  `DatasetProfile` with row_count=10000 and a row per column.
- Adding `excel_parser.py` makes `.xlsx` upload work without any other
  code change.
- File over `MAX_FILE_SIZE_MB` returns 413.

## Out of scope

- Cloud storage (Supabase Storage adapter is a Polish item).
- Schema inference for nested JSON.
- Streaming uploads / chunked uploads.
