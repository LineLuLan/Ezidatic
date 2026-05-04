# Session Handoff Log

Reverse-chronological. Latest entry on top. Append a new entry at the
**end of every session** before stopping.

---

## 2026-05-05 — Session 15: Sprint 5 "Quality" backlog filed

- **Branch**: `develop` (cross-cutting docs only, per CLAUDE.md). No
  code change.
- **Done**:
  - Added Sprint 5 section to `docs/TRACKING.md` between Sprint 4 and
    Polish — 12 rows: 4 Agent (Q5-AGENT-01..04), 3 EDA (Q5-EDA-01..03),
    5 ML (Q5-ML-01..05). Each with P0/P1/P2 priority + status `pending`.
  - Created `docs/modules/M_QUALITY.md` with full detail per issue:
    Root cause (file:line), Proposed fix, Acceptance criterion, Touches.
    Reuse notes (TrainRequest.extras pattern, ChartSpec discriminated
    union, registry pattern from RULES §2). Suggested execution order
    P0 → P1 → P2.
- **Why**: Session 14 confirmed all blueprint features `done`, but
  user feedback flagged agent reliability + EDA/ML accuracy gaps. P0
  items (Q5-AGENT-01, Q5-AGENT-02, Q5-ML-01, Q5-ML-02) are 1-session
  prompt + helper edits with high ROI. P1/P2 items extend
  `TrainRequest`/`ChartSpec` and need cross-side commits per RULES §2.
- **Next session start**: Pick first P0 issue. Recommended order:
  1. **Q5-AGENT-01** on `backend` — router few-shot examples
     (`backend/app/services/agents/router.py:22-30` prompt edit;
     write `tests/test_agent_router.py` fixture eval).
  2. **Q5-AGENT-02** on `backend` — SQL worker schema enrichment
     (`backend/app/services/agents/workers/sql_worker.py:44-47`).
  3. **Q5-ML-01** on `backend` — replace `fillna(0)` with median/mode
     (`backend/app/api/v1/ml.py:49`); extend `TrainRequest.imputation`.
  4. **Q5-ML-02** on `backend` — auto-encode categoricals
     (`backend/app/api/v1/ml.py:47-48`).
  Each one: branch `backend`, implement, `pytest`, push, update
  TRACKING.md (`pending → in_review`), append HANDOFF, user merges.
- **Blockers**: None. P0 wave is self-contained — no new env vars, no
  schema migrations, no FE changes.
- **Tests at session end**: docs only; pre-existing `pytest 43/43` and
  FE typecheck/build state unchanged.
- **Notes**:
  - **Docs propagation**: per `feedback_docs_on_every_branch.md`, when
    user merges these doc changes off `develop`, both `backend` and
    `frontend` need the new TRACKING + M_QUALITY.md too. Easiest:
    after merging, fast-forward (or merge develop → backend, develop →
    frontend) so side branches carry the backlog before any Q5 work
    starts.
  - **Polish vs Quality**: POL-01..08 are infra/CI/deploy concerns,
    intentionally separate from Q5 (which is *correctness/quality*).
    Both backlogs can be drained in parallel.
  - **Out of scope** (logged in M_QUALITY.md): vector RAG, streaming
    SQL execution, active-learning feedback loop, paid-model swap.

---

## 2026-05-04 — Session 14: Sprint 4 merged to develop (BE + FE) — feature-complete

- **Branch**: `develop` — merged `backend` (Session 12 commits + docs
  `a42c9b4`) and `frontend` (Session 13 — `21449d7` + docs `0225efc`)
  one after the other. Conflicts on TRACKING + HANDOFF resolved per
  RULES §4 ("keep both sets") — backend rows kept from HEAD, frontend
  rows added underneath.
- **Done**: All 14 Sprint 4 task IDs (8 BE + 6 FE) flipped to `done`
  in TRACKING. **Every blueprint feature module is now `done`**:
  M0 Auth, M1 Ingestion, M2 Preprocessing, M3 EDA, M4 AutoML, M5 Chat.
  POL-08 (SQLite-portable migrations) stays as `in_review` in the
  Polish section.
- **State**: working tree clean. `pytest` 43/43 (43 BE tests across 8
  files), `pnpm typecheck` + `pnpm build` clean (verified pre-merge).
  10 frontend routes including `/chat/[sessionId]` (3.41 kB / 220 kB
  FLJS).
- **Next session start**: User performs **E2E browser smoke** per
  WALKTHROUGH §7. Quick path:
    cd backend
    export DATABASE_URL='sqlite+aiosqlite:///./data/dev.db'
    mkdir -p data && alembic upgrade head
    uvicorn app.main:app --reload --port 8000
  Then in another tab:
    cd frontend && pnpm dev
  Open http://localhost:3000, register, upload a CSV, exercise EDA →
  Preprocess → AutoML → Chat in order. WALKTHROUGH §§7.1–7.7 cover
  each step.
- **After E2E**: remaining work is Polish (POL-01..07). Highest impact:
  POL-02 GitHub Actions CI (so future PRs auto-run pytest + pnpm
  build), POL-05 Redis cache for LLM responses (cuts free-tier token
  usage), POL-03 Render+Vercel+Supabase deploy.
- **Blockers**: None for E2E. OpenRouter SSL caveat from Session 12
  is still environment-specific; the fallback chain skips it cleanly
  so chat works via Groq + Gemini.
- **Tests at session end**: 43/43 pytest, FE typecheck/build clean.

---

## 2026-05-04 — Session 12: Sprint 4 BE complete (M5 Agentic Chat)

- **Branch**: `backend` — 5 commits on top of `70d6458` (develop tip
  after Sprint 3 merge):
  - `d2d1bb1` — `feat(chat)` 4-provider chain (Groq/Gemini/OpenRouter/
    Ollama) + LLMResponse dataclass with usage. Updated `.env.example`
    + `config.py` defaults to working models (`gemini-2.5-flash-lite`
    + `gemini-embedding-001` + `z-ai/glm-4.5-air:free`) since
    `gemini-2.0-flash` and `text-embedding-004` are no longer free /
    deprecated, and most Llama-`:free` on OpenRouter are upstream
    rate-limited.
  - `3e5718a` — `feat(chat)` robust router (strips code fences, finds
    first {...} block, falls back to `QueryType.EXPLAIN` on parse
    failure). Live-verified against Groq with 5 sample questions.
  - `964520a` — `feat(chat)` query_dataset tool (Polars SQLContext;
    rejects non-SELECT and multi-statement) + plot_chart tool (wraps
    histogram/bar/scatter/heatmap helpers) + sql_worker_stream (1
    one-shot LLM call to draft SQL → tool execution → streamed
    summary).
  - `7a7cb2f` — `feat(chat)` chat endpoints. POST/GET /chat/sessions,
    GET messages, POST /sessions/{id}/messages (StreamingResponse SSE,
    `text/event-stream`). SSE event protocol = `intent | delta |
    tool_calls | error | done | saved`. Persists user row before
    streaming starts, assistant row after the stream completes; the
    assistant row carries content, tool_calls JSON, token_usage JSON,
    provider_used.
  - `6d53061` — `test(chat)` 10 cases (43/43 suite total). Includes a
    `fake_registry` fixture that swaps in scripted providers per test,
    so the chat round-trip can be exercised deterministically without
    burning real Groq tokens.
- **Done — Sprint 4 BE** (all 8 task IDs `in_review` in TRACKING):
  M5-BE-01..08 — see commit map above.
- **Tests**: `pytest -q` → **43 passed in 20.82s**. Test files now:
  test_health (4), test_auth (5), test_datasets (6), test_ingestion
  (2), test_eda (4), test_preprocessing (5), test_ml (7), **test_chat
  (10)**.
- **Live key check (this session)**:
  - Groq + Gemini + OpenRouter keys all valid against `/models`.
  - **Updated `.env`**:
    `GEMINI_MODEL=gemini-2.0-flash` → `gemini-2.5-flash-lite` (2.0 is
    quota=0 on free tier; 2.5-flash-lite is the fastest non-thinking
    GA model that still fits free tier).
    `GEMINI_EMBED_MODEL=text-embedding-004` → `gemini-embedding-001`
    (text-embedding-004 returns 404 not found).
    `OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free` →
    `z-ai/glm-4.5-air:free` (Llama free tier is upstream-rate-limited
    via Venice; GLM-4.5-Air was the only free model that responded
    cleanly).
  - **Environment SSL caveat**: this dev box can't verify
    openrouter.ai's TLS chain (urllib + httpx + curl all fail with
    `unable to get local issuer certificate`). The fallback chain
    handles it gracefully — Groq is priority=1 so OpenRouter is
    skipped in practice. If the user wants OpenRouter active they need
    `pip install --upgrade certifi` or set `SSL_CERT_FILE` to a
    Mozilla bundle.
- **Next session start**: User merges `backend` → `develop`. Then
  Sprint 4 FE on `frontend`: M5-FE-01..06 (SSE chat input,
  MessageList streaming, provider badge, tool-call display, embed
  ChartRenderer in messages, session list sidebar). Read
  `docs/modules/M5_CHAT_AGENTS.md`.
- **Blockers**: none for FE work. For E2E browser smoke against the
  Sprint 4 chat: SQLite path works (POL-08), Groq + Gemini keys work,
  router + sql_worker + SSE all wired. WALKTHROUGH §7.7 ships a curl
  recipe for the chat flow.
- **Notes**:
  - `LLMProvider.invoke` now returns `LLMResponse(content, provider,
    usage)`. Anyone calling it externally must read `.content`.
    `router.py` and `explain_worker.py` were updated; sql_worker uses
    `.content` directly; the chat endpoint reads `last_provider` and
    `last_usage` off the adapter.
  - Streaming usage: providers populate `self.last_stream_usage` on
    the final SSE chunk; `LLMAdapter.stream` copies it to
    `last_usage` after the iterator drains. SSE generator persists
    those on the assistant ChatMessage row.
  - SSE event types: keep stable for the FE (`intent` first, then any
    number of `delta`, optionally `tool_calls`, then `done`, then
    `saved`). FE state machine should accumulate `delta.text` until
    `done`, then refresh the message list to pick up the persisted
    row (or use `done.tool_calls` for inline rendering before the
    fetch).
  - Polars `pl.SQLContext` table name is hard-coded to `data`. The
    sql_worker prompt tells the LLM about that table only. If we ever
    expose multiple datasets per session, give each a different
    SQLContext key.

---

## 2026-05-04 — Session 13: Sprint 4 FE complete (chat UI)

- **Branch**: `frontend` — 1 commit (`21449d7`) on top of `70d6458`
  (develop tip after Sprint 3 merge). Note: this branch does NOT carry
  Sprint 4 BE — that lives on `backend` (Session 12 commits +
  `a42c9b4` docs). Both sides are `in_review` waiting for user merge.
- **Done** (all 6 Sprint 4 FE task IDs `in_review`):
  - **M5-FE-01..06** chat UI:
    - `lib/types.ts` mirror types — ChatSession, ChatToolCall,
      ChatStreamEvent (discriminated union over the SSE protocol).
    - `lib/sse.ts` — async generator that splits the response stream
      on `\n\n` and yields parsed `data: <json>` lines. Tolerates
      malformed lines so a flaky chunk doesn't kill the whole stream.
    - `lib/hooks/useChat.ts` — useChatSessions / useCreateChatSession
      / useChatMessages (TanStack queries) + useSendChatMessage (a
      bespoke streaming hook because TanStack's useMutation doesn't
      fit SSE). Drives a StreamingState ({active, intent, text,
      toolCalls, providerUsed, tokenUsage, error}); on `saved` event
      it invalidates the messages query.
    - `components/chat/{ChatInput,MessageBubble,MessageList,
      ProviderBadge,SessionSidebar,ToolCallView}.tsx` — provider
      badge color-codes by name (groq=orange, gemini=blue, …);
      ToolCallView special-cases `plot_chart` results, validating
      them as ChartSpec and rendering inline via the existing
      ChartRenderer.
    - `app/(dashboard)/chat/page.tsx` — sessions index. Wrapped in
      <Suspense> because `useSearchParams()` requires it under static
      prerender. Auto-creates a session and redirects when arriving
      with `?dataset_id=...` so the DatasetCard "Chat" CTA flows
      naturally.
    - `app/(dashboard)/chat/[sessionId]/page.tsx` — main chat view:
      sidebar + history + streaming bubble + input.
    - `DatasetCard` adds two new CTAs: AutoML + Chat (the latter
      points at `/chat?dataset_id={id}`). All four feature flows now
      launch from the dataset card.
- **Tests / verification**: `pnpm typecheck` clean. `pnpm build` clean.
  Routes: `/chat` 1.09 kB / 108 kB FLJS, `/chat/[sessionId]` 3.41 kB /
  220 kB FLJS (recharts pulled in for the inline plot_chart
  rendering).
- **Next session start**: User merges `backend` → `develop` (brings in
  Sprint 4 BE chat endpoints + provider chain + workers + tools +
  WALKTHROUGH §7.7), then `frontend` → `develop` (this Session 13
  commit). After both merge, **E2E smoke** per WALKTHROUGH §7.7 — set
  `DATABASE_URL=sqlite+aiosqlite:///./data/dev.db`, `alembic upgrade
  head`, run uvicorn + `pnpm dev`, register, upload a CSV, click
  Chat on the DatasetCard, ask "How many rows have salary > 50000?"
  and confirm streaming + tool_call + provider_used in the
  /chat/[id] page.
- **Blockers**: None on the FE side. BE Session 12 already verified
  Groq + Gemini keys live; OpenRouter has an environment-specific SSL
  caveat that the fallback chain handles transparently.
- **Notes**:
  - The streaming hook keeps an optimistic user message in the cache
    while the SSE stream runs. On `saved` it invalidates and the
    cache picks up both rows from the BE — the optimistic copy is
    naturally replaced.
  - `useSearchParams()` in `chat/page.tsx` MUST stay inside a
    `<Suspense>` boundary or the static prerender step throws. Don't
    flatten unless the page becomes server-component-only.
  - ToolCallView is the single place that decides whether a tool
    result renders inline as a chart vs. a JSON dump. Future tools
    that emit non-ChartSpec rich UIs should add a branch there.
  - The chat UI deliberately has no chart for sql_worker results —
    the BE summary text already cites the SQL + result preview, so
    the FE keeps the bubble compact.

---

## 2026-05-04 — Session 11: Sprint 3 merged to develop (BE + FE) + .env scaffolded

- **Branch**: `develop` — merged `backend` (Session 9 commits, including
  POL-08 SQLite-portable migrations + Sprint 3 BE M4 AutoML) and
  `frontend` (Session 10 — Sprint 3 FE M4 AutoML page) one after the
  other.
- **Done**: All 11 Sprint 3 task IDs flipped to `done` in TRACKING (7
  BE + 4 FE). POL-08 stays as `in_review` in the Polish section but
  effectively merged. Conflicts on TRACKING + HANDOFF resolved per
  RULES §4 ("keep both sets") — backend rows kept from HEAD, frontend
  rows added underneath.
- **State**: working tree clean. `pytest` 33/33, `pnpm typecheck` +
  `pnpm build` clean (verified pre-merge).
- **Next session start**: Sprint 4 (M5 Agentic Chat). User has been
  asked to populate `backend/.env` with at least one LLM provider key
  (Groq is the recommended primary; Gemini also for embedding). The
  fallback chain is Groq → Gemini → OpenRouter → Ollama. Read
  `docs/modules/M5_CHAT_AGENTS.md` first. M5-BE-01..08 + M5-FE-01..06.
- **Blockers**: Sprint 4 BE needs at least one provider key in
  `backend/.env`. Without keys, Sprint 4 BE work can still write the
  provider adapters and tests (mocked HTTP), but live integration
  smoke needs a real key.
- **Tests at session end**: 33/33 pytest, FE typecheck/build clean.

---

## 2026-05-04 — Session 9: SQLite-portable migrations + Sprint 3 BE (M4 AutoML)

- **Branch**: `backend` — 3 commits on top of `4e7c79c` (develop tip
  after Sprint 2 merge):
  - `658aa99` — `fix(db)` migrations 0001 + 0002 portable (sa.Uuid +
    sa.JSON.with_variant(JSONB, "postgresql")). 0002 downgrade now uses
    `op.batch_alter_table` so it works on SQLite < 3.35 too.
  - `f32b1ee` — `docs(walkthrough)` adds §4.1 "Quick path: SQLite (no
    Docker)"; existing Docker/Postgres path renumbered §4.2–§4.5.
  - `7e9a742` — `feat(ml)` Sprint 3 AutoML (M4-BE-01..07).
- **Done — Polish**:
  - **POL-08 (new ID)** — `658aa99`. Verified by running
    `DATABASE_URL=sqlite+aiosqlite:///./data/dev.db alembic upgrade head`
    on a fresh file: 8 tables created with the expected columns
    (CHAR(32) for UUIDs, JSON for JSONB). `pytest -q` 26/26 still
    green afterwards.
- **Done — Sprint 3 BE** (all 7 task IDs `in_review` in TRACKING):
  - **M4-BE-01..03** new estimators: `random_forest_classifier`,
    `logistic_regression` (built-in StandardScaler so LBFGS converges;
    importances = mean abs coefficient across classes), 
    `random_forest_regressor`, `lightgbm_regressor`. Each one new file
    + a single `@ModelRegistry.register` decorator + one import in
    `app/services/ml/__init__.py` — extension via registry, not core
    edits (RULES §2).
  - **M4-BE-04..05** `POST /api/v1/ml/train`: loads dataset (prefers
    `preprocessed_storage_path`), drops null-target rows, drops
    non-numeric features (fillna 0), runs `auto_train`, picks best by
    accuracy (classification) / r2 (regression), saves the winning
    model via joblib at `<storage>/models/{id}_{name}.joblib`,
    persists 1 `MlExperiment` row per leaderboard entry with
    `artifact_path` only on the winner.
  - **M4-BE-06** `GET /api/v1/ml/leaderboard/{dataset_id}`:
    workspace-scoped, returns `ExperimentOut[]` ordered by
    `created_at` desc.
  - **M4-BE-07** background training: `body.background=true` enqueues
    via FastAPI `BackgroundTasks`. The task opens its own DB session
    via `get_sessionmaker()` because the request session closes after
    the response is sent. Returns immediately with a stub
    `TrainResponse{leaderboard:[], extras:{status:"queued"}}`.
- **Tests**: `pytest -q` → **33 passed in 16.27s**. New file
  `tests/test_ml.py` (7 cases): registry coverage, classification
  end-to-end (60-row Iris-shaped, sorted accuracy desc, best has
  feature_importance, artifact exists), regression end-to-end (80-row
  synthetic linear, best r2 > 0.8), `/leaderboard` returns persisted
  rows with exactly one carrying `artifact_path`, unknown target →
  422, cross-workspace 404, saved artifact round-trips via joblib +
  predicts (handles the (scaler, model) tuple from logistic_regression).
- **Next session start**: User merges `backend` → `develop`. Then
  Sprint 3 FE on `frontend`: M4-FE-01 (TrainForm — RHF + Zod for
  target_column + task_type), M4-FE-02 (Leaderboard table sorted by
  primary metric), M4-FE-03 (ExperimentDrawer with feature-importance
  bar chart via `ChartRenderer`), M4-FE-04 (polling for in-progress
  background runs). Read `docs/modules/M4_AUTOML.md` first.
- **Blockers**: No external API keys for Sprint 3. Sprint 4 (Chat) is
  when GROQ_API_KEY / GEMINI_API_KEY become required. Also: full E2E
  browser smoke is now unblocked thanks to POL-08 — set
  `DATABASE_URL=sqlite+aiosqlite:///./data/dev.db`, `alembic upgrade
  head`, `uvicorn app.main:app --reload`, then `pnpm dev` on the
  frontend.
- **Notes**:
  - Feature-prep happens inside the train endpoint, not the auto_train
    runner, so the runner stays test-friendly with arbitrary X/y. If
    the user uploads a CSV with categorical features and didn't run
    preprocessing, the endpoint drops them and reports
    `extras.dropped_non_numeric`. With zero numeric columns left we
    raise `ValidationError("no_features")` rather than silently
    failing.
  - `logistic_regression` saves as a `(scaler, model)` tuple via
    joblib. The artifact-reload test handles both shapes; future
    Sprint 4 chat tools that load these artifacts must do the same
    isinstance check.
  - Sprint 3 acceptance "all classifiers train < 30s" easily met for
    the 60-row Iris-shaped fixture; large datasets may need
    background=true.

---

## 2026-05-04 — Session 10: Sprint 3 FE complete (AutoML UI)

- **Branch**: `frontend` — 1 commit (`5430b67`) on top of `4e7c79c`
  (develop tip after Sprint 2 merge). Note: this branch does NOT carry
  Sprint 3 BE; that lives on `backend` (Session 9 — `7e9a742`) and the
  SQLite-portable migrations polish (Session 9 — `658aa99`). Both are
  `in_review` waiting for user to merge backend → develop.
- **Done** (all 4 Sprint 3 FE task IDs `in_review` in TRACKING):
  - **M4-FE-01..04** AutoML page. New `lib/types.ts` Sprint 3 types
    (TaskType, TrainRequest, LeaderboardEntry, TrainResponse,
    ExperimentOut) mirroring backend schemas. New `lib/hooks/useMl.ts`
    (`useTrainModel` mutation + `useLeaderboard` query that accepts an
    optional `pollMs` for `refetchInterval`). New
    `components/ml/{TrainForm,Leaderboard,ExperimentDrawer}.tsx`. The
    `/ml/[id]/page.tsx` stub is now a working page: column dropdown is
    fed from `useDataset` (preprocessed columns when available), the
    train form posts via mutation, and on `background=true` the page
    flips into polling mode (5s interval) until the leaderboard grows
    past the pre-submit row count.
- **Tests / verification**: `pnpm typecheck` clean. `pnpm build` clean.
  Routes: `/ml/[id]` 7.74 kB / 219 kB FLJS (recharts heavy via the
  feature-importance bar chart).
- **Next session start**: User merges `backend` → `develop` first
  (brings in Sprint 3 BE + SQLite-portable migrations + AutoML smoke in
  WALKTHROUGH §7.6), then `frontend` → `develop` (this Session 10
  commit). After both lands, **Sprint 4 (M5 Agentic Chat)** is the next
  feature batch — that's when LLM API keys (GROQ_API_KEY,
  GEMINI_API_KEY) become required. Read `docs/modules/M5_CHAT_AGENTS.md`
  next.
- **Blockers**: Sprint 4 needs at least one provider key. Free tiers:
  console.groq.com (primary) + aistudio.google.com (Gemini, also used
  for embedding text-embedding-004). Manual E2E browser smoke is
  unblocked by Session 9's POL-08 — set
  `DATABASE_URL=sqlite+aiosqlite:///./data/dev.db`, `alembic upgrade
  head`, run uvicorn + `pnpm dev`, register, upload, train, observe
  leaderboard.
- **Notes**:
  - Polling stop condition is "row count strictly grew past pre-submit
    snapshot" — after the BackgroundTask finishes the leaderboard
    query gains N rows in one fetch, so this fires reliably. The hook
    sets `refetchInterval` only while polling is active.
  - The drawer flags logistic_regression's importance as
    "coefficient-based and scale-dependent" so users don't rank
    features cross-model directly.
  - Train submit uses `setPollUntilCount(before)` AFTER awaiting the
    mutation. If the BE returns sync results (background=false), the
    leaderboard refetches once instead of polling.

---

## 2026-05-04 — Session 8: Sprint 2 merged to develop (BE + FE)

- **Branch**: `develop` — merged `backend` (Session 6) then `frontend`
  (Session 7) one after the other. Auth-cookie-not-HttpOnly deviation
  unchanged; SQLite-runtime portability still pending.
- **Done**: All 13 Sprint 2 task IDs flipped to `done` in TRACKING (7 BE
  + 6 FE). Active branches table updated. Conflicts on TRACKING + HANDOFF
  resolved per RULES §4 ("keep both sets") — backend rows kept from
  HEAD, frontend rows added underneath.
- **State**: working tree clean. `pytest` 26/26, `pnpm typecheck` +
  `pnpm build` clean (verified pre-merge on the side branches).
- **Next session start**: Sprint 3 (M4 AutoML). BE first on `backend`:
  M4-BE-01..07 (RandomForest, LogisticRegression, regressor variants,
  POST /ml/train, model artifact persistence, GET /ml/leaderboard,
  background-task training). FE on `frontend`: M4-FE-01..04 (train form,
  leaderboard table, drawer with feature importance, polling). Read
  `docs/modules/M4_AUTOML.md` first.
- **Blockers**: Manual E2E browser smoke still requires BE running.
  Sprint 3 BE work is self-contained (sklearn + lightgbm already in
  `backend/requirements.txt`); no new external API keys needed yet.
  Sprint 4 chat is when LLM provider keys become required.
- **Tests at session end**: 26/26 pytest, FE typecheck/build clean.

---

## 2026-05-04 — Session 6: Sprint 2 BE complete (EDA + preprocessing)

- **Branch**: `backend` — 5 commits on top of `4e620ea` (which was the
  develop tip after Sprint 1 was merged in Session 4).
- **Done** (all 7 Sprint 2 BE task IDs flipped to `in_review` in TRACKING):
  - **Migration 0002 + model fields** — `8dae0ef`. `Dataset.preprocessed_storage_path`
    (String 1024 nullable) + `PipelineLog.params` (JSON / JSONB on Postgres).
    Added `LocalStorage.path_for_preprocessed(dataset_id)` → `{id}_pp.csv`.
    Sprint 1 tests still 17/17 green.
  - **EDA helpers + endpoints (M3-BE-01..03)** — `6d84b6e`. `scatter_spec` +
    `heatmap_spec` (Pearson via pandas round-trip; Polars lacks full-matrix
    corr). `_clean()` replaces NaN/Inf with None for Pydantic + JSON. Endpoints
    `GET /eda/{id}/profile` (returns cached `Dataset.profile`, recomputes if
    None) + `GET /eda/{id}/charts` (auto-picks histogram per numeric, bar for
    categorical with cardinality ≤ 50, one heatmap when ≥ 2 numerics; reads
    from `preprocessed_storage_path` when set).
  - **Preprocessing steps + registry (M2-BE-01..02)** — `d72dff5`.
    `RemoveOutliers` (IQR Tukey-fence, configurable `iqr_factor`) and
    `EncodeCategorical` (`one_hot` via `to_dummies` or `label` via Categorical
    physical codes). `steps/__init__.py` is now a real registry surface:
    `STEP_REGISTRY` dict + `build_step(name, params)` raising
    `ValidationError("unknown_step")` on miss.
  - **Preprocessing endpoints (M2-BE-03..04)** — `baaadfa`. `POST
    /preprocessing/{id}/run` validates non-empty step list, loads df via
    ParserRegistry, runs `Pipeline`, writes transformed CSV to
    `path_for_preprocessed`, persists one `PipelineLog` per step (1-indexed
    `step_order`, both `params` and `applied_changes` populated). `GET
    /preprocessing/{id}/logs` ordered by `created_at` then `step_order` so
    multiple runs read in insertion order. Wired into `api/v1/__init__.py`.
  - **Tests** — `3d637ab`. `tests/test_eda.py` (4 cases) + `tests/test_preprocessing.py`
    (5 cases). Suite now 26/26 (Sprint 1: 17 + Sprint 2: 9). NaN-cleansing
    asserted via no `"NaN"`/`"Infinity"` substring in response text + null
    cells in heatmap for constant columns. Registry extensibility test
    registers a runtime-only `Dummy` step and resolves through `build_step`.
  - **WALKTHROUGH** — bumped §5 test table to Sprint 2 totals; added §7.4
    (EDA smoke) + §7.5 (preprocessing smoke) curl recipes; renumbered the
    Swagger section to §7.6.
- **Tests at session end**: `pytest -q` → **26 passed in 11.42s**.
- **Next session start**: User reviews + merges `backend` → `develop`.
  Then **Sprint 2 FE** on `frontend`: M3-FE-01..03 (EDA charts page +
  per-column drilldown + responsive container) and M2-FE-01..03 (pipeline
  builder + run + log viewer). Read `docs/modules/M3_EDA_CHARTS.md` and
  `docs/modules/M2_PREPROCESSING.md`. The FE skeleton already has
  `ChartRenderer` + `recharts` adapter (histogram/bar/line/scatter wired,
  heatmap/pie are TODO fallback) — Sprint 2 FE includes shipping the
  heatmap renderer alongside the page.
- **Blockers**: Manual E2E browser smoke still needs BE running (no Docker
  per user). The SQLite-runtime polish task is still pending; tests don't
  hit it because they go through `Base.metadata.create_all`. Migration 0002
  follows Sprint 1 style (Postgres-only types) so SQLite-portable migrations
  remain a future single Polish task that touches both 0001 and 0002.
- **Notes**:
  - `Pipeline.run()` returns `(df, list[dict])` and does NOT persist the
    audit log — the endpoint is the only place where `PipelineLog` rows are
    written. Keep that boundary if Pipeline is ever called from a
    background task.
  - `step_order` is 1-indexed *per request*. Two consecutive runs both
    create a `step_order=1` row; ordering across runs is captured by
    `created_at`. The `GET /logs` endpoint sorts by both.
  - Heatmap cells with NaN correlations (constant column ↔ anything) come
    back as `value: null`, not the string `"NaN"` — verified in
    `test_charts_handle_constant_column_without_nan`.
  - One-hot via Polars `to_dummies` does not implement a `drop_first`
    option; AutoML (Sprint 3) will need to handle the resulting
    multi-collinearity if present.

---

## 2026-05-04 — Session 7: Sprint 2 FE complete (EDA page + preprocessing builder)

- **Branch**: `frontend` — 3 commits on top of `4e620ea` (develop tip
  after Session 5). Note: this branch does **not** carry Sprint 2 BE; the
  BE endpoints live on `backend` (Session 6) and aren't merged to
  develop yet. Sprint 2 FE compiles and types check against the shared
  types, but full E2E browser smoke needs the user to merge backend →
  develop and run the BE.
- **Done** (all 6 Sprint 2 FE task IDs flipped to `in_review` in TRACKING):
  - **Nav + CTAs** — `4f9a949`. `middleware.ts` adds `/preprocessing`
    to PROTECTED_PREFIXES. The dashboard sidebar's broken `/eda/_`
    placeholders now route to `/datasets` with section labels (EDA,
    Preprocessing, AutoML, Chat) — the user picks a dataset first, then
    drills in. `DatasetCard` lost its outer Link (it nested anchors when
    we added action buttons); title still links to detail, and a footer
    row exposes EDA, Preprocess, and Detail buttons per card.
  - **EDA page (M3-FE-01..03)** — `65d4647`. New `lib/hooks/useEda.ts`
    (useEdaProfile + useEdaCharts) and Sprint 2 type additions in
    `lib/types.ts`. `components/charts/adapters/recharts.tsx` ships a
    real heatmap renderer (square correlation grid; positive
    correlations red, negative blue, alpha = |value|, null cells render
    "—" on faint gray). `ColumnTable` gained optional `onSelect` +
    `selectedName` (still backwards-compatible for the Sprint 1 detail
    page). `app/(dashboard)/eda/[id]/page.tsx` replaced its stub with a
    full layout: stats card → clickable column list → drilldown
    spotlight that matches a chart by axis label/title → full charts
    grid (`lg:grid-cols-2`). M3-FE-03 responsive container is handled
    by recharts' existing `ResponsiveContainer` plus the page grid.
  - **Preprocessing page (M2-FE-01..03)** — `5c83663`. New
    `lib/hooks/usePreprocessing.ts` (`usePipelineLogs` + `useRunPipeline`;
    on success invalidates `["eda", id]` and `["datasets", id]` so EDA
    re-renders against the preprocessed CSV). New `components/preprocessing/`
    with `StepEditor` (step-name select bound to KNOWN_STEPS, JSON
    params textarea with live parse-error display) + `LogViewer` (table
    of all PipelineLog rows with pretty-printed JSON cells). New
    `app/(dashboard)/preprocessing/[id]/page.tsx`: linear chain (Add /
    Remove / Run), success Alert showing transformed_path + row/column
    count, audit log section below.
- **Tests / verification**: `pnpm typecheck` clean. `pnpm build`
  produces 10 routes. Notable sizes: `/eda/[id]` 106 kB / 215 kB FLJS
  (recharts heavy), `/preprocessing/[id]` 6.09 kB / 116 kB,
  `/datasets` 4.71 kB. Middleware 25.8 kB.
- **Next session start**: User reviews + merges `backend` → `develop`
  first, then `frontend` → `develop` (or merges develop → frontend to
  E2E smoke). After both Sprint 2 sides are integrated, **Sprint 3
  (M4 AutoML)** kicks off: M4-BE-01..07 on `backend` (RandomForest,
  LogisticRegression, regressor variants, POST /ml/train, model
  artifacts, GET /ml/leaderboard, background-task training) and
  M4-FE-01..04 on `frontend` (train form, leaderboard table, drawer with
  feature importance, polling). Read `docs/modules/M4_AUTOML.md` next.
- **Blockers**: Manual E2E browser smoke still needs BE running. To do
  it without Docker, follow the SQLite-runtime polish task once it
  lands; otherwise spin up Postgres or any reachable Postgres + apply
  migrations 0001 and 0002.
- **Notes**:
  - The drilldown matcher in `EdaPage` walks `spec.x_axis.label`,
    `spec.y_axis.label`, and `spec.title` to find the chart for a
    selected column. It intentionally returns `null` for heatmaps —
    those render at the page level, not per column.
  - `KNOWN_STEPS` in `StepEditor.tsx` is the only FE place that knows
    the step name → default-params mapping. If the BE registry adds a
    new step, add it here in the same commit (RULES §2 cross-side
    rule).
  - Heatmap colors are inline RGBA strings, not Tailwind classes,
    because Tailwind purges unknown classes at build time. The renderer
    sits inside `adapters/recharts.tsx`; swapping to ECharts later only
    re-implements `renderHeatmap()` in the new adapter file.
  - The auth cookie remains intentionally NOT HttpOnly — same Sprint 1
    deviation, still tracked in `ARCHITECTURE.md` Deviations.

---

## 2026-05-04 — Session 5 (close): manual FE smoke checklist

- **Branch**: `develop` (no code change). Session ended after Sprint 1
  merge so the next session starts clean.
- **State**: working tree clean. Local main 1 commit ahead of origin
  (the bootstrap docs commit `8289e16`); origin develop = `a2f5720`.
  All background processes (uvicorn, pnpm) stopped. No node/python
  processes leftover.
- **Manual FE smoke that works without BE running**:
  1. `cd frontend && pnpm dev` → http://localhost:3000.
  2. Landing `/` renders with Get-started + Sign-in buttons.
  3. `/login` and `/register` — RHF + Zod validation works:
     - Empty submit → inline errors per field.
     - `password` < 8 chars → "Password must be at least 8".
     - Bad email → "Please enter a valid email".
  4. Submit a valid form → red Alert ("Failed to fetch" or similar)
     because BE isn't running. That's expected; it confirms the
     api-client + AlertDescription wiring is correct.
  5. Try `/datasets` directly in the URL bar → middleware redirects
     to `/login?from=/datasets`. That validates the route guard.
  6. To unblock the dashboard for visual inspection without a real
     login: open DevTools console and run
     `document.cookie='ezidatic_token=test;path=/'`, then revisit
     `/datasets`. Middleware lets it through, the page calls
     `GET /api/v1/datasets` and shows an Alert with the network
     error. Use this to verify the layout, sidebar nav, Dropzone,
     and DatasetCard styling.
- **What still needs BE running** (deferred to next session): the
  full register → upload → list → detail browser flow, and the
  /datasets/{id} detail page rendering real ColumnTable rows.
- **Next session start**: Two paths, pick one:
  1. **Sprint 2 BE** on `backend`: pull develop, then implement
     M2 (preprocessing) + M3 (EDA / chart specs). Start with
     `docs/modules/M2_PREPROCESSING.md` and `M3_EDA_CHARTS.md`.
  2. **BE runtime path without Docker**: make the migration portable
     (sa.Uuid + sa.JSON with JSONB variant) so `alembic upgrade head`
     works against `sqlite+aiosqlite:///./data/dev.db`. Land a
     `WALKTHROUGH.md` "Quick path: SQLite" subsection. Then full FE
     E2E becomes possible without Docker.
- **Blockers**: None. User explicitly opted out of Docker for now.

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
