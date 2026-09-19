#!/bin/sh
# The watchman of the full run. It does three things nobody can do by hand at
# night, and it does them in this order, because they depend on each other.
#
#   1. It notices the transition from the first track to the second and drives
#      the search load sample EXACTLY THEN. During the trailing run, not before
#      and not after: that is the question the plan asks.
#   2. It notices the end of BOTH tracks. End here means: the work stock is empty
#      AND the figure embedded has stood still for three recordings. The stock
#      alone is not enough, because the second track runs for hours on an empty
#      stock; embedded alone is not enough either, because the figure stands
#      still between two claims without the track being finished.
#   3. It takes the OOM proof AFTER the run and BEFORE any intervention, and
#      measures the vector stock afterwards. A proof an hour later is still
#      valid, one after the first restart is none at all.
#
# It does not ask the instance itself: it reads the last line of the recordings
# of 96d-statusbeobachter.py. That process holds the session, and two ways to log
# in are two ways that can break. The reader is 96c-lesen.py, and its counters
# come from under "backend": the top level indexed is the PHP half and stays 0 by
# design (pitfall 8, which cost the semantic run nine hours of blind logging).
#
# **The one change against 42b-wachter.sh.** The two search load samples run over
# scripts/ops/search_load.py and no longer over 45-suchlast.py. That predecessor
# reaches its helper module through a directory of the load test box, and the
# module does not live in this repository at all, so a run of it cannot be
# repeated from a checkout; criterion 4 of this phase asks for exactly that.
# search_load.py exists for that reason, takes the address, the account and the
# container as arguments and imports nothing outside the standard library.
#
# The parameters of both samples are concurrency 1 and ten rounds, so that the
# figures are comparable to the two readings of the semantic run over the same
# OCS route: 1.129,0 ms p95 while the second track was running, and 524,0 ms p95
# on a full vector stock without side load.
#
# **The contract of this run is a file, and the message is the extra**
# (pitfall 6). After the OOM proof and the vector stock this script writes
# 00-FERTIG with the moment, the duration and the wake word, and ONLY THEN does
# it call the notification chain. The topic of the chain answered 403 on 05.09.
# from this very box; a step that hangs on a message arriving would have ended
# there.
#
# The password comes out of a file into an environment variable and is handed on
# with --password-env, which carries the NAME and not the value. An argument
# stands in the process list of the box and in every log that records the command
# (T-10-27).
#
# The exit codes: 13 the round cap was reached without the end of both tracks, so
# the run is INCOMPLETE and the report has to say so; 14 there was never a usable
# recording, so the watchman watched nothing.
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
BASE="${BASE:-https://loadtest.infranode.dev}"
KONTO="${KONTO:-lasttest}"
AUFNAHMEN="${AUFNAHMEN:-$OUT/96-statusseite.jsonl}"
CSV="${CSV:-$OUT/96-volllauf.csv}"
LESER="${LESER:-$SKRIPTE/96c-lesen.py}"
LAST="${LAST:-$REPO/scripts/ops/search_load.py}"
BESTAND="${BESTAND:-$REPO/docs/measurements/2026-09-05-semantiklauf-m7g/skripte/42d-bestand.py}"
MELDEKETTE="${MELDEKETTE:-$SKRIPTE/96e-ntfy-watch.sh}"
# The password file of the load test account on the box. The value is read into
# an environment variable and never handed to a command line.
PWFILE="${PWFILE:-$HOME/work/.pw/lasttest}"
# The raw file of the OOM proof. This name is an interface: 95-spitze.sh in the
# role nachher refuses its restart with exit code 12 as long as the file is
# missing, because a restart clears memory.peak and memory.events.
OOM_BEWEIS="${OOM_BEWEIS:-$OUT/96-oom-beweis.txt}"
FERTIG="${FERTIG:-$OUT/00-FERTIG}"
# The three numbers of the loop, unchanged against the predecessor: 340 rounds of
# five minutes are a good day and a half, the transition is called at the first
# two hundred vectors, and three still recordings are fifteen minutes of quiet.
DECKEL="${DECKEL:-340}"
INTERVALL="${INTERVALL:-300}"
SCHWELLE="${SCHWELLE:-200}"
STILL="${STILL:-3}"
WECKWORT="${WECKWORT:-volllauf pruefen}"

mkdir -p "$OUT"
ZIEL="$OUT/96b-waechter.txt"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

FINDLING_LOAD_PASSWORD=$(sudo cat "$PWFILE")
export FINDLING_LOAD_PASSWORD

START=$(date +%s)
CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"

# One reading of the cgroup, always both figures side by side: anon is the heap,
# memory.current counts the page cache of the same cgroup, and the vector store
# is read by a brute force scan that lands in exactly that cache (pattern 3).
zaehler() {
    printf -- '-- cgroup-lesung %s --\n' "$1"
    sudo cat "$SCOPE/memory.events"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s memory.max=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" \
        "$(sudo cat "$SCOPE/memory.peak")" \
        "$(sudo cat "$SCOPE/memory.max")"
}

# The full OOM proof, all six counters plus the two figures of the container.
# Written to its own raw file, because the next step reads that file rather than
# a sentence in a plan.
oom_beweis() {
    {
        date -u +"oom-beweis $1 %Y-%m-%dT%H:%M:%SZ"
        echo "-- 1. memory.events of the cgroup --"
        sudo cat "$SCOPE/memory.events"
        echo "-- 2. memory.events.local --"
        sudo cat "$SCOPE/memory.events.local"
        echo "-- 3. memory.max, memory.peak, memory.current --"
        sudo cat "$SCOPE/memory.max" "$SCOPE/memory.peak" "$SCOPE/memory.current"
        echo "-- 4. OOMKilled and the restart count of the container --"
        sudo docker inspect "$CONTAINER" \
            --format 'OOMKilled={{.State.OOMKilled}} RestartCount={{.RestartCount}} Status={{.State.Status}} StartedAt={{.State.StartedAt}}'
    } 2>&1
}

# One search load sample over the route a user takes. Concurrency 1 and ten
# rounds in both places, so the two figures are comparable with each other and
# with the two readings of the semantic run.
suchlast() {
    sudo -E python3 "$LAST" \
        --base-url "$BASE" --user "$KONTO" --password-env FINDLING_LOAD_PASSWORD \
        --concurrency 1 --rounds 10 --container "$CONTAINER" \
        >"$1" 2>"$1.err" || true
    tail -5 "$1.err" || true
}

RUNDE=0
LEER=0
GESEHEN=0
SUCHLAST_GEFAHREN=0
LETZTES_EMBEDDED=-1
EMBEDDED_STILL=0
LESUNGEN=0

{
    date -u +'waechter-start %Y-%m-%dT%H:%M:%SZ'
    printf 'aufnahmen: %s\n' "$AUFNAHMEN"
    printf 'leser: %s\n' "$LESER"
    printf 'lastwerkzeug: %s\n' "$LAST"
    printf 'deckel: %s runden a %s s\n' "$DECKEL" "$INTERVALL"
    echo "vergleichswerte der Suchlast: 1.129,0 ms p95 im Nachlauf, 524,0 ms p95 bei vollem Bestand"

    while [ "$RUNDE" -lt "$DECKEL" ]; do
        RUNDE=$((RUNDE + 1))
        # Captured into a variable first and defaulted, because the watchman runs
        # under set -eu: a reader that printed nothing would leave $1 unset and
        # end the watchman over a half written line.
        lesung=$(tail -1 "$AUFNAHMEN" 2>/dev/null | python3 "$LESER" 2>/dev/null || true)
        [ -n "$lesung" ] || lesung='unklar unklar unklar'
        # shellcheck disable=SC2086
        set -- $lesung
        vorrat="${1:-unklar}"
        indexed="${2:-unklar}"
        embedded="${3:-unklar}"
        if [ "$vorrat" != unklar ] || [ "$embedded" != unklar ]; then
            LESUNGEN=$((LESUNGEN + 1))
        fi

        case "$vorrat" in
        '0' | unklar) ;;
        *) GESEHEN=1 ;;
        esac

        # The transition: the second track has begun. From the first vectors on
        # the question of the plan is answerable, and it is only answerable while
        # the track is running.
        if [ "$SUCHLAST_GEFAHREN" -eq 0 ] && [ "$embedded" != unklar ] && [ "$embedded" -gt "$SCHWELLE" ]; then
            echo "=== The transition from the first to the second track, reading 9 of the list ==="
            zaehler 'am-uebergang-der-spuren'
            date -u +'suchlast-nachlauf-start %Y-%m-%dT%H:%M:%SZ'
            suchlast "$OUT/96-suchlast-nachlauf.json"
            date -u +'suchlast-nachlauf-ende %Y-%m-%dT%H:%M:%SZ'
            zaehler 'nach-der-suchlast-im-nachlauf'
            SUCHLAST_GEFAHREN=1
        fi

        # Does the second track stand still?
        if [ "$embedded" != unklar ] && [ "$embedded" = "$LETZTES_EMBEDDED" ]; then
            EMBEDDED_STILL=$((EMBEDDED_STILL + 1))
        else
            EMBEDDED_STILL=0
        fi
        if [ "$embedded" != unklar ]; then
            LETZTES_EMBEDDED="$embedded"
        fi

        if [ "$vorrat" = '0' ] && [ "$GESEHEN" -eq 1 ] &&
            [ "$EMBEDDED_STILL" -ge "$STILL" ] && [ "$SUCHLAST_GEFAHREN" -eq 1 ]; then
            LEER=$((LEER + 1))
        else
            LEER=0
        fi

        date -u +"waechter runde=$RUNDE vorrat=$vorrat indexed=$indexed embedded=$embedded gesehen=$GESEHEN still=$EMBEDDED_STILL leer=$LEER %Y-%m-%dT%H:%M:%SZ"
        if [ "$LEER" -ge "$STILL" ]; then
            break
        fi
        sleep "$INTERVALL"
    done

    if [ "$LEER" -ge "$STILL" ]; then
        echo 'ende-erkannt ja' >"$WORK/urteil"
    else
        echo 'ende-erkannt nein' >"$WORK/urteil"
    fi
    printf 'lesungen %s\n' "$LESUNGEN" >>"$WORK/urteil"
    date -u +'lauf-ende-erkannt %Y-%m-%dT%H:%M:%SZ'
    cat "$WORK/urteil"

    # The OOM proof, taken here and not further down, because everything that
    # follows is an intervention: a search load sample raises memory.peak, and a
    # peak read after it is a peak of the measurement rather than of the run. The
    # same counters are read once more at the very end of this script and appended
    # to the same file, labelled, so both readings are on record.
    echo "=== The OOM proof, reading 10 of the list, BEFORE any intervention ==="
    oom_beweis 'ende-beider-spuren-vor-jedem-eingriff' | tee "$OOM_BEWEIS"

    echo "=== The work stock as the PHP half reports it ==="
    sudo docker exec --user www-data "$NEXTCLOUD" php occ findling:index 2>&1 || true

    echo "=== Search load AFTER the run, on the full vector stock ==="
    date -u +'suchlast-danach-start %Y-%m-%dT%H:%M:%SZ'
    suchlast "$OUT/96-suchlast-danach.json"
    date -u +'suchlast-danach-ende %Y-%m-%dT%H:%M:%SZ'
    zaehler 'nach-der-suchlast-bei-vollem-bestand'

    echo "=== The observers down, so their closing lines are written ==="
    touch /tmp/sampler-stop
    sleep 3
    sudo pkill -TERM -f "rss_sampler.sh $CONTAINER" || true
    pkill -TERM -f '96d-statusbeobachter' || true
    sleep 5
    sudo chown "$(id -u):$(id -g)" "$OUT"/* 2>/dev/null || true
    grep 'summary' "$CSV" || true
    wc -l "$CSV" "$AUFNAHMEN" || true

    echo "=== The vector stock: chunks, documents and bytes per document ==="
    {
        date -u +'vektorbestand %Y-%m-%dT%H:%M:%SZ'
        echo "-- the files of the data store, with their sizes --"
        sudo docker exec "$CONTAINER" sh -c 'ls -la /nc_app_findling_backend_data; du -sb /nc_app_findling_backend_data/* 2>/dev/null'
        echo "-- chunks, documents and bytes per document, over 42d-bestand.py --"
        sudo docker cp "$BESTAND" "$CONTAINER:/tmp/42d-bestand.py"
        sudo docker exec "$CONTAINER" /app/.venv/bin/python /tmp/42d-bestand.py
    } 2>&1 | tee "$OUT/96-vektorbestand.txt"

    echo "=== The same counters once more, at the end of the watchman ==="
    oom_beweis 'ende-des-waechters-nach-den-nachlaufschritten' | tee -a "$OOM_BEWEIS"

    date -u +'waechter-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Everything below the pipeline, because the return code of a pipeline belongs to
# tee: an exit inside the block above would only leave the subshell, and the
# refusal would be a line in the raw file that nobody reads.
urteil=$(head -1 "$WORK/urteil" 2>/dev/null || echo 'ende-erkannt nein')
lesungen=$(sed -n 's/^lesungen //p' "$WORK/urteil" 2>/dev/null || echo 0)

# The wake file, and it is written BEFORE the notification chain is called. The
# file is the contract; the message is the extra, and it is the part that failed
# with a 403 on 05.09. from this very box.
DAUER=$(awk -v s="$(($(date +%s) - START))" 'BEGIN{printf "%.1f", s/3600}')
{
    date -u +'volllauf-fertig %Y-%m-%dT%H:%M:%SZ'
    printf 'stunden=%s\n' "$DAUER"
    printf '%s\n' "$urteil"
    printf 'oom-beweis=%s\n' "$OOM_BEWEIS"
    printf 'weckwort: %s\n' "$WECKWORT"
} >"$FERTIG"

if [ -x "$MELDEKETTE" ] || [ -f "$MELDEKETTE" ]; then
    sh "$MELDEKETTE" senden "Findling 10-04 Volllauf fertig" \
        "Beide Spuren sind durch, nach ${DAUER} h. Der OOM-Beweis ist erhoben, 00-FERTIG liegt im Laufverzeichnis. Naechster Schritt: Agent mit '${WECKWORT}' wecken." \
        default || true
fi

if [ "$lesungen" -eq 0 ]; then
    echo "96b-waechter: not one usable recording in $AUFNAHMEN" >&2
    echo "96b-waechter: the watchman watched nothing, so its verdict is about the observer" >&2
    echo "96b-waechter: and not about the run; check 96d-statusbeobachter and start over" >&2
    exit 14
fi

if [ "$urteil" != 'ende-erkannt ja' ]; then
    echo "96b-waechter: the round cap of $DECKEL was reached without the end of both tracks" >&2
    echo "96b-waechter: the figures up to here are secured, and the run is INCOMPLETE" >&2
    echo "96b-waechter: a run time without an end is not a run time and must not be reported as one" >&2
    exit 13
fi

echo "96B-WAECHTER-FERTIG"
