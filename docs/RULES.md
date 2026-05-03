# Rules — Codebase, Extensibility, Git Workflow

Non-negotiable. If a rule needs to change, open a discussion with the user;
never edit it unilaterally.

---

## 1. Locked Tech Stack

Once chosen, do not swap libraries to avoid rewrites. Justified swaps need an
explicit ask and a Deviations entry in `ARCHITECTURE.md`.

### Backend

| Layer | Choice |
|-------|--------|
| Framework | FastAPI 0.115 (async) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Validation | Pydantic v2 + pydantic-settings |
| Data | Polars (primary) + Pandas (compat layer only) |
| ML | scikit-learn + LightGBM |
| LLM | LangChain + multi-provider adapter (Groq → Gemini → OpenRouter → Ollama) |
| Vector | ChromaDB (local) → Supabase pgvector (deploy) |
| Auth | JWT custom in `backend/app/core/security.py` |
| Storage | Local FS (dev) → Supabase Storage (prod) |
| Cache/Queue | Redis (Upstash free in prod) |
| Test | pytest + httpx |
| Lint/Format | Ruff + Black, line-length 100, target py311 |

### Frontend

| Layer | Choice |
|-------|--------|
| Framework | Next.js 14 App Router + TypeScript strict |
| State | Zustand |
| Data | TanStack Query v5 |
| UI | Tailwind v3 + Shadcn UI |
| Charts | Recharts (default) — swappable via adapter pattern |
| Forms | React Hook Form + Zod |
| Streaming | Vercel AI SDK |
| Lint/Format | ESLint + Prettier (with prettier-plugin-tailwindcss) |
| Package mgmt | pnpm |

### Why locked

The blueprint already evaluated alternatives. Switching costs (rewriting
shared types, retraining muscle memory, breaking existing tests) outweigh the
gain for a 4-sprint timeline.

---

## 2. Extensibility Rules

Every new capability MUST plug in via a registry, never by editing core code.

### Registries (in `backend/app/services/`)

| Registry | Where | What plugs in |
|----------|-------|---------------|
| `ParserRegistry` | `ingestion/base.py` | New file formats (`.parquet`, `.xlsx`, `.json`) |
| `ModelRegistry` | `ml/base_estimator.py` | New ML estimators |
| `ProviderRegistry` | `agents/providers/base.py` | New LLM providers |
| `ToolRegistry` | `agents/tools/base.py` | New agent tools (function-calling) |
| `BaseStep` subclasses | `preprocessing/steps/` | New preprocessing steps |

### Hard rules

- No hard-coded model names, prompts, thresholds, or hyperparameters in
  business logic. Put them in `app/config.py` (`Settings`) or the relevant
  registry's class attributes.
- Public interfaces are ABCs. Anything calling a parser/estimator/provider/
  tool must call it through the interface, not the concrete class.
- Adding a new parser/estimator/provider must be a single file with no
  changes to `__init__.py` aggregations beyond one import line — the
  registry picks it up automatically.
- Frontend `ChartRenderer` switches by `spec.type`, never by chart library
  internals. Adding a chart type = adding a branch in the adapter.
- Shared types (`ChartSpec`, `Dataset`, `ChatMessage`) live in
  `frontend/lib/types.ts` and MUST mirror the corresponding Pydantic
  schemas in `backend/app/schemas/`. Backend schema change = same-PR
  update on the frontend type.

---

## 3. Git Workflow

### Branches

```
main      ← develop ← backend
                    ← frontend
```

- `main` — production-ready only. Tagged releases. Never push directly.
- `develop` — integration. User merges side branches here after testing.
  Cross-cutting changes (docs, infra, root config) are committed here
  directly.
- `backend` — backend work in progress. Pushed by author, reviewed by user,
  merged to `develop` by user.
- `frontend` — same as backend, for the FE.

### Workflow per feature

1. Pick the next task from `docs/TRACKING.md`.
2. `git checkout backend` (or `frontend`); pull latest.
3. Implement the smallest vertical slice that delivers the task.
4. Run side-specific verification (`pytest`, or `pnpm typecheck && pnpm build`).
5. Commit using Conventional Commits.
6. Push to the side branch.
7. Update `docs/TRACKING.md` (status → `in_review`, commit hash) and append
   to `docs/HANDOFF.md`. These updates can be on the side branch (if they
   touch only `docs/TRACKING.md` + `docs/HANDOFF.md` lines) or on `develop`
   in a separate commit — pick whichever avoids merge conflicts.
8. Notify the user. They test, then merge to `develop`. When a sprint is
   stable, they merge `develop` to `main`.

### Commit conventions

[Conventional Commits](https://www.conventionalcommits.org/):

```
feat(scope): short imperative summary

Optional body explaining why and how.

Co-Authored-By: ...
```

Allowed types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`,
`build`, `ci`. Common scopes: `auth`, `ingestion`, `preprocessing`, `eda`,
`ml`, `chat`, `agents`, `ui`, `api`, `db`.

### Hard rules

- Never `--force` push to `main` or `develop`.
- Never `--no-verify` past hooks. Fix the underlying lint/test failure.
- Never amend a published commit.
- One commit = one vertical slice. Do not bundle 5 features into 1 commit.
- Backend commits should not touch `frontend/` and vice versa, except for
  shared-type changes (`frontend/lib/types.ts`) which are allowed in a
  backend commit when the schema changes.

---

## 4. Documentation Rules

After every feature merged to `develop`:

- Update `docs/TRACKING.md`: status → `done`, fill the commit hash.
- Append a new entry to `docs/HANDOFF.md` (latest first). Include: what
  was done, what's next, blockers, test status.
- If the feature added a new registry entry (parser/estimator/etc.), add
  one line to the relevant module file in `docs/modules/`.

If a feature deviates from the blueprint, add a row to the Deviations table
in `docs/ARCHITECTURE.md`.

### Docs-on-every-branch rule

`CLAUDE.md` (root) and the entire `docs/` folder MUST be present on every
active branch — `main`, `develop`, `backend`, `frontend`, and any future
side branches. Sessions that start on a side branch read `CLAUDE.md` and
`docs/HANDOFF.md` first; missing those files leaves the session blind.

Propagation rules:

- Whenever a commit on `develop` touches `docs/` or `CLAUDE.md`, merge
  `develop` into both side branches in the same session and push:
  `git checkout backend && git merge develop && git push origin backend`,
  same for `frontend`.
- New branches must be created from a tip that already contains `docs/`
  (i.e. `develop` or later). Never fork from a commit that predates the
  docs bootstrap.
- A side-branch commit MAY update `docs/TRACKING.md` and append to
  `docs/HANDOFF.md`. Conflicts on those two files between `develop` and
  a side branch are normal — resolve by keeping both sets of changes
  (TRACKING rows are append-only, HANDOFF entries are append-on-top).

---

## 5. Testing Minimum

- **Backend**: any new endpoint has at least one happy-path pytest test
  using the `client` fixture in `tests/conftest.py`. Critical logic
  (registries, pipeline runner, fallback adapter) has a unit test.
- **Frontend**: any new page must render without runtime errors in
  `pnpm build`. Critical components (`ChartRenderer`, stream handlers)
  get a Vitest unit test once Vitest is wired (Sprint 2).

---

## 6. Permissions Reminder

- Do not push directly to `main`. The user does this manually after merging
  `develop`.
- Do not run destructive git operations (`reset --hard`, `branch -D`,
  force-push) without explicit user instruction.
- Do not change the values in this file without an explicit user ask.
