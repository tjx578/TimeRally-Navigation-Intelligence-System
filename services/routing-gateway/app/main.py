"""Routing gateway FastAPI service.

Eksposes:
- POST /v1/routing/route
- POST /v1/routing/matrix
- POST /v1/routing/nearest
- POST /v1/routing/match
- GET  /health, /healthz, /readyz
"""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .providers import (
    GoogleProvider,
    GraphHopperProvider,
    MockProvider,
    OSRMProvider,
    RouteRequestModel,
    RouteResultModel,
    RoutingProvider,
    ValhallaProvider,
)
from .providers.base import LatLngModel


_PROVIDERS: dict[str, RoutingProvider] = {
    "valhalla": ValhallaProvider(),
    "osrm": OSRMProvider(),
    "graphhopper": GraphHopperProvider(),
    "google": GoogleProvider(),
    "mock": MockProvider(),
}


app = FastAPI(title="Time Rally Routing Gateway", version="0.1.0")


class RouteEnvelopeRequest(BaseModel):
    provider: str = "auto"
    route: RouteRequestModel


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _provider_priority() -> list[str]:
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    allow_mock = _to_bool(os.getenv("ROUTING_ALLOW_MOCK_FALLBACK"), default=app_env != "production")
    raw_priority = [
        os.getenv("ROUTING_PROVIDER_PRIMARY"),
        os.getenv("ROUTING_PROVIDER_FALLBACK"),
        os.getenv("ROUTING_PROVIDER_STANDBY"),
        os.getenv("ROUTING_DEFAULT_PROVIDER"),
        "osrm",
        "valhalla",
        "graphhopper",
    ]
    if allow_mock:
        raw_priority.append("mock")

    priority: list[str] = []
    for item in raw_priority:
        provider = (item or "").strip().lower()
        if provider in _PROVIDERS and provider not in priority:
            priority.append(provider)
    return priority


def _configured_urls() -> dict[str, str | None]:
    return {
        "osrm": os.getenv("OSRM_URL"),
        "valhalla": os.getenv("VALHALLA_URL"),
        "graphhopper": os.getenv("GRAPHHOPPER_URL"),
        "google": "configured" if os.getenv("GOOGLE_MAPS_API_KEY") else None,
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "providers": list(_PROVIDERS.keys()),
        "priority": _provider_priority(),
    }


@app.get("/healthz")
def healthz() -> dict:
    return health()


@app.get("/readyz")
def ready() -> dict:
    priority = _provider_priority()
    status = "ready" if priority else "degraded"
    return {
        "status": status,
        "providers": list(_PROVIDERS.keys()),
        "priority": priority,
        "configured_urls": _configured_urls(),
    }


def _resolve_provider(provider_name: str) -> RoutingProvider:
    if provider_name in {"", "auto", "primary"}:
        priority = _provider_priority()
        if not priority:
            raise HTTPException(status_code=503, detail="tidak ada provider routing siap")
        provider_name = priority[0]
    provider = _PROVIDERS.get(provider_name)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"provider {provider_name} tidak terdaftar")
    return provider


async def _route_auto(request: RouteRequestModel) -> RouteResultModel:
    warnings: list[str] = []
    last_result: RouteResultModel | None = None
    priority = _provider_priority()
    if not priority:
        raise HTTPException(status_code=503, detail="tidak ada provider routing siap")

    for provider_name in priority:
        provider = _PROVIDERS[provider_name]
        try:
            result = await provider.route(request)
        except Exception as exc:  # noqa: BLE001
            warnings.append(f"{provider_name} exception: {exc}")
            continue
        last_result = result
        if result.segments:
            if warnings:
                result.warnings = [*warnings, *result.warnings]
            return result
        warnings.extend(f"{provider_name}: {warning}" for warning in result.warnings)

    if last_result is None:
        raise HTTPException(status_code=503, detail="semua provider routing gagal")
    last_result.warnings = warnings or last_result.warnings
    return last_result


@app.post("/v1/routing/route", response_model=RouteResultModel)
async def route(req: RouteEnvelopeRequest) -> RouteResultModel:
    if not req.route.allow_reorder and len(req.route.waypoints) < 2:
        raise HTTPException(status_code=400, detail="minimal 2 waypoint")
    if req.provider in {"", "auto", "primary"}:
        return await _route_auto(req.route)
    provider = _resolve_provider(req.provider)
    return await provider.route(req.route)


class NearestRequest(BaseModel):
    provider: str = "valhalla"
    point: LatLngModel


@app.post("/v1/routing/nearest", response_model=LatLngModel)
async def nearest(req: NearestRequest) -> LatLngModel:
    provider = _resolve_provider(req.provider)
    return await provider.nearest(req.point)


class MatrixRequest(BaseModel):
    provider: str = "valhalla"
    origins: list[LatLngModel]
    destinations: list[LatLngModel]


@app.post("/v1/routing/matrix")
async def matrix(req: MatrixRequest) -> dict:
    provider = _resolve_provider(req.provider)
    rows = await provider.matrix(req.origins, req.destinations)
    return {"provider": provider.name, "matrix": rows}


class MatchRequest(BaseModel):
    provider: str = "valhalla"
    trace: list[LatLngModel]


@app.post("/v1/routing/match")
async def match(req: MatchRequest) -> dict:
    provider = _resolve_provider(req.provider)
    matched = await provider.match(req.trace)
    return {"provider": provider.name, "trace": [p.dict() for p in matched]}
