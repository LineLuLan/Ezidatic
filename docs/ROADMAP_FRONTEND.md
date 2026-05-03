# Frontend Roadmap — 4 Sprints

Mirror of the backend roadmap, focused on UI + state. Tasks here match IDs
in `TRACKING.md`. Module deep-dives live in `docs/modules/M{n}_*.md`.

> **Conventions**
> - All FE work happens on the `frontend` branch.
> - Commit per slice (Conventional Commits).
> - Every new page must `pnpm build` cleanly. Vitest comes online in Sprint 2+.
> - Shared types (`lib/types.ts`) MUST mirror BE Pydantic schemas. Update both
>   together — even if the BE diff is the trigger.

---

## Sprint 1 — Auth + Upload (M0 + M1)

**Goal**: User can register, log in, upload a CSV, see it in a list.

### Deliverables

- [ ] **M0-FE-01**: Login form on `/login` with React Hook Form + Zod
      mirroring `LoginRequest`.
- [ ] **M0-FE-02**: Register form on `/register`.
- [ ] **M0-FE-03**: `useAuthStore` persists token; redirect to `/datasets` on success.
- [ ] **M0-FE-04**: Route guard / middleware redirects unauthenticated users
      to `/login`.
- [ ] **M1-FE-01**: Wire `Dropzone` → POST `/api/v1/datasets` with progress.
- [ ] **M1-FE-02**: Datasets list page with TanStack Query, refresh on upload.
- [ ] **M1-FE-03**: Dataset row shows status badge (pending / ready / failed).
- [ ] **M1-FE-04**: Dataset detail page (`/datasets/[id]`) with profile table
      (name, dtype, null_count, unique_count).

### Definition of Done

- `pnpm build` green; no TS errors.
- Manual: register a user, upload sample.csv, see it in the list with
  populated profile.

---

## Sprint 2 — Charts + Preprocessing (M2 + M3)

**Goal**: User can browse auto-generated charts and apply a preprocessing
pipeline.

### Deliverables

- [ ] **M3-FE-01**: EDA page renders all charts from
      `GET /eda/{id}/charts` via `ChartRenderer`.
- [ ] **M3-FE-02**: Add tabs/filters: per-column drilldown.
- [ ] **M3-FE-03**: Wire `ResponsiveContainer` so charts fit on resize.
- [ ] **M2-FE-01**: Pipeline builder UI — drag-orderable list of steps with
      param forms (RHF + Zod).
- [ ] **M2-FE-02**: `Run pipeline` button → POST + show audit log.
- [ ] **M2-FE-03**: Pipeline log viewer (table of step + applied changes).
- [ ] Wire Vitest + first component test for `ChartRenderer`.

### Definition of Done

- Histograms + bars + scatter render against real BE responses.
- Pipeline builder round-trips: user adds 2 steps, runs, sees logs.

---

## Sprint 3 — AutoML UI (M4)

**Goal**: One-click train + leaderboard + feature importance visualization.

### Deliverables

- [ ] **M4-FE-01**: Train form — select target column, task type. Submit →
      show "training" state.
- [ ] **M4-FE-02**: Leaderboard table sorted by primary metric, with
      train_time per row.
- [ ] **M4-FE-03**: Click a row → drawer/dialog with full metrics +
      feature importance bar chart (reuse `ChartRenderer`).
- [ ] **M4-FE-04**: Polling or websocket for in-progress experiments.

### Definition of Done

- User picks a target column, kicks off auto_train, sees a populated
  leaderboard within ~1 minute on a small dataset.

---

## Sprint 4 — Chat UI (M5)

**Goal**: Streaming chat with provider attribution and tool-call display.

### Deliverables

- [ ] **M5-FE-01**: Chat input (RHF) sending POST + reading SSE chunks via
      Vercel AI SDK or native `EventSource`.
- [ ] **M5-FE-02**: `MessageList` with role-aware rendering (user / assistant /
      tool). Streaming partial assistant message.
- [ ] **M5-FE-03**: Display the provider used (badge: groq / gemini / etc.).
- [ ] **M5-FE-04**: Tool-call display: when assistant emits a tool_call,
      render the tool name + JSON args in a collapsible block.
- [ ] **M5-FE-05**: Embed `ChartRenderer` when assistant returns a ChartSpec
      (e.g., from `plot_chart` tool).
- [ ] **M5-FE-06**: Session list sidebar — switch between sessions.

### Definition of Done

- Sending a message renders assistant tokens as they arrive.
- Provider fallback works visibly: disabling Groq still streams from Gemini.

---

## Polish (post-Sprint 4)

- [ ] Auth-aware top-bar with sign-out.
- [ ] Empty states + error boundaries on every page.
- [ ] Loading skeletons (shadcn skeleton).
- [ ] Dark mode toggle (next-themes).
- [ ] Accessibility pass (focus rings, alt text, ARIA on charts).
- [ ] Lighthouse + bundle size review.
