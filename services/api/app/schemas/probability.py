from pydantic import BaseModel

from app.schemas.places import Coordinate


class MissingWaypointContext(BaseModel):
    missing_waypoint_text: str
    previous_waypoint_id: str
    next_waypoint_id: str
    target_distance_km: float | None = None
    target_time_seconds: int | None = None
    navigation_action: str | None = None
    landmark_type_hint: str | None = None


class ProbabilityRouteCandidate(BaseModel):
    id: str
    label: str
    coordinate: Coordinate | None = None
    confidence: float
    distance_deviation_percent: float
    time_deviation_seconds: int
    route_corridor_fit: float
    landmark_fit: float
    turn_geometry_fit: float
    provider: str
    reasons: list[str]
    status: str


class InferMissingWaypointRequest(BaseModel):
    event_id: str | None = None
    context: MissingWaypointContext
    max_candidates: int = 5


class InferMissingWaypointResponse(BaseModel):
    missing_waypoint_text: str
    recommended_candidate_id: str | None = None
    candidates: list[ProbabilityRouteCandidate]
    status: str


class RouteEditOperation(BaseModel):
    event_id: str
    sub_trayek_id: str | None = None
    leg_id: str | None = None
    operation: str
    snap_to_road: bool = True
    geometry: list[Coordinate] = []
    reason: str | None = None


class RouteEditResponse(BaseModel):
    operation_id: str
    affected_leg_ids: list[str]
    requires_revalidation: bool
    status: str

