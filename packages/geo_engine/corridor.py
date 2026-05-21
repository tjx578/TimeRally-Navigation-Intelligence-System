"""Corridor analysis untuk probability resolver.

Corridor = buffer di sekitar route polyline A->C. Kandidat B yang ada di
corridor lebih mungkin menjadi waypoint yang hilang.
"""

from __future__ import annotations

from math import cos, radians

from geo_engine.distance import haversine_meters


Point = tuple[float, float]  # (lat, lng)


def _project_to_meters(lat: float, lng: float, lat_ref: float) -> Point:
    """Konversi lat/lng ke koordinat lokal (meter) di sekitar lat_ref."""
    lat_factor = 111_320.0
    lng_factor = 111_320.0 * cos(radians(lat_ref))
    return lat * lat_factor, lng * lng_factor


def distance_point_to_segment_meters(
    point: Point, a: Point, b: Point
) -> float:
    """Distance titik ke segmen lat/lng (proyeksi ekuirektangular lokal)."""
    lat_ref = (point[0] + a[0] + b[0]) / 3.0
    px, py = _project_to_meters(point[0], point[1], lat_ref)
    ax, ay = _project_to_meters(a[0], a[1], lat_ref)
    bx, by = _project_to_meters(b[0], b[1], lat_ref)
    abx, aby = bx - ax, by - ay
    apx, apy = px - ax, py - ay
    ab_sq = abx * abx + aby * aby
    if ab_sq == 0:
        # a == b, fallback haversine
        return haversine_meters(point[0], point[1], a[0], a[1])
    t = max(0.0, min(1.0, (apx * abx + apy * aby) / ab_sq))
    cx, cy = ax + t * abx, ay + t * aby
    dx, dy = px - cx, py - cy
    return (dx * dx + dy * dy) ** 0.5


def distance_point_to_line_meters(point: Point, polyline: list[Point]) -> float:
    if len(polyline) < 2:
        if not polyline:
            return float("inf")
        return haversine_meters(point[0], point[1], polyline[0][0], polyline[0][1])
    return min(
        distance_point_to_segment_meters(point, polyline[i], polyline[i + 1])
        for i in range(len(polyline) - 1)
    )


def point_in_corridor(point: Point, polyline: list[Point], corridor_m: float = 300.0) -> bool:
    return distance_point_to_line_meters(point, polyline) <= corridor_m


def corridor_fit(point: Point, polyline: list[Point], corridor_m: float = 300.0) -> float:
    """Skor 0..1: 1 berarti di garis, 0 berarti di luar corridor."""
    d = distance_point_to_line_meters(point, polyline)
    if d <= 0:
        return 1.0
    if d >= corridor_m:
        return 0.0
    return round(1.0 - d / corridor_m, 4)
