"""Client OCR worker untuk photo intake."""

from __future__ import annotations

import httpx
from pydantic import ValidationError

from app.adapters.google_vision_ocr import GoogleVisionOcrAdapter, GoogleVisionOcrError
from app.schemas.contracts import PhotoOcrRequest, PhotoOcrResponse
from app.settings.config import Settings


class OcrWorkerError(RuntimeError):
    """Raised saat OCR worker tidak bisa dipakai oleh API."""


def _worker_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v1/ocr/photo"


def _normalized_provider(settings: Settings) -> str:
    return settings.ocr_provider.strip().lower()


def _should_use_worker(settings: Settings) -> bool:
    provider = _normalized_provider(settings)
    return provider == "worker" or (provider == "auto" and bool(settings.ocr_worker_url))


def _should_use_google_vision(settings: Settings) -> bool:
    provider = _normalized_provider(settings)
    return provider in {"google_vision", "vision"} or (
        provider == "auto"
        and not settings.ocr_worker_url
        and settings.google_vision_enabled
    )


def _call_google_vision(request: PhotoOcrRequest) -> PhotoOcrResponse:
    adapter = GoogleVisionOcrAdapter()
    if not adapter.available:
        raise OcrWorkerError(adapter.init_error or "Google Vision OCR belum tersedia.")
    try:
        return adapter.recognize(request)
    except GoogleVisionOcrError as exc:
        raise OcrWorkerError(f"Google Vision OCR gagal: {exc}") from exc


def call_ocr_worker(request: PhotoOcrRequest, settings: Settings) -> PhotoOcrResponse | None:
    """Jalankan OCR photo intake sesuai provider yang dikonfigurasi."""
    provider = _normalized_provider(settings)
    if _should_use_google_vision(settings):
        return _call_google_vision(request)
    if provider not in {"auto", "worker", "google_vision", "vision"}:
        raise OcrWorkerError(
            f"OCR_PROVIDER={settings.ocr_provider!r} tidak dikenal. "
            "Gunakan auto, worker, atau google_vision."
        )
    if not _should_use_worker(settings) or not settings.ocr_worker_url:
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
