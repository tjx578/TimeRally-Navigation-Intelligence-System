# Architecture

## Ringkasan

Arsitektur menggunakan prinsip local-first dan provider-neutral. Sistem tidak mengunci diri pada Google Maps, Valhalla, OSRM, atau GraphHopper. Semua engine routing dipanggil lewat `routing-gateway`, sedangkan logika rally tetap berada di `packages/rally_core`.

```text
User/OCR/File
  -> API
  -> Rally Parser
  -> Knowledge Engine
  -> Place Resolver
  -> Routing Gateway
  -> Constraint Engine
  -> Probability Resolver
  -> Scoring Engine
  -> Exporter
  -> Web/Mobile UI
```

## Komponen Utama

### Rally Parser

Tugas:
- Membaca soal rally mentah.
- Mengurai event, sub-trayek, total jarak, total waktu, mode kecepatan.
- Mengurai instruksi seperti BKN, BKR, JT, O, X, T, br, POM, SDN, KMPAL.
- Mengubah teks menjadi struktur waypoint berurutan.

### Knowledge Engine

Tugas:
- Menyimpan SOP, singkatan, formula, KMPAL, dan place alias.
- Mencari POI dari data lokal sebelum memanggil provider eksternal.
- Memberi confidence untuk hasil lookup.

### Place Resolver

Tugas:
- Resolve waypoint menjadi koordinat.
- Provider urutan:
  1. Verified local POI.
  2. KMPAL database.
  3. Nominatim lokal.
  4. Google Places online.
  5. Manual/inferred candidate.

### Routing Gateway

Tugas:
- Menyediakan interface netral untuk route, matrix, nearest, snap, map matching.
- Adapter:
  - Valhalla untuk offline/tiled graph.
  - OSRM untuk route/table cepat.
  - GraphHopper untuk custom profiles dan alternative engine.
  - Google Routes/Directions untuk online validation.

### Constraint Engine

Tugas:
- Memastikan rute mengikuti absolute binding constraint.
- Validasi:
  - total jarak,
  - total waktu,
  - jarak dan waktu per sub-trayek,
  - chaining finish/start,
  - route realism,
  - coordinate precision.

### Probability Engine

Tugas:
- Menyelesaikan waypoint yang hilang.
- Menghitung kandidat berdasarkan waktu, jarak, tipe landmark, arah, bentuk jalan, dan koridor route.
- Menandai hasil sebagai `inferred`, bukan `verified`.

### Scoring Engine

Tugas:
- Menghitung score championship.
- Memberi penalty jika ada placeholder coordinate, broken chain, time formula error, atau distance violation.
- Menghasilkan report "siap lomba" atau "belum layak".

### Map UI

Tugas:
- Menampilkan route, waypoint, confidence, warning, dan sub-trayek.
- Mengizinkan koreksi manual kandidat.
- Export roadbook dan navigasi.

## Boundary Penting

Google Maps digunakan sebagai provider online dan validator. Offline map harus memakai OSM/PMTiles/MBTiles, bukan data Google yang dicache.

