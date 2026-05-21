"""Client OCR worker untuk photo intake."""

from __future__ import annotations

import httpx
from pydantic import ValidationError

from app.schemas.contracts import PhotoOcrRequest, PhotoOcrResponse
from app.settings.config import Settings


class OcrWorkerError(RuntimeError):
    """Raised saat OCR worker tidak bisa dipakai oleh API."""


def _worker_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v1/ocr/photo"


def call_ocr_worker(request: PhotoOcrRequest, settings: Settings) -> PhotoOcrResponse | None:
    """Forward photo payload ke worker jika `OCR_WORKER_URL` dikonfigurasi."""
    if not settings.ocr_worker_url:
        return None

    try:
        with httpx.Client(timeout=settings.ocr_worker_timeout_seconds) as client:
            response = client.post(
                _worker_endpoint(settings.ocr_worker_url),
                json=request.model_dump(mode="json"),
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise OcrWorkerError(f"OCR worker tidak bisa dihubungi: {exc}") from exc

    try:
        return PhotoOcrResponse.model_validate(response.json())
    except (ValueError, ValidationError) as exc:
        raise OcrWorkerError("OCR worker mengembalikan response tidak valid.") from exc
