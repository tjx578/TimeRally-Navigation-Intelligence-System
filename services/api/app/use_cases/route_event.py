"""Use case: route lintas waypoint via RoutingAdapter."""

from __future__ import annotations

from app.adapters.routing import MockRoutingProvider, RoutingAdapter
from rally_core.routing.models import (
    LatLng,
    ProviderResult,
    Provider,
    RouteRequest,
    RouteWaypoint,
)


_adapter = RoutingAdapter([MockRoutingProvider(name="mock"), MockRoutingProvider(name="valhalla"), MockRoutingProvider(name="osrm")])


def route_event(
    waypoints: list[RouteWaypoint],
    *,
    provider: Provider = "valhalla",
    profile: str = "rally_car",
    allow_reorder: bool = False,
) -> ProviderResult:
    request = RouteRequest(
        waypoints=waypoints,
        provider=provider,
        profile=profile,
        allow_reorder=allow_reorder,
    )
    return _adapter.route(request)
