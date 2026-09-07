#!/bin/sh
# The hard limit, then the idle base load, in the form of 06-11.
#
# The limit first, and read back out of the cgroup: a register throws it away
# (06.1-RESEARCH part 5.2, pitfall 5), and a run that measures against 4 GB when
# it means to measure against 2 measures nothing at all (T-06.1-76). Nothing is
# measured before that line is proven.
#
# Then the base load, with the same three questions as 49-modellgrundlast.sh of
# 06-11, and with its two helper scripts unchanged so that the numbers are
# comparable rather than merely adjacent (T-06.1-74):
#   A. the anon base line of the container, model never loaded
#   B. the footprint of the weights alone, in a process of their own
#   C. which step of the startup buys it, step by step
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
ZIEL="$OUT/63-grundlast.txt"

{
    date -u +'grundlast %Y-%m-%dT%H:%M:%SZ'

    echo "=== The hard limit, set again after the register, read out of the cgroup ==="
    sudo docker update --memory=2g --memory-swap=2g nc_app_findling_backend >/dev/null
    CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
    printf 'memory.max=%s\n' "$(sudo cat "$SCOPE/memory.max")"
    printf 'memory.swap.max=%s\n' "$(sudo cat "$SCOPE/memory.swap.max")"
    sudo docker inspect nc_app_findling_backend \
        --format 'Image={{.Config.Image}} Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}} StartedAt={{.State.StartedAt}}'

    echo "=== memory.events, read BEFORE the measurement touches anything ==="
    sudo cat "$SCOPE/memory.events"

    echo "=== A. The base line of the container, model never loaded in this start ==="
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s\n' "$(sudo cat "$SCOPE/memory.current")"
    printf 'memory.peak=%s\n' "$(sudo cat "$SCOPE/memory.peak")"
    echo "-- the processes of the cgroup and their RSS in kB --"
    sudo docker exec nc_app_findling_backend sh -c 'ps -o pid,rss,comm -A' || true
    echo "-- the log of this start, so the arming is readable --"
    START=$(sudo docker inspect nc_app_findling_backend --format '{{.State.StartedAt}}')
    sudo docker logs --timestamps --since "$START" nc_app_findling_backend 2>&1 | tail -25
    printf 'pass-finished lines since this start: '
    sudo docker logs --since "$START" nc_app_findling_backend 2>&1 | grep -c 'pass finished' || true

    echo "=== B. The footprint of the weights alone, in a process of their own ==="
    sudo docker cp /home/ubuntu/work/49b-gewichte.py nc_app_findling_backend:/tmp/49b-gewichte.py
    sudo docker exec nc_app_findling_backend /app/.venv/bin/python /tmp/49b-gewichte.py

    echo "=== The cgroup right after B, so the share is visible ==="
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s\n' "$(sudo cat "$SCOPE/memory.current")"

    echo "=== C. Which step of the startup buys it, step by step ==="
    sudo docker cp /home/ubuntu/work/52-woher-die-grundlast.py nc_app_findling_backend:/tmp/52-woher.py
    sudo docker exec nc_app_findling_backend /app/.venv/bin/python /tmp/52-woher.py

    echo "=== memory.events again, after B and C, so the two readings bracket them ==="
    sudo cat "$SCOPE/memory.events"

    date -u +'grundlast-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"
echo "63-GRUNDLAST-FERTIG"
