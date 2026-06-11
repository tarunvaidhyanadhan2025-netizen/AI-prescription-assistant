"""
Prescription OCR & Medicine Safety Platform
FastAPI application entry point.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analysis, health, prescriptions, upload
from app.core.rate_limit import RateLimitMiddleware
from app.core.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Provider: {settings.MODEL_PROVIDER} | Model: {settings.MODEL_NAME or '(default)'} | OCR: {settings.OCR_PROVIDER}")

    # Create DB tables (non-fatal if DB unavailable)
    try:
        from app.core.database import create_tables
        await create_tables()
        logger.info("Database tables ready.")
    except Exception as exc:
        logger.warning(f"DB init failed (non-fatal): {exc}")

    logger.info("Startup complete.")
    yield
    logger.info("Shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Prescription OCR and Medicine Safety Analysis Platform. "
            "Supports Gemini, OpenAI, Ollama — switch via MODEL_PROVIDER env var."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        RateLimitMiddleware,
        enabled=settings.ENVIRONMENT != "test",
    )

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}s"
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
        detail = str(exc) if not settings.is_production else "An unexpected error occurred."
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": detail,
                "type": type(exc).__name__,
                "path": str(request.url),
            },
        )

    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])
    app.include_router(prescriptions.router, prefix="/api/v1", tags=["Prescriptions"])

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "provider": settings.MODEL_PROVIDER,
            "docs": "/docs",
        }

    return app


app = create_app()
