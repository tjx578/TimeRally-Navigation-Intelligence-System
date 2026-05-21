"""Valhalla provider adapter."""

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


_DECODE_PRECISION = 1e6  # Valhalla 'shape' default precision 6


def _decode_shape(shape: str) -> list[LatLngModel]:
    """Polyline6 decoder (algoritma Google)."""
    coords: list[LatLngModel] = []
    index = 0
    lat = 0
    lng = 0
    length = len(shape)
    while index < length:
        result = 1
        shift = 0
        while True:
            b = ord(shape[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lat += (~(result >> 1)) if (result & 1) else (result >> 1)

        result = 1
        shift = 0
        while True:
            b = ord(shape[index]) - 63 - 1
            index += 1
            result += b << shift
            shift += 5
            if b < 0x1F:
                break
        lng += (~(result >> 1)) if (result & 1) else (result >> 1)
        coords.append(LatLngModel(lat=lat / _DECODE_PRECISION, lng=lng / _DECODE_PRECISION))
    return coords


class ValhallaProvider(RoutingProvider):
    name = "valhalla"

    def __init__(self, base_url: str | None = None, costing: str = "auto") -> None:
        self.base_url = (base_url or os.getenv("VALHALLA_URL", "http://localhost:8002")).rstrip("/")
        self.costing = costing

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
        payload = {
            "locations": [
                {"lat": w.coord.lat, "lon": w.coord.lng, "type": "break"}
                for w in request.waypoints
            ],
            "costing": self.costing,
            "directions_options": {"units": "kilometers"},
        }
        url = f"{self.base_url}/route"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:  # noqa: BLE001
            return RouteResultModel(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=[f"Valhalla unreachable: {exc}"],
            )

        trip = data.get("trip", {})
        legs = trip.get("legs", [])
        segments: list[RouteSegmentModel] = []
        total_d_m, total_t_s = 0, 0
        for idx, leg in enumerate(legs):
            wp_a = request.waypoints[idx]
            wp_b = request.waypoints[idx + 1]
            shape = leg.get("shape", "")
            polyline_pts = _decode_shape(shape) if shape else [wp_a.coord, wp_b.coord]
            distance_km = float(leg.get("summary", {}).get("length", 0.0))
            duration_s = int(round(leg.get("summary", {}).get("time", 0)))
            distance_m = int(round(distance_km * 1000.0))
            total_d_m += distance_m
            total_t_s += duration_s
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
            total_distance_m=total_d_m,
            total_duration_s=total_t_s,
            confidence=0.97,
        )
