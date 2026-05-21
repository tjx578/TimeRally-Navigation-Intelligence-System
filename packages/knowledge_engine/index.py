"""KnowledgeIndex: pintu masuk pencarian local-first.

Penggunaan:

    idx = KnowledgeIndex(
        abbreviations=default_abbreviation_dictionary(),
        places=PlaceAliasStore.from_yaml_file("data/curated/places/bali.yaml"),
        kmpal=KMPALDatabase.from_yaml_file("data/curated/kmpal/bali.yaml"),
    )

    hits = idx.lookup("KSM 2")
    candidates = idx.search_place("Pantai Mertasari")

KnowledgeIndex tidak melakukan network call. Untuk Google/Nominatim, panggil
service eksternal terpisah.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from knowledge_engine.abbreviations import (
    AbbreviationDictionary,
    AbbreviationEntry,
    default_abbreviation_dictionary,
)
from knowledge_engine.kmpal import KMPALDatabase, KMPALPoint
from knowledge_engine.places import PlaceAlias, PlaceAliasStore


@dataclass
class KnowledgeHit:
    kind: str  # abbreviation | place | kmpal
    confidence: float
    payload: dict[str, Any]


@dataclass
class KnowledgeIndex:
    abbreviations: AbbreviationDictionary = field(default_factory=default_abbreviation_dictionary)
    places: PlaceAliasStore = field(default_factory=PlaceAliasStore)
    kmpal: KMPALDatabase = field(default_factory=KMPALDatabase)

    def lookup(self, token: str) -> list[KnowledgeHit]:
        hits: list[KnowledgeHit] = []
        for entry in self.abbreviations.find(token):
            hits.append(self._abbreviation_hit(entry))
        kmpal = self.kmpal.find(token)
        if kmpal:
            hits.append(self._kmpal_hit(kmpal))
        place = self.places.find_exact(token)
        if place:
            hits.append(self._place_hit(place, 1.0))
        return hits

    def search_place(self, query: str, limit: int = 10) -> list[KnowledgeHit]:
        results = self.places.search(query, limit=limit)
        return [self._place_hit(p, 0.9) for p in results]

    def search_kmpal(self, code: str) -> list[KnowledgeHit]:
        return [self._kmpal_hit(p) for p in self.kmpal.find_all_code(code)]

    # ----- internal helpers -----

    def _abbreviation_hit(self, entry: AbbreviationEntry) -> KnowledgeHit:
        return KnowledgeHit(
            kind="abbreviation",
            confidence=0.95 if entry.case_sensitive else 0.92,
            payload={
                "token": entry.token,
                "meaning": entry.meaning,
                "kind": entry.kind,
                "case_sensitive": entry.case_sensitive,
            },
        )

    def _kmpal_hit(self, point: KMPALPoint) -> KnowledgeHit:
        return KnowledgeHit(
            kind="kmpal",
            confidence=point.confidence,
            payload={
                "code": point.code,
                "km": point.km,
                "lat": point.lat,
                "lng": point.lng,
                "description": point.description,
                "region": point.region,
                "source": point.source,
            },
        )

    def _place_hit(self, place: PlaceAlias, confidence: float) -> KnowledgeHit:
        return KnowledgeHit(
            kind="place",
            confidence=min(confidence, place.confidence),
            payload={
                "name": place.canonical_name,
                "aliases": place.aliases,
                "lat": place.lat,
                "lng": place.lng,
                "category": place.category,
                "region": place.region,
                "source": place.source,
            },
        )
