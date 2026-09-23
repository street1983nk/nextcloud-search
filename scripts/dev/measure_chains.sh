#!/bin/sh
# Measure the position of ascii_fold in the four new analysis chains.
#
# Same shape as scripts/dev/measure_compounds.sh with one visible difference:
# there is no container. All four Snowball stop word lists and all four Snowball
# stemmers are compiled into tantivy, so uv run out of backend/ measures exactly
# what the product ships and a container would only cost run time. The German
# counterpart needs one because /usr/share/dict/ngerman comes from a Debian
# package that does not exist on a developer machine.
#
# Written by the probe into the output directory:
#   familien.tsv     language, lemma, form, recipe, tokens
#   kennzahlen.txt   numbers and digests only
#   verluste.tsv     the form pairs the shipped chain A+ does not bring together
#
# Expected from the phase research, measured on 2026-09-23:
#   total_families=65  total_pairs=573  total_Aplus_hits=467  total_Cplus_hits=463
#   es_supplement=77  it_supplement=10  nl_supplement=0  pt_supplement=30
# A deviation is a finding for the measurement report, not a reason to edit a
# file by hand.
#
# The probe runs the winning candidate against snowball_analyzer from the
# package for every form of every family and exits with 1 on the first
# difference, so a run that ends with 0 is the proof that the measured chain is
# the shipped chain.
#
# Usage: scripts/dev/measure_chains.sh [output-directory]

set -eu

# The pin stands here as a whole pip argument and not as a bare version number,
# so that a grep for the pin finds the line that really names it. It follows the
# pin in backend/pyproject.toml; this script installs nothing, it only reports
# which tantivy the measuring environment is expected to carry.
#
# The line is not only claimed to follow that pin, it is held to it: plan 17-08
# moved the pin from 0.26.0 to 0.26.2 and this line stayed behind, and the
# script prints it as the provenance of a measurement run, where a wrong engine
# name is a wrong measurement report. Since the audit of 2026-09-23 (M-17-06)
# test_the_measurement_script_names_the_pinned_engine in
# backend/tests/test_upgrade_compatibility.py greps this file for TANTIVY_PIN,
# so the next move of the pin cannot happen by halves again.
TANTIVY="tantivy==0.26.2"

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd)

FIXTURES="$REPO_ROOT/backend/tests/fixtures"
STOPWORDS="$FIXTURES/snowball_stopwords_0_26_2.txt"
PROBE="$SCRIPT_DIR/chain_probe.py"
OUT_DIR="${1:-$REPO_ROOT/docs/measurements/2026-09-analyseketten/rohdaten}"

if [ ! -d "$REPO_ROOT/backend/src/findling" ]; then
    echo "measure_chains: no backend package at $REPO_ROOT/backend/src/findling" >&2
    exit 1
fi

for code in es it nl pt; do
    if [ ! -f "$FIXTURES/chain_cases_$code.txt" ]; then
        echo "measure_chains: no case list at $FIXTURES/chain_cases_$code.txt" >&2
        exit 1
    fi
done

if ! command -v uv >/dev/null 2>&1; then
    echo "measure_chains: uv is required, the local system Python of this project is broken" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
OUT_DIR=$(CDPATH='' cd -- "$OUT_DIR" && pwd)

echo "measure_chains: $TANTIVY, no container"
echo "measure_chains: output=$OUT_DIR"

# --stopwords is optional for the probe. Without the fixture it skips the
# tightness half rather than failing, and it says so on stderr.
set -- "$PROBE"
if [ -f "$STOPWORDS" ]; then
    echo "measure_chains: stopwords=$STOPWORDS"
    set -- "$@" --stopwords "$STOPWORDS"
else
    echo "measure_chains: no $STOPWORDS, the leak measurement is skipped" >&2
fi

cd -- "$REPO_ROOT/backend"
exec uv run python "$@" "$FIXTURES" "$OUT_DIR"
