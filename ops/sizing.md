# Server Sizing — Time Rally Production

Sumber: `deep-research-report (2).md`. Dokumen ini diturunkan apa adanya tanpa
mengubah rancangan; ia hanya berfungsi sebagai operational reference.

## Topologi target

- **App VPS** menjalankan Traefik, frontend static, FastAPI API, routing-gateway,
  place-resolver, tracking-gateway.
- **Routing VPS** menjalankan Valhalla (primary), OSRM (hot backup), GraphHopper
  (standby/tertiary), dan PMTiles serving.
- **Supabase** terkelola untuk Postgres + PostGIS + Storage + Auth.

## Alokasi resource

| Component                | Placement     | CPU       | RAM         | Disk        | Catatan                                                  |
|--------------------------|---------------|-----------|-------------|-------------|-----------------------------------------------------------|
| Traefik + frontend (web) | App VPS       | 0.5–1     | 0.5–1 GB    | 5–10 GB     | Sangat ringan, sama-origin dengan API.                    |
| FastAPI API              | App VPS       | 1–2       | 1–2 GB      | 10–20 GB    | Sediakan ruang untuk docs/export/temp.                    |
| routing-gateway          | App VPS       | 0.5–1     | 0.5–1 GB    | 5 GB        | Proxy/normalisasi/fallback.                               |
| place-resolver           | App VPS       | 0.5–1     | 0.5–1 GB    | 5–10 GB     | Cache + curated POI/KMPAL.                                |
| tracking-gateway         | App VPS       | 0.5–1     | 0.5–1 GB    | 10 GB       | Burst tolerance + logs.                                   |
| Valhalla (primary)       | Routing VPS   | 3–4       | 8–16 GB     | 80–150 GB   | Mode utama, mendukung route/matrix/match/isochrone.       |
| OSRM (hot backup)        | Routing VPS   | 2–3       | 4–8 GB      | 50–100 GB   | Cepat untuk route/nearest/match.                          |
| GraphHopper (standby)    | Routing VPS   | 2–3       | 6–12 GB     | 50–100 GB   | Cold/tertiary; aktifkan hanya jika PBF moderat.           |
| PMTiles serving          | Routing VPS   | 0.5–1     | 0.5–1 GB    | 20–100 GB   | Static HTTP range request server.                         |
| Postgres + PostGIS       | Supabase      | managed   | managed     | managed     | Jangan self-host malam sebelum lomba.                     |

## Hostinger plan mapping

| Layer        | Plan      | Spesifikasi                                          | Alasan                                                                       |
|--------------|-----------|------------------------------------------------------|------------------------------------------------------------------------------|
| App VPS      | KVM 4     | 4 vCPU, 16 GB RAM, 200 GB NVMe, 16 TB bandwidth      | Headroom cukup untuk Traefik+SPA+FastAPI+gateway+cache+log.                  |
| Routing VPS  | KVM 8     | 8 vCPU, 32 GB RAM, 400 GB NVMe, 32 TB bandwidth      | Cukup untuk Valhalla regional + OSRM + PMTiles. GraphHopper sesuai PBF.      |
| Fallback     | KVM 8     | sama dengan di atas                                  | Boleh single-box hanya bila wilayah peta moderat dan resiko diterima.        |

## Cost band (estimasi)

| Profil | Estimasi /bulan | Konteks                                                                              |
|--------|-----------------|---------------------------------------------------------------------------------------|
| Low    | ~$40–$70        | Satu VPS + DB managed terkecil, hanya untuk test load sangat kecil.                  |
| Medium | ~$70–$130       | **Rekomendasi**: KVM 4 + KVM 8 + Supabase + domain + Sentry free.                    |
| High   | ~$140+          | Tambah standby node, storage, PITR/lebih banyak retention, dll.                      |

## Failure-domain hardening

1. Jangan campur Postgres ke VPS yang sama. Pakai Supabase.
2. Pisahkan routing/tile dari app/API agar I/O spike tidak men-down-kan UI.
3. Snapshot Hostinger VPS sebelum lomba (T-2h dan T-15 menit).
4. Backup `.env.prod` ke password manager terkunci, jangan ke git.
5. Verifikasi rollback path: `git checkout <prev-sha>` + `docker compose pull && up -d`
   harus selesai < 15 menit. Latih sebelum hari-H.

## Saturation alarm threshold (Prometheus)

| Metric                                  | Warning  | Critical |
|-----------------------------------------|----------|----------|
| CPU usage / 5m avg (app VPS)            | 70%      | 90%      |
| CPU usage / 5m avg (routing VPS)        | 80%      | 95%      |
| Memory usage (any host)                 | 75%      | 90%      |
| Disk usage (`/`)                        | 75%      | 90%      |
| Disk usage (`/opt/timerally-routing`)   | 70%      | 85%      |
| 5xx rate dari Traefik                   | > 1%     | > 3%     |
| Latency p95 `/v1/routing/route`         | > 1.5s   | > 3.5s   |
| Routing provider fallback rate / 5m     | > 10%    | > 30%    |
