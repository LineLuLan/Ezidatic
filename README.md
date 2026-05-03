<div align="center">

# 🧠 Ezidatic

**An Extensible AI Data Analyst Platform**

Upload a dataset. Get instant EDA, AutoML, and an AI agent that talks to your data.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Roadmap](#-roadmap) · [Contributing](#-contributing)

</div>

---

## ✨ Features

- 📂 **Multi-format ingestion** — CSV, TSV today; Excel, JSON, Parquet via pluggable parsers
- 🔍 **Auto EDA** — instant profiling, distributions, correlations, outlier detection
- 🧹 **Composable preprocessing** — chain of pluggable cleaning steps with full audit trail
- 🤖 **AutoML engine** — auto-train and rank multiple algorithms (LightGBM, Random Forest, Logistic Regression, ...)
- 💬 **Agentic chat** — Router-Worker LLM topology that picks the right specialist agent for each question
- 🔌 **Multi-provider LLM** — Groq → Gemini → OpenRouter → Ollama with automatic fallback
- 🧱 **Extensible by design** — Adapter Pattern, Pipeline Architecture, plug-in registries everywhere

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js + TS)                       │
│      Upload  ·  EDA  ·  AutoML  ·  Chat (streaming)              │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST + SSE
┌────────────────────────────▼─────────────────────────────────────┐
│                   API Gateway (FastAPI)                          │
└──────┬──────────────────┬──────────────────┬─────────────────────┘
       │                  │                  │
┌──────▼──────┐   ┌───────▼───────┐  ┌───────▼────────┐
│  Ingestion  │   │  ML Pipeline  │  │  Agent System  │
│   (Polars)  │   │   (sklearn)   │  │  Router-Worker │
└──────┬──────┘   └───────┬───────┘  └───────┬────────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
       ┌──────────────────┼──────────────────┐
       ▼                  ▼                  ▼
┌─────────────┐   ┌───────────────┐   ┌──────────────┐
│ PostgreSQL  │   │  Vector Store │   │ LLM Adapter  │
│ (Supabase)  │   │   (Chroma)    │   │ (multi-prov) │
└─────────────┘   └───────────────┘   └──────────────┘
```

Full architectural notes live in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 🛠 Tech Stack

| Layer | Tech |
|-------|------|
| **Frontend** | Next.js 14 · TypeScript · Tailwind · Shadcn UI · Zustand · TanStack Query · Recharts |
| **Backend** | FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 · Alembic |
| **Data** | Polars · Pandas · scikit-learn · LightGBM |
| **AI** | LangChain · Groq · Gemini · OpenRouter · Ollama |
| **Storage** | PostgreSQL (Supabase) · ChromaDB · Redis (Upstash) |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 20+** and **pnpm** (or `npm`/`yarn`)
- **PostgreSQL 15+** (local install or [Supabase](https://supabase.com/) free tier)
- **Redis** (optional, but recommended — [Upstash](https://upstash.com/) free tier works)
- API keys (at least one): [Groq](https://console.groq.com/), [Google AI Studio](https://aistudio.google.com/), or [OpenRouter](https://openrouter.ai/)

### 1. Clone & install

```bash
git clone https://github.com/<your-username>/ezidatic.git
cd ezidatic
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then fill in your keys
alembic upgrade head               # run migrations
uvicorn app.main:app --reload      # http://localhost:8000
```

API docs auto-generated at `http://localhost:8000/docs`.

### 3. Frontend setup

```bash
cd frontend
pnpm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm dev                           # http://localhost:3000
```

### 4. Optional — Local LLM with Ollama

If you want fully offline development:

```bash
# install from https://ollama.com/
ollama pull llama3.2:3b
ollama serve
```

Then set `OLLAMA_BASE_URL=http://localhost:11434` in `backend/.env`.

---

## 🔑 Environment Variables

The backend reads from `backend/.env`. Key variables:

```bash
# App
SECRET_KEY=change-me
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/ezidatic

# LLM Providers (priority order — set the ones you have)
GROQ_API_KEY=gsk_xxx
GEMINI_API_KEY=AIza_xxx
OPENROUTER_API_KEY=sk-or-xxx
OLLAMA_BASE_URL=http://localhost:11434

# Storage
STORAGE_BACKEND=local              # or 'supabase'
MAX_FILE_SIZE_MB=50
```

See `backend/.env.example` for the full list.

---

## 📁 Project Structure

```
ezidatic/
├── frontend/                # Next.js + TypeScript
│   ├── app/                 # App Router pages
│   ├── components/          # UI, charts, chat
│   └── lib/                 # API client, stores (Zustand)
│
├── backend/                 # FastAPI
│   ├── app/
│   │   ├── api/v1/          # REST endpoints
│   │   ├── services/        # Business logic
│   │   │   ├── ingestion/   # File parsers (plug-in registry)
│   │   │   ├── preprocessing/  # Pipeline steps
│   │   │   ├── eda/         # Profiling + chart specs
│   │   │   ├── ml/          # AutoML registry
│   │   │   └── agents/      # LLM adapter, router, workers, tools
│   │   └── models/          # SQLAlchemy models
│   ├── alembic/             # DB migrations
│   └── tests/
│
└── docs/                    # Architecture & API documentation
```

---

## 🧩 Extending Ezidatic

The project is built around plug-in registries. Adding new capabilities is intentionally trivial.

### Add a new file format

```python
# backend/app/services/ingestion/parquet_parser.py
@ParserRegistry.register
class ParquetParser(DataParser):
    extensions = [".parquet"]

    async def parse(self, file_path):
        return pl.read_parquet(file_path)

    def profile(self, df):
        ...
```

That's it — the upload endpoint picks it up automatically.

### Add a new ML algorithm

```python
# backend/app/services/ml/estimators/xgboost_clf.py
@ModelRegistry.register
class XGBoostClassifier(BaseEstimator):
    name = "xgboost_classifier"
    task = "classification"

    def fit(self, X_train, y_train, X_val, y_val):
        ...
```

The auto-trainer iterates the registry — no other changes required.

### Add a new LLM provider

Implement the `LLMProvider` interface in `backend/app/services/agents/providers/`, register it in `LLMAdapter`, and you're done.

---

## 🗺 Roadmap

- [x] Sprint 1 — Auth, CSV upload, dataset profiling
- [ ] Sprint 2 — Preprocessing pipeline + EDA charts
- [ ] Sprint 3 — AutoML with leaderboard
- [ ] Sprint 4 — Agentic chat with Router-Worker
- [ ] Polish — Free-tier deployment + report

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full blueprint.

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
pnpm test
```

---

## 🤝 Contributing

Pull requests welcome. For major changes, open an issue first to discuss what you'd like to change.

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit using [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, ...)
4. Push and open a PR

---

## 📜 License

MIT — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgements

- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Polars](https://pola.rs/) for blazing-fast DataFrames
- [Groq](https://groq.com/) for free, fast LLM inference
- [Shadcn UI](https://ui.shadcn.com/) for beautiful headless components
- All the open-source contributors who make student projects like this possible

---

<div align="center">

**Built with ☕ and curiosity.**

</div>