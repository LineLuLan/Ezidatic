# M4 — AutoML Engine

**Goal**: Click "train" → iterate every registered estimator → return a
ranked leaderboard with metrics + feature importance. Adding a new
algorithm = one file.

**Sprint**: 3.

## Files

### Backend

| Path | Responsibility |
|------|----------------|
| `backend/app/services/ml/base_estimator.py` | `BaseEstimator`, `ModelRegistry`, `TrainResult` (drafted) |
| `backend/app/services/ml/auto_train.py` | `auto_train(X, y, task)` runner (drafted) |
| `backend/app/services/ml/estimators/lightgbm_clf.py` | Sample (drafted) |
| `backend/app/services/ml/estimators/random_forest.py` (new) | RF for both tasks |
| `backend/app/services/ml/estimators/logistic_reg.py` (new) | LogReg classification |
| `backend/app/services/ml/estimators/lightgbm_reg.py` (new) | LightGBM regression |
| `backend/app/services/ml/__init__.py` | Auto-import every estimator |
| `backend/app/api/v1/ml.py` | `POST /train`, `GET /leaderboard/{id}` |
| `backend/app/models/ml_experiment.py` | Already exists |
| `backend/tests/test_ml.py` (new) | Train all classifiers on a tiny fixture |

### Frontend

| Path | Responsibility |
|------|----------------|
| `frontend/app/(dashboard)/ml/[id]/page.tsx` | Train form + leaderboard |
| `frontend/components/ml/TrainForm.tsx` (new) | RHF form for target + task |
| `frontend/components/ml/Leaderboard.tsx` (new) | Sorted table |
| `frontend/components/ml/ExperimentDrawer.tsx` (new) | Detail drawer w/ feature importance chart |

## DB tables touched

`ml_experiments`.

## Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/v1/ml/train` | `TrainRequest` | `TrainResponse` (sync) or `{job_id}` (background) |
| GET | `/api/v1/ml/leaderboard/{dataset_id}` | – | `LeaderboardEntry[]` |

## Extension points

```python
# backend/app/services/ml/estimators/xgboost_clf.py
@ModelRegistry.register
class XGBoostClassifier(BaseEstimator):
    name = "xgboost_classifier"
    task = "classification"
    def fit(self, ...): ...
```

Add the import line to `app/services/ml/estimators/__init__.py` (or to the
parent `app/services/ml/__init__.py`). The auto-trainer iterates the
registry; no other change needed.

## Tasks

- [ ] **M4-BE-01** RandomForestClassifier
- [ ] **M4-BE-02** LogisticRegression
- [ ] **M4-BE-03** Regressor variants (LightGBM, RandomForest)
- [ ] **M4-BE-04** POST /ml/train wired (load dataset, build X/y, leaderboard)
- [ ] **M4-BE-05** Save best model artifact (joblib) under `LOCAL_STORAGE_DIR/models/`
- [ ] **M4-BE-06** GET /ml/leaderboard/{id}
- [ ] **M4-BE-07** Background training (FastAPI BackgroundTasks)
- [ ] **M4-FE-01** TrainForm
- [ ] **M4-FE-02** Leaderboard table
- [ ] **M4-FE-03** ExperimentDrawer with feature importance bar chart
- [ ] **M4-FE-04** Polling for in-progress experiments

## Acceptance criteria

- For a 1k-row toy dataset, all classifiers train < 30s combined and
  produce a leaderboard sorted by accuracy desc.
- Tree-based models return a non-empty `feature_importance` dict.
- Saved artifact reloads via joblib and predicts identical results.

## Out of scope

- Hyperparameter search (FLAML / Optuna). Defaults only for Sprint 3.
- Model versioning / experiment tracking beyond a single row per run.
- Train/test split configuration in the UI (hard-coded 80/20 + seed=42).
