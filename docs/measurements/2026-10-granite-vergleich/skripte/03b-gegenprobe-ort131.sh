#!/bin/sh
# Step 3b of the granite comparison: the int8 runs of step 3 once more, with the
# onnxruntime of backend/uv.lock instead of the one of the shipped image.
#
# The shipped image 1.4.3 carries onnxruntime 1.30.0, backend/uv.lock pins
# 1.31.0, and the next release would ship the second (pitfall 14). This step
# answers whether the runtime moves a rank: the same tool, the same files, the
# same switches, only the runtime differs. It runs through uv on the development
# machine, offline (UV_OFFLINE=1); the tool itself never opens a connection.
# It is a cross check and no ground for the rule, which reads step 3.
#
#   WORK  scratch directory of steps 1 and 2 (required)
#   OUT   raw file (default rohdaten/03b-gegenprobe-ort131.txt next to this directory)
#
# Called from the repository root: sh docs/measurements/2026-10-granite-vergleich/skripte/03b-gegenprobe-ort131.sh
set -eu

: "${WORK:?WORK must name the scratch directory of steps 1 and 2}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${OUT:-$HERE/rohdaten/03b-gegenprobe-ort131.txt}"
export UV_OFFLINE=1 PYTHONUTF8=1

memory() { grep -E '^(MemFree|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo | tr -s ' ' | tr '\n' ' '; }

{
    echo "schritt 3b, $(date -u +%Y-%m-%dT%H:%M:%SZ), uv run aus backend, UV_OFFLINE=1"
    (cd backend && uv run python -c "import onnxruntime, tokenizers, numpy; print('onnxruntime', onnxruntime.__version__, 'tokenizers', tokenizers.__version__, 'numpy', numpy.__version__)")
} >"$OUT"

for language in de en fr; do
    for run in "e5/model.onnx e5 on mean" "granite-int8-a/model.onnx granite off cls"; do
        # shellcheck disable=SC2086
        set -- $run
        {
            echo
            echo "speicher vorher: $(memory)"
            (cd backend && uv run python ../scripts/dev/model_quality.py \
                --model "$WORK/$1" --tokenizer "$WORK/$2" \
                --dataset "../testdata/semantik/$language.jsonl" \
                --prefixes "$3" --pooling "$4" --vector-dtype int8 --per-case) 2>&1
        } >>"$OUT"
        grep -E '^MRR' "$OUT" | tail -n 1 | tr -s ' ' | sed "s#^#$language $1 #"
    done
done

# The raw file goes into a public repository, so the scratch directory is
# written as WORK, in both slash forms the tools print it in.
MASK_A="$WORK" MASK_B="$(printf '%s' "$WORK" | tr '/' '\\')" awk '
    { for (n = 1; n <= 2; n++) { key = (n == 1) ? ENVIRON["MASK_A"] : ENVIRON["MASK_B"]
        while ((i = index($0, key)) > 0) $0 = substr($0, 1, i - 1) "WORK" substr($0, i + length(key)) }
      print }' "$OUT" >"$OUT.tmp" && mv "$OUT.tmp" "$OUT"
