"""
Analysis Routes
Full AI-powered prescription analysis: explanation, side effects,
dosage safety, drowsiness, age warnings, alternatives via RAG agents.
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.agents.explanation_agent import ExplanationAgent
from app.agents.retrieval_agent import RetrievalAgent
from app.agents.safety_agent import SafetyAgent
from app.config import settings
from app.models.response import FullAnalysisResponse, MedicineAnalysis
from app.services.explanation_service import ExplanationService
from app.services.medicine_service import MedicineService
from app.services.rag_service import RAGService
from app.services.warning_service import WarningService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class AnalysisRequest(BaseModel):
    """Optional body for POST-based analysis."""
    prescription_id: str
    patient_age: Optional[int] = None
    language: Optional[str] = "en"
    medicines: Optional[list[str]] = None  # Override OCR-detected list


@router.get(
    "/analysis/{prescription_id}",
    response_model=FullAnalysisResponse,
    summary="Run full prescription analysis",
    description=(
        "Given a prescription_id returned by /upload, runs the full AI pipeline: "
        "RAG retrieval, medicine explanation, side effect detection, dosage safety check, "
        "drowsiness flag, age-specific warnings, and alternative suggestions."
    ),
)
async def analyse_prescription(
    request: Request,
    prescription_id: str,
    patient_age: Optional[int] = None,
    language: Optional[str] = "en",
):
    """GET-based analysis using query params."""
    return await _run_analysis(
        request=request,
        prescription_id=prescription_id,
        patient_age=patient_age,
        language=language,
        medicines_override=None,
    )


@router.post(
    "/analysis",
    response_model=FullAnalysisResponse,
    summary="Run full prescription analysis (POST)",
)
async def analyse_prescription_post(request: Request, body: AnalysisRequest):
    """POST-based analysis with optional medicine list override."""
    return await _run_analysis(
        request=request,
        prescription_id=body.prescription_id,
        patient_age=body.patient_age,
        language=body.language or "en",
        medicines_override=body.medicines,
    )


async def _run_analysis(
    request: Request,
    prescription_id: str,
    patient_age: Optional[int],
    language: str,
    medicines_override: Optional[list[str]],
) -> FullAnalysisResponse:
    """
    Core analysis pipeline:
    1. Resolve medicine list (override or load from cache/OCR file).
    2. For each medicine: RAG retrieval → explanation → safety → warnings.
    3. Aggregate into FullAnalysisResponse.
    """

    if language not in settings.SUPPORTED_LANGUAGES:
        language = settings.DEFAULT_LANGUAGE

    # ── Resolve medicines ──────────────────────────────────────────────────
    medicines: list[str] = []

    if medicines_override:
        medicines = [m.strip() for m in medicines_override if m.strip()]
    else:
        # Try to load from a metadata sidecar saved by OCR pipeline
        sidecar_path = os.path.join(settings.upload_dir_path, f"{prescription_id}.meta")
        if os.path.exists(sidecar_path):
            import json
            try:
                with open(sidecar_path) as f:
                    meta = json.load(f)
                medicines = meta.get("detected_medicines", [])
                if patient_age is None:
                    patient_age = meta.get("patient_age")
                if language == "en":
                    language = meta.get("language", "en")
            except Exception as exc:
                logger.warning(f"Could not read sidecar for {prescription_id}: {exc}")

    if not medicines:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No medicines found for prescription_id '{prescription_id}'. "
                "Please upload the prescription first via POST /api/v1/upload."
            ),
        )

    # ── Initialise services ────────────────────────────────────────────────
    vector_store = getattr(request.app.state, "vector_store", None)
    if vector_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not yet initialised. Please retry in a moment.",
        )

    rag_service = RAGService(vector_store)
    medicine_service = MedicineService()
    warning_service = WarningService()
    explanation_service = ExplanationService()

    retrieval_agent = RetrievalAgent(rag_service)
    safety_agent = SafetyAgent(warning_service, medicine_service)
    explanation_agent = ExplanationAgent(explanation_service)

    # ── Per-medicine analysis ──────────────────────────────────────────────
    analyses: list[MedicineAnalysis] = []

    for med_name in medicines:
        logger.info(f"Analysing medicine: {med_name} | age={patient_age} | lang={language}")

        try:
            # 1. RAG retrieval
            retrieved_context = await retrieval_agent.retrieve(med_name)

            # 2. AI explanation
            explanation = await explanation_agent.explain(
                medicine_name=med_name,
                context=retrieved_context,
                language=language,
            )

            # 3. Safety checks
            safety_report = await safety_agent.evaluate(
                medicine_name=med_name,
                context=retrieved_context,
                patient_age=patient_age,
                language=language,
            )

            analyses.append(
                MedicineAnalysis(
                    medicine_name=med_name,
                    explanation=explanation.explanation,
                    use_case=explanation.use_case,
                    side_effects=safety_report.side_effects,
                    causes_drowsiness=safety_report.causes_drowsiness,
                    dosage_info=safety_report.dosage_info,
                    dosage_safe=safety_report.dosage_safe,
                    age_warnings=safety_report.age_warnings,
                    alternatives=safety_report.alternatives,
                    severity_level=safety_report.severity_level,
                    rag_sources=retrieved_context.sources,
                )
            )

        except Exception as exc:
            logger.error(f"Analysis failed for '{med_name}': {exc}", exc_info=True)
            analyses.append(
                MedicineAnalysis(
                    medicine_name=med_name,
                    explanation=f"Analysis unavailable: {str(exc)}",
                    use_case="",
                    side_effects=[],
                    causes_drowsiness=False,
                    dosage_info="",
                    dosage_safe=True,
                    age_warnings=[],
                    alternatives=[],
                    severity_level="unknown",
                    rag_sources=[],
                )
            )

    # ── Aggregate overall safety flags ─────────────────────────────────────
    any_drowsy = any(a.causes_drowsiness for a in analyses)
    any_unsafe_dosage = any(not a.dosage_safe for a in analyses)
    has_age_warnings = any(bool(a.age_warnings) for a in analyses)

    overall_severity = "low"
    severity_rank = {"low": 0, "medium": 1, "high": 2, "critical": 3, "unknown": -1}
    for a in analyses:
        if severity_rank.get(a.severity_level, -1) > severity_rank.get(overall_severity, 0):
            overall_severity = a.severity_level

    return FullAnalysisResponse(
        prescription_id=prescription_id,
        patient_age=patient_age,
        language=language,
        medicines=analyses,
        overall_drowsiness_warning=any_drowsy,
        overall_dosage_concern=any_unsafe_dosage,
        overall_age_warning=has_age_warnings,
        overall_severity=overall_severity,
        total_medicines_analysed=len(analyses),
        summary=(
            f"Analysed {len(analyses)} medicine(s). "
            + ("⚠ Drowsiness risk detected. " if any_drowsy else "")
            + ("⚠ Dosage concern detected. " if any_unsafe_dosage else "")
            + ("⚠ Age-specific warning present. " if has_age_warnings else "")
        ),
    )
