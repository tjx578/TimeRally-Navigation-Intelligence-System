/**
 * Missing waypoint review feature.
 *
 * Membungkus /v1/probability/infer-missing-waypoint dan formatter UI.
 */

import { postJson } from "../../lib/api/client";
import type { ProbabilityRouteOption } from "../../types/rally";

export interface InferRequest {
  event_id?: string;
  context: {
    missing_waypoint_text: string;
    previous_waypoint_id: string;
    next_waypoint_id: string;
    target_distance_km?: number;
    target_time_seconds?: number;
    navigation_action?: string;
    landmark_type_hint?: string;
  };
  max_candidates?: number;
}

export interface InferResponse {
  missing_waypoint_text: string;
  recommended_candidate_id: string | null;
  candidates: Array<{
    id: string;
    label: string;
    coordinate?: { lat: number; lng: number };
    confidence: number;
    distance_deviation_percent: number;
    time_deviation_seconds: number;
    route_corridor_fit: number;
    landmark_fit: number;
    turn_geometry_fit: number;
    provider: string;
    reasons: string[];
    status: string;
  }>;
  status: string;
}

export async function inferMissing(req: InferRequest): Promise<InferResponse> {
  return postJson<InferRequest, InferResponse>("/v1/probability/infer-missing-waypoint", req);
}

export function toProbabilityOptions(resp: InferResponse): ProbabilityRouteOption[] {
  return resp.candidates.map((c) => ({
    id: c.id,
    label: c.label,
    missingWaypointLabel: resp.missing_waypoint_text,
    confidence: c.confidence,
    distanceDeviationPercent: c.distance_deviation_percent,
    timeDeviationSeconds: c.time_deviation_seconds,
    routeCorridorFit: c.route_corridor_fit,
    landmarkFit: c.landmark_fit,
    turnGeometryFit: c.turn_geometry_fit,
    provider: c.provider,
    status:
      c.status === "auto_select_inferred"
        ? "recommended"
        : c.status === "needs_confirmation"
        ? "review"
        : "rejected",
    reasons: c.reasons,
  }));
}

export function confidenceBadge(confidence: number): "high" | "medium" | "low" {
  if (confidence >= 0.85) return "high";
  if (confidence >= 0.7) return "medium";
  return "low";
}
