#!/bin/sh
# The state of the box as the machine start left it, read before any intervention.
#
# Two things are settled here and nowhere else. First, memory.events: it has to be
# read before anything is touched, otherwise the numbers describe the tidy up and
# not the run (T-06.1-75, and the lesson of 06-11). Second, the counter proof to
# DI-05-36 on the image that was on the box when it was parked, which is the one
# from 06-11 and predates the fix of plan 06.1-01: the expectation is zero passes,
# and that zero is the before half of the comparison the new image answers.
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
ZIEL="$OUT/60-bestand.txt"

{
    date -u +'bestand %Y-%m-%dT%H:%M:%SZ'

    echo "=== The machine ==="
    printf 'arch=%s cores=%s\n' "$(uname -m)" "$(nproc)"
    free -h | head -2
    echo "-- the memory cap that makes the parity, read back --"
    cat /proc/cmdline

    echo "=== The container, as the machine start left it ==="
    sudo docker inspect nc_app_findling_backend \
        --format 'Image={{.Config.Image}} StartedAt={{.State.StartedAt}} Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}}'

    CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

    echo "=== memory.events, read BEFORE any intervention ==="
    sudo cat "$SCOPE/memory.events"
    echo "-- memory.events.local, for completeness --"
    sudo cat "$SCOPE/memory.events.local" 2>/dev/null || echo "(not present on this kernel)"

    echo "=== memory.stat and the two counters ==="
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s\n' "$(sudo cat "$SCOPE/memory.current")"
    printf 'memory.peak=%s\n' "$(sudo cat "$SCOPE/memory.peak")"
    printf 'memory.max=%s\n' "$(sudo cat "$SCOPE/memory.max")"

    echo "=== DI-05-36, counter proof on the OLD image: passes since the machine start ==="
    START=$(sudo docker inspect nc_app_findling_backend --format '{{.State.StartedAt}}')
    printf 'container-start %s\n' "$START"
    printf 'pass-finished lines: '
    sudo docker logs --since "$START" nc_app_findling_backend 2>&1 | grep -c 'pass finished' || true
    echo "-- the whole log of this start, so the zero is readable and not asserted --"
    sudo docker logs --timestamps --since "$START" nc_app_findling_backend 2>&1 | tail -20

    echo "=== The volume: corpus, index and the two databases ==="
    df -h /mnt/findling
    sudo ls -la /mnt/findling/docker/volumes/nc_app_findling_backend_data/_data

    echo "=== The marks in state.db, embedding_version among them ==="
    sudo python3 - <<'PY'
import sqlite3

path = "/mnt/findling/docker/volumes/nc_app_findling_backend_data/_data/state.db"
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
for key, value in connection.execute("select key, value from meta order by key"):
    print(f"  {key} = {value}")
counts = connection.execute(
    "select state, count(*) from files where deleted_at is null group by state order by state"
).fetchall()
print("  files by state:", counts)
PY

    date -u +'bestand-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"
echo "60-BESTAND-FERTIG"
