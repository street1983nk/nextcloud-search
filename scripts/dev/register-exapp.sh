#!/bin/sh
# Start the ExApp on the host and register it with the local test Nextcloud.
#
# One command from a running compose stack to a search that answers. The script
# is idempotent: an existing registration is removed first, and a backend that
# already answers its heartbeat is left running.
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
BACKEND_SECRET=12345
BACKEND_PORT=10035
BACKEND_VERSION=0.1.0
NEXTCLOUD_URL=http://localhost:${FINDLING_PORT:-8080}
# The container reaches the host process under this name, never under localhost:
# localhost inside the container is the container itself.
HOST_FROM_CONTAINER=host.docker.internal
RUN_DIR="${REPO_ROOT}/.dev"
LOG_FILE="${RUN_DIR}/exapp.log"
PID_FILE="${RUN_DIR}/exapp.pid"

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
	printf 'backend already answers on port %s, leaving it alone\n' "${BACKEND_PORT}"
else
	printf 'starting the backend, log goes to %s\n' "${LOG_FILE}"
	# APP_HOST is 0.0.0.0 here and 127.0.0.1 in the integration workflow. In CI
	# both sides live on the same host, here Nextcloud sits in a container and
	# has to reach a process outside of it. A loopback bind would be invisible
	# from there, and the registration would time out with a healthy looking log.
	# The HaRP shared key stays unset on purpose: setting it makes the server
	# bind a unix socket instead of the port, and nothing here talks to a socket.
	(
		cd "${REPO_ROOT}/backend" || exit 1
		APP_ID="${BACKEND_ID}"
		APP_SECRET="${BACKEND_SECRET}"
		APP_PORT="${BACKEND_PORT}"
		APP_VERSION="${BACKEND_VERSION}"
		APP_HOST=0.0.0.0
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
nextcloud_occ app_api:app:register "${BACKEND_ID}" "${DAEMON_NAME}" --json-info \
	"{\"id\":\"${BACKEND_ID}\",\"name\":\"Findling Backend\",\"daemon_config_name\":\"${DAEMON_NAME}\",\"version\":\"${BACKEND_VERSION}\",\"secret\":\"${BACKEND_SECRET}\",\"port\":${BACKEND_PORT},\"scopes\":[],\"system\":0,\"routes\":[{\"url\":\".*\",\"verb\":\"GET,POST,PUT,DELETE\",\"access_level\":1,\"headers_to_exclude\":[]}]}" \
	--force-scopes --wait-finish

printf 'registered\n'
