"""FastAPI entry point."""

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.v1 import api_router
from app.config import settings
from app.utils.logger import configure_logging

configure_logging()
log = structlog.get_logger()

app = FastAPI(
    title="Ezidatic API",
    version=__version__,
    description="Extensible AI Data Analyst Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "version": __version__, "env": settings.app_env}


app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def on_startup() -> None:  # noqa: D401
    """Trigger registry imports (parsers, estimators, providers)."""
    from app.services import agents, ingestion, ml  # noqa: F401

    log.info("ezidatic.startup", env=settings.app_env, version=__version__)
