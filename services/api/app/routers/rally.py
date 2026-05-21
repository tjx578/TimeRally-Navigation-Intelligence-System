"""Router /v1/rally - parse soal rally dan photo OCR intake."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.contracts import (
    PhotoOcrRequest,
    PhotoOcrResponse,
    ParsedSubTrayekResponse,
    ParsedWaypointResponse,
    RallyParseRequest,
    RallyParseResponse,
    UnresolvedTokenResponse,
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
        trayek_name=event.trayek_name,
        location=event.location,
        normalized_text=event.normalized_text,
        total_distance_km=event.total_distance_km,
        total_time_minutes=event.total_time_minutes,
        sub_trayek_count=len(event.sub_trayeks),
        waypoint_count=event.waypoint_count,
        sub_trayeks=[
            ParsedSubTrayekResponse(
                id=sub.id,
                label=sub.label,
                title=sub.title,
                distance_km=sub.distance_km,
                duration_minutes=sub.duration_minutes,
                speed_mode=sub.speed_mode,
                distance_counted_in_total=sub.distance_counted_in_total,
                waypoints=[
                    ParsedWaypointResponse(
                        id=wp.id,
                        sub_trayek_id=wp.sub_trayek_id,
                        order=wp.order,
                        raw_text=wp.raw_text,
                        action=wp.action,
                        landmark_type=wp.landmark_type,
                        landmark_name=wp.landmark_name,
                        relation=wp.relation,
                        kmpal_marker=wp.kmpal_marker,
                        notes=wp.notes,
                        ambiguous=wp.ambiguous,
                    )
                    for wp in sub.waypoints
                ],
            )
            for sub in event.sub_trayeks
        ],
        unresolved_tokens=[
            UnresolvedTokenResponse(
                token=token.token,
                sub_trayek_id=token.sub_trayek_id,
                line_index=token.line_index,
                reason=token.reason,
            )
            for token in result.unresolved_tokens
        ],
        warnings=result.warnings,
        status=result.status,
        next_action=(
            "resolve waypoints" if event.sub_trayeks else "kirim soal lebih lengkap"
        ),
    )


@router.post("/photo-ocr", response_model=PhotoOcrResponse)
def photo_ocr(request: PhotoOcrRequest) -> PhotoOcrResponse:
    """Photo OCR intake.

    Implementasi OCR penuh dijalankan oleh worker terpisah (Tesseract/PaddleOCR).
    Endpoint ini tidak mengarang event demo; bila worker belum tersedia, UI wajib
    jatuh ke manual paste agar operator tidak memakai data palsu di lapangan.
    """
    warnings: list[str] = []
    if not request.photos:
        warnings.append("Minimal satu foto soal diperlukan.")
    for photo in request.photos:
        if not photo.image_base64 and not photo.filename:
            warnings.append("Setiap foto harus punya base64 atau filename.")
            break

    return PhotoOcrResponse(
        event_name="",
        trayek_name="",
        location="",
        normalized_text="",
        detected_total_distance_km=None,
        detected_total_time_minutes=None,
        photo_count=len(request.photos),
        status="ocr_worker_unavailable_manual_parse_required",
        warnings=[
            *warnings,
            "Foto diterima, tetapi OCR worker belum dikonfigurasi. Tempel hasil OCR/manual text ke panel soal sebelum mapping dan export.",
        ],
    )
