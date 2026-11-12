#!/usr/bin/env bash
# The update proof of issue #51: does the companion app survive the update the
# way the app store performs it, in the process that already loaded the old
# release?
#
# occ app:update and the update button of the apps page load the installed
# app, replace its files and run the new migrations in ONE PHP process. The
# classes of the old release stay the loaded ones. 1.6.3 shipped a migration
# that read a constant new in 1.6.3 and died there with "Undefined constant",
# on every instance that updated from the store. Neither the unit suite nor
# the upgrade jobs saw it: the suite runs with the new classes, and the jobs
# ran occ upgrade, which is a fresh process.
#
# This script runs that exact path in a throwaway Nextcloud container:
#
#   control    the released companion 1.6.2 is updated to the released 1.6.3.
#              This MUST fail with "Undefined constant". It is the positive
#              control of the harness: a proof that cannot see the bug of
#              1.6.3 proves nothing about the candidate.
#   candidate  for every tag in FROM_TAGS, the released companion of that tag
#              is updated to the php/ tree of this checkout. This MUST pass,
#              every migration of the candidate applied and installed_version
#              at the version of the candidate.
#
# The old releases are the signed archives of the GitHub releases, the bytes
# the store hands out. The driver is scripts/ci/update_in_process_driver.php.
#
# Usage:
#
#     scripts/ci/update_in_process_proof.sh
#
# Environment:
#
#     FROM_TAGS   releases the candidate is updated from (default "v1.6.2 v1.6.3")
#     NC_IMAGE    the Nextcloud image (default nextcloud:33-apache, the lower
#                 bound of the window in php/appinfo/info.xml)
#     REPO_SLUG   owner/name of the repository with the releases
#
# Needs docker and curl. Touches only containers whose name starts with
# findling-update-proof- and removes them again. Exit code 0 only when the
# control failed the way it has to and every candidate run passed.
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)

FROM_TAGS="${FROM_TAGS:-v1.6.2 v1.6.3}"
NC_IMAGE="${NC_IMAGE:-nextcloud:33-apache}"
REPO_SLUG="${REPO_SLUG:-${GITHUB_REPOSITORY:-street1983nk/nextcloud-search}}"
CONTROL_FROM="v1.6.2"
CONTROL_TO="v1.6.3"
CONTROL_MESSAGE="Undefined constant"
APP_ID="findling"
PREFIX="findling-update-proof"

WORK=$(mktemp -d)
cleanup() {
	MSYS_NO_PATHCONV=1 docker ps -aq --filter "name=^${PREFIX}-" | while read -r id; do MSYS_NO_PATHCONV=1 docker rm -f "${id}" >/dev/null 2>&1 || true; done
	rm -rf "${WORK}"
}
trap cleanup EXIT

# Git Bash on Windows rewrites /var/... arguments into Windows paths. The
# containers want their paths as they are, so every docker call goes through
# dk, and a path on the host is converted by hand where docker cp needs one.
# On any other system both are the plain thing.
dk() {
	MSYS_NO_PATHCONV=1 docker "$@"
}
host_path() {
	if command -v cygpath >/dev/null 2>&1; then
		cygpath -m "$1"
	else
		printf '%s
' "$1"
	fi
}

# The signed companion archive of a release, loaded once per tag.
release_archive() {
	local tag=$1 file="${WORK}/${1}.tar.gz"
	if [ ! -s "${file}" ]; then
		curl -sfL --retry 3 --retry-delay 5 -o "${file}" \
			"https://github.com/${REPO_SLUG}/releases/download/${tag}/${APP_ID}.tar.gz" \
			|| { echo "the companion archive of ${tag} could not be loaded" >&2; exit 1; }
	fi
	printf '%s\n' "${file}"
}

# A fresh Nextcloud on SQLite with the released companion of a tag enabled.
start_instance() {
	local name=$1 tag=$2 archive
	archive=$(release_archive "${tag}")
	dk rm -f "${name}" >/dev/null 2>&1 || true
	dk run -d --name "${name}" \
		-e SQLITE_DATABASE=nextcloud \
		-e NEXTCLOUD_ADMIN_USER=admin \
		-e NEXTCLOUD_ADMIN_PASSWORD="proof-$(date +%s)-${RANDOM}" \
		"${NC_IMAGE}" >/dev/null
	local tries=0
	until dk exec -u www-data "${name}" php occ status 2>/dev/null | grep -q 'installed: true'; do
		tries=$((tries + 1))
		if [ "${tries}" -gt 90 ]; then
			echo "${name} did not finish its installation" >&2
			dk logs --tail 40 "${name}" >&2
			exit 1
		fi
		sleep 2
	done
	dk cp "$(host_path "${archive}")" "${name}:/tmp/old.tar.gz" >/dev/null
	dk exec "${name}" sh -c "tar -xzf /tmp/old.tar.gz -C /var/www/html/custom_apps && chown -R www-data:www-data /var/www/html/custom_apps/${APP_ID}"
	dk exec -u www-data "${name}" php occ app:enable "${APP_ID}"
	dk cp "$(host_path "${SCRIPT_DIR}/update_in_process_driver.php")" "${name}:/tmp/driver.php" >/dev/null
}

# Hands the new app to the instance and runs the update in one process.
# $3 is a directory on the host or a release archive.
run_update() {
	local name=$1 new=$2
	dk exec "${name}" sh -c "rm -rf /tmp/new && mkdir -p /tmp/new"
	if [ -d "${new}" ]; then
		dk cp "$(host_path "${new}")/." "${name}:/tmp/new/${APP_ID}" >/dev/null
	else
		dk cp "$(host_path "${new}")" "${name}:/tmp/new.tar.gz" >/dev/null
		dk exec "${name}" tar -xzf /tmp/new.tar.gz -C /tmp/new
	fi
	dk exec "${name}" chown -R www-data:www-data /tmp/new
	dk exec -u www-data "${name}" php /tmp/driver.php "${APP_ID}" "/tmp/new/${APP_ID}"
}

failures=0

echo "== control: released ${CONTROL_FROM} to released ${CONTROL_TO}, has to fail with '${CONTROL_MESSAGE}'"
start_instance "${PREFIX}-control" "${CONTROL_FROM}"
set +e
control_out=$(run_update "${PREFIX}-control" "$(release_archive "${CONTROL_TO}")" 2>&1)
control_rc=$?
set -e
printf '%s\n' "${control_out}"
if [ "${control_rc}" -eq 0 ] || ! printf '%s\n' "${control_out}" | grep -q "UPDATE-PROOF failed .*${CONTROL_MESSAGE}"; then
	echo "CONTROL BROKEN: the harness did not reproduce the failure of ${CONTROL_TO}, so it cannot vouch for the candidate"
	failures=$((failures + 1))
else
	echo "control ok: the failure of ${CONTROL_TO} is reproduced"
fi
dk rm -f "${PREFIX}-control" >/dev/null

for tag in ${FROM_TAGS}; do
	echo "== candidate: released ${tag} to php/ of this checkout, has to pass"
	name="${PREFIX}-from-${tag//./-}"
	start_instance "${name}" "${tag}"
	set +e
	out=$(run_update "${name}" "${REPO_ROOT}/php" 2>&1)
	rc=$?
	set -e
	printf '%s\n' "${out}"
	if [ "${rc}" -ne 0 ] || ! printf '%s\n' "${out}" | grep -q '^UPDATE-PROOF ok '; then
		echo "CANDIDATE FAILED from ${tag}"
		failures=$((failures + 1))
	else
		# The app answers after the update, in a fresh process.
		dk exec -u www-data "${name}" php occ app:list --output=json | grep -q "\"${APP_ID}\"" \
			|| { echo "CANDIDATE FAILED from ${tag}: the app is not listed after the update"; failures=$((failures + 1)); }
	fi
	dk rm -f "${name}" >/dev/null
done

if [ "${failures}" -ne 0 ]; then
	echo "update proof: ${failures} failure(s)"
	exit 1
fi
echo "update proof: control reproduced, every candidate run passed"
