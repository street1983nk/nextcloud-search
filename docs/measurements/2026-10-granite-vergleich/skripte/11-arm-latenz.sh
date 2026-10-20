#!/bin/sh
# Step 11 of the granite comparison: arm64 throughput and single query latency,
# on the bare m7g.large, strictly serial. The same measurement as step 4
# (04-latenz-amd64.sh), with two differences that are the point of the box:
#
#   - every container runs with --memory 2g --memory-swap 2g, and the limit is
#     read back out of the cgroup of a container before the first figure is
#     taken (T-35-38). A limit that did not arrive ends this script red.
#   - no --cpuset-cpus: the box has two cores and nothing else runs on it.
#
#   A. throughput: python -m findling.embed.bench --mode tokens-per-second
#   B. single query latency: 04-anfrage-latenz.py, five fresh containers per
#      model, one cold sample each and 100 warm queries after ten throw away ones
#
#   WORK   upload directory on the box (required): e5/, granite-int8/,
#          semantik/de.jsonl, skripte/
#   IMAGE  the shipped image by digest (default store release 1.4.3)
#   STARTS fresh containers per model for B (default 5)
#   OUT    raw file (default WORK/rohdaten/11-arm-latenz.txt)
set -eu

: "${WORK:?WORK must name the upload directory}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend@sha256:036eb67e3e1144bc371142e18fcbfe94327b2a6edbfc0d1aea2f32d93302fc6d}"
STARTS="${STARTS:-5}"
OUT="${OUT:-$WORK/rohdaten/11-arm-latenz.txt}"
LIMIT_BYTES=2147483648

mkdir -p "$(dirname "$OUT")"
: >"$OUT"
say() { printf '%s\n' "$*" | tee -a "$OUT"; }
memory() {
    say "speicher box $1: $(grep -E '^(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"
}
run() {
    sudo docker run --rm --network none --memory 2g --memory-swap 2g "$@" 2>&1 | grep -v telemetry
}

say "schritt 11 latenz arm64, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "image $(sudo docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}} {{.Os}}/{{.Architecture}}')"
say "box: $(nproc) kerne, $(uname -m), $(grep -m 1 -E '^(CPU part|model name)' /proc/cpuinfo | tr -s ' \t' ' ')"
limit=$(run --entrypoint cat "$IMAGE" /sys/fs/cgroup/memory.max)
swap=$(run --entrypoint cat "$IMAGE" /sys/fs/cgroup/memory.swap.max)
say "cgroup rueckgelesen: memory.max $limit, memory.swap.max $swap"
if [ "$limit" != "$LIMIT_BYTES" ]; then
    say "grenze NICHT 2 GiB, es wird nicht gemessen"
    exit 1
fi
say "threads 2, network none, --memory 2g --memory-swap 2g, keine parallellast"
memory vorher

# label, model directory, pooling, query prefix
for entry in "e5-int8|e5|mean|query: " "granite-int8|granite-int8|cls|"; do
    label="${entry%%|*}"
    rest="${entry#*|}"
    model="${rest%%|*}"
    rest="${rest#*|}"
    pooling="${rest%%|*}"
    prefix="${rest#*|}"

    say ""
    say "== $label, modell sha256 $(sha256sum "$WORK/$model/model.onnx" | cut -d ' ' -f 1)"
    memory "vor $label"
    say "-- A durchsatz (findling.embed.bench --mode tokens-per-second)"
    run -v "$WORK/$model:/model:ro" -e FINDLING_EMBED_MODEL_DIR=/model --entrypoint python "$IMAGE" \
        -m findling.embed.bench --mode tokens-per-second | tee -a "$OUT"

    say "-- B einzelanfrage, $STARTS frische container, je 100 warme anfragen aus de.jsonl"
    start=1
    while [ "$start" -le "$STARTS" ]; do
        say "start $start"
        run -v "$WORK:/work:ro" --entrypoint python "$IMAGE" /work/skripte/04-anfrage-latenz.py \
            --model "/work/$model/model.onnx" --tokenizer "/work/$model" --dataset /work/semantik/de.jsonl \
            --pooling "$pooling" --prefix "$prefix" --threads 2 --warm 100 | tee -a "$OUT"
        start=$((start + 1))
    done
    memory "nach $label"
done

# The summary per model, read back out of this very file, as in step 4.
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
    }' "$OUT" | sort >"$OUT.sum"
cat "$OUT.sum" | tee -a "$OUT"
rm -f "$OUT.sum"
say "schritt 11 fertig $(date -u +%Y-%m-%dT%H:%M:%SZ)"
