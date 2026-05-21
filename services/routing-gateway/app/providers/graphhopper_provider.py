"""GraphHopper provider adapter."""

from __future__ import annotations

import os

import httpx

from .base import (
    LatLngModel,
    RouteRequestModel,
    RouteResultModel,
    RouteSegmentModel,
    RoutingProvider,
)


def _decode_polyline5(polyline: str) -> list[LatLngModel]:
    coords: list[LatLngModel] = []
    index = 0
    lat = 0
    lng = 0
    length = len(polyline)
    while index < length:
        result = 1
        shift = 0
        while True:
            b = ord(polyline[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lat += (~(result >> 1)) if (result & 1) else (result >> 1)

        result = 1
        shift = 0
        while True:
            b = ord(polyline[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lng += (~(result >> 1)) if (result & 1) else (result >> 1)
        coords.append(LatLngModel(lat=lat / 1e5, lng=lng / 1e5))
    return coords


class GraphHopperProvider(RoutingProvider):
    name = "graphhopper"

    def __init__(
        self,
        base_url: str | None = None,
        vehicle: str = "car",
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("GRAPHHOPPER_URL", "http://localhost:8989")).rstrip("/")
        self.vehicle = vehicle
        self.api_key = api_key or os.getenv("GRAPHHOPPER_API_KEY")

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
        params: list[tuple[str, str]] = [
            ("vehicle", self.vehicle),
            ("points_encoded", "true"),
            ("calc_points", "true"),
            ("instructions", "false"),
        ]
        for w in request.waypoints:
            params.append(("point", f"{w.coord.lat},{w.coord.lng}"))
        if self.api_key:
            params.append(("key", self.api_key))
        url = f"{self.base_url}/route"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=[f"GraphHopper unreachable: {exc}"],
            )

        paths = data.get("paths") or []
        if not paths:
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=["GraphHopper no path"],
            )
        primary = paths[0]
        points = _decode_polyline5(primary.get("points", ""))
        # GraphHopper tidak per-leg; bagi rata berdasarkan urutan waypoint
        segments: list[RouteSegmentModel] = []
        total_d = int(round(primary.get("distance", 0)))
        total_t = int(round(primary.get("time", 0) / 1000.0))
        if len(request.waypoints) - 1 > 0:
            per_d = total_d // (len(request.waypoints) - 1)
            per_t = total_t // (len(request.waypoints) - 1)
        else:
            per_d, per_t = 0, 0
        for a, b in zip(request.waypoints, request.waypoints[1:]):
            segments.append(
                RouteSegmentModel(
                    from_waypoint=a.id,
                    to_waypoint=b.id,
                    distance_m=per_d,
                    duration_s=per_t,
                    provider=self.name,
                    polyline=points,  # shared polyline
                    status="ok",
                )
            )
        return RouteResultModel(
            provider=self.name,
            segments=segments,
            total_distance_m=total_d,
            total_duration_s=total_t,
            confidence=0.9,
        )
