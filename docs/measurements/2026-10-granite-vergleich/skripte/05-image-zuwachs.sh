#!/bin/sh
# Step 5 of the granite comparison: what a second model would add to the image.
#
# Read from the file sizes, as section 4 of the README says: uncompressed and
# gzip -c <file> | wc -c for every file granite would bring next to e5. The
# gzip figure stands in for the compressed layer a pull transfers; the
# uncompressed one is what the image takes on disk.
#
# The licence text is a stand in. The revision carries no LICENSE file, and the
# model card names Apache-2.0, so a shipped COPYING file for granite would be
# the Apache-2.0 text. backend/docker/licenses/COPYING.sqlite-vec is exactly
# that text (taken from LICENSE-APACHE of sqlite-vec) and is measured in its
# place. A probe image is not built: the development machine has too little
# free memory for a second image build next to the running stack, and the file
# sum answers the question without it.
#
#   WORK  scratch directory of steps 1 and 2 (required)
#   OUT   raw file (default rohdaten/05-image-zuwachs.txt next to this directory)
#
# Called from the repository root: sh docs/measurements/2026-10-granite-vergleich/skripte/05-image-zuwachs.sh
set -eu

: "${WORK:?WORK must name the scratch directory of steps 1 and 2}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${OUT:-$HERE/rohdaten/05-image-zuwachs.txt}"
LICENCE="backend/docker/licenses/COPYING.sqlite-vec"

: >"$OUT"
say() { printf '%s\n' "$*" | tee -a "$OUT"; }

say "schritt 5 image-zuwachs, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "speicher vorher: $(grep -E '^(MemFree|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"
say "datei | unkomprimiert byte | gzip byte | sha256"

total_raw=0
total_gzip=0
for entry in \
    "granite-int8-a/model.onnx|model.onnx (eigener int8-Build)" \
    "granite/tokenizer.json|tokenizer.json" \
    "granite/tokenizer_config.json|tokenizer_config.json" \
    "granite/special_tokens_map.json|special_tokens_map.json" \
    "granite/config.json|config.json" \
    "granite/1_Pooling/config.json|1_Pooling/config.json" \
    "LICENCE|Lizenztext Apache-2.0 (Platzhalter: COPYING.sqlite-vec)"; do
    path="${entry%%|*}"
    name="${entry#*|}"
    if [ "$path" = LICENCE ]; then
        file="$LICENCE"
    else
        file="$WORK/$path"
    fi
    raw="$(wc -c <"$file" | tr -d ' ')"
    packed="$(gzip -c "$file" | wc -c | tr -d ' ')"
    total_raw=$((total_raw + raw))
    total_gzip=$((total_gzip + packed))
    say "$name | $raw | $packed | $(sha256sum "$file" | cut -d ' ' -f 1)"
done
say "summe | $total_raw | $total_gzip |"
say "summe in MB (10^6): unkomprimiert $(awk -v b="$total_raw" 'BEGIN { printf "%.1f", b / 1e6 }'), gzip $(awk -v b="$total_gzip" 'BEGIN { printf "%.1f", b / 1e6 }')"

# For scale: the e5 files the image carries today, measured the same way.
e5_raw=0
e5_gzip=0
for file in model.onnx tokenizer.json tokenizer_config.json special_tokens_map.json config.json; do
    e5_raw=$((e5_raw + $(wc -c <"$WORK/e5/$file" | tr -d ' ')))
    e5_gzip=$((e5_gzip + $(gzip -c "$WORK/e5/$file" | wc -c | tr -d ' ')))
done
say "zum vergleich e5 heute (model.onnx, tokenizer.json, tokenizer_config.json, special_tokens_map.json, config.json; ohne sentencepiece.bpe.model): unkomprimiert $e5_raw, gzip $e5_gzip"
say "probe-image: nicht gebaut (Speicher), Zuwachs aus den Dateigroessen"
say "schritt 5 fertig"
