#!/bin/sh
# The hard limit, then the idle base load, in the form of 63-grundlast.sh.
#
# The limit first, and read back out of the cgroup: a register throws it away
# (pitfall 4), and a run that measures against 4 GB when it means to measure
# against 2 measures nothing at all. Nothing is measured before that line is
# proven.
#
# Then the base load, with the same questions as the two predecessors and with
# the two helper scripts UNCHANGED. That is not tidiness, it is the whole point:
# the step names of 52-woher-die-grundlast.py are the comparison keys, and a
# renamed line turns a comparison figure into a merely adjacent one, which is
# exactly what criterion 3 forbids.
#
#   A. the anon base line of the container, model never loaded
#   B. the footprint of the weights alone, in a process of their own
#   C. which step of the startup buys it, step by step
#   D. the fine decomposition into five separately named items
#
# Part D is new against 63-grundlast.sh. It runs 01-grundlast-fein.py of the fine
# measurement inside a container of the image, the way measure.yml does it, with
# --network none and the script directory as a read only mount. Plan 10-02 has
# that same measurement from a native arm runner (five items, 543,7 MB), so this
# is the first time the figure comes from the box itself and stands next to it.
#
# Part D carries a guard the workflow does not have, and DI-10-01 is the reason.
# A docker run creates an empty directory for a mount whose source does not
# exist, the tool then writes an empty file, and the step stays green: that is
# how chars-per-token-prose.txt in measure.yml came out at 0 bytes. So the mount
# source is checked before the run and the output is checked afterwards, and a
# missing decomposition is a named verdict rather than a blank in the report.
#
# The plausibility line at the end is NOT an abort. The expectation is roughly
# 118 to 150 MB (calculated from the lazy build saving of 575,0 MB against the
# arm base load), and the predecessors measured 691,8 MB in 06-11 and 693,4 MB in
# the follow up measurement. A measured base load around 690 MB would mean the
# lazy build does not take on this box, and that would be the most important
# finding of the whole run. It has to be measured and reported, not thrown away,
# so the script says grundlast-erwartung verfehlt and carries on.
set -eu

# Everything a machine could differ in is a variable with a default, so this
# file carries no path of one machine. The first default is derived from the
# location of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend:dev}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
# The two helpers of the predecessors, called unchanged. Their step names are the
# comparison keys of criterion 3.
SEMANTIK="${SEMANTIK:-$REPO/docs/measurements/2026-09-05-semantiklauf-m7g/skripte}"
GEWICHTE="${GEWICHTE:-$SEMANTIK/49b-gewichte.py}"
WOHER="${WOHER:-$SEMANTIK/52-woher-die-grundlast.py}"
# The fine decomposition, and the directory that is mounted for it, exactly as
# measure.yml mounts it.
FEIN_DIR="${FEIN_DIR:-$REPO/docs/measurements/2026-09-grundlast-fein/skripte}"
FEIN="${FEIN:-$FEIN_DIR/01-grundlast-fein.py}"
# The threshold of the plausibility line, in bytes. 400 MB, well above the
# expectation and well below the two predecessor figures.
SCHWELLE="${SCHWELLE:-419430400}"

mkdir -p "$OUT"
ZIEL="$OUT/94-grundlast.txt"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

mb_von() {
    awk -v bytes="$1" 'BEGIN { printf "%.1f", bytes / 1048576 }'
}

{
    date -u +'grundlast %Y-%m-%dT%H:%M:%SZ'

    echo "=== The hard limit, set again after the register, read out of the cgroup ==="
    sudo docker update --memory=2g --memory-swap=2g "$CONTAINER" >/dev/null
    CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
    printf 'memory.max=%s\n' "$(sudo cat "$SCOPE/memory.max")"
    printf 'memory.swap.max=%s\n' "$(sudo cat "$SCOPE/memory.swap.max")"
    sudo docker inspect "$CONTAINER" \
        --format 'Image={{.Config.Image}} StartedAt={{.State.StartedAt}} RestartCount={{.RestartCount}}'

    echo "=== memory.events, reading 4 of the run, BEFORE the measurement touches anything ==="
    sudo cat "$SCOPE/memory.events"

    echo "=== A. The base line of the container, model never loaded in this start ==="
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    anon=$(sudo grep -E '^anon ' "$SCOPE/memory.stat" | awk '{print $2}')
    printf '%s\n' "$anon" >"$WORK/anon"
    printf 'memory.current=%s\n' "$(sudo cat "$SCOPE/memory.current")"
    printf 'memory.peak=%s\n' "$(sudo cat "$SCOPE/memory.peak")"
    echo "-- the processes of the cgroup and their RSS in kB --"
    sudo docker exec "$CONTAINER" sh -c 'ps -o pid,rss,comm -A' || true
    echo "-- the log of this start, so the arming is readable --"
    START=$(sudo docker inspect "$CONTAINER" --format '{{.State.StartedAt}}')
    sudo docker logs --timestamps --since "$START" "$CONTAINER" 2>&1 | tail -25
    printf 'pass-finished lines since this start: '
    sudo docker logs --since "$START" "$CONTAINER" 2>&1 | grep -c 'pass finished' || true

    echo "=== B. The footprint of the weights alone, in a process of their own ==="
    sudo docker cp "$GEWICHTE" "$CONTAINER:/tmp/49b-gewichte.py"
    sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/49b-gewichte.py

    echo "=== The cgroup right after B, so the share is visible ==="
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s\n' "$(sudo cat "$SCOPE/memory.current")"

    echo "=== C. Which step of the startup buys it, step by step ==="
    # Copied and called unchanged. The step names in its output are the
    # comparison keys, and none of them is renamed anywhere in this run.
    sudo docker cp "$WOHER" "$CONTAINER:/tmp/52-woher.py"
    sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/52-woher.py

    echo "=== D. The fine decomposition into five named items, as measure.yml runs it ==="
    if [ ! -f "$FEIN" ]; then
        echo "feinmessung-vollstaendig nein"
        echo "the mount source $FEIN does not exist. A docker run would create an"
        echo "empty directory for it and the tool would write an empty file, which is"
        echo "exactly how chars-per-token-prose.txt came out at 0 bytes (DI-10-01)."
        echo nein >"$WORK/fein-ok"
    else
        echo ja >"$WORK/fein-ok"
        sudo docker run --rm --network none \
            -v "$FEIN_DIR:/skripte:ro" \
            --entrypoint /app/.venv/bin/python "$IMAGE" \
            /skripte/01-grundlast-fein.py >"$WORK/fein.txt" 2>"$WORK/fein.err" || true
        cat "$WORK/fein.txt"
        if [ -s "$WORK/fein.err" ]; then
            echo "-- standard error of part D --"
            sed 's/^/  /' "$WORK/fein.err"
        fi
        # The output has to carry the base line and the last of the five items,
        # or the file is a blank with a section title over it.
        if grep -q '00-leerer-prozess' "$WORK/fein.txt" && grep -q '12c-zweiter-chunkerlauf' "$WORK/fein.txt"; then
            echo "feinmessung-vollstaendig ja"
        else
            echo "feinmessung-vollstaendig nein"
            echo "the output carries no 00-leerer-prozess or no 12c-zweiter-chunkerlauf,"
            echo "so the five items of plan 10-02 have nothing to be held against"
            echo nein >"$WORK/fein-ok"
        fi
        echo "-- the native arm expectation of plan 10-02, for the report --"
        echo "erwartung-fein-arm64 543,7 MB over five items, base line 13,0 MB"
    fi

    echo "=== memory.events again, after B, C and D, so the readings bracket them ==="
    sudo cat "$SCOPE/memory.events"

    echo "=== The plausibility line, and it is not an abort ==="
    gemessen_mb=$(mb_von "$anon")
    printf 'grundlast-gemessen            %s MB (anon of part A, %s bytes)\n' "$gemessen_mb" "$anon"
    printf 'grundlast-erwartet            118 bis 150 MB (calculated, assumption A5)\n'
    printf 'grundlast-vorwert-06-11       691,8 MB\n'
    printf 'grundlast-vorwert-nachmessung 693,4 MB\n'
    if [ "$anon" -gt "$SCHWELLE" ]; then
        printf 'grundlast-erwartung verfehlt: %s MB gemessen, 118 bis 150 MB erwartet\n' "$gemessen_mb"
        echo "This is a finding and not a measurement error. A base load around 690 MB"
        echo "means the lazy build does not take on this box, and that is the most"
        echo "important thing this run could say. It is reported, not repeated."
    else
        printf 'grundlast-erwartung getroffen: %s MB liegt unter der Schwelle\n' "$gemessen_mb"
    fi

    date -u +'grundlast-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# The one refusal of this step, read back out of the file because the exit status
# of a pipeline that ends in tee is the status of tee. The base load itself is
# never a reason to stop; an empty part D is, because a blank in the report is
# the failure this whole phase is about.
if [ "$(cat "$WORK/fein-ok" 2>/dev/null || echo nein)" != 'ja' ]; then
    echo "94-grundlast: part D produced no decomposition (DI-10-01)" >&2
    echo "94-grundlast: check the mount source and run this step again" >&2
    exit 11
fi

echo "94-GRUNDLAST-FERTIG"
