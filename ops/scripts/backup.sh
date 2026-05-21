#!/usr/bin/env sh
set -eu

: "${BACKUP_ROOT:=/opt/time-rally/backups}"
: "${SUPABASE_DB_URL:?SUPABASE_DB_URL is required}"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="${BACKUP_ROOT}/${timestamp}"
mkdir -p "${backup_dir}"

pg_dump --format=custom --no-owner --no-acl --dbname "${SUPABASE_DB_URL}" \
  --file "${backup_dir}/supabase.dump"

if [ -n "${STORAGE_BACKUP_BUCKET:-}" ] && command -v aws >/dev/null 2>&1; then
  aws s3 sync "${backup_dir}" "s3://${STORAGE_BACKUP_BUCKET}/${timestamp}/"
fi

printf 'backup_dir=%s\n' "${backup_dir}"
