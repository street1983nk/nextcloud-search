#!/bin/sh
# The full run, triggered and then left alone: 50.000 files, full text, OCR and
# embedding, one worker, hard limit 2 GiB, some nineteen hours. The way is the one
# of 42-semantiklauf.sh of the semantic run, with the same two reasons it had.
#
#   1. The status observer records every 120 s and not every 300 s. The boundary
#      between the first and the second track comes out of its row, and a phase
#      duration that is accurate to five minutes is not a measurement, it is an
#      estimate with a decimal place.
#   2. Next to indexed stands embedded. The second figure is the second track,
#      and without it its duration cannot be read off anything.
#
# **And one thing this script does that no predecessor did: the dry run of the
# reader stands in the raw file.** Pitfall 8 of the research is the most
# expensive mistake of both predecessors: 42c-lesen.py read indexed and embedded
# on the top level of the recording, where the indexed of the PHP half stands and
# stays 0 by design and where embedded does not stand at all. The watchman logged
# zeroes for a whole night while the container held 47.000 vectors, so the search
# load sample of the trailing run never ran and the end of both tracks would have
# been noticed nine hours late. The lesson of the research is to drive the reader
# once against a known number before the run is triggered. This script does that
# and PROTOCOLS the answer, because a check whose result is not written down is a
# memory and not a check. The same three figures are also the starting point of
# the run, which is the second reason they are worth a line: if indexed is
# already above zero at the trigger, the measured run time is a lower bound, and
# the report has to say so instead of assuming a zero start.
#
# The trigger is deliberately app:enable followed by findling:index without
# arguments. The queue was filled in step 4 by 93-nullstand.sh with
# `findling:index --restart -n`, and -n is not decoration there: without it the
# command asks back, gets no answer in a script, reports "Nothing was changed",
# and the caller believes the run is running (finding of the dress rehearsal).
# This step does not restart the queue, it switches the app on and times from
# there.
#
# The counter check after the trigger waits 360 seconds, and the number is
# measured against the SLOWEST clock involved, not against the one that came to
# mind: the poller backoff runs up to 300 s, and AIO calls cron.php only every
# five minutes, where the first job of the app queues nothing yet. Pitfall 11 is
# the same waiting period got wrong: the counter check of the semantic run
# declared the run dead 52 seconds too early. The verdict of this script stays as
# it is and the addendum is written UNDERNEATH it, because a raw file whose
# verdict was overwritten no longer proves what was measured.
#
# The exit code: 14 means there was no work stock after the waiting period, so
# the run is not running. The sampler and the observer are deliberately left
# alive in that case, because their rows are the state before, and the watchman
# is NOT started, because 340 rounds against a run that never started are a day
# and a half of nothing.
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
DATA_ROOT="${DATA_ROOT:-/mnt/findling}"
SAMPLER="${SAMPLER:-$REPO/scripts/ops/rss_sampler.sh}"
BEOBACHTER="${BEOBACHTER:-$SKRIPTE/96d-statusbeobachter.py}"
LESER="${LESER:-$SKRIPTE/96c-lesen.py}"
WAECHTER="${WAECHTER:-$SKRIPTE/96b-waechter.sh}"
MELDEKETTE="${MELDEKETTE:-$SKRIPTE/96e-ntfy-watch.sh}"
# The password file of the administrator on the box. The value is read into an
# environment variable and never handed to a command line.
PWFILE="${PWFILE:-$HOME/work/.pw/admin}"
AUFNAHMEN="${AUFNAHMEN:-$OUT/96-statusseite.jsonl}"
CSV="${CSV:-$OUT/96-volllauf.csv}"
# The two intervals, and the reason for each: five seconds for the memory row,
# because the peak has to be readable to the second, and 120 seconds for the
# status row, because the boundary between the tracks comes out of it.
SAMPLER_INTERVALL="${SAMPLER_INTERVALL:-5}"
STATUS_INTERVALL="${STATUS_INTERVALL:-120}"
# The waiting period of the counter check, measured against the slowest clock:
# poller backoff up to 300 s plus two rounds of the five minute system cron.
FRIST="${FRIST:-360}"

mkdir -p "$OUT"
ZIEL="$OUT/96-volllauf-start.txt"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

FINDLING_ADMIN_PASSWORD=$(sudo cat "$PWFILE")
export FINDLING_ADMIN_PASSWORD

occ() { sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"; }

{
    date -u +'volllauf-vorbereitung %Y-%m-%dT%H:%M:%SZ'
    printf 'basis: %s\n' "$BASE"
    printf 'aufnahmen: %s\n' "$AUFNAHMEN"
    printf 'frist der gegenprobe: %s s\n' "$FRIST"

    echo "=== The state before the app is switched on, reading 8 of the list ==="
    sudo docker inspect "$CONTAINER" \
        --format 'Image={{.Config.Image}} Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}}'
    CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
    printf 'cgroup: %s\n' "$SCOPE"
    sudo cat "$SCOPE/memory.events"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s memory.max=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" \
        "$(sudo cat "$SCOPE/memory.peak")" \
        "$(sudo cat "$SCOPE/memory.max")"
    df -h "$DATA_ROOT" | tail -1
    occ app:list 2>&1 | grep -i findling || true

    echo "=== The observers, started BEFORE the app is switched on ==="
    # Both fully redirected and detached: a background process that keeps the
    # standard output of this block open would keep the tee of this script from
    # ever ending.
    setsid nohup sudo sh "$SAMPLER" "$CONTAINER" "$SAMPLER_INTERVALL" "$CSV" \
        >"$OUT/96-sampler.log" 2>&1 </dev/null &
    setsid nohup sudo -E python3 "$BEOBACHTER" "$AUFNAHMEN" "$STATUS_INTERVALL" "$PWFILE" "$BASE" \
        >"$OUT/96-statusbeobachter.log" 2>&1 </dev/null &
    # Long enough for the sampler to have written its header and the observer to
    # have logged in and taken its first reading.
    sleep 20
    wc -l "$CSV" "$AUFNAHMEN" || true
    tail -3 "$OUT/96-statusbeobachter.log" || true

    echo "=== The dry run of the reader, against a real recording (pitfall 8) ==="
    lesung=$(tail -1 "$AUFNAHMEN" 2>/dev/null | python3 "$LESER" 2>/dev/null || true)
    [ -n "$lesung" ] || lesung='unklar unklar unklar'
    printf 'leser: %s\n' "$LESER"
    printf 'letzte-aufnahme-gelesen: %s\n' "$lesung"
    printf '%s\n' "$lesung" >"$WORK/startpunkt"
    echo "-- the three words are vorrat, indexed and embedded, in that order --"
    echo "-- unklar three times here means the observer has no session yet: fix that"
    echo "   BEFORE the trigger, because the watchman reads this very row --"
    # The same figures are the starting point of the run. Written down as such,
    # because a run time counted from a start that was not a zero start is a lower
    # bound and has to be reported as one.
    startindexed=$(printf '%s\n' "$lesung" | awk '{print $2}')
    echo "startpunkt-indexed $startindexed"
    case "$startindexed" in
    '0' | unklar) echo "startpunkt-bewertung nullstart oder unbekannt" ;;
    *) echo "startpunkt-bewertung schon indexierte Dateien vorhanden, die Laufzeit ist eine Untergrenze" ;;
    esac

    echo "=== The trigger: only now is the app switched on ==="
    date -u +'volllauf-start %Y-%m-%dT%H:%M:%SZ'
    occ app:enable findling 2>&1 || true
    occ findling:index 2>&1 || true

    echo "=== The counter check after $FRIST seconds: is something really working ==="
    sleep "$FRIST"
    date -u +'gegenprobe %Y-%m-%dT%H:%M:%SZ'
    occ findling:index >"$WORK/gegenprobe.txt" 2>&1 || true
    cat "$WORK/gegenprobe.txt"

    echo "-- DI-05-36, the second half of the proof: COUNTED passes of the poller --"
    CSTART=$(sudo docker inspect "$CONTAINER" --format '{{.State.StartedAt}}')
    sudo docker logs --since "$CSTART" "$CONTAINER" 2>&1 | grep -c 'pass finished' || true
    sudo docker logs --tail 8 "$CONTAINER" 2>&1 || true

    echo "=== The verdict, out of the row of the observer ==="
    lesung=$(tail -1 "$AUFNAHMEN" 2>/dev/null | python3 "$LESER" 2>/dev/null || true)
    [ -n "$lesung" ] || lesung='unklar unklar unklar'
    printf 'gegenprobe-gelesen: %s\n' "$lesung"
    vorrat=$(printf '%s\n' "$lesung" | awk '{print $1}')
    case "$vorrat" in
    '' | '0' | unklar) echo 'arbeitsvorrat-da nein' >"$WORK/urteil" ;;
    *) echo 'arbeitsvorrat-da ja' >"$WORK/urteil" ;;
    esac
    cat "$WORK/urteil"

    echo "-- Nachtrag, unter dem Urteil und nicht an seiner Stelle --"
    echo "   Ein Vorrat von 0 nach $FRIST s ist Annahme A2 der Recherche: der Befehl"
    echo "   findling:index --restart stand am 05.09. eingestellt, die Notiz war zwei"
    echo "   Tage alt und die Box war seither aus. Dann wird findling:index --restart -n"
    echo "   erneut abgesetzt und die Frist laeuft von vorn. Erst wenn der Vorrat nach"
    echo "   einer zweiten Frist auf null bleibt, ist das ein Befund ueber die Box."

    date -u +'volllauf-vorbereitung-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

# Everything below the pipeline, because the return code of a pipeline belongs to
# tee: an exit inside the block above would only leave the subshell, and the
# refusal would be a line in the raw file that nobody reads.
urteil=$(cat "$WORK/urteil" 2>/dev/null || echo 'arbeitsvorrat-da nein')

if [ "$urteil" != 'arbeitsvorrat-da ja' ]; then
    echo "96-volllauf: no work stock after $FRIST seconds, so the run is not running" >&2
    echo "96-volllauf: the watchman was NOT started, because 340 rounds against a run" >&2
    echo "96-volllauf: that never began are a day and a half of nothing" >&2
    echo "96-volllauf: sampler and observer are left alive on purpose, their rows are" >&2
    echo "96-volllauf: the state before; issue findling:index --restart -n and repeat" >&2
    exit 14
fi

# The detached half: the watchman for the nineteen hours, and the notification
# chain beside it. Both are started only now, after the counter check, and both
# are fully redirected so that neither holds a pipe of this script.
setsid nohup sh "$WAECHTER" >"$OUT/96b-waechter.log" 2>&1 </dev/null &
echo "waechter gestartet, protokoll $OUT/96b-waechter.log"
setsid nohup sh "$MELDEKETTE" warten >"$OUT/96e-ntfy-watch.log" 2>&1 </dev/null &
echo "meldekette im wartemodus gestartet, protokoll $OUT/96e-ntfy-watch.log"
sh "$MELDEKETTE" start || true

echo "96-VOLLLAUF-GESTARTET"
