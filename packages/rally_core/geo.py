"""Geo helpers internal package rally_core.

Untuk operasi geospasial yang lebih lengkap pakai packages/geo_engine.
File ini hanya menyediakan haversine ringan agar constraint engine
tidak punya dependency lintas-package.
"""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_METERS = 6_371_000


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance haversine dalam meter."""
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlmb = radians(lng2 - lng1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(min(1.0, sqrt(a)))


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return haversine_meters(lat1, lng1, lat2, lng2) / 1000.0
