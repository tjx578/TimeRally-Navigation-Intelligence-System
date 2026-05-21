"""OCR worker dengan mode Google Cloud Vision dan fallback manual."""

from __future__ import annotations

import base64
import os
from statistics import mean

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Time Rally OCR Worker", version="0.2.0")


class QuestionPhotoInput(BaseModel):
    filename: str
    mime_type: str | None = None
    image_base64: str | None = Field(default=None)


class OcrPhotoRequest(BaseModel):
    photos: list[QuestionPhotoInput] = Field(default_factory=list)
    auto_parse: bool = True
    auto_map_subtrayek: bool = True
    event_id: str | None = None
    photo_uri: str | None = None
    operator_hint: str | None = None


class OcrPhotoResponse(BaseModel):
    event_name: str = ""
    trayek_name: str = ""
    location: str = ""
    normalized_text: str = ""
    detected_total_distance_km: float | None = None
    detected_total_time_minutes: int | None = None
    photo_count: int = 0
    status: str = "manual_required"
    warnings: list[str] = Field(default_factory=list)


def _ocr_engine() -> str:
    return os.getenv("OCR_ENGINE", "disabled").strip().lower()


def _min_confidence() -> float:
    try:
        return float(os.getenv("OCR_MIN_CONFIDENCE", "0.1"))
    except ValueError:
        return 0.1


def _decode_base64_image(photo: QuestionPhotoInput) -> bytes:
    if not photo.image_base64:
        raise ValueError(f"{photo.filename}: payload base64 kosong.")
    payload = photo.image_base64.strip()
    if "," in payload and payload.lower().startswith("data:"):
        payload = payload.split(",", 1)[1]
    return base64.b64decode(payload, validate=True)


def _google_vision_ocr(photo: QuestionPhotoInput) -> tuple[str, float]:
    try:
        from google.cloud import vision
    except ImportError as exc:  # pragma: no cover - tergantung image worker
        raise RuntimeError("google-cloud-vision belum terpasang di image OCR worker.") from exc

    client = vision.ImageAnnotatorClient()
    response = client.document_text_detection(image=vision.Image(content=_decode_base64_image(photo)))
    if response.error.message:
        raise RuntimeError(f"{photo.filename}: {response.error.message}")

    annotation = response.full_text_annotation
    text = annotation.text if annotation else ""
    confidences: list[float] = []
    if annotation:
        for page in annotation.pages:
            for block in page.blocks:
                if block.confidence:
                    confidences.append(float(block.confidence))

    confidence = mean(confidences) if confidences else (1.0 if text.strip() else 0.0)
    return text.strip(), confidence


def _run_ocr(req: OcrPhotoRequest) -> tuple[str, list[str], float]:
    engine = _ocr_engine()
    warnings: list[str] = []
    if engine not in {"google_vision", "vision"}:
        return (
            "",
            [
                "OCR worker aktif, tetapi OCR_ENGINE belum diset ke google_vision. "
                "Gunakan input teks manual terverifikasi.",
            ],
            0.0,
        )

    texts: list[str] = []
    confidences: list[float] = []
    for index, photo in enumerate(req.photos, start=1):
        try:
            text, confidence = _google_vision_ocr(photo)
        except (RuntimeError, ValueError) as exc:
            warnings.append(str(exc))
            continue

        if confidence < _min_confidence():
            warnings.append(
                f"{photo.filename}: confidence OCR rendah ({confidence:.2f}); wajib review manual."
            )
        if text:
            texts.append(f"--- FOTO {index}: {photo.filename} ---\n{text}")
        confidences.append(confidence)

    return "\n\n".join(texts).strip(), warnings, mean(confidences) if confidences else 0.0


@app.get("/health")
@app.get("/healthz")
def health() -> dict:
    return {"status": "ok", "service": "ocr-worker", "engine": _ocr_engine()}


@app.get("/readyz")
def ready() -> dict:
    configured = _ocr_engine() in {"google_vision", "vision"}
    return {
        "status": "ready" if configured else "degraded",
        "checks": {
            "ocr_engine_configured": configured,
            "engine": _ocr_engine(),
            "manual_review_required": True,
        },
    }


@app.post("/v1/ocr/photo", response_model=OcrPhotoResponse)
def intake_photo(req: OcrPhotoRequest) -> OcrPhotoResponse:
    if not req.photos:
        return OcrPhotoResponse(
            photo_count=0,
            status="failed",
            warnings=["Minimal satu foto soal diperlukan untuk OCR."],
        )

    normalized_text, warnings, confidence = _run_ocr(req)
    if not normalized_text:
        return OcrPhotoResponse(
            photo_count=len(req.photos),
            status="manual_required",
            warnings=[
                *warnings,
                "OCR belum menghasilkan teks yang bisa dipakai; tempel hasil OCR/manual text ke panel soal.",
            ],
        )

    status = "ocr_ready" if confidence >= _min_confidence() else "ocr_low_confidence_review_required"
    return OcrPhotoResponse(
        normalized_text=normalized_text,
        photo_count=len(req.photos),
        status=status,
        warnings=warnings,
    )
