#!/bin/sh
# The environment of the arm64 install run: two archives and one fresh instance.
#
# What this prepares and why each part is here.
#
#   1. A clean checkout of the shipped commit, cloned on the box. The archives
#      must not come out of a Windows working tree: finding 5 of
#      docs/install-check.md established that a tree with CRLF produces a
#      byte-wise different package, so the clone is the source and git on Linux
#      gives it LF endings.
#   2. A throwaway CA with a leaf certificate CN=findling, exactly as the amd64
#      run did (finding 2). A run by hand cannot reach the store signing secret,
#      so what is proven is that the archive carries a signature over exactly its
#      own file list, not that the store would accept the certificate.
#   3. The code signature itself, produced with the occ of the ALREADY running
#      instance. Signing needs a Nextcloud that has its own services, and the
#      fresh instance must not have seen either half of Findling before the check
#      starts. Signing a staged directory installs nothing, so the running
#      instance is the cheapest signer available.
#   4. A fresh instance in the shape of the amd64 run: nextcloud:34.0.3-apache
#      on arm64, HaRP and an nginx front proxy, on port 8097, in a network of its
#      own.
#   5. The CA appended to resources/codesigning/root.crt of that instance WITH a
#      leading newline. That newline is finding 3 of the amd64 run: the shipped
#      root.crt ends without one, a plain cat glues two certificates into one
#      line, splitCerts() then finds no certificate and the leaf cannot be
#      validated.
set -eu

OUT=/home/ubuntu/work/nachmessung
mkdir -p "$OUT"
REPO=/home/ubuntu/work/repo0918
WORK=/home/ubuntu/work/arm64
NET=findling-arm64
NC=findling-arm64-nc
HARP=findling-arm64-harp
PROXY=findling-arm64-proxy
PORT=8097
PLATFORM=linux/arm64
NC_IMAGE=nextcloud:34.0.3-apache
HARP_IMAGE=ghcr.io/nextcloud/nextcloud-appapi-harp:release
ADMIN_PASS_FILE=/home/ubuntu/work/.pw/arm64-admin

rm -rf "$WORK"
mkdir -p "$WORK/dist" "$WORK/ca"

{
    date -u +'arm64-vorbereiten-start %Y-%m-%dT%H:%M:%SZ'

    echo "=== 1. The checkout the archives come from ==="
    cd "$REPO"
    git log --oneline -1
    git status --short | head -5
    echo "-- the proof that this tree has LF endings --"
    if grep -qU $'\r' php/appinfo/info.xml; then
        echo "the checkout carries CRLF, so it must not build a release archive" >&2
        exit 1
    fi
    echo "php/appinfo/info.xml carries no carriage return"

    echo "=== 2. The throwaway CA and the leaf certificate CN=findling ==="
    cd "$WORK/ca"
    openssl req -x509 -newkey rsa:2048 -sha256 -days 2 -nodes \
        -keyout ca.key -out ca.crt -subj '/CN=findling-arm64-throwaway-ca' 2>/dev/null
    openssl req -newkey rsa:2048 -sha256 -nodes \
        -keyout findling.key -out findling.csr -subj '/CN=findling' 2>/dev/null
    openssl x509 -req -in findling.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
        -days 2 -sha256 -out findling.crt 2>/dev/null
    openssl x509 -in findling.crt -noout -subject -issuer
    chmod 600 findling.key ca.key

    echo "=== 3. Stage the companion, sign it with the occ of the running instance ==="
    cd "$REPO"
    sh scripts/release/store-archive.sh stage-companion "$WORK/build-php"
    ls "$WORK/build-php"
    sudo docker cp "$WORK/build-php/findling" nextcloud-aio-nextcloud:/tmp/sign-findling
    sudo docker cp "$WORK/ca/findling.key" nextcloud-aio-nextcloud:/tmp/findling.key
    sudo docker cp "$WORK/ca/findling.crt" nextcloud-aio-nextcloud:/tmp/findling.crt
    sudo docker exec nextcloud-aio-nextcloud chown -R 33:33 /tmp/sign-findling /tmp/findling.key /tmp/findling.crt
    sudo docker exec --user www-data nextcloud-aio-nextcloud php occ integrity:sign-app \
        --privateKey=/tmp/findling.key --certificate=/tmp/findling.crt --path=/tmp/sign-findling
    rm -rf "$WORK/build-php/findling/appinfo/signature.json"
    sudo docker cp nextcloud-aio-nextcloud:/tmp/sign-findling/appinfo/signature.json \
        "$WORK/build-php/findling/appinfo/signature.json"
    test -s "$WORK/build-php/findling/appinfo/signature.json"
    echo "appinfo/signature.json was written and is not empty"
    sudo docker exec nextcloud-aio-nextcloud rm -rf /tmp/sign-findling /tmp/findling.key /tmp/findling.crt

    echo "=== 4. Pack both archives ==="
    sh scripts/release/store-archive.sh pack "$WORK/build-php" findling "$WORK/dist/findling.tar.gz"
    sh scripts/release/store-archive.sh assert-contents "$WORK/dist/findling.tar.gz" findling 1
    sh scripts/release/store-archive.sh stage-backend "$WORK/build-backend"
    sh scripts/release/store-archive.sh pack "$WORK/build-backend" findling_backend "$WORK/dist/findling_backend.tar.gz"
    sh scripts/release/store-archive.sh assert-contents "$WORK/dist/findling_backend.tar.gz" findling_backend 0
    sha256sum "$WORK/dist/findling.tar.gz" "$WORK/dist/findling_backend.tar.gz"

    echo "=== 5. The fresh instance: pull the images for arm64 ==="
    sudo docker network create "$NET" 2>/dev/null || true
    sudo docker pull --platform "$PLATFORM" "$NC_IMAGE" 2>&1 | tail -2
    sudo docker pull --platform "$PLATFORM" "$HARP_IMAGE" 2>&1 | tail -2
    sudo docker pull --platform "$PLATFORM" nginx:1.27-alpine 2>&1 | tail -2
    sudo docker image inspect "$NC_IMAGE" --format 'nextcloud arch={{.Architecture}}'
    sudo docker image inspect "$HARP_IMAGE" --format 'harp arch={{.Architecture}}'

    echo "=== 6. Start the instance and install it with SQLite ==="
    ADMIN_PASS=$(sudo cat "$ADMIN_PASS_FILE")
    sudo docker rm -f "$NC" "$HARP" "$PROXY" 2>/dev/null || true
    sudo docker run -d --name "$NC" --network "$NET" --platform "$PLATFORM" \
        -e NEXTCLOUD_TRUSTED_DOMAINS="localhost $PROXY" \
        "$NC_IMAGE" >/dev/null
    sleep 25
    sudo docker exec --user www-data "$NC" php occ maintenance:install \
        --database=sqlite --admin-user admin --admin-pass "$ADMIN_PASS" 2>&1 | tail -4
    sudo docker exec --user www-data "$NC" php occ config:system:set \
        trusted_domains 1 --value="$PROXY" 2>&1 | tail -2
    sudo docker exec --user www-data "$NC" php occ config:system:set \
        overwrite.cli.url --value="http://$PROXY" 2>&1 | tail -2
    sudo docker exec --user www-data "$NC" php occ status 2>&1 | tail -8
    sudo docker exec --user www-data "$NC" php occ app:list 2>&1 | grep -i findling || \
        echo "the instance knows neither half of findling, as required"

    echo "=== 7. HaRP and the front proxy ==="
    HARP_KEY=$(openssl rand -hex 24)
    printf '%s' "$HARP_KEY" > "$WORK/harp.key"
    chmod 600 "$WORK/harp.key"
    sudo docker run -d --name "$HARP" --network "$NET" --platform "$PLATFORM" \
        -e HP_SHARED_KEY="$HARP_KEY" \
        -e NC_INSTANCE_URL="http://$PROXY" \
        -e HP_FRP_ADDRESS="$HARP:8782" \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        "$HARP_IMAGE" >/dev/null
    printf 'server {\n  listen 80;\n  client_max_body_size 512M;\n  location / {\n    proxy_pass http://%s;\n    proxy_set_header Host $host;\n    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n    proxy_set_header X-Forwarded-Proto http;\n  }\n}\n' "$NC" > "$WORK/proxy.conf"
    sudo docker run -d --name "$PROXY" --network "$NET" --platform "$PLATFORM" \
        -p "$PORT:80" -v "$WORK/proxy.conf:/etc/nginx/conf.d/default.conf:ro" \
        nginx:1.27-alpine >/dev/null
    sleep 6
    sudo docker ps --filter "name=findling-arm64" --format '{{.Names}} {{.Image}} {{.Status}}'
    curl -sS -o /dev/null -w 'proxy=%{http_code}\n' "http://localhost:$PORT/status.php"
    curl -sS "http://localhost:$PORT/status.php"
    echo

    echo "=== 8. The CA into root.crt, WITH the newline that finding 3 is about ==="
    sudo docker exec "$NC" sh -c 'tail -c 1 resources/codesigning/root.crt | xxd | tail -1'
    sudo docker cp "$WORK/ca/ca.crt" "$NC:/tmp/ca.crt"
    sudo docker exec "$NC" sh -c 'printf "\n" >> resources/codesigning/root.crt && cat /tmp/ca.crt >> resources/codesigning/root.crt'
    echo "-- certificates in root.crt, counted with a line anchor --"
    sudo docker exec "$NC" grep -c '^-----BEGIN CERTIFICATE-----$' resources/codesigning/root.crt

    echo "=== 9. The deploy daemon over HaRP ==="
    sudo docker exec --user www-data "$NC" php occ app_api:daemon:register \
        harp_arm64 "Harp Proxy (arm64 box)" docker-install http "$HARP:8780" \
        "http://$PROXY" \
        --harp --harp_frp_address "$HARP:8782" \
        --harp_shared_key "$HARP_KEY" \
        --net "$NET" --set-default 2>&1 | tail -4
    sudo docker exec --user www-data "$NC" php occ app_api:daemon:list 2>&1 | tail -12

    date -u +'arm64-vorbereiten-ende %Y-%m-%dT%H:%M:%SZ'
} 2>&1 | tee "$OUT/80-arm64-vorbereiten.txt"
echo "80-FERTIG" > "$OUT/80-FERTIG"
