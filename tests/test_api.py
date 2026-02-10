"""Tests for the FastAPI REST API."""

import pytest
from fastapi.testclient import TestClient

from legacylipi.api.deps import set_session_manager
from legacylipi.api.main import create_app
from legacylipi.api.session_manager import SessionManager


@pytest.fixture(autouse=True)
def _setup_session_manager():
    """Inject a fresh session manager for each test."""
    sm = SessionManager()
    set_session_manager(sm)
    yield
    set_session_manager(sm)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestConfigEndpoints:
    def test_get_languages(self, client: TestClient):
        resp = client.get("/api/v1/config/languages")
        assert resp.status_code == 200
        data = resp.json()
        assert "target" in data
        assert "ocr" in data
        assert "en" in data["target"]
        assert "mar" in data["ocr"]

    def test_get_translators(self, client: TestClient):
        resp = client.get("/api/v1/config/translators")
        assert resp.status_code == 200
        data = resp.json()
        assert "backends" in data
        assert "trans" in data["backends"]
        assert "openai_models" in data
        assert "ollama_models" in data

    def test_get_options(self, client: TestClient):
        resp = client.get("/api/v1/config/options")
        assert resp.status_code == 200
        data = resp.json()
        assert "output_formats" in data
        assert "translation_modes" in data
        assert "workflow_modes" in data
        assert "ocr_engines" in data


class TestSessionEndpoints:
    def test_upload_pdf(self, client: TestClient, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")

        with open(pdf_path, "rb") as f:
            resp = client.post(
                "/api/v1/sessions/upload", files={"file": ("test.pdf", f, "application/pdf")}
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data
        assert data["filename"] == "test.pdf"
        assert data["file_size"] > 0

    def test_upload_rejects_non_pdf(self, client: TestClient, tmp_path):
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("not a pdf")

        with open(txt_path, "rb") as f:
            resp = client.post(
                "/api/v1/sessions/upload", files={"file": ("test.txt", f, "text/plain")}
            )

        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"]

    def test_delete_session(self, client: TestClient, tmp_path):
        # First upload
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")

        with open(pdf_path, "rb") as f:
            resp = client.post(
                "/api/v1/sessions/upload", files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = resp.json()["session_id"]

        # Delete
        resp = client.delete(f"/api/v1/sessions/{session_id}")
        assert resp.status_code == 200

    def test_delete_nonexistent_session(self, client: TestClient):
        resp = client.delete("/api/v1/sessions/nonexistent-id")
        assert resp.status_code == 404


class TestProcessingEndpoints:
    def _upload(self, client: TestClient, tmp_path) -> str:
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")
        with open(pdf_path, "rb") as f:
            resp = client.post(
                "/api/v1/sessions/upload", files={"file": ("test.pdf", f, "application/pdf")}
            )
        return resp.json()["session_id"]

    def test_scan_copy_returns_job_id(self, client: TestClient, tmp_path):
        session_id = self._upload(client, tmp_path)
        resp = client.post(
            f"/api/v1/sessions/{session_id}/scan-copy",
            json={"dpi": 300, "color_mode": "color", "quality": 85},
        )
        assert resp.status_code == 200
        assert "job_id" in resp.json()

    def test_convert_returns_job_id(self, client: TestClient, tmp_path):
        session_id = self._upload(client, tmp_path)
        resp = client.post(
            f"/api/v1/sessions/{session_id}/convert",
            json={
                "ocr_engine": "easyocr",
                "ocr_lang": "mar",
                "ocr_dpi": 300,
                "output_format": "pdf",
            },
        )
        assert resp.status_code == 200
        assert "job_id" in resp.json()

    def test_translate_returns_job_id(self, client: TestClient, tmp_path):
        session_id = self._upload(client, tmp_path)
        resp = client.post(
            f"/api/v1/sessions/{session_id}/translate",
            json={"target_lang": "en", "translator": "mock"},
        )
        assert resp.status_code == 200
        assert "job_id" in resp.json()

    def test_processing_nonexistent_session(self, client: TestClient):
        resp = client.post(
            "/api/v1/sessions/nonexistent/scan-copy",
            json={"dpi": 300, "color_mode": "color", "quality": 85},
        )
        assert resp.status_code == 404


class TestDownloadEndpoint:
    def test_download_no_result(self, client: TestClient, tmp_path):
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake content")
        with open(pdf_path, "rb") as f:
            resp = client.post(
                "/api/v1/sessions/upload", files={"file": ("test.pdf", f, "application/pdf")}
            )
        session_id = resp.json()["session_id"]

        resp = client.get(f"/api/v1/sessions/{session_id}/download")
        assert resp.status_code == 404

    def test_download_nonexistent_session(self, client: TestClient):
        resp = client.get("/api/v1/sessions/nonexistent/download")
        assert resp.status_code == 404
