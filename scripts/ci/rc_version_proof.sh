#!/usr/bin/env bash
# The run blocks of .github/workflows/rc-version-proof.yml, one file with one
# subcommand per step (plan 43-10, D-43-10, D-43-13). The workflow stays a thin
# frame because deploy-harp.yml sits 36 bytes under the 500 KB cap of GitHub
# Actions and backend/tests/test_workflow_size.py holds every file under it:
# anything that can grow lives here.
#
# What the two jobs prove, before anybody hands the reporter a test build:
#
#   A6 (subcommands a6-swap, a6): on a FRESH Nextcloud of each supported line
#   a companion 1.6.3-rc.1 installs OVER a released 1.6.2 (occ upgrade green,
#   app:list shows 1.6.3-rc.1, the 1.6.3 migration ran, the per document hint
#   flag stands at 1), and the comparison the server itself uses for "update
#   available" reads 1.6.3 as newer than 1.6.3-rc.1. The comparison is not
#   assumed, it is grepped out of the server checkout of this very run, file
#   and line go to the log, and php -r executes that form.
#
#   A5 (subcommands a5-harp, a5-proxy, a5-register, a5): on the path of the
#   reporter (a HaRP deploy daemon, the pattern of deploy-harp.yml) a backend
#   1.6.2 registered from the info.xml of tag v1.6.2 updates through
#   occ app_api:app:update findling_backend --info-xml <raw URL of the
#   testbuild info.xml>, pulls the immutable image :<sha>, and a later
#   info.xml with version 1.6.3 on the same image is applied as an update.
#   The comparison AppAPI uses is grepped out of the AppAPI checkout, file and
#   line go to the log, and php -r executes it for both pairs. Every occ
#   output is printed verbatim; a step that refuses without --force-update is
#   repeated with it and both outputs are shown.
#
# A failed verdict means: no test build for the reporter, the findings go to
# the owner and the decision is taken in 43-11 (must_have 5 of 43-10-PLAN.md).
#
# Inputs arrive as environment variables and never as interpolated text
# (Sec-L7 shape, T-43-32): RC_REF, ARCHIVE_RUN_ID, IMAGE_SHA, HARP_IMAGE,
# HARP_SHARED_KEY, GH_TOKEN. Every one of them is validated against a fixed
# shape before it is used.

set -eo pipefail

REPO='street1983nk/nextcloud-search'
RC_VERSION='1.6.3-rc.1'
BASE_VERSION='1.6.2'
STORE_VERSION='1.6.3'
MIGRATION_163='001603Date20261108000000'
# The DER sha256 of the companion signing key, the same value release.yml
# checks (docs/certificates.md): a certificate that does not belong to our key
# must not green a signature check.
FINDLING_CERT_FPR='c99e28f3decd64cf5d3e7fdecaac4e3d29b3444c71b7cb914aff81519f2108ab'

summary() {
  # One line to the job summary and to the log, so the verdict is readable in
  # both places. The summary file is absent when the script runs locally.
  printf '%s\n' "$1"
  if [ -n "${GITHUB_STEP_SUMMARY}" ]; then
    printf '%s\n' "$1" >> "${GITHUB_STEP_SUMMARY}"
  fi
}

fail_a6() {
  summary "A6: failed $1"
  exit 1
}

fail_a5() {
  summary "A5: failed $1"
  exit 1
}

# The php reading of "a is newer than b", printed verbatim and judged by the
# exit code. The operator form '>' is the form the grepped call sites use; the
# bare three-argument-less call is printed next to it so the log shows the raw
# integer as well (W-a of 43-10-PLAN.md).
compare_pair() {
  local newer="$1" older="$2" fail_fn="$3"
  local verdict raw
  verdict=$(php -r 'var_export(version_compare($argv[1], $argv[2], ">"));' "${newer}" "${older}")
  raw=$(php -r 'var_export(version_compare($argv[1], $argv[2]));' "${newer}" "${older}")
  echo "php -r version_compare('${newer}', '${older}', '>') = ${verdict} (raw comparison ${raw})"
  if [ "${verdict}" != "true" ]; then
    "${fail_fn}" "php reads '${newer}' as not newer than '${older}', so the version order does not hold"
  fi
}

require_env() {
  local name
  for name in "$@"; do
    if [ -z "${!name}" ]; then
      echo "the environment variable ${name} is empty and this step cannot run without it"
      exit 1
    fi
  done
}

check_image_sha() {
  case "${IMAGE_SHA}" in
    *[!0-9a-f]*) echo "IMAGE_SHA '${IMAGE_SHA}' is not lowercase hex"; exit 1 ;;
  esac
  if [ "${#IMAGE_SHA}" -ne 40 ]; then
    echo "IMAGE_SHA '${IMAGE_SHA}' does not have 40 characters"
    exit 1
  fi
}

read_xml_version() {
  sed -n 's:.*<version>\(.*\)</version>.*:\1:p' "$1" | sed -n '1p'
}

read_xml_image_tag() {
  sed -n 's:.*<image-tag>\(.*\)</image-tag>.*:\1:p' "$1" | sed -n '1p'
}

# occ with a verbatim transcript: the plan demands the outputs word for word,
# and a step that refuses without --force-update is repeated with it. The
# transcript goes to stdout AND to a file, so the retry logic can judge the
# exit code while nothing of the output is lost.
run_occ_update() {
  local rc=0 out
  echo "--- occ $* ---"
  set +e
  out=$(timeout 600 ./occ "$@" 2>&1)
  rc=$?
  set -e
  printf '%s\n' "${out}"
  echo "--- exit ${rc} ---"
  return "${rc}"
}

backend_listed_at() {
  timeout 60 ./occ app_api:app:list | grep -F -q "$1"
}

wait_for_exapp_heartbeat() {
  # The probe reads the answer where AppAPI reads it: the container log. The
  # front proxy of this job does not route /exapps/ (proof runs 42537244567
  # and 42538879801: the container answered heartbeat, init and enabled with
  # 200 through the HaRP tunnel and spoke to Nextcloud over OCS while the
  # curl against localhost:8090 starved), so an outside curl here probes the
  # nginx of the harness and not the product. 300 s for the cold start.
  local i
  for i in $(seq 1 150); do
    if docker logs nc_app_findling_backend 2>&1 | grep -q '"GET /heartbeat HTTP/1.1" 200'; then
      echo "the container answered heartbeat with 200 through the HaRP tunnel (its own log)"
      return 0
    fi
    sleep 2
  done
  echo "the container log never showed a heartbeat answered with 200"
  return 1
}

# ---------------------------------------------------------------------------
# a6-swap: put the RELEASED companion 1.6.2 into the findling checkout before
# setup-test-nc moves it to apps/findling. The instance then starts its life
# at 1.6.2, which is the precondition of the whole upgrade proof.
# ---------------------------------------------------------------------------
a6_swap() {
  require_env GH_TOKEN RUNNER_TEMP
  local dir="${RUNNER_TEMP}/companion-162" top version
  mkdir -p "${dir}"
  gh release download "v${BASE_VERSION}" --pattern findling.tar.gz \
    --repo "${REPO}" -D "${dir}"
  # sed reads the listing to its end, so tar never sees a closed pipe (the
  # head of the first try died of SIGPIPE under pipefail: "tar: stdout:
  # write error", proof run 42537244567).
  top=$(tar -tzf "${dir}/findling.tar.gz" | sed -n '1p' | cut -d/ -f1)
  if [ "${top}" != "findling" ]; then
    echo "the companion archive of v${BASE_VERSION} does not carry the single top directory 'findling' but '${top}'"
    exit 1
  fi
  mkdir -p "${dir}/unpack"
  tar -xzf "${dir}/findling.tar.gz" -C "${dir}/unpack"
  rm -rf findling-src/php
  mv "${dir}/unpack/findling" findling-src/php
  version=$(read_xml_version findling-src/php/appinfo/info.xml)
  if [ "${version}" != "${BASE_VERSION}" ]; then
    echo "the swapped companion carries version '${version}' and not ${BASE_VERSION}"
    exit 1
  fi
  echo "the companion of release v${BASE_VERSION} replaces the checkout copy, setup-test-nc installs it next"
}

# ---------------------------------------------------------------------------
# a6: the upgrade proof on the fresh instance, run from the workspace root of
# the server checkout after setup-test-nc.
# ---------------------------------------------------------------------------
a6_proof() {
  require_env GH_TOKEN RUNNER_TEMP ARCHIVE_RUN_ID
  case "${ARCHIVE_RUN_ID}" in
    *[!0-9]*|'') fail_a6 "ARCHIVE_RUN_ID '${ARCHIVE_RUN_ID}' is not a run id" ;;
  esac

  local installed
  installed=$(timeout 60 ./occ config:app:get findling installed_version)
  echo "installed companion before the upgrade: ${installed}"
  if [ "${installed}" != "${BASE_VERSION}" ]; then
    fail_a6 "the instance starts at '${installed}' and not at ${BASE_VERSION}, so this run proves nothing"
  fi

  # One row in findling_scan_stats, seeded by SQL and not by a crawl: the
  # crawl of this app is driven by the backend container, and this job
  # registers none on purpose (A6 is about the companion alone). The 1.6.3
  # migration reads "at least one row" as the update signal and never asks
  # where the row came from, so a seeded row exercises exactly the branch an
  # updated instance takes.
  echo "seeding one scan row by SQL, because no backend container exists in this job to crawl one"
  sqlite3 data/owncloud.db \
    "INSERT INTO oc_findling_scan_stats (storage_id, files_seen, updated_at) VALUES (999001, 1, datetime('now'));"
  sqlite3 data/owncloud.db "SELECT count(*) FROM oc_findling_scan_stats;"

  # The signed rc archive out of the release.yml dispatch named by the input.
  local dist="${RUNNER_TEMP}/rc-dist" archive sig
  mkdir -p "${dist}"
  # --dir spelled out: the -d shorthand is not known to the gh of the runner
  # (proof run 42538879801).
  gh run download "${ARCHIVE_RUN_ID}" -n store-release --dir "${dist}" --repo "${REPO}"
  archive=$(find "${dist}" -name findling.tar.gz -not -path '*source*' | sed -n '1p')
  sig=$(find "${dist}" -name findling.tar.gz.sig | sed -n '1p')
  if [ -z "${archive}" ] || [ -z "${sig}" ]; then
    fail_a6 "run ${ARCHIVE_RUN_ID} does not carry findling.tar.gz and its .sig in the store-release artifact"
  fi
  echo "archive $(wc -c < "${archive}") bytes, signature $(wc -c < "${sig}") bytes"

  # The public certificate, proven to belong to our key before it greens
  # anything (same canonical DER reading as release.yml, T-43-29).
  curl -fsSL \
    "https://github.com/nextcloud/app-certificate-requests/raw/master/findling/findling.crt" \
    -o "${RUNNER_TEMP}/findling.crt"
  local fpr
  fpr=$(openssl x509 -in "${RUNNER_TEMP}/findling.crt" -noout -pubkey \
    | openssl pkey -pubin -outform DER | openssl sha256 -r | cut -d' ' -f1)
  if [ "${fpr}" != "${FINDLING_CERT_FPR}" ]; then
    fail_a6 "the fetched certificate does not belong to the key of docs/certificates.md"
  fi
  openssl x509 -in "${RUNNER_TEMP}/findling.crt" -noout -pubkey > "${RUNNER_TEMP}/findling.pub"
  openssl base64 -d -A -in "${sig}" -out "${RUNNER_TEMP}/findling.sig.bin"
  openssl dgst -sha512 -verify "${RUNNER_TEMP}/findling.pub" \
    -signature "${RUNNER_TEMP}/findling.sig.bin" "${archive}" \
    || fail_a6 "the release signature over the rc archive does not verify"

  # Unpack, read the version out of the archive rather than trusting the
  # input, and put it over apps/findling exactly as the reporter would.
  local unpack="${RUNNER_TEMP}/rc-app" rc_version
  mkdir -p "${unpack}"
  tar -xzf "${archive}" -C "${unpack}"
  rc_version=$(read_xml_version "${unpack}/findling/appinfo/info.xml")
  if [ "${rc_version}" != "${RC_VERSION}" ]; then
    fail_a6 "the archive carries version '${rc_version}' and not ${RC_VERSION}"
  fi
  rm -rf apps/findling
  mv "${unpack}/findling" apps/findling

  echo "--- occ upgrade ---"
  timeout 300 ./occ upgrade || fail_a6 "occ upgrade went red"

  timeout 60 ./occ app:list --output=json > "${RUNNER_TEMP}/app-list.json"
  if ! grep -F -q "\"findling\":\"${RC_VERSION}\"" "${RUNNER_TEMP}/app-list.json"; then
    grep -o '"findling":"[^"]*"' "${RUNNER_TEMP}/app-list.json" || true
    fail_a6 "app:list does not show findling at ${RC_VERSION} after the upgrade"
  fi
  echo "app:list shows findling at ${RC_VERSION}"

  local migrated
  migrated=$(sqlite3 data/owncloud.db \
    "SELECT count(*) FROM oc_migrations WHERE app='findling' AND version='${MIGRATION_163}';")
  if [ "${migrated}" != "1" ]; then
    fail_a6 "the migration ${MIGRATION_163} did not run (oc_migrations holds ${migrated} rows for it)"
  fi
  echo "oc_migrations carries ${MIGRATION_163}"

  local hint
  hint=$(timeout 60 ./occ config:app:get findling coverage_per_document_hint)
  if [ "${hint}" != "1" ]; then
    fail_a6 "coverage_per_document_hint stands at '${hint}' and not at 1 although a scan row exists"
  fi
  echo "coverage_per_document_hint = 1"

  # The comparison the server itself uses for "update available", found in the
  # server checkout of this very run instead of assumed, file and line to the
  # log, then executed by php -r in exactly that operator form.
  echo "the server side version comparison, grepped out of this checkout:"
  grep -rn "version_compare" lib/private/Installer.php lib/private/App/AppStore/ \
    | tee "${RUNNER_TEMP}/server-compare.log" || true
  if [ ! -s "${RUNNER_TEMP}/server-compare.log" ]; then
    fail_a6 "no version_compare call was found in lib/private/Installer.php or lib/private/App/AppStore of this server checkout"
  fi
  compare_pair "${STORE_VERSION}" "${RC_VERSION}" fail_a6
  compare_pair "${RC_VERSION}" "${BASE_VERSION}" fail_a6

  summary "A6: ok"
  echo "A6 detail: ${BASE_VERSION} to ${RC_VERSION} upgraded, migration ran, hint flag 1, server comparison reads ${STORE_VERSION} as newer than ${RC_VERSION}"
}

# ---------------------------------------------------------------------------
# a5-harp: the HaRP deploy daemon container, the pattern of deploy-harp.yml.
# ---------------------------------------------------------------------------
a5_harp() {
  require_env HARP_IMAGE RUNNER_TEMP GITHUB_ENV
  local harp_key code i
  harp_key=$(openssl rand -hex 16)
  echo "::add-mask::${harp_key}"
  echo "HARP_SHARED_KEY=${harp_key}" >> "${GITHUB_ENV}"
  mkdir -p "${RUNNER_TEMP}/certs"
  docker run -d --name appapi-harp --net host \
    -e HP_SHARED_KEY="${harp_key}" \
    -e NC_INSTANCE_URL="http://localhost:8080" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "${RUNNER_TEMP}/certs:/certs" \
    "${HARP_IMAGE}"
  # The readiness gate is the very call AppAPI makes first; a bare TCP probe
  # answers long before HAProxy inside the container binds the port
  # (deploy-harp.yml, run 33743374344).
  for i in $(seq 1 30); do
    code=$(curl -s -o /dev/null -m 5 -w '%{http_code}' \
      -H "harp-shared-key: ${harp_key}" \
      -H 'docker-engine-port: 24000' \
      http://localhost:8780/exapps/app_api/v1.44/_ping || true)
    if [ "${code}" = "200" ]; then
      echo "harp answers the docker engine route on 8780"
      return 0
    fi
    sleep 2
  done
  echo "harp did not answer the docker engine route on 8780, last status '${code}'"
  docker logs appapi-harp || true
  exit 1
}

# ---------------------------------------------------------------------------
# a5-proxy: one address in front of Nextcloud and HaRP, the nginx of
# deploy-harp.yml: AppAPI resolves the ExApp as {nextcloud_url}/exapps/{id},
# and the container reports its status to the same base address.
# ---------------------------------------------------------------------------
a5_proxy() {
  require_env HARP_SHARED_KEY RUNNER_TEMP
  cat > "${RUNNER_TEMP}/exapps-proxy.conf" <<'CONF'
server {
  listen 8090;
  location /exapps/ {
    proxy_pass http://127.0.0.1:8780;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_read_timeout 1800s;
    proxy_send_timeout 1800s;
  }
  location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_read_timeout 300s;
    client_max_body_size 512M;
  }
}
CONF
  docker run -d --name exapps-proxy --net host \
    -v "${RUNNER_TEMP}/exapps-proxy.conf:/etc/nginx/conf.d/default.conf:ro" \
    nginx:1.27-alpine
  local i nc_code harp_code
  for i in $(seq 1 30); do
    nc_code=$(curl -s -o /dev/null -m 5 -w '%{http_code}' http://localhost:8090/status.php || true)
    harp_code=$(curl -s -o /dev/null -m 5 -w '%{http_code}' \
      -H "harp-shared-key: ${HARP_SHARED_KEY}" \
      -H 'docker-engine-port: 24000' \
      http://localhost:8090/exapps/app_api/v1.44/_ping || true)
    if [ "${nc_code}" = "200" ] && [ "${harp_code}" = "200" ]; then
      echo "the front proxy answers for Nextcloud and for HaRP"
      return 0
    fi
    sleep 2
  done
  echo "the front proxy did not serve both halves, status.php '${nc_code}' and the docker engine route '${harp_code}'"
  docker logs exapps-proxy || true
  exit 1
}

# ---------------------------------------------------------------------------
# a5-register: the HaRP daemon in AppAPI and the backend at the released
# 1.6.2, registered from the info.xml of tag v1.6.2, which pulls the public
# image :1.6.2 from ghcr.io. That is the state the reporter starts from.
# ---------------------------------------------------------------------------
a5_register() {
  require_env HARP_SHARED_KEY RUNNER_TEMP
  git -C findling-src show "v${BASE_VERSION}:backend/appinfo/info.xml" \
    > "${RUNNER_TEMP}/info-162.xml"
  local version tag
  version=$(read_xml_version "${RUNNER_TEMP}/info-162.xml")
  tag=$(read_xml_image_tag "${RUNNER_TEMP}/info-162.xml")
  echo "registration file of tag v${BASE_VERSION}: version ${version}, image-tag ${tag}"
  if [ "${version}" != "${BASE_VERSION}" ] || [ "${tag}" != "${BASE_VERSION}" ]; then
    fail_a5 "the info.xml of tag v${BASE_VERSION} does not carry ${BASE_VERSION} as version and image-tag"
  fi

  timeout 30 ./occ app_api:daemon:register \
    harp_proxy_host "Harp Proxy (Host)" docker-install http localhost:8780 \
    http://localhost:8090 \
    --harp --harp_frp_address localhost:8782 \
    --harp_shared_key "${HARP_SHARED_KEY}" \
    --net host --set-default
  timeout 30 ./occ app_api:daemon:list

  timeout 600 ./occ app_api:app:register findling_backend harp_proxy_host \
    --info-xml "${RUNNER_TEMP}/info-162.xml" --wait-finish \
    || fail_a5 "the registration of the released ${BASE_VERSION} backend went red"

  local container running
  container=$(docker ps --filter 'name=findling_backend' --format '{{.Names}}')
  if [ -z "${container}" ]; then
    docker ps -a
    fail_a5 "no running container matches findling_backend after the ${BASE_VERSION} registration"
  fi
  running=$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "${container}" \
    | sed -n 's/^APP_VERSION=//p' | sed -n '1p')
  echo "container ${container} runs APP_VERSION ${running}"
  if [ "${running}" != "${BASE_VERSION}" ]; then
    fail_a5 "the container runs APP_VERSION '${running}' and not ${BASE_VERSION}"
  fi
  timeout 60 ./occ app_api:app:list
}

# ---------------------------------------------------------------------------
# a5: the update proof on the path of the reporter, verbatim outputs.
# ---------------------------------------------------------------------------
a5_proof() {
  require_env HARP_SHARED_KEY RUNNER_TEMP RC_REF IMAGE_SHA
  check_image_sha
  case "${RC_REF}" in
    *[!A-Za-z0-9._/-]*|'') fail_a5 "RC_REF '${RC_REF}' is not a plain ref name" ;;
  esac

  # The comparison AppAPI uses on app_api:app:update, found in the AppAPI
  # checkout of this very run, file and line to the log (W7).
  echo "the AppAPI update command comparison, grepped out of apps/app_api:"
  grep -rn -E "version_compare|isUpdateAvailable|force-update" \
    apps/app_api/lib/Command/ExApp apps/app_api/lib/Service 2>/dev/null \
    | head -n 40 | tee "${RUNNER_TEMP}/appapi-compare.log" || true
  if [ ! -s "${RUNNER_TEMP}/appapi-compare.log" ]; then
    fail_a5 "no comparison call was found in apps/app_api/lib/Command/ExApp or apps/app_api/lib/Service"
  fi

  # The store side update detection of AppAPI (the list of available ExApp
  # updates out of the app store), with the narrow candidates first and the
  # whole lib tree as the fallback when a branch moved the file.
  local store_log="${RUNNER_TEMP}/appapi-store-compare.log" store_hit
  grep -rn "version_compare" \
    apps/app_api/lib/Service/ExAppArchiveFetcher.php \
    apps/app_api/lib/Fetcher \
    apps/app_api/lib/Service/AppAPIService.php 2>/dev/null \
    > "${store_log}" || true
  if [ ! -s "${store_log}" ]; then
    grep -rn "version_compare" apps/app_api/lib 2>/dev/null > "${store_log}" || true
  fi
  if [ ! -s "${store_log}" ]; then
    fail_a5 "no version_compare call was found anywhere under apps/app_api/lib"
  fi
  cat "${store_log}"
  store_hit=$(head -n 1 "${store_log}")
  echo "Store-Erkennung AppAPI: ${store_hit%%:*}:$(printf '%s' "${store_hit}" | cut -d: -f2) nutzt version_compare"

  compare_pair "${RC_VERSION}" "${BASE_VERSION}" fail_a5
  compare_pair "${STORE_VERSION}" "${RC_VERSION}" fail_a5

  # The URL form the reporter uses, letter for letter, read once up front so a
  # missing branch fails here with a sentence and not inside occ.
  local url="https://raw.githubusercontent.com/${REPO}/${RC_REF}/testbuild/findling_backend-${RC_VERSION}-info.xml"
  echo "testbuild info.xml of the reporter path: ${url}"
  curl -fsSL "${url}" -o "${RUNNER_TEMP}/testbuild-info.xml" \
    || fail_a5 "the testbuild info.xml is not reachable under ${url}"
  local tb_version tb_tag
  tb_version=$(read_xml_version "${RUNNER_TEMP}/testbuild-info.xml")
  tb_tag=$(read_xml_image_tag "${RUNNER_TEMP}/testbuild-info.xml")
  echo "testbuild info.xml carries version ${tb_version}, image-tag ${tb_tag}"
  if [ "${tb_version}" != "${RC_VERSION}" ] || [ "${tb_tag}" != "${IMAGE_SHA}" ]; then
    fail_a5 "the testbuild info.xml does not carry ${RC_VERSION} with image-tag ${IMAGE_SHA}"
  fi

  # Step one of the reporter: 1.6.2 to 1.6.3-rc.1 over the raw URL. A refusal
  # without --force-update is repeated with it, both outputs verbatim.
  local rc_force='not needed'
  if ! run_occ_update app_api:app:update findling_backend --info-xml "${url}" \
    || ! backend_listed_at "${RC_VERSION}"; then
    echo "the plain update did not land at ${RC_VERSION}, repeating with --force-update"
    rc_force='needed'
    run_occ_update app_api:app:update findling_backend --info-xml "${url}" --force-update \
      || fail_a5 "the update to ${RC_VERSION} went red even with --force-update"
    backend_listed_at "${RC_VERSION}" \
      || fail_a5 "app_api:app:list does not show ${RC_VERSION} even after --force-update"
  fi
  timeout 60 ./occ app_api:app:list
  echo "update ${BASE_VERSION} to ${RC_VERSION} over the raw URL landed, --force-update ${rc_force}"

  # The pull of the immutable image is asserted on the running container, not
  # on the pull log: the reference it runs from has to carry the input sha.
  local container image
  container=$(docker ps --filter 'name=findling_backend' --format '{{.Names}}')
  if [ -z "${container}" ]; then
    docker ps -a
    fail_a5 "no running container matches findling_backend after the rc update"
  fi
  image=$(docker inspect --format '{{.Config.Image}}' "${container}")
  echo "container ${container} runs image ${image}"
  case "${image}" in
    *"${IMAGE_SHA}"*) echo "the image reference carries the immutable tag :${IMAGE_SHA}" ;;
    *) fail_a5 "the container image '${image}' does not carry the immutable tag ${IMAGE_SHA}" ;;
  esac
  wait_for_exapp_heartbeat || fail_a5 "the ${RC_VERSION} container never answered its heartbeat"

  # Step two, the question Pitfall 6 is about: a store shaped info.xml with
  # version 1.6.3 on the SAME image is offered and applied as an update over
  # the rc. The file is the info.xml of this checkout (version 1.6.3) with
  # only the image-tag moved to the immutable sha.
  local main_version
  main_version=$(read_xml_version findling-src/backend/appinfo/info.xml)
  if [ "${main_version}" != "${STORE_VERSION}" ]; then
    fail_a5 "the checkout carries version '${main_version}' and not ${STORE_VERSION}, so no store shaped file can be built"
  fi
  sed "s|<image-tag>[^<]*</image-tag>|<image-tag>${IMAGE_SHA}</image-tag>|" \
    findling-src/backend/appinfo/info.xml > "${RUNNER_TEMP}/info-163-test.xml"
  echo "store shaped info.xml built in this run: version ${STORE_VERSION}, image-tag ${IMAGE_SHA}"

  local store_force='not needed'
  if ! run_occ_update app_api:app:update findling_backend --info-xml "${RUNNER_TEMP}/info-163-test.xml" \
    || ! backend_listed_at "${STORE_VERSION}"; then
    echo "the plain update did not land at ${STORE_VERSION}, repeating with --force-update"
    store_force='needed'
    run_occ_update app_api:app:update findling_backend --info-xml "${RUNNER_TEMP}/info-163-test.xml" --force-update \
      || fail_a5 "the update to ${STORE_VERSION} went red even with --force-update"
    backend_listed_at "${STORE_VERSION}" \
      || fail_a5 "app_api:app:list does not show ${STORE_VERSION} even after --force-update"
  fi
  timeout 60 ./occ app_api:app:list
  wait_for_exapp_heartbeat || fail_a5 "the ${STORE_VERSION} container never answered its heartbeat"
  echo "update ${RC_VERSION} to ${STORE_VERSION} applied, --force-update ${store_force}"

  summary "A5: ok"
  echo "A5 detail: ${BASE_VERSION} registered over HaRP, raw URL update to ${RC_VERSION} (--force-update ${rc_force}), store shaped ${STORE_VERSION} applied over it (--force-update ${store_force})"
}

case "$1" in
  a6-swap) a6_swap ;;
  a6) a6_proof ;;
  a5-harp) a5_harp ;;
  a5-proxy) a5_proxy ;;
  a5-register) a5_register ;;
  a5) a5_proof ;;
  *)
    echo "unknown subcommand '$1'; one of a6-swap, a6, a5-harp, a5-proxy, a5-register, a5"
    exit 1
    ;;
esac
