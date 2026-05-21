# Production Plan Delta — Repo vs Deep Research Report

Dokumen ini memetakan target rancangan di `deep-research-report (2).md`
terhadap state aktual repo, dan mencatat penambahan seamless yang sudah
diterapkan tanpa mengubah rancangan utama (two-VPS topology, Supabase
managed, Traefik ACME, PMTiles, GitHub Actions deploy, Sentry optional).

## Verdict Per Bagian

| Area Rancangan | Realita Repo Sebelum | Tindakan | Status Sekarang |
|---|---|---|---|
| Two-VPS topology (app + routing) | `docker-compose.prod.yml` punya `routing-engines` profile | Tetap; tinggal split `--profile edge` di app VPS dan `--profile routing-engines` di routing VPS | Selaras |
| Traefik static config | `infra/traefik/traefik.yml` minimal | Tambah HTTP→HTTPS redirect, dynamic file provider, dashboard non-insecure, log JSON | Selaras |
| Traefik dynamic middleware | Belum ada | Tambah `infra/traefik/dynamic/middlewares.yml` (secure headers, basic-auth dashboard, rate limit, CORS) + `users.htpasswd.example` | Selaras |
| Traefik service di compose | Tidak ada | Tambah service `traefik` (profile `edge`) + labels untuk `web` dan `api`, network `time-rally-edge`, volume `traefik_letsencrypt` | Selaras |
| `apps/web-map-console/.env.production` | 4 var | Tambah `VITE_ROUTING_PUBLIC_BASE`, `VITE_SENTRY_DSN`, `VITE_SENTRY_ENVIRONMENT`, `VITE_SENTRY_TRACES_SAMPLE_RATE` | Selaras |
| `apps/web-map-console/Dockerfile` | 4 ARG VITE | Tambah ARG yang sama agar build-time injection lengkap | Selaras |
| `apps/web-map-console/nginx.conf` | SPA fallback minimal | Tambah gzip, security headers, cache rule `js/css/woff2 1y immutable`, `.pmtiles` range-friendly, index.html no-cache | Selaras |
| `services/api/settings/config.py` | Tidak ada Supabase/Sentry/TTL | Tambah `supabase_*`, `sentry_*`, `export_signed_url_ttl_seconds`, `public_web_url`, `public_api_url` | Selaras |
| Supabase Storage policies | Belum ada | Tambah `supabase/migrations/202605210002_storage_policies.sql` (exports-private, uploads-private, assets-public) | Selaras |
| Supabase Storage adapter | Belum ada | Tambah `services/api/app/adapters/supabase_storage.py` (signed URL + upload). Idle/no-op kalau env kosong | Selaras |
| Sentry init backend | Belum ada | Tambah `services/api/app/observability/sentry.py` + hook di `create_app()` | Selaras |
| Sentry init frontend | Belum ada | Tambah `apps/web-map-console/src/lib/observability/sentry.ts` + hook di `main.tsx` | Selaras |
| `.github/workflows/deploy.yml` | Belum ada | Tambah build+push GHCR, Supabase `db push`, deploy SSH app+routing | Selaras |
| `ops/sizing.md` (KVM 4/8) | Belum ada | Tambah dokumen sizing + alarm threshold | Selaras |
| `ops/runbooks/go_live_checklist.md` | Belum ada | Tambah checklist final gate | Selaras |
| `.env.prod.example` | Sudah lumayan | Tambah `PUBLIC_*`, `TRAEFIK_ACME_EMAIL`, `WEB_HOST`, `API_HOST`, `SENTRY_*`, `EXPORT_SIGNED_URL_TTL_SECONDS`, `SUPABASE_*_BUCKET` | Selaras |
| Routing-gateway fallback chain | Sudah ada di `services/routing-gateway/app/main.py` + `route_event.py` | Tidak diubah | Selaras |
| Supabase schema (events, members, raw_inputs, dst.) | Lengkap di migration `0001` | Tidak diubah | Lebih lengkap dari laporan |

## Yang TIDAK Diubah (sesuai instruksi)

- Struktur dasar `docker-compose.prod.yml` tetap, hanya **ditambah** Traefik service, network, dan labels.
- `traefik.yml` lama (entryPoints/providers/api/certificatesResolvers) tetap; hanya **dilengkapi** dengan redirect, dynamic file provider, log format JSON, dashboard non-insecure.
- Skema Supabase migration awal tetap intact; storage policies ditambah sebagai migration baru.
- Routing-gateway fallback logic tidak disentuh — sudah benar.
- CI workflow lama tetap; deploy workflow baru ditambahkan terpisah.

## Catatan Implementasi

1. **Supabase Storage adapter no-op safe.** Kalau `SUPABASE_URL` /
   `SUPABASE_SERVICE_ROLE_KEY` tidak diset, signed URL builder return
   `signed_url=None`. Endpoint export tetap berjalan dengan filesystem sink
   yang sudah ada.
2. **Sentry SDK optional dependency.** `sentry-sdk` dan `@sentry/react`
   tidak ditambahkan ke requirements/package.json. Bila DSN tidak diset,
   bootstrap return False dan log tidak terganggu. Bila perlu, instal:
   - server: `pip install sentry-sdk`
   - web: `npm install @sentry/react`
3. **Traefik basic-auth dashboard.** Gunakan
   `htpasswd -nbB ops 'change-me' > infra/traefik/dynamic/users.htpasswd`.
   File `users.htpasswd` tidak boleh tracked git.
4. **Convention path Storage.** Adapter Supabase mengasumsikan
   `<event_id>/...` sebagai prefix path. Storage policy menolak path tanpa
   UUID di segmen pertama, sehingga upload member tidak bisa bocor ke event
   yang bukan mereka.

## Open Items (di luar scope deploy)

- OCR worker production (sekarang masih demo intake). Bisa di-onboard tanpa
  ubah rancangan dengan profile `ocr` yang sudah ada di compose.
- Native field-mobile (PWA sudah ada).
- PITR untuk Supabase: tetap optional sesuai laporan.
