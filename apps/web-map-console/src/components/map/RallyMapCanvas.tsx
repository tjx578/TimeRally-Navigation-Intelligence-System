import maplibregl from "maplibre-gl";
import { useEffect, useRef } from "react";
import { fallbackCenter } from "../../lib/map/mapStyle";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

export function RallyMapCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const activeRoute = useRallyWorkspaceStore((state) =>
    state.mappedSubTrayeks.find((route) => route.id === state.execution.activeSubTrayekId)
  );

  useEffect(() => {
    if (!containerRef.current || mapRef.current) {
      return;
    }

    mapRef.current = new maplibregl.Map({
      container: containerRef.current,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: { "background-color": "#e5edf6" }
          }
        ]
      },
      center: [fallbackCenter.lng, fallbackCenter.lat],
      zoom: fallbackCenter.zoom
    });

    mapRef.current.addControl(new maplibregl.NavigationControl({ visualizePitch: true }));

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !activeRoute || activeRoute.geometry.length < 2) {
      return;
    }

    const renderRoute = () => {
      const coordinates = activeRoute.geometry.map((point) => [point.lng, point.lat]);
      const routeData = {
        type: "Feature" as const,
        properties: {
          sub: activeRoute.sub,
          status: activeRoute.mapStatus
        },
        geometry: {
          type: "LineString" as const,
          coordinates
        }
      } as Parameters<maplibregl.GeoJSONSource["setData"]>[0];

      const existingSource = map.getSource("active-subtrayek-route") as maplibregl.GeoJSONSource | undefined;
      if (existingSource) {
        existingSource.setData(routeData);
      } else {
        map.addSource("active-subtrayek-route", {
          type: "geojson",
          data: routeData
        });
        map.addLayer({
          id: "active-subtrayek-route-line",
          type: "line",
          source: "active-subtrayek-route",
          paint: {
            "line-color": "#0f766e",
            "line-width": 5,
            "line-opacity": 0.88
          }
        });
      }

      const bounds = coordinates.reduce(
        (nextBounds, coordinate) => nextBounds.extend(coordinate as [number, number]),
        new maplibregl.LngLatBounds(coordinates[0] as [number, number], coordinates[0] as [number, number])
      );
      map.fitBounds(bounds, { padding: 72, maxZoom: 13.5, duration: 450 });
    };

    if (map.loaded()) {
      renderRoute();
    } else {
      map.once("load", renderRoute);
    }
  }, [activeRoute]);

  return (
    <>
      <div className="map-canvas" ref={containerRef} />
      {activeRoute ? (
        <div className="map-route-card">
          <strong>Sub {activeRoute.sub}</strong>
          <span>{activeRoute.startLabel} - {activeRoute.finishLabel}</span>
        </div>
      ) : null}
    </>
  );
}
