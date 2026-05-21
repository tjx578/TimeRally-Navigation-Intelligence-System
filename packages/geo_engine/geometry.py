"""Polyline simplification & snap utilities."""

from __future__ import annotations

from geo_engine.corridor import distance_point_to_segment_meters
from geo_engine.distance import haversine_meters


Point = tuple[float, float]


def simplify_polyline(points: list[Point], tolerance_m: float = 5.0) -> list[Point]:
    """Douglas-Peucker simplification dengan tolerance dalam meter."""
    if len(points) <= 2:
        return points[:]

    def _dp(start: int, end: int) -> list[int]:
        # Cari titik dengan distance terbesar ke segmen [start..end]
        if end - start <= 1:
            return []
        max_dist = -1.0
        max_idx = -1
        for i in range(start + 1, end):
            d = distance_point_to_segment_meters(points[i], points[start], points[end])
            if d > max_dist:
                max_dist = d
                max_idx = i
        if max_dist > tolerance_m:
            left = _dp(start, max_idx)
            right = _dp(max_idx, end)
            return left + [max_idx] + right
        return []

    keep_idx = sorted({0, len(points) - 1} | set(_dp(0, len(points) - 1)))
    return [points[i] for i in keep_idx]


def snap_to_polyline(point: Point, polyline: list[Point]) -> tuple[Point, float]:
    """Snap titik ke vertex polyline terdekat. Return (snapped, distance_m)."""
    if not polyline:
        return point, float("inf")
    best = polyline[0]
    best_d = haversine_meters(point[0], point[1], best[0], best[1])
    for cand in polyline[1:]:
        d = haversine_meters(point[0], point[1], cand[0], cand[1])
        if d < best_d:
            best = cand
            best_d = d
    return best, best_d
