"""FastAPI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1 import api_router
from app.config import settings
from app.core.exceptions import AppException
from app.utils.logger import configure_logging

configure_logging()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Trigger registry imports (parsers, estimators, providers) on startup.

    Imports are tolerant of missing optional deps so dev environments without
    every ML/LLM library can still boot the auth + ingestion endpoints.
    """
    try:
        from app.services import ingestion  # noqa: F401  (parser registry)
    except ImportError as e:
        log.warning("ingestion registry skipped", error=str(e))
    try:
        from app.services import ml  # noqa: F401  (estimator registry)
    except ImportError as e:
        log.warning("ml registry skipped", error=str(e))
    try:
        from app.services import agents  # noqa: F401  (provider/tool registries)
    except ImportError as e:
        log.warning("agents registry skipped", error=str(e))

    log.info("ezidatic.startup", env=settings.app_env, version=__version__)
    yield


app = FastAPI(
    title="Ezidatic API",
    version=__version__,
    description="Extensible AI Data Analyst Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "version": __version__, "env": settings.app_env}


app.include_router(api_router, prefix="/api/v1")
