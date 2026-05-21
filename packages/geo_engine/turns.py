"""Turn geometry analysis."""

from __future__ import annotations

from typing import Literal

from geo_engine.distance import bearing_degrees


TurnLabel = Literal[
    "jalan_terus",
    "belok_kanan",
    "belok_kiri",
    "tikung_kanan",
    "tikung_kiri",
    "balik_arah",
    "ambil_kanan",
    "ambil_kiri",
]


def turn_angle_degrees(
    prev_lat: float,
    prev_lng: float,
    pivot_lat: float,
    pivot_lng: float,
    next_lat: float,
    next_lng: float,
) -> float:
    """Sudut belok di pivot. Positif = kanan, negatif = kiri, 180/-180 = balik.

    Output dalam range [-180, 180].
    """
    b_in = bearing_degrees(prev_lat, prev_lng, pivot_lat, pivot_lng)
    b_out = bearing_degrees(pivot_lat, pivot_lng, next_lat, next_lng)
    diff = (b_out - b_in + 540.0) % 360.0 - 180.0
    return round(diff, 2)


def classify_turn(angle_deg: float) -> TurnLabel:
    """Klasifikasi sudut belok ke label rally."""
    a = angle_deg
    if -15 < a < 15:
        return "jalan_terus"
    if 15 <= a < 60:
        return "tikung_kanan"
    if 60 <= a < 135:
        return "belok_kanan"
    if a >= 135:
        return "balik_arah" if a > 165 else "ambil_kanan"
    if -60 < a <= -15:
        return "tikung_kiri"
    if -135 < a <= -60:
        return "belok_kiri"
    return "balik_arah" if a < -165 else "ambil_kiri"
