/**
 * Sub trayek validation feature.
 *
 * Memanggil /v1/validation/timing-table dan menyajikan hasil ke
 * TimingValidationTable.
 */

import { postJson } from "../../lib/api/client";
import type {
  SubTrayekSpeedMode,
  SubTrayekTimingRow,
  TimingValidationStatus,
  TrayekTimingValidation,
} from "../../types/rally";

export interface TimingValidateRequest {
  trayek_id: string;
  declared_distance_km: number;
  declared_duration_minutes: number;
  rally_start_time?: string;
  distance_tolerance_km?: number;
  duration_tolerance_minutes?: number;
  rows: Array<{
    sub: string;
    duration_minutes: number;
    distance_km?: number | null;
    inferred_distance_km?: number | null;
    distance_counted_in_total?: boolean;
    speed_mode?: SubTrayekSpeedMode;
  }>;
}

interface TimingValidateResponse {
  trayek_id: string;
  declared_distance_km: number;
  declared_duration_minutes: number;
  calculated_distance_km: number;
  calculated_duration_minutes: number;
  distance_delta_km: number;
  duration_delta_minutes: number;
  status: TimingValidationStatus;
  rows: Array<{
    sub: string;
    duration_minutes: number;
    distance_km: number | null;
    inferred_distance_km: number | null;
    distance_counted_in_total: boolean;
    speed_mode: SubTrayekSpeedMode;
    calculated_speed_kmh: number | null;
    km_per_second: number | null;
    classification_label: string;
    scheduled_start_time: string | null;
    scheduled_finish_time: string | null;
    cumulative_start_minutes: number | null;
    cumulative_finish_minutes: number | null;
    status: TimingValidationStatus;
    notes: string[];
  }>;
  warnings: string[];
}

export async function validateTimingTable(req: TimingValidateRequest): Promise<TrayekTimingValidation> {
  const resp = await postJson<TimingValidateRequest, TimingValidateResponse>(
    "/v1/validation/timing-table",
    req
  );
  const rows: SubTrayekTimingRow[] = resp.rows.map((row) => ({
    id: `${resp.trayek_id}-${row.sub}`,
    sub: row.sub,
    title: row.sub,
    declaredDistanceKm: row.distance_km,
    inferredDistanceKm: row.inferred_distance_km ?? undefined,
    declaredDurationMinutes: row.duration_minutes,
    distanceCountedInTotal: row.distance_counted_in_total,
    calculatedSpeedKmh: row.calculated_speed_kmh,
    kmPerSecond: row.km_per_second,
    speedMode: row.speed_mode,
    classificationLabel: row.classification_label,
    scheduledStartTime: row.scheduled_start_time ?? "",
    scheduledFinishTime: row.scheduled_finish_time ?? "",
    cumulativeStartMinutes: row.cumulative_start_minutes ?? 0,
    cumulativeFinishMinutes: row.cumulative_finish_minutes ?? 0,
    routeTextExcerpt: "",
    startRawText: null,
    finishRawText: null,
    startStatus: "missing",
    finishStatus: "missing",
    needsUserStart: false,
    needsUserFinish: false,
    status: row.status,
    notes: row.notes,
  }));
  return {
    trayekId: resp.trayek_id,
    declaredDistanceKm: resp.declared_distance_km,
    declaredDurationMinutes: resp.declared_duration_minutes,
    calculatedDistanceKm: resp.calculated_distance_km,
    calculatedDurationMinutes: resp.calculated_duration_minutes,
    distanceDeltaKm: resp.distance_delta_km,
    durationDeltaMinutes: resp.duration_delta_minutes,
    toleranceDistanceKm: req.distance_tolerance_km ?? 0.05,
    toleranceDurationMinutes: req.duration_tolerance_minutes ?? 0,
    status: resp.status,
    rows,
    warnings: resp.warnings,
  };
}
