#!/bin/sh
# Step 1 of the granite comparison: fetch and check the model artefacts.
#
# granite comes from the pinned revision of ibm-granite/granite-embedding-97m-
# multilingual-r2 and nowhere else. The fp32 file is checked against the sha256
# in section 3 of the README, the tokenizer against size and digest out of the
# research of plan 35-03 and against the LFS digest the hub sends along. Any
# difference ends the step with a non zero code before a single number is
# measured (T-35-SC).
#
# e5 is taken out of the shipped image with docker create and docker cp, the
# way docs/measurements/2026-09-06-vektordistanzen/ read it, and its model file
# is checked against MODEL_SHA256 of .github/workflows/integration.yml.
#
# Nothing lands in the repository: WORK names a scratch directory outside of it.
#
#   WORK   scratch directory for the artefacts (required)
#   IMAGE  the shipped image (default the store release 1.4.3)
#   OUT    raw file (default rohdaten/01-artefakte.txt next to this directory)
#
# Called from the repository root: sh docs/measurements/2026-10-granite-vergleich/skripte/01-artefakte.sh
set -eu

: "${WORK:?WORK must name a scratch directory outside the repository}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend:1.4.3}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${OUT:-$HERE/rohdaten/01-artefakte.txt}"

REVISION="835ad14087e140460703cf0fae09f97d469d65c2"
REPO="ibm-granite/granite-embedding-97m-multilingual-r2"
BASE="https://huggingface.co/$REPO/resolve/$REVISION"
# README section 3.
FP32_SHA256="68e592b160673d30250824c1116bc6ab33f70efb22b97c9e1d7ce1e69c1c9d70"
FP32_BYTES=390004608
# Research of plan 35-03: 25.301.672 bytes, sha256 4f2842d5...582f.
TOKENIZER_BYTES=25301672
TOKENIZER_HEAD="4f2842d5"
TOKENIZER_TAIL="582f"
# MODEL_SHA256 of .github/workflows/integration.yml, the int8 e5 of the image.
E5_SHA256="8da4c9ba0ad59f58e8566839425d7fd6339d31414d0ce5cba2d7d0afb75dd8b6"
# MODEL_REVISION and the fp32 digest of backend/Dockerfile.
E5_REVISION="614241f622f53c4eeff9890bdc4f31cfecc418b3"
E5_FP32_SHA256="ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"

mkdir -p "$(dirname "$OUT")" "$WORK/granite/1_Pooling" "$WORK/e5"
: >"$OUT"
say() { printf '%s\n' "$*" | tee -a "$OUT"; }
fail() { say "ABBRUCH: $*"; exit 1; }
memory() { say "speicher $1: $(grep -E '^(MemFree|MemAvailable|SwapTotal|SwapFree):' /proc/meminfo | tr -s ' ' | tr '\n' ' ')"; }
digest() { sha256sum "$1" | cut -d ' ' -f 1; }
bytes() { wc -c <"$1" | tr -d ' '; }

say "schritt 1 artefakte, $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "granite $REPO revision $REVISION"
memory vorher

# The digest the hub reports for an LFS file, read from the redirect header.
hub_digest() {
    curl -fsSI "$BASE/$1" | tr -d '\r' | sed -n 's/^x-linked-etag: *"\{0,1\}\([0-9a-f]\{64\}\)"\{0,1\}$/\1/ip' | head -n 1
}

# A file already in WORK is not fetched again; every check below runs on it all
# the same, so a second run proves the same digests without the download.
fetch() {
    if [ -s "$2" ]; then
        return 0
    fi
    curl -fsSL --retry 3 --retry-delay 2 -o "$2" "$1"
}

for file in onnx/model.onnx tokenizer.json tokenizer_config.json special_tokens_map.json config.json 1_Pooling/config.json; do
    target="$WORK/granite/$file"
    [ "$file" = onnx/model.onnx ] && target="$WORK/granite/model.onnx"
    if fetch "$BASE/$file" "$target"; then
        say "geholt $file $(bytes "$target") byte sha256 $(digest "$target")"
    else
        rm -f "$target"
        say "fehlt $file in der Revision (kein Fehler, wenn optional)"
        [ "$file" = special_tokens_map.json ] || fail "$file nicht geholt"
    fi
done

fp32="$WORK/granite/model.onnx"
[ "$(digest "$fp32")" = "$FP32_SHA256" ] || fail "fp32 sha256 weicht ab"
[ "$(bytes "$fp32")" = "$FP32_BYTES" ] || fail "fp32 groesse weicht ab"
say "pruefung fp32 sha256 gleich README $FP32_SHA256, $FP32_BYTES byte: OK"

tokenizer="$WORK/granite/tokenizer.json"
tokenizer_sha="$(digest "$tokenizer")"
[ "$(bytes "$tokenizer")" = "$TOKENIZER_BYTES" ] || fail "tokenizer groesse weicht ab"
case "$tokenizer_sha" in
    "$TOKENIZER_HEAD"*"$TOKENIZER_TAIL") ;;
    *) fail "tokenizer sha256 passt nicht zu $TOKENIZER_HEAD...$TOKENIZER_TAIL" ;;
esac
hub_tokenizer="$(hub_digest tokenizer.json)"
[ "$hub_tokenizer" = "$tokenizer_sha" ] || fail "tokenizer sha256 ungleich hub ($hub_tokenizer)"
say "pruefung tokenizer $TOKENIZER_BYTES byte, sha256 $tokenizer_sha (= $TOKENIZER_HEAD...$TOKENIZER_TAIL, = hub x-linked-etag): OK"
hub_fp32="$(hub_digest onnx/model.onnx)"
[ "$hub_fp32" = "$FP32_SHA256" ] || fail "fp32 hub digest weicht ab ($hub_fp32)"
say "gegenprobe fp32 hub x-linked-etag $hub_fp32: OK"

# The IBM int8 file, only as a further point of comparison (README section 3).
ibm="$WORK/granite-ibm-int8/model.onnx"
mkdir -p "$(dirname "$ibm")"
fetch "$BASE/onnx/model_quint8_avx2.onnx" "$ibm"
hub_ibm="$(hub_digest onnx/model_quint8_avx2.onnx)"
[ "$hub_ibm" = "$(digest "$ibm")" ] || fail "IBM int8 sha256 ungleich hub ($hub_ibm)"
say "geholt onnx/model_quint8_avx2.onnx $(bytes "$ibm") byte sha256 $(digest "$ibm") (= hub): OK"

say "e5 aus dem ausgelieferten Image $IMAGE"
say "image $(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}} {{.Created}}')"
container="$(docker create "$IMAGE")"
docker cp "$container:/usr/local/share/findling/model/." "$WORK/e5/" >/dev/null
docker rm "$container" >/dev/null
for file in model.onnx tokenizer.json tokenizer_config.json special_tokens_map.json config.json; do
    say "e5 $file $(bytes "$WORK/e5/$file") byte sha256 $(digest "$WORK/e5/$file")"
done
[ "$(digest "$WORK/e5/model.onnx")" = "$E5_SHA256" ] || fail "e5 sha256 ungleich MODEL_SHA256"
say "pruefung e5 model.onnx gleich MODEL_SHA256 $E5_SHA256: OK"

# The fp32 reference of e5: the input the image quantises, from the revision and
# with the digest of backend/Dockerfile (MODEL_REVISION, fetch onnx/model.onnx).
# Its tokenizer is the one of the image, whose digest equals the Dockerfile one.
E5_BASE="https://huggingface.co/intfloat/multilingual-e5-small/resolve/$E5_REVISION"
e5fp32="$WORK/e5-fp32/model.onnx"
mkdir -p "$(dirname "$e5fp32")"
fetch "$E5_BASE/onnx/model.onnx" "$e5fp32"
[ "$(digest "$e5fp32")" = "$E5_FP32_SHA256" ] || fail "e5 fp32 sha256 ungleich Dockerfile"
say "pruefung e5 fp32 $(bytes "$e5fp32") byte sha256 gleich Dockerfile $E5_FP32_SHA256: OK"

memory nachher
say "schritt 1 fertig"
