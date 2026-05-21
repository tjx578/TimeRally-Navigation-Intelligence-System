import {
  BALI_BOUNDS,
  buildBaliVectorSource,
  offlineMapConfig,
  resolveStyleUrl,
} from "../../config/offlineMap";

/**
 * Style fallback statis (PMTiles minimal) kalau TileServer GL belum tersedia.
 * Tetap dipertahankan untuk skenario online cloud + PMTiles.
 */
export const offlineMapStyle = {
  version: 8,
  sources: {
    "offline-tiles": {
      type: "vector",
      url: "pmtiles://offline-map.pmtiles"
    }
  },
  layers: [
    {
      id: "background",
      type: "background",
      paint: {
        "background-color": "#eef2f7"
      }
    }
  ]
};

function numberFromEnv(value: string | undefined, fallback: number) {
  if (!value) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export const fallbackCenter = {
  lng: numberFromEnv(import.meta.env.VITE_MAP_CENTER_LNG, 115.216667),
  lat: numberFromEnv(import.meta.env.VITE_MAP_CENTER_LAT, -8.65),
  zoom: numberFromEnv(import.meta.env.VITE_MAP_ZOOM, 12),
};

export const baliBounds = BALI_BOUNDS;

/**
 * Tentukan style yang dipakai MapLibre:
 *   1. Kalau VITE_MAP_STYLE_URL diset, pakai sebagai URL eksternal.
 *   2. Kalau VITE_TILE_BASE_URL diset, bangun source vector "bali" inline.
 *   3. Fallback ke `offlineMapStyle` (PMTiles).
 *
 * Output bisa langsung diumpan ke `new maplibregl.Map({ style })`.
 */
export function resolveMapStyle(): string | typeof offlineMapStyle | {
  version: number;
  sources: Record<string, unknown>;
  layers: Array<Record<string, unknown>>;
} {
  const styleUrl = resolveStyleUrl();
  if (styleUrl) return styleUrl;

  const vector = buildBaliVectorSource();
  if (vector) {
    return {
      version: 8,
      sources: {
        bali: vector,
      },
      layers: [
        {
          id: "background",
          type: "background",
          paint: { "background-color": "#eef2f7" },
        },
        {
          id: "bali-roads",
          type: "line",
          source: "bali",
          "source-layer": "transportation",
          paint: { "line-color": "#5b6770", "line-width": 1.0 },
        },
      ],
    };
  }

  return offlineMapStyle;
}

export { offlineMapConfig };
