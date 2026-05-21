"""Distance & bearing helpers."""

from __future__ import annotations

from math import asin, atan2, cos, degrees, radians, sin, sqrt


EARTH_RADIUS_METERS = 6_371_000


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlmb = radians(lng2 - lng1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(min(1.0, sqrt(a)))


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    return haversine_meters(lat1, lng1, lat2, lng2) / 1000.0


def bearing_degrees(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial bearing dari titik 1 ke titik 2 (derajat 0..360)."""
    phi1, phi2 = radians(lat1), radians(lat2)
    dl = radians(lng2 - lng1)
    x = sin(dl) * cos(phi2)
    y = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(dl)
    brng = degrees(atan2(x, y))
    return (brng + 360.0) % 360.0
