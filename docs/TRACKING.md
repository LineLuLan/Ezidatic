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
| `develop` | (Sprint 1 merge) | Integration. Sprint 1 BE + FE merged. |
| `backend` | `3d637ab` | Sprint 2 BE complete (EDA + preprocessing). In review. |
| `frontend` | `c251105` | Sprint 1 FE complete (auth + datasets). |

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
| M3-BE-01 | EDA | BE | GET /eda/{id}/profile | in_review | backend | `6d84b6e` |
| M3-BE-02 | EDA | BE | GET /eda/{id}/charts | in_review | backend | `6d84b6e` |
| M3-BE-03 | EDA | BE | scatter + heatmap helpers | in_review | backend | `6d84b6e` |
| M2-BE-01 | Preprocessing | BE | RemoveOutliers step | in_review | backend | `d72dff5` |
| M2-BE-02 | Preprocessing | BE | EncodeCategorical step | in_review | backend | `d72dff5` |
| M2-BE-03 | Preprocessing | BE | POST /preprocessing run | in_review | backend | `baaadfa` |
| M2-BE-04 | Preprocessing | BE | GET /preprocessing logs | in_review | backend | `baaadfa` |
| M3-FE-01 | EDA | FE | EDA page renders charts | pending | frontend | – |
| M3-FE-02 | EDA | FE | Per-column drilldown | pending | frontend | – |
| M3-FE-03 | EDA | FE | Responsive container | pending | frontend | – |
| M2-FE-01 | Preprocessing | FE | Pipeline builder UI | pending | frontend | – |
| M2-FE-02 | Preprocessing | FE | Run pipeline + audit | pending | frontend | – |
| M2-FE-03 | Preprocessing | FE | Pipeline log viewer | pending | frontend | – |

## Sprint 3 — AutoML (M4)

| ID | Module | Side | Task | Status | Branch | Commit |
|----|--------|------|------|--------|--------|--------|
| M4-BE-01 | AutoML | BE | RandomForestClassifier | pending | backend | – |
| M4-BE-02 | AutoML | BE | LogisticRegression | pending | backend | – |
| M4-BE-03 | AutoML | BE | Regressor variants | pending | backend | – |
| M4-BE-04 | AutoML | BE | POST /ml/train wired | pending | backend | – |
| M4-BE-05 | AutoML | BE | Save model artifact | pending | backend | – |
| M4-BE-06 | AutoML | BE | GET /ml/leaderboard/{id} | pending | backend | – |
| M4-BE-07 | AutoML | BE | Background-task training | pending | backend | – |
| M4-FE-01 | AutoML | FE | Train form | pending | frontend | – |
| M4-FE-02 | AutoML | FE | Leaderboard table | pending | frontend | – |
| M4-FE-03 | AutoML | FE | Drawer with feature importance | pending | frontend | – |
| M4-FE-04 | AutoML | FE | Polling/websocket | pending | frontend | – |

## Sprint 4 — Agentic Chat (M5)

| ID | Module | Side | Task | Status | Branch | Commit |
|----|--------|------|------|--------|--------|--------|
| M5-BE-01 | Chat | BE | Gemini/OpenRouter/Ollama providers | pending | backend | – |
| M5-BE-02 | Chat | BE | Verify fallback under failure | pending | backend | – |
| M5-BE-03 | Chat | BE | Router classification | pending | backend | – |
| M5-BE-04 | Chat | BE | sql_worker + explain_worker | pending | backend | – |
| M5-BE-05 | Chat | BE | query_dataset + plot_chart tools | pending | backend | – |
| M5-BE-06 | Chat | BE | Create session endpoint | pending | backend | – |
| M5-BE-07 | Chat | BE | Stream messages SSE | pending | backend | – |
| M5-BE-08 | Chat | BE | Token usage + provider persisted | pending | backend | – |
| M5-FE-01 | Chat | FE | SSE chat input | pending | frontend | – |
| M5-FE-02 | Chat | FE | MessageList streaming | pending | frontend | – |
| M5-FE-03 | Chat | FE | Provider badge | pending | frontend | – |
| M5-FE-04 | Chat | FE | Tool-call display | pending | frontend | – |
| M5-FE-05 | Chat | FE | Embed ChartRenderer in messages | pending | frontend | – |
| M5-FE-06 | Chat | FE | Session list sidebar | pending | frontend | – |

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
