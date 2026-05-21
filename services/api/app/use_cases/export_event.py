"""Use case: bangun semua artefak export dan tulis ke configured sink."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.adapters.export_sink import get_export_sink

from rally_core.exporters import (
    build_offline_manifest,
    build_roadbook_table,
    export_event_yaml,
    export_geojson,
    export_gpx,
    export_kml,
    render_roadbook_markdown,
)
from rally_core.exporters.manifest import OfflineArtifact
from rally_core.parser.models import RallyEvent
from rally_core.routing.models import RouteSegment, RouteWaypoint


_FORMATS_DEFAULT = ("yaml", "gpx", "kml", "geojson", "roadbook.md")


@dataclass
class ExportRequestPayload:
    event_id: str
    event: RallyEvent
    waypoints: list[RouteWaypoint]
    segments: list[RouteSegment]
    rally_start_clock_minutes: int | None = None
    formats: tuple[str, ...] = _FORMATS_DEFAULT


@dataclass
class GeneratedArtifact:
    format: str
    path: str
    size_bytes: int


@dataclass
class ExportResultPayload:
    event_id: str
    artifacts: list[GeneratedArtifact] = field(default_factory=list)
    manifest_path: str | None = None
    notes: list[str] = field(default_factory=list)


def export_event_artifacts(payload: ExportRequestPayload) -> ExportResultPayload:
    sink = get_export_sink()
    artifacts: list[GeneratedArtifact] = []
    manifest_artifacts: list[OfflineArtifact] = []
    waypoints_by_id = {wp.id: wp for wp in payload.waypoints}

    if "yaml" in payload.formats:
        content = export_event_yaml(payload.event)
        artifact = sink.write(payload.event_id, "event.yaml", content)
        artifacts.append(GeneratedArtifact("yaml", artifact.path, artifact.size_bytes))
        manifest_artifacts.append(
            OfflineArtifact(
                name="event", format="yaml", path=artifact.path, size_bytes=artifact.size_bytes
            )
        )
    if "gpx" in payload.formats:
        gpx = export_gpx(payload.event.event_name, payload.waypoints, payload.segments)
        artifact = sink.write(payload.event_id, "route.gpx", gpx)
        artifacts.append(GeneratedArtifact("gpx", artifact.path, artifact.size_bytes))
        manifest_artifacts.append(
            OfflineArtifact(name="route", format="gpx", path=artifact.path, size_bytes=artifact.size_bytes)
        )
    if "kml" in payload.formats:
        kml = export_kml(payload.event.event_name, payload.waypoints, payload.segments)
        artifact = sink.write(payload.event_id, "route.kml", kml)
        artifacts.append(GeneratedArtifact("kml", artifact.path, artifact.size_bytes))
        manifest_artifacts.append(
            OfflineArtifact(name="route", format="kml", path=artifact.path, size_bytes=artifact.size_bytes)
        )
    if "geojson" in payload.formats:
        gj = export_geojson(payload.waypoints, payload.segments)
        artifact = sink.write(payload.event_id, "route.geojson", gj)
        artifacts.append(GeneratedArtifact("geojson", artifact.path, artifact.size_bytes))
        manifest_artifacts.append(
            OfflineArtifact(
                name="route", format="geojson", path=artifact.path, size_bytes=artifact.size_bytes
            )
        )
    if "roadbook.md" in payload.formats:
        legs = build_roadbook_table(
            payload.segments,
            waypoints_by_id,
            payload.rally_start_clock_minutes,
        )
        md = render_roadbook_markdown(payload.event.event_name, legs)
        artifact = sink.write(payload.event_id, "roadbook.md", md)
        artifacts.append(GeneratedArtifact("roadbook.md", artifact.path, artifact.size_bytes))
        manifest_artifacts.append(
            OfflineArtifact(
                name="roadbook", format="md", path=artifact.path, size_bytes=artifact.size_bytes
            )
        )

    manifest = build_offline_manifest(
        event_id=payload.event_id,
        event_name=payload.event.event_name,
        artifacts=manifest_artifacts,
    )
    import json

    manifest_artifact = sink.write(
        payload.event_id,
        "manifest.json",
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2),
    )
    return ExportResultPayload(
        event_id=payload.event_id,
        artifacts=artifacts,
        manifest_path=manifest_artifact.path,
        notes=[f"{len(artifacts)} artefak berhasil dibuat"],
    )
