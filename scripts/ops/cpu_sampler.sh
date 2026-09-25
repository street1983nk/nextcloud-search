#!/bin/sh
# Sample the CPU time of one container so the core usage of a run is a number.
#
# The sibling of rss_sampler.sh, built on the same frame and for the same kind
# of reader: somebody who wants to know how many cores a block of the load test
# really kept busy, and who would otherwise read it off a top screenshot. The
# figure comes from the cgroup of the container, usage_usec in cpu.stat, which
# counts every process of the cgroup including the tesseract grandchildren of a
# long lived extraction child. Asking the docker client instead would hand back
# a percentage averaged over an interval nobody chose; the cgroup counter is
# cumulative and exact, and the two words that would ask the client do not
# appear below, and a test keeps them out.
#
# Next to it goes the cpu line of /proc/stat of the host, total and idle
# jiffies, so that a report can say what the rest of the machine did while the
# container worked. That line is the whole host and not the container, which is
# the point: a busy host next to an idle container is a finding of its own.
#
# What comes out: a CSV with epoch, usage_usec, box_total_jiffies,
# box_idle_jiffies and uptime_usec per sample. The last column is the clock the
# core usage is computed with, read out of /proc/uptime, because epoch seconds
# are too coarse for an interval of a few seconds. One closing line carries the
# number of samples, the mean and the highest core usage (delta usage_usec over
# delta wall time in microseconds, so 1.000 is one core kept fully busy) and the
# reason the run ended: "signal" for Ctrl-C or TERM, "cgroup gone" when the
# container disappeared under the sampler, which is what a container rebuild
# does. Every line carries a fixed prefix, so the samples can be filtered out of
# a log that also carries everything else:
#
#     grep '^findling-cpu ' run.log | cut -d' ' -f2- > cpu.csv
#
# Usage: scripts/ops/cpu_sampler.sh <container-name-or-id> [interval-seconds] [output-file]
#
# It refuses to work rather than write zeroes: a row of zeroes in a report looks
# like a measurement, and that is worse than a missing file. And it does not die
# quietly when the cgroup goes away halfway: every read is preceded by a check,
# and a failed check ends the run through the closing line.

set -eu

PREFIX='findling-cpu'
DEFAULT_INTERVAL=5

NAME="${1:-}"
INTERVAL="${2:-$DEFAULT_INTERVAL}"
OUTPUT="${3:-}"

if [ -z "$NAME" ]; then
    echo "cpu_sampler: a container name or id is required" >&2
    echo "usage: cpu_sampler.sh <container-name-or-id> [interval-seconds] [output-file]" >&2
    echo "AppAPI builds the ExApp container name itself, so ask docker instead of guessing it:" >&2
    echo "  docker ps --filter name=findling_backend --format '{{.Names}}'" >&2
    exit 2
fi

case "$INTERVAL" in
    '' | *[!0-9]*)
        echo "cpu_sampler: the interval has to be a whole number of seconds, got '$INTERVAL'" >&2
        exit 2
        ;;
esac
if [ "$INTERVAL" -lt 1 ]; then
    echo "cpu_sampler: the interval has to be at least one second, got '$INTERVAL'" >&2
    exit 2
fi

for tool in docker awk date sleep; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "cpu_sampler: $tool is required and not on the path" >&2
        exit 1
    fi
done

# The id and not the name is what the cgroup path is built from, and asking
# docker for it is also the existence check.
if ! CONTAINER_ID=$(docker inspect -f '{{.Id}}' "$NAME" 2>/dev/null); then
    echo "cpu_sampler: docker does not know a container called '$NAME'" >&2
    echo "the name of the ExApp container comes from buildExAppContainerName, so look it up:" >&2
    echo "  docker ps --filter name=findling_backend --format '{{.Names}}'" >&2
    exit 1
fi

# Both cgroup driver layouts, as in rss_sampler.sh: systemd puts the container
# under system.slice/docker-<id>.scope, cgroupfs under docker/<id>. The root is
# overridable for a test. Without a readable cpu.stat there is nothing to
# measure, and the script says so instead of writing zeroes.
CGROUP_ROOT="${FINDLING_CGROUP_ROOT:-/sys/fs/cgroup}"
CGROUP=''
for candidate in \
    "$CGROUP_ROOT/system.slice/docker-$CONTAINER_ID.scope" \
    "$CGROUP_ROOT/docker/$CONTAINER_ID"; do
    if [ -r "$candidate/cpu.stat" ]; then
        CGROUP="$candidate"
        break
    fi
done
if [ -z "$CGROUP" ]; then
    echo "cpu_sampler: no readable cpu.stat for container $NAME" >&2
    echo "tried $CGROUP_ROOT/system.slice/docker-<id>.scope and $CGROUP_ROOT/docker/<id>" >&2
    echo "without it there is nothing to measure, and a line of zeroes would look like a measurement" >&2
    exit 1
fi

emit() {
    if [ -z "$OUTPUT" ]; then
        printf '%s %s\n' "$PREFIX" "$1"
    else
        printf '%s %s\n' "$PREFIX" "$1" >>"$OUTPUT"
    fi
}

# One row, or a non zero return when any of the three sources could not be
# read. A cpu.stat without usage_usec counts as unreadable: an empty field
# would otherwise become a zero in the arithmetic below.
sample() {
    stamp=$(date +%s)
    usage=$(awk '$1 == "usage_usec" { found = $2 } END { if (found == "") exit 1; printf "%s", found }' "$CGROUP/cpu.stat") || return 1
    box=$(awk '$1 == "cpu" { printf "%d,%d", $2 + $3 + $4 + $5 + $6 + $7 + $8 + $9, $5; found = 1 } END { if (!found) exit 1 }' /proc/stat) || return 1
    uptime=$(awk 'NR == 1 { printf "%.0f", $1 * 1000000 }' /proc/uptime) || return 1
    printf '%s,%s,%s,%s\n' "$stamp" "$usage" "$box" "$uptime"
}

# Core usage of one interval, three decimals, na when no time has passed.
cores() {
    awk -v used="$1" -v wall="$2" 'BEGIN { if (wall > 0) printf "%.3f", used / wall; else printf "na" }'
}

LINES=0
FIRST_USAGE=''
FIRST_UPTIME=''
LAST_USAGE=''
LAST_UPTIME=''
MAX_CORES='na'

finish() {
    trap - INT TERM
    reason="$1"
    mean='na'
    if [ "$LINES" -gt 1 ]; then
        mean=$(cores $((LAST_USAGE - FIRST_USAGE)) $((LAST_UPTIME - FIRST_UPTIME)))
    fi
    emit "summary samples=$LINES mean_cores=$mean max_cores=$MAX_CORES reason=$reason"
    if [ "$LINES" -eq 0 ]; then
        echo "cpu_sampler: not one sample was written, so there is nothing to report" >&2
        exit 1
    fi
    exit 0
}

trap 'finish signal' INT TERM

echo "cpu_sampler: container=$NAME cgroup=$CGROUP interval=${INTERVAL}s" >&2
emit "epoch,usage_usec,box_total_jiffies,box_idle_jiffies,uptime_usec"

while :; do
    # A container rebuild removes the cgroup. Under set -eu the next read would
    # end the script without a word, so the check comes first and the way out
    # is the closing line.
    if [ ! -r "$CGROUP/cpu.stat" ]; then
        finish 'cgroup gone'
    fi
    if ! row=$(sample); then
        finish 'cgroup gone'
    fi
    emit "$row"
    LINES=$((LINES + 1))
    usage=$(printf '%s' "$row" | awk -F, '{ printf "%s", $2 }')
    uptime=$(printf '%s' "$row" | awk -F, '{ printf "%s", $5 }')
    if [ -z "$FIRST_USAGE" ]; then
        FIRST_USAGE="$usage"
        FIRST_UPTIME="$uptime"
    else
        current=$(cores $((usage - LAST_USAGE)) $((uptime - LAST_UPTIME)))
        MAX_CORES=$(awk -v top="$MAX_CORES" -v now="$current" 'BEGIN {
            if (now == "na") { printf "%s", top }
            else if (top == "na" || now + 0 > top + 0) { printf "%s", now }
            else { printf "%s", top }
        }')
    fi
    LAST_USAGE="$usage"
    LAST_UPTIME="$uptime"
    sleep "$INTERVAL"
done
