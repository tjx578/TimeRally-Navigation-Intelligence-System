import type { StyleSpecification } from "maplibre-gl";
import { Protocol } from "pmtiles";

type MapLibreProtocolHost = {
  addProtocol?: unknown;
};

let pmtilesProtocolInstalled = false;

function truthy(value: string | undefined) {
  return value === "true" || value === "1";
}

export function getPmtilesUrl() {
  return import.meta.env.VITE_PMTILES_URL ?? "";
}

export function isPmtilesReady() {
  return truthy(import.meta.env.VITE_PMTILES_READY);
}

export function getMapStyleUrl() {
  return import.meta.env.VITE_MAP_STYLE_URL ?? "";
}

export function getMapFallbackStyleUrl() {
  return import.meta.env.VITE_MAP_FALLBACK_STYLE_URL ?? "";
}

export function installPmtilesProtocol(maplibre: MapLibreProtocolHost) {
  const addProtocol = maplibre.addProtocol as
    | ((scheme: string, handler: unknown) => void)
    | undefined;
  if (!addProtocol) {
    return false;
  }

  if (!pmtilesProtocolInstalled) {
    const protocol = new Protocol();
    addProtocol("pmtiles", protocol.tile);
    pmtilesProtocolInstalled = true;
  }
  return true;
}

/** Demo style publik MapLibre, dipakai untuk dev kalau env belum dikonfigurasi. */
const DEMO_MAPLIBRE_STYLE = "https://demotiles.maplibre.org/style.json";

async function canLoadUrl(url: string, options: RequestInit = {}): Promise<boolean> {
  try {
    const response = await fetch(url, {
      method: "HEAD",
      cache: "no-store",
      mode: "cors",
      ...options
    });
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Pilih style MapLibre dengan urutan fallback:
 *
 *   1. VITE_MAP_STYLE_URL (TileServer GL / MapTiler / MapLibre style.json) jika reachable.
 *   2. PMTiles inline style kalau VITE_PMTILES_URL hidup atau VITE_PMTILES_READY=true.
 *   3. VITE_MAP_FALLBACK_STYLE_URL kalau di-set.
 *   4. Demo MapLibre publik (butuh internet umum).
 *   5. OSM raster.
 *
 * Tujuannya: jangan biarkan map kosong gara-gara satu URL salah.
 */
export async function resolveInitialMapStyle(usePmtiles: boolean): Promise<StyleSpecification | string> {
  const mapStyleUrl = getMapStyleUrl();
  const pmtilesUrl = getPmtilesUrl();
  const fallbackStyleUrl = getMapFallbackStyleUrl();

  if (mapStyleUrl && (await canLoadUrl(mapStyleUrl))) {
    return mapStyleUrl;
  }

  if (usePmtiles && pmtilesUrl) {
    const ready = isPmtilesReady() || (await canLoadUrl(pmtilesUrl, { headers: { Range: "bytes=0-0" } }));
    if (ready) {
      return buildPmtilesStyle(pmtilesUrl);
    }
  }

  if (fallbackStyleUrl) {
    return fallbackStyleUrl;
  }

  if (await canLoadUrl(DEMO_MAPLIBRE_STYLE)) {
    return DEMO_MAPLIBRE_STYLE;
  }

  return buildOnlineRasterFallbackStyle();
}

export function buildPmtilesStyle(pmtilesUrl: string): StyleSpecification {
  const url = pmtilesUrl.startsWith("pmtiles://") ? pmtilesUrl : `pmtiles://${pmtilesUrl}`;
  return {
    version: 8,
    sources: {
      "offline-tiles": {
        type: "vector",
        url
      }
    },
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#e5edf6" }
      },
      {
        id: "landcover",
        type: "fill",
        source: "offline-tiles",
        "source-layer": "landcover",
        paint: { "fill-color": "#d9edc2", "fill-opacity": 0.72 }
      },
      {
        id: "landuse",
        type: "fill",
        source: "offline-tiles",
        "source-layer": "landuse",
        paint: { "fill-color": "#d1e8bd", "fill-opacity": 0.64 }
      },
      {
        id: "water",
        type: "fill",
        source: "offline-tiles",
        "source-layer": "water",
        paint: { "fill-color": "#a8d8f0" }
      },
      {
        id: "buildings",
        type: "fill",
        source: "offline-tiles",
        "source-layer": "building",
        minzoom: 13,
        paint: { "fill-color": "#d6cbc0", "fill-opacity": 0.72 }
      },
      {
        id: "roads-casing",
        type: "line",
        source: "offline-tiles",
        "source-layer": "transportation",
        paint: {
          "line-color": "#ffffff",
          "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.8, 13, 4.5],
          "line-opacity": 0.9
        }
      },
      {
        id: "roads",
        type: "line",
        source: "offline-tiles",
        "source-layer": "transportation",
        paint: {
          "line-color": "#60717d",
          "line-width": ["interpolate", ["linear"], ["zoom"], 8, 0.45, 13, 2.4],
          "line-opacity": 0.88
        }
      }
    ]
  } as StyleSpecification;
}

/**
 * Versi sinkron untuk caller yang sudah tahu state PMTiles-nya
 * (mis. service worker). Lebih sederhana dari `resolveInitialMapStyle`.
 */
export function buildOfflineStyle(usePmtiles: boolean): StyleSpecification | string {
  const mapStyleUrl = getMapStyleUrl();
  if (mapStyleUrl) {
    return mapStyleUrl;
  }
  const pmtilesUrl = getPmtilesUrl();
  if (usePmtiles && pmtilesUrl) {
    return buildPmtilesStyle(pmtilesUrl);
  }
  return buildOnlineRasterFallbackStyle();
}

export function buildOnlineRasterFallbackStyle(): StyleSpecification {
  return {
    version: 8,
    sources: {
      osm: {
        type: "raster",
        tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution: "© OpenStreetMap contributors"
      }
    },
    layers: [
      {
        id: "background",
        type: "background",
        paint: { "background-color": "#e5edf6" }
      },
      {
        id: "osm-raster",
        type: "raster",
        source: "osm",
        paint: { "raster-opacity": 0.96 }
      }
    ]
  } as StyleSpecification;
}
