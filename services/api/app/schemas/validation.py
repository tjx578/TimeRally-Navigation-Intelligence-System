from pydantic import BaseModel
from typing import Literal


class ValidationRequest(BaseModel):
    target_distance_km: float
    target_time_minutes: int
    calculated_distance_km: float
    calculated_time_minutes: float
    chaining_gap_meters: float = 0


class ValidationResponse(BaseModel):
    distance_status: str
    time_status: str
    chaining_status: str
    score: int
    warnings: list[str]


class SubTrayekTimingInput(BaseModel):
    sub: str
    duration_minutes: float
    distance_km: float | None = None
    inferred_distance_km: float | None = None
    distance_counted_in_total: bool = True
    speed_mode: Literal[
        "liaison_zero_trip",
        "average_speed",
        "fixed_second",
        "remaining_distance",
    ] = "average_speed"


class SubTrayekTimingResult(SubTrayekTimingInput):
    calculated_speed_kmh: float | None
    km_per_second: float | None
    classification_label: str
    scheduled_start_time: str | None = None
    scheduled_finish_time: str | None = None
    cumulative_start_minutes: float | None = None
    cumulative_finish_minutes: float | None = None
    status: Literal["valid", "warning", "error", "unchecked"]
    notes: list[str]


class TimingTableValidationRequest(BaseModel):
    trayek_id: str
    declared_distance_km: float
    declared_duration_minutes: float
    rally_start_time: str | None = None
    distance_tolerance_km: float = 0.05
    duration_tolerance_minutes: float = 0
    rows: list[SubTrayekTimingInput]


class TimingTableValidationResponse(BaseModel):
    trayek_id: str
    declared_distance_km: float
    declared_duration_minutes: float
    calculated_distance_km: float
    calculated_duration_minutes: float
    distance_delta_km: float
    duration_delta_minutes: float
    status: Literal["valid", "warning", "error", "unchecked"]
    rows: list[SubTrayekTimingResult]
    warnings: list[str]
