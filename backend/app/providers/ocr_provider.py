"""
OCR provider abstraction.
Supports Tesseract and EasyOCR via the same interface.
Switch via OCR_PROVIDER env var.
"""
from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List

from app.core.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

MEDICINE_PATTERNS = [
    # Standard prefixes: Tab. Cap. etc.
    r"\b(?:Tab|Cap|Syp|Inj|Gel|Oint|Drops?|Susp|Cream|Lotion|Spray|Capsule|Tablet)\.\s*([A-Z][a-zA-Z]+)",
    # Numbered list: "1 | MedicineName" or "1. MedicineName" or "1) MedicineName"
    r"^\s*[\[\(]?\s*\d+\s*[\]\)]?\s*[|.)\s]\s*([A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{2,}){0,3})",
    # Dosage strength pattern
    r"\b([A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{2,})?)\s+\d+\s*(?:mg|mcg|g|ml|IU|%)\b",
    # Known drug suffixes
    r"\b([A-Z][a-zA-Z]*(?:cillin|mycin|zole|pril|sartan|olol|pam|pine|xacin|statin|mab|nib|tide|vir|floxacin|azole|dipine|setron|fenac|profen|parin|olone|isone|gliptin|gliflozin))\b",
    # Brand names in parentheses like (capsule) or (lotion) preceded by name
    r"([A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{2,}){0,2})\s*\([a-z]+\)",
    # Rx prefix
    r"Rx[:\s]+([A-Z][a-zA-Z]+)",
]

NON_MEDICINE_WORDS = {
    "PATIENT", "NAME", "DATE", "DOCTOR", "HOSPITAL", "CLINIC", "ADDRESS",
    "PHONE", "AGE", "WEIGHT", "HEIGHT", "SIGNATURE", "PRINT", "TAKE",
    "TIMES", "DAILY", "MORNING", "NIGHT", "BEFORE", "AFTER", "MEALS",
    "WEEKS", "DAYS", "MONTHS", "DOSE", "REFILL", "TOTAL", "EACH",
    "PRESCRIPTION", "DISPENSE", "GENERIC", "BRAND", "ONCE", "TWICE",
    "UNIT", "UNITS", "TABLET", "TABLETS", "CAPSULE", "CAPSULES",
    "APPLY", "ORAL", "TOPICAL", "EXTERNAL", "INTERNAL", "USE",
    "RIGHT", "LEFT", "BOTH", "EYES", "EAR", "EARS", "DROPS",
    "STORE", "BELOW", "KEEP", "REACH", "CHILDREN", "SHAKE", "WELL",
    "EXPIRY", "BATCH", "MFG", "MANUFACTURED", "DISTRIBUTED", "LICENSED",
    "WATER", "EXTRACT", "FRAGRANCE", "COLOUR", "COLOR",
    "WITH", "FROM", "THAT", "THIS", "ONLY", "ALSO", "PLUS", "FREE",
    "DIAGNOSIS", "SENSITIVE", "FREQUENCY", "DURATION", "MEDICATIONS",
    "CONTINUE", "REVIEW", "NECESSARY", "FEMALE", "MALE", "YEAR",
    "BASED", "NORMAL", "GENTLE", "SKIN", "HAIR", "FACE", "BODY",
    "LOTION", "CLEANSER", "SUNSCREEN", "WASH", "BATH", "BOTTLE",
}


@dataclass
class OCRResult:
    raw_text: str
    cleaned_text: str
    detected_medicines: List[str] = field(default_factory=list)
    confidence: float = 0.0


class BaseOCRProvider(ABC):
    @abstractmethod
    async def extract(self, image_path: str) -> OCRResult: ...

    def _clean_text(self, text: str) -> str:
        text = text.replace("\xa0", " ").replace("\t", " ")
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _detect_medicines(self, text: str) -> List[str]:
        candidates: set[str] = set()

        # Pattern-based extraction
        for pattern in MEDICINE_PATTERNS:
            for m in re.findall(pattern, text, re.MULTILINE | re.IGNORECASE):
                name = m.strip().title()
                if name.upper() not in NON_MEDICINE_WORDS and len(name) > 3:
                    candidates.add(name)

        # Line-by-line extraction for numbered prescription format
        # Matches lines like: "1 | Venusia Sun Aqua" or "2   Physiogel ..."
        for line in text.split("\n"):
            line = line.strip()
            # Match numbered lines
            m = re.match(r'^[\[\(]?\s*\d+\s*[\]\)]?\s*[|.\s]\s*(.+)$', line)
            if m:
                rest = m.group(1).strip()
                # Take first 1-3 words as the medicine name
                words = rest.split()
                name_words = []
                for word in words[:4]:
                    # Stop at pipe, parenthesis, or lowercase continuation words
                    clean = re.sub(r'[^a-zA-Z]', '', word)
                    if not clean or clean.lower() in {
                        'apply', 'use', 'take', 'to', 'and', 'for',
                        'the', 'of', 'in', 'at', 'oe', 'ge'
                    }:
                        break
                    if len(clean) >= 3:
                        name_words.append(clean.title())
                if name_words:
                    name = " ".join(name_words)
                    if name.upper() not in NON_MEDICINE_WORDS:
                        candidates.add(name)

        # Clean up: remove anything that's purely numbers or single chars
        cleaned = {
            c for c in candidates
            if len(c) > 3
            and not c.replace(" ", "").isdigit()
            and c.upper() not in NON_MEDICINE_WORDS
        }
        return sorted(cleaned)


class TesseractOCRProvider(BaseOCRProvider):
    def __init__(self):
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
            self._pytesseract = pytesseract
        except ImportError:
            raise RuntimeError("pytesseract not installed. Run: pip install pytesseract")
        self._config = f"--oem 3 --psm 6 -l {settings.TESSERACT_LANG}"

    async def extract(self, image_path: str) -> OCRResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_sync, image_path)

    def _extract_sync(self, image_path: str) -> OCRResult:
        from PIL import Image, ImageEnhance, ImageFilter

        img = Image.open(image_path).convert("RGB").convert("L")
        w, h = img.size
        if w < 1000 or h < 1000:
            scale = 2
            img = img.resize((w * scale, h * scale), Image.LANCZOS)
        img = img.filter(ImageFilter.SHARPEN)
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.MedianFilter(size=3))

        try:
            data = self._pytesseract.image_to_data(
                img, config=self._config, output_type=self._pytesseract.Output.DICT
            )
            raw_text = self._pytesseract.image_to_string(img, config=self._config)
        except self._pytesseract.TesseractNotFoundError:
            raise RuntimeError(f"Tesseract not found at '{settings.TESSERACT_CMD}'")

        confs = [c for c in data["conf"] if isinstance(c, (int, float)) and c > 0]
        confidence = round((sum(confs) / len(confs)) / 100, 4) if confs else 0.0
        cleaned = self._clean_text(raw_text)
        return OCRResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            detected_medicines=self._detect_medicines(cleaned),
            confidence=confidence,
        )


class EasyOCRProvider(BaseOCRProvider):
    def __init__(self):
        try:
            import easyocr
            self._reader = easyocr.Reader(["en"], gpu=False)
        except ImportError:
            raise RuntimeError("easyocr not installed. Run: pip install easyocr")

    async def extract(self, image_path: str) -> OCRResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_sync, image_path)

    def _extract_sync(self, image_path: str) -> OCRResult:
        results = self._reader.readtext(image_path, detail=1)
        lines = [text for (_, text, _) in results]
        confs = [conf for (_, _, conf) in results]

        raw_text = "\n".join(lines)
        confidence = round(sum(confs) / len(confs), 4) if confs else 0.0
        cleaned = self._clean_text(raw_text)
        return OCRResult(
            raw_text=raw_text,
            cleaned_text=cleaned,
            detected_medicines=self._detect_medicines(cleaned),
            confidence=confidence,
        )


@lru_cache(maxsize=1)
def get_ocr_provider() -> BaseOCRProvider:
    provider = settings.OCR_PROVIDER.lower()
    if provider == "easyocr":
        return EasyOCRProvider()
    return TesseractOCRProvider()
