#!/usr/bin/env bash
# Helpers GCP. Source dari script lain.
set -Eeuo pipefail

COMMON_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
REPO_ROOT="$( cd -- "${COMMON_DIR}/../.." &>/dev/null && pwd )"
ENV_FILE="${ENV_FILE:-${REPO_ROOT}/.env.gcp}"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

: "${PROJECT_ID:?PROJECT_ID belum diset. Contoh: export PROJECT_ID=timerally-prod}"
: "${REGION:=asia-southeast2}"
: "${ROUTING_ZONE:=${REGION}-a}"

ARTIFACT_REPO="${ARTIFACT_REPO:-timerally}"
ARTIFACT_HOST="${REGION}-docker.pkg.dev"
ARTIFACT_BASE="${ARTIFACT_HOST}/${PROJECT_ID}/${ARTIFACT_REPO}"

CLOUD_SQL_INSTANCE="${CLOUD_SQL_INSTANCE:-timerally-db}"
CLOUD_SQL_TIER="${CLOUD_SQL_TIER:-db-custom-2-8192}"
CLOUD_SQL_DB="${CLOUD_SQL_DB:-timerally}"
CLOUD_SQL_USER="${CLOUD_SQL_USER:-timerally_app}"

BUCKET_NAME="${BUCKET_NAME:-${PROJECT_ID}-assets}"
SECRET_PREFIX="${SECRET_PREFIX:-timerally}"

ROUTING_VM_NAME="${ROUTING_VM_NAME:-timerally-routing-bali}"
ROUTING_VM_MACHINE_TYPE="${ROUTING_VM_MACHINE_TYPE:-n2-standard-8}"
ROUTING_VM_DISK_GB="${ROUTING_VM_DISK_GB:-300}"
ROUTING_VM_DISK_TYPE="${ROUTING_VM_DISK_TYPE:-pd-ssd}"

API_SERVICE="${API_SERVICE:-timerally-api}"
ROUTING_GATEWAY_SERVICE="${ROUTING_GATEWAY_SERVICE:-timerally-routing-gateway}"
PLACE_RESOLVER_SERVICE="${PLACE_RESOLVER_SERVICE:-timerally-place-resolver}"
TRACKING_GATEWAY_SERVICE="${TRACKING_GATEWAY_SERVICE:-timerally-tracking-gateway}"
WEB_SERVICE="${WEB_SERVICE:-timerally-web}"

IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date -u +%Y%m%d%H%M)}"

log() {
  printf '[gcp:%s] %s\n' "$(date -u +%H:%M:%S)" "$*"
}

require_cmd() {
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      log "command '$cmd' tidak ditemukan di PATH"
      return 1
    fi
  done
}

ensure_project() {
  gcloud config set project "${PROJECT_ID}" >/dev/null
  log "active project: ${PROJECT_ID}"
}
