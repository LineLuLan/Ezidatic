# M3 — EDA & Chart Spec

**Goal**: Backend produces a frontend-agnostic JSON `ChartSpec`; the frontend
renders via an adapter. Switching chart libraries later = swapping one file.

**Sprint**: 2 (some helpers may begin in Sprint 1 stretch).

## Files

### Backend

| Path | Responsibility |
|------|----------------|
| `backend/app/services/eda/profiler.py` | Per-column stats (already drafted) |
| `backend/app/services/eda/chart_spec.py` | `histogram_spec`, `bar_spec` (already drafted), `scatter_spec`, `heatmap_spec` (new) |
| `backend/app/schemas/chart.py` | `ChartSpec`, `AxisSpec`, `SeriesSpec` (already drafted) |
| `backend/app/api/v1/eda.py` | `GET /profile`, `GET /charts` |
| `backend/tests/test_eda.py` (new) | ChartSpec validation + edge cases |

### Frontend

| Path | Responsibility |
|------|----------------|
| `frontend/components/charts/ChartRenderer.tsx` | Adapter switch (already drafted) |
| `frontend/components/charts/adapters/recharts.tsx` | Recharts implementation |
| `frontend/components/charts/adapters/echarts.tsx` (future) | Drop-in alternative |
| `frontend/app/(dashboard)/eda/[id]/page.tsx` | Page that fetches charts and lays them out |
| `frontend/lib/types.ts` | `ChartSpec` mirror |

## DB tables touched

None directly (reads `datasets` and `dataset_columns`).

## Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| GET | `/api/v1/eda/{dataset_id}/profile` | – | `DatasetProfile` |
| GET | `/api/v1/eda/{dataset_id}/charts` | – | `ChartSpec[]` |

## Extension points

Adding a new chart type:

1. Add `ChartType` literal in `backend/app/schemas/chart.py` and
   `frontend/lib/types.ts`.
2. Add a helper in `chart_spec.py`.
3. Add a branch in `frontend/components/charts/adapters/recharts.tsx`.

## Tasks

- [ ] **M3-BE-01** GET /eda/{id}/profile (rich, with stats)
- [ ] **M3-BE-02** GET /eda/{id}/charts (auto-pick numeric vs categorical)
- [ ] **M3-BE-03** scatter + heatmap helpers
- [ ] **M3-FE-01** EDA page renders all returned charts
- [ ] **M3-FE-02** Per-column drilldown
- [ ] **M3-FE-03** Charts stay responsive on resize

## Acceptance criteria

- For a dataset with mixed numeric/categorical columns, `GET /charts`
  returns at least one histogram per numeric column and one bar per
  categorical column with cardinality ≤ 50.
- Each `ChartSpec` validates against the Pydantic schema (no NaN, no
  Infinity).
- Swapping `recharts.tsx` adapter to a stub renderer renders all charts
  without runtime errors elsewhere.

## Out of scope

- User-customizable chart configuration (color, axis ranges) — defaults
  only.
- Charts on derived/preprocessed datasets — Sprint 2 hooks this up after M2.
- Saving charts to favorites.
