#!/usr/bin/env bash
# Run the PHP security gates of the companion app locally, inside Docker, the
# way the jobs of .github/workflows/php.yml run them on a runner (phase 44).
#
# Usage:
#
#     scripts/dev/php_gates_docker.sh psalm
#     scripts/dev/php_gates_docker.sh all
#
#   psalm  the job psalm-taint: scripts/ci/psalm_taint_gate.sh once per
#          nextcloud/ocp tag of the job matrix, serially
#   all    every gate this script knows, serially (today: psalm)
#
# The subcommands cs (php-cs-fixer) and workflows (zizmor and actionlint) are
# added by later plans of phase 44. An unknown subcommand ends with exit 2.
#
# How a run is arranged, and why:
#
#   - The gates never see the working tree. php/ is mirrored from scratch into
#     a cache directory outside the repository, from git ls-files (tracked
#     files plus untracked files that are not ignored), so vendor directories
#     and other ignored output never come along. Carriage returns are removed
#     from every text file of the mirror: on Windows the working tree holds
#     CRLF, a runner checks out LF, and the gates must judge what CI judges.
#   - The OCP tags are read out of the job psalm-taint in php.yml and never
#     written down here, so the local recipe cannot drift from the CI matrix.
#   - The gate script itself is the one CI runs, copied into the mirror.
#   - php and composer run in containers (pinned by digest, --rm, no name, no
#     port). jq runs on the host: neither image carries it, and the owner
#     decided against installing packages into a container (phase 44, "Host-jq
#     per Shim"). A small php shim on PATH hands every php call of the gate to
#     the container, with the cache directory mounted at the identical path, so
#     every path the gate passes along means the same file on both sides.
#
# FINDLING_PHP_GATES_DIR overrides where the cache directory lives (default
# ${TMPDIR:-/tmp}/findling-php-gates). Each leg rebuilds the mirror; only the
# composer download cache is kept between runs.
#
# Needs Docker, git, jq and bash on the host. The exit code is 0 only when every
# leg of every requested gate is green.
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)
PHP_WORKFLOW="${REPO_ROOT}/.github/workflows/php.yml"

# The same digests as in 44-RESEARCH.md (composer:2 and php:8.3-cli, looked up
# for phase 44). A new digest is a new owner decision, not a silent refresh.
COMPOSER_IMAGE="composer:2@sha256:50ea4d33fdcde1adb0f045547295faa1548b33872e5f789dae5b02ce2fb5de93"
PHP83_IMAGE="php:8.3-cli@sha256:9e2a4e9b1704c05cc469fddbf9b0f0f205e2bb13efd249bbad177289ebdc5c7c"

say() {
	echo "php_gates_docker: $*"
}

die() {
	echo "php_gates_docker: $*" >&2
	exit 1
}

usage() {
	echo "usage: scripts/dev/php_gates_docker.sh psalm|all" >&2
	exit 2
}

[ "$#" -eq 1 ] || usage
case "$1" in
	psalm | all) COMMAND="$1" ;;
	*) usage ;;
esac

# Docker Desktop on Windows wants C:/... in a mount, Git Bash hands out
# /c/...; cygpath -m converts, and on any other system the path stays as it is.
to_mount_path() {
	if command -v cygpath >/dev/null 2>&1; then
		cygpath -m "$1"
	else
		printf '%s\n' "$1"
	fi
}

# Every "- vNN.N.N" line between the header of the job psalm-taint and the
# header of the next job: the ocp matrix of that job and nothing else. One sed
# call and no pipe, like read_workflow_key in phpunit_docker.sh.
read_ocp_tags() {
	sed -n -E '/^  psalm-taint:/,/^  [A-Za-z0-9_-]+:/{s/^[[:space:]]+-[[:space:]]+(v[0-9]+\.[0-9]+\.[0-9]+)[[:space:]]*$/\1/p}' "${PHP_WORKFLOW}"
}

[ -f "${PHP_WORKFLOW}" ] || die "no workflow at ${PHP_WORKFLOW}"
command -v jq >/dev/null 2>&1 || die "jq is required on the host; the gates count their findings with it"
docker info >/dev/null 2>&1 || die "docker is not reachable; start Docker Desktop first"

GATES_BASE="${FINDLING_PHP_GATES_DIR:-${TMPDIR:-/tmp}/findling-php-gates}"
mkdir -p "${GATES_BASE}"
GATES_BASE=$(CDPATH='' cd -- "${GATES_BASE}" && pwd)
MIRROR="${GATES_BASE}/tree"
COMPOSER_CACHE="${GATES_BASE}/composer-cache"
SHIM_DIR="${GATES_BASE}/bin"
BASE_MOUNT=$(to_mount_path "${GATES_BASE}")
mkdir -p "${COMPOSER_CACHE}" "${SHIM_DIR}"

# Rebuild the mirror: php/ as git sees it plus the gate scripts, CR removed.
build_mirror() {
	rm -rf "${MIRROR}"
	mkdir -p "${MIRROR}"
	local list="${GATES_BASE}/files.lst"
	: >"${list}"
	local path
	while IFS= read -r -d '' path; do
		# A tracked file deleted in the working tree is not there to copy.
		if [ -f "${REPO_ROOT}/${path}" ]; then
			printf '%s\n' "${path}" >>"${list}"
		fi
	done < <(git -C "${REPO_ROOT}" ls-files -z --cached --others --exclude-standard -- php scripts/ci/psalm_taint_gate.sh)
	[ -s "${list}" ] || die "git ls-files gave no file under php/"
	tar -C "${REPO_ROOT}" -cf - -T "${list}" | tar -C "${MIRROR}" -xf -
	# grep -I skips binary files, so only text files lose their carriage returns.
	local crlf="${GATES_BASE}/crlf.lst"
	grep -rlI $'\r' "${MIRROR}" >"${crlf}" || true
	if [ -s "${crlf}" ]; then
		tr '\n' '\0' <"${crlf}" | xargs -0 sed -i 's/\r$//'
	fi
	rm -f "${list}" "${crlf}"
}

# The composer cache lives next to the mirror and survives it; everything else
# runs in the mirror. The paths inside the container equal the host paths.
run_composer() {
	local workdir="$1"
	shift
	MSYS_NO_PATHCONV=1 docker run --rm \
		-v "${BASE_MOUNT}:${GATES_BASE}" -w "${workdir}" \
		-e "COMPOSER_CACHE_DIR=${COMPOSER_CACHE}" \
		"${COMPOSER_IMAGE}" composer "$@"
}

# The php shim: the gate calls php, the shim runs it in php:8.3-cli with the
# cache directory mounted at the identical path and the caller's directory as
# working directory.
write_php_shim() {
	local image="$1"
	cat >"${SHIM_DIR}/php" <<EOF
#!/usr/bin/env bash
# Written by scripts/dev/php_gates_docker.sh on every run; do not edit.
set -euo pipefail
MSYS_NO_PATHCONV=1 exec docker run --rm -v "${BASE_MOUNT}:${GATES_BASE}" -w "\${PWD}" "${image}" php "\$@"
EOF
	chmod +x "${SHIM_DIR}/php"
}

run_psalm_gate() {
	local tags
	tags=$(read_ocp_tags)
	local count
	count=$(printf '%s\n' "${tags}" | grep -c . || true)
	if [ "${count}" -lt 3 ]; then
		die "found ${count} nextcloud/ocp tag(s) in the job psalm-taint of ${PHP_WORKFLOW}, expected at least 3"
	fi
	write_php_shim "${PHP83_IMAGE}"
	local tag
	for tag in ${tags}; do
		say "psalm taint gate against nextcloud/ocp ${tag}"
		build_mirror
		run_composer "${MIRROR}/php/tools/psalm" install --no-interaction --no-progress --no-scripts
		run_composer "${MIRROR}/php/tools/psalm" require --dev "nextcloud/ocp:${tag}" --no-interaction --no-progress --no-scripts -W
		run_composer "${MIRROR}/php" dump-autoload --no-scripts
		# TMPDIR inside the mirror: the SARIF reports are written by php in the
		# container and read by jq on the host, so they need a shared path.
		mkdir -p "${MIRROR}/.tmp"
		if ! (cd "${MIRROR}" && TMPDIR="${MIRROR}/.tmp" PATH="${SHIM_DIR}:${PATH}" bash scripts/ci/psalm_taint_gate.sh); then
			die "psalm taint gate is red against nextcloud/ocp ${tag}"
		fi
	done
	say "psalm taint gate green against ${count} nextcloud/ocp tags"
}

case "${COMMAND}" in
	psalm) run_psalm_gate ;;
	all) run_psalm_gate ;;
esac
