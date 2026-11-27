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
#   control 2  the released companion of the newest tag in FROM_TAGS is
#              updated to php/ of this checkout WITHOUT the migrations of its
#              own release (every lib/Migration/Version*.php that the archive
#              of that tag does not carry). On a minor step this MUST fail
#              with "survived the minor step": the driver plants the recorded
#              container version before the swap and demands it gone after a
#              minor step (plan 45-26), and only the migration of the step
#              drops it. Skipped on a patch step, which may keep the value.
#   candidate  for every tag in FROM_TAGS, the released companion of that tag
#              is updated to the php/ tree of this checkout. This MUST pass,
#              every migration of the candidate applied, installed_version
#              at the version of the candidate and, after a minor step, the
#              planted recorded version gone.
#
# FROM_TAGS holds the last release of every minor line from 1.3 on and every
# 1.6 tag from v1.6.2 on, then v1.7.0: v1.3.2 has neither markScanStale() nor
# scan_recounted_at and holds I-45-26-01, v1.4.3 is the way of I-45-23-07,
# v1.5.1 closes the line 1.5, and the newest tag is the release before the
# candidate (backend/tests/test_update_in_process_proof.py holds that).
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
#     FROM_TAGS   releases the candidate is updated from (default "v1.3.2
#                 v1.4.3 v1.5.1 v1.6.2 v1.6.3 v1.6.4 v1.6.5 v1.7.0"); the last word is
#                 the start of control 2
#     NC_IMAGE    the Nextcloud image (default nextcloud:33-apache, the lower
#                 bound of the window in php/appinfo/info.xml)
#     REPO_SLUG   owner/name of the repository with the releases
#
# Needs docker and curl. Touches only containers whose name starts with
# findling-update-proof- and removes them again. Exit code 0 only when both
# controls failed the way they have to (control 2 skipped on a patch step)
# and every candidate run passed.
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)

FROM_TAGS="${FROM_TAGS:-v1.3.2 v1.4.3 v1.5.1 v1.6.2 v1.6.3 v1.6.4 v1.6.5 v1.7.0}"
NC_IMAGE="${NC_IMAGE:-nextcloud:33-apache}"
REPO_SLUG="${REPO_SLUG:-${GITHUB_REPOSITORY:-street1983nk/nextcloud-search}}"
CONTROL_FROM="v1.6.2"
CONTROL_TO="v1.6.3"
CONTROL_MESSAGE="Undefined constant"
CONTROL2_MESSAGE="survived the minor step"
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

# Control 2: the newest tag updated to the candidate without the migrations
# of its own release. Major and minor of both are compared; only a minor step
# has to drop the recorded version.
read -r -a from_list <<< "${FROM_TAGS}"
newest_tag="${from_list[${#from_list[@]}-1]}"
candidate_version=$(grep -m1 -oE '<version>[0-9]+\.[0-9]+\.[0-9]+</version>' "${REPO_ROOT}/php/appinfo/info.xml" | sed 's/<[^>]*>//g')
control2_ran=0
if [ "$(printf '%s' "${newest_tag#v}" | cut -d. -f1,2)" = "$(printf '%s' "${candidate_version}" | cut -d. -f1,2)" ]; then
	echo "control 2 skipped: ${newest_tag} and the candidate ${candidate_version} share major and minor, a patch step may keep the recorded version"
else
	echo "== control 2: released ${newest_tag} to php/ of this checkout without the migrations of ${candidate_version}, has to fail with '${CONTROL2_MESSAGE}'"
	control2_dir="${WORK}/php-control2"
	rm -rf "${control2_dir}"
	cp -R "${REPO_ROOT}/php" "${control2_dir}"
	# The paths of the archive, normalised: a leading ./ goes, and only the
	# file name under <app id>/lib/Migration/ is compared. Without this an
	# archive packed as ./findling/... would match nothing.
	in_tag=$(tar -tzf "$(release_archive "${newest_tag}")" | sed 's#^\./##' | sed -n "s#^${APP_ID}/lib/Migration/\\(Version[^/]*\\.php\\)\$#\\1#p" | LC_ALL=C sort)
	removed=()
	for file in "${control2_dir}"/lib/Migration/Version*.php; do
		base=$(basename "${file}")
		if ! grep -qxF "${base}" <<< "${in_tag}"; then
			rm -f "${file}"
			removed+=("${base}")
		fi
	done
	echo "control 2 removes: ${removed[*]}"
	if [ "${#removed[@]}" -eq 0 ]; then
		echo "CONTROL 2 BROKEN: no migration of the candidate is missing from ${newest_tag}"
		failures=$((failures + 1))
	else
		start_instance "${PREFIX}-control2" "${newest_tag}"
		set +e
		control2_out=$(run_update "${PREFIX}-control2" "${control2_dir}" 2>&1)
		control2_rc=$?
		set -e
		printf '%s\n' "${control2_out}"
		# A pass and another failure are two different statements (R-45-21-19):
		# exit 0 means the candidate slipped through the probe, any other
		# failure (docker gone, archive missing) means this run proves nothing,
		# and the log has to say which of the two happened.
		if [ "${control2_rc}" -eq 0 ]; then
			echo "CONTROL 2 BROKEN: the candidate without the migrations of ${candidate_version} passed the probe, so the probe cannot vouch for the migration of the minor step"
			failures=$((failures + 1))
		elif ! printf '%s\n' "${control2_out}" | grep -q "UPDATE-PROOF failed .*${CONTROL2_MESSAGE}"; then
			echo "CONTROL 2 BROKEN: the run from ${newest_tag} failed, but not with '${CONTROL2_MESSAGE}', so this run proves nothing about the migration of the minor step"
			failures=$((failures + 1))
		else
			echo "control 2 ok: without the migrations of ${candidate_version} the recorded version survives ${newest_tag} -> ${candidate_version}, and the probe sees it"
			control2_ran=1
		fi
		dk rm -f "${PREFIX}-control2" >/dev/null
	fi
fi

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
if [ "${control2_ran}" -eq 1 ]; then
	echo "update proof: both controls reproduced, every candidate run passed"
else
	echo "update proof: control 1 reproduced, control 2 skipped (patch step), every candidate run passed"
fi
