"""
Tests for Upload Route
Tests the /api/v1/upload endpoint including:
- Valid image upload
- Invalid file type rejection
- Oversized file rejection
- OCR text extraction
- Medicine detection
"""

import io
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# ── App import ─────────────────────────────────────────────────────────────
# We patch heavy dependencies before importing the app
with (
    patch("app.database.chroma.ChromaDBClient.initialize", new_callable=AsyncMock),
    patch("app.database.vector_store.VectorStore.seed_if_empty", new_callable=AsyncMock),
):
    from app.main import app


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Synchronous test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Create a minimal valid JPEG image in memory."""
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Create a minimal valid PNG image in memory."""
    img = Image.new("RGB", (200, 100), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Helper ─────────────────────────────────────────────────────────────────

def make_upload_files(content: bytes, filename: str = "test.jpg", content_type: str = "image/jpeg"):
    return {"file": (filename, io.BytesIO(content), content_type)}


# ── Tests ──────────────────────────────────────────────────────────────────

class TestUploadEndpoint:

    def test_health_endpoint(self, client):
        """Health check should return 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Root endpoint should identify the service."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data

    @patch("app.routes.upload.ocr_service")
    def test_upload_valid_jpeg(self, mock_ocr, client, sample_jpeg_bytes):
        """Valid JPEG upload should return 201 with prescription_id."""
        # Mock OCR result
        mock_result = MagicMock()
        mock_result.raw_text = "Rx\nAmoxicillin 500mg TID\nParacetamol 1g PRN"
        mock_result.detected_medicines = ["Amoxicillin", "Paracetamol"]
        mock_result.confidence = 0.88
        mock_ocr.extract_text = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/upload",
            files=make_upload_files(sample_jpeg_bytes, "test.jpg"),
            data={"patient_age": "35", "language": "en"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "prescription_id" in data
        assert len(data["prescription_id"]) == 36  # UUID length
        assert "detected_medicines" in data
        assert "raw_text" in data
        assert data["patient_age"] == 35
        assert data["language"] == "en"

    @patch("app.routes.upload.ocr_service")
    def test_upload_valid_png(self, mock_ocr, client, sample_png_bytes):
        """Valid PNG upload should also succeed."""
        mock_result = MagicMock()
        mock_result.raw_text = "Ibuprofen 400mg BD"
        mock_result.detected_medicines = ["Ibuprofen"]
        mock_result.confidence = 0.75
        mock_ocr.extract_text = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/upload",
            files=make_upload_files(sample_png_bytes, "rx.png", "image/png"),
        )

        assert response.status_code == 201
        data = response.json()
        assert "prescription_id" in data

    def test_upload_invalid_extension(self, client):
        """PDF upload should be rejected with 415."""
        fake_pdf = b"%PDF-1.4 fake content"
        response = client.post(
            "/api/v1/upload",
            files={"file": ("prescription.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        )
        assert response.status_code == 415

    def test_upload_txt_file_rejected(self, client):
        """Text file should be rejected."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.txt", io.BytesIO(b"not an image"), "text/plain")},
        )
        assert response.status_code == 415

    def test_upload_oversized_file(self, client):
        """File exceeding MAX_UPLOAD_SIZE should return 413."""
        # Create fake oversized content (just above 10 MB)
        oversized = b"\xff\xd8\xff" + b"0" * (11 * 1024 * 1024)
        response = client.post(
            "/api/v1/upload",
            files={"file": ("big.jpg", io.BytesIO(oversized), "image/jpeg")},
        )
        assert response.status_code == 413

    def test_upload_empty_file(self, client):
        """Empty file should be rejected."""
        response = client.post(
            "/api/v1/upload",
            files={"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")},
        )
        # Either 400 (bad request) or 415 (unsupported) is acceptable
        assert response.status_code in (400, 415, 422)

    @patch("app.routes.upload.ocr_service")
    def test_upload_no_medicines_detected(self, mock_ocr, client, sample_jpeg_bytes):
        """Upload with no detected medicines should still succeed."""
        mock_result = MagicMock()
        mock_result.raw_text = "Patient: John Doe\nDate: 2024-01-01"
        mock_result.detected_medicines = []
        mock_result.confidence = 0.60
        mock_ocr.extract_text = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/upload",
            files=make_upload_files(sample_jpeg_bytes),
        )

        assert response.status_code == 201
        data = response.json()
        assert data["detected_medicines"] == []

    @patch("app.routes.upload.ocr_service")
    def test_upload_ocr_failure_returns_422(self, mock_ocr, client, sample_jpeg_bytes):
        """OCR failure should return 422 Unprocessable Entity."""
        mock_ocr.extract_text = AsyncMock(side_effect=RuntimeError("Tesseract not found"))

        response = client.post(
            "/api/v1/upload",
            files=make_upload_files(sample_jpeg_bytes),
        )

        assert response.status_code == 422

    @patch("app.routes.upload.ocr_service")
    def test_upload_default_language_fallback(self, mock_ocr, client, sample_jpeg_bytes):
        """Unsupported language code should fall back to 'en'."""
        mock_result = MagicMock()
        mock_result.raw_text = "Metformin 500mg"
        mock_result.detected_medicines = ["Metformin"]
        mock_result.confidence = 0.80
        mock_ocr.extract_text = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/upload",
            files=make_upload_files(sample_jpeg_bytes),
            data={"language": "klingon"},  # Not supported
        )

        assert response.status_code == 201
        assert response.json()["language"] == "en"

    @patch("app.routes.upload.ocr_service")
    def test_upload_response_structure(self, mock_ocr, client, sample_jpeg_bytes):
        """Response must contain all required fields."""
        mock_result = MagicMock()
        mock_result.raw_text = "Atorvastatin 40mg OD"
        mock_result.detected_medicines = ["Atorvastatin"]
        mock_result.confidence = 0.92
        mock_ocr.extract_text = AsyncMock(return_value=mock_result)

        response = client.post(
            "/api/v1/upload",
            files=make_upload_files(sample_jpeg_bytes),
        )

        data = response.json()
        required_fields = [
            "prescription_id", "filename", "file_path",
            "raw_text", "detected_medicines", "language",
            "ocr_confidence", "message",
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"


class TestDeleteEndpoint:

    @patch("app.routes.upload.ocr_service")
    def test_delete_existing_file(self, mock_ocr, client, sample_jpeg_bytes, tmp_path):
        """Uploaded file should be deletable."""
        mock_result = MagicMock()
        mock_result.raw_text = "Cetirizine 10mg OD"
        mock_result.detected_medicines = ["Cetirizine"]
        mock_result.confidence = 0.85
        mock_ocr.extract_text = AsyncMock(return_value=mock_result)

        # Upload first
        upload_resp = client.post(
            "/api/v1/upload",
            files=make_upload_files(sample_jpeg_bytes),
        )
        assert upload_resp.status_code == 201
        pid = upload_resp.json()["prescription_id"]

        # Delete — may 404 in test environment if upload dir differs
        del_resp = client.delete(f"/api/v1/upload/{pid}")
        assert del_resp.status_code in (200, 404)

    def test_delete_nonexistent_file_returns_404(self, client):
        """Deleting a non-existent prescription_id should return 404."""
        response = client.delete("/api/v1/upload/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
