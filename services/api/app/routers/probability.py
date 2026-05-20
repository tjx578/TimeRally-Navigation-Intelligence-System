from fastapi import APIRouter

from app.schemas.probability import (
    InferMissingWaypointRequest,
    InferMissingWaypointResponse,
    RouteEditOperation,
    RouteEditResponse,
)


router = APIRouter()


@router.post("/infer-missing-waypoint", response_model=InferMissingWaypointResponse)
def infer_missing_waypoint(request: InferMissingWaypointRequest) -> InferMissingWaypointResponse:
    return InferMissingWaypointResponse(
        missing_waypoint_text=request.context.missing_waypoint_text,
        recommended_candidate_id=None,
        candidates=[],
        status="skeleton_ready: wire packages.rally_core.probability",
    )


@router.post("/route-edit", response_model=RouteEditResponse)
def apply_route_edit(operation: RouteEditOperation) -> RouteEditResponse:
    return RouteEditResponse(
        operation_id="route-edit-skeleton",
        affected_leg_ids=[operation.leg_id] if operation.leg_id else [],
        requires_revalidation=True,
        status="skeleton_ready: wire route editor and constraints",
    )

