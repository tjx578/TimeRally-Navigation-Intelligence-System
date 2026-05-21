#!/usr/bin/env bash
#
# Build vector MBTiles untuk Bali pakai Tilemaker (OpenMapTiles-compatible).
#
# Usage:
#   ./build_tiles.sh                                # default tag bulan UTC
#   BALI_MBTILES=bali-v2026-05.mbtiles ./build_tiles.sh
#
# Memerlukan: docker
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd docker
ensure_dirs

BALI_PBF_PATH="${EXTRACTS_DIR}/${BALI_PBF}"
if [[ ! -f "${BALI_PBF_PATH}" ]]; then
  log "${BALI_PBF_PATH} belum ada. Jalankan ./extract.sh dulu."
  exit 2
fi

cp -f "${BALI_PBF_PATH}" "${TILES_DIR}/${BALI_PBF}"
mkdir -p "${TILES_DIR}/tmp"

log "build MBTiles: ${TILES_DIR}/${BALI_MBTILES}"
docker run --rm --pull always \
  -v "${TILES_DIR}":/data \
  ghcr.io/systemed/tilemaker:master \
  /data/${BALI_PBF} \
  --output /data/${BALI_MBTILES} \
  --store /data/tmp \
  2>&1 | tee "${LOG_DIR}/tilemaker.log"

log "selesai: $(realpath "${TILES_DIR}/${BALI_MBTILES}")"
ls -lh "${TILES_DIR}/${BALI_MBTILES}"

# Symlink "latest" untuk konsistensi nama di compose.
ln -sfn "${BALI_MBTILES}" "${TILES_DIR}/bali-latest.mbtiles"
log "symlink: ${TILES_DIR}/bali-latest.mbtiles -> ${BALI_MBTILES}"
