#!/bin/sh
# Measure the folder budget of the unified search filter (plan 32-03, D-32-06).
#
# The container ranks the whole index and knows nothing about the folder of
# the dialog, so PHP throws away what lies outside it. A narrow folder whose
# hits rank deep behind a thousand better hits outside is the case that decides
# how many rounds and how many candidates per round the folder mode needs
# (research assumption A2, pitfall 4). This script builds that case on a test
# instance, waits until the index carries it, and times the dialog route.
#
# The corpus, under one term that occurs nowhere else (ordnermessung32):
#   /Messung32/Aussen/       1000 short files, the term thirty times each,
#                            so they rank on top
#   /Messung32/Innen/Tief/   10 long files, the term once each, about one
#                            percent of the hits and ranked behind all of the
#                            above
#   /Messung32/Einzeln/      1 long file, the term once, about 0.1 percent
#
# The term is not part of any file name, so the title field adds nothing to
# the ranking and the order is the body score alone.
#
# Modes:
#   setup     create the corpus over WebDAV
#   wait      poll until the work stock of occ findling:index --status in the
#             container named by FINDLING_OCC_CONTAINER is empty (skipped when
#             the variable is unset), then until the dialog route without a
#             folder returns five real hits. That all 1011 files are in the
#             index is not observable through the dialog; the report checks it
#             once against the container directly.
#   measure   time every query of the plan, one warm up call discarded, then
#             REPETITIONS calls; raw seconds and the summary line go to the
#             output directory under the given label
#   cleanup   delete /Messung32 over WebDAV; emptying the trash bin is an occ
#             call (occ trashbin:cleanup <user>) and left to the operator
#
# Usage:
#   FINDLING_MEASURE_PASSWORD=... scripts/dev/measure_folder_filter.sh \
#       <setup|wait|measure|cleanup> [base-url] [user] [repetitions] [label]
#
# Defaults: base-url http://localhost:8090, user testuser, repetitions 20,
# label adhoc. The password (an app password is the cheap one to check) is read
# from the environment only and handed to curl on standard input, so it never
# appears on a command line, in a log of this script or in the raw data.
#
# The median is the rank value at ceil(0.5 * n) of the sorted series and the
# maximum is the largest value, both without interpolation, the rule of
# docs/measurements/2026-09-seitenbudget/README.md.

set -eu

MODE="${1:-}"
BASE="${2:-http://localhost:8090}"
NC_USER="${3:-testuser}"
REPETITIONS="${4:-20}"
LABEL="${5:-adhoc}"

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)
OUT_DIR="${FINDLING_MEASURE_OUT:-$REPO_ROOT/docs/measurements/2026-10-ordnerfilter/rohdaten}"

TERM_WORD="ordnermessung32"
ROOT="Messung32"
OUTER_FILES=1000
INNER_FILES=10

if [ -z "${FINDLING_MEASURE_PASSWORD:-}" ]; then
    echo "measure_folder_filter: set FINDLING_MEASURE_PASSWORD, the password is never an argument" >&2
    exit 1
fi

for tool in curl jq awk sort; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "measure_folder_filter: $tool is required" >&2
        exit 1
    fi
done

# curl with the credentials on standard input. Every call that sends a body
# reads it from a file, so standard input stays free for the config.
nc_curl() {
    printf 'user = "%s:%s"\n' "$NC_USER" "$FINDLING_MEASURE_PASSWORD" | curl -K - -s "$@"
}

dav() {
    printf '%s/remote.php/dav/files/%s/%s' "$BASE" "$NC_USER" "$1"
}

# A long body with the term exactly once, in the middle. The filler words are
# fixed and occur in no query of this script.
long_body() {
    awk -v term="$TERM_WORD" -v seed="$1" 'BEGIN {
        split("Ablage Bestand Eintrag Feldnotiz Kapitel Abschnitt Vermerk Hinweis Anlage Seite", w, " ")
        for (i = 0; i < 400; i++) {
            if (i == 200) { printf "%s ", term }
            printf "%s%s ", w[(i + seed) % 10 + 1], (i % 13 == 0 ? "\n" : "")
        }
        printf "\n"
    }'
}

short_body() {
    awk -v term="$TERM_WORD" -v n="$1" 'BEGIN {
        for (i = 0; i < 30; i++) { printf "%s ", term }
        printf "\nAussen %d\n", n
    }'
}

put_file() {
    code=$(nc_curl -o /dev/null -w '%{http_code}' -T "$1" "$(dav "$2")")
    case "$code" in
        201|204) ;;
        *) echo "measure_folder_filter: PUT $2 answered $code" >&2; exit 1 ;;
    esac
}

mkcol() {
    code=$(nc_curl -o /dev/null -w '%{http_code}' -X MKCOL "$(dav "$1")")
    case "$code" in
        201|405) ;;
        *) echo "measure_folder_filter: MKCOL $1 answered $code" >&2; exit 1 ;;
    esac
}

do_setup() {
    work=$(mktemp -d)
    trap 'rm -rf "$work"' EXIT
    for dir in "$ROOT" "$ROOT/Aussen" "$ROOT/Innen" "$ROOT/Innen/Tief" "$ROOT/Einzeln"; do
        mkcol "$dir"
    done
    i=1
    while [ "$i" -le "$OUTER_FILES" ]; do
        short_body "$i" > "$work/body.txt"
        put_file "$work/body.txt" "$ROOT/Aussen/aussen-$(printf '%04d' "$i").txt"
        i=$((i + 1))
    done
    i=1
    while [ "$i" -le "$INNER_FILES" ]; do
        long_body "$i" > "$work/body.txt"
        put_file "$work/body.txt" "$ROOT/Innen/Tief/innen-$(printf '%02d' "$i").txt"
        i=$((i + 1))
    done
    long_body 0 > "$work/body.txt"
    put_file "$work/body.txt" "$ROOT/Einzeln/einzeln-01.txt"
    echo "measure_folder_filter: corpus written, $OUTER_FILES + $INNER_FILES + 1 files under /$ROOT"
}

# One dialog call; prints "seconds hits paginated". A hit is an entry with a
# file id above zero, so the door to the result page and the canary are not
# counted.
dialog_call() {
    out=$(mktemp)
    seconds=$(nc_curl -H 'OCS-APIRequest: true' -o "$out" -w '%{time_total}' \
        "$BASE/ocs/v2.php/search/providers/findling/search?format=json&term=$TERM_WORD&limit=$1$2")
    # The door entry carries its attributes as an empty JSON array, not as an
    # object, so the file id is read only off an object.
    hits=$(jq '[.ocs.data.entries[]
        | select(((.attributes | if type == "object" then .fileId else null end) // "0") | tonumber > 0)]
        | length' "$out") || { rm -f "$out"; return 1; }
    paginated=$(jq '.ocs.data.isPaginated' "$out") || { rm -f "$out"; return 1; }
    rm -f "$out"
    printf '%s %s %s\n' "$seconds" "$hits" "$paginated"
}

do_wait() {
    if [ -n "${FINDLING_OCC_CONTAINER:-}" ]; then
        while :; do
            stock=$(docker exec -u www-data "$FINDLING_OCC_CONTAINER" php occ findling:index --status \
                | awk '/scheduled|handed to the worker/ { sum += $NF } END { print sum + 0 }')
            [ "$stock" -eq 0 ] && break
            echo "measure_folder_filter: work stock $stock, waiting"
            sleep 10
        done
    fi
    while :; do
        unfiltered=$(dialog_call 5 "" | awk '{ print $2 + 0 }')
        echo "measure_folder_filter: unfiltered hits at limit 5: ${unfiltered:-none}"
        if [ "${unfiltered:-0}" -ge 5 ]; then
            break
        fi
        sleep 10
    done
}

# Rank value at ceil(p * n), no interpolation.
rank_value() {
    sort -n "$1" | awk -v p="$2" '{ v[NR] = $1 } END { r = int(p * NR); if (r < p * NR) r++; if (r < 1) r = 1; print v[r] }'
}

do_measure() {
    mkdir -p "$OUT_DIR"
    summary="$OUT_DIR/$LABEL.tsv"
    printf 'variant\tquery\tlimit\thits\tisPaginated\tmedian_s\tmax_s\tn\n' > "$summary"
    for limit in 5 10; do
        for query in ohne innen einzeln; do
            case "$query" in
                ohne) extra="" ;;
                innen) extra="&folder=%2F$ROOT%2FInnen" ;;
                einzeln) extra="&folder=%2F$ROOT%2FEinzeln" ;;
            esac
            raw="$OUT_DIR/$LABEL-$query-limit$limit.txt"
            : > "$raw"
            seen=$(mktemp)
            dialog_call "$limit" "$extra" > /dev/null
            n=0
            while [ "$n" -lt "$REPETITIONS" ]; do
                line=$(dialog_call "$limit" "$extra") || exit 1
                # shellcheck disable=SC2086
                set -- $line
                if [ "$#" -ne 3 ]; then
                    echo "measure_folder_filter: unreadable answer for $query at limit $limit" >&2
                    exit 1
                fi
                printf '%s\n' "$1" >> "$raw"
                printf '%s %s\n' "$2" "$3" >> "$seen"
                n=$((n + 1))
            done
            # Every distinct value over the series, joined with a slash, so a
            # hit count that moves between calls shows up as 4/5 and not as
            # the last value alone.
            hits_seen=$(awk '{ print $1 }' "$seen" | sort -n -u | paste -sd/ -)
            paginated_seen=$(awk '{ print $2 }' "$seen" | sort -u | paste -sd/ -)
            rm -f "$seen"
            median=$(rank_value "$raw" 0.5)
            maximum=$(rank_value "$raw" 1)
            printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
                "$LABEL" "$query" "$limit" "$hits_seen" "$paginated_seen" "$median" "$maximum" "$n" >> "$summary"
        done
    done
    cat "$summary"
}

do_cleanup() {
    code=$(nc_curl -o /dev/null -w '%{http_code}' -X DELETE "$(dav "$ROOT")")
    echo "measure_folder_filter: DELETE /$ROOT answered $code"
}

case "$MODE" in
    setup) do_setup ;;
    wait) do_wait ;;
    measure) do_measure ;;
    cleanup) do_cleanup ;;
    *)
        echo "usage: FINDLING_MEASURE_PASSWORD=... $0 <setup|wait|measure|cleanup> [base-url] [user] [repetitions] [label]" >&2
        exit 2
        ;;
esac
