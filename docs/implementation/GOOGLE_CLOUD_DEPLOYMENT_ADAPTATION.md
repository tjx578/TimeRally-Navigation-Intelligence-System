# Google Cloud Deployment Adaptation

Adaptasi ini menurunkan brief Google Cloud-only ke repo tanpa mengubah alur
utama pemecahan soal rally. Cloud Run menjalankan service stateless, Compute
Engine menjalankan engine routing/tiles berat, Cloud SQL menggantikan Supabase
Postgres bila target production dipindahkan penuh ke Google Cloud, dan Cloud
Storage menyimpan export/photo/map artifacts.

## Yang Diimplementasikan

- `.env.gcp.example` untuk template konfigurasi GCP.
- `infra/gcp/cloudbuild.yaml` dan `build_and_push.sh` untuk build image lewat
  Cloud Build ke Artifact Registry.
- `deploy_cloud_run.sh` untuk API, routing-gateway, place-resolver,
  tracking-gateway, OCR worker, dan web nginx di Cloud Run.
- `deploy_routing_vm.sh`, `routing-vm-compose.yml`, dan
  `routing-vm-nginx.conf` untuk OSRM/TileServer/Valhalla standby di VM.
- `cloud_sql_migrate.sh` dan `supabase/migrations/cloudsql/*.sql` untuk schema
  Cloud SQL + PostGIS tanpa objek Supabase-only.
- `secrets_load.sh` untuk Secret Manager.
- API export sink mendukung `EXPORTS_ROOT=gs://bucket/prefix`, sehingga export
  GPX/KML/GeoJSON/YAML/roadbook bisa masuk Cloud Storage.
- Dockerfile API/place-resolver membawa `data/curated` agar Cloud Run tetap
  punya knowledge base lokal.

## Keputusan Teknis

- Google tetap validator online, bukan source offline utama.
- OSRM/Valhalla/TileServer tidak dipaksa ke Cloud Run karena artefaknya besar
  dan prosesnya long-running.
- Cloud SQL migration memakai `rally_app_users` sebagai pengganti
  `auth.users`. Enforcement user/event dilakukan di backend dulu untuk field
  test cepat; RLS Cloud SQL bisa ditambahkan setelah auth final.
- Edge backup lokal tetap wajib untuk lomba karena Google Cloud production
  tidak sama dengan offline lapangan.

## Belum Diotomatisasi

- HTTPS load balancer/domain mapping final.
- Cloud Storage signed URL endpoint khusus GCS.
- Upload otomatis artefak MBTiles/OSRM dari workstation ke VM.
- RLS Cloud SQL berbasis Identity Platform/Firebase Auth.
