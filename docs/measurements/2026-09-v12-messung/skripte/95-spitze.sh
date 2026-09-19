#!/bin/sh
# The first search as an EVENT, in two roles, plus the levels 1, 4 and 8.
#
# Why the same step runs twice, in four sentences. The follow up measurement
# measured the first search against a FULL vector stock and got the sentence the
# store claim rests on (anon 694,3 MB before, 1.116,6 MB after, plus 422,3 MB,
# and those are the model weights). This run has no stock at all before the
# rebuild, so the same reading here answers a different question, namely what a
# cold start costs when only the weights arrive. DI-07-02 asks whether the
# ceiling of 1,5 s has to be raised, and it asks about the WORSE of the two
# cases, which is the cold start on a full vector stock, because there the vector
# scan falls into the same single container call as the loading of the weights.
# So the step takes a role as an argument and runs once before the full run and
# once after it, and the role goes into the name of every raw file it writes.
#
# The order of the role nachher is not a preference, it is a constraint. A
# docker restart resets memory.peak and memory.events, so the OOM proof of the
# full run has to be taken BEFORE the restart. Taking it afterwards would prove
# nothing at all: the counters would read nought because they were cleared, not
# because nothing happened. This script therefore refuses to restart the
# container unless the raw file of the OOM proof is already on disk (T-10-17).
#
# Unchanged against 64-spitze.sh, on purpose: memory.events is read BEFORE the
# first search, the sampler runs beside it with a two second interval so the
# second of the peak is readable, EXACTLY ONE search is driven against a
# container that has never seen one, and the levels 1, 4 and 8 follow. anon and
# memory.current are read side by side everywhere, because a brute force scan
# pulls the vector stock into the file cache of the same cgroup and anon does not
# count it.
#
# One number changed against 64-spitze.sh and it is the single search. The
# predecessor drove its "first search alone" with rounds 3, which is three
# requests, so the first of them carried the cold start and the other two
# diluted it. DI-07-02 asks for the cold start, so the single search here is one
# request. The level series that follows keeps the parameters of the predecessor
# exactly, and it is the series the comparison of criterion 3 runs over.
#
# The password comes out of the environment variable FINDLING_LOAD_PASSWORD and
# is handed over with --password-env, which carries the NAME and not the value.
# An argument stands in the process list of the box and in every log that records
# the command (T-10-15).
#
# Usage: 95-spitze.sh <vorher|nachher>
# The exit codes: 2 an unknown role, 12 the role nachher without the OOM proof.
set -eu

rolle="${1:-}"
case "$rolle" in
vorher | nachher) ;;
*)
    echo "95-spitze: the role is a mandatory argument and it is vorher or nachher" >&2
    echo "95-spitze: usage: 95-spitze.sh <vorher|nachher>" >&2
    echo "95-spitze: vorher runs on an empty vector stock before the full run," >&2
    echo "95-spitze: nachher runs on the full stock after the OOM proof and a restart" >&2
    exit 2
    ;;
esac

# Everything a machine could differ in is a variable with a default, so this
# file carries no path of one machine. The first default is derived from the
# location of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
BASE="${BASE:-https://loadtest.infranode.dev}"
KONTO="${KONTO:-lasttest}"
SAMPLER="${SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
LAST="${LAST:-$REPO/scripts/ops/search_load.py}"
# The password file of the load test account on the box. The value is read into
# an environment variable and never handed to a command line.
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
# The raw file of the OOM proof of the full run. The role nachher refuses to
# restart the container before this file exists, because a restart clears
# memory.peak and memory.events. Plan 10-04 writes it.
OOM_BEWEIS="${OOM_BEWEIS:-$OUT/96-oom-beweis.txt}"
# The two figures the cold start is held against. The ceiling is the PHP
# constant ExAppService::REQUEST_TIMEOUT_SECONDS = 1.5, in milliseconds, and the
# predecessor is the OCS route figure of plan 07-01: 1.332,1 ms, which left a
# margin of 167,9 ms to that ceiling on an arm64 box.
DECKE_MS="${DECKE_MS:-1500}"
VORWERT_MS="${VORWERT_MS:-1332.1}"

mkdir -p "$OUT"
ZIEL="$OUT/95-spitze-$rolle.txt"
CSV="$OUT/95-$rolle.csv"
ERSTE="$OUT/95-$rolle-erste-suche.json"

FINDLING_LOAD_PASSWORD=$(sudo cat "$PWFILE")
export FINDLING_LOAD_PASSWORD

# The role nachher presupposes the OOM proof, and this is the check that turns
# that sentence into a refusal instead of a note in a plan.
if [ "$rolle" = 'nachher' ] && [ ! -s "$OOM_BEWEIS" ]; then
    echo "95-spitze: the role nachher needs the OOM proof of the full run first" >&2
    echo "95-spitze: $OOM_BEWEIS is missing or empty" >&2
    echo "95-spitze: a docker restart clears memory.peak and memory.events, so the" >&2
    echo "95-spitze: proof taken afterwards would read nought for the wrong reason" >&2
    exit 12
fi

{
    date -u +"spitze-$rolle-start %Y-%m-%dT%H:%M:%SZ"
    echo "rolle: $rolle"
    case "$rolle" in
    vorher) echo "bestand: leer, vor dem Volllauf" ;;
    nachher) echo "bestand: voll, nach dem OOM-Beweis und einem bewussten Neustart" ;;
    esac

    if [ "$rolle" = 'nachher' ]; then
        echo "=== The deliberate restart, and it happens AFTER the OOM proof ==="
        echo "the OOM proof is on disk: $OOM_BEWEIS"
        ls -la "$OOM_BEWEIS"
        echo "-- the counters one last time before they are cleared --"
        CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
        SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
        sudo cat "$SCOPE/memory.events"
        printf 'memory.peak=%s\n' "$(sudo cat "$SCOPE/memory.peak")"
        date -u +'neustart-start %Y-%m-%dT%H:%M:%SZ'
        sudo docker restart "$CONTAINER" >/dev/null
        date -u +'neustart-ende %Y-%m-%dT%H:%M:%SZ'
        # The container has to be up before a search is driven at it, and the
        # frist is measured against the slowest thing that happens here, which is
        # the arming of the poller and not the process start.
        sleep 30
        sudo docker inspect "$CONTAINER" \
            --format 'Running={{.State.Running}} StartedAt={{.State.StartedAt}} RestartCount={{.RestartCount}}'
        sudo docker logs --timestamps --tail 15 "$CONTAINER" 2>&1
    fi

    # Resolved here and not earlier, because the role nachher restarts the
    # container above and a stale scope path would read the wrong cgroup.
    CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
    printf 'cgroup: %s\n' "$SCOPE"

    echo "=== memory.events, read BEFORE the first search of this role ==="
    sudo cat "$SCOPE/memory.events"
    echo "-- and the two figures next to it, as the zero point of the peak --"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s memory.max=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" \
        "$(sudo cat "$SCOPE/memory.peak")" \
        "$(sudo cat "$SCOPE/memory.max")"

    echo "=== The sampler beside it, two seconds, so the second of the peak is readable ==="
    sudo sh "$SAMPLER" "$CONTAINER" 2 "$CSV" &
    SAMPLER_PID=$!
    printf 'sampler-pid %s\n' "$SAMPLER_PID"
    sleep 6

    echo "=== The very first search of this container start, exactly one request ==="
    date -u +'erste-suche-vor %Y-%m-%dT%H:%M:%SZ'
    sudo -E python3 "$LAST" \
        --base-url "$BASE" --user "$KONTO" --password-env FINDLING_LOAD_PASSWORD \
        --concurrency 1 --rounds 1 --container "$CONTAINER" \
        >"$ERSTE" 2>"$ERSTE.err" || true
    date -u +'erste-suche-nach %Y-%m-%dT%H:%M:%SZ'
    tail -5 "$ERSTE.err" || true
    echo "-- the cgroup right after the first search --"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"
    sudo cat "$SCOPE/memory.events"

    echo "=== The cold start of this role, against the ceiling and against 07-01 ==="
    python3 - "$ERSTE" "$rolle" "$DECKE_MS" "$VORWERT_MS" <<'PY'
import json
import pathlib
import sys

pfad, rolle, decke, vorwert = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])


def de(zahl: float) -> str:
    """German thousands and decimal separator, as the reports write them."""
    return f"{zahl:,.1f}".replace(",", "#").replace(".", ",").replace("#", ".")


text = pathlib.Path(pfad).read_text(encoding="utf-8") if pathlib.Path(pfad).is_file() else ""
if not text.strip():
    print("kaltstart-gemessen (keine Antwort, siehe die Fehlerdatei daneben)")
    raise SystemExit(0)

bericht = json.loads(text)
# search_load.py writes p50_ms, p95_ms and max_ms only if at least one request
# was answered. A role in which every request failed has to say so, not end in a
# KeyError over a report that exists.
if "max_ms" not in bericht:
    print(f"kaltstart-rolle              {rolle}")
    print(f"kaltstart-anfragen           {bericht.get('requests', 0)} "
          f"(davon fehlgeschlagen {bericht.get('failures', 0)})")
    print("kaltstart-gemessen           keine Anfrage wurde beantwortet")
    print(f"kaltstart-fehlerarten        {bericht.get('failure_kinds', {})}")
    raise SystemExit(0)

gemessen = float(bericht["max_ms"])
print(f"kaltstart-rolle              {rolle}")
print(f"kaltstart-anfragen           {bericht['requests']} (davon fehlgeschlagen {bericht['failures']})")
print(f"kaltstart-gemessen           {de(gemessen)} ms")
print(f"kaltstart-decke              {de(decke)} ms (ExAppService::REQUEST_TIMEOUT_SECONDS = 1.5)")
print(f"kaltstart-marge              {de(decke - gemessen)} ms")
print(f"kaltstart-vorwert            {de(vorwert)} ms (Plan 07-01, ueber den OCS-Weg)")
print(f"kaltstart-abstand-zum-vorwert {de(gemessen - vorwert)} ms")
if rolle == "nachher":
    print("Dies ist die Zahl, nach der DI-07-02 fragt: der Kaltstart auf vollem")
    print("Vektorbestand, also der schlechtere der beiden Faelle.")
print("Ueber die Konstante entscheidet dieses Skript nicht, es liefert die Zahl.")
PY

    for stufe in 1 4 8; do
        echo "=== Concurrency $stufe ==="
        date -u +"stufe-$stufe-vor %Y-%m-%dT%H:%M:%SZ"
        sudo -E python3 "$LAST" \
            --base-url "$BASE" --user "$KONTO" --password-env FINDLING_LOAD_PASSWORD \
            --concurrency "$stufe" --rounds 3 --container "$CONTAINER" \
            >"$OUT/95-$rolle-stufe-$stufe.json" 2>"$OUT/95-$rolle-stufe-$stufe.err" || true
        date -u +"stufe-$stufe-nach %Y-%m-%dT%H:%M:%SZ"
        tail -5 "$OUT/95-$rolle-stufe-$stufe.err" || true
        echo "-- the cgroup after concurrency $stufe --"
        sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
        printf 'memory.current=%s memory.peak=%s\n' \
            "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"
        sudo cat "$SCOPE/memory.events"
    done

    echo "=== The sampler down, and its closing line is the OOM proof of this role ==="
    sudo kill -TERM "$SAMPLER_PID" 2>/dev/null || true
    sleep 3
    tail -5 "$CSV"

    echo "=== memory.events, the full set of counters, at the end of this role ==="
    sudo cat "$SCOPE/memory.events"
    printf 'OOMKilled=%s\n' "$(sudo docker inspect "$CONTAINER" --format '{{.State.OOMKilled}}')"
    printf 'RestartCount=%s\n' "$(sudo docker inspect "$CONTAINER" --format '{{.RestartCount}}')"

    echo "=== The highest anon of this role, out of the csv ==="
    sudo python3 - "$CSV" <<'PY'
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

    date -u +"spitze-$rolle-ende %Y-%m-%dT%H:%M:%SZ"
} 2>&1 | tee "$ZIEL"

# The closing word keeps its fixed shape and names the role next to it, so a
# grep for the step finds both runs and can still tell them apart.
echo "95-SPITZE-FERTIG rolle=$rolle"
