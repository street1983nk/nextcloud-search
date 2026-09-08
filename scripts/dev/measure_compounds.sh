#!/bin/sh
# Measure recipe A case by case against the real Debian word list.
#
# Same shape as scripts/dev/measure_wordlist.sh, and for the same reason:
# /usr/share/dict/ngerman comes from the Debian package wngerman and does not
# exist on a developer machine. The container is the base image the ExApp ships
# on, so the tokens it prints are the tokens the product produces.
#
# One difference to measure_wordlist.sh, on purpose: the package version is
# pinned hard. This measurement is the ground every later plan of phase 8 quotes
# a line from, so it has to be bound to exactly the list the image carries.
#
# Written by the probe into the output directory:
#   tokens-rezept-a.tsv   word, chars, in_ngerman, entry_in_list, tokens
#   fixture-subset.txt    the entries the Python fixture needs, from the real list
#   kennzahlen.txt        numbers and digests only
#
# Expected from the phase research, for the full variant:
#   source_lines=356010  entries=276496
#   wordlist_hash=b1f64012ca7f5b6e57de2cb1bafa2521cb6606f3ccef5d6fd17396edc808dde0
# A deviation is a finding for the measurement report, not a reason to edit a
# file by hand.
#
# The probe compares the tokens of the subset against the tokens of the full
# list for every case and exits with 1 on the first difference, so a run that
# ends with 0 is the proof that the fixture is the list.
#
# With --against the same comparison is made for a list the caller names, which
# is how the fixture of the test suite is checked. The fixture is the union of
# the generated subset with the entries the suite already had, and a union is
# not automatically as good as its parts: one more entry can send a split that
# used to succeed into a dead end. So the union gets measured too.
#
# Usage: scripts/dev/measure_compounds.sh [--against list] [output-directory]
# On Windows call it from Git Bash with MSYS_NO_PATHCONV=1, otherwise MSYS
# rewrites the container paths of the mounts.

set -eu

# The two pins stand here as whole apt and pip arguments, not as bare version
# numbers, so that a grep for the pin finds the line that really installs it.
IMAGE="python:3.13-slim-trixie"
WNGERMAN="wngerman=20161207-15"
TANTIVY="tantivy==0.26.0"

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)

AGAINST=""
if [ "${1:-}" = "--against" ]; then
    if [ $# -lt 2 ]; then
        echo "measure_compounds: --against needs the path of a list" >&2
        exit 2
    fi
    AGAINST=$(CDPATH='' cd -- "$(dirname -- "$2")" && pwd)/$(basename -- "$2")
    if [ ! -f "$AGAINST" ]; then
        echo "measure_compounds: no list at $AGAINST" >&2
        exit 1
    fi
    shift 2
fi

CASES="$REPO_ROOT/backend/tests/fixtures/compound_cases_de.txt"
PROBE="$SCRIPT_DIR/compound_probe.py"
OUT_DIR="${1:-$REPO_ROOT/docs/measurements/2026-09-komposita-rezept-a/rohdaten}"

if [ ! -d "$REPO_ROOT/backend/src/findling" ]; then
    echo "measure_compounds: no backend package at $REPO_ROOT/backend/src/findling" >&2
    exit 1
fi

if [ ! -f "$CASES" ]; then
    echo "measure_compounds: no case list at $CASES" >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "measure_compounds: docker is required, there is no Debian word list on this machine" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
OUT_DIR=$(CDPATH='' cd -- "$OUT_DIR" && pwd)

echo "measure_compounds: image=$IMAGE $WNGERMAN $TANTIVY"
echo "measure_compounds: output=$OUT_DIR"

# The mounts as positional parameters rather than one long line, because the
# list of --against is optional and a shell without arrays has no other way to
# add an argument without losing the quoting of the ones before it.
set -- \
    --volume "$REPO_ROOT/backend/src:/opt/findling/src:ro" \
    --volume "$PROBE:/opt/findling/compound_probe.py:ro" \
    --volume "$CASES:/opt/findling/compound_cases_de.txt:ro" \
    --volume "$OUT_DIR:/opt/findling/out"

PROBE_ARGS=""
if [ -n "$AGAINST" ]; then
    echo "measure_compounds: against=$AGAINST"
    set -- "$@" --volume "$AGAINST:/opt/findling/against.txt:ro"
    PROBE_ARGS="--against /opt/findling/against.txt"
fi

# Everything the run reads is mounted read only, so the measurement cannot write
# into the repository, and the container is gone with --rm.
docker run --rm \
    "$@" \
    --env "PYTHONPATH=/opt/findling/src" \
    --env "PYTHONDONTWRITEBYTECODE=1" \
    --env "PROBE_ARGS=$PROBE_ARGS" \
    "$IMAGE" \
    sh -eu -c '
        apt-get update >/dev/null
        apt-get install -y --no-install-recommends "'"$WNGERMAN"'" >/dev/null
        rm -rf /var/lib/apt/lists/*
        pip install --quiet --no-cache-dir --disable-pip-version-check "'"$TANTIVY"'"
        # Unquoted on purpose: PROBE_ARGS is either empty or the two words of
        # the option, and both container paths are fixed and carry no space.
        # shellcheck disable=SC2086
        python /opt/findling/compound_probe.py $PROBE_ARGS \
            /opt/findling/compound_cases_de.txt \
            /opt/findling/out
    '
