# Runbook: Redeploy & Verify Cloud Run `timerally-web`

Gunakan ini setiap kali ada perubahan UI / style / PMTiles yang harus dilihat
operator. Mengatasi pola lama "image latest cached, deploy tidak terlihat".

## Akar masalah yang dicegah

1. Cloud Run reuse image lama karena tag tidak unik.
2. Build frontend tidak membawa `.env.production` baru sehingga style URL salah.
3. Browser punya Service Worker / Cache Storage lama yang menahan bundle lama.
4. `index.html` di-cache oleh browser atau nginx.
5. Reverse proxy `/v1/` belum di-include.

## Komponen yang sudah dipasang di repo

| File | Peran |
|------|-------|
| `apps/web-map-console/public/maps/bali-style.json` | Style MapLibre Bali (ikut ter-copy ke `dist/` lewat folder `public/`). |
| `apps/web-map-console/nginx.conf` | Proxy `/v1/` ke API + no-cache untuk `index.html` + no-store untuk style + immutable untuk `/assets/`. |
| `apps/web-map-console/src/lib/offline/registerServiceWorker.ts` | **Kill-switch**: unregister SW lama + bersihkan Cache Storage + reload sekali. |
| `apps/web-map-console/index.html` | Meta `Cache-Control: no-cache, no-store, must-revalidate`. |
| `infra/gcp/redeploy_web.sh` | Build + push image dengan TAG = timestamp UTC, lalu `gcloud run deploy --image` + `update-traffic --to-latest`. |
| `infra/gcp/check_web_deploy.sh` | Diagnose: revision aktif, `/maps/bali-style.json`, asset JS terbaru, marker env, `/v1/healthz`. |

## Quick procedure

```bash
# 0. Pastikan .env.gcp punya PROJECT_ID, REGION, BUCKET_NAME.
cp .env.gcp.example .env.gcp   # kalau belum
# edit .env.gcp

# 1. Redeploy
./infra/gcp/redeploy_web.sh

# 2. Diagnose
./infra/gcp/check_web_deploy.sh
```

`check_web_deploy.sh` exit 0 = hijau, exit 1 = ada marker yang belum lulus.
Periksa pesan "FAIL ..." di akhir.

## Manual fallback (kalau script tidak tersedia)

```bash
TAG=$(date +%Y%m%d%H%M%S)
WEB_URL=$(gcloud run services describe timerally-web \
  --region asia-southeast2 --format='value(status.url)')

# Build & push image baru
gcloud builds submit \
  --tag "asia-southeast2-docker.pkg.dev/$PROJECT_ID/timerally/web:$TAG" \
  -f apps/web-map-console/Dockerfile .

# Deploy + shift traffic
gcloud run deploy timerally-web \
  --image "asia-southeast2-docker.pkg.dev/$PROJECT_ID/timerally/web:$TAG" \
  --region asia-southeast2 --platform managed --allow-unauthenticated \
  --cpu 1 --memory 512Mi --min-instances 1 --max-instances 3 --port 8080
gcloud run services update-traffic timerally-web \
  --region asia-southeast2 --to-latest

# Verifikasi style file
curl -s "$WEB_URL/maps/bali-style.json" | head -40

# Verifikasi bundle JS punya marker env
JS_PATH=$(curl -s "$WEB_URL" | grep -o '/assets/[^"]*\.js' | head -1)
curl -s "$WEB_URL$JS_PATH" | grep -o "bali-style.json\|bali.pmtiles\|VITE_MAP_STYLE_URL" | sort -u
```

## Manual cache clear di browser operator

Bila operator masih lihat versi lama padahal `check_web_deploy.sh` hijau,
jalankan di DevTools console halaman web:

```js
navigator.serviceWorker?.getRegistrations?.()
  .then(rs => rs.forEach(r => r.unregister()));
caches?.keys().then(keys => keys.forEach(k => caches.delete(k)));
localStorage.clear();
sessionStorage.clear();
location.reload();
```

Atau buka di Incognito untuk memastikan tidak ada cache.

## Kapan ini dipanggil

- Setelah perubahan style `bali-style.json`.
- Setelah perubahan `nginx.conf` (proxy `/v1/`, header cache).
- Setelah perubahan `.env.production` (URL PMTiles, sentry, dst.).
- Setelah perubahan komponen UI yang harus segera dilihat tim lapangan.

## Gate sebelum field test

`check_web_deploy.sh` HARUS exit 0 sebelum operator boleh memulai run. Kalau
gagal, jangan continue — perbaiki dulu image / style / proxy.
