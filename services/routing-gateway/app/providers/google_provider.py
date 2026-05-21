"""Google Routes provider adapter.

Hanya dipakai dalam Championship Online Mode / validator online. Output
TIDAK boleh dicampur dengan data offline OSM (prinsip mutlak no. 4).
"""

from __future__ import annotations

import os

import httpx

from .base import (
    RouteRequestModel,
    RouteResultModel,
    RouteSegmentModel,
    RoutingProvider,
)


class GoogleProvider(RoutingProvider):
    name = "google"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        self.enabled = (os.getenv("GOOGLE_ENABLED") or "").lower() in {"1", "true", "yes"}

    async def route(self, request: RouteRequestModel) -> RouteResultModel:
        if not self.enabled or not self.api_key:
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=["google_disabled atau API key kosong"],
            )
        if len(request.waypoints) < 2:
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.5,
                warnings=["minimum 2 waypoint diperlukan"],
            )
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        body = {
            "origin": {
                "location": {
                    "latLng": {
                        "latitude": request.waypoints[0].coord.lat,
                        "longitude": request.waypoints[0].coord.lng,
                    }
                }
            },
            "destination": {
                "location": {
                    "latLng": {
                        "latitude": request.waypoints[-1].coord.lat,
                        "longitude": request.waypoints[-1].coord.lng,
                    }
                }
            },
            "intermediates": [
                {
                    "location": {
                        "latLng": {
                            "latitude": w.coord.lat,
                            "longitude": w.coord.lng,
                        }
                    }
                }
                for w in request.waypoints[1:-1]
            ],
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
        }
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "routes.distanceMeters,routes.duration,routes.legs.distanceMeters,"
                "routes.legs.duration,routes.legs.polyline.encodedPolyline"
            ),
        }
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=[f"Google Routes error: {exc}"],
            )

        routes = data.get("routes") or []
        if not routes:
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=["Google no route"],
            )
        primary = routes[0]
        legs = primary.get("legs", [])
        segments: list[RouteSegmentModel] = []
        total_d = int(round(primary.get("distanceMeters", 0)))
        # Duration format "300s"
        dur_raw = primary.get("duration", "0s")
        total_t = int(float(str(dur_raw).rstrip("s")))
        for idx, leg in enumerate(legs):
            wp_a = request.waypoints[idx]
            wp_b = request.waypoints[min(idx + 1, len(request.waypoints) - 1)]
            distance_m = int(round(leg.get("distanceMeters", 0)))
            dur_raw = leg.get("duration", "0s")
            duration_s = int(float(str(dur_raw).rstrip("s")))
            segments.append(
                RouteSegmentModel(
                    from_waypoint=wp_a.id,
                    to_waypoint=wp_b.id,
                    distance_m=distance_m,
                    duration_s=duration_s,
                    provider=self.name,
                    polyline=[wp_a.coord, wp_b.coord],
                    status="ok",
                )
            )
        return RouteResultModel(
            provider=self.name,
            segments=segments,
            total_distance_m=total_d,
            total_duration_s=total_t,
            confidence=0.99,
            warnings=["google_online: validator mode, jangan cache untuk offline"],
        )
