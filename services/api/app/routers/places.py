"""Router /v1/places - place search local-first."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.places import (
    Coordinate,
    PlaceCandidate,
    PlaceSearchRequest,
    PlaceSearchResponse,
)
from app.use_cases import resolve_place_query


router = APIRouter()


@router.post("/search", response_model=PlaceSearchResponse)
def search_places(request: PlaceSearchRequest) -> PlaceSearchResponse:
    candidates = resolve_place_query(
        request.query,
        category_hint=request.category_hint,
        max_results=request.max_results,
    )
    if not candidates:
        return PlaceSearchResponse(
            query=request.query,
            candidates=[],
            status="empty: tidak ada hit di curated local. Eskalasi ke nominatim/google.",
        )
    return PlaceSearchResponse(
        query=request.query,
        candidates=[
            PlaceCandidate(
                name=c.name,
                coordinate=Coordinate(lat=c.lat, lng=c.lng),
                source=c.source,
                status="verified_local",
                confidence=c.confidence,
                reason=c.reasons,
                category=c.category,
                district=c.region or None,
            )
            for c in candidates
        ],
        status="ok",
    )
