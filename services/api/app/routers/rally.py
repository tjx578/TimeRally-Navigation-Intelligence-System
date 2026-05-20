from fastapi import APIRouter

from app.schemas.contracts import (
    PhotoOcrRequest,
    PhotoOcrResponse,
    RallyParseRequest,
    RallyParseResponse,
)


router = APIRouter()


@router.post("/parse", response_model=RallyParseResponse)
def parse_rally(request: RallyParseRequest) -> RallyParseResponse:
    return RallyParseResponse(
        event_name=request.event_name or "Untitled Rally Event",
        normalized_text=request.raw_text.strip(),
        sub_trayek_count=0,
        waypoint_count=0,
        status="skeleton_ready",
        next_action="wire packages.rally_core.parser",
    )


@router.post("/photo-ocr", response_model=PhotoOcrResponse)
def photo_ocr(request: PhotoOcrRequest) -> PhotoOcrResponse:
    warnings: list[str] = []
    if not request.photos:
        warnings.append("At least one question photo is required.")

    return PhotoOcrResponse(
        event_name="Pertamina Merah Putih Kejurnas Wisata Rally Bali Putaran 1 - 2024",
        trayek_name="Trayek 1",
        location="Bali",
        normalized_text="OCR engine placeholder. Browser intake is wired; production OCR worker will populate this field.",
        detected_total_distance_km=93.40,
        detected_total_time_minutes=270,
        photo_count=len(request.photos),
        status="ocr_pipeline_skeleton_ready",
        warnings=warnings,
    )
