# Offline Bali Map Pack

Runbook untuk menyiapkan paket peta offline Bali (basemap MBTiles + OSRM MLD)
yang dipakai di edge node pada hari lomba. Diturunkan dari
`docs/implementation/OFFLINE_BALI_PLAN_DELTA.md`.

## Filosofi

- **Build di mana saja** (workstation, VPS, atau langsung edge node).
- **Serve dari edge node** di LAN rally agar tetap jalan tanpa internet.
- **Artefak immutable**: setiap build menghasilkan file ber-tag (`bali-v2026-05.mbtiles`).
- **Rollback cepat**: simpan dua artefak terakhir; symlink `bali-latest.mbtiles`
  menunjuk artefak aktif.

## Prerequisites

| Tool | Versi minimum | Catatan |
|---|---|---|
| Docker | 24+ | dipakai semua build dan service |
| osmium-tool | 1.14+ | clipping polygon `complete_ways` |
| wget | apa pun | unduh seed Geofabrik |
| bash | 5+ | helper script |

## Layout host

Default akar offline: `/srv/timerally/offline`. Override pakai env
`OFFLINE_BALI_ROOT=...`.

```
/srv/timerally/offline/
├── extracts/   # PBF mentah dan hasil clip Bali
├── tiles/      # MBTiles + workspace tilemaker
├── osrm/       # graph OSRM siap routed
├── valhalla/   # standby Valhalla custom_files
└── logs/       # transcript build
```

## Build chain

1. **Extract Bali**

   ```bash
   tools/offline-bali/extract.sh
   # SEED_SOURCE=indonesia tools/offline-bali/extract.sh   # paling fresh
   ```

2. **Build basemap MBTiles**

   ```bash
   tools/offline-bali/build_tiles.sh
   ```

3. **(Opsional) Build overlay rally**

   ```bash
   tools/offline-bali/build_overlays.sh \
       data/fixtures/rally_cases/checkpoints.geojson \
       data/fixtures/rally_cases/hazards.geojson
   ```

4. **Build OSRM MLD graph**

   ```bash
   tools/offline-bali/build_routing.sh
   ```

5. **(Opsional) Build Valhalla tiles standby**

   ```bash
   tools/offline-bali/build_valhalla.sh
   ```

## Run di edge node

```bash
# .env minimal di edge node
export OFFLINE_BALI_ROOT=/srv/timerally/offline
export OFFLINE_PUBLIC_URL=http://192.168.50.10:8080/
export OFFLINE_MBTILES_FILE=bali-latest.mbtiles
export OFFLINE_OSRM_FILE=bali-mainland.osrm

docker compose \
  -f infra/compose/docker-compose.dev.yml \
  -f infra/compose/docker-compose.offline-bali.yml \
  up -d
```

## Smoke test

```bash
TILES_HOST=http://192.168.50.10:8080 \
OSRM_HOST=http://192.168.50.10:5000 \
tools/offline-bali/smoke_tests.sh
```

Smoke test akan memverifikasi:

- artefak PBF/MBTiles/OSRM ada,
- TileServer GL HTTP 200,
- OSRM `nearest`, `route`, `table`, `match` semuanya `code: Ok`,
- (kalau aktif) Valhalla `/status` mengembalikan `version`.

## Frontend

1. Salin `apps/web-map-console/.env.local.example` menjadi `.env.local`,
   sesuaikan IP edge node.
2. `npm run dev` (development) atau rebuild image production
   (`docker compose -f infra/compose/docker-compose.prod.yml build web`).
3. Verifikasi browser network panel:
   - request tiles ke `:8080` lokal,
   - request routing ke `:8010` (gateway) atau `:5000` (OSRM langsung).

## Rollback

1. Cek symlink aktif: `ls -l /srv/timerally/offline/tiles/bali-latest.mbtiles`.
2. Pointing ulang ke build sebelumnya:
   ```bash
   ln -sfn bali-v2026-04.mbtiles /srv/timerally/offline/tiles/bali-latest.mbtiles
   docker compose restart tileserver-offline
   ```
3. Untuk OSRM, simpan dua direktori per build (`osrm-2026-05/`, `osrm-2026-04/`)
   dan swap simbolik link `bali-mainland.osrm`.

## Catatan keamanan

- Bind tile server dan OSRM ke LAN saja kalau memungkinkan, bukan ke 0.0.0.0 publik.
- OSM attribution wajib muncul di UI sesuai ODbL.
- File polygon `bali-mainland.geojson` di-version di git (lihat
  `tools/offline-bali/bali-mainland.geojson`), tetapi PBF/MBTiles hasil build
  TIDAK boleh masuk git (sudah ada di `.gitignore`).
