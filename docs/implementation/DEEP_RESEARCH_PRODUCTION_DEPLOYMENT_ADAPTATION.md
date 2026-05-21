# Deep Research Production Deployment Adaptation

Dokumen ini merangkum adaptasi dari `deep-research-report (1).md` ke repo.
Perubahan sengaja bersifat operasional dan reliability hardening, bukan
penggantian logika inti pemecahan soal rally.

## Implementasi

- Health/readiness endpoints ditambahkan pada API, routing-gateway,
  place-resolver, tracking-gateway, dan OCR worker.
- Routing gateway sekarang mendukung provider `auto` dengan urutan env:
  OSRM primary, Valhalla fallback, GraphHopper standby, dan mock hanya bila
  diizinkan.
- Web console memiliki offline queue untuk request operasional penting dan hook
  PMTiles opsional untuk basemap offline.
- Compose produksi ditambahkan untuk VPS: web, API, routing, resolver,
  tracking, profile routing engines, OCR worker, dan monitoring.
- Template reverse proxy, Traefik, monitoring blackbox, backup/restore, systemd,
  dan runbook race day ditambahkan.
- `.env.prod.example` memisahkan kunci browser yang boleh publik dari kunci
  Supabase server-side.

## Batasan yang Sengaja Tidak Dipalsukan

- OCR worker belum mengeluarkan teks otomatis sebelum engine OCR final dipasang.
- Routing engine tidak membawa data peta bawaan; operator harus menyiapkan data
  OSRM/Valhalla/GraphHopper untuk area event.
- Supabase production tetap harus memakai migration resmi dan credential asli.
- PMTiles membutuhkan file basemap area lomba dan plugin PMTiles browser bila
  ingin memakai protokol `pmtiles://`.
