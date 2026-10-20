#!/bin/sh
# Step 2 of the granite comparison: the own int8 build, twice.
#
# scripts/dev/quantize_model.py is called unchanged, with the window of section
# 3 of the README (85.000.000 to 110.000.000 bytes, pitfall 10). The default
# window of the script stays the e5 one; it guards the shipped model. Two runs
# must produce byte identical files, the same proof 2026-09-05 gave for e5.
#
# A run that fails, or a file outside the window, is a finding (assumption A2)
# and not a reason to move the window: the output is kept in the raw file and
# the IBM file of step 1 becomes the point of comparison.
#
#   WORK  scratch directory of step 1 (required); the builds land in
#         WORK/granite-int8-a and WORK/granite-int8-b
#   OUT   raw file (default rohdaten/02-int8.txt next to this directory)
#
# Called from the repository root: sh docs/measurements/2026-10-granite-vergleich/skripte/02-int8.sh
set -eu

: "${WORK:?WORK must name the scratch directory of step 1}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${OUT:-$HERE/rohdaten/02-int8.txt}"
MIN_BYTES=85000000
MAX_BYTES=110000000

: >"$OUT"
say() { printf '%s\n' "$*" | tee -a "$OUT"; }
memory() { say "speicher $1: $(grep -E '^(MemFree|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"; }
digest() { sha256sum "$1" | cut -d ' ' -f 1; }
bytes() { wc -c <"$1" | tr -d ' '; }

say "schritt 2 int8, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "eingabe $WORK/granite/model.onnx sha256 $(digest "$WORK/granite/model.onnx")"
say "fenster $MIN_BYTES bis $MAX_BYTES byte"

status=0
for run in a b; do
    target="$WORK/granite-int8-$run"
    rm -rf "$target"
    mkdir -p "$target"
    memory "vor lauf $run"
    started="$(date +%s)"
    if (cd backend && uv run --group quantize python ../scripts/dev/quantize_model.py \
        --input "$WORK/granite/model.onnx" --output "$target/model.onnx" \
        --min-bytes "$MIN_BYTES" --max-bytes "$MAX_BYTES") >>"$OUT" 2>&1; then
        say "lauf $run fertig in $(($(date +%s) - started)) s: $(bytes "$target/model.onnx") byte sha256 $(digest "$target/model.onnx")"
    else
        say "BEFUND lauf $run: quantize_model.py endete mit Fehler (Annahme A2), Ausgabe oben"
        status=1
    fi
    memory "nach lauf $run"
done

if [ "$status" -eq 0 ]; then
    for run in a b; do
        size="$(bytes "$WORK/granite-int8-$run/model.onnx")"
        if [ "$size" -ge "$MIN_BYTES" ] && [ "$size" -le "$MAX_BYTES" ]; then
            say "lauf $run im fenster: $size byte"
        else
            say "BEFUND lauf $run ausserhalb des fensters: $size byte"
            status=1
        fi
    done
    if cmp "$WORK/granite-int8-a/model.onnx" "$WORK/granite-int8-b/model.onnx" >>"$OUT" 2>&1; then
        say "cmp a gegen b: byte gleich"
    else
        say "BEFUND cmp a gegen b: verschieden"
        status=1
    fi
fi

say "schritt 2 fertig, status $status"

# The raw file goes into a public repository, so the scratch directory is
# written as WORK, in both slash forms the tools print it in.
MASK_A="$WORK" MASK_B="$(printf '%s' "$WORK" | tr '/' '\\')" awk '
    { for (n = 1; n <= 2; n++) { key = (n == 1) ? ENVIRON["MASK_A"] : ENVIRON["MASK_B"]
        while ((i = index($0, key)) > 0) $0 = substr($0, 1, i - 1) "WORK" substr($0, i + length(key)) }
      print }' "$OUT" >"$OUT.tmp" && mv "$OUT.tmp" "$OUT"
exit "$status"
