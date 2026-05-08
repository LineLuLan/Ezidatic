# Ezidatic — Walkthrough (Setup, Run, Test)

The hands-on runbook. Read this once when you first clone the repo,
then keep it open whenever you spin up the dev environment.

> **This file must reflect the current state of the project.** When a
> new dependency, env var, command, or test step lands, update this
> file in the same commit. See `RULES.md` §4 for the rule.

---

## 0. Prerequisites

Install once on the machine:

| Tool | Version | Why |
|------|---------|-----|
| Python | 3.11 or 3.13 | Backend runtime |
| Node.js | ≥ 20 | Frontend runtime |
| pnpm | ≥ 9 | Frontend package manager + monorepo root (Husky lives here) |
| Docker Desktop | latest | Postgres + Redis + Chroma for dev |
| Git | latest | Version control |

Optional but recommended:

- **Windows**: use **Git Bash** for the commands below; PowerShell variants
  noted where they diverge.
- **VS Code** with the Python + ESLint + Prettier extensions.

Quick check:

```bash
python --version    # 3.11+
node --version      # v20+
pnpm --version      # 9+
docker --version
```

---

## 1. Clone and orient

```bash
git clone https://github.com/<your-username>/Ezidatic.git
cd Ezidatic
git fetch --all
git branch -a
```

You should see `main`, `develop`, `backend`, `frontend` plus the matching
`origin/*` refs. Branch model is `main ← develop ← backend / frontend`
— see `RULES.md` §3 for the workflow.

Read these in order:

1. `CLAUDE.md` (root) — index of what to read.
2. `docs/HANDOFF.md` — what the previous session left behind.
3. `docs/TRACKING.md` — what's in flight.

Then install the **monorepo root** dev dependencies (Husky pre-commit
hooks, lint-staged, prettier — see §10 for behavior):

```bash
pnpm install            # at the repo root, NOT inside frontend/
```

The `prepare` script wires `core.hooksPath` to `.husky/_` so every
subsequent `git commit` runs the pre-commit hook. Run this once per
clone.

---

## 2. Backend: first-time setup

```bash
cd backend
python -m venv .venv
```

Activate the venv:

| Shell | Command |
|-------|---------|
| Git Bash (Windows) | `source .venv/Scripts/activate` |
| PowerShell (Windows) | `.\.venv\Scripts\Activate.ps1` |
| macOS / Linux | `source .venv/bin/activate` |

Install runtime + dev dependencies:

```bash
pip install --upgrade pip
pip install -r requirements-dev.txt   # includes -r requirements.txt
```

Copy the env template:

```bash
cp .env.example .env
```

Edit `backend/.env` if you want non-defaults. The committed defaults work
locally:

- `DATABASE_URL=postgresql+asyncpg://ezidatic:ezidatic@localhost:5432/ezidatic`
  — pointed at the `docker compose` Postgres.
- `STORAGE_BACKEND=local`, `LOCAL_STORAGE_DIR=./data/uploads`,
  `MAX_FILE_SIZE_MB=50`.
- LLM provider keys (`GROQ_API_KEY`, …) are blank — fine until Sprint 4.

> **Skip this step if you only want to run pytest.** The test suite uses
> in-memory SQLite (see §5), so `.env` isn't required for tests.

---

## 3. Frontend: first-time setup

```bash
cd ../frontend
pnpm install
cp .env.local.example .env.local
```

`.env.local` only needs `NEXT_PUBLIC_API_URL=http://localhost:8000`.

---

## 4. Run the dev environment

You have two paths: **Quick path (SQLite, no Docker)** for solo dev, or
**Full path (Docker + Postgres + Redis + Chroma)** for the full stack
(needed for chat/vector features in Sprint 4).

### 4.1 Quick path: SQLite (no Docker)

Migrations are cross-DB since the SQLite-portable rewrite. Set the URL
in `backend/.env` or export it ad-hoc:

```bash
cd backend
mkdir -p data
export DATABASE_URL='sqlite+aiosqlite:///./data/dev.db'   # Git Bash
# PowerShell: $env:DATABASE_URL='sqlite+aiosqlite:///./data/dev.db'
alembic upgrade head     # creates dev.db with all 8 tables
uvicorn app.main:app --reload --port 8000
```

Notes:
- UUIDs are stored as CHAR(32) hex on SQLite; JSONB columns become plain
  JSON. Round-trip-equivalent for everything in Sprint 1–3.
- Vector store / Redis are not exercised by Sprint 1–3 endpoints, so
  this path is enough for auth + ingestion + EDA + preprocessing +
  AutoML.
- To reset: `rm backend/data/dev.db && alembic upgrade head`.

### 4.2 Full path: Docker (Postgres + Redis + Chroma)

From the repo root:

```bash
docker compose up -d
```

This starts:

- Postgres 15 on `localhost:5432` (db `ezidatic`, user `ezidatic`, pw `ezidatic`).
- Redis 7 on `localhost:6379`.
- Chroma latest on `localhost:8001`.

Health check:

```bash
docker compose ps
docker compose logs -f postgres   # ctrl+c to stop tailing
```

### 4.3 Apply migrations (Postgres)

```bash
cd backend
alembic upgrade head
```

You should see `0001` then `0002` applied. To reset the DB:

```bash
docker compose down -v   # nukes the postgres volume
docker compose up -d postgres
alembic upgrade head
```

### 4.4 Run the backend

```bash
uvicorn app.main:app --reload --port 8000
```

Open:

- `http://localhost:8000/health` → `{"status":"ok",…}`
- `http://localhost:8000/docs` → interactive OpenAPI for every route.

### 4.5 Run the frontend

In another terminal:

```bash
cd frontend
pnpm dev
```

Open `http://localhost:3000`. The dashboard pages are still stubs at the
moment — Sprint 1 FE wires them up against the backend.

---

## 5. Test the backend

The test suite is **independent of Docker / Postgres**. It uses
`aiosqlite` in-memory plus `StaticPool` so every developer can run it
the moment `pip install -r requirements-dev.txt` finishes.

```bash
cd backend
# venv must be active
pytest
```

Targeted runs:

```bash
pytest tests/test_auth.py -v
pytest tests/test_datasets.py::test_upload_csv_returns_ready_with_profile -v
pytest -k "register or login" -v
```

Coverage:

```bash
pytest --cov=app --cov-report=term-missing
```

### What the suite covers as of Sprint 5 P0 (ML + Agent waves)

| File | Tests | What it verifies |
|------|-------|------------------|
| `tests/test_health.py` | 4 | `/health` + 3 registry-population assertions |
| `tests/test_auth.py` | 5 | Register, dup-email, login, wrong password, unknown email |
| `tests/test_datasets.py` | 6 | Upload, format reject, auth required, list, detail, x-workspace 404 |
| `tests/test_ingestion.py` | 2 | CSV + Excel registered; suffix dispatch |
| `tests/test_eda.py` | 8 | Profile blob, auto-pick charts, NaN-clean heatmap, x-workspace 404, **`is_datetime` profile flag (Q5-EDA-01)**, **line chart for date column**, **auto-scatter top |corr| pair (Q5-EDA-03)**, **boxplot for skewed numeric (Q5-EDA-02)** |
| `tests/test_preprocessing.py` | 5 | 3-step run + audit, log ordering across runs, unknown-step 422, empty-steps 422, registry extensibility |
| `tests/test_ml.py` | 16 | Registry coverage, classification + regression train end-to-end, leaderboard persistence, missing target 422, cross-workspace 404, joblib artifact reload, **mixed-dtype auto-encoding (Q5-ML-02)**, **NaN median-imputation (Q5-ML-01)**, **high-cardinality drop**, **5-fold CV reporting (Q5-ML-03)**, **metric=f1_macro re-ranks leaderboard (Q5-ML-04)**, **imbalanced fixture flags `class_balance`**, **`tune=True` persists best_params (Q5-ML-05)**, **default `tune=False` omits best_params**, **tune ≥ baseline on ≥2/3 estimators (200-row fixture)** |
| `tests/test_chat.py` | 13 | Provider fallback (success + all-fail), router robust JSON parsing + EXPLAIN fallback, query_dataset SQL + non-SELECT reject, session CRUD, SSE round-trip with persisted token_usage + provider_used + tool_calls, cross-workspace 404, **SQL retry on first-attempt failure (Q5-AGENT-03)**, **both-fail surfaces both errors**, **EXPLAIN branch ships grounded profile to LLM (Q5-AGENT-04)** |
| `tests/test_agent_quality.py` | 12 | **Q5-AGENT-01** ROUTER_PROMPT few-shot examples per QueryType + preserves `{question}` placeholder. **Q5-AGENT-02** profile_column emits sample_values, sql_worker `_column_schema` renders nulls/unique/min/max/samples per line, truncates over the 1500-char budget, falls back to `(unknown)` for unprofiled datasets. **Q5-AGENT-04** `build_grounded_context` carries real stats, prioritises keyword-matched columns, handles empty profile, truncates to budget |

Total: **71** as of Sprint 5 (43 end-of-Sprint 4 → 46 → 54 → 57 → 64 → 67 after Q5-ML-03/04 BE → 68 after Q5-EDA-02 BE → 71 after Q5-ML-05 BE).

> Heads-up: a few of the registry tests need optional deps installed
> (`polars`, `lightgbm`). `requirements.txt` pins them, but if you
> install only a subset for a quick auth test, expect those to fail
> until you `pip install` the rest.

---

## 6. Test the frontend

For Sprint 1 the contract is simply "must build and typecheck":

```bash
cd frontend
pnpm typecheck   # tsc --noEmit
pnpm build       # next build
pnpm lint
```

Vitest comes online in Sprint 2 (`docs/ROADMAP_FRONTEND.md`). No frontend
unit tests are required yet.

---

## 7. End-to-end smoke (Sprint 1 BE)

With `docker compose up -d` + `uvicorn` running, exercise the full
auth → upload → list → detail flow.

### 7.1 Register and grab a token (Git Bash / Linux / macOS)

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"supersecret"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

echo "$TOKEN"
```

PowerShell:

```powershell
$body = '{"email":"alice@example.com","password":"supersecret"}'
$resp = Invoke-RestMethod -Method POST -Uri http://localhost:8000/api/v1/auth/register `
    -ContentType 'application/json' -Body $body
$TOKEN = $resp.access_token
$TOKEN
```

### 7.2 Upload a CSV

Create a sample first:

```bash
cat > sample.csv <<'CSV'
name,age,city
Alice,30,Hanoi
Bob,25,Saigon
Carol,,Hanoi
Dave,40,Saigon
CSV
```

Upload:

```bash
curl -s -X POST http://localhost:8000/api/v1/datasets \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample.csv"
```

PowerShell:

```powershell
curl.exe -s -X POST http://localhost:8000/api/v1/datasets `
  -H "Authorization: Bearer $TOKEN" `
  -F "file=@sample.csv"
```

Response should include `"status":"ready"`, `"row_count":4`, `"column_count":3`.

### 7.3 List + detail

```bash
curl -s http://localhost:8000/api/v1/datasets \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

DATASET_ID=...   # paste from list response

curl -s "http://localhost:8000/api/v1/datasets/$DATASET_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

The detail response carries the full per-column profile.

### 7.4 EDA — profile + charts (Sprint 2)

```bash
curl -s "http://localhost:8000/api/v1/eda/$DATASET_ID/profile" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

curl -s "http://localhost:8000/api/v1/eda/$DATASET_ID/charts" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

`/profile` returns the cached `DatasetProfile` JSON. Each column object
now also carries `is_datetime: bool` (Q5-EDA-01) and `sample_values:
list[str]` (Q5-AGENT-02). `/charts` returns a list of `ChartSpec`s —
one histogram per numeric column, one bar per categorical column with
cardinality ≤ 50, plus one heatmap when at least two numeric columns
exist.

**Sprint 5 P1/P2 EDA additions**:

- **Q5-EDA-01**: every column flagged `is_datetime=True` (native
  Polars temporal dtype OR ≥80% of a 50-row string sample parses to
  datetime) gets a `line` ChartSpec of `count(*)` over a span-aware
  period (1d if span < 90 days, 1w if < 2 years, else 1mo).
  Datetime columns are excluded from the bar-chart branch so they
  don't double-render.
- **Q5-EDA-03**: after the heatmap is built, the picker ranks
  unique unordered correlation pairs by `|corr|` and emits up to
  3 auto-scatters for pairs above `0.5`. Pairs with NaN
  correlation (e.g. constant columns) are skipped.
- **Q5-EDA-02**: numeric columns with `|skew| > 1` (Polars
  `Series.skew`) gain a `boxplot` ChartSpec alongside the
  histogram. The single-row series carries Tukey quartiles
  (`q1/median/q3`), whisker fences clamped to actual `min/max`,
  and up to 50 sampled outliers (`metadata.outlier_count_total`
  preserves the full count). Recharts has no native boxplot —
  the FE renders inline SVG (single horizontal box).

### 7.5 Preprocessing — run + logs (Sprint 2)

```bash
curl -s -X POST "http://localhost:8000/api/v1/preprocessing/$DATASET_ID/run" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      {"step":"handle_missing","params":{"strategy":"mean"}},
      {"step":"remove_outliers","params":{"iqr_factor":1.5}},
      {"step":"encode_categorical","params":{"strategy":"one_hot"}}
    ]
  }' | python -m json.tool

curl -s "http://localhost:8000/api/v1/preprocessing/$DATASET_ID/logs" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

`POST /run` writes the transformed file to `<storage>/<id>_pp.csv`,
sets `Dataset.preprocessed_storage_path`, and persists one `PipelineLog`
row per step (with both `params` and `applied_changes`). After a
preprocessing run, `GET /eda/{id}/charts` reads from the preprocessed
file instead of the raw upload.

### 7.6 AutoML — train + leaderboard (Sprint 3)

```bash
# Synchronous: returns the full leaderboard inline
curl -s -X POST "http://localhost:8000/api/v1/ml/train" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dataset_id\": \"$DATASET_ID\",
    \"target_column\": \"species\",
    \"task_type\": \"classification\"
  }" | python -m json.tool

# Background: queues + returns immediately. Poll /leaderboard.
curl -s -X POST "http://localhost:8000/api/v1/ml/train" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"dataset_id\": \"$DATASET_ID\",
    \"target_column\": \"species\",
    \"task_type\": \"classification\",
    \"background\": true
  }" | python -m json.tool

curl -s "http://localhost:8000/api/v1/ml/leaderboard/$DATASET_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

`POST /train` runs every estimator registered for the requested
`task_type` (3 classifiers / 2 regressors as of Sprint 3), sorts by the
primary metric (accuracy / r2), saves the winner via joblib at
`<storage>/models/{id}_{name}.joblib`, and persists one `MlExperiment`
per leaderboard entry (the winner gets `artifact_path`).

**Sprint 5 P0 data prep (Q5-ML-01/02)**: the endpoint now imputes and
encodes automatically — running §7.5 preprocessing first is no longer
required for mixed-dtype CSVs.

- Imputation: NaN in numeric cols → column median (default), NaN in
  categorical cols → column mode. Override per request via
  `"imputation": "mean"` or `"imputation": "zero"` (zero = legacy
  pre-Sprint5 behavior).
- Encoding by cardinality: `≤20` unique → one-hot, `21..200` → label
  encode, `>200` → drop.
- Audit: response `extras.imputed_columns` /
  `extras.encoded_columns` / `extras.dropped_high_card` /
  `extras.dropped_datetime` show what was applied. Read these to
  understand why a feature appeared (or didn't) in
  `best.feature_importance`.

**Sprint 5 P1 metrics (Q5-ML-03/04)**: training now runs k-fold CV
and reports per-fold variance plus optional metric override.

- 5-fold CV (StratifiedKFold for classification, KFold for
  regression). `n_splits` auto-clamps for tiny minority classes
  (`max(2, min(5, min_class_count))`).
- Each leaderboard entry's `metrics` dict now carries `cv_mean`,
  `cv_std`, `<metric>_std` (e.g. `accuracy_std`), `primary_metric`
  (string), and `n_splits`. The FE drawer should render
  "5-fold CV: μ=… ± …".
- **Pick the ranking metric** via `"metric"` in the train body:
  `"accuracy" | "f1_macro" | "roc_auc" | "r2"`. When omitted, defaults
  to accuracy/r2 by task. Falls back to the default if the chosen
  metric isn't computable (e.g. roc_auc on an estimator without
  `predict_proba`).
- **Imbalance hint**: classification responses include
  `extras.class_balance = {counts, ratio, imbalanced}`. `imbalanced`
  flips when `max_class / min_class > 1.5`. Use this on the FE to
  prompt the user toward `f1_macro` / `roc_auc` instead of accuracy.

**Sprint 5 P2 tuning (Q5-ML-05)**: opt-in randomized hyperparameter
search per estimator, gated behind `TrainRequest.tune: bool = false`.

- Set `"tune": true` in the train body to enable. Default `false`
  keeps the fast path unchanged.
- Each estimator class declares a `param_distributions` dict
  (RF: n_estimators / max_depth / min_samples_split / max_features;
  LightGBM: n_estimators / learning_rate / num_leaves /
  min_child_samples; LogReg: C). `auto_train` samples
  `settings.ml_tune_n_iter` (default 5) combinations plus the
  empty-dict safety floor `{}`, scores each on the SAME outer
  splitter the leaderboard reports against, and picks the
  highest-scoring set.
- **Reusing the outer splitter** for inner search means the tuner's
  pick is — by construction — the strongest sampled candidate on
  the leaderboard's reporting folds. Combined with the `{}` safety
  floor, `tune=True` cannot regress below `tune=False`.
- Tuned values land in `entry.metrics.best_params` on the API
  response and on the persisted `MlExperiment.hyperparams` column.
  When the safety floor wins (defaults already optimal), neither
  field is set — i.e. tuning ran but found no improvement.
- Determinism: `settings.ml_tune_random_seed` (default 42) seeds
  the candidate sampler.
- Cost: with the splitter shared, each estimator runs `n_iter + 1`
  outer-CV evaluations during tuning. On the 60-row Iris fixture
  one estimator takes ~2s; on a 200-row fixture ~6s per estimator.
  Flip to `background=true` for real-world data.

### 7.7 Chat — sessions + SSE messages (Sprint 4)

Requires at least one LLM provider key in `.env` (Groq is the
recommended primary; Gemini is fallback #1; OpenRouter + Ollama are
optional).

```bash
# Create a session, optionally bound to a dataset.
SESSION_ID=$(curl -s -X POST "http://localhost:8000/api/v1/chat/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"smoke\",\"dataset_id\":\"$DATASET_ID\"}" \
  | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "$SESSION_ID"

# Stream a message. Use --no-buffer so curl flushes SSE chunks live.
curl --no-buffer -N -X POST \
  "http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"How many rows have salary > 50000?"}'

# Inspect persisted history afterwards.
curl -s "http://localhost:8000/api/v1/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

SSE event protocol (one event per `data: <json>\n\n` line):
- `{"type":"intent","value":"sql|ml|eda|explain|small_talk"}` — emitted
  once after the router classifies.
- `{"type":"delta","text":"..."}` — streamed content tokens.
- `{"type":"tool_calls","data":[{...}]}` — emitted by sql_worker after
  it runs `query_dataset`.
- `{"type":"error","message":"..."}` — every provider failed or an
  unhandled exception fired during dispatch.
- `{"type":"done","content":"...","tool_calls":...,"provider_used":...,
  "token_usage":...,"intent":...}` — final summary; assistant
  ChatMessage persists from this payload.
- `{"type":"saved"}` — assistant row committed.

The user message persists synchronously before streaming starts, so a
disconnect mid-stream still records the question. The chat picks the
first available provider in `Groq → Gemini → OpenRouter → Ollama`
order.

### 7.8 Same flow via Swagger UI

Open `http://localhost:8000/docs`, click **Authorize**, paste the JWT
from §7.1, then exercise the routes from the UI. Easier than curl for
multipart uploads.

---

## 8. Common errors and fixes

| Symptom | Cause | Fix |
|--------|------|-----|
| `ModuleNotFoundError: asyncpg` when running pytest | `app.core.database` was eager — fixed in `feat(auth)` commit (`ba23131`) | Pull latest `backend` |
| `module 'bcrypt' has no attribute '__about__'` | passlib 1.7.x vs bcrypt 4.x+ | Already replaced with `bcrypt` direct in `app.core.security` |
| `Form data requires "python-multipart"` | Missing dep | `pip install python-multipart` (already in `requirements.txt`) |
| `NameError: Fields must not use names with leading underscores` | FastAPI body field starts with `_` | Rename `_file` → `file` in the route handler |
| Postgres connection refused | Docker not up | `docker compose up -d postgres` |
| `alembic: command not found` | venv not active | Activate the venv (see §2) |
| `pnpm: command not found` | pnpm not installed | `npm i -g pnpm` |
| 401 on every dataset call | Missing/expired bearer token | Re-run §7.1 to mint a new token (`ACCESS_TOKEN_EXPIRE_MINUTES` defaults to 1440) |
| Charts in tests fail due to missing polars | Optional deps not installed | `pip install polars lightgbm groq` |
| `ruff: command not found` / `black: command not found` on `git commit` | Backend venv not active in shell | Activate the venv (see §2). The pre-commit hook needs `ruff` + `black` on PATH for any commit that touches `backend/**/*.py`. |
| `husky - command not found` after clone | Root `pnpm install` not run yet | Run `pnpm install` at the repo root (see §1). |

---

## 9. Cheatsheet

```bash
# Repo root (one-off after clone — installs Husky pre-commit hook)
pnpm install                           # at the repo root

# Backend daily
cd backend && source .venv/Scripts/activate
uvicorn app.main:app --reload          # dev server
pytest -q                              # all tests
ruff check .                           # lint
black .                                # format

# Backend DB
alembic upgrade head                   # apply migrations
alembic revision -m "describe change"  # new migration (manual edits expected)
alembic downgrade -1                   # rollback last

# Frontend daily
cd frontend
pnpm dev                               # dev server
pnpm build                             # production build
pnpm typecheck                         # tsc --noEmit
pnpm format                            # prettier --write

# Docker
docker compose up -d                   # start postgres + redis + chroma
docker compose down                    # stop, keep volumes
docker compose down -v                 # stop + drop data

# Git workflow (per RULES.md §3) — pre-commit hook runs prettier (FE) + ruff/black (BE) on staged files
git checkout backend && git pull
# ... implement feature, run pytest ...
git add -A && git commit -m "feat(scope): ..."   # hook auto-formats; commit aborts on fix-needed
git push origin backend
```

---

## 10. Pre-commit hook (Husky + lint-staged)

The repo root owns a Husky 9 setup so every `git commit` validates the
**staged subset** of files before recording a commit. Behavior:

| Staged files match | Action |
|--------------------|--------|
| `frontend/**/*.{ts,tsx,js,jsx,json,md,css}` | `prettier --write` |
| `backend/**/*.py` | `ruff check --fix`, then `black` |
| Anything else (root configs, `docs/**`, `*.toml`, lockfiles, etc.) | Skipped — hook exits 0 |

Notes:

- The hook runs through `pnpm exec lint-staged` (config lives in the
  root `package.json` under the `lint-staged` key).
- Frontend formatting uses the binaries from the **root** `node_modules`
  (prettier 3.4.2 + prettier-plugin-tailwindcss 0.6.9 — pinned to match
  `frontend/.prettierrc`). Re-run `pnpm install` at the root if the
  binary is missing.
- Backend formatting requires `ruff` + `black` on PATH. Activate the
  backend venv (§2) before committing `backend/**/*.py` files.
- ESLint is intentionally **NOT** in pre-commit yet — `eslint-config-next`
  14.2.18 has a peer-conflict with eslint v9 (Session 26 HANDOFF). Once
  POL-02 (CI) lands, eslint will gate on push instead.
- The hook **does NOT** auto-stage the formatter's edits — lint-staged
  re-stages modified files for you (the standard lint-staged flow). You
  end up with the formatted version inside the commit.
- Bypassing the hook with `--no-verify` is forbidden (`RULES.md` §3).
  Fix the underlying lint/format failure instead.

---

## 11. When to update this file

Update `docs/WALKTHROUGH.md` whenever any of the following change:

- A new runtime / dev dependency lands.
- A new env var is required by code.
- A new command is needed to run, build, migrate, or test.
- A new common error becomes worth documenting (so the next dev doesn't
  rediscover it).

Bundle the doc update with the code change (one commit, one slice).
