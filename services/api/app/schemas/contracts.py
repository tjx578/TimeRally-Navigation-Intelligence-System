from pydantic import BaseModel, Field


class ParsedWaypointResponse(BaseModel):
    id: str
    sub_trayek_id: str
    order: int
    raw_text: str
    action: str | None = None
    landmark_type: str | None = None
    landmark_name: str | None = None
    relation: str | None = None
    kmpal_marker: str | None = None
    notes: list[str] = Field(default_factory=list)
    ambiguous: bool = False


class ParsedSubTrayekResponse(BaseModel):
    id: str
    label: str
    title: str
    distance_km: float | None = None
    duration_minutes: float | None = None
    speed_mode: str
    distance_counted_in_total: bool
    waypoints: list[ParsedWaypointResponse]


class UnresolvedTokenResponse(BaseModel):
    token: str
    sub_trayek_id: str | None = None
    line_index: int
    reason: str


class RallyParseRequest(BaseModel):
    raw_text: str = Field(..., description="Raw rally problem text or OCR output")
    event_name: str | None = None
    total_distance_km: float | None = None
    total_time_minutes: int | None = None


class RallyParseResponse(BaseModel):
    event_name: str
    trayek_name: str | None = None
    location: str | None = None
    normalized_text: str
    total_distance_km: float | None = None
    total_time_minutes: float | None = None
    sub_trayek_count: int
    waypoint_count: int
    sub_trayeks: list[ParsedSubTrayekResponse] = Field(default_factory=list)
    unresolved_tokens: list[UnresolvedTokenResponse] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
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
