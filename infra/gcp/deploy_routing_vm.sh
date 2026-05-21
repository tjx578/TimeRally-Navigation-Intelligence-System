#!/usr/bin/env bash
#
# Create/update the Compute Engine VM used for OSRM/Valhalla/TileServer.
# This script prepares Docker and uploads the routing VM compose files. Start
# the stack only after Bali MBTiles and OSRM graph artifacts are present.
set -Eeuo pipefail

HERE="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &>/dev/null && pwd )"
# shellcheck source=common.sh
source "${HERE}/common.sh"

require_cmd gcloud
ensure_project

STARTUP_SCRIPT="$(mktemp)"
cat > "${STARTUP_SCRIPT}" <<'SCRIPT'
#!/usr/bin/env bash
set -Eeuo pipefail
apt-get update
apt-get install -y docker.io docker-compose-plugin git curl unzip nginx
systemctl enable --now docker
mkdir -p /srv/timerally/offline/{extracts,tiles,osrm,valhalla/custom_files,logs}
mkdir -p /srv/timerally/compose
chmod -R 775 /srv/timerally
SCRIPT
trap 'rm -f "${STARTUP_SCRIPT}"' EXIT

if ! gcloud compute instances describe "${ROUTING_VM_NAME}" --zone="${ROUTING_ZONE}" >/dev/null 2>&1; then
  log "create routing VM ${ROUTING_VM_NAME} (${ROUTING_VM_MACHINE_TYPE})"
  gcloud compute instances create "${ROUTING_VM_NAME}" \
    --zone="${ROUTING_ZONE}" \
    --machine-type="${ROUTING_VM_MACHINE_TYPE}" \
    --boot-disk-size="${ROUTING_VM_DISK_GB}GB" \
    --boot-disk-type="${ROUTING_VM_DISK_TYPE}" \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=timerally-routing \
    --metadata-from-file startup-script="${STARTUP_SCRIPT}"
else
  log "routing VM ${ROUTING_VM_NAME} sudah ada"
fi

log "upload routing compose files"
gcloud compute ssh "${ROUTING_VM_NAME}" --zone="${ROUTING_ZONE}" --command \
  "sudo mkdir -p /srv/timerally/compose && sudo chown -R \$USER:\$USER /srv/timerally"
gcloud compute scp "${HERE}/routing-vm-compose.yml" \
  "${ROUTING_VM_NAME}:/srv/timerally/compose/docker-compose.yml" \
  --zone="${ROUTING_ZONE}"
gcloud compute scp "${HERE}/routing-vm-nginx.conf" \
  "${ROUTING_VM_NAME}:/srv/timerally/compose/routing-vm-nginx.conf" \
  --zone="${ROUTING_ZONE}"

if [[ "${START_ROUTING_STACK:-false}" == "true" ]]; then
  log "start routing VM stack"
  gcloud compute ssh "${ROUTING_VM_NAME}" --zone="${ROUTING_ZONE}" --command \
    "cd /srv/timerally/compose && docker compose up -d"
else
  log "skip docker compose up. Set START_ROUTING_STACK=true after artifacts exist."
fi

log "routing VM deploy step selesai"
