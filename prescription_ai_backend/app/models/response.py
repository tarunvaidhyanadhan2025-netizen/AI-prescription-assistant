"""
Response Pydantic Models
Structured output models for the full analysis pipeline.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class MedicineAnalysis(BaseModel):
    """
    Complete analysis result for a single medicine.
    Combines explanation, safety, dosage, and warning data.
    """
    medicine_name: str = Field(..., description="Name of the medicine as detected/provided")

    # Explanation
    explanation: str = Field("", description="Plain-language explanation of the medicine")
    use_case: str = Field("", description="Primary therapeutic use")

    # Safety
    side_effects: List[str] = Field(
        default_factory=list,
        description="Common and notable side effects"
    )
    causes_drowsiness: bool = Field(False, description="True if this medicine causes drowsiness")

    # Dosage
    dosage_info: str = Field("", description="Dosage summary appropriate for patient age")
    dosage_safe: bool = Field(True, description="True if the prescribed dose appears within safe limits")

    # Warnings
    age_warnings: List[str] = Field(
        default_factory=list,
        description="Age-specific safety warnings (paediatric, elderly)"
    )
    alternatives: List[str] = Field(
        default_factory=list,
        description="Suggested alternative medicines"
    )

    # Risk level
    severity_level: str = Field(
        "low",
        description="Overall risk level: low | medium | high | critical"
    )

    # RAG traceability
    rag_sources: List[str] = Field(
        default_factory=list,
        description="Source documents used from vector store"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "medicine_name": "Amoxicillin",
                "explanation": "Amoxicillin is a penicillin antibiotic that fights bacteria.",
                "use_case": "Bacterial infections including ear, chest, and urinary tract infections.",
                "side_effects": ["Diarrhoea", "Nausea", "Rash"],
                "causes_drowsiness": False,
                "dosage_info": "500mg every 8 hours for 7 days.",
                "dosage_safe": True,
                "age_warnings": [],
                "alternatives": ["Azithromycin", "Clarithromycin"],
                "severity_level": "low",
                "rag_sources": ["Amoxicillin"]
            }
        }


class FullAnalysisResponse(BaseModel):
    """
    Top-level response for a full prescription analysis.
    Contains per-medicine analyses and aggregate safety flags.
    """
    prescription_id: str = Field(..., description="Prescription UUID from upload step")
    patient_age: Optional[int] = Field(None, description="Patient age in years")
    language: str = Field("en", description="Language of the response")

    # Per-medicine analyses
    medicines: List[MedicineAnalysis] = Field(
        default_factory=list,
        description="Individual analysis for each detected medicine"
    )

    # Aggregate flags
    overall_drowsiness_warning: bool = Field(
        False,
        description="True if any medicine in the prescription causes drowsiness"
    )
    overall_dosage_concern: bool = Field(
        False,
        description="True if any dosage appears unsafe"
    )
    overall_age_warning: bool = Field(
        False,
        description="True if any age-specific warning is triggered"
    )
    overall_severity: str = Field(
        "low",
        description="Highest severity level across all medicines"
    )
    total_medicines_analysed: int = Field(0, description="Count of medicines analysed")
    summary: str = Field("", description="Human-readable summary of the analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "prescription_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "patient_age": 8,
                "language": "en",
                "medicines": [],
                "overall_drowsiness_warning": False,
                "overall_dosage_concern": False,
                "overall_age_warning": True,
                "overall_severity": "medium",
                "total_medicines_analysed": 2,
                "summary": "Analysed 2 medicine(s). ⚠ Age-specific warning present."
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    message: str
    path: Optional[str] = None
    details: Optional[dict] = None
