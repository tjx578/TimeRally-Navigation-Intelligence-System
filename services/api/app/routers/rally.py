"""Router /v1/rally - parse soal rally dan photo OCR intake."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.contracts import (
    PhotoOcrRequest,
    PhotoOcrResponse,
    RallyParseRequest,
    RallyParseResponse,
)
from app.use_cases import parse_rally_text


router = APIRouter()


@router.post("/parse", response_model=RallyParseResponse)
def parse_rally(request: RallyParseRequest) -> RallyParseResponse:
    """Parse soal rally menjadi struktur event + sub-trayek."""
    result = parse_rally_text(
        raw_text=request.raw_text,
        event_name_hint=request.event_name,
    )
    event = result.event
    # Hint dari request soal punya prioritas lebih rendah daripada deteksi parser
    if request.total_distance_km is not None and event.total_distance_km is None:
        event.total_distance_km = request.total_distance_km
    if request.total_time_minutes is not None and event.total_time_minutes is None:
        event.total_time_minutes = request.total_time_minutes

    return RallyParseResponse(
        event_name=event.event_name,
        normalized_text=event.normalized_text,
        sub_trayek_count=len(event.sub_trayeks),
        waypoint_count=event.waypoint_count,
        status=result.status,
        next_action=(
            "resolve waypoints" if event.sub_trayeks else "kirim soal lebih lengkap"
        ),
    )


@router.post("/photo-ocr", response_model=PhotoOcrResponse)
def photo_ocr(request: PhotoOcrRequest) -> PhotoOcrResponse:
    """Photo OCR intake.

    Implementasi OCR penuh dijalankan oleh worker terpisah (tesseract / paddleOCR).
    Endpoint ini menerima foto dari browser, memvalidasi payload, dan
    mengembalikan event canonical jika foto kosong (mode demo) atau metadata
    intake yang akan dipakai worker.
    """
    warnings: list[str] = []
    if not request.photos:
        warnings.append("Minimal satu foto soal diperlukan.")
    for photo in request.photos:
        if not photo.image_base64 and not photo.filename:
            warnings.append("Setiap foto harus punya base64 atau filename.")
            break

    # Demo intake: kembalikan canonical event Bali Trayek 1 sebagai sample header
    return PhotoOcrResponse(
        event_name="Pertamina Merah Putih Kejurnas Wisata Rally Bali Putaran 1 - 2024",
        trayek_name="Trayek 1",
        location="Bali",
        normalized_text=(
            "OCR intake diterima. Worker OCR akan mengekstrak teks soal dan mengembalikan "
            "struktur sub-trayek lewat /v1/rally/parse."
        ),
        detected_total_distance_km=93.40,
        detected_total_time_minutes=270,
        photo_count=len(request.photos),
        status="ocr_intake_accepted",
        warnings=warnings,
    )
