"""
Warning Service
Generates age-specific warnings, drowsiness alerts, contraindication
flags, pregnancy/lactation notes, and general safety advisories.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Static warning rules ──────────────────────────────────────────────────
# medicine_name_lower → warning config
STATIC_WARNINGS: Dict[str, Dict[str, Any]] = {
    "aspirin": {
        "pediatric": {
            "age_max": 15,
            "message": "Aspirin is contraindicated in children under 16 due to risk of Reye's syndrome, a rare but life-threatening condition.",
            "severity": "critical",
        },
        "pregnancy": "Avoid in third trimester; may cause premature closure of the ductus arteriosus.",
        "elderly": "Increased GI bleeding risk. Use lowest effective dose with a PPI.",
    },
    "diazepam": {
        "pediatric": {"age_max": 6, "message": "Use with extreme caution in infants. Risk of respiratory depression.", "severity": "high"},
        "pregnancy": "Category D – known fetal risk. Avoid unless benefits outweigh risks.",
        "elderly": "Increased risk of falls, cognitive impairment, and paradoxical agitation. Reduce dose by 50%.",
        "drowsiness": True,
        "drowsiness_note": "Causes significant drowsiness and sedation. Do NOT drive or operate machinery.",
    },
    "metformin": {
        "pediatric": {"age_min": 10, "message": "Only approved for children ≥10 years for type 2 diabetes.", "severity": "medium"},
        "pregnancy": "Generally considered safe but consult endocrinologist.",
        "elderly": "Reduce dose if eGFR 30–45. Contraindicated if eGFR <30.",
        "renal_note": "Monitor kidney function regularly.",
    },
    "warfarin": {
        "pediatric": {"age_max": 18, "message": "Anticoagulation in children requires specialist management.", "severity": "high"},
        "pregnancy": "Category X – known fetal harm (embryopathy in first trimester). Absolutely avoid.",
        "elderly": "High bleeding risk. Requires close INR monitoring.",
        "diet_interaction": "Avoid sudden changes in vitamin K intake (leafy greens).",
    },
    "codeine": {
        "pediatric": {"age_max": 12, "message": "Contraindicated in children <12. Risk of respiratory depression due to ultra-rapid CYP2D6 metabolism.", "severity": "critical"},
        "breastfeeding": "Avoid – can cause fatal neonatal morphine toxicity.",
        "drowsiness": True,
        "drowsiness_note": "Causes drowsiness. Avoid alcohol and CNS depressants.",
    },
    "ibuprofen": {
        "pediatric": {"age_min": 3, "message": "Not recommended for infants <3 months.", "severity": "high"},
        "pregnancy": "Avoid after 20 weeks – risk of oligohydramnios and premature ductus closure.",
        "elderly": "Risk of GI bleeding, renal impairment, and fluid retention. Use with caution.",
        "renal_note": "Avoid in renal impairment (eGFR <30).",
    },
    "tetracycline": {
        "pediatric": {"age_max": 8, "message": "Contraindicated in children <8 years – causes permanent tooth discolouration and bone growth inhibition.", "severity": "high"},
        "pregnancy": "Category D – tooth/bone effects on fetus. Avoid.",
    },
    "fluoroquinolones": {
        "pediatric": {"age_max": 18, "message": "Generally avoided in children and adolescents due to cartilage toxicity risk.", "severity": "medium"},
        "drowsiness": False,
    },
    "cetirizine": {
        "drowsiness": True,
        "drowsiness_note": "May cause drowsiness in some patients, especially at higher doses.",
        "elderly": "May cause urinary retention in elderly males with BPH.",
    },
    "amitriptyline": {
        "drowsiness": True,
        "drowsiness_note": "Causes significant drowsiness and anticholinergic effects. Do NOT drive.",
        "pediatric": {"age_max": 12, "message": "Not recommended in children <12 for depression.", "severity": "medium"},
        "elderly": "High-risk drug in elderly (Beers Criteria). Risk of falls, confusion, arrhythmias.",
        "pregnancy": "Use only if benefit outweighs risk.",
    },
    "lithium": {
        "pregnancy": "Category D – neonatal toxicity. Avoid in first trimester.",
        "elderly": "Narrow therapeutic index. Frequent monitoring required.",
        "renal_note": "Contraindicated in renal failure. Hydration is critical.",
    },
}

# Medicines known to cause drowsiness
DROWSY_MEDICINES = {
    "diazepam", "lorazepam", "alprazolam", "clonazepam", "zolpidem",
    "diphenhydramine", "hydroxyzine", "cetirizine", "chlorphenamine",
    "promethazine", "amitriptyline", "nortriptyline", "doxepin",
    "quetiapine", "olanzapine", "risperidone", "haloperidol",
    "codeine", "tramadol", "morphine", "oxycodone", "fentanyl",
    "gabapentin", "pregabalin", "phenobarbital", "carbamazepine",
    "valproate", "clonidine", "mirtazapine", "trazodone",
    "baclofen", "cyclobenzaprine", "carisoprodol", "methocarbamol",
    "doxylamine", "melatonin",
}


@dataclass
class WarningResult:
    """Aggregated warning output for a medicine."""
    medicine_name: str
    age_warnings: List[str] = field(default_factory=list)
    pregnancy_warning: str = ""
    breastfeeding_warning: str = ""
    elderly_warning: str = ""
    drowsiness_warning: str = ""
    causes_drowsiness: bool = False
    severity_level: str = "low"
    additional_notes: List[str] = field(default_factory=list)
    llm_generated: bool = False


class WarningService:
    """
    Generates safety warnings:
    1. Rule-based static warnings from STATIC_WARNINGS.
    2. DROWSY_MEDICINES set for quick drowsiness detection.
    3. LLM-generated warnings for unknown medicines.
    """

    def __init__(self):
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def get_warnings(
        self,
        medicine_name: str,
        medicine_data: Dict[str, Any],
        patient_age: Optional[int] = None,
    ) -> WarningResult:
        """
        Generate comprehensive warnings for a medicine and patient context.
        """
        key = medicine_name.lower().strip()
        static = STATIC_WARNINGS.get(key, {})

        age_warnings: List[str] = []
        severity = "low"

        # ── Age-specific warnings ──────────────────────────────────────────
        if patient_age is not None:
            ped = static.get("pediatric")
            if ped and isinstance(ped, dict):
                age_max = ped.get("age_max")
                age_min = ped.get("age_min")
                triggered = False
                if age_max and patient_age <= age_max:
                    triggered = True
                elif age_min and patient_age < age_min:
                    triggered = True
                if triggered:
                    age_warnings.append(ped["message"])
                    sev = ped.get("severity", "medium")
                    severity = self._max_severity(severity, sev)

            # Elderly warnings
            if patient_age >= 65:
                elderly_warn = static.get("elderly", "")
                if elderly_warn:
                    age_warnings.append(f"Elderly (≥65): {elderly_warn}")
                    severity = self._max_severity(severity, "medium")

        # ── Drowsiness ────────────────────────────────────────────────────
        causes_drowsiness = (
            key in DROWSY_MEDICINES
            or static.get("drowsiness", False)
            or medicine_data.get("causes_drowsiness", False)
        )
        drowsiness_warning = ""
        if causes_drowsiness:
            drowsiness_warning = static.get(
                "drowsiness_note",
                f"{medicine_name} may cause drowsiness. Avoid driving or operating heavy machinery.",
            )

        # ── Other warnings from data ───────────────────────────────────────
        additional_notes = []
        for note_key in ("renal_note", "diet_interaction"):
            note = static.get(note_key)
            if note:
                additional_notes.append(note)

        # Pregnancy / breastfeeding
        pregnancy_warning = static.get("pregnancy", "")
        breastfeeding_warning = static.get("breastfeeding", "")
        elderly_warning = static.get("elderly", "")

        # ── LLM enrichment if no static data ─────────────────────────────
        llm_generated = False
        if not static and not causes_drowsiness:
            try:
                llm_w = await self._llm_warnings(medicine_name, patient_age)
                age_warnings.extend(llm_w.get("age_warnings", []))
                if llm_w.get("causes_drowsiness"):
                    causes_drowsiness = True
                    drowsiness_warning = llm_w.get("drowsiness_note", "")
                if not pregnancy_warning:
                    pregnancy_warning = llm_w.get("pregnancy_warning", "")
                severity = self._max_severity(severity, llm_w.get("severity_level", "low"))
                llm_generated = True
            except Exception as exc:
                logger.warning(f"LLM warning enrichment failed for '{medicine_name}': {exc}")

        return WarningResult(
            medicine_name=medicine_name,
            age_warnings=age_warnings,
            pregnancy_warning=pregnancy_warning,
            breastfeeding_warning=breastfeeding_warning,
            elderly_warning=elderly_warning,
            drowsiness_warning=drowsiness_warning,
            causes_drowsiness=causes_drowsiness,
            severity_level=severity,
            additional_notes=additional_notes,
            llm_generated=llm_generated,
        )

    # ── Internal ───────────────────────────────────────────────────────────

    @staticmethod
    def _max_severity(current: str, new: str) -> str:
        rank = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        return new if rank.get(new, 0) > rank.get(current, 0) else current

    async def _llm_warnings(
        self, medicine_name: str, patient_age: Optional[int]
    ) -> Dict[str, Any]:
        age_ctx = f"The patient is {patient_age} years old." if patient_age else ""
        prompt = (
            f"As a clinical pharmacist, provide safety warnings for {medicine_name}. "
            f"{age_ctx} "
            "Return ONLY a JSON object with keys: "
            "'age_warnings' (list), 'causes_drowsiness' (bool), "
            "'drowsiness_note' (str), 'pregnancy_warning' (str), "
            "'severity_level' (low/medium/high/critical)."
        )
        try:
            response = await self._client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a clinical pharmacist. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.0,
                max_tokens=400,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content or "{}")
        except Exception as exc:
            logger.error(f"LLM warning call failed: {exc}")
            return {}
