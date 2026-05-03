# M5 — Agentic Chat

**Goal**: A chat that picks the right specialist (router-worker), can call
tools (function-calling), streams tokens via SSE, and falls back across LLM
providers if the primary fails.

**Sprint**: 4.

## Files

### Backend

| Path | Responsibility |
|------|----------------|
| `backend/app/services/agents/llm_adapter.py` | Multi-provider w/ fallback (drafted) |
| `backend/app/services/agents/router.py` | Query classifier (drafted) |
| `backend/app/services/agents/providers/base.py` | LLMProvider ABC + ProviderRegistry (drafted) |
| `backend/app/services/agents/providers/groq.py` | Sample provider (drafted) |
| `backend/app/services/agents/providers/gemini.py` (new) | Priority 2 |
| `backend/app/services/agents/providers/openrouter.py` (new) | Priority 3 |
| `backend/app/services/agents/providers/ollama.py` (new) | Priority 4 (local) |
| `backend/app/services/agents/workers/explain_worker.py` | Sample (drafted) |
| `backend/app/services/agents/workers/sql_worker.py` (new) | Polars expr generation + sandbox exec |
| `backend/app/services/agents/workers/ml_worker.py` (new) | Triggers an `auto_train` and explains |
| `backend/app/services/agents/tools/base.py` | BaseTool + ToolRegistry (drafted) |
| `backend/app/services/agents/tools/query_dataset.py` | Sample stub (drafted) |
| `backend/app/services/agents/tools/plot_chart.py` (new) | Returns a ChartSpec |
| `backend/app/api/v1/chat.py` | Sessions + streaming messages (SSE) |
| `backend/app/models/chat.py` | ChatSession + ChatMessage (already exist) |
| `backend/tests/test_agents.py` (new) | Fallback, router, persistence |

### Frontend

| Path | Responsibility |
|------|----------------|
| `frontend/app/(dashboard)/chat/[sessionId]/page.tsx` | Chat container |
| `frontend/components/chat/MessageList.tsx` | Render w/ streaming partial |
| `frontend/components/chat/ChatInput.tsx` (new) | RHF + send |
| `frontend/components/chat/ProviderBadge.tsx` (new) | Show `provider_used` |
| `frontend/components/chat/ToolCallBlock.tsx` (new) | Collapsible JSON |
| `frontend/lib/stores/chatStore.ts` | Already drafted |
| `frontend/lib/types.ts` | `ChatMessage`, `ChatRole` already mirror BE |

## DB tables touched

`chat_sessions`, `chat_messages`.

## Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/v1/chat/sessions` | `{dataset_id?}` | `ChatSessionOut` |
| GET | `/api/v1/chat/sessions` | – | `ChatSessionOut[]` |
| GET | `/api/v1/chat/sessions/{id}/messages` | – | `ChatMessageOut[]` |
| POST | `/api/v1/chat/sessions/{id}/messages` | `ChatMessageIn` | SSE stream of tokens; final assistant message persisted |

## Extension points

- New provider: implement `LLMProvider`, decorate with `@ProviderRegistry.register`,
  add the import to `providers/__init__.py`.
- New tool: subclass `BaseTool`, instantiate, call `ToolRegistry.register(tool)`.
- New worker: a function `(question, context, llm) -> response`. Add to the
  router's worker dispatch map.

## Tasks

- [ ] **M5-BE-01** Gemini, OpenRouter, Ollama providers (priorities 2/3/4)
- [ ] **M5-BE-02** Verify fallback: kill primary, next provider takes over
- [ ] **M5-BE-03** Wire `router.route(question)` to QueryType
- [ ] **M5-BE-04** sql_worker (Polars expr + sandbox exec) + explain_worker (real impl)
- [ ] **M5-BE-05** query_dataset (real exec) + plot_chart tool
- [ ] **M5-BE-06** POST /chat/sessions create session
- [ ] **M5-BE-07** SSE stream POST /chat/sessions/{id}/messages, persist final assistant
- [ ] **M5-BE-08** Token usage + provider_used persisted on every message
- [ ] **M5-FE-01** ChatInput sending POST + reading SSE
- [ ] **M5-FE-02** MessageList with streaming partial assistant
- [ ] **M5-FE-03** ProviderBadge
- [ ] **M5-FE-04** ToolCallBlock
- [ ] **M5-FE-05** Embed ChartRenderer when assistant returns a ChartSpec
- [ ] **M5-FE-06** Session list sidebar w/ switch

## Acceptance criteria

- Sending a message streams tokens to the UI as they arrive.
- Disabling Groq (clear `GROQ_API_KEY` in env, restart) → next request
  visibly uses `provider_used = "gemini"`.
- A question routed to `eda` → assistant returns a ChartSpec → frontend
  embeds it via ChartRenderer.
- The router classification is accurate on a held-out test set (≥80%).

## Out of scope

- Agent memory / long-term context across sessions (Sprint 4 keeps it
  per-session only).
- Multi-turn tool-loop beyond depth 1 (call → result → answer).
- Vector retrieval / RAG (skeleton has Chroma but the wiring is a Polish
  task).
- Cost guardrails (request caps) — Polish.
