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

from geo_engine.distance import haversine_meters

from rally_core.routing.models import (
    LatLng,
    Provider,
    ProviderResult,
    RouteRequest,
    RouteSegment,
)


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


class RoutingAdapter:
    """Facade penyatuan provider.

    Default urutan provider: ROUTING_DEFAULT_PROVIDER lalu mock fallback.
    """

    def __init__(self, providers: Iterable[MockRoutingProvider] | None = None) -> None:
        provider_list = list(providers) if providers else [MockRoutingProvider()]
        self._providers = {p.name: p for p in provider_list}

    def route(self, request: RouteRequest) -> ProviderResult:
        provider_name = request.provider
        provider = self._providers.get(provider_name) or self._providers.get("mock")
        if provider is None:
            raise RuntimeError("Tidak ada provider routing yang terdaftar")
        return provider.route(request)
