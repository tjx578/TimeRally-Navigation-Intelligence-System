# Race Day Runbook

Runbook ini menjaga alur sistem tetap sama: input soal, parsing, validasi,
route resolving, map review, export roadbook, dan tracking. Langkah di bawah
menambah kontrol operasional agar sistem siap dipakai di event nyata.

## H-1

- Isi `.env.prod` dari `.env.prod.example`; jangan masukkan service role key ke frontend.
- Pastikan `SUPABASE_DB_URL`, `DATABASE_URL`, dan `API_CORS_ORIGINS` memakai domain produksi.
- Siapkan data routing area lomba:
  - OSRM MLD: `region.osrm`, `region.osrm.partition`, `region.osrm.cells`.
  - Valhalla tiles atau PBF area lomba.
  - GraphHopper graph cache bila dipakai sebagai standby.
- Siapkan `VITE_PMTILES_URL` untuk file basemap PMTiles area lomba.
- Jalankan backup awal: `ops/scripts/backup.sh`.
- Validasi config: `docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml config`.

## Start

```sh
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml up -d
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml ps
```

Healthcheck wajib hijau:

- `GET /healthz` untuk web, API, routing-gateway, place-resolver, tracking-gateway.
- `GET /readyz` untuk API dan routing-gateway sebelum soal pertama diproses.

## Routing Failover

Default produksi:

```env
ROUTING_PROVIDER_PRIMARY=osrm
ROUTING_PROVIDER_FALLBACK=valhalla
ROUTING_PROVIDER_STANDBY=graphhopper
ROUTING_ALLOW_MOCK_FALLBACK=false
```

Saat provider utama bermasalah, ubah urutan env lalu restart hanya gateway:

```sh
docker compose --env-file .env.prod -f infra/compose/docker-compose.prod.yml up -d routing-gateway
```

Gunakan provider `auto` dari UI/API untuk mengikuti urutan env tanpa mengubah
workflow solving.

## Saat Soal Masuk

- Masukkan teks soal hasil OCR/manual.
- Cek parser menemukan sub-trayek, JT, KMPAL, dan target jarak/waktu.
- Jalankan route review; rute dianggap siap hanya jika status sub-trayek tidak `needs_review`.
- Gunakan map panel untuk cek chaining antar sub-trayek dan missing waypoint probability.
- Export YAML/GPX/KML setelah validasi jarak/waktu masuk toleransi event.

## Offline / Sinyal Lemah

- Web console menyimpan request penting ke offline queue saat jaringan drop.
- Saat koneksi balik, queue otomatis flush.
- Jika PMTiles tersedia, map tetap menampilkan basemap area lomba.
- Jika OCR worker masih `manual_required`, operator wajib menyalin teks soal terverifikasi.

## Setelah Finish

- Export artefak final dan simpan hash/manifest.
- Jalankan backup database.
- Simpan log healthcheck, route provider yang dipakai, dan hasil validasi.
