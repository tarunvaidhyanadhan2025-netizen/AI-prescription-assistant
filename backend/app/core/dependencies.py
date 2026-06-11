"""FastAPI dependency injection."""
from __future__ import annotations

from fastapi import Depends

from app.providers.factory import get_llm_provider
from app.services.analysis_service import AnalysisService
from app.services.llm_service import LLMService


def get_llm_service() -> LLMService:
    return LLMService(get_llm_provider())


def get_analysis_service(
    llm: LLMService = Depends(get_llm_service),
) -> AnalysisService:
    return AnalysisService(llm)
