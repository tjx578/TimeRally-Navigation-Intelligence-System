"""Use case: route lintas waypoint via RoutingAdapter."""

from __future__ import annotations

from app.adapters.routing import GatewayRoutingProvider, MockRoutingProvider, RoutingAdapter
from rally_core.routing.models import (
    ProviderResult,
    Provider,
    RouteRequest,
    RouteWaypoint,
)


_adapter = RoutingAdapter(
    [
        GatewayRoutingProvider(name="valhalla"),
        GatewayRoutingProvider(name="osrm"),
        GatewayRoutingProvider(name="graphhopper"),
        GatewayRoutingProvider(name="google"),
        MockRoutingProvider(name="mock"),
    ]
)


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
