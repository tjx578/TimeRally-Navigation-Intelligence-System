"""OCR worker placeholder with explicit manual verification semantics."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="Time Rally OCR Worker", version="0.1.0")


class OcrPhotoRequest(BaseModel):
    event_id: str
    photo_uri: str
    operator_hint: str | None = None


class OcrPhotoResponse(BaseModel):
    status: str = "manual_required"
    extracted_text: str = ""
    confidence: float = 0.0
    warnings: list[str] = Field(default_factory=list)


@app.get("/health")
@app.get("/healthz")
def health() -> dict:
    return {"status": "ok", "service": "ocr-worker"}


@app.get("/readyz")
def ready() -> dict:
    return {
        "status": "degraded",
        "checks": {
            "ocr_engine_configured": False,
            "manual_review_required": True,
        },
    }


@app.post("/v1/ocr/photo", response_model=OcrPhotoResponse)
def intake_photo(req: OcrPhotoRequest) -> OcrPhotoResponse:
    return OcrPhotoResponse(
        warnings=[
            f"OCR engine belum dikonfigurasi untuk event {req.event_id}; "
            "gunakan input teks manual terverifikasi.",
        ],
    )
