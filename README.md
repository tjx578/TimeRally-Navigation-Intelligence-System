# Time Rally Navigation Intelligence System

Blueprint repo untuk membangun sistem NaviPRO/Time Rally yang tugas eksplisitnya adalah membantu navigator menang lomba time rally: membaca soal, memahami singkatan rally, menemukan waypoint, menghitung waktu, memvalidasi constraint, dan menghasilkan rute presisi yang dapat dipakai di lapangan.

## Misi Sistem

Sistem ini tidak hanya menampilkan peta. Sistem ini menjadi rally intelligence layer:

1. Mengubah soal rally mentah menjadi struktur sub-trayek.
2. Memahami singkatan, landmark, KMPAL, tulip, zero point, dan instruksi arah.
3. Menyelesaikan waypoint hilang dengan probabilitas tertinggi berbasis waktu, jarak, arah, dan jaringan jalan.
4. Menghitung jarak, waktu, ETA, kecepatan target, dan deviasi per leg.
5. Memvalidasi absolute binding constraint sebelum rute dianggap layak.
6. Menghasilkan YAML/EAML, GPX, KML, GeoJSON, Google Maps link, dan roadbook navigasi.
7. Mendukung mode online Google Maps dan mode offline OSM/Valhalla/OSRM.

## Stack Acuan Open Source

| Area | Repo Acuan | Peran Dalam Sistem |
|---|---|---|
| Offline/online routing | Project-OSRM/osrm-backend | Fast route, table/matrix, nearest, map matching. |
| Flexible routing | graphhopper/graphhopper | Alternative engine, custom weighting, map matching. |
| Offline tiled routing | valhalla/valhalla | Core offline routing, matrix, map matching, isochrone. |
| Web map renderer | maplibre/maplibre-gl-js | UI peta utama dengan vector tiles. |
| Lightweight map renderer | Leaflet/Leaflet | UI sederhana, KML/GPX/GeoJSON review. |
| Offline map benchmark | organicmaps/organicmaps | Acuan desain offline mobile dan field navigation. |
| Geocoder OSM | osm-search/Nominatim | Search nama tempat dan reverse geocoding lokal. |
| Tile server | maptiler/tileserver-gl | Serve MBTiles/vector/raster tiles. |
| Tile pipeline | openmaptiles/openmaptiles | Skema basemap OSM. |
| Offline tile package | protomaps/PMTiles | Single-file offline tile archive. |
| Live tracking | traccar/traccar | Tracking kendaraan, geofence, checkpoint, replay. |

## Hubungan Dengan Folder Lama

Folder lama di `D:\TIME RALLY` diperlakukan sebagai sumber legacy:

| Folder Lama | Masuk Ke Skeleton |
|---|---|
| `Dokumen_Markdown` | `data/curated/rally_rules` dan `docs` |
| `Data_JSON`, `Data_CSV` | `data/curated/places` |
| `Data_YAML` | `data/curated/rally_rules`, `data/curated/kmpal`, `data/fixtures` |
| `Kode_Python` | `packages/rally_core`, `packages/geo_engine`, `services/api` |
| `Kode_Web` | `apps/web-map-console`, `services/api` |
| `Rute_GPS` | `data/fixtures/rally_cases` |
| `Spreadsheet`, `PDF`, `Word`, `Gambar` | `data/raw` dan `docs/evidence` |

## Top Level Repo

```text
apps/       UI web dan mobile untuk navigator, analyst, dan race control.
services/   API, routing gateway, place resolver, tile service, tracking gateway.
packages/   Core logic: parser, reasoning, constraints, probability, scoring.
data/       Raw data, curated POI, KMPAL, map extract, fixture soal rally.
infra/      Docker, compose, k8s, deployment stack.
ops/        Runbook lomba, quality gates, release checklist.
docs/       Arsitektur, ADR, pipeline reasoning, API contract.
tests/      Unit, integration, golden test berbasis kasus rally.
tools/      Importer, validator, benchmark, migration scripts.
```

## Mode Operasi

### Championship Online Mode

Google Maps digunakan sebagai validator online dan link-out, bukan sebagai satu-satunya sumber kebenaran. Sistem tetap memprioritaskan knowledge lokal, KMPAL, dan constraint rally.

### Offline Rally Mode

OSM extract, Valhalla/OSRM, Nominatim lokal, dan PMTiles/MBTiles dipakai agar navigator tetap bisa bekerja tanpa internet.

### Hybrid Winning Mode

Mode rekomendasi: local-first, Google-validated. Sistem memilih rute yang paling memenuhi soal, bukan rute tercepat versi map umum.

## Prinsip Mutlak

1. Urutan waypoint dari soal tidak boleh dioptimasi ulang tanpa izin.
2. Constraint jarak dan waktu adalah binding.
3. Waypoint inferensi wajib diberi confidence dan alasan.
4. Data Google dipisahkan dari data offline/OSM/manual.
5. Output final harus menjelaskan status: verified, inferred, warning, atau violation.

