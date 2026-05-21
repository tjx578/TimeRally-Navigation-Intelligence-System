from pydantic import BaseModel

from app.schemas.places import Coordinate


class RoutingWaypoint(BaseModel):
    id: str
    name: str
    coordinate: Coordinate


class RouteRequest(BaseModel):
    waypoints: list[RoutingWaypoint]
    provider: str = "auto"
    profile: str = "rally_car"
    allow_reorder: bool = False


class RouteLeg(BaseModel):
    from_waypoint: str
    to_waypoint: str
    distance_m: int
    duration_s: int
    provider: str
    status: str


class RouteResponse(BaseModel):
    provider: str
    legs: list[RouteLeg]
    total_distance_m: int
    total_duration_s: int
    status: str
