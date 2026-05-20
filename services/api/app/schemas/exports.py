from pydantic import BaseModel


class ExportRequest(BaseModel):
    event_id: str
    formats: list[str] = ["yaml", "gpx", "kml", "geojson"]
    include_validation_report: bool = True
    include_candidate_review: bool = True


class ExportArtifact(BaseModel):
    format: str
    path: str
    status: str


class ExportResponse(BaseModel):
    event_id: str
    artifacts: list[ExportArtifact]
    status: str

