#!/usr/bin/env bash
#
# Build OSRM MLD graph untuk Bali. Output di ${OSRM_DIR}/bali-mainland.osrm*.
#
# Usage:
#   ./build_routing.sh                              # default profile car
#   OSRM_PROFILE=/opt/bicycle.lua ./build_routing.sh
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

cp -f "${BALI_PBF_PATH}" "${OSRM_DIR}/${BALI_PBF}"

OSRM_IMAGE="${OSRM_IMAGE:-ghcr.io/project-osrm/osrm-backend:latest}"
OSRM_PROFILE="${OSRM_PROFILE:-/opt/car.lua}"

log "osrm-extract pakai profile ${OSRM_PROFILE}"
docker run --rm -t -v "${OSRM_DIR}:/data" "${OSRM_IMAGE}" \
  osrm-extract -p "${OSRM_PROFILE}" "/data/${BALI_PBF}" \
  2>&1 | tee "${LOG_DIR}/osrm-extract.log"

log "osrm-partition"
docker run --rm -t -v "${OSRM_DIR}:/data" "${OSRM_IMAGE}" \
  osrm-partition "/data/bali-mainland.osrm" \
  2>&1 | tee "${LOG_DIR}/osrm-partition.log"

log "osrm-customize"
docker run --rm -t -v "${OSRM_DIR}:/data" "${OSRM_IMAGE}" \
  osrm-customize "/data/bali-mainland.osrm" \
  2>&1 | tee "${LOG_DIR}/osrm-customize.log"

log "selesai. Artefak:"
ls -lh "${OSRM_DIR}/bali-mainland.osrm"*
