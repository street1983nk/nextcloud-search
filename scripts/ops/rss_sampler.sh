#!/bin/sh
# Sample the memory of one container so the number survives a recalculation.
#
# Why anon and not peak, in four sentences, and these are the same four that go
# into docs/performance.md: anon is the amount of memory in anonymous mappings,
# which is exactly the heap that INDEX_WORKERS=1, the Tantivy writer heap and
# tesseract produce. memory.current and memory.peak add the page cache to that,
# and the Tantivy index is an mmap on disk, so every index block that is read
# lands in the file cache of the very same cgroup. On a 20 GB corpus that cache
# is the largest single item in the figure and it is completely reclaimable, so a
# store claim taken from memory.peak would describe the app as worse than it is.
# Both are recorded anyway, because the first reader who asks the docker client
# for the memory of the container gets a number built on memory.current and has
# to find that difference explained rather than hidden. That client is also the
# reason this script reads the cgroup files itself: the two words it would take
# to ask do not appear anywhere below, and a test keeps them out.
#
# What comes out: a CSV with timestamp, anon, file, slab, current and peak per
# sample, and one closing line with the highest anon seen, the final memory.peak,
# the contents of memory.events and the OOMKilled flag of the container. Those
# four together are the OOM proof; a text search for "Killed" in a log is not,
# because it does not find the case where a child process of the cgroup was the
# one that was killed.
#
# Every line carries a fixed prefix, as the measuring steps in
# .github/workflows/resilience.yml do, so that the samples can be filtered out of
# a log that also carries everything else:
#
#     grep '^findling-rss ' run.log | cut -d' ' -f2- > rss.csv
#
# Usage: scripts/ops/rss_sampler.sh <container-name-or-id> [interval-seconds] [output-file]
#
# Stop it with Ctrl-C or with a TERM signal; the closing line is written on the
# way out. It refuses to work rather than write zeroes: a row of zeroes in a
# report looks like a measurement, and that is worse than a missing file.

set -eu

PREFIX='findling-rss'
DEFAULT_INTERVAL=5

NAME="${1:-}"
INTERVAL="${2:-$DEFAULT_INTERVAL}"
OUTPUT="${3:-}"

if [ -z "$NAME" ]; then
    echo "rss_sampler: a container name or id is required" >&2
    echo "usage: rss_sampler.sh <container-name-or-id> [interval-seconds] [output-file]" >&2
    echo "AppAPI builds the ExApp container name itself, so ask docker instead of guessing it:" >&2
    echo "  docker ps --filter name=findling_backend --format '{{.Names}}'" >&2
    exit 2
fi

case "$INTERVAL" in
    '' | *[!0-9]*)
        echo "rss_sampler: the interval has to be a whole number of seconds, got '$INTERVAL'" >&2
        exit 2
        ;;
esac
if [ "$INTERVAL" -lt 1 ]; then
    echo "rss_sampler: the interval has to be at least one second, got '$INTERVAL'" >&2
    exit 2
fi

for tool in docker awk date sleep; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "rss_sampler: $tool is required and not on the path" >&2
        exit 1
    fi
done

# The id and not the name is what the cgroup path is built from, and asking
# docker for it is also the existence check.
if ! CONTAINER_ID=$(docker inspect -f '{{.Id}}' "$NAME" 2>/dev/null); then
    echo "rss_sampler: docker does not know a container called '$NAME'" >&2
    echo "the name of the ExApp container comes from buildExAppContainerName, so look it up:" >&2
    echo "  docker ps --filter name=findling_backend --format '{{.Names}}'" >&2
    exit 1
fi

# Where the cgroup of a container sits depends on the cgroup driver of the
# daemon, and both forms exist in the field. With the systemd driver, which is
# the default on Ubuntu 24.04 and therefore on the load test box, it is
# system.slice/docker-<id>.scope. With the cgroupfs driver it is
# /sys/fs/cgroup/docker/<id>. Both are tried, the root is overridable for a test
# that runs inside a container, and if neither of them carries a memory.stat the
# script gives up. It does not fall back to zeroes: see the last paragraph of the
# header.
CGROUP_ROOT="${FINDLING_CGROUP_ROOT:-/sys/fs/cgroup}"
CGROUP=''
for candidate in \
    "$CGROUP_ROOT/system.slice/docker-$CONTAINER_ID.scope" \
    "$CGROUP_ROOT/docker/$CONTAINER_ID"; do
    if [ -r "$candidate/memory.stat" ]; then
        CGROUP="$candidate"
        break
    fi
done
if [ -z "$CGROUP" ]; then
    echo "rss_sampler: no readable memory.stat for container $NAME" >&2
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

# memory.peak arrived in kernel 5.19 and memory.events can be unreadable in a
# nested setup. Neither is the number the store claim is made from, so a missing
# one is reported as na and does not end the run; a missing anon does, because
# that one is read out of memory.stat whose presence was checked above.
read_number() {
    if [ -r "$1" ]; then
        awk 'NR == 1 { printf "%s", $1 }' "$1"
    else
        printf 'na'
    fi
}

sample() {
    stamp=$(date +%s)
    current=$(read_number "$CGROUP/memory.current")
    peak=$(read_number "$CGROUP/memory.peak")
    awk -v stamp="$stamp" -v current="$current" -v peak="$peak" '
        $1 == "anon" { anon = $2 }
        $1 == "file" { file = $2 }
        $1 == "slab" { slab = $2 }
        END { printf "%d,%d,%d,%d,%s,%s\n", stamp, anon, file, slab, current, peak }
    ' "$CGROUP/memory.stat"
}

LINES=0
MAX_ANON=0

finish() {
    trap - INT TERM
    events=$(awk '{ printf "%s%s=%s", (NR > 1 ? " " : ""), $1, $2 }' "$CGROUP/memory.events" 2>/dev/null || printf 'unreadable')
    oom_killed=$(docker inspect -f '{{.State.OOMKilled}}' "$NAME" 2>/dev/null || printf 'unknown')
    final_peak=$(read_number "$CGROUP/memory.peak")
    emit "summary samples=$LINES max_anon=$MAX_ANON peak=$final_peak events=[$events] oom_killed=$oom_killed"
    if [ "$LINES" -eq 0 ]; then
        echo "rss_sampler: not one sample was written, so there is nothing to report" >&2
        exit 1
    fi
    exit 0
}

trap finish INT TERM

echo "rss_sampler: container=$NAME cgroup=$CGROUP interval=${INTERVAL}s" >&2
emit "timestamp,anon,file,slab,current,peak"

while :; do
    row=$(sample)
    emit "$row"
    LINES=$((LINES + 1))
    anon=${row#*,}
    anon=${anon%%,*}
    if [ "$anon" -gt "$MAX_ANON" ]; then
        MAX_ANON="$anon"
    fi
    sleep "$INTERVAL"
done
