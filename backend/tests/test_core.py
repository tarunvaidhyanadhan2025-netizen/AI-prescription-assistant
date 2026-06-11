"""
Core service tests.
Uses template mode — no external dependencies required.
"""
from __future__ import annotations

import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def template_provider():
    from app.providers.template_provider import TemplateProvider
    return TemplateProvider()


@pytest.fixture
def llm_service(template_provider):
    from app.services.llm_service import LLMService
    return LLMService(template_provider)


@pytest.fixture
def mock_vector_store(llm_service):
    from app.services.vector_store_service import VectorStoreService, RetrievedContext
    vs = VectorStoreService(llm_service)
    vs._enabled = False  # Disable ChromaDB for tests
    return vs


@pytest.fixture
def analysis_service(llm_service):
    from app.services.analysis_service import AnalysisService
    return AnalysisService(llm_service)


# ── LLMService tests ────────────────────────────────────────────────────────

class TestLLMService:
    def test_is_template_mode(self, llm_service):
        assert llm_service.is_template_mode is True
        assert llm_service.provider_name == "template"

    def test_parse_json_clean(self, llm_service):
        raw = '{"key": "value"}'
        result = llm_service._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_json_with_fences(self, llm_service):
        raw = "```json\n{\"key\": \"value\"}\n```"
        result = llm_service._parse_json(raw)
        assert result == {"key": "value"}

    def test_parse_json_invalid_returns_fallback(self, llm_service):
        raw = "not json at all"
        result = llm_service._parse_json(raw, fallback={"error": True})
        assert result == {"error": True}


# ── TemplateService tests ────────────────────────────────────────────────────

class TestTemplateService:
    @pytest.fixture
    def svc(self):
        from app.templates.template_service import TemplateService
        return TemplateService()

    def test_get_explanation_default(self, svc):
        result = svc.get_explanation("UnknownMed")
        assert "explanation" in result
        assert result["source"] == "template"

    def test_get_explanation_by_class(self, svc):
        result = svc.get_explanation("Paracetamol", drug_class="Analgesic / Antipyretic")
        assert "pain" in result["explanation"].lower()

    def test_get_warnings_no_class(self, svc):
        result = svc.get_warnings("UnknownMed")
        assert isinstance(result["side_effects"], list)
        assert isinstance(result["causes_drowsiness"], bool)

    def test_get_warnings_with_age_child(self, svc):
        result = svc.get_warnings("SomeMed", patient_age=8)
        assert len(result["age_warnings"]) > 0

    def test_get_warnings_with_age_elderly(self, svc):
        result = svc.get_warnings("SomeMed", patient_age=70)
        assert len(result["age_warnings"]) > 0

    def test_get_dosage_adult(self, svc):
        result = svc.get_dosage("Paracetamol", drug_class="Analgesic / Antipyretic", patient_age=30)
        assert "500mg" in result["dosage_info"] or "directed" in result["dosage_info"].lower()

    def test_get_dosage_pediatric(self, svc):
        result = svc.get_dosage("Paracetamol", drug_class="Analgesic / Antipyretic", patient_age=8)
        assert result["dosage_info"] != ""

    def test_drowsiness_benzodiazepine(self, svc):
        result = svc.get_warnings("Diazepam", drug_class="Benzodiazepine")
        assert result["causes_drowsiness"] is True


# ── AnalysisService tests ────────────────────────────────────────────────────

class TestAnalysisService:
    @pytest.mark.asyncio
    async def test_analyse_medicine_template_mode(self, analysis_service):
        result = await analysis_service.analyse_medicine("Paracetamol")
        assert result.medicine_name == "Paracetamol"
        assert result.explanation != ""
        assert result.generated_by == "template"

    @pytest.mark.asyncio
    async def test_analyse_medicine_with_age(self, analysis_service):
        result = await analysis_service.analyse_medicine("Amoxicillin", patient_age=8)
        assert result.medicine_name == "Amoxicillin"

    @pytest.mark.asyncio
    async def test_refine_ocr_template_mode(self, analysis_service):
        result = await analysis_service.refine_ocr(
            raw_text="Tab. Amoxicillin 500mg",
            initial_medicines=["Amoxicillin"],
        )
        assert "medicines" in result
        assert len(result["medicines"]) > 0


# ── OCR provider tests ───────────────────────────────────────────────────────

class TestOCRMedicineDetection:
    @pytest.fixture
    def provider(self):
        from app.providers.ocr_provider import TesseractOCRProvider
        p = TesseractOCRProvider.__new__(TesseractOCRProvider)
        # Skip actual tesseract init
        return p

    def test_detect_medicines_tab_prefix(self, provider):
        text = "Tab. Amoxicillin 500mg\nCap. Metformin 250mg"
        result = provider._detect_medicines(text)
        assert any("Amoxicillin" in r for r in result)

    def test_detect_medicines_suffix(self, provider):
        text = "The patient was prescribed Amoxicillin and Metformin"
        result = provider._detect_medicines(text)
        assert any("Amoxicillin" in r for r in result)

    def test_exclude_non_medicine_words(self, provider):
        text = "PATIENT NAME DATE DOCTOR HOSPITAL"
        result = provider._detect_medicines(text)
        assert len(result) == 0

    def test_clean_text(self, provider):
        text = "hello   world\n\n\n\ntest"
        cleaned = provider._clean_text(text)
        assert "   " not in cleaned
        assert "\n\n\n" not in cleaned
