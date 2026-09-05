#!/bin/sh
# Der Semantiklauf: 50.000 Dateien, Volltext, OCR und Einbettung, ein Arbeiter,
# harte Grenze 2 GB. Der Weg ist der von 13-volllauf.sh aus Plan 05-21, mit zwei
# Unterschieden, und beide sind der Grund fuer diesen Plan.
#
#   1. Der Statusbeobachter nimmt alle 120 s statt alle 300 s auf. Aus seiner
#      Reihe kommt die Grenze zwischen der ersten und der zweiten Spur, und eine
#      Phasendauer, die auf fuenf Minuten genau ist, ist keine Messung, sondern
#      eine Schaetzung mit Nachkommastelle.
#   2. Neben indexed steht embedded. Die zweite Zahl ist die zweite Spur, und
#      ohne sie waere ihre Dauer nicht ablesbar.
#
# Der Anstoss ist ausdruecklich `findling:index --restart -n`. Ohne -n fragt der
# Befehl zurueck, bekommt in einem Skript keine Antwort, meldet "Nothing was
# changed", und der Aufrufer denkt, der Lauf laufe (Fund der Generalprobe).
set -eu

OUT=/home/ubuntu/work/semantiklauf
mkdir -p "$OUT"
DOMAIN='loadtest.infranode.dev'
PW=/home/ubuntu/work/.pw/admin

echo "=== Zustand vor dem Einschalten ==="
sudo docker inspect nc_app_findling_backend --format 'Image={{.Config.Image}} Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}}'
CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
sudo cat "/sys/fs/cgroup/system.slice/docker-$CID.scope/memory.events"
df -h /mnt/findling | tail -1

echo "=== Beobachter starten, VOR dem Einschalten der App ==="
setsid nohup sudo /home/ubuntu/work/rss_sampler.sh nc_app_findling_backend 5 \
    "$OUT/semantiklauf.csv" > "$OUT/sampler.log" 2>&1 < /dev/null &
setsid nohup /home/ubuntu/work/statusbeobachter2.py "$OUT/statusseite.jsonl" 120 \
    "$PW" "$DOMAIN" > "$OUT/statusbeobachter.log" 2>&1 < /dev/null &
sleep 10
wc -l "$OUT/semantiklauf.csv" "$OUT/statusseite.jsonl"

echo "=== Anstoss: erst jetzt wird die App eingeschaltet ==="
{
    date -u +'semantiklauf-start %Y-%m-%dT%H:%M:%SZ'
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ app:enable findling
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ findling:index
} 2>&1 | tee "$OUT/00-start.txt"

echo "=== Gegenprobe nach sechs Minuten: arbeitet wirklich etwas ==="
# Sechs statt drei Minuten wie in 05-21, weil der Poller nach dem Neuaufsatz im
# Rueckzug von 300 s stand: die PHP-Haelfte war zwischen purge und enable weg,
# und der Container hat das richtig als "entfernt" gelesen. Die erste Frage nach
# dem Einschalten kann deshalb bis zu fuenf Minuten auf sich warten lassen.
sleep 360
{
    date -u +'gegenprobe %Y-%m-%dT%H:%M:%SZ'
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ findling:index
} 2>&1 | tee -a "$OUT/00-start.txt"

echo "-- DI-05-36, der zweite Teil des Beweises: gezaehlte Durchgaenge des Pollers --" | tee -a "$OUT/00-start.txt"
CSTART=$(sudo docker inspect nc_app_findling_backend --format '{{.State.StartedAt}}')
sudo docker logs --since "$CSTART" nc_app_findling_backend 2>&1 | grep -c 'pass finished' | tee -a "$OUT/00-start.txt"
sudo docker logs --tail 8 nc_app_findling_backend 2>&1 | tee -a "$OUT/00-start.txt"

python3 - <<'PY' | tee -a "$OUT/00-start.txt"
import json
import pathlib

zeilen = pathlib.Path("/home/ubuntu/work/semantiklauf/statusseite.jsonl").read_text(encoding="utf-8").splitlines()
letzte = json.loads(zeilen[-1]) if zeilen else {}
vorrat = int(letzte.get("scheduled", 0)) + int(letzte.get("running", 0))
print("statusseite:", json.dumps({k: letzte.get(k) for k in
      ("at", "runState", "indexed", "indexedPercent", "embedded", "embeddedPercent",
       "scheduled", "running", "backendReachable")}, ensure_ascii=False))
print("PRUEFUNG OK: es liegt Arbeit an" if vorrat > 0 else "PRUEFUNG ROT: kein Vorrat, der Lauf laeuft nicht")
PY
echo "42-SEMANTIKLAUF-GESTARTET"
