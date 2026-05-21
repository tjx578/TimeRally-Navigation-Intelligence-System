"""Cross-service data contracts (TypedDict/pydantic-friendly dataclass)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Status = Literal[
    "verified_local",
    "verified_kmpal",
    "verified_osm",
    "verified_google_online",
    "inferred_high_confidence",
    "inferred_low_confidence",
    "unresolved",
]


@dataclass
class Coordinate:
    lat: float
    lng: float


@dataclass
class Place:
    id: str
    name: str
    coordinate: Coordinate
    category: str = "unknown"
    source: str = "unknown"
    confidence: float = 1.0
    region: str = ""


@dataclass
class Candidate:
    id: str
    place: Place
    confidence: float
    status: Status
    reasons: list[str] = field(default_factory=list)
    distance_deviation_percent: float = 0.0
    time_deviation_seconds: float = 0.0


@dataclass
class Waypoint:
    id: str
    sub_trayek_id: str
    order: int
    raw_text: str
    coordinate: Optional[Coordinate]
    candidates: list[Candidate] = field(default_factory=list)
    status: Status = "unresolved"
    action: Optional[str] = None
    landmark_type: Optional[str] = None
    landmark_name: Optional[str] = None
    notes: list[str] = field(default_factory=list)


@dataclass
class SubTrayek:
    id: str
    label: str
    title: str
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
    speed_mode: str = "unknown"
    distance_counted_in_total: bool = True
    waypoints: list[Waypoint] = field(default_factory=list)


@dataclass
class RallyEvent:
    id: str
    name: str
    location: str = ""
    rally_start_time: Optional[str] = None
    total_distance_km: Optional[float] = None
    total_time_minutes: Optional[float] = None
    sub_trayeks: list[SubTrayek] = field(default_factory=list)


@dataclass
class RouteSegment:
    from_waypoint: str
    to_waypoint: str
    distance_m: int
    duration_s: int
    polyline: list[Coordinate] = field(default_factory=list)
    provider: str = "valhalla"
    status: str = "ok"


@dataclass
class ValidationCheck:
    name: str
    status: str
    target: Optional[float] = None
    actual: Optional[float] = None
    delta: Optional[float] = None
    unit: Optional[str] = None
    message: str = ""


@dataclass
class ValidationReport:
    event_id: str
    overall_status: str
    checks: list[ValidationCheck] = field(default_factory=list)


@dataclass
class ChampionshipScore:
    event_id: str
    total: float
    components: dict[str, float] = field(default_factory=dict)
    penalties: list[str] = field(default_factory=list)
    verdict: str = "marginal"


@dataclass
class ExportArtifact:
    format: str
    path: str
    status: str
    size_bytes: int = 0


@dataclass
class ExportManifest:
    event_id: str
    generated_at: str
    artifacts: list[ExportArtifact] = field(default_factory=list)
