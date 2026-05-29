"""
Validators Utility
Input validation helpers for file uploads, medicine names,
patient data, and API request parameters.
"""

import re
from pathlib import Path
from typing import List, Optional

from app.config import settings

# ── Magic bytes for image format detection ─────────────────────────────────
IMAGE_MAGIC_BYTES = {
    b"\xff\xd8\xff": "jpeg",       # JPEG
    b"\x89PNG\r\n\x1a\n": "png",  # PNG
    b"II*\x00": "tiff",            # TIFF (little-endian)
    b"MM\x00*": "tiff",            # TIFF (big-endian)
    b"BM": "bmp",                  # BMP
    b"RIFF": "webp",               # WEBP (partial — needs further check)
    b"GIF87a": "gif",
    b"GIF89a": "gif",
}

# ── Allowed medicine name characters ──────────────────────────────────────
MEDICINE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9\s\-\(\)\.\/]{2,100}$")

# ── Suspicious patterns (prompt injection / XSS guards) ──────────────────
SUSPICIOUS_PATTERNS = [
    re.compile(r"<script", re.I),
    re.compile(r"javascript:", re.I),
    re.compile(r"ignore\s+previous\s+instructions", re.I),
    re.compile(r"system\s+prompt", re.I),
    re.compile(r"\bexec\b|\beval\b|\bimport\b", re.I),
    re.compile(r"DROP\s+TABLE|DELETE\s+FROM|INSERT\s+INTO", re.I),
]


# ── File Validators ────────────────────────────────────────────────────────

def validate_image_file(content: bytes, extension: str) -> None:
    """
    Validate that uploaded file bytes match the declared extension.
    Raises ValueError if the file appears to be invalid or malicious.

    Args:
        content: Raw file bytes.
        extension: Declared file extension (e.g., ".jpg").

    Raises:
        ValueError: If file is invalid.
    """
    if not content:
        raise ValueError("Uploaded file is empty.")

    if len(content) < 8:
        raise ValueError("File is too small to be a valid image.")

    # Check magic bytes
    detected_format = _detect_image_format(content)

    ext_lower = extension.lower().lstrip(".")
    # Normalise extension aliases
    ext_map = {"jpg": "jpeg", "tif": "tiff"}
    ext_lower = ext_map.get(ext_lower, ext_lower)

    if detected_format is None:
        raise ValueError(
            f"File does not appear to be a valid image. "
            f"Declared extension: {extension}."
        )

    # Allow webp regardless of magic byte match (RIFF header is shared with WAV)
    if ext_lower == "webp":
        if not content[:4] == b"RIFF" or b"WEBP" not in content[:12]:
            raise ValueError("File does not appear to be a valid WebP image.")
        return

    if detected_format != ext_lower and not (
        detected_format == "jpeg" and ext_lower == "jpg"
    ):
        raise ValueError(
            f"File content ({detected_format}) does not match "
            f"declared extension ({extension})."
        )


def _detect_image_format(content: bytes) -> Optional[str]:
    """Detect image format from magic bytes."""
    for magic, fmt in IMAGE_MAGIC_BYTES.items():
        if content[:len(magic)] == magic:
            return fmt
    return None


def validate_file_extension(filename: str) -> str:
    """
    Validate and return the lowercase file extension.
    Raises ValueError if not a supported image type.
    """
    ext = Path(filename).suffix.lower()
    if ext not in settings.OCR_SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file extension '{ext}'. "
            f"Allowed: {settings.OCR_SUPPORTED_EXTENSIONS}"
        )
    return ext


def validate_file_size(content: bytes) -> None:
    """Raise ValueError if file exceeds the configured maximum size."""
    if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"File size {len(content) / 1024 / 1024:.1f} MB exceeds "
            f"maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
        )


# ── Input Validators ───────────────────────────────────────────────────────

def validate_medicine_name(name: str) -> str:
    """
    Validate and sanitise a medicine name.
    Returns cleaned name or raises ValueError.
    """
    if not name or not name.strip():
        raise ValueError("Medicine name cannot be empty.")

    cleaned = name.strip()

    if len(cleaned) < 2:
        raise ValueError(f"Medicine name '{cleaned}' is too short.")

    if len(cleaned) > 100:
        raise ValueError(f"Medicine name exceeds 100 characters.")

    if not MEDICINE_NAME_PATTERN.match(cleaned):
        raise ValueError(
            f"Medicine name '{cleaned}' contains invalid characters. "
            "Only letters, numbers, spaces, hyphens, and parentheses are allowed."
        )

    # Check for suspicious patterns (prompt injection guard)
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(cleaned):
            raise ValueError(f"Medicine name contains disallowed content.")

    return cleaned


def validate_medicine_list(medicines: List[str]) -> List[str]:
    """
    Validate a list of medicine names.
    Returns cleaned list with invalid entries removed.
    """
    validated = []
    for med in medicines:
        try:
            clean = validate_medicine_name(med)
            validated.append(clean)
        except ValueError:
            pass  # Skip invalid entries silently
    return validated


def validate_patient_age(age: Optional[int]) -> Optional[int]:
    """
    Validate patient age.
    Returns age or raises ValueError.
    """
    if age is None:
        return None
    if not isinstance(age, int):
        raise ValueError("Patient age must be an integer.")
    if age < 0 or age > 120:
        raise ValueError(f"Patient age {age} is outside valid range (0–120).")
    return age


def validate_language_code(language: str) -> str:
    """
    Validate ISO 639-1 language code.
    Falls back to default if unsupported.
    """
    if not language:
        return settings.DEFAULT_LANGUAGE
    lang = language.lower().strip()
    if lang not in settings.SUPPORTED_LANGUAGES:
        return settings.DEFAULT_LANGUAGE
    return lang


def validate_prescription_id(prescription_id: str) -> str:
    """
    Validate that a prescription_id looks like a UUID.
    """
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE,
    )
    if not uuid_pattern.match(prescription_id):
        raise ValueError(
            f"Invalid prescription_id format '{prescription_id}'. "
            "Expected UUID format (e.g., 3fa85f64-5717-4562-b3fc-2c963f66afa6)."
        )
    return prescription_id.lower()


def sanitise_text_input(text: str, max_length: int = 5000) -> str:
    """
    Sanitise free-text input:
    - Strip leading/trailing whitespace
    - Truncate to max_length
    - Remove null bytes
    - Check for suspicious content
    """
    if not text:
        return ""

    cleaned = text.strip().replace("\x00", "")
    cleaned = cleaned[:max_length]

    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(cleaned):
            raise ValueError("Input contains disallowed content.")

    return cleaned
