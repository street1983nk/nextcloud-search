#!/bin/sh
# The state of the box as the machine start left it, read before any intervention.
#
# This is 60-bestand.sh of the follow up measurement with one change and one
# addition, and both of them come out of what happened on 2026-09-07.
#
# The change: the sqlite query runs only if state.db is there. 60-bestand.sh
# opens the file without reservation, and on this box that file does not exist:
# the data store nc_app_findling_backend_data was removed on 07.09. at 06:46:03Z
# by an unregister --rm-data of a SECOND Nextcloud on the same docker daemon. A
# missing data store is the observation this run starts from, not the error that
# stops it, and an sqlite traceback here would end the step before the rest of
# the inventory is read.
#
# The addition: three figures that were assumed rather than read last time.
# mem=4G comes out of /proc/cmdline (it lives in a grub drop in and survives a
# reboot, which is exactly why it has to be read and not trusted), the free space
# on the data root is printed with a number (30 of 60 GB were used on 07.09., the
# new index needs about 0,85 GB, and the old image 06-11-arm still occupies
# space), and docker ps counts the Nextcloud instances on this daemon. More than
# one is a reason to stop: the volume name of an ExApp follows from its app id
# alone, so a --rm-data in step 3 would take the volume of the other instance
# with it (pitfall 5).
#
# memory.events is read here and nowhere earlier. Whoever reads it after the
# tidy up measures the tidy up and not the run (T-06.1-75, and the lesson of
# 06-11).
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
OUT="${OUT:-$SKRIPTE/../rohdaten}"
# The data root of the box, and the docker root plus the ExApp volume inside it.
DATA_ROOT="${DATA_ROOT:-/mnt/findling}"
VOLUME="${VOLUME:-$DATA_ROOT/docker/volumes/nc_app_findling_backend_data/_data}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
# A Nextcloud server container is one whose image carries the server itself:
# nextcloud/aio-nextcloud for an All-in-One instance, library/nextcloud for a
# hand rolled one. The other AIO containers (database, redis, apache,
# notify-push, imaginary, borgbackup, and the AppAPI daemon) carry other images
# and are not counted.
SERVER_IMAGES="${SERVER_IMAGES:-nextcloud/aio-nextcloud|(^|/)nextcloud:}"
# The memory cap that makes the comparison with the 4 GB box possible.
CMDLINE_CAP="${CMDLINE_CAP:-mem=4G}"

mkdir -p "$OUT"
ZIEL="$OUT/90-bestand.txt"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

{
    date -u +'bestand %Y-%m-%dT%H:%M:%SZ'

    echo "=== The machine ==="
    printf 'arch=%s cores=%s\n' "$(uname -m)" "$(nproc)"
    free -h | head -2
    echo "-- the memory cap that makes the parity, read back and not assumed --"
    cat /proc/cmdline
    if grep -q -- "$CMDLINE_CAP" /proc/cmdline; then
        echo "mem-cap-gefunden ja ($CMDLINE_CAP)"
    else
        echo "mem-cap-gefunden nein ($CMDLINE_CAP is NOT on the kernel command line)"
    fi

    echo "=== The Nextcloud instances on this docker daemon ==="
    echo "-- every running container, so the count below can be checked --"
    sudo docker ps --format '{{.Names}}  {{.Image}}  {{.Status}}'
    sudo docker ps --format '{{.Image}}' | grep -Ec "$SERVER_IMAGES" >"$WORK/instanzen" || true
    [ -s "$WORK/instanzen" ] || echo 0 >"$WORK/instanzen"
    instanzen=$(cat "$WORK/instanzen")
    printf 'nextcloud-instanzen %s\n' "$instanzen"
    if [ "$instanzen" -eq 1 ]; then
        echo "nextcloud-einzahl ja"
    else
        echo "nextcloud-einzahl nein"
        echo "the run stops here: --rm-data in step 3 would hit the volume of"
        echo "every instance that carries the same app id (pitfall 5, 07.09.)"
    fi

    echo "=== The container, as the machine start left it ==="
    sudo docker inspect "$CONTAINER" \
        --format 'Image={{.Config.Image}} StartedAt={{.State.StartedAt}} Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}} RestartCount={{.RestartCount}} OOMKilled={{.State.OOMKilled}}'

    CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

    echo "=== memory.events, read BEFORE any intervention ==="
    sudo cat "$SCOPE/memory.events"
    echo "-- memory.events.local, for completeness --"
    sudo cat "$SCOPE/memory.events.local" 2>/dev/null || echo "(not present on this kernel)"

    echo "=== memory.stat and the counters, anon and memory.current side by side ==="
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s\n' "$(sudo cat "$SCOPE/memory.current")"
    printf 'memory.peak=%s\n' "$(sudo cat "$SCOPE/memory.peak")"
    printf 'memory.max=%s\n' "$(sudo cat "$SCOPE/memory.max")"
    printf 'memory.swap.max=%s\n' "$(sudo cat "$SCOPE/memory.swap.max")"

    echo "=== Whether the parked container was armed at all: passes since its start ==="
    START=$(sudo docker inspect "$CONTAINER" --format '{{.State.StartedAt}}')
    printf 'container-start %s\n' "$START"
    printf 'pass-finished lines: '
    sudo docker logs --since "$START" "$CONTAINER" 2>&1 | grep -c 'pass finished' || true
    echo "-- the tail of this start, so the number is readable and not asserted --"
    sudo docker logs --timestamps --since "$START" "$CONTAINER" 2>&1 | tail -20

    echo "=== The space on the data root, with a number ==="
    df -h "$DATA_ROOT"
    df -BG "$DATA_ROOT"
    echo "-- what the images occupy, the old 06-11-arm among them --"
    sudo docker image ls --format '{{.Repository}}:{{.Tag}}  {{.Size}}  {{.ID}}'
    echo "-- images, containers, volumes and build cache in one place --"
    sudo docker system df

    echo "=== The volume of the ExApp, and what is left in it ==="
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'
    sudo ls -la "$VOLUME" 2>&1 || echo "(the volume directory is not readable or not there)"

    echo "=== The corpus, which is the part that survived 07.09. ==="
    sudo du -sh "$DATA_ROOT/ncdata/lasttest/files/loadtest" 2>&1 || \
        echo "(the corpus directory is not readable or not there)"

    echo "=== The marks in state.db, but only if there is a state.db ==="
    # Read only if the file is there. A missing data store is the observation
    # this run starts from, and the query would otherwise stop the step with an
    # sqlite error before the sections above are of any use.
    if sudo test -f "$VOLUME/state.db"; then
        sudo python3 - "$VOLUME/state.db" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
for key, value in connection.execute("select key, value from meta order by key"):
    print(f"  {key} = {value}")
# The column is called state and not verdict. Read once against the real schema
# before it is armed, which is the second half of pitfall 8.
counts = connection.execute(
    "select state, count(*) from files where deleted_at is null group by state order by state"
).fetchall()
print("  files by state:", counts)
PY
    else
        echo "kein state.db im Volumen, erwartet nach dem Volumenvorfall vom 07.09."
        echo "(the data store was removed at 06:46:03Z by an unregister --rm-data of a"
        echo " second Nextcloud on this daemon: state.db, vectors.db, the 785 MB tantivy"
        echo " index and the word list went with it. This is an observation, not a fault)"
    fi

    date -u +'bestand-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# The verdict is read back out of the temporary file rather than out of the
# pipeline, because the exit status of a pipeline that ends in tee is the status
# of tee.
instanzen=$(cat "$WORK/instanzen")
if [ "$instanzen" -ne 1 ]; then
    echo "90-bestand: $instanzen Nextcloud instances are running, expected exactly one" >&2
    echo "90-bestand: step 3 runs --rm-data, and it would hit every one of them" >&2
    exit 5
fi

echo "90-BESTAND-FERTIG"
