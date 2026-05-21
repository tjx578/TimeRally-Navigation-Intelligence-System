#!/usr/bin/env bash
#
# Smoke test stack offline Bali sesuai deep-research-report (3).
#
# Usage:
#   TILES_HOST=http://192.168.50.10:8080 OSRM_HOST=http://192.168.50.10:5000 ./smoke_tests.sh
#
# Default: localhost. Test ini idempotent; jalankan ulang setelah deploy.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

TILES_HOST="${TILES_HOST:-http://localhost:8080}"
OSRM_HOST="${OSRM_HOST:-http://localhost:5000}"
VALHALLA_HOST="${VALHALLA_HOST:-http://localhost:8002}"

pass=0
fail=0

check() {
  local label="$1"
  shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
    log "OK   ${label}"
  else
    fail=$((fail + 1))
    log "FAIL ${label}"
  fi
}

# 1. Artefak ada
check "extract pbf"  test -s "${EXTRACTS_DIR}/${BALI_PBF}"
check "mbtiles"      bash -c "ls ${TILES_DIR}/bali-*.mbtiles >/dev/null 2>&1"
check "osrm graph"   test -s "${OSRM_DIR}/bali-mainland.osrm"

# 2. Tile server
check "tiles HTTP 200" bash -c "curl -fsS -o /dev/null -w '%{http_code}' '${TILES_HOST}/' | grep -q '^200$'"

# 3. OSRM endpoints
check "osrm nearest" bash -c \
  "curl -fsS '${OSRM_HOST}/nearest/v1/driving/115.212629,-8.670458?number=1' | grep -q '\"code\":\"Ok\"'"
check "osrm route" bash -c \
  "curl -fsS '${OSRM_HOST}/route/v1/driving/115.212629,-8.670458;115.262153,-8.506853?steps=true&geometries=geojson&overview=full' | grep -q '\"code\":\"Ok\"'"
check "osrm table" bash -c \
  "curl -fsS '${OSRM_HOST}/table/v1/driving/115.212629,-8.670458;115.262153,-8.506853;114.960000,-8.200000?annotations=distance,duration' | grep -q '\"code\":\"Ok\"'"
check "osrm match" bash -c \
  "curl -fsS '${OSRM_HOST}/match/v1/driving/115.212629,-8.670458;115.220000,-8.660000;115.262153,-8.506853?geometries=geojson&overview=full&radiuses=20;20;20' | grep -q '\"code\":\"Ok\"'"

# 4. (Opsional) Valhalla status
if curl -fsS "${VALHALLA_HOST}/status" >/dev/null 2>&1; then
  check "valhalla status" bash -c \
    "curl -fsS '${VALHALLA_HOST}/status' | grep -q version"
else
  log "SKIP valhalla status (host ${VALHALLA_HOST} tidak merespons)"
fi

log "----"
log "RESULT: ${pass} passed, ${fail} failed"
exit $(( fail > 0 ? 1 : 0 ))
