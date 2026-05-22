"""Google Cloud Vision OCR adapter untuk photo intake.

Mengubah ``PhotoOcrRequest.photos[].image_base64`` jadi teks soal menggunakan
``vision.ImageAnnotatorClient.document_text_detection``. Dipakai oleh
``adapters.ocr_worker.call_ocr_worker`` ketika ``OCR_PROVIDER=google_vision``.

Library ``google-cloud-vision`` adalah optional dependency. Kalau modul belum
terinstal di image, ``GoogleVisionOcrAdapter.available`` = False dan caller
akan fallback ke worker HTTP / manual paste.
"""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass

from app.schemas.contracts import (
    PhotoOcrRequest,
    PhotoOcrResponse,
)


class GoogleVisionOcrError(RuntimeError):
    """Raised saat Vision OCR gagal memproses payload."""


@dataclass
class _PhotoOcrFragment:
    filename: str
    text: str
    page_role: str | None = None


class GoogleVisionOcrAdapter:
    """Wrapper tipis di sekitar ImageAnnotatorClient.

    Penggunaan:
        adapter = GoogleVisionOcrAdapter()
        if adapter.available:
            response = adapter.recognize(request)
    """

    def __init__(self) -> None:
        self._client = None
        self._init_error: str | None = None
        try:
            from google.cloud import vision  # type: ignore[import-not-found]

            self._client_cls = vision.ImageAnnotatorClient
            self._image_cls = vision.Image
        except Exception as exc:  # noqa: BLE001 - SDK boleh tidak terinstal di dev.
            self._client_cls = None
            self._image_cls = None
            self._init_error = f"google-cloud-vision tidak tersedia: {exc}"

    @property
    def available(self) -> bool:
        return self._client_cls is not None

    @property
    def init_error(self) -> str | None:
        return self._init_error

    def _client_singleton(self):
        if not self.available:
            raise GoogleVisionOcrError(self._init_error or "vision client belum siap")
        if self._client is None:
            try:
                self._client = self._client_cls()  # type: ignore[misc]
            except Exception as exc:  # noqa: BLE001
                raise GoogleVisionOcrError(
                    f"gagal inisialisasi ImageAnnotatorClient: {exc}"
                ) from exc
        return self._client

    def recognize_image_bytes(self, image_bytes: bytes) -> str:
        """Jalankan document_text_detection pada satu image bytes."""
        client = self._client_singleton()
        image = self._image_cls(content=image_bytes)  # type: ignore[misc]
        response = client.document_text_detection(image=image)
        if getattr(response, "error", None) and response.error.message:
            raise GoogleVisionOcrError(response.error.message)
        full = getattr(response, "full_text_annotation", None)
        if full and full.text:
            return full.text.strip()
        if response.text_annotations:
            return response.text_annotations[0].description.strip()
        return ""

    def recognize(self, request: PhotoOcrRequest) -> PhotoOcrResponse:
        """Proses seluruh photos di request, gabungkan teks per halaman."""
        if not self.available:
            raise GoogleVisionOcrError(self._init_error or "vision client belum siap")
        if not request.photos:
            raise GoogleVisionOcrError("photos kosong; tidak ada gambar untuk OCR")

        fragments: list[_PhotoOcrFragment] = []
        warnings: list[str] = []
        for photo in request.photos:
            if not photo.image_base64:
                warnings.append(
                    f"{photo.filename or 'foto'} tidak punya image_base64; lewati."
                )
                continue
            try:
                image_bytes = base64.b64decode(photo.image_base64, validate=False)
            except (binascii.Error, ValueError) as exc:
                warnings.append(f"{photo.filename or 'foto'}: base64 invalid ({exc}).")
                continue
            try:
                text = self.recognize_image_bytes(image_bytes)
            except GoogleVisionOcrError as exc:
                warnings.append(
                    f"{photo.filename or 'foto'}: vision error ({exc})."
                )
                continue
            fragments.append(
                _PhotoOcrFragment(
                    filename=photo.filename or "",
                    text=text,
                )
            )

        normalized_text = "\n\n".join(f.text for f in fragments if f.text).strip()
        status = "ok" if normalized_text else "empty"

        return PhotoOcrResponse(
            event_name="",
            trayek_name="",
            location="",
            normalized_text=normalized_text,
            detected_total_distance_km=None,
            detected_total_time_minutes=None,
            photo_count=len(request.photos),
            status=status,
            warnings=warnings,
        )
