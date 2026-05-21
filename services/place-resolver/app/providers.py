"""Resolution provider chain - local-first.

Urutan:
1. Local verified POI (curated YAML)
2. KMPAL database
3. Nominatim (jika tersedia)
4. Google Places (jika diaktifkan)
5. Inferred / unresolved
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from knowledge_engine import KnowledgeIndex


@dataclass
class ResolvedCandidate:
    name: str
    lat: float
    lng: float
    source: str
    status: str
    confidence: float
    reasons: list[str]


class LocalProvider:
    name = "local"

    def __init__(self, index: KnowledgeIndex) -> None:
        self.index = index

    def search(self, query: str, limit: int) -> list[ResolvedCandidate]:
        out: list[ResolvedCandidate] = []
        for hit in self.index.search_place(query, limit=limit):
            p = hit.payload
            out.append(
                ResolvedCandidate(
                    name=p["name"],
                    lat=p["lat"],
                    lng=p["lng"],
                    source=p.get("source", "curated_local"),
                    status="verified_local",
                    confidence=hit.confidence,
                    reasons=["match dari curated local"],
                )
            )
        return out


class KMPALProvider:
    name = "kmpal"

    def __init__(self, index: KnowledgeIndex) -> None:
        self.index = index

    def search(self, query: str, limit: int) -> list[ResolvedCandidate]:
        results: list[ResolvedCandidate] = []
        point = self.index.kmpal.find(query)
        if point:
            results.append(
                ResolvedCandidate(
                    name=f"{point.code} {point.km:g} km",
                    lat=point.lat,
                    lng=point.lng,
                    source=point.source,
                    status="verified_kmpal",
                    confidence=point.confidence,
                    reasons=["KMPAL terkalibrasi"],
                )
            )
        return results[:limit]


class NominatimProvider:
    name = "nominatim"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.getenv("NOMINATIM_URL", "")).rstrip("/")

    async def search(self, query: str, limit: int) -> list[ResolvedCandidate]:
        if not self.base_url:
            return []
        url = f"{self.base_url}/search"
        params = {"q": query, "format": "json", "limit": limit, "addressdetails": 0}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception:  # noqa: BLE001
            return []
        out: list[ResolvedCandidate] = []
        for item in data:
            out.append(
                ResolvedCandidate(
                    name=item.get("display_name", query),
                    lat=float(item["lat"]),
                    lng=float(item["lon"]),
                    source="nominatim_local",
                    status="verified_osm",
                    confidence=0.8,
                    reasons=["match dari nominatim local"],
                )
            )
        return out


class GoogleProvider:
    name = "google"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        self.enabled = (os.getenv("GOOGLE_ENABLED") or "").lower() in {"1", "true", "yes"}

    async def search(self, query: str, limit: int) -> list[ResolvedCandidate]:
        if not self.enabled or not self.api_key:
            return []
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.location",
        }
        body = {"textQuery": query, "pageSize": limit}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except Exception:  # noqa: BLE001
            return []
        out: list[ResolvedCandidate] = []
        for item in data.get("places", []):
            location = item.get("location", {})
            out.append(
                ResolvedCandidate(
                    name=item.get("displayName", {}).get("text", query),
                    lat=float(location.get("latitude", 0)),
                    lng=float(location.get("longitude", 0)),
                    source="google_places",
                    status="verified_google_online",
                    confidence=0.85,
                    reasons=["match dari google places online"],
                )
            )
        return out
