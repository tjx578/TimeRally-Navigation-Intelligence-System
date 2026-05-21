"""Place alias store - mapping nama lokal ke koordinat verified."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

import yaml


_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


def _normalize(name: str) -> str:
    return _NORMALIZE_RE.sub(" ", name.lower()).strip()


@dataclass
class PlaceAlias:
    canonical_name: str
    aliases: list[str]
    lat: float
    lng: float
    category: str = "unknown"
    region: str = ""
    confidence: float = 1.0
    source: str = "curated_local"


@dataclass
class PlaceAliasStore:
    aliases: list[PlaceAlias] = field(default_factory=list)

    def add(self, alias: PlaceAlias) -> None:
        self.aliases.append(alias)

    def search(self, query: str, limit: int = 10) -> list[PlaceAlias]:
        norm = _normalize(query)
        if not norm:
            return []
        scored: list[tuple[float, PlaceAlias]] = []
        for p in self.aliases:
            haystacks = [_normalize(p.canonical_name)] + [_normalize(a) for a in p.aliases]
            best = 0.0
            for h in haystacks:
                if not h:
                    continue
                if h == norm:
                    best = max(best, 1.0)
                elif norm in h or h in norm:
                    overlap = min(len(norm), len(h)) / max(len(norm), len(h))
                    best = max(best, 0.6 + 0.3 * overlap)
                else:
                    norm_tokens = set(norm.split())
                    h_tokens = set(h.split())
                    if norm_tokens and h_tokens:
                        jacc = len(norm_tokens & h_tokens) / len(norm_tokens | h_tokens)
                        if jacc > 0:
                            best = max(best, 0.3 + 0.4 * jacc)
            if best > 0:
                scored.append((best, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in scored[:limit]]

    def find_exact(self, name: str) -> Optional[PlaceAlias]:
        norm = _normalize(name)
        for p in self.aliases:
            if _normalize(p.canonical_name) == norm:
                return p
            if any(_normalize(a) == norm for a in p.aliases):
                return p
        return None

    def add_many(self, items: Iterable[PlaceAlias]) -> None:
        for it in items:
            self.add(it)

    @classmethod
    def from_yaml_file(cls, path: str | Path) -> "PlaceAliasStore":
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        items = [
            PlaceAlias(
                canonical_name=p["name"],
                aliases=list(p.get("aliases", [])),
                lat=float(p["lat"]),
                lng=float(p["lng"]),
                category=p.get("category", "unknown"),
                region=p.get("region", ""),
                confidence=float(p.get("confidence", 1.0)),
                source=p.get("source", "curated_local"),
            )
            for p in raw.get("places", [])
        ]
        return cls(aliases=items)
