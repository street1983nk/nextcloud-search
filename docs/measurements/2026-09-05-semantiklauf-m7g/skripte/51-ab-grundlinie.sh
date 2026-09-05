#!/bin/sh
# A/B ueber die Grundlinie: liegt sie am Abbild oder am Zustand des Volumens?
#
# Der Befund, der diesen Test ausloest: das Abbild mit der Semantik haelt im
# Leerlauf 686 MB anon, und Plan 05-21 hat im selben Zustand 58,7 MB gemessen.
# Zwei Erklaerungen sind moeglich, und sie fuehren zu verschiedenen Berichten:
#
#   (a) Die Semantik kostet diese Grundlast. Dann ist die Zahl ein Ergebnis
#       dieser Phase und gehoert in den Store-Text (D-17c).
#   (b) Der Unterschied liegt am Zustand des Volumens. 05-21 startete gegen ein
#       LEERES Volumen, das die Wortliste erst bauen musste; hier liegt sie
#       bereits da und wird gelesen. Dann waere die Zahl kein Ergebnis dieser
#       Phase, sondern eine, die 05-21 zu frueh abgelesen hat.
#
# Der Test unterscheidet die beiden, indem er das Abbild wechselt und den
# Zustand haelt: dasselbe Volumen, dasselbe Nextcloud, nur das alte Abbild ohne
# Semantik. Haelt es auch 686 MB, ist (b) richtig. Haelt es 59 MB, ist (a)
# richtig.
#
# Danach wird auf das Abbild dieses Laufs zurueckgestellt, ueber AppAPI, also
# mit Bewaffnung, und die harte Grenze neu gesetzt.
set -eu

OUT=/home/ubuntu/work/semantiklauf
ZIEL="$OUT/51-ab-grundlinie.txt"
REPO=/home/ubuntu/work/repo0611

occ() {
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ "$@"
}

anon_jetzt() {
    cid=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
    sudo grep -E '^anon ' "/sys/fs/cgroup/system.slice/docker-$cid.scope/memory.stat" |
        awk '{printf "%s Byte, %.1f MB\n", $2, $2/1048576}'
}

wechsel() {
    tag="$1"
    sed -e 's|<registry>[^<]*</registry>|<registry>localhost:5000</registry>|' \
        -e 's|<image>[^<]*</image>|<image>findling_backend</image>|' \
        -e "s|<image-tag>[^<]*</image-tag>|<image-tag>$tag</image-tag>|" \
        "$REPO/backend/appinfo/info.xml" > /home/ubuntu/work/info-box.xml
    sudo docker cp /home/ubuntu/work/info-box.xml nextcloud-aio-nextcloud:/tmp/info-box.xml
    sudo docker exec nextcloud-aio-nextcloud chown 33:33 /tmp/info-box.xml
    occ app_api:app:unregister findling_backend
    occ app_api:app:register findling_backend harp_aio --info-xml /tmp/info-box.xml --wait-finish
    sudo docker update --memory=2g --memory-swap=2g nc_app_findling_backend >/dev/null
}

{
    date -u +'ab-grundlinie %Y-%m-%dT%H:%M:%SZ'
    echo "=== Runde A: das Abbild dieses Laufs, mit Semantik ==="
    sudo docker inspect nc_app_findling_backend --format 'Image={{.Config.Image}}'
    anon_jetzt

    echo "=== Wechsel auf das Abbild aus Plan 05-21, ohne Semantik, Volumen bleibt ==="
    wechsel 05-21-arm
    sleep 45
    echo "-- Runde B, Abbild ohne Semantik, derselbe Zustand --"
    sudo docker inspect nc_app_findling_backend --format 'Image={{.Config.Image}}'
    anon_jetzt
    echo "-- das Protokoll dieses Starts --"
    sudo docker logs --tail 12 nc_app_findling_backend 2>&1

    echo "=== Zurueck auf das Abbild dieses Laufs ==="
    wechsel 06-11-arm
    sleep 45
    echo "-- Runde A2, zur Gegenprobe --"
    sudo docker inspect nc_app_findling_backend --format 'Image={{.Config.Image}} Memory={{.HostConfig.Memory}}'
    anon_jetzt
    echo "-- die Bewaffnung, wieder bewiesen --"
    sudo docker logs --tail 12 nc_app_findling_backend 2>&1 | grep -E 'enabled|wordlist|automaton' || true
    date -u +'ab-grundlinie-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"
echo "51-AB-FERTIG"
