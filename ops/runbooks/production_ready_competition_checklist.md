# Production Ready Competition Checklist

Dokumen ini adalah checklist terakhir sebelum Time Rally Navigation Intelligence System
dipakai untuk test jalan dengan soal event nyata.

## Gate Teknis Wajib

- `python -m ruff check .` harus hijau.
- `python -m pytest -q` harus hijau.
- `python -m compileall -q packages services tests tools` harus hijau.
- `npm run build` di `apps/web-map-console` harus hijau.
- `docker compose -f infra/compose/docker-compose.dev.yml config` harus hijau tanpa `.env` lokal.
- GitHub Actions CI harus berjalan untuk Python, web build, dan compose config pada push/PR.

## Environment Production

Isi `.env` dari `.env.example` dan jangan commit `.env`.

- `ENVIRONMENT=production`
- `API_CORS_ORIGINS` berisi domain web app resmi, bukan wildcard.
- `ROUTING_GATEWAY_URL` mengarah ke service routing gateway internal.
- `EXPORTS_ROOT` mengarah ke volume persisten.
- `KNOWLEDGE_ROOT` mengarah ke data curated yang sudah divalidasi.
- Google/GraphHopper key hanya di secret manager atau environment runtime.
- Supabase URL/key/service role hanya di secret manager, bukan di repo.

## Database Supabase

- Jalankan migration di `supabase/migrations`.
- Pastikan RLS aktif pada semua tabel operasional.
- User event harus masuk `rally_event_members` sebelum bisa membaca atau mengubah data event.
- Data GPS live dan audit log harus diuji dengan user non-admin dan admin.
- Backup database dan export artifact harus diuji sebelum hari lomba.

## Routing dan Map Offline

- Siapkan extract OSM area lomba.
- Build dan jalankan minimal satu routing engine production: Valhalla atau OSRM.
- Siapkan PMTiles/MBTiles area lomba untuk mode offline.
- Validasi 10-20 rute kontrol dari soal lama/event lama terhadap jarak dan waktu resmi.
- Gateway routing harus menolak fallback mock untuk output final lomba.
- Google Maps hanya dipakai sebagai validator online atau link-out, bukan sumber tunggal.

## OCR dan Input Soal

- OCR worker production harus tersedia jika ingin upload foto langsung.
- Jika OCR worker belum aktif, operator wajib paste hasil OCR/manual text ke panel soal.
- Hasil parse harus direview: total jarak, total waktu, setiap sub-trayek, waypoint ambigu, dan token unresolved.
- Sistem tidak boleh memakai data demo sebagai hasil parsing/OCR.

## Field Device

- Laptop navigator sudah membuka web app dan login sebelum start.
- Browser sudah pernah membuka app sekali agar app shell masuk cache.
- Device clock disinkronkan dengan Time.is atau sumber jam resmi lomba.
- Power bank, tethering cadangan, dan hotspot lokal tersedia.
- Export GPX/KML/GeoJSON/roadbook sudah diuji di device cadangan.

## Acceptance Sebelum Dipakai Lomba

Sistem boleh dipakai untuk test jalan jika:

- Tidak ada test/lint/build yang gagal.
- Soal event lama bisa diparse menjadi sub-trayek tanpa data demo.
- Setiap waypoint final punya koordinat atau status unresolved yang eksplisit.
- Export endpoint hanya menghasilkan artifact setelah waypoints dan route segments final dikirim.
- Roadbook final berisi jarak, durasi, ETA, dan status validasi.
- Minimal satu skenario offline reload web app berhasil.

## Blocker Yang Harus Ditutup Untuk Full Race-Day Ready

- OCR worker nyata belum ada di repo ini.
- Offline basemap/routing data area lomba harus disediakan di luar repo karena ukuran besar.
- Deployment production, TLS, domain, secret manager, dan backup harus dipasang di environment tujuan.
- Visual QA browser lokal perlu dijalankan di mesin target karena browser otomatis dapat memblokir localhost/file URL.
