/* eslint-disable no-restricted-globals */

/**
 * Service worker Time Rally web console.
 *
 * Aturan baku (dipasang setelah audit PMTiles 2026-05):
 *   1. Jangan intercept request method != GET.
 *   2. Jangan intercept request API (`/v1/`) - selalu jalan dari network.
 *   3. JANGAN cache request PMTiles atau request yang punya header `Range`.
 *      `bali.pmtiles` selalu dilayani via HTTP 206 Partial Content - Cache API
 *      menolak `cache.put()` untuk response 206 dan akan crash service worker.
 *   4. Hanya cache response 200 dengan type 'basic'/'cors'; lewati 'opaque' agar
 *      tidak menyimpan response yang tidak bisa diverifikasi.
 *   5. `install` harus tahan banting: kalau satu app-shell asset 404, install
 *      tetap lanjut (logging silent).
 *   6. `activate` membersihkan cache lama dengan nama berbeda.
 */

const CACHE_NAME = "time-rally-web-console-v2";
const APP_SHELL = ["/", "/index.html", "/manifest.webmanifest", "/icon.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(async (cache) => {
      await Promise.all(
        APP_SHELL.map(async (url) => {
          try {
            const response = await fetch(url, { cache: "no-store" });
            if (response.ok) {
              await cache.put(url, response.clone());
            }
          } catch {
            // diam saja: jangan gagalkan install karena satu asset 404
          }
        })
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;

  if (request.method !== "GET") {
    return;
  }

  let url;
  try {
    url = new URL(request.url);
  } catch {
    return;
  }

  // API: biarkan langsung ke jaringan, tidak boleh di-cache oleh SW ini.
  if (url.pathname.startsWith("/v1/")) {
    return;
  }

  // PMTiles dan request dengan Range: jangan disentuh.
  // Response 206 Partial Content TIDAK valid untuk cache.put() sehingga
  // menyentuh kategori ini akan mematahkan loading basemap.
  if (
    url.pathname.endsWith(".pmtiles") ||
    url.pathname.endsWith(".mbtiles") ||
    request.headers.has("range")
  ) {
    return;
  }

  // Layani dari cache kalau ada, kalau tidak fetch network dan simpan kalau aman.
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(request)
        .then((response) => {
          if (!response || response.status !== 200) {
            return response;
          }
          if (response.type !== "basic" && response.type !== "cors") {
            return response;
          }

          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, copy).catch(() => {
              // Cache.put dapat gagal untuk response 206, partial, dsb.
              // Diamkan supaya halaman tidak crash.
            });
          });
          return response;
        })
        .catch(() => caches.match("/index.html"));
    })
  );
});
