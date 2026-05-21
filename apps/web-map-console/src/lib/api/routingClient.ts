/**
 * Routing API client.
 *
 * Default memanggil API utama (`VITE_API_BASE_URL`) via path `/v1/routing/route`.
 * Saat mode offline (VITE_OFFLINE_MODE=true) dan VITE_ROUTING_GATEWAY_URL diset,
 * client akan memforward request langsung ke gateway di edge node sehingga
 * latency lebih rendah dan tidak melewati API rally yang mungkin ditujukan
 * untuk parser/validation/export.
 */

import { offlineMapConfig } from "../../config/offlineMap";

export type RoutingProvider = "auto" | "valhalla" | "osrm" | "graphhopper" | "google" | "mock";

export interface RoutingWaypoint {
  id: string;
  name: string;
  coordinate: { lat: number; lng: number };
}

export interface RoutingRequest {
  provider?: RoutingProvider;
  profile?: string;
  allow_reorder?: boolean;
  waypoints: RoutingWaypoint[];
}

export interface RoutingResponse {
  provider: RoutingProvider;
  legs: Array<{
    from_waypoint: string;
    to_waypoint: string;
    distance_m: number;
    duration_s: number;
    provider: RoutingProvider;
    status: string;
  }>;
  total_distance_m: number;
  total_duration_s: number;
  status: string;
}

function resolveBase(): string {
  if (offlineMapConfig.offlineMode && offlineMapConfig.routingGatewayUrl) {
    return offlineMapConfig.routingGatewayUrl.replace(/\/$/, "");
  }
  const apiBase = import.meta.env.VITE_API_BASE_URL ?? "";
  return apiBase.replace(/\/$/, "");
}

export async function postRoute(request: RoutingRequest): Promise<RoutingResponse> {
  const base = resolveBase();
  // Gateway dan API rally sama-sama eksposes /v1/routing/route.
  const url = `${base}/v1/routing/route`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      provider: request.provider ?? "auto",
      profile: request.profile ?? "rally_car",
      allow_reorder: request.allow_reorder ?? false,
      waypoints: request.waypoints,
    }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`routing failed ${response.status}: ${detail}`);
  }
  return response.json() as Promise<RoutingResponse>;
}
