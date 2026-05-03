# Ezidatic — Claude Read-First

This file is the entry point for any Claude session working on this repo.
Read the **always-read** list before doing anything else.

## Always-read (every session, in order)

1. `docs/HANDOFF.md` — what the previous session did and where to pick up.
2. `docs/TRACKING.md` — master task tracker with current statuses.
3. `docs/RULES.md` — locked stack, extensibility rules, git workflow.
4. `CLAUDE.md` (this file).

## Read when relevant

- `docs/WALKTHROUGH.md` — hands-on runbook (setup, run, test, smoke). **Read this first** when running anything for the first time, or when a command is unfamiliar.
- `ezidatic-blueprint.md` — original architecture spec (immutable source of truth).
- `docs/ROADMAP_BACKEND.md` / `docs/ROADMAP_FRONTEND.md` — sprint deliverables per side.
- `docs/modules/M{n}_*.md` — detailed plan for the module currently in scope.
- `docs/ARCHITECTURE.md` — how the live code differs from the blueprint (deviations log).
- `README.md` — public-facing project overview.

## Workflow at a glance (full version in `docs/RULES.md`)

- Backend work happens on the `backend` branch. Frontend on `frontend`.
- Commit after every vertical slice using Conventional Commits.
  Examples: `feat(ingestion): add excel parser`, `fix(eda): handle empty column`.
- Push the side branch when a feature is ready for review. The user merges it
  into `develop` after testing. `main` only receives finalized releases from
  `develop`.
- Do NOT push directly to `main`. Do NOT change the locked stack in
  `docs/RULES.md` without an explicit ask.
- Update `docs/TRACKING.md` and append `docs/HANDOFF.md` at the end of every
  session.

## Map of the repo

```
Ezidatic/
├── CLAUDE.md                <- you are here
├── README.md                <- public overview
├── ezidatic-blueprint.md    <- architecture source of truth
├── docker-compose.yml       <- postgres + redis + chroma for dev
├── .env.example             <- shared docker vars
├── docs/                    <- everything Claude reads
├── backend/                 <- FastAPI (work on `backend` branch)
└── frontend/                <- Next.js (work on `frontend` branch)
```

## When the user asks you to do BE work

1. `git checkout backend` (create from `develop` if missing).
2. Pull latest: `git pull origin backend`.
3. Read the relevant `docs/modules/M{n}_*.md`.
4. Implement, write tests, run `pytest`.
5. Commit + push to `backend`.
6. Update `docs/TRACKING.md` + `docs/HANDOFF.md`.

## When the user asks you to do FE work

1. `git checkout frontend` (create from `develop` if missing).
2. Pull latest: `git pull origin frontend`.
3. Read the relevant `docs/modules/M{n}_*.md`.
4. Implement, run `pnpm typecheck`, `pnpm build`.
5. Commit + push to `frontend`.
6. Update `docs/TRACKING.md` + `docs/HANDOFF.md`.

## When the user asks you to do something cross-cutting (docs, infra, refactor that spans both)

Work on `develop` directly. Smaller commits are still required.
