/**
 * Time Rally Field Mobile service worker.
 *
 * Strategy:
 * - precache shell (HTML, JS, CSS, manifest, map style).
 * - cache-first untuk tiles & event yaml.
 * - network-first dengan offline fallback untuk API.
 *
 * Field rule: jangan menghapus cache rally yang sudah dipersiapkan untuk lomba.
 */

const CACHE_VERSION = "time-rally-field-v1";
const SHELL = [
  "/",
  "/index.html",
  "/manifest.webmanifest",
  "/styles.css",
  "/app.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(SHELL))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_VERSION && !key.startsWith("time-rally-event-")) {
            return caches.delete(key);
          }
          return null;
        })
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET") return;

  if (url.pathname.startsWith("/tiles/") || url.pathname.endsWith(".pmtiles") || url.pathname.endsWith(".mbtiles")) {
    event.respondWith(cacheFirst(event.request));
    return;
  }
  if (url.pathname.startsWith("/v1/")) {
    event.respondWith(networkFirst(event.request));
    return;
  }
  event.respondWith(staleWhileRevalidate(event.request));
});

async function cacheFirst(request) {
  const cache = await caches.open("time-rally-tiles");
  const cached = await cache.match(request);
  if (cached) return cached;
  const fresh = await fetch(request);
  if (fresh.ok) cache.put(request, fresh.clone());
  return fresh;
}

async function networkFirst(request) {
  try {
    const fresh = await fetch(request);
    const cache = await caches.open("time-rally-api");
    if (fresh.ok) cache.put(request, fresh.clone());
    return fresh;
  } catch (err) {
    const cache = await caches.open("time-rally-api");
    const cached = await cache.match(request);
    if (cached) return cached;
    return new Response(
      JSON.stringify({ status: "offline", message: "API tidak tersedia, gunakan paket offline." }),
      { status: 503, headers: { "Content-Type": "application/json" } }
    );
  }
}

async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_VERSION);
  const cached = await cache.match(request);
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    })
    .catch(() => cached);
  return cached ?? fetchPromise;
}
