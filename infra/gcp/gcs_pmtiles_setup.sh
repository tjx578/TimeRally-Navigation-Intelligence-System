#!/usr/bin/env bash
#
# Setup GCS bucket untuk PMTiles publik:
#   1. Pastikan bucket sudah ada (delegasi ke bootstrap.sh).
#   2. Aktifkan public-read pada object PMTiles (allUsers viewer).
#   3. Pasang CORS yang allow GET + Range request dari domain Cloud Run / app.
#   4. Upload bali.pmtiles dari path lokal kalau diberikan.
#
# Tanpa langkah ini, MapLibre + pmtiles akan gagal load dengan error CORS atau
# 403, dan map tampak kosong meskipun style sudah benar.
#
# Usage:
#   PMTILES_LOCAL=/srv/timerally/offline/tiles/bali-latest.mbtiles.pmtiles \
#     ./infra/gcp/gcs_pmtiles_setup.sh
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

PMTILES_OBJECT="${PMTILES_OBJECT:-maps/bali.pmtiles}"
CORS_FILE="$(mktemp -t cors.XXXXXX.json)"

log "bucket: gs://${BUCKET_NAME}"

cat > "${CORS_FILE}" <<EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "HEAD", "OPTIONS"],
    "responseHeader": ["Range", "Content-Range", "Content-Length", "Content-Type", "ETag", "Last-Modified"],
    "maxAgeSeconds": 3600
  }
]
EOF

log "pasang CORS configuration (GET/HEAD/OPTIONS, expose Range header)"
gcloud storage buckets update "gs://${BUCKET_NAME}" --cors-file="${CORS_FILE}"
rm -f "${CORS_FILE}"

# Public read di object level (kalau bucket uniform-bucket-level-access,
# pakai bucket-level allUsers viewer; tetap lebih sempit dari objectAdmin).
log "grant allUsers viewer untuk konten PMTiles"
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="allUsers" \
  --role="roles/storage.objectViewer" >/dev/null

if [[ -n "${PMTILES_LOCAL:-}" ]]; then
  if [[ ! -f "${PMTILES_LOCAL}" ]]; then
    log "file ${PMTILES_LOCAL} tidak ditemukan"
    exit 2
  fi
  log "upload ${PMTILES_LOCAL} -> gs://${BUCKET_NAME}/${PMTILES_OBJECT}"
  gcloud storage cp "${PMTILES_LOCAL}" "gs://${BUCKET_NAME}/${PMTILES_OBJECT}"
fi

log "verifikasi HEAD + Range"
PMTILES_URL="https://storage.googleapis.com/${BUCKET_NAME}/${PMTILES_OBJECT}"
if curl -fsS -I "${PMTILES_URL}" -H "Range: bytes=0-15" >/dev/null 2>&1; then
  log "OK  ${PMTILES_URL}"
else
  log "FAIL HEAD/Range gagal di ${PMTILES_URL} - cek IAM dan keberadaan object"
  exit 1
fi
