#!/usr/bin/env bash
#
# Redeploy Cloud Run `timerally-web` dengan TAG unik sehingga revision baru
# selalu di-pull. Mencegah kasus "image latest cached, deploy tidak terlihat".
#
# Steps:
#   1. Tulis ulang apps/web-map-console/.env.production (override via env var).
#   2. Build image via Cloud Build (tag = timestamp UTC).
#   3. Deploy ke Cloud Run dengan image baru.
#   4. Update traffic ke revision terbaru.
#
# Usage:
#   ./infra/gcp/redeploy_web.sh
#
# Override (opsional):
#   VITE_API_BASE_URL=""                       # same-origin lewat nginx
#   VITE_MAP_STYLE_URL="/maps/bali-style.json"
#   VITE_PMTILES_URL="https://storage.googleapis.com/${BUCKET_NAME}/maps/bali.pmtiles"
#   VITE_PMTILES_READY="true"
#   VITE_MAP_CENTER_LNG="115.1889"
#   VITE_MAP_CENTER_LAT="-8.4095"
#   VITE_MAP_ZOOM="9"
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

TAG="${WEB_IMAGE_TAG:-$(date -u +%Y%m%d%H%M%S)}"
IMAGE="${ARTIFACT_BASE}/web:${TAG}"

ENV_FILE_PATH="${REPO_ROOT}/apps/web-map-console/.env.production"

log "writing ${ENV_FILE_PATH}"
cat > "${ENV_FILE_PATH}" <<EOF
VITE_API_BASE_URL=${VITE_API_BASE_URL:-}
VITE_MAP_STYLE_URL=${VITE_MAP_STYLE_URL:-/maps/bali-style.json}
VITE_PMTILES_URL=${VITE_PMTILES_URL:-https://storage.googleapis.com/${BUCKET_NAME}/maps/bali.pmtiles}
VITE_PMTILES_READY=${VITE_PMTILES_READY:-true}
VITE_MAP_CENTER_LNG=${VITE_MAP_CENTER_LNG:-115.1889}
VITE_MAP_CENTER_LAT=${VITE_MAP_CENTER_LAT:-${VITE_MAP_CENTER_LAT:-115.1889}}
VITE_MAP_CENTER_LAT=${VITE_MAP_CENTER_LAT:--8.4095}
VITE_MAP_ZOOM=${VITE_MAP_ZOOM:-9}
VITE_ROUTING_PUBLIC_BASE=${VITE_ROUTING_PUBLIC_BASE:-}
VITE_SENTRY_DSN=${VITE_SENTRY_DSN:-}
VITE_SENTRY_ENVIRONMENT=${VITE_SENTRY_ENVIRONMENT:-production}
VITE_SENTRY_TRACES_SAMPLE_RATE=${VITE_SENTRY_TRACES_SAMPLE_RATE:-0.05}
EOF
# Hapus duplikat VITE_MAP_CENTER_LAT yang muncul karena fallback double-resolve.
# Ambil yang terakhir saja.
sed -i.bak '/^VITE_MAP_CENTER_LAT=.*115\.1889$/d' "${ENV_FILE_PATH}" || true
rm -f "${ENV_FILE_PATH}.bak"

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
log "lanjut verifikasi via ./infra/gcp/check_web_deploy.sh"
