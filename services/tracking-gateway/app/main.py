"""Tracking gateway service.

Membungkus Traccar / live GPS in-memory store dengan API rally:
- POST /v1/tracking/ingest: terima posisi GPS dari device lapangan.
- GET  /v1/tracking/state/{device_id}: state terkini.
- POST /v1/tracking/replay: hitung deviasi terhadap route GPX/GeoJSON.
- GET  /v1/tracking/checkpoints/{event_id}: status checkpoint.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from geo_engine.corridor import distance_point_to_line_meters
from geo_engine.distance import haversine_meters


app = FastAPI(title="Time Rally Tracking Gateway", version="0.1.0")


@dataclass
class TrackedPoint:
    timestamp: float
    lat: float
    lng: float
    speed_kmh: float | None = None
    bearing: float | None = None
    accuracy_m: float | None = None


@dataclass
class DeviceState:
    device_id: str
    last_seen: float = 0.0
    points: Deque[TrackedPoint] = field(default_factory=lambda: deque(maxlen=2048))


_DEVICES: dict[str, DeviceState] = defaultdict(lambda: DeviceState(device_id=""))


class IngestPoint(BaseModel):
    device_id: str
    timestamp: float | None = None
    lat: float
    lng: float
    speed_kmh: float | None = None
    bearing: float | None = None
    accuracy_m: float | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "devices": list(_DEVICES.keys())}


@app.post("/v1/tracking/ingest")
def ingest(point: IngestPoint) -> dict:
    state = _DEVICES.setdefault(point.device_id, DeviceState(device_id=point.device_id))
    state.device_id = point.device_id
    ts = point.timestamp or time.time()
    state.last_seen = ts
    state.points.append(
        TrackedPoint(
            timestamp=ts,
            lat=point.lat,
            lng=point.lng,
            speed_kmh=point.speed_kmh,
            bearing=point.bearing,
            accuracy_m=point.accuracy_m,
        )
    )
    return {"status": "ok", "buffered": len(state.points)}


@app.get("/v1/tracking/state/{device_id}")
def state(device_id: str) -> dict:
    if device_id not in _DEVICES:
        raise HTTPException(status_code=404, detail="device not found")
    s = _DEVICES[device_id]
    last = s.points[-1] if s.points else None
    return {
        "device_id": s.device_id,
        "last_seen": s.last_seen,
        "buffered_points": len(s.points),
        "last": (
            None
            if last is None
            else {
                "timestamp": last.timestamp,
                "lat": last.lat,
                "lng": last.lng,
                "speed_kmh": last.speed_kmh,
                "bearing": last.bearing,
            }
        ),
    }


class ReplayRequest(BaseModel):
    device_id: str
    route_polyline: list[list[float]]  # [[lat,lng], ...]
    corridor_m: float = 250.0


@app.post("/v1/tracking/replay")
def replay(req: ReplayRequest) -> dict:
    if req.device_id not in _DEVICES:
        raise HTTPException(status_code=404, detail="device not found")
    s = _DEVICES[req.device_id]
    polyline = [(p[0], p[1]) for p in req.route_polyline]
    deviations: list[dict] = []
    total = 0
    off = 0
    for pt in s.points:
        d = distance_point_to_line_meters((pt.lat, pt.lng), polyline)
        total += 1
        if d > req.corridor_m:
            off += 1
            deviations.append(
                {
                    "timestamp": pt.timestamp,
                    "lat": pt.lat,
                    "lng": pt.lng,
                    "deviation_m": round(d, 1),
                }
            )
    return {
        "device_id": req.device_id,
        "total_points": total,
        "off_corridor_points": off,
        "off_corridor_ratio": round(off / total, 4) if total else 0,
        "deviations": deviations[:50],
    }


class CheckpointHit(BaseModel):
    name: str
    lat: float
    lng: float
    radius_m: float = 50.0


class CheckpointsRequest(BaseModel):
    device_id: str
    checkpoints: list[CheckpointHit]


@app.post("/v1/tracking/checkpoints/check")
def checkpoints(req: CheckpointsRequest) -> dict:
    if req.device_id not in _DEVICES:
        raise HTTPException(status_code=404, detail="device not found")
    s = _DEVICES[req.device_id]
    hits: list[dict] = []
    for cp in req.checkpoints:
        first_hit_time: float | None = None
        for pt in s.points:
            if haversine_meters(pt.lat, pt.lng, cp.lat, cp.lng) <= cp.radius_m:
                first_hit_time = pt.timestamp
                break
        hits.append(
            {
                "name": cp.name,
                "lat": cp.lat,
                "lng": cp.lng,
                "radius_m": cp.radius_m,
                "hit": first_hit_time is not None,
                "first_hit_at": first_hit_time,
            }
        )
    return {"device_id": req.device_id, "checkpoints": hits}
