"""Lintas-service data contracts.

Setiap service & UI MENGACU ke kontrak ini. Jangan duplikasi definisi
dataclass yang sama di service lain.
"""

from data_contracts.models import (
    Coordinate,
    Place,
    Candidate,
    Waypoint,
    SubTrayek,
    RallyEvent,
    RouteSegment,
    ValidationReport,
    ChampionshipScore,
    ExportArtifact,
    ExportManifest,
)

__all__ = [
    "Coordinate",
    "Place",
    "Candidate",
    "Waypoint",
    "SubTrayek",
    "RallyEvent",
    "RouteSegment",
    "ValidationReport",
    "ChampionshipScore",
    "ExportArtifact",
    "ExportManifest",
]
