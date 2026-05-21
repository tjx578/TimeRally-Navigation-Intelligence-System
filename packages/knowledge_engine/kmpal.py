"""KMPAL database.

KMPAL = Kilometer Penanda (titik nol) di setiap area rally.
Format token: <KODE> <KM>, contoh: "KSM 2", "DPS 11", "PNT 0", "CT 7".

Database memetakan token KMPAL ke koordinat referensi yang sudah disurvey.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


_KMPAL_TOKEN_RE = re.compile(r"^([A-Z]{2,4})\s*(\d+(?:\.\d+)?)$")


@dataclass
class KMPALPoint:
    code: str  # KSM, DPS, PNT, CT, dst.
    km: float
    lat: float
    lng: float
    description: str = ""
    region: str = ""
    confidence: float = 1.0
    source: str = "local_survey"


@dataclass
class KMPALDatabase:
    points: list[KMPALPoint] = field(default_factory=list)

    def add(self, point: KMPALPoint) -> None:
        self.points.append(point)

    def find(self, token: str) -> Optional[KMPALPoint]:
        match = _KMPAL_TOKEN_RE.match(token.strip().upper())
        if not match:
            return None
        code, km = match.group(1), float(match.group(2))
        for p in self.points:
            if p.code.upper() == code and abs(p.km - km) < 0.05:
                return p
        return None

    def find_all_code(self, code: str) -> list[KMPALPoint]:
        return [p for p in self.points if p.code.upper() == code.upper()]

    def parse_compound(self, marker: str) -> list[KMPALPoint]:
        """Parse marker compound seperti 'KSM 2/DPS 11/PNT 0' -> list KMPAL ditemukan."""
        parts = [p.strip() for p in marker.replace("|", "/").split("/")]
        results: list[KMPALPoint] = []
        for part in parts:
            point = self.find(part)
            if point:
                results.append(point)
        return results

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "KMPALDatabase":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        points = [
            KMPALPoint(
                code=p["code"],
                km=float(p["km"]),
                lat=float(p["lat"]),
                lng=float(p["lng"]),
                description=p.get("description", ""),
                region=p.get("region", ""),
                confidence=float(p.get("confidence", 1.0)),
                source=p.get("source", "local_survey"),
            )
            for p in raw.get("points", [])
        ]
        return cls(points=points)
