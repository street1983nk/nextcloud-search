#!/bin/sh
# Die Dauerlast der Modellgewichte, als eigene Zahl.
#
# Warum diese Zahl ueberhaupt gebraucht wird. IDX-08 haelt INDEX_WORKERS auf 1,
# und damit treffen sich die Aktivierungen des Einbettens und die Spitze der OCR
# nicht. Die geladenen GEWICHTE liegen aber weiter im Speicher, waehrend die
# OCR-Spitze entsteht. Das ist keine Verletzung von IDX-08, aber es ist ein
# Posten, den die Formulierung "nie gleichzeitig" nicht abdeckt, und deshalb
# gehoert er getrennt ausgewiesen statt in der Gesamtspitze zu verschwinden.
#
# Gemessen wird zweimal, weil eine Zahl allein hier nicht traegt:
#   A. Die anon-Grundlinie des Containers JETZT. Das Modell ist nie geladen
#      worden (lazy_load), die zweite Spur hat nicht angefangen, und die
#      PHP-Haelfte ist aus. Sauberer wird der Nullpunkt nicht mehr.
#   B. Der Fussabdruck der Gewichte allein, an einem eigenen Prozess: RSS vor
#      dem Laden gegen RSS nach einer echten Einbettung, im selben Prozess
#      gelesen. Der Prozess laeuft in derselben cgroup, also zaehlt der Wert
#      dort mit, aber er ist hier isoliert ablesbar und nicht mit dem Rest des
#      Containers vermischt.
#
# Die dritte Zahl kommt nach dem Lauf: die Grundlinie im Ruhezustand mit
# geladenem Modell. Erst die drei zusammen sagen, was die Gewichte kosten und
# was davon Dauerlast ist.
set -eu

OUT=/home/ubuntu/work/semantiklauf
mkdir -p "$OUT"
CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

{
    date -u +'modellgrundlast %Y-%m-%dT%H:%M:%SZ'
    echo "=== A. Die Grundlinie des Containers, Modell nie geladen ==="
    sudo docker inspect nc_app_findling_backend --format 'Image={{.Config.Image}} StartedAt={{.State.StartedAt}}'
    echo "-- memory.stat, die drei Posten --"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    echo "-- memory.current und memory.peak --"
    sudo cat "$SCOPE/memory.current" "$SCOPE/memory.peak"
    echo "-- die Prozesse der cgroup, mit ihrem RSS in kB --"
    sudo docker exec nc_app_findling_backend sh -c 'ps -o pid,rss,comm -A' || true

    echo "=== B. Der Fussabdruck der Gewichte allein, in einem eigenen Prozess ==="
    sudo docker cp /home/ubuntu/work/49b-gewichte.py nc_app_findling_backend:/tmp/49b-gewichte.py
    sudo docker exec nc_app_findling_backend /app/.venv/bin/python /tmp/49b-gewichte.py

    echo "=== Die cgroup unmittelbar nach B, damit der Anteil sichtbar wird ==="
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    sudo cat "$SCOPE/memory.current"
    date -u +'modellgrundlast-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$OUT/49-modellgrundlast.txt"
echo "49-MODELLGRUNDLAST-FERTIG"
