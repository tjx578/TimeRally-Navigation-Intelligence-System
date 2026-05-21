"""Geo utility package.

Berisi fungsi geospasial level rendah yang dipakai oleh:
- rally_core.constraints (chaining, route realism)
- rally_core.probability (corridor fit)
- routing-gateway adapter (snap candidate scoring)
- web UI lewat API (geometry simplification)
"""

from geo_engine.distance import haversine_meters, haversine_km, bearing_degrees
from geo_engine.corridor import (
    distance_point_to_line_meters,
    point_in_corridor,
    corridor_fit,
)
from geo_engine.geometry import simplify_polyline, snap_to_polyline
from geo_engine.turns import classify_turn, turn_angle_degrees

__all__ = [
    "haversine_meters",
    "haversine_km",
    "bearing_degrees",
    "distance_point_to_line_meters",
    "point_in_corridor",
    "corridor_fit",
    "simplify_polyline",
    "snap_to_polyline",
    "classify_turn",
    "turn_angle_degrees",
]
