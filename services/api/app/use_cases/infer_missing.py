"""Use case: probability resolver missing waypoint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from rally_core.probability.resolver import (
    CandidatePlace,
    MissingWaypointContext,
    MissingWaypointResolver,
    ResolveResult,
    WaypointAnchor,
)


_resolver = MissingWaypointResolver()


@dataclass
class InferMissingInput:
    missing_text: str
    previous: WaypointAnchor
    next: WaypointAnchor
    target_distance_km: float | None
    target_time_seconds: float | None
    navigation_action: str | None
    landmark_type_hint: str | None
    text_context: str
    candidates: list[CandidatePlace]
    max_alternatives: int = 5


def infer_missing_waypoint(payload: InferMissingInput) -> ResolveResult:
    context = MissingWaypointContext(
        missing_text=payload.missing_text,
        previous=payload.previous,
        next=payload.next,
        target_distance_km=payload.target_distance_km,
        target_time_seconds=payload.target_time_seconds,
        navigation_action=payload.navigation_action,
        landmark_type_hint=payload.landmark_type_hint,
        text_context=payload.text_context,
    )
    return _resolver.evaluate(context, payload.candidates, max_alternatives=payload.max_alternatives)
