# Service Worker + PMTiles Fix

Tanggal: 2026-05-22. Akar masalah: service worker meng-intercept request
`bali.pmtiles` lalu memanggil `cache.put()` pada response **206 Partial Content**.
Cache API menolak response 206; SW throw `TypeError: Failed to execute 'put'
on 'Cache': Partial response (status code 206) is unsupported`. Akibatnya
basemap kosong walaupun PMTiles + style URL sudah benar.

## File yang dipasang

| Path | Peran |
|------|-------|
| `apps/web-map-console/public/service-worker.js` | SW v2 - skip PMTiles/Range, skip API `/v1/`, simpan hanya response 200 basic/cors, install tahan-error per-asset. |
| `apps/web-map-console/src/lib/offline/registerServiceWorker.ts` | Dua mode: kill-switch SW lama (default) atau register SW v2 (`VITE_ENABLE_SERVICE_WORKER=true`). |
| `apps/web-map-console/src/vite-env.d.ts` | Tipe untuk `VITE_ENABLE_SERVICE_WORKER`, `VITE_SERVICE_WORKER_PATH`. |

## Aturan SW v2

1. **Method != GET**: lewatkan, jangan respondWith.
2. **`/v1/*`**: lewatkan (langsung jaringan, tidak boleh di-cache).
3. **`.pmtiles` / `.mbtiles` / Header `Range`**: lewatkan.
4. **Cache only**: response 200 dengan `type` `basic` atau `cors`. Opaque dan partial dilewati.
5. **`cache.put()` selalu di-`.catch(() => {})`** sebagai pengaman.
6. **Install app shell**: per-asset try/catch supaya satu 404 tidak menggagalkan install.
7. **Activate**: hapus cache dengan nama yang bukan `time-rally-web-console-v2` agar cache lama hilang.

## Bagaimana mengaktifkan SW v2

Pada `.env.production`:

```dotenv
VITE_ENABLE_SERVICE_WORKER=true
```

Setelah deploy, operator lama akan otomatis:

1. SW lama di-unregister (deteksi scope yang tidak match `/service-worker.js`).
2. Cache yang tidak diawali `time-rally-web-console-v` dihapus.
3. Reload sekali (flag `sessionStorage` mencegah loop).
4. SW v2 didaftarkan.

## Validasi setelah deploy

DevTools → Application → Service Workers:

- Hanya ada SATU SW aktif: `https://<host>/service-worker.js`.
- Cache Storage → hanya `time-rally-web-console-v2`.

DevTools → Network → filter `pmtiles`:

- Status 200 atau 206.
- Header `Range: bytes=...` muncul.
- TIDAK ADA error `Failed to execute 'put' on 'Cache': Partial response`.

DevTools → Console: tidak ada error SW.

## Recovery di sisi operator

Kalau operator masih kena versi SW lama yang sudah ter-cache HTML/JS:

```js
navigator.serviceWorker.getRegistrations()
  .then(rs => rs.forEach(r => r.unregister()));
caches.keys().then(keys => keys.forEach(k => caches.delete(k)));
sessionStorage.clear();
localStorage.clear();
location.reload();
```

Versi `registerServiceWorker.ts` baru otomatis melakukan langkah 1-2 dan reload
sekali. Operator hanya perlu **buka halaman**; tidak perlu jalan snippet manual.

## Hubungan dengan audit PMTiles 2026-05

Bug ini adalah **Bug #5 yang baru ditemukan** setelah audit awal. Audit
sebelumnya menutup 5 bug paralel (vite base path, Dockerfile ARG, hard-code
bucket, SW lama, CORS GCS). SW 206 issue bukan kategori CORS, melainkan
**Cache API semantics** — perlu fix di kode SW, bukan di GCS.

Audit dokumen induk: `docs/implementation/PMTILES_AUDIT_2026_05.md`.
