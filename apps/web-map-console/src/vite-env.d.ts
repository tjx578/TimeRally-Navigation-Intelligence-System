/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_SUPABASE_URL?: string;
  readonly VITE_SUPABASE_ANON_KEY?: string;
  readonly VITE_PMTILES_URL?: string;
  readonly VITE_ROUTING_PUBLIC_BASE?: string;
  readonly VITE_SENTRY_DSN?: string;
  readonly VITE_SENTRY_ENVIRONMENT?: string;
  readonly VITE_SENTRY_TRACES_SAMPLE_RATE?: string;
  // Offline Bali endpoints (lihat .env.local.example)
  readonly VITE_OFFLINE_MODE?: string;
  readonly VITE_MAP_STYLE_URL?: string;
  readonly VITE_MAP_CENTER_LNG?: string;
  readonly VITE_MAP_CENTER_LAT?: string;
  readonly VITE_MAP_ZOOM?: string;
  readonly VITE_TILEJSON_URL?: string;
  readonly VITE_TILE_BASE_URL?: string;
  readonly VITE_ROUTING_GATEWAY_URL?: string;
  readonly VITE_OSRM_URL?: string;
  readonly VITE_VALHALLA_URL?: string;
  // Debug toggle: pasang demo LineString merah supaya operator bisa cek layer line saat smoke test.
  readonly VITE_DEBUG_DEMO_ROUTE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
