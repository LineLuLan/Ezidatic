# M_QUALITY — Sprint 5 Quality backlog

**Goal**: Address agent reliability, EDA chart relevance, and ML training
correctness gaps observed after Sprint 4 smoke. Each issue ships with
a measurable acceptance criterion so progress is verifiable.

**Sprint**: 5.

## Priority legend

- **P0** — high ROI, low blast radius. Prompt edits, simple imputation
  swap. Pick first.
- **P1** — schema or capability extension. Touches `TrainRequest`,
  `ChartSpec`, or worker control flow. Cross-side commits per RULES §2.
- **P2** — polish. Optional features, defaulted off.

## Order of execution (suggested)

1. **P0 wave**: Q5-AGENT-01, Q5-AGENT-02, Q5-ML-01, Q5-ML-02.
2. **P1 wave**: Q5-AGENT-03, Q5-AGENT-04, Q5-EDA-01, Q5-ML-03, Q5-ML-04.
3. **P2 wave**: Q5-EDA-02, Q5-EDA-03, Q5-ML-05.

## Cross-cutting reuse

- **Registry pattern (RULES §2)**: `ParserRegistry`, `ModelRegistry`,
  `ProviderRegistry`. Q5-EDA-02 / Q5-EDA-03 use existing chart-spec
  helpers — no new registry needed.
- **`TrainRequest` extension** (`backend/app/schemas/ml.py`): already has
  `background: bool`. Add `imputation`, `metric`, `tune` as optional
  fields with defaults that preserve old behaviour.
- **`extras` dict in `TrainResponse`**: Sprint 3 already uses
  `dropped_non_numeric`. Add `encoded_columns`, `imputed_columns`,
  `cv_mean`, `cv_std` through the same channel — no schema break.
- **`ChartSpec` discriminated union**: Q5-EDA-02 adds `boxplot` variant.
  `frontend/lib/types.ts` must update in the same commit.

---

## Agent

### Q5-AGENT-01 — Router few-shot examples [P0]

**Root cause**
File: `backend/app/services/agents/router.py:22-30`
`ROUTER_PROMPT` is zero-shot. Free-tier models (Gemini 2.5-flash-lite,
GLM-4.5-air, Groq llama 3.x small) misclassify ambiguous questions; the
parse-failure path silently falls back to `EXPLAIN`, masking the
misroute.

**Proposed fix**
Add 3-5 labeled examples per category (sql / ml / eda / explain /
small_talk) inside the system prompt. Keep the JSON output schema
unchanged so `_parse_router_json()` stays untouched.

**Acceptance**
- 25-question fixture (5 per category) classifies correctly ≥80% across
  Groq + Gemini providers when run live.
- Existing `tests/test_chat.py` (10 cases) stays green — fixture mock
  providers do not invoke the live router.

**Touches**
- `backend/app/services/agents/router.py` — prompt edit only.
- `backend/tests/test_agent_router.py` (new) — fixture-driven evaluation
  using a scripted provider that echoes the prompt back.

---

### Q5-AGENT-02 — SQL worker schema enrichment [P0]

**Root cause**
File: `backend/app/services/agents/workers/sql_worker.py:44-47`
`_column_schema()` exposes only `name (dtype)` to the LLM. With no
sample values, ranges, or distinct-count hints, the model invents string
literals and aggregates that don't match the data.

**Proposed fix**
Pull `min`, `max`, `unique_count`, and up to 3 `sample_values` per
column from `dataset.profile.columns[*]` (already populated by the
profiler). Render as a compact YAML-ish block in the SQL prompt. Cap
total schema length to ~1500 chars to fit free-tier context.

**Acceptance**
- 10 fixture questions ("how many X with Y > Z?") → ≥8 produce executable
  SQL on first try.
- Profile data is already cached on `Dataset.profile` — no extra DB
  queries.

**Touches**
- `backend/app/services/agents/workers/sql_worker.py` — `_column_schema`
  + prompt formatter.
- `backend/tests/test_chat.py` — extend fixture profile with
  `sample_values` so the schema renders.

---

### Q5-AGENT-03 — SQL worker self-correction retry [P1]

**Root cause**
File: `backend/app/services/agents/workers/sql_worker.py:96-103`
On `tool.execute(...)` failure the worker yields the error text and
returns. No retry, even though Polars SQL errors are usually
deterministic and easy for the LLM to fix once shown the message.

**Proposed fix**
Wrap tool execution in a 1-attempt retry: on first failure, send the
LLM `(original SQL, error message)` and ask for a corrected statement.
Cap at 1 retry to bound cost.

**Acceptance**
- Regression test: scripted provider returns malformed SQL on call 1,
  fixed SQL on call 2 → tool succeeds, summary streams normally,
  `tool_calls` audit shows both attempts.
- No retry on permission / dataset-not-found errors (those are not
  recoverable by re-prompting).

**Touches**
- `backend/app/services/agents/workers/sql_worker.py`.
- `backend/tests/test_chat.py` — new case for retry path.

---

### Q5-AGENT-04 — Explain worker grounded with profile [P1]

**Root cause**
File: `backend/app/services/agents/workers/explain_worker.py:10-21`
The worker accepts a `context` string but the chat endpoint currently
passes empty / minimal text. The LLM answers "why is salary high?"
without ever seeing the salary stats — pure freestyle, often wrong.

**Proposed fix**
Inside the chat endpoint's EXPLAIN branch (or the worker itself), load
the dataset and inject a profile snippet (per-column dtype + summary
stats, capped to top-N most-relevant columns based on simple keyword
overlap with the question). Pass that as the `context` param.

**Acceptance**
- Smoke test: ask "what's the average salary?" on a fixture dataset →
  the response cites the actual computed mean (within rounding) instead
  of inventing a number.
- No measurable latency regression vs current path (profile is already
  in memory on `Dataset.profile`).

**Touches**
- `backend/app/services/agents/workers/explain_worker.py` — accept
  optional `dataset_id` + `db`, build context internally.
- `backend/app/api/v1/chat.py` — wire the EXPLAIN branch.
- `backend/tests/test_chat.py` — assert mean appears in response.

---

## EDA

### Q5-EDA-01 — Datetime detection + time-series line chart [P1]

**Root cause**
Files: `backend/app/services/eda/profiler.py:16` (only checks
`dtype.is_numeric()`); `backend/app/api/v1/eda.py:67-82` (chart picker
has no temporal branch).
Datasets with date columns get bar charts (cardinality fails) or get
ignored — users lose the most natural EDA view.

**Proposed fix**
Profiler: add a `is_datetime` flag per column (Polars `Datetime` /
`Date` dtype, or string columns parseable by `pl.Series.str.to_datetime`
on a 50-row sample).
Chart picker: for each datetime column, emit a line chart of
`count(*) over period` where period = day if span < 90 days, week if
< 2 years, else month. If a numeric "value" column is paired with the
datetime, also emit `mean(value) over period` line.

**Acceptance**
- CSV with `date` + `value` columns produces a line ChartSpec in
  `/eda/{id}/charts`.
- Existing 4 EDA tests remain green; add 1 new test for datetime path.

**Touches**
- `backend/app/services/eda/profiler.py` — datetime detection.
- `backend/app/services/eda/chart_spec.py` — `line_spec` helper if not
  present.
- `backend/app/api/v1/eda.py` — picker branch.
- `backend/tests/test_eda.py` — fixture with date column.

---

### Q5-EDA-02 — Box plot helper + renderer [P2]

**Root cause**
File: `backend/app/services/eda/chart_spec.py`
No box-plot helper. Outliers are visible only as histogram tails, which
is awkward for skewed distributions.

**Proposed fix**
BE: add `boxplot_spec(col)` returning `{type: 'boxplot', q1, median, q3,
whisker_low, whisker_high, outliers[]}`. Auto-emit for numeric columns
with `|skew| > 1` (already in profile via Polars).
FE: extend `ChartSpec` discriminated union; add `renderBoxplot` in
`frontend/components/charts/adapters/recharts.tsx` (recharts has no
native boxplot — render with `BarChart` + custom segments, or fall
back to a static SVG).

**Acceptance**
- A dataset with a known skewed column emits 1 boxplot in
  `/eda/{id}/charts`.
- FE renders without errors; no `pnpm build` regression.

**Touches**
- `backend/app/services/eda/chart_spec.py`.
- `backend/app/api/v1/eda.py`.
- `frontend/lib/types.ts` (ChartSpec union).
- `frontend/components/charts/adapters/recharts.tsx`.
- `backend/tests/test_eda.py`.

---

### Q5-EDA-03 — Auto-scatter for top-correlated pairs [P2]

**Root cause**
File: `backend/app/services/eda/chart_spec.py:60-78`
`scatter_spec` exists but `backend/app/api/v1/eda.py` never calls it.
Heatmap shows correlations but doesn't drill into them.

**Proposed fix**
After computing the heatmap, sort pairs by `|corr|` and emit scatter
charts for the top 3 with `|corr| > 0.5`. Skip if heatmap absent
(< 2 numerics).

**Acceptance**
- Dataset with strong linear correlation produces ≥1 scatter ChartSpec.
- No regression on dataset with no strong correlations (just heatmap).

**Touches**
- `backend/app/api/v1/eda.py` — picker logic.
- `backend/tests/test_eda.py` — new fixture with correlated cols.

---

## ML

### Q5-ML-01 — Median/mode imputation [P0]

**Root cause**
File: `backend/app/api/v1/ml.py:49`
`fillna(0)` for numeric features destroys the distribution and biases
linear models. Trees handle it but accuracy still drops vs proper
imputation.

**Proposed fix**
Per-column strategy: median for numeric, mode for object/categorical.
Compute on the training fold only (not on full df, to avoid leakage).
Add optional `TrainRequest.imputation: 'median' | 'mean' | 'zero' = 'median'`.

**Acceptance**
- Fixture: 80-row regression dataset with 10% NaN injection. Trained
  model R² with `imputation='median'` ≥ R² with `imputation='zero'`.
- Existing 7 ML tests remain green (default behaviour change is
  acceptable; bump test fixtures if needed).
- `extras.imputed_columns` lists the columns + strategy used.

**Touches**
- `backend/app/api/v1/ml.py` — `_build_xy` helper.
- `backend/app/schemas/ml.py` — extend TrainRequest.
- `backend/tests/test_ml.py`.

---

### Q5-ML-02 — Auto-encode categorical features [P0]

**Root cause**
File: `backend/app/api/v1/ml.py:47-48`
Non-numeric columns are silently dropped before training. A CSV that's
mostly categorical (department, country, status) effectively trains on
nothing useful.

**Proposed fix**
Per-column rule:
- cardinality ≤ 20 → one-hot encode (Polars `to_dummies`).
- 20 < cardinality ≤ 200 → label encode.
- cardinality > 200 → drop, log to `extras.dropped_high_card`.

Log applied encodings to `extras.encoded_columns`.

**Acceptance**
- Fixture: classification dataset with 1 numeric + 2 categorical cols
  trains successfully and the leaderboard's `feature_importance` keys
  cover encoded categorical features.
- Test confirms `extras.encoded_columns` populated.

**Touches**
- `backend/app/api/v1/ml.py` — `_build_xy`.
- `backend/app/schemas/ml.py` — `TrainResponse.extras` typing.
- `backend/tests/test_ml.py` — new mixed-dtype fixture.

---

### Q5-ML-03 — 5-fold CV reporting [P1]

**Root cause**
File: `backend/app/services/ml/auto_train.py:29`
Single `train_test_split(test_size=0.2, random_state=42)`. Reported
metrics are optimistic and high-variance on small datasets.

**Proposed fix**
Run `cross_val_score` with k=5 (stratified for classification). Persist
`cv_mean` + `cv_std` on each `MlExperiment` row alongside test metrics.
Surface in leaderboard API response and the FE drawer.

**Acceptance**
- Each leaderboard entry exposes `cv_mean` + `cv_std`.
- FE drawer shows "5-fold CV: μ=0.87 ± 0.04" alongside test metric.

**Touches**
- `backend/app/services/ml/auto_train.py`.
- `backend/app/models/ml.py` (or `MlExperiment.metrics` JSON field if
  already flexible).
- `backend/app/schemas/ml.py` — `LeaderboardEntry` + `ExperimentOut`.
- `frontend/lib/types.ts` (mirror).
- `frontend/components/ml/ExperimentDrawer.tsx`.
- `backend/tests/test_ml.py`.

---

### Q5-ML-04 — Class imbalance handling + metric choice [P1]

**Root cause**
File: `backend/app/services/ml/auto_train.py:49-54`
Classification ranks by raw `accuracy`. On a 95/5 dataset accuracy=0.95
is achieved by predicting majority class always — useless.

**Proposed fix**
Detect imbalance in train endpoint: if `max_class_count / min_class_count
> 1.5`, set `extras.imbalanced = true` and recommend a non-accuracy
metric.
Add `TrainRequest.metric: 'accuracy' | 'f1_macro' | 'roc_auc' = 'accuracy'`.
Auto-train ranks by chosen metric.
FE: TrainForm exposes a metric radio group; the recommendation surfaces
as a hint when imbalance is detected on the dataset profile (cheap
client-side check from the column profile if the target's value_counts
are exposed).

**Acceptance**
- TrainRequest with `metric='f1_macro'` produces leaderboard ordered
  by F1.
- Imbalanced fixture (95/5) returns `extras.imbalanced=true`.

**Touches**
- `backend/app/services/ml/auto_train.py`.
- `backend/app/api/v1/ml.py`.
- `backend/app/schemas/ml.py`.
- `frontend/lib/types.ts`, `frontend/components/ml/TrainForm.tsx`.
- `backend/tests/test_ml.py`.

---

### Q5-ML-05 — Hyperparameter tuning [P2]

**Root cause**
All estimators use sklearn defaults. No grid / randomized search → easy
wins are left on the table.

**Proposed fix**
Per-estimator param distributions in
`backend/app/services/ml/estimators/*.py` (e.g., `n_estimators`,
`max_depth`, `learning_rate`). Use `RandomizedSearchCV` with `n_iter=5`,
`cv=3`. Gate behind `TrainRequest.tune: bool = False` so default path
stays fast.

**Acceptance**
- `tune=True` on a fixture takes longer but yields metric ≥ `tune=False`
  baseline on at least 2 of 3 estimators.
- Default `tune=False` path keeps current 33/33 → 43/43 timing within
  10% (so CI doesn't bog down).

**Touches**
- `backend/app/services/ml/estimators/*.py` — add `param_distributions`.
- `backend/app/services/ml/auto_train.py` — conditional search.
- `backend/app/schemas/ml.py`.
- `backend/tests/test_ml.py`.

---

## Out of scope

- **Vector RAG / embeddings for chat**: Sprint 4 already wired Gemini
  embeddings as a provider capability but no retrieval layer exists.
  Not part of Q5.
- **Streaming SQL execution**: Polars SQLContext is materialised; we
  stream the LLM summary, not the rows. Not Q5.
- **Active-learning loop / feedback collection**: would need a UI for
  the user to mark "good / bad" answers and a store. Big, out of Q5.
- **Replacing free-tier models with paid Claude / GPT-4**: that fixes
  *quality* but is an infra/billing decision, not a code task.
