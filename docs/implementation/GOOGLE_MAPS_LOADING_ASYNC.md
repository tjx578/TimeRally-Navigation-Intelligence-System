# Google Maps JS API: `loading=async` Fix

Tanggal: 2026-05-22. Warning yang ditampilkan oleh Google di console:

```
Google Maps JavaScript API has been loaded directly without loading=async.
```

Bukan error fatal — script Google Maps tetap load. Tapi tanpa `loading=async`,
script memblokir thread main saat parsing dan akan berhenti didukung pada
rilis Maps mendatang.

## File yang dipasang

| Path | Peran |
|------|-------|
| `apps/web-map-console/src/lib/maps/googleMapsLoader.ts` | Loader async + dedupe. URL selalu menyertakan `loading=async`, tag `<script>` punya atribut `async` + `defer`. Promise di-cache di `window.__timeRallyGoogleMapsLoader__` sehingga `loadGoogleMaps()` aman dipanggil berkali-kali. |
| `apps/web-map-console/src/components/map/GoogleRallyMapCanvas.tsx` | Komponen MapCanvas alternatif berbasis `google.maps.Map`. Memakai loader di atas. Dipakai opsional untuk skenario validator/preview online. |
| `apps/web-map-console/src/vite-env.d.ts` | Tipe `VITE_GOOGLE_MAPS_API_KEY`. |
| `apps/web-map-console/tsconfig.json` | `types: ["google.maps", "vite/client"]` agar `google.maps.*` ter-resolve dari `@types/google.maps`. |
| `apps/web-map-console/package.json` | Tambah `@types/google.maps` devDependency. |

## URL script yang dibangun

```
https://maps.googleapis.com/maps/api/js
  ?key=...
  &libraries=places,geometry
  &loading=async
  &callback=initTimeRallyGoogleMap
```

Plus tag:

```html
<script src="..." async defer data-time-rally-google-maps="true"></script>
```

## Kapan dipakai

- **Default**: MapLibre + PMTiles (`RallyMapCanvas`).
- **Validator/preview online**: `GoogleRallyMapCanvas`. Aktifkan dengan
  mengganti import komponen map di `WorkspaceShell.tsx` ke
  `GoogleRallyMapCanvas`, lalu set `VITE_GOOGLE_MAPS_API_KEY` di
  `.env.production`.

`docs/implementation/BASEMAP_OPTIONS.md` masih mendiktekan bahwa Google Maps
bukan basemap offline; komponen ini khusus skenario online.

## Verifikasi setelah deploy

1. DevTools → Console. Warning "loaded without loading=async" **hilang**.
2. DevTools → Network → filter `maps.googleapis.com`. Request `js?key=...`
   muncul **dengan** parameter `loading=async`.
3. Element inspector pada tag `<script>` yang baru: `async` dan `defer`
   ada, plus atribut `data-time-rally-google-maps="true"`.
4. `window.__timeRallyGoogleMapsLoader__` adalah Promise resolved.

## Catatan keamanan

- `VITE_GOOGLE_MAPS_API_KEY` adalah public key. Wajib batasi di Google Cloud
  Console:
  - **HTTP referrer** allowlist: `https://timerally-web-*.run.app/*`, custom
    domain Cloud Run, dan `localhost:5173` untuk dev.
  - **API restrictions**: hanya Maps JavaScript API + Places API + Routes API
    sesuai kebutuhan.
- JANGAN pakai key yang sama dengan `GOOGLE_MAPS_API_KEY` server-side
  (routing-gateway). Server-side key berhak akses Directions/Routes server
  dan tidak boleh diekspos ke browser.

## Hubungan dengan audit lain

- `PMTILES_AUDIT_2026_05.md`: warning ini bukan kategori PMTiles, tapi
  Maps SDK loading. Tetap saya catat di dokumen audit terpisah karena
  perbaikannya independen.
- `SERVICE_WORKER_PMTILES_FIX.md`: SW v2 sudah mem-bypass request ke
  `maps.googleapis.com` (bukan PMTiles, bukan API rally, bukan asset
  basic/cors `/`), jadi tidak ada konflik.
