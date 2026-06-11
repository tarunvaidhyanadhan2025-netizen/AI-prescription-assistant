"""Health check route."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import get_llm_service
from app.core.settings import settings
from app.providers.factory import get_llm_provider
from app.schemas.responses import HealthResponse
from app.services.llm_service import LLMService

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="System health check")
async def health(request: Request, llm: LLMService = Depends(get_llm_service)):
    llm_ok = await llm.health_check()
    vector_store = getattr(request.app.state, "vector_store", None)
    vector_count = 0
    if vector_store and vector_store._collection:
        try:
            vector_count = vector_store._collection.count()
        except Exception:
            pass

    return HealthResponse(
        status="ok" if llm_ok else "degraded",
        version=settings.APP_VERSION,
        provider=get_llm_provider().name,
        vector_db_enabled=settings.VECTOR_DB_ENABLED,
        ocr_provider=settings.OCR_PROVIDER,
        details={
            "llm_healthy": llm_ok,
            "vector_db_documents": vector_count,
            "template_mode": settings.use_template_mode,
            "environment": settings.ENVIRONMENT,
        },
    )


@router.get("/health/models", summary="List available models for current provider")
async def list_models(llm: LLMService = Depends(get_llm_service)):
    """Shows what models your API key can access. Useful for debugging 404 model errors."""
    provider = get_llm_provider()
    models = []
    error = None

    try:
        if hasattr(provider, "list_available_models"):
            models = await provider.list_available_models()
        else:
            models = [f"(listing not supported for {provider.name})"]
    except Exception as e:
        error = str(e)

    return {
        "provider": provider.name,
        "configured_model": settings.MODEL_NAME or "(default)",
        "available_models": models,
        "error": error,
    }
