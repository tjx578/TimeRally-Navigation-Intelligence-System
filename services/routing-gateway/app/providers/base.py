"""Base provider interface dan model request/response."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field


ProviderName = Literal["valhalla", "osrm", "graphhopper", "google", "mock"]


class LatLngModel(BaseModel):
    lat: float
    lng: float


class WaypointModel(BaseModel):
    id: str
    name: str
    coord: LatLngModel


class RouteRequestModel(BaseModel):
    waypoints: list[WaypointModel]
    profile: str = "rally_car"
    allow_reorder: bool = False
    avoid: list[str] = Field(default_factory=list)


class RouteSegmentModel(BaseModel):
    from_waypoint: str
    to_waypoint: str
    distance_m: int
    duration_s: int
    provider: ProviderName
    polyline: list[LatLngModel] = Field(default_factory=list)
    status: str = "ok"


class RouteResultModel(BaseModel):
    provider: ProviderName
    segments: list[RouteSegmentModel]
    total_distance_m: int
    total_duration_s: int
    confidence: float = 1.0
    warnings: list[str] = Field(default_factory=list)


class RoutingProvider(ABC):
    name: ProviderName = "mock"

    @abstractmethod
    async def route(self, request: RouteRequestModel) -> RouteResultModel:
        ...

    async def nearest(self, point: LatLngModel) -> LatLngModel:
        return point

    async def matrix(
        self,
        origins: list[LatLngModel],
        destinations: list[LatLngModel],
    ) -> list[list[int]]:
        return [[0 for _ in destinations] for _ in origins]

    async def match(self, trace: list[LatLngModel]) -> list[LatLngModel]:
        return trace
