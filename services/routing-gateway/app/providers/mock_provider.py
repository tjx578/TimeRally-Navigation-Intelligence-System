"""Mock provider: jawaban deterministic offline (haversine + detour factor)."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

from .base import (
    LatLngModel,
    RouteRequestModel,
    RouteResultModel,
    RouteSegmentModel,
    RoutingProvider,
)


EARTH_R = 6_371_000


def _haversine_m(a: LatLngModel, b: LatLngModel) -> int:
    phi1, phi2 = radians(a.lat), radians(b.lat)
    dphi = radians(b.lat - a.lat)
    dlmb = radians(b.lng - a.lng)
    h = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlmb / 2) ** 2
    return int(round(2 * EARTH_R * asin(min(1.0, sqrt(h)))))


class MockProvider(RoutingProvider):
    name = "mock"

    def __init__(self, average_speed_kmh: float = 35.0, detour_factor: float = 1.25) -> None:
        self.average_speed_kmh = average_speed_kmh
        self.detour_factor = detour_factor

    async def route(self, request: RouteRequestModel) -> RouteResultModel:
        if len(request.waypoints) < 2:
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.5,
                warnings=["minimum 2 waypoint diperlukan"],
            )
        segments: list[RouteSegmentModel] = []
        total_d, total_t = 0, 0
        for a, b in zip(request.waypoints, request.waypoints[1:]):
            d_straight = _haversine_m(a.coord, b.coord)
            d_route = int(round(d_straight * self.detour_factor))
            dur = int(round(d_route / 1000.0 / self.average_speed_kmh * 3600.0))
            segments.append(
                RouteSegmentModel(
                    from_waypoint=a.id,
                    to_waypoint=b.id,
                    distance_m=d_route,
                    duration_s=dur,
                    provider=self.name,
                    polyline=[a.coord, b.coord],
                    status="mock",
                )
            )
            total_d += d_route
            total_t += dur
        return RouteResultModel(
            provider=self.name,
            segments=segments,
            total_distance_m=total_d,
            total_duration_s=total_t,
            confidence=0.6,
            warnings=["mock_routing_active"],
        )
