#!/bin/sh
# Step 3 of the granite comparison: quality of both models in one run.
#
# scripts/dev/model_quality.py runs inside the shipped image, without network
# (docker run --network none), with the model directories of steps 1 and 2, the
# tool and the test set mounted read only. Every case of de, en and fr, with
# --per-case for the pairwise comparison of section 1 (a) of the README.
#
#   e5       --pooling mean --prefixes on   (as shipped)
#   granite  --pooling cls  --prefixes off  (pitfall 11)
#
# Each model twice: int8 weights with int8 vectors, which is the shipped
# combination the rule judges, and fp32 weights with fp32 vectors as reference.
# The IBM int8 file of step 1 is one more point of comparison and no ground for
# the decision. The positive control runs granite int8 with mean pooling: it has
# to come out measurably worse than cls, or the switch does not reach the
# arithmetic and the run does not count.
#
# Sequence length is 512 for both, fixed in the tool (MAX_SEQUENCE_TOKENS). The
# extra line for granite at 1024 needs a switch the tool does not have, which is
# written down as a deviation in the README rather than patched in here.
#
#   WORK   scratch directory of steps 1 and 2 (required)
#   IMAGE  the shipped image (default the store release 1.4.3)
#   RAW    raw directory (default rohdaten/ next to this directory)
#
# Called from the repository root: sh docs/measurements/2026-10-granite-vergleich/skripte/03-qualitaet.sh
set -eu

: "${WORK:?WORK must name the scratch directory of steps 1 and 2}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend:1.4.3}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
RAW="${RAW:-$HERE/rohdaten}"
# pwd -W gives the form docker on Windows mounts; elsewhere plain pwd.
REPO_ROOT="$(cd "$HERE/../../.." && { pwd -W 2>/dev/null || pwd; })"
mkdir -p "$RAW"

memory() { grep -E '^(MemFree|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo | tr -s ' ' | tr '\n' ' '; }

# One measurement: raw file, model file, tokenizer directory, then the switches.
measure() {
    out="$1"
    model="$2"
    tokenizer="$3"
    shift 3
    {
        echo "schritt 3, $(date -u +%Y-%m-%dT%H:%M:%SZ), image $IMAGE, network none"
        echo "speicher vorher: $(memory)"
        echo "modell sha256 $(sha256sum "$WORK/$model" | cut -d ' ' -f 1)"
        echo "testset sha256 (LF) $DATA_SHA256"
    } >"$out"
    started="$(date +%s)"
    docker run --rm --network none \
        -v "$WORK:/work:ro" \
        -v "$REPO_ROOT/scripts/dev:/tools:ro" \
        -v "$REPO_ROOT/testdata/semantik:/data:ro" \
        --entrypoint python "$IMAGE" /tools/model_quality.py \
        --model "/work/$model" --tokenizer "/work/$tokenizer" --per-case "$@" 2>&1 \
        | grep -v 'telemetry' >>"$out"
    {
        echo "dauer $(($(date +%s) - started)) s"
        echo "speicher nachher: $(memory)"
    } >>"$out"
    grep -E '^(dataset|pooling|MRR)' "$out" | tr -s ' ' | tr '\n' ' '
    echo "<- $(basename "$out")"
}

for language in de en fr; do
    data="--dataset /data/$language.jsonl"
    # The digest of README section 2 is the one of the LF blob; a Windows
    # checkout carries CR, which the tool ignores and this line strips.
    DATA_SHA256="$(tr -d '\r' <"$REPO_ROOT/testdata/semantik/$language.jsonl" | sha256sum | cut -d ' ' -f 1)"
    # shellcheck disable=SC2086
    measure "$RAW/03-qualitaet-e5-int8-$language.txt" e5/model.onnx e5 \
        $data --prefixes on --pooling mean --vector-dtype int8
    # shellcheck disable=SC2086
    measure "$RAW/03-qualitaet-e5-fp32-$language.txt" e5-fp32/model.onnx e5 \
        $data --prefixes on --pooling mean --vector-dtype fp32
    # shellcheck disable=SC2086
    measure "$RAW/03-qualitaet-granite-int8-$language.txt" granite-int8-a/model.onnx granite \
        $data --prefixes off --pooling cls --vector-dtype int8
    # shellcheck disable=SC2086
    measure "$RAW/03-qualitaet-granite-fp32-$language.txt" granite/model.onnx granite \
        $data --prefixes off --pooling cls --vector-dtype fp32
    # shellcheck disable=SC2086
    measure "$RAW/03-qualitaet-granite-ibmint8-$language.txt" granite-ibm-int8/model.onnx granite \
        $data --prefixes off --pooling cls --vector-dtype int8
    # shellcheck disable=SC2086
    measure "$RAW/03-positivkontrolle-$language.tmp" granite-int8-a/model.onnx granite \
        $data --prefixes off --pooling mean --vector-dtype int8
done

# The positive control in one file, each language against its cls run.
control="$RAW/03-positivkontrolle.txt"
{
    echo "positivkontrolle: granite int8 mit --pooling mean gegen --pooling cls, sonst gleich"
    for language in de en fr; do
        echo
        cat "$RAW/03-positivkontrolle-$language.tmp"
        mean_mrr="$(sed -n 's/^MRR *//p' "$RAW/03-positivkontrolle-$language.tmp")"
        cls_mrr="$(sed -n 's/^MRR *//p' "$RAW/03-qualitaet-granite-int8-$language.txt")"
        verdict="$(awk -v m="$mean_mrr" -v c="$cls_mrr" 'BEGIN { print (m < c) ? "mean schlechter: OK" : "mean NICHT schlechter: Lauf zaehlt nicht" }')"
        echo "vergleich $language: MRR mean $mean_mrr, MRR cls $cls_mrr, $verdict"
    done
} >"$control"
rm -f "$RAW"/03-positivkontrolle-*.tmp
grep '^vergleich' "$control"
