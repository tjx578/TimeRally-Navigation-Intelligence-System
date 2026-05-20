# Open Source Stack Mapping

Dokumen ini memetakan repo open source terpercaya ke fungsi Time Rally Navigation Intelligence System.

## Routing Engines

### OSRM

Repo: `Project-OSRM/osrm-backend`

Digunakan untuk:
- `route`: rute antar waypoint.
- `table`: distance matrix antar kandidat.
- `nearest`: snap waypoint ke node jalan terdekat.
- `match`: map matching GPS track.
- `trip`: hanya untuk analisis, bukan mengubah urutan soal.

Kapan dipakai:
- Butuh jawaban cepat.
- Backend server punya map extract regional.
- Analisis banyak kandidat missing waypoint.

### Valhalla

Repo: `valhalla/valhalla`

Digunakan untuk:
- offline routing berbasis tiled graph,
- route, matrix, map matching,
- turn-by-turn instruction,
- edge/cost model yang bisa dipakai untuk profil rally.

Kapan dipakai:
- Mode offline dan field-ready.
- Peta region disiapkan sebelum lomba.
- Butuh routing yang mudah dipaketkan per wilayah.

### GraphHopper

Repo: `graphhopper/graphhopper`

Digunakan untuk:
- alternative routing,
- custom model/profile,
- map matching,
- isochrone,
- sanity check terhadap OSRM/Valhalla.

Kapan dipakai:
- Butuh fleksibilitas profile.
- Membandingkan hasil routing saat OSRM/Valhalla berbeda.

## Map Rendering

### MapLibre GL JS

Repo: `maplibre/maplibre-gl-js`

Peran:
- UI peta utama.
- Render vector tile offline/online.
- Menampilkan layer:
  - route polyline,
  - waypoint,
  - confidence heat,
  - sub-trayek boundary,
  - warning marker.

### Leaflet

Repo: `Leaflet/Leaflet`

Peran:
- UI ringan untuk review data.
- Cocok untuk KML/GPX/GeoJSON viewer.
- Cocok untuk tool internal dan low-spec device.

## Geocoding and Search

### Nominatim

Repo: `osm-search/Nominatim`

Peran:
- offline search,
- reverse geocode,
- alternative to Google Geocoding.

Catatan:
- Untuk lomba, data lokal NaviPRO tetap prioritas di atas Nominatim karena POI rally sering lebih spesifik daripada nama OSM umum.

## Tiles and Offline Map

### OpenMapTiles

Repo: `openmaptiles/openmaptiles`

Peran:
- skema vector tile.
- dasar style MapLibre.

### TileServer GL

Repo: `maptiler/tileserver-gl`

Peran:
- serve MBTiles untuk browser dan app.

### PMTiles

Repo: `protomaps/PMTiles`

Peran:
- single-file tile package.
- cocok untuk distribusi offline field kit.

## Offline Navigation Benchmark

### Organic Maps

Repo: `organicmaps/organicmaps`

Peran:
- benchmark UX offline navigation.
- acuan import/export KML, KMZ, GPX, GeoJSON.
- bukan komponen wajib backend, tetapi penting sebagai referensi field usability.

## Live Tracking

### Traccar

Repo: `traccar/traccar`

Peran:
- live GPS tracking kendaraan.
- checkpoint/geofence.
- replay route setelah lomba.
- audit deviasi rute.

