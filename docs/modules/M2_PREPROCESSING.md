# M2 — Preprocessing Pipeline

**Goal**: Compose preprocessing steps as a Chain of Responsibility, persist
the audit log so every transformation is reversible/explainable.

**Sprint**: 2.

## Files

### Backend

| Path | Responsibility |
|------|----------------|
| `backend/app/services/preprocessing/pipeline.py` | `Pipeline` runner (already drafted) |
| `backend/app/services/preprocessing/steps/base.py` | `BaseStep` + `StepResult` (already drafted) |
| `backend/app/services/preprocessing/steps/handle_missing.py` | Sample step |
| `backend/app/services/preprocessing/steps/remove_outliers.py` (new) | IQR-based outlier removal |
| `backend/app/services/preprocessing/steps/encode_categorical.py` (new) | One-hot + label encoding |
| `backend/app/api/v1/preprocessing.py` (new) | `POST /run`, `GET /logs` |
| `backend/app/models/dataset.py` | `PipelineLog` (already exists) |
| `backend/tests/test_preprocessing.py` (new) | Pipeline with 2+ steps |

### Frontend

| Path | Responsibility |
|------|----------------|
| `frontend/app/(dashboard)/preprocessing/[id]/page.tsx` (new) | Pipeline builder UI |
| `frontend/components/preprocessing/StepEditor.tsx` (new) | Per-step form (RHF) |
| `frontend/components/preprocessing/LogViewer.tsx` (new) | Audit log table |

## DB tables touched

`pipeline_logs`.

## Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/v1/preprocessing/{dataset_id}/run` | `[{step: "handle_missing", params: {...}}, ...]` | `{logs: [...], dataset_id, transformed_path}` |
| GET | `/api/v1/preprocessing/{dataset_id}/logs` | – | `PipelineLog[]` |

## Extension points

```python
# backend/app/services/preprocessing/steps/normalize.py
class Normalize(BaseStep):
    name = "normalize"
    def apply(self, df):
        ...
```

Register the step name in a small dispatch map (or move to a registry like
the others if more than ~10 steps appear).

## Tasks

- [ ] **M2-BE-01** RemoveOutliers step (IQR method)
- [ ] **M2-BE-02** EncodeCategorical step (one-hot + label)
- [ ] **M2-BE-03** POST /preprocessing/{id}/run with audit persistence
- [ ] **M2-BE-04** GET /preprocessing/{id}/logs
- [ ] **M2-FE-01** Pipeline builder UI (drag-orderable)
- [ ] **M2-FE-02** Run pipeline button + result toast
- [ ] **M2-FE-03** Log viewer

## Acceptance criteria

- A pipeline with `handle_missing` + `remove_outliers` + `encode_categorical`
  applied to a fixture dataset produces:
  - zero null cells,
  - row count reduced according to IQR cuts,
  - categorical columns expanded into one-hot.
- `pipeline_logs` rows are written in step order with applied_changes JSONB
  containing affected columns.

## Out of scope

- Reverse / undo (the logs make it possible but the UI doesn't expose it).
- Branching DAGs (linear chain only for Sprint 2).
- Save pipeline as a reusable preset.
