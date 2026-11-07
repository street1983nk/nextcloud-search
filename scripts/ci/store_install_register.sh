#!/usr/bin/env bash
# The run of the step "Store install 6, the ExApp out of the archive, image out of the registry"
# in .github/workflows/deploy-harp.yml, moved out of the workflow in plan
# 41-08 because the workflow file reached the 500 KB cap of GitHub Actions.
# It runs from the workspace root, with the environment of that step and
# the shell options of a run block (bash -e -o pipefail).
#
# The registration a store install performs, with the file a store install
# reads. --wait-finish makes the handshake synchronous, so the assertions
# that follow measure a finished installation and not a race.
#
# The info.xml comes out of the unpacked archive and from nowhere else. Not
# a preference: pre-info.xslt drops the routes block, the store database
# never sees it, and AppAPI reads it back out of this file at installation
# time. A path into findling-src here would be the warning sign of pitfall
# 8 and would turn this into a manual-install test wearing a store install
# costume.

set -eo pipefail

echo "registering with ${STORE_INFO_XML}"
grep -E '<registry>|<image>|<image-tag>' "${STORE_INFO_XML}"
"${RUNNER_TEMP}/nc-occ.sh" app_api:app:register findling_backend harp_proxy_host \
  --info-xml "${STORE_INFO_XML}" --wait-finish

container=$(docker ps --filter 'name=findling_backend' --format '{{.Names}}')
if [ -z "${container}" ]; then
  echo "no running container matches findling_backend, so the deploy daemon created nothing out of the archive"
  docker ps -a
  exit 1
fi
docker ps --filter "name=${container}" --format '{{.Names}}\t{{.Image}}\t{{.Status}}'

volume=$(docker volume ls --filter 'name=findling_backend' --format '{{.Name}}')
if [ -z "${volume}" ]; then
  echo "no volume matches findling_backend, so the archive installation has no data volume"
  docker volume ls
  exit 1
fi
echo "exapp volume: ${volume}"

# The image the container really runs, read off the container rather
# than off the registration, and compared against the reference the
# archive named. This is where an installation that quietly used some
# other image would show.
running_image=$(docker inspect --format '{{.Config.Image}}' "${container}")
echo "the container runs image ${running_image}"
# The repository path and not the whole reference, because AppAPI may
# address the image by digest once it has resolved the tag. What has to
# hold is that the image comes from the registry the archive names and
# never from localhost:5000, which is the address the developer path
# uses one pass earlier.
case "${running_image}" in
  *"${STORE_IMAGE_PATH}"*) ;;
  *)
    echo "the container runs '${running_image}' while the archive named '${STORE_IMAGE_PATH}'"
    exit 1
    ;;
esac
case "${running_image}" in
  *"${LOCAL_REGISTRY}"*)
    echo "the container runs the image of the local registry, so this pass measured the developer path again"
    exit 1
    ;;
esac

"${RUNNER_TEMP}/nc-occ.sh" app_api:app:list | tee store-app-list.txt
if ! grep -q 'findling_backend' store-app-list.txt; then
  echo "app_api:app:list does not know findling_backend, so the registration out of the archive did not survive"
  exit 1
fi

# The other half of the measurement of Store install 5, and the reason
# that step means anything: the same table, the same app, the same
# instance, one registration later with the block in place. The five
# routes of backend/appinfo/info.xml have to be there with their verbs
# and their access levels (PUBLIC 0, USER 1, ADMIN 2, see
# ExAppService::mapExAppRouteAccessLevelNameToNumber), because that is
# what "AppAPI reads the routes out of the file the registration is
# handed" means when it is measured instead of asserted. Compared as
# one string so that a missing row, a changed verb and a widened access
# level all show up as the same failure. The order comes from sort and
# not from the query, because group_concat has no defined order and a
# comparison that depends on one would be flaky rather than strict.
#
# A sixth route turns this step red, and that is the point: widening
# the reachable surface of the container is a decision, and it has to
# be made here as well as in backend/appinfo/info.xml.
routes_now=$(sqlite3 -cmd '.timeout 30000' "${FINDLING_DB}" \
  "SELECT url || ':' || verb || ':' || access_level FROM oc_ex_apps_routes WHERE appid = 'findling_backend';" \
  | sort | tr '\n' ' ' | sed -e 's/ *$//')
echo "oc_ex_apps_routes after the archive registration: ${routes_now}"

# Two comparisons and not one, and the reason is a red run of
# 2026-09-07 (run 34126702669, all three legs). Plan 06.1-19 put the
# five urls into their anchored form (DI-06.1-13), AppAPI wrote exactly
# that into the table, and this step failed anyway because the expected
# string here still spelled the bare names. The measurement was right
# and the expectation was stale, which is the one failure mode a single
# hard coded literal cannot tell apart from a real one.
#
# So the expectation is now read out of the archive that was just
# installed, and the literal stays as a second, independent question:
#
#   1. does the table match what the archive declares? That is what
#      this step was built for: AppAPI reads the routes out of the file
#      the registration is handed, and a dropped or rewritten row shows
#      here.
#   2. does the archive declare exactly the six reviewed routes? That
#      is the ratchet. A seventh route or a widened access level is a
#      decision and has to be made here as well as in
#      backend/appinfo/info.xml. A derived expectation on its own would
#      accept a widened surface without a word.
#
# Phase 27 made that decision for the two probe routes, /probe (POST)
# and /probe/state (GET), both ADMIN, which took the reviewed set from
# five to seven (run 36578517817 failed here before the literal knew).
# The content routes /search and /snippets left the list afterwards,
# seven back to five: their only caller is the companion over the
# signed path, which never reads this table, and declared with USER
# they were open to every logged in user (routes comment in
# backend/appinfo/info.xml).
#
# Plan 43-04 made that decision for /coverage (POST, ADMIN): the per
# document count of the admin page, a body of storage ids only and an
# answer of numbers only (T-43-10 to T-43-13), five to six. The first
# CI run of phase 43 (run 42378151024) failed here before the literal
# knew.
#
# The access level crosses from a name in the XML to a number in the
# table, PUBLIC 0, USER 1, ADMIN 2, see
# ExAppService::mapExAppRouteAccessLevelNameToNumber.
routes_declared=$(awk '
  /<url>/          { s = $0; sub(/.*<url>/, "", s); sub(/<\/url>.*/, "", s); url = s }
  /<verb>/         { s = $0; sub(/.*<verb>/, "", s); sub(/<\/verb>.*/, "", s); verb = s }
  /<access_level>/ { s = $0; sub(/.*<access_level>/, "", s); sub(/<\/access_level>.*/, "", s); lvl = s }
  /<\/route>/      {
    n = 2
    if (lvl == "PUBLIC") { n = 0 }
    if (lvl == "USER")   { n = 1 }
    print url ":" verb ":" n
    url = ""; verb = ""; lvl = ""
  }
' "${ARCHIVE_INFO_XML}" | sort | tr '\n' ' ' | sed -e 's/ *$//')
echo "the archive declares: ${routes_declared}"

routes_want='^/coverage$:POST:2 ^/diagnose$:GET:2 ^/probe$:POST:2 ^/probe/state$:GET:2 ^/rates$:GET:2 ^/status$:GET:2'
if [ "${routes_declared}" != "${routes_want}" ]; then
  echo "the archive declares '${routes_declared}' instead of the six reviewed routes '${routes_want}'"
  echo "widening or renaming the reachable surface of the container is a decision, and it has to be made here too"
  exit 1
fi
if [ "${routes_now}" != "${routes_declared}" ]; then
  echo "the archive registration produced '${routes_now}' while the archive declares '${routes_declared}', so the routes of the installed app are not the ones the archive declares"
  exit 1
fi
echo "the five routes of the archive arrived with their verbs and access levels, and Store install 5 measured zero rows for the same file without the block"

# The same canary call the developer path makes, and the same three
# assertions: exactly one entry, the title, and a subline that carries
# the host name and the timestamp of the process that produced it plus
# the user id that only the signed AppAPI header could have carried
# into the backend. A hard coded hit in PHP cannot pass this. What it
# does not prove, and what Store install 5 measured instead, is
# anything about the route table: the signed path does not consult it.
curl -sf -u "testuser:${TESTUSER_PASS}" \
  -H 'OCS-APIRequest: true' \
  -H 'Accept: application/json' \
  'http://localhost:8080/ocs/v2.php/search/providers/findling/search?term=findling-canary' | tee store-out.json
if ! jq -e '.ocs.data.entries | length == 1' store-out.json > /dev/null; then
  echo "the search did not return exactly one hit, so nothing answered out of the container the archive installed"
  exit 1
fi
jq -e '.ocs.data.entries[0].title == "findling-canary"' store-out.json
jq -e '.ocs.data.entries[0].subline | startswith("produced inside container ")' store-out.json
jq -e '.ocs.data.entries[0].subline | endswith("for user testuser")' store-out.json

{
  echo "STORE_CONTAINER=${container}"
  echo "STORE_VOLUME=${volume}"
} >> "${GITHUB_ENV}"
{
  echo ""
  echo "- store install container: \`${container}\`"
  echo "- store install volume: \`${volume}\`"
  echo "- image: \`${running_image}\`"
} >> "${GITHUB_STEP_SUMMARY}"
