#!/bin/sh
# The OCR phase at cgroup level, with three languages, on a fresh batch.
#
# Why a fresh batch and not the corpus again. The 51.961 documents on the volume
# are indexed and carry a content hash, so a second pass over them skips the
# whole pipeline: an OCR phase cannot be measured on files that will not be read
# again. A full restart of the crawl would read all of them, and that is the
# nineteen hour run this plan exists to avoid.
#
# So 120 files of the scan_single category are uploaded into a folder of their own
# over WebDAV, which is the path a real user takes and the path that raises the
# events the app listens to. 120 pages at roughly three and a half seconds each
# is around seven minutes of pure OCR, which is long enough for the phase to have
# a plateau and short enough to fit inside the cap of this run.
#
# What this measures and what it does not. It measures the anon plateau and the
# anon peak of the container while it does nothing but OCR, with deu+eng+fra. It
# does NOT reproduce the 1.562,7 MB of the OCR phase of 06-11, because that
# figure came out of a phase that ran for hours over 9.916 scans next to the
# embedding track; that comparison is drawn in the report and its limits are
# named there rather than hidden here.
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
CONTAINER=nc_app_findling_backend
QUELLE=/mnt/findling/ncdata/lasttest/files/loadtest
ZIEL='https://loadtest.infranode.dev/remote.php/dav/files/lasttest/ocrdrei'
ANZAHL=120

CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
PW=$(sudo cat /home/ubuntu/work/.pw/lasttest)

{
    date -u +'ocrphase-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== memory.events, read BEFORE the batch ==="
    sudo cat "$SCOPE/memory.events"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"

    echo "=== The batch: $ANZAHL files of the scan_single category ==="
    sudo ls "$QUELLE" | head -"$ANZAHL" > /tmp/ocrdrei-namen.txt
    wc -l /tmp/ocrdrei-namen.txt

    echo "=== The sampler beside it, two seconds ==="
    sudo sh /home/ubuntu/work/rss_sampler.sh "$CONTAINER" 2 "$OUT/ocrphase.csv" &
    SAMPLER=$!
    sleep 4

    echo "=== Upload over WebDAV, the path a user takes ==="
    curl -sS -o /dev/null -u "lasttest:$PW" -X MKCOL "$ZIEL" || true
    date -u +'upload-vor %Y-%m-%dT%H:%M:%SZ'
    sudo xargs -a /tmp/ocrdrei-namen.txt -P 4 -I@ \
        curl -sS -o /dev/null -w '%{http_code}\n' -u "lasttest:$PW" \
        -T "$QUELLE/@" "$ZIEL/@" 2>&1 | sort | uniq -c
    date -u +'upload-nach %Y-%m-%dT%H:%M:%SZ'

    echo "=== The background jobs, so the crawl picks the folder up ==="
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ files:scan --path=/lasttest/files/ocrdrei 2>&1 | tail -6
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ findling:index --status 2>&1 | tail -12

    echo "=== The OCR phase, watched for at most twelve minutes ==="
    ende=$(( $(date +%s) + 720 ))
    # A bounded number of readings and not an open loop: the phase is expected to
    # take about seven minutes, and a run that waits forever on a phase that never
    # starts would eat the cap of the whole box.
    for runde in $(seq 1 36); do
        jetzt=$(date +%s)
        if [ "$jetzt" -ge "$ende" ]; then
            echo "the twelve minutes are up, the phase is reported as it stands"
            break
        fi
        anon=$(sudo grep -E '^anon ' "$SCOPE/memory.stat" | awk '{print $2}')
        zeilen=$(sudo docker logs --tail 400 "$CONTAINER" 2>&1 | grep -c 'pass finished' || true)
        printf '%s runde=%s anon=%s MB=%s pass_finished=%s\n' \
            "$(date -u +%H:%M:%SZ)" "$runde" "$anon" \
            "$(awk -v b="${anon:-0}" 'BEGIN{printf "%.1f", b/1048576}')" "$zeilen"
        sleep 20
    done

    echo "=== The verdicts of the batch ==="
    sudo python3 /home/ubuntu/work/68-bestand-endungen.py \
        /mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/state.db --prefix ocrdrei

    echo "=== The log of the phase, the OCR lines among them ==="
    sudo docker logs --timestamps --tail 60 "$CONTAINER" 2>&1 | tail -40

    echo "=== The sampler down ==="
    sudo kill -TERM "$SAMPLER" 2>/dev/null || true
    sleep 3
    tail -3 "$OUT/ocrphase.csv"

    echo "=== memory.events, all six counters, after the phase ==="
    sudo cat "$SCOPE/memory.events"
    printf 'OOMKilled=%s RestartCount=%s\n' \
        "$(sudo docker inspect "$CONTAINER" --format '{{.State.OOMKilled}}')" \
        "$(sudo docker inspect "$CONTAINER" --format '{{.RestartCount}}')"

    date -u +'ocrphase-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$OUT/71-ocrphase.txt"
echo "71-FERTIG" > "$OUT/71-FERTIG"
