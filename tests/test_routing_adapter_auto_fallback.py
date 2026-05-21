from __future__ import annotations

from dataclasses import dataclass

from app.adapters.routing import MockRoutingProvider, RoutingAdapter
from app.settings import get_settings
from rally_core.routing.models import ProviderResult, RouteRequest, RouteWaypoint, LatLng


@dataclass
class EmptyProvider:
    name: str

    def route(self, request: RouteRequest) -> ProviderResult:
        return ProviderResult(
            provider=self.name,  # type: ignore[arg-type]
            segments=[],
            total_distance_m=0,
            total_duration_s=0,
            confidence=0.0,
            warnings=[f"{self.name}_unavailable"],
        )


def test_routing_adapter_auto_fallback_uses_next_ready_provider(monkeypatch):
    monkeypatch.setenv("ROUTING_PROVIDER_PRIMARY", "osrm")
    monkeypatch.setenv("ROUTING_ALLOW_MOCK_FALLBACK", "true")
    get_settings.cache_clear()
    adapter = RoutingAdapter(
        [
            EmptyProvider("osrm"),  # type: ignore[list-item]
            MockRoutingProvider(name="mock"),
        ]
    )
    request = RouteRequest(
        provider="auto",
        waypoints=[
            RouteWaypoint(id="a", name="Start", coord=LatLng(lat=-8.67, lng=115.22)),
            RouteWaypoint(id="b", name="Finish", coord=LatLng(lat=-8.68, lng=115.23)),
        ],
    )

    result = adapter.route(request)

    assert result.provider == "mock"
    assert result.total_distance_m > 0
    assert "osrm: osrm_unavailable" in result.warnings
    get_settings.cache_clear()
