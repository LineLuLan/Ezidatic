# Master Task Tracker

Source of truth for "what's done / what's next" across both sides. Update
**every** time a feature ships. IDs match the deliverables lists in
`ROADMAP_BACKEND.md` and `ROADMAP_FRONTEND.md`.

**Status legend**:
- `pending` — not started.
- `in_progress` — actively being worked on.
- `in_review` — pushed to side branch, waiting for user merge to `develop`.
- `done` — merged to `develop`.

**Branch**: which branch the work landed on first (`backend`, `frontend`, `develop`).

---

## Active branches

| Branch | Latest commit | Notes |
|--------|---------------|-------|
| `main` | (initial) | Production. Only release merges land here. |
| `develop` | (Sprint 4 merge) | Integration. All sprints (1+2+3+4) BE + FE merged. |
| `backend` | `d732e09` | Sprint 5 P0 ML (Q5-ML-01/02) — in_review. |
| `frontend` | `21449d7` | Sprint 4 FE merged into develop. |

> Update the latest-commit cells with the short SHA after each push.

---

## Sprint 1 — Foundation (M0 + M1)

| ID | Module | Side | Task | Status | Branch | Commit |
|----|--------|------|------|--------|--------|--------|
| M0-BE-01 | Auth | BE | User SQLAlchemy model | done | backend | `ba23131` |
| M0-BE-02 | Auth | BE | Workspace + auto-create | done | backend | `ba23131` |
| M0-BE-03 | Auth | BE | POST /auth/register | done | backend | `ba23131` |
| M0-BE-04 | Auth | BE | POST /auth/login | done | backend | `ba23131` |
| M0-BE-05 | Auth | BE | current_user_id dep + current_user/workspace | done | backend | `ba23131` |
| M1-BE-01 | Ingestion | BE | Dataset + DatasetColumn + migration 0001 | done | backend | `8c9ea6f` |
| M1-BE-02 | Ingestion | BE | POST /datasets upload | done | backend | `4eba7e0` |
| M1-BE-03 | Ingestion | BE | Profile via ParserRegistry, persist columns | done | backend | `4eba7e0` |
| M1-BE-04 | Ingestion | BE | GET /datasets list | done | backend | `4eba7e0` |
| M1-BE-05 | Ingestion | BE | GET /datasets/{id} detail | done | backend | `4eba7e0` |
| M1-BE-06 | Ingestion | BE | ExcelParser sample | done | backend | `fb56857` |
| M0-FE-01 | Auth | FE | Login form (RHF + Zod) | done | frontend | `02d52c2` |
| M0-FE-02 | Auth | FE | Register form | done | frontend | `02d52c2` |
| M0-FE-03 | Auth | FE | useAuthStore + cookie sync + redirect | done | frontend | `02d52c2` |
| M0-FE-04 | Auth | FE | Route guard middleware.ts | done | frontend | `02d52c2` |
| M1-FE-01 | Ingestion | FE | Dropzone wire-up (TanStack mutation) | done | frontend | `8215932` |
| M1-FE-02 | Ingestion | FE | Datasets list w/ TanStack Query | done | frontend | `8215932` |
| M1-FE-03 | Ingestion | FE | StatusBadge + DatasetCard | done | frontend | `8215932` |
| M1-FE-04 | Ingestion | FE | Dataset detail page + ColumnTable | done | frontend | `9ec1967` |

## Sprint 2 — EDA + Preprocessing (M2 + M3)

| ID | Module | Side | Task | Status | Branch | Commit |
|----|--------|------|------|--------|--------|--------|
| M3-BE-01 | EDA | BE | GET /eda/{id}/profile | done | backend | `6d84b6e` |
| M3-BE-02 | EDA | BE | GET /eda/{id}/charts | done | backend | `6d84b6e` |
| M3-BE-03 | EDA | BE | scatter + heatmap helpers | done | backend | `6d84b6e` |
| M2-BE-01 | Preprocessing | BE | RemoveOutliers step | done | backend | `d72dff5` |
| M2-BE-02 | Preprocessing | BE | EncodeCategorical step | done | backend | `d72dff5` |
| M2-BE-03 | Preprocessing | BE | POST /preprocessing run | done | backend | `baaadfa` |
| M2-BE-04 | Preprocessing | BE | GET /preprocessing logs | done | backend | `baaadfa` |
| M3-FE-01 | EDA | FE | EDA page renders charts | done | frontend | `65d4647` |
| M3-FE-02 | EDA | FE | Per-column drilldown | done | frontend | `65d4647` |
| M3-FE-03 | EDA | FE | Responsive container | done | frontend | `65d4647` |
| M2-FE-01 | Preprocessing | FE | Pipeline builder UI | done | frontend | `5c83663` |
| M2-FE-02 | Preprocessing | FE | Run pipeline + audit | done | frontend | `5c83663` |
| M2-FE-03 | Preprocessing | FE | Pipeline log viewer | done | frontend | `5c83663` |

## Sprint 3 — AutoML (M4)

| ID | Module | Side | Task | Status | Branch | Commit |
|----|--------|------|------|--------|--------|--------|
| M4-BE-01 | AutoML | BE | RandomForestClassifier | done | backend | `7e9a742` |
| M4-BE-02 | AutoML | BE | LogisticRegression | done | backend | `7e9a742` |
| M4-BE-03 | AutoML | BE | Regressor variants | done | backend | `7e9a742` |
| M4-BE-04 | AutoML | BE | POST /ml/train wired | done | backend | `7e9a742` |
| M4-BE-05 | AutoML | BE | Save model artifact | done | backend | `7e9a742` |
| M4-BE-06 | AutoML | BE | GET /ml/leaderboard/{id} | done | backend | `7e9a742` |
| M4-BE-07 | AutoML | BE | Background-task training | done | backend | `7e9a742` |
| M4-FE-01 | AutoML | FE | Train form | done | frontend | `5430b67` |
| M4-FE-02 | AutoML | FE | Leaderboard table | done | frontend | `5430b67` |
| M4-FE-03 | AutoML | FE | Drawer with feature importance | done | frontend | `5430b67` |
| M4-FE-04 | AutoML | FE | Polling/websocket | done | frontend | `5430b67` |

## Sprint 4 — Agentic Chat (M5)

| ID | Module | Side | Task | Status | Branch | Commit |
|----|--------|------|------|--------|--------|--------|
| M5-BE-01 | Chat | BE | Gemini/OpenRouter/Ollama providers | done | backend | `d2d1bb1` |
| M5-BE-02 | Chat | BE | Verify fallback under failure | done | backend | `6d53061` |
| M5-BE-03 | Chat | BE | Router classification | done | backend | `3e5718a` |
| M5-BE-04 | Chat | BE | sql_worker + explain_worker | done | backend | `964520a` |
| M5-BE-05 | Chat | BE | query_dataset + plot_chart tools | done | backend | `964520a` |
| M5-BE-06 | Chat | BE | Create session endpoint | done | backend | `7a7cb2f` |
| M5-BE-07 | Chat | BE | Stream messages SSE | done | backend | `7a7cb2f` |
| M5-BE-08 | Chat | BE | Token usage + provider persisted | done | backend | `7a7cb2f` |
| M5-FE-01 | Chat | FE | SSE chat input | done | frontend | `21449d7` |
| M5-FE-02 | Chat | FE | MessageList streaming | done | frontend | `21449d7` |
| M5-FE-03 | Chat | FE | Provider badge | done | frontend | `21449d7` |
| M5-FE-04 | Chat | FE | Tool-call display | done | frontend | `21449d7` |
| M5-FE-05 | Chat | FE | Embed ChartRenderer in messages | done | frontend | `21449d7` |
| M5-FE-06 | Chat | FE | Session list sidebar | done | frontend | `21449d7` |

## Sprint 5 — Quality (Agent + EDA + ML)

> Filed Session 15 as a follow-up to Sprint 4 smoke. Detail per issue
> lives in `docs/modules/M_QUALITY.md`. Priority **P0 = high ROI / low
> risk**, **P1 = schema or capability extension**, **P2 = polish**.

| ID | Module | Side | Task | Priority | Status |
|----|--------|------|------|----------|--------|
| Q5-AGENT-01 | Chat | BE | Router few-shot examples | P0 | pending |
| Q5-AGENT-02 | Chat | BE | SQL worker schema enrichment (sample values + ranges) | P0 | pending |
| Q5-AGENT-03 | Chat | BE | SQL worker self-correction retry on tool failure | P1 | pending |
| Q5-AGENT-04 | Chat | BE | Explain worker grounded with dataset profile | P1 | pending |
| Q5-EDA-01 | EDA | BE | Datetime detection + time-series line chart | P1 | pending |
| Q5-EDA-02 | EDA | BE+FE | Box plot helper + renderer for skewed numerics | P2 | pending |
| Q5-EDA-03 | EDA | BE | Auto-scatter for top-correlated pairs | P2 | pending |
| Q5-ML-01 | AutoML | BE | Median/mode imputation (replace fillna(0)) | P0 | in_review (`d732e09`) |
| Q5-ML-02 | AutoML | BE | Auto-encode categorical features (drop only as last resort) | P0 | in_review (`d732e09`) |
| Q5-ML-03 | AutoML | BE+FE | 5-fold CV reporting (cv_mean, cv_std) | P1 | pending |
| Q5-ML-04 | AutoML | BE+FE | Class-imbalance handling + metric selection (F1/AUC) | P1 | pending |
| Q5-ML-05 | AutoML | BE | Lightweight hyperparameter tuning (randomized search) | P2 | pending |

---

## Polish (post-Sprint 4)

| ID | Side | Task | Status |
|----|------|------|--------|
| POL-01 | repo | Husky + lint-staged | pending |
| POL-02 | repo | GitHub Actions CI | pending |
| POL-03 | infra | Deploy Render + Vercel + Supabase + Upstash | pending |
| POL-04 | infra | UptimeRobot ping for Render | pending |
| POL-05 | BE | Redis cache for LLM responses | pending |
| POL-06 | FE | Dark mode + a11y pass | pending |
| POL-07 | docs | Final report + slides | pending |
| POL-08 | BE | SQLite-portable migrations (no-Docker dev path) | in_review (`658aa99`) |
