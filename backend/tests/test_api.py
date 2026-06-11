"""
API integration tests using TestClient.
All tests use template mode — no LLM calls.
"""
from __future__ import annotations

import json
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def set_template_env(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "template")
    monkeypatch.setenv("VECTOR_DB_ENABLED", "false")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    # Clear lru_cache so env changes are picked up
    from app.providers.factory import get_llm_provider
    from app.core.settings import get_settings
    get_llm_provider.cache_clear()
    get_settings.cache_clear()

    from app.main import create_app
    from app.services.vector_store_service import VectorStoreService
    from app.services.llm_service import LLMService
    from app.providers.template_provider import TemplateProvider

    app = create_app()
    llm = LLMService(TemplateProvider())
    vs = VectorStoreService(llm)
    vs._enabled = False
    app.state.vector_store = vs

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        data = r.json()
        assert data["provider"] == "template"
        assert data["version"] != ""


class TestRoot:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "service" in r.json()


class TestUpload:
    def _make_image(self, tmp_path):
        """Create a minimal valid PNG for testing."""
        from PIL import Image
        import io
        img = Image.new("RGB", (200, 100), color="white")
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Tab. Amoxicillin 500mg\nCap. Metformin 250mg", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_upload_unsupported_type(self, client):
        r = client.post(
            "/api/v1/upload",
            files={"file": ("test.pdf", b"fake content", "application/pdf")},
        )
        assert r.status_code == 400

    def test_upload_too_large(self, client, monkeypatch):
        monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
        from app.core.settings import get_settings
        get_settings.cache_clear()
        r = client.post(
            "/api/v1/upload",
            files={"file": ("test.png", b"x" * 100, "image/png")},
        )
        # Either 413 or 422 (tesseract won't find the fake image)
        assert r.status_code in (400, 413, 422)


class TestAnalysis:
    def _write_sidecar(self, tmp_path, prescription_id, medicines, age=None):
        meta = {
            "prescription_id": prescription_id,
            "detected_medicines": medicines,
            "patient_age": age,
            "language": "en",
        }
        path = tmp_path / f"{prescription_id}.meta"
        path.write_text(json.dumps(meta))
        return str(tmp_path)

    def test_analysis_not_found(self, client):
        r = client.get("/api/v1/analysis/nonexistent-id")
        assert r.status_code == 404

    def test_analysis_post_with_medicines(self, client):
        r = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": "test-123",
                "medicines": ["Paracetamol", "Amoxicillin"],
                "patient_age": 30,
                "language": "en",
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_medicines_analysed"] == 2
        assert len(data["medicines"]) == 2
        assert data["provider_used"] == "template"
        for med in data["medicines"]:
            assert med["explanation"] != ""
            assert med["dosage_info"] != ""

    def test_analysis_elderly_age(self, client):
        r = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": "test-456",
                "medicines": ["Diazepam"],
                "patient_age": 72,
                "language": "en",
            },
        )
        assert r.status_code == 200
        data = r.json()
        med = data["medicines"][0]
        assert len(med["age_warnings"]) > 0

    def test_analysis_drowsiness_flag(self, client):
        r = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": "test-789",
                "medicines": ["Diazepam"],
            },
        )
        assert r.status_code == 200
        data = r.json()
        # Benzodiazepine should flag drowsiness
        assert data["overall_drowsiness_warning"] is True

    def test_analysis_language_tamil(self, client):
        r = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": "test-lang",
                "medicines": ["Paracetamol"],
                "language": "ta",
            },
        )
        assert r.status_code == 200

    def test_analysis_empty_medicines_list(self, client):
        r = client.post(
            "/api/v1/analysis",
            json={
                "prescription_id": "test-empty",
                "medicines": [],
            },
        )
        assert r.status_code == 404
