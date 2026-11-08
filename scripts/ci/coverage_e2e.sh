#!/usr/bin/env bash
# Coverage end to end (plan 43-07, D-43-08, D-43-11, D-43-14, issue #25).
#
# The three earlier fixes of #25 were green in their parts and wrong in the
# figure an admin reads. This run measures that figure, on a real Nextcloud
# with a real Samba server, against a truth computed without Findling code
# (scripts/ci/coverage_truth.sh).
#
# Topology, the same in every variant:
#   - Samba on the runner, two shares (daten, archiv) with acl_xattr, users
#     aaron, alice, bob, carol, dave. Sub folders with Unix rights, so that
#     alice, bob and carol each see something the others do not and nobody
#     sees everything; a positive control at the Samba server comes first.
#   - The same file name on both shares (two documents), documents only in
#     the folder of a member that is not the largest one, one file of a type
#     nobody reads on each share, one file locked for every user by a DENY
#     ACE (listed, not readable: D-43-11) and one locked for bob only (N1).
#     A stuck file (failed/repeatedly_stuck) is not built: it cannot be made
#     without touching Findling code, the PHPUnit of 43-05 carries that side.
#   - One storage configuration per share with log-in credentials, a second
#     configuration of archiv at another mount point for carol, a local
#     storage with a file nobody reads (B1), and the folder daten/projekt
#     shared by alice to aaron, who sorts before alice and becomes the reader
#     of the files of her storage, while bob sees the same folder through his
#     own mount (A1, N2).
#   - After indexing: carol loses the daten configuration (oc_storages keeps
#     the row: stamped), dave is deleted (no oc_storages row: gone), the
#     local storage is removed.
#
# Variants (VARIANT):
#   gate-crawl  head, the crawl is unfinished during phase A
#   gate-queue  head, the crawl is done and scheduled >= quiet_max in phase A
#   v1.6.2      the released 1.6.2 on the same topology, positive control 2
#   upgrade     indexed by 1.6.2, then updated to the head (doc key backfill,
#               one container row without a file cache row), the gate-queue
#               proof, then back to 1.6.2 and up again with a rename (W5, G1)
#
# SMB modes (SMB_MODE, plan 43-18, owner decision F3): wrapped, icewind/smb
# drives the smbclient binary; native, the php-smbclient extension. The leg
# proves its mode with function_exists('smbclient_state_new') before anything
# is counted, a leg in the wrong mode is an invalid run.
#
# Runs from the root of the Nextcloud server checkout. Expects VARIANT,
# SMB_MODE, NC_URL, HARNESS (checkout of the head), SRC (checkout the instance
# was set up from), RESULT_FILE, EXAPP_SECRET, EXAPP_PORT, RUNNER_TEMP.
# Passwords are fixed test values of a throwaway runner and are never printed.

set -euo pipefail

: "${VARIANT:?VARIANT is required}"
: "${SMB_MODE:?SMB_MODE is required}"
: "${NC_URL:?NC_URL is required}"
: "${HARNESS:?HARNESS is required}"
: "${SRC:?SRC is required}"
: "${RESULT_FILE:?RESULT_FILE is required}"
: "${EXAPP_SECRET:?EXAPP_SECRET is required}"
: "${EXAPP_PORT:?EXAPP_PORT is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"

case "${VARIANT}" in
  gate-crawl | gate-queue | v1.6.2 | upgrade) ;;
  *)
    echo "::error::unknown variant ${VARIANT}"
    exit 1
    ;;
esac
case "${SMB_MODE}" in
  wrapped | native) ;;
  *)
    echo "::error::unknown smb mode ${SMB_MODE}"
    exit 1
    ;;
esac

SERVER_ROOT="${PWD}"
WORK="${RUNNER_TEMP}/coverage-e2e"
NC_DATA="${SERVER_ROOT}/data"
NC_DB="${NC_DATA}/owncloud.db"
STATE_DB="${RUNNER_TEMP}/findling/state.db"
EXAPP_LOG="${RUNNER_TEMP}/exapp.log"
EXAPP_PID="${RUNNER_TEMP}/exapp.pid"
NETBIOS=DECKUNG
RELEASE_COMPANION_URL='https://github.com/street1983nk/nextcloud-search/releases/download/v1.6.2/findling.tar.gz'
BACKLOG_IMAGES=30
DRAIN_TIMEOUT=1500
SWEEP_TIMEOUT=240
# The backend the instance runs right now; the upgrade variant moves it.
BACKEND_DIR="${SRC}/backend"

mkdir -p "${WORK}"
# One collation for sort and comm everywhere.
export LC_ALL=C
umask 022

failures=0
rows=()
notes=()
# The two figures of a 1.6.2 companion that may not drain (see drain).
outage_abort_tolerated=0
drain_incomplete=0

fail() {
  echo "::error::$*"
  write_result || true
  exit 1
}

step() {
  echo "--- $* ---"
}

note() {
  echo "$*"
  notes+=("$*")
}

# check <name> <expected> <shown>: compare and count, never stop the run.
check() {
  if ! compare "$1" "$2" "$3"; then
    failures=$((failures + 1))
  fi
}

password_of() {
  case "$1" in
    admin) printf '%s' 'password' ;;
    aaron) printf '%s' 'Deckung-aaron-43-q7' ;;
    alice) printf '%s' 'Deckung-alice-43-x4' ;;
    bob) printf '%s' 'Deckung-bob-43-m2' ;;
    carol) printf '%s' 'Deckung-carol-43-k9' ;;
    dave) printf '%s' 'Deckung-dave-43-v5' ;;
    *) fail "no test password for $1" ;;
  esac
}

nc_occ() {
  timeout 300 ./occ "$@"
}

# shellcheck source=scripts/ci/coverage_truth.sh
source "${HARNESS}/scripts/ci/coverage_truth.sh"

head_under_test() {
  [ "${VARIANT}" != "v1.6.2" ]
}

# head_companion: the PHP half of the head answers the gateway right now. True
# for gate-crawl and gate-queue, for upgrade only between an update to the
# head and the rollback (companion_updated), never for v1.6.2. The probes and
# the verdicts of plan 43-18 depend on it: the container of 1.6.2 judges a 422
# failed/gateway_error. The empty file is no tell, both companions answer it
# with 200 and zero bytes (run 42418778026).
companion_updated=0
head_companion() {
  case "${VARIANT}" in
    gate-crawl | gate-queue) return 0 ;;
    upgrade) [ "${companion_updated}" = "1" ] ;;
    *) return 1 ;;
  esac
}

# -- words --------------------------------------------------------------------

# Every file of the corpus carries one word of its own, ten letters without
# the shapes OCR confuses (no i, l, o), far apart from each other in edit
# distance, so neither a fuzzy match nor a stemmer can make one word find a
# second file.
#
# next_word puts the word into NEXT_WORD and prints nothing. It must never run
# as $(next_word): a command substitution is a subshell, the increment of
# word_count stays there, and every file got the same word (since a5182e98,
# run 42425348629, 43-DEBUG-SUCHE.md). words_unique holds the run to it.
WORDS="${WORK}/words.tsv"
: > "${WORDS}"
word_count=0
NEXT_WORD=""
next_word() {
  local hex letters='abcdefghjkmnpqrs' word='zq' i
  word_count=$((word_count + 1))
  hex=$(printf 'coverage-43-07-%s' "${word_count}" | sha256sum | cut -c1-8)
  for ((i = 0; i < 8; i++)); do
    word+="${letters:$((16#${hex:i:1})):1}"
  done
  NEXT_WORD="${word}"
}

# words_unique <label>: no word twice in WORDS, otherwise the search cross
# check counts ranks of one shared word and not files.
words_unique() {
  local twice lines distinct
  twice=$(cut -f1 "${WORDS}" | sort | uniq -d | tr '\n' ' ')
  [ -z "${twice// /}" ] || fail "$1: words used for more than one file: ${twice}"
  lines=$(wc -l < "${WORDS}")
  distinct=$(cut -f1 "${WORDS}" | sort -u | wc -l)
  [ "${lines}" -gt 1 ] && [ "${lines}" -eq "${distinct}" ] \
    || fail "$1: ${distinct} distinct words for ${lines} files"
  note "$1: ${lines} files, ${distinct} distinct words"
}

# samba_file <share> <relative path> [extra word]: a text file written by root.
samba_file() {
  local word
  next_word
  word="${NEXT_WORD}"
  printf 'Coverage proof %s %s\n' "${word}" "${3:-}" | sudo tee "/srv/$1/$2" > /dev/null
  sudo chmod 0644 "/srv/$1/$2"
  printf '%s\t%s\n' "${word}" "$(basename "$2")" >> "${WORDS}"
}

# -- Nextcloud helpers ----------------------------------------------------------

dav() {
  # dav <uid> <method> <path> <outfile> [extra curl args]: prints the HTTP status
  local uid="$1" method="$2" path="$3" outfile="$4"
  shift 4
  curl -s --max-time 120 -o "${outfile}" -w '%{http_code}' -u "${uid}:$(password_of "${uid}")" -X "${method}" "$@" \
    "${NC_URL}/remote.php/dav/files/${uid}/${path}"
}

login() {
  local code
  code=$(dav "$1" PROPFIND "" "${WORK}/login-$1.xml" -H 'Depth: 1' || true)
  [ "${code}" = "207" ] || fail "the PROPFIND of $1 answered HTTP ${code}"
}

ncdb() {
  sqlite3 -readonly "${NC_DB}" "$1"
}

statedb() {
  sqlite3 -readonly "${STATE_DB}" "$1"
}

sid_like() {
  ncdb "SELECT numeric_id FROM oc_storages WHERE id LIKE '$1' ORDER BY numeric_id LIMIT 1;"
}

mounted_sid() {
  [ "$(ncdb "SELECT COUNT(*) FROM oc_mounts WHERE storage_id = $1;")" -gt 0 ]
}

open_rows() {
  nc_occ findling:index | awk '
    $1 == "scheduled" { scheduled = $2 }
    /^  handed to the worker/ { running = $NF }
    END { print (scheduled + 0) + (running + 0) }'
}

CRAWL_SQL="SELECT COUNT(*) FROM oc_jobs
  WHERE class = 'OCA\\Findling\\BackgroundJobs\\SchedulerJob'
     OR (class = 'OCA\\Findling\\BackgroundJobs\\StorageCrawlJob' AND argument NOT LIKE '%recount%');"
crawl_pending() {
  ncdb "${CRAWL_SQL}"
}

run_crawl() {
  timeout 120 ./occ background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once || true
  local round
  for round in $(seq 1 30); do
    [ "$(crawl_pending)" = "0" ] && return 0
    timeout 240 ./occ background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop_after 60 || true
  done
  [ "$(crawl_pending)" = "0" ] || fail "the crawl did not end after ${round} worker runs"
}

living_rows() {
  statedb "SELECT COUNT(*) FROM files WHERE deleted_at IS NULL;" 2> /dev/null || echo 0
}

# drain: queue empty, no crawl row, and the state database still for 20 s.
#
# Behind a 1.6.2 companion (v1.6.2, and upgrade before the update) an abort
# is the expected answer and no failure (plan 43-18): 1.6.2 counts a 422
# towards its outage threshold (poller.py of 1.6.2, _count_refusal), so a pass
# may end as an outage. There the abort after three outages becomes the note
# outage_abort_tolerated=<lines>, the drain goes on until DRAIN_TIMEOUT and
# ends there with drain_incomplete=1 instead of a failure, and the run goes on
# to its next phase; positive control 2 still reads the figures. Behind the
# head companion both stay failures.
drain() {
  local deadline=$(($(date +%s) + DRAIN_TIMEOUT)) open crawl last="" now mark outages tolerant=0
  head_companion || tolerant=1
  mark=$(log_mark)
  while :; do
    # Three passes stopped on an unavailable gateway: nothing drains after
    # that, the report says why instead of the timeout.
    outages=$(log_since "${mark}" | grep -c 'the content gateway is unavailable' || true)
    if [ "${outages}" -ge 3 ] && [ "${tolerant}" = "0" ]; then
      hang_report
      fail "the content gateway stopped ${outages} indexing passes, the queue cannot drain"
    fi
    open=$(open_rows)
    crawl=$(crawl_pending)
    now="$(living_rows)/$(statedb "SELECT COALESCE(MAX(indexed_at), 0) || ':' || COUNT(*) FROM files;" 2> /dev/null || echo -)"
    echo "draining: open=${open} crawl=${crawl} state=${now} outages=${outages}"
    if [ "${open}" = "0" ] && [ "${crawl}" = "0" ] && [ "${now}" = "${last}" ]; then
      drain_tolerated "${tolerant}" "${outages}"
      return 0
    fi
    last="${now}"
    if [ "$(date +%s)" -ge "${deadline}" ]; then
      if [ "${tolerant}" = "1" ]; then
        drain_tolerated "${tolerant}" "${outages}"
        drain_incomplete=1
        note "drain_incomplete=1 (a 1.6.2 companion, the queue did not drain within ${DRAIN_TIMEOUT} s, open=${open})"
        return 0
      fi
      fail "the queue did not drain within ${DRAIN_TIMEOUT} s"
    fi
    sleep 20
  done
}

# drain_tolerated <tolerant> <outage lines>: the note of a tolerated abort.
drain_tolerated() {
  if [ "$1" = "1" ] && [ "$2" -ge 3 ]; then
    outage_abort_tolerated=$((outage_abort_tolerated + $2))
    note "outage_abort_tolerated=$2 (a 1.6.2 companion, counted towards its outage threshold)"
  fi
}

# -- the admin overview ------------------------------------------------------------

apppw=""
take_app_password() {
  if OC_PASS=password timeout 60 ./occ user:add-app-password admin --password-from-env > "${WORK}/apppw.txt" 2>&1; then
    apppw=$(grep -oE '[A-Za-z0-9+/=._-]{40,}' "${WORK}/apppw.txt" | tail -1 || true)
  fi
  rm -f "${WORK}/apppw.txt"
  [ -n "${apppw}" ] || fail "no app password could be taken for the admin overview"
  echo "::add-mask::${apppw}"
}

overview() {
  local status
  status=$(curl -s --max-time 120 -o "${WORK}/overview.json" -w '%{http_code}' \
    -u "admin:${apppw}" -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
    "${NC_URL}/index.php/apps/findling/admin/overview" || true)
  [ "${status}" = "200" ]
}

cov() {
  jq -r "$1" "${WORK}/overview.json"
}

# signature: what would change the figures between two reads.
signature() {
  printf '%s|%s|%s' \
    "$(statedb "SELECT COUNT(*) || ':' || COALESCE(SUM(state = 'indexed'), 0) || ':' || COALESCE(MAX(indexed_at), 0) FROM files WHERE deleted_at IS NULL;" 2> /dev/null || echo -)" \
    "$(ncdb "SELECT COUNT(*) FROM oc_findling_file_state;" 2> /dev/null || echo -)" \
    "$(ncdb "SELECT COALESCE(SUM(files_seen), 0) FROM oc_findling_scan_stats;" 2> /dev/null || echo -)"
}

# read_settled <label>: an overview read with the same state before and after
# it, and, for the head, a finished per document count. Leaves the overview in
# ${WORK}/overview-<label>.json and the snapshots in SNAP_NC/SNAP_ST.
read_settled() {
  local label="$1" try before after counting
  for try in $(seq 1 60); do
    before=$(signature)
    if overview; then
      after=$(signature)
      counting=$(cov '.coverage.counting // false')
      if [ "${before}" = "${after}" ] && { ! head_under_test || [ "${counting}" = "false" ]; }; then
        snapshot_dbs "${label}"
        if [ "$(signature)" = "${after}" ]; then
          cp "${WORK}/overview.json" "${WORK}/overview-${label}.json"
          return 0
        fi
      fi
    fi
    sleep 5
  done
  fail "no settled overview for ${label} within five minutes"
}

# -- the container ----------------------------------------------------------------

backend_version() {
  sed -n 's:.*<version>\(.*\)</version>.*:\1:p' "$1/appinfo/info.xml" | head -n 1
}

stop_backend() {
  local pid
  pid=$(cat "${EXAPP_PID}" 2> /dev/null || true)
  [ -n "${pid}" ] || return 0
  kill -TERM "${pid}" 2> /dev/null || true
  for _ in $(seq 1 90); do
    kill -0 "${pid}" 2> /dev/null || return 0
    sleep 1
  done
  kill -9 "${pid}" 2> /dev/null || true
  sleep 2
}

# start_backend <backend dir> [NAME=value ...]: started directly and not
# through uv, so the pid is the server (see setup-test-nc), then armed again
# through AppAPI the way resilience.yml does it.
start_backend() {
  local dir="$1" py version
  shift
  (cd "${dir}" && uv sync --frozen > /dev/null)
  py=$(cd "${dir}" && uv run --frozen python -c 'import sys; print(sys.executable)')
  version=$(backend_version "${dir}")
  (
    cd "${dir}"
    export APP_ID=findling_backend
    export APP_SECRET="${EXAPP_SECRET}"
    export APP_PORT="${EXAPP_PORT}"
    export APP_VERSION="${version}"
    export APP_HOST=127.0.0.1
    export NEXTCLOUD_URL="${NC_URL}"
    export APP_PERSISTENT_STORAGE="${RUNNER_TEMP}/findling"
    local assignment
    for assignment in "$@"; do
      export "${assignment?}"
    done
    exec "${py}" -m findling.main >> "${EXAPP_LOG}" 2>&1
  ) &
  echo $! > "${EXAPP_PID}"
  BACKEND_DIR="${dir}"
  for _ in $(seq 1 60); do
    if curl -sf "http://127.0.0.1:${EXAPP_PORT}/heartbeat" > /dev/null; then
      nc_occ app_api:app:disable findling_backend > /dev/null
      nc_occ app_api:app:enable findling_backend > /dev/null
      echo "backend ${version} out of ${dir} answers and is armed"
      return 0
    fi
    sleep 1
  done
  tail -n 50 "${EXAPP_LOG}" || true
  fail "the backend out of ${dir} did not come up"
}

log_mark() {
  wc -l < "${EXAPP_LOG}"
}

log_since() {
  tail -n +"$(($1 + 1))" "${EXAPP_LOG}"
}

# -- diagnosis of a hanging content gateway -----------------------------------------

# The second dispatch (run 42394655350) drained nothing on all four variants:
# every gateway call of the backend ran into its read timeout, and after that
# the pause wish and the queue as well, so all workers of php -S were taken.
# These helpers say which request hangs before the drain waits 25 minutes.
PHP_SERVER_LOG="${RUNNER_TEMP}/php-server.log"

hang_report() {
  echo "--- processes (smbclient, php) ---"
  ps -eo pid,etimes,stat,args | grep -E 'smbclient|php' | grep -v grep || echo "none"
  echo "--- connections to 8080 ---"
  ss -tn state established '( sport = :8080 )' 2> /dev/null | tail -n +2 | wc -l
  echo "--- php extensions (smbclient) ---"
  php -m | grep -i smbclient || echo "no smbclient extension, icewind/smb drives the smbclient binary"
  echo "--- file ids next to the hanging fetch (test files only) ---"
  ncdb "SELECT fileid || ' ' || storage || ' ' || path FROM oc_filecache WHERE fileid BETWEEN 80 AND 110 ORDER BY fileid;" || true
  echo "--- php -S, last lines ---"
  tail -n 60 "${PHP_SERVER_LOG}" 2> /dev/null || echo "no php server log"
}

# The time a probe may take (plan 43-18, B2). The nudge of the head companion
# ends smbclient in under one second, and the product deadline of 80 s must
# never be the answer here; a probe at or over this limit is a failure. Not for
# gross.bin, which is slow on purpose (large_probe).
PROBE_MAX_SECONDS=10
probe_failures=0
# The file id of gemeinsam/leer.txt of alice, set before the probes.
leer_fid=""

# gateway_curl <uid> <file id> <outfile> <max seconds>: one fetch the way the
# backend does it. Prints "<status> <seconds> <bytes>", 000 when curl gave up.
gateway_curl() {
  local uid="$1" fid="$2" outfile="$3" max="$4" auth
  auth=$(printf '%s:%s' "${uid}" "${EXAPP_SECRET}" | base64 -w0)
  curl -s -m "${max}" -o "${outfile}" -w '%{http_code} %{time_total} %{size_download}' \
    -H 'AA-VERSION: 2.2.0' \
    -H 'EX-APP-ID: findling_backend' \
    -H "EX-APP-VERSION: $(backend_version "${BACKEND_DIR}")" \
    -H "AUTHORIZATION-APP-API: ${auth}" \
    -H 'OCS-APIRequest: true' \
    "${NC_URL}/ocs/v2.php/apps/findling/files/${fid}?userId=${uid}" || true
}

# probe_problem <label> <problem> [collect]: without collect the run stops at
# once with the hang report (a worker of php -S that hangs stays taken after
# curl gives up); with collect the problem is counted in probe_failures and
# the next probe still runs, the run stops after all of them.
probe_problem() {
  if [ "${3:-}" = "collect" ]; then
    probe_failures=$((probe_failures + 1))
    echo "::warning::gateway probe $1: $2"
    return 0
  fi
  hang_report
  fail "gateway probe $1: $2"
}

# gateway_probe <label> <uid> <file id> <expected status> [collect]: one fetch
# that must answer the expected status in under PROBE_MAX_SECONDS; for
# leer.txt it must also carry zero bytes, from either companion.
gateway_probe() {
  local label="$1" uid="$2" fid="$3" expected="$4" mode="${5:-}" result code seconds size problem=""
  [ -n "${fid}" ] || fail "gateway probe ${label}: no file id"
  result=$(gateway_curl "${uid}" "${fid}" /dev/null 60)
  read -r code seconds size <<< "${result:-000 0 0}"
  note "gateway probe ${label} (file ${fid}, ${uid}): http ${code}, ${seconds} s, ${size} bytes, expected ${expected}"
  rows+=("| probe | ${label} (${uid}) | ${expected} | ${code} in ${seconds} s |")
  [ "${code}" = "${expected}" ] || problem="http ${code} instead of ${expected}"
  if awk -v took="${seconds}" -v limit="${PROBE_MAX_SECONDS}" 'BEGIN { exit !(took + 0 >= limit + 0) }'; then
    problem="${problem:+${problem}, }${seconds} s, the limit is ${PROBE_MAX_SECONDS} s"
  fi
  if [ "${fid}" = "${leer_fid}" ] && [ "${size}" != "0" ]; then
    problem="${problem:+${problem}, }${size} bytes for the empty file"
  fi
  [ -z "${problem}" ] || probe_problem "${label}" "${problem}" "${mode}"
}

# throttle_smb <rate> / unthrottle_smb: SMB traffic on 127.0.0.1:445 (both
# directions) down to the given tc rate, one htb class with a filter on the
# port, everything else on lo unshaped. The EXIT trap removes it in every case.
#
# Two limits decide the rate. smbclient hands a get on in whole SMB2 read
# blocks of 8 MiB (Samba source3/libsmb/clireadwrite.c:363-366), and
# icewind/smb starts smbclient with -t 20 (3rdparty/icewind/smb/src/Options.php:14,
# raised only through the storage option timeout,
# apps/files_external/lib/Lib/Storage/SMB.php:103-106): one block has to
# arrive within those 20 s, so the default storage needs about 420 KB/s
# (run 42425348629: 422 after 60 s at 200 KB/s). Below that the remedy is the
# option timeout or php-smbclient.
#
# THROTTLE_RATE, about 1 MB/s: a block in about 8.4 s, inside the 20 s of a
# default storage, and still a silence of seconds before the first data and
# between the two blocks of gross.bin.
# THROTTLE_RATE_SLOW, about 200 KB/s: a block in about 42 s, past the 20 s,
# inside the 80 s deadlines of the gateway; fetched with timeout=120 on the
# storage, which proves the remedy for an admin (large_probe_long).
THROTTLE_RATE=8mbit
THROTTLE_RATE_SLOW=1600kbit
throttle_smb() {
  local rate="$1"
  sudo tc qdisc add dev lo root handle 1: htb default 10 || return 1
  sudo tc class add dev lo parent 1: classid 1:10 htb rate 10gbit \
    && sudo tc class add dev lo parent 1: classid 1:20 htb rate "${rate}" ceil "${rate}" \
    && sudo tc filter add dev lo parent 1: protocol ip prio 1 u32 match ip dport 445 0xffff flowid 1:20 \
    && sudo tc filter add dev lo parent 1: protocol ip prio 1 u32 match ip sport 445 0xffff flowid 1:20 \
    || {
      unthrottle_smb
      return 1
    }
}
unthrottle_smb() {
  sudo tc qdisc del dev lo root 2> /dev/null || true
}
trap unthrottle_smb EXIT

# large_fetch <label> <file id> <rate> <min seconds> <max seconds> [collect]:
# gross.bin (10 MiB) through the gateway while SMB is throttled (W1, W1b), so
# pauses of up to 200 ms and many empty reads really happen in the wrapped
# mode. 200, the bytes equal to the source, no hang; the number of reads
# against MAX_READS is the PHPUnit case of 43-17. A throttled fetch under the
# minimum did not wait for a whole block, so the throttle did not work and the
# probe tested no silence. curl gives up at the maximum.
large_fetch() {
  local label="$1" fid="$2" rate="$3" floor="$4" max="$5" mode="${6:-}"
  local want have result code seconds size throttled=0 problem=""
  [ -n "${fid}" ] || fail "gateway probe ${label}: no file id"
  want=$(sudo sha256sum /srv/daten/gemeinsam/gross.bin | cut -d' ' -f1)
  if throttle_smb "${rate}"; then
    throttled=1
  else
    note "tc could not throttle port 445 on lo, gross.bin runs unthrottled (${label})"
  fi
  result=$(gateway_curl alice "${fid}" "${WORK}/gross.out" "${max}")
  unthrottle_smb
  read -r code seconds size <<< "${result:-000 0 0}"
  have=$(sha256sum "${WORK}/gross.out" 2> /dev/null | cut -d' ' -f1 || true)
  rm -f "${WORK}/gross.out"
  note "gateway probe ${label} (file ${fid}, alice, ${rate}): http ${code}, ${seconds} s, ${size} bytes, throttled=${throttled}, sha256 $([ "${have}" = "${want}" ] && echo equal || echo different)"
  rows+=("| probe | ${label} gross.bin (alice), ${rate}, throttled=${throttled} | 200, same sha256, ${floor} to ${max} s | ${code} in ${seconds} s |")
  [ "${code}" = "200" ] || problem="http ${code} instead of 200"
  [ "${have}" = "${want}" ] || problem="${problem:+${problem}, }the bytes differ from the source"
  if [ "${throttled}" = "1" ] \
    && awk -v took="${seconds}" -v floor="${floor}" 'BEGIN { exit !(took + 0 < floor + 0) }'; then
    problem="${problem:+${problem}, }${seconds} s throttled, under ${floor} s, so the throttle did not hold back a block"
  fi
  [ -z "${problem}" ] || probe_problem "${label}" "${problem}" "${mode}"
}

# large_probe <file id> [collect]: the default storage (smbclient -t 20) at
# about 1 MB/s. 10 MiB are about 10.5 s; 8 s is under a single 8 MiB block at
# that rate (8.4 s), and an unthrottled fetch takes well under a second.
# 60 s leave room for the 20 s of each of the two blocks.
LARGE_MIN_SECONDS=8
LARGE_MAX_SECONDS=60
large_probe() {
  large_fetch large "$1" "${THROTTLE_RATE}" "${LARGE_MIN_SECONDS}" "${LARGE_MAX_SECONDS}" "${2:-}"
}

# large_probe_long <file id> <mount id> [collect]: the remedy for a slow line.
# The storage gets the backend option timeout=120 (files_external:config, the
# option is hidden in the web form), smbclient then waits 120 s per
# operation, and gross.bin at about 200 KB/s must arrive whole: 10 MiB in
# about 52 s, a block in about 42 s, so under 40 s the throttle did not work.
# The option is cleared afterwards (an empty value is no timeout,
# SMB.php:103-106), so the crawl runs with the default of a fresh storage.
LONG_TIMEOUT_SECONDS=120
LARGE_LONG_MIN_SECONDS=40
LARGE_LONG_MAX_SECONDS=150
large_probe_long() {
  local fid="$1" mid="$2" mode="${3:-}" set_to
  [ -n "${mid}" ] || fail "gateway probe large-long: no mount id"
  nc_occ files_external:config "${mid}" timeout "${LONG_TIMEOUT_SECONDS}" > /dev/null \
    || fail "files_external:config could not set the timeout of mount ${mid}"
  set_to=$(nc_occ files_external:config "${mid}" timeout | tr -d '\r\n ')
  [ "${set_to}" = "${LONG_TIMEOUT_SECONDS}" ] \
    || fail "the timeout of mount ${mid} reads '${set_to}' instead of ${LONG_TIMEOUT_SECONDS}, the remedy probe tests nothing"
  note "mount ${mid}: backend option timeout=${set_to} for large-long"
  large_fetch large-long "${fid}" "${THROTTLE_RATE_SLOW}" "${LARGE_LONG_MIN_SECONDS}" "${LARGE_LONG_MAX_SECONDS}" "${mode}"
  nc_occ files_external:config "${mid}" timeout "" > /dev/null \
    || fail "files_external:config could not clear the timeout of mount ${mid}"
  set_to=$(nc_occ files_external:config "${mid}" timeout | tr -d '\r\n ')
  [ -z "${set_to}" ] || fail "the timeout of mount ${mid} still reads '${set_to}' after the remedy probe"
}

# no_stale_smbclient <label>: no smbclient process below a php -S process older
# than 60 s (W12). The parents are the php -S processes of composer run serve
# (pgrep -f 'php -S', the workers carry the command line of their master).
# Below and not only directly below: icewind/smb starts the binary through
# proc_open, so a shell or stdbuf may sit in between.
no_stale_smbclient() {
  local label="$1" parents stale
  parents=$(pgrep -f 'php -S' | tr '\n' ' ' || true)
  [ -n "${parents// /}" ] || fail "no php -S process found, the check for a stale smbclient tests nothing"
  stale=$(ps -eo pid=,ppid=,etimes=,comm= | awk -v parents=" ${parents} " '
    { parent[$1] = $2; age[$1] = $3; name[$1] = $4 }
    END {
      for (pid in name) {
        if (name[pid] != "smbclient" || age[pid] <= 60) continue
        up = parent[pid]
        for (depth = 0; depth < 5 && up > 1; depth++) {
          if (index(parents, " " up " ")) { print pid " " age[pid] "s"; break }
          up = parent[up]
        }
      }
    }')
  if [ -n "${stale}" ]; then
    hang_report
    fail "a smbclient process outlived its request (${label}): $(printf '%s' "${stale}" | tr '\n' ' ')"
  fi
  note "no smbclient below php -S older than 60 s (${label})"
}

# locked_ids <name> [storage]: the file ids of a locked file, comma separated.
locked_ids() {
  if [ -n "${2:-}" ]; then
    ncdb "SELECT fileid FROM oc_filecache WHERE name = '$1' AND storage = $2;"
  else
    ncdb "SELECT fileid FROM oc_filecache WHERE name = '$1';"
  fi | paste -sd, -
}

# judge_locked <label> <state/reason> <log mark> [container]: every living
# container row of gesperrt-alle.txt and the row of bob of gesperrt-bob.txt
# carry the verdict, oc_findling_file_state as well (unless container), and no
# pass since the mark was taken as an outage (B3).
judge_locked() {
  local label="$1" want="$2" mark="$3" only="${4:-}" all bob ids rows_st match_st rows_nc match_nc outage_lines
  all=$(locked_ids gesperrt-alle.txt)
  bob=$(locked_ids gesperrt-bob.txt "${daten_bob}")
  [ -n "${all}" ] && [ -n "${bob}" ] || fail "no file cache row of the locked files"
  ids="${all},${bob}"
  rows_st=$(statedb "SELECT COUNT(*) FROM files WHERE deleted_at IS NULL AND file_id IN (${ids});")
  match_st=$(statedb "SELECT COUNT(*) FROM files WHERE deleted_at IS NULL AND file_id IN (${ids})
                        AND state || '/' || COALESCE(reason, '-') = '${want}';")
  note "${label}: ${match_st} of ${rows_st} container rows of the locked files are ${want}"
  rows+=("| ${label} | container rows of the locked files ${want} | ${rows_st} | ${match_st} |")
  [ "${rows_st}" -ge 2 ] || {
    failures=$((failures + 1))
    echo "::warning::${label}: only ${rows_st} living container rows of the locked files, the check tests nothing"
  }
  check "${label} container verdicts ${want}" "${rows_st}" "${match_st}"
  [ "${only}" = "container" ] && return 0
  rows_nc=$(ncdb "SELECT COUNT(*) FROM oc_findling_file_state WHERE file_id IN (${ids});")
  match_nc=$(ncdb "SELECT COUNT(*) FROM oc_findling_file_state WHERE file_id IN (${ids})
                     AND state || '/' || COALESCE(reason, '-') = '${want}';")
  rows+=("| ${label} | oc_findling_file_state rows of the locked files ${want} | ${rows_nc} | ${match_nc} |")
  [ "${rows_nc}" -ge 2 ] || {
    failures=$((failures + 1))
    echo "::warning::${label}: only ${rows_nc} oc_findling_file_state rows of the locked files"
  }
  check "${label} oc_findling_file_state verdicts ${want}" "${rows_nc}" "${match_nc}"
  outage_lines=$(log_since "${mark}" | grep -c 'taken as an outage' || true)
  rows+=("| ${label} | log lines 'taken as an outage' | 0 | ${outage_lines} |")
  check "${label} no pass taken as an outage" 0 "${outage_lines}"
}

# coverage_body: the body the companion would send, built from oc_mounts and
# the storage ids, groups of SMB storages mounted at least twice.
coverage_body() {
  local mounted groups
  mounted=$(ncdb "SELECT DISTINCT storage_id FROM oc_mounts ORDER BY storage_id;" | jq -R 'tonumber' | jq -cs '.')
  groups=$(ncdb "SELECT s.numeric_id || char(9) || 'smb::' || substr(s.id, instr(s.id, '@') + 1)
                   FROM oc_storages AS s
                  WHERE s.id LIKE 'smb::%' AND s.numeric_id IN (SELECT storage_id FROM oc_mounts)
                  ORDER BY s.numeric_id;" \
    | jq -R 'split("\t") | {id: (.[0] | tonumber), key: .[1]}' \
    | jq -cs 'group_by(.key) | map(map(.id)) | map(select(length >= 2))')
  jq -cn --argjson mounted "${mounted}" --argjson groups "${groups}" '{mounted: $mounted, groups: $groups}'
}

# post_coverage: POST /coverage straight to the container, with the AppAPI
# headers of a test registration. Leaves the answer in ${WORK}/coverage.json.
post_coverage() {
  local auth
  auth=$(printf 'admin:%s' "${EXAPP_SECRET}" | base64 -w0)
  coverage_body > "${WORK}/coverage-body.json"
  curl -s -m 120 -X POST "http://127.0.0.1:${EXAPP_PORT}/coverage" \
    -H 'Content-Type: application/json' \
    -H 'EX-APP-ID: findling_backend' \
    -H "EX-APP-VERSION: $(backend_version "${BACKEND_DIR}")" \
    -H "AUTHORIZATION-APP-API: ${auth}" \
    --data @"${WORK}/coverage-body.json" -o "${WORK}/coverage.json" || true
  jq -c '{counting, docKeysMissing, docKeysUnresolved, docKeysCorrected}' "${WORK}/coverage.json" 2> /dev/null \
    || echo "unreadable answer"
}

# put_companion <dir> <version>: the PHP half out of a directory, with the
# version the update announces.
put_companion() {
  rm -rf apps/findling
  cp -r "$1" apps/findling
  sed -i "s:<version>[^<]*</version>:<version>$2</version>:" apps/findling/appinfo/info.xml
}

write_result() {
  {
    echo "## Coverage end to end, variant ${VARIANT}, smb ${SMB_MODE} (plan 43-07, 43-18)"
    echo
    echo "| Phase | Figure | Truth | Shown |"
    echo "|-------|--------|-------|-------|"
    if [ "${#rows[@]}" -gt 0 ]; then
      printf '%s\n' "${rows[@]}"
    fi
    echo "| drain | outage_abort_tolerated | - | ${outage_abort_tolerated} |"
    echo "| drain | drain_incomplete | - | ${drain_incomplete} |"
    echo
    if [ "${#notes[@]}" -gt 0 ]; then
      printf -- '- %s\n' "${notes[@]}"
    fi
    echo
    echo "failures=${failures}"
    echo "outage_abort_tolerated=${outage_abort_tolerated}"
    echo "drain_incomplete=${drain_incomplete}"
  } > "${RESULT_FILE}"
}

# ===================================================================================
# 1. Samba
# ===================================================================================

step "samba"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq samba smbclient sqlite3 > /dev/null
note "samba: $(smbd --version)"

for group in g_alice g_bob g_carol g_alicebob; do
  sudo groupadd -f "${group}"
done
for uid in aaron alice bob carol; do
  id "${uid}" > /dev/null 2>&1 || sudo useradd -M -s /usr/sbin/nologin "${uid}"
done
sudo usermod -a -G g_alice,g_alicebob alice
sudo usermod -a -G g_bob,g_alicebob bob
sudo usermod -a -G g_carol carol

# acl_xattr exactly as measured in A6 (plan 39-04): the stored NT ACL decides
# for the DENY ACEs, the Unix rights of the folders decide who may enter.
sudo tee /etc/samba/smb.conf > /dev/null << EOF
[global]
   netbios name = ${NETBIOS}
   workgroup = WORKGROUP
   server role = standalone server
   security = user
   map to guest = never
   smb ports = 445
   interfaces = lo
   bind interfaces only = yes
   disable netbios = yes
   log level = 1

[daten]
   path = /srv/daten
   read only = no
   browseable = yes
   create mask = 0666
   directory mask = 0777
   vfs objects = acl_xattr
   acl_xattr:ignore system acls = yes
   store dos attributes = yes

[archiv]
   path = /srv/archiv
   read only = no
   browseable = yes
   create mask = 0666
   directory mask = 0777
   vfs objects = acl_xattr
   acl_xattr:ignore system acls = yes
   store dos attributes = yes
EOF
testparm -s > /dev/null 2>&1 || fail "testparm rejected the generated smb.conf"

for uid in alice bob carol; do
  pass=$(password_of "${uid}")
  printf '%s\n%s\n' "${pass}" "${pass}" | sudo smbpasswd -a -s "${uid}" > /dev/null
  printf 'username = %s\npassword = %s\ndomain = %s\n' "${uid}" "${pass}" "${NETBIOS}" > "${WORK}/auth-${uid}"
  chmod 0600 "${WORK}/auth-${uid}"
done

# Folders: (share, folder, mode, group). gemeinsam of daten is writable so that
# alice can put the two locked files through SMB and own them (smbcacls).
sudo mkdir -p /srv/daten /srv/archiv
sudo chmod 0755 /srv/daten /srv/archiv
while read -r share folder mode group; do
  sudo mkdir -p "/srv/${share}/${folder}"
  sudo chown "root:${group}" "/srv/${share}/${folder}"
  sudo chmod "${mode}" "/srv/${share}/${folder}"
done << 'EOF'
daten gemeinsam 0777 root
daten projekt 0750 g_alicebob
daten nur-alice 0750 g_alice
daten nur-bob 0750 g_bob
daten nur-carol 0750 g_carol
archiv gemeinsam 0755 root
archiv nur-alice 0750 g_alice
archiv nur-bob 0750 g_bob
archiv nur-carol 0750 g_carol
EOF

# daten: alice sees 3 + 3 + 4 (+ 2 locked + gleich), bob 3 + 3 + 1, carol 3 + 2.
for n in 1 2 3; do samba_file daten "gemeinsam/daten-gemeinsam-${n}.txt"; done
for n in 1 2 3; do samba_file daten "projekt/projekt-${n}.txt"; done
for n in 1 2 3 4; do samba_file daten "nur-alice/daten-alice-${n}.txt"; done
samba_file daten "nur-bob/daten-bob-1.txt"
for n in 1 2; do samba_file daten "nur-carol/daten-carol-${n}.txt"; done
samba_file daten "gemeinsam/gleich.txt" "zqgleichdoc"
# archiv: bob is the largest member here, alice and carol hold one each alone.
for n in 1 2; do samba_file archiv "gemeinsam/archiv-gemeinsam-${n}.txt"; done
for n in 1 2 3; do samba_file archiv "nur-bob/archiv-bob-${n}.txt"; done
samba_file archiv "nur-alice/archiv-alice-1.txt"
samba_file archiv "nur-carol/archiv-carol-1.txt"
samba_file archiv "gemeinsam/gleich.txt" "zqgleichdoc"
# One file per share of a type nobody reads.
for share in daten archiv; do
  head -c 4096 /dev/urandom | sudo tee "/srv/${share}/gemeinsam/daten-${share}.bin" > /dev/null
  sudo chmod 0644 "/srv/${share}/gemeinsam/daten-${share}.bin"
done
# gross.bin (plan 43-18, W1): 10 MB for the slow fetch of the wrapped legs. A
# type outside TRUTH_TYPES_REGEX and refused by type, so it moves no truth.
head -c 10485760 /dev/urandom | sudo tee /srv/daten/gemeinsam/gross.bin > /dev/null
sudo chmod 0644 /srv/daten/gemeinsam/gross.bin

# The two locked files, put by alice through SMB so she owns them.
next_word
locked_all_word="${NEXT_WORD}"
next_word
locked_bob_word="${NEXT_WORD}"
printf 'Coverage proof %s\n' "${locked_all_word}" > "${WORK}/gesperrt-alle.txt"
printf 'Coverage proof %s\n' "${locked_bob_word}" > "${WORK}/gesperrt-bob.txt"
printf '%s\t%s\n' "${locked_all_word}" gesperrt-alle.txt >> "${WORDS}"
printf '%s\t%s\n' "${locked_bob_word}" gesperrt-bob.txt >> "${WORDS}"
# leer.txt (plan 43-18, B2): readable, zero bytes, no word of its own and not
# in WORDS. It counts in the denominator truth (find, type txt) and never in
# the numerator, the head judges it failed/empty_file. A product that takes it
# out of the denominator in phase B is a finding, the truth stays.
: > "${WORK}/leer.txt"
sudo systemctl restart smbd
up=0
for _ in $(seq 1 30); do
  if smbclient -L //127.0.0.1 -A "${WORK}/auth-alice" > /dev/null 2>&1; then
    up=1
    break
  fi
  sleep 1
done
[ "${up}" = 1 ] || fail "smbd did not answer on 127.0.0.1:445"
smbclient //127.0.0.1/daten -A "${WORK}/auth-alice" \
  -c "cd gemeinsam; lcd ${WORK}; put gesperrt-alle.txt; put gesperrt-bob.txt; put leer.txt" > /dev/null \
  || fail "alice could not put the two locked files and the empty file onto daten"
[ "$(stat -c %s /srv/daten/gemeinsam/leer.txt)" = "0" ] || fail "leer.txt on daten is not empty"
for uid in bob carol alice; do
  smbcacls //127.0.0.1/daten gemeinsam/gesperrt-alle.txt -A "${WORK}/auth-alice" \
    --add "ACL:${NETBIOS}\\${uid}:DENIED/0x0/READ" > /dev/null \
    || fail "smbcacls could not add the DENY ACE of ${uid} to the file locked for everybody"
done
smbcacls //127.0.0.1/daten gemeinsam/gesperrt-bob.txt -A "${WORK}/auth-alice" \
  --add "ACL:${NETBIOS}\\bob:DENIED/0x0/READ" > /dev/null \
  || fail "smbcacls could not add the DENY ACE of bob"

# The unreadable files of the truth: locked for every user, and nothing else.
printf 'smb:daten\tgemeinsam/gesperrt-alle.txt\n' > "${WORK}/unreadable.tsv"

# -- positive control at the Samba server ------------------------------------------

smb_get() {
  # smb_get <uid> <share> <path>: exit 0 only when the file arrived with content
  rm -f "${WORK}/get.out"
  smbclient "//127.0.0.1/$2" -A "${WORK}/auth-$1" -c "get $3 ${WORK}/get.out" > "${WORK}/smb-get.log" 2>&1 \
    && [ -s "${WORK}/get.out" ]
}
smb_ls() {
  smbclient "//127.0.0.1/$2" -A "${WORK}/auth-$1" -c "ls $3/*" > "${WORK}/smb-ls.log" 2>&1
}

step "positive control at the Samba server"
smb_ls alice daten nur-alice || fail "positive control: alice cannot list her own folder, run invalid"
if smb_ls bob daten nur-alice; then
  fail "positive control: bob lists the folder of alice through SMB, run invalid"
fi
if sudo -u bob ls /srv/daten/nur-alice > /dev/null 2>&1; then
  fail "positive control: bob lists the folder of alice on the file system, run invalid"
fi
for uid in alice bob carol; do
  if smb_get "${uid}" daten gemeinsam/gesperrt-alle.txt; then
    fail "positive control: ${uid} reads the file locked for everybody, run invalid"
  fi
done
smb_get alice daten gemeinsam/gesperrt-bob.txt || fail "positive control: alice cannot read the file locked for bob, run invalid"
if smb_get bob daten gemeinsam/gesperrt-bob.txt; then
  fail "positive control: bob reads the file locked for him, run invalid"
fi
smb_get bob daten gemeinsam/daten-gemeinsam-1.txt || fail "positive control: bob cannot read a free file, run invalid"
note "positive control at Samba: bob cannot enter a folder of alice, nobody reads the file locked for all, alice reads the file locked for bob"

# ===================================================================================
# 2. Nextcloud
# ===================================================================================

step "nextcloud"
# The mode of the leg (F3, T-43-57): php -S runs on the same PHP as this CLI.
smb_mode_seen=$(php -r 'echo function_exists("smbclient_state_new") ? "native" : "wrapped";')
rows+=("| setup | smb mode (function_exists smbclient_state_new) | ${SMB_MODE} | ${smb_mode_seen} |")
[ "${smb_mode_seen}" = "${SMB_MODE}" ] || fail "the leg runs ${smb_mode_seen}, not ${SMB_MODE}, the run is invalid"
note "smb mode: ${smb_mode_seen}"
nc_occ config:system:set skeletondirectory --value='' > /dev/null
nc_occ background:cron > /dev/null
nc_occ app:enable files_external > /dev/null
nc_occ files_external:backends storage --output=json | grep -q '"smb"' \
  || fail "files_external does not list the smb backend"
nc_occ config:system:set files_external_allow_create_new_local --value=true --type=boolean > /dev/null
nc_occ config:app:set findling index_external_storage --value=1 --type=boolean > /dev/null
take_app_password

if head_under_test && [ "${VARIANT}" != "upgrade" ]; then
  # A fresh installation has no hint (43-06): the migration finds no scan row.
  if nc_occ config:app:get findling coverage_per_document_hint > /dev/null 2>&1; then
    fail "the per document hint is set on a fresh installation"
  fi
  note "coverage_per_document_hint: absent on the fresh installation"
fi

for uid in aaron alice bob carol dave; do
  OC_PASS=$(password_of "${uid}") timeout 120 ./occ user:add --password-from-env --display-name "${uid}" "${uid}" > /dev/null
done

mount_id_of() {
  printf '%s\n' "$1" | grep -oE '[0-9]+' | tail -n 1
}
smb_mount() {
  # smb_mount <mount point> <share>: prints the mount id
  mount_id_of "$(nc_occ files_external:create "$1" smb password::logincredentials \
    -c host=127.0.0.1 -c share="$2" -c root= -c domain="${NETBIOS}")"
}
daten_mount=$(smb_mount /daten daten)
archiv_mount=$(smb_mount /archiv archiv)
archiv_two_mount=$(smb_mount /archiv-zwei archiv)
for mid in "${daten_mount}" "${archiv_mount}" "${archiv_two_mount}"; do
  [ -n "${mid}" ] || fail "files_external:create returned no mount id"
  nc_occ files_external:option "${mid}" enable_sharing true > /dev/null
done
nc_occ files_external:applicable "${daten_mount}" --add-user alice --add-user bob --add-user carol > /dev/null
nc_occ files_external:applicable "${archiv_mount}" --add-user alice --add-user bob --add-user carol > /dev/null
nc_occ files_external:applicable "${archiv_two_mount}" --add-user carol > /dev/null

sudo mkdir -p /srv/lokal
sudo chown "$(id -un):$(id -gn)" /srv/lokal
head -c 4096 /dev/urandom > /srv/lokal/zusatz.bin
local_mount=$(mount_id_of "$(nc_occ files_external:create /lokal local null::null -c datadir=/srv/lokal)")
[ -n "${local_mount}" ] || fail "the local storage could not be created"
nc_occ files_external:applicable "${local_mount}" --add-user alice > /dev/null

step "first login per user"
for uid in aaron alice bob carol dave; do
  login "${uid}"
done
for uid in alice bob carol; do
  state=$(timeout 90 php "${HARNESS}/scripts/ci/smb_acl_probe.php" "${SERVER_ROOT}" creds "${uid}" || echo "probe-error")
  if [ "${state}" != "stored" ]; then
    PROBE_PASS=$(password_of "${uid}") timeout 90 php "${HARNESS}/scripts/ci/smb_acl_probe.php" "${SERVER_ROOT}" seed "${uid}" > /dev/null
    note "credentials of ${uid} seeded through ICredentialsManager"
  fi
done

# Home files: dave (deleted later, one of them becomes the container row
# without a file cache row of the upgrade variant), alice (notiz.txt for the
# way back to 1.6.2).
home_file() {
  local word
  next_word
  word="${NEXT_WORD}"
  mkdir -p "$(dirname "${NC_DATA}/$1/files/$2")"
  printf 'Coverage proof %s\n' "${word}" > "${NC_DATA}/$1/files/$2"
  printf '%s\t%s\n' "${word}" "$(basename "$2")" >> "${WORDS}"
}
home_file dave dave-1.txt
home_file dave dave-2.txt
home_file dave verwaist.txt
home_file alice notiz.txt
nc_occ files:scan --all > /dev/null

step "reshare of daten/projekt to aaron"
curl -s -u "alice:$(password_of alice)" -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
  -d 'path=/daten/projekt' -d 'shareType=0' -d 'shareWith=aaron' -d 'permissions=1' \
  "${NC_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares" -o "${WORK}/share.json"
jq -e '.ocs.meta.statuscode == 200' "${WORK}/share.json" > /dev/null \
  || fail "the share of daten/projekt to aaron was not created: $(jq -c '.ocs.meta' "${WORK}/share.json" 2> /dev/null)"
login aaron
nc_occ files:scan --all > /dev/null

daten_alice=$(sid_like 'smb::alice@%//daten/%')
daten_bob=$(sid_like 'smb::bob@%//daten/%')
daten_carol=$(sid_like 'smb::carol@%//daten/%')
archiv_carol=$(sid_like 'smb::carol@%//archiv/%')
home_dave=$(sid_like 'home::dave')
# Not 'local::%': the data directory itself is a local storage of its own
# (local::<datadir>/) with the lowest id and no oc_mounts row (first dispatch,
# run 42381671975, failed here on all four variants).
local_sid=$(sid_like 'local::/srv/lokal%')
for pair in "daten_alice:${daten_alice}" "daten_bob:${daten_bob}" "daten_carol:${daten_carol}" \
  "archiv_carol:${archiv_carol}" "home_dave:${home_dave}" "local:${local_sid}"; do
  [ -n "${pair#*:}" ] || fail "no storage row for ${pair%%:*}"
  mounted_sid "${pair#*:}" || fail "${pair%%:*} is not in oc_mounts"
done
[ "${daten_alice}" != "${daten_bob}" ] || fail "alice and bob share one storage id, the group case tests nothing"
mounts_of_carol_archiv=$(ncdb "SELECT COUNT(*) FROM oc_mounts WHERE storage_id = ${archiv_carol} AND user_id = 'carol';")
note "carol mounts archiv ${mounts_of_carol_archiv} times (second mount point of the same share)"

# ===================================================================================
# 3. Indexing, with the reconcile switched off (job env)
# ===================================================================================

step "gateway probes before the crawl"
# W10: a short answer for a file the container expects with 0 bytes counts as
# whole there (requeueAs rows carry size 0). Apart from leer.txt no test file
# has size 0 in the file cache, so that limit meets no file of this run.
zero_sized=$(ncdb "SELECT COUNT(*) FROM oc_filecache AS fc JOIN oc_mimetypes AS m ON m.id = fc.mimetype
                    WHERE fc.size = 0 AND m.mimetype <> 'httpd/unix-directory' AND fc.name <> 'leer.txt'
                      AND (fc.name LIKE '%.txt' OR fc.name LIKE '%.png' OR fc.name LIKE '%.bin');")
check "test files of size 0 besides leer.txt (W10)" 0 "${zero_sized}"
leer_fid=$(ncdb "SELECT fileid FROM oc_filecache WHERE storage = ${daten_alice} AND name = 'leer.txt' LIMIT 1;")
[ -n "${leer_fid}" ] || fail "leer.txt has no file cache row"
# Before the queue fills, so no backend fetch holds a worker yet: a home file
# without SMB first, then a readable file of alice on daten.
gateway_probe home alice "$(ncdb "SELECT fc.fileid FROM oc_filecache AS fc JOIN oc_storages AS s ON s.numeric_id = fc.storage
                                    WHERE s.id = 'home::alice' AND fc.name = 'notiz.txt' LIMIT 1;")" 200
gateway_probe smb alice "$(ncdb "SELECT fileid FROM oc_filecache
                                  WHERE storage = ${daten_alice} AND name = 'daten-alice-1.txt' LIMIT 1;")" 200
# The files with a DENY ACE (run 42401892996: one fetch after 87 to 90 of bob
# never ended). 422 from both companions: the head through its deadline or
# its nudge, 1.6.2 only in the native mode, where fopen returns false. Both run
# before any hard stop, so both answers are seen.
gateway_probe locked-for-bob bob "$(ncdb "SELECT fileid FROM oc_filecache
                                            WHERE storage = ${daten_bob} AND name = 'gesperrt-bob.txt' LIMIT 1;")" 422 collect
gateway_probe locked-for-all alice "$(ncdb "SELECT fileid FROM oc_filecache
                                              WHERE storage = ${daten_alice} AND name = 'gesperrt-alle.txt' LIMIT 1;")" 422 collect
# The empty file: 200 with zero bytes from both companions. The plan assumed
# 400 from the 1.6.2 companion (StreamResponse.php:47-49 with Output.php:37);
# run 42418778026 measured 200 with 0 bytes on v1.6.2/native and on
# upgrade/native, so the empty file tells the companions apart no longer. The
# probe still holds both to a readable answer without bytes (B2, T-43-62).
gateway_probe empty alice "${leer_fid}" 200 collect
if [ "${SMB_MODE}" = "wrapped" ]; then
  gross_fid=$(ncdb "SELECT fileid FROM oc_filecache WHERE storage = ${daten_alice} AND name = 'gross.bin' LIMIT 1;")
  large_probe "${gross_fid}" collect
  large_probe_long "${gross_fid}" "${daten_mount}" collect
fi
if [ "${probe_failures}" -gt 0 ]; then
  hang_report
  fail "${probe_failures} gateway probe(s) answered other than expected"
fi
sleep 5
no_stale_smbclient "after the probes"

words_unique "words before the crawl"
step "crawl and drain"
crawl_mark=$(log_mark)
nc_occ findling:index --restart --no-interaction > /dev/null
run_crawl
drain
note "indexed: $(statedb "SELECT COUNT(*) FROM files WHERE deleted_at IS NULL AND state = 'indexed';") living rows indexed, $(living_rows) living rows"
note "verdict of the file locked for all: container $(statedb "SELECT state || '/' || COALESCE(reason, '-') FROM files WHERE deleted_at IS NULL AND path LIKE '%gesperrt-alle.txt' LIMIT 1;" || echo none), Nextcloud $(ncdb "SELECT r.state || '/' || COALESCE(r.reason, '-') FROM oc_findling_file_state AS r JOIN oc_filecache AS fc ON fc.fileid = r.file_id WHERE fc.name = 'gesperrt-alle.txt' LIMIT 1;" || echo none)"
note "verdict of leer.txt: container $(statedb "SELECT state || '/' || COALESCE(reason, '-') FROM files WHERE deleted_at IS NULL AND file_id = ${leer_fid};" || echo none)"
# The verdicts of plan 43-18 (B3). Behind the head companion a 422 is
# skipped/unreadable on both sides and no pass was taken as an outage; v1.6.2
# is the counter check with failed/gateway_error in the container. upgrade is
# judged after phase B, see there.
if head_companion; then
  judge_locked "after the first drain" "skipped/unreadable" "${crawl_mark}"
elif [ "${VARIANT}" = "v1.6.2" ]; then
  judge_locked "1.6.2 after the first drain" "failed/gateway_error" "${crawl_mark}" container
fi

# ===================================================================================
# 3b. The update of the upgrade variant (D-43-14, R2)
# ===================================================================================

if [ "${VARIANT}" = "upgrade" ]; then
  step "a container row without a file cache row"
  orphan=$(ncdb "SELECT fc.fileid FROM oc_filecache AS fc WHERE fc.storage = ${home_dave} AND fc.path = 'files/verwaist.txt';")
  [ -n "${orphan}" ] || fail "verwaist.txt has no file cache row"
  [ "$(statedb "SELECT COUNT(*) FROM files WHERE file_id = ${orphan} AND deleted_at IS NULL;")" = "1" ] \
    || fail "verwaist.txt has no living container row, the case tests nothing"
  # Past every event: the file goes from the disk and its row from the file
  # cache, so no job ever tells the container.
  rm -f "${NC_DATA}/dave/files/verwaist.txt"
  sqlite3 "${NC_DB}" "DELETE FROM oc_filecache WHERE fileid = ${orphan};"
  note "upgrade: one container row without a file cache row, made by deleting the file and its oc_filecache row after the indexing"

  step "container first: the head backend next to the 1.6.2 companion"
  stop_backend
  head_mark=$(log_mark)
  start_backend "${HARNESS}/backend"
  sleep 10
  answer=$(post_coverage)
  echo "coverage with the 1.6.2 companion: ${answer}"
  jq -e '.counting == true and .docKeysMissing > 0' "${WORK}/coverage.json" > /dev/null \
    || fail "the head container next to the 1.6.2 companion does not answer counting with missing keys: ${answer}"
  note "upgrade: before the companion update /coverage answers ${answer}"

  step "companion update"
  started=$(date +%s)
  put_companion "${HARNESS}/php" 1.6.3
  nc_occ upgrade > /dev/null
  companion_updated=1
  hint=$(nc_occ config:app:get findling coverage_per_document_hint || echo absent)
  check "upgrade hint coverage_per_document_hint" 1 "${hint}"
  backfill_mark=$(log_mark)
  post_coverage > /dev/null
  deadline=$(($(date +%s) + 900))
  while :; do
    if log_since "${backfill_mark}" | grep -q 'doc key backfill, done=[0-9]* missing=0 '; then
      break
    fi
    [ "$(date +%s)" -lt "${deadline}" ] || fail "the doc key backfill did not reach missing=0 within 900 s"
    sleep 10
  done
  backfill_seconds=$(($(date +%s) - started))
  log_since "${backfill_mark}" | grep 'doc key backfill, done=' | sed 's/^/backfill: /' || true
  answer=$(post_coverage)
  jq -e '.counting == false and .docKeysMissing == 0 and .docKeysUnresolved >= 1' "${WORK}/coverage.json" > /dev/null \
    || {
      failures=$((failures + 1))
      echo "::warning::after the backfill /coverage answers ${answer}"
    }
  note "upgrade: backfill done after ${backfill_seconds} s, $(log_since "${backfill_mark}" | grep -c 'doc key backfill, done=' || true) rounds, /coverage ${answer}"
  rows+=("| upgrade | docKeysMissing after the backfill | 0 | $(jq -r '.docKeysMissing' "${WORK}/coverage.json") |")
fi

# ===================================================================================
# 4. B1, then the topology change
# ===================================================================================

step "B1: the denominator before and after removing the extra storage"
read_settled b1-before
b1_before=$(jq -r '.coverage.indexable' "${WORK}/overview-b1-before.json")
nc_occ files_external:delete -y "${local_mount}" > /dev/null
login alice
for _ in $(seq 1 30); do
  mounted_sid "${local_sid}" || break
  sleep 1
done
mounted_sid "${local_sid}" && fail "the removed local storage stays in oc_mounts"
read_settled b1-after
b1_after=$(jq -r '.coverage.indexable' "${WORK}/overview-b1-after.json")
rows+=("| B1 | denominator before / after removing the extra storage | ${b1_before} | ${b1_after} |")
if head_under_test; then
  check "B1 denominator unchanged" "${b1_before}" "${b1_after}"
fi

stop_backend

# W5: a catch-up round may sweep even with the reconcile off; then phase A
# would measure a second sweep and not the first one.
swept_before=$(statedb "SELECT value FROM meta WHERE key = 'storage_sweep_at';" || true)
[ -z "${swept_before}" ] || fail "a catch-up round swept before phase A, the run is invalid"
note "storage_sweep_at before phase A: not set"

step "topology change"
nc_occ files_external:applicable "${daten_mount}" --remove-user carol > /dev/null
login carol
nc_occ user:delete dave > /dev/null
for _ in $(seq 1 30); do
  mounted_sid "${daten_carol}" || break
  sleep 1
done
mounted_sid "${daten_carol}" && fail "the daten storage of carol stays in oc_mounts after the configuration was taken away"
mounted_sid "${home_dave}" && fail "the home of the deleted dave stays in oc_mounts"
[ -n "$(sid_like 'smb::carol@%//daten/%')" ] || fail "the daten storage of carol lost its oc_storages row, it would be gone and not stamped"
[ -z "$(sid_like 'home::dave')" ] || fail "the home of the deleted dave keeps its oc_storages row"

# ===================================================================================
# 5. Phase A: the gate is blocked, the poller runs
# ===================================================================================

restart_env=(FINDLING_RECONCILE_ENABLED=true FINDLING_RECONCILE_MIN_INTERVAL_HOURS=1 FINDLING_EMBED_ENABLED=false)
if [ "${VARIANT}" = "gate-crawl" ]; then
  # A planned crawl that no cron has run: CrawlAdvanceService::crawling() is
  # true while the SchedulerJob row exists, and the poller cannot advance it.
  nc_occ findling:index --restart --no-interaction > /dev/null
  [ "$(crawl_pending)" != "0" ] || fail "no crawl row after the restart of the crawl"
  note "phase A gate: crawl unfinished (SchedulerJob planned, never run), quiet_max default"
else
  step "a backlog of ${BACKLOG_IMAGES} OCR images in the home of alice"
  mkdir -p "${WORK}/backlog"
  for n in $(seq 1 "${BACKLOG_IMAGES}"); do
    next_word
    word="${NEXT_WORD}"
    printf '%s\t%s\n' "${word}" "backlog-${n}.png" >> "${WORDS}"
    printf '%s\n' "${word}" > "${WORK}/backlog/backlog-${n}.word"
  done
  (cd "${BACKEND_DIR}" && uv run --frozen python - "${WORK}/backlog" "${BACKLOG_IMAGES}") << 'PY'
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

folder, count = Path(sys.argv[1]), int(sys.argv[2])
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 110)
except OSError:
    font = ImageFont.load_default(size=110)
for n in range(1, count + 1):
    word = (folder / f"backlog-{n}.word").read_text(encoding="ascii").strip()
    image = Image.new("L", (1800, 320), 255)
    ImageDraw.Draw(image).text((60, 90), word, fill=0, font=font)
    image.save(folder / f"backlog-{n}.png")
PY
  dav alice MKCOL backlog "${WORK}/mkcol.out" > /dev/null || true
  for n in $(seq 1 "${BACKLOG_IMAGES}"); do
    code=$(dav alice PUT "backlog/backlog-${n}.png" /dev/null -T "${WORK}/backlog/backlog-${n}.png")
    case "${code}" in
      201 | 204) ;;
      *) fail "the upload of backlog-${n}.png answered HTTP ${code}" ;;
    esac
  done
  restart_env+=(FINDLING_RECONCILE_QUIET_MAX=1)
  note "phase A gate: queue busy, ${BACKLOG_IMAGES} OCR images scheduled, FINDLING_RECONCILE_QUIET_MAX=1, $(open_rows) open rows before the restart"
fi

phase_a_mark=$(log_mark)
start_backend "${BACKEND_DIR}" "${restart_env[@]}"

step "phase A: waiting for the storage sweep"
deadline=$(($(date +%s) + SWEEP_TIMEOUT))
sweep_line=""
while [ "$(date +%s)" -lt "${deadline}" ]; do
  sweep_line=$(log_since "${phase_a_mark}" | grep -m 1 'storage sweep, absent=' || true)
  [ -n "${sweep_line}" ] && break
  sleep 5
done
stands_down=$(log_since "${phase_a_mark}" | grep -m 1 'reconcile stands down' || true)
sweep_quote=$(printf '%s' "${sweep_line}" | grep -oE 'storage sweep, absent=[0-9]+ gone=[0-9]+ deselected=[0-9]+ stamped=[0-9]+ removed=[0-9]+' || true)
stands_quote=$(printf '%s' "${stands_down}" | grep -oE 'reconcile stands down.*' || true)
note "phase A log: ${sweep_quote:-no sweep line}; ${stands_quote:-no stands down line}"

if head_under_test; then
  [ -n "${sweep_line}" ] || fail "no storage sweep within ${SWEEP_TIMEOUT} s while the gate was blocked"
  [ -n "${stands_down}" ] || fail "the gate was not blocked, there is no 'reconcile stands down', so phase A measures nothing"
  gone=$(printf '%s' "${sweep_quote}" | sed -E 's/.* gone=([0-9]+).*/\1/')
  stamped=$(printf '%s' "${sweep_quote}" | sed -E 's/.* stamped=([0-9]+).*/\1/')
  [ "${gone}" -ge 1 ] || { failures=$((failures + 1)); echo "::warning::the sweep saw no gone storage"; }
  [ "${stamped}" -ge 1 ] || { failures=$((failures + 1)); echo "::warning::the sweep stamped no storage"; }
  step "phase A: the delete jobs are worked off"
  deadline=$(($(date +%s) + 300))
  while :; do
    left=$(statedb "SELECT COUNT(*) FROM files WHERE storage_id = ${home_dave} AND deleted_at IS NULL;")
    [ "${left}" = "0" ] && break
    [ "$(date +%s)" -lt "${deadline}" ] || fail "${left} rows of the deleted home are still living after 300 s"
    sleep 5
  done
  vanished=$(statedb "SELECT COUNT(*) FROM vanished_storages WHERE storage_id = ${daten_carol};")
  [ "${vanished}" = "1" ] || { failures=$((failures + 1)); echo "::warning::vanished_storages does not hold the daten storage of carol"; }
  note "phase A: rows of the deleted home are tombstones, vanished_storages holds the storage taken from carol: ${vanished}"
else
  if [ -n "${sweep_line}" ]; then
    note "positive control: 1.6.2 swept behind a blocked gate, unexpected"
  else
    note "positive control: 1.6.2 did not sweep within ${SWEEP_TIMEOUT} s behind the blocked gate"
  fi
fi

read_settled phase-a
a_num_truth=$(truth_numerator_list | wc -l)
a_num_shown=$(jq -r '.coverage.indexed' "${WORK}/overview-phase-a.json")
a_den_shown=$(jq -r '.coverage.indexable' "${WORK}/overview-phase-a.json")
a_percent=$(jq -r '.coverage.percent' "${WORK}/overview-phase-a.json")
rows+=("| A | numerator | ${a_num_truth} | ${a_num_shown} |")
if head_under_test; then
  a_den_expected=$(expected_denominator_phase_a)
  rows+=("| A | denominator (D-43-11 rule in SQL) | ${a_den_expected} | ${a_den_shown} |")
  rows+=("| A | percent | not null, at most 100 | ${a_percent} |")
  check "phase A numerator" "${a_num_truth}" "${a_num_shown}"
  check "phase A denominator" "${a_den_expected}" "${a_den_shown}"
  if [ "${a_percent}" = "null" ] || [ "${a_percent}" -gt 100 ]; then
    failures=$((failures + 1))
    echo "::warning::phase A percent is ${a_percent}"
  fi
  walked=$(log_since "${phase_a_mark}" | grep -c 'reconcile round walked' || true)
  rows+=("| A | walked rounds | 0 | ${walked} |")
  check "phase A walked rounds" 0 "${walked}"
else
  rows+=("| A | denominator | - | ${a_den_shown} |")
fi

# ===================================================================================
# 6. Phase B: queue empty, crawl done
# ===================================================================================

step "phase B: release the gate"
if [ "${VARIANT}" = "gate-crawl" ]; then
  run_crawl
fi
drain
read_settled phase-b-1
sleep 30
drain
read_settled phase-b

users_left=$(nc_occ user:list --output=json | jq -r 'keys[]' | tr '\n' ' ')
truth_numerator_list > "${WORK}/numerator.tsv"
truth_denominator_list "daten:alice bob;archiv:alice bob carol" "${users_left}" > "${WORK}/denominator.tsv"
b_num_truth=$(wc -l < "${WORK}/numerator.tsv")
b_den_truth=$(wc -l < "${WORK}/denominator.tsv")
b_unreadable_truth=$(truth_not_readable "${WORK}/unreadable.tsv" "${WORK}/denominator.tsv")
b_num_shown=$(jq -r '.coverage.indexed' "${WORK}/overview-phase-b.json")
b_den_shown=$(jq -r '.coverage.indexable' "${WORK}/overview-phase-b.json")
b_unreadable_shown=$(jq -r '.coverage.notReadable // "-"' "${WORK}/overview-phase-b.json")
outside=$(comm -23 "${WORK}/numerator.tsv" "${WORK}/denominator.tsv" | wc -l)
rows+=("| B | numerator | ${b_num_truth} | ${b_num_shown} |")
rows+=("| B | denominator (Samba union and homes) | ${b_den_truth} | ${b_den_shown} |")
rows+=("| B | notReadable | ${b_unreadable_truth} | ${b_unreadable_shown} |")
rows+=("| B | searchable documents outside the denominator truth | 0 | ${outside} |")
note "phase B: the D-43-11 rule in SQL gives $(expected_denominator_phase_a) for the same state"

positive_control_compare "phase B numerator" "${b_num_truth}" "${b_num_shown}"

if head_under_test; then
  check "phase B numerator" "${b_num_truth}" "${b_num_shown}"
  check "phase B denominator" "${b_den_truth}" "${b_den_shown}"
  check "phase B notReadable" "${b_unreadable_truth}" "${b_unreadable_shown}"
  check "phase B numerator inside the denominator" 0 "${outside}"
  a1=$(a1_rows_checked projekt/projekt-1.txt projekt/projekt-2.txt projekt/projekt-3.txt)
  rows+=("| B | a1_rows_checked (reshared files with two rows and one key) | 3 | ${a1} |")
  echo "a1_rows_checked=${a1}"
  [ "${a1}" -gt 0 ] || fail "the reshare case tests nothing, the run is invalid"
  check "a1_rows_checked" 3 "${a1}"
else
  positive_control_reference "${b_num_truth}" "${b_num_shown}" "${b_den_truth}" "${b_den_shown}"
  note "positive control 2: 1.6.2 shows ${b_num_shown} of ${b_den_shown}, truth ${b_num_truth} of ${b_den_truth}"
fi

sleep 5
no_stale_smbclient "after phase B"
if [ "${VARIANT}" = "upgrade" ]; then
  # Only now (B3): the reconcile hands the 1.6.2 rows failed/gateway_error
  # with budget out again, and the head judges them skipped/unreadable. A
  # different verdict is a finding for the coordinator, never a looser check.
  judge_locked "upgrade after phase B" "skipped/unreadable" "${head_mark}"
fi

step "search cross check"
words_unique "words before the search cross check"
# shellcheck disable=SC2086 # the user list is a word list on purpose
found=$(search_crosscheck "${WORDS}" ${users_left})
rows+=("| B | words found through the search (W4) | ${b_num_truth} | ${found} |")
check "search cross check" "${b_num_truth}" "${found}"
if [ -s "${WORK}/crosscheck-missing.txt" ]; then
  note "files whose word the search does not find: $(sort "${WORK}/crosscheck-missing.txt" | tr '\n' ' ')"
  # Run 42418778026 listed 45 names for 8 missing words: most of them are
  # never searchable (backlog images, locked files). The names in the
  # numerator truth are the misses that count; each missing name comes with
  # the short form of the raw answer for the first user (entries and titles,
  # file names of the test topology, no content).
  in_truth=$(cut -f2 "${WORK}/numerator.tsv" | sed 's#.*/##' | sort -u)
  while IFS=$'\t' read -r miss_name miss_raw; do
    if printf '%s\n' "${in_truth}" | grep -qxF -- "${miss_name}"; then
      note "search miss in the numerator truth: ${miss_name}, ${miss_raw}"
    else
      note "search miss outside the numerator truth: ${miss_name}, ${miss_raw}"
    fi
  done < "${WORK}/crosscheck-raw.txt"
fi

# ===================================================================================
# 7. Upgrade variant: back to 1.6.2, then up again with a rename (W5, G1)
# ===================================================================================

if [ "${VARIANT}" = "upgrade" ]; then
  step "rollback to 1.6.2"
  notiz=$(ncdb "SELECT fc.fileid FROM oc_filecache AS fc JOIN oc_storages AS s ON s.numeric_id = fc.storage WHERE s.id = 'home::alice' AND fc.path = 'files/notiz.txt';")
  [ -n "${notiz}" ] || fail "notiz.txt has no file cache row"
  stop_backend
  curl -fsSL -o "${WORK}/findling-1.6.2.tar.gz" "${RELEASE_COMPANION_URL}" || fail "the 1.6.2 companion archive could not be downloaded"
  rm -rf "${WORK}/release" && mkdir -p "${WORK}/release"
  tar -xzf "${WORK}/findling-1.6.2.tar.gz" -C "${WORK}/release"
  [ -f "${WORK}/release/findling/appinfo/info.xml" ] || fail "the 1.6.2 archive carries no findling/appinfo/info.xml"
  put_companion "${WORK}/release/findling" 1.6.2
  companion_updated=0
  nc_occ config:app:set findling installed_version --value=1.6.2 > /dev/null
  start_backend "${SRC}/backend"
  has_column=$(statedb "SELECT COUNT(*) FROM pragma_table_info('files') WHERE name = 'doc_key';")
  has_index=$(statedb "SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name = 'files_storage_doc_key';")
  before_at=$(statedb "SELECT COALESCE(indexed_at, 0) FROM files WHERE file_id = ${notiz};")
  next_word
  rollback_word="${NEXT_WORD}"
  # A word no file carried before (it used to be the one word of all files):
  # only the new content of notiz.txt can find it now.
  if cut -f1 "${WORDS}" | grep -qxF -- "${rollback_word}"; then
    fail "the rollback word is already in use, the rollback search tests nothing"
  fi
  printf 'Coverage proof %s\n' "${rollback_word}" > "${WORK}/notiz.txt"
  code=$(dav alice PUT notiz.txt /dev/null -T "${WORK}/notiz.txt")
  case "${code}" in 201 | 204) ;; *) fail "the change of notiz.txt answered HTTP ${code}" ;; esac
  rollback=failed
  deadline=$(($(date +%s) + 600))
  while [ "$(date +%s)" -lt "${deadline}" ]; do
    after_at=$(statedb "SELECT COALESCE(indexed_at, 0) || ' ' || state FROM files WHERE file_id = ${notiz};" || echo "0 -")
    if [ "${after_at%% *}" -gt "${before_at}" ] && [ "${after_at##* }" = "indexed" ]; then
      printf '%s\tnotiz.txt\n' "${rollback_word}" > "${WORK}/rollback-word.tsv"
      if [ "$(search_crosscheck "${WORK}/rollback-word.tsv" alice)" = "1" ]; then
        rollback=ok
        break
      fi
    fi
    sleep 10
  done
  [ "${has_column}" = "1" ] && [ "${has_index}" = "1" ] || rollback=failed
  echo "rollback_1_6_2=${rollback}"
  note "rollback_1_6_2=${rollback} (doc_key column ${has_column}, index ${has_index}, a changed file judged and found by 1.6.2)"
  [ "${rollback}" = "ok" ] || failures=$((failures + 1))

  step "rename under 1.6.2"
  code=$(dav alice MOVE notiz.txt /dev/null -H "Destination: ${NC_URL}/remote.php/dav/files/alice/notiz-umbenannt.txt")
  case "${code}" in 201 | 204) ;; *) fail "the rename of notiz.txt answered HTTP ${code}" ;; esac
  old_key=$(printf '%s' 'files/notiz.txt' | sha256sum | cut -d' ' -f1)
  new_key=$(printf '%s' 'files/notiz-umbenannt.txt' | sha256sum | cut -d' ' -f1)
  deadline=$(($(date +%s) + 300))
  while :; do
    renamed=$(statedb "SELECT COUNT(*) FROM files WHERE file_id = ${notiz} AND path LIKE '%notiz-umbenannt.txt';")
    [ "${renamed}" = "1" ] && break
    [ "$(date +%s)" -lt "${deadline}" ] || fail "1.6.2 did not take the rename within 300 s"
    sleep 5
  done
  stale=$(statedb "SELECT doc_key FROM files WHERE file_id = ${notiz};")
  [ "${stale}" = "${old_key}" ] || fail "after the rename under 1.6.2 the key is not the stale one, the rename case tests nothing, the run is invalid"

  step "second update to the head"
  stop_backend
  put_companion "${HARNESS}/php" 1.6.3
  nc_occ upgrade > /dev/null
  companion_updated=1
  bands=$(sed -n 's/^DOC_KEY_BACKFILL_BANDS_PER_ROUND: Final = \([0-9]*\).*/\1/p' "${HARNESS}/backend/src/findling/worker/doc_keys.py")
  tick=$(sed -n 's/^DOC_KEY_TICK_SECONDS: Final = \([0-9]*\).*/\1/p' "${HARNESS}/backend/src/findling/worker/doc_keys.py")
  [ -n "${bands}" ] && [ -n "${tick}" ] || fail "the backfill constants could not be read"
  living=$(living_rows)
  rounds=$(((living + 200 * bands - 1) / (200 * bands) + 1))
  bound=$((rounds * tick + 60))
  started=$(date +%s)
  start_backend "${HARNESS}/backend"
  second=failed
  while [ "$(($(date +%s) - started))" -le "${bound}" ]; do
    if [ "$(statedb "SELECT doc_key FROM files WHERE file_id = ${notiz};")" = "${new_key}" ]; then
      second=ok
      break
    fi
    sleep 10
  done
  answer=$(post_coverage)
  if [ "${second}" = "ok" ] && ! jq -e '.docKeysCorrected >= 1 and .counting == false' "${WORK}/coverage.json" > /dev/null; then
    second=failed
  fi
  echo "second_upgrade_rename=${second}"
  note "second_upgrade_rename=${second} (bound ${rounds} rounds of ${tick} s plus 60 s for the start, ${living} living rows, took $(($(date +%s) - started)) s, /coverage ${answer})"
  [ "${second}" = "ok" ] || failures=$((failures + 1))
fi

write_result
cat "${RESULT_FILE}"
[ "${failures}" = "0" ] || {
  echo "::error::${failures} comparisons of variant ${VARIANT} differ from the truth"
  exit 1
}
