#!/bin/sh
# Step 7 of the granite comparison: the text of the 500 sample files, once, in
# the shipped image, without network, on the development machine.
#
# The text does not depend on the embedding model. Extracting it here keeps the
# OCR of about a hundred scans off the rented box, where it would cost time and
# say nothing about the two models; the box then only chunks and embeds. The
# README names this as a deviation.
#
#   WORK   scratch directory, holds stichprobe/ from step 6 (required)
#   IMAGE  the shipped image (default the store release 1.4.3)
#   CPUS   cores for --cpuset-cpus (default 2,3)
#
# Writes WORK/text/texte.jsonl (outside the repository) and
# rohdaten/07-text.txt (names, states, character counts and sha256, no text).
set -eu

: "${WORK:?WORK must name the scratch directory of step 6}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend:1.4.3}"
CPUS="${CPUS:-2,3}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
# pwd -W gives the form docker on Windows mounts; elsewhere plain pwd.
SKRIPTE="$(cd "$HERE/skripte" && { pwd -W 2>/dev/null || pwd; })"
ROH="$(cd "$HERE/rohdaten" && { pwd -W 2>/dev/null || pwd; })"

mkdir -p "$WORK/text"
echo "schritt 7 start $(date -u +%Y-%m-%dT%H:%M:%SZ), image $(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}')"
MSYS_NO_PATHCONV=1 docker run --rm --network none --cpuset-cpus "$CPUS" \
    -v "$WORK/stichprobe:/corpus:ro" -v "$WORK/text:/out" -v "$SKRIPTE:/skripte:ro" -v "$ROH:/roh" \
    --entrypoint python "$IMAGE" /skripte/07-text.py \
    --corpus /corpus --out /out/texte.jsonl --report /roh/07-text.txt
echo "texte.jsonl sha256 $(sha256sum "$WORK/text/texte.jsonl" | cut -d ' ' -f 1)" | tee -a "$HERE/rohdaten/07-text.txt"
echo "image $(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}')" >>"$HERE/rohdaten/07-text.txt"
echo "schritt 7 ende $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$HERE/rohdaten/07-text.txt"
