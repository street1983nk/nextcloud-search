#!/bin/sh
# Der Neuaufsatz vor dem Semantiklauf: beide Haelften auf null, das Abbild mit
# der Semantik registriert, und die Registrierung ist zugleich die Bewaffnung.
#
# Warum beide Haelften und nicht nur eine. Der Index von Plan 05-21 steht noch,
# mit 51.961 Dokumenten und ihren Verdikten. Der Container erkennt eine
# unveraenderte Datei an ihrer file_id und ueberspringt sie, also haette ein Lauf
# gegen diesen Bestand die OCR-Spitze nie erzeugt, und genau sie ist die eine
# Zahl, gegen die die Embedding-Spitze zu halten ist (IDX-08). Der Datenspeicher
# des Containers geht deshalb mit --rm-data, und die PHP-Haelfte ueber
# findling:purge --now, das Tabellen, Auftraege und Einstellungen raeumt.
#
# Warum die Registrierung ueber AppAPI laeuft und nicht ueber docker start:
# DI-05-36. Ein Container, den die Neustartregel von Docker hochbringt, beantwortet
# Suchen und indexiert nie wieder, und die Verwaltungsseite kann diesen Zustand
# nicht anzeigen (DI-05-38). occ app_api:app:register ist der Weg, auf dem der
# Poller bewaffnet wird, und der Beweis dafuer ist ein gezaehlter Durchgang im
# Protokoll und keine Annahme.
set -eu

TAG=06-11-arm
REPO=/home/ubuntu/work/repo0611
OUT=/home/ubuntu/work/semantik
mkdir -p "$OUT"
LOG="$OUT/41-neuaufsatz.log"

occ() {
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ "$@"
}

exec > "$LOG" 2>&1
date -u +'neuaufsatz-start %Y-%m-%dT%H:%M:%SZ'

echo "=== Der Bestand VOR dem Raeumen, damit der Bericht ihn nennen kann ==="
occ findling:index || true
sudo docker exec nc_app_findling_backend sh -c 'ls -la /nc_app_findling_backend_data' || true

echo "=== PHP-Haelfte raeumen ==="
occ findling:purge --now -n || true
occ app:list | grep -A20 'Disabled' | head -8 || true

echo "=== Container samt Datenspeicher weg ==="
sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'
occ app_api:app:unregister findling_backend --rm-data || true
echo "-- der Datenspeicher danach, es darf keiner mehr da sein --"
sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'
sudo docker ps -a --filter name=findling_backend --format '{{.Names}} {{.Status}}'

echo "=== Die PHP-Haelfte des neuen Standes in den Nextcloud-Container ==="
sudo docker exec nextcloud-aio-nextcloud rm -rf /var/www/html/custom_apps/findling
sudo docker cp "$REPO/php" nextcloud-aio-nextcloud:/var/www/html/custom_apps/findling
sudo docker exec nextcloud-aio-nextcloud chown -R 33:33 /var/www/html/custom_apps/findling
sudo docker exec -i nextcloud-aio-nextcloud php < /home/ubuntu/work/phphash.php

echo "=== info.xml mit dem Kennzeichen der Box ==="
sed -e 's|<registry>[^<]*</registry>|<registry>localhost:5000</registry>|' \
    -e 's|<image>[^<]*</image>|<image>findling_backend</image>|' \
    -e "s|<image-tag>[^<]*</image-tag>|<image-tag>$TAG</image-tag>|" \
    "$REPO/backend/appinfo/info.xml" > /home/ubuntu/work/info-box.xml
grep -E '<registry>|<image>|<image-tag>' /home/ubuntu/work/info-box.xml
sudo docker cp /home/ubuntu/work/info-box.xml nextcloud-aio-nextcloud:/tmp/info-box.xml
sudo docker exec nextcloud-aio-nextcloud chown 33:33 /tmp/info-box.xml

echo "=== Registrierung ueber AppAPI, also die Bewaffnung ==="
date -u +'register-start %Y-%m-%dT%H:%M:%SZ'
occ app_api:app:register findling_backend harp_aio --info-xml /tmp/info-box.xml --wait-finish
date -u +'register-ende %Y-%m-%dT%H:%M:%SZ'
CSTART=$(sudo docker inspect nc_app_findling_backend --format '{{.State.StartedAt}}')
echo "container-start $CSTART"
sudo docker inspect nc_app_findling_backend --format 'Image={{.Config.Image}} Restart={{.HostConfig.RestartPolicy.Name}}'

echo "=== Harte Grenze, nach der Registrierung, weil sie sie nicht ueberlebt ==="
sudo docker update --memory=2g --memory-swap=2g nc_app_findling_backend
sudo docker inspect nc_app_findling_backend --format 'Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}}'
CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
echo "-- memory.max der cgroup --"
sudo cat "/sys/fs/cgroup/system.slice/docker-$CID.scope/memory.max"
echo "-- memory.events vor dem Lauf, alle Zaehler sollen 0 sein --"
sudo cat "/sys/fs/cgroup/system.slice/docker-$CID.scope/memory.events"

echo "=== Die Semantik im laufenden Container, nicht nur im Abbild ==="
sudo docker exec nc_app_findling_backend sh -c 'env | grep -E "FINDLING_EMBED|FINDLING_VEC0|HF_HUB" | sort'
sudo docker exec -i nc_app_findling_backend /app/.venv/bin/python - <<'PY'
from findling.config import settings

s = settings()
print("embed_enabled:", s.embed_enabled)
print("token_cap:", s.embed_token_cap)
print("batch:", s.embed_batch_size, "sequence:", s.embed_sequence_len)
print("model_dir:", s.embed_model_dir)
PY

echo "=== DI-05-36: der Beweis der Bewaffnung, an einer Handlung ==="
# Gezaehlt werden Durchgaenge des Pollers im Protokoll, ab dem Start DIESES
# Containers, und nicht ein Zustand: ein Zustand, der zum falschen Zeitpunkt
# abgelesen wird, sieht aus wie eine Bewegung (die Lehre aus Drill 1b, 05-21).
echo "-- Runde 1, 90 Sekunden nach der Registrierung --"
sleep 90
sudo docker logs --since "$CSTART" nc_app_findling_backend 2>&1 | grep -c 'pass finished' || true
echo "-- Runde 2, weitere 90 Sekunden --"
sleep 90
sudo docker logs --since "$CSTART" nc_app_findling_backend 2>&1 | grep -c 'pass finished' || true
echo "-- die letzten Protokollzeilen --"
sudo docker logs --tail 15 nc_app_findling_backend 2>&1

date -u +'neuaufsatz-ende %Y-%m-%dT%H:%M:%SZ'
echo "41-NEUAUFSATZ-FERTIG"
