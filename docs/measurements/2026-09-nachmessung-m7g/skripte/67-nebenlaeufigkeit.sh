#!/bin/sh
# The concurrency series again, with enough requests to carry a promise.
#
# Run 64 answered the question of the peak, on a container that had never seen a
# search, and that is the one reading the store number comes from. What it could
# not do is carry a promise: three rounds per level is 3 to 48 requests, and a
# p95 over 48 samples is an anecdote with a percentile sign in front of it.
#
# So this one runs the same tool over five levels with ten rounds each, 410
# requests in all, and it adds the level 12 between the last one that held the
# budget and the first that did not. The promise is the highest level whose p95
# stays under 2500 ms while the three damage counters stay at zero, and it is
# read off this table afterwards.
#
# The model is loaded at this point, deliberately: a promise about concurrency is
# a promise about the steady state, and putting the one time cost of the first
# embedding into the first level of the table would flatter every level after it.
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
CONTAINER=nc_app_findling_backend
BASE=https://loadtest.infranode.dev
ZIEL="$OUT/67-nebenlaeufigkeit.txt"
RUNDEN=10

CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

FINDLING_LOAD_PASSWORD=$(sudo cat /home/ubuntu/work/.pw/lasttest)
export FINDLING_LOAD_PASSWORD

{
    date -u +'nebenlaeufigkeit-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== memory.events, read BEFORE this series ==="
    sudo cat "$SCOPE/memory.events"

    echo "=== The sampler beside it ==="
    sudo sh /home/ubuntu/work/rss_sampler.sh "$CONTAINER" 2 "$OUT/nebenlaeufigkeit.csv" &
    SAMPLER=$!
    sleep 4

    for stufe in 1 4 8 12 16; do
        echo "=== Concurrency $stufe over $RUNDEN rounds ==="
        date -u +"stufe-$stufe-vor %Y-%m-%dT%H:%M:%SZ"
        sudo -E /usr/bin/python3 /home/ubuntu/work/search_load.py \
            --base-url "$BASE" --user lasttest --concurrency "$stufe" --rounds "$RUNDEN" \
            --container "$CONTAINER" > "$OUT/67-stufe-$stufe.json" 2> "$OUT/67-stufe-$stufe.err" || true
        date -u +"stufe-$stufe-nach %Y-%m-%dT%H:%M:%SZ"
        tail -3 "$OUT/67-stufe-$stufe.err" || true
        sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
        printf 'memory.current=%s memory.peak=%s\n' \
            "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"
        sudo cat "$SCOPE/memory.events"
        # A pause between the levels, so the level that follows measures itself
        # and not the tail of the one before it.
        sleep 20
    done

    echo "=== The sampler down ==="
    sudo kill -TERM "$SAMPLER" 2>/dev/null || true
    sleep 3
    tail -3 "$OUT/nebenlaeufigkeit.csv"

    echo "=== The table this promise is read off ==="
    sudo python3 - <<'PY'
import json
import pathlib

out = pathlib.Path("/home/ubuntu/work/nachmessung")
print(f"{'conc':>5} {'req':>5} {'fail':>5} {'p50':>9} {'p95':>9} {'max':>9} {'budget':>7} {'anon MB':>9} {'current MB':>11}")
for stufe in (1, 4, 8, 12, 16):
    payload = json.loads((out / f"67-stufe-{stufe}.json").read_text(encoding="utf-8"))
    after = payload["memory"]["after"]
    print(
        f"{payload['concurrency']:>5} {payload['requests']:>5} {payload['failures']:>5} "
        f"{payload['p50_ms']:>9} {payload['p95_ms']:>9} {payload['max_ms']:>9} "
        f"{str(payload['p95_within_budget']):>7} {after['anon'] / 1048576:>9.1f} "
        f"{after['memory.current'] / 1048576:>11.1f}"
    )
PY

    echo "=== memory.events, all six counters, at the end of the series ==="
    sudo cat "$SCOPE/memory.events"
    printf 'OOMKilled=%s RestartCount=%s\n' \
        "$(sudo docker inspect "$CONTAINER" --format '{{.State.OOMKilled}}')" \
        "$(sudo docker inspect "$CONTAINER" --format '{{.RestartCount}}')"

    date -u +'nebenlaeufigkeit-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"
echo "67-FERTIG" > "$OUT/67-FERTIG"
