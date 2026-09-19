#!/bin/sh
# The proof that the image and the working tree are the same state, as a step of
# its own with a raw file of its own.
#
# Why this file exists. Both predecessor reports claim the equality, and in both
# the raw data of that step is empty. 40-abbild.log carries the section title
# "Baumhash im Abbild" with nothing under it, and 61-wechsel.txt carries its
# English counterpart with nothing under it. The cause in 40-abbild.sh is a
# docker run without -i, so the python in the image got no standard input and
# read EOF at once. 61-wechsel.sh added the -i and the output is still missing,
# and the reason for that is documented nowhere in this repository.
#
# So the recipe stops travelling over standard input. 40b-baumhash.py is copied
# into a container of the image with docker cp and called with two arguments, and
# an argument needs no standard input at all. The three readings go into one raw
# file, 40b-baumhash.txt, and this script reads that file back before it exits.
# The real failure of both predecessors was not the missing -i, it was that
# nobody looked at the file afterwards.
set -eu

# Everything a machine could differ in is a variable with a default, so this file
# carries no path of one machine. The defaults are derived from the location of
# the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
RECIPE="$SKRIPTE/40b-baumhash.py"
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend:dev}"

# The root of the installed package inside the image, and the two globs. The
# python3.13 in the path is the interpreter of the image and moves with it.
IMAGE_ROOT='/app/.venv/lib/python3.13/site-packages/findling'
PY_GLOB='**/*.py'
PHP_GLOB='**/*.php'

mkdir -p "$OUT"
ZIEL="$OUT/40b-baumhash.txt"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# The container is created and not run, so the recipe is on its file system
# before the entry point starts. A bind mount would work too and would depend on
# the mount options of the box, which is one variable more than this step needs.
read_the_image() {
    cid=$(sudo docker create --network none --entrypoint /app/.venv/bin/python "$IMAGE" \
        /tmp/40b-baumhash.py "$IMAGE_ROOT" "$PY_GLOB")
    sudo docker cp "$RECIPE" "$cid:/tmp/40b-baumhash.py"
    status=0
    sudo docker start -a "$cid" || status=$?
    sudo docker rm -f "$cid" >/dev/null
    return "$status"
}

# A reading is allowed to fail without ending the script right here, because the
# raw file has to exist either way. The count at the end is what turns a missing
# hash into a failed step, and a step that dies before it writes anything leaves
# exactly the blank the two predecessors left.
reading() {
    ziel="$1"
    shift
    if "$@" >"$ziel" 2>"$ziel.err"; then
        return 0
    fi
    echo "the reading failed, standard error follows:" >>"$ziel"
    sed 's/^/  /' "$ziel.err" >>"$ziel"
    return 0
}

hash_of() {
    sed -n 's/^baumhash: //p' "$1"
}

echo "1 of 3: the package inside the image"
reading "$WORK/abbild.txt" read_the_image

echo "2 of 3: the package in the working tree"
reading "$WORK/arbeitsbaum.txt" python3 "$RECIPE" "$REPO/backend/src/findling" "$PY_GLOB"

echo "3 of 3: the php half in the working tree"
reading "$WORK/php.txt" python3 "$RECIPE" "$REPO/php" "$PHP_GLOB"

image_hash=$(hash_of "$WORK/abbild.txt")
tree_hash=$(hash_of "$WORK/arbeitsbaum.txt")
if [ -n "$image_hash" ] && [ "$image_hash" = "$tree_hash" ]; then
    verdict='ja'
else
    verdict='nein'
fi

{
    date -u +'baumhash-start %Y-%m-%dT%H:%M:%SZ'
    echo "abbild: $IMAGE"
    sudo docker image inspect "$IMAGE" \
        --format 'digest={{index .RepoDigests 0}} arch={{.Architecture}} created={{.Created}}' || true
    echo "repo: $REPO"

    echo "=== The tree hash of the package INSIDE the image ==="
    cat "$WORK/abbild.txt"

    echo "=== The tree hash of the package in the working tree ==="
    cat "$WORK/arbeitsbaum.txt"

    echo "=== The tree hash of the php half in the working tree ==="
    cat "$WORK/php.txt"

    echo "=== The verdict ==="
    echo "abbild-baumhash: $image_hash"
    echo "arbeitsbaum-baumhash: $tree_hash"
    echo "baumhash-gleich $verdict"

    date -u +'baumhash-ende %Y-%m-%dT%H:%M:%SZ'
} >"$ZIEL"

cat "$ZIEL"

# The check both predecessors did not have. An empty raw file and a raw file with
# fewer than three hashes are failed steps, not a report with a blank in it. The
# pattern is anchored on purpose: the two verdict lines carry a label in front of
# the word and must not be counted as readings.
if [ ! -s "$ZIEL" ]; then
    echo "40b-baumhash: the raw file $ZIEL is empty" >&2
    exit 3
fi

counted=$(grep -c '^baumhash: ' "$ZIEL" || true)
if [ "$counted" -ne 3 ]; then
    echo "40b-baumhash: $ZIEL carries $counted tree hashes instead of three" >&2
    exit 3
fi

if [ "$verdict" != 'ja' ]; then
    echo "40b-baumhash: the image and the working tree are NOT the same state" >&2
    echo "40b-baumhash: every figure measured after this line would belong to an unknown state" >&2
    exit 4
fi

echo "40B-BAUMHASH-FERTIG"
