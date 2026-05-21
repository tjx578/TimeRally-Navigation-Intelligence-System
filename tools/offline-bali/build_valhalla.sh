#!/usr/bin/env bash
#
# Build Valhalla tiles (standby engine). Output di ${VALHALLA_DIR}.
#
# Usage:
#   ./build_valhalla.sh
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

cp -f "${BALI_PBF_PATH}" "${VALHALLA_DIR}/${BALI_PBF}"

log "build valhalla tiles via valhalla-scripted (foreground sekali)"
docker run --rm \
  -v "${VALHALLA_DIR}:/custom_files" \
  -e build_admins=True \
  -e build_time_zones=True \
  -e build_elevation=False \
  -e force_rebuild=False \
  -e serve_tiles=False \
  ghcr.io/valhalla/valhalla-scripted:latest \
  2>&1 | tee "${LOG_DIR}/valhalla-build.log"

log "selesai. Cek ${VALHALLA_DIR}"
ls -lh "${VALHALLA_DIR}"
