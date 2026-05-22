# Audit: Mengapa Perubahan Tidak Berdampak & PMTiles Tidak Tampil

Tanggal: 2026-05-22. Auditor: explore-data / engineering:debug.

## Ringkasan eksekutif

Dua gejala (frontend tidak update setelah deploy; PMTiles Bali tidak render)
disebabkan oleh **5 bug paralel** di repo. Tiap-tiap bug sudah ditambal di
turn yang sama. Berikut akar masalah dan validasi.

| # | Bug | File | Akibat |
|---|-----|------|--------|
| 1 | `base: "./"` di Vite | `apps/web-map-console/vite.config.ts` | Asset URL relatif. Deep-link / refresh route -> 404 -> halaman "tidak berubah" walau bundle baru. |
| 2 | Dockerfile `ARG VITE_X=""` lalu `ENV VITE_X=$VITE_X` | `apps/web-map-console/Dockerfile` | Vite memprioritaskan ENV shell > `.env.production`. ARG default `""` MENGOVERRIDE konfigurasi yang ditulis `redeploy_web.sh` -> bundle dideploy dengan env kosong. |
| 3 | Style PMTiles hard-code bucket | `apps/web-map-console/public/maps/bali-style.json` | URL `pmtiles://https://storage.googleapis.com/timerally-bali-maps/...` tidak match bucket riil operator -> 404 -> map kosong. |
| 4 | Service worker lama menahan bundle | `apps/web-map-console/src/lib/offline/registerServiceWorker.ts` | Browser memuat HTML/JS lama dari cache SW meskipun image Cloud Run baru. |
| 5 | GCS PMTiles tidak punya CORS / public read | (operasional) | Browser blok request `Range` lintas-origin -> pmtiles handler tidak bisa mendekod -> map blank tanpa error UI. |

## Detail teknis dan validasi fix

### Bug #1 — Vite base path

**Sebelum**: `base: "./"`. Setelah `npm run build`, `dist/index.html` berisi
`<script type="module" src="./assets/index-abc.js">`. Saat browser request
`/some/deep/path`, asset diresolusi relatif jadi `/some/deep/assets/index-abc.js`
-> 404.

**Sesudah**: `base: "/"`. Asset jadi absolut `/assets/index-abc.js` -> selalu
benar untuk SPA di Cloud Run + nginx.

**Validasi**: jalankan `npm run build` lalu `grep src= dist/index.html`. Path
harus dimulai `/assets/...`, BUKAN `./assets/...`.

### Bug #2 — Dockerfile ARG meng-override .env.production

**Sebelum**: Dockerfile punya
```
ARG VITE_MAP_STYLE_URL=""
ENV VITE_MAP_STYLE_URL=$VITE_MAP_STYLE_URL
RUN npm run build
```
Saat `npm run build` jalan, shell `VITE_MAP_STYLE_URL` sudah diset = `""`.
Vite memprioritaskan shell ENV di atas file `.env.production`. Hasilnya
`import.meta.env.VITE_MAP_STYLE_URL` di bundle = `""`, walau `.env.production`
isinya `/maps/bali-style.json`.

**Sesudah**: seluruh blok ARG/ENV VITE_* di Dockerfile dihapus. Sumber tunggal
build = `apps/web-map-console/.env.production` yang ditulis `redeploy_web.sh`
sebelum docker build.

**Validasi**:
```
JS_PATH=$(curl -s "$WEB_URL" | grep -o '/assets/[^"]*\.js' | head -1)
curl -s "$WEB_URL$JS_PATH" | grep -o "bali-style.json\|VITE_MAP_STYLE_URL" | sort -u
```
Harus muncul `bali-style.json` dan `VITE_MAP_STYLE_URL`.

### Bug #3 — Style hard-code bucket

**Sebelum**: `public/maps/bali-style.json` punya URL absolut
`pmtiles://https://storage.googleapis.com/timerally-bali-maps/maps/bali.pmtiles`.
Operator yang bucket-nya `timerally-prod-assets` tidak akan dapat tile.

**Sesudah**: template `public/maps/bali-style.template.json` pakai placeholder
`__PMTILES_URL__`. `redeploy_web.sh` substitute placeholder dari env
`PMTILES_URL` (default `https://storage.googleapis.com/${BUCKET_NAME}/maps/bali.pmtiles`)
sebelum docker build. Output `bali-style.json` di-gitignore.

**Validasi**:
```
curl -s "$WEB_URL/maps/bali-style.json" | grep -o 'pmtiles://[^"]*'
```
Output harus URL yang sesuai bucket Anda, bukan `__PMTILES_URL__`.

### Bug #4 — Service worker lama

**Sebelum**: `registerServiceWorker.ts` empty stub. Browser yang sebelumnya
sempat memuat SW field-mobile `/service-worker.js` tetap memegang precache.

**Sesudah**: bootstrap aktif memanggil `getRegistrations()` -> unregister
semua -> hapus semua `caches` -> reload sekali (flag sessionStorage).

**Validasi**: di browser console: `await navigator.serviceWorker.getRegistrations()`
harus return `[]` setelah halaman dibuka sekali.

### Bug #5 — GCS bucket PMTiles

PMTiles dilayani via HTTP Range request. Tanpa CORS, browser akan menerima
respons tapi memblokir akses ke body karena cross-origin.

**Fix operasional**:
```
PMTILES_LOCAL=/srv/timerally/offline/tiles/bali.pmtiles \
  ./infra/gcp/gcs_pmtiles_setup.sh
```
Script:
- pasang CORS `origin: *, method: GET/HEAD/OPTIONS, exposeHeader: Range, Content-Range, ETag`,
- grant `allUsers` -> `roles/storage.objectViewer`,
- upload `bali.pmtiles` ke `gs://${BUCKET_NAME}/maps/bali.pmtiles`,
- verifikasi HEAD + Range.

## Procedure deploy yang baru

```bash
# 1. Build PMTiles Bali (sekali)
tools/offline-bali/extract.sh
tools/offline-bali/build_tiles.sh

# 2. Convert MBTiles -> PMTiles (kalau perlu). Pakai pmtiles CLI atau go-pmtiles.

# 3. Upload + setup CORS bucket
PMTILES_LOCAL=/srv/timerally/offline/tiles/bali.pmtiles \
  ./infra/gcp/gcs_pmtiles_setup.sh

# 4. Redeploy web (substitute style + tag unik)
./infra/gcp/redeploy_web.sh

# 5. Diagnose
./infra/gcp/check_web_deploy.sh
```

`check_web_deploy.sh` exit 0 + bundle JS punya marker `bali-style.json` +
`/maps/bali-style.json` mengandung URL bucket Anda + curl Range PMTiles OK ->
field test boleh start.

## Pelajaran yang dipetakan ke aturan repo

1. **Jangan pakai `base: "./"` untuk SPA yang dideploy di reverse proxy.**
2. **Jangan deklarasikan `ARG VITE_X=""` di Dockerfile**; biarkan Vite baca dari `.env.production`. Kalau harus override per-build, pass `--build-arg VITE_X=...` eksplisit DAN hapus default `""`.
3. **Style MapLibre yang menunjuk bucket cloud HARUS template + substitute saat build**, bukan hard-code.
4. **Service worker lama wajib aktif dicabut** selama window rollout. SW baru hanya boleh dihidupkan setelah strategi cache versioning siap.
5. **GCS bucket yang dipakai MapLibre WAJIB punya CORS + public read** sebelum field test.

`ops/runbooks/cloud_run_web_redeploy.md` sudah merujuk dokumen ini.
