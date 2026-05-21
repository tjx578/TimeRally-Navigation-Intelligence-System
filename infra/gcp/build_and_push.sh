#!/usr/bin/env bash
#
# Build all production images through Google Cloud Build and push them to
# Artifact Registry. This avoids local Docker differences on Windows laptops.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

SUBSTITUTIONS=(
  "_REGION=${REGION}"
  "_REPOSITORY=${ARTIFACT_REPO}"
  "_IMAGE_TAG=${IMAGE_TAG}"
  "_VITE_API_BASE_URL=${VITE_API_BASE_URL:-${PUBLIC_API_URL:-}}"
  "_VITE_ROUTING_PUBLIC_BASE=${VITE_ROUTING_PUBLIC_BASE:-${PUBLIC_API_URL:-}}"
  "_VITE_PMTILES_URL=${VITE_PMTILES_URL:-}"
  "_VITE_SUPABASE_URL=${VITE_SUPABASE_URL:-}"
  "_VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY:-}"
  "_VITE_SENTRY_DSN=${VITE_SENTRY_DSN:-}"
)

log "submit Cloud Build for tag ${IMAGE_TAG}"
gcloud builds submit \
  --config="${HERE}/cloudbuild.yaml" \
  --substitutions="$(IFS=,; echo "${SUBSTITUTIONS[*]}")" \
  .

log "images pushed under ${ARTIFACT_BASE}: ${IMAGE_TAG}"
