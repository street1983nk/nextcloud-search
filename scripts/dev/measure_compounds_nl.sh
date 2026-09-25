#!/bin/sh
# Measure recipe B case by case against the real Dutch Debian word list, and the
# resident memory of the second automaton.
#
# Same shape as scripts/dev/measure_compounds.sh, and for the same reason:
# /usr/share/dict/dutch comes from the Debian package wdutch and does not exist
# on a developer machine. The container is the base image the ExApp ships on,
# with the engine pin of backend/pyproject.toml, so the tokens it prints are the
# tokens the product produces.
#
# Written by the probe into the output directory:
#   tokens-rezept-b.tsv   word, chars, in_dutch, entry_in_list,
#                         tokens_without_splitter, tokens
#   fixture-subset.txt    the entries the Python fixture needs, from the real list
#   kennzahlen.txt        numbers, digests and the chain cases that differ
#   ram.txt               three runs of the memory mode, lauf=1..3
#
# Expected from the phase research of 2026-09-25, recipe B 4-14:
#   source_lines=413288  entries=316740  digest=ee7f3b8380c75283...
#   compounds_found_via_constituent=21 of 28
#   compounds_found_without_splitter=0 of 28
#   sentinels_whole=32 of 33
#   ram_nl_released_mb between 17.5 and 17.7 (amd64)
# A deviation is a finding, not a reason to edit a file by hand.
#
# The probe compares the tokens of the subset against the tokens of the full
# list for every word of both case lists and exits with 1 on the first
# difference, so a run that ends with 0 is the proof that the fixture is the
# list. With --against the same comparison is made for a list the caller names,
# which is how backend/tests/fixtures/constituents_nl.txt is checked.
#
# Usage: scripts/dev/measure_compounds_nl.sh [--against list] [output-directory]
# On Windows call it from Git Bash with MSYS_NO_PATHCONV=1, otherwise MSYS
# rewrites the container paths of the mounts.

set -eu

# The pins stand here as whole apt and pip arguments, not as bare version
# numbers, so that a grep for the pin finds the line that really installs it.
# wngerman is needed by the memory mode only, which holds the German list and
# the German automaton first, in the order of the running container.
IMAGE="python:3.13-slim-trixie"
WDUTCH="wdutch=1:2.20.19+1-3"
WNGERMAN="wngerman=20161207-15"
TANTIVY="tantivy==0.26.2"

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)

AGAINST=""
if [ "${1:-}" = "--against" ]; then
    if [ $# -lt 2 ]; then
        echo "measure_compounds_nl: --against needs the path of a list" >&2
        exit 2
    fi
    AGAINST=$(CDPATH='' cd -- "$(dirname -- "$2")" && pwd)/$(basename -- "$2")
    if [ ! -f "$AGAINST" ]; then
        echo "measure_compounds_nl: no list at $AGAINST" >&2
        exit 1
    fi
    shift 2
fi

CASES="$REPO_ROOT/backend/tests/fixtures/compound_cases_nl.txt"
CHAIN_CASES="$REPO_ROOT/backend/tests/fixtures/chain_cases_nl.txt"
PROBE="$SCRIPT_DIR/compound_probe_nl.py"
OUT_DIR="${1:-$REPO_ROOT/docs/measurements/2026-09-komposita-nl/rohdaten}"

if [ ! -d "$REPO_ROOT/backend/src/findling" ]; then
    echo "measure_compounds_nl: no backend package at $REPO_ROOT/backend/src/findling" >&2
    exit 1
fi

for list in "$CASES" "$CHAIN_CASES"; do
    if [ ! -f "$list" ]; then
        echo "measure_compounds_nl: no case list at $list" >&2
        exit 1
    fi
done

if ! command -v docker >/dev/null 2>&1; then
    echo "measure_compounds_nl: docker is required, there is no Debian word list on this machine" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
OUT_DIR=$(CDPATH='' cd -- "$OUT_DIR" && pwd)

echo "measure_compounds_nl: image=$IMAGE $WDUTCH $WNGERMAN $TANTIVY"
echo "measure_compounds_nl: output=$OUT_DIR"

# The mounts as positional parameters rather than one long line, because the
# list of --against is optional and a shell without arrays has no other way to
# add an argument without losing the quoting of the ones before it.
set -- \
    --volume "$REPO_ROOT/backend/src:/opt/findling/src:ro" \
    --volume "$PROBE:/opt/findling/compound_probe_nl.py:ro" \
    --volume "$CASES:/opt/findling/compound_cases_nl.txt:ro" \
    --volume "$CHAIN_CASES:/opt/findling/chain_cases_nl.txt:ro" \
    --volume "$OUT_DIR:/opt/findling/out"

PROBE_ARGS=""
if [ -n "$AGAINST" ]; then
    echo "measure_compounds_nl: against=$AGAINST"
    set -- "$@" --volume "$AGAINST:/opt/findling/against.txt:ro"
    PROBE_ARGS="--against /opt/findling/against.txt"
fi

# One install recipe for both modes. DEBIAN_FRONTEND=noninteractive because
# dictionaries-common would otherwise ask which dictionary is the default.
INSTALL='
    apt-get update >/dev/null
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        "'"$WDUTCH"'" "'"$WNGERMAN"'" >/dev/null
    rm -rf /var/lib/apt/lists/*
    pip install --quiet --no-cache-dir --disable-pip-version-check "'"$TANTIVY"'"
'

# Everything the run reads is mounted read only, so the measurement cannot write
# into the repository except through its output directory, and the container is
# gone with --rm.
docker run --rm \
    "$@" \
    --env "PYTHONPATH=/opt/findling/src" \
    --env "PYTHONDONTWRITEBYTECODE=1" \
    --env "PROBE_ARGS=$PROBE_ARGS" \
    "$IMAGE" \
    sh -eu -c "$INSTALL"'
        # Unquoted on purpose: PROBE_ARGS is either empty or the two words of
        # the option, and both container paths are fixed and carry no space.
        # shellcheck disable=SC2086
        python /opt/findling/compound_probe_nl.py $PROBE_ARGS \
            /opt/findling/compound_cases_nl.txt \
            /opt/findling/chain_cases_nl.txt \
            /opt/findling/out
    '

# The memory mode, three times and every time in a fresh container, so no run
# inherits the allocator state of another. Numbers only.
RAM_FILE="$OUT_DIR/ram.txt"
: > "$RAM_FILE"
for run in 1 2 3; do
    echo "lauf=$run" >> "$RAM_FILE"
    docker run --rm \
        --volume "$REPO_ROOT/backend/src:/opt/findling/src:ro" \
        --volume "$PROBE:/opt/findling/compound_probe_nl.py:ro" \
        --env "PYTHONPATH=/opt/findling/src" \
        --env "PYTHONDONTWRITEBYTECODE=1" \
        "$IMAGE" \
        sh -eu -c "$INSTALL"'
            python /opt/findling/compound_probe_nl.py --ram
        ' >> "$RAM_FILE"
done
echo "measure_compounds_nl: memory written to $RAM_FILE"
