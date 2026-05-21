"""Use case: resolve place query menjadi candidate list (local-first)."""

from __future__ import annotations

from dataclasses import dataclass

from app.adapters.knowledge import build_default_knowledge_index


@dataclass
class ResolvedCandidate:
    name: str
    lat: float
    lng: float
    source: str
    confidence: float
    category: str
    region: str
    reasons: list[str]


def resolve_place_query(
    query: str,
    *,
    category_hint: str | None = None,
    max_results: int = 10,
) -> list[ResolvedCandidate]:
    index = build_default_knowledge_index()
    hits = index.search_place(query, limit=max_results)
    out: list[ResolvedCandidate] = []
    for hit in hits:
        payload = hit.payload
        reasons: list[str] = ["match dari curated local"]
        if category_hint and category_hint.lower() in str(payload.get("category", "")).lower():
            reasons.append("category cocok dengan hint")
        out.append(
            ResolvedCandidate(
                name=payload["name"],
                lat=payload["lat"],
                lng=payload["lng"],
                source=payload.get("source", "curated_local"),
                confidence=hit.confidence,
                category=payload.get("category", "unknown"),
                region=payload.get("region", ""),
                reasons=reasons,
            )
        )
    return out
