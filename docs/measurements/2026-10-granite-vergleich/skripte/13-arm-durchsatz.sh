#!/bin/sh
# Step 13 of the granite comparison: embedding throughput of both models on the
# fixed sample of 500 documents, on arm64, the base of the extrapolation in
# step 14.
#
# The text of the sample comes from step 7 (WORK/text/texte.jsonl, sha256
# checked by 10-box-aufbau.sh pruefen). 13-arm-durchsatz.py cuts every document
# with the product chunker and the tokenizer of the model, 1024 token cap, and
# embeds the chunks with the batch size and sequence length of the product.
# One fresh container per run, --memory 2g --memory-swap 2g, alternating e5 and
# granite, RUNS per model.
#
#   WORK   upload directory on the box (required)
#   IMAGE  the shipped image by digest (default store release 1.4.3)
#   RUNS   runs per model (default 2)
#   OUT    raw file (default WORK/rohdaten/13-arm-durchsatz.txt)
set -eu

: "${WORK:?WORK must name the upload directory}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend@sha256:036eb67e3e1144bc371142e18fcbfe94327b2a6edbfc0d1aea2f32d93302fc6d}"
RUNS="${RUNS:-2}"
OUT="${OUT:-$WORK/rohdaten/13-arm-durchsatz.txt}"
LIMIT_BYTES=2147483648

mkdir -p "$(dirname "$OUT")"
: >"$OUT"
say() { printf '%s\n' "$*" | tee -a "$OUT"; }
run() {
    sudo docker run --rm --network none --memory 2g --memory-swap 2g "$@" 2>&1 | grep -v telemetry
}

say "schritt 13 durchsatz arm64, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "image $(sudo docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}} {{.Os}}/{{.Architecture}}')"
say "texte sha256 $(sha256sum "$WORK/text/texte.jsonl" | cut -d ' ' -f 1)"
say "speicher box: $(grep -E '^(MemTotal|MemAvailable|SwapTotal):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"

number=1
while [ "$number" -le "$RUNS" ]; do
    for entry in "e5-int8|e5|mean|passage: " "granite-int8|granite-int8|cls|"; do
        label="${entry%%|*}"
        rest="${entry#*|}"
        model="${rest%%|*}"
        rest="${rest#*|}"
        pooling="${rest%%|*}"
        prefix="${rest#*|}"
        say ""
        say "== $label lauf $number, start $(date -u +%Y-%m-%dT%H:%M:%SZ)"
        result=$(run -v "$WORK:/work:ro" --entrypoint python "$IMAGE" /work/skripte/13-arm-durchsatz.py \
            --texts /work/text/texte.jsonl --model "/work/$model/model.onnx" --tokenizer "/work/$model" \
            --pooling "$pooling" --prefix "$prefix" --label "$label")
        say "$result"
        limit=$(printf '%s\n' "$result" | sed -n 's/^cgroup_memory.max=//p')
        if [ "$limit" != "$LIMIT_BYTES" ]; then
            say "grenze NICHT 2 GiB ($limit), der lauf zaehlt nicht"
            exit 1
        fi
    done
    number=$((number + 1))
done

say ""
say "== zusammenfassung (median ueber die laeufe)"
awk '
    /^== zusammenfassung/ { exit }
    /^== / { label = $2 }
    /^(documents_per_minute|chunks_per_document_mean|chunks|embed_seconds|total_seconds|cgroup_memory\.peak)=/ {
        split($0, kv, "="); key = kv[1]; values[label SUBSEP key] = values[label SUBSEP key] " " kv[2]; keys[key] = 1; labels[label] = 1
    }
    function median(list,    n, a, i, j, t) {
        n = split(list, a, " ")
        for (i = 1; i <= n; i++) for (j = i + 1; j <= n; j++) if (a[j] + 0 < a[i] + 0) { t = a[i]; a[i] = a[j]; a[j] = t }
        return (n % 2) ? a[(n + 1) / 2] : (a[n / 2] + a[n / 2 + 1]) / 2
    }
    END {
        for (label in labels) for (key in keys)
            printf "%s %s median %s (laeufe:%s)\n", label, key, median(values[label SUBSEP key]), values[label SUBSEP key]
    }' "$OUT" | sort >"$OUT.sum"
cat "$OUT.sum" | tee -a "$OUT"
rm -f "$OUT.sum"
say "schritt 13 fertig $(date -u +%Y-%m-%dT%H:%M:%SZ)"
