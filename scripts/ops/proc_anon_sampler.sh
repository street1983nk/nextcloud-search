#!/bin/sh
# Sample the anonymous memory of every process inside one container.
#
# rss_sampler.sh answers how much the container holds; this one answers who in
# the container holds it. The cgroup figure cannot tell the server process from
# the extraction child from a tesseract grandchild, and the OCR block of the
# load test is exactly the case where that split is the question. So this
# script asks the kernel inside the container, process by process, for three
# fields of /proc/<pid>/status and nothing else:
#
#   Name     the short process name the kernel keeps, at most 15 characters
#   RssAnon  the anonymous resident memory, the heap in the sense of rss_sampler
#   VmHWM    the highest resident memory the process ever had
#
# Nothing else is read, on purpose. The argument list of a process can carry
# file paths of the instance being indexed, and its environment can carry
# credentials; neither file is opened, and a test keeps the name of the first
# one out of this text (T-02-14).
#
# What comes out: a CSV with epoch, pid, name, rssanon_kb and vmhwm_kb, one row
# per process per sample, and one closing line with the number of samples and
# the highest RssAnon seen per process name. A comma inside a process name is
# written as an underscore so the CSV stays a CSV. Every line carries a fixed
# prefix:
#
#     grep '^findling-anon ' run.log | cut -d' ' -f2- > anon.csv
#
# Usage: scripts/ops/proc_anon_sampler.sh <container-name-or-id> [interval-seconds] [output-file]
#
# Stop it with Ctrl-C or with a TERM signal; the closing line is written on the
# way out. It refuses to work rather than write zeroes: a sample that finds no
# process at all is not a sample.

set -eu

PREFIX='findling-anon'
DEFAULT_INTERVAL=5

NAME="${1:-}"
INTERVAL="${2:-$DEFAULT_INTERVAL}"
OUTPUT="${3:-}"

if [ -z "$NAME" ]; then
    echo "proc_anon_sampler: a container name or id is required" >&2
    echo "usage: proc_anon_sampler.sh <container-name-or-id> [interval-seconds] [output-file]" >&2
    echo "AppAPI builds the ExApp container name itself, so ask docker instead of guessing it:" >&2
    echo "  docker ps --filter name=findling_backend --format '{{.Names}}'" >&2
    exit 2
fi

case "$INTERVAL" in
    '' | *[!0-9]*)
        echo "proc_anon_sampler: the interval has to be a whole number of seconds, got '$INTERVAL'" >&2
        exit 2
        ;;
esac
if [ "$INTERVAL" -lt 1 ]; then
    echo "proc_anon_sampler: the interval has to be at least one second, got '$INTERVAL'" >&2
    exit 2
fi

for tool in docker awk date sleep sort; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "proc_anon_sampler: $tool is required and not on the path" >&2
        exit 1
    fi
done

if ! CONTAINER_ID=$(docker inspect -f '{{.Id}}' "$NAME" 2>/dev/null); then
    echo "proc_anon_sampler: docker does not know a container called '$NAME'" >&2
    echo "the name of the ExApp container comes from buildExAppContainerName, so look it up:" >&2
    echo "  docker ps --filter name=findling_backend --format '{{.Names}}'" >&2
    exit 1
fi

emit() {
    if [ -z "$OUTPUT" ]; then
        printf '%s %s\n' "$PREFIX" "$1"
    else
        printf '%s %s\n' "$PREFIX" "$1" >>"$OUTPUT"
    fi
}

# Inside the container only grep runs, which every Debian based image carries,
# over the status files of every process. A process that ends between the
# expansion of the glob and the read is a vanished file and not an error, hence
# the silenced stderr and the true. The parsing happens out here, so the image
# needs no awk. Kernel threads carry no RssAnon line and drop out on their own.
READER='grep -H -E "^(Name|RssAnon|VmHWM):" /proc/[0-9]*/status 2>/dev/null || true'

sample() {
    raw=$(docker exec "$CONTAINER_ID" sh -c "$READER") || return 1
    printf '%s\n' "$raw" | awk -F: '
        NF >= 3 {
            split($1, parts, "/")
            pid = parts[3]
            field = $2
            value = $3
            for (i = 4; i <= NF; i++) value = value ":" $i
            sub(/^[ \t]+/, "", value)
            if (field == "Name") { gsub(/,/, "_", value); name[pid] = value }
            else { sub(/[ \t]*kB$/, "", value); if (field == "RssAnon") anon[pid] = value; else hwm[pid] = value }
        }
        END { for (pid in anon) printf "%s,%s,%d,%d\n", pid, name[pid], anon[pid], hwm[pid] }
    ' | sort -t, -k1,1n
}

LINES=0
SAMPLES=0
MAXES=''

finish() {
    trap - INT TERM
    reason="$1"
    tops=$(printf '%s\n' "$MAXES" | awk -F, 'NF == 2 { printf "%s%s=%s", (seen++ ? " " : ""), $1, $2 }')
    emit "summary samples=$SAMPLES rows=$LINES max_rssanon_kb=[$tops] reason=$reason"
    if [ "$LINES" -eq 0 ]; then
        echo "proc_anon_sampler: not one sample was written, so there is nothing to report" >&2
        exit 1
    fi
    exit 0
}

trap 'finish signal' INT TERM

echo "proc_anon_sampler: container=$NAME interval=${INTERVAL}s" >&2
emit "epoch,pid,name,rssanon_kb,vmhwm_kb"

while :; do
    stamp=$(date +%s)
    if ! rows=$(sample); then
        finish 'container gone'
    fi
    if [ -z "$rows" ]; then
        finish 'no process readable'
    fi
    SAMPLES=$((SAMPLES + 1))
    # Line by line and not word by word: a process name may carry a space.
    while IFS= read -r row; do
        emit "$stamp,$row"
        LINES=$((LINES + 1))
    done <<EOF
$rows
EOF
    MAXES=$(printf '%s\n%s\n' "$MAXES" "$rows" | awk -F, '
        NF == 2 { name = $1; value = $2 + 0 }
        NF == 4 { name = $2; value = $3 + 0 }
        NF == 2 || NF == 4 { if (!(name in top) || value > top[name]) top[name] = value }
        END { for (name in top) printf "%s,%d\n", name, top[name] }
    ' | sort)
    sleep "$INTERVAL"
done
