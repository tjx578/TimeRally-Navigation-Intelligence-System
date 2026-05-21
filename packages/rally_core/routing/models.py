"""Domain model routing rally."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


Provider = Literal["auto", "valhalla", "osrm", "graphhopper", "google", "mock"]


@dataclass
class LatLng:
    lat: float
    lng: float

    def as_tuple(self) -> tuple[float, float]:
        return (self.lat, self.lng)

    def as_geojson(self) -> list[float]:
        # GeoJSON pakai [lng, lat]
        return [self.lng, self.lat]


@dataclass
class RouteWaypoint:
    id: str
    name: str
    coord: LatLng
    role: str = "waypoint"  # start | waypoint | finish | regroup | inferred


@dataclass
class TurnInstruction:
    text: str
    distance_m: int
    type: str = "continue"


@dataclass
class RouteSegment:
    from_waypoint: str
    to_waypoint: str
    distance_m: int
    duration_s: int
    polyline: list[LatLng] = field(default_factory=list)
    turn_instructions: list[TurnInstruction] = field(default_factory=list)
    provider: Provider = "valhalla"
    status: str = "ok"
    notes: list[str] = field(default_factory=list)


@dataclass
class RouteRequest:
    waypoints: list[RouteWaypoint]
    provider: Provider = "auto"
    profile: str = "rally_car"
    allow_reorder: bool = False  # default: rally TIDAK boleh reorder
    avoid: list[str] = field(default_factory=list)


@dataclass
class ProviderResult:
    provider: Provider
    segments: list[RouteSegment]
    total_distance_m: int
    total_duration_s: int
    confidence: float = 1.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ProviderComparison:
    primary: ProviderResult
    secondaries: list[ProviderResult]
    distance_spread_m: int
    duration_spread_s: int
    note: Optional[str] = None


@dataclass
class RoadbookLeg:
    order: int
    sub_trayek_id: str
    from_waypoint: str
    to_waypoint: str
    distance_m: int
    duration_s: int
    cumulative_distance_m: int
    cumulative_duration_s: int
    instruction: str
    landmark: Optional[str] = None
    eta_clock: Optional[str] = None
    speed_target_kmh: Optional[float] = None
    status: str = "verified"


@dataclass
class RouteValidationContext:
    target_distance_km: float
    target_time_minutes: float
    speed_mode: str
    sub_trayek_id: str
