"""Routing adapter di sisi API.

API tidak memanggil OSRM/Valhalla/GraphHopper langsung. Di lingkungan production,
adapter akan memforward request ke services/routing-gateway. Untuk development
dan testing, MockRoutingProvider menyediakan jawaban deterministic berbasis
straight-line + small detour factor sehingga seluruh pipeline tetap bisa
dijalankan offline tanpa engine routing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import httpx

from app.settings import get_settings
from geo_engine.distance import haversine_meters

from rally_core.routing.models import (
    LatLng,
    Provider,
    ProviderResult,
    RouteRequest,
    RouteSegment,
)


def _rounded_int(value: object) -> int:
    return int(round(float(value or 0)))


@dataclass
class MockRoutingProvider:
    """Hitung segmen rute lurus dengan asumsi kecepatan rata-rata.

    Berguna untuk smoke test pipeline dari parser sampai exporter tanpa
    dependency engine eksternal.
    """

    name: Provider = "mock"
    average_speed_kmh: float = 35.0
    detour_factor: float = 1.25  # rute jalan biasanya 1.2x straight-line

    def route(self, request: RouteRequest) -> ProviderResult:
        segments: list[RouteSegment] = []
        if len(request.waypoints) < 2:
            return ProviderResult(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.5,
                warnings=["minimum 2 waypoint diperlukan"],
            )

        total_d = 0
        total_t = 0
        for a, b in zip(request.waypoints, request.waypoints[1:]):
            d_straight = haversine_meters(a.coord.lat, a.coord.lng, b.coord.lat, b.coord.lng)
            d_route = int(round(d_straight * self.detour_factor))
            duration = int(round(d_route / 1000.0 / self.average_speed_kmh * 3600.0))
            segments.append(
                RouteSegment(
                    from_waypoint=a.id,
                    to_waypoint=b.id,
                    distance_m=d_route,
                    duration_s=duration,
                    polyline=[a.coord, b.coord],
                    provider=self.name,
                    status="mock",
                    notes=[
                        "mock provider - production harus pakai Valhalla/OSRM via routing-gateway",
                    ],
                )
            )
            total_d += d_route
            total_t += duration
        return ProviderResult(
            provider=self.name,
            segments=segments,
            total_distance_m=total_d,
            total_duration_s=total_t,
            confidence=0.6,
            warnings=["mock_routing_active"],
        )


@dataclass
class GatewayRoutingProvider:
    """Forward provider nyata ke service routing-gateway."""

    name: Provider
    base_url: str | None = None
    timeout_s: float = 20.0

    def _base_url(self) -> str:
        return (self.base_url or get_settings().routing_gateway_url).rstrip("/")

    def route(self, request: RouteRequest) -> ProviderResult:
        payload = {
            "provider": self.name,
            "route": {
                "profile": request.profile,
                "allow_reorder": request.allow_reorder,
                "avoid": request.avoid,
                "waypoints": [
                    {
                        "id": wp.id,
                        "name": wp.name,
                        "coord": {"lat": wp.coord.lat, "lng": wp.coord.lng},
                    }
                    for wp in request.waypoints
                ],
            },
        }
        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                response = client.post(f"{self._base_url()}/v1/routing/route", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:  # noqa: BLE001
            return ProviderResult(
                provider=self.name,
                segments=[],
                total_distance_m=0,
                total_duration_s=0,
                confidence=0.0,
                warnings=[f"routing_gateway_unreachable:{exc}"],
            )

        segments: list[RouteSegment] = []
        for segment in data.get("segments", []):
            polyline = [
                LatLng(lat=float(pt["lat"]), lng=float(pt["lng"]))
                for pt in segment.get("polyline", [])
                if "lat" in pt and "lng" in pt
            ]
            segments.append(
                RouteSegment(
                    from_waypoint=segment["from_waypoint"],
                    to_waypoint=segment["to_waypoint"],
                    distance_m=_rounded_int(segment.get("distance_m", 0)),
                    duration_s=_rounded_int(segment.get("duration_s", 0)),
                    polyline=polyline,
                    provider=self.name,
                    status=segment.get("status", "ok"),
                )
            )
        return ProviderResult(
            provider=self.name,
            segments=segments,
            total_distance_m=_rounded_int(data.get("total_distance_m", 0)),
            total_duration_s=_rounded_int(data.get("total_duration_s", 0)),
            confidence=float(data.get("confidence", 1.0)),
            warnings=list(data.get("warnings", [])),
        )


class RoutingAdapter:
    """Facade penyatuan provider.

    Provider eksplisit tetap dipakai apa adanya. Provider `auto` memakai urutan
    environment sehingga race day bisa hot-swap OSRM/Valhalla/GraphHopper.
    """

    def __init__(
        self,
        providers: Iterable[MockRoutingProvider | GatewayRoutingProvider] | None = None,
    ) -> None:
        provider_list = list(providers) if providers else [MockRoutingProvider()]
        self._providers = {p.name: p for p in provider_list}

    def _provider_priority(self) -> list[str]:
        settings = get_settings()
        raw_priority = [
            settings.routing_provider_primary,
            settings.routing_provider_fallback,
            settings.routing_provider_standby,
            settings.routing_default_provider,
            "osrm",
            "valhalla",
            "graphhopper",
            "google",
        ]
        if settings.routing_allow_mock_fallback:
            raw_priority.append("mock")

        priority: list[str] = []
        for item in raw_priority:
            name = (item or "").strip().lower()
            if name in {"", "auto", "primary"}:
                continue
            if name in self._providers and name not in priority:
                priority.append(name)
        return priority

    @staticmethod
    def _is_success(result: ProviderResult) -> bool:
        return bool(result.segments)

    def _route_auto(self, request: RouteRequest) -> ProviderResult:
        warnings: list[str] = []
        last_result: ProviderResult | None = None
        for provider_name in self._provider_priority():
            provider = self._providers[provider_name]
            result = provider.route(request)
            last_result = result
            if self._is_success(result):
                if warnings:
                    result.warnings = [*warnings, *result.warnings]
                return result
            warnings.extend(f"{provider_name}: {warning}" for warning in result.warnings)

        if last_result is not None:
            last_result.warnings = warnings or last_result.warnings
            return last_result
        provider = self._providers.get("mock")
        if provider is None:
            raise RuntimeError("Tidak ada provider routing yang terdaftar")
        return provider.route(request)

    def route(self, request: RouteRequest) -> ProviderResult:
        provider_name = request.provider
        if provider_name in {"", "auto", "primary"}:
            return self._route_auto(request)
        provider = self._providers.get(provider_name) or self._providers.get("mock")
        if provider is None:
            raise RuntimeError("Tidak ada provider routing yang terdaftar")
        return provider.route(request)
