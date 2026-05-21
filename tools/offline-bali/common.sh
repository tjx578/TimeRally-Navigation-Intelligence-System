#!/usr/bin/env bash
# Helpers untuk script offline-bali. Source dari script lain.
set -Eeuo pipefail

OFFLINE_BALI_ROOT="${OFFLINE_BALI_ROOT:-/srv/timerally/offline}"
EXTRACTS_DIR="${OFFLINE_BALI_ROOT}/extracts"
TILES_DIR="${OFFLINE_BALI_ROOT}/tiles"
OSRM_DIR="${OFFLINE_BALI_ROOT}/osrm"
VALHALLA_DIR="${OFFLINE_BALI_ROOT}/valhalla/custom_files"
LOG_DIR="${OFFLINE_BALI_ROOT}/logs"

# Default source = Nusa Tenggara (smaller, faster). Override pakai SEED_SOURCE=indonesia.
SEED_SOURCE="${SEED_SOURCE:-nusa-tenggara}"

case "${SEED_SOURCE}" in
  nusa-tenggara)
    SEED_URL="https://download.geofabrik.de/asia/indonesia/nusa-tenggara-latest.osm.pbf"
    SEED_FILE="nusa-tenggara-latest.osm.pbf"
    ;;
  indonesia)
    SEED_URL="https://download.geofabrik.de/asia/indonesia-latest.osm.pbf"
    SEED_FILE="indonesia-latest.osm.pbf"
    ;;
  *)
    echo "Unknown SEED_SOURCE=${SEED_SOURCE}. Pakai nusa-tenggara atau indonesia." >&2
    exit 2
    ;;
esac

BALI_PBF="bali-mainland.osm.pbf"
BALI_MBTILES_DEFAULT="bali-v$(date -u +%Y-%m).mbtiles"
BALI_MBTILES="${BALI_MBTILES:-${BALI_MBTILES_DEFAULT}}"

require_cmd() {
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "[ERR] command '$cmd' tidak ditemukan di PATH." >&2
      return 1
    fi
  done
}

log() {
  printf '[offline-bali] %s\n' "$*"
}

ensure_dirs() {
  mkdir -p "${EXTRACTS_DIR}" "${TILES_DIR}" "${OSRM_DIR}" "${VALHALLA_DIR}" "${LOG_DIR}"
}

script_dir() {
  cd -- "$( dirname -- "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}" )" &>/dev/null && pwd
}
