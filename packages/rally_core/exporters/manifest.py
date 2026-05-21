"""Offline package manifest builder.

Manifest digunakan oleh field-mobile dan offline package builder untuk
mengetahui artefak apa saja yang harus disinkronkan ke device.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class OfflineArtifact:
    name: str
    format: str
    path: str
    size_bytes: int = 0
    checksum_sha256: str | None = None


@dataclass
class OfflineManifest:
    event_id: str
    event_name: str
    generated_at: str
    artifacts: list[OfflineArtifact] = field(default_factory=list)
    tile_package: str | None = None
    routing_graph: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_name": self.event_name,
            "generated_at": self.generated_at,
            "artifacts": [a.__dict__ for a in self.artifacts],
            "tile_package": self.tile_package,
            "routing_graph": self.routing_graph,
            "notes": self.notes,
        }


def build_offline_manifest(
    event_id: str,
    event_name: str,
    artifacts: list[OfflineArtifact],
    tile_package: str | None = None,
    routing_graph: str | None = None,
) -> OfflineManifest:
    return OfflineManifest(
        event_id=event_id,
        event_name=event_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        artifacts=artifacts,
        tile_package=tile_package,
        routing_graph=routing_graph,
    )
