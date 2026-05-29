"""
AI Prescription Explainer & Safety Assistant
Main FastAPI Application Entry Point
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database.chroma import ChromaDBClient
from app.database.vector_store import VectorStore
from app.routes import analysis, health, upload
from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # ── Startup ──────────────────────────────────────────────────────────
    logger.info("Starting AI Prescription Explainer & Safety Assistant...")

    # Initialise ChromaDB client
    try:
        chroma_client = ChromaDBClient()
        await chroma_client.initialize()
        app.state.chroma_client = chroma_client
        logger.info("ChromaDB initialised successfully.")
    except Exception as exc:
        logger.error(f"ChromaDB initialisation failed: {exc}")
        raise

    # Seed vector store with medicine data
    try:
        vector_store = VectorStore(chroma_client)
        await vector_store.seed_if_empty()
        app.state.vector_store = vector_store
        logger.info("Vector store ready.")
    except Exception as exc:
        logger.error(f"Vector store seeding failed: {exc}")
        raise

    logger.info("Application startup complete.")
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    logger.info("Shutting down application...")
    try:
        await chroma_client.close()
    except Exception as exc:
        logger.warning(f"Error during ChromaDB shutdown: {exc}")
    logger.info("Shutdown complete.")


# ── Application Factory ────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered prescription image analyser that extracts medicines via OCR, "
            "explains usage, detects safety risks, checks dosages, and provides "
            "age-specific warnings using RAG + LLM agents."
        ),
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── Middleware ─────────────────────────────────────────────────────────

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.ENVIRONMENT == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS,
        )

    # ── Request timing middleware ──────────────────────────────────────────

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.4f}s"
        return response

    # ── Global exception handler ───────────────────────────────────────────

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred. Please try again.",
                "path": str(request.url),
            },
        )

    # ── Routers ────────────────────────────────────────────────────────────

    app.include_router(health.router, prefix="/api/v1", tags=["Health"])
    app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
    app.include_router(analysis.router, prefix="/api/v1", tags=["Analysis"])

    # ── Root endpoint ──────────────────────────────────────────────────────

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
        }

    return app


app = create_app()
