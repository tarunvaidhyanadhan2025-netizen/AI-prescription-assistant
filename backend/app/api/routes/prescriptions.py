"""Prescription history route — list and retrieve past prescriptions."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request, status
from pydantic import BaseModel

from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class PrescriptionSummary(BaseModel):
    prescription_id: str
    detected_medicines: List[str]
    ocr_confidence: float
    patient_age: Optional[int]
    language: str
    doctor_name: str
    notes: str


class PrescriptionListResponse(BaseModel):
    total: int
    prescriptions: List[PrescriptionSummary]


def _upload_dir() -> Path:
    """Read upload dir at request time so monkeypatching works in tests."""
    from app.core.settings import get_settings
    s = get_settings()
    p = Path(s.UPLOAD_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.get(
    "/prescriptions",
    response_model=PrescriptionListResponse,
    summary="List uploaded prescriptions",
)
async def list_prescriptions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List all uploaded prescriptions sorted by recency (newest first)."""
    upload_dir = _upload_dir()
    meta_files = sorted(upload_dir.glob("*.meta"), key=os.path.getmtime, reverse=True)

    total = len(meta_files)
    page = meta_files[offset: offset + limit]

    summaries: List[PrescriptionSummary] = []
    for meta_path in page:
        try:
            with open(meta_path) as f:
                data = json.load(f)
            summaries.append(
                PrescriptionSummary(
                    prescription_id=data.get("prescription_id", meta_path.stem),
                    detected_medicines=data.get("detected_medicines", []),
                    ocr_confidence=data.get("ocr_confidence", 0.0),
                    patient_age=data.get("patient_age"),
                    language=data.get("language", "en"),
                    doctor_name=data.get("doctor_name", ""),
                    notes=data.get("notes", ""),
                )
            )
        except Exception as e:
            logger.warning(f"Could not read meta file {meta_path}: {e}")

    return PrescriptionListResponse(total=total, prescriptions=summaries)


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=PrescriptionSummary,
    summary="Get prescription metadata",
)
async def get_prescription(prescription_id: str):
    """Get metadata for a specific prescription by ID."""
    meta_path = _upload_dir() / f"{prescription_id}.meta"
    if not meta_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription '{prescription_id}' not found.",
        )
    try:
        with open(meta_path) as f:
            data = json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read prescription metadata: {e}",
        )
    return PrescriptionSummary(
        prescription_id=data.get("prescription_id", prescription_id),
        detected_medicines=data.get("detected_medicines", []),
        ocr_confidence=data.get("ocr_confidence", 0.0),
        patient_age=data.get("patient_age"),
        language=data.get("language", "en"),
        doctor_name=data.get("doctor_name", ""),
        notes=data.get("notes", ""),
    )
