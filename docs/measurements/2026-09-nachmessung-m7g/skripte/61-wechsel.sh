#!/bin/sh
# The image of this run: the multi arch image of the shipped state, pulled from
# ghcr instead of built on the box.
#
# Why not built here, as in 06-11. The tree of this run carries no change to
# backend/ since the commit the multi arch workflow last built (9645799), so the
# image in the registry IS the shipped state, and building it again on the box
# would spend forty minutes of a capped run to produce the same code with a
# different layer hash. What the report needs is the proof that the two agree,
# and that proof is the tree hash over the package, not the build.
#
# unregister WITHOUT --rm-data: the data store nc_app_findling_backend_data stays
# and with it state.db, vectors.db and the tantivy index. The run measures on the
# corpus of 06-11 and must not measure the building of an empty index.
#
# The hard limit does not survive a register (06.1-RESEARCH part 5.2, pitfall 5),
# so it is set afterwards and read back out of the cgroup, not out of the client.
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
ZIEL="$OUT/61-wechsel.txt"
IMAGE='ghcr.io/street1983nk/findling_backend:dev'

occ() {
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ "$@"
}

{
    date -u +'wechsel-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== The image, its digest and its architecture ==="
    sudo docker image inspect "$IMAGE" \
        --format 'Id={{.Id}} Arch={{.Architecture}} Created={{.Created}} Digest={{index .RepoDigests 0}}'

    echo "=== The tree hash of the package INSIDE the image ==="
    sudo docker run --rm -i --entrypoint /app/.venv/bin/python "$IMAGE" - <<'PY'
import hashlib
import pathlib

root = pathlib.Path("/app/.venv/lib/python3.13/site-packages/findling")
digest = hashlib.sha256()
count = 0
for path in sorted(root.rglob("*.py")):
    data = path.read_bytes().replace(b"\r\n", b"\n")
    digest.update(
        path.relative_to(root).as_posix().encode()
        + b"\0"
        + hashlib.sha256(data).hexdigest().encode()
        + b"\n"
    )
    count += 1
print("dateien:", count)
print("baumhash:", digest.hexdigest())
PY

    echo "=== What the image brings for the semantic half and for the OCR ==="
    sudo docker run --rm --entrypoint /bin/sh "$IMAGE" -c '
      echo "-- the model directory --"
      ls -la /usr/local/share/findling/model
      echo "-- sha256 of the int8 file --"
      find /usr/local/share/findling/model -name "*.onnx" -exec sha256sum {} \;
      echo "-- the tesseract languages that are really installed --"
      tesseract --list-langs 2>&1
      echo "-- the environment defaults --"
      env | grep -i "FINDLING\|HF_HUB" | sort
    '

    echo "=== The data store before the swap ==="
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'

    echo "=== unregister without --rm-data, then register on the ghcr image ==="
    sudo docker cp /home/ubuntu/work/61-info-box.xml nextcloud-aio-nextcloud:/tmp/61-info-box.xml
    sudo docker exec nextcloud-aio-nextcloud chown 33:33 /tmp/61-info-box.xml
    grep -E '<registry>|<image>|<image-tag>' /home/ubuntu/work/61-info-box.xml
    occ app_api:app:unregister findling_backend 2>&1
    occ app_api:app:register findling_backend harp_aio \
        --info-xml /tmp/61-info-box.xml --wait-finish 2>&1

    echo "=== The data store after the swap, the same one ==="
    sudo docker volume ls --filter name=findling_backend --format '{{.Name}}'

    echo "=== The hard limit, set again because a register throws it away ==="
    sudo docker update --memory=2g --memory-swap=2g nc_app_findling_backend >/dev/null
    sudo docker inspect nc_app_findling_backend \
        --format 'Image={{.Config.Image}} Memory={{.HostConfig.Memory}} MemorySwap={{.HostConfig.MemorySwap}}'
    CID=$(sudo docker inspect -f '{{.Id}}' nc_app_findling_backend)
    SCOPE="/sys/fs/cgroup/system.slice/docker-$CID.scope"
    echo "-- read back out of the cgroup and not out of the client --"
    printf 'memory.max=%s\n' "$(sudo cat "$SCOPE/memory.max")"
    printf 'memory.swap.max=%s\n' "$(sudo cat "$SCOPE/memory.swap.max")"

    echo "=== The state of the ExApp and the armed marker in the volume ==="
    occ app_api:app:list 2>&1 | head -30
    sudo ls -la /mnt/findling/docker/volumes/nc_app_findling_backend_data/_data

    echo "=== The log of this start ==="
    START=$(sudo docker inspect nc_app_findling_backend --format '{{.State.StartedAt}}')
    printf 'container-start %s\n' "$START"
    sudo docker logs --timestamps --since "$START" nc_app_findling_backend 2>&1 | tail -30

    date -u +'wechsel-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$ZIEL"
echo "61-WECHSEL-FERTIG"
