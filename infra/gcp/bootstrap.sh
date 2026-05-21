#!/usr/bin/env bash
#
# Bootstrap project GCP: enable API, Artifact Registry, Cloud SQL + PostGIS,
# GCS bucket, VPC firewall, Cloud Run service account, VM routing.
# Idempotent: aman dijalankan ulang.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

log "enable required APIs"
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  vision.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  vpcaccess.googleapis.com \
  servicenetworking.googleapis.com \
  iam.googleapis.com

# ----- Artifact Registry -----
if ! gcloud artifacts repositories describe "${ARTIFACT_REPO}" --location="${REGION}" >/dev/null 2>&1; then
  log "create Artifact Registry ${ARTIFACT_REPO} @ ${REGION}"
  gcloud artifacts repositories create "${ARTIFACT_REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Time Rally container images"
else
  log "Artifact Registry ${ARTIFACT_REPO} sudah ada"
fi

# ----- Cloud SQL -----
if ! gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" >/dev/null 2>&1; then
  log "create Cloud SQL instance ${CLOUD_SQL_INSTANCE} (${CLOUD_SQL_TIER})"
  gcloud sql instances create "${CLOUD_SQL_INSTANCE}" \
    --database-version=POSTGRES_16 \
    --tier="${CLOUD_SQL_TIER}" \
    --region="${REGION}" \
    --storage-size=100GB \
    --storage-type=SSD \
    --availability-type=zonal \
    --backup-start-time=18:00
else
  log "Cloud SQL ${CLOUD_SQL_INSTANCE} sudah ada"
fi

if ! gcloud sql databases describe "${CLOUD_SQL_DB}" --instance="${CLOUD_SQL_INSTANCE}" >/dev/null 2>&1; then
  log "create database ${CLOUD_SQL_DB}"
  gcloud sql databases create "${CLOUD_SQL_DB}" --instance="${CLOUD_SQL_INSTANCE}"
else
  log "database ${CLOUD_SQL_DB} sudah ada"
fi

if ! gcloud sql users list --instance="${CLOUD_SQL_INSTANCE}" --format='value(name)' | grep -qx "${CLOUD_SQL_USER}"; then
  PASSWORD="$(openssl rand -base64 24)"
  log "create user ${CLOUD_SQL_USER}; password disimpan di Secret Manager"
  gcloud sql users create "${CLOUD_SQL_USER}" \
    --instance="${CLOUD_SQL_INSTANCE}" \
    --password="${PASSWORD}"
  printf '%s' "${PASSWORD}" | gcloud secrets create "${SECRET_PREFIX}-db-password" \
    --data-file=- --replication-policy=automatic 2>/dev/null || \
    printf '%s' "${PASSWORD}" | gcloud secrets versions add "${SECRET_PREFIX}-db-password" --data-file=-
else
  log "user ${CLOUD_SQL_USER} sudah ada"
fi

# ----- Cloud Storage bucket -----
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" >/dev/null 2>&1; then
  log "create GCS bucket gs://${BUCKET_NAME}"
  gcloud storage buckets create "gs://${BUCKET_NAME}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
else
  log "bucket gs://${BUCKET_NAME} sudah ada"
fi

# Sub-prefix yang dipakai aplikasi (sekedar marker; tidak wajib).
for prefix in exports/ photos/ maps/ backups/; do
  printf 'placeholder\n' | gcloud storage cp - "gs://${BUCKET_NAME}/${prefix}.keep" --quiet >/dev/null 2>&1 || true
done

# ----- Cloud Run service account -----
SA_EMAIL="${SECRET_PREFIX}-runtime@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" >/dev/null 2>&1; then
  log "create service account ${SA_EMAIL}"
  gcloud iam service-accounts create "${SECRET_PREFIX}-runtime" \
    --display-name="Time Rally runtime SA"
fi

log "grant least-privilege IAM"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudsql.client" --condition=None >/dev/null
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor" --condition=None >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://${BUCKET_NAME}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin" >/dev/null

# ----- Firewall untuk VM routing -----
if ! gcloud compute firewall-rules describe allow-timerally-web >/dev/null 2>&1; then
  log "firewall allow-timerally-web (80/443)"
  gcloud compute firewall-rules create allow-timerally-web \
    --allow=tcp:80,tcp:443 \
    --target-tags=timerally-routing \
    --source-ranges=0.0.0.0/0
fi

log "bootstrap selesai. Lanjutkan ke cloud_sql_migrate.sh, build_and_push.sh, deploy_*.sh"
