# Championship Day Runbook

Runbook hari lomba time rally. Tujuannya: memastikan sistem **siap menang**,
bukan sekadar berjalan.

## T-72 jam: Persiapan

1. Pastikan OSM extract regional sudah dibangun (`tools/osm_extract.sh`).
2. Bangun graph Valhalla + OSRM dan verifikasi `/health` ketiga service.
3. Sinkronkan curated places & KMPAL dari `data/curated/` ke server.
4. Jalankan smoke test pipeline (`pytest tests/smoke`).

## T-24 jam: Validasi Soal

1. Import soal rally melalui UI Input Workbench.
2. Jalankan `POST /v1/rally/parse` dan periksa `unresolved_tokens`.
3. Resolve setiap waypoint ambigu via place resolver / probability engine.
4. Validasi timing-table lewat `POST /v1/validation/timing-table`.
5. Generate Export pack: YAML, GPX, KML, GeoJSON, Roadbook MD.
6. Pasang `manifest.json` ke offline package dan sinkronkan ke field-mobile.

## T-2 jam: Briefing

1. Cetak roadbook dari `apps/web-map-console` (Roadbook feature).
2. Pasang offline package PMTiles ke device navigator.
3. Verifikasi `tracking-gateway/health` dan device login.
4. Test kirim 5 titik dummy ke `/v1/tracking/ingest`.

## T-15 menit: Pra-Start

1. Jalankan master-clock tap detik di field-mobile, sinkronkan ke jam start.
2. Pastikan `RallyExecutionState.roadbookReady` = true.
3. Kunci rute (`route-editor` → mode `lock`).

## Go / No-Go Gate

GO bila:

- tidak ada unresolved waypoint kritis,
- deviasi jarak di dalam toleransi (0.5 km total, 0.2 km per sub),
- deviasi waktu di dalam toleransi (1 menit total, 0.5 menit per sub),
- chaining sub-trayek valid (gap < 50 m),
- semua kandidat inferred sudah direview,
- offline package terbuka di field-mobile.

NO-GO bila:

- masih ada placeholder koordinat,
- chaining putus,
- start/finish hilang,
- rute kontradiksi dengan total jarak sub-trayek,
- confidence kritis < 0.7.

## During Race

1. Pantau Traccar + `POST /v1/tracking/replay`.
2. Bila instruksi ambigu, panggil `POST /v1/probability/infer-missing-waypoint`
   dengan candidate dari marshal lapangan.
3. Hindari edit rute di field-mobile selama lomba. Hanya advisory.
4. Catat checkpoint timing aktual.

## After Race

1. Export GPS trace dari Traccar / field-mobile.
2. Jalankan replay deviation audit.
3. Generate final report:
   - `validation-report.md`
   - `championship-score.json`
   - `candidate-review.md`
   - `tracking-deviation.json`
4. Backup seluruh artefak ke `exports/<event_id>/`.
5. Tambahkan kasus baru ke `tests/golden/` agar regression terkalibrasi.

## Rollback Plan

Jika engine routing offline gagal:

1. Switch routing default ke `mock` (`ROUTING_DEFAULT_PROVIDER=mock`).
2. Pastikan navigator memegang roadbook cetak.
3. Aktifkan Google Routes sebagai validator hanya di area online.

## Sign-off

Race Director, Map Engineer, Navigator, dan IT On-Call wajib
menandatangani checklist sebelum start.
