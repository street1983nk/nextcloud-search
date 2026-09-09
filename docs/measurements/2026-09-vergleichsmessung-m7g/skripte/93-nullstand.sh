#!/bin/sh
# Both halves stand at nought, proven with figures, before the base load is
# measured and before the rebuild is started.
#
# Why this step exists at all. The base load of step 5 is the MESS-01 core
# figure, and it is only a base load if nothing has been indexed yet and the
# model has never been loaded. "The volume is empty" is exactly the kind of
# sentence the two predecessor reports could not back up at the tree hash, so
# this step reads four sources and prints a number from each of them:
#
#   1. the contents of the volume: state.db, vectors.db and the tantivy
#      directory have to be missing or empty
#   2. the end states of oc_findling_file_state, over occ
#   3. the marks in meta, but only if a state.db exists at all
#   4. the work stock of the PHP half, over occ findling:index without arguments
#
# Why the -n on the restart. Without it the command asks back ("Start over?
# [y/N]"), gets no answer in a script, prints "Nothing was changed." and returns
# SUCCESS. The caller then believes a rebuild is running while nothing was
# queued at all, and the next thing anybody notices is a work stock that stays
# at nought for hours.
#
# Why the wait is 360 seconds and not 60. Two clocks, and the frist is measured
# against the slower one: the poller of the container backs off up to 300 s, and
# All-in-One calls cron.php only every five minutes, where the FIRST job of the
# app queues nothing yet. So two rounds of the five minute system cron have to
# pass before an empty work stock is a statement rather than an artefact. The
# counter proof of the semantic run declared a run dead 52 seconds too early for
# exactly this reason (pitfall 11).
#
# What happens if the work stock is still nought afterwards: this script writes
# arbeitsvorrat-da nein and ends with 10. That is a red verdict and not a
# success. Assumption A2 of the research names the remedy, and 00-ablauf.md
# carries it: the command is issued again and the frist starts over. It is not
# one of the four abort paths of the run.
set -eu

# Everything a machine could differ in is a variable with a default, so this
# file carries no path of one machine. The first default is derived from the
# location of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
OUT="${OUT:-$SKRIPTE/../rohdaten}"
DATA_ROOT="${DATA_ROOT:-/mnt/findling}"
VOLUME="${VOLUME:-$DATA_ROOT/docker/volumes/nc_app_findling_backend_data/_data}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
# The frist, in seconds, against the slowest clock involved. 300 s poller backoff
# plus two rounds of the five minute system cron, so 360 is the floor and not the
# target.
FRIST="${FRIST:-360}"

mkdir -p "$OUT"
ZIEL="$OUT/93-nullstand.txt"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

# The two blocks of the status output, read out of one call rather than out of
# two: they are two sources, but asking twice would let them disagree.
vorrat_von() {
    awk '/^Work stock/ {found = 1; next}
         found && /^  (scheduled|handed to the worker)/ {sum += $NF}
         END {print sum + 0}' "$1"
}

{
    date -u +'nullstand-start %Y-%m-%dT%H:%M:%SZ'
    echo "volumen: $VOLUME"

    CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

    echo "=== memory.events, reading 3 of the run, BEFORE the restart is issued ==="
    sudo cat "$SCOPE/memory.events"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s memory.max=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" \
        "$(sudo cat "$SCOPE/memory.peak")" \
        "$(sudo cat "$SCOPE/memory.max")"

    echo "=== Source 1: the contents of the volume ==="
    sudo ls -la "$VOLUME" 2>&1 || echo "(the volume directory is not readable or not there)"
    for datei in state.db vectors.db; do
        if sudo test -f "$VOLUME/$datei"; then
            printf '%s vorhanden, groesse in byte: %s\n' \
                "$datei" "$(sudo stat -c '%s' "$VOLUME/$datei")"
        else
            printf '%s fehlt\n' "$datei"
        fi
    done
    if sudo test -d "$VOLUME/index"; then
        printf 'tantivy-verzeichnis vorhanden, dateien: %s, groesse: %s\n' \
            "$(sudo find "$VOLUME/index" -type f | wc -l)" \
            "$(sudo du -sh "$VOLUME/index" | cut -f1)"
    else
        echo "tantivy-verzeichnis fehlt"
    fi

    echo "=== Source 2 and 4: the end states and the work stock, over occ ==="
    occ findling:index >"$WORK/status-vorher.txt" 2>&1 || true
    cat "$WORK/status-vorher.txt"
    echo "-- source 4, the work stock of the PHP half, as one number --"
    printf 'arbeitsvorrat-vorher %s\n' "$(vorrat_von "$WORK/status-vorher.txt")"
    echo "-- source 2, the end states as Nextcloud recorded them --"
    # The column is called state and not verdict, and the rows below are the ones
    # oc_findling_file_state holds. On this box 37 rows were left after 07.09.
    sed -n '/^End states/,/^$/p' "$WORK/status-vorher.txt"

    echo "=== Source 3: the marks in meta, but only if there is a state.db ==="
    if sudo test -f "$VOLUME/state.db"; then
        sudo python3 - "$VOLUME/state.db" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
for key, value in connection.execute("select key, value from meta order by key"):
    print(f"  {key} = {value}")
# The column is called state and not verdict. Pitfall 8, second half: a reading
# script is run dry against the real schema once before it is armed.
counts = connection.execute(
    "select state, count(*) from files where deleted_at is null group by state order by state"
).fetchall()
print("  files by state:", counts)
PY
    else
        echo "kein state.db im Volumen, also keine Marken zu lesen"
        echo "(expected: the data store was removed on 07.09. and step 3 registered"
        echo " an empty one. The container seeds it on its first pass)"
    fi

    echo "=== The rebuild, queued with -n so the command does not ask back ==="
    date -u +'restart-start %Y-%m-%dT%H:%M:%SZ'
    occ findling:index --restart -n 2>&1
    date -u +'restart-ende %Y-%m-%dT%H:%M:%SZ'
    echo "-- if the line above says 'Nothing was changed.' the -n did not take --"

    echo "=== The frist of $FRIST seconds, against the slowest clock involved ==="
    echo "-- 300 s poller backoff and two rounds of the five minute system cron --"
    sleep "$FRIST"
    date -u +'frist-ende %Y-%m-%dT%H:%M:%SZ'

    echo "=== The work stock after the frist, which is the verdict of this step ==="
    occ findling:index >"$WORK/status-nachher.txt" 2>&1 || true
    cat "$WORK/status-nachher.txt"
    vorrat=$(vorrat_von "$WORK/status-nachher.txt")
    printf 'arbeitsvorrat-nachher %s\n' "$vorrat"
    printf '%s\n' "$vorrat" >"$WORK/vorrat"
    if [ "$vorrat" -gt 0 ]; then
        echo "arbeitsvorrat-da ja"
    else
        echo "arbeitsvorrat-da nein"
        echo "ROTES URTEIL: the rebuild did not start. Assumption A2 of the research"
        echo "  names the remedy and 00-ablauf.md carries it: issue findling:index"
        echo "  --restart -n again and let the frist run over. Do NOT read the base"
        echo "  load as if the run had started."
    fi
    echo "-- the log of the container over the frist, so the poller is readable --"
    sudo docker logs --timestamps --tail 25 "$CONTAINER" 2>&1

    date -u +'nullstand-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Read back out of the file rather than out of the pipeline, because the exit
# status of a pipeline that ends in tee is the status of tee.
vorrat=$(cat "$WORK/vorrat" 2>/dev/null || echo 0)
if [ "$vorrat" -le 0 ]; then
    echo "93-nullstand: the work stock is still nought after $FRIST seconds" >&2
    echo "93-nullstand: issue findling:index --restart -n again (assumption A2)" >&2
    exit 10
fi

echo "93-NULLSTAND-FERTIG"
