#!/usr/bin/env bash
#
# Redeploy Cloud Run `timerally-web` dengan TAG unik dan style PMTiles yang
# di-substitute dari template. Mengatasi 3 akar masalah dari audit terakhir:
#   1. Vite tidak boleh pakai ARG default "" yang meng-override .env.production.
#   2. bali-style.json tidak boleh hard-code bucket name; pakai template.
#   3. Tag image harus unik tiap deploy supaya Cloud Run mengambil revision baru.
#
# Usage:
#   ./infra/gcp/redeploy_web.sh
#
# Override env:
#   PMTILES_URL          = URL absolut ke bali.pmtiles (https://storage.googleapis.com/...).
#                          Default: dibangun dari BUCKET_NAME (lihat common.sh).
#   VITE_MAP_STYLE_URL   = path style.json yang dipakai frontend (default /maps/bali-style.json).
#   VITE_API_BASE_URL    = "" untuk same-origin via nginx.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

TAG="${WEB_IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
IMAGE="${ARTIFACT_BASE}/web:${TAG}"

ENV_FILE_PATH="${REPO_ROOT}/apps/web-map-console/.env.production"
TEMPLATE_PATH="${REPO_ROOT}/apps/web-map-console/public/maps/bali-style.template.json"
STYLE_OUT_PATH="${REPO_ROOT}/apps/web-map-console/public/maps/bali-style.json"

PMTILES_URL_VALUE="${PMTILES_URL:-https://storage.googleapis.com/${BUCKET_NAME}/maps/bali.pmtiles}"
STYLE_VALUE="${VITE_MAP_STYLE_URL:-/maps/bali-style.json}"

log "PMTILES_URL=${PMTILES_URL_VALUE}"

# ----- 1. Tulis .env.production -----
log "writing ${ENV_FILE_PATH}"
cat > "${ENV_FILE_PATH}" <<EOF
VITE_API_BASE_URL=${VITE_API_BASE_URL:-}
VITE_MAP_STYLE_URL=${STYLE_VALUE}
VITE_PMTILES_URL=${PMTILES_URL_VALUE}
VITE_PMTILES_READY=${VITE_PMTILES_READY:-true}
VITE_MAP_CENTER_LNG=${VITE_MAP_CENTER_LNG:-115.1889}
VITE_MAP_CENTER_LAT=${VITE_MAP_CENTER_LAT:--8.4095}
VITE_MAP_ZOOM=${VITE_MAP_ZOOM:-9}
VITE_ROUTING_PUBLIC_BASE=${VITE_ROUTING_PUBLIC_BASE:-}
VITE_SENTRY_DSN=${VITE_SENTRY_DSN:-}
VITE_SENTRY_ENVIRONMENT=${VITE_SENTRY_ENVIRONMENT:-production}
VITE_SENTRY_TRACES_SAMPLE_RATE=${VITE_SENTRY_TRACES_SAMPLE_RATE:-0.05}
EOF

# ----- 2. Render style dari template -----
if [[ ! -f "${TEMPLATE_PATH}" ]]; then
  log "template style tidak ditemukan: ${TEMPLATE_PATH}"
  exit 2
fi
log "render ${STYLE_OUT_PATH} dari template"
sed "s|__PMTILES_URL__|${PMTILES_URL_VALUE}|g" "${TEMPLATE_PATH}" > "${STYLE_OUT_PATH}"

# ----- 3. Build image via Cloud Build -----
log "building web image -> ${IMAGE}"
CLOUDBUILD_TMP="$(mktemp -t cloudbuild-web.XXXXXX.yaml)"
cat > "${CLOUDBUILD_TMP}" <<EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-f'
      - 'apps/web-map-console/Dockerfile'
      - '-t'
      - '${IMAGE}'
      - '.'
images:
  - '${IMAGE}'
options:
  logging: CLOUD_LOGGING_ONLY
EOF
gcloud builds submit --config "${CLOUDBUILD_TMP}" "${REPO_ROOT}"
rm -f "${CLOUDBUILD_TMP}"

# ----- 4. Deploy + shift traffic -----
log "deploying ${WEB_SERVICE} (${IMAGE})"
gcloud run deploy "${WEB_SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 512Mi \
  --min-instances 1 \
  --max-instances 3 \
  --port 8080

log "shift 100% traffic ke revision terbaru"
gcloud run services update-traffic "${WEB_SERVICE}" \
  --region "${REGION}" \
  --to-latest

WEB_URL="$(gcloud run services describe "${WEB_SERVICE}" \
  --region "${REGION}" \
  --format='value(status.url)')"

log "deploy selesai: ${WEB_URL}"
log "verifikasi: ./infra/gcp/check_web_deploy.sh"
