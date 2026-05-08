# M_DEPLOY — Free-tier production deploy (POL-03 + POL-04)

**Goal**: ship a publicly reachable demo URL using only free tiers, per
the blueprint §10 deploy mapping. Cover both POL-03 (deploy 4 services)
and POL-04 (UptimeRobot keep-alive) since POL-04 strictly depends on
POL-03's Render URL.

**Sprint**: Polish.

**Status**: planning artifact — DO NOT execute until the account-setup
checklist (§0) is complete. See `docs/TRACKING.md` for live status.

---

## 0. Prerequisites — accounts to create (do these BEFORE running any
##    code in §3+)

| # | Service | Why it's needed | Free tier ceiling | Sign-up URL |
|---|---------|-----------------|-------------------|-------------|
| 1 | **GitHub** | Already used for the repo | Unlimited public repos | (already set) |
| 2 | **Supabase** | Postgres + file storage + pgvector | 500 MB DB, 1 GB Storage, unlimited API calls | https://supabase.com |
| 3 | **Upstash** | Redis for LLM cache (POL-05 ride-along) | 10K Redis commands/day, 256 MB DB | https://upstash.com |
| 4 | **Render** | Backend host (FastAPI) | 750 build-hours/month, sleeps after 15 min idle | https://render.com |
| 5 | **Vercel** | Frontend host (Next.js) | Unlimited Hobby projects | https://vercel.com |
| 6 | **UptimeRobot** | Ping Render every 10 min to defeat cold-start | 50 monitors free | https://uptimerobot.com |
| 7 | **Groq** | Primary LLM | Generous free credits, no card | https://console.groq.com |
| 8 | **Google AI Studio** | Gemini fallback + embeddings | 60 RPM free | https://aistudio.google.com |
| 9 | **OpenRouter** | Last-mile fallback (free models) | ~20 req/min on free tier | https://openrouter.ai |

After sign-up, generate these credentials and stash them in a password
manager (NEVER commit them):

- Supabase: project URL, anon key, service-role key, DB connection
  string (Direct URL + Pooler URL), Storage bucket name (`datasets`)
- Upstash: Redis REST URL + REST Token, AND the `redis://` connection
  URL (the `asyncio` Redis client we'll add uses the latter)
- Render: deploy hook URL (auto-generated when service is created)
- Vercel: project tied to the GitHub repo; secrets set via dashboard
- UptimeRobot: API key only needed if scripting; dashboard works fine
- LLM API keys: `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`

**Estimated time** to complete §0: **45–60 min** spread across 9 sites.
Most have email/Google sign-in; only Supabase + Render require a credit
card on file (charge $0 unless you exceed free tier).

---

## 1. Service map — dev → prod

| Layer | Dev (this repo today) | Prod target |
|-------|-----------------------|-------------|
| Frontend host | `pnpm dev` on `localhost:3000` | **Vercel** (auto-build from `main` on push) |
| Backend host | `uvicorn` on `localhost:8000` | **Render** Web Service (auto-build from `main` on push) |
| Database | Postgres in `docker compose` (or SQLite via WALKTHROUGH §4.1) | **Supabase Postgres** (free tier `db.<ref>.supabase.co:5432`) |
| File storage | `LocalStorage` writes under `backend/data/uploads/` | **Supabase Storage** bucket `datasets` |
| Vector store | ChromaDB in `docker compose` (`localhost:8001`) | **Supabase pgvector** extension on the same Postgres (no extra service) |
| Redis cache | `docker compose redis` on `localhost:6379` | **Upstash Redis** (TLS, pay-per-command) |
| Secrets | `backend/.env` (gitignored) | Render env-var dashboard + Vercel env-var dashboard |
| LLM keys | local `.env` | Same — keys are provider-side, host-agnostic |

ASCII flow:

```
  Browser
     │
     │  HTTPS
     ▼
  ┌───────────────┐        ┌────────────────────┐
  │  Vercel (FE)  │ ─────▶ │  Render (BE/api)   │
  │   Next.js 14  │  CORS  │     FastAPI        │
  └───────────────┘        └─────────┬──────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              ▼                      ▼                      ▼
     ┌─────────────────┐   ┌─────────────────┐   ┌──────────────────┐
     │  Supabase       │   │  Upstash Redis  │   │  Groq / Gemini / │
     │   Postgres+pg   │   │   (TLS, REST)   │   │  OpenRouter      │
     │   Storage       │   │                 │   │  (LLMs)          │
     └─────────────────┘   └─────────────────┘   └──────────────────┘
```

---

## 2. Code changes required BEFORE deploy

POL-03 isn't pure infra — the repo as of `f3991b4` only knows how to
talk to local Postgres / local FS / local Chroma. Three small slices
must land on `backend` first (each its own commit on the `backend`
branch, then merged through develop):

### 2.1 SupabaseStorage backend (BE)

Estimated effort: ~80 LOC, 1 hour.

- New file `backend/app/services/storage/base.py` — `StorageBackend`
  ABC with the same surface `LocalStorage` exposes today (`path_for`,
  `write_bytes`, `path_for_preprocessed`, `models_dir`,
  `path_for_model`). Add a `read_bytes(...)` method since Supabase is
  remote (LocalStorage gets it for free via `Path.read_bytes()`).
- New file `backend/app/services/storage/supabase.py` — wraps the
  `supabase-py` SDK (`supabase.storage.from_("datasets")`). For
  cross-call URLs, return signed URLs with TTL ≥ 1 hour rather than
  filesystem paths — change `path_for*` to return `str` that can be
  either a local path or a signed URL.
- Existing call sites that currently take `Path` from `LocalStorage`
  become `str` (or a small `StorageRef` dataclass with `.uri` +
  `.local_path` Optional). Audit: `app/api/v1/datasets.py`,
  `app/services/preprocessing/runner.py`, `app/services/ml/auto_train.py`.
- Registry: `STORAGE_REGISTRY: dict[str, type[StorageBackend]] =
  {"local": LocalStorage, "supabase": SupabaseStorage}`. `get_storage()`
  reads `settings.storage_backend` and dispatches.
- Add `supabase==2.x` to `backend/requirements.txt`.
- Tests: monkeypatch `get_storage` in `tests/conftest.py` to keep using
  `LocalStorage` against a temp dir — tests must NOT hit real Supabase.

### 2.2 pgvector wiring (BE) — OPTIONAL for MVP

The Sprint 4 chat code uses ChromaDB only for an embedding-cache-style
feature that isn't on the user-facing critical path. Two paths:

- **MVP path**: keep `VECTOR_BACKEND=chroma` and run ChromaDB on Render
  via a sidecar process. Render free tier doesn't support sidecars, so
  practically this means the prod deploy launches Chroma in-process
  (`chromadb.PersistentClient(path="/var/data/chroma")` — works on a
  Render disk if we add one). No code change.
- **Clean path**: add `VECTOR_BACKEND=supabase` support — switch to
  `langchain-postgres` `PGVector` against the same Supabase DB. Reuses
  existing pgvector extension. Adds `pgvector==0.x` +
  `langchain-postgres==0.x` to requirements.

Recommend MVP path for the demo deadline. Track the clean path as a
follow-up POL.

### 2.3 Redis cache layer (BE) — coincides with POL-05

POL-05 is "Redis cache for LLM responses" — also pending. Land it
together with deploy: cache key = `sha256(provider + model + system +
user_message)`, TTL = 24 h, store the full provider-response JSON. New
file `backend/app/services/agents/cache.py` with a thin wrapper around
`redis.asyncio.Redis.from_url(settings.redis_url)`. Settings already
has `redis_url`. `LlmRouter.invoke()` checks cache before fanning out
to providers; on hit, sets the persisted message's `provider_used`
field to e.g. `"groq (cached)"` for transparency.

If you want to ship POL-03 first and POL-05 second, that's fine — the
deploy works without Redis cache (every request hits the LLM). Just
keep `REDIS_URL` set so `redis-py` ping at startup doesn't blow up.

### 2.4 CORS for the prod FE domain (BE)

`backend/app/config.py` `cors_origins` defaults to
`"http://localhost:3000"`. Add the Vercel preview + prod domains via
the Render env-var:

```
CORS_ORIGINS=http://localhost:3000,https://ezidatic.vercel.app,https://*.vercel.app
```

Wildcard handling — current `cors_origins_list` does plain split. Either
keep wildcard support (FastAPI `allow_origin_regex`) or list each
preview URL explicitly. Recommend `allow_origin_regex` for preview
deployments; wire in `app/main.py` `CORSMiddleware(allow_origin_regex=
r"https://.*\.vercel\.app$")`.

### 2.5 Frontend `NEXT_PUBLIC_API_URL` (FE)

`frontend/.env.local.example` currently sets
`NEXT_PUBLIC_API_URL=http://localhost:8000`. In Vercel, set the prod
value to the Render service URL (e.g.
`https://ezidatic-api.onrender.com`). No code change — `NEXT_PUBLIC_*`
is already inlined at build time.

---

## 3. Step-by-step deploy procedure

### 3.1 Supabase project (first, because Render points at it)

1. Dashboard → New project. Pick a region close to Render (US East /
   Frankfurt). Note the **DB password** prompted at creation.
2. Settings → Database → **Connection string (URI, asyncpg-compatible)**.
   Copy the *Pooler* URL (port 6543, transaction mode) — we need
   pooled because Render's free tier has a low connection cap. Format:
   `postgresql+asyncpg://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:6543/postgres`.
3. SQL Editor → run `create extension if not exists vector;` to enable
   pgvector. (Required even on MVP path because Sprint 4 chat may
   probe for it.)
4. Storage → New bucket → **`datasets`**, public OFF, file-size-limit
   50 MB. Copy the **bucket name** + **service-role key** (Settings →
   API → Project API keys → `service_role`). The service-role key
   bypasses RLS — the backend uses it.
5. Run alembic against the prod DB **once** before deploying:
   ```bash
   cd backend
   export DATABASE_URL='postgresql+asyncpg://postgres.<ref>:<pwd>@aws-0-<region>.pooler.supabase.com:6543/postgres'
   alembic upgrade head
   ```
   Verify in Supabase Table Editor that all 8 tables landed.

### 3.2 Upstash Redis

1. Dashboard → Create database. Type "Regional" (cheapest), region
   matching Render. Eviction policy: `allkeys-lru` (cache use case).
2. Connect tab → copy the `redis://` URL (TLS-enabled). Format:
   `rediss://default:<token>@<host>.upstash.io:6379`.
   (Note `rediss://` with two s's = TLS.) `redis-py` v5 understands
   this scheme natively.

### 3.3 Render — backend service

1. Dashboard → New + Web Service → Connect the GitHub repo. Pick the
   `main` branch.
2. Settings:
   - **Name**: `ezidatic-api` (or pick your own — affects the
     `*.onrender.com` URL).
   - **Region**: same as Supabase + Upstash.
   - **Branch**: `main`.
   - **Root Directory**: `backend`.
   - **Runtime**: Python 3 (Render's "3.13" if available; fall back to
     "3.12" — see §5 risk-2).
   - **Build Command**: `pip install -r requirements.txt`.
     (Note: `requirements-dev.txt` is unnecessary in prod — saves
     install time + memory.)
   - **Start Command**: `alembic upgrade head && uvicorn app.main:app
     --host 0.0.0.0 --port $PORT`.
   - **Plan**: Free.
3. Environment tab — paste the secrets (do NOT use the
   `.env.example` defaults verbatim, they're dev-only):

   | Key | Value source |
   |-----|-------------|
   | `APP_ENV` | `production` |
   | `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
   | `DATABASE_URL` | Supabase Pooler URL from §3.1 step 2 |
   | `REDIS_URL` | Upstash `rediss://` URL from §3.2 step 2 |
   | `STORAGE_BACKEND` | `supabase` |
   | `SUPABASE_URL` | `https://<ref>.supabase.co` |
   | `SUPABASE_SERVICE_ROLE_KEY` | service_role key from §3.1 step 4 |
   | `SUPABASE_BUCKET` | `datasets` |
   | `MAX_FILE_SIZE_MB` | `50` |
   | `VECTOR_BACKEND` | `chroma` (MVP path) — uses Render disk |
   | `CHROMA_PERSIST_DIR` | `/var/data/chroma` (matches the disk in step 4) |
   | `GROQ_API_KEY` | from §0 step 7 |
   | `GROQ_MODEL` | `llama-3.3-70b-versatile` |
   | `GEMINI_API_KEY` | from §0 step 8 |
   | `OPENROUTER_API_KEY` | from §0 step 9 |
   | `CORS_ORIGINS` | `https://ezidatic.vercel.app` (update after §3.4) |

4. Disks tab → Add a 1 GB persistent disk mounted at `/var/data` —
   used by Chroma to survive deploys. Free tier allows one disk.
5. Deploy. First build is slow (chromadb + lightgbm + polars wheels +
   Render's free CPU is slow) — expect **5–10 min**.
6. After "Live", visit `https://ezidatic-api.onrender.com/health` and
   confirm `{"status": "ok", ...}`.

### 3.4 Vercel — frontend project

1. Dashboard → New project → Import the same GitHub repo. Vercel will
   detect Next.js automatically.
2. Settings:
   - **Framework preset**: Next.js (auto).
   - **Root Directory**: `frontend`.
   - **Build Command**: `pnpm build` (auto).
   - **Install Command**: `pnpm install --frozen-lockfile` (auto).
   - **Output Directory**: `.next` (auto).
3. Environment Variables — Production scope:

   | Key | Value |
   |-----|-------|
   | `NEXT_PUBLIC_API_URL` | `https://ezidatic-api.onrender.com` (no trailing slash) |

4. Deploy. First build ~2 min. Note the prod URL (e.g.
   `https://ezidatic.vercel.app`).
5. Go BACK to Render → Environment → update `CORS_ORIGINS` to the new
   Vercel URL → manual redeploy. **Don't skip this** — without it the
   frontend will get CORS errors on every API call.

### 3.5 UptimeRobot — keep-alive (POL-04)

**Pre-req**: §3.3 Render deploy must be live. Verify
`https://ezidatic-api.onrender.com/health` returns 200 in a browser
or curl before continuing — if it 404s/500s, fix Render first
(no point pinging a broken endpoint).

1. **Sign up + verify email** at https://uptimerobot.com (free tier,
   no card). Verify the email — UptimeRobot won't send alerts to
   unverified addresses.
2. **My Settings** → confirm time zone (alert timestamps use it).
3. Dashboard → **+ New monitor**. Fill exactly:

   | Field | Value | Why |
   |-------|-------|-----|
   | Monitor Type | **HTTP(s)** | Plain HTTP GET; Render's `/health` returns JSON 200. |
   | Friendly Name | `Ezidatic API health` | Shows in alerts + dashboard rows. |
   | URL (or IP) | `https://ezidatic-api.onrender.com/health` | Replace with your actual Render service URL. |
   | Monitoring Interval | **5 minutes** | Free-tier minimum. Must be ≤ 14 min to defeat Render's 15-min idle sleep. |
   | Monitor Timeout | 30 seconds | Renders cold start can take ~30s; longer timeout avoids false-positive downtime alerts on first wake. |
   | HTTP Method | GET | Default. |
   | Alert When | Status code is **NOT** 200 | Default for HTTP(s); just confirm. |

4. Scroll to **Alert Contacts** → tick your verified email → Save.
   (Optional: add a Slack / Discord webhook contact too. Free tier
   allows up to 3 alert contacts per monitor.)
5. Click **Create Monitor**. UptimeRobot fires the first ping within
   ~60 seconds; the row turns green when it gets a 200.
6. **Validation step** (do this before declaring POL-04 done):
   - Wait ~10 minutes (≥ 2 ping cycles).
   - Open the monitor → "Logs" tab. Should show 2+ "Up" entries.
   - Open Render → service → Events. Should NOT show recent
     "Service is sleeping" / "Spinning up" entries — the constant
     5-min ping prevents the 15-min idle window from closing.
   - **Expected**: median response time on the monitor row drops to
     <300 ms within 30 minutes (Render is awake, hot path).

**Anti-patterns**:
- Don't lower the interval to 1 min hoping for "more uptime" — free
  tier caps at 5 min; the form will reject 1 min.
- Don't ping a non-`/health` route (e.g. `/`) — `/health` is the
  only route guaranteed to be 200 even when no LLM keys are set.
- Don't rely on Render's "Always On" toggle — that's a paid plan
  feature; UptimeRobot is the free workaround.

**Cost**: 0$/month. UptimeRobot free supports 50 monitors at 5-min
intervals; we use 1.

After §3.5 and the validation step pass, POL-04 is `done`. Flip both
POL-03 and POL-04 statuses in `docs/TRACKING.md` in the same docs
commit (since they ride together).

**Rollback**: pause the monitor (don't delete) — UptimeRobot keeps
the historical uptime % data. Render service then sleeps after 15
min idle as before.

---

## 4. End-to-end smoke test (run after §3.5)

Same flow as `docs/WALKTHROUGH.md` §7 but against prod:

1. **Register**: `curl -X POST https://ezidatic-api.onrender.com/api/v1/auth/register -d '{"email":"smoke@test.com","password":"smoke1234"}'` → returns access token.
2. **Upload CSV**: `curl -F file=@sample.csv https://ezidatic-api.onrender.com/api/v1/datasets -H "Authorization: Bearer <token>"` → returns dataset id, status `ready`. Verify the file shows up under Supabase Storage → `datasets/` bucket.
3. **Profile**: `GET /api/v1/eda/<id>/profile` → expected JSON profile.
4. **Charts**: `GET /api/v1/eda/<id>/charts` → list of ChartSpec.
5. **Train**: `POST /api/v1/ml/train` with target column → leaderboard.
6. **Chat**: open `https://ezidatic.vercel.app/chat`, create session
   tied to the dataset, ask "summarize this data" → SSE streams back
   from Groq.

Acceptance: every step returns a 2xx, no CORS errors in browser
DevTools, dataset file is reachable from Supabase Storage UI.

---

## 5. Risks + mitigations

| # | Risk | Likelihood | Mitigation |
|---|------|-----------|-----------|
| 1 | **Render cold start** — first request after 15 min sleep takes ~30 s | High | UptimeRobot 5-min ping (§3.5). Net cost: ~14k Render hours/year < 750 h/month free quota. |
| 2 | **Render runtime version mismatch** — Render's "Python 3" picks 3.12 by default; CI uses 3.13. `requirements.txt` tested on 3.13. | Medium | Either lock Render to 3.13 via `runtime.txt` (a single line `python-3.13.x` in `backend/`) or test 3.12 locally first. Recommend `runtime.txt` for determinism. |
| 3 | **Supabase 500 MB DB cap** — chat sessions accumulate messages | Low (demo timeline) | Audit row counts per table monthly; truncate `chat_message` older than 30 days if needed. |
| 4 | **Supabase 1 GB Storage cap** — uploaded CSVs accumulate | Medium | Per-workspace quota check on upload (already have `MAX_FILE_SIZE_MB=50`). For demo, periodic manual cleanup is fine. |
| 5 | **Upstash 10K commands/day** | Low | LLM cache: 1 GET + 1 SETEX per chat message = ~5K commands/day at typical demo traffic. Only an issue if traffic spikes. |
| 6 | **LLM provider rate limits** during demo | Medium | Already have `Groq → Gemini → OpenRouter → Ollama` fallback chain. Confirm it works in prod by intentionally setting `GROQ_API_KEY=invalid` in Render and re-running smoke step 6. |
| 7 | **Secret leakage** — accidentally committing `.env` | High if careless | `.gitignore` already covers `.env`. Pre-commit hook (POL-01) doesn't lint `.env` but doesn't auto-stage it either. Convention: every secret enters via Render/Vercel/Supabase dashboard, never via git. |
| 8 | **CORS misconfig** — frontend gets blocked | High on first deploy | §3.4 step 5 covers it. If using preview deployments, the regex pattern in §2.4 handles `*.vercel.app`. |
| 9 | **Migration drift** — alembic head differs between dev SQLite and prod Postgres | Low | POL-08 already made migrations cross-DB. Run `alembic upgrade head` once on Supabase before first deploy (§3.1 step 5). |
| 10 | **Storage backend code is not yet shipped** — §2.1 must land first | High (this IS the blocker) | §2.1 + §2.4 (CORS) on `backend` branch first. §2.3 + §2.5 can happen in parallel. After they land + merge, rerun §3 from scratch. |

---

## 6. Order of execution (when you have credentials)

1. **§0 — Account setup** (one-time, ~1 hour).
2. **§2.1 SupabaseStorage code** on `backend` branch (BE work session,
   ~3 hours including tests).
3. **§2.4 CORS regex code** on `backend` branch (~30 min).
4. *(Optional)* **§2.3 Redis cache code** on `backend` branch (POL-05
   ride-along, ~2 hours).
5. **Merge backend → develop** after the BE wave is green in CI.
6. **§3.1 Supabase setup + §3.2 Upstash setup** (45 min).
7. **§3.3 Render deploy** + first smoke (`/health`) (1 hour incl.
   build wait).
8. **§3.4 Vercel deploy** + CORS update (30 min).
9. **§4 End-to-end smoke** (15 min).
10. **§3.5 UptimeRobot** (5 min) — POL-04 done.
11. **TRACKING + HANDOFF + FINAL_REPORT (POL-07)** updates (30 min).

Total estimate when starting from credentials in hand: **~8 hours**
of focused work spread over 1–2 sessions.

---

## 7. Rollback plan

Each external service is independent — the worst case is "feature X
broken" not "everything down":

- **Vercel**: rollback = re-deploy a prior git commit from the Vercel
  Deployments tab. One click, ~2 min.
- **Render**: rollback = manual deploy of a prior commit via the Render
  dashboard. ~5 min.
- **Supabase DB**: rollback = `alembic downgrade -1` against the prod
  DB. Drop a column or revert an enum at most. **Always test the
  downgrade SQL on a fresh local copy first**.
- **Upstash**: rollback = flush the cache, no schema state.
- **UptimeRobot**: rollback = pause the monitor.

Worst-case full rollback: revert `backend/app/services/storage/__init__.py`
to the LocalStorage-only state, set `STORAGE_BACKEND=local` on Render,
redeploy. Files in Supabase Storage become orphaned but remain
downloadable for 7 days (Supabase soft-delete window).

---

## 8. Out of scope for POL-03

- **Custom domain** (e.g. `ezidatic.app`) — Vercel + Render both
  support it but it adds DNS setup + TLS certificate provisioning. Use
  the freebie `*.vercel.app` / `*.onrender.com` URLs for the demo.
- **Production-grade monitoring** beyond UptimeRobot (Sentry, Grafana,
  log aggregation) — separate POL.
- **Auto-scaling / non-free tier** — explicitly outside POL-03's "free
  tier" scope.
- **HuggingFace Spaces backup deploy** mentioned in blueprint §10 —
  separate POL if Render proves unstable during demo.
- **Hardening**: rate limiting, DDoS, WAF, secret rotation. Demo-grade
  app, not a fortress.

---

## 9. References

- Blueprint §10 (`ezidatic-blueprint.md` lines 1000–1015) — the
  free-tier service mapping this plan implements.
- Blueprint §8 (`.env.example` template, lines 900–945) — the canonical
  env-var list for prod secrets.
- `docs/RULES.md` §1 — locked stack, why we can't swap Render for Fly
  without an explicit ask.
- `docs/WALKTHROUGH.md` §11 — CI behavior; CI doesn't auto-deploy yet.
  Adding a "deploy on tag push" GitHub Action is a separate POL.
- `backend/app/config.py` — current Settings class, single source of
  truth for env-var names.
