#!/bin/sh
# Measure the constituent list and the compound automaton against the real
# Debian word list.
#
# This has to run in a throwaway container: /usr/share/dict/ngerman comes from
# the Debian package wngerman and does not exist on a developer machine. The
# container is the same base image the ExApp ships on, so the numbers it prints
# are the numbers the product will see.
#
# Printed: lines of the source list, entries after filtering, SHA-256 of the
# filtered list, filter time, automaton build time, resident memory growth and
# throughput in tokens per second. Numbers only, never a token and never a word
# (T-02-14).
#
# Expected from the phase research, for the full variant:
#   source_lines=356010  entries=276496  build_seconds~0.44  rss_growth~23 MB
# A clear deviation is a finding for the plan summary, not a reason to change
# the recipe.
#
# Usage: scripts/dev/measure_wordlist.sh [full|nouns]

set -eu

IMAGE="python:3.13-slim-trixie"
TANTIVY_VERSION="0.26.0"
VARIANT="${1:-full}"

case "$VARIANT" in
    full | nouns) ;;
    *)
        echo "measure_wordlist: variant has to be full or nouns, got '$VARIANT'" >&2
        exit 2
        ;;
esac

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)

if [ ! -d "$REPO_ROOT/backend/src/findling" ]; then
    echo "measure_wordlist: no backend package at $REPO_ROOT/backend/src/findling" >&2
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "measure_wordlist: docker is required, there is no Debian word list on this machine" >&2
    exit 1
fi

echo "measure_wordlist: image=$IMAGE variant=$VARIANT tantivy=$TANTIVY_VERSION"

# The source tree is mounted read only. The measurement never writes into the
# repository, and the container is gone with --rm, so a run leaves nothing behind.
docker run --rm \
    --volume "$REPO_ROOT/backend/src:/opt/findling/src:ro" \
    --env "PYTHONPATH=/opt/findling/src" \
    --env "PYTHONDONTWRITEBYTECODE=1" \
    --env "FINDLING_COMPOUND_DICT=$VARIANT" \
    "$IMAGE" \
    sh -eu -c '
        apt-get update >/dev/null
        apt-get install -y --no-install-recommends wngerman >/dev/null
        rm -rf /var/lib/apt/lists/*
        pip install --quiet --no-cache-dir --disable-pip-version-check "tantivy=='"$TANTIVY_VERSION"'"
        python -m findling.index.wordlist
        python -m findling.index.analyzer
    '
