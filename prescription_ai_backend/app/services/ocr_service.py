"""
OCR Service
Uses Tesseract (via pytesseract) to extract text from prescription images.
Includes pre-processing with Pillow and OpenCV for improved accuracy.
"""

import asyncio
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Configure Tesseract binary path ───────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

# ── Known medicine name patterns ──────────────────────────────────────────
# Generic patterns used for quick extraction before LLM validation.
MEDICINE_PATTERNS = [
    # "Tab. Amoxicillin 500mg" / "Cap. Paracetamol"
    r"\b(?:Tab|Cap|Syp|Inj|Gel|Oint|Drops?|Susp)\.\s*([A-Z][a-zA-Z]+)",
    # "AMOXICILLIN 500MG" — all-caps drug name
    r"\b([A-Z]{4,})\s+\d+\s*(?:mg|mcg|g|ml|IU)\b",
    # Rx line: "Rx: DrugName"
    r"Rx[:\s]+([A-Z][a-zA-Z]+)",
    # Numbered list: "1. DrugName"
    r"^\s*\d+[\.\)]\s*([A-Z][a-zA-Z]{3,})",
]

# Common filler words to exclude from medicine detection
NON_MEDICINE_WORDS = {
    "PATIENT", "NAME", "DATE", "DOCTOR", "HOSPITAL", "CLINIC", "ADDRESS",
    "PHONE", "AGE", "WEIGHT", "HEIGHT", "SIGNATURE", "PRINT", "TAKE",
    "TIMES", "DAILY", "MORNING", "NIGHT", "BEFORE", "AFTER", "MEALS",
    "WEEKS", "DAYS", "MONTHS", "DOSE", "REFILL", "TOTAL", "EACH",
}


@dataclass
class OCRResult:
    """Structured result from the OCR pipeline."""
    raw_text: str
    cleaned_text: str
    detected_medicines: List[str] = field(default_factory=list)
    confidence: float = 0.0
    language_detected: str = "en"


class OCRService:
    """
    Prescription OCR pipeline:
    1. Load image with Pillow.
    2. Pre-process (grayscale, contrast, denoise, upscale).
    3. Run Tesseract with optimised config.
    4. Post-process: clean whitespace, extract medicine candidates.
    """

    def __init__(self):
        self._tesseract_config = (
            "--oem 3 "          # LSTM + legacy engine
            "--psm 6 "          # Assume uniform block of text
            f"-l {settings.TESSERACT_LANG}"
        )

    # ── Public API ─────────────────────────────────────────────────────────

    async def extract_text(self, image_path: str) -> OCRResult:
        """
        Async wrapper — runs blocking Tesseract in a thread pool.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_text_sync, image_path)

    # ── Internal ───────────────────────────────────────────────────────────

    def _extract_text_sync(self, image_path: str) -> OCRResult:
        """Synchronous OCR pipeline."""
        logger.info(f"Starting OCR for: {image_path}")

        # Load image
        try:
            img = Image.open(image_path)
        except Exception as exc:
            raise RuntimeError(f"Cannot open image '{image_path}': {exc}") from exc

        # Pre-process
        processed = self._preprocess(img)

        # Run Tesseract with detailed data for confidence
        try:
            data = pytesseract.image_to_data(
                processed,
                config=self._tesseract_config,
                output_type=pytesseract.Output.DICT,
            )
            raw_text = pytesseract.image_to_string(processed, config=self._tesseract_config)
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                f"Tesseract not found at '{settings.TESSERACT_CMD}'. "
                "Please install Tesseract and set TESSERACT_CMD in .env."
            )
        except Exception as exc:
            raise RuntimeError(f"Tesseract OCR failed: {exc}") from exc

        # Calculate average confidence (ignore -1 values for non-word tokens)
        confidences = [c for c in data["conf"] if isinstance(c, (int, float)) and c > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        avg_confidence = round(avg_confidence / 100, 4)  # normalise 0–1

        cleaned = self._clean_text(raw_text)
        medicines = self._detect_medicines(cleaned)

        logger.info(
            f"OCR complete | confidence={avg_confidence:.2%} | "
            f"chars={len(cleaned)} | medicines_detected={len(medicines)}"
        )

        return OCRResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            detected_medicines=medicines,
            confidence=avg_confidence,
        )

    def _preprocess(self, img: Image.Image) -> Image.Image:
        """
        Image pre-processing chain for improved OCR accuracy:
        - Convert to grayscale
        - Upscale if small
        - Sharpen
        - Increase contrast
        - Threshold (binarise) — helps printed text
        """
        # Convert to RGB first (handles CMYK, palette modes)
        img = img.convert("RGB")

        # Grayscale
        img = img.convert("L")

        # Upscale small images (Tesseract works best at ~300 DPI)
        w, h = img.size
        if w < 1000 or h < 1000:
            scale = max(2, 300 // min(w, h) if min(w, h) > 0 else 2)
            img = img.resize((w * scale, h * scale), Image.LANCZOS)
            logger.debug(f"Upscaled image {scale}x to {img.size}")

        # Sharpen
        img = img.filter(ImageFilter.SHARPEN)

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # Median filter to reduce noise
        img = img.filter(ImageFilter.MedianFilter(size=3))

        return img

    def _clean_text(self, text: str) -> str:
        """Normalise whitespace and remove junk characters from OCR output."""
        # Replace non-breaking spaces, tabs with regular spaces
        text = text.replace("\xa0", " ").replace("\t", " ")
        # Collapse multiple spaces
        text = re.sub(r" {2,}", " ", text)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _detect_medicines(self, text: str) -> List[str]:
        """
        Heuristic medicine name extractor.
        Uses regex patterns + blocklist filtering.
        Real validation is done by the LLM agent downstream.
        """
        candidates: set[str] = set()

        for pattern in MEDICINE_PATTERNS:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for m in matches:
                name = m.strip().title()
                if name.upper() not in NON_MEDICINE_WORDS and len(name) > 3:
                    candidates.add(name)

        # Also scan for words that look like common medicine suffixes
        suffix_pattern = r"\b([A-Z][a-zA-Z]*(?:cillin|mycin|zole|pril|sartan|olol|pam|pine|xacin|statin|mab|nib|tide|vir))\b"
        suffix_matches = re.findall(suffix_pattern, text, re.IGNORECASE)
        for m in suffix_matches:
            name = m.strip().title()
            if name.upper() not in NON_MEDICINE_WORDS:
                candidates.add(name)

        result = sorted(candidates)
        logger.debug(f"Detected medicine candidates: {result}")
        return result
