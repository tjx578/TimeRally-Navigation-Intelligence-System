from fastapi import APIRouter

from app.schemas.places import PlaceSearchRequest, PlaceSearchResponse


router = APIRouter()


@router.post("/search", response_model=PlaceSearchResponse)
def search_places(request: PlaceSearchRequest) -> PlaceSearchResponse:
    return PlaceSearchResponse(
        query=request.query,
        candidates=[],
        status="skeleton_ready: wire place-resolver providers",
    )

