#!/usr/bin/env sh
set -eu

: "${SUPABASE_DB_URL:?SUPABASE_DB_URL is required}"

if [ "$#" -ne 1 ]; then
  echo "usage: restore.sh /path/to/supabase.dump" >&2
  exit 2
fi

pg_restore --clean --if-exists --no-owner --dbname "${SUPABASE_DB_URL}" "$1"
