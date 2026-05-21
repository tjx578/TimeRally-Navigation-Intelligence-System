"""Formula waktu rally.

Mendukung 4 mode kecepatan utama:

- average_speed: total_distance / total_time
- fixed_second: km per second (mode Tetap Detik)
- remaining_distance: speed dihitung dari sisa jarak ke finish
- liaison_zero_trip: hanya waktu yang dihitung; jarak tidak dijumlahkan ke total
"""

from __future__ import annotations

from typing import Literal


SpeedMode = Literal["average_speed", "fixed_second", "remaining_distance", "liaison_zero_trip", "unknown"]


def average_speed_kmh(distance_km: float, duration_minutes: float) -> float | None:
    if duration_minutes <= 0:
        return None
    return round(distance_km / (duration_minutes / 60.0), 4)


def fixed_second_per_km(speed_kmh: float) -> float | None:
    if speed_kmh <= 0:
        return None
    return round(3600.0 / speed_kmh, 4)


def km_per_second(speed_kmh: float) -> float | None:
    if speed_kmh <= 0:
        return None
    return round(speed_kmh / 3600.0, 8)


def leg_duration_seconds(distance_km: float, speed_kmh: float) -> float | None:
    if speed_kmh <= 0:
        return None
    return round(distance_km / speed_kmh * 3600.0, 3)


def remaining_distance_speed(
    total_distance_km: float,
    cumulative_distance_km: float,
    remaining_time_minutes: float,
) -> float | None:
    """Mode 'sisa jarak finish': speed dihitung dari sisa jarak / sisa waktu."""
    remaining = total_distance_km - cumulative_distance_km
    if remaining <= 0 or remaining_time_minutes <= 0:
        return None
    return round(remaining / (remaining_time_minutes / 60.0), 4)


def classify_label(speed_mode: SpeedMode) -> str:
    return {
        "average_speed": "Kecepatan rata-rata",
        "fixed_second": "Kecepatan tetap detik",
        "remaining_distance": "Sisa jarak finish",
        "liaison_zero_trip": "Start / zero trip",
        "unknown": "Mode tidak diketahui",
    }[speed_mode]
