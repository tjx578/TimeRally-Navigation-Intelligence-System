#!/usr/bin/env bash
#
# Extract Bali mainland dari sumber Geofabrik.
# Output: ${OFFLINE_BALI_ROOT}/extracts/bali-mainland.osm.pbf
#
# Usage:
#   SEED_SOURCE=nusa-tenggara ./extract.sh        # default, lebih cepat
#   SEED_SOURCE=indonesia ./extract.sh            # paling fresh, lebih lambat
#
# Memerlukan: osmium-tool, wget.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd osmium wget
ensure_dirs

cd "${EXTRACTS_DIR}"

if [[ ! -f "${SEED_FILE}" ]]; then
  log "download seed: ${SEED_URL}"
  wget -N "${SEED_URL}"
else
  log "seed sudah ada (${SEED_FILE}); skip download. Hapus manual kalau mau refresh."
fi

POLY_GEOJSON="${HERE}/bali-mainland.geojson"
if [[ ! -f "${POLY_GEOJSON}" ]]; then
  log "polygon Bali tidak ditemukan: ${POLY_GEOJSON}"
  exit 2
fi

log "clip dengan polygon: ${POLY_GEOJSON}"
osmium extract \
  --strategy=complete_ways \
  --overwrite \
  -p "${POLY_GEOJSON}" \
  "${SEED_FILE}" \
  -o "${BALI_PBF}"

log "selesai: $(realpath "${BALI_PBF}")"
ls -lh "${BALI_PBF}"
