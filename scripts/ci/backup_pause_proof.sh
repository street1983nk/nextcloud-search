#!/usr/bin/env bash
# The run of the step "Backup pause, across restarts of the backend and of Nextcloud"
# in .github/workflows/deploy-harp.yml, moved out of the workflow in plan
# 41-08 because the workflow file reached the 500 KB cap of GitHub Actions.
# It runs from the workspace root, with the environment of that step and
# the shell options of a run block (bash -e -o pipefail).
#
# =====================================================================
# The backup pause of issue #37 on a real instance (plan 41-07, D-41-05).
# docs/backup.md promises exactly what this step proves, in this order:
#
#   (1) the container and the volume carry the names the guide uses
#       (assumption A1 of 41-RESEARCH); a different name is a finding
#       about the guide, and the error names the real one
#   (2) occ findling:pause --wait ends with exit 0 and prints "Paused."
#   (3) the overview reports pause=paused and a pausedSince
#   (4) state.db-wal and vectors.db-wal are 0 bytes or absent
#   (5) the search still answers a hit for a term indexed before
#   (6) a docker restart of the backend container comes back paused
#       (unknown on the way is allowed, running never), within 120 s of
#       the overview answering again, and the indexed counter stands
#   (7) a restart of Nextcloud comes back paused as well
#   (8) a file uploaded during the pause is not indexed for 30 s, cron
#       rounds included, and the counter stands
#   (9) occ findling:resume reaches running within 60 s and the new file
#       is indexed within the budget of the language proof
#
# Nextcloud runs here as the PHP builtin server of setup-test-nc and not
# as a container, so (7) restarts that process: the pause wish lives in
# appconfig, that is in the database, and a server process that starts
# again has to read it from there like a restarted container would.
#
# ONE leg only, the reference leg stable34 on ubuntu-24.04 that the store
# upgrade steps use as well. The pause is backend and companion code that
# does not differ between server versions or architectures, the two
# restarts cost minutes, and the job cap of 45 minutes is shared with the
# store upgrade steps that run on this leg. The PHP side of the pause is
# covered on its own by PHPUnit.
#
# A trap resumes on every exit, so a red assertion here never leaves the
# later steps a paused instance. Nothing of a file's content is printed;
# the two probe files are removed again at the end.
# =====================================================================

set -eo pipefail

# The budget of the language proof: one text file of one sentence
# is indexed inside the first cron round on every leg measured so far.
BACKUP_PAUSE_BUDGET_SECONDS="${LANGUAGE_PROOF_BUDGET_SECONDS}"
work="${RUNNER_TEMP}/backup-pause"
mkdir -p "${work}"
dav='http://localhost:8080/remote.php/dav/files/testuser'
route='http://localhost:8080/ocs/v2.php/search/providers/findling/search'
term_before='qxvzjkbackupalpha'
term_during='qxvzjkbackupbravo'

resume_on_exit() {
  timeout 120 ./occ findling:resume > /dev/null 2>&1 || true
}
trap resume_on_exit EXIT

# -- (1) the names of the guide ---------------------------------------
# Read into variables first: a grep -q at the end of a pipe may end
# docker early on a broken pipe.
names=$(docker ps --format '{{.Names}}')
volumes=$(docker volume ls --format '{{.Name}}')
echo "docker ps:"
echo "${names}"
echo "docker volume ls:"
echo "${volumes}"
if ! grep -qx 'nc_app_findling_backend' <<< "${names}"; then
  echo "::error::docs/backup.md names the container nc_app_findling_backend, the running one is '${EXAPP_CONTAINER:-none}', so the guide has to be corrected (A1)"
  exit 1
fi
if ! grep -qx 'nc_app_findling_backend_data' <<< "${volumes}"; then
  echo "::error::docs/backup.md names the volume nc_app_findling_backend_data, the volume is '${EXAPP_VOLUME:-none}', so the guide has to be corrected (A1)"
  exit 1
fi
echo "A1 holds: container nc_app_findling_backend, volume nc_app_findling_backend_data"
container='nc_app_findling_backend'

# -- the admin overview, the way the language proof reads it ----------
apppw=""
if NC_PASS=password timeout 60 ./occ user:add-app-password admin \
  --password-from-env > "${work}/apppw.txt" 2>&1; then
  apppw=$(grep -oE '[A-Za-z0-9+/=._-]{40,}' "${work}/apppw.txt" | tail -1)
fi
if [ -z "${apppw}" ]; then
  apppw=$(curl -s -u admin:password -H 'OCS-APIRequest: true' \
    'http://localhost:8080/ocs/v2.php/core/getapppassword?format=json' \
    | grep -o '"apppassword":"[^"]*"' | cut -d'"' -f4 || true)
fi
rm -f "${work}/apppw.txt"
if [ -z "${apppw}" ]; then
  echo "::error::no app password could be taken, so the pause state could not be read"
  exit 1
fi
echo "::add-mask::${apppw}"

# Prints "<pause> <indexed>" or "none -" while the page does not answer.
overview() {
  local status
  status=$(curl -s -o "${work}/overview.json" -w '%{http_code}' \
    -u "admin:${apppw}" \
    -H 'OCS-APIRequest: true' \
    -H 'Accept: application/json' \
    http://localhost:8080/index.php/apps/findling/admin/overview || true)
  if [ "${status}" != "200" ]; then
    echo "none -"
    return
  fi
  jq -r '"\(.pause // "none") \(.backend.indexed // "-")"' "${work}/overview.json" 2> /dev/null || echo "none -"
}

hits() {
  curl -s -o "${work}/hits.json" \
    -u "testuser:${TESTUSER_PASS}" \
    -H 'OCS-APIRequest: true' \
    -H 'Accept: application/json' \
    "${route}?term=$1" || true
  jq -r '.ocs.data.entries | length' "${work}/hits.json" 2> /dev/null || echo 0
}

# upload <file label> <term>; the term stays out of the file name,
# so only the indexed content can answer it.
upload() {
  local status
  printf 'Backup pause probe %s.\n' "$2" > "${work}/$1.txt"
  status=$(curl -s -o /dev/null -w '%{http_code}' -T "${work}/$1.txt" \
    -u "testuser:${TESTUSER_PASS}" "${dav}/backup-probe-$1.txt")
  case "${status}" in
    201|204) echo "backup-probe-$1.txt uploaded, HTTP ${status}" ;;
    *) echo "::error::the upload of backup-probe-$1.txt answered HTTP ${status}"; exit 1 ;;
  esac
}

# Cron rounds until the term answers a hit, inside the budget.
wait_for_hit() {
  local deadline=$(( $(date +%s) + BACKUP_PAUSE_BUDGET_SECONDS ))
  local rounds=0
  while [ "$(date +%s)" -lt "${deadline}" ]; do
    rounds=$(( rounds + 1 ))
    timeout 300 php -f cron.php > "${work}/cron-$1-${rounds}.log" 2>&1 || true
    if [ "$(hits "$1")" -ge 1 ]; then
      echo "$1 answers a hit after ${rounds} cron round(s)"
      return 0
    fi
    sleep 10
  done
  return 1
}

# The paused state after a restart: unknown on the way is allowed,
# running is not, paused has to arrive within 120 s of the first
# answer. Sets seen_states and fails the step on its own.
wait_paused_after() {
  local reach=$(( $(date +%s) + 300 ))
  local first="" now line state
  seen_states=""
  while :; do
    now=$(date +%s)
    line=$(overview)
    state=${line%% *}
    if [ "${state}" != "none" ]; then
      [ -z "${first}" ] && first="${now}"
      case " ${seen_states} " in
        *" ${state} "*) ;;
        *) seen_states="${seen_states} ${state}" ;;
      esac
      if [ "${state}" = "running" ] || [ "${state}" = "unsupported" ]; then
        echo "::error::after the restart of $1 the overview reported pause=${state} (seen:${seen_states}), so the pause did not survive the restart"
        exit 1
      fi
      if [ "${state}" = "paused" ]; then
        echo "after the restart of $1: pause=paused $(( now - first ))s after the first answer, states seen:${seen_states}"
        return 0
      fi
      if [ $(( now - first )) -gt 120 ]; then
        echo "::error::after the restart of $1 the overview did not report paused within 120 s (seen:${seen_states})"
        exit 1
      fi
    elif [ "${now}" -gt "${reach}" ]; then
      echo "::error::after the restart of $1 the overview did not answer within 300 s"
      exit 1
    fi
    sleep 5
  done
}

# -- a term indexed before the pause ----------------------------------
upload before "${term_before}"
if ! wait_for_hit "${term_before}"; then
  echo "::error::${term_before} was not indexed within BACKUP_PAUSE_BUDGET_SECONDS=${BACKUP_PAUSE_BUDGET_SECONDS}, so the pause has nothing to keep"
  exit 1
fi

# -- (2) occ findling:pause --wait ------------------------------------
rc=0
timeout 1900 ./occ findling:pause --wait=1800 > "${work}/pause.txt" 2>&1 || rc=$?
cat "${work}/pause.txt"
if [ "${rc}" -ne 0 ] || ! grep -q 'Paused\.' "${work}/pause.txt"; then
  echo "::error::occ findling:pause --wait ended with exit ${rc} and without 'Paused.'"
  exit 1
fi
echo "occ findling:pause --wait: exit 0, Paused."

# -- (3) the overview reports paused ----------------------------------
line=$(overview)
since=$(jq -r '.pausedSince // empty' "${work}/overview.json" 2> /dev/null || true)
if [ "${line%% *}" != "paused" ] || ! [[ "${since}" =~ ^[0-9]+$ ]]; then
  echo "::error::the overview reports pause='${line%% *}' and pausedSince='${since}' instead of paused and a time"
  exit 1
fi
indexed_paused="${line#* }"
echo "overview: pause=paused, pausedSince=${since}, indexed=${indexed_paused}"

# -- (4) nothing left in the write-ahead logs -------------------------
docker exec "${container}" sh -c '
  cd "${APP_PERSISTENT_STORAGE}" || exit 1
  for f in state.db-wal vectors.db-wal; do
    if [ -e "$f" ]; then echo "$f $(stat -c %s "$f")"; else echo "$f absent"; fi
  done' > "${work}/wal.txt"
cat "${work}/wal.txt"
if [ "$(wc -l < "${work}/wal.txt")" -ne 2 ] \
  || grep -vqE '^(state|vectors)\.db-wal (0|absent)$' "${work}/wal.txt"; then
  echo "::error::a write-ahead log is not empty while paused, so a copy now would not be consistent"
  exit 1
fi
echo "wal: state.db-wal and vectors.db-wal are empty or absent"

# -- (5) search keeps working -----------------------------------------
if [ "$(hits "${term_before}")" -lt 1 ]; then
  echo "::error::the search for ${term_before} answers no hit while paused"
  exit 1
fi
echo "search while paused: ${term_before} answers a hit"

# -- (6) restart of the backend container -----------------------------
docker restart "${container}" > /dev/null
echo "docker restart ${container}"
wait_paused_after "the backend container"
line=$(overview)
if [ "${line#* }" != "${indexed_paused}" ]; then
  echo "::error::the indexed counter moved from ${indexed_paused} to ${line#* } across the container restart while paused"
  exit 1
fi
echo "pause after the container restart: paused, indexed still ${indexed_paused}"

# -- (7) restart of Nextcloud -----------------------------------------
pkill -f 'php -S 0.0.0.0:8080' || true
for _ in $(seq 1 30); do
  curl -sf http://localhost:8080/status.php > /dev/null || break
  sleep 1
done
NEXTCLOUD_HOST=0.0.0.0 nohup composer run serve > "${work}/serve.log" 2>&1 &
up=""
for _ in $(seq 1 60); do
  if curl -sf http://localhost:8080/status.php > /dev/null; then
    up="yes"
    break
  fi
  sleep 2
done
if [ -z "${up}" ]; then
  echo "::error::Nextcloud did not answer within 120 s after its restart"
  tail -n 20 "${work}/serve.log" || true
  exit 1
fi
echo "Nextcloud restarted"
wait_paused_after "Nextcloud"
echo "pause after the Nextcloud restart: paused"

# -- (8) a new file waits ---------------------------------------------
upload during "${term_during}"
end=$(( $(date +%s) + 30 ))
while [ "$(date +%s)" -lt "${end}" ]; do
  timeout 120 php -f cron.php > /dev/null 2>&1 || true
  line=$(overview)
  if [ "${line%% *}" != "paused" ] || [ "${line#* }" != "${indexed_paused}" ] \
    || [ "$(hits "${term_during}")" -ne 0 ]; then
    echo "::error::during the pause the overview reads '${line}' and ${term_during} answers $(hits "${term_during}") hit(s), expected paused ${indexed_paused} and none"
    exit 1
  fi
  sleep 5
done
echo "pause held 30 s with a new file: indexed still ${indexed_paused}, no hit for ${term_during}"

# -- (9) resume -------------------------------------------------------
timeout 120 ./occ findling:resume | tee "${work}/resume.txt"
running=""
for _ in $(seq 1 12); do
  line=$(overview)
  if [ "${line%% *}" = "running" ]; then
    running="yes"
    break
  fi
  sleep 5
done
if [ -z "${running}" ]; then
  echo "::error::after occ findling:resume the overview reports pause='${line%% *}' instead of running within 60 s"
  exit 1
fi
echo "pause after resume: running"
if ! wait_for_hit "${term_during}"; then
  echo "::error::${term_during} was not indexed within BACKUP_PAUSE_BUDGET_SECONDS=${BACKUP_PAUSE_BUDGET_SECONDS} after the resume"
  exit 1
fi
echo "resume: the file uploaded during the pause is indexed"

for name in before during; do
  curl -s -o /dev/null -X DELETE -u "testuser:${TESTUSER_PASS}" "${dav}/backup-probe-${name}.txt" || true
done
{
  echo "### Backup pause on ${MATRIX_SERVER_VERSION} / ${MATRIX_RUNNER}"
  echo ""
  echo "- container \`nc_app_findling_backend\`, volume \`nc_app_findling_backend_data\` (A1)"
  echo "- pause --wait: Paused., WAL empty or absent, search answered"
  echo "- paused after the backend restart and after the Nextcloud restart, counter ${indexed_paused}"
  echo "- resume: running, the new file indexed"
} >> "${GITHUB_STEP_SUMMARY}"
