#!/bin/sh
# The counter proof to DI-05-36 on the image that ships, over a machine restart.
#
# Script 60 measured the before half on the image of 06-11, which predates the
# fix of plan 06.1-01: zero passes after the machine came up, and a container
# that had to be switched off and on again by hand before it indexed anything.
#
# This is the after half, and it is a number rather than a claim. The machine is
# restarted, nothing is touched afterwards, and the two questions are asked:
# does the armed marker survive, and does the poller finish passes without any
# occ call in between. Work is put in front of it on purpose, because an armed
# poller with an empty work stock and a dead one look exactly alike from
# outside: 30 files are uploaded BEFORE the restart, so there is something to
# find on the other side of it.
#
# Call: 72-neustart.sh vorher   before the reboot
#       72-neustart.sh nachher  after it
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
CONTAINER=nc_app_findling_backend
QUELLE=/mnt/findling/ncdata/lasttest/files/loadtest
ZIEL='https://loadtest.infranode.dev/remote.php/dav/files/lasttest/neustart'
PHASE="${1:?vorher oder nachher}"

case "$PHASE" in
vorher)
    PW=$(sudo cat /home/ubuntu/work/.pw/lasttest)
    {
        date -u +'neustart-vorher %Y-%m-%dT%H:%M:%SZ'
        echo "=== The armed marker before the restart ==="
        sudo ls -la /mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/
        echo "=== 30 files as work for the other side of the restart ==="
        curl -sS -o /dev/null -u "lasttest:$PW" -X MKCOL "$ZIEL" || true
        sudo ls "$QUELLE" | sed -n '200,229p' > /tmp/neustart-namen.txt
        wc -l /tmp/neustart-namen.txt
        sudo xargs -a /tmp/neustart-namen.txt -P 4 -I@ \
            curl -sS -o /dev/null -w '%{http_code}\n' -u "lasttest:$PW" \
            -T "$QUELLE/@" "$ZIEL/@" 2>&1 | sort | uniq -c
        sudo docker exec --user www-data nextcloud-aio-nextcloud php occ files:scan --path=/lasttest/files/neustart 2>&1 | tail -4
        echo "=== The container state that has to survive ==="
        sudo docker inspect "$CONTAINER" \
            --format 'Image={{.Config.Image}} Memory={{.HostConfig.Memory}} StartedAt={{.State.StartedAt}}'
        date -u +'neustart-vorher-ende %Y-%m-%dT%H:%M:%SZ'
    } 2>&1 | tee "$OUT/72-neustart-vorher.txt"
    ;;
nachher)
    {
        date -u +'neustart-nachher %Y-%m-%dT%H:%M:%SZ'
        echo "=== The machine, freshly booted ==="
        uptime
        echo "=== The container, and NOT one occ call was made before this line ==="
        sudo docker inspect "$CONTAINER" \
            --format 'Image={{.Config.Image}} Memory={{.HostConfig.Memory}} StartedAt={{.State.StartedAt}} RestartCount={{.RestartCount}}'
        echo "=== The armed marker, survived or not ==="
        sudo ls -la /mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/
        START=$(sudo docker inspect "$CONTAINER" --format '{{.State.StartedAt}}')
        printf 'container-start %s\n' "$START"
        echo "=== The passes, watched for at most eight minutes, bounded ==="
        for runde in $(seq 1 24); do
            zeilen=$(sudo docker logs --since "$START" "$CONTAINER" 2>&1 | grep -c 'pass finished' || true)
            anon=$(sudo grep -E '^anon ' \
                "/sys/fs/cgroup/system.slice/docker-$(sudo docker inspect -f '{{.Id}}' "$CONTAINER").scope/memory.stat" \
                | awk '{print $2}')
            printf '%s runde=%s pass_finished=%s anon=%s MB=%s\n' \
                "$(date -u +%H:%M:%SZ)" "$runde" "$zeilen" "$anon" \
                "$(awk -v b="${anon:-0}" 'BEGIN{printf "%.1f", b/1048576}')"
            if [ "$zeilen" -ge 3 ]; then
                echo "three passes are enough: the container is armed without a single occ call"
                break
            fi
            sleep 20
        done
        echo "=== The log of this start ==="
        sudo docker logs --timestamps --since "$START" "$CONTAINER" 2>&1 | head -25
        printf 'pass-finished lines since the machine start: '
        sudo docker logs --since "$START" "$CONTAINER" 2>&1 | grep -c 'pass finished' || true
        echo "=== The verdicts of the thirty ==="
        sudo python3 /home/ubuntu/work/68-bestand-endungen.py \
            /mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/state.db --prefix neustart
        echo "=== The hard limit after the machine start, read out of the cgroup ==="
        CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
        printf 'memory.max=%s\n' "$(sudo cat "/sys/fs/cgroup/system.slice/docker-$CID.scope/memory.max")"
        date -u +'neustart-nachher-ende %Y-%m-%dT%H:%M:%SZ'
    } 2>&1 | tee "$OUT/72-neustart-nachher.txt"
    echo "72-FERTIG" > "$OUT/72-FERTIG"
    ;;
*)
    echo "72-neustart.sh <vorher|nachher>" >&2
    exit 2
    ;;
esac
