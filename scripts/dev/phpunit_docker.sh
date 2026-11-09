#!/usr/bin/env bash
# Run the PHPUnit suite of the companion app locally, inside Docker, the way
# the phpunit job of .github/workflows/php.yml runs it on a runner.
#
# There is no PHP and no composer on the development machine of this project,
# but there is Docker, and the suite needs nothing but mocks and the autoload
# space of nextcloud/server. So this script builds the same arrangement as the
# CI job, once, in a cache directory, and reruns the suite in it:
#
#   - a checkout of nextcloud/server on the branch SERVER_VERSION of php.yml,
#     with its submodules, installed as a throwaway SQLite instance so that the
#     server bootstrap has a config to read (no test touches it)
#   - php/ of this repository mirrored into apps/findling of that checkout,
#     afresh on every run
#   - the dev dependencies from the committed composer.lock, --no-scripts
#   - the suite in nextcloud:32.0.15-apache, which carries PHP 8.3; the image
#     is only the runtime, the server code comes from the mounted checkout
#
# SERVER_VERSION and MINIMUM_TESTS are read out of php.yml and never written
# down here, so the local recipe cannot drift from the CI job. Without
# arguments the executed test count is checked against MINIMUM_TESTS, exactly
# like the step "State how many tests actually ran". Arguments are handed to
# PHPUnit unchanged (for example --filter RouteSecurity); a filtered run skips
# the count check and says so, because a filter is meant to run fewer tests.
#
# Usage:
#
#     scripts/dev/phpunit_docker.sh
#     scripts/dev/phpunit_docker.sh --filter RouteSecurity
#
# FINDLING_PHPUNIT_SERVER overrides where the server checkout lives.
#
# The exit code is the one of PHPUnit, or 1 when PHPUnit passed but fewer tests
# ran than the floor. The last line names the JUnit file, so later gates can
# read it on the host.
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)
PHP_WORKFLOW="${REPO_ROOT}/.github/workflows/php.yml"

FINDLING_PHPUNIT_SERVER="${FINDLING_PHPUNIT_SERVER:-${HOME}/.cache/findling-phpunit/server}"
SERVER_DIR="${FINDLING_PHPUNIT_SERVER}"

RUNTIME_IMAGE="nextcloud:32.0.15-apache"
COMPOSER_IMAGE="composer:2"

# Docker Desktop on Windows wants C:/... in a mount, Git Bash hands out
# /c/...; cygpath -m converts, and on any other system the path stays as it is.
to_mount_path() {
	if command -v cygpath >/dev/null 2>&1; then
		cygpath -m "$1"
	else
		printf '%s\n' "$1"
	fi
}

# One sed call per key and no pipe: under pipefail a "| head -1" can end the
# run with SIGPIPE. The anchor needs leading whitespace, so a comment line,
# which starts with "#", never matches.
read_workflow_key() {
	sed -n -E "/^[[:space:]]+$1:/{s/^[[:space:]]+$1:[[:space:]]+([^[:space:]#]+).*/\\1/p;q}" "${PHP_WORKFLOW}"
}

SERVER_VERSION=$(read_workflow_key SERVER_VERSION)
MINIMUM_TESTS=$(read_workflow_key MINIMUM_TESTS)
if [ -z "${SERVER_VERSION}" ] || [ -z "${MINIMUM_TESTS}" ]; then
	echo "phpunit_docker: could not read SERVER_VERSION and MINIMUM_TESTS from ${PHP_WORKFLOW}" >&2
	exit 1
fi

if ! docker info >/dev/null 2>&1; then
	echo "phpunit_docker: docker is not reachable; start Docker Desktop first" >&2
	exit 1
fi

if [ ! -d "${SERVER_DIR}/.git" ]; then
	echo "phpunit_docker: cloning nextcloud/server ${SERVER_VERSION} into ${SERVER_DIR}"
	mkdir -p "$(dirname -- "${SERVER_DIR}")"
	# autocrlf off: the checkout is only ever read by Linux PHP in a container.
	git -c core.autocrlf=false clone --depth 1 --branch "${SERVER_VERSION}" \
		--recurse-submodules --shallow-submodules \
		https://github.com/nextcloud/server.git "${SERVER_DIR}"
fi

# A checkout on another branch is never reused and never removed by this
# script: the OCP the tests mock against would silently be the wrong one.
current_branch=$(git -C "${SERVER_DIR}" rev-parse --abbrev-ref HEAD)
if [ "${current_branch}" != "${SERVER_VERSION}" ]; then
	echo "phpunit_docker: ${SERVER_DIR} is on ${current_branch}, php.yml wants ${SERVER_VERSION}" >&2
	echo "phpunit_docker: delete that directory and run again to get a fresh checkout" >&2
	exit 1
fi

SERVER_MOUNT=$(to_mount_path "${SERVER_DIR}")
PHP_MOUNT=$(to_mount_path "${REPO_ROOT}/php")

# The same throwaway instance the CI job installs: SQLite, test-only admin,
# no port published, never reachable. The container runs as root, and occ only
# insists that its user owns config/, which on a bind mount is root as well.
if [ ! -f "${SERVER_DIR}/config/config.php" ]; then
	echo "phpunit_docker: installing a throwaway Nextcloud so the server bootstrap has a config"
	MSYS_NO_PATHCONV=1 docker run --rm \
		-v "${SERVER_MOUNT}:/srv/server" -w /srv/server \
		--entrypoint php "${RUNTIME_IMAGE}" \
		occ maintenance:install --database=sqlite \
		--admin-user admin --admin-pass password --data-dir /srv/server/data
fi

# Mirror php/ into apps/findling from scratch, vendor excepted. A file deleted
# in the repository must not live on in the mirror, or the run checks a tree
# that does not exist. php/ is mounted read-only.
MSYS_NO_PATHCONV=1 docker run --rm \
	-v "${SERVER_MOUNT}:/srv/server" -v "${PHP_MOUNT}:/src:ro" \
	--entrypoint sh "${RUNTIME_IMAGE}" -c '
		set -e
		mkdir -p /srv/server/apps/findling
		find /srv/server/apps/findling -mindepth 1 -maxdepth 1 ! -name vendor -exec rm -rf {} +
		tar -C /src --exclude=./vendor --exclude=./.phpunit.cache --exclude=./junit.xml -cf - . \
			| tar -C /srv/server/apps/findling -xf -
	'

# composer install only when the lock changed since the last install, recorded
# as a stamp inside vendor. Strictly from the committed composer.lock and with
# --no-scripts, same as the CI job.
APP_DIR="${SERVER_DIR}/apps/findling"
lock_sum=$(sha256sum "${REPO_ROOT}/php/composer.lock")
lock_sum=${lock_sum%% *}
stamp="${APP_DIR}/vendor/.findling-lock.sha256"
if [ ! -f "${APP_DIR}/vendor/autoload.php" ] || [ ! -f "${stamp}" ] \
	|| [ "$(cat "${stamp}")" != "${lock_sum}" ]; then
	echo "phpunit_docker: composer install from the committed composer.lock"
	MSYS_NO_PATHCONV=1 docker run --rm \
		-v "${SERVER_MOUNT}:/srv/server" -w /srv/server/apps/findling \
		"${COMPOSER_IMAGE}" composer install --no-interaction --no-progress --no-scripts
	printf '%s\n' "${lock_sum}" > "${stamp}"
fi

# On every run: composer.json sets optimize-autoloader, so a classmap from the
# last run would not know a class that came under tests/ since.
MSYS_NO_PATHCONV=1 docker run --rm \
	-v "${SERVER_MOUNT}:/srv/server" -w /srv/server/apps/findling \
	"${COMPOSER_IMAGE}" composer dump-autoload --no-scripts

# The JUnit file lives in the mounted server directory: /tmp of a --rm
# container is gone after the run, and apps/findling is wiped by the mirror.
# The count uses the same simplexml expression as the CI step.
INNER=$(cat <<'EOF'
rm -f /srv/server/findling-junit.xml
set +e
php vendor/bin/phpunit --no-progress --log-junit /srv/server/findling-junit.xml "$@"
rc=$?
set -e
count=$(php -r '
  $log = @simplexml_load_file("/srv/server/findling-junit.xml");
  if ($log === false) { fwrite(STDERR, "junit is not readable\n"); exit(1); }
  $total = 0;
  foreach ($log->testsuite as $suite) { $total += (int)$suite["tests"]; }
  echo $total;
') || count=0
echo "phpunit_docker: ${count} tests executed, floor ${MINIMUM_TESTS}"
if [ "$#" -gt 0 ]; then
  echo "phpunit_docker: arguments given, the floor check is skipped for this filtered run"
elif [ "${rc}" -eq 0 ] && [ "${count}" -lt "${MINIMUM_TESTS}" ]; then
  echo "phpunit_docker: fewer tests ran than the floor, so the run proves nothing" >&2
  rc=1
fi
exit "${rc}"
EOF
)

# The shared catalogues under backend/tests/fixtures (doc_key_cases.json,
# share_identity_cases.json and others) are read by the PHP suites as well.
# The CI job keeps the whole repository in findling-src; here only that one
# directory is mounted, read-only, and FINDLING_REPO_ROOT points the suites
# at it.
FIXTURES_MOUNT=$(to_mount_path "${REPO_ROOT}/backend/tests/fixtures")

set +e
MSYS_NO_PATHCONV=1 docker run --rm \
	-v "${SERVER_MOUNT}:/srv/server" -w /srv/server/apps/findling \
	-v "${FIXTURES_MOUNT}:/findling-repo/backend/tests/fixtures:ro" \
	-e "FINDLING_REPO_ROOT=/findling-repo" \
	-e "MINIMUM_TESTS=${MINIMUM_TESTS}" \
	--entrypoint sh "${RUNTIME_IMAGE}" -c "${INNER}" phpunit_docker "$@"
rc=$?
set -e

echo "phpunit_docker: junit at ${SERVER_MOUNT}/findling-junit.xml"
exit "${rc}"
