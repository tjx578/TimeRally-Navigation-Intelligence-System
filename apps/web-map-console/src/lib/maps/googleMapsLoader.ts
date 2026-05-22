/**
 * Google Maps JavaScript API loader.
 *
 * Catatan utama dari peringatan Google "Google Maps JavaScript API has been
 * loaded directly without loading=async": script tag <script> WAJIB punya
 * parameter `loading=async` di URL, dan diberi atribut `async` pada tag.
 *
 * Loader ini:
 *   1. Memastikan script Google Maps hanya dimuat SEKALI per halaman.
 *   2. Memakai parameter loading=async + atribut async + defer di tag <script>.
 *   3. Mengembalikan Promise<google.maps> yang resolve setelah script + callback
 *      siap, sehingga component bisa menunggu tanpa pasang sendiri global callback.
 */

declare global {
  interface Window {
    __timeRallyGoogleMapsLoader__?: Promise<typeof google>;
    initTimeRallyGoogleMap?: () => void;
  }
}

export interface GoogleMapsLoaderOptions {
  apiKey: string;
  libraries?: ReadonlyArray<"places" | "geometry" | "drawing" | "visualization" | "marker">;
  language?: string;
  region?: string;
  /** Endpoint resmi Google Maps. Jangan diubah kecuali untuk testing. */
  endpoint?: string;
}

const DEFAULT_LIBRARIES = ["places", "geometry"] as const;
const DEFAULT_ENDPOINT = "https://maps.googleapis.com/maps/api/js";

function buildSrc(options: GoogleMapsLoaderOptions): string {
  const params = new URLSearchParams();
  params.set("key", options.apiKey);
  params.set("libraries", (options.libraries ?? DEFAULT_LIBRARIES).join(","));
  params.set("loading", "async");
  params.set("callback", "initTimeRallyGoogleMap");
  if (options.language) params.set("language", options.language);
  if (options.region) params.set("region", options.region);
  return `${options.endpoint ?? DEFAULT_ENDPOINT}?${params.toString()}`;
}

export function loadGoogleMaps(options: GoogleMapsLoaderOptions): Promise<typeof google> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("Google Maps loader hanya berjalan di browser"));
  }
  if (!options.apiKey) {
    return Promise.reject(new Error("VITE_GOOGLE_MAPS_API_KEY belum diset"));
  }

  if (window.__timeRallyGoogleMapsLoader__) {
    return window.__timeRallyGoogleMapsLoader__;
  }

  const promise = new Promise<typeof google>((resolve, reject) => {
    // Callback global wajib karena URL menyertakan callback=initTimeRallyGoogleMap.
    window.initTimeRallyGoogleMap = () => {
      const ns = (window as unknown as { google?: typeof google }).google;
      if (ns?.maps) {
        resolve(ns);
      } else {
        reject(new Error("Google Maps callback dipanggil tetapi google.maps tidak tersedia"));
      }
    };

    const existing = document.querySelector<HTMLScriptElement>(
      "script[data-time-rally-google-maps]"
    );
    if (existing) {
      // Script sudah ada dari load sebelumnya - tunggu callback eksisting.
      return;
    }

    const script = document.createElement("script");
    script.src = buildSrc(options);
    script.async = true;
    script.defer = true;
    script.dataset.timeRallyGoogleMaps = "true";
    script.onerror = () => reject(new Error("Gagal memuat script Google Maps"));
    document.head.appendChild(script);
  });

  window.__timeRallyGoogleMapsLoader__ = promise;
  return promise;
}
