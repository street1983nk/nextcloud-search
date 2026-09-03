#!/bin/sh
# Start the ExApp on the host and register it with the local test Nextcloud.
#
# One command from a running compose stack to a search that answers. The script
# is idempotent with one deliberate exception: an existing registration is
# removed first, and a backend that already answers its heartbeat is left running
# with the secret it was started with, which is kept in .dev/exapp.secret, unless
# that backend no longer matches the sources. A process whose version or whose
# route list disagrees with backend/appinfo/info.xml is stopped and started
# again, with a line naming the reason. That directory is gitignored, so no
# credential of a local run can reach the repository.
#
# Why the exception exists (DI-04-02 of phase 4): the host process is started
# once and lives on across checkouts. After a plan that adds a route it answers
# 404 for it, which looks exactly like a defect of the PHP half, and after a
# version bump it reports the old version, which is what the lockstep check of
# the other half compares against. Both are minutes of searching for a fault
# that is nothing but a stale process.
#
# Everything that touches Nextcloud goes through the container. There is no PHP
# and no composer on this development machine, so a bare php or occ call would
# fail with a confusing "command not found" instead of a useful message.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "${SCRIPT_DIR}/../.." && pwd)
COMPOSE_FILE="${SCRIPT_DIR}/compose.yaml"

BACKEND_ID=findling_backend
DAEMON_NAME=manual_install
BACKEND_PORT=10035
NEXTCLOUD_URL=http://localhost:${FINDLING_PORT:-8080}
# The one file that says what this container is and what it exposes. Version and
# route list are both read out of it below, so neither can drift away from the
# declaration the released app carries.
INFO_XML="${REPO_ROOT}/backend/appinfo/info.xml"
# The container reaches the host process under this name, never under localhost:
# localhost inside the container is the container itself.
HOST_FROM_CONTAINER=host.docker.internal
RUN_DIR="${REPO_ROOT}/.dev"
LOG_FILE="${RUN_DIR}/exapp.log"
PID_FILE="${RUN_DIR}/exapp.pid"
SECRET_FILE="${RUN_DIR}/exapp.secret"

# The bind address of the development backend.
#
# 0.0.0.0 and not 127.0.0.1, and that is not laziness: Nextcloud runs in a
# container here and reaches this process from the outside, so a loopback bind is
# invisible from there and the registration times out with a healthy looking log.
#
# The narrow version of this is the address of the docker bridge, but which
# address that is differs between a plain Linux daemon (typically 172.17.0.1),
# Docker Desktop and WSL2, where host.docker.internal is not the bridge gateway at
# all. So the default stays reachable and the variable is the way to narrow it:
#
#     FINDLING_APP_HOST=172.17.0.1 scripts/dev/register-exapp.sh
#
# What made the old default actually dangerous was the second half, a secret that
# was the string 12345 in a public repository. That part is fixed below: the
# secret is random per run.
BACKEND_HOST="${FINDLING_APP_HOST:-0.0.0.0}"

# One secret per run, stored next to the log so a second run can find the backend
# it started. A fixed secret in a public repository is a credential everybody has,
# and it authenticates the one route that reads file content.
new_secret() {
	if command -v openssl >/dev/null 2>&1; then
		openssl rand -hex 16
		return
	fi
	# No openssl on this machine: sixteen bytes out of the kernel, hex encoded.
	od -vAn -N16 -tx1 /dev/urandom | tr -d ' \n'
}

nextcloud_occ() {
	docker compose -f "${COMPOSE_FILE}" exec -T -u www-data app php occ "$@"
}

# Stop the backend this script started, and take its pid file with it.
#
# A pid file without a live process behind it is stale and gets removed. A pid
# file with a live process behind it belongs to a backend that either no longer
# answers its heartbeat or no longer matches the sources: it holds the port, so
# it is stopped rather than left to make the next start fail with "address
# already in use".
#
# Without a pid file there is nothing this function can do, and it says so: the
# process was started by hand or the file was deleted, and only the person at
# the keyboard can decide what to do with it.
stop_backend() {
	if [ ! -f "${PID_FILE}" ]; then
		printf 'no pid file at %s, so nothing here can stop that process\n' "${PID_FILE}"
		return 0
	fi

	OLD_PID=$(cat "${PID_FILE}")
	if [ -n "${OLD_PID}" ] && kill -0 "${OLD_PID}" 2>/dev/null; then
		printf 'stopping the backend with pid %s\n' "${OLD_PID}"
		kill -TERM "${OLD_PID}" 2>/dev/null || true
		i=0
		while [ "${i}" -lt 10 ]; do
			if ! kill -0 "${OLD_PID}" 2>/dev/null; then
				break
			fi
			i=$((i + 1))
			sleep 1
		done
		kill -KILL "${OLD_PID}" 2>/dev/null || true
	else
		printf 'removing the stale pid file %s\n' "${PID_FILE}"
	fi
	rm -f "${PID_FILE}"
}

# One line per declared route: url, verb, numeric access level.
#
# Parsed out of the file instead of written here, and that is the whole point.
# The list used to be a literal with a single entry claiming parity with a file
# that had declared five routes since phase 2, so the local instance had a
# surface no released installation has and the difference showed up as a defect
# somewhere else (DI-04-01). A list that is read cannot drift.
#
# The three level names are the constants of OCA\AppAPI\Db\ExAppRouteAccessLevel:
# PUBLIC 0, USER 1, ADMIN 2. An unknown one stops the script rather than being
# guessed at, because guessing here either locks the route or opens it.
declared_routes() {
	awk '
		BEGIN { FS = "[<>]" }
		/<routes>/ { inside = 1; next }
		/<\/routes>/ { inside = 0; next }
		inside != 1 { next }
		/<url>/ { url = $3; next }
		/<verb>/ { verb = $3; next }
		/<access_level>/ { level = $3; next }
		/<\/route>/ {
			if (url == "" || verb == "" || level == "") next
			number = -1
			if (level == "PUBLIC") number = 0
			if (level == "USER") number = 1
			if (level == "ADMIN") number = 2
			if (number < 0) {
				printf "unknown access level %s in the routes of info.xml\n", level > "/dev/stderr"
				exit 1
			}
			printf "%s %s %d\n", url, verb, number
			url = ""
			verb = ""
			level = ""
		}
	' "${INFO_XML}"
}

# The header AppAPI signs a request with, for a probe out of this script.
#
# The middleware compares the app id and the secret and nothing else; the version
# header only has to be there. The user name in it is any name, because the
# reading routes of this container read no identity at all.
app_api_authorization() {
	printf 'admin:%s' "$1" | base64 | tr -d '\r\n'
}

# The HTTP status code of one path of the running backend, "000" when nothing
# answered. Used to ask whether a path is mounted at all: a GET on a route that
# only takes POST answers 405, which is a mounted path, and a path that does not
# exist answers 404.
probe_code() {
	curl -s -o /dev/null -w '%{http_code}' \
		-H "EX-APP-ID: ${BACKEND_ID}" \
		-H "EX-APP-VERSION: ${BACKEND_VERSION}" \
		-H "AUTHORIZATION-APP-API: $1" \
		"http://127.0.0.1:${BACKEND_PORT}/$2" 2>/dev/null || printf '000'
}

# Why a backend that answers its heartbeat still cannot be reused, and an empty
# line when it can. One reason is printed, the first one found, because the
# answer to all of them is the same restart.
stale_reason() {
	stale_auth=$(app_api_authorization "$1")
	# -sf, so that an answer with a status code of 400 and above arrives here as
	# nothing at all. A 401 carries the word "Unauthorized" in its body, and
	# without -f that text would be searched for a version and reported as a
	# version mismatch, which names the wrong cause for the right restart.
	stale_status=$(curl -sf \
		-H "EX-APP-ID: ${BACKEND_ID}" \
		-H "EX-APP-VERSION: ${BACKEND_VERSION}" \
		-H "AUTHORIZATION-APP-API: ${stale_auth}" \
		"http://127.0.0.1:${BACKEND_PORT}/status" 2>/dev/null || true)
	if [ -z "${stale_status}" ]; then
		printf 'it does not answer its status route, so neither its version nor its routes can be read'
		return 0
	fi

	stale_version=$(printf '%s' "${stale_status}" | sed -n 's/.*"appVersion":"\([^"]*\)".*/\1/p')
	if [ "${stale_version}" != "${BACKEND_VERSION}" ]; then
		printf 'it reports the version %s and the sources say %s' \
			"${stale_version:-none}" "${BACKEND_VERSION}"
		return 0
	fi

	for stale_route in ${ROUTE_URLS}; do
		if [ "$(probe_code "${stale_auth}" "${stale_route}")" = "404" ]; then
			printf 'the declared route %s is not mounted in it' "${stale_route}"
			return 0
		fi
	done
}

BACKEND_VERSION=$(sed -n 's:.*<version>\(.*\)</version>.*:\1:p' "${INFO_XML}" | head -n 1)
if [ -z "${BACKEND_VERSION}" ]; then
	printf 'no version could be read from %s\n' "${INFO_XML}" >&2
	exit 1
fi

ROUTE_LINES=$(declared_routes)
if [ -z "${ROUTE_LINES}" ]; then
	printf 'no route could be read from %s\n' "${INFO_XML}" >&2
	exit 1
fi

# The parse is compared against the file it parsed. A regular expression that
# stopped matching would produce a shorter list and a registration that quietly
# exposes less than the release does, which is the failure this whole change is
# about.
ROUTES_DECLARED=$(grep -c '<route>' "${INFO_XML}")
ROUTES_PARSED=$(printf '%s\n' "${ROUTE_LINES}" | wc -l | tr -d ' ')
if [ "${ROUTES_DECLARED}" != "${ROUTES_PARSED}" ]; then
	printf '%s declares %s routes and %s could be read\n' \
		"${INFO_XML}" "${ROUTES_DECLARED}" "${ROUTES_PARSED}" >&2
	exit 1
fi

ROUTES_JSON=""
ROUTE_URLS=""
while read -r route_url route_verb route_level; do
	[ -n "${route_url}" ] || continue
	ROUTE_URLS="${ROUTE_URLS} ${route_url}"
	if [ -n "${ROUTES_JSON}" ]; then
		ROUTES_JSON="${ROUTES_JSON},"
	fi
	ROUTES_JSON="${ROUTES_JSON}{\"url\":\"${route_url}\",\"verb\":\"${route_verb}\",\"access_level\":${route_level},\"headers_to_exclude\":[]}"
done <<EOF
${ROUTE_LINES}
EOF

printf 'registering version %s with %s routes from %s\n' \
	"${BACKEND_VERSION}" "${ROUTES_PARSED}" "backend/appinfo/info.xml"

mkdir -p "${RUN_DIR}"

printf 'waiting for %s\n' "${NEXTCLOUD_URL}"
i=0
while [ "${i}" -lt 60 ]; do
	if curl -sf "${NEXTCLOUD_URL}/status.php" >/dev/null 2>&1; then
		break
	fi
	i=$((i + 1))
	sleep 2
done
if [ "${i}" -ge 60 ]; then
	printf 'nextcloud did not answer on %s/status.php\n' "${NEXTCLOUD_URL}" >&2
	printf 'start it first: docker compose -f %s up -d\n' "${COMPOSE_FILE}" >&2
	exit 1
fi

printf 'enabling app_api and findling\n'
nextcloud_occ app:install app_api >/dev/null 2>&1 || true
nextcloud_occ app:enable app_api
nextcloud_occ app:enable findling

# Whether the process that is already listening can be kept, decided below.
REUSE_BACKEND=0
BACKEND_SECRET=""

if curl -sf "http://127.0.0.1:${BACKEND_PORT}/heartbeat" >/dev/null 2>&1; then
	# A backend that answers is left running, but only if this script knows its
	# secret. Registering a fresh secret against a process that still uses the old
	# one fails the handshake with a signature error that reads like a code defect.
	if [ -r "${SECRET_FILE}" ]; then
		BACKEND_SECRET=$(cat "${SECRET_FILE}")
		# The one question that decides between idempotent and restart. A process
		# that answers is not automatically the process these sources describe.
		STALE=$(stale_reason "${BACKEND_SECRET}")
		if [ -z "${STALE}" ]; then
			printf 'backend already answers on port %s and matches the sources, reusing the secret from %s\n' \
				"${BACKEND_PORT}" "${SECRET_FILE}"
			REUSE_BACKEND=1
		else
			printf 'restarting the backend on port %s, because %s\n' "${BACKEND_PORT}" "${STALE}"
			stop_backend
		fi
	else
		printf 'something answers the heartbeat on port %s, but %s does not exist,\n' \
			"${BACKEND_PORT}" "${SECRET_FILE}" >&2
		printf 'so its secret is unknown and the handshake could only fail. Stop that\n' >&2
		printf 'process and run this script again.\n' >&2
		exit 1
	fi
else
	stop_backend
fi

if [ "${REUSE_BACKEND}" -eq 0 ]; then
	# One fresh secret per start, written with owner only permissions before the
	# process that uses it exists.
	if [ -n "${FINDLING_APP_SECRET:-}" ]; then
		BACKEND_SECRET="${FINDLING_APP_SECRET}"
	else
		BACKEND_SECRET=$(new_secret)
	fi
	(
		umask 077
		printf '%s\n' "${BACKEND_SECRET}" >"${SECRET_FILE}"
	)

	printf 'starting the backend on %s:%s, log goes to %s\n' \
		"${BACKEND_HOST}" "${BACKEND_PORT}" "${LOG_FILE}"
	# The HaRP shared key stays unset on purpose: setting it makes the server bind
	# a unix socket instead of the port, and nothing here talks to a socket.
	(
		cd "${REPO_ROOT}/backend" || exit 1
		APP_ID="${BACKEND_ID}"
		APP_SECRET="${BACKEND_SECRET}"
		APP_PORT="${BACKEND_PORT}"
		APP_VERSION="${BACKEND_VERSION}"
		APP_HOST="${BACKEND_HOST}"
		APP_PERSISTENT_STORAGE="${RUN_DIR}/storage"
		export APP_ID APP_SECRET APP_PORT APP_VERSION APP_HOST APP_PERSISTENT_STORAGE
		export NEXTCLOUD_URL
		exec uv run python -m findling.main
	) >"${LOG_FILE}" 2>&1 &
	printf '%s\n' "$!" >"${PID_FILE}"

	i=0
	while [ "${i}" -lt 30 ]; do
		if curl -sf "http://127.0.0.1:${BACKEND_PORT}/heartbeat" >/dev/null 2>&1; then
			break
		fi
		i=$((i + 1))
		sleep 1
	done
	if [ "${i}" -ge 30 ]; then
		printf 'backend did not answer its heartbeat, last log lines:\n' >&2
		tail -n 40 "${LOG_FILE}" >&2 || true
		exit 1
	fi
fi

# Idempotency. An old registration points at an old secret, and the handshake
# below would fail with a signature error that reads like a code problem.
nextcloud_occ app_api:app:unregister "${BACKEND_ID}" >/dev/null 2>&1 || true

printf 'registering the deploy daemon\n'
nextcloud_occ app_api:daemon:register --net host \
	"${DAEMON_NAME}" "Manual Install" manual-install http \
	"${HOST_FROM_CONTAINER}" "${NEXTCLOUD_URL}" >/dev/null 2>&1 \
	|| printf 'daemon %s exists already\n' "${DAEMON_NAME}"

printf 'registering the ExApp, this blocks until the handshake is done\n'
# The route list and the version come out of backend/appinfo/info.xml, so they
# cannot drift from the declaration a released installation carries. Neither is
# written here any more: the literal that used to stand in this line declared one
# route while the file declared five, and a catch all ".*" with the writing verbs
# would give the local instance a surface no release has, so that the first thing
# to break in CI while working here would be exactly that difference.
nextcloud_occ app_api:app:register "${BACKEND_ID}" "${DAEMON_NAME}" --json-info \
	"{\"id\":\"${BACKEND_ID}\",\"name\":\"Findling Backend\",\"daemon_config_name\":\"${DAEMON_NAME}\",\"version\":\"${BACKEND_VERSION}\",\"secret\":\"${BACKEND_SECRET}\",\"port\":${BACKEND_PORT},\"scopes\":[],\"system\":0,\"routes\":[${ROUTES_JSON}]}" \
	--force-scopes --wait-finish

printf 'registered\n'
