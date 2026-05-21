/**
 * Validation feature.
 *
 * Membungkus panggilan POST /v1/validation/route dan /v1/validation/timing-table,
 * lalu mengubah respons menjadi struktur UI yang siap dirender.
 */

import { postJson } from "../../lib/api/client";
import type { ValidationSummary } from "../../types/rally";

export interface ValidateRouteRequest {
  target_distance_km: number;
  target_time_minutes: number;
  calculated_distance_km: number;
  calculated_time_minutes: number;
  chaining_gap_meters?: number;
}

export interface ValidateRouteResponse {
  distance_status: "compliant" | "warning" | "violation" | "unchecked";
  time_status: "compliant" | "warning" | "violation" | "unchecked";
  chaining_status: "compliant" | "warning" | "violation" | "unchecked";
  score: number;
  warnings: string[];
}

export async function validateRoute(req: ValidateRouteRequest): Promise<ValidateRouteResponse> {
  return postJson<ValidateRouteRequest, ValidateRouteResponse>("/v1/validation/route", req);
}

export function toValidationSummary(resp: ValidateRouteResponse): ValidationSummary {
  const downgrade = (s: ValidateRouteResponse["distance_status"]) =>
    s === "unchecked" ? "warning" : (s as "compliant" | "warning" | "violation");
  return {
    distanceStatus: downgrade(resp.distance_status),
    timeStatus: downgrade(resp.time_status),
    chainingStatus: downgrade(resp.chaining_status),
    score: resp.score,
  };
}

export function severityColor(
  status: "compliant" | "warning" | "violation" | "unchecked"
): string {
  switch (status) {
    case "compliant":
      return "#2e7d32";
    case "warning":
      return "#f9a825";
    case "violation":
      return "#c62828";
    default:
      return "#757575";
  }
}
