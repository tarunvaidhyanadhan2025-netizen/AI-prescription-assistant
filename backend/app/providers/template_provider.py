"""
Template provider — serves responses from YAML templates.
Zero external dependencies. Works with no API keys.
"""
from __future__ import annotations

from typing import List, Optional

from app.providers.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TemplateProvider(BaseLLMProvider):
    """
    Dummy LLM provider used in TEMPLATE mode.
    complete() is never called in template mode — TemplateService handles it.
    embed() uses local sentence-transformers if available, else returns zeros.
    """

    def __init__(self):
        self._embed_model = None
        self._embed_tried = False

    @property
    def name(self) -> str:
        return "template"

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        import json
        import re
        from app.templates.template_service import TemplateService, _NAME_TO_CLASS
        
        svc = TemplateService()

        # 1. OCR Refinement
        if "clinical pharmacist and OCR expert" in system_prompt or "OCR" in system_prompt:
            raw_text_lower = user_prompt.lower()
            detected = []
            seen = set()
            for med_key in _NAME_TO_CLASS.keys():
                pattern = rf"\b{re.escape(med_key)}\b"
                if re.search(pattern, raw_text_lower):
                    display_name = med_key.capitalize()
                    if med_key not in seen:
                        seen.add(med_key)
                        detected.append({
                            "name": display_name,
                            "original_ocr": display_name,
                            "dosage": "500mg" if "500mg" in user_prompt else "",
                            "frequency": "",
                            "confidence": 0.95
                        })
            
            if not detected:
                # Default fallback if nothing matches
                detected = [{
                    "name": "Paracetamol",
                    "original_ocr": "Paracetamol",
                    "dosage": "",
                    "frequency": "",
                    "confidence": 0.5
                }]

            result_dict = {
                "medicines": detected,
                "patient_info": {"age": None, "diagnosis": ""},
                "doctor_name": "",
                "notes": ""
            }
            return LLMResponse(
                content=json.dumps(result_dict),
                provider=self.name,
                model="template-ocr",
            )

        # 2. Batch / Single Medicine Analysis
        patient_age = None
        age_match = re.search(r"Patient Age:\s*(\d+)", user_prompt)
        if age_match:
            patient_age = int(age_match.group(1))

        language = "en"
        lang_match = re.search(r"Language(?:\s+for\s+explanations)?:\s*(\w+)", user_prompt, re.IGNORECASE)
        if lang_match:
            lang_name = lang_match.group(1).strip()
            from app.services.analysis_service import LANGUAGE_NAMES
            name_to_code = {v.lower(): k for k, v in LANGUAGE_NAMES.items()}
            language = name_to_code.get(lang_name.lower(), "en")

        medicine_names = []
        for line in user_prompt.splitlines():
            line = line.strip()
            match = re.match(r"^\d+\.\s*(.+)$", line)
            if match:
                medicine_names.append(match.group(1).strip())

        if not medicine_names:
            single_match = re.search(r"Medicine:\s*(.+)$", user_prompt, re.MULTILINE)
            if single_match:
                medicine_names.append(single_match.group(1).strip())

        if not medicine_names:
            medicine_names = ["Paracetamol"]

        analyses = []
        for name in medicine_names:
            drug_class = _NAME_TO_CLASS.get(name.lower(), "Prescription Medicine")
            exp_data = svc.get_explanation(name, drug_class=drug_class, language=language)
            warn_data = svc.get_warnings(name, drug_class=drug_class, patient_age=patient_age)
            dose_data = svc.get_dosage(name, drug_class=drug_class, patient_age=patient_age)

            analyses.append({
                "medicine_name": name,
                "explanation": exp_data.get("explanation", ""),
                "use_case": exp_data.get("use_case", ""),
                "mechanism": exp_data.get("mechanism", ""),
                "how_to_take": exp_data.get("how_to_take", ""),
                "drug_class": drug_class,
                "side_effects": warn_data.get("side_effects", []),
                "serious_side_effects": warn_data.get("serious_side_effects", []),
                "causes_drowsiness": warn_data.get("causes_drowsiness", False),
                "drowsiness_note": warn_data.get("drowsiness_note", ""),
                "dosage_info": dose_data.get("dosage_info", ""),
                "dosage_safe": True,
                "dosage_notes": [dose_data["notes"]] if dose_data.get("notes") else [],
                "age_warnings": warn_data.get("age_warnings", []),
                "contraindications": warn_data.get("contraindications", []),
                "alternatives": [],
                "severity_level": warn_data.get("severity_level", "low")
            })

        if "JSON array" in system_prompt or "array" in system_prompt.lower():
            content = json.dumps(analyses)
        else:
            content = json.dumps(analyses[0])

        return LLMResponse(
            content=content,
            provider=self.name,
            model="template-analysis",
        )

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Try sentence-transformers; fall back to zero vectors."""
        if not self._embed_tried:
            self._embed_tried = True
            try:
                from sentence_transformers import SentenceTransformer
                from app.core.settings import settings
                self._embed_model = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info("Template provider: loaded local embedding model.")
            except Exception as e:
                logger.warning(f"Template provider: local embeddings unavailable ({e}).")

        if self._embed_model is not None:
            import asyncio
            loop = asyncio.get_event_loop()
            vectors = await loop.run_in_executor(
                None, lambda: self._embed_model.encode(texts, convert_to_numpy=True)
            )
            return [v.tolist() for v in vectors]

        # Last resort: zero vectors (384-dim matches MiniLM)
        return [[0.0] * 384 for _ in texts]

    async def health_check(self) -> bool:
        return True
