"""
Safety Agent
Orchestrates safety evaluation for a medicine:
- Side effects
- Drowsiness detection
- Dosage safety check
- Age-specific warnings
- Drug alternatives
Combines WarningService + MedicineService + LLM reasoning.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.medicine_service import MedicineService
from app.services.rag_service import RetrievedContext
from app.services.warning_service import WarningService
from app.utils.logger import get_logger

logger = get_logger(__name__)

SAFETY_SYSTEM_PROMPT = """You are a senior clinical pharmacist providing a comprehensive 
medicine safety evaluation. Use the provided context to give accurate, evidence-based information.
Always prioritise patient safety. Respond ONLY with valid JSON.
"""

SAFETY_HUMAN_PROMPT = """
Medicine: {medicine_name}
Patient Age: {patient_age}
Retrieved Clinical Context:
---
{rag_context}
---
Language for output: {language}

Evaluate the safety of this medicine and return ONLY a JSON object:
{{
  "side_effects": ["<effect1>", "<effect2>", ...],
  "serious_side_effects": ["<serious1>", ...],
  "causes_drowsiness": <true/false>,
  "drowsiness_note": "<note if drowsy>",
  "dosage_info": "<standard dosage summary>",
  "dosage_safe": <true/false>,
  "dosage_notes": ["<note1>", ...],
  "age_warnings": ["<warning1>", ...],
  "alternatives": ["<alt1>", "<alt2>", ...],
  "severity_level": "<low|medium|high|critical>",
  "contraindications": ["<contra1>", ...],
  "important_notes": ["<note1>", ...]
}}
"""


@dataclass
class SafetyReport:
    """Comprehensive safety report for a medicine."""
    medicine_name: str
    side_effects: List[str] = field(default_factory=list)
    serious_side_effects: List[str] = field(default_factory=list)
    causes_drowsiness: bool = False
    drowsiness_note: str = ""
    dosage_info: str = ""
    dosage_safe: bool = True
    dosage_notes: List[str] = field(default_factory=list)
    age_warnings: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    severity_level: str = "low"
    contraindications: List[str] = field(default_factory=list)
    important_notes: List[str] = field(default_factory=list)


class SafetyAgent:
    """
    Safety evaluation agent that combines:
    1. Rule-based WarningService (fast, reliable)
    2. MedicineService local DB lookup
    3. LLM-based comprehensive safety analysis (RAG-augmented)
    """

    def __init__(self, warning_service: WarningService, medicine_service: MedicineService):
        self._warning_service = warning_service
        self._medicine_service = medicine_service
        self._llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            max_tokens=1200,
        )
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", SAFETY_SYSTEM_PROMPT),
            ("human", SAFETY_HUMAN_PROMPT),
        ])
        self._chain = self._prompt | self._llm

    async def evaluate(
        self,
        medicine_name: str,
        context: RetrievedContext,
        patient_age: Optional[int] = None,
        language: str = "en",
    ) -> SafetyReport:
        """
        Run full safety evaluation pipeline.
        Merges rule-based warnings with LLM analysis.
        """
        # Step 1: Get local medicine data
        med_data = await self._medicine_service.get_medicine_info(medicine_name)

        # Step 2: Rule-based warnings
        warning_result = await self._warning_service.get_warnings(
            medicine_name=medicine_name,
            medicine_data=med_data,
            patient_age=patient_age,
        )

        # Step 3: LLM-based analysis with RAG context
        llm_report = await self._llm_safety_analysis(
            medicine_name=medicine_name,
            rag_context=context.combined_text,
            patient_age=patient_age,
            language=language,
        )

        # Step 4: Merge results (rule-based takes priority for critical warnings)
        merged_age_warnings = list(set(
            warning_result.age_warnings + llm_report.get("age_warnings", [])
        ))
        merged_side_effects = list(set(
            med_data.get("side_effects", {}).get("common", []) +
            llm_report.get("side_effects", [])
        ))
        merged_serious = list(set(
            med_data.get("side_effects", {}).get("serious", []) +
            llm_report.get("serious_side_effects", [])
        ))
        merged_alternatives = list(set(
            med_data.get("alternatives", []) +
            llm_report.get("alternatives", [])
        ))[:5]  # Cap at 5 alternatives

        # Drowsiness: either source can flag it
        causes_drowsiness = (
            warning_result.causes_drowsiness
            or llm_report.get("causes_drowsiness", False)
            or med_data.get("causes_drowsiness", False)
        )
        drowsiness_note = (
            warning_result.drowsiness_warning
            or llm_report.get("drowsiness_note", "")
        )

        # Severity: take the highest
        rule_sev = warning_result.severity_level
        llm_sev = llm_report.get("severity_level", "low")
        severity = self._max_severity(rule_sev, llm_sev)

        # Dosage info
        dosage_adult = med_data.get("common_dosages", {}).get("adult", "")
        dosage_info = dosage_adult or llm_report.get("dosage_info", "Consult prescriber.")

        # Age-adjusted dosage
        if patient_age and patient_age < 12:
            ped_dose = med_data.get("common_dosages", {}).get("pediatric", "")
            if ped_dose:
                dosage_info = f"Paediatric: {ped_dose}"
        elif patient_age and patient_age >= 65:
            elderly_dose = med_data.get("common_dosages", {}).get("elderly", "")
            if elderly_dose:
                dosage_info = f"Elderly: {elderly_dose}"

        # Add pregnancy warning to notes if present
        important_notes = list(llm_report.get("important_notes", []))
        if warning_result.pregnancy_warning:
            important_notes.append(f"Pregnancy: {warning_result.pregnancy_warning}")
        if warning_result.breastfeeding_warning:
            important_notes.append(f"Breastfeeding: {warning_result.breastfeeding_warning}")
        for note in warning_result.additional_notes:
            if note not in important_notes:
                important_notes.append(note)

        return SafetyReport(
            medicine_name=medicine_name,
            side_effects=merged_side_effects[:8],
            serious_side_effects=merged_serious[:5],
            causes_drowsiness=causes_drowsiness,
            drowsiness_note=drowsiness_note,
            dosage_info=dosage_info,
            dosage_safe=llm_report.get("dosage_safe", True),
            dosage_notes=llm_report.get("dosage_notes", []),
            age_warnings=merged_age_warnings,
            alternatives=merged_alternatives,
            severity_level=severity,
            contraindications=(
                med_data.get("contraindications", []) +
                llm_report.get("contraindications", [])
            )[:6],
            important_notes=important_notes[:5],
        )

    # ── Internal ───────────────────────────────────────────────────────────

    async def _llm_safety_analysis(
        self,
        medicine_name: str,
        rag_context: str,
        patient_age: Optional[int],
        language: str,
    ) -> Dict[str, Any]:
        """Run LLM safety analysis with RAG-augmented context."""
        age_str = str(patient_age) if patient_age is not None else "Not provided"
        ctx = rag_context or "No additional context available. Use your clinical knowledge."

        try:
            response = await self._chain.ainvoke({
                "medicine_name": medicine_name,
                "patient_age": age_str,
                "rag_context": ctx[:3000],  # Limit context size
                "language": language,
            })
            raw = response.content if hasattr(response, "content") else str(response)
            return self._parse_json(raw)
        except Exception as exc:
            logger.error(f"LLM safety analysis failed for '{medicine_name}': {exc}", exc_info=True)
            return {}

    def _parse_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(l for l in lines if not l.strip().startswith("```"))
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _max_severity(a: str, b: str) -> str:
        rank = {"low": 0, "medium": 1, "high": 2, "critical": 3, "unknown": -1}
        return a if rank.get(a, 0) >= rank.get(b, 0) else b
