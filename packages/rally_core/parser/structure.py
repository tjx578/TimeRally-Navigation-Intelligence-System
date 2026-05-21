"""Deteksi struktur global event rally: nama event, total jarak/waktu, mode kecepatan."""

from __future__ import annotations

import re
from dataclasses import dataclass


_DISTANCE_RE = re.compile(
    r"(?:total\s+jarak|jarak\s+total|distance|km(?:\.?\s+total)?|jrk(?:\.?\s+total)?)[^\d]*"
    r"(\d+(?:[\.,]\d+)?)\s*km",
    re.IGNORECASE,
)
_DURATION_RE = re.compile(
    r"(?:total\s+waktu|waktu\s+total|duration|wkt\.?\s+total)[^\d]*"
    r"(\d{1,3})\s*(?:menit|min|m)\b",
    re.IGNORECASE,
)
_START_TIME_RE = re.compile(
    r"(?:start|mulai|wkt\.?\s+start|jam\s+start)[^\d]*"
    r"(\d{1,2})[:.](\d{2})",
    re.IGNORECASE,
)
_EVENT_NAME_RE = re.compile(r"(?im)^\s*(?:event|rally|trayek|lomba)\s*[:\-]\s*(.+)$")
_LOCATION_RE = re.compile(r"(?im)^\s*(?:lokasi|location|kota)\s*[:\-]\s*(.+)$")


@dataclass
class DetectedHeader:
    event_name: str | None = None
    trayek_name: str | None = None
    location: str | None = None
    total_distance_km: float | None = None
    total_time_minutes: float | None = None
    rally_start_time: str | None = None


def detect_header(text: str) -> DetectedHeader:
    header = DetectedHeader()

    match = _DISTANCE_RE.search(text)
    if match:
        header.total_distance_km = float(match.group(1).replace(",", "."))

    match = _DURATION_RE.search(text)
    if match:
        header.total_time_minutes = float(match.group(1))

    match = _START_TIME_RE.search(text)
    if match:
        header.rally_start_time = f"{int(match.group(1)):02d}:{int(match.group(2)):02d}"

    match = _EVENT_NAME_RE.search(text)
    if match:
        header.event_name = match.group(1).strip().rstrip(".")

    match = _LOCATION_RE.search(text)
    if match:
        header.location = match.group(1).strip().rstrip(".")

    # Fallback: ambil baris pertama yang non-kosong sebagai event_name jika belum ada
    if header.event_name is None:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.lower().startswith(("sub", "trayek", "total", "start")):
                header.event_name = stripped[:160]
                break

    # Trayek detection
    trayek_match = re.search(r"(?i)trayek\s+([0-9]+|[ivxIVX]+)", text)
    if trayek_match:
        header.trayek_name = f"Trayek {trayek_match.group(1).upper()}"

    return header
