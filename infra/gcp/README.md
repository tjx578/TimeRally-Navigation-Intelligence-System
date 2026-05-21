# Google Cloud Deployment

Target deploy alternatif untuk Time Rally Navigation Intelligence System, mengikuti rancangan
"Google Cloud-only cloud stack". Stack ini **paralel** dengan path Supabase + Hostinger yang
sudah ada di `infra/compose/docker-compose.prod.yml` — pilih satu sebagai target produksi.

## Komponen

| Layer        | Service GCP                                | Catatan |
|--------------|---------------------------------------------|---------|
| API/web stateless | Cloud Run                              | FastAPI + nginx static frontend |
| Routing engines   | Compute Engine VM (`n2-standard-8`)    | OSRM primary + Valhalla backup + TileServer GL + PMTiles |
| Database          | Cloud SQL PostgreSQL 16 + PostGIS      | Pengganti Supabase Postgres |
| Object storage    | Cloud Storage bucket                   | exports / photos / mbtiles backup |
| Secret management | Secret Manager                         | DB URL, API keys, signing secret |
| Container registry| Artifact Registry                      | Image untuk Cloud Run |
| Monitoring        | Cloud Logging + Cloud Monitoring       | Otomatis untuk Cloud Run; Ops Agent untuk VM |

## File di folder ini

| File | Fungsi |
|------|--------|
| `bootstrap.sh`        | Enable API, buat Artifact Registry, Cloud SQL, GCS bucket, firewall, service account. Idempotent. |
| `build_and_push.sh`   | Build & push 4 image API/services + 1 image web ke Artifact Registry. |
| `deploy_cloud_run.sh` | Deploy 4 Cloud Run services (api, routing-gateway, place-resolver, tracking-gateway) + 1 nginx web. |
| `deploy_routing_vm.sh`| Generate cloud-init/startup-script untuk install Docker dan jalankan OSRM/Valhalla/TileServer di VM. |
| `cloud_sql_migrate.sh`| Apply migration `supabase/migrations/cloudsql/*.sql` via Cloud SQL Auth Proxy. |
| `secrets_load.sh`     | Sync secret lokal `.env.gcp` ke Secret Manager. |
| `cloudbuild.yaml`     | Cloud Build definition untuk semua image production. |
| `routing-vm-compose.yml` | Compose stack khusus VM routing GCP. |

## Quick start

```bash
# 0. Copy env template
cp .env.gcp.example .env.gcp
# edit PROJECT_ID, domain, DATABASE_URL, OSRM_URL, VITE_PMTILES_URL

# 1. Bootstrap
export PROJECT_ID=timerally-prod
export REGION=asia-southeast2
export ROUTING_ZONE=asia-southeast2-a
./infra/gcp/bootstrap.sh

# 2. Secret Manager + Cloud SQL schema (PostGIS + tabel rally)
./infra/gcp/secrets_load.sh
./infra/gcp/cloud_sql_migrate.sh

# 3. Build & push image
./infra/gcp/build_and_push.sh

# 4. Deploy Cloud Run
./infra/gcp/deploy_cloud_run.sh

# 5. Bring up routing VM (OSRM + Valhalla + TileServer)
./infra/gcp/deploy_routing_vm.sh
```

`deploy_routing_vm.sh` sengaja tidak otomatis menjalankan stack routing jika
artefak Bali belum ada. Upload dulu `bali-latest.mbtiles` dan `bali-mainland.osrm*`
ke `/srv/timerally/offline`, lalu jalankan ulang dengan:

```bash
START_ROUTING_STACK=true ./infra/gcp/deploy_routing_vm.sh
```

## Domain

Same-origin direkomendasikan untuk mengurangi kompleksitas CORS:

```
app.timerally.id/         -> Cloud Run web (nginx + dist Vite)
app.timerally.id/v1/      -> Cloud Run API
app.timerally.id/route/   -> reverse proxy ke routing VM (port 5000)
app.timerally.id/tiles/   -> reverse proxy ke TileServer GL (port 8080)
```

Untuk MVP, pakai Cloud Run domain mapping per-service (`api.timerally.id`, `routing.timerally.id`,
`tiles.timerally.id`). Pindah ke same-origin via Global External HTTPS LB setelah stabil.

## Catatan keamanan

- Routing VM hanya buka port 80/443 publik; port 5000/8002/8080 hanya internal VPC.
- Service account Cloud Run minimal: `roles/cloudsql.client`, `roles/storage.objectAdmin` (bucket
  `${BUCKET_NAME}` only), `roles/secretmanager.secretAccessor`.
- Tidak ada secret di env Cloud Run. Pakai `--set-secrets=KEY=projects/.../secrets/.../versions/latest`.
- Cloud SQL hanya Private IP (VPC peering). Cloud Run akses via Serverless VPC Connector.
- Cloud Storage bucket `uniform-bucket-level-access`. Signed URL TTL `EXPORT_SIGNED_URL_TTL_SECONDS`.

## Hubungan dengan rancangan offline Bali

VM routing GCP menjalankan stack yang kompatibel dengan `infra/compose/docker-compose.offline-bali.yml`.
Artefak (PBF, MBTiles, OSRM graph) bisa dibangun di workstation pakai `tools/offline-bali/*.sh`
lalu di-upload ke VM via `gcloud compute scp`. Lihat `ops/offline/bali/README.md`.

## Quality gate

Sebelum deploy ulang:

```bash
python -m ruff check .
python -m pytest -q
cd apps/web-map-console && npm run build
docker compose --env-file .env.prod.example -f infra/compose/docker-compose.prod.yml config
OFFLINE_BALI_ROOT=/tmp/timerally/offline docker compose \
  -f infra/compose/docker-compose.dev.yml \
  -f infra/compose/docker-compose.offline-bali.yml config
bash -n infra/gcp/*.sh tools/offline-bali/*.sh
```
