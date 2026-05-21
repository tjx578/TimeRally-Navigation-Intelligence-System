"""Router /v1/export - export artefak rally."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.exports import ExportArtifact, ExportRequest, ExportResponse
from rally_core.exporters import build_offline_manifest
from rally_core.exporters.manifest import OfflineArtifact


router = APIRouter()


_FORMAT_TO_FILENAME = {
    "yaml": "event.yaml",
    "gpx": "route.gpx",
    "kml": "route.kml",
    "geojson": "route.geojson",
    "roadbook": "roadbook.md",
    "roadbook.md": "roadbook.md",
}


@router.post("/artifacts", response_model=ExportResponse)
def create_export(request: ExportRequest) -> ExportResponse:
    """Buat artefak hasil export.

    Endpoint ini mengembalikan path tujuan artefak (siap dipakai download).
    Generator artefak akan dipanggil oleh worker pipeline saat event sudah
    melewati semua quality gate. Generator runtime ada di
    ``rally_core.exporters`` dan dipanggil via use case ``export_event_artifacts``.
    """
    artifacts: list[ExportArtifact] = []
    manifest_artifacts: list[OfflineArtifact] = []
    for fmt in request.formats:
        filename = _FORMAT_TO_FILENAME.get(fmt.lower(), f"route.{fmt}")
        path = f"exports/{request.event_id}/{filename}"
        artifacts.append(ExportArtifact(format=fmt, path=path, status="queued"))
        manifest_artifacts.append(OfflineArtifact(name=filename, format=fmt, path=path))

    manifest = build_offline_manifest(
        event_id=request.event_id,
        event_name=request.event_id,
        artifacts=manifest_artifacts,
    )

    return ExportResponse(
        event_id=request.event_id,
        artifacts=artifacts,
        status=f"queued: manifest @ {manifest.generated_at}",
    )
