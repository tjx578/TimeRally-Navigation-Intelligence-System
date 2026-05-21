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

export const fallbackCenter = {
  lng: 115.216667,
  lat: -8.65,
  zoom: 12
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

