# 🧠 Ezidatic — Project Blueprint

> **An Extensible AI Data Analyst Platform**
> Student-friendly stack — free-tier optimized, multi-provider fallback, designed for easy extension toward a full SaaS.
> **Goal**: A web app that lets users upload datasets (CSV / Excel / JSON), auto-generate EDA, run AutoML, and chat with an AI Agent to analyze data.

---

## 📑 Table of Contents

1. [Architectural Philosophy](#1-architectural-philosophy)
2. [System Architecture Overview](#2-system-architecture-overview)
3. [Tech Stack Breakdown](#3-tech-stack-breakdown)
4. [Free-Tier & Fallback Strategy](#4-free-tier--fallback-strategy)
5. [Folder Structure](#5-folder-structure)
6. [Core Subsystems & Code Skeleton](#6-core-subsystems--code-skeleton)
7. [Database Schema](#7-database-schema)
8. [Config & Environment](#8-config--environment)
9. [Implementation Roadmap (4 Sprints)](#9-implementation-roadmap-4-sprints)
10. [Free-Tier Deployment](#10-free-tier-deployment)

---

## 1. Architectural Philosophy

To keep Ezidatic easy to extend (new file formats, new LLMs, multi-agent topologies), the codebase follows four principles:

| Principle | What it means in practice |
|-----------|--------------------------|
| **Decoupling** | UI ↔ API Gateway ↔ Business Logic ↔ AI Engine are strictly separated. Layers communicate through interfaces, never through concrete classes. |
| **Adapter Pattern** | LLMs, vector stores, and file storage all sit behind a common interface. Switching providers = changing one config line. |
| **Pipeline Architecture** | ETL, cleaning, and ML steps are chained nodes (Chain of Responsibility / DAG). Adding a step never requires touching core code. |
| **Config-driven** | No hard-coded model names, thresholds, or hyperparameters. Everything lives in `settings.py` or `.env`. |

**Why this matters for a student project**: When a reviewer asks *"Can you add XGBoost?"*, the answer is: write a class that inherits `BaseEstimator` and add one line to the registry. That kind of extensibility is a strong selling point.

---

## 2. System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js + TS)                       │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│  │ Upload  │  │   EDA    │  │  AutoML  │  │  Chat (stream) │   │
│  └─────────┘  └──────────┘  └──────────┘  └────────────────┘   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST + SSE/WebSocket
┌────────────────────────────▼─────────────────────────────────────┐
│                   API Gateway (FastAPI)                          │
│   /api/v1/datasets   /api/v1/ml   /api/v1/chat   /api/v1/eda     │
└──────┬──────────────────┬──────────────────┬─────────────────────┘
       │                  │                  │
┌──────▼──────┐   ┌───────▼───────┐  ┌───────▼────────┐
│  Ingestion  │   │  ML Pipeline  │  │  Agent System  │
│  Pipeline   │   │  (sklearn +   │  │  Router-Worker │
│  (Polars)   │   │   AutoML)     │  │  (LangChain)   │
└──────┬──────┘   └───────┬───────┘  └───────┬────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
┌──────▼──────┐   ┌───────▼───────┐   ┌──────▼──────┐
│ PostgreSQL  │   │  ChromaDB /   │   │  LLM Adapter│
│ (Supabase)  │   │  Supabase Vec │   │  Layer      │
└─────────────┘   └───────────────┘   └──────┬──────┘
                                             │
                          ┌──────────────────┼──────────────────┐
                          ▼                  ▼                  ▼
                   ┌──────────┐      ┌──────────┐      ┌──────────┐
                   │  Groq    │      │ Gemini   │      │ Ollama   │
                   │ (Primary)│      │(Fallback)│      │ (Local)  │
                   └──────────┘      └──────────┘      └──────────┘
```

---

## 3. Tech Stack Breakdown

### 3.1 Frontend (Client Layer)

| Layer | Tech | Why |
|-------|------|-----|
| Framework | **Next.js 14 (App Router) + TypeScript** | Built-in SSR, end-to-end type-safety |
| State | **Zustand** | Lighter than Redux, no boilerplate, perfect for chat session state |
| UI | **Shadcn UI + Tailwind CSS** | Headless components — theming changes never touch logic |
| Charts | **Recharts** (default) or **ECharts** (advanced) | Recharts is simple; ECharts handles complex visualizations |
| Forms | **React Hook Form + Zod** | Type-safe validation, mirrors backend Pydantic schemas |
| Data Fetching | **TanStack Query (React Query)** | Caching, retries, optimistic updates out of the box |
| Streaming | **Vercel AI SDK** (`ai` package) | Trivial LLM response streaming |

### 3.2 Backend (API & Core Service Layer)

| Layer | Tech | Why |
|-------|------|-----|
| Framework | **FastAPI** | Async-native, auto-generated OpenAPI, built-in DI |
| Data Processing | **Polars** (primary) + **Pandas** (compat) | Polars is 5–10x faster than Pandas; fall back to Pandas only when an ML library demands it |
| ORM | **SQLAlchemy 2.0 (async)** + **Alembic** | Version-controlled migrations, async-first |
| Validation | **Pydantic v2** | Schema validation; shared with frontend through OpenAPI |
| Background Jobs | **Celery + Redis** or **FastAPI BackgroundTasks** | Start with BackgroundTasks; upgrade to Celery when concurrency demands it |
| Testing | **Pytest + httpx** | Async test client, easy mocking |

### 3.3 AI & Data Layer

| Layer | Tech | Why |
|-------|------|-----|
| Orchestration | **LangChain** (Python) | Wide ecosystem, many ready-made tools |
| LLM Providers | **Groq** (free + fast) → **Gemini** (free) → **OpenRouter** (free models) → **Ollama** (local) | Multi-provider through an adapter |
| Embeddings | **Gemini `text-embedding-004`** (free, 1500 RPD) or **`sentence-transformers`** (local) | Free + offline option |
| Vector Store | **ChromaDB** (local, free) or **Supabase pgvector** (free 500 MB) | Start with Chroma, migrate to Supabase on deploy |
| ML | **scikit-learn + LightGBM** | Covers ~99% of tabular use cases |
| AutoML | **FLAML** or a custom registry | FLAML is lighter than AutoGluon and free |

---

## 4. Free-Tier & Fallback Strategy

> **Philosophy**: Never depend on a single provider. When one runs out of quota, automatically switch to the next.

### 4.1 LLM Provider Comparison

| Provider | Free Tier | Speed | Recommended Models | Use Case |
|----------|-----------|-------|--------------------|----------|
| **Groq** | ~14,400 RPD, generous rate limits | ⚡ Very fast (500+ tok/s) | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant` | **Primary** — chat, router |
| **Google Gemini** | 1500 RPD (Flash), 50 RPD (Pro) | Fast | `gemini-2.0-flash`, `gemini-1.5-flash` | **Fallback 1** — multimodal, embeddings |
| **OpenRouter** | Free models (Llama, Mistral, DeepSeek) | Medium | `meta-llama/llama-3.3-70b-instruct:free`, `deepseek/deepseek-chat:free` | **Fallback 2** — model variety |
| **Ollama** | Local (your CPU/GPU) | Depends on hardware | `llama3.2:3b`, `qwen2.5:7b` | **Offline mode** — academic demos, no internet |
| **Hugging Face Inference** | Limited free tier | Slow | Embedding models | Embedding backup |

> **Note**: Free-tier limits change frequently — always confirm current quotas on each provider's pricing page before you commit.

### 4.2 Fallback Logic (pseudo-code)

```python
PROVIDER_PRIORITY = ["groq", "gemini", "openrouter", "ollama"]

async def llm_call(prompt: str, **kwargs):
    last_error = None
    for provider_name in PROVIDER_PRIORITY:
        try:
            provider = LLMRegistry.get(provider_name)
            if not provider.is_available():  # check API key + rate limit
                continue
            return await provider.invoke(prompt, **kwargs)
        except RateLimitError as e:
            last_error = e
            continue
        except Exception as e:
            logger.warning(f"{provider_name} failed: {e}")
            last_error = e
            continue
    raise AllProvidersFailedError(last_error)
```

### 4.3 Database & Storage Free Tiers

| Service | Free Tier | Purpose |
|---------|-----------|---------|
| **Supabase** | 500 MB Postgres + 1 GB Storage + pgvector | Primary DB + file storage + vectors |
| **Neon** | 0.5 GB Postgres (serverless) | Backup if Supabase fills up |
| **Upstash Redis** | 10K commands/day | Cache, rate limit, session |
| **Cloudflare R2** | 10 GB storage | Hosting large CSVs when Supabase Storage is exhausted |

---

## 5. Folder Structure

```
ezidatic/
├── frontend/                          # Next.js app
│   ├── app/
│   │   ├── (auth)/login/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── datasets/page.tsx
│   │   │   ├── eda/[id]/page.tsx
│   │   │   ├── ml/[id]/page.tsx
│   │   │   └── chat/[sessionId]/page.tsx
│   │   ├── api/                       # API routes (proxy if needed)
│   │   └── layout.tsx
│   ├── components/
│   │   ├── ui/                        # shadcn components
│   │   ├── charts/
│   │   │   ├── ChartRenderer.tsx      # consumes JSON spec → renders
│   │   │   └── adapters/
│   │   │       ├── recharts.ts
│   │   │       └── echarts.ts
│   │   ├── chat/
│   │   │   ├── MessageList.tsx
│   │   │   └── StreamingMessage.tsx
│   │   └── upload/Dropzone.tsx
│   ├── lib/
│   │   ├── api-client.ts              # typed fetch wrapper
│   │   ├── types.ts                   # types shared with backend
│   │   └── stores/
│   │       ├── chatStore.ts           # Zustand
│   │       └── datasetStore.ts
│   ├── package.json
│   └── tsconfig.json
│
├── backend/                           # FastAPI app
│   ├── app/
│   │   ├── main.py                    # entry point
│   │   ├── config.py                  # Pydantic Settings
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── datasets.py        # /api/v1/datasets
│   │   │       ├── eda.py
│   │   │       ├── ml.py
│   │   │       └── chat.py
│   │   ├── core/
│   │   │   ├── database.py            # SQLAlchemy session
│   │   │   ├── security.py            # JWT, hashing
│   │   │   └── deps.py                # FastAPI dependencies
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── dataset.py
│   │   │   └── chat.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── dataset.py
│   │   │   └── chat.py
│   │   ├── services/
│   │   │   ├── ingestion/
│   │   │   │   ├── base.py            # DataParser interface
│   │   │   │   ├── csv_parser.py
│   │   │   │   ├── excel_parser.py
│   │   │   │   └── json_parser.py
│   │   │   ├── preprocessing/
│   │   │   │   ├── pipeline.py        # DataPipeline + DAG
│   │   │   │   └── steps/
│   │   │   │       ├── base.py        # BaseStep
│   │   │   │       ├── handle_missing.py
│   │   │   │       ├── remove_outliers.py
│   │   │   │       └── encode_categorical.py
│   │   │   ├── eda/
│   │   │   │   ├── profiler.py        # statistics
│   │   │   │   └── chart_spec.py      # JSON spec generator
│   │   │   ├── ml/
│   │   │   │   ├── base_estimator.py
│   │   │   │   ├── factory.py         # ModelFactory
│   │   │   │   ├── auto_train.py      # iterates over registry
│   │   │   │   └── estimators/
│   │   │   │       ├── lightgbm_clf.py
│   │   │   │       ├── random_forest.py
│   │   │   │       └── logistic_reg.py
│   │   │   └── agents/
│   │   │       ├── llm_adapter.py     # multi-provider adapter
│   │   │       ├── providers/
│   │   │       │   ├── base.py        # LLMProvider interface
│   │   │       │   ├── groq.py
│   │   │       │   ├── gemini.py
│   │   │       │   ├── openrouter.py
│   │   │       │   └── ollama.py
│   │   │       ├── router.py          # query classifier
│   │   │       ├── workers/
│   │   │       │   ├── sql_worker.py
│   │   │       │   ├── ml_worker.py
│   │   │       │   └── explain_worker.py
│   │   │       └── tools/
│   │   │           ├── base.py        # BaseTool
│   │   │           ├── registry.py    # Tool Registry
│   │   │           ├── query_dataset.py
│   │   │           └── plot_chart.py
│   │   └── utils/
│   │       ├── logger.py
│   │       └── exceptions.py
│   ├── alembic/                       # migrations
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_ingestion.py
│   │   └── test_agents.py
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docker-compose.yml                 # dev env: postgres, redis, chroma
├── .env.example
├── README.md
└── docs/
    ├── ARCHITECTURE.md
    └── API.md
```

---

## 6. Core Subsystems & Code Skeleton

### 🧩 Module 1 — Ingestion & Storage

**Goal**: Plug in new formats (Excel, JSON, Parquet, SQL) by writing a single class.

**`backend/app/services/ingestion/base.py`**

```python
from abc import ABC, abstractmethod
from pathlib import Path
import polars as pl

class DataParser(ABC):
    """Interface for any file parser."""

    extensions: list[str] = []  # e.g. [".csv"]

    @abstractmethod
    async def parse(self, file_path: Path) -> pl.DataFrame:
        """Read a file and return a DataFrame."""
        ...

    @abstractmethod
    def profile(self, df: pl.DataFrame) -> dict:
        """Build metadata: row_count, columns, dtypes, null_count, ..."""
        ...


class ParserRegistry:
    _registry: dict[str, type[DataParser]] = {}

    @classmethod
    def register(cls, parser_cls: type[DataParser]):
        for ext in parser_cls.extensions:
            cls._registry[ext.lower()] = parser_cls
        return parser_cls

    @classmethod
    def get_parser(cls, file_path: Path) -> DataParser:
        ext = file_path.suffix.lower()
        if ext not in cls._registry:
            raise ValueError(f"Unsupported file format: {ext}")
        return cls._registry[ext]()
```

**`backend/app/services/ingestion/csv_parser.py`**

```python
import polars as pl
from pathlib import Path
from .base import DataParser, ParserRegistry

@ParserRegistry.register
class CsvParser(DataParser):
    extensions = [".csv", ".tsv"]

    async def parse(self, file_path: Path) -> pl.DataFrame:
        sep = "\t" if file_path.suffix == ".tsv" else ","
        return pl.read_csv(file_path, separator=sep, infer_schema_length=10_000)

    def profile(self, df: pl.DataFrame) -> dict:
        return {
            "row_count": df.height,
            "column_count": df.width,
            "columns": [
                {
                    "name": col,
                    "dtype": str(df[col].dtype),
                    "null_count": df[col].null_count(),
                    "unique_count": df[col].n_unique(),
                }
                for col in df.columns
            ],
        }
```

**Adding Excel later**: Create `excel_parser.py` with `extensions = [".xlsx", ".xls"]` and use `pl.read_excel()`. Zero changes elsewhere.

---

### 🧩 Module 2 — Preprocessing Pipeline

**`backend/app/services/preprocessing/steps/base.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
import polars as pl

@dataclass
class StepResult:
    df: pl.DataFrame
    log: dict  # records changes (for audit + undo)


class BaseStep(ABC):
    name: str

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def apply(self, df: pl.DataFrame) -> StepResult:
        ...


class Pipeline:
    """Chain of Responsibility — runs steps sequentially."""

    def __init__(self, steps: list[BaseStep]):
        self.steps = steps

    def run(self, df: pl.DataFrame) -> tuple[pl.DataFrame, list[dict]]:
        logs = []
        current = df
        for step in self.steps:
            result = step.apply(current)
            current = result.df
            logs.append({"step": step.name, **result.log})
        return current, logs
```

**`backend/app/services/preprocessing/steps/handle_missing.py`**

```python
import polars as pl
from .base import BaseStep, StepResult

class HandleMissingValues(BaseStep):
    name = "handle_missing"

    def apply(self, df: pl.DataFrame) -> StepResult:
        strategy = self.params.get("strategy", "mean")  # mean | median | drop | fill
        affected = []
        for col in df.columns:
            if df[col].null_count() == 0:
                continue
            if df[col].dtype.is_numeric():
                fill_value = df[col].mean() if strategy == "mean" else df[col].median()
                df = df.with_columns(pl.col(col).fill_null(fill_value))
                affected.append({"column": col, "fill": float(fill_value)})
            else:
                df = df.with_columns(pl.col(col).fill_null("Unknown"))
                affected.append({"column": col, "fill": "Unknown"})
        return StepResult(df=df, log={"affected": affected})
```

**Usage**:

```python
pipeline = Pipeline([
    HandleMissingValues(strategy="median"),
    RemoveOutliers(method="iqr", threshold=1.5),
    EncodeCategorical(method="onehot"),
])
clean_df, logs = pipeline.run(raw_df)
# Persist logs to pipeline_logs → full audit trail
```

---

### 🧩 Module 3 — EDA & Chart Spec

**Philosophy**: The backend returns a JSON spec; the frontend renders it. Switching chart libraries means swapping an adapter.

**`backend/app/services/eda/chart_spec.py`**

```python
from pydantic import BaseModel
from typing import Literal
import numpy as np

class ChartSpec(BaseModel):
    """Standardized, frontend-agnostic JSON spec."""
    type: Literal["bar", "line", "scatter", "histogram", "heatmap", "pie"]
    title: str
    x_axis: dict  # {"key": "month", "label": "Month", "type": "category"}
    y_axis: dict
    series: list[dict]  # [{"name": "revenue", "data": [...]}]
    metadata: dict = {}  # chart-specific options


def histogram_spec(df, column: str, bins: int = 30) -> ChartSpec:
    counts, edges = np.histogram(df[column].drop_nulls(), bins=bins)
    return ChartSpec(
        type="histogram",
        title=f"Distribution of {column}",
        x_axis={"key": "bin", "label": column, "type": "numeric"},
        y_axis={"key": "count", "label": "Frequency", "type": "numeric"},
        series=[{
            "name": column,
            "data": [{"bin": float(edges[i]), "count": int(counts[i])} for i in range(bins)]
        }],
    )
```

**Frontend `ChartRenderer.tsx`** (Recharts adapter):

```tsx
import { BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";

interface ChartSpec {
  type: string;
  title: string;
  x_axis: { key: string; label: string };
  y_axis: { key: string; label: string };
  series: { name: string; data: any[] }[];
}

export function ChartRenderer({ spec }: { spec: ChartSpec }) {
  if (spec.type === "histogram" || spec.type === "bar") {
    return (
      <BarChart width={600} height={300} data={spec.series[0].data}>
        <XAxis dataKey={spec.x_axis.key} />
        <YAxis />
        <Tooltip />
        <Bar dataKey={spec.y_axis.key} fill="#3b82f6" />
      </BarChart>
    );
  }
  // ... other chart types
}
```

---

### 🧩 Module 4 — AutoML Engine

**`backend/app/services/ml/base_estimator.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class TrainResult:
    model: object
    metrics: dict   # {"accuracy": 0.92, "f1": 0.89, ...}
    feature_importance: dict | None = None
    train_time_sec: float = 0.0


class BaseEstimator(ABC):
    name: str
    task: str  # "classification" | "regression"

    def __init__(self, **hyperparams):
        self.hyperparams = hyperparams

    @abstractmethod
    def fit(self, X_train, y_train, X_val, y_val) -> TrainResult:
        ...


class ModelRegistry:
    _registry: dict[str, type[BaseEstimator]] = {}

    @classmethod
    def register(cls, estimator_cls: type[BaseEstimator]):
        cls._registry[estimator_cls.name] = estimator_cls
        return estimator_cls

    @classmethod
    def list_for_task(cls, task: str) -> list[type[BaseEstimator]]:
        return [c for c in cls._registry.values() if c.task == task]
```

**`backend/app/services/ml/estimators/lightgbm_clf.py`**

```python
import time
from lightgbm import LGBMClassifier
from sklearn.metrics import accuracy_score, f1_score
from ..base_estimator import BaseEstimator, TrainResult, ModelRegistry

@ModelRegistry.register
class LightGBMClassifier(BaseEstimator):
    name = "lightgbm_classifier"
    task = "classification"

    def fit(self, X_train, y_train, X_val, y_val) -> TrainResult:
        t0 = time.time()
        model = LGBMClassifier(**self.hyperparams)
        model.fit(X_train, y_train)
        preds = model.predict(X_val)
        return TrainResult(
            model=model,
            metrics={
                "accuracy": accuracy_score(y_val, preds),
                "f1_macro": f1_score(y_val, preds, average="macro"),
            },
            feature_importance=dict(zip(X_train.columns, model.feature_importances_)),
            train_time_sec=time.time() - t0,
        )
```

**`backend/app/services/ml/auto_train.py`**

```python
async def auto_train(X, y, task: str = "classification"):
    """Iterate over every registered estimator and rank them."""
    from sklearn.model_selection import train_test_split
    X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    results = []
    for EstimatorCls in ModelRegistry.list_for_task(task):
        estimator = EstimatorCls()  # default hyperparams
        try:
            result = estimator.fit(X_tr, y_tr, X_val, y_val)
            results.append({"name": EstimatorCls.name, **result.metrics, "time": result.train_time_sec})
        except Exception as e:
            logger.error(f"{EstimatorCls.name} failed: {e}")

    primary_metric = "accuracy" if task == "classification" else "r2"
    return sorted(results, key=lambda r: r[primary_metric], reverse=True)
```

---

### 🧩 Module 5 — Agentic Chat (Router-Worker)

**`backend/app/services/agents/providers/base.py`**

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class LLMProvider(ABC):
    name: str
    priority: int = 100  # lower number = higher priority

    @abstractmethod
    async def is_available(self) -> bool:
        """Check API key + cached rate limits."""
        ...

    @abstractmethod
    async def invoke(self, messages: list[dict], **kwargs) -> str:
        ...

    @abstractmethod
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        ...
```

**`backend/app/services/agents/providers/groq.py`**

```python
import os
from groq import AsyncGroq
from .base import LLMProvider

class GroqProvider(LLMProvider):
    name = "groq"
    priority = 1

    def __init__(self):
        self.client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    async def is_available(self) -> bool:
        return bool(os.getenv("GROQ_API_KEY"))

    async def invoke(self, messages: list[dict], **kwargs) -> str:
        resp = await self.client.chat.completions.create(
            model=self.model, messages=messages, **kwargs
        )
        return resp.choices[0].message.content

    async def stream(self, messages, **kwargs):
        stream = await self.client.chat.completions.create(
            model=self.model, messages=messages, stream=True, **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
```

**`backend/app/services/agents/llm_adapter.py`**

```python
from .providers.base import LLMProvider
from .providers.groq import GroqProvider
from .providers.gemini import GeminiProvider
from .providers.openrouter import OpenRouterProvider
from .providers.ollama import OllamaProvider

class LLMAdapter:
    """Multi-provider with automatic fallback."""

    def __init__(self):
        self.providers: list[LLMProvider] = sorted(
            [GroqProvider(), GeminiProvider(), OpenRouterProvider(), OllamaProvider()],
            key=lambda p: p.priority,
        )

    async def invoke(self, messages, **kwargs):
        last_error = None
        for provider in self.providers:
            if not await provider.is_available():
                continue
            try:
                return await provider.invoke(messages, **kwargs)
            except Exception as e:
                logger.warning(f"{provider.name} failed: {e}")
                last_error = e
        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def stream(self, messages, **kwargs):
        for provider in self.providers:
            if not await provider.is_available():
                continue
            try:
                async for chunk in provider.stream(messages, **kwargs):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"{provider.name} stream failed: {e}")
        raise RuntimeError("All providers failed")
```

**`backend/app/services/agents/router.py`**

```python
import json
from enum import Enum

class QueryType(str, Enum):
    SQL = "sql"           # "How many users purchased in May?"
    ML = "ml"             # "Train a model to predict churn"
    EDA = "eda"           # "Show me a histogram of the age column"
    EXPLAIN = "explain"   # "Why did the model predict this?"
    SMALL_TALK = "small_talk"


ROUTER_PROMPT = """You are a router that classifies user questions about a dataset.
Return JSON: {{"type": "sql|ml|eda|explain|small_talk", "reason": "..."}}

Question: {question}
"""

async def route(question: str, llm: LLMAdapter) -> QueryType:
    """Use a lightweight LLM (Llama 3.1 8B on Groq) for classification — extremely cheap."""
    response = await llm.invoke(
        messages=[{"role": "user", "content": ROUTER_PROMPT.format(question=question)}],
        model_override="llama-3.1-8b-instant",  # fast + light
        response_format={"type": "json_object"},
    )
    parsed = json.loads(response)
    return QueryType(parsed["type"])
```

**`backend/app/services/agents/tools/base.py`** & **`registry.py`**

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class BaseTool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel]

    @abstractmethod
    async def execute(self, **kwargs) -> dict:
        ...

    def to_openai_function(self) -> dict:
        """Convert to the OpenAI function-calling format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.args_schema.model_json_schema(),
        }


class ToolRegistry:
    _tools: dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool):
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> BaseTool:
        return cls._tools[name]

    @classmethod
    def all_schemas(cls) -> list[dict]:
        return [t.to_openai_function() for t in cls._tools.values()]
```

**Worker using tools** — example `sql_worker`:

```python
async def sql_worker(question: str, dataset_id: str, llm: LLMAdapter):
    # 1. Fetch the dataset schema from the DB (column metadata)
    schema = await get_dataset_schema(dataset_id)

    # 2. Ask the LLM to generate a SQL/Polars query
    messages = [
        {"role": "system", "content": f"Schema: {schema}. Return a Polars expression."},
        {"role": "user", "content": question},
    ]
    code = await llm.invoke(messages)

    # 3. Execute inside a sandbox (RestrictedPython or subprocess)
    result = await safe_execute(code, dataset_id)
    return result
```

---

## 7. Database Schema

> **Notes**: UUIDs everywhere, JSONB for flexible metadata, multi-tenant ready from day one.

```sql
-- Users
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       TEXT UNIQUE NOT NULL,
    password_hash TEXT,                    -- nullable for OAuth users
    role        TEXT DEFAULT 'user',       -- user | admin
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Workspaces (for future multi-tenant support)
CREATE TABLE workspaces (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Datasets
CREATE TABLE datasets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    original_name   TEXT NOT NULL,
    storage_path    TEXT NOT NULL,         -- e.g. supabase://bucket/path
    file_size       BIGINT,
    file_format     TEXT,                  -- csv, xlsx, json
    status          TEXT DEFAULT 'pending', -- pending | ready | failed
    row_count       INTEGER,
    column_count    INTEGER,
    profile         JSONB,                 -- nullable, extra metadata
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_datasets_workspace ON datasets(workspace_id);

-- Column metadata (separated → fast metadata queries without loading the file)
CREATE TABLE dataset_columns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id      UUID REFERENCES datasets(id) ON DELETE CASCADE,
    column_name     TEXT NOT NULL,
    data_type       TEXT NOT NULL,         -- int64, float64, string, bool, date
    is_nullable     BOOLEAN DEFAULT TRUE,
    null_count      INTEGER,
    unique_count    INTEGER,
    sample_values   JSONB,                 -- top 5 sample values
    stats           JSONB                  -- min, max, mean, std for numerics
);

-- Pipeline logs (audit trail + undo)
CREATE TABLE pipeline_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id      UUID REFERENCES datasets(id) ON DELETE CASCADE,
    step_name       TEXT NOT NULL,
    step_order      INTEGER NOT NULL,
    applied_changes JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ML experiments
CREATE TABLE ml_experiments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id      UUID REFERENCES datasets(id) ON DELETE CASCADE,
    target_column   TEXT NOT NULL,
    task_type       TEXT NOT NULL,         -- classification | regression
    model_type      TEXT NOT NULL,         -- lightgbm_classifier, ...
    metrics         JSONB,
    hyperparams     JSONB,
    artifact_path   TEXT,                  -- pickled model path
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Chat sessions
CREATE TABLE chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    dataset_id      UUID REFERENCES datasets(id) ON DELETE SET NULL,
    title           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role            TEXT NOT NULL,         -- user | assistant | tool
    content         TEXT,
    tool_calls      JSONB,
    token_usage     JSONB,                 -- {"prompt": 100, "completion": 50}
    provider_used   TEXT,                  -- groq | gemini | ...
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);
```

---

## 8. Config & Environment

**`.env.example`**

```bash
# === App ===
APP_ENV=development
APP_PORT=8000
SECRET_KEY=change-this-to-a-random-string

# === Database (Supabase free tier) ===
DATABASE_URL=postgresql+asyncpg://postgres:[password]@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_BUCKET=datasets

# === Redis (Upstash free) ===
REDIS_URL=redis://default:xxx@xxx.upstash.io:6379

# === LLM Providers (priority order) ===
# 1. Groq — primary
GROQ_API_KEY=gsk_xxx
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_ROUTER_MODEL=llama-3.1-8b-instant

# 2. Gemini — fallback + embeddings
GEMINI_API_KEY=AIza_xxx
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBED_MODEL=text-embedding-004

# 3. OpenRouter — secondary fallback
OPENROUTER_API_KEY=sk-or-xxx
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# 4. Ollama — local fallback
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b

# === Vector Store ===
VECTOR_BACKEND=chroma         # chroma | supabase
CHROMA_PERSIST_DIR=./data/chroma

# === Storage ===
STORAGE_BACKEND=supabase      # supabase | local
LOCAL_STORAGE_DIR=./data/uploads
MAX_FILE_SIZE_MB=50
```

**`backend/app/config.py`**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str
    database_url: str

    # LLM
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    gemini_api_key: str | None = None
    openrouter_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # Storage
    storage_backend: str = "local"
    max_file_size_mb: int = 50

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 9. Implementation Roadmap (4 Sprints)

| Sprint | Weeks | Goal | Deliverable |
|--------|-------|------|-------------|
| **1** | 1–2 | Foundation | Auth, CSV upload, metadata storage, basic profile |
| **2** | 3–4 | EDA + Pipeline | Chart-spec API, preprocessing pipeline, frontend chart rendering |
| **3** | 5–6 | AutoML | Model registry, auto-training of 3–4 algorithms, leaderboard UI |
| **4** | 7–8 | Agentic Chat | LLM adapter + fallback, router-worker, tool calling, streaming |
| *Polish* | 9 | Demo + report | Free-tier deploy, write the report, build slides |

**Sprint 1 in detail** (so you don't get overwhelmed):

- [ ] Set up the monorepo (frontend + backend)
- [ ] Docker Compose for `postgres` + `redis`
- [ ] FastAPI: `/datasets` POST upload + GET list
- [ ] Implement `CsvParser` + `ParserRegistry`
- [ ] Next.js upload page with a dropzone
- [ ] Push files to Supabase Storage
- [ ] Render the list of uploaded datasets

---

## 10. Free-Tier Deployment

| Service | Free Tier | Role |
|---------|-----------|------|
| **Vercel** | Hobby plan, unlimited | Frontend (Next.js) |
| **Render** | 750 h/month | Backend (FastAPI) — sleeps after 15 min idle |
| **Fly.io** | 3 small VMs | Backend alternative — no sleep |
| **Supabase** | 500 MB DB + 1 GB storage | Postgres + file storage + auth |
| **Upstash** | 10K Redis cmd/day | Cache + rate limit |
| **Hugging Face Spaces** | Free CPU/GPU | Backup deploy + demo |

**Tips for students**:
- **Render** sleeps after idle → the first user waits ~30 s. Fix it with a cron ping every 10 minutes (UptimeRobot is free).
- **Supabase free** caps at 500 MB → compress datasets, or move large files to Cloudflare R2 (10 GB free).
- If LLM calls explode → cache responses in Redis with a key of `hash(prompt + dataset_id)`.

---

## 🎯 Defense Checklist — "Bonus Points"

When defending Ezidatic to a review panel, emphasize:

- ✅ **Adapter Pattern**: Demo a provider switch by commenting one env line — the app keeps working.
- ✅ **Plug-in Pipeline**: Show how to add a new cleaning step in ~30 lines.
- ✅ **Multi-Provider Fallback**: Disable the Groq key live → app gracefully falls back to Gemini.
- ✅ **End-to-End Type Safety**: Pydantic on the backend → OpenAPI → TypeScript on the frontend.
- ✅ **Audit Trail**: Every data transformation is logged in `pipeline_logs` → reversible.
- ✅ **Multi-Tenant Ready**: Even though demo is single-user, the schema already carries `workspace_id` → zero-effort scaling.

---

## 📚 Recommended Reading

- **FastAPI**: https://fastapi.tiangolo.com/tutorial/
- **Polars**: https://docs.pola.rs/user-guide/
- **LangChain**: https://python.langchain.com/docs/get_started/introduction
- **Groq Console**: https://console.groq.com/
- **Supabase Python**: https://supabase.com/docs/reference/python/introduction
- **Shadcn UI**: https://ui.shadcn.com/

---

> **Final word**: Don't try to ship every module at once. Build a vertical slice first (one end-to-end flow: upload → profile → one chart), then expand. Once the spine is in place — adapters, registries, pipeline — every new feature snaps in with almost no friction.
