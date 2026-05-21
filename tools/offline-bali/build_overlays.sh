#!/usr/bin/env bash
#
# Build rally overlay MBTiles dari GeoJSON (checkpoints, hazards, dst.) pakai Tippecanoe.
# Kemudian merge dengan basemap pakai tile-join (juga dari image Tippecanoe).
#
# Usage:
#   ./build_overlays.sh checkpoints.geojson hazards.geojson no-go-zones.geojson
#
# Memerlukan: docker
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd docker
ensure_dirs

if [[ $# -lt 1 ]]; then
  log "Usage: $0 <geojson> [geojson ...]"
  exit 2
fi

OVERLAY_MBTILES="${OVERLAY_MBTILES:-rally-overlays.mbtiles}"
BUNDLE_MBTILES="${BUNDLE_MBTILES:-bali-bundle.mbtiles}"

# Copy input GeoJSON ke workspace tiles
INPUT_FILES=()
for f in "$@"; do
  if [[ ! -f "$f" ]]; then
    log "input tidak ada: $f"
    exit 2
  fi
  cp -f "$f" "${TILES_DIR}/$(basename "$f")"
  INPUT_FILES+=("/data/$(basename "$f")")
done

TIPPECANOE_IMAGE="${TIPPECANOE_IMAGE:-ghcr.io/felt/tippecanoe:latest}"

log "build overlay MBTiles -> ${OVERLAY_MBTILES}"
docker run --rm -v "${TILES_DIR}:/data" "${TIPPECANOE_IMAGE}" \
  tippecanoe -f \
    -Z10 -z16 \
    -o "/data/${OVERLAY_MBTILES}" \
    -l rally \
    --drop-densest-as-needed \
    --extend-zooms-if-still-dropping \
    "${INPUT_FILES[@]}"

if [[ -f "${TILES_DIR}/bali-latest.mbtiles" ]]; then
  log "merge dengan basemap -> ${BUNDLE_MBTILES}"
  docker run --rm -v "${TILES_DIR}:/data" "${TIPPECANOE_IMAGE}" \
    tile-join -f -o "/data/${BUNDLE_MBTILES}" \
      "/data/bali-latest.mbtiles" \
      "/data/${OVERLAY_MBTILES}"
  ls -lh "${TILES_DIR}/${BUNDLE_MBTILES}"
else
  log "basemap belum dibuat; lewati tile-join. Jalankan build_tiles.sh dulu kalau ingin bundle."
fi
