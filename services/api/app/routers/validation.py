"""Router /v1/validation - validasi binding constraint dan timing table."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.validation import (
    SubTrayekTimingResult,
    TimingTableValidationRequest,
    TimingTableValidationResponse,
    ValidationRequest,
    ValidationResponse,
)
from rally_core.constraints.engine import ConstraintEngine


router = APIRouter()


def _parse_clock_minutes(value: str | None) -> int | None:
    if not value:
        return None
    hours, minutes = value.split(":", maxsplit=1)
    return int(hours) * 60 + int(minutes)


def _format_clock(total_minutes: float | None) -> str | None:
    if total_minutes is None:
        return None
    normalized = int(round(total_minutes)) % 1440
    return f"{normalized // 60:02d}:{normalized % 60:02d}"


def _classification_label(speed_mode: str) -> str:
    if speed_mode == "fixed_second":
        return "Kecepatan tetap detik"
    if speed_mode == "average_speed":
        return "Kecepatan rata-rata"
    if speed_mode == "remaining_distance":
        return "Sisa jarak finish"
    return "Start/zero trip"


@router.post("/route", response_model=ValidationResponse)
def validate_route(request: ValidationRequest) -> ValidationResponse:
    engine = ConstraintEngine()
    dist_check = engine.check_total_distance(
        target_km=request.target_distance_km,
        calculated_km=request.calculated_distance_km,
    )
    time_check = engine.check_total_time(
        target_min=float(request.target_time_minutes),
        calculated_min=request.calculated_time_minutes,
    )
    chaining_status = (
        "compliant"
        if request.chaining_gap_meters <= engine.chaining_tolerance_m
        else "warning"
        if request.chaining_gap_meters <= engine.chaining_tolerance_m * 4
        else "violation"
    )

    score_components = [dist_check.status, time_check.status, chaining_status]
    score = sum(1 for s in score_components if s == "compliant") * 33

    warnings: list[str] = []
    if dist_check.status != "compliant":
        warnings.append(dist_check.message)
    if time_check.status != "compliant":
        warnings.append(time_check.message)
    if chaining_status != "compliant":
        warnings.append(f"chaining gap {request.chaining_gap_meters:.1f} m melebihi toleransi")
    if request.target_distance_km <= 0:
        warnings.append("target_distance_km must be greater than zero")

    return ValidationResponse(
        distance_status=dist_check.status,
        time_status=time_check.status,
        chaining_status=chaining_status,
        score=score,
        warnings=warnings,
    )


@router.post("/timing-table", response_model=TimingTableValidationResponse)
def validate_timing_table(request: TimingTableValidationRequest) -> TimingTableValidationResponse:
    calculated_distance = round(
        sum(
            (row.distance_km if row.distance_km is not None else row.inferred_distance_km) or 0
            for row in request.rows
            if row.distance_counted_in_total
        ),
        3,
    )
    calculated_duration = round(sum(row.duration_minutes for row in request.rows), 3)
    distance_delta = round(calculated_distance - request.declared_distance_km, 3)
    duration_delta = round(calculated_duration - request.declared_duration_minutes, 3)

    warnings: list[str] = []
    if abs(distance_delta) > request.distance_tolerance_km:
        warnings.append("Jumlah jarak sub-trayek tidak sesuai dengan total jarak pada soal.")
    if abs(duration_delta) > request.duration_tolerance_minutes:
        warnings.append("Jumlah waktu sub-trayek tidak sesuai dengan total waktu pada soal.")

    rows: list[SubTrayekTimingResult] = []
    start_clock_minutes = _parse_clock_minutes(request.rally_start_time)
    cumulative_minutes = 0.0
    for row in request.rows:
        cumulative_start = cumulative_minutes
        cumulative_finish = cumulative_start + row.duration_minutes
        cumulative_minutes = cumulative_finish
        notes: list[str] = []
        speed = None
        row_status = "valid"
        distance_for_speed = row.distance_km if row.distance_km is not None else row.inferred_distance_km
        if distance_for_speed is not None and row.duration_minutes > 0:
            speed = round(distance_for_speed / row.duration_minutes * 60, 2)
        km_per_second = round(speed / 3600, 8) if speed is not None else None
        if row.duration_minutes <= 0:
            row_status = "error"
            notes.append("Durasi sub-trayek harus lebih besar dari nol.")
        if row.distance_counted_in_total and row.distance_km is None and row.inferred_distance_km is None:
            row_status = "warning"
            notes.append("Sub-trayek dihitung ke total, tetapi jarak belum terbaca dari OCR.")
        if row.inferred_distance_km is not None:
            row_status = "warning"
            notes.append("Jarak sub-trayek diisi dari hasil rekonsiliasi total dan perlu review navigator.")
        if not row.distance_counted_in_total:
            notes.append("Sub ini dipakai untuk waktu pengantar dan tidak dihitung ke total jarak.")

        rows.append(
            SubTrayekTimingResult(
                **(row.model_dump() if hasattr(row, "model_dump") else row.dict()),
                calculated_speed_kmh=speed,
                km_per_second=km_per_second,
                classification_label=_classification_label(row.speed_mode),
                scheduled_start_time=_format_clock(
                    start_clock_minutes + cumulative_start if start_clock_minutes is not None else None
                ),
                scheduled_finish_time=_format_clock(
                    start_clock_minutes + cumulative_finish if start_clock_minutes is not None else None
                ),
                cumulative_start_minutes=cumulative_start,
                cumulative_finish_minutes=cumulative_finish,
                status=row_status,
                notes=notes,
            )
        )

    status = "valid" if not warnings and all(row.status == "valid" for row in rows) else "warning"
    if any(row.status == "error" for row in rows):
        status = "error"

    return TimingTableValidationResponse(
        trayek_id=request.trayek_id,
        declared_distance_km=request.declared_distance_km,
        declared_duration_minutes=request.declared_duration_minutes,
        calculated_distance_km=calculated_distance,
        calculated_duration_minutes=calculated_duration,
        distance_delta_km=distance_delta,
        duration_delta_minutes=duration_delta,
        status=status,
        rows=rows,
        warnings=warnings,
    )
