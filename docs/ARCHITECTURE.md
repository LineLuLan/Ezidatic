# Architecture

The architectural source of truth is [`../ezidatic-blueprint.md`](../ezidatic-blueprint.md).
Re-read it whenever you're unsure how a subsystem fits in. This file only
records **deviations** from the blueprint and short notes about the live code.

## Pointer map

| Concern | Where to look |
|---------|---------------|
| High-level architecture diagram | `ezidatic-blueprint.md` §2 |
| Folder structure (live) | `CLAUDE.md` map, plus `backend/` and `frontend/` directly |
| Locked stack | `docs/RULES.md` §1 |
| Plug-in contracts (registries) | `docs/RULES.md` §2 |
| Module-by-module plans | `docs/modules/M0..M5_*.md` |
| Sprint deliverables | `docs/ROADMAP_BACKEND.md`, `docs/ROADMAP_FRONTEND.md` |

## Deviations from the blueprint

Add a row here whenever live code deviates from the blueprint, with a one-line
rationale. The blueprint stays untouched — this file is the running diff.

| Date | Where | Deviation | Rationale |
|------|-------|-----------|-----------|
| 2026-05-03 | `backend/app/services/ingestion/__init__.py` | Registry population happens via `__init__.py` import side-effects rather than a manual `import_module()` call at startup | Simpler; lets `from app.services.ingestion import ParserRegistry` work without an extra wiring step |
| 2026-05-03 | `backend/alembic/env.py` | Async-aware (uses `async_engine_from_config` + `asyncio.run`) — blueprint didn't specify | Required because we use `asyncpg` |
| 2026-05-03 | `frontend/lib/api-client.ts` | JWT pulled from `localStorage` directly | OK for MVP; switch to httpOnly cookie in Polish if security review demands it |

## Subsystem notes (only what's not obvious from the blueprint)

### Ingestion
- `ParserRegistry._registry` keyed by lowercase extension. Importing
  `app.services.ingestion` (or any `.csv_parser` style submodule) is what
  registers a parser. Don't rely on lazy import elsewhere — it must happen
  before the first `get_parser()` call. The FastAPI `startup` event does this.

### ML
- `ModelRegistry` keyed by class-level `name`. `auto_train.py` filters by
  `task` attribute. The leaderboard primary metric is `accuracy` for
  classification, `r2` for regression — change in `auto_train.py`, not
  per-estimator.

### Agents
- `LLMAdapter` instantiates one provider per `ProviderRegistry.all()` entry
  on construction. Providers are sorted by `priority` ascending. Adding a
  provider = decorate the class + add an `__init__.py` import.
- The `model_override` kwarg is consumed (popped) inside each provider's
  `invoke` / `stream` so it doesn't leak to the SDK.
