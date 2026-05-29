"""
Dosage Safety Service
Checks prescribed dosages against safe limits, age-based rules,
and weight-based rules. Uses rule-based logic + LLM for edge cases.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Dosage safety rules (rule-based layer) ────────────────────────────────
# Format: medicine_name_lower -> {max_daily_mg, unit, child_max_mg_per_kg}
DOSAGE_RULES: Dict[str, Dict[str, Any]] = {
    "paracetamol": {
        "max_daily_mg": 4000,
        "single_dose_max_mg": 1000,
        "unit": "mg",
        "child_max_mg_per_kg_per_dose": 15,
        "child_max_mg_per_kg_per_day": 60,
        "notes": "Do not exceed 4g/day in adults; reduce in hepatic impairment.",
    },
    "acetaminophen": {  # alias
        "max_daily_mg": 4000,
        "single_dose_max_mg": 1000,
        "unit": "mg",
        "child_max_mg_per_kg_per_dose": 15,
        "child_max_mg_per_kg_per_day": 60,
        "notes": "Same as paracetamol.",
    },
    "ibuprofen": {
        "max_daily_mg": 2400,
        "single_dose_max_mg": 800,
        "unit": "mg",
        "child_max_mg_per_kg_per_dose": 10,
        "child_max_mg_per_kg_per_day": 40,
        "notes": "Take with food. Avoid in renal impairment.",
    },
    "amoxicillin": {
        "max_daily_mg": 3000,
        "single_dose_max_mg": 1000,
        "unit": "mg",
        "child_max_mg_per_kg_per_day": 90,
        "notes": "High-dose regimen used for resistant pneumonia.",
    },
    "metformin": {
        "max_daily_mg": 2550,
        "single_dose_max_mg": 1000,
        "unit": "mg",
        "notes": "Reduce or avoid in eGFR <30. Risk of lactic acidosis.",
    },
    "aspirin": {
        "max_daily_mg": 4000,
        "single_dose_max_mg": 1000,
        "unit": "mg",
        "child_contraindicated": True,
        "child_note": "Contraindicated in children <16 due to Reye's syndrome risk.",
        "notes": "Antiplatelet dose: 75-100mg/day.",
    },
    "cetirizine": {
        "max_daily_mg": 10,
        "single_dose_max_mg": 10,
        "unit": "mg",
        "notes": "Once daily dosing recommended.",
    },
    "omeprazole": {
        "max_daily_mg": 80,
        "single_dose_max_mg": 40,
        "unit": "mg",
        "notes": "40mg once daily for erosive esophagitis; 20mg for maintenance.",
    },
    "atorvastatin": {
        "max_daily_mg": 80,
        "single_dose_max_mg": 80,
        "unit": "mg",
        "notes": "Higher doses increase myopathy risk. Take at bedtime.",
    },
    "amlodipine": {
        "max_daily_mg": 10,
        "single_dose_max_mg": 10,
        "unit": "mg",
        "notes": "Start at 5mg; titrate up if needed.",
    },
    "diazepam": {
        "max_daily_mg": 40,
        "single_dose_max_mg": 10,
        "unit": "mg",
        "notes": "Schedule IV controlled substance. High addiction risk.",
        "elderly_caution": "Reduce dose by 50% in elderly.",
    },
    "lisinopril": {
        "max_daily_mg": 40,
        "single_dose_max_mg": 40,
        "unit": "mg",
        "notes": "Monitor potassium; avoid in pregnancy (Cat D).",
    },
}


@dataclass
class DosageCheckResult:
    """Result of a dosage safety evaluation."""
    medicine_name: str
    prescribed_dose_mg: Optional[float]
    max_safe_dose_mg: Optional[float]
    is_safe: bool
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    llm_assessment: str = ""


class DosageService:
    """
    Evaluates dosage safety:
    1. Rule-based check against DOSAGE_RULES.
    2. Age/weight-adjusted checks.
    3. LLM fallback for unknown medicines.
    """

    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def check_dosage(
        self,
        medicine_name: str,
        prescribed_dose_str: str,
        patient_age: Optional[int] = None,
        patient_weight_kg: Optional[float] = None,
        frequency_per_day: int = 1,
    ) -> DosageCheckResult:
        """
        Main dosage safety check.
        Parses the prescribed dose string, applies rules, and returns an assessment.
        """
        # Parse dose from string like "500mg" or "1g"
        prescribed_mg = self._parse_dose_mg(prescribed_dose_str)
        daily_mg = prescribed_mg * frequency_per_day if prescribed_mg else None

        key = medicine_name.lower().strip()
        rule = DOSAGE_RULES.get(key)

        warnings: List[str] = []
        recommendations: List[str] = []
        is_safe = True

        if rule:
            max_daily = rule.get("max_daily_mg")
            max_single = rule.get("single_dose_max_mg")
            notes = rule.get("notes", "")

            # Single dose check
            if prescribed_mg and max_single and prescribed_mg > max_single:
                is_safe = False
                warnings.append(
                    f"Single dose {prescribed_mg}mg exceeds maximum recommended "
                    f"single dose of {max_single}mg for {medicine_name}."
                )

            # Daily dose check
            if daily_mg and max_daily and daily_mg > max_daily:
                is_safe = False
                warnings.append(
                    f"Daily dose {daily_mg}mg ({frequency_per_day}x{prescribed_mg}mg) "
                    f"exceeds maximum recommended daily dose of {max_daily}mg for {medicine_name}."
                )

            # Age checks
            if patient_age is not None:
                is_safe, w, r = self._apply_age_rules(
                    rule, medicine_name, prescribed_mg, patient_age, is_safe, patient_weight_kg
                )
                warnings.extend(w)
                recommendations.extend(r)

            # Elderly check
            if patient_age and patient_age >= 65:
                elderly_caution = rule.get("elderly_caution")
                if elderly_caution:
                    warnings.append(f"Elderly caution: {elderly_caution}")

            if notes:
                recommendations.append(f"Clinical note: {notes}")

            return DosageCheckResult(
                medicine_name=medicine_name,
                prescribed_dose_mg=prescribed_mg,
                max_safe_dose_mg=max_daily,
                is_safe=is_safe,
                warnings=warnings,
                recommendations=recommendations,
            )

        else:
            # LLM fallback for unknown medicines
            logger.info(f"No rule for '{medicine_name}', using LLM dosage check.")
            llm_result = await self._llm_dosage_check(
                medicine_name, prescribed_dose_str, patient_age
            )
            return DosageCheckResult(
                medicine_name=medicine_name,
                prescribed_dose_mg=prescribed_mg,
                max_safe_dose_mg=None,
                is_safe=llm_result.get("is_safe", True),
                warnings=llm_result.get("warnings", []),
                recommendations=llm_result.get("recommendations", []),
                llm_assessment=llm_result.get("assessment", ""),
            )

    # ── Internal helpers ───────────────────────────────────────────────────

    def _parse_dose_mg(self, dose_str: str) -> Optional[float]:
        """
        Parse a dose string to milligrams.
        Handles: "500mg", "1g", "0.5g", "250 mg", "1000MG".
        """
        if not dose_str:
            return None
        dose_str = dose_str.strip()
        match = re.search(r"(\d+(?:\.\d+)?)\s*(mg|g|mcg|µg)", dose_str, re.IGNORECASE)
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2).lower()
        if unit == "g":
            return value * 1000
        elif unit in ("mcg", "µg"):
            return value / 1000
        return value

    def _apply_age_rules(
        self,
        rule: Dict[str, Any],
        medicine_name: str,
        prescribed_mg: Optional[float],
        patient_age: int,
        is_safe: bool,
        weight_kg: Optional[float],
    ):
        """Apply age-specific dosage rules."""
        warnings = []
        recommendations = []

        # Child contraindicated
        if patient_age < 16 and rule.get("child_contraindicated"):
            is_safe = False
            warnings.append(
                rule.get("child_note") or
                f"{medicine_name} is contraindicated in children under 16."
            )
            return is_safe, warnings, recommendations

        # Paediatric weight-based dosing
        if patient_age < 12 and weight_kg and prescribed_mg:
            per_kg_per_dose = rule.get("child_max_mg_per_kg_per_dose")
            if per_kg_per_dose:
                max_child_dose = per_kg_per_dose * weight_kg
                if prescribed_mg > max_child_dose:
                    is_safe = False
                    warnings.append(
                        f"Paediatric dose {prescribed_mg}mg exceeds weight-based max "
                        f"({per_kg_per_dose}mg/kg × {weight_kg}kg = {max_child_dose}mg) "
                        f"for {medicine_name}."
                    )
        elif patient_age < 12:
            recommendations.append(
                f"Paediatric dosing for {medicine_name} should be weight-based. "
                "Consult a paediatrician."
            )

        return is_safe, warnings, recommendations

    async def _llm_dosage_check(
        self,
        medicine_name: str,
        dose_str: str,
        patient_age: Optional[int],
    ) -> Dict[str, Any]:
        """Use OpenAI to assess dosage safety for unknown medicines."""
        age_ctx = f"Patient age: {patient_age} years." if patient_age else "Patient age unknown."
        prompt = (
            f"As a clinical pharmacist, evaluate the safety of this prescription:\n"
            f"Medicine: {medicine_name}\n"
            f"Prescribed dose: {dose_str}\n"
            f"{age_ctx}\n\n"
            "Return ONLY a JSON object with keys: "
            "'is_safe' (bool), 'warnings' (list of strings), "
            "'recommendations' (list of strings), 'assessment' (string summary)."
        )

        try:
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a clinical pharmacist. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            return json.loads(raw)
        except Exception as exc:
            logger.error(f"LLM dosage check failed: {exc}")
            return {"is_safe": True, "warnings": [], "recommendations": [], "assessment": ""}
