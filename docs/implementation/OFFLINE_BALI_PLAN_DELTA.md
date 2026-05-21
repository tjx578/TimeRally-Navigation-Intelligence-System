# Offline Bali Plan — Delta Implementasi

Dokumen ini memetakan rancangan `deep-research-report (3).md` ke artefak nyata
di repo. Tidak ada bagian rancangan yang diubah; hanya ditambah lapisan glue.

## Ringkas

Rantai produksi end-to-end yang diminta laporan sekarang sudah punya artefak
di repo:

```
Geofabrik PBF
    └─ tools/offline-bali/extract.sh      (osmium clip pakai bali-mainland.geojson)
    └─ tools/offline-bali/build_tiles.sh  (Tilemaker -> bali-vYYYY-MM.mbtiles)
    └─ tools/offline-bali/build_routing.sh(OSRM extract/partition/customize)
    └─ tools/offline-bali/build_valhalla.sh (standby)
    └─ tools/offline-bali/build_overlays.sh (Tippecanoe overlays + tile-join)

Edge node:
    docker compose -f compose.dev.yml -f compose.offline-bali.yml up -d
    └─ tileserver-offline @ :8080 (TileServer GL membaca MBTiles read-only)
    └─ osrm-offline       @ :5000 (OSRM MLD)
    └─ valhalla-offline   @ :8002 (profile valhalla-standby)
    └─ routing-gateway env override -> osrm-offline / valhalla-offline

Frontend:
    apps/web-map-console/.env.local      (VITE_OFFLINE_MODE + endpoint LAN)
    apps/web-map-console/src/config/offlineMap.ts (single source of truth)
    apps/web-map-console/src/lib/api/routingClient.ts (pakai gateway LAN)
    apps/web-map-console/src/lib/map/mapStyle.ts (resolveMapStyle pakai
        VITE_MAP_STYLE_URL atau bangun source vector inline dari
        VITE_TILE_BASE_URL)
```

## Mapping verified vs proposed dari laporan

| Status laporan | Path | Action repo |
|---|---|---|
| Verified | `apps/web-map-console/` | tetap; tidak diubah |
| Verified | `apps/web-map-console/vite.config.ts` | tetap |
| Verified | `infra/compose/docker-compose.dev.yml` | tetap (sudah di-update sebelumnya, tidak disentuh lagi) |
| Proposed | `infra/compose/docker-compose.offline-bali.yml` | dibuat |
| Proposed | `apps/web-map-console/.env.local` | `.env.local.example` dibuat (jangan commit `.env.local`) |
| Proposed | `apps/web-map-console/src/config/offlineMap.ts` | dibuat |
| Proposed | `ops/offline/bali/README.md` | dibuat |

## Tambahan yang tidak ada di laporan tetapi sudah seamless

| Path | Alasan |
|---|---|
| `tools/offline-bali/common.sh` | helper bash bersama (path, log, prerequisite check) |
| `tools/offline-bali/extract.sh` | jalankan `osmium extract --strategy=complete_ways -p bali-mainland.geojson` sesuai laporan |
| `tools/offline-bali/build_tiles.sh` | run Tilemaker container `ghcr.io/systemed/tilemaker:master` dengan `--store` SSD-spill |
| `tools/offline-bali/build_routing.sh` | OSRM MLD pipeline (`osrm-extract → osrm-partition → osrm-customize`) |
| `tools/offline-bali/build_valhalla.sh` | Valhalla scripted image untuk build tile sekali jalan |
| `tools/offline-bali/build_overlays.sh` | Tippecanoe + `tile-join` untuk overlay rally |
| `tools/offline-bali/smoke_tests.sh` | seluruh smoke test laporan, exit code 0/1 |
| `tools/offline-bali/bali-mainland.geojson` | polygon Bali mainland (24 vertex) |
| `apps/web-map-console/src/lib/api/routingClient.ts` | client routing yang otomatis pilih gateway LAN saat `VITE_OFFLINE_MODE=true` |
| `apps/web-map-console/src/lib/map/mapStyle.ts` | tambah `resolveMapStyle()` + integrasi `offlineMap.ts` tanpa hapus PMTiles fallback |

## Yang TIDAK diubah

- `vite.config.ts` — proxy `/v1` ke API tetap.
- `docker-compose.dev.yml`, `docker-compose.prod.yml` — overlay offline-bali dipakai sebagai file tambahan, bukan rewrite.
- Style PMTiles fallback (`offlineMapStyle`) tetap ada untuk skenario online.
- File parser/probability/scoring di `packages/rally_core/` — tidak disentuh.

## Operasional

| Fase | Komando |
|---|---|
| Build artefak (1x) | `tools/offline-bali/extract.sh && tools/offline-bali/build_tiles.sh && tools/offline-bali/build_routing.sh` |
| Up stack offline | `docker compose -f infra/compose/docker-compose.dev.yml -f infra/compose/docker-compose.offline-bali.yml up -d` |
| Verify | `TILES_HOST=http://<edge-ip>:8080 OSRM_HOST=http://<edge-ip>:5000 tools/offline-bali/smoke_tests.sh` |
| Frontend offline | salin `apps/web-map-console/.env.local.example` → `.env.local`, set IP edge node, `npm run dev` |
| Standby Valhalla | `tools/offline-bali/build_valhalla.sh` lalu compose `--profile valhalla-standby` |

## Open items (di luar scope laporan)

- `npm run build` belum diverifikasi karena tidak ada VM aktif di sesi ini; kode TS bersifat additive sehingga harus build hijau.
- Rally overlays butuh GeoJSON aktual; tinggal letakkan di `data/fixtures/rally_cases/*.geojson`.
- Tile attribution di UI MapLibre kerangka sudah punya properti `attribution`; pastikan UI menampilkan OSM credit (ODbL).
