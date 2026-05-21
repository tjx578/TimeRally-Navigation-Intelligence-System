"""Routing gateway FastAPI service.

Eksposes:
- POST /v1/routing/route
- POST /v1/routing/matrix
- POST /v1/routing/nearest
- POST /v1/routing/match
- GET  /health
"""

from __future__ import annotations

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
    provider: str = "valhalla"
    route: RouteRequestModel


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "providers": list(_PROVIDERS.keys())}


@app.post("/v1/routing/route", response_model=RouteResultModel)
async def route(req: RouteEnvelopeRequest) -> RouteResultModel:
    provider = _PROVIDERS.get(req.provider)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"provider {req.provider} tidak terdaftar")
    if not req.route.allow_reorder and len(req.route.waypoints) < 2:
        raise HTTPException(status_code=400, detail="minimal 2 waypoint")
    return await provider.route(req.route)


class NearestRequest(BaseModel):
    provider: str = "valhalla"
    point: LatLngModel


@app.post("/v1/routing/nearest", response_model=LatLngModel)
async def nearest(req: NearestRequest) -> LatLngModel:
    provider = _PROVIDERS.get(req.provider)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"provider {req.provider} tidak terdaftar")
    return await provider.nearest(req.point)


class MatrixRequest(BaseModel):
    provider: str = "valhalla"
    origins: list[LatLngModel]
    destinations: list[LatLngModel]


@app.post("/v1/routing/matrix")
async def matrix(req: MatrixRequest) -> dict:
    provider = _PROVIDERS.get(req.provider)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"provider {req.provider} tidak terdaftar")
    rows = await provider.matrix(req.origins, req.destinations)
    return {"provider": req.provider, "matrix": rows}


class MatchRequest(BaseModel):
    provider: str = "valhalla"
    trace: list[LatLngModel]


@app.post("/v1/routing/match")
async def match(req: MatchRequest) -> dict:
    provider = _PROVIDERS.get(req.provider)
    if provider is None:
        raise HTTPException(status_code=400, detail=f"provider {req.provider} tidak terdaftar")
    matched = await provider.match(req.trace)
    return {"provider": req.provider, "trace": [p.dict() for p in matched]}
