#!/bin/sh
# Step 12 of the granite comparison: anonymous memory of both models on arm64,
# after the method of docs/measurements/2026-09-fp32-speicher/ section 3.
#
# One fresh container per run, --memory 2g --memory-swap 2g, the runs one after
# the other and alternating e5 and granite, RUNS per model. 12-arm-speicher.py
# prints RssAnon before and after tokenizer, session and first batch, and the
# memory.peak of the cgroup of its own container at the end; the limit of that
# cgroup is printed next to it, so every block carries its own readback.
#
#   WORK   upload directory on the box (required)
#   IMAGE  the shipped image by digest (default store release 1.4.3)
#   RUNS   runs per model (default 3)
#   OUT    raw file (default WORK/rohdaten/12-arm-speicher.txt)
set -eu

: "${WORK:?WORK must name the upload directory}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend@sha256:036eb67e3e1144bc371142e18fcbfe94327b2a6edbfc0d1aea2f32d93302fc6d}"
RUNS="${RUNS:-3}"
OUT="${OUT:-$WORK/rohdaten/12-arm-speicher.txt}"
LIMIT_BYTES=2147483648

mkdir -p "$(dirname "$OUT")"
: >"$OUT"
say() { printf '%s\n' "$*" | tee -a "$OUT"; }
run() {
    sudo docker run --rm --network none --memory 2g --memory-swap 2g "$@" 2>&1 | grep -v telemetry
}

say "schritt 12 speicher arm64, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "image $(sudo docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}} {{.Os}}/{{.Architecture}}')"
say "methode 2026-09-fp32-speicher abschnitt 3, batch 8 x 512 token, threads 2, arena aus"
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
        say "== $label lauf $number"
        result=$(run -v "$WORK:/work:ro" --entrypoint python "$IMAGE" /work/skripte/12-arm-speicher.py \
            --model "/work/$model/model.onnx" --tokenizer "/work/$model" \
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
say "== zusammenfassung (median ueber die laeufe, kB; peak in byte)"
awk '
    /^== zusammenfassung/ { exit }
    /^== / { label = $2 }
    /^(rss_anon_[a-z0-9]+_kb|delta_[a-z0-9]+_kb|cgroup_memory\.peak)=/ {
        split($0, kv, "="); key = kv[1]; values[label SUBSEP key] = values[label SUBSEP key] " " kv[2]; keys[key] = 1; labels[label] = 1
    }
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
        for (label in labels) for (key in keys)
            printf "%s %s median %s max %s (laeufe:%s)\n", label, key, median(values[label SUBSEP key]), largest(values[label SUBSEP key]), values[label SUBSEP key]
    }' "$OUT" | sort >"$OUT.sum"
cat "$OUT.sum" | tee -a "$OUT"
rm -f "$OUT.sum"
say "schritt 12 fertig $(date -u +%Y-%m-%dT%H:%M:%SZ)"
