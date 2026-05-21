# Google Cloud Race Day Runbook

Runbook ini untuk jalur deployment Google Cloud. Untuk lomba, tetap bawa edge
backup lokal berisi MBTiles/PMTiles dan OSRM graph.

## H-1

- Copy `.env.gcp.example` ke `.env.gcp`.
- Isi `PROJECT_ID`, `PUBLIC_WEB_URL`, `PUBLIC_API_URL`, `ROUTING_GATEWAY_URL`,
  `OSRM_URL`, `VALHALLA_URL`, `VITE_PMTILES_URL`, dan `DATABASE_URL`.
- Jalankan:

```bash
./infra/gcp/bootstrap.sh
./infra/gcp/secrets_load.sh
./infra/gcp/cloud_sql_migrate.sh
./infra/gcp/build_and_push.sh
./infra/gcp/deploy_cloud_run.sh
./infra/gcp/deploy_routing_vm.sh
```

## VM Routing

Upload artefak:

```bash
gcloud compute scp --recurse /srv/timerally/offline \
  timerally-routing-bali:/srv/timerally/ \
  --zone=asia-southeast2-a
```

Start stack setelah artefak ada:

```bash
START_ROUTING_STACK=true ./infra/gcp/deploy_routing_vm.sh
```

Smoke test:

```bash
curl -fsS https://routing.timerally.id/healthz
curl -fsS "https://routing.timerally.id/osrm/nearest/v1/driving/115.212629,-8.670458?number=1"
curl -I https://tiles.timerally.id/tiles/
```

## Cloud Run

Healthcheck:

```bash
curl -fsS https://api.timerally.id/healthz
curl -fsS https://api.timerally.id/readyz
```

Pastikan `readyz` tidak degraded karena:

- CORS belum benar.
- `EXPORTS_ROOT` bukan `gs://...` atau parent local tidak ada.
- `KNOWLEDGE_ROOT` tidak ikut masuk image.
- `ROUTING_GATEWAY_URL` belum mengarah ke service routing gateway.

## Field Test

- Buka web console dari laptop dan HP.
- Parse soal event lama.
- Route provider pakai `auto`.
- Pastikan export menghasilkan path `gs://.../exports/<event_id>/...`.
- Matikan internet perangkat test sebentar untuk cek offline queue UI.
- Siapkan edge node lokal sebagai fallback jika domain cloud tidak reachable.
