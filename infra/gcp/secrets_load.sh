#!/usr/bin/env bash
#
# Load local .env.gcp values into Secret Manager. The .env.gcp file must never
# be committed.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
ROOT="$( cd -- "${HERE}/../.." &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

ENV_FILE="${ENV_FILE:-${ROOT}/.env.gcp}"
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
else
  log "${ENV_FILE} tidak ditemukan; hanya env shell aktif yang dipakai"
fi

put_secret() {
  local name="$1"
  local value="$2"
  if [[ -z "${value}" ]]; then
    log "skip secret ${name} (kosong)"
    return 0
  fi
  if gcloud secrets describe "${name}" >/dev/null 2>&1; then
    printf '%s' "${value}" | gcloud secrets versions add "${name}" --data-file=-
  else
    printf '%s' "${value}" | gcloud secrets create "${name}" \
      --data-file=- \
      --replication-policy=automatic
  fi
}

put_secret "${SECRET_PREFIX}-database-url" "${DATABASE_URL:-}"
put_secret "${SECRET_PREFIX}-google-maps-api-key" "${GOOGLE_MAPS_API_KEY:-}"
put_secret "${SECRET_PREFIX}-sentry-dsn" "${SENTRY_DSN:-}"

log "secret sync selesai"
