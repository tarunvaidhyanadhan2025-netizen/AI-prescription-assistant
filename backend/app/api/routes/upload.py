"""Upload route — accepts prescription image, runs OCR, returns structured result."""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.core.dependencies import get_analysis_service
from app.core.settings import settings
from app.providers.ocr_provider import get_ocr_provider
from app.schemas.responses import UploadResponse
from app.services.analysis_service import AnalysisService
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"}


@router.post("/upload", response_model=UploadResponse, summary="Upload prescription image")
async def upload_prescription(
    file: UploadFile,
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    # Validate extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # Validate size
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit.",
        )

    # Save file
    prescription_id = str(uuid.uuid4())
    safe_filename = f"{prescription_id}{ext}"
    upload_path = os.path.join(settings.upload_dir_path, safe_filename)

    with open(upload_path, "wb") as f:
        f.write(content)
    logger.info(f"Saved upload: {upload_path}")

    # OCR extraction
    ocr_provider = get_ocr_provider()
    try:
        ocr_result = await ocr_provider.extract(upload_path)
    except Exception as exc:
        logger.error(f"OCR failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"OCR extraction failed: {str(exc)}",
        )

    # LLM refinement — the source of truth for the medicine list.
    # KEY FIX: we use ONLY the LLM-refined list when it returns results.
    # The OCR regex list is ONLY a fallback when LLM returns empty.
    # Merging them caused the "17 medicines from 4" bug.
    llm_failed = False
    refined = {}
    try:
        refined = await analysis_service.refine_ocr(
            raw_text=ocr_result.cleaned_text,
            initial_medicines=ocr_result.detected_medicines,
        )
    except Exception as exc:
        logger.error(f"LLM refinement failed: {exc}", exc_info=True)
        llm_failed = True
        refined = {
            "medicines": [],
            "patient_info": {},
            "doctor_name": "",
            "notes": f"AI refinement error: {str(exc)}",
        }

    # Build final medicine list:
    # 1. Use LLM output if it returned any medicines.
    # 2. Only fall back to OCR regex if LLM returned nothing.
    llm_medicines = [
        m.get("name", "").strip()
        for m in refined.get("medicines", [])
        if m.get("name", "").strip()
    ]

    if llm_medicines:
        # Trust LLM completely — it was given the strict prompt to extract
        # only the actual Rx medicines, not ingredients or demographics.
        all_medicines = list(dict.fromkeys(llm_medicines))  # preserve order, deduplicate
        logger.info(f"Using LLM-refined medicine list: {all_medicines}")
    else:
        # LLM returned nothing (template mode, or LLM failure) — fall back to OCR.
        all_medicines = list(dict.fromkeys(ocr_result.detected_medicines))
        logger.warning(
            f"LLM returned no medicines — using OCR fallback: {all_medicines}"
            + (" (LLM had an error)" if llm_failed else "")
        )

    # Extract patient info
    patient_info = refined.get("patient_info", {})
    patient_age = patient_info.get("age")

    # Save sidecar metadata
    meta = {
        "prescription_id": prescription_id,
        "detected_medicines": all_medicines,
        "patient_age": patient_age,
        "language": "en",
        "ocr_confidence": ocr_result.confidence,
        "doctor_name": refined.get("doctor_name", ""),
        "notes": refined.get("notes", ""),
    }
    sidecar_path = os.path.join(settings.upload_dir_path, f"{prescription_id}.meta")
    with open(sidecar_path, "w") as f:
        json.dump(meta, f)

    return UploadResponse(
        prescription_id=prescription_id,
        filename=file.filename or safe_filename,
        raw_text=ocr_result.raw_text[:2000],
        cleaned_text=ocr_result.cleaned_text[:2000],
        detected_medicines=all_medicines,
        ocr_confidence=ocr_result.confidence,
        message=f"Prescription uploaded. Found {len(all_medicines)} medicine(s). "
                f"Use prescription_id '{prescription_id}' to run analysis.",
    )
