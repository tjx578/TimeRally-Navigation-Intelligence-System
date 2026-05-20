from pydantic import BaseModel, Field


class RallyParseRequest(BaseModel):
    raw_text: str = Field(..., description="Raw rally problem text or OCR output")
    event_name: str | None = None
    total_distance_km: float | None = None
    total_time_minutes: int | None = None


class RallyParseResponse(BaseModel):
    event_name: str
    normalized_text: str
    sub_trayek_count: int
    waypoint_count: int
    status: str
    next_action: str


class QuestionPhotoInput(BaseModel):
    filename: str
    mime_type: str | None = None
    image_base64: str | None = Field(
        default=None,
        description="Optional base64 payload for browser photo OCR intake",
    )


class PhotoOcrRequest(BaseModel):
    photos: list[QuestionPhotoInput]
    auto_parse: bool = True
    auto_map_subtrayek: bool = True


class PhotoOcrResponse(BaseModel):
    event_name: str
    trayek_name: str
    location: str
    normalized_text: str
    detected_total_distance_km: float | None
    detected_total_time_minutes: int | None
    photo_count: int
    status: str
    warnings: list[str]
