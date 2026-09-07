#!/bin/sh
# The peak and the concurrency series, in one detached run.
#
# Order matters and it is the order of 06-11: memory.events is read BEFORE the
# first search, because the first semantic search is the event the peak of 06-11
# began with, to the second, and a reading taken afterwards would describe the
# reclaim rather than the run (T-06.1-75).
#
# The series is 1, 4, 8, 16. Out of it follows the promise, and the promise is
# the highest level that holds the budget of 2500 ms with p95 and leaves the
# three damage counters at zero. The number is fixed afterwards and not before
# (open question 5 of 06.1-11).
#
# memory.current is read next to anon at every level, because a brute force scan
# pulls the vector stock into the file cache of the same cgroup and anon does not
# count it.
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
CONTAINER=nc_app_findling_backend
BASE=https://loadtest.infranode.dev
ZIEL="$OUT/64-spitze.txt"

CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

FINDLING_LOAD_PASSWORD=$(sudo cat /home/ubuntu/work/.pw/lasttest)
export FINDLING_LOAD_PASSWORD

{
    date -u +'spitze-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== memory.events, read BEFORE the first search of this run ==="
    sudo cat "$SCOPE/memory.events"
    echo "-- and the two figures next to it, as the zero point of the peak --"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"

    echo "=== The sampler beside it, two seconds, so the second of the peak is readable ==="
    sudo sh /home/ubuntu/work/rss_sampler.sh "$CONTAINER" 2 "$OUT/nachmessung.csv" &
    SAMPLER=$!
    printf 'sampler-pid %s\n' "$SAMPLER"
    sleep 6

    echo "=== The very first semantic search of this container start, alone ==="
    date -u +'erste-suche-vor %Y-%m-%dT%H:%M:%SZ'
    sudo -E /usr/bin/python3 /home/ubuntu/work/search_load.py \
        --base-url "$BASE" --user lasttest --concurrency 1 --rounds 3 \
        --container "$CONTAINER" > "$OUT/64-stufe-01.json" 2> "$OUT/64-stufe-01.err" || true
    date -u +'erste-suche-nach %Y-%m-%dT%H:%M:%SZ'
    tail -5 "$OUT/64-stufe-01.err" || true
    echo "-- the cgroup right after the first search --"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"
    sudo cat "$SCOPE/memory.events"

    for stufe in 4 8 16; do
        echo "=== Concurrency $stufe ==="
        date -u +"stufe-$stufe-vor %Y-%m-%dT%H:%M:%SZ"
        sudo -E /usr/bin/python3 /home/ubuntu/work/search_load.py \
            --base-url "$BASE" --user lasttest --concurrency "$stufe" --rounds 3 \
            --container "$CONTAINER" > "$OUT/64-stufe-$stufe.json" 2> "$OUT/64-stufe-$stufe.err" || true
        date -u +"stufe-$stufe-nach %Y-%m-%dT%H:%M:%SZ"
        tail -5 "$OUT/64-stufe-$stufe.err" || true
        echo "-- the cgroup after concurrency $stufe --"
        sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
        printf 'memory.current=%s memory.peak=%s\n' \
            "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"
        sudo cat "$SCOPE/memory.events"
    done

    echo "=== The sampler down, and its closing line is the OOM proof ==="
    sudo kill -TERM "$SAMPLER" 2>/dev/null || true
    sleep 3
    tail -5 "$OUT/nachmessung.csv"

    echo "=== memory.events, the full set of six counters, at the end ==="
    sudo cat "$SCOPE/memory.events"
    printf 'OOMKilled=%s\n' "$(sudo docker inspect "$CONTAINER" --format '{{.State.OOMKilled}}')"
    printf 'RestartCount=%s\n' "$(sudo docker inspect "$CONTAINER" --format '{{.RestartCount}}')"

    echo "=== The highest anon of this run, out of the csv ==="
    sudo python3 - "$OUT/nachmessung.csv" <<'PY'
import datetime
import sys

# Every line of the sampler carries a fixed prefix word before the csv, so the
# row is the last whitespace separated token and not the whole line.
hoechste = 0
stempel = 0
with open(sys.argv[1], encoding="utf-8") as handle:
    for line in handle:
        row = line.strip().split()
        if not row:
            continue
        felder = row[-1].split(",")
        if len(felder) < 6 or not felder[1].isdigit():
            continue
        anon = int(felder[1])
        if anon > hoechste:
            hoechste = anon
            stempel = int(felder[0])
when = datetime.datetime.fromtimestamp(stempel, datetime.UTC).isoformat() if stempel else "unknown"
print(f"anon-spitze {hoechste} bytes = {hoechste / 1048576:.1f} MB at {when}")
PY

    date -u +'spitze-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"
echo "64-SPITZE-FERTIG" > "$OUT/64-FERTIG"
echo "64-SPITZE-FERTIG"
