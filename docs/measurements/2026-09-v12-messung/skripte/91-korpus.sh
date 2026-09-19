#!/bin/sh
# It is the same corpus, and this is the step that proves it.
#
# Criterion 1 says "with the existing v1.0 corpus (51.961 documents)". The corpus
# survived 07.09. because it lives in the data store of Nextcloud and not in the
# volume of the ExApp: 50.000 files and 20.208.046.426 bytes under
# ncdata/lasttest/files/loadtest. What has to be shown is that they are still the
# same bytes, and the recipe for that is 44-korpus-pruefsumme.py of the semantic
# run, called here unchanged: sha256 over the sorted lines "name,size,sha256".
#
# Why this step runs BEFORE the image swap and before the index build. It reads
# 20 GB and costs a few minutes. A wrong verdict found afterwards costs the 19
# hours of the rebuild, and those 19 hours would have produced an index over a
# corpus that the report cannot compare to anything. These are the cheapest
# minutes of the whole run.
#
# Why the x86 line is the wrong value to compare against. The generator writes
# the same seed on both architectures, and the checksum differs anyway, because
# the glyph rasterisation of the PDF pages comes out differently on arm64. The
# corpus of the box is the arm64 one, so the target is
#   bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72   (arm64, THIS box)
# and the value
#   c03a8803...                                                        (x86, the WRONG one here)
# belongs to the corpus of the amd64 machine. Comparing against it would produce
# a mismatch that does not exist and would stop a run that was fine.
#
# The exit codes: 6 means the corpus is not the same, 7 means the reading itself
# did not produce a checksum. Both leave the raw file behind, because a step that
# dies before it writes anything leaves exactly the blank both predecessor
# reports left at the tree hash.
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The first default is derived from the location
# of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
DATA_ROOT="${DATA_ROOT:-/mnt/findling}"
KORPUS="${KORPUS:-$DATA_ROOT/ncdata/lasttest/files/loadtest}"
# The recipe of the semantic run, called unchanged. Called as python3 <file>
# rather than through its shebang, so a carriage return in a checkout cannot
# turn this step into a "bad interpreter" (pitfall 2).
PRUEFSUMME="${PRUEFSUMME:-$REPO/docs/measurements/2026-09-05-semantiklauf-m7g/skripte/44-korpus-pruefsumme.py}"

# The three figures of the arm64 corpus. Written down here and not computed,
# because a check that recomputes its own expectation agrees with itself no
# matter what the corpus does.
ERWARTETE_SUMME='bcbef9b2cb067c2200df2a4a2e89408f690710983117d4e78328024046098a72'
ERWARTETE_BYTE='20208046426'
ERWARTETE_DATEIEN='50000'

mkdir -p "$OUT"
ZIEL="$OUT/91-korpus.txt"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# The reading is allowed to fail without ending the script right here, for the
# reason in the head: the raw file has to exist either way.
status=0
sudo python3 "$PRUEFSUMME" "$KORPUS" >"$WORK/lesung.txt" 2>"$WORK/lesung.err" || status=$?

gelesen=$(cat "$WORK/lesung.txt" 2>/dev/null || true)
summe=$(printf '%s' "$gelesen" | sed -n 's/.*checksum=\([0-9a-f]*\).*/\1/p')
byte=$(printf '%s' "$gelesen" | sed -n 's/.*bytes=\([0-9]*\).*/\1/p')
dateien=$(printf '%s' "$gelesen" | sed -n 's/.*files=\([0-9]*\).*/\1/p')

if [ -n "$summe" ] && [ "$summe" = "$ERWARTETE_SUMME" ] && [ "$byte" = "$ERWARTETE_BYTE" ]; then
    verdict='ja'
else
    verdict='nein'
fi

{
    date -u +'korpus-start %Y-%m-%dT%H:%M:%SZ'
    echo "korpus: $KORPUS"
    echo "rezept: $PRUEFSUMME"

    echo "=== The reading, as the recipe printed it ==="
    cat "$WORK/lesung.txt"
    if [ "$status" -ne 0 ]; then
        echo "the reading failed with exit code $status, standard error follows:"
        sed 's/^/  /' "$WORK/lesung.err"
    fi

    echo "=== The comparison, value by value ==="
    printf 'pruefsumme-gemessen  %s\n' "${summe:-(none)}"
    printf 'pruefsumme-erwartet  %s\n' "$ERWARTETE_SUMME"
    printf 'byte-gemessen        %s\n' "${byte:-(none)}"
    printf 'byte-erwartet        %s\n' "$ERWARTETE_BYTE"
    printf 'dateien-gemessen     %s\n' "${dateien:-(none)}"
    printf 'dateien-erwartet     %s\n' "$ERWARTETE_DATEIEN"
    echo "-- the file count is informative: a different one would change the checksum --"
    echo "-- the x86 line c03a8803... is NOT the value this box is compared against --"

    echo "=== The verdict ==="
    echo "korpus-gleich $verdict"

    date -u +'korpus-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

if [ -z "$summe" ]; then
    echo "91-korpus: the reading produced no checksum at all" >&2
    echo "91-korpus: $ZIEL carries the standard error of the recipe" >&2
    exit 7
fi

if [ "$verdict" != 'ja' ]; then
    echo "91-korpus: this is NOT the corpus the v1.0 baseline was measured on" >&2
    echo "91-korpus: the index rebuild must not be started, it would cost 19 hours" >&2
    echo "91-korpus: for an index over a corpus the report cannot compare (criterion 1)" >&2
    exit 6
fi

echo "91-KORPUS-FERTIG"
