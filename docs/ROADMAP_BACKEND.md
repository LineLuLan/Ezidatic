# Backend Roadmap — 4 Sprints

Each sprint targets specific modules. Tasks here mirror IDs in `TRACKING.md`.
Detailed plans per module live in `docs/modules/M{n}_*.md`.

> **Conventions**
> - All BE work happens on the `backend` branch.
> - Commit per vertical slice (Conventional Commits).
> - Each endpoint must ship with at least one pytest happy-path test.
> - Migrations: one Alembic revision per sprint (or per substantial schema change).

---

## Sprint 1 — Foundation (M0 + M1)

**Goal**: Auth + CSV upload + dataset profiling end-to-end.
**Modules**: M0 (Auth), M1 (Ingestion).
**Migration**: `0001_init.py` covering all 8 blueprint tables.

### Deliverables

- [ ] **M0-BE-01**: `User` SQLAlchemy model + `UserPublic` schema.
- [ ] **M0-BE-02**: `Workspace` model. Auto-create personal workspace on register.
- [ ] **M0-BE-03**: `POST /api/v1/auth/register` (email + password → token).
- [ ] **M0-BE-04**: `POST /api/v1/auth/login` (returns access token).
- [ ] **M0-BE-05**: `current_user_id` dep wired across protected routes.
- [ ] **M1-BE-01**: `Dataset`, `DatasetColumn` models + Alembic migration.
- [ ] **M1-BE-02**: `POST /api/v1/datasets` — multipart upload, save to
      `LOCAL_STORAGE_DIR`, persist Dataset row with status=`pending`.
- [ ] **M1-BE-03**: Dispatch CsvParser via ParserRegistry, run `profile()`,
      persist DatasetColumn rows + Dataset.profile JSONB, set status=`ready`.
- [ ] **M1-BE-04**: `GET /api/v1/datasets` (workspace-scoped list).
- [ ] **M1-BE-05**: `GET /api/v1/datasets/{id}` (detail w/ columns).
- [ ] **M1-BE-06**: Add ExcelParser sample (`.xlsx`) to demo registry growth.

### Definition of Done

- `pytest` green, includes happy-path tests for register, login, upload, list, detail.
- `alembic upgrade head` succeeds against a fresh PG container.
- Manual smoke: `curl` register → login → upload sample.csv → list returns 1
  row with `row_count` populated.

---

## Sprint 2 — EDA + Preprocessing (M2 + M3)

**Goal**: Profile-driven charts + chained preprocessing pipeline.
**Modules**: M2 (Preprocessing), M3 (EDA).
**Migration**: `0002_pipeline_logs.py` if needed (already in 0001 ideally).

### Deliverables

- [ ] **M3-BE-01**: `GET /api/v1/eda/{dataset_id}/profile` (rich profile incl.
      stats per column).
- [ ] **M3-BE-02**: `GET /api/v1/eda/{dataset_id}/charts` returns list of
      `ChartSpec` covering numeric histograms + categorical bar charts.
- [ ] **M3-BE-03**: Add scatter + heatmap chart-spec helpers.
- [ ] **M2-BE-01**: `RemoveOutliers` step (IQR-based).
- [ ] **M2-BE-02**: `EncodeCategorical` step (one-hot + label).
- [ ] **M2-BE-03**: `POST /api/v1/preprocessing/{dataset_id}/run` — accept
      ordered list of steps + params, run Pipeline, persist PipelineLog rows,
      write a transformed snapshot path on Dataset (or new derived dataset).
- [ ] **M2-BE-04**: `GET /api/v1/preprocessing/{dataset_id}/logs` for audit.

### Definition of Done

- pytest covers Pipeline with 2+ steps; outlier + encoding produce expected
  shape changes.
- ChartSpec validates against the Pydantic schema; no NaN leakage.

---

## Sprint 3 — AutoML (M4)

**Goal**: One-click train across all registered estimators with ranked
leaderboard.
**Modules**: M4.
**Migration**: covered by 0001 (`ml_experiments` already exists).

### Deliverables

- [ ] **M4-BE-01**: Add `RandomForestClassifier` estimator.
- [ ] **M4-BE-02**: Add `LogisticRegression` estimator.
- [ ] **M4-BE-03**: Add `LightGBMRegressor` + `RandomForestRegressor` (task=`regression`).
- [ ] **M4-BE-04**: Wire `auto_train()` into `POST /api/v1/ml/train` —
      load Dataset, build X/y, run leaderboard, persist `MlExperiment` per row.
- [ ] **M4-BE-05**: Save best model artifact to `LOCAL_STORAGE_DIR/models/`.
- [ ] **M4-BE-06**: `GET /api/v1/ml/leaderboard/{dataset_id}` returns ranked
      experiments with feature importance.
- [ ] **M4-BE-07**: Background-task version of `/train` (FastAPI BackgroundTasks)
      so the request returns immediately with an experiment-group ID.

### Definition of Done

- pytest with a tiny fixture dataset trains all classifiers in < 30s and
  yields a sorted leaderboard.
- Feature importance is non-empty for tree-based models.

---

## Sprint 4 — Agentic Chat (M5)

**Goal**: Streaming chat with router-worker topology, multi-provider fallback,
and 1+ tool wired.
**Modules**: M5.
**Migration**: covered by 0001 (chat tables already exist).

### Deliverables

- [ ] **M5-BE-01**: Implement `GeminiProvider`, `OpenRouterProvider`,
      `OllamaProvider` — register with priority 2/3/4.
- [ ] **M5-BE-02**: Verify `LLMAdapter.invoke` and `.stream` actually fall
      back when the primary provider raises (force-disable Groq in test).
- [ ] **M5-BE-03**: Wire `router.route(question)` to classify into QueryType.
- [ ] **M5-BE-04**: Implement `sql_worker` (Polars expression generation +
      sandboxed exec) and `explain_worker`.
- [ ] **M5-BE-05**: Implement `query_dataset` tool (real exec) +
      `plot_chart` tool (returns ChartSpec).
- [ ] **M5-BE-06**: `POST /api/v1/chat/sessions` create session.
- [ ] **M5-BE-07**: `POST /api/v1/chat/sessions/{id}/messages` stream via SSE,
      persist user + assistant messages, route → worker → tool, return final
      assistant message after stream ends.
- [ ] **M5-BE-08**: Token usage + provider name persisted on
      `ChatMessage` rows.

### Definition of Done

- pytest covers fallback (mock provider failures), router classification on a
  fixed test set, and persistence of streamed assistant message.
- Manual SSE smoke via `curl` with the right headers.

---

## Polish (post-Sprint 4)

- [ ] Add Husky + lint-staged in repo root (cross-cutting; on `develop`).
- [ ] Add GitHub Actions: lint + test on PR to `develop`.
- [ ] Deploy: Render (BE) + Vercel (FE) + Supabase (DB + Storage) + Upstash (Redis).
- [ ] Cron-ping Render to keep the service warm (UptimeRobot).
- [ ] Cache LLM responses in Redis keyed by `hash(prompt + dataset_id)`.
- [ ] Write final report + slides.
