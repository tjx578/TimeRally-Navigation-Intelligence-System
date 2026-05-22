from __future__ import annotations

import pytest

import app.adapters.ocr_worker as ocr_worker
from app.schemas.contracts import PhotoOcrRequest, PhotoOcrResponse, QuestionPhotoInput
from app.settings.config import Settings


def _photo_request() -> PhotoOcrRequest:
    return PhotoOcrRequest(
        photos=[
            QuestionPhotoInput(
                filename="soal.jpg",
                mime_type="image/jpeg",
                image_base64="ZHVtbXk=",
            )
        ]
    )


def test_google_vision_provider_calls_api_adapter(monkeypatch):
    class FakeGoogleVisionAdapter:
        available = True
        init_error = None

        def recognize(self, request: PhotoOcrRequest) -> PhotoOcrResponse:
            return PhotoOcrResponse(
                event_name="",
                trayek_name="",
                location="",
                normalized_text="Sub A\nJT di O Lapangan",
                detected_total_distance_km=None,
                detected_total_time_minutes=None,
                photo_count=len(request.photos),
                status="ok",
                warnings=["vision dipakai"],
            )

    monkeypatch.setattr(
        ocr_worker,
        "GoogleVisionOcrAdapter",
        FakeGoogleVisionAdapter,
    )

    response = ocr_worker.call_ocr_worker(
        _photo_request(),
        Settings(ocr_provider="google_vision"),
    )

    assert response is not None
    assert response.status == "ok"
    assert response.normalized_text == "Sub A\nJT di O Lapangan"
    assert response.photo_count == 1


def test_auto_provider_uses_google_vision_when_enabled_without_worker(monkeypatch):
    class FakeGoogleVisionAdapter:
        available = True
        init_error = None

        def recognize(self, request: PhotoOcrRequest) -> PhotoOcrResponse:
            return PhotoOcrResponse(
                event_name="",
                trayek_name="",
                location="",
                normalized_text="OCR text",
                detected_total_distance_km=None,
                detected_total_time_minutes=None,
                photo_count=len(request.photos),
                status="ok",
                warnings=[],
            )

    monkeypatch.setattr(
        ocr_worker,
        "GoogleVisionOcrAdapter",
        FakeGoogleVisionAdapter,
    )

    response = ocr_worker.call_ocr_worker(
        _photo_request(),
        Settings(ocr_provider="auto", google_vision_enabled=True),
    )

    assert response is not None
    assert response.normalized_text == "OCR text"


def test_google_vision_provider_reports_missing_sdk(monkeypatch):
    class MissingGoogleVisionAdapter:
        available = False
        init_error = "google-cloud-vision tidak tersedia"

    monkeypatch.setattr(
        ocr_worker,
        "GoogleVisionOcrAdapter",
        MissingGoogleVisionAdapter,
    )

    with pytest.raises(ocr_worker.OcrWorkerError, match="google-cloud-vision"):
        ocr_worker.call_ocr_worker(
            _photo_request(),
            Settings(ocr_provider="google_vision"),
        )
