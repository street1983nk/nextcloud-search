#!/bin/sh
# The image of this run, and the proof that it carries the state this report
# claims to have measured.
#
# This is 61-wechsel.sh of the follow up measurement with four changes.
#
# 1. The tree hash step calls 40b-baumhash.sh of plan 10-01 and writes its own
#    raw file. It is not rebuilt as a heredoc here. Both predecessor reports
#    claim that image and working tree are the same state and both left that
#    step EMPTY in the raw data, so this script reads the raw file back before it
#    goes on: it has to exist, carry three anchored baumhash: lines and the
#    verdict baumhash-gleich ja. Anything else stops the run, because every
#    figure measured afterwards would belong to an unknown state.
#
# 2. The digest is written down and held against the one plan 10-02 noted. :dev
#    is a moving pointer and a report names a digest. A deviation is a named
#    finding rather than a footnote, and it is NOT the abort criterion: the
#    docker.yml path filter reaches into backend/**, so a commit that only adds
#    a test file moves the digest without changing a line of the image. The
#    comparison that carries weight is the tree hash of change 1.
#
# 3. unregister runs WITH --rm-data, and here is why, in three sentences. An
#    empty volume is what this run wants: the index is gone since 07.09. and
#    both halves have to start from nought, so a leftover state.db would make
#    the container skip files by their file_id and the rebuild would never
#    happen. It is the same switch that did the damage on 07.09., when a second
#    Nextcloud on this daemon removed the volume of the first one, because the
#    volume name of an ExApp follows from its app id alone. It runs BEFORE the
#    index build and never after it, and the script counts the running Nextcloud
#    instances first and refuses to go on unless there is exactly one.
#
# 4. The info.xml copy is made OUTSIDE the working tree, <image-tag> is moved
#    from 1.0.3 to dev with sed, and afterwards
#    git status --porcelain backend/appinfo/info.xml has to be empty. The copy
#    is kept as the raw file 92-info-box.xml, so the report can show what was
#    registered with (T-10-18).
#
# The order of the second half is not free, it is a dependency chain: the PHP
# half goes in first, then the registration, then the hard limit. The directory
# of the PHP half MUST be called findling. With any other name the class loader
# finds nothing, the search provider stays invisible, and there is no error
# message anywhere that says so. And the hard limit does not survive a register
# (pitfall 4), so it is set afterwards and read back OUT OF THE CGROUP, never
# out of the docker client, with 2147483648 as the expected value.
#
# The exit codes: 4 the tree hash, 5 more than one Nextcloud, 8 a working tree
# that is not clean, 9 a hard limit that did not take.
set -eu

# Everything a machine could differ in is a variable with a default, so this
# file carries no path of one machine. The first default is derived from the
# location of the script itself, which holds on the box and in a checkout alike.
SKRIPTE=$(cd "$(dirname "$0")" && pwd)
REPO="${REPO:-$(cd "$SKRIPTE/../../../.." && pwd)}"
OUT="${OUT:-$SKRIPTE/../rohdaten}"
IMAGE="${IMAGE:-ghcr.io/street1983nk/findling_backend:dev}"
CONTAINER="${CONTAINER:-nc_app_findling_backend}"
NEXTCLOUD="${NEXTCLOUD:-nextcloud-aio-nextcloud}"
DAEMON="${DAEMON:-harp_aio}"
APP_ID="${APP_ID:-findling_backend}"
PHP_APP="${PHP_APP:-findling}"
# The image that carries the Nextcloud server itself, for the count of change 3.
SERVER_IMAGES="${SERVER_IMAGES:-nextcloud/aio-nextcloud|(^|/)nextcloud:}"

# The digest plan 10-02 noted, in both shapes it can be read in. The runner gets
# the manifest index after a pull on the tag, docker image inspect on a local
# machine can name the platform digest instead, and two different things under
# one field name are a trap for this run.
DIGEST_INDEX="${DIGEST_INDEX:-sha256:eed6a5fcb152373e7bf6d7725da774844d4012cfe0cbe02b261f31a865e4cce3}"
DIGEST_ARM64="${DIGEST_ARM64:-sha256:ae58d93005dc18849c3bd128cef51bea0530c143f5719a284fd694b6f9e09d44}"
# The version the info.xml of this tree carries, and the tag it is moved to.
VERSION="${VERSION:-1.0.3}"
IMAGE_TAG="${IMAGE_TAG:-dev}"
# The hard limit, in bytes, as the cgroup reports it.
ERWARTETE_GRENZE="${ERWARTETE_GRENZE:-2147483648}"

mkdir -p "$OUT"
ZIEL="$OUT/92-wechsel.txt"
BAUMHASH="$OUT/40b-baumhash.txt"
INFO_KOPIE="$OUT/92-info-box.xml"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

occ() {
    sudo docker exec --user www-data "$NEXTCLOUD" php occ "$@"
}

# Phase A, and nothing in it touches anything. Every verdict of this phase is
# written into a file of its own, because the exit status of a pipeline that ends
# in tee is the status of tee, and because the abort has to happen before the
# first destructive command of phase B and not after it.
{
    date -u +'wechsel-vorlauf %Y-%m-%dT%H:%M:%SZ'
    echo "abbild: $IMAGE"
    echo "repo: $REPO"

    echo "=== How many Nextcloud instances run on this docker daemon ==="
    echo "-- every running container, so the count below can be checked --"
    sudo docker ps --format '{{.Names}}  {{.Image}}  {{.Status}}'
    sudo docker ps --format '{{.Image}}' | grep -Ec "$SERVER_IMAGES" >"$WORK/instanzen" || true
    [ -s "$WORK/instanzen" ] || echo 0 >"$WORK/instanzen"
    printf 'nextcloud-instanzen %s\n' "$(cat "$WORK/instanzen")"

    echo "=== The image, pulled from ghcr and not built on the box ==="
    # Not built here: a build costs about forty minutes of a capped run and
    # produces the same code under a different layer hash. What the report needs
    # is the proof that the two agree, and that proof is the tree hash.
    sudo docker pull "$IMAGE"
    sudo docker image inspect "$IMAGE" \
        --format 'Id={{.Id}} Arch={{.Architecture}} Created={{.Created}} Digest={{index .RepoDigests 0}}'
    sudo docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}' \
        | sed 's/.*@//' >"$WORK/digest"
    gelesener_digest=$(cat "$WORK/digest")
    printf 'digest-gemessen        %s\n' "$gelesener_digest"
    printf 'digest-erwartet-index  %s\n' "$DIGEST_INDEX"
    printf 'digest-erwartet-arm64  %s\n' "$DIGEST_ARM64"
    if [ "$gelesener_digest" = "$DIGEST_INDEX" ] || [ "$gelesener_digest" = "$DIGEST_ARM64" ]; then
        echo "digest-gleich ja"
    else
        echo "digest-gleich nein"
        echo "BEFUND: the digest of :dev is not the one plan 10-02 wrote down."
        echo "  :dev is a moving pointer, and the path filter of docker.yml reaches"
        echo "  into backend/**, so a commit that only adds a test file moves this"
        echo "  string without changing the image. This belongs into the report as a"
        echo "  finding. The comparison that decides is the tree hash below."
    fi

    echo "=== The tree hash, as its own step with its own raw file ==="
    # Called and not rebuilt. The step judges itself and ends with 3 or 4 if it
    # cannot; the readings below repeat the check because a called script that
    # was replaced by an older copy would otherwise pass unnoticed.
    #
    # Handed over and not left to agree by accident: both scripts carry the same
    # defaults, so an unexported override here would have proven the tree hash
    # against one image while the registration below used another. That is the
    # T-10-13 failure with a green step in front of it.
    export IMAGE OUT REPO
    baumhash_status=0
    sh "$SKRIPTE/40b-baumhash.sh" || baumhash_status=$?
    printf '40b-baumhash exit code: %s\n' "$baumhash_status"
    if [ -s "$BAUMHASH" ]; then
        gezaehlt=$(grep -c '^baumhash: ' "$BAUMHASH" || true)
        printf 'baumhash-zeilen %s (three are expected)\n' "$gezaehlt"
        sed -n 's/^\(baumhash-gleich .*\)$/\1/p' "$BAUMHASH" >"$WORK/baumhash-urteil"
        cat "$WORK/baumhash-urteil"
        if [ "$gezaehlt" -eq 3 ] && grep -q '^baumhash-gleich ja$' "$BAUMHASH"; then
            echo ja >"$WORK/baumhash-ok"
        else
            echo nein >"$WORK/baumhash-ok"
        fi
    else
        echo "the raw file $BAUMHASH is missing or empty"
        echo nein >"$WORK/baumhash-ok"
    fi

    echo "=== What the image brings for the semantic half and for the OCR ==="
    sudo docker run --rm --network none --entrypoint /bin/sh "$IMAGE" -c '
      echo "-- the model directory --"
      ls -la /usr/local/share/findling/model
      echo "-- sha256 of the int8 file --"
      find /usr/local/share/findling/model -name "*.onnx" -exec sha256sum {} \;
      echo "-- the tesseract languages that are really installed --"
      tesseract --list-langs 2>&1
      echo "-- the environment defaults --"
      env | grep -i "FINDLING\|HF_HUB" | sort
    '

    echo "=== The info.xml copy, made outside the working tree ==="
    printf 'the version this tree carries: '
    grep -m1 -o "<version>[^<]*</version>" "$REPO/backend/appinfo/info.xml"
    printf 'the image-tag this tree carries: '
    grep -m1 -o "<image-tag>[^<]*</image-tag>" "$REPO/backend/appinfo/info.xml"
    if ! grep -q "<image-tag>$VERSION</image-tag>" "$REPO/backend/appinfo/info.xml"; then
        echo "note: the image-tag is not $VERSION, the sed below moves whatever is there to $IMAGE_TAG"
    fi
    sed "s|<image-tag>[^<]*</image-tag>|<image-tag>$IMAGE_TAG</image-tag>|" \
        "$REPO/backend/appinfo/info.xml" >"$WORK/92-info-box.xml"
    grep -E '<registry>|<image>|<image-tag>' "$WORK/92-info-box.xml"
    cp "$WORK/92-info-box.xml" "$INFO_KOPIE"
    echo "the copy is kept as $INFO_KOPIE, so the report can show what was registered with"
    echo "-- and the working tree has to be untouched by all of this (T-10-18) --"
    (cd "$REPO" && git status --porcelain backend/appinfo/info.xml) >"$WORK/status.txt" 2>&1 || true
    if [ -s "$WORK/status.txt" ]; then
        echo "arbeitsbaum-unberuehrt nein"
        cat "$WORK/status.txt"
    else
        echo "arbeitsbaum-unberuehrt ja"
    fi

    date -u +'wechsel-vorlauf-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$WORK/vorlauf.txt"

# The three refusals of phase A, every one of them before the first command that
# changes anything.
instanzen=$(cat "$WORK/instanzen")
if [ "$instanzen" -ne 1 ]; then
    echo "92-wechsel: $instanzen Nextcloud instances are running, expected exactly one" >&2
    echo "92-wechsel: --rm-data would hit the volume of every one of them (07.09.)" >&2
    exit 5
fi
if [ "$(cat "$WORK/baumhash-ok" 2>/dev/null || echo nein)" != 'ja' ]; then
    echo "92-wechsel: the tree hash proof did not produce three hashes and a ja" >&2
    echo "92-wechsel: criterion 1 would not be provable, and every figure measured" >&2
    echo "92-wechsel: after this line would belong to an unknown state" >&2
    exit 4
fi
if [ -s "$WORK/status.txt" ]; then
    echo "92-wechsel: backend/appinfo/info.xml is not clean in the working tree" >&2
    echo "92-wechsel: the measured state would not be the state of the repository" >&2
    exit 8
fi

# Phase B, and from here on the box is being changed.
{
    # The whole of phase A goes into the raw file, so one file carries the step.
    cat "$WORK/vorlauf.txt"

    date -u +'wechsel-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== The data store before the swap ==="
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'

    echo "=== unregister WITH --rm-data, deliberately, and before the index build ==="
    occ app_api:app:unregister "$APP_ID" --rm-data 2>&1 || \
        occ app_api:app:unregister "$APP_ID" --rm-data --force 2>&1 || true
    echo "-- the data store afterwards, there must be none left --"
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'
    sudo docker ps -a --filter name=findling_backend --format '{{.Names}} {{.Status}}'

    echo "=== The PHP half of this state, into the container of Nextcloud ==="
    # The directory MUST be called findling. With any other name the class
    # loader finds nothing and the search provider stays invisible, without an
    # error message anywhere.
    sudo docker exec "$NEXTCLOUD" rm -rf "/var/www/html/custom_apps/$PHP_APP"
    sudo docker cp "$REPO/php" "$NEXTCLOUD:/var/www/html/custom_apps/$PHP_APP"
    sudo docker exec "$NEXTCLOUD" chown -R 33:33 "/var/www/html/custom_apps/$PHP_APP"
    sudo docker exec "$NEXTCLOUD" sh -c 'ls -la /var/www/html/custom_apps/findling | head -5'
    occ app:enable "$PHP_APP" 2>&1
    occ app:list 2>&1 | grep -i -A1 "$PHP_APP" | head -6 || true

    echo "=== The registration, over AppAPI, which is also the arming ==="
    sudo docker cp "$INFO_KOPIE" "$NEXTCLOUD:/tmp/92-info-box.xml"
    sudo docker exec "$NEXTCLOUD" chown 33:33 /tmp/92-info-box.xml
    date -u +'register-start %Y-%m-%dT%H:%M:%SZ'
    occ app_api:app:register "$APP_ID" "$DAEMON" \
        --info-xml /tmp/92-info-box.xml --wait-finish 2>&1
    date -u +'register-ende %Y-%m-%dT%H:%M:%SZ'

    echo "=== The hard limit, set again because a register throws it away ==="
    sudo docker update --memory=2g --memory-swap=2g "$CONTAINER" >/dev/null
    sudo docker inspect "$CONTAINER" \
        --format 'Image={{.Config.Image}} StartedAt={{.State.StartedAt}} Restart={{.HostConfig.RestartPolicy.Name}}'
    CID=$(sudo docker inspect -f '{{.Id}}' "$CONTAINER")
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
    echo "-- read back out of the cgroup and not out of the client --"
    gemessene_grenze=$(sudo cat "$SCOPE/memory.max")
    gemessener_swap=$(sudo cat "$SCOPE/memory.swap.max")
    printf 'memory.max=%s\n' "$gemessene_grenze"
    printf 'memory.swap.max=%s\n' "$gemessener_swap"
    printf 'grenze-erwartet=%s\n' "$ERWARTETE_GRENZE"
    if [ "$gemessene_grenze" = "$ERWARTETE_GRENZE" ]; then
        echo "grenze-gesetzt ja"
        echo ja >"$WORK/grenze-ok"
    else
        echo "grenze-gesetzt nein"
        echo nein >"$WORK/grenze-ok"
    fi

    echo "=== memory.events, reading 2 of the run, after the registration ==="
    sudo cat "$SCOPE/memory.events"
    echo "-- anon and memory.current side by side, as everywhere in this run --"
    sudo grep -E '^(anon|file|slab) ' "$SCOPE/memory.stat"
    printf 'memory.current=%s memory.peak=%s\n' \
        "$(sudo cat "$SCOPE/memory.current")" "$(sudo cat "$SCOPE/memory.peak")"

    echo "=== The state of the ExApp and the empty volume it starts from ==="
    occ app_api:app:list 2>&1 | head -30
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'
    sudo docker exec "$CONTAINER" sh -c 'ls -la /nc_app_findling_backend_data' 2>&1 || true

    echo "=== The log of this start ==="
    START=$(sudo docker inspect "$CONTAINER" --format '{{.State.StartedAt}}')
    printf 'container-start %s\n' "$START"
    sudo docker logs --timestamps --since "$START" "$CONTAINER" 2>&1 | tail -30

    date -u +'wechsel-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"

if [ "$(cat "$WORK/grenze-ok" 2>/dev/null || echo nein)" != 'ja' ]; then
    echo "92-wechsel: memory.max is not $ERWARTETE_GRENZE" >&2
    echo "92-wechsel: a run that measures against 4 GB while it means 2 GiB measures nothing" >&2
    exit 9
fi

echo "92-WECHSEL-FERTIG"
