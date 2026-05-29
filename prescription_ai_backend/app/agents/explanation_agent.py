"""
Explanation Agent
LangChain agent that generates patient-friendly, multilingual
medicine explanations from RAG context + LLM reasoning.
"""

import json
from dataclasses import dataclass
from typing import Optional

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.prompts.explanation_prompt import (
    EXPLANATION_HUMAN_PROMPT,
    EXPLANATION_SYSTEM_PROMPT,
)
from app.services.explanation_service import ExplanationResult
from app.services.rag_service import RetrievedContext
from app.utils.logger import get_logger

logger = get_logger(__name__)

LANGUAGE_NAMES = {
    "en": "English", "ta": "Tamil", "hi": "Hindi",
    "fr": "French", "es": "Spanish", "de": "German",
    "zh": "Chinese (Simplified)", "ar": "Arabic",
    "pt": "Portuguese", "ru": "Russian",
}


@dataclass
class ExplanationAgentResult:
    """Result from the explanation agent."""
    medicine_name: str
    explanation: str
    use_case: str
    mechanism: str
    how_to_take: str
    language: str
    source: str = "llm_agent"


class ExplanationAgent:
    """
    Agent that wraps ExplanationService and adds:
    - Conversation history for follow-up questions
    - Structured JSON output enforcement
    - Graceful fallbacks
    """

    def __init__(self, explanation_service):
        self._explanation_service = explanation_service
        self._llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", EXPLANATION_SYSTEM_PROMPT),
            ("human", EXPLANATION_HUMAN_PROMPT),
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
        Generate explanation via ExplanationService.
        Falls back to direct LLM call on failure.
        """
        try:
            result = await self._explanation_service.explain(
                medicine_name=medicine_name,
                context=context,
                patient_age=patient_age,
                language=language,
            )
            return result
        except Exception as exc:
            logger.warning(
                f"ExplanationService failed for '{medicine_name}': {exc}. "
                "Falling back to direct LLM call."
            )
            return await self._direct_llm_explain(medicine_name, context, patient_age, language)

    async def _direct_llm_explain(
        self,
        medicine_name: str,
        context: RetrievedContext,
        patient_age: Optional[int],
        language: str,
    ) -> ExplanationResult:
        """Direct LLM explanation without the service layer."""
        lang_name = LANGUAGE_NAMES.get(language, "English")
        age_ctx = f"Patient is {patient_age} years old." if patient_age else ""
        rag_ctx = context.combined_text or "Use your clinical pharmacology knowledge."

        try:
            response = await self._chain.ainvoke({
                "medicine_name": medicine_name,
                "rag_context": rag_ctx[:2500],
                "language": lang_name,
                "patient_age_context": age_ctx,
            })
            raw = response.content if hasattr(response, "content") else str(response)
            parsed = self._parse_json(raw)

            return ExplanationResult(
                medicine_name=medicine_name,
                explanation=parsed.get("explanation", raw),
                use_case=parsed.get("use_case", ""),
                mechanism=parsed.get("mechanism", ""),
                how_to_take=parsed.get("how_to_take", ""),
                language=language,
                generated_by_llm=True,
            )
        except Exception as exc:
            logger.error(f"Direct LLM explain failed for '{medicine_name}': {exc}")
            return ExplanationResult(
                medicine_name=medicine_name,
                explanation="Explanation unavailable. Please consult your pharmacist or prescriber.",
                use_case="",
                mechanism="",
                how_to_take="Take as directed by your doctor.",
                language=language,
                generated_by_llm=False,
            )

    def _parse_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(l for l in lines if not l.strip().startswith("```"))
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"explanation": raw, "use_case": "", "mechanism": "", "how_to_take": ""}
