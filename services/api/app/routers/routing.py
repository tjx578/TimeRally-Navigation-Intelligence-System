from fastapi import APIRouter

from app.schemas.routing import RouteRequest, RouteResponse


router = APIRouter()


@router.post("/route", response_model=RouteResponse)
def route(request: RouteRequest) -> RouteResponse:
    return RouteResponse(
        provider=request.provider,
        legs=[],
        total_distance_m=0,
        total_duration_s=0,
        status="skeleton_ready: wire routing-gateway provider",
    )

