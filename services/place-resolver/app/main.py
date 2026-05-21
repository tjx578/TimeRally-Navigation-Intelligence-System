"""Place resolver service.

Eksposes:
- POST /v1/places/search
- POST /v1/places/reverse
- GET  /health
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from knowledge_engine import (
    KMPALDatabase,
    KnowledgeIndex,
    PlaceAliasStore,
    default_abbreviation_dictionary,
)

from .providers import (
    GoogleProvider,
    KMPALProvider,
    LocalProvider,
    NominatimProvider,
    ResolvedCandidate,
)


def _load_knowledge() -> KnowledgeIndex:
    root = Path(os.getenv("KNOWLEDGE_ROOT", "data/curated"))
    place_store = PlaceAliasStore()
    kmpal_db = KMPALDatabase()
    if (root / "places").is_dir():
        for yaml_file in (root / "places").glob("*.yaml"):
            try:
                place_store.add_many(PlaceAliasStore.from_yaml_file(yaml_file).aliases)
            except Exception:  # noqa: BLE001
                continue
    if (root / "kmpal").is_dir():
        for yaml_file in (root / "kmpal").glob("*.yaml"):
            try:
                kmpal_db.points.extend(KMPALDatabase.from_yaml_file(yaml_file).points)
            except Exception:  # noqa: BLE001
                continue
    return KnowledgeIndex(
        abbreviations=default_abbreviation_dictionary(),
        places=place_store,
        kmpal=kmpal_db,
    )


_INDEX = _load_knowledge()
_LOCAL = LocalProvider(_INDEX)
_KMPAL = KMPALProvider(_INDEX)
_NOMINATIM = NominatimProvider()
_GOOGLE = GoogleProvider()


app = FastAPI(title="Time Rally Place Resolver", version="0.1.0")


class SearchRequest(BaseModel):
    query: str
    max_results: int = 10
    use_online: bool = False


class SearchResponseItem(BaseModel):
    name: str
    lat: float
    lng: float
    source: str
    status: str
    confidence: float
    reasons: list[str]


class SearchResponse(BaseModel):
    query: str
    candidates: list[SearchResponseItem]
    total: int


def _dedupe(candidates: list[ResolvedCandidate]) -> list[ResolvedCandidate]:
    seen: set[tuple[str, float, float]] = set()
    out: list[ResolvedCandidate] = []
    for c in candidates:
        key = (c.name.lower(), round(c.lat, 5), round(c.lng, 5))
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "providers": ["local", "kmpal", "nominatim", "google"],
        "nominatim_enabled": bool(_NOMINATIM.base_url),
        "google_enabled": _GOOGLE.enabled,
        "kmpal_points": len(_INDEX.kmpal.points),
        "places_local": len(_INDEX.places.aliases),
    }


@app.post("/v1/places/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    aggregated: list[ResolvedCandidate] = []
    aggregated.extend(_LOCAL.search(req.query, req.max_results))
    aggregated.extend(_KMPAL.search(req.query, req.max_results))
    if req.use_online:
        aggregated.extend(await _NOMINATIM.search(req.query, req.max_results))
        aggregated.extend(await _GOOGLE.search(req.query, req.max_results))
    deduped = _dedupe(aggregated)[: req.max_results]
    return SearchResponse(
        query=req.query,
        candidates=[SearchResponseItem(**c.__dict__) for c in deduped],
        total=len(deduped),
    )


class ReverseRequest(BaseModel):
    lat: float
    lng: float
    use_online: bool = False


@app.post("/v1/places/reverse", response_model=SearchResponse)
async def reverse(req: ReverseRequest) -> SearchResponse:
    # Reverse geocode: cari di KMPAL terdekat, lalu fallback nominatim
    matches: list[ResolvedCandidate] = []
    closest: tuple[float, ResolvedCandidate] | None = None
    from geo_engine.distance import haversine_meters

    for point in _INDEX.kmpal.points:
        d = haversine_meters(req.lat, req.lng, point.lat, point.lng)
        cand = ResolvedCandidate(
            name=f"{point.code} {point.km:g} km",
            lat=point.lat,
            lng=point.lng,
            source=point.source,
            status="verified_kmpal",
            confidence=max(0.0, 1.0 - d / 5000.0),
            reasons=[f"jarak {d:.0f} m dari titik kueri"],
        )
        if closest is None or d < closest[0]:
            closest = (d, cand)
    if closest and closest[0] < 500:
        matches.append(closest[1])

    if req.use_online and _NOMINATIM.base_url:
        nominatim_hits = await _NOMINATIM.search(f"{req.lat},{req.lng}", 1)
        matches.extend(nominatim_hits)

    return SearchResponse(
        query=f"reverse:{req.lat},{req.lng}",
        candidates=[SearchResponseItem(**c.__dict__) for c in matches],
        total=len(matches),
    )
