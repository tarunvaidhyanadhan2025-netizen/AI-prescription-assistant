"""
Prescription Pydantic Models
Request/response models for the upload pipeline.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class OCRResultModel(BaseModel):
    """Represents raw OCR extraction output."""
    raw_text: str = Field(..., description="Raw text extracted by Tesseract OCR")
    cleaned_text: str = Field("", description="Cleaned and normalised OCR text")
    detected_medicines: List[str] = Field(
        default_factory=list,
        description="List of medicine names detected via regex heuristics"
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Average OCR confidence score (0–1)"
    )
    language_detected: str = Field("en", description="Detected language of the prescription")


class PrescriptionUploadResponse(BaseModel):
    """Response returned after a successful prescription image upload."""
    prescription_id: str = Field(
        ...,
        description="Unique UUID for this prescription. Use in subsequent /analysis calls."
    )
    filename: str = Field(..., description="Original uploaded filename")
    file_path: str = Field(..., description="Server-side file path (internal use)")
    raw_text: str = Field(..., description="Raw OCR-extracted text from the image")
    detected_medicines: List[str] = Field(
        default_factory=list,
        description="Heuristically detected medicine names from OCR output"
    )
    patient_age: Optional[int] = Field(
        None,
        ge=0,
        le=120,
        description="Patient age in years (if provided)"
    )
    language: str = Field("en", description="Preferred response language")
    ocr_confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Average OCR extraction confidence"
    )
    message: str = Field(..., description="Human-readable status message")

    class Config:
        json_schema_extra = {
            "example": {
                "prescription_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "filename": "prescription.jpg",
                "file_path": "./uploads/3fa85f64-5717-4562-b3fc-2c963f66afa6.jpg",
                "raw_text": "Rx\nAmoxicillin 500mg TID x 7 days\nParacetamol 500mg PRN",
                "detected_medicines": ["Amoxicillin", "Paracetamol"],
                "patient_age": 35,
                "language": "en",
                "ocr_confidence": 0.87,
                "message": "Prescription uploaded and OCR completed."
            }
        }
