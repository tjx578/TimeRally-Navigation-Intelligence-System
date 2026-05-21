"""Domain models untuk hasil parsing soal rally."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional


SpeedMode = Literal[
    "liaison_zero_trip",
    "average_speed",
    "fixed_second",
    "fixed_minute",
    "remaining_distance",
    "free_time",
    "unknown",
]


@dataclass
class ParsedWaypoint:
    """Waypoint hasil parsing soal.

    Belum memiliki koordinat. Resolver yang bertanggung jawab mengisi koordinat.
    """

    id: str
    sub_trayek_id: str
    order: int
    raw_text: str
    action: Optional[str] = None  # belok_kanan, belok_kiri, jalan_terus, dst.
    landmark_type: Optional[str] = None  # bundaran, simpang_empat, banjar, dst.
    landmark_name: Optional[str] = None
    relation: Optional[str] = None  # at, before, after
    kmpal_marker: Optional[str] = None  # contoh: "KSM 2/DPS 11/PNT 0"
    notes: list[str] = field(default_factory=list)
    ambiguous: bool = False


@dataclass
class SubTrayek:
    """Sub trayek (Sub A, Sub B, dst.)."""

    id: str
    label: str  # A, B, C
    title: str
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
    speed_mode: SpeedMode = "unknown"
    distance_counted_in_total: bool = True
    waypoints: list[ParsedWaypoint] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)


@dataclass
class RallyEvent:
    """Container rally event hasil parsing."""

    event_name: str
    trayek_name: Optional[str] = None
    location: Optional[str] = None
    total_distance_km: Optional[float] = None
    total_time_minutes: Optional[float] = None
    rally_start_time: Optional[str] = None
    sub_trayeks: list[SubTrayek] = field(default_factory=list)
    source: str = "manual"
    normalized_text: str = ""

    @property
    def waypoint_count(self) -> int:
        return sum(len(s.waypoints) for s in self.sub_trayeks)


@dataclass
class UnresolvedToken:
    """Token soal yang tidak bisa dipetakan parser."""

    token: str
    sub_trayek_id: Optional[str]
    line_index: int
    reason: str


@dataclass
class ParseResult:
    """Hasil akhir parsing soal."""

    event: RallyEvent
    unresolved_tokens: list[UnresolvedToken] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if not self.event.sub_trayeks:
            return "empty"
        if self.warnings or self.unresolved_tokens:
            return "warning"
        return "ok"
