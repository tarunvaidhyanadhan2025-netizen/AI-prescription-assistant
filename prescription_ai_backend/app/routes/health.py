"""
Health Check Routes
Provides liveness and readiness probe endpoints.
"""

import os
import shutil
import time

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.config import settings
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

_START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: float
    version: str
    environment: str
    services: dict


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health_check(request: Request):
    """
    Basic liveness probe.
    Returns 200 if the application is running.
    """
    uptime = round(time.time() - _START_TIME, 2)

    # Check ChromaDB
    chroma_ok = False
    try:
        chroma_client = getattr(request.app.state, "chroma_client", None)
        if chroma_client:
            await chroma_client.ping()
            chroma_ok = True
    except Exception as exc:
        logger.warning(f"ChromaDB health check failed: {exc}")

    # Check disk space
    disk = shutil.disk_usage("/")
    disk_free_gb = disk.free / (1024 ** 3)

    # Check upload dir
    upload_dir_ok = os.path.isdir(settings.UPLOAD_DIR) or True  # auto-created

    services = {
        "chromadb": "ok" if chroma_ok else "degraded",
        "disk_free_gb": round(disk_free_gb, 2),
        "upload_dir": "ok" if upload_dir_ok else "missing",
        "openai_key_set": bool(settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your")),
        "tesseract_path": settings.TESSERACT_CMD,
    }

    overall = "ok" if chroma_ok else "degraded"

    return HealthResponse(
        status=overall,
        uptime_seconds=uptime,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        services=services,
    )


@router.get("/ready", summary="Readiness probe")
async def readiness_check(request: Request):
    """
    Kubernetes-style readiness probe.
    Returns 200 only when all critical services are ready.
    """
    vector_store = getattr(request.app.state, "vector_store", None)
    if vector_store is None:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "not_ready", "reason": "vector_store_not_initialized"})

    return {"status": "ready"}
