# Go-Live Checklist — Time Rally Production

Diturunkan langsung dari `deep-research-report (2).md`. Centang semua sebelum
mengizinkan field test berjalan.

## DNS & TLS

- [ ] `dig app.example.com`, `dig api.example.com`, `dig route.example.com`,
      `dig tiles.example.com` semuanya resolve ke VPS yang benar.
- [ ] Buka HTTPS untuk seluruh hostname publik. Sertifikat valid (Let's Encrypt
      via Traefik ACME) tanpa trust warning.
- [ ] Port 80 reachable selama renewal ACME window.

## Frontend

- [ ] `https://app.example.com` memuat tanpa error console.
- [ ] Service worker terdaftar (`navigator.serviceWorker.controller` aktif).
- [ ] PMTiles loadable: pan/zoom basemap tanpa tile protocol error.
- [ ] Tidak ada VITE_* yang menjabarkan service-role key di network panel.

## API

- [ ] `curl -fsS https://api.example.com/healthz` -> HTTP 200 JSON.
- [ ] `/readyz` -> `status: ready` dan list provider routing healthy.
- [ ] `/v1/rally/parse` mengembalikan struktur sub-trayek/waypoint untuk
      fixture event lama Jembrana.
- [ ] `/v1/routing/route` mengembalikan polyline real (bukan mock) bila
      provider Valhalla / OSRM aktif.
- [ ] `/v1/export/artifacts` menulis file ke bucket `exports-private` dan
      mengembalikan signed URL yang valid sebelum TTL.

## Supabase

- [ ] `select postgis_full_version();` sukses lewat SQL editor.
- [ ] Migration `202605210001_initial_field_ops_schema.sql` dan
      `202605210002_storage_policies.sql` jalan tanpa error.
- [ ] Anon key gagal `select` pada `rally_waypoints` tanpa membership.
- [ ] User dengan role `navigator` bisa baca event ia ikut, dan tidak bisa
      baca event lain.
- [ ] Signed URL pada `exports-private` expire setelah `EXPORT_SIGNED_URL_TTL_SECONDS`.

## Routing VPS

- [ ] Valhalla `/route` smoke test untuk dua koordinat menghasilkan polyline.
- [ ] OSRM `/route/v1/driving/lon1,lat1;lon2,lat2` -> `code: Ok`.
- [ ] (Opsional) GraphHopper /route ok jika diaktifkan.
- [ ] Gateway fallback teruji: matikan Valhalla → request tetap balas
      melalui OSRM, tanpa 5xx ke client.

## Observability

- [ ] Sentry DSN di-set di server (`SENTRY_DSN`) dan client (`VITE_SENTRY_DSN`).
- [ ] Kirim satu handled error dari API dan dari web; verifikasi muncul di
      dashboard Sentry.
- [ ] Prometheus scrape `/metrics` (jika diaktifkan) atau setidaknya
      blackbox probe `app`, `api`, `tiles`, `route` hijau.

## Snapshot & Rollback

- [ ] Snapshot Hostinger pada app VPS dan routing VPS sebelum start.
- [ ] `.env.prod` disimpan di password manager terkunci.
- [ ] Tag git release (`git tag v0.x.0 && git push --tags`).
- [ ] Latih rollback: `git checkout <prev-sha>` + `docker compose pull && up -d`
      selesai dalam < 15 menit.

## Field Pack

- [ ] Roadbook MD dicetak / disinkronkan ke field-mobile.
- [ ] PMTiles untuk wilayah lomba tersedia offline di field-mobile.
- [ ] Tracking-gateway menerima ingest dummy 5 titik per device.
- [ ] Navigator bisa lihat heatmap deviasi dari `POST /v1/tracking/replay`.

## Final Gate

Race direction baru boleh **START** kalau:
- HTTPS valid,
- frontend hijau,
- API health hijau,
- minimal 1 routing primary + 1 fallback hijau,
- signed URL export sukses unduh sekali end-to-end,
- 1 roadbook nyata berhasil dibuat dari soal nyata dari UI.
