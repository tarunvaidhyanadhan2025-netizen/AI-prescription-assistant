"""Analysis route — full medicine safety analysis.

Optimized: entire prescription analysed in 2 total LLM calls.
  Call 1 (upload): OCR refinement  → clean medicine list
  Call 2 (here):   Batch analysis  → all medicines in one prompt
"""
from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_analysis_service
from app.core.settings import settings
from app.providers.factory import get_llm_provider
from app.schemas.responses import AnalysisRequest, FullAnalysisResponse, MedicineAnalysis
from app.services.analysis_service import AnalysisService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

SEVERITY_RANK = {"unknown": -1, "low": 0, "medium": 1, "high": 2, "critical": 3}


@router.get(
    "/analysis/{prescription_id}",
    response_model=FullAnalysisResponse,
    summary="Analyse prescription (GET)",
)
async def analyse_get(
    prescription_id: str,
    patient_age: Optional[int] = None,
    language: Optional[str] = "en",
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    return await _run_analysis(analysis_service, prescription_id, patient_age, language or "en", None)


@router.post(
    "/analysis",
    response_model=FullAnalysisResponse,
    summary="Analyse prescription (POST)",
)
async def analyse_post(
    body: AnalysisRequest,
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    return await _run_analysis(
        analysis_service,
        body.prescription_id,
        body.patient_age,
        body.language or "en",
        body.medicines,
    )


async def _run_analysis(
    analysis_service: AnalysisService,
    prescription_id: str,
    patient_age: Optional[int],
    language: str,
    medicines_override: Optional[list],
) -> FullAnalysisResponse:
    if language not in settings.SUPPORTED_LANGUAGES:
        language = settings.DEFAULT_LANGUAGE

    # Resolve medicine list
    medicines: list[str] = []
    if medicines_override:
        medicines = [m.strip() for m in medicines_override if m.strip()]
    else:
        sidecar = os.path.join(settings.upload_dir_path, f"{prescription_id}.meta")
        if os.path.exists(sidecar):
            try:
                with open(sidecar) as f:
                    meta = json.load(f)
                medicines = meta.get("detected_medicines", [])
                if patient_age is None:
                    patient_age = meta.get("patient_age")
                if language == "en":
                    language = meta.get("language", "en")
            except Exception as e:
                logger.warning(f"Could not read sidecar for {prescription_id}: {e}")

    if not medicines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No medicines found for prescription_id '{prescription_id}'. "
                   "Upload first via POST /api/v1/upload.",
        )

    # KEY OPTIMIZATION: single batch call for all medicines instead of N calls.
    logger.info(
        f"Batch-analysing {len(medicines)} medicine(s) in 1 LLM call | "
        f"age={patient_age} | lang={language}"
    )
    try:
        analyses: list[MedicineAnalysis] = await analysis_service.analyse_medicines_batch(
            medicine_names=medicines,
            patient_age=patient_age,
            language=language,
        )
    except Exception as exc:
        logger.error(f"Batch analysis failed: {exc}", exc_info=True)
        # Return error entries for every medicine rather than a 500
        analyses = [
            MedicineAnalysis(
                medicine_name=m,
                explanation=f"Analysis error from AI: {str(exc)}",
                use_case="",
                dosage_info="Consult your pharmacist.",
                generated_by="error",
            )
            for m in medicines
        ]

    # Aggregate
    any_drowsy = any(a.causes_drowsiness for a in analyses)
    any_unsafe = any(not a.dosage_safe for a in analyses)
    any_age_warn = any(bool(a.age_warnings) for a in analyses)
    overall_severity = max(
        (a.severity_level for a in analyses),
        key=lambda s: SEVERITY_RANK.get(s, 0),
        default="low",
    )

    provider = get_llm_provider().name

    return FullAnalysisResponse(
        prescription_id=prescription_id,
        patient_age=patient_age,
        language=language,
        medicines=analyses,
        overall_drowsiness_warning=any_drowsy,
        overall_dosage_concern=any_unsafe,
        overall_age_warning=any_age_warn,
        overall_severity=overall_severity,
        total_medicines_analysed=len(analyses),
        provider_used=provider,
        summary=(
            f"Analysed {len(analyses)} medicine(s) using {provider}. "
            + ("⚠ Drowsiness risk. " if any_drowsy else "")
            + ("⚠ Dosage concern. " if any_unsafe else "")
            + ("⚠ Age-specific warning. " if any_age_warn else "")
        ),
    )
