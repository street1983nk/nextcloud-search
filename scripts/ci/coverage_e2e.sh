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
#   - Since plan 43-25 the case of issue #25 as it was reported (D-43-15,
#     D-43-17): every mount names the Samba server by one host alias from
#     /etc/hosts. The share daten is configured with the root / and with two
#     sub roots (sicherheit for alice and carol, projekt for bob), and once
#     more for bob in another spelling (share Daten, the host in upper case).
#     The alias is exactly as long as it takes for the storage ids of the sub
#     root sicherheit to pass 64 characters, which Nextcloud stores as an md5;
#     four mounts on that sub root carry the four ways such an id gets its
#     login: password::password with the user in the configuration,
#     password::logincredentials, password::global and password::userprovided.
#     The first two can be rebuilt from the configuration, the last two cannot
#     and are counted on their own (EXPECTED_SEPARATE_K in coverage_truth.sh).
#     Two files that differ in case only (Bericht.txt, bericht.txt), a public
#     link on a folder of an SMB mount, and a share [homes] for alice and bob
#     with a file of the same name in each home directory.
#   - Every mount is written to ${WORK}/mounts.tsv as it was created (mount
#     point, share, root, users, mechanism, login at the Samba server); the
#     truth finds the file behind a file cache row through that log and
#     through Samba itself, never through a storage id.
#
# Variants (VARIANT):
#   gate-crawl  head, the crawl is unfinished during phase A
#   gate-queue  head, the crawl is done and scheduled >= quiet_max in phase A
#   v1.6.2      the released 1.6.2 on the same topology, positive control 2
#   upgrade     indexed by 1.6.2, then updated to the head (doc key backfill,
#               one container row without a file cache row), the gate-queue
#               proof, then back to 1.6.2 and up again with a rename (W5, G1)
#   upgrade-rc1     indexed by the test build rc.1 (document keys of
#                   generation 1, which count a file once per root), then the
#                   container alone goes to the head and runs next to the rc.1
#                   companion, then the companion follows and every key is
#                   rebuilt; the gate-queue proof, then back to 1.6.2 and up
#                   again like upgrade (plan 43-26)
#   upgrade-rc1-cf  the same start, the other order: the companion goes to the
#                   head first and runs next to the rc.1 container, then a
#                   backup pause, then the head container. While the pause
#                   holds no key is rebuilt and the generation gate of
#                   POST /coverage alone keeps the old keys out of the figure
#                   (B1 of plan 43-24, T-43-79); after the resume the rebuild,
#                   then the gate-queue proof
#
# SMB modes (SMB_MODE, plan 43-18, owner decision F3): wrapped, icewind/smb
# drives the smbclient binary; native, the php-smbclient extension. The leg
# proves its mode with function_exists('smbclient_state_new') before anything
# is counted, a leg in the wrong mode is an invalid run.
#
# Runs from the root of the Nextcloud server checkout. Expects VARIANT,
# SMB_MODE, NC_URL, HARNESS (checkout of the head), SRC (checkout the instance
# was set up from), RESULT_FILE, EXAPP_SECRET, EXAPP_PORT, RUNNER_TEMP, and
# for upgrade-rc1 BASE_SRC (a checkout of v1.6.2 for the way back).
#
# What stands where once the setup action is through (coverage-e2e.yml and
# .github/actions/setup-test-nc):
#   ${SRC}/backend       the backend the instance was set up from, in place
#   ${SRC}/php           gone, the action moved it to apps/findling
#   apps/findling        the companion that is installed right now
#   ${HARNESS}/backend, ${HARNESS}/php   the head, both in place
#   ${BASE_SRC}/backend  the released 1.6.2, upgrade-rc1 only; its companion
#                        comes out of the release archive, not out of this tree
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
  gate-crawl | gate-queue | v1.6.2 | upgrade | upgrade-rc1 | upgrade-rc1-cf) ;;
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
# The host every mount names (plan 43-25), an alias of 127.0.0.1 in /etc/hosts.
# 38 characters on purpose. A storage id reads smb::<login>@<host>//<share>/<root>
# with the root as /x/ (apps/files_external/lib/Lib/Storage/SMB.php getId), and
# Nextcloud stores an id of more than 64 characters as its md5
# (lib/private/Files/Cache/Storage.php adjustStorageId):
#   root /            smb::alice@<38>//daten//             5+5+1+38+2+5+1+1  = 58, written out
#   root projekt      smb::bob@<38>//daten//projekt/       5+3+1+38+2+5+1+9  = 64, written out
#   root sicherheit   smb::bob@<38>//daten//sicherheit/    5+3+1+38+2+5+1+12 = 67, an md5
# so the mounts on the sub root sicherheit are the hashed ones, with any login.
SMB_HOST='samba.deckung-findling-abnahme.example'
SMB_HOST_UPPER="${SMB_HOST^^}"
RELEASE_COMPANION_URL='https://github.com/street1983nk/nextcloud-search/releases/download/v1.6.2/findling.tar.gz'
BACKLOG_IMAGES=30
DRAIN_TIMEOUT=1500
SWEEP_TIMEOUT=240
# The catch-up of 1.5 under 1.6.2 (upgrade leg, run 42477570073): its once
# task looks at the mark every 300 s (RECONCILE_TICK_SECONDS of 1.6.2) and a
# round behind a busy queue waits one more tick, so two ticks, the round and
# a margin.
CATCHUP_TIMEOUT=900
# The backend the instance runs right now; the upgrade variants move it.
BACKEND_DIR="${SRC}/backend"
# The backend of the released 1.6.2 for the way back: the tree the instance
# was set up from in the variant upgrade, a checkout of its own in upgrade-rc1.
OLD_BACKEND_DIR=""
case "${VARIANT}" in
  upgrade) OLD_BACKEND_DIR="${SRC}/backend" ;;
  upgrade-rc1)
    : "${BASE_SRC:?BASE_SRC is required for upgrade-rc1}"
    OLD_BACKEND_DIR="${BASE_SRC}/backend"
    ;;
esac
# The longest wait for a rebuild of the document keys after an update from
# rc.1. A round starts every DOC_KEY_TICK_SECONDS (300 s) and a round that met
# a companion of another key format first waits out its cooldown (300 s, then
# doubled) unless a coverage call ends it, so three ticks and a margin.
REBUILD_TIMEOUT=1200
# How long the generation gate is watched under the backup pause: four reads
# of the wish (PAUSE_POLL_SECONDS, 15 s). Without the pause the first round of
# the document keys runs as soon as the container is armed.
PAUSE_HOLD_SECONDS=60
# By how much a storage sweep stamp of rc.1 is aged before the head starts,
# see age_sweep_stamp.
SWEEP_AGE_SECONDS=10800

mkdir -p "${WORK}"
# The mount log (plan 43-25): one line per configuration as it was created,
# "<mount point>\t<share>\t<root>\t<users>\t<mechanism>\t<login>". The login is
# the account at the Samba server, "-" where every user logs in as himself.
# No field is empty, the root of a share is written "/".
MOUNTS="${WORK}/mounts.tsv"
: > "${MOUNTS}"
# One collation for sort and comm everywhere.
export LC_ALL=C
umask 022

failures=0
rows=()
notes=()
# The verdict lines of the upgrade variants, "<name>: ok (<detail>)", printed
# at the start of a line in the result file (plan 43-26).
verdicts=()
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

# verdict <name> <ok|failed> <detail>: one verdict line; anything but ok counts
# as a failure of the leg.
verdict() {
  echo "$1: $2 ($3)"
  verdicts+=("$1: $2 ($3)")
  [ "$2" = "ok" ] || failures=$((failures + 1))
}

password_of() {
  case "$1" in
    admin) printf '%s' 'password' ;;
    aaron) printf '%s' 'Deckung-aaron-43-q7' ;;
    alice) printf '%s' 'Deckung-alice-43-x4' ;;
    bob) printf '%s' 'Deckung-bob-43-m2' ;;
    carol) printf '%s' 'Deckung-carol-43-k9' ;;
    dave) printf '%s' 'Deckung-dave-43-v5' ;;
    # Accounts of the Samba server only, no Nextcloud users (plan 43-25).
    dglobal) printf '%s' 'Deckung-dglobal-43-h3' ;;
    deigen) printf '%s' 'Deckung-deigen-43-n8' ;;
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
#
# The two variants that start at rc.1 begin with the flag set: the test build
# was cut after plans 43-17 to 43-20 and carries the gateway and the verdicts
# of the head, the document keys are what tells it apart. Only the way back to
# 1.6.2 in upgrade-rc1 clears the flag.
companion_updated=0
case "${VARIANT}" in
  upgrade-rc1 | upgrade-rc1-cf) companion_updated=1 ;;
esac
head_companion() {
  case "${VARIANT}" in
    gate-crawl | gate-queue) return 0 ;;
    upgrade | upgrade-rc1 | upgrade-rc1-cf) [ "${companion_updated}" = "1" ] ;;
    *) return 1 ;;
  esac
}

# from_rc1: the instance was set up from the test build rc.1.
from_rc1() {
  case "${VARIANT}" in
    upgrade-rc1 | upgrade-rc1-cf) return 0 ;;
    *) return 1 ;;
  esac
}

# head_container: the container that answers right now is the one of the head.
# Always in gate-crawl and gate-queue; elsewhere only after start_backend took
# it out of the harness checkout. It decides the body of POST /coverage: the
# head demands docKeyFormat 2 and answers 422 without it (plan 43-24), every
# older container forbids the field (extra forbid) and answers 422 with it.
head_container() {
  case "${VARIANT}" in
    gate-crawl | gate-queue) return 0 ;;
    *) [ "${BACKEND_DIR}" = "${HARNESS}/backend" ] ;;
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

# Run 42482017221: a read that met a writer of Nextcloud or of the container
# ended the leg with "database is locked (5)". .timeout waits up to 10 s for
# the lock and prints nothing (sqlite3_busy_timeout in shell.c.in).
ncdb() {
  sqlite3 -readonly -cmd ".timeout 10000" "${NC_DB}" "$1"
}

statedb() {
  sqlite3 -readonly -cmd ".timeout 10000" "${STATE_DB}" "$1"
}

sid_like() {
  ncdb "SELECT numeric_id FROM oc_storages WHERE id LIKE '$1' ORDER BY numeric_id LIMIT 1;"
}

# sid_is <storage id>: the numeric id of exactly this id string. LIKE folds
# ASCII case in SQLite, and since plan 43-25 two storages differ in the
# spelling of host and share only.
sid_is() {
  ncdb "SELECT numeric_id FROM oc_storages WHERE id = '$1';"
}

# hashed_id <login>: the storage id of a mount on the sub root sicherheit as
# Nextcloud builds it; hashed_sid <login>: the row Nextcloud stores for it,
# under the md5 of that id.
hashed_id() {
  printf 'smb::%s@%s//daten//sicherheit/' "$1" "${SMB_HOST}"
}
hashed_sid() {
  sid_is "$(hashed_id "$1" | md5sum | cut -d' ' -f1)"
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

# backend_version <dir>: the version in <dir>/appinfo/info.xml, of either half.
# A directory without that file ends the run with its name: the setup action
# moves findling-src/php to apps/findling, and run 42991291089 read the moved
# directory and ended on a bare "sed: can't read".
backend_version() {
  [ -f "$1/appinfo/info.xml" ] || {
    echo "::error::harness finding: no appinfo/info.xml below $1, a version was asked of a directory that is not there" >&2
    return 1
  }
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

# locked_file_ids: every file cache row a login is refused on, comma separated.
# gesperrt-alle.txt on each storage of the root of daten (nobody reads it) and
# gesperrt-bob.txt on the two storages bob reaches that root through: daten,
# and since plan 43-25 the same share in its other spelling (spelled_bob). The
# second one was missing here until run 42991291089, whose head legs logged
# six refusals (file ids 85, 121, 122, 158, 159, 182) and judged five.
locked_file_ids() {
  local all bob
  all=$(locked_ids gesperrt-alle.txt)
  bob=$(ncdb "SELECT fileid FROM oc_filecache WHERE name = 'gesperrt-bob.txt'
                 AND storage IN (${daten_bob}, ${spelled_bob});" | paste -sd, -)
  [ -n "${all}" ] && [ -n "${bob}" ] || fail "no file cache row of the locked files"
  printf '%s,%s' "${all}" "${bob}"
}

# locked_diagnosis <label> <ids>: one line per row of the locked files, from
# the container (storage, state, reason, attempts, etag, deleted_at, the
# tombstoned rows too) and from the return channel, plus whether the one time
# streak renewal of plan 43-20 ever logged. Ids and reason codes only, never a
# path or content.
locked_diagnosis() {
  local label="$1" ids="$2" line
  note "${label}: storages daten_alice=${daten_alice} daten_bob=${daten_bob} daten_carol=${daten_carol}"
  while IFS= read -r line; do
    note "${label}: container ${line}"
  done < <(statedb "SELECT 'file_id=' || file_id || ' storage=' || storage_id
                        || ' state=' || state || '/' || COALESCE(reason, '-')
                        || ' attempts=' || attempts
                        || ' etag=' || COALESCE(etag, '-')
                        || ' deleted_at=' || COALESCE(deleted_at, '-')
                      FROM files WHERE file_id IN (${ids}) ORDER BY file_id;")
  while IFS= read -r line; do
    note "${label}: file_state ${line}"
  done < <(ncdb "SELECT 'file_id=' || file_id || ' state=' || state || '/' || COALESCE(reason, '-')
                     || ' updated_at=' || updated_at
                   FROM oc_findling_file_state WHERE file_id IN (${ids}) ORDER BY file_id;")
  note "${label}: renewal log lines: $(grep -c 'refusal streaks renewed once after the update' "${EXAPP_LOG}" || true)" \
    "$(grep -o 'refusal streaks renewed once after the update, rows=[0-9]*' "${EXAPP_LOG}" | tail -n 2 | tr '\n' ' ' || true)"
}

# locked_queue <label> <ids>: one line per queue row of the locked files, ids
# and counters only. Which of these rows 1.6.2 leaves behind decides what the
# head can say about them later (see judge_locked), and run 42991291089 kept
# no line of it.
locked_queue() {
  local label="$1" ids="$2" line seen=0
  while IFS= read -r line; do
    seen=$((seen + 1))
    note "${label}: queue ${line}"
  # locked_at as it is stored: the epoch marks a free row (QueueMapper
  # freeMark), any later moment the claim that holds it.
  done < <(ncdb "SELECT 'file_id=' || file_id || ' storage=' || storage_id || ' kind=' || COALESCE(kind, '-')
                     || ' retries=' || retries || ' locked_at=' || COALESCE(locked_at, '-')
                   FROM oc_findling_queue WHERE file_id IN (${ids}) ORDER BY file_id;")
  [ "${seen}" -gt 0 ] || note "${label}: queue holds no row of the locked files"
}

# gone_copy_before <storage>: called while no container runs, right before the
# topology change takes the storage away. Leaves in GONE_COPY_QUEUED how many
# queue rows are open for the copy of gesperrt-alle.txt on it and in
# GONE_COPY_VERDICT what oc_findling_file_state says about that copy
# ("state/reason updated_at", or "none").
GONE_COPY_QUEUED=""
GONE_COPY_VERDICT=""
gone_copy_before() {
  local sid="$1" copy
  copy=$(locked_ids gesperrt-alle.txt "${sid}")
  [ -n "${copy}" ] || fail "no file cache row of gesperrt-alle.txt on the storage ${sid} that is about to go, the gone check tests nothing"
  locked_queue "before the topology change" "$(locked_file_ids)"
  GONE_COPY_QUEUED=$(ncdb "SELECT COUNT(*) FROM oc_findling_queue WHERE file_id IN (${copy});")
  GONE_COPY_VERDICT=$(gone_copy_verdict "${copy}")
  case "${GONE_COPY_QUEUED}" in
    '' | *[!0-9]*) fail "the queue rows of the copy on the storage that is about to go could not be counted" ;;
  esac
  note "before the topology change: the copy of gesperrt-alle.txt on the storage ${sid} has ${GONE_COPY_QUEUED} open queue row(s), oc_findling_file_state says ${GONE_COPY_VERDICT}"
}

# gone_copy_verdict <ids>: "state/reason updated_at" per row, "none" without one.
gone_copy_verdict() {
  local seen
  seen=$(ncdb "SELECT state || '/' || COALESCE(reason, '-') || ' ' || updated_at
                 FROM oc_findling_file_state WHERE file_id IN ($1) ORDER BY file_id;" | paste -sd';' -)
  printf '%s' "${seen:-none}"
}

# judge_locked <label> <state/reason> <log mark> [container] [gone storage]
#              [queue rows of the gone copy] [verdict of the gone copy before]:
# every living container row of gesperrt-alle.txt and the row of bob of
# gesperrt-bob.txt carry the verdict, oc_findling_file_state as well (unless
# container), and no pass since the mark was taken as an outage (B3). A gone
# storage is one the topology change removed before this judgement: its copy of
# gesperrt-alle.txt can never be judged again, so it leaves the verdict count.
#
# What Nextcloud says about that copy afterwards has one writer and one
# condition. skipped/gone is written by QueueService::describe and nowhere
# else, at the claim of a queue row whose file no mount shows any more
# (usersFor answers nobody). The head hands no new row out for such a file:
# the reconcile walks mounted storages only, and the sweep stamps a storage
# that merely left the mount list (plan 43-02). So the copy stands
# skipped/gone exactly when a queue row for it was still open at the moment
# the storage went, and whether one is depends on 1.6.2 alone. A pass of 1.6.2
# whose refusals reach min(5, claimed) files on two storages is taken as an
# outage: the refused rows stay charged in the queue until their lock times
# out, the rest of the pass goes back refunded (poller.py of 1.6.2,
# _count_refusal, GATEWAY_SAME_STATUS_OUTAGE_AFTER). A pass of one file never
# escalates, its refusal is acknowledged failed/gateway_error and the row is
# gone.
#   Four locked rows (until plan 43-25, run 42498330790): the retry pass
#   claims four, escalates at the fourth, the row of carol stays charged, and
#   the head reads it skipped/gone after the storage went.
#   Six locked rows (plan 43-25 added the storage of bob in the other
#   spelling with two more, run 42991291089): the retry pass claims six in
#   the order the walk queued them, storage by storage, escalates at the
#   fifth (09:06:09, open=6, outages=1), and the sixth, the copy of carol on
#   the storage walked last, goes back refunded. Two minutes later it is claimed alone and acknowledged
#   (09:08:09, open=5, its verdict in oc_findling_file_state carries that
#   second). No row of it is left for the head, which never touched the copy;
#   the check demanded skipped/gone without looking at the queue and failed.
#
# So both outcomes are held to their condition, measured by gone_copy_before
# while no container ran:
#   a row was open   the copy must stand skipped/gone
#   no row was open  the verdict must be byte for byte the one from before the
#                    topology change, the head had nothing to judge
# A copy that is neither is a finding about the head and stays a failure.
judge_locked() {
  local label="$1" want="$2" mark="$3" only="${4:-}" gone_sid="${5:-}" gone_queued="${6:-}" gone_before="${7:-}" ids gone not_gone="" rows_st match_st rows_nc match_nc gone_rows gone_match gone_now outage_lines
  ids=$(locked_file_ids)
  locked_diagnosis "${label}" "${ids}"
  if [ -n "${gone_sid}" ]; then
    gone=$(locked_ids gesperrt-alle.txt "${gone_sid}")
    [ -n "${gone}" ] || fail "${label}: no file cache row of gesperrt-alle.txt on the gone storage ${gone_sid}, the gone check tests nothing"
    not_gone=" AND file_id NOT IN (${gone})"
  fi
  rows_st=$(statedb "SELECT COUNT(*) FROM files WHERE deleted_at IS NULL AND file_id IN (${ids})${not_gone};")
  match_st=$(statedb "SELECT COUNT(*) FROM files WHERE deleted_at IS NULL AND file_id IN (${ids})${not_gone}
                        AND state || '/' || COALESCE(reason, '-') = '${want}';")
  note "${label}: ${match_st} of ${rows_st} container rows of the locked files are ${want}"
  rows+=("| ${label} | container rows of the locked files ${want} | ${rows_st} | ${match_st} |")
  [ "${rows_st}" -ge 2 ] || {
    failures=$((failures + 1))
    echo "::warning::${label}: only ${rows_st} living container rows of the locked files, the check tests nothing"
  }
  check "${label} container verdicts ${want}" "${rows_st}" "${match_st}"
  [ "${only}" = "container" ] && return 0
  rows_nc=$(ncdb "SELECT COUNT(*) FROM oc_findling_file_state WHERE file_id IN (${ids})${not_gone};")
  match_nc=$(ncdb "SELECT COUNT(*) FROM oc_findling_file_state WHERE file_id IN (${ids})${not_gone}
                     AND state || '/' || COALESCE(reason, '-') = '${want}';")
  rows+=("| ${label} | oc_findling_file_state rows of the locked files ${want} | ${rows_nc} | ${match_nc} |")
  [ "${rows_nc}" -ge 2 ] || {
    failures=$((failures + 1))
    echo "::warning::${label}: only ${rows_nc} oc_findling_file_state rows of the locked files"
  }
  check "${label} oc_findling_file_state verdicts ${want}" "${rows_nc}" "${match_nc}"
  if [ -n "${gone_sid}" ]; then
    case "${gone_queued}" in
      '' | *[!0-9]*) fail "${label}: the queue rows of the copy on the gone storage were not counted before the topology change" ;;
    esac
    locked_queue "${label}" "${ids}"
    gone_rows=$(ncdb "SELECT COUNT(*) FROM oc_findling_file_state WHERE file_id IN (${gone});")
    [ "${gone_rows}" -ge 1 ] || {
      failures=$((failures + 1))
      echo "::warning::${label}: no oc_findling_file_state row of the locked file on the gone storage, the gone check tests nothing"
    }
    if [ "${gone_queued}" -ge 1 ]; then
      gone_match=$(ncdb "SELECT COUNT(*) FROM oc_findling_file_state WHERE file_id IN (${gone})
                           AND state || '/' || COALESCE(reason, '-') = 'skipped/gone';")
      rows+=("| ${label} | oc_findling_file_state rows of the locked file on the gone storage skipped/gone (${gone_queued} queue row(s) open when it went) | ${gone_rows} | ${gone_match} |")
      check "${label} gone storage verdicts skipped/gone" "${gone_rows}" "${gone_match}"
      note "${label}: gone_path=exercised (${gone_queued} queue row(s) were open for the copy when its storage went)"
    else
      gone_now=$(gone_copy_verdict "${gone}")
      rows+=("| ${label} | verdict of the locked file on the gone storage, no queue row was open when it went | ${gone_before} | ${gone_now} |")
      check "${label} gone storage verdict untouched without a queue row" "${gone_before}" "${gone_now}"
      note "${label}: gone_path=not_exercised (1.6.2 left no queue row for the copy on the gone storage, the head had nothing to claim)"
    fi
  fi
  outage_lines=$(log_since "${mark}" | grep -c 'taken as an outage' || true)
  rows+=("| ${label} | log lines 'taken as an outage' | 0 | ${outage_lines} |")
  check "${label} no pass taken as an outage" 0 "${outage_lines}"
}

# coverage_body: a body in the form the companion sends, built from oc_mounts
# and the storage ids, groups of SMB storages with a written out id that are
# mounted at least twice. The groups are not the ones of the head companion
# (no folded spelling, the root in the key, no hashed id) and no figure is read
# from the answer; the callers read counting and the doc key counters only.
# docKeyFormat 2 goes in for the container of the head and for no other one,
# see head_container. A style as the first argument overrides that choice
# (plan 43-26): with-format is the body of a head companion, without-format
# the body of a companion of rc.1, whichever container answers.
coverage_body() {
  local style="${1:-}" mounted groups
  if [ -z "${style}" ]; then
    style=without-format
    if head_container; then
      style=with-format
    fi
  fi
  mounted=$(ncdb "SELECT DISTINCT storage_id FROM oc_mounts ORDER BY storage_id;" | jq -R 'tonumber' | jq -cs '.')
  groups=$(ncdb "SELECT s.numeric_id || char(9) || 'smb::' || substr(s.id, instr(s.id, '@') + 1)
                   FROM oc_storages AS s
                  WHERE s.id LIKE 'smb::%' AND s.numeric_id IN (SELECT storage_id FROM oc_mounts)
                  ORDER BY s.numeric_id;" \
    | jq -R 'split("\t") | {id: (.[0] | tonumber), key: .[1]}' \
    | jq -cs 'group_by(.key) | map(map(.id)) | map(select(length >= 2))')
  case "${style}" in
    with-format)
      jq -cn --argjson mounted "${mounted}" --argjson groups "${groups}" \
        '{mounted: $mounted, groups: $groups, docKeyFormat: 2}'
      ;;
    without-format)
      jq -cn --argjson mounted "${mounted}" --argjson groups "${groups}" '{mounted: $mounted, groups: $groups}'
      ;;
    *)
      # To stderr: the caller redirects stdout into the body file.
      echo "::error::unknown body style ${style}" >&2
      return 1
      ;;
  esac
}

# coverage_status <style>: POST /coverage with a body of the given style and
# print the HTTP status, 000 when curl gave up. The answer stays in
# ${WORK}/coverage.json.
coverage_status() {
  local auth
  auth=$(printf 'admin:%s' "${EXAPP_SECRET}" | base64 -w0)
  # No status at all for a style nobody knows: the caller compares against
  # 200 or 422 and counts the empty answer as a difference.
  coverage_body "$1" > "${WORK}/coverage-body.json" || return 1
  curl -s -m 120 -X POST "http://127.0.0.1:${EXAPP_PORT}/coverage" \
    -H 'Content-Type: application/json' \
    -H 'EX-APP-ID: findling_backend' \
    -H "EX-APP-VERSION: $(backend_version "${BACKEND_DIR}")" \
    -H "AUTHORIZATION-APP-API: ${auth}" \
    --data @"${WORK}/coverage-body.json" -o "${WORK}/coverage.json" -w '%{http_code}' || true
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

# ===================================================================================
# The variants that start at the test build rc.1 (plan 43-26)
# ===================================================================================

doc_key_mark() {
  statedb "SELECT value FROM meta WHERE key = 'doc_key_backfill_after';" 2> /dev/null || echo unreadable
}

# keyed_rows: living container rows that carry a document key. "unreadable"
# and never 0 when the database gave no answer, so a failed read cannot pass
# for "no key was written".
keyed_rows() {
  statedb "SELECT COUNT(*) FROM files WHERE deleted_at IS NULL AND doc_key IS NOT NULL;" 2> /dev/null || echo unreadable
}

doc_key_tick() {
  sed -n 's/^DOC_KEY_TICK_SECONDS: Final = \([0-9]*\).*/\1/p' "${HARNESS}/backend/src/findling/worker/doc_keys.py"
}

# log_count <mark> <text>: the log lines since the mark that carry the text.
log_count() {
  log_since "$1" | grep -c -- "$2" || true
}

# generation_one_with_keys <meta value> <keyed rows>: the keys of rc.1 are
# still there. The meta value of rc.1 begins with its generation, "1:", and a
# living row carries a key. Both are needed for the generation gate of the
# head to be what answers: a value of generation 2 or no key at all means the
# rebuild already ran, or that there never was anything to rebuild.
generation_one_with_keys() {
  case "$1" in
    1:*) ;;
    *) return 1 ;;
  esac
  case "$2" in
    '' | *[!0-9]*) return 1 ;;
  esac
  [ "$2" -gt 0 ]
}

# counts_above <shown> <floor>: both are numbers and the first is larger.
counts_above() {
  case "$1" in
    '' | *[!0-9]*) return 1 ;;
  esac
  case "$2" in
    '' | *[!0-9]*) return 1 ;;
  esac
  [ "$1" -gt "$2" ]
}

# wait_counted <label> <limit>: POST /coverage until the container answers
# counting false with no key missing; the seconds it took are left in
# COUNTED_SECONDS, the last answer in ${WORK}/coverage.json. Never run as
# $(wait_counted): fail has to end the run, not a subshell.
COUNTED_SECONDS=0
wait_counted() {
  local label="$1" limit="$2" started answer
  started=$(date +%s)
  while :; do
    answer=$(post_coverage)
    if jq -e '.counting == false and .docKeysMissing == 0' "${WORK}/coverage.json" > /dev/null 2>&1; then
      COUNTED_SECONDS=$(($(date +%s) - started))
      echo "${label}: counting false and no key missing after ${COUNTED_SECONDS} s"
      return 0
    fi
    [ "$(($(date +%s) - started))" -lt "${limit}" ] \
      || fail "${label}: the container still counts after ${limit} s: ${answer}"
    sleep 10
  done
}

# wait_for_catchup <version>: the one time catch-up of 1.5 finishes under the
# version the instance was set up from, before anything of the head runs (run
# 42477570073, the whole reasoning stands at the update of the variant
# upgrade). The mark and its done word are read from the tree of that version.
# The seconds are left in CATCHUP_SECONDS.
CATCHUP_SECONDS=0
wait_for_catchup() {
  local version="$1" key done_word started deadline now
  key=$(sed -n 's/^CATCHUP_MARK: Final = "\([a-z0-9_]*\)".*/\1/p' "${SRC}/backend/src/findling/store/repo.py")
  done_word=$(sed -n 's/^CATCHUP_DONE: Final = "\([a-z]*\)".*/\1/p' "${SRC}/backend/src/findling/store/repo.py")
  [ -n "${key}" ] && [ -n "${done_word}" ] \
    || fail "the catch-up mark of ${version} could not be read from store/repo.py"
  started=$(date +%s)
  deadline=$((started + CATCHUP_TIMEOUT))
  while :; do
    now=$(statedb "SELECT value FROM meta WHERE key = '${key}';" || true)
    [ "${now}" = "${done_word}" ] && break
    [ "$(date +%s)" -lt "${deadline}" ] \
      || fail "${version} did not finish the catch-up of 1.5 within ${CATCHUP_TIMEOUT} s (${key}='${now}'), the leg cannot start the head without a catch-up round"
    sleep 10
  done
  CATCHUP_SECONDS=$(($(date +%s) - started))
  # The catch-up round may hand rows back to the queue; they settle under the
  # old version before anything of the head runs.
  drain
  note "${VARIANT}: ${key}=${done_word} under ${version} after ${CATCHUP_SECONDS} s of waiting"
  rows+=("| ${VARIANT} | catch-up of 1.5 done under ${version} before the head starts | ${done_word} | ${done_word} after ${CATCHUP_SECONDS} s |")
}

# age_sweep_stamp: called while no container runs, between rc.1 and the head.
#
# 1.6.2 writes no storage_sweep_at, rc.1 does: its catch-up cycle sweeps (plan
# 43-02), minutes before phase A. The sweep has a cadence of its own
# (reconcile.py _sweep_due: the minimum pause, then the preferred hour or
# twice the pause), so a stamp that young would keep the head from sweeping
# in phase A for an hour and the leg could never show the first sweep after
# the topology change. An instance that ran rc.1 for days has an old stamp;
# this makes the stamp that old (SWEEP_AGE_SECONDS, three times the pause of
# phase A) and changes nothing else. W5 keeps its meaning: the stamp has to
# be exactly this value before phase A, a sweep of the head before that moves
# it and the run is invalid.
sweep_stamp_expected=""
age_sweep_stamp() {
  local stamp
  stamp=$(statedb "SELECT value FROM meta WHERE key = 'storage_sweep_at';" || true)
  if [ -z "${stamp}" ]; then
    note "${VARIANT}: rc.1 left no storage_sweep_at, nothing to age"
    return 0
  fi
  case "${stamp}" in
    *[!0-9]*) fail "storage_sweep_at of rc.1 reads '${stamp}', which is no time" ;;
  esac
  sweep_stamp_expected=$((stamp - SWEEP_AGE_SECONDS))
  sqlite3 -cmd ".timeout 10000" "${STATE_DB}" \
    "UPDATE meta SET value = '${sweep_stamp_expected}' WHERE key = 'storage_sweep_at';"
  [ "$(statedb "SELECT value FROM meta WHERE key = 'storage_sweep_at';" || true)" = "${sweep_stamp_expected}" ] \
    || fail "the storage sweep stamp of rc.1 could not be aged"
  note "${VARIANT}: storage_sweep_at of rc.1 aged by ${SWEEP_AGE_SECONDS} s while no container ran, as on an instance that ran rc.1 for hours"
}

# page_shows <label> <kind>: the admin overview, read through the companion
# that is installed right now, goes the way named by kind:
#   old-way   the figure of 1.6.2 (no per document count, nothing counting),
#             the answer of a companion to a container it cannot talk keys with
#   no-figure the per document count is counting and the share is null
# A page that does not answer is a failure, never a pass.
page_shows() {
  local label="$1" kind="$2" filter seen=unreadable
  case "${kind}" in
    old-way) filter='.coverage.perDocument == false and .coverage.counting == false' ;;
    no-figure) filter='.coverage.perDocument == true and .coverage.counting == true and .coverage.percent == null' ;;
    *) fail "unknown page kind ${kind}" ;;
  esac
  for _ in $(seq 1 12); do
    if overview; then
      seen=$(jq -c '.coverage | {perDocument, counting, percent}' "${WORK}/overview.json" 2> /dev/null || echo unreadable)
      break
    fi
    sleep 5
  done
  rows+=("| mixed | ${label}: the page, ${kind} | ${kind} | ${seen} |")
  if [ "${seen}" != "unreadable" ] && jq -e "${filter}" "${WORK}/overview.json" > /dev/null 2>&1; then
    echo "compare ${label}, the page ${kind}: ${seen}, as expected"
    return 0
  fi
  failures=$((failures + 1))
  echo "::warning::compare ${label}, the page ${kind}: ${seen}, different"
}

# update_companion_to_head: the PHP half of the head over the one of rc.1,
# through occ upgrade. This is the version proof of the test build since rc.2
# was struck (owner decision of 2026-11-09): the reporter goes from rc.1
# straight to the release, so the installed version has to stand at rc.1
# before, php has to read the head as newer in the operator form the server
# uses, and occ upgrade has to leave the head version behind.
update_companion_to_head() {
  local head_version before after newer
  head_version=$(backend_version "${HARNESS}/php")
  [ -n "${head_version}" ] || fail "the companion of the head carries no version"
  before=$(nc_occ config:app:get findling installed_version || echo unreadable)
  check "installed_version of the companion before the update" "${rc1_version}" "${before}"
  newer=$(php -r 'var_export(version_compare($argv[1], $argv[2], ">"));' "${head_version}" "${rc1_version}" || echo unreadable)
  check "php reads ${head_version} as newer than ${rc1_version}" true "${newer}"
  put_companion "${HARNESS}/php" "${head_version}"
  nc_occ upgrade > /dev/null
  companion_updated=1
  after=$(nc_occ config:app:get findling installed_version || echo unreadable)
  rows+=("| update | installed_version of the companion, from ${before} | ${head_version} | ${after} |")
  check "installed_version of the companion after occ upgrade" "${head_version}" "${after}"
}

# rc1_baseline: what both variants need from rc.1 before anything of the head
# runs. The catch-up of 1.5 is over, rc.1 has finished its own count, its keys
# are of generation 1, and positive control 4: the figure rc.1 shows lies
# above the files on the host by more than the head may (EXPECTED_SEPARATE_K).
# rc.1 keys a file by the root it was reached through, so this topology has to
# make it count the files below the sub roots more than once; if it does not,
# an update that shows the truth afterwards proves nothing.
rc1_keyed=0
rc1_baseline() {
  local mark truth shown floor
  step "rc.1: the catch-up of 1.5 finishes under rc.1"
  wait_for_catchup "${rc1_version}"
  step "rc.1: its own count is finished"
  wait_counted "rc.1 before the update" "${REBUILD_TIMEOUT}"
  mark=$(doc_key_mark)
  rc1_keyed=$(keyed_rows)
  rows+=("| rc.1 | living rows with a key of generation 1 before the update | more than 0 | ${rc1_keyed} |")
  generation_one_with_keys "${mark}" "${rc1_keyed}" \
    || fail "rc.1 left no keys of generation 1 (${rc1_keyed} keyed rows), the update has nothing to rebuild, the run is invalid"
  read_settled rc1-baseline
  [ "$(jq -r '.coverage.perDocument' "${WORK}/overview-rc1-baseline.json")" = "true" ] \
    || fail "rc.1 does not show a per document count, the run is invalid"
  truth_physical
  truth=$(truth_numerator_list | wc -l)
  shown=$(jq -r '.coverage.indexed' "${WORK}/overview-rc1-baseline.json")
  floor=$(with_separate_k "${truth}")
  rows+=("| rc.1 | positive control 4, numerator of rc.1 (files on the host: ${truth}) | more than ${floor} | ${shown} |")
  counts_above "${shown}" "${floor}" \
    || fail "rc.1 does not count the roots twice here, the run is invalid"
  note "positive control 4: rc.1 shows ${shown} documents, ${truth} files are on the host, the head may show ${floor}"
}

# mixed_container_first: the head container next to the companion of rc.1, then
# the companion.
mixed_container_first() {
  local before_failures="${failures}" tick deadline status mark keyed fid state key living answer
  step "container first: the head backend next to the rc.1 companion"
  stop_backend
  age_sweep_stamp
  head_mark=$(log_mark)
  start_backend "${HARNESS}/backend"
  tick=$(doc_key_tick)
  [ -n "${tick}" ] || fail "DOC_KEY_TICK_SECONDS could not be read"

  # The first round forgets the keys of generation 1 and asks the companion
  # for new ones; rc.1 answers without the format, and the round waits.
  deadline=$(($(date +%s) + tick + 120))
  while [ "$(log_count "${head_mark}" 'the companion has another doc key format')" = "0" ]; do
    [ "$(date +%s)" -lt "${deadline}" ] \
      || fail "the head container never logged 'another doc key format' next to the rc.1 companion"
    sleep 5
  done
  note "container first: the backfill logged 'another doc key format' $(log_count "${head_mark}" 'the companion has another doc key format') time(s)"
  keyed=$(keyed_rows)
  rows+=("| mixed | container first: living rows with a key after the first round (before: ${rc1_keyed}) | 0 | ${keyed} |")
  check "container first, the keys of generation 1 are forgotten" 0 "${keyed}"

  # The body of an rc.1 companion carries no format.
  status=$(coverage_status without-format)
  rows+=("| mixed | container first: /coverage for the body of an rc.1 companion | 422 | ${status} |")
  check "container first, /coverage for the body of an rc.1 companion" 422 "${status}"
  page_shows "container first" old-way

  # No job writes a key: a new file is indexed through a job of the rc.1
  # companion, which carries a key of the old format.
  next_word
  printf 'Coverage proof %s\n' "${NEXT_WORD}" > "${WORK}/mischbetrieb.txt"
  printf '%s\tmischbetrieb.txt\n' "${NEXT_WORD}" >> "${WORDS}"
  status=$(dav alice PUT mischbetrieb.txt /dev/null -T "${WORK}/mischbetrieb.txt")
  case "${status}" in
    201 | 204) ;;
    *) fail "the upload of mischbetrieb.txt answered HTTP ${status}" ;;
  esac
  fid=$(ncdb "SELECT fc.fileid FROM oc_filecache AS fc JOIN oc_storages AS s ON s.numeric_id = fc.storage
               WHERE s.id = 'home::alice' AND fc.path = 'files/mischbetrieb.txt';")
  [ -n "${fid}" ] || fail "mischbetrieb.txt has no file cache row"
  deadline=$(($(date +%s) + 600))
  while :; do
    state=$(statedb "SELECT state FROM files WHERE file_id = ${fid} AND deleted_at IS NULL;" || true)
    [ "${state}" = "indexed" ] && break
    [ "$(date +%s)" -lt "${deadline}" ] \
      || fail "the head container did not index a new file next to the rc.1 companion within 600 s (state '${state}'), the job case tests nothing"
    sleep 5
  done
  key=$(statedb "SELECT COALESCE(doc_key, 'none') FROM files WHERE file_id = ${fid};" || echo unreadable)
  rows+=("| mixed | container first: key of a file indexed through a job of the rc.1 companion | none | ${key} |")
  check "container first, a job of the rc.1 companion writes no key" none "${key}"
  check "container first, no living row carries a key" 0 "$(keyed_rows)"

  # The container itself answers: with the format of the head it counts, and
  # says that every key is missing. So the 422 above was the format.
  status=$(coverage_status with-format)
  check "container first, /coverage for a body with the format of the head" 200 "${status}"
  answer=$(jq -c '{counting, docKeysMissing}' "${WORK}/coverage.json" 2> /dev/null || echo unreadable)
  if ! jq -e '.counting == true and .docKeysMissing > 0' "${WORK}/coverage.json" > /dev/null 2>&1; then
    failures=$((failures + 1))
    echo "::warning::container first: before the companion update /coverage answers ${answer}, not counting with missing keys"
  fi
  note "container first: before the companion update /coverage answers ${answer}"

  step "container first: the companion follows"
  update_companion_to_head
  wait_counted "container first, the rebuild" "${REBUILD_TIMEOUT}"
  mark=$(doc_key_mark)
  living=$(living_rows)
  rows+=("| mixed | container first: generation of the keys after the rebuild | 2 | ${mark%%:*} |")
  check "container first, generation of the keys after the rebuild" 2 "${mark%%:*}"
  if [ "${failures}" = "${before_failures}" ]; then
    verdict mixed_container_first ok "rebuild ${COUNTED_SECONDS} s until counting false, ${living} living rows"
  else
    verdict mixed_container_first failed "$((failures - before_failures)) checks differ, rebuild ${COUNTED_SECONDS} s, ${living} living rows"
  fi
}

# mixed_companion_first_pause: the head companion next to the container of
# rc.1, then a backup pause, then the head container (B1 of plan 43-24).
mixed_companion_first_pause() {
  local before_failures="${failures}" status mark keyed mark_after keyed_after answer living paused
  step "companion first: the head companion next to the rc.1 container"
  update_companion_to_head
  # The container of rc.1 forbids the field the head companion sends.
  status=$(coverage_status with-format)
  rows+=("| mixed | companion first: /coverage of the rc.1 container for the body of the head companion | 422 | ${status} |")
  check "companion first, /coverage of the rc.1 container for the body of the head companion" 422 "${status}"
  status=$(coverage_status without-format)
  check "companion first, the rc.1 container answers a body of its own format" 200 "${status}"
  page_shows "companion first" old-way

  step "companion first: backup pause, then the head container"
  # --wait: exit 0 only when the container said paused, so nothing of it is
  # still writing when it is stopped.
  timeout 400 ./occ findling:pause --wait 300 > "${WORK}/pause.out" 2>&1 || {
    cat "${WORK}/pause.out"
    fail "harness finding: the rc.1 container did not say paused within 300 s after occ findling:pause"
  }
  stop_backend
  age_sweep_stamp
  head_mark=$(log_mark)
  start_backend "${HARNESS}/backend"

  # The moment plan 43-24 is about: the head container holds keys of the old
  # generation and may not rebuild them. The answer is read between two reads
  # of the state, and both have to show the old generation with keys;
  # otherwise the rebuild already ran and the answer says nothing about the
  # gate.
  mark=$(doc_key_mark)
  keyed=$(keyed_rows)
  status=$(coverage_status with-format)
  answer=$(jq -c '{counting, docKeysMissing}' "${WORK}/coverage.json" 2> /dev/null || echo unreadable)
  mark_after=$(doc_key_mark)
  keyed_after=$(keyed_rows)
  rows+=("| mixed | companion first: keys of generation 1 while the pause holds (meta ${mark%%:*}:, ${mark_after%%:*}:) | more than 0 | ${keyed}, ${keyed_after} |")
  generation_one_with_keys "${mark}" "${keyed}" && generation_one_with_keys "${mark_after}" "${keyed_after}" \
    || fail "the gate was not exercised, the run is invalid"
  rows+=("| mixed | companion first: /coverage of the head container under the pause | 200 counting | ${status} ${answer} |")
  check "companion first, /coverage of the head container under the pause" 200 "${status}"
  if ! jq -e '.counting == true and .docKeysMissing > 0' "${WORK}/coverage.json" > /dev/null 2>&1; then
    failures=$((failures + 1))
    echo "::warning::companion first: under the pause /coverage answers ${answer}, not counting"
  fi
  page_shows "companion first, under the pause" no-figure

  # As long as the pause holds: several reads of the wish later the keys are
  # still the old ones and the answer is still counting.
  sleep "${PAUSE_HOLD_SECONDS}"
  paused=$(nc_occ findling:pause 2>&1 | sed -n 's/^Status: //p' | tail -n 1 || true)
  mark=$(doc_key_mark)
  keyed=$(keyed_rows)
  status=$(coverage_status with-format)
  answer=$(jq -c '{counting, docKeysMissing}' "${WORK}/coverage.json" 2> /dev/null || echo unreadable)
  generation_one_with_keys "${mark}" "${keyed}" \
    || fail "the keys were rebuilt while the backup pause held (status '${paused}'): the gate was not exercised, the run is invalid"
  rows+=("| mixed | companion first: after ${PAUSE_HOLD_SECONDS} s under the pause (status ${paused:-unknown}) | 200 counting | ${status} ${answer} |")
  check "companion first, /coverage after ${PAUSE_HOLD_SECONDS} s under the pause" 200 "${status}"
  if ! jq -e '.counting == true and .docKeysMissing > 0' "${WORK}/coverage.json" > /dev/null 2>&1; then
    failures=$((failures + 1))
    echo "::warning::companion first: after ${PAUSE_HOLD_SECONDS} s under the pause /coverage answers ${answer}, not counting"
  fi
  note "companion first: under the pause the meta value stays generation 1 with ${keyed} keyed rows, /coverage ${answer}, pause status ${paused:-unknown}"

  step "companion first: resume, the rebuild"
  nc_occ findling:resume > /dev/null
  wait_counted "companion first, the rebuild after the resume" "${REBUILD_TIMEOUT}"
  mark=$(doc_key_mark)
  living=$(living_rows)
  rows+=("| mixed | companion first: generation of the keys after the rebuild | 2 | ${mark%%:*} |")
  check "companion first, generation of the keys after the rebuild" 2 "${mark%%:*}"
  if [ "${failures}" = "${before_failures}" ]; then
    verdict mixed_companion_first_pause ok "rebuild ${COUNTED_SECONDS} s after the resume until counting false, ${living} living rows"
  else
    verdict mixed_companion_first_pause failed "$((failures - before_failures)) checks differ, rebuild ${COUNTED_SECONDS} s, ${living} living rows"
  fi
}

write_result() {
  {
    echo "## Coverage end to end, variant ${VARIANT}, smb ${SMB_MODE} (plan 43-07, 43-18, 43-25, 43-26)"
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
    if [ "${#verdicts[@]}" -gt 0 ]; then
      echo
      printf '%s\n' "${verdicts[@]}"
    fi
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
# dglobal and deigen (plan 43-25) are accounts of the Samba server only: the
# logins behind the global credentials and behind the credentials bob enters
# for one storage. Unix names of at most 32 characters, the long storage ids
# come from the host alias and the sub root.
for uid in aaron alice bob carol dglobal deigen; do
  id "${uid}" > /dev/null 2>&1 || sudo useradd -M -s /usr/sbin/nologin "${uid}"
done
sudo usermod -a -G g_alice,g_alicebob alice
sudo usermod -a -G g_bob,g_alicebob bob
sudo usermod -a -G g_carol carol

# The host alias. Both spellings have to resolve before any mount names them,
# otherwise the mount in upper case would test a dead storage.
printf '127.0.0.1 %s\n' "${SMB_HOST}" | sudo tee -a /etc/hosts > /dev/null
[ "${#SMB_HOST}" = "38" ] || fail "the host alias has ${#SMB_HOST} characters, the id lengths of the topology were derived for 38"
for spelling in "${SMB_HOST}" "${SMB_HOST_UPPER}"; do
  getent hosts "${spelling}" | grep -q '^127\.0\.0\.1[[:space:]]' \
    || fail "harness finding: getent does not resolve the host alias in one of its two spellings to 127.0.0.1"
done
[ "${SMB_HOST}" != "${SMB_HOST_UPPER}" ] || fail "the host alias has no letter to spell in upper case"

# The home directories behind [homes], where the account database says they
# are. useradd -M made none.
for uid in alice bob; do
  home_dir=$(getent passwd "${uid}" | cut -d: -f6)
  [ -n "${home_dir}" ] && [ "${home_dir}" != "/" ] || fail "${uid} has no home directory in the account database"
  sudo mkdir -p "${home_dir}"
  sudo chown "${uid}:" "${home_dir}"
  sudo chmod 0700 "${home_dir}"
done

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

[homes]
   read only = no
   browseable = no
   create mask = 0600
   directory mask = 0700
EOF
testparm -s > /dev/null 2>&1 || fail "testparm rejected the generated smb.conf"

for uid in alice bob carol dglobal deigen; do
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
daten sicherheit 0755 root
archiv gemeinsam 0755 root
archiv nur-alice 0750 g_alice
archiv nur-bob 0750 g_bob
archiv nur-carol 0750 g_carol
EOF

# daten: alice sees 3 + 3 + 4 (+ 2 locked + gleich), bob 3 + 3 + 1, carol 3 + 2.
for n in 1 2 3; do samba_file daten "gemeinsam/daten-gemeinsam-${n}.txt"; done
for n in 1 2 3; do samba_file daten "projekt/projekt-${n}.txt"; done
word_projekt_3="${NEXT_WORD}"
for n in 1 2 3 4; do samba_file daten "nur-alice/daten-alice-${n}.txt"; done
samba_file daten "nur-bob/daten-bob-1.txt"
for n in 1 2; do samba_file daten "nur-carol/daten-carol-${n}.txt"; done
samba_file daten "gemeinsam/gleich.txt" "zqgleichdoc"
# Plan 43-25. sicherheit: two files and nothing else, open to every account
# (0755), reached through the mounts with the root / and through the mounts on
# the sub root. EXPECTED_SEPARATE_K and NAIVE_SURPLUS in coverage_truth.sh are
# derived from exactly these two files; a third one moves both.
samba_file daten "sicherheit/sicherheit-1.txt"
word_sicherheit_1="${NEXT_WORD}"
samba_file daten "sicherheit/sicherheit-2.txt"
word_sicherheit_2="${NEXT_WORD}"
# Two files that differ in case only: two files on a Linux server, two rows in
# the file cache, two documents.
samba_file daten "gemeinsam/Bericht.txt"
word_twin_upper="${NEXT_WORD}"
samba_file daten "gemeinsam/bericht.txt"
word_twin_lower="${NEXT_WORD}"
# [homes]: a file of the same name in the home directory of alice and of bob.
# Two files that must never become one document.
homes_file() {
  # homes_file <account> <name>: a text file in the home directory, owned by the account
  local home_dir
  next_word
  home_dir=$(getent passwd "$1" | cut -d: -f6)
  printf 'Coverage proof %s\n' "${NEXT_WORD}" | sudo tee "${home_dir}/$2" > /dev/null
  sudo chown "$1:" "${home_dir}/$2"
  sudo chmod 0644 "${home_dir}/$2"
  printf '%s\t%s\n' "${NEXT_WORD}" "$2" >> "${WORDS}"
}
homes_file alice privat.txt
word_privat_alice="${NEXT_WORD}"
homes_file bob privat.txt
word_privat_bob="${NEXT_WORD}"
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

# The unreadable files of the truth, by their path on the host: locked for
# every user, and nothing else.
printf '/srv/daten/gemeinsam/gesperrt-alle.txt\n' > "${WORK}/unreadable.tsv"

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

# Plan 43-25: the cases of roots and spellings at the Samba server itself,
# before Nextcloud sees any of them.
smb_get_word() {
  # smb_get_word <uid> <share> <path> <word> <other word>: the file arrives and
  # carries its own word and not the one of its neighbour
  smb_get "$1" "$2" "$3" && grep -q -- "$4" "${WORK}/get.out" && ! grep -q -- "$5" "${WORK}/get.out"
}
smb_get_word alice daten gemeinsam/Bericht.txt "${word_twin_upper}" "${word_twin_lower}" \
  && smb_get_word alice daten gemeinsam/bericht.txt "${word_twin_lower}" "${word_twin_upper}" \
  || fail "harness finding: Samba does not hand out the two files that differ in case as two files"
smb_get_word alice homes privat.txt "${word_privat_alice}" "${word_privat_bob}" \
  && smb_get_word bob homes privat.txt "${word_privat_bob}" "${word_privat_alice}" \
  || fail "harness finding: the share homes does not give alice and bob each their own privat.txt"
smbclient "//${SMB_HOST_UPPER}/Daten" -A "${WORK}/auth-bob" -c "ls sicherheit/*" > "${WORK}/smb-ls.log" 2>&1 \
  && grep -q 'sicherheit-1.txt' "${WORK}/smb-ls.log" \
  || fail "harness finding: Samba does not answer for the share in its other spelling behind the host in upper case"
for uid in dglobal deigen; do
  smb_ls "${uid}" daten sicherheit || fail "harness finding: the Samba account ${uid} cannot list the folder sicherheit"
done
note "positive control at Samba: the case twins are two files, homes gives each account its own file, the share answers as Daten behind the host in upper case"

# ===================================================================================
# 2. Nextcloud
# ===================================================================================

step "nextcloud"
# The mode of the leg (F3, T-43-57): php -S runs on the same PHP as this CLI.
smb_mode_seen=$(php -r 'echo function_exists("smbclient_state_new") ? "native" : "wrapped";')
rows+=("| setup | smb mode (function_exists smbclient_state_new) | ${SMB_MODE} | ${smb_mode_seen} |")
[ "${smb_mode_seen}" = "${SMB_MODE}" ] || fail "the leg runs ${smb_mode_seen}, not ${SMB_MODE}, the run is invalid"
note "smb mode: ${smb_mode_seen}"
# Where the leg starts (plan 43-26). A variant that starts at rc.1 has to find
# a release candidate in both halves and in the installed version, otherwise
# it would prove an update from the head to the head. The way back needs the
# tree of the released 1.6.2.
#
# The companion is read where it is installed: the setup action moves
# findling-src/php to apps/findling (setup-test-nc, "Move the PHP companion to
# apps/findling"), so ${SRC}/php does not exist once the instance is up (run
# 42991291089, both legs from rc.1 ended here). ${SRC}/backend stays where the
# checkout put it, and the harness and the tree of 1.6.2 are never moved.
rc1_version=""
if from_rc1; then
  rc1_version=$(backend_version apps/findling) || fail "the installed companion carries no readable version"
  case "${rc1_version}" in
    *-rc.*) ;;
    *) fail "${VARIANT} was set up from version '${rc1_version}', which is no release candidate, the run is invalid" ;;
  esac
  [ "$(backend_version "${SRC}/backend")" = "${rc1_version}" ] \
    || fail "the two halves of the release candidate carry different versions, the run is invalid"
  rc1_installed=$(nc_occ config:app:get findling installed_version || echo unreadable)
  rows+=("| setup | installed_version of the companion the leg starts at | ${rc1_version} | ${rc1_installed} |")
  [ "${rc1_installed}" = "${rc1_version}" ] \
    || fail "the instance runs the companion '${rc1_installed}' and not ${rc1_version}, the run is invalid"
  note "${VARIANT} starts at ${rc1_version} in both halves"
fi
if [ -n "${OLD_BACKEND_DIR}" ]; then
  [ "$(backend_version "${OLD_BACKEND_DIR}")" = "1.6.2" ] \
    || fail "the tree for the way back carries '$(backend_version "${OLD_BACKEND_DIR}")' and not 1.6.2"
fi
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
  # smb_mount <mount point> <share> <root> <host> <mechanism> [-c key=value ...]:
  # prints the mount id
  local point="$1" share="$2" root="$3" host="$4" mechanism="$5"
  shift 5
  mount_id_of "$(nc_occ files_external:create "${point}" smb "${mechanism}" \
    -c host="${host}" -c share="${share}" -c root="${root}" -c domain="${NETBIOS}" "$@")"
}
mount_users() {
  # mount_users <mount id> <user> ...: sharing on, and the users it applies to
  local mid="$1" uid applicable=()
  shift
  [ -n "${mid}" ] || fail "files_external:create returned no mount id"
  for uid in "$@"; do
    applicable+=(--add-user "${uid}")
  done
  nc_occ files_external:option "${mid}" enable_sharing true > /dev/null
  nc_occ files_external:applicable "${mid}" "${applicable[@]}" > /dev/null
}
mount_log() {
  # mount_log <mount point> <share> <root> <users> <mechanism> <login>: one line
  # of the mount log, exactly what was typed into the configuration
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" "$5" "$6" >> "${MOUNTS}"
}
LOGIN_MECHANISM='password::logincredentials'

daten_mount=$(smb_mount /daten daten / "${SMB_HOST}" "${LOGIN_MECHANISM}")
mount_users "${daten_mount}" alice bob carol
mount_log /daten daten / 'alice bob carol' "${LOGIN_MECHANISM}" -
archiv_mount=$(smb_mount /archiv archiv / "${SMB_HOST}" "${LOGIN_MECHANISM}")
mount_users "${archiv_mount}" alice bob carol
mount_log /archiv archiv / 'alice bob carol' "${LOGIN_MECHANISM}" -
archiv_two_mount=$(smb_mount /archiv-zwei archiv / "${SMB_HOST}" "${LOGIN_MECHANISM}")
mount_users "${archiv_two_mount}" carol
mount_log /archiv-zwei archiv / carol "${LOGIN_MECHANISM}" -

# Plan 43-25: the same share daten once more, under sub roots, in another
# spelling, with ids Nextcloud hashes, and the share homes.
#
# Two sub roots. sicherheit for two users, which is at the same time the
# hashed case with log-in credentials: the product can rebuild the id from the
# configuration and the user id of the mount. projekt for one user, an id of
# exactly 64 characters that stays written out.
sicherheit_mount=$(smb_mount /daten-sicherheit daten sicherheit "${SMB_HOST}" "${LOGIN_MECHANISM}")
mount_users "${sicherheit_mount}" alice carol
mount_log /daten-sicherheit daten sicherheit 'alice carol' "${LOGIN_MECHANISM}" -
projekt_mount=$(smb_mount /daten-projekt daten projekt "${SMB_HOST}" "${LOGIN_MECHANISM}")
mount_users "${projekt_mount}" bob
mount_log /daten-projekt daten projekt bob "${LOGIN_MECHANISM}" -
# The other spelling: share Daten, the host in upper case, for bob, who also
# has the mount /daten. Two storages of one user on one tree.
spelled_mount=$(smb_mount /Daten-gross Daten / "${SMB_HOST_UPPER}" "${LOGIN_MECHANISM}")
mount_users "${spelled_mount}" bob
mount_log /Daten-gross Daten / bob "${LOGIN_MECHANISM}" -
# Hashed, the user in the configuration: bob logs in for carol. The product
# can rebuild the id from the configured user (not from the user of the mount).
password_mount=$(smb_mount /lang-kennwort daten sicherheit "${SMB_HOST}" password::password \
  -c user=bob -c password="$(password_of bob)")
mount_users "${password_mount}" carol
mount_log /lang-kennwort daten sicherheit carol password::password bob
# Hashed, global credentials of the admin: the account dglobal logs in for
# alice. The login is in the credentials store only, the id cannot be rebuilt.
global_mount=$(smb_mount /lang-global daten sicherheit "${SMB_HOST}" password::global)
mount_users "${global_mount}" alice
mount_log /lang-global daten sicherheit alice password::global dglobal
# Hashed, credentials the user entered for this storage: the account deigen
# logs in for bob. Cannot be rebuilt either.
provided_mount=$(smb_mount /lang-eigen daten sicherheit "${SMB_HOST}" password::userprovided)
mount_users "${provided_mount}" bob
mount_log /lang-eigen daten sicherheit bob password::userprovided deigen
# [homes]: one configuration, one share name, a different directory per login.
homes_mount=$(smb_mount /heim homes / "${SMB_HOST}" "${LOGIN_MECHANISM}")
mount_users "${homes_mount}" alice bob
mount_log /heim homes / 'alice bob' "${LOGIN_MECHANISM}" -

sudo mkdir -p /srv/lokal
sudo chown "$(id -un):$(id -gn)" /srv/lokal
head -c 4096 /dev/urandom > /srv/lokal/zusatz.bin
local_mount=$(mount_id_of "$(nc_occ files_external:create /lokal local null::null -c datadir=/srv/lokal)")
[ -n "${local_mount}" ] || fail "the local storage could not be created"
nc_occ files_external:applicable "${local_mount}" --add-user alice > /dev/null
mount_log /lokal - /srv/lokal alice null::null "$(id -un)"

# The credentials of the two mounts whose login no configuration names, put
# where the settings pages of Nextcloud put them and under the same names
# (apps/files_external/lib/Lib/Auth/Password/GlobalAuth.php: user '' and
# password::global for an admin mount; UserProvided.php: the user and
# password::userprovided/<mount id>), encrypted by the credentials manager.
# No browser, the same call the pages end in.
cat > "${WORK}/seed_credentials.php" << 'PHP'
<?php

declare(strict_types=1);

// seed_credentials.php <server root> <user id or ''> <identifier> <login>
// The password comes from SEED_PASS and is never printed.
if (PHP_SAPI !== 'cli' || $argc !== 5) {
	exit(2);
}
require_once $argv[1] . '/lib/base.php';
$password = getenv('SEED_PASS');
if (!is_string($password) || $password === '') {
	fwrite(STDERR, "SEED_PASS is empty\n");
	exit(2);
}
\OCP\Server::get(\OCP\Security\ICredentialsManager::class)
	->store($argv[2], $argv[3], ['user' => $argv[4], 'password' => $password]);
echo "seeded\n";
PHP
seed_credentials() {
  # seed_credentials <user id or ''> <identifier> <login at the Samba server>
  local seeded
  seeded=$(SEED_PASS=$(password_of "$3") timeout 90 php "${WORK}/seed_credentials.php" "${SERVER_ROOT}" "$1" "$2" "$3" | tail -n 1 || true)
  [ "${seeded}" = "seeded" ] \
    || fail "harness finding: the credentials of ${2%%/*} could not be stored without a browser, the case cannot be built"
}
seed_credentials '' 'password::global' dglobal
seed_credentials bob "password::userprovided/${provided_mount}" deigen

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

step "public link on a folder of an SMB mount"
# share_type 3 (plan 43-25): a link is no mount and no storage, it must not
# move any figure.
curl -s -u "alice:$(password_of alice)" -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
  -d 'path=/daten/gemeinsam' -d 'shareType=3' -d 'permissions=1' \
  "${NC_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares" -o "${WORK}/link.json"
jq -e '.ocs.meta.statuscode == 200 and .ocs.data.share_type == 3' "${WORK}/link.json" > /dev/null \
  || fail "the public link on daten/gemeinsam was not created: $(jq -c '.ocs.meta' "${WORK}/link.json" 2> /dev/null)"
nc_occ files:scan --all > /dev/null

# Exact ids from here on (sid_is): the storages of bob on daten and on Daten
# differ in spelling only.
daten_alice=$(sid_is "smb::alice@${SMB_HOST}//daten//")
daten_bob=$(sid_is "smb::bob@${SMB_HOST}//daten//")
daten_carol=$(sid_is "smb::carol@${SMB_HOST}//daten//")
# The root of daten once more for bob, through the other spelling of host and
# share (plan 43-25): a storage of its own, with its own copies of the locked
# files (locked_file_ids).
spelled_bob=$(sid_is "smb::bob@${SMB_HOST_UPPER}//Daten//")
[ -n "${spelled_bob}" ] || fail "harness finding: no storage row for the other spelling of the share of bob"
archiv_carol=$(sid_is "smb::carol@${SMB_HOST}//archiv//")
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

step "the storages of plan 43-25 exist as planned"
# Written out ids: the sub root projekt (64 characters), the other spelling,
# and homes once per user.
for pair in "projekt_bob:$(sid_is "smb::bob@${SMB_HOST}//daten//projekt/")" \
  "spelled_bob:$(sid_is "smb::bob@${SMB_HOST_UPPER}//Daten//")" \
  "homes_alice:$(sid_is "smb::alice@${SMB_HOST}//homes//")" \
  "homes_bob:$(sid_is "smb::bob@${SMB_HOST}//homes//")"; do
  [ -n "${pair#*:}" ] || fail "harness finding: no storage row with a written out id for ${pair%%:*}"
  mounted_sid "${pair#*:}" || fail "harness finding: ${pair%%:*} is not in oc_mounts"
done
# Hashed ids, one per mechanism (W4). Each id string has more than 64
# characters, Nextcloud keeps its md5, the storage is mounted and holds the
# two files of the sub root. The login is the account whose name stands in the
# id: alice herself, bob from the configuration, dglobal and deigen from the
# credentials store. A case that could not be built stops the run here, it is
# never left out.
hashed_sids=""
for pair in "password::logincredentials:alice" "password::password:bob" \
  "password::global:dglobal" "password::userprovided:deigen"; do
  hashed_login="${pair##*:}"
  hashed_text=$(hashed_id "${hashed_login}")
  [ "${#hashed_text}" -gt 64 ] || fail "the id of the ${pair%:*} mount has ${#hashed_text} characters, Nextcloud would not hash it"
  hashed_row=$(hashed_sid "${hashed_login}")
  [ -n "${hashed_row}" ] \
    || fail "harness finding: no storage row under the md5 of the ${pair%:*} id, the case could not be built without a browser"
  mounted_sid "${hashed_row}" || fail "harness finding: the ${pair%:*} storage is not in oc_mounts"
  hashed_files=$(ncdb "SELECT COUNT(*) FROM oc_filecache WHERE storage = ${hashed_row}
                         AND path IN ('sicherheit-1.txt', 'sicherheit-2.txt');")
  [ "${hashed_files}" = "2" ] \
    || fail "harness finding: the ${pair%:*} storage holds ${hashed_files} of the 2 files of its sub root, its login does not work"
  hashed_sids="${hashed_sids:+${hashed_sids},}${hashed_row}"
done
hashed_hex=$(ncdb "SELECT COUNT(*) FROM oc_storages WHERE numeric_id IN (${hashed_sids})
                     AND length(id) = 32 AND id NOT GLOB '*[^0-9a-f]*';")
rows+=("| setup | storages whose id is 32 hex, one per mechanism (W4) | 4 | ${hashed_hex} |")
[ "${hashed_hex}" = "4" ] || fail "${hashed_hex} of the 4 storages on the sub root carry a 32 hex id, the hashed case tests nothing"
# The case twins: two rows in the file cache of one storage.
twin_rows=$(ncdb "SELECT COUNT(*) FROM oc_filecache WHERE storage = ${daten_alice}
                    AND path IN ('gemeinsam/Bericht.txt', 'gemeinsam/bericht.txt');")
rows+=("| setup | file cache rows of the two files that differ in case | 2 | ${twin_rows} |")
if [ "${twin_rows}" != "2" ]; then
  note "case twins: $(ncdb "SELECT COUNT(*) FROM oc_filecache WHERE storage = ${daten_alice} AND path LIKE 'gemeinsam/_ericht.txt';") rows match without regard to case"
  fail "harness finding: the file cache holds ${twin_rows} rows for the two files that differ in case"
fi
homes_rows=$(ncdb "SELECT COUNT(*) FROM oc_filecache AS fc JOIN oc_mounts AS m ON m.storage_id = fc.storage
                    WHERE fc.path = 'privat.txt' AND m.mount_point IN ('/alice/files/heim/', '/bob/files/heim/');")
rows+=("| setup | privat.txt through the share homes, one per user | 2 | ${homes_rows} |")
[ "${homes_rows}" = "2" ] || fail "harness finding: ${homes_rows} file cache rows of privat.txt behind the share homes instead of 2"
note "mount log: $(wc -l < "${MOUNTS}") configurations"

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
  # Run 42477570073: the head container started next to the 1.6.2 companion
  # with the reconcile off found the one time catch-up of 1.5 still open
  # (main.py _the_catch_up_is_open), ran its cycle, and that cycle sweeps since
  # 43-02 (reconcile.py, SWEEP_MARK), so W5 stopped the run before phase A.
  # Right for a user: 1.6.2 had simply not finished it in the few minutes of
  # this job. 1.6.2 runs the cycle with the reconcile off as well (v1.6.2
  # main.py:1277-1282, a once task): part A in the poller on verdicts
  # generation 3, part B one reconcile round behind the quiet gate (crawl
  # over, fewer than RECONCILE_QUIET_MAX scheduled rows), checked every
  # RECONCILE_TICK_SECONDS (300 s). So the leg waits here, under 1.6.2, as a
  # longer running 1.6.2 instance would have, until CATCHUP_MARK says done.
  # Before the orphan below: the catch-up walk would otherwise take verwaist.txt
  # as gone, and the unresolved key case would test nothing (the same run
  # answered docKeysUnresolved 0 after the backfill). 1.6.2 writes no
  # storage_sweep_at at all, so W5 keeps its meaning: a sweep of the head
  # before phase A is still an invalid run.
  step "upgrade: the catch-up of 1.5 finishes under 1.6.2"
  wait_for_catchup 1.6.2
  swept_162=$(statedb "SELECT value FROM meta WHERE key = 'storage_sweep_at';" || true)
  [ -z "${swept_162}" ] || fail "storage_sweep_at is set under 1.6.2, W5 would read a sweep that is not the head's"
  # What 1.6.2 leaves in the queue for the locked files, and how it judged
  # them, before anything of the head runs (see judge_locked).
  locked_queue "under 1.6.2 before the update" "$(locked_file_ids)"
  locked_diagnosis "under 1.6.2 before the update" "$(locked_file_ids)"
  note "under 1.6.2 before the update: every queue row as file id:kind:retries: $(ncdb "SELECT COALESCE(group_concat(file_id || ':' || COALESCE(kind, '-') || ':' || retries, ' '), 'none') FROM oc_findling_queue;" || echo unreadable)"

  step "a container row without a file cache row"
  orphan=$(ncdb "SELECT fc.fileid FROM oc_filecache AS fc WHERE fc.storage = ${home_dave} AND fc.path = 'files/verwaist.txt';")
  [ -n "${orphan}" ] || fail "verwaist.txt has no file cache row"
  [ "$(statedb "SELECT COUNT(*) FROM files WHERE file_id = ${orphan} AND deleted_at IS NULL;")" = "1" ] \
    || fail "verwaist.txt has no living container row, the case tests nothing"
  # Past every event: the file goes from the disk and its row from the file
  # cache, so no job ever tells the container.
  rm -f "${NC_DATA}/dave/files/verwaist.txt"
  sqlite3 -cmd ".timeout 10000" "${NC_DB}" "DELETE FROM oc_filecache WHERE fileid = ${orphan};"
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
  if jq -e '.counting == false and .docKeysMissing == 0 and .docKeysUnresolved >= 1' "${WORK}/coverage.json" > /dev/null; then
    verdict upgrade_1_6_2 ok "1.6.2 to the head, container first, backfill ${backfill_seconds} s until counting false, $(living_rows) living rows"
  else
    echo "::warning::after the backfill /coverage answers ${answer}"
    verdict upgrade_1_6_2 failed "after the backfill /coverage answers ${answer}"
  fi
  note "upgrade: backfill done after ${backfill_seconds} s, $(log_since "${backfill_mark}" | grep -c 'doc key backfill, done=' || true) rounds, /coverage ${answer}"
  rows+=("| upgrade | docKeysMissing after the backfill | 0 | $(jq -r '.docKeysMissing' "${WORK}/coverage.json") |")
fi

# ===================================================================================
# 3c. The update of the two variants that start at rc.1 (plan 43-26)
# ===================================================================================

if from_rc1; then
  rc1_failures_before="${failures}"
  rc1_baseline
  if [ "${VARIANT}" = "upgrade-rc1" ]; then
    rc1_order="container first"
    mixed_container_first
  else
    rc1_order="companion first with a backup pause"
    mixed_companion_first_pause
  fi
  # Both halves are the head now. The figures against the truth follow in the
  # phases A and B like in every head leg; this line stands for the update
  # itself: the version moved through occ upgrade, the keys were rebuilt once
  # and the count ended.
  if [ "${failures}" = "${rc1_failures_before}" ]; then
    verdict upgrade_rc1 ok "${rc1_version} to $(backend_version "${HARNESS}/php"), ${rc1_order}, rebuild ${COUNTED_SECONDS} s until counting false, $(living_rows) living rows"
  else
    verdict upgrade_rc1 failed "${rc1_version} to $(backend_version "${HARNESS}/php"), ${rc1_order}, $((failures - rc1_failures_before)) checks differ"
  fi
fi

# ===================================================================================
# 4. B1, then the topology change
# ===================================================================================

step "B1: the denominator before and after removing the extra storage"
if [ "${VARIANT}" = "gate-crawl" ] || [ "${VARIANT}" = "gate-queue" ]; then
  # A fresh installation of the head (run 42991291089, the three legs of these
  # two variants): the document key task found no state.db at its first round
  # and came back a tick of 300 s later, so the generation gate of POST
  # /coverage answered counting until then and the round after the tick forgot
  # and asked again the 95 keys the jobs had written. read_settled below waited
  # those minutes, and the catch-up cycle swept in them (W5). Since the fix the
  # generation stands in the meta value seconds after the database is born,
  # long before the crawl and two drain periods are over, and no round has a
  # key to ask for. Both are states, not times: read here, before anything
  # waits on the count.
  fresh_mark=$(doc_key_mark)
  rows+=("| B1 | generation of the document keys on the fresh installation after the first drain | 2 | ${fresh_mark%%:*} |")
  case "${fresh_mark}" in
    2:*) ;;
    *) fail "product finding: the fresh database carries no key generation after the first drain (meta value '${fresh_mark}'), the per document count would wait for a tick of the document key task" ;;
  esac
  refilled=$(log_count 0 'doc key backfill, done=')
  rows+=("| B1 | backfill rounds on the fresh installation (keys of jobs forgotten and asked again) | 0 | ${refilled} |")
  check "B1 no backfill round on a fresh installation" 0 "${refilled}"
fi
b1_started=$(date +%s)
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
b1_seconds=$(($(date +%s) - b1_started))
note "B1: both settled reads took ${b1_seconds} s"

stop_backend

# W5: a catch-up round may sweep even with the reconcile off; then phase A
# would measure a second sweep and not the first one.
#
# The variants that start at rc.1 carry the stamp rc.1 wrote, aged before the
# head started (age_sweep_stamp); there the stamp has to be exactly that value,
# so a sweep of the head before phase A still ends the run here. Everywhere
# else the expected value is empty and the check is the one it always was.
#
# What this check rests on in gate-crawl and gate-queue, said once: a fresh
# installation has the catch-up of 1.5 open, the once task of the head looks
# at its mark when it is armed and then every RECONCILE_TICK_SECONDS (300 s),
# and its cycle sweeps. So the container that the setup action armed has to be
# stopped here within 300 s of that arming; run 42991291089 got here after
# 335 s (B1 alone waited 213 s for the count) and the cycle had swept. The
# cycle is right to sweep, so this is a limit of the harness and not of the
# product, and the check turns a run past the limit into an invalid run, never
# into a figure. The seconds B1 took are in the message for that reason.
swept_before=$(statedb "SELECT value FROM meta WHERE key = 'storage_sweep_at';" || true)
[ "${swept_before}" = "${sweep_stamp_expected}" ] \
  || fail "a catch-up round swept before phase A, the run is invalid (storage_sweep_at '${swept_before}', expected '${sweep_stamp_expected}', B1 took ${b1_seconds} s)"
note "storage_sweep_at before phase A: ${swept_before:-not set}${sweep_stamp_expected:+ (the aged stamp of rc.1, untouched by the head)}"

# The copy of the locked file on the storage the topology change is about to
# take from carol (variant upgrade, see judge_locked): whether 1.6.2 left a
# queue row for it decides what the head can say about it after phase B.
if [ "${VARIANT}" = "upgrade" ]; then
  gone_copy_before "${daten_carol}"
fi

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
[ -n "$(sid_is "smb::carol@${SMB_HOST}//daten//")" ] || fail "the daten storage of carol lost its oc_storages row, it would be gone and not stamped"
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
truth_physical
a_num_truth=$(truth_numerator_list | wc -l)
a_num_shown=$(jq -r '.coverage.indexed' "${WORK}/overview-phase-a.json")
a_den_shown=$(jq -r '.coverage.indexable' "${WORK}/overview-phase-a.json")
a_percent=$(jq -r '.coverage.percent' "${WORK}/overview-phase-a.json")
rows+=("| A | numerator, files on the host | ${a_num_truth} | ${a_num_shown} |")
if head_under_test; then
  # The head has to show the physical truth plus the two storages it cannot
  # tell (EXPECTED_SEPARATE_K), in both figures, and nothing else.
  a_num_expected=$(with_separate_k "${a_num_truth}")
  a_den_truth=$(expected_denominator_phase_a)
  a_den_expected=$(with_separate_k "${a_den_truth}")
  rows+=("| A | numerator, truth plus k=${EXPECTED_SEPARATE_K} | ${a_num_expected} | ${a_num_shown} |")
  rows+=("| A | denominator (D-43-11 rule in SQL over inodes: ${a_den_truth}) plus k=${EXPECTED_SEPARATE_K} | ${a_den_expected} | ${a_den_shown} |")
  rows+=("| A | percent | not null, at most 100 | ${a_percent} |")
  check "phase A numerator" "${a_num_expected}" "${a_num_shown}"
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
truth_physical

users_left=$(nc_occ user:list --output=json | jq -r 'keys[]' | tr '\n' ' ')
# Both lists are "<device:inode>\t<path on the host>", one line per inode and
# sorted by it (plan 43-25); they are compared by the first column only.
truth_numerator_list > "${WORK}/numerator.tsv"
truth_denominator_list "${users_left}" > "${WORK}/denominator.tsv"
b_num_truth=$(wc -l < "${WORK}/numerator.tsv")
b_den_truth=$(wc -l < "${WORK}/denominator.tsv")
b_unreadable_truth=$(truth_not_readable "${WORK}/unreadable.tsv" "${WORK}/denominator.tsv")
b_num_shown=$(jq -r '.coverage.indexed' "${WORK}/overview-phase-b.json")
b_den_shown=$(jq -r '.coverage.indexable' "${WORK}/overview-phase-b.json")
b_unreadable_shown=$(jq -r '.coverage.notReadable // "-"' "${WORK}/overview-phase-b.json")
outside=$(comm -23 <(cut -f1 "${WORK}/numerator.tsv") <(cut -f1 "${WORK}/denominator.tsv") | wc -l)
rows+=("| B | numerator, files on the host | ${b_num_truth} | ${b_num_shown} |")
rows+=("| B | denominator, files on the host (what every mounted login reaches, and the homes) | ${b_den_truth} | ${b_den_shown} |")
rows+=("| B | notReadable | ${b_unreadable_truth} | ${b_unreadable_shown} |")
rows+=("| B | searchable documents outside the denominator truth | 0 | ${outside} |")
note "phase B: the D-43-11 rule in SQL over inodes gives $(expected_denominator_phase_a) for the same state"

if head_under_test; then
  b_num_expected=$(with_separate_k "${b_num_truth}")
  b_den_expected=$(with_separate_k "${b_den_truth}")
  rows+=("| B | numerator, truth plus k=${EXPECTED_SEPARATE_K} | ${b_num_expected} | ${b_num_shown} |")
  rows+=("| B | denominator, truth plus k=${EXPECTED_SEPARATE_K} | ${b_den_expected} | ${b_den_shown} |")
  positive_control_compare "phase B numerator" "${b_num_expected}" "${b_num_shown}"
  # Positive control 3: a truth that keys by share and root as written must
  # miss the physical one by the planted number, otherwise this topology says
  # nothing about roots and spellings.
  b_num_naive=$(truth_numerator_naive | wc -l)
  rows+=("| B | positive control 3, naive numerator minus files on the host | ${NAIVE_SURPLUS} | $((b_num_naive - b_num_truth)) |")
  note "share identities of the counting (numbers only): $(jq -c '.coverage.shareIdentity // "absent"' "${WORK}/overview-phase-b.json")"
  check "phase B numerator" "${b_num_expected}" "${b_num_shown}"
  check "phase B denominator" "${b_den_expected}" "${b_den_shown}"
  check "phase B notReadable" "${b_unreadable_truth}" "${b_unreadable_shown}"
  check "phase B numerator inside the denominator" 0 "${outside}"
  # After the comparisons, so their lines are in the log when this one stops
  # the run.
  positive_control_naive "${b_num_naive}" "${b_num_truth}"
  a1=$(a1_rows_checked /srv/daten/projekt/projekt-1.txt /srv/daten/projekt/projekt-2.txt /srv/daten/projekt/projekt-3.txt)
  rows+=("| B | a1_rows_checked (files of the reshared folder: rows on two storages or more, one key) | 3 | ${a1} |")
  echo "a1_rows_checked=${a1}"
  [ "${a1}" -gt 0 ] || fail "the reshare case tests nothing, the run is invalid"
  check "a1_rows_checked" 3 "${a1}"
else
  positive_control_compare "phase B numerator" "${b_num_truth}" "${b_num_shown}"
  positive_control_reference "${b_num_truth}" "${b_num_shown}" "${b_den_truth}" "${b_den_shown}"
  note "positive control 2: 1.6.2 shows ${b_num_shown} of ${b_den_shown}, truth ${b_num_truth} of ${b_den_truth}"
fi

sleep 5
no_stale_smbclient "after phase B"
if [ "${VARIANT}" = "upgrade" ]; then
  # Only now (B3): the reconcile hands the 1.6.2 rows failed/gateway_error
  # with budget out again, and the head judges them skipped/unreadable. A
  # different verdict is a finding for the coordinator, never a looser check.
  # The topology change removed the daten storage of carol before this point:
  # the reachable locked rows stand skipped/unreadable, and its copy of
  # gesperrt-alle.txt stands skipped/gone if 1.6.2 left a queue row for it,
  # untouched if it did not (judge_locked, gone_copy_before).
  judge_locked "upgrade after phase B" "skipped/unreadable" "${head_mark}" "" "${daten_carol}" \
    "${GONE_COPY_QUEUED}" "${GONE_COPY_VERDICT}"
fi

step "search cross check"
words_unique "words before the search cross check"
# The expected count (run 42477570073): not the number of truth rows. In four
# legs the truth held 23 rows and only 22 of them carried a planted word, all
# 36 misses were outside the truth, so one indexed document of the truth has
# no word of the harness and no search can count it. The expected count is
# the number of WORDS lines whose file name is a basename in the truth: a
# word counts once per file it was written into, so the two gleich.txt (daten
# and archiv, one word each) stay two expected hits when both are in the
# truth. That is never looser than before: a word of a truth name must find
# its file (the title match of search_crosscheck), a word outside the truth
# that is found pushes found above the expected count, and the misses in the
# truth are a check of their own, so a hit outside cannot hide a miss inside.
in_truth=$(cut -f2 "${WORK}/numerator.tsv" | sed 's#.*/##' | sort -u)
cut -f2 "${WORDS}" | sort -u > "${WORK}/word-names.txt"
search_expected=0
while IFS=$'\t' read -r _ word_name; do
  if printf '%s\n' "${in_truth}" | grep -qxF -- "${word_name}"; then
    search_expected=$((search_expected + 1))
  fi
done < "${WORDS}"
# Every truth row without a planted word, by its file name (never a path, a
# host or content), so the next run names the document.
no_word=0
while IFS=$'\t' read -r _ nw_path; do
  if ! grep -qxF -- "${nw_path##*/}" "${WORK}/word-names.txt"; then
    no_word=$((no_word + 1))
    note "numerator truth row without a planted word: ${nw_path##*/}"
  fi
done < "${WORK}/numerator.tsv"
rows+=("| B | numerator truth rows without a planted word (not searchable by the harness) | - | ${no_word} |")
[ "${search_expected}" -gt 0 ] || fail "no planted word belongs to the numerator truth, the search cross check tests nothing"
# shellcheck disable=SC2086 # the user list is a word list on purpose
found=$(search_crosscheck "${WORDS}" ${users_left})
rows+=("| B | words found through the search (W4), expected words of truth names | ${search_expected} | ${found} |")
check "search cross check" "${search_expected}" "${found}"
truth_misses=0
if [ -s "${WORK}/crosscheck-missing.txt" ]; then
  note "files whose word the search does not find: $(sort "${WORK}/crosscheck-missing.txt" | tr '\n' ' ')"
  # Run 42418778026 listed 45 names for 8 missing words: most of them are
  # never searchable (backlog images, locked files). The names in the
  # numerator truth are the misses that count; each missing name comes with
  # the short form of the raw answer for the first user (entries and titles,
  # file names of the test topology, no content).
  while IFS=$'\t' read -r miss_name miss_raw; do
    if printf '%s\n' "${in_truth}" | grep -qxF -- "${miss_name}"; then
      truth_misses=$((truth_misses + 1))
      note "search miss in the numerator truth: ${miss_name}, ${miss_raw}"
    else
      note "search miss outside the numerator truth: ${miss_name}, ${miss_raw}"
    fi
  done < "${WORK}/crosscheck-raw.txt"
fi
rows+=("| B | search misses in the numerator truth | 0 | ${truth_misses} |")
check "search misses in the numerator truth" 0 "${truth_misses}"

step "search and rights are untouched by the counting (W5)"
# The document key and the share identity serve the count only (plan 43-21).
# Per user, through the unified search: each of the case twins is found under
# its own name and not under the other one, a user finds the files of his sub
# root, and a file behind the share homes is found by its owner and gives the
# other user no entry at all.
search_entries() {
  # search_entries <user> <word> [title]: the number of entries of the Findling
  # provider for the word, all of them or the ones with this title
  curl -s -G -u "$1:$(password_of "$1")" \
    -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
    --data-urlencode "term=$2" --data-urlencode "limit=25" \
    "${NC_URL}/ocs/v2.php/search/providers/findling/search" -o "${WORK}/probe.json" || true
  if [ -n "${3:-}" ]; then
    jq -r --arg name "$3" '[.ocs.data.entries[]? | select(.title == $name)] | length' "${WORK}/probe.json" 2> /dev/null || echo unreadable
  else
    jq -r '.ocs.data.entries | if type == "array" then length else "no-list" end' "${WORK}/probe.json" 2> /dev/null || echo unreadable
  fi
}
search_probe() {
  # search_probe <label> <user> <word> <title or ''> <found|none>
  local label="$1" entries seen
  entries=$(search_entries "$2" "$3" "$4")
  case "${entries}" in
    0) seen=none ;;
    '' | *[!0-9]*) seen="no answer (${entries})" ;;
    *) seen=found ;;
  esac
  rows+=("| W5 | ${label} | $5 | ${seen} |")
  check "search probe ${label}" "$5" "${seen}"
}
for uid in alice bob; do
  search_probe "${uid} finds Bericht.txt by its word" "${uid}" "${word_twin_upper}" Bericht.txt found
  search_probe "${uid} finds bericht.txt by its word" "${uid}" "${word_twin_lower}" bericht.txt found
  search_probe "${uid}, the word of Bericht.txt gives no bericht.txt" "${uid}" "${word_twin_upper}" bericht.txt none
  search_probe "${uid}, the word of bericht.txt gives no Bericht.txt" "${uid}" "${word_twin_lower}" Bericht.txt none
done
# carol has nothing of daten left but the two mounts on the sub root.
search_probe "carol finds sicherheit-1.txt below her sub root" carol "${word_sicherheit_1}" sicherheit-1.txt found
search_probe "alice finds sicherheit-2.txt below her sub root" alice "${word_sicherheit_2}" sicherheit-2.txt found
search_probe "bob finds projekt-3.txt below his sub root" bob "${word_projekt_3}" projekt-3.txt found
search_probe "alice finds her privat.txt behind homes" alice "${word_privat_alice}" privat.txt found
search_probe "bob finds his privat.txt behind homes" bob "${word_privat_bob}" privat.txt found
search_probe "bob gets no entry for the word of the privat.txt of alice" bob "${word_privat_alice}" '' none
search_probe "alice gets no entry for the word of the privat.txt of bob" alice "${word_privat_bob}" '' none

# ===================================================================================
# 7. upgrade and upgrade-rc1: back to 1.6.2, then up again with a rename (W5, G1)
# ===================================================================================

if [ -n "${OLD_BACKEND_DIR}" ]; then
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
  start_backend "${OLD_BACKEND_DIR}"
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
  # The same result once more as a verdict line, which also counts a failure.
  verdict rollback_1_6_2 "${rollback}" "doc_key column ${has_column}, index ${has_index}, a changed file judged and found by 1.6.2"

  step "rename under 1.6.2"
  code=$(dav alice MOVE notiz.txt /dev/null -H "Destination: ${NC_URL}/remote.php/dav/files/alice/notiz-umbenannt.txt")
  case "${code}" in 201 | 204) ;; *) fail "the rename of notiz.txt answered HTTP ${code}" ;; esac
  # Key format 2 (plans 43-22, 43-24): sha256 over '2' NUL share NUL share
  # path. A home storage has no share, so the share is empty and the share
  # path is the internal path. Written out here from that definition (the
  # derivations in backend/tests/fixtures/coverage_topology.json have the same
  # form), not read from the product. The first update rebuilt every key in
  # this format, 1.6.2 leaves the column alone, so the stale key under 1.6.2
  # is the format 2 key of the old path.
  old_key=$(printf '2\000%s\000%s' '' 'files/notiz.txt' | sha256sum | cut -d' ' -f1)
  new_key=$(printf '2\000%s\000%s' '' 'files/notiz-umbenannt.txt' | sha256sum | cut -d' ' -f1)
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
  verdict second_upgrade_rename "${second}" "${living} living rows, bound ${bound} s"
fi

write_result
cat "${RESULT_FILE}"
[ "${failures}" = "0" ] || {
  echo "::error::${failures} comparisons of variant ${VARIANT} differ from the truth"
  exit 1
}
