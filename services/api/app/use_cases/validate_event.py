"""Use case: validasi absolute binding constraint event rally."""

from __future__ import annotations

from dataclasses import dataclass

from rally_core.constraints.engine import (
    ChainingInput,
    ConstraintEngine,
    SubTrayekValidationInput,
)
from rally_core.constraints.types import ConstraintCheck


@dataclass
class ValidationInput:
    target_distance_km: float | None
    target_time_minutes: float | None
    calculated_distance_km: float | None
    calculated_time_minutes: float | None
    sub_trayeks: list[SubTrayekValidationInput]
    chains: list[ChainingInput]
    route_distance_km: float | None = None
    straight_line_distance_km: float | None = None
    coordinates: list[tuple[float, float]] | None = None


def validate_event(payload: ValidationInput) -> list[ConstraintCheck]:
    engine = ConstraintEngine()
    checks: list[ConstraintCheck] = []
    checks.append(
        engine.check_total_distance(payload.target_distance_km, payload.calculated_distance_km)
    )
    checks.append(
        engine.check_total_time(payload.target_time_minutes, payload.calculated_time_minutes)
    )
    for sub in payload.sub_trayeks:
        checks.extend(engine.check_sub_trayek(sub))
    checks.extend(engine.check_chaining(payload.chains))
    if payload.coordinates:
        checks.append(engine.check_coordinate_precision(payload.coordinates))
    if payload.route_distance_km is not None and payload.straight_line_distance_km is not None:
        checks.append(
            engine.check_route_realism(
                straight_line_distance_km=payload.straight_line_distance_km,
                route_distance_km=payload.route_distance_km,
            )
        )
    return checks
