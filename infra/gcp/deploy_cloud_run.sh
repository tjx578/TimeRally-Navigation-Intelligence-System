#!/usr/bin/env bash
#
# Deploy stateless TimeRally services to Cloud Run. Routing engines and tiles
# remain on Compute Engine VM; this script deploys API, gateways, resolver,
# tracking, OCR worker, and static web nginx container.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

SA_EMAIL="${SECRET_PREFIX}-runtime@${PROJECT_ID}.iam.gserviceaccount.com"
CLOUD_SQL_CONNECTION="${PROJECT_ID}:${REGION}:${CLOUD_SQL_INSTANCE}"

secret_flag() {
  local env_name="$1"
  local secret_name="$2"
  if gcloud secrets describe "${secret_name}" >/dev/null 2>&1; then
    printf '%s=%s:latest' "${env_name}" "${secret_name}"
  fi
}

join_by_comma() {
  local IFS=,
  echo "$*"
}

run_deploy() {
  local service="$1"
  local image="$2"
  shift 2
  log "deploy Cloud Run ${service}"
  gcloud run deploy "${service}" \
    --image="${image}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --service-account="${SA_EMAIL}" \
    "$@"
}

API_IMAGE="${ARTIFACT_BASE}/api:${IMAGE_TAG}"
ROUTING_IMAGE="${ARTIFACT_BASE}/routing-gateway:${IMAGE_TAG}"
PLACE_IMAGE="${ARTIFACT_BASE}/place-resolver:${IMAGE_TAG}"
TRACKING_IMAGE="${ARTIFACT_BASE}/tracking-gateway:${IMAGE_TAG}"
OCR_IMAGE="${ARTIFACT_BASE}/ocr-worker:${IMAGE_TAG}"
WEB_IMAGE="${ARTIFACT_BASE}/web:${IMAGE_TAG}"

run_deploy "${OCR_SERVICE}" "${OCR_IMAGE}" \
  --cpu="${OCR_CPU:-1}" \
  --memory="${OCR_MEMORY:-1Gi}" \
  --min-instances="${OCR_MIN_INSTANCES:-0}" \
  --set-env-vars="APP_ENV=production,OCR_ENGINE=${OCR_ENGINE:-google_vision},OCR_MIN_CONFIDENCE=${OCR_MIN_CONFIDENCE:-0.1}"

OCR_WORKER_URL_DEFAULT="$(gcloud run services describe "${OCR_SERVICE}" \
  --region="${REGION}" \
  --format='value(status.url)')"

API_SECRETS=()
for item in \
  "$(secret_flag DATABASE_URL "${SECRET_PREFIX}-database-url")" \
  "$(secret_flag SENTRY_DSN "${SECRET_PREFIX}-sentry-dsn")"; do
  [[ -n "${item}" ]] && API_SECRETS+=("${item}")
done

API_ARGS=(
  --cpu="${API_CPU:-2}"
  --memory="${API_MEMORY:-4Gi}"
  --min-instances="${API_MIN_INSTANCES:-1}"
  --add-cloudsql-instances="${CLOUD_SQL_CONNECTION}"
  --set-env-vars="APP_ENV=production,PUBLIC_API_URL=${PUBLIC_API_URL:-},PUBLIC_WEB_URL=${PUBLIC_WEB_URL:-},API_CORS_ORIGINS=${API_CORS_ORIGINS:-${PUBLIC_WEB_URL:-}},EXPORTS_ROOT=${EXPORTS_ROOT:-gs://${BUCKET_NAME}/exports},GCS_BUCKET_NAME=${BUCKET_NAME},GCS_EXPORTS_PREFIX=${GCS_EXPORTS_PREFIX:-exports},GCS_PHOTOS_PREFIX=${GCS_PHOTOS_PREFIX:-photos},KNOWLEDGE_ROOT=/app/data/curated,ROUTING_GATEWAY_URL=${ROUTING_GATEWAY_URL:-http://routing-gateway:8010},OCR_WORKER_URL=${OCR_WORKER_URL:-${OCR_WORKER_URL_DEFAULT}},OCR_WORKER_TIMEOUT_SECONDS=${OCR_WORKER_TIMEOUT_SECONDS:-90},SENTRY_ENVIRONMENT=${SENTRY_ENVIRONMENT:-production},SENTRY_TRACES_SAMPLE_RATE=${SENTRY_TRACES_SAMPLE_RATE:-0.05}"
)
if [[ "${#API_SECRETS[@]}" -gt 0 ]]; then
  API_ARGS+=(--set-secrets="$(join_by_comma "${API_SECRETS[@]}")")
fi
run_deploy "${API_SERVICE}" "${API_IMAGE}" "${API_ARGS[@]}"

ROUTING_SECRETS=()
GOOGLE_SECRET="$(secret_flag GOOGLE_MAPS_API_KEY "${SECRET_PREFIX}-google-maps-api-key")"
[[ -n "${GOOGLE_SECRET}" ]] && ROUTING_SECRETS+=("${GOOGLE_SECRET}")
ROUTING_ARGS=(
  --cpu="${ROUTING_CPU:-1}"
  --memory="${ROUTING_MEMORY:-1Gi}"
  --min-instances="${ROUTING_MIN_INSTANCES:-1}"
  --set-env-vars="APP_ENV=production,ROUTING_DEFAULT_PROVIDER=${ROUTING_DEFAULT_PROVIDER:-auto},ROUTING_PROVIDER_PRIMARY=${ROUTING_PROVIDER_PRIMARY:-osrm},ROUTING_PROVIDER_FALLBACK=${ROUTING_PROVIDER_FALLBACK:-valhalla},ROUTING_PROVIDER_STANDBY=${ROUTING_PROVIDER_STANDBY:-graphhopper},ROUTING_ALLOW_MOCK_FALLBACK=${ROUTING_ALLOW_MOCK_FALLBACK:-false},OSRM_URL=${OSRM_URL:-},VALHALLA_URL=${VALHALLA_URL:-},GRAPHHOPPER_URL=${GRAPHHOPPER_URL:-},GOOGLE_ENABLED=${GOOGLE_ENABLED:-false}"
)
if [[ "${#ROUTING_SECRETS[@]}" -gt 0 ]]; then
  ROUTING_ARGS+=(--set-secrets="$(join_by_comma "${ROUTING_SECRETS[@]}")")
fi
run_deploy "${ROUTING_GATEWAY_SERVICE}" "${ROUTING_IMAGE}" "${ROUTING_ARGS[@]}"

PLACE_ARGS=(
  --cpu="${PLACE_CPU:-1}"
  --memory="${PLACE_MEMORY:-1Gi}"
  --min-instances="${PLACE_MIN_INSTANCES:-0}"
  --set-env-vars="APP_ENV=production,KNOWLEDGE_ROOT=/app/data/curated,NOMINATIM_URL=${NOMINATIM_URL:-},GOOGLE_ENABLED=${GOOGLE_ENABLED:-false}"
)
if [[ -n "${GOOGLE_SECRET}" ]]; then
  PLACE_ARGS+=(--set-secrets="${GOOGLE_SECRET}")
fi
run_deploy "${PLACE_RESOLVER_SERVICE}" "${PLACE_IMAGE}" "${PLACE_ARGS[@]}"

run_deploy "${TRACKING_GATEWAY_SERVICE}" "${TRACKING_IMAGE}" \
  --cpu="${TRACKING_CPU:-1}" \
  --memory="${TRACKING_MEMORY:-1Gi}" \
  --min-instances="${TRACKING_MIN_INSTANCES:-0}" \
  --set-env-vars="APP_ENV=production"

run_deploy "${WEB_SERVICE}" "${WEB_IMAGE}" \
  --cpu="${WEB_CPU:-1}" \
  --memory="${WEB_MEMORY:-512Mi}" \
  --min-instances="${WEB_MIN_INSTANCES:-1}"

log "Cloud Run deploy selesai"
