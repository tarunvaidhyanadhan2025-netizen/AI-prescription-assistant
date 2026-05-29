"""
Parser Utility
Helper functions for parsing OCR text, extracting dosage information,
frequencies, durations, and other prescription data.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ── Regex patterns ─────────────────────────────────────────────────────────

# Dosage: "500mg", "1.5g", "250 mcg", "10 IU"
DOSAGE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(mg|mcg|µg|g|ml|mL|IU|units?)",
    re.IGNORECASE,
)

# Frequency: "TID", "BID", "OD", "QID", "twice daily", "3 times a day"
FREQUENCY_PATTERNS = [
    (re.compile(r"\b(once\s+daily|OD|QD|q\.?d\.?)\b", re.I), "Once daily"),
    (re.compile(r"\b(twice\s+daily|BID|BD|b\.?i\.?d\.?)\b", re.I), "Twice daily"),
    (re.compile(r"\b(three\s+times\s+(a\s+)?daily|TID|TDS|t\.?i\.?d\.?)\b", re.I), "Three times daily"),
    (re.compile(r"\b(four\s+times\s+(a\s+)?daily|QID|QDS|q\.?i\.?d\.?)\b", re.I), "Four times daily"),
    (re.compile(r"\bevery\s+(\d+)\s*hours?\b", re.I), "Every {n} hours"),
    (re.compile(r"\b(at\s+bedtime|nocte|hs|h\.?s\.?)\b", re.I), "At bedtime"),
    (re.compile(r"\b(as\s+needed|PRN|p\.?r\.?n\.?|when\s+required)\b", re.I), "As needed"),
    (re.compile(r"\b(with\s+meals?|pc|p\.?c\.?|after\s+food)\b", re.I), "With meals"),
    (re.compile(r"\b(before\s+meals?|ac|a\.?c\.?)\b", re.I), "Before meals"),
]

# Duration: "7 days", "2 weeks", "1 month", "x5", "for 10 days"
DURATION_PATTERN = re.compile(
    r"(?:for\s+|x\s*)?(\d+)\s*(days?|weeks?|months?)",
    re.IGNORECASE,
)

# Patient age: "Age: 45", "45 years", "45 yrs", "DOB:"
AGE_PATTERNS = [
    re.compile(r"(?:age[:\s]+|aged?\s+)(\d{1,3})\s*(?:years?|yrs?)?", re.I),
    re.compile(r"(\d{1,3})\s*(?:years?\s*old|yrs?\s*old)", re.I),
    re.compile(r"(?:pt\.?\s+age|patient\s+age)[:\s]*(\d{1,3})", re.I),
]

# Weight: "70kg", "Weight: 65 kg"
WEIGHT_PATTERN = re.compile(
    r"(?:weight[:\s]+|wt\.?\s*[:\s]*)(\d+(?:\.\d+)?)\s*kg",
    re.IGNORECASE,
)

# Doctor name: "Dr. Smith", "Dr John"
DOCTOR_PATTERN = re.compile(
    r"(?:Dr\.?|Doctor)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)",
)

# Date patterns: "01/05/2024", "2024-01-05", "5 Jan 2024"
DATE_PATTERNS = [
    re.compile(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b"),
    re.compile(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b", re.I),
]


@dataclass
class ParsedPrescriptionLine:
    """Structured data extracted from a single prescription line."""
    raw_line: str
    medicine_name: str = ""
    dosage: str = ""
    frequency: str = ""
    duration: str = ""
    route: str = ""
    notes: str = ""


@dataclass
class ParsedPrescription:
    """Fully parsed prescription data."""
    lines: List[ParsedPrescriptionLine] = field(default_factory=list)
    patient_age: Optional[int] = None
    patient_weight_kg: Optional[float] = None
    doctor_name: str = ""
    prescription_date: str = ""
    diagnosis: str = ""
    raw_text: str = ""


def parse_dosage(text: str) -> Optional[str]:
    """
    Extract dosage string from text.
    Returns e.g. "500mg", "1.5g", "250mcg".
    """
    match = DOSAGE_PATTERN.search(text)
    if match:
        return f"{match.group(1)}{match.group(2).lower()}"
    return None


def parse_dosage_mg(text: str) -> Optional[float]:
    """
    Parse dosage and normalise to milligrams.
    Returns float or None.
    """
    match = DOSAGE_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    if unit == "g":
        return value * 1000.0
    elif unit in ("mcg", "µg"):
        return value / 1000.0
    elif unit in ("iu", "units", "unit"):
        return None  # Cannot normalise to mg
    return value  # already in mg or mL


def parse_frequency(text: str) -> Optional[str]:
    """
    Detect dosing frequency from a prescription line.
    Returns a human-readable string or None.
    """
    for pattern, label in FREQUENCY_PATTERNS:
        match = pattern.search(text)
        if match:
            if "{n}" in label:
                n = match.group(1)
                return label.replace("{n}", n)
            return label
    return None


def parse_frequency_per_day(text: str) -> int:
    """
    Returns the number of doses per day.
    Defaults to 1 if unknown.
    """
    freq = parse_frequency(text) or ""
    freq_lower = freq.lower()
    if "twice" in freq_lower or "two" in freq_lower:
        return 2
    if "three" in freq_lower:
        return 3
    if "four" in freq_lower:
        return 4
    # "every N hours"
    match = re.search(r"every\s+(\d+)\s*hours?", freq_lower)
    if match:
        hours = int(match.group(1))
        return max(1, 24 // hours)
    return 1


def parse_duration(text: str) -> Optional[str]:
    """
    Extract treatment duration from text.
    Returns e.g. "7 days", "2 weeks".
    """
    match = DURATION_PATTERN.search(text)
    if match:
        return f"{match.group(1)} {match.group(2).lower()}"
    return None


def parse_patient_age(text: str) -> Optional[int]:
    """
    Attempt to extract patient age from prescription text.
    Returns integer age or None.
    """
    for pattern in AGE_PATTERNS:
        match = pattern.search(text)
        if match:
            age = int(match.group(1))
            if 0 <= age <= 120:
                return age
    return None


def parse_patient_weight(text: str) -> Optional[float]:
    """Extract patient weight in kg."""
    match = WEIGHT_PATTERN.search(text)
    if match:
        return float(match.group(1))
    return None


def parse_doctor_name(text: str) -> str:
    """Extract doctor name from text."""
    match = DOCTOR_PATTERN.search(text)
    return match.group(1).strip() if match else ""


def parse_prescription_date(text: str) -> str:
    """Extract prescription date as a string."""
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(0)
    return ""


def parse_prescription_lines(text: str) -> List[ParsedPrescriptionLine]:
    """
    Split prescription text into lines and parse each for medicine/dosage/frequency.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    parsed_lines = []

    # Skip lines that are clearly headers or patient info
    skip_keywords = {
        "patient", "name:", "address", "phone", "date:", "rx", "signature",
        "refills", "dispense", "label", "dea", "npi", "licensed",
    }

    for line in lines:
        line_lower = line.lower()
        if any(kw in line_lower for kw in skip_keywords):
            continue
        if len(line) < 4:
            continue

        dosage = parse_dosage(line)
        frequency = parse_frequency(line)
        duration = parse_duration(line)

        # Only include lines that have at least a dosage or frequency indicator
        if dosage or frequency:
            parsed_lines.append(ParsedPrescriptionLine(
                raw_line=line,
                dosage=dosage or "",
                frequency=frequency or "",
                duration=duration or "",
            ))

    return parsed_lines


def extract_medicine_lines(text: str) -> List[Tuple[str, str, str]]:
    """
    High-level extraction: returns list of (medicine_name, dosage, frequency) tuples.
    Uses simple line-based heuristics.
    """
    parsed = parse_prescription_lines(text)
    results = []
    for p in parsed:
        # Try to extract medicine name: first word(s) before the dosage
        line = p.raw_line
        dosage_match = DOSAGE_PATTERN.search(line)
        if dosage_match:
            medicine_candidate = line[:dosage_match.start()].strip()
            # Clean up common prefixes
            medicine_candidate = re.sub(r"^\d+[\.\)]\s*", "", medicine_candidate)
            medicine_candidate = re.sub(r"^(?:Tab|Cap|Syp|Inj)\.?\s*", "", medicine_candidate, flags=re.I)
            medicine_candidate = medicine_candidate.strip(" .,;:")
            if 3 <= len(medicine_candidate) <= 50:
                results.append((medicine_candidate, p.dosage, p.frequency))

    return results


def clean_medicine_name(name: str) -> str:
    """
    Normalise a medicine name:
    - Title case
    - Remove trailing punctuation
    - Strip common OCR artifacts
    """
    # Remove non-alphabetic leading/trailing characters
    name = re.sub(r"^[^A-Za-z]+", "", name)
    name = re.sub(r"[^A-Za-z0-9\s\-]+$", "", name)
    # Collapse spaces
    name = re.sub(r"\s+", " ", name).strip()
    # Title case
    return name.title()
