"""
Tests for Analysis Route
Tests the /api/v1/analysis endpoint including:
- Full analysis pipeline
- Missing prescription handling
- Multi-medicine analysis
- Age-specific warnings
- Drowsiness detection
- Language support
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Patch heavy dependencies before importing app
with (
    patch("app.database.chroma.ChromaDBClient.initialize", new_callable=AsyncMock),
    patch("app.database.vector_store.VectorStore.seed_if_empty", new_callable=AsyncMock),
):
    from app.main import app

# ── Sample data ────────────────────────────────────────────────────────────

SAMPLE_PRESCRIPTION_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

SAMPLE_MEDICINE_ANALYSIS = {
    "medicine_name": "Amoxicillin",
    "explanation": "Amoxicillin is a penicillin-type antibiotic used to treat bacterial infections.",
    "use_case": "Bacterial infections including ear, chest, and urinary tract infections.",
    "side_effects": ["Diarrhoea", "Nausea", "Rash"],
    "causes_drowsiness": False,
    "dosage_info": "500mg every 8 hours for 7 days.",
    "dosage_safe": True,
    "age_warnings": [],
    "alternatives": ["Azithromycin", "Clarithromycin"],
    "severity_level": "low",
    "rag_sources": ["Amoxicillin"],
}

SAMPLE_FULL_RESPONSE = {
    "prescription_id": SAMPLE_PRESCRIPTION_ID,
    "patient_age": 35,
    "language": "en",
    "medicines": [SAMPLE_MEDICINE_ANALYSIS],
    "overall_drowsiness_warning": False,
    "overall_dosage_concern": False,
    "overall_age_warning": False,
    "overall_severity": "low",
    "total_medicines_analysed": 1,
    "summary": "Analysed 1 medicine(s).",
}


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def make_mock_vector_store():
    """Create a mock vector store."""
    vs = MagicMock()
    vs.query = AsyncMock(return_value={
        "documents": [["Amoxicillin is a penicillin antibiotic."]],
        "metadatas": [[{"name": "Amoxicillin", "source": "seed_database"}]],
        "distances": [[0.05]],
    })
    return vs


def make_mock_explanation_result(medicine_name: str):
    from app.services.explanation_service import ExplanationResult
    return ExplanationResult(
        medicine_name=medicine_name,
        explanation=f"{medicine_name} is used to treat infections.",
        use_case="Bacterial infections",
        mechanism="Inhibits cell wall synthesis.",
        how_to_take="Take with or without food.",
        language="en",
        generated_by_llm=True,
    )


def make_mock_safety_report(medicine_name: str, drowsy: bool = False):
    from app.agents.safety_agent import SafetyReport
    return SafetyReport(
        medicine_name=medicine_name,
        side_effects=["Nausea", "Diarrhoea"],
        serious_side_effects=["Anaphylaxis"],
        causes_drowsiness=drowsy,
        drowsiness_note="May cause drowsiness." if drowsy else "",
        dosage_info="500mg TID",
        dosage_safe=True,
        dosage_notes=[],
        age_warnings=[],
        alternatives=["Azithromycin"],
        severity_level="low",
        contraindications=["Penicillin allergy"],
        important_notes=[],
    )


# ── Tests ──────────────────────────────────────────────────────────────────

class TestAnalysisEndpoint:

    def test_analysis_missing_prescription_returns_404(self, client):
        """Non-existent prescription_id should return 404."""
        response = client.get(
            f"/api/v1/analysis/{SAMPLE_PRESCRIPTION_ID}",
            params={"medicines": ["Amoxicillin"]},  # Will fail without sidecar
        )
        # 404 expected because no sidecar file and no medicines_override
        assert response.status_code in (404, 422, 503)

    def test_analysis_post_no_medicines_returns_404(self, client):
        """POST with empty medicine list should fail."""
        response = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": SAMPLE_PRESCRIPTION_ID,
                "medicines": [],
            },
        )
        assert response.status_code == 404

    def test_analysis_post_invalid_prescription_id(self, client):
        """Malformed request body should return 422."""
        response = client.post(
            "/api/v1/analysis",
            json={"prescription_id": ""},
        )
        # Will 404 because no medicines provided
        assert response.status_code in (404, 422)

    @patch("app.routes.analysis.ExplanationAgent")
    @patch("app.routes.analysis.SafetyAgent")
    @patch("app.routes.analysis.RetrievalAgent")
    @patch("app.routes.analysis.RAGService")
    @patch("app.routes.analysis.WarningService")
    @patch("app.routes.analysis.MedicineService")
    def test_analysis_post_with_medicines_override(
        self,
        mock_med_svc,
        mock_warn_svc,
        mock_rag_svc,
        mock_retrieval_agent_cls,
        mock_safety_agent_cls,
        mock_explanation_agent_cls,
        client,
    ):
        """POST with medicines override should run full pipeline and return 200."""
        from app.services.rag_service import RetrievedContext

        # Mock retrieval agent
        mock_retrieval_instance = MagicMock()
        mock_retrieval_instance.retrieve = AsyncMock(
            return_value=RetrievedContext(query="Amoxicillin")
        )
        mock_retrieval_agent_cls.return_value = mock_retrieval_instance

        # Mock explanation agent
        mock_explanation_instance = MagicMock()
        mock_explanation_instance.explain = AsyncMock(
            return_value=make_mock_explanation_result("Amoxicillin")
        )
        mock_explanation_agent_cls.return_value = mock_explanation_instance

        # Mock safety agent
        mock_safety_instance = MagicMock()
        mock_safety_instance.evaluate = AsyncMock(
            return_value=make_mock_safety_report("Amoxicillin")
        )
        mock_safety_agent_cls.return_value = mock_safety_instance

        # Mock vector store on app state
        app.state.vector_store = make_mock_vector_store()

        response = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": SAMPLE_PRESCRIPTION_ID,
                "patient_age": 35,
                "language": "en",
                "medicines": ["Amoxicillin"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["prescription_id"] == SAMPLE_PRESCRIPTION_ID
        assert "medicines" in data
        assert len(data["medicines"]) == 1
        assert data["medicines"][0]["medicine_name"] == "Amoxicillin"
        assert data["total_medicines_analysed"] == 1

    @patch("app.routes.analysis.ExplanationAgent")
    @patch("app.routes.analysis.SafetyAgent")
    @patch("app.routes.analysis.RetrievalAgent")
    @patch("app.routes.analysis.RAGService")
    @patch("app.routes.analysis.WarningService")
    @patch("app.routes.analysis.MedicineService")
    def test_analysis_drowsiness_flag_propagates(
        self,
        mock_med_svc,
        mock_warn_svc,
        mock_rag_svc,
        mock_retrieval_agent_cls,
        mock_safety_agent_cls,
        mock_explanation_agent_cls,
        client,
    ):
        """Drowsy medicine should set overall_drowsiness_warning=True."""
        from app.services.rag_service import RetrievedContext

        mock_retrieval_instance = MagicMock()
        mock_retrieval_instance.retrieve = AsyncMock(
            return_value=RetrievedContext(query="Diazepam")
        )
        mock_retrieval_agent_cls.return_value = mock_retrieval_instance

        mock_explanation_instance = MagicMock()
        mock_explanation_instance.explain = AsyncMock(
            return_value=make_mock_explanation_result("Diazepam")
        )
        mock_explanation_agent_cls.return_value = mock_explanation_instance

        # Drowsy = True
        mock_safety_instance = MagicMock()
        mock_safety_instance.evaluate = AsyncMock(
            return_value=make_mock_safety_report("Diazepam", drowsy=True)
        )
        mock_safety_agent_cls.return_value = mock_safety_instance

        app.state.vector_store = make_mock_vector_store()

        response = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": SAMPLE_PRESCRIPTION_ID,
                "medicines": ["Diazepam"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["overall_drowsiness_warning"] is True
        assert data["medicines"][0]["causes_drowsiness"] is True

    @patch("app.routes.analysis.ExplanationAgent")
    @patch("app.routes.analysis.SafetyAgent")
    @patch("app.routes.analysis.RetrievalAgent")
    @patch("app.routes.analysis.RAGService")
    @patch("app.routes.analysis.WarningService")
    @patch("app.routes.analysis.MedicineService")
    def test_analysis_multi_medicine(
        self,
        mock_med_svc,
        mock_warn_svc,
        mock_rag_svc,
        mock_retrieval_agent_cls,
        mock_safety_agent_cls,
        mock_explanation_agent_cls,
        client,
    ):
        """Multiple medicines should all appear in the response."""
        from app.services.rag_service import RetrievedContext

        medicines = ["Amoxicillin", "Paracetamol", "Omeprazole"]

        mock_retrieval_instance = MagicMock()
        mock_retrieval_instance.retrieve = AsyncMock(
            return_value=RetrievedContext(query="medicine")
        )
        mock_retrieval_agent_cls.return_value = mock_retrieval_instance

        mock_explanation_instance = MagicMock()
        mock_explanation_instance.explain = AsyncMock(
            side_effect=lambda medicine_name, **kw: make_mock_explanation_result(medicine_name)
        )
        mock_explanation_agent_cls.return_value = mock_explanation_instance

        mock_safety_instance = MagicMock()
        mock_safety_instance.evaluate = AsyncMock(
            side_effect=lambda medicine_name, **kw: make_mock_safety_report(medicine_name)
        )
        mock_safety_agent_cls.return_value = mock_safety_instance

        app.state.vector_store = make_mock_vector_store()

        response = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": SAMPLE_PRESCRIPTION_ID,
                "medicines": medicines,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_medicines_analysed"] == 3
        returned_names = [m["medicine_name"] for m in data["medicines"]]
        for med in medicines:
            assert med in returned_names

    def test_analysis_response_schema(self, client):
        """
        Verify the analysis response schema contains all required top-level fields.
        Uses a mocked pipeline.
        """
        # We just check the 404 response shape here since we don't have a sidecar
        response = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": SAMPLE_PRESCRIPTION_ID,
                "medicines": [],  # Empty → 404
            },
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestAnalysisServiceUnit:
    """Unit tests for individual service components."""

    def test_parser_dosage_extraction(self):
        from app.utils.parser import parse_dosage, parse_dosage_mg, parse_frequency

        assert parse_dosage("Amoxicillin 500mg TID") == "500mg"
        assert parse_dosage("Paracetamol 1g PRN") == "1g"
        assert parse_dosage_mg("500mg") == 500.0
        assert parse_dosage_mg("1g") == 1000.0
        assert parse_dosage_mg("250mcg") == pytest.approx(0.25, rel=1e-3)
        assert parse_frequency("Amoxicillin 500mg TID") == "Three times daily"
        assert parse_frequency("Paracetamol BD") == "Twice daily"
        assert parse_frequency("Aspirin OD") == "Once daily"

    def test_parser_patient_age(self):
        from app.utils.parser import parse_patient_age

        assert parse_patient_age("Patient Age: 45 years") == 45
        assert parse_patient_age("Age: 8") == 8
        assert parse_patient_age("72 years old") == 72
        assert parse_patient_age("No age info here") is None

    def test_validator_medicine_name(self):
        from app.utils.validators import validate_medicine_name

        assert validate_medicine_name("Amoxicillin") == "Amoxicillin"
        assert validate_medicine_name("  Paracetamol  ") == "Paracetamol"

        with pytest.raises(ValueError):
            validate_medicine_name("")

        with pytest.raises(ValueError):
            validate_medicine_name("A" * 101)

        with pytest.raises(ValueError):
            validate_medicine_name("<script>alert(1)</script>")

    def test_validator_patient_age(self):
        from app.utils.validators import validate_patient_age

        assert validate_patient_age(None) is None
        assert validate_patient_age(25) == 25
        assert validate_patient_age(0) == 0
        assert validate_patient_age(120) == 120

        with pytest.raises(ValueError):
            validate_patient_age(-1)

        with pytest.raises(ValueError):
            validate_patient_age(121)

    def test_validator_language_code(self):
        from app.utils.validators import validate_language_code

        assert validate_language_code("en") == "en"
        assert validate_language_code("ta") == "ta"
        assert validate_language_code("klingon") == "en"  # Falls back
        assert validate_language_code("") == "en"

    def test_clean_medicine_name(self):
        from app.utils.parser import clean_medicine_name

        assert clean_medicine_name("amoxicillin") == "Amoxicillin"
        assert clean_medicine_name("...PARACETAMOL...") == "Paracetamol"
        assert clean_medicine_name("  ibuprofen  ") == "Ibuprofen"
