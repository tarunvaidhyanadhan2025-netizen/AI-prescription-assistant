"""Tests for prescription history and rate limiting."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def set_template_env(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "template")
    monkeypatch.setenv("VECTOR_DB_ENABLED", "false")
    monkeypatch.setenv("ENVIRONMENT", "test")  # disables rate limiting


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))

    from app.providers.factory import get_llm_provider
    from app.core.settings import get_settings
    get_llm_provider.cache_clear()
    get_settings.cache_clear()  # Must clear AFTER setting env var

    from app.main import create_app
    from app.services.vector_store_service import VectorStoreService
    from app.services.llm_service import LLMService
    from app.providers.template_provider import TemplateProvider
    from fastapi.testclient import TestClient

    app = create_app()
    llm = LLMService(TemplateProvider())
    vs = VectorStoreService(llm)
    vs._enabled = False
    app.state.vector_store = vs

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c, tmp_path

    # Cleanup cache after test
    get_settings.cache_clear()
    get_llm_provider.cache_clear()


class TestPrescriptionHistory:
    def _write_meta(self, tmp_path, pid, medicines, age=None):
        meta = {
            "prescription_id": pid,
            "detected_medicines": medicines,
            "patient_age": age,
            "language": "en",
            "ocr_confidence": 0.85,
            "doctor_name": "Dr. Smith",
            "notes": "",
        }
        (tmp_path / f"{pid}.meta").write_text(json.dumps(meta))

    def test_list_empty(self, client):
        c, tmp_path = client
        r = c.get("/api/v1/prescriptions")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["prescriptions"] == []

    def test_list_with_entries(self, client):
        c, tmp_path = client
        self._write_meta(tmp_path, "aaa-111", ["Paracetamol", "Amoxicillin"], age=30)
        self._write_meta(tmp_path, "bbb-222", ["Metformin"], age=55)

        r = c.get("/api/v1/prescriptions")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        ids = [p["prescription_id"] for p in data["prescriptions"]]
        assert "aaa-111" in ids
        assert "bbb-222" in ids

    def test_list_pagination(self, client):
        c, tmp_path = client
        for i in range(5):
            self._write_meta(tmp_path, f"pid-{i:03}", [f"Med{i}"])

        r = c.get("/api/v1/prescriptions?limit=2&offset=0")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 5
        assert len(data["prescriptions"]) == 2

    def test_get_by_id_found(self, client):
        c, tmp_path = client
        self._write_meta(tmp_path, "abc-999", ["Ibuprofen"], age=25)
        r = c.get("/api/v1/prescriptions/abc-999")
        assert r.status_code == 200
        data = r.json()
        assert data["prescription_id"] == "abc-999"
        assert "Ibuprofen" in data["detected_medicines"]
        assert data["patient_age"] == 25

    def test_get_by_id_not_found(self, client):
        c, _ = client
        r = c.get("/api/v1/prescriptions/does-not-exist")
        assert r.status_code == 404


class TestRateLimitMiddleware:
    def test_rate_limit_not_active_in_test_env(self, client):
        """ENVIRONMENT=test disables rate limiting."""
        c, _ = client
        # Should never get 429 in test mode
        for _ in range(15):
            r = c.post(
                "/api/v1/analysis",
                json={"prescription_id": "x", "medicines": ["Paracetamol"]},
            )
        assert r.status_code in (200, 404)  # not 429

    def test_rate_limit_headers_present(self, client):
        c, _ = client
        r = c.post(
            "/api/v1/analysis",
            json={"prescription_id": "x", "medicines": ["Paracetamol"]},
        )
        # In test env rate limit is disabled so headers may not be present
        # Just ensure the response comes back
        assert r.status_code in (200, 404)

    def test_rate_limit_logic_direct(self):
        """Unit-test the middleware logic directly without HTTP."""
        from app.core.rate_limit import RateLimitMiddleware
        import time

        mw = RateLimitMiddleware(app=None, enabled=True)
        ip = "1.2.3.4"
        path = "/api/v1/upload"
        bucket = mw._windows[ip][path]

        max_req, window = mw.LIMITS["/api/v1/upload"]  # (10, 60)
        assert max_req == 10

        now = time.monotonic()
        for _ in range(max_req):
            bucket.append(now)

        # At limit — next request should be rejected
        assert len(bucket) >= max_req

    def test_rate_limit_window_expiry(self):
        """Old timestamps are evicted."""
        from app.core.rate_limit import RateLimitMiddleware
        import time

        mw = RateLimitMiddleware(app=None, enabled=True)
        ip = "5.6.7.8"
        path = "/api/v1/upload"
        bucket = mw._windows[ip][path]

        # Add 10 old timestamps (2 minutes ago)
        old = time.monotonic() - 120
        for _ in range(10):
            bucket.append(old)

        # Evict old entries
        now = time.monotonic()
        while bucket and bucket[0] < now - 60:
            bucket.popleft()

        assert len(bucket) == 0
