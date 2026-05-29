"""
OCR Agent
LangChain-powered agent that refines raw OCR text,
validates extracted medicine names using LLM intelligence,
and corrects common OCR errors in drug names.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a clinical pharmacist and medical OCR expert.
Your job is to:
1. Analyse raw OCR-extracted text from prescription images.
2. Identify ALL medicine names, including misspelled/partially recognised ones.
3. Correct common OCR errors in medicine names (e.g., "Arnoxicillin" → "Amoxicillin").
4. Extract dosage information associated with each medicine.
5. Determine patient details if visible (age, weight).

You MUST respond with valid JSON only. No preamble, no explanation outside JSON.
"""

HUMAN_PROMPT = """
Raw OCR Text:
---
{raw_text}
---

Extract all medicines and return ONLY a JSON object with this exact structure:
{{
  "medicines": [
    {{
      "name": "<corrected medicine name>",
      "original_ocr": "<what OCR extracted>",
      "dosage": "<dosage string or empty>",
      "frequency": "<frequency or empty>",
      "duration": "<duration or empty>",
      "confidence": <0.0 to 1.0>
    }}
  ],
  "patient_info": {{
    "age": <null or integer>,
    "weight_kg": <null or float>,
    "diagnosis": "<detected diagnosis or empty>"
  }},
  "prescription_date": "<date or empty>",
  "doctor_name": "<doctor name or empty>",
  "notes": "<any special instructions>"
}}
"""


@dataclass
class OCRAgentResult:
    """Structured output from the OCR agent."""
    medicines: List[dict] = field(default_factory=list)
    medicine_names: List[str] = field(default_factory=list)
    patient_info: dict = field(default_factory=dict)
    prescription_date: str = ""
    doctor_name: str = ""
    notes: str = ""
    raw_llm_response: str = ""


class OCRAgent:
    """
    LangChain-powered OCR refinement agent.
    Takes raw Tesseract output and uses LLM to:
    - Correct OCR errors in medicine names
    - Extract structured prescription data
    - Identify dosages and frequencies
    """

    def __init__(self):
        self._llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.0,  # Deterministic for medical data
            max_tokens=1500,
        )
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", HUMAN_PROMPT),
        ])
        self._chain = self._prompt | self._llm

    async def process(self, raw_text: str, initial_medicines: Optional[List[str]] = None) -> OCRAgentResult:
        """
        Process OCR text through the LLM agent.

        Args:
            raw_text: Raw text from Tesseract OCR.
            initial_medicines: Pre-detected medicines from regex (for context).

        Returns:
            OCRAgentResult with structured, corrected data.
        """
        if not raw_text or not raw_text.strip():
            logger.warning("OCR agent received empty text.")
            return OCRAgentResult(
                medicines=[],
                medicine_names=initial_medicines or [],
            )

        # Truncate very long texts to avoid token overflow
        truncated_text = raw_text[:4000] if len(raw_text) > 4000 else raw_text

        logger.debug(f"OCR agent processing {len(truncated_text)} chars of OCR text.")

        try:
            response = await self._chain.ainvoke({"raw_text": truncated_text})
            raw_content = response.content if hasattr(response, "content") else str(response)

            # Parse JSON
            parsed = self._parse_response(raw_content)
            medicines = parsed.get("medicines", [])
            medicine_names = [m["name"] for m in medicines if m.get("name")]

            # Deduplicate while preserving order
            seen = set()
            unique_names = []
            for name in medicine_names:
                name_lower = name.lower().strip()
                if name_lower not in seen:
                    seen.add(name_lower)
                    unique_names.append(name)

            logger.info(f"OCR agent found {len(unique_names)} medicines: {unique_names}")

            return OCRAgentResult(
                medicines=medicines,
                medicine_names=unique_names,
                patient_info=parsed.get("patient_info", {}),
                prescription_date=parsed.get("prescription_date", ""),
                doctor_name=parsed.get("doctor_name", ""),
                notes=parsed.get("notes", ""),
                raw_llm_response=raw_content,
            )

        except Exception as exc:
            logger.error(f"OCR agent failed: {exc}", exc_info=True)
            # Gracefully fall back to initial medicines
            return OCRAgentResult(
                medicines=[{"name": m, "original_ocr": m, "confidence": 0.5} for m in (initial_medicines or [])],
                medicine_names=initial_medicines or [],
            )

    def _parse_response(self, raw: str) -> dict:
        """Parse LLM JSON response, handling markdown code fences."""
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Strip first and last fence lines
            cleaned = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            )
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(f"OCR agent JSON parse error: {exc}. Raw: {raw[:200]}")
            return {"medicines": [], "patient_info": {}}
