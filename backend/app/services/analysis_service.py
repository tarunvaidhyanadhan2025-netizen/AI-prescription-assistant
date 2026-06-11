"""
AnalysisService — pure AI, no YAML, no templates, no vector store.

Flow per prescription (2 LLM calls total):
  Call 1 — refine_ocr()              : clean medicine list from raw OCR
  Call 2 — analyse_medicines_batch() : all medicines in one prompt

If the AI fails, errors are surfaced clearly to the caller — no silent fallbacks.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from app.schemas.responses import MedicineAnalysis
from app.services.llm_service import LLMService
from app.utils.logger import get_logger

logger = get_logger(__name__)

LANGUAGE_NAMES = {
    "en": "English", "ta": "Tamil", "hi": "Hindi", "fr": "French",
    "es": "Spanish", "de": "German", "zh": "Chinese", "ar": "Arabic",
}

# ── OCR Refinement Prompt ─────────────────────────────────────────────────────

_OCR_REFINE_SYSTEM = """You are a clinical pharmacist and OCR expert.
Your ONLY job: extract the list of medicines actually prescribed to the patient.

CRITICAL RULES:
- Include ONLY medicines from the numbered prescription list (e.g. 1) Tab. Abciximab, 2) Tab. Vomilast).
- Do NOT include: patient name, age, address, diagnosis, doctor name, hospital name, city names,
  sub-ingredients listed under a medicine (e.g. "Doxylamine 10mg + Pyridoxine 10mg" under Vomilast),
  dosage instructions, BP readings, weight, height, BMI, or any non-medicine text.
- Each medicine should appear EXACTLY ONCE — use its brand name as prescribed.
- Correct obvious OCR errors in medicine names.
- Return ONLY valid JSON. No preamble, no markdown."""

_OCR_REFINE_HUMAN = """
Raw OCR text from prescription:
---
{raw_text}
---

Extract ONLY the medicines from the numbered prescription list (the "R" / Rx section).
Do NOT include sub-ingredients, demographics, or non-medicine text.

Return ONLY this JSON:
{{
  "medicines": [
    {{
      "name": "<corrected medicine name exactly as prescribed, e.g. Tab. Abciximab>",
      "original_ocr": "<raw OCR text>",
      "dosage": "<dosage if visible, else empty>",
      "frequency": "<frequency if visible, else empty>",
      "confidence": <0.0-1.0>
    }}
  ],
  "patient_info": {{"age": <null or int>, "diagnosis": "<or empty>"}},
  "doctor_name": "<or empty>",
  "notes": "<special instructions like bed rest, diet advice>"
}}
"""

# ── Batch Analysis Prompt ─────────────────────────────────────────────────────

_BATCH_SYSTEM = """You are a senior clinical pharmacist providing accurate, evidence-based medicine information.

CRITICAL RULES:
1. Respond ONLY with a valid JSON array. No preamble, no explanation outside JSON.
2. Analyse every medicine listed using your clinical training knowledge.
3. For Indian brand names, describe the actual active ingredient
   (e.g. Gestakind = Isoxsuprine SR uterine relaxant, Vomilast = Doxylamine+Pyridoxine+Folic Acid,
   Zoclar = Clarithromycin, Pan = Pantoprazole, Combiflam = Ibuprofen+Paracetamol).
4. If you genuinely do not know a medicine, set:
   explanation = "This medicine could not be identified. Please consult your pharmacist."
   drug_class = "Unknown"
   severity_level = "unknown"
   Do NOT invent or hallucinate information.
5. severity_level must be exactly one of: low, medium, high, critical, unknown.
6. Return exactly one object per medicine in the same order as the input list."""

_BATCH_HUMAN = """
Patient Age: {patient_age}
Language for explanations: {language}

Medicines to analyse (ALL of them, in order):
{medicine_list}

Return ONLY a valid JSON array — one object per medicine, preserving input order:
[
  {{
    "medicine_name": "<name as given>",
    "explanation": "<2-3 sentence patient-friendly description>",
    "use_case": "<what conditions it treats — be specific>",
    "mechanism": "<how it works in the body>",
    "how_to_take": "<when and how to take it>",
    "drug_class": "<specific drug class>",
    "side_effects": ["<common side effect>"],
    "serious_side_effects": ["<serious side effect if any>"],
    "causes_drowsiness": <true|false>,
    "drowsiness_note": "<explain if drowsy, else empty string>",
    "dosage_info": "<typical dose with mg and frequency>",
    "dosage_safe": <true|false>,
    "dosage_notes": ["<dosage note>"],
    "age_warnings": ["<age-specific warning if relevant>"],
    "contraindications": ["<when not to take>"],
    "alternatives": ["<alternative medicine>"],
    "severity_level": "<low|medium|high|critical|unknown>"
  }}
]
"""

# ── Single-medicine fallback (used when batch returns wrong count) ─────────────

_SINGLE_SYSTEM = """You are a senior clinical pharmacist. Respond ONLY with valid JSON. No preamble."""

_SINGLE_HUMAN = """
Medicine: {medicine_name}
Patient Age: {patient_age}
Language: {language}

Use your clinical knowledge. For Indian brand names, identify the active ingredient and describe that.
If unrecognised, set explanation = "This medicine could not be identified. Consult your pharmacist."

Return ONLY a valid JSON object:
{{
  "explanation": "<2-3 sentence patient-friendly description>",
  "use_case": "<what conditions it treats>",
  "mechanism": "<how it works in the body>",
  "how_to_take": "<when and how to take it>",
  "drug_class": "<specific drug class>",
  "side_effects": ["<common side effect>"],
  "serious_side_effects": ["<serious side effect if any>"],
  "causes_drowsiness": <true|false>,
  "drowsiness_note": "<explain if drowsy, else empty string>",
  "dosage_info": "<typical dose with mg and frequency>",
  "dosage_safe": <true|false>,
  "dosage_notes": ["<dosage note>"],
  "age_warnings": ["<age-specific warning if relevant>"],
  "contraindications": ["<when not to take>"],
  "alternatives": ["<alternative medicine>"],
  "severity_level": "<low|medium|high|critical|unknown>"
}}
"""


# ── Type coercers ─────────────────────────────────────────────────────────────

def _s(v, d: str = "") -> str:
    if v is None: return d
    if isinstance(v, list): return " ".join(str(x) for x in v).strip() or d
    return str(v).strip() or d

def _l(v) -> list:
    if not v: return []
    if isinstance(v, str): return [v.strip()] if v.strip() else []
    if isinstance(v, list): return [str(x).strip() for x in v if x and str(x).strip()]
    return []

def _b(v, d: bool = False) -> bool:
    if isinstance(v, bool): return v
    if isinstance(v, str): return v.lower() in ("true", "yes", "1")
    return d

def _sev(v: Any) -> str:
    return v if isinstance(v, str) and v in ("low", "medium", "high", "critical", "unknown") else "unknown"


# ── Service ───────────────────────────────────────────────────────────────────

class AnalysisService:
    """
    Pure-AI analysis service.

    - No YAML templates
    - No vector store
    - No local drug class lookups
    - AI errors are surfaced explicitly, not swallowed
    """

    def __init__(self, llm_service: LLMService):
        self._llm = llm_service

    # ── Public API ────────────────────────────────────────────────────────────

    async def refine_ocr(
        self,
        raw_text: str,
        initial_medicines: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Call 1 of 2: send raw OCR text to AI, get back clean medicine list.
        Returns structured dict. On AI failure, raises — caller surfaces the error.
        """
        if not raw_text.strip():
            return {
                "medicines": [{"name": m, "original_ocr": m, "confidence": 0.5}
                              for m in (initial_medicines or [])],
                "patient_info": {"age": None, "diagnosis": ""},
                "doctor_name": "",
                "notes": "",
            }

        result = await self._llm.complete_json(
            system_prompt=_OCR_REFINE_SYSTEM,
            user_prompt=_OCR_REFINE_HUMAN.format(raw_text=raw_text[:4000]),
            fallback=None,
            temperature=0.0,
        )

        if result is None:
            raise RuntimeError(
                "AI failed to process the prescription OCR. "
                "The AI provider returned no response. Check your API key and quota."
            )

        return result

    async def analyse_medicines_batch(
        self,
        medicine_names: List[str],
        patient_age: Optional[int] = None,
        language: str = "en",
    ) -> List[MedicineAnalysis]:
        """
        Call 2 of 2: analyse ALL medicines in a single AI call.
        Falls back to per-medicine calls only if the batch returns wrong count.
        Raises on total AI failure — error is surfaced to the user.
        """
        if not medicine_names:
            return []

        lang_name = LANGUAGE_NAMES.get(language, "English")
        age_str = str(patient_age) if patient_age is not None else "Not specified"

        medicine_list = "\n".join(
            f"{i + 1}. {name}" for i, name in enumerate(medicine_names)
        )

        raw = await self._llm.complete(
            system_prompt=_BATCH_SYSTEM,
            user_prompt=_BATCH_HUMAN.format(
                patient_age=age_str,
                language=lang_name,
                medicine_list=medicine_list,
            ),
            max_tokens=min(8192, 800 + len(medicine_names) * 600),
        )

        if not raw or not raw.strip():
            raise RuntimeError(
                "AI returned an empty response during medicine analysis. "
                "Check your API key, quota, and model name."
            )

        batch_results = self._llm.parse_json(raw, fallback=None)

        if isinstance(batch_results, list) and len(batch_results) == len(medicine_names):
            logger.info(f"Batch analysis OK: {len(medicine_names)} medicines in 1 call")
            return [
                self._build(item, medicine_names[i])
                for i, item in enumerate(batch_results)
            ]

        # Wrong count — fall back per-medicine
        logger.warning(
            f"Batch returned {len(batch_results) if isinstance(batch_results, list) else 'invalid'} "
            f"results for {len(medicine_names)} medicines — falling back to individual calls"
        )
        return await self._individual_fallback(medicine_names, age_str, lang_name)

    async def analyse_medicine(
        self,
        medicine_name: str,
        patient_age: Optional[int] = None,
        language: str = "en",
    ) -> MedicineAnalysis:
        """Single-medicine analysis. Delegates to batch method."""
        results = await self.analyse_medicines_batch(
            [medicine_name], patient_age=patient_age, language=language
        )
        return results[0]

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _individual_fallback(
        self,
        medicine_names: List[str],
        age_str: str,
        lang_name: str,
    ) -> List[MedicineAnalysis]:
        results = []
        for name in medicine_names:
            raw = await self._llm.complete_json(
                system_prompt=_SINGLE_SYSTEM,
                user_prompt=_SINGLE_HUMAN.format(
                    medicine_name=name,
                    patient_age=age_str,
                    language=lang_name,
                ),
                fallback=None,
            )
            if raw:
                results.append(self._build(raw, name))
            else:
                results.append(self._ai_error(name, "AI returned no response for this medicine."))
        return results

    def _build(self, result: Dict, medicine_name: str) -> MedicineAnalysis:
        return MedicineAnalysis(
            medicine_name=medicine_name,
            explanation=_s(result.get("explanation")),
            use_case=_s(result.get("use_case")),
            mechanism=_s(result.get("mechanism")),
            how_to_take=_s(result.get("how_to_take")),
            drug_class=_s(result.get("drug_class")),
            side_effects=_l(result.get("side_effects"))[:8],
            serious_side_effects=_l(result.get("serious_side_effects"))[:5],
            causes_drowsiness=_b(result.get("causes_drowsiness")),
            drowsiness_note=_s(result.get("drowsiness_note")),
            dosage_info=_s(result.get("dosage_info")),
            dosage_safe=_b(result.get("dosage_safe"), True),
            dosage_notes=_l(result.get("dosage_notes")),
            age_warnings=_l(result.get("age_warnings")),
            contraindications=_l(result.get("contraindications"))[:6],
            alternatives=_l(result.get("alternatives"))[:5],
            severity_level=_sev(result.get("severity_level")),
            rag_sources=[],
            generated_by=self._llm.provider_name,
        )

    @staticmethod
    def _ai_error(medicine_name: str, reason: str) -> MedicineAnalysis:
        return MedicineAnalysis(
            medicine_name=medicine_name,
            explanation=f"AI Error: {reason}",
            use_case="",
            mechanism="",
            how_to_take="",
            drug_class="",
            side_effects=[],
            serious_side_effects=[],
            causes_drowsiness=False,
            drowsiness_note="",
            dosage_info="Consult your pharmacist.",
            dosage_safe=True,
            dosage_notes=[],
            age_warnings=[],
            contraindications=[],
            alternatives=[],
            severity_level="unknown",
            rag_sources=[],
            generated_by="error",
        )
