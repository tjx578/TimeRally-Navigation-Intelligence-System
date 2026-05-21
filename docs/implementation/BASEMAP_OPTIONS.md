# Opsi Basemap & Troubleshooting Map Tidak Tampil

## TL;DR

`apps/web-map-console` punya **fallback chain** otomatis:

1. `VITE_MAP_STYLE_URL` kalau di-set dan reachable (HEAD 200).
2. `VITE_PMTILES_URL` PMTiles inline (HEAD ok atau `VITE_PMTILES_READY=true`).
3. `VITE_MAP_FALLBACK_STYLE_URL` kalau di-set.
4. Demo MapLibre publik `https://demotiles.maplibre.org/style.json`.
5. OSM raster `https://tile.openstreetmap.org/{z}/{x}/{y}.png`.

Operator **tidak harus** selalu pakai offline. Mode tergantung kondisi lapangan.

## Kalau map tidak tampil

Cek satu per satu:

### A. Container map 0×0

Buka DevTools → Elements. Klik `<div class="map-canvas">`. Box model harus
menunjukkan height > 0. Kalau 0:

- pastikan `.map-region` punya `height: 100%` (sudah default di CSS).
- pastikan parent grid (`.workspace` row 2) tidak punya `min-height: 0` di parent yang membuat row kolaps.
- pastikan window size sudah konsisten (resize observer akan otomatis trigger `map.resize()` setelah perubahan layout).

### B. Style fail load

Buka DevTools → Network. Cari request style.json / pmtiles. Kalau 404 / CORS:

- `VITE_MAP_STYLE_URL` salah → kosongkan supaya fallback demotiles aktif.
- PMTiles host tidak ada → kosongkan `VITE_PMTILES_URL`.
- Console akan menampilkan banner merah "Basemap gagal dimuat: ..." dengan pesan error MapLibre.

### C. PMTiles protocol gagal

`pmtiles` package wajib terinstall (`npm install pmtiles`). Sudah ada di
`package.json`. Kalau `installPmtilesProtocol` return false, console fallback
ke style.json / OSM raster — tidak crash.

### D. Offline penuh tanpa internet

`demotiles.maplibre.org` dan `tile.openstreetmap.org` butuh internet. Untuk
true offline, **wajib** isi salah satu dari:

- `VITE_MAP_STYLE_URL=http://<edge-ip>:8080/styles/basic/style.json`
- `VITE_PMTILES_URL=https://<bucket>/bali.pmtiles`

Lihat `ops/offline/bali/README.md` untuk build artefak.

## Bisakah pakai Google Maps?

Pertanyaan ini muncul beberapa kali, jawaban ringkasnya: **opsional, terbatas, dan tidak gratis**.

### Skenario yang boleh

| Skenario | Status di repo |
|---------|----------------|
| Tampilkan basemap Google di MapLibre langsung | TIDAK didukung. Google tidak menyediakan vector tile style.json untuk MapLibre. |
| Embed peta Google interaktif di iframe | Boleh untuk preview link, bukan canvas utama. |
| Open dirrections di Google Maps app via deep link | Sudah didukung lewat `Google Maps URL` di waypoint export. |
| Pakai Google Routes / Directions sebagai validator routing | Sudah ada provider `google` di `services/routing-gateway`. Aktifkan via `GOOGLE_ENABLED=true` + `GOOGLE_MAPS_API_KEY`. |

### Yang TIDAK boleh menurut rancangan

`docs/OPEN_SOURCE_STACK.md` dan `docs/ARCHITECTURE.md` menetapkan **Google Maps hanya validator online dan link-out, bukan offline source of truth**. Alasannya:

- Tile Google tidak boleh di-cache offline (TOS).
- Vector style Google tidak terbuka untuk MapLibre.
- Dependensi koneksi internet → tidak field-ready.

### Cara aksesnya

- Sebagai **validator routing** untuk rute online: aktifkan provider `google` di routing-gateway, lalu set `provider: "google"` saat memanggil `/v1/routing/route`. Output tidak boleh dicampur dengan data offline.
- Sebagai **link-out**: setiap waypoint canonical sudah punya helper untuk membangun `https://www.google.com/maps/dir/?api=1&...`. UI tinggal pasang tombol "Buka di Google Maps".
- Sebagai **basemap interaktif**: pakai iframe Google Maps Embed API di panel terpisah, bukan menggantikan MapLibre.

### Jadi harus selalu offline?

**Tidak**. Repo mendukung tiga mode (lihat `README.md` Mode Operasi):

| Mode | Basemap | Routing | Kapan dipakai |
|------|---------|---------|---------------|
| Championship Online | TileServer cloud / MapTiler / demo MapLibre | Valhalla/OSRM cloud + Google validator | Persiapan, briefing, online review |
| Hybrid Winning | TileServer cloud (atau Google Routes validator) + cache lokal | Valhalla/OSRM cloud, fallback ke offline | Race day di area sinyal stabil |
| Offline Rally | PMTiles/TileServer LAN + OSRM/Valhalla LAN | Routing-gateway LAN | Race day di area tanpa sinyal |

Operator memilih mode lewat env (`VITE_MAP_STYLE_URL`, `VITE_PMTILES_URL`,
`VITE_OFFLINE_MODE`, `ROUTING_DEFAULT_PROVIDER`, `GOOGLE_ENABLED`).
Konfigurasi default `.env.production.example` sengaja **online-leaning**
(demotiles.maplibre.org sebagai fallback otomatis) sehingga sistem baru
dideploy tetap kelihatan map-nya, sebelum operator mengaktifkan offline pack.
