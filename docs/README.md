# Ezidatic — Docs Index

All long-form project documentation lives here. `CLAUDE.md` at the repo root
points back to this folder.

## Files

| File | Purpose |
|------|---------|
| [`RULES.md`](./RULES.md) | Locked stack, extensibility rules, git workflow, commit conventions, testing minimum. The non-negotiable contract. |
| [`ROADMAP_BACKEND.md`](./ROADMAP_BACKEND.md) | 4-sprint backend plan with deliverables, DoD, migrations, tests. |
| [`ROADMAP_FRONTEND.md`](./ROADMAP_FRONTEND.md) | 4-sprint frontend plan with deliverables, DoD, tests. |
| [`TRACKING.md`](./TRACKING.md) | Master task tracker — every task has an ID, owner, status, branch, commit. |
| [`HANDOFF.md`](./HANDOFF.md) | Reverse-chronological session log. Latest entry first. |
| [`ARCHITECTURE.md`](./ARCHITECTURE.md) | Pointer back to the blueprint plus a Deviations log. |
| [`modules/M0_AUTH.md`](./modules/M0_AUTH.md) | Auth (User, Workspace, JWT, login/register). |
| [`modules/M1_INGESTION.md`](./modules/M1_INGESTION.md) | ParserRegistry, file upload, dataset profiling. |
| [`modules/M2_PREPROCESSING.md`](./modules/M2_PREPROCESSING.md) | Preprocessing pipeline, audit log, UI builder. |
| [`modules/M3_EDA_CHARTS.md`](./modules/M3_EDA_CHARTS.md) | Profiler, ChartSpec, ChartRenderer adapter. |
| [`modules/M4_AUTOML.md`](./modules/M4_AUTOML.md) | BaseEstimator, ModelRegistry, auto_train, leaderboard UI. |
| [`modules/M5_AGENTIC_CHAT.md`](./modules/M5_AGENTIC_CHAT.md) | LLM adapter, router, workers, tools, streaming chat UI. |

## Quick links

- Source of truth for architecture: [`../ezidatic-blueprint.md`](../ezidatic-blueprint.md)
- Public README: [`../README.md`](../README.md)
