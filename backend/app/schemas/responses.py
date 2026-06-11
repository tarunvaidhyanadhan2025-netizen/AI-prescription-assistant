"""API schemas — request/response models."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Upload ─────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    prescription_id: str
    filename: str
    raw_text: str
    cleaned_text: str
    detected_medicines: List[str]
    ocr_confidence: float
    message: str


# ── Analysis ───────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    prescription_id: str
    patient_age: Optional[int] = None
    language: str = "en"
    medicines: Optional[List[str]] = None  # Override OCR-detected list


class MedicineAnalysis(BaseModel):
    medicine_name: str
    explanation: str
    use_case: str
    mechanism: str = ""
    how_to_take: str = ""
    side_effects: List[str] = []
    serious_side_effects: List[str] = []
    causes_drowsiness: bool = False
    drowsiness_note: str = ""
    dosage_info: str
    dosage_safe: bool = True
    dosage_notes: List[str] = []
    age_warnings: List[str] = []
    contraindications: List[str] = []
    alternatives: List[str] = []
    severity_level: str = "low"
    rag_sources: List[str] = []
    drug_class: str = ""
    generated_by: str = "template"  # template | llm


class FullAnalysisResponse(BaseModel):
    prescription_id: str
    patient_age: Optional[int]
    language: str
    medicines: List[MedicineAnalysis]
    overall_drowsiness_warning: bool
    overall_dosage_concern: bool
    overall_age_warning: bool
    overall_severity: str
    total_medicines_analysed: int
    provider_used: str = "template"
    summary: str


# ── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    provider: str
    vector_db_enabled: bool
    ocr_provider: str
    details: Dict[str, Any] = {}
