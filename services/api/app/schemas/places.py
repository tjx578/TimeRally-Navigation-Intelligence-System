from pydantic import BaseModel


class Coordinate(BaseModel):
    lat: float
    lng: float


class PlaceSourceReference(BaseModel):
    source: str
    source_license: str
    google_place_id: str | None = None
    google_maps_url: str | None = None
    verification_status: str = "needs_review"
    allowed_use: str | None = None


class PlaceSearchRequest(BaseModel):
    query: str
    category_hint: str | None = None
    location_bias: Coordinate | None = None
    max_results: int = 10


class PlaceCandidate(BaseModel):
    name: str
    coordinate: Coordinate | None = None
    source: str
    status: str
    confidence: float
    reason: list[str] = []
    category: str | None = None
    category_group: str | None = None
    district: str | None = None
    village: str | None = None
    reference: PlaceSourceReference | None = None


class PlaceSearchResponse(BaseModel):
    query: str
    candidates: list[PlaceCandidate]
    status: str


class PlaceImportProfile(BaseModel):
    rows: int
    unique_place_ids: int
    blank_coordinates: int
    outside_region: int
    duplicate_name_count: int
    governance_status: str
