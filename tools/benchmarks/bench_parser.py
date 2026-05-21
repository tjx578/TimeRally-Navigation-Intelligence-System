"""Benchmark sederhana rally parser.

Mengukur:
- parse latency rata-rata,
- jumlah waypoint per detik,
- normalisasi text vs raw size.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "rally_core"))
sys.path.insert(0, str(ROOT / "packages" / "geo_engine"))
sys.path.insert(0, str(ROOT / "packages" / "knowledge_engine"))

from rally_core import RallyParser  # noqa: E402


SAMPLE = """
Event: Pertamina Merah Putih Bali 2024
Trayek 1
Total Jarak 93.4 km
Total Waktu 270 menit
Start 07:30

Sub A: Menuju zero trip
Title: Menuju zero trip
Jarak: 0 km
Waktu: 5 menit
Mode: Liaison Zero Trip
BKR di POM SDN

Sub B: Zero trip ke KC Denpasar Barat
Jarak: 20.1 km
Waktu: 60 menit
Mode: Average Speed
JT di O Lapangan Renon
BKN di X LR Imam Bonjol
BKR di T br Suwung Kauh
KSM 2/DPS 11/PNT 0 finish
"""


def main(iterations: int = 200) -> int:
    parser = RallyParser()
    durations: list[float] = []
    waypoints = 0
    for _ in range(iterations):
        t0 = time.perf_counter()
        result = parser.parse(SAMPLE)
        durations.append(time.perf_counter() - t0)
        waypoints = result.event.waypoint_count
    avg = mean(durations) * 1000
    print(f"iterations           : {iterations}")
    print(f"avg parse (ms)       : {avg:.3f}")
    print(f"min parse (ms)       : {min(durations) * 1000:.3f}")
    print(f"max parse (ms)       : {max(durations) * 1000:.3f}")
    print(f"waypoints detected   : {waypoints}")
    print(f"throughput (wp/s)    : {waypoints / mean(durations):.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
