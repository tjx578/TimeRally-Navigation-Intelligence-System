#!/usr/bin/env bash
#
# Diagnose Cloud Run timerally-web setelah deploy.
# Otomatisasi langkah verifikasi:
#   1. Revision aktif & image tag.
#   2. /maps/bali-style.json apakah ada dan punya marker `pmtiles://` + `transportation`.
#   3. Asset JS terakhir di index.html, lalu grep marker env build:
#         bali-style.json, bali.pmtiles, timerally-bali-maps, VITE_MAP_STYLE_URL.
#   4. /v1/healthz lewat nginx (kalau proxy /v1/ di-include).
#
# Exit code:
#   0 = semua marker hijau
#   1 = ada marker yang gagal
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud curl

WEB_URL="${WEB_URL:-$(gcloud run services describe "${WEB_SERVICE}" \
  --region "${REGION}" \
  --format='value(status.url)' 2>/dev/null || true)}"

if [[ -z "${WEB_URL}" ]]; then
  log "tidak dapat menemukan URL Cloud Run ${WEB_SERVICE}. Set WEB_URL manual."
  exit 1
fi

log "service URL: ${WEB_URL}"

pass=0
fail=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass=$((pass + 1))
    log "OK   ${label}"
  else
    fail=$((fail + 1))
    log "FAIL ${label}"
  fi
}

# ----- 1. Revision aktif -----
log "1. revision aktif"
gcloud run services describe "${WEB_SERVICE}" \
  --region "${REGION}" \
  --format="yaml(status.latestReadyRevisionName,status.traffic,spec.template.spec.containers[0].image)" || true

# ----- 2. Style file -----
log "2. /maps/bali-style.json"
STYLE_BODY="$(curl -fsS "${WEB_URL}/maps/bali-style.json" || true)"
if [[ -n "${STYLE_BODY}" ]]; then
  printf '%s\n' "${STYLE_BODY}" | head -40
  check "style body mengandung pmtiles://" bash -c "printf '%s' \"${STYLE_BODY}\" | grep -q 'pmtiles://'"
  check "style body mengandung 'transportation'" bash -c "printf '%s' \"${STYLE_BODY}\" | grep -q 'transportation'"
else
  log "FAIL style body kosong / 404"
  fail=$((fail + 1))
fi

# ----- 3. Asset JS terbaru -----
log "3. index.html -> asset JS terbaru"
INDEX_HTML="$(curl -fsS "${WEB_URL}/" || true)"
JS_PATH="$(printf '%s' "${INDEX_HTML}" | grep -o '/assets/[^"]*\.js' | head -1 || true)"
if [[ -z "${JS_PATH}" ]]; then
  log "FAIL tidak menemukan /assets/*.js di index"
  fail=$((fail + 1))
else
  log "asset JS: ${JS_PATH}"
  JS_BODY="$(curl -fsS "${WEB_URL}${JS_PATH}" || true)"
  for marker in "bali-style.json" "bali.pmtiles" "VITE_MAP_STYLE_URL"; do
    if printf '%s' "${JS_BODY}" | grep -q "${marker}"; then
      pass=$((pass + 1))
      log "OK   bundle JS mengandung ${marker}"
    else
      fail=$((fail + 1))
      log "FAIL bundle JS TIDAK mengandung ${marker}"
    fi
  done
fi

# ----- 4. /v1/healthz lewat nginx -----
log "4. /v1/healthz via reverse proxy nginx"
if curl -fsS "${WEB_URL}/v1/healthz" >/dev/null 2>&1; then
  pass=$((pass + 1))
  log "OK   nginx -> API /v1/healthz"
else
  fail=$((fail + 1))
  log "FAIL /v1/healthz tidak respons via nginx (cek proxy_pass)"
fi

log "----"
log "RESULT: ${pass} passed, ${fail} failed"
exit $(( fail > 0 ? 1 : 0 ))
