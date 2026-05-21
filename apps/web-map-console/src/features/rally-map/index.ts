/**
 * Rally map feature.
 *
 * Helper untuk membangun GeoJSON FeatureCollection dari workspace store
 * dan menentukan style layer MapLibre.
 */

import type { Coordinate, RoadbookLeg, Waypoint } from "../../types/rally";

export interface RallyFeatureCollection {
  type: "FeatureCollection";
  features: Array<
    | {
        type: "Feature";
        geometry: { type: "Point"; coordinates: [number, number] };
        properties: Record<string, unknown> & { kind: "waypoint" };
      }
    | {
        type: "Feature";
        geometry: { type: "LineString"; coordinates: [number, number][] };
        properties: Record<string, unknown> & { kind: "segment" };
      }
  >;
}

export function buildRallyFeatureCollection(
  waypoints: Waypoint[],
  legGeometries?: Array<{ legId: string; coords: Coordinate[] }>
): RallyFeatureCollection {
  const features: RallyFeatureCollection["features"] = [];
  waypoints.forEach((wp) => {
    if (!wp.coordinate) return;
    features.push({
      type: "Feature",
      geometry: { type: "Point", coordinates: [wp.coordinate.lng, wp.coordinate.lat] },
      properties: {
        id: wp.id,
        label: wp.label,
        status: wp.status,
        confidence: wp.confidence,
        kind: "waypoint",
      },
    });
  });
  legGeometries?.forEach((leg) => {
    if (leg.coords.length < 2) return;
    features.push({
      type: "Feature",
      geometry: {
        type: "LineString",
        coordinates: leg.coords.map((c) => [c.lng, c.lat] as [number, number]),
      },
      properties: { id: leg.legId, kind: "segment" },
    });
  });
  return { type: "FeatureCollection", features };
}

export function computeFitBounds(waypoints: Waypoint[]): [[number, number], [number, number]] | null {
  const valid = waypoints.filter((w): w is Waypoint & { coordinate: Coordinate } => !!w.coordinate);
  if (valid.length === 0) return null;
  let minLat = Infinity;
  let maxLat = -Infinity;
  let minLng = Infinity;
  let maxLng = -Infinity;
  valid.forEach((w) => {
    minLat = Math.min(minLat, w.coordinate.lat);
    maxLat = Math.max(maxLat, w.coordinate.lat);
    minLng = Math.min(minLng, w.coordinate.lng);
    maxLng = Math.max(maxLng, w.coordinate.lng);
  });
  return [
    [minLng, minLat],
    [maxLng, maxLat],
  ];
}

export function legColor(leg: RoadbookLeg): string {
  switch (leg.status) {
    case "ok":
      return "#1976d2";
    case "warning":
      return "#f9a825";
    case "violation":
      return "#c62828";
  }
}
