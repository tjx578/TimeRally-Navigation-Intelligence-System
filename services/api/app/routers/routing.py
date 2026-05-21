"""Router /v1/routing - provider-neutral routing."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.routing import RouteLeg, RouteRequest, RouteResponse
from app.use_cases import route_event
from rally_core.routing.models import LatLng, Provider, RouteWaypoint


router = APIRouter()


def _rounded_int(value: object) -> int:
    return int(round(float(value or 0)))


@router.post("/route", response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    provider_name: Provider = request.provider  # type: ignore[assignment]
    waypoints = [
        RouteWaypoint(
            id=wp.id,
            name=wp.name,
            coord=LatLng(lat=wp.coordinate.lat, lng=wp.coordinate.lng),
        )
        for wp in request.waypoints
    ]
    result = route_event(
        waypoints,
        provider=provider_name,
        profile=request.profile,
        allow_reorder=request.allow_reorder,
    )
    legs = [
        RouteLeg(
            from_waypoint=seg.from_waypoint,
            to_waypoint=seg.to_waypoint,
            distance_m=_rounded_int(seg.distance_m),
            duration_s=_rounded_int(seg.duration_s),
            provider=seg.provider,
            status=seg.status,
        )
        for seg in result.segments
    ]
    return RouteResponse(
        provider=result.provider,
        legs=legs,
        total_distance_m=_rounded_int(result.total_distance_m),
        total_duration_s=_rounded_int(result.total_duration_s),
        status="ok" if result.segments else "empty",
    )
