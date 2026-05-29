"""
Upload Routes
Handles prescription image uploads, validates them, runs OCR,
and returns extracted text + detected medicine names.
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.models.prescription import PrescriptionUploadResponse
from app.services.ocr_service import OCRService
from app.utils.logger import get_logger
from app.utils.validators import validate_image_file

router = APIRouter()
logger = get_logger(__name__)

# Initialise OCR service (stateless, safe to share)
ocr_service = OCRService()


@router.post(
    "/upload",
    response_model=PrescriptionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a prescription image",
    description=(
        "Accepts a prescription image (JPEG, PNG, TIFF, BMP, WEBP), "
        "runs Tesseract OCR to extract text, detects medicine names, "
        "and returns a prescription_id for subsequent analysis calls."
    ),
)
async def upload_prescription(
    request: Request,
    file: UploadFile = File(..., description="Prescription image file"),
    patient_age: Optional[int] = Form(None, description="Patient age in years (optional, enables age-specific warnings)"),
    language: Optional[str] = Form("en", description="Preferred response language (ISO 639-1 code)"),
):
    """
    Upload endpoint:
    1. Validate file type and size.
    2. Save to disk with a UUID filename.
    3. Run OCR to extract raw text.
    4. Detect medicine names from OCR output.
    5. Return prescription_id + raw_text + detected_medicines.
    """

    # ── Validate ───────────────────────────────────────────────────────────
    ext = Path(file.filename or "upload").suffix.lower()
    if ext not in settings.OCR_SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Supported: {settings.OCR_SUPPORTED_EXTENSIONS}",
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    try:
        validate_image_file(content, ext)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # ── Validate language ──────────────────────────────────────────────────
    if language not in settings.SUPPORTED_LANGUAGES:
        language = settings.DEFAULT_LANGUAGE
        logger.warning(f"Unsupported language requested; falling back to '{language}'.")

    # ── Persist file ───────────────────────────────────────────────────────
    prescription_id = str(uuid.uuid4())
    upload_path = os.path.join(settings.upload_dir_path, f"{prescription_id}{ext}")
    try:
        with open(upload_path, "wb") as fh:
            fh.write(content)
        logger.info(f"Saved upload to {upload_path} ({len(content)} bytes)")
    except OSError as exc:
        logger.error(f"Failed to save upload: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save uploaded file.",
        )

    # ── OCR ────────────────────────────────────────────────────────────────
    try:
        ocr_result = await ocr_service.extract_text(upload_path)
    except Exception as exc:
        logger.error(f"OCR failed for {upload_path}: {exc}", exc_info=True)
        # Clean up orphaned file
        try:
            os.remove(upload_path)
        except OSError:
            pass
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"OCR extraction failed: {str(exc)}",
        )

    if not ocr_result.raw_text.strip():
        logger.warning(f"OCR produced empty text for {upload_path}")

    logger.info(
        f"Upload complete | prescription_id={prescription_id} | "
        f"medicines_detected={len(ocr_result.detected_medicines)}"
    )

    return PrescriptionUploadResponse(
        prescription_id=prescription_id,
        filename=file.filename or f"{prescription_id}{ext}",
        file_path=upload_path,
        raw_text=ocr_result.raw_text,
        detected_medicines=ocr_result.detected_medicines,
        patient_age=patient_age,
        language=language,
        ocr_confidence=ocr_result.confidence,
        message=(
            "Prescription uploaded and OCR completed. "
            "Call /api/v1/analysis/{prescription_id} to get the full safety report."
        ),
    )


@router.delete(
    "/upload/{prescription_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an uploaded prescription image",
)
async def delete_prescription_file(prescription_id: str):
    """
    Remove a previously uploaded image from disk.
    Useful for privacy-sensitive workflows.
    """
    upload_dir = settings.upload_dir_path
    deleted = False
    for ext in settings.OCR_SUPPORTED_EXTENSIONS:
        candidate = os.path.join(upload_dir, f"{prescription_id}{ext}")
        if os.path.exists(candidate):
            os.remove(candidate)
            deleted = True
            logger.info(f"Deleted {candidate}")
            break

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No file found for prescription_id '{prescription_id}'.",
        )

    return {"message": f"File for prescription_id '{prescription_id}' deleted successfully."}
