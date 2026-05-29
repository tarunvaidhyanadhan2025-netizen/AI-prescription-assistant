"""
Explanation Service
Uses LangChain + OpenAI to generate plain-language medicine explanations,
use cases, mechanisms of action, and multilingual support.
"""

import json
from dataclasses import dataclass
from typing import Optional

from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.prompts.explanation_prompt import (
    EXPLANATION_SYSTEM_PROMPT,
    EXPLANATION_HUMAN_PROMPT,
    MULTILINGUAL_SYSTEM_PROMPT,
)
from app.services.rag_service import RetrievedContext
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Language name map for prompt engineering
LANGUAGE_NAMES = {
    "en": "English",
    "ta": "Tamil",
    "hi": "Hindi",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "zh": "Chinese (Simplified)",
    "ar": "Arabic",
    "pt": "Portuguese",
    "ru": "Russian",
}


@dataclass
class ExplanationResult:
    """Structured explanation for a medicine."""
    medicine_name: str
    explanation: str
    use_case: str
    mechanism: str
    how_to_take: str
    language: str
    generated_by_llm: bool = True


class ExplanationService:
    """
    Generates patient-friendly medicine explanations using LangChain + OpenAI.
    Supports multilingual output via language parameter.
    """

    def __init__(self):
        self._llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )
        # Build LangChain prompt template
        self._prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(EXPLANATION_SYSTEM_PROMPT),
            HumanMessagePromptTemplate.from_template(EXPLANATION_HUMAN_PROMPT),
        ])
        self._chain = self._prompt | self._llm

    async def explain(
        self,
        medicine_name: str,
        context: RetrievedContext,
        patient_age: Optional[int] = None,
        language: str = "en",
    ) -> ExplanationResult:
        """
        Generate a plain-language explanation for a medicine.

        Args:
            medicine_name: Name of the medicine.
            context: RAG-retrieved context documents.
            patient_age: Patient age for tailored language.
            language: ISO 639-1 language code.

        Returns:
            ExplanationResult with structured fields.
        """
        lang_name = LANGUAGE_NAMES.get(language, "English")
        age_ctx = f"The patient is {patient_age} years old." if patient_age else ""
        rag_context = context.combined_text or "No additional context available."

        logger.debug(f"Explaining '{medicine_name}' in {lang_name}")

        try:
            response = await self._chain.ainvoke({
                "medicine_name": medicine_name,
                "rag_context": rag_context,
                "language": lang_name,
                "patient_age_context": age_ctx,
            })

            raw_text = response.content if hasattr(response, "content") else str(response)

            # Parse JSON response
            parsed = self._parse_json_response(raw_text)

            return ExplanationResult(
                medicine_name=medicine_name,
                explanation=parsed.get("explanation", raw_text),
                use_case=parsed.get("use_case", ""),
                mechanism=parsed.get("mechanism", ""),
                how_to_take=parsed.get("how_to_take", ""),
                language=language,
                generated_by_llm=True,
            )

        except Exception as exc:
            logger.error(f"Explanation generation failed for '{medicine_name}': {exc}", exc_info=True)
            return ExplanationResult(
                medicine_name=medicine_name,
                explanation=f"Explanation unavailable. Please consult your pharmacist.",
                use_case="",
                mechanism="",
                how_to_take="",
                language=language,
                generated_by_llm=False,
            )

    async def explain_batch(
        self,
        medicines: list[str],
        contexts: dict,
        language: str = "en",
    ) -> dict[str, ExplanationResult]:
        """
        Batch explain multiple medicines concurrently.
        """
        import asyncio
        tasks = [
            self.explain(
                medicine_name=med,
                context=contexts.get(med, RetrievedContext(query=med)),
                language=language,
            )
            for med in medicines
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output = {}
        for med, result in zip(medicines, results):
            if isinstance(result, Exception):
                logger.error(f"Batch explain failed for '{med}': {result}")
                output[med] = ExplanationResult(
                    medicine_name=med,
                    explanation="Explanation unavailable.",
                    use_case="", mechanism="", how_to_take="", language=language,
                )
            else:
                output[med] = result
        return output

    # ── Internal ───────────────────────────────────────────────────────────

    def _parse_json_response(self, raw: str) -> dict:
        """
        Parse LLM response — try JSON first, fall back to raw text.
        """
        # Strip markdown fences
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
        try:
            return json.loads(cleaned)
        except (json.JSONDecodeError, ValueError):
            # Return raw text wrapped in explanation key
            return {"explanation": raw, "use_case": "", "mechanism": "", "how_to_take": ""}
