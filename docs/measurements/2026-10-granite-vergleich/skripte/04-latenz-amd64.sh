#!/bin/sh
# Step 4 of the granite comparison: amd64 throughput and single query latency
# on the development machine, strictly serial (D-35-11).
#
# Everything runs in the shipped image, without network, pinned to two cores
# (--cpuset-cpus 2,3) with two intra op threads, one model after the other, no
# browser and no other load. Free memory of the host and of the container VM is
# written before every block; the README asks for about 4 GB free.
#
#   A. throughput: python -m findling.embed.bench --mode tokens-per-second, the
#      product tool, unchanged (batch 8, sequence 512, threads 2)
#   B. single query latency: 04-anfrage-latenz.py next to this file, five fresh
#      containers per model, each giving one cold sample (session plus first
#      query) and 100 warm queries of de.jsonl after ten throw away ones
#
# B does not go through the search path of the product: its model wrapper is
# fixed to e5 and granite would need a code change (pitfall 12). Both models
# therefore go through the same script; the README names this as a deviation.
#
#   WORK   scratch directory of steps 1 and 2 (required)
#   IMAGE  the shipped image (default the store release 1.4.3)
#   CPUS   cores for --cpuset-cpus (default 2,3)
#   STARTS fresh containers per model for B (default 5)
#   OUT    raw file (default rohdaten/04-latenz-amd64.txt next to this directory)
#
# Called from the repository root: sh docs/measurements/2026-10-granite-vergleich/skripte/04-latenz-amd64.sh
set -eu

: "${WORK:?WORK must name the scratch directory of steps 1 and 2}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend:1.4.3}"
CPUS="${CPUS:-2,3}"
STARTS="${STARTS:-5}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${OUT:-$HERE/rohdaten/04-latenz-amd64.txt}"
# pwd -W gives the form docker on Windows mounts; elsewhere plain pwd.
REPO_ROOT="$(cd "$HERE/../../.." && { pwd -W 2>/dev/null || pwd; })"
SKRIPTE="$REPO_ROOT/docs/measurements/2026-10-granite-vergleich/skripte"

: >"$OUT"
say() { printf '%s\n' "$*" | tee -a "$OUT"; }
memory() {
    say "speicher host $1: $(grep -E '^(MemFree|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"
    say "speicher vm $1: $(docker run --rm --network none --entrypoint cat "$IMAGE" /proc/meminfo | grep -E '^(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree):' | tr -s ' ' | tr '\n' ' ')"
}
run() {
    docker run --rm --network none --cpuset-cpus "$CPUS" "$@" 2>&1 | grep -v telemetry
}

say "schritt 4 latenz amd64, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "image $(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}')"
say "cpu host: $(grep -m 1 'model name' /proc/cpuinfo | cut -d ':' -f 2 | sed 's/^ *//'), $(grep -c '^processor' /proc/cpuinfo) logische kerne"
say "cpuset $CPUS, threads 2, network none, browser geschlossen, keine parallellast"
memory vorher

# model label, model file, tokenizer directory, pooling, query prefix
for entry in "e5-int8|e5/model.onnx|e5|mean|query: " "granite-int8|granite-int8-a/model.onnx|granite|cls|"; do
    label="${entry%%|*}"
    rest="${entry#*|}"
    model="${rest%%|*}"
    rest="${rest#*|}"
    tokenizer="${rest%%|*}"
    rest="${rest#*|}"
    pooling="${rest%%|*}"
    prefix="${rest#*|}"

    say ""
    say "== $label, modell sha256 $(sha256sum "$WORK/$model" | cut -d ' ' -f 1)"
    memory "vor $label"
    say "-- A durchsatz (findling.embed.bench --mode tokens-per-second)"
    run -v "$WORK/$tokenizer:/model:ro" -v "$WORK/$model:/model/model.onnx:ro" \
        -e FINDLING_EMBED_MODEL_DIR=/model --entrypoint python "$IMAGE" \
        -m findling.embed.bench --mode tokens-per-second | tee -a "$OUT"

    say "-- B einzelanfrage, $STARTS frische container, je 100 warme anfragen aus de.jsonl"
    start=1
    while [ "$start" -le "$STARTS" ]; do
        say "start $start"
        run -v "$WORK:/work:ro" -v "$SKRIPTE:/skripte:ro" -v "$REPO_ROOT/testdata/semantik:/data:ro" \
            --entrypoint python "$IMAGE" /skripte/04-anfrage-latenz.py \
            --model "/work/$model" --tokenizer "/work/$tokenizer" --dataset /data/de.jsonl \
            --pooling "$pooling" --prefix "$prefix" --threads 2 --warm 100 | tee -a "$OUT"
        start=$((start + 1))
    done
    memory "nach $label"
done

# The summary per model: cold over the fresh starts, warm as the median of the
# per start p50 and p95. Read back out of this very file.
say ""
say "== zusammenfassung"
awk '
    /^== zusammenfassung/ { exit }
    /^== / { label = $2; sub(",", "", label) }
    /^tokens_per_second_p50=/ { split($0, kv, "="); tps[label] = kv[2] }
    /^cold_ms=/ { split($0, kv, "="); cold[label] = cold[label] " " kv[2] }
    /^warm_p50_ms=/ { split($0, kv, "="); w50[label] = w50[label] " " kv[2] }
    /^warm_p95_ms=/ { split($0, kv, "="); w95[label] = w95[label] " " kv[2] }
    function median(list,    n, a, i, j, t) {
        n = split(list, a, " ")
        for (i = 1; i <= n; i++) for (j = i + 1; j <= n; j++) if (a[j] + 0 < a[i] + 0) { t = a[i]; a[i] = a[j]; a[j] = t }
        return (n % 2) ? a[(n + 1) / 2] : (a[n / 2] + a[n / 2 + 1]) / 2
    }
    function largest(list,    n, a, i, m) {
        n = split(list, a, " "); m = a[1]
        for (i = 2; i <= n; i++) if (a[i] + 0 > m + 0) m = a[i]
        return m
    }
    END {
        for (label in cold)
            printf "%s tokens_per_second_p50 %s, kalt p50 %s ms max %s ms (starts:%s), warm p50 %s ms, warm p95 %s ms\n",
                label, tps[label], median(cold[label]), largest(cold[label]), cold[label], median(w50[label]), median(w95[label])
    }' "$OUT" | sort | tee -a "$OUT.sum"
cat "$OUT.sum" >>"$OUT"
rm -f "$OUT.sum"

# The raw file goes into a public repository, so the scratch directory is
# written as WORK, in both slash forms the tools print it in.
MASK_A="$WORK" MASK_B="$(printf '%s' "$WORK" | tr '/' '\\')" awk '
    { for (n = 1; n <= 2; n++) { key = (n == 1) ? ENVIRON["MASK_A"] : ENVIRON["MASK_B"]
        while ((i = index($0, key)) > 0) $0 = substr($0, 1, i - 1) "WORK" substr($0, i + length(key)) }
      print }' "$OUT" >"$OUT.tmp" && mv "$OUT.tmp" "$OUT"
say "schritt 4 fertig"
