from fastapi import APIRouter

from app.schemas.exports import ExportArtifact, ExportRequest, ExportResponse


router = APIRouter()


@router.post("/artifacts", response_model=ExportResponse)
def create_export(request: ExportRequest) -> ExportResponse:
    artifacts = [
        ExportArtifact(format=fmt, path=f"exports/{request.event_id}/route.{fmt}", status="planned")
        for fmt in request.formats
    ]
    return ExportResponse(event_id=request.event_id, artifacts=artifacts, status="skeleton_ready")

