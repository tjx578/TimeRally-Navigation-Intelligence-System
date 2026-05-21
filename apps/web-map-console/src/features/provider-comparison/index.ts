/**
 * Provider comparison feature.
 *
 * Memanggil routing-gateway dengan beberapa provider sekaligus
 * dan menyajikan rangkuman delta jarak/waktu.
 */

import { postJson } from "../../lib/api/client";

export type ProviderName = "valhalla" | "osrm" | "graphhopper" | "google" | "mock";

interface CompareWaypoint {
  id: string;
  name: string;
  coordinate: { lat: number; lng: number };
}

export interface ProviderRouteResult {
  provider: ProviderName;
  totalDistanceM: number;
  totalDurationS: number;
  warnings: string[];
  legs: Array<{
    from_waypoint: string;
    to_waypoint: string;
    distance_m: number;
    duration_s: number;
    provider: ProviderName;
    status: string;
  }>;
}

interface RouteApiResp {
  provider: ProviderName;
  legs: Array<{
    from_waypoint: string;
    to_waypoint: string;
    distance_m: number;
    duration_s: number;
    provider: ProviderName;
    status: string;
  }>;
  total_distance_m: number;
  total_duration_s: number;
  status: string;
}

async function callProvider(
  waypoints: CompareWaypoint[],
  provider: ProviderName
): Promise<ProviderRouteResult> {
  const resp = await postJson<unknown, RouteApiResp>("/v1/routing/route", {
    provider,
    profile: "rally_car",
    allow_reorder: false,
    waypoints,
  });
  return {
    provider,
    totalDistanceM: resp.total_distance_m,
    totalDurationS: resp.total_duration_s,
    warnings: resp.status === "ok" ? [] : [resp.status],
    legs: resp.legs,
  };
}

export async function compareProviders(
  waypoints: CompareWaypoint[],
  providers: ProviderName[] = ["valhalla", "osrm"]
): Promise<ProviderRouteResult[]> {
  return Promise.all(providers.map((p) => callProvider(waypoints, p)));
}

export function summarizeSpread(results: ProviderRouteResult[]): {
  distanceSpreadM: number;
  durationSpreadS: number;
  agreement: "tight" | "moderate" | "loose";
} {
  if (results.length === 0) return { distanceSpreadM: 0, durationSpreadS: 0, agreement: "tight" };
  const d = results.map((r) => r.totalDistanceM);
  const t = results.map((r) => r.totalDurationS);
  const distanceSpread = Math.max(...d) - Math.min(...d);
  const durationSpread = Math.max(...t) - Math.min(...t);
  const denom = Math.max(...d) || 1;
  const ratio = distanceSpread / denom;
  const agreement: "tight" | "moderate" | "loose" =
    ratio < 0.05 ? "tight" : ratio < 0.15 ? "moderate" : "loose";
  return { distanceSpreadM: distanceSpread, durationSpreadS: durationSpread, agreement };
}
