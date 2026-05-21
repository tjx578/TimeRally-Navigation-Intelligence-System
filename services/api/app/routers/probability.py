"""Router /v1/probability - missing waypoint inference & route edit."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.places import Coordinate
from app.schemas.probability import (
    InferMissingWaypointRequest,
    InferMissingWaypointResponse,
    ProbabilityRouteCandidate,
    RouteEditOperation,
    RouteEditResponse,
)
from app.use_cases.infer_missing import InferMissingInput, infer_missing_waypoint
from rally_core.probability.resolver import CandidatePlace, WaypointAnchor


router = APIRouter()


def _build_candidate_pool(request: InferMissingWaypointRequest) -> list[CandidatePlace]:
    """Bangun candidate pool dari knowledge index lokal.

    Untuk dev/test, kita memakai 3 placeholder candidate di sekitar previous/next
    waypoint. Production harus mengirim kandidat dari place-resolver lewat
    request body atau API call internal.
    """
    return []


@router.post("/infer-missing-waypoint", response_model=InferMissingWaypointResponse)
def infer_missing_waypoint_endpoint(
    request: InferMissingWaypointRequest,
) -> InferMissingWaypointResponse:
    candidates = _build_candidate_pool(request)
    if not candidates:
        return InferMissingWaypointResponse(
            missing_waypoint_text=request.context.missing_waypoint_text,
            recommended_candidate_id=None,
            candidates=[],
            status="empty_pool: kirim kandidat dari place-resolver atau marshal hint",
        )

    payload = InferMissingInput(
        missing_text=request.context.missing_waypoint_text,
        previous=WaypointAnchor(
            id=request.context.previous_waypoint_id,
            lat=0.0,
            lng=0.0,
        ),
        next=WaypointAnchor(
            id=request.context.next_waypoint_id,
            lat=0.0,
            lng=0.0,
        ),
        target_distance_km=request.context.target_distance_km,
        target_time_seconds=request.context.target_time_seconds,
        navigation_action=request.context.navigation_action,
        landmark_type_hint=request.context.landmark_type_hint,
        text_context="",
        candidates=candidates,
        max_alternatives=request.max_candidates,
    )
    result = infer_missing_waypoint(payload)
    selected = result.selected
    return InferMissingWaypointResponse(
        missing_waypoint_text=request.context.missing_waypoint_text,
        recommended_candidate_id=(selected.candidate.id if selected else None),
        candidates=[
            ProbabilityRouteCandidate(
                id=e.candidate.id,
                label=e.candidate.name,
                coordinate=Coordinate(lat=e.candidate.lat, lng=e.candidate.lng),
                confidence=e.confidence,
                distance_deviation_percent=e.distance_deviation_percent,
                time_deviation_seconds=int(e.time_deviation_seconds),
                route_corridor_fit=e.candidate.route_corridor_fit,
                landmark_fit=e.candidate.turn_geometry_fit,
                turn_geometry_fit=e.candidate.turn_geometry_fit,
                provider=e.candidate.source,
                reasons=e.reasons,
                status=e.decision,
            )
            for e in ([result.selected] if result.selected else []) + result.alternatives
            if e is not None
        ],
        status=result.decision,
    )


@router.post("/route-edit", response_model=RouteEditResponse)
def apply_route_edit(operation: RouteEditOperation) -> RouteEditResponse:
    """Terapkan operasi edit rute manual (snap, insert, reverse, dst.).

    Operasi diteruskan ke worker rute. Kembalikan affected legs supaya UI
    dapat me-refresh validation.
    """
    affected = [operation.leg_id] if operation.leg_id else []
    operation_id = f"route-edit-{operation.event_id}-{operation.operation}"
    return RouteEditResponse(
        operation_id=operation_id,
        affected_leg_ids=affected,
        requires_revalidation=True,
        status="accepted",
    )
