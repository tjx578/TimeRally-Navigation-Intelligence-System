#!/usr/bin/env bash
#
# Apply Cloud SQL compatible migrations. Requires cloud-sql-proxy and psql.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
ROOT="$( cd -- "${HERE}/../.." &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud psql cloud-sql-proxy pg_isready
ensure_project

LOCAL_PORT="${LOCAL_PORT:-5433}"
INSTANCE_CONNECTION_NAME="$(gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" --format='value(connectionName)')"
DB_PASSWORD="$(gcloud secrets versions access latest --secret="${SECRET_PREFIX}-db-password")"

log "start Cloud SQL Auth Proxy on 127.0.0.1:${LOCAL_PORT}"
cloud-sql-proxy "${INSTANCE_CONNECTION_NAME}" --address 127.0.0.1 --port "${LOCAL_PORT}" &
PROXY_PID="$!"
trap 'kill "${PROXY_PID}" >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 30); do
  if pg_isready -h 127.0.0.1 -p "${LOCAL_PORT}" -U "${CLOUD_SQL_USER}" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

export PGPASSWORD="${DB_PASSWORD}"
for migration in "${ROOT}"/supabase/migrations/cloudsql/*.sql; do
  [[ -e "${migration}" ]] || continue
  log "apply $(basename "${migration}")"
  psql \
    --host=127.0.0.1 \
    --port="${LOCAL_PORT}" \
    --username="${CLOUD_SQL_USER}" \
    --dbname="${CLOUD_SQL_DB}" \
    --set=ON_ERROR_STOP=1 \
    --file="${migration}"
done

log "Cloud SQL migrations selesai"
