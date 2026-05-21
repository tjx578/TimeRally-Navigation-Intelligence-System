from pydantic import BaseModel, Field

from app.schemas.places import Coordinate


class ExportWaypoint(BaseModel):
    id: str
    name: str
    coordinate: Coordinate
    role: str = "waypoint"


class ExportRouteSegment(BaseModel):
    from_waypoint: str
    to_waypoint: str
    distance_m: int
    duration_s: int
    polyline: list[Coordinate] = Field(default_factory=list)
    provider: str = "valhalla"
    status: str = "ok"


class ExportRequest(BaseModel):
    event_id: str
    event_name: str | None = None
    normalized_text: str = ""
    rally_start_clock_minutes: int | None = None
    formats: list[str] = Field(default_factory=lambda: ["yaml", "gpx", "kml", "geojson", "roadbook.md"])
    include_validation_report: bool = True
    include_candidate_review: bool = True
    waypoints: list[ExportWaypoint] = Field(default_factory=list)
    segments: list[ExportRouteSegment] = Field(default_factory=list)


class ExportArtifact(BaseModel):
    format: str
    path: str
    status: str
    size_bytes: int | None = None


class ExportResponse(BaseModel):
    event_id: str
    artifacts: list[ExportArtifact]
    status: str
