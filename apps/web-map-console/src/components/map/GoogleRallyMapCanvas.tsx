import { useEffect, useRef, useState } from "react";
import { loadGoogleMaps } from "../../lib/maps/googleMapsLoader";
import { fallbackCenter } from "../../lib/map/mapStyle";
import { useRallyWorkspaceStore } from "../../lib/state/rallyWorkspaceStore";

/**
 * GoogleRallyMapCanvas — alternatif MapLibre untuk skenario online dengan
 * Google Maps JS API. Dipakai untuk validator/route preview, BUKAN basemap
 * offline (lihat docs/implementation/BASEMAP_OPTIONS.md).
 *
 * Loader memakai parameter `loading=async` agar Google tidak mengeluarkan
 * peringatan deprecation di console.
 */

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? "";

type RouteCoord = { lat: number; lng: number };

type MapStatus =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready" }
  | { kind: "error"; message: string };

export function GoogleRallyMapCanvas() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const polylineRef = useRef<google.maps.Polyline | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const [status, setStatus] = useState<MapStatus>({ kind: "idle" });
  const activeRoute = useRallyWorkspaceStore((state) =>
    state.mappedSubTrayeks.find((route) => route.id === state.execution.activeSubTrayekId)
  );

  useEffect(() => {
    let cancelled = false;
    if (!GOOGLE_MAPS_API_KEY) {
      setStatus({
        kind: "error",
        message: "VITE_GOOGLE_MAPS_API_KEY belum diset; basemap Google tidak aktif.",
      });
      return;
    }

    setStatus({ kind: "loading" });
    loadGoogleMaps({ apiKey: GOOGLE_MAPS_API_KEY })
      .then((ns) => {
        if (cancelled || !containerRef.current) return;
        const center = {
          lat: Number(import.meta.env.VITE_MAP_CENTER_LAT) || fallbackCenter.lat,
          lng: Number(import.meta.env.VITE_MAP_CENTER_LNG) || fallbackCenter.lng,
        };
        const zoom = Number(import.meta.env.VITE_MAP_ZOOM) || fallbackCenter.zoom;

        mapRef.current = new ns.maps.Map(containerRef.current, {
          center,
          zoom,
          mapTypeControl: true,
          streetViewControl: false,
          fullscreenControl: false,
        });
        setStatus({ kind: "ready" });
      })
      .catch((err: unknown) => {
        const message = err instanceof Error ? err.message : String(err);
        setStatus({ kind: "error", message });
      });

    return () => {
      cancelled = true;
      polylineRef.current?.setMap(null);
      polylineRef.current = null;
      markersRef.current.forEach((m) => m.setMap(null));
      markersRef.current = [];
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || status.kind !== "ready") return;

    // Bersihkan overlay lama.
    polylineRef.current?.setMap(null);
    polylineRef.current = null;
    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];

    if (!activeRoute || activeRoute.geometry.length < 2) {
      return;
    }

    const path: RouteCoord[] = activeRoute.geometry.map((p) => ({ lat: p.lat, lng: p.lng }));

    polylineRef.current = new google.maps.Polyline({
      path,
      map,
      strokeColor: "#0f766e",
      strokeOpacity: 0.92,
      strokeWeight: 6,
    });

    const start = path[0];
    const finish = path[path.length - 1];
    markersRef.current.push(
      new google.maps.Marker({
        position: start,
        map,
        label: activeRoute.startLabel ?? "S",
      })
    );
    markersRef.current.push(
      new google.maps.Marker({
        position: finish,
        map,
        label: activeRoute.finishLabel ?? "F",
      })
    );
    path.slice(1, -1).forEach((coord, idx) => {
      markersRef.current.push(
        new google.maps.Marker({
          position: coord,
          map,
          label: `${idx + 1}`,
        })
      );
    });

    const bounds = new google.maps.LatLngBounds();
    path.forEach((p) => bounds.extend(p));
    map.fitBounds(bounds, 72);
  }, [activeRoute, status.kind]);

  return (
    <>
      <div className="map-canvas" ref={containerRef} />
      {status.kind === "loading" ? (
        <div className="map-status-banner loading" role="status">
          Memuat Google Maps...
        </div>
      ) : null}
      {status.kind === "error" ? (
        <div className="map-status-banner error" role="alert">
          Google Maps tidak siap: {status.message}
        </div>
      ) : null}
    </>
  );
}
