"""Export GeoJSON FeatureCollection."""

from __future__ import annotations

import json
from typing import Any

from rally_core.routing.models import RouteSegment, RouteWaypoint


def event_geojson(
    waypoints: list[RouteWaypoint],
    segments: list[RouteSegment],
) -> dict[str, Any]:
    features: list[dict[str, Any]] = []

    for wp in waypoints:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": wp.coord.as_geojson()},
                "properties": {
                    "id": wp.id,
                    "name": wp.name,
                    "role": wp.role,
                    "kind": "waypoint",
                },
            }
        )

    for seg in segments:
        if not seg.polyline:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [p.as_geojson() for p in seg.polyline],
                },
                "properties": {
                    "from": seg.from_waypoint,
                    "to": seg.to_waypoint,
                    "distance_m": seg.distance_m,
                    "duration_s": seg.duration_s,
                    "provider": seg.provider,
                    "status": seg.status,
                    "kind": "segment",
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}


def export_geojson(
    waypoints: list[RouteWaypoint],
    segments: list[RouteSegment],
    indent: int | None = 2,
) -> str:
    return json.dumps(event_geojson(waypoints, segments), ensure_ascii=False, indent=indent)
