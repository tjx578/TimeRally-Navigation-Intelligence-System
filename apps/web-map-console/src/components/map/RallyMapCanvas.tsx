import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { fallbackCenter } from "../../lib/map/mapStyle";
import { installPmtilesProtocol, resolveInitialMapStyle } from "../../lib/pmtiles";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

const ROUTE_SOURCE_ID = "active-subtrayek-route";
const ROUTE_LAYER_ID = "active-subtrayek-route-line";
const ROUTE_HALO_LAYER_ID = "active-subtrayek-route-halo";
const WAYPOINT_SOURCE_ID = "active-subtrayek-waypoints";
const WAYPOINT_LAYER_ID = "active-subtrayek-waypoints-circle";
const START_FINISH_SOURCE_ID = "active-subtrayek-start-finish";
const START_FINISH_LAYER_ID = "active-subtrayek-start-finish-circle";
const START_FINISH_LABEL_LAYER_ID = "active-subtrayek-start-finish-label";

const DEBUG_DEMO_ROUTE = import.meta.env.VITE_DEBUG_DEMO_ROUTE === "true";
const DEBUG_SOURCE_ID = "debug-route";
const DEBUG_LAYER_ID = "debug-route-line";

type LngLat = [number, number];

type FeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    properties: Record<string, unknown>;
    geometry:
      | { type: "Point"; coordinates: LngLat }
      | { type: "LineString"; coordinates: LngLat[] };
  }>;
};

type MapStatus =
  | { kind: "loading"; message: string }
  | { kind: "ready" }
  | { kind: "error"; message: string };

function emptyCollection(): FeatureCollection {
  return { type: "FeatureCollection", features: [] };
}

function parseInitialCenter(): { lng: number; lat: number; zoom: number } {
  const lng = Number(import.meta.env.VITE_MAP_CENTER_LNG);
  const lat = Number(import.meta.env.VITE_MAP_CENTER_LAT);
  const zoom = Number(import.meta.env.VITE_MAP_ZOOM);
  return {
    lng: Number.isFinite(lng) ? lng : fallbackCenter.lng,
    lat: Number.isFinite(lat) ? lat : fallbackCenter.lat,
    zoom: Number.isFinite(zoom) ? zoom : fallbackCenter.zoom,
  };
}

export function RallyMapCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const mapModuleRef = useRef<typeof import("maplibre-gl") | null>(null);
  const resizeObserverRef = useRef<ResizeObserver | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [status, setStatus] = useState<MapStatus>({ kind: "loading", message: "Memuat basemap..." });

  const activeRoute = useRallyWorkspaceStore((state) =>
    state.mappedSubTrayeks.find((route) => route.id === state.execution.activeSubTrayekId)
  );

  useEffect(() => {
    let cancelled = false;

    async function initializeMap() {
      if (!containerRef.current || mapRef.current) {
        return;
      }

      const maplibregl = await import("maplibre-gl");
      if (cancelled || !containerRef.current || mapRef.current) {
        return;
      }

      mapModuleRef.current = maplibregl;
      const pmtilesEnabled = installPmtilesProtocol(maplibregl);
      const style = await resolveInitialMapStyle(pmtilesEnabled);
      if (cancelled || !containerRef.current || mapRef.current) {
        return;
      }

      const initialCenter = parseInitialCenter();
      const map = new maplibregl.Map({
        container: containerRef.current,
        style,
        center: [initialCenter.lng, initialCenter.lat],
        zoom: initialCenter.zoom,
        attributionControl: { compact: true },
      });

      mapRef.current = map;

      map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }));
      map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");

      map.on("error", (event) => {
        const message =
          (event as { error?: Error }).error?.message ?? "Gagal memuat tile / style basemap";
        if (!cancelled) {
          setStatus({
            kind: "error",
            message,
          });
        }
      });

      map.on("load", () => {
        if (cancelled) return;
        setMapReady(true);
        setStatus({ kind: "ready" });
        // Saat container baru render, MapLibre kadang masih punya size 0
        // sampai layout grid stabil. Trigger resize manual setelah layout.
        requestAnimationFrame(() => {
          map.resize();
        });
        if (DEBUG_DEMO_ROUTE) {
          installDebugRoute(map);
        }
      });

      // ResizeObserver: kalau workspace berubah layout (mis. panel pindah, mobile),
      // MapLibre wajib di-resize manual supaya canvas mengikuti.
      if (typeof ResizeObserver !== "undefined" && containerRef.current) {
        const observer = new ResizeObserver(() => {
          if (mapRef.current) {
            mapRef.current.resize();
          }
        });
        observer.observe(containerRef.current);
        resizeObserverRef.current = observer;
      }
    }

    void initializeMap().catch((err: unknown) => {
      const message = err instanceof Error ? err.message : String(err);
      setStatus({ kind: "error", message });
    });

    return () => {
      cancelled = true;
      resizeObserverRef.current?.disconnect();
      resizeObserverRef.current = null;
      mapRef.current?.remove();
      mapRef.current = null;
      mapModuleRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const maplibregl = mapModuleRef.current;
    if (!map || !maplibregl || !mapReady) {
      return;
    }

    const renderRoute = () => {
      if (!activeRoute || activeRoute.geometry.length < 2) {
        resetCollection(map, ROUTE_SOURCE_ID);
        resetCollection(map, WAYPOINT_SOURCE_ID);
        resetCollection(map, START_FINISH_SOURCE_ID);
        return;
      }

      const coordinates: LngLat[] = activeRoute.geometry.map(
        (point) => [point.lng, point.lat] as LngLat
      );

      const routeFeature = {
        type: "Feature" as const,
        properties: {
          sub: activeRoute.sub,
          status: activeRoute.mapStatus,
        },
        geometry: {
          type: "LineString" as const,
          coordinates,
        },
      } as Parameters<GeoJSONSource["setData"]>[0];

      ensureLineSource(map, ROUTE_SOURCE_ID, routeFeature);

      if (!map.getLayer(ROUTE_HALO_LAYER_ID)) {
        map.addLayer({
          id: ROUTE_HALO_LAYER_ID,
          type: "line",
          source: ROUTE_SOURCE_ID,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: { "line-color": "#ffffff", "line-width": 12, "line-opacity": 0.55 },
        });
      }

      if (!map.getLayer(ROUTE_LAYER_ID)) {
        map.addLayer({
          id: ROUTE_LAYER_ID,
          type: "line",
          source: ROUTE_SOURCE_ID,
          layout: { "line-join": "round", "line-cap": "round" },
          paint: { "line-color": "#0f766e", "line-width": 8, "line-opacity": 0.92 },
        });
      }

      const intermediates = coordinates.slice(1, coordinates.length - 1);
      ensureGeojsonSource(map, WAYPOINT_SOURCE_ID, {
        type: "FeatureCollection",
        features: intermediates.map((coord, index) => ({
          type: "Feature",
          properties: { kind: "waypoint", sequence: index + 1 },
          geometry: { type: "Point", coordinates: coord },
        })),
      });
      if (!map.getLayer(WAYPOINT_LAYER_ID)) {
        map.addLayer({
          id: WAYPOINT_LAYER_ID,
          type: "circle",
          source: WAYPOINT_SOURCE_ID,
          paint: {
            "circle-radius": 5,
            "circle-color": "#0ea5e9",
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 2,
            "circle-opacity": 0.95,
          },
        });
      }

      const startCoord = coordinates[0];
      const finishCoord = coordinates[coordinates.length - 1];
      ensureGeojsonSource(map, START_FINISH_SOURCE_ID, {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: { kind: "start", label: activeRoute.startLabel ?? "Start" },
            geometry: { type: "Point", coordinates: startCoord },
          },
          {
            type: "Feature",
            properties: { kind: "finish", label: activeRoute.finishLabel ?? "Finish" },
            geometry: { type: "Point", coordinates: finishCoord },
          },
        ],
      });
      if (!map.getLayer(START_FINISH_LAYER_ID)) {
        map.addLayer({
          id: START_FINISH_LAYER_ID,
          type: "circle",
          source: START_FINISH_SOURCE_ID,
          paint: {
            "circle-radius": 8,
            "circle-color": [
              "match",
              ["get", "kind"],
              "start",
              "#16a34a",
              "finish",
              "#dc2626",
              "#1d4ed8",
            ],
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 3,
          },
        });
      }
      if (!map.getLayer(START_FINISH_LABEL_LAYER_ID)) {
        map.addLayer({
          id: START_FINISH_LABEL_LAYER_ID,
          type: "symbol",
          source: START_FINISH_SOURCE_ID,
          layout: {
            "text-field": ["get", "label"],
            "text-size": 11,
            "text-anchor": "top",
            "text-offset": [0, 0.9],
            "text-allow-overlap": false,
          },
          paint: {
            "text-color": "#0f172a",
            "text-halo-color": "#ffffff",
            "text-halo-width": 1.5,
          },
        });
      }

      const bounds = coordinates.reduce(
        (nextBounds, coordinate) => nextBounds.extend(coordinate),
        new maplibregl.LngLatBounds(coordinates[0], coordinates[0])
      );
      map.fitBounds(bounds, { padding: 72, maxZoom: 13.5, duration: 450 });
    };

    if (map.loaded()) {
      renderRoute();
    } else {
      map.once("load", renderRoute);
    }
  }, [activeRoute, mapReady]);

  return (
    <>
      <div className="map-canvas" ref={containerRef} />
      {status.kind === "loading" ? (
        <div className="map-status-banner loading" role="status">
          {status.message}
        </div>
      ) : null}
      {status.kind === "error" ? (
        <div className="map-status-banner error" role="alert">
          Basemap gagal dimuat: {status.message}
        </div>
      ) : null}
      {activeRoute ? (
        <div className="map-route-card">
          <strong>Sub {activeRoute.sub}</strong>
          <span>{activeRoute.startLabel} - {activeRoute.finishLabel}</span>
        </div>
      ) : null}
    </>
  );
}

function ensureLineSource(
  map: MapLibreMap,
  sourceId: string,
  feature: Parameters<GeoJSONSource["setData"]>[0]
) {
  const existing = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (existing) {
    existing.setData(feature);
    return;
  }
  map.addSource(sourceId, { type: "geojson", data: feature });
}

function ensureGeojsonSource(
  map: MapLibreMap,
  sourceId: string,
  collection: FeatureCollection
) {
  const existing = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (existing) {
    existing.setData(collection as Parameters<GeoJSONSource["setData"]>[0]);
    return;
  }
  map.addSource(sourceId, {
    type: "geojson",
    data: collection as Parameters<GeoJSONSource["setData"]>[0],
  });
}

function resetCollection(map: MapLibreMap, sourceId: string) {
  const existing = map.getSource(sourceId) as GeoJSONSource | undefined;
  if (existing) {
    existing.setData(emptyCollection() as Parameters<GeoJSONSource["setData"]>[0]);
  }
}

function installDebugRoute(map: MapLibreMap | null) {
  if (!map) return;
  if (map.getSource(DEBUG_SOURCE_ID)) return;
  map.addSource(DEBUG_SOURCE_ID, {
    type: "geojson",
    data: {
      type: "Feature",
      properties: {},
      geometry: {
        type: "LineString",
        coordinates: [
          [115.2126, -8.6705],
          [115.23, -8.64],
          [115.26, -8.61],
          [115.3, -8.57],
          [115.325, -8.5442],
        ],
      },
    },
  });
  map.addLayer({
    id: DEBUG_LAYER_ID,
    type: "line",
    source: DEBUG_SOURCE_ID,
    layout: { "line-join": "round", "line-cap": "round" },
    paint: { "line-color": "#ff0000", "line-width": 8, "line-opacity": 0.95 },
  });
}
