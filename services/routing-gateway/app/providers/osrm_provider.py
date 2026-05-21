"""OSRM provider adapter."""

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


class OSRMProvider(RoutingProvider):
    name = "osrm"

    def __init__(self, base_url: str | None = None, profile: str = "driving") -> None:
        self.base_url = (base_url or os.getenv("OSRM_URL", "http://localhost:5000")).rstrip("/")
        self.profile = profile

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

        # OSRM koordinat: lon,lat;lon,lat;...
        coords = ";".join(f"{w.coord.lng},{w.coord.lat}" for w in request.waypoints)
        url = f"{self.base_url}/route/v1/{self.profile}/{coords}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "true",
            "alternatives": "false",
        }
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
                warnings=[f"OSRM unreachable: {exc}"],
            )

        routes = data.get("routes") or []
        if not routes:
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=["OSRM no route"],
            )

        primary = routes[0]
        legs = primary.get("legs", [])
        segments: list[RouteSegmentModel] = []
        total_d = 0
        total_t = 0
        for idx, leg in enumerate(legs):
            wp_a = request.waypoints[idx]
            wp_b = request.waypoints[idx + 1]
            polyline_pts: list[LatLngModel] = []
            for step in leg.get("steps", []):
                geom = step.get("geometry", {}).get("coordinates", [])
                for pt in geom:
                    polyline_pts.append(LatLngModel(lng=pt[0], lat=pt[1]))
            distance_m = int(round(leg.get("distance", 0)))
            duration_s = int(round(leg.get("duration", 0)))
            total_d += distance_m
            total_t += duration_s
            segments.append(
                RouteSegmentModel(
                    from_waypoint=wp_a.id,
                    to_waypoint=wp_b.id,
                    distance_m=distance_m,
                    duration_s=duration_s,
                    provider=self.name,
                    polyline=polyline_pts,
                    status="ok",
                )
            )
        return RouteResultModel(
            provider=self.name,
            segments=segments,
            total_distance_m=total_d,
            total_duration_s=total_t,
            confidence=0.95,
        )
