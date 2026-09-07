#!/bin/sh
# The install path of a stranger, walked by hand on a fresh instance.
#
# .github/workflows/deploy-harp.yml walks this path on every run, over four
# server versions, and it is the reference this script deliberately copies. What
# CI cannot do is the part this file exists for: an instance that has never seen
# a line of Findling, set up the way a selfhoster sets one up, with the system
# cron of that instance as the clock and without the shortcuts a test job allows
# itself.
#
# Two rules decide almost every detail below.
#
#   1. Nothing comes out of the working tree. Both halves arrive as the two
#      release archives, the image comes out of the registry the archive names,
#      and the route list is read by AppAPI out of that archive. A test that
#      reaches into a checkout proves nothing about a store installation
#      (pitfall 8 of 06.1-RESEARCH).
#   2. Nothing measures our own access. The image pull is attempted with an
#      empty credential store before anything is installed, and a failure is a
#      finding that stops this script rather than a reason to log in
#      (assumption A6, threat T-06.1-66).
#
# The script builds nothing and fetches nothing from a checkout: it takes the
# address of the instance, the account names of the administrator and the
# ordinary user, and the two archives as arguments. Building and signing the
# archives is the release process and lives in scripts/release/store-archive.sh
# and .github/workflows/release.yml.
#
# The two passwords are NOT arguments. The security audit of plan 06.1-17 found
# them in the argument list, where any account on the same machine reads them
# out of the process list for as long as the run lasts, and a run of this script
# lasts the better part of an hour. They come out of FINDLING_ADMIN_PASS and
# FINDLING_USER_PASS, a --admin or --user value that still carries a colon is
# refused rather than quietly used, and every call that needs a login reads it
# from a curl configuration file in the working directory of the run, which is
# removed with that directory. Refusing rather than accepting and warning,
# because by the time the warning is printed the password has already stood in
# the process list (DI-06.1-18).
#
# It is written for both environments. The difference between the amd64 run and
# the arm64 run on the box is --aio-image-tag plus --platform, and nothing else.
#
# POSIX sh, and no dependency beyond curl, docker, tar and the occ of the
# instance. No jq: the two JSON answers this script reads are checked with a
# narrow pattern each, and every one of those patterns is spelled out where it
# is used.
set -eu

# ---------------------------------------------------------------------------
# Defaults. Every one of them can be overridden on the command line, and every
# one of them is printed into the log before the first step runs, because a
# protocol that does not say what it assumed is a protocol nobody can repeat.
# ---------------------------------------------------------------------------
INSTANCE_URL=""
ADMIN_UID=""
USER_UID=""
EXEC_PREFIX=""
COMPANION_ARCHIVE=""
BACKEND_ARCHIVE=""
ARCHIVE_VERSION=""
DAEMON_NAME=""
APPS_DIR="custom_apps"
STAGE_DIR="/tmp/findling-store-check"
LOG_FILE=""

# The AIO image tag. This is the one knob that carries the whole arm64 half of
# decision E-H5: all-in-one publishes its own tag for that architecture, so the
# same schedule runs on the box with --aio-image-tag latest-arm64 --platform
# linux/arm64 and is otherwise identical. On a docker-compose instance the tag
# has no counterpart, and the script says so in the log instead of pretending to
# check something.
AIO_IMAGE_TAG="latest"
FLAVOUR="compose"
AIO_CONTAINER="nextcloud-aio-nextcloud"
PLATFORM="linux/amd64"

# The image tag substitution, off by default. The archive names
# registry/image/image-tag and AppAPI pulls exactly that reference. Before the
# release tag exists that reference does not exist either, and CI answers that
# with a named finding on a branch and a hard failure on main. The same rule
# here: without this option a missing tag stops the run.
TAG_SUBSTITUTE=""

# The clocks. The budget of the zero config proof is counted in cron rounds and
# not in seconds, and that is the whole point of pitfall 4 of 06.1-RESEARCH:
# plan 06-11 declared a healthy run dead by 52 seconds because it measured its
# own guess instead of the slowest clock involved. The slowest clock here is the
# system cron of the instance, which runs every five minutes, so the unit of the
# budget is one cron round and the seconds are derived from it and never the
# other way round.
CRON_INTERVAL_SECONDS=300
ZERO_CONFIG_CRON_ROUNDS=6
CRON_DRIVER="script"
SETTLE_SECONDS=10

# Whether a local copy of the image may be deleted so that the deploy daemon has
# to fetch it from the registry itself. Off by default because this script runs
# on a developer machine that may hold that image for other work.
RMI_LOCAL_IMAGE=0
KEEP_INSTALLATION=0
TAMPER_PROBE=1
DB_TABLES_CMD=""

# The upper bound of a single occ call. app_api:app:register --wait-finish waits
# for the container to report that its initialisation finished, and when that
# report cannot reach Nextcloud it waits for ever: measured on 06.09.2026, where
# a healthy container ran while the registration never returned. A run that
# hangs teaches nobody anything, so every occ call carries a limit and an
# overrun is a finding. The value covers an image pull of about a gigabyte plus
# the initialisation behind it.
OCC_TIMEOUT=1800
TIMEOUT_CMD=""

# The invented search word, and it is invented on purpose. The German analyzer
# splits compounds against a dictionary, so a real compound can be indexed as
# its parts and a miss would say nothing about the index. deploy-harp.yml uses
# the same word for the same reason, which keeps the two protocols comparable.
ZERO_CONFIG_WORD="florpel"
ZERO_CONFIG_FILE="findling-zero-config.txt"

usage() {
	cat <<'USAGE'
usage: aio_install_check.sh --url URL --admin USER --exec CMD
                            --companion FILE --backend FILE --version X.Y.Z
                            --daemon NAME [options]

Walks the install path of a stranger on one fresh instance and writes one log
line per step with the result and the duration.

Required:
  --url URL             address of the instance, for instance http://localhost:8097
  --admin USER          administrator of that instance, account name only
  --exec CMD            how to run a command inside the instance, as the web
                        server user and with the Nextcloud web root as the
                        working directory. Examples:
                          compose: "docker exec -i -u www-data -w /var/www/html findling-store-nc"
                          AIO:     "docker exec -i --user www-data -w /var/www/html nextcloud-aio-nextcloud"
  --companion FILE      findling.tar.gz of the release, signed
  --backend FILE        findling_backend.tar.gz of the release
  --version X.Y.Z       the version both archives are expected to carry
  --daemon NAME         the AppAPI deploy daemon to install into

Environment:
  FINDLING_ADMIN_PASS   password of the administrator. Read from the environment
                        and never from the command line, because an argument is
                        readable in the process list of the machine for as long
                        as the run lasts. A --admin or --user value that carries
                        a colon is refused for the same reason.
  FINDLING_USER_PASS    password of the ordinary user
                        (default: FINDLING_ADMIN_PASS)

                        Example:
                          FINDLING_ADMIN_PASS=secret \
                            scripts/dev/aio_install_check.sh --admin admin ...

Options:
  --user USER           ordinary user for the upload and the search, account
                        name only (default: the administrator)
  --apps-dir DIR        app directory inside the instance, relative to the web
                        root (default: custom_apps)
  --stage-dir DIR       staging directory inside the instance for the backend
                        archive (default: /tmp/findling-store-check)
  --aio-image-tag TAG   the all-in-one image tag of the instance
                        (default: latest, on the ARM box: latest-arm64)
  --flavour compose|aio which way the instance was set up (default: compose)
  --aio-container NAME  the AIO master container (default: nextcloud-aio-nextcloud)
  --platform PLATFORM   docker platform of the pull (default: linux/amd64)
  --substitute-tag TAG  install against this image tag instead of the one the
                        archive names, and record the substitution as a finding.
                        Only for a run before the release tag exists.
  --cron-driver system|script
                        who drives the background jobs. system means the
                        instance has its own cron and this script only waits one
                        interval per round; script means nothing drives it and
                        this script calls cron.php once per round, which is the
                        identical command a system cron runs (default: script)
  --cron-interval SEC   the interval of that system cron (default: 300)
  --cron-rounds N       budget of the zero config proof in cron rounds
                        (default: 6)
  --db-tables-cmd CMD   a command that prints the oc_findling_* tables of the
                        instance, one per line. Without it the table half of
                        uninstall promises 4 and 5 is reported as not performed
                        rather than silently passed.
  --occ-timeout SEC     upper bound of a single occ call (default: 1800)
  --rmi-local-image     delete a local copy of the image after the anonymous
                        pull so the deploy daemon has to fetch it itself
  --no-tamper-probe     skip the falsification of the integrity check
  --keep                leave the installation in place at the end
  --log FILE            protocol file (default: a file in the current directory)
  -h, --help            this text
USAGE
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [ "$#" -gt 0 ]; do
	case "$1" in
		--url) INSTANCE_URL="$2"; shift 2 ;;
		--admin) ADMIN_UID="$2"; shift 2 ;;
		--user) USER_UID="$2"; shift 2 ;;
		--exec) EXEC_PREFIX="$2"; shift 2 ;;
		--companion) COMPANION_ARCHIVE="$2"; shift 2 ;;
		--backend) BACKEND_ARCHIVE="$2"; shift 2 ;;
		--version) ARCHIVE_VERSION="$2"; shift 2 ;;
		--daemon) DAEMON_NAME="$2"; shift 2 ;;
		--apps-dir) APPS_DIR="$2"; shift 2 ;;
		--stage-dir) STAGE_DIR="$2"; shift 2 ;;
		--aio-image-tag) AIO_IMAGE_TAG="$2"; shift 2 ;;
		--flavour) FLAVOUR="$2"; shift 2 ;;
		--aio-container) AIO_CONTAINER="$2"; shift 2 ;;
		--platform) PLATFORM="$2"; shift 2 ;;
		--substitute-tag) TAG_SUBSTITUTE="$2"; shift 2 ;;
		--cron-driver) CRON_DRIVER="$2"; shift 2 ;;
		--cron-interval) CRON_INTERVAL_SECONDS="$2"; shift 2 ;;
		--cron-rounds) ZERO_CONFIG_CRON_ROUNDS="$2"; shift 2 ;;
		--db-tables-cmd) DB_TABLES_CMD="$2"; shift 2 ;;
		--occ-timeout) OCC_TIMEOUT="$2"; shift 2 ;;
		--rmi-local-image) RMI_LOCAL_IMAGE=1; shift ;;
		--no-tamper-probe) TAMPER_PROBE=0; shift ;;
		--keep) KEEP_INSTALLATION=1; shift ;;
		--log) LOG_FILE="$2"; shift 2 ;;
		-h|--help) usage; exit 0 ;;
		*) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
	esac
done

for required in INSTANCE_URL ADMIN_UID EXEC_PREFIX COMPANION_ARCHIVE \
	BACKEND_ARCHIVE ARCHIVE_VERSION DAEMON_NAME; do
	eval "value=\${$required}"
	if [ -z "${value}" ]; then
		echo "missing argument for ${required}" >&2
		usage >&2
		exit 2
	fi
done

# The refusal of the audit finding. See the header: a password that reached this
# point as an argument has already stood in the process list, so accepting it
# and printing a note would be a warning about something that already happened.
for named in ADMIN_UID USER_UID; do
	eval "value=\${$named}"
	case "${value}" in
		*:*)
			echo "--admin and --user take the account name only, and ${named} carries a colon." >&2
			echo "The passwords belong in FINDLING_ADMIN_PASS and FINDLING_USER_PASS," >&2
			echo "because an argument is readable in the process list of this machine." >&2
			exit 2
			;;
	esac
done

ADMIN_PASSWORD="${FINDLING_ADMIN_PASS:-}"
if [ -z "${ADMIN_PASSWORD}" ]; then
	echo "FINDLING_ADMIN_PASS is empty or unset, so the run has no password for ${ADMIN_UID}." >&2
	echo "Set it in the environment of the call, never as an argument." >&2
	exit 2
fi
USER_PASSWORD="${FINDLING_USER_PASS:-}"
if [ -z "${USER_UID}" ]; then
	USER_UID="${ADMIN_UID}"
	USER_PASSWORD="${ADMIN_PASSWORD}"
fi
if [ -z "${USER_PASSWORD}" ]; then
	echo "FINDLING_USER_PASS is empty or unset, so the run has no password for ${USER_UID}." >&2
	echo "Set it in the environment of the call, never as an argument." >&2
	exit 2
fi

[ -n "${LOG_FILE}" ] || LOG_FILE="./install-check-$(date -u +%Y%m%dT%H%M%SZ).log"

WORK_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t findling-install-check)
: > "${LOG_FILE}"

# One credentials file per account, and every curl call that needs a login reads
# it with -K. curl -u "user:password" would take the password out of the
# argument list of this script only to put it into the argument list of curl,
# once per call, which is the finding and not a smaller version of it. The files
# live in the working directory of the run, they are created with no permission
# for anybody but the owner, and the cleanup takes the directory with them.
#
# curl reads a double quoted value with backslash escapes, so a password
# carrying a backslash or a quotation mark is escaped here rather than left to
# break the file in a way that reads like a wrong password.
ADMIN_CONF="${WORK_DIR}/admin.curlrc"
USER_CONF="${WORK_DIR}/user.curlrc"
ADMIN_PASSWORD_FILE="${WORK_DIR}/admin.password"

write_credentials() {  # $1 target file, $2 account, $3 password
	escaped=$(printf '%s' "$3" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
	: > "$1"
	chmod 600 "$1"
	printf 'user = "%s:%s"\n' "$2" "${escaped}" >> "$1"
}

write_credentials "${ADMIN_CONF}" "${ADMIN_UID}" "${ADMIN_PASSWORD}"
write_credentials "${USER_CONF}" "${USER_UID}" "${USER_PASSWORD}"

# The session login further down posts the password as a form field rather than
# as an authorization header, and --data-urlencode "name@file" is how curl reads
# such a field out of a file. Without a trailing newline, because curl sends the
# content of the file verbatim and a newline would be part of the password.
: > "${ADMIN_PASSWORD_FILE}"
chmod 600 "${ADMIN_PASSWORD_FILE}"
printf '%s' "${ADMIN_PASSWORD}" >> "${ADMIN_PASSWORD_FILE}"

# Every occ call of this run goes through one function, and that function
# records before it runs. The zero config proof further down has to be able to
# state which commands ran between the installation and the first hit, and a
# list somebody keeps by hand is a list that goes stale. The limit of the method
# is stated here rather than left to be discovered: a call that goes around this
# function is invisible to the record.
OCC_LOG="${WORK_DIR}/occ-calls.txt"
: > "${OCC_LOG}"

# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { printf '%s %s\n' "$(stamp)" "$*" | tee -a "${LOG_FILE}"; }
finding() { log "FINDING: $*"; }

STEP_NAME=""
STEP_START=0
step_begin() {
	STEP_NAME="$1"
	STEP_START=$(date +%s)
	log "STEP ${STEP_NAME}: start"
}
step_end() {
	log "STEP ${STEP_NAME}: $1 after $(( $(date +%s) - STEP_START ))s"
}
die() {
	finding "$*"
	log "the run stopped at step ${STEP_NAME}"
	exit 1
}

# The two ways into the instance. EXEC_PREFIX is expanded unquoted on purpose:
# it is a command prefix of several words, and this is the one place in this
# script where word splitting is wanted.
inst() { $EXEC_PREFIX "$@"; }
occ() {
	printf 'occ %s\n' "$*" >> "${OCC_LOG}"
	if [ -n "${TIMEOUT_CMD}" ]; then
		"${TIMEOUT_CMD}" "${OCC_TIMEOUT}" $EXEC_PREFIX php occ "$@"
	else
		$EXEC_PREFIX php occ "$@"
	fi
}

# A number out of a piece of JSON, by a narrow pattern and not by a parser.
#
# Two rules learned the hard way on 06.09.2026, when a first version of this
# read "indexed 41 of 0 indexable" out of a healthy answer. First, the search is
# done with grep -o and the first match is taken: a sed pattern that begins with
# .* is greedy and silently reports the LAST occurrence of a key, and this
# answer carries indexed twice, once for this side and once inside coverage.
# Second, the caller narrows the text to the object it means before it asks for
# a key, which is what json_object below is for. A number may carry a decimal
# point, because the coverage share is a share and not a count.
json_number() {
	printf '%s' "$2" | grep -o "\"$1\":[0-9][0-9.]*" | head -1 | sed -e 's/.*://' -e 's/\.$//'
}
# The body of a named object of a JSON answer, whitespace removed. Only the
# first level of it: the objects this script reads carry numbers and flags and
# no nested object, and a pattern that tried to balance braces would be a parser
# written in sed.
json_object() {
	tr -d ' \n\r' < "$2" | sed -n 's/.*"'"$1"'":{\([^}]*\)}.*/\1/p'
}

# ---------------------------------------------------------------------------
# Cleanup. A run that stops in the middle must not leave a half registered ExApp
# on somebody's instance, which is the whole reason this is a trap and not a
# final step.
# ---------------------------------------------------------------------------
INSTALL_STARTED=0
RUN_COMPLETE=0
cleanup() {
	status=$?
	set +e
	if [ "${KEEP_INSTALLATION}" -eq 1 ]; then
		log "cleanup: --keep was given, the installation stays as it is"
	elif [ "${INSTALL_STARTED}" -eq 1 ]; then
		log "cleanup: taking the installation off the instance"
		occ app_api:app:unregister findling_backend --rm-data >/dev/null 2>&1
		occ findling:purge --arm --no-interaction >/dev/null 2>&1
		occ app:remove findling >/dev/null 2>&1
		left=$(docker ps -a --filter 'name=findling_backend' --format '{{.Names}}')
		if [ -n "${left}" ]; then
			docker rm -f ${left} >/dev/null 2>&1
			log "cleanup: removed the container ${left}"
		fi
		inst rm -rf "${STAGE_DIR}" >/dev/null 2>&1
		log "cleanup: done"
	fi
	rm -rf "${WORK_DIR}"
	if [ "${RUN_COMPLETE}" -eq 1 ]; then
		log "the protocol of this run is ${LOG_FILE}"
	fi
	exit "${status}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# ---------------------------------------------------------------------------
# Step 0, the ground this run stands on
# ---------------------------------------------------------------------------
step_begin "0 preflight, the instance and the two archives"
log "instance url ${INSTANCE_URL}"
log "instance exec ${EXEC_PREFIX}"
log "flavour ${FLAVOUR}, aio image tag ${AIO_IMAGE_TAG}, platform ${PLATFORM}"
log "archives ${COMPANION_ARCHIVE} and ${BACKEND_ARCHIVE}, expected version ${ARCHIVE_VERSION}"
log "deploy daemon ${DAEMON_NAME}"

for tool in curl docker tar; do
	command -v "${tool}" >/dev/null 2>&1 || die "${tool} is not on the path, and this script needs it"
done
TIMEOUT_CMD=$(command -v timeout 2>/dev/null || true)
if [ -n "${TIMEOUT_CMD}" ]; then
	log "every occ call is limited to ${OCC_TIMEOUT}s"
else
	finding "no timeout command on this host, so an occ call that never returns would hang this run"
fi
[ -f "${COMPANION_ARCHIVE}" ] || die "the companion archive ${COMPANION_ARCHIVE} does not exist"
[ -f "${BACKEND_ARCHIVE}" ] || die "the backend archive ${BACKEND_ARCHIVE} does not exist"

mkdir -p "${WORK_DIR}/extract"
tar -xzf "${BACKEND_ARCHIVE}" -C "${WORK_DIR}/extract"
tar -xzf "${COMPANION_ARCHIVE}" -C "${WORK_DIR}/extract"
ARCHIVE_INFO="${WORK_DIR}/extract/findling_backend/appinfo/info.xml"
COMPANION_INFO="${WORK_DIR}/extract/findling/appinfo/info.xml"
[ -f "${ARCHIVE_INFO}" ] || die "the backend archive carries no findling_backend/appinfo/info.xml"
[ -f "${COMPANION_INFO}" ] || die "the companion archive carries no findling/appinfo/info.xml"

read_version() { sed -n 's:.*<version>\([^<]*\)</version>.*:\1:p' "$1" | head -1; }
backend_version=$(read_version "${ARCHIVE_INFO}")
companion_version=$(read_version "${COMPANION_INFO}")
log "the backend archive says version ${backend_version}, the companion archive says ${companion_version}"
if [ "${backend_version}" != "${ARCHIVE_VERSION}" ] || [ "${companion_version}" != "${ARCHIVE_VERSION}" ]; then
	die "the archives do not both carry version ${ARCHIVE_VERSION}, so this run would report a version it did not install"
fi
if [ ! -s "${WORK_DIR}/extract/findling/appinfo/signature.json" ]; then
	die "the companion archive carries no appinfo/signature.json, and integrity:check-app would skip it and answer 0"
fi
log "the companion archive carries appinfo/signature.json"

status_line=$(occ status 2>&1 | tr -d '\r' | tr '\n' ' ')
log "occ status: ${status_line}"
case "${status_line}" in
	*installed*true*) ;;
	*) die "the instance does not answer occ status with an installed server" ;;
esac

# Fresh means fresh. An instance that already knows one of the two halves would
# let this run inherit a state nobody wrote down, and the whole point of the run
# is an instance that has never seen a line of Findling.
if occ app:list 2>/dev/null | grep -q 'findling'; then
	die "the instance already knows an app called findling, so this is not a fresh instance"
fi
if occ app_api:app:list 2>/dev/null | grep -q 'findling_backend'; then
	die "the instance already knows an ExApp called findling_backend, so this is not a fresh instance"
fi
log "the instance knows neither half yet"

# The address a HUMAN gets, which is not the address this script uses.
#
# Every check below goes through basic authentication against --url, and basic
# authentication carries the whole address in every request. A browser does not:
# it follows the redirect Nextcloud sends after the login, and Nextcloud builds
# that redirect from overwrite.cli.url and overwritehost. The official server
# image leaves overwrite.cli.url at "http://localhost" without a port when the
# compose file does not set OVERWRITECLIURL, so an instance published on any
# other port sends the browser to port 80.
#
# Measured on 07.09.2026 during the owner sight check of plan 06.1-19: every API
# assertion of this script passed, the search answered, the admin page answered,
# and the owner got ERR_CONNECTION_REFUSED after logging in. A run that is green
# on an instance no person can use is exactly the shape of finding this phase
# exists to remove, so it is named here.
#
# A finding and not a die: the mismatch breaks nothing this script measures, and
# an instance that is only ever driven by API is legitimately configured this
# way. The remedy is one line in the compose file (OVERWRITECLIURL) or one occ
# call, and it belongs to whoever set the instance up.
overwrite_url=$(occ config:system:get overwrite.cli.url 2>/dev/null | tr -d '\r\n' || true)
instance_authority=${INSTANCE_URL#*://}
if [ -z "${overwrite_url}" ]; then
	finding "the instance has no overwrite.cli.url, so a browser may be redirected somewhere other than ${INSTANCE_URL} after a login"
elif [ "${overwrite_url#*://}" != "${instance_authority}" ]; then
	finding "overwrite.cli.url is '${overwrite_url}' while this run drives ${INSTANCE_URL}; every check below still holds, but a browser is redirected to '${overwrite_url}' after a login and a person may land on a refused connection"
else
	log "overwrite.cli.url is '${overwrite_url}', so a browser lands where this run drives"
fi

# The clock. This is read and named rather than assumed, because every wait of
# this script is a multiple of it (pitfall 4).
cron_mode=$(occ config:app:get core backgroundjobs_mode 2>/dev/null | tr -d '\r\n' || true)
[ -n "${cron_mode}" ] || cron_mode="unset, which Nextcloud reads as ajax"
log "the background job mode of this instance is '${cron_mode}'"
log "the cron interval used for every wait below is ${CRON_INTERVAL_SECONDS}s, driven by the ${CRON_DRIVER}"
log "the zero config budget is ${ZERO_CONFIG_CRON_ROUNDS} cron rounds, which is $(( ZERO_CONFIG_CRON_ROUNDS * CRON_INTERVAL_SECONDS ))s of system cron time"

if [ "${FLAVOUR}" = "aio" ]; then
	aio_image=$(docker inspect --format '{{.Config.Image}}' "${AIO_CONTAINER}" 2>/dev/null || true)
	if [ -z "${aio_image}" ]; then
		die "the flavour is aio but no container named ${AIO_CONTAINER} answers, so nothing here knows which all-in-one this is"
	fi
	log "the all-in-one container ${AIO_CONTAINER} runs ${aio_image}, expected tag ${AIO_IMAGE_TAG}"
	case "${aio_image}" in
		*":${AIO_IMAGE_TAG}") ;;
		*) finding "the all-in-one container runs '${aio_image}' while --aio-image-tag says '${AIO_IMAGE_TAG}'" ;;
	esac
else
	log "the flavour is ${FLAVOUR}, so the all-in-one image tag ${AIO_IMAGE_TAG} is recorded and not checked"
fi
step_end "ok"

# ---------------------------------------------------------------------------
# Step 1, the image out of the registry, without any credentials.
#
# This is assumption A6 and threat T-06.1-66, and it runs before anything is
# installed because it costs a minute and because a stranger install test that
# measures our own registry access measures nothing. A failure here is a finding
# and stops the run; logging in and then claiming a stranger could do the same
# is the one thing this step exists to prevent.
#
# The reference is read out of the archive and never written here, because the
# archive is what AppAPI reads. Today that reference is ghcr.io and the image
# path of this project; the day it moves, this step follows the archive and not
# a string in this file.
# ---------------------------------------------------------------------------
step_begin "1 the anonymous pull, assumption A6"
registry=$(sed -n 's:.*<registry>\(.*\)</registry>.*:\1:p' "${ARCHIVE_INFO}" | head -1)
image=$(sed -n 's:.*<image>\(.*\)</image>.*:\1:p' "${ARCHIVE_INFO}" | head -1)
tag=$(sed -n 's:.*<image-tag>\(.*\)</image-tag>.*:\1:p' "${ARCHIVE_INFO}" | head -1)
if [ -z "${registry}" ] || [ -z "${image}" ] || [ -z "${tag}" ]; then
	die "the archive info.xml does not name registry, image and image-tag, so nothing here knows what to pull"
fi
IMAGE_PATH="${registry}/${image}"
RELEASED="${IMAGE_PATH}:${tag}"
log "the archive asks for ${RELEASED}"

# An empty docker configuration, created here and exported for every docker
# command of this run. Not a flag on one call: the deploy daemon pulls through
# the same docker daemon, so the credential store it reads has to be the empty
# one too.
DOCKER_CONFIG="${WORK_DIR}/docker-anonymous"
export DOCKER_CONFIG
mkdir -p "${DOCKER_CONFIG}"
log "docker configuration directory ${DOCKER_CONFIG}, contents: $(ls -A "${DOCKER_CONFIG}" | tr '\n' ' ')"

STORE_INFO_LOCAL="${ARCHIVE_INFO}"
REFERENCE="${RELEASED}"
if docker buildx imagetools inspect "${RELEASED}" > "${WORK_DIR}/manifest-released.txt" 2>&1; then
	log "the tag the archive names exists, so the archive info.xml is used byte for byte"
else
	cat "${WORK_DIR}/manifest-released.txt" >> "${LOG_FILE}"
	if [ -z "${TAG_SUBSTITUTE}" ]; then
		die "${RELEASED} does not exist in the registry, and that is a store installation that would fail at a user's instance"
	fi
	finding "${RELEASED} does not exist in the registry; this run installs against the tag ${TAG_SUBSTITUTE} instead, on the same terms deploy-harp.yml uses on a branch"
	REFERENCE="${IMAGE_PATH}:${TAG_SUBSTITUTE}"
	docker buildx imagetools inspect "${REFERENCE}" > "${WORK_DIR}/manifest-substitute.txt" 2>&1 \
		|| die "${REFERENCE} does not exist either, so there is nothing to install"
	STORE_INFO_LOCAL="${WORK_DIR}/info-store.xml"
	sed -e "s|<image-tag>[^<]*</image-tag>|<image-tag>${TAG_SUBSTITUTE}</image-tag>|" \
		"${ARCHIVE_INFO}" > "${STORE_INFO_LOCAL}"
	# Exactly one line differs, and it is shown rather than described. The
	# routes block above all comes out of the archive unchanged.
	#
	# Both sides are compared without their carriage returns, and that is not
	# cosmetic: an archive built on a checkout with CRLF line endings is read
	# by sed here and written back with the line endings the tool of that host
	# produces, and a comparison that counts those as differences reports the
	# whole file instead of the one line. The substitution itself works on the
	# original bytes; only this count is normalised.
	tr -d '\r' < "${ARCHIVE_INFO}" > "${WORK_DIR}/info-archive.cmp"
	tr -d '\r' < "${STORE_INFO_LOCAL}" > "${WORK_DIR}/info-store.cmp"
	diff "${WORK_DIR}/info-archive.cmp" "${WORK_DIR}/info-store.cmp" >> "${LOG_FILE}" 2>&1 || true
	changed=$(diff "${WORK_DIR}/info-archive.cmp" "${WORK_DIR}/info-store.cmp" | grep -c '^[<>]' || true)
	[ "${changed}" -eq 2 ] || die "the substitution changed ${changed} lines instead of the one image-tag line"
	log "the substitution changed exactly the image-tag line"
fi

had_locally=0
docker image inspect "${REFERENCE}" >/dev/null 2>&1 && had_locally=1
docker pull --platform "${PLATFORM}" "${REFERENCE}" >> "${LOG_FILE}" 2>&1 \
	|| die "the pull of ${REFERENCE} failed with an empty credential store, so a stranger cannot fetch this image; this is a finding and not a reason to log in"
DIGEST=$(docker image inspect --format '{{index .RepoDigests 0}}' "${REFERENCE}")
log "pulled anonymously: ${DIGEST}"

if [ "${had_locally}" -eq 1 ] && [ "${RMI_LOCAL_IMAGE}" -eq 0 ]; then
	finding "the image was already on this host before the run, so the deploy daemon below may find it locally and never touch the registry; the pull above still proves the anonymous access, and --rmi-local-image makes the second half provable too"
else
	docker rmi "${REFERENCE}" >/dev/null 2>&1 || true
	log "the local copy is gone, the deploy daemon has to pull it again"
fi
step_end "ok, A6 confirmed for ${REFERENCE}"

# ---------------------------------------------------------------------------
# Step 2, the companion out of the archive, verified by the instance.
#
# occ integrity:check-app reads appinfo/signature.json, validates the
# certificate against resources/codesigning/root.crt, verifies the signature
# over the hash list and recomputes the SHA-512 of every file the app ships. No
# network and no store are involved, which is why it works on a fresh instance
# at all. The trap that makes a naive version of this a false green: CheckApp
# skips an app without a signature.json and returns 0 while printing "App
# signature not found, skipping app integrity check". So the file is asserted to
# be there, that sentence is asserted to be absent, and the output is asserted
# to be empty on top.
# ---------------------------------------------------------------------------
step_begin "2 the companion out of the archive"
INSTALL_STARTED=1
inst tar -xz -C "${APPS_DIR}" < "${COMPANION_ARCHIVE}" \
	|| die "the companion archive could not be unpacked into ${APPS_DIR} of the instance"
inst test -f "${APPS_DIR}/findling/appinfo/signature.json" \
	|| die "the extracted companion carries no appinfo/signature.json, and integrity:check-app would skip it and answer 0"
occ app:enable findling >> "${LOG_FILE}" 2>&1 || die "occ app:enable findling failed"
log "the companion is unpacked and enabled, and not one path led into a working tree"

check_integrity() {
	status=0
	occ integrity:check-app findling > "$1" 2>&1 || status=$?
	cat "$1" >> "${LOG_FILE}"
	return "${status}"
}

status=0
check_integrity "${WORK_DIR}/integrity-clean.txt" || status=$?
[ "${status}" -eq 0 ] || die "occ integrity:check-app findling answered ${status} on an untouched archive installation"
if grep -q 'skipping app integrity check' "${WORK_DIR}/integrity-clean.txt"; then
	die "the check skipped the app instead of verifying it, so the exit code above says nothing"
fi
if [ -s "${WORK_DIR}/integrity-clean.txt" ]; then
	die "occ integrity:check-app findling printed something, and a clean verdict is an empty answer"
fi
log "occ integrity:check-app findling: empty answer, verdict clean"

if [ "${TAMPER_PROBE}" -eq 1 ]; then
	# The falsification, and the reason the check above means anything. One
	# appended line in one shipped file, and the verdict has to turn.
	probe="${APPS_DIR}/findling/lib/AppInfo/Application.php"
	probe_backup="${STAGE_DIR}-probe-original"
	inst cp "${probe}" "${probe_backup}" || die "the probe copy of ${probe} could not be made"
	inst sh -c "printf '\n// a single line appended by the tamper probe of plan 06.1-16\n' >> ${probe}"
	status=0
	check_integrity "${WORK_DIR}/integrity-tampered.txt" || status=$?
	if [ "${status}" -eq 0 ]; then
		die "one altered file did not change the verdict, so the integrity check of this instance is not checking"
	fi
	grep -q 'INVALID_HASH' "${WORK_DIR}/integrity-tampered.txt" \
		|| die "the check failed but did not name the altered file as an invalid hash, so it failed for another reason"
	log "tamper probe: one altered line, verdict INVALID_HASH, exit ${status}"
	inst cp "${probe_backup}" "${probe}"
	inst rm -f "${probe_backup}"
	status=0
	check_integrity "${WORK_DIR}/integrity-restored.txt" || status=$?
	if [ "${status}" -ne 0 ] || [ -s "${WORK_DIR}/integrity-restored.txt" ]; then
		die "the restored file does not verify again, so the probe left the installation in a state nobody meant"
	fi
	log "restored: empty answer, verdict clean again"
else
	finding "the tamper probe was skipped, so the clean verdict above is unfalsified"
fi
step_end "ok"

# ---------------------------------------------------------------------------
# Step 3, the ExApp out of the archive, image out of the registry.
#
# The info.xml handed to app_api:app:register is the one out of the archive,
# unchanged apart from an image tag substitution that was printed as a diff
# above. That is not a detail: pre-info.xslt drops the routes block, so the
# store database never sees the routes of this container and AppAPI reads them
# out of the archive at installation time.
# ---------------------------------------------------------------------------
step_begin "3 the ExApp out of the archive"
inst sh -c "rm -rf ${STAGE_DIR} && mkdir -p ${STAGE_DIR}"
inst tar -xz -C "${STAGE_DIR}" < "${BACKEND_ARCHIVE}" \
	|| die "the backend archive could not be unpacked into ${STAGE_DIR} of the instance"
INSTANCE_INFO_XML="${STAGE_DIR}/findling_backend/appinfo/info.xml"
if [ "${STORE_INFO_LOCAL}" != "${ARCHIVE_INFO}" ]; then
	# The one substituted line has to reach the instance too, and it is written
	# over the staged copy so that everything else still comes out of the
	# archive.
	inst sh -c "sed -e 's|<image-tag>[^<]*</image-tag>|<image-tag>${TAG_SUBSTITUTE}</image-tag>|' ${INSTANCE_INFO_XML} > ${INSTANCE_INFO_XML}.store && mv ${INSTANCE_INFO_XML}.store ${INSTANCE_INFO_XML}"
fi
inst grep -E '<registry>|<image>|<image-tag>' "${INSTANCE_INFO_XML}" | tee -a "${LOG_FILE}"
routes=$(inst grep -c '<route>' "${INSTANCE_INFO_XML}" | tr -d '\r' || true)
log "the info.xml this registration uses carries ${routes} route elements out of the archive"
[ "${routes}" -gt 0 ] || die "the archive info.xml carries no routes block, so this would install an app with no search route and no error message"

occ app_api:app:register findling_backend "${DAEMON_NAME}" \
	--info-xml "${INSTANCE_INFO_XML}" --wait-finish >> "${LOG_FILE}" 2>&1 \
	|| die "occ app_api:app:register findling_backend failed against the daemon ${DAEMON_NAME}"

STORE_CONTAINER=$(docker ps --filter 'name=findling_backend' --format '{{.Names}}')
[ -n "${STORE_CONTAINER}" ] || die "no running container matches findling_backend, so the deploy daemon created nothing out of the archive"
STORE_VOLUME=$(docker volume ls --filter 'name=findling_backend' --format '{{.Name}}')
[ -n "${STORE_VOLUME}" ] || die "no volume matches findling_backend, so the archive installation has no data volume"
running_image=$(docker inspect --format '{{.Config.Image}}' "${STORE_CONTAINER}")
log "container ${STORE_CONTAINER}, volume ${STORE_VOLUME}, image ${running_image}"
case "${running_image}" in
	*"${IMAGE_PATH}"*) ;;
	*) die "the container runs '${running_image}' while the archive named '${IMAGE_PATH}'" ;;
esac
case "${running_image}" in
	*localhost:*|*127.0.0.1:*)
		die "the container runs an image of a local registry, so this run measured a developer path and not a store installation"
		;;
esac
occ app_api:app:list 2>&1 | tee -a "${LOG_FILE}" | grep -q 'findling_backend' \
	|| die "app_api:app:list does not know findling_backend, so the registration out of the archive did not survive"
step_end "ok"

# ---------------------------------------------------------------------------
# Step 4, the zero config proof.
#
# Nothing is configured after the installation. The file arrives over WebDAV as
# an ordinary user, which is what a user does and what puts it into the file
# cache without occ files:scan. The engine is driven by the system cron, or by
# the identical command a system cron runs when nothing else drives it, and the
# budget is counted in cron rounds. What is NOT here, and must never be, is occ
# findling:index, occ background-job:worker or any occ config:app:set: those are
# development shortcuts and a zero config proof that uses one of them proves the
# opposite of its name.
#
# The coverage of the admin page is read once per round and written into the
# protocol with its timestamp, so that the proof is a series of numbers and not
# an impression.
# ---------------------------------------------------------------------------
step_begin "4 the zero config proof"
OCC_MARKER=$(wc -l < "${OCC_LOG}" | tr -d ' ')
log "every occ call of this run up to here:"
cat -n "${OCC_LOG}" >> "${LOG_FILE}"
log "the installation is complete after ${OCC_MARKER} occ calls, and nothing below may add one"

user_name=${USER_UID}
printf 'The findling zero config proof word is %s.\n' "${ZERO_CONFIG_WORD}" > "${WORK_DIR}/zero-config.txt"
code=$(curl -s -o /dev/null -w '%{http_code}' -T "${WORK_DIR}/zero-config.txt" \
	-K "${USER_CONF}" \
	"${INSTANCE_URL}/remote.php/dav/files/${user_name}/${ZERO_CONFIG_FILE}")
case "${code}" in
	201|204) log "the file was uploaded over WebDAV as ${user_name}, HTTP ${code}" ;;
	*) die "the upload answered HTTP ${code}, so there is no document to find" ;;
esac

# The coverage of the admin page. Basic authentication first, because that is
# one request; a session login only if the instance refuses it, because the
# route is a frontpage route and demands the request token of a session.
#
# The session is built lazily and not in advance, and that is not a detail of
# style: an attempt that runs before anybody needs it reports a failure into the
# protocol on every instance that answers basic authentication perfectly well,
# and a finding that means nothing is worse than no finding at all.
COVERAGE_TOKEN=""
COVERAGE_SESSION_TRIED=0
COVERAGE_COOKIES="${WORK_DIR}/cookies.txt"
admin_session() {
	rm -f "${COVERAGE_COOKIES}"
	token=$(curl -s -c "${COVERAGE_COOKIES}" "${INSTANCE_URL}/login" \
		| sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' | head -1)
	[ -n "${token}" ] || return 1
	# --data-urlencode and not -d, and that is the whole difference between a
	# session and a redirect back to the login page: a request token carries +
	# and / and =, and a plain -d sends the + as a space, which the CSRF check
	# refuses. Measured on 06.09.2026.
	curl -s -o /dev/null -L -b "${COVERAGE_COOKIES}" -c "${COVERAGE_COOKIES}" \
		--data-urlencode "user=${ADMIN_UID}" \
		--data-urlencode "password@${ADMIN_PASSWORD_FILE}" \
		--data-urlencode "requesttoken=${token}" "${INSTANCE_URL}/login" || return 1
	COVERAGE_TOKEN=$(curl -s -b "${COVERAGE_COOKIES}" -c "${COVERAGE_COOKIES}" \
		"${INSTANCE_URL}/settings/admin" \
		| sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' | head -1)
	[ -n "${COVERAGE_TOKEN}" ]
}
coverage_line() {
	out="${WORK_DIR}/overview.json"
	code=$(curl -s -o "${out}" -w '%{http_code}' -K "${ADMIN_CONF}" \
		-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		"${INSTANCE_URL}/apps/findling/admin/overview" || true)
	if [ "${code}" != "200" ] && [ "${COVERAGE_SESSION_TRIED}" -eq 0 ]; then
		COVERAGE_SESSION_TRIED=1
		if admin_session; then
			log "basic authentication was refused for the admin page, an administrator session was established instead"
		else
			finding "the admin page answered HTTP ${code} to basic authentication and no administrator session could be established either, so the coverage stays unread"
		fi
	fi
	if [ "${code}" != "200" ] && [ -n "${COVERAGE_TOKEN}" ]; then
		code=$(curl -s -o "${out}" -w '%{http_code}' -b "${COVERAGE_COOKIES}" \
			-H "requesttoken: ${COVERAGE_TOKEN}" -H 'Accept: application/json' \
			"${INSTANCE_URL}/apps/findling/admin/overview" || true)
	fi
	if [ "${code}" != "200" ]; then
		echo "coverage unreadable, HTTP ${code}"
		return 0
	fi
	# The coverage object and not the whole answer: the answer carries indexed
	# twice, and the one that belongs to this figure is the one inside coverage.
	cov=$(json_object coverage "${out}")
	if [ -z "${cov}" ]; then
		echo "the answer carries no coverage object"
		return 0
	fi
	# An absent number is printed as unknown rather than as an empty gap: the
	# share is null while nothing is indexable yet, and a protocol that shows a
	# blank there reads like a defect of the reader.
	percent=$(json_number percent "${cov}")
	[ -n "${percent}" ] || percent="unknown"
	printf 'coverage %s per cent, indexed %s of %s indexable, %s embedded\n' \
		"${percent}" \
		"$(json_number indexed "${cov}")" \
		"$(json_number indexable "${cov}")" \
		"$(json_number embedded "${cov}")"
}
# The first point of the series, before a single background job has run. Without
# it the protocol shows a figure and not a movement, and the promise of this
# step is that the figure rises without anybody doing anything.
log "round 0, before the first cron round: $(coverage_line)"

FOUND=""
ROUNDS=0
FIRST_HIT_SECONDS=0
zero_start=$(date +%s)
while [ "${ROUNDS}" -lt "${ZERO_CONFIG_CRON_ROUNDS}" ]; do
	ROUNDS=$(( ROUNDS + 1 ))
	if [ "${CRON_DRIVER}" = "system" ]; then
		# The instance drives its own background jobs, so one round is one
		# interval of that cron and this script only waits.
		sleep "${CRON_INTERVAL_SECONDS}"
	else
		# Nothing drives them, so this script runs the identical command a
		# system cron runs. That is the mechanism and not a shortcut, at a
		# cadence this run controls; the protocol converts the rounds back into
		# system cron time so that nobody reads the wall clock of this run as
		# the time a real instance would need.
		inst php -f cron.php >> "${LOG_FILE}" 2>&1 || true
		sleep "${SETTLE_SECONDS}"
	fi
	log "round ${ROUNDS}: $(coverage_line)"
	code=$(curl -s -o "${WORK_DIR}/search.json" -w '%{http_code}' \
		-K "${USER_CONF}" -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		"${INSTANCE_URL}/ocs/v2.php/search/providers/findling/search?term=${ZERO_CONFIG_WORD}" || true)
	# An entries list that begins with an object is a hit, an empty list is not.
	# The pattern is narrow on purpose and the assertion on the file name below
	# is what makes it an assertion about this document.
	if [ "${code}" = "200" ] && tr -d ' \n\r' < "${WORK_DIR}/search.json" | grep -q '"entries":\[{'; then
		FOUND="yes"
		FIRST_HIT_SECONDS=$(( $(date +%s) - zero_start ))
		break
	fi
	log "round ${ROUNDS}: HTTP ${code}, no hit yet, $(( ZERO_CONFIG_CRON_ROUNDS - ROUNDS )) rounds of the budget left"
done

if [ -z "${FOUND}" ]; then
	docker logs "${STORE_CONTAINER}" 2>&1 | tail -n 60 >> "${LOG_FILE}" || true
	die "no content hit within ${ZERO_CONFIG_CRON_ROUNDS} cron rounds, which is $(( ZERO_CONFIG_CRON_ROUNDS * CRON_INTERVAL_SECONDS ))s of system cron time; this is a finding and not a reason to raise the budget"
fi
cat "${WORK_DIR}/search.json" >> "${LOG_FILE}"
grep -q "${ZERO_CONFIG_FILE}" "${WORK_DIR}/search.json" \
	|| die "the search answered with a hit that does not name ${ZERO_CONFIG_FILE}, so it found something else"
log "content hit after ${ROUNDS} cron rounds, ${FIRST_HIT_SECONDS}s of wall clock, which is $(( ROUNDS * CRON_INTERVAL_SECONDS ))s of system cron time"
log "at the hit: $(coverage_line)"

tail -n +$(( OCC_MARKER + 1 )) "${OCC_LOG}" > "${WORK_DIR}/occ-since-install.txt"
log "occ calls between the installation and the hit:"
cat "${WORK_DIR}/occ-since-install.txt" >> "${LOG_FILE}"
if [ -s "${WORK_DIR}/occ-since-install.txt" ]; then
	die "an occ call ran between the installation and the hit, so this was not a zero config proof"
fi
log "none, which is what zero config means"
step_end "ok"

# ---------------------------------------------------------------------------
# Step 5, the six uninstall promises.
#
# Word for word the six assertions of deploy-harp.yml, against the installation
# the archive produced on this instance. Two yardsticks for one promise would be
# worse than none, so the sentences are the ones the workflow prints and the
# order is the order it uses. The order matters twice: promise 1 cannot be made
# after promise 3, and promise 4 cannot be made after promise 5, because the
# intent mark is a one shot flag.
# ---------------------------------------------------------------------------
tables_of_instance() {
	if [ -z "${DB_TABLES_CMD}" ]; then
		echo "__not_performed__"
		return 0
	fi
	sh -c "${DB_TABLES_CMD}" | tr -d '\r' | sort | tr '\n' ' ' | sed -e 's/ *$//'
}
settings_of_instance() {
	# config:list reads oc_appconfig and answers for an app that is no longer
	# installed as well, which is the case this has to survive: after the remove
	# the app is gone and the question is whether its settings are.
	#
	# Only lines that carry a value are counted, and that is not pedantry: the
	# answer wraps every value in two lines of structure, "apps": { and
	# "findling": [, and a count that takes them along reports two settings for
	# an app whose settings are all gone. Measured on 06.09.2026, where exactly
	# that turned a clean uninstall into a false finding.
	occ config:list findling 2>/dev/null | grep -cE '^[[:space:]]+"[^"]+": ("|[0-9-])' || true
}

step_begin "5 uninstall promise 1, an unregister without the flag keeps the volume"
occ app_api:app:unregister findling_backend >> "${LOG_FILE}" 2>&1 || die "the unregister without the flag failed"
still_there=$(docker ps -a --filter "name=${STORE_CONTAINER}" --format '{{.Names}}')
[ -z "${still_there}" ] || die "the container ${STORE_CONTAINER} survived the unregister, so the deregistration removed nothing"
kept=$(docker volume ls --filter "name=${STORE_VOLUME}" --format '{{.Name}}')
[ "${kept}" = "${STORE_VOLUME}" ] || die "the volume ${STORE_VOLUME} is gone after an unregister without --rm-data, and the documented default is that it stays; found '${kept}'"
log "container gone, volume ${kept} kept"
step_end "ok"

step_begin "5 uninstall promise 2, a second registration picks up the volume it left"
occ app_api:app:register findling_backend "${DAEMON_NAME}" \
	--info-xml "${INSTANCE_INFO_XML}" --wait-finish >> "${LOG_FILE}" 2>&1 \
	|| die "the second registration out of the archive failed"
container=$(docker ps --filter 'name=findling_backend' --format '{{.Names}}')
[ -n "${container}" ] || die "the second registration out of the archive created no running container"
volume=$(docker volume ls --filter 'name=findling_backend' --format '{{.Name}}')
[ "${volume}" = "${STORE_VOLUME}" ] || die "the second registration did not take the volume of the first one, expected ${STORE_VOLUME} and found '${volume}'"
log "registered again as ${container} on the kept volume ${volume}"
step_end "ok"

step_begin "5 uninstall promise 3, an unregister with --rm-data removes the volume"
[ -n "${STORE_VOLUME}" ] || die "no volume name from the install step, so an empty filter result would be a false green"
occ app_api:app:unregister findling_backend --rm-data >> "${LOG_FILE}" 2>&1 || die "the unregister with --rm-data failed"
left=$(docker volume ls --filter "name=${STORE_VOLUME}" --format '{{.Name}}')
[ -z "${left}" ] || die "the volume ${STORE_VOLUME} survived an unregister with --rm-data, found '${left}'"
container=$(docker ps -a --filter "name=${STORE_CONTAINER}" --format '{{.Names}}')
[ -z "${container}" ] || die "the container ${STORE_CONTAINER} survived the unregister with --rm-data"
log "container and volume ${STORE_VOLUME} both gone"
step_end "ok"

step_begin "5 uninstall promise 4, a disable without intent keeps tables and settings"
expected='oc_findling_file_state oc_findling_queue oc_findling_scan_stats'
tables=$(tables_of_instance)
settings=$(settings_of_instance)
log "before the disable: tables [${tables}], settings ${settings}"
if [ "${tables}" = "__not_performed__" ]; then
	finding "no --db-tables-cmd was given, so the table half of promises 4 and 5 is not performed on this instance; the settings half below is"
elif [ "${tables}" != "${expected}" ]; then
	die "the three tables of the app are not all there before the disable, expected [${expected}] and found [${tables}]"
fi
occ app:disable findling >> "${LOG_FILE}" 2>&1 || die "occ app:disable findling failed"
tables=$(tables_of_instance)
settings=$(settings_of_instance)
log "after the disable: tables [${tables}], settings ${settings}"
if [ "${tables}" != "__not_performed__" ] && [ "${tables}" != "${expected}" ]; then
	die "the disable removed tables although no intent was armed, expected [${expected}] and found [${tables}]"
fi
[ "${settings}" -ge 1 ] || die "the disable emptied the settings of the app although no intent was armed, ${settings} values left"
step_end "ok"

step_begin "5 uninstall promise 5, a remove with intent clears tables and settings"
occ app:enable findling >> "${LOG_FILE}" 2>&1 || die "occ app:enable findling failed"
occ app_api:app:register findling_backend "${DAEMON_NAME}" \
	--info-xml "${INSTANCE_INFO_XML}" --wait-finish >> "${LOG_FILE}" 2>&1 \
	|| die "the registration before promise 6 failed"
occ findling:purge --arm --no-interaction >> "${LOG_FILE}" 2>&1 || die "occ findling:purge --arm failed"
occ app:remove findling >> "${LOG_FILE}" 2>&1 || die "occ app:remove findling failed"
tables=$(tables_of_instance)
settings=$(settings_of_instance)
log "after the remove with intent: tables [${tables}], settings ${settings}"
if [ "${tables}" != "__not_performed__" ] && [ -n "${tables}" ]; then
	die "the remove with intent left tables behind: [${tables}]"
fi
[ "${settings}" -eq 0 ] || die "the remove with intent left ${settings} settings behind"
if inst test -e "${APPS_DIR}/findling"; then
	die "the remove left the extracted archive behind in ${APPS_DIR}/findling, which a developer installation would not have shown"
fi
log "no tables, no settings, no directory"
step_end "ok"

step_begin "5 uninstall promise 6, the container without a companion retreats"
container=$(docker ps --filter 'name=findling_backend' --format '{{.Names}}')
[ -n "${container}" ] || die "no running container after the companion was removed, so the container did not survive the half removal"
noisy_lines() { docker logs "${container}" 2>&1 | grep -cE '^(WARNING|ERROR|CRITICAL):' || true; }
before=$(noisy_lines)
entered=""
# 24 waits of ten seconds, the same budget deploy-harp.yml gives this promise.
# The retreat is announced after three unanswered passes at 15 and 30 seconds,
# so the budget is roughly four times the announcement and is derived from the
# poller clock and not guessed.
attempt=0
while [ "${attempt}" -lt 24 ]; do
	attempt=$(( attempt + 1 ))
	if docker logs "${container}" 2>&1 | grep -q 'the queue has not answered for'; then
		entered="yes"
		break
	fi
	sleep 10
done
if [ -z "${entered}" ]; then
	docker logs "${container}" 2>&1 | tail -n 40 >> "${LOG_FILE}"
	die "the container never announced the retreat, so it is either still polling pass by pass or it is not polling at all"
fi
alive=$(docker ps --filter "name=${container}" --format '{{.Status}}')
[ -n "${alive}" ] || die "the container stopped during the retreat instead of waiting it out"
after=$(noisy_lines)
grew=$(( after - before ))
if [ "${grew}" -gt 5 ]; then
	docker logs "${container}" 2>&1 | grep -E '^(WARNING|ERROR|CRITICAL):' | tail -n 20 >> "${LOG_FILE}"
	die "the container wrote ${grew} new warning or error lines while its caller was gone, which is an error loop and not a retreat"
fi
log "container ${container} is ${alive}, retreat announced, ${grew} new warning or error lines"
step_end "ok"

RUN_COMPLETE=1
log "SUMMARY: image ${REFERENCE} at ${DIGEST}"
log "SUMMARY: version ${ARCHIVE_VERSION}, content hit after ${ROUNDS} cron rounds of ${CRON_INTERVAL_SECONDS}s, no occ call in between"
log "SUMMARY: all six uninstall promises hold on this instance"
