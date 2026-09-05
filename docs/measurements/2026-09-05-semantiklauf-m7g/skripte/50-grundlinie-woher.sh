#!/bin/sh
# Woher die Grundlinie kommt, gemessen statt vermutet.
#
# Der Anlass: der Container mit der Semantik haelt im Leerlauf 691,8 MB anon, der
# ohne sie hielt im selben Zustand 58,7 MB (Plan 05-21, erste Zeile von
# volllauf.csv). Das ist das Elffache, bevor eine einzige Datei angefasst wurde,
# und es ist genau die Sorte Zahl, die man nicht in einen Bericht schreibt, ohne
# zu wissen, was sie erzeugt.
#
# Die Messung: den Container ueber AppAPI neu starten, also auf dem Weg, der ihn
# auch bewaffnet, und danach anon im Sekundentakt gegen das Protokoll halten.
# Welche Zeile den Sprung macht, sagt dann, welcher Schritt ihn erzeugt.
set -eu

OUT=/home/ubuntu/work/semantiklauf
mkdir -p "$OUT"
ZIEL="$OUT/50-grundlinie-woher.txt"

occ() {
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ "$@"
}

{
    date -u +'grundlinie-woher %Y-%m-%dT%H:%M:%SZ'
    echo "=== Vergleichswert aus Plan 05-21: 58,7 MB anon im Leerlauf, Abbild 05-21-arm ==="
    echo "=== Der Zustand jetzt, Abbild 06-11-arm ==="
    CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
    sudo grep -E '^anon ' "/sys/fs/cgroup/system.slice/docker-$CID.scope/memory.stat"

    echo "=== Neustart ueber AppAPI, also mit Bewaffnung ==="
    occ app_api:app:disable findling_backend
    sleep 5
    occ app_api:app:enable findling_backend
    sleep 2
    CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
    sudo docker update --memory=2g --memory-swap=2g nc_app_findling_backend >/dev/null
    START=$(sudo docker inspect nc_app_findling_backend --format '{{.State.StartedAt}}')
    echo "container-start $START"

    echo "=== anon im Sekundentakt, 90 Sekunden ==="
    i=0
    while [ "$i" -lt 45 ]; do
        i=$((i + 1))
        wert=$(sudo grep -E '^anon ' "$SCOPE/memory.stat" 2>/dev/null | awk '{print $2}')
        printf '%s sekunde=%s anon=%s MB=%s\n' \
            "$(date -u +%H:%M:%SZ)" "$((i * 2))" "$wert" \
            "$(awk -v b="${wert:-0}" 'BEGIN{printf "%.1f", b/1048576}')"
        sleep 2
    done

    echo "=== Das Protokoll dieses Starts, mit Zeitstempeln ==="
    sudo docker logs --timestamps --since "$START" nc_app_findling_backend 2>&1 | tail -40

    echo "=== Die Prozesse und ihr RSS ==="
    sudo docker cp /home/ubuntu/work/50b-prozesse.py nc_app_findling_backend:/tmp/50b-prozesse.py
    sudo docker exec nc_app_findling_backend /app/.venv/bin/python /tmp/50b-prozesse.py

    date -u +'grundlinie-woher-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"
echo "50-GRUNDLINIE-FERTIG"
