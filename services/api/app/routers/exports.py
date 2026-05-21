"""Router /v1/export - export artefak rally."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.exports import ExportArtifact, ExportRequest, ExportResponse
from app.use_cases.export_event import ExportRequestPayload, export_event_artifacts
from rally_core.parser.models import RallyEvent
from rally_core.routing.models import LatLng, RouteSegment, RouteWaypoint


router = APIRouter()


@router.post("/artifacts", response_model=ExportResponse)
def create_export(request: ExportRequest) -> ExportResponse:
    """Buat artefak hasil export.

    Production path harus menulis artefak nyata. Jika UI belum mengirim route
    final, endpoint mengembalikan status blocked agar operator tidak salah
    mengira export sudah dibuat.
    """
    if not request.waypoints or not request.segments:
        return ExportResponse(
            event_id=request.event_id,
            artifacts=[
                ExportArtifact(
                    format=fmt,
                    path="",
                    status="blocked_missing_route_data",
                )
                for fmt in request.formats
            ],
            status="blocked: kirim waypoints dan route segments final sebelum export",
        )

    event = RallyEvent(
        event_name=request.event_name or request.event_id,
        normalized_text=request.normalized_text,
        source="api_export",
    )
    waypoints = [
        RouteWaypoint(
            id=wp.id,
            name=wp.name,
            coord=LatLng(lat=wp.coordinate.lat, lng=wp.coordinate.lng),
            role=wp.role,
        )
        for wp in request.waypoints
    ]
    segments = [
        RouteSegment(
            from_waypoint=segment.from_waypoint,
            to_waypoint=segment.to_waypoint,
            distance_m=segment.distance_m,
            duration_s=segment.duration_s,
            polyline=[
                LatLng(lat=point.lat, lng=point.lng)
                for point in segment.polyline
            ],
            provider=segment.provider,  # type: ignore[arg-type]
            status=segment.status,
        )
        for segment in request.segments
    ]
    formats = tuple("roadbook.md" if fmt == "roadbook" else fmt for fmt in request.formats)
    result = export_event_artifacts(
        ExportRequestPayload(
            event_id=request.event_id,
            event=event,
            waypoints=waypoints,
            segments=segments,
            rally_start_clock_minutes=request.rally_start_clock_minutes,
            formats=formats,
        )
    )

    return ExportResponse(
        event_id=request.event_id,
        artifacts=[
            ExportArtifact(
                format=artifact.format,
                path=artifact.path,
                status="generated",
                size_bytes=artifact.size_bytes,
            )
            for artifact in result.artifacts
        ],
        status=f"generated: manifest @ {result.manifest_path}",
    )
