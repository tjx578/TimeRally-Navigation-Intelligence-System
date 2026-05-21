/**
 * Offline Bali map config.
 *
 * Tujuan modul ini: SATU sumber kebenaran untuk endpoint tile, style, dan
 * routing, sehingga komponen MapLibre dan API client tidak perlu membaca
 * `import.meta.env` langsung.
 *
 * Aktivasi:
 *   - Set VITE_OFFLINE_MODE=true di .env.local (atau di build production
 *     untuk image yang akan dipakai di edge node).
 *   - Set VITE_MAP_STYLE_URL ke style.json dari TileServer GL.
 *   - Set VITE_ROUTING_GATEWAY_URL ke routing-gateway lokal.
 *
 * Bali bounding box dipakai untuk:
 *   - membatasi request tiles supaya tidak mengirim ke luar pulau,
 *   - membantu MapLibre fit bounds saat aplikasi pertama load,
 *   - dan menjaga frontend tetap di area lomba.
 */

const env = import.meta.env;

const truthy = (value: string | undefined): boolean => value === "true" || value === "1";

export const BALI_BOUNDS: [number, number, number, number] = [114.4, -8.92, 115.8, -8.02];

export const offlineMapConfig = {
  offlineMode: truthy(env.VITE_OFFLINE_MODE),
  styleUrl: env.VITE_MAP_STYLE_URL ?? null,
  tileJsonUrl: env.VITE_TILEJSON_URL ?? null,
  tileBaseUrl: env.VITE_TILE_BASE_URL ?? null,
  routingGatewayUrl:
    env.VITE_ROUTING_GATEWAY_URL ??
    env.VITE_ROUTING_PUBLIC_BASE ??
    env.VITE_API_BASE_URL ??
    "",
  osrmUrl: env.VITE_OSRM_URL ?? null,
  valhallaUrl: env.VITE_VALHALLA_URL ?? null,
  bounds: BALI_BOUNDS,
  minZoom: 0,
  maxZoom: 15,
} as const;

export type OfflineMapConfig = typeof offlineMapConfig;

/**
 * Bangun MapLibre vector source untuk Bali. Dipakai kalau frontend tidak
 * mengonsumsi style JSON penuh dari TileServer GL.
 */
export function buildBaliVectorSource(): {
  type: "vector";
  tiles: string[];
  bounds: [number, number, number, number];
  minzoom: number;
  maxzoom: number;
  attribution: string;
} | null {
  if (!offlineMapConfig.tileBaseUrl) return null;
  return {
    type: "vector",
    tiles: [`${offlineMapConfig.tileBaseUrl.replace(/\/$/, "")}/data/bali/{z}/{x}/{y}.pbf`],
    bounds: offlineMapConfig.bounds,
    minzoom: offlineMapConfig.minZoom,
    maxzoom: offlineMapConfig.maxZoom,
    attribution: "© OpenStreetMap contributors",
  };
}

/**
 * Pilih routing base URL:
 *   - offline mode: prefer routing-gateway LAN,
 *   - online mode: API base URL umum,
 *   - kosong: fallback ke "/" (proxy Vite di dev).
 */
export function resolveRoutingBase(): string {
  return offlineMapConfig.routingGatewayUrl || "/";
}

/**
 * Pilih style URL final: prioritas styleUrl eksplisit, fallback ke
 * `${tileBaseUrl}/styles/basic/style.json`. Bisa null kalau belum dikonfigurasi.
 */
export function resolveStyleUrl(): string | null {
  if (offlineMapConfig.styleUrl) return offlineMapConfig.styleUrl;
  if (offlineMapConfig.tileBaseUrl) {
    return `${offlineMapConfig.tileBaseUrl.replace(/\/$/, "")}/styles/basic/style.json`;
  }
  return null;
}
