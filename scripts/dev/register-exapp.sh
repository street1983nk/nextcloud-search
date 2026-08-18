#!/bin/sh
# Start the ExApp on the host and register it with the local test Nextcloud.
#
# One command from a running compose stack to a search that answers. The script
# is idempotent: an existing registration is removed first, and a backend that
# already answers its heartbeat is left running with the secret it was started
# with, which is kept in .dev/exapp.secret. That directory is gitignored, so no
# credential of a local run can reach the repository.
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
BACKEND_VERSION=0.1.0
NEXTCLOUD_URL=http://localhost:${FINDLING_PORT:-8080}
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

if curl -sf "http://127.0.0.1:${BACKEND_PORT}/heartbeat" >/dev/null 2>&1; then
	# A backend that answers is left running, but only if this script knows its
	# secret. Registering a fresh secret against a process that still uses the old
	# one fails the handshake with a signature error that reads like a code defect.
	if [ -r "${SECRET_FILE}" ]; then
		BACKEND_SECRET=$(cat "${SECRET_FILE}")
		printf 'backend already answers on port %s, reusing the secret from %s\n' \
			"${BACKEND_PORT}" "${SECRET_FILE}"
	else
		printf 'something answers the heartbeat on port %s, but %s does not exist,\n' \
			"${BACKEND_PORT}" "${SECRET_FILE}" >&2
		printf 'so its secret is unknown and the handshake could only fail. Stop that\n' >&2
		printf 'process and run this script again.\n' >&2
		exit 1
	fi
else
	# A pid file without a live process behind it is stale and gets removed. A pid
	# file with a live process behind it belongs to a backend that no longer answers
	# its heartbeat: it holds the port, so it is stopped rather than left to make
	# the next start fail with "address already in use".
	if [ -f "${PID_FILE}" ]; then
		OLD_PID=$(cat "${PID_FILE}")
		if [ -n "${OLD_PID}" ] && kill -0 "${OLD_PID}" 2>/dev/null; then
			printf 'a backend with pid %s is running but does not answer, stopping it\n' "${OLD_PID}"
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
	fi

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
# The route list mirrors backend/appinfo/info.xml exactly: one route, POST on
# search, USER level. A catch all ".*" with the writing verbs would give the local
# instance a surface no released installation has, and the first thing that breaks
# in CI but works here would be exactly that difference.
nextcloud_occ app_api:app:register "${BACKEND_ID}" "${DAEMON_NAME}" --json-info \
	"{\"id\":\"${BACKEND_ID}\",\"name\":\"Findling Backend\",\"daemon_config_name\":\"${DAEMON_NAME}\",\"version\":\"${BACKEND_VERSION}\",\"secret\":\"${BACKEND_SECRET}\",\"port\":${BACKEND_PORT},\"scopes\":[],\"system\":0,\"routes\":[{\"url\":\"search\",\"verb\":\"POST\",\"access_level\":1,\"headers_to_exclude\":[]}]}" \
	--force-scopes --wait-finish

printf 'registered\n'
