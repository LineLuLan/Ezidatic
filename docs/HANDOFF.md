# Session Handoff Log

Reverse-chronological. Latest entry on top. Append a new entry at the
**end of every session** before stopping.

---

## 2026-05-04 — Session 4: Sprint 1 merged to develop

- **Branch**: `develop` — merged `backend` (Session 2) and `frontend`
  (Session 3) one after the other.
- **Done**: Sprint 1 BE + FE rows in TRACKING flipped to `done`. The
  expected TRACKING + HANDOFF conflicts on the merge were resolved per
  RULES §4 (keep both sets). Active branches table updated to reflect
  `develop` as the integrated tip.
- **Next session start**: User decides when to merge `develop` → `main`
  for Sprint 1 release tag. After that, **Sprint 2** kicks off — M2
  preprocessing + M3 EDA / charts. Tasks pre-populated in TRACKING
  (M3-BE-01..03, M2-BE-01..04, M3-FE-01..03, M2-FE-01..03). Read
  `docs/modules/M2_PREPROCESSING.md` and `docs/modules/M3_EDA_CHARTS.md`.
- **Blockers**: Manual E2E browser smoke still pending — needs BE
  running (skip Docker → install asyncpg + point DATABASE_URL at any
  reachable Postgres, or wait for the SQLite-runtime Polish task).
- **Tests at session end**: `pytest` 17/17 (BE), `pnpm build` clean (FE).

---

## 2026-05-04 — Session 2: Sprint 1 BE complete (auth + ingestion)

- **Branch**: `backend` (4 commits on top of `caadcc3`).
- **Done** (all Sprint 1 BE task IDs flipped to `in_review` in TRACKING):
  - **Migration 0001** — `8c9ea6f`. All 8 blueprint tables (users,
    workspaces, datasets, dataset_columns, pipeline_logs, ml_experiments,
    chat_sessions, chat_messages) with UUID PKs, JSONB metadata, FK
    cascade per blueprint §7.
  - **Auth (M0)** — `ba23131`. POST `/auth/register` (creates User +
    personal Workspace + JWT), POST `/auth/login` (verify password +
    JWT). `current_user_id`, `current_user`, `current_workspace` deps
    on `api/deps.py`. Switched passlib → `bcrypt` direct (passlib 1.7.x
    crashes against bcrypt 4.x). Made the SQLAlchemy engine lazy.
    Models now use portable `sa.Uuid` + `sa.JSON` (Postgres-only types
    are kept in the migration). `AppException` global handler renders
    JSON `{code, message}`.
  - **Ingestion (M1-02..05)** — `4eba7e0`. POST `/datasets`
    (multipart, validates extension via ParserRegistry, enforces
    `MAX_FILE_SIZE_MB`, persists Dataset + DatasetColumn rows + profile
    JSON, sets status `ready`/`failed`). GET list (workspace-scoped),
    GET detail (with columns + raw profile). New `services/storage/`
    backend (LocalStorage; ABC-ready for Supabase later).
  - **Excel parser (M1-06)** — `fb56857`. `.xlsx`/`.xls` registered;
    demonstrates that adding a format = one new file + one import line.
- **Tests**: 17/17 pass — `pytest`. 5 auth + 6 dataset + 4 health/
  registry + 2 ingestion-registry. SQLite in-memory via `aiosqlite` +
  `StaticPool`; storage redirected to `tmp_path` per test.
- **Next session start**: User merges `backend` → `develop` after
  testing. Then start **Sprint 1 FE** on `frontend` (M0-FE-01..04 +
  M1-FE-01..04). Read `docs/modules/M0_AUTH.md` and `M1_INGESTION.md`.
- **Blockers**: Tests run against SQLite, not Postgres. To verify on
  real Postgres: `docker compose up -d postgres`, set
  `DATABASE_URL=postgresql+asyncpg://...` in `backend/.env`, run
  `alembic upgrade head`, then `uvicorn app.main:app`. The migration
  was tested manually for shape only — exercise it once when the user
  starts the dev server first time.
- **Notes**:
  - Replaced `@app.on_event("startup")` with a lifespan context manager.
    The lifespan is tolerant of missing optional deps (groq, lightgbm,
    polars) so the auth path works in minimal environments.
  - Test fixtures: `client` (DB-backed unauth), `auth_client`
    (registers a fresh user + injects bearer header), `isolated_storage`
    (monkeypatches `Settings.local_storage_dir` to `tmp_path`).
  - The skeleton `current_user_id` dep was preserved verbatim — only
    additive deps were added. JWT schema unchanged: `sub` = User UUID.

---

## 2026-05-04 — Session 3: Sprint 1 FE complete (auth + datasets UI)

- **Branch**: `frontend` (3 commits on top of `f22951a`).
- **Done** (all marked `in_review` in TRACKING):
  - **UI primitives** — manually written shadcn-style:
    `components/ui/{input,label,card,alert}.tsx`. Reused the existing
    `Button` + `cn()` helper.
  - **Auth (M0)** — `02d52c2`. New `(auth)/layout.tsx` (centered shell),
    `/login` and `/register` pages with RHF + Zod schemas mirroring
    Pydantic (email + min-8 password). New `lib/hooks/useAuth.ts`
    (useLogin/useRegister/useLogout TanStack mutations). authStore now
    has `hydrated` flag and delegates token persistence to api-client
    helpers `setToken`/`clearToken` which sync localStorage AND a
    non-HttpOnly cookie. New `middleware.ts` reads the cookie at the
    edge to redirect protected/auth routes accordingly.
  - **Ingestion list + upload (M1-FE-01..03)** — `8215932`. New
    `components/datasets/{StatusBadge,DatasetCard}.tsx`. Dropzone
    rewritten to use `useUploadDataset` mutation (drag-drop + click
    browse, accepts `.csv,.tsv,.xlsx,.xls`). `/datasets` page now
    renders a grid of DatasetCards with empty/loading/error states.
    New `lib/hooks/useDatasets.ts`.
  - **Ingestion detail (M1-FE-04)** — `9ec1967`. New
    `app/(dashboard)/datasets/[id]/page.tsx` consuming `useDataset(id)`,
    plus `components/datasets/ColumnTable.tsx` rendering the per-column
    profile (dtype, nulls, unique, min/max/mean/std).
- **Tests / verification**: `pnpm typecheck` clean; `pnpm build`
  produces 9 routes + 25.8 kB middleware. `/datasets` 7.57 kB,
  `/datasets/[id]` 2.74 kB, `/login` + `/register` 2.95 / 3 kB.
  Manual UI smoke against a real BE not yet executed (BE in_review on
  `backend`; user opted out of Docker).
- **Next session start**: User reviews + merges `backend` → `develop`,
  then `frontend` → `develop` (or merges `develop` → `frontend` first
  to pull BE changes for E2E smoke). Then **Sprint 2** kicks off:
  M2 (preprocessing) + M3 (EDA / charts). Read
  `docs/modules/M2_PREPROCESSING.md` and `docs/modules/M3_EDA_CHARTS.md`.
- **Blockers**: Manual E2E (register → upload CSV → list → detail in
  the browser) requires BE running. To skip Docker, follow
  `WALKTHROUGH.md` §4.3 with `DATABASE_URL=postgresql+asyncpg://…`
  pointed at any reachable Postgres OR set up an SQLite dev path
  (currently only used by tests; Polish task to support SQLite at
  runtime via the lazy engine).
- **Notes**:
  - **Auth cookie is intentionally NOT HttpOnly** so client can clear
    it on logout. Logged in `ARCHITECTURE.md` Deviations. Switch to
    HttpOnly in Polish.
  - The `useAuth.ts` hook is the only file that knows about the
    `/api/v1/auth/{login,register}` paths; everything else goes
    through the typed `api()` wrapper in `lib/api-client.ts`.
  - `useDatasets.ts` defines `DatasetDetail` as the shape returned by
    GET `/datasets/{id}` — extends `Dataset` with `columns` and raw
    `profile`. Update both BE schema and this type together when
    fields change (RULES §2 cross-side rule).
  - When the user merges `backend` → `develop`, the BE TRACKING rows
    will conflict with the FE TRACKING rows shipped here. RULES §4
    says "keep both sets" — TRACKING is append-only.

---

## 2026-05-03 — Session 1 (addendum): Sync docs to all branches

- **Branch**: `develop` (rule update) + `backend` + `frontend` (merge sync).
- **Done**:
  - Added "Docs-on-every-branch rule" in `docs/RULES.md` §4.
  - Merged `develop` into `backend`; merged `develop` into `frontend` so
    both side branches now carry `CLAUDE.md` + the full `docs/` tree.
- **Why**: User flagged that side branches were missing docs after the
  initial bootstrap. From now on, any docs change on develop must be
  propagated to backend + frontend in the same session.
- **Next session start**: unchanged — Sprint 1 M0/M1 work.
- **Tests**: no code changed; nothing to run.

Entry template:

```
## YYYY-MM-DD — Session N: <one-line title>

- **Branch**: where work landed.
- **Done**: bullet list of completed task IDs (match TRACKING.md).
- **Next session start**: where to pick up — file paths, task IDs, blockers.
- **Blockers**: anything waiting on a decision or external dependency.
- **Tests**: pytest / pnpm build status at session end.
- **Notes**: anything surprising worth remembering (avoid duplicating code).
```

---

## 2026-05-03 — Session 1: Bootstrap skeleton + docs system

- **Branch**: docs/infra committed on `develop`. BE skeleton on `backend`.
  FE skeleton on `frontend`.
- **Done**:
  - Initialized 4 branches: `main` ← `develop` ← `backend` / `frontend`,
    pushed `develop`, `backend`, `frontend` to origin.
  - **BE skeleton** (`backend` branch, commit `c7eab89`): FastAPI app
    skeleton with locked stack, full registries (Parser, Model, Provider,
    Tool) + 1 sample each (CSV, LightGBM, Groq, query_dataset),
    SQLAlchemy 2.0 models for all 8 blueprint tables, Pydantic v2 schemas,
    Alembic init for async, JWT helpers, structlog, CORS, pytest smoke.
    All API endpoints stubbed with `NotImplementedError` tagged by sprint.
  - **FE skeleton** (`frontend` branch, commit `a1c1d28`): Next.js 14 App
    Router, TS strict, Tailwind, shadcn config, sample Button, page stubs
    for /login + dashboard /datasets|eda|ml|chat, ChartRenderer +
    Recharts adapter, typed fetch wrapper, Zustand stores (auth/chat/
    dataset), TanStack Query provider, shared types mirroring BE schemas.
  - **Root infra + docs** (this commit, on `develop`): docker-compose
    (postgres + redis + chroma), root `.env.example`, root `.gitignore`,
    `CLAUDE.md` index, `docs/RULES.md`, `docs/ROADMAP_BACKEND.md`,
    `docs/ROADMAP_FRONTEND.md`, `docs/TRACKING.md` with all task IDs
    pre-populated, `docs/ARCHITECTURE.md`, this `HANDOFF.md`, and
    `docs/modules/M0..M5` deep-dive plans.
- **Next session start**: Sprint 1, **M0-BE-01..05** (Auth) — implement
  on `backend`. Then **M1-BE-01..06** (Ingestion). Read
  `docs/modules/M0_AUTH.md` and `docs/modules/M1_INGESTION.md` first.
  Frontend Sprint 1 (M0-FE-01..04, M1-FE-01..04) can run in parallel.
- **Blockers**: None. User must run `pip install -r backend/requirements.txt`
  and `pnpm install` in `frontend/` before first dev session (skeleton
  doesn't ship `node_modules` or `.venv`).
- **Tests**: Skeleton not run yet. Smoke tests written in
  `backend/tests/test_health.py` cover `/health` + 3 registry-population
  assertions. Will pass once dependencies install.
- **Notes**:
  - Local `main` is one commit ahead of `origin/main` (the
    blueprint+README docs commit). It will move to origin via the
    standard `develop → main` merge later.
  - Pushing directly to `main` is blocked by safety policy — that matches
    the workflow rule in `RULES.md`. Don't try.
  - Backend `__init__.py` for `services/ingestion`, `services/ml`, and
    `services/agents/providers` does the registry-population imports.
    Don't remove those `# noqa: F401` lines.
  - `frontend/lib/types.ts` mirrors the Pydantic ChartSpec / Dataset /
    ChatMessage exactly. Whenever BE changes one of those schemas, update
    both in the same commit (this is in `RULES.md`).
