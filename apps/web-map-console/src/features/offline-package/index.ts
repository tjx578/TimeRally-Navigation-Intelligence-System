/**
 * Offline package feature.
 *
 * Mendaftarkan service worker, mengelola cache MapLibre style, dan menyiapkan
 * paket peta PMTiles agar field-mobile bisa bekerja tanpa internet.
 */

export interface OfflinePackageStatus {
  hasStyle: boolean;
  hasTiles: boolean;
  cachedRouteCount: number;
  warning?: string;
}

const STORAGE_KEY = "time-rally.offline.cached-route-ids";

export function listCachedRoutes(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function rememberCachedRoute(eventId: string): void {
  if (typeof window === "undefined") return;
  const current = new Set(listCachedRoutes());
  current.add(eventId);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(current)));
}

export function forgetCachedRoute(eventId: string): void {
  if (typeof window === "undefined") return;
  const current = new Set(listCachedRoutes());
  current.delete(eventId);
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(Array.from(current)));
}

export async function probeOfflinePackage(styleUrl: string, tilesUrl: string): Promise<OfflinePackageStatus> {
  let hasStyle = false;
  let hasTiles = false;
  let warning: string | undefined;
  try {
    const r1 = await fetch(styleUrl, { method: "HEAD" });
    hasStyle = r1.ok;
  } catch {
    warning = "style.json tidak dapat diakses";
  }
  try {
    const r2 = await fetch(tilesUrl, { method: "HEAD" });
    hasTiles = r2.ok;
  } catch {
    warning = (warning ?? "") + " | tiles tidak dapat diakses";
  }
  return {
    hasStyle,
    hasTiles,
    cachedRouteCount: listCachedRoutes().length,
    warning,
  };
}
