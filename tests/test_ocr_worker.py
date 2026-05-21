"""Smoke test OCR worker tanpa memanggil engine eksternal."""

from __future__ import annotations

from fastapi.testclient import TestClient

from workers.ocr.app.main import app


def test_ocr_worker_disabled_engine_requires_manual(monkeypatch):
    monkeypatch.setenv("OCR_ENGINE", "disabled")
    client = TestClient(app)

    resp = client.post(
        "/v1/ocr/photo",
        json={
            "photos": [
                {
                    "filename": "soal.jpg",
                    "mime_type": "image/jpeg",
                    "image_base64": "dGVzdA==",
                }
            ]
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "manual_required"
    assert body["photo_count"] == 1
    assert "OCR_ENGINE" in " ".join(body["warnings"])


def test_ocr_worker_readyz_reports_configured_engine(monkeypatch):
    monkeypatch.setenv("OCR_ENGINE", "google_vision")
    client = TestClient(app)

    resp = client.get("/readyz")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ready"
    assert body["checks"]["ocr_engine_configured"] is True
