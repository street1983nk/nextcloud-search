#!/usr/bin/env bash
# Run the PHP security gates of the companion app locally, inside Docker, the
# way the jobs of .github/workflows/php.yml run them on a runner (phase 44).
#
# Usage:
#
#     scripts/dev/php_gates_docker.sh psalm
#     scripts/dev/php_gates_docker.sh cs
#     scripts/dev/php_gates_docker.sh workflows
#     scripts/dev/php_gates_docker.sh all
#
#   psalm      the job psalm-taint: scripts/ci/psalm_taint_gate.sh once per
#              nextcloud/ocp tag of the job matrix, serially
#   cs         the job php-cs: scripts/ci/php_cs_gate.sh in php:8.2-cli
#   workflows  the jobs zizmor and actionlint of .github/workflows/
#              workflow-lint.yml: scripts/ci/workflow_lint_gate.sh once in the
#              zizmor image and once in the actionlint image, serially
#   all        every gate this script knows, serially: psalm, cs, workflows
#
# An unknown subcommand ends with exit 2.
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
#     port). The Psalm gate needs jq, which runs on the host: neither image
#     carries it, and the owner decided against installing packages into a
#     container (decision E-09 of phase 44, "Host-jq per Shim"). A small php
#     shim on PATH hands every php call of that gate to the container, with the
#     cache directory mounted at the identical path, so every path the gate
#     passes along means the same file on both sides. The style gate needs no
#     jq and runs inside php:8.2-cli as a whole.
#   - The workflow gate needs no mirror: workflows and shell scripts are LF in
#     every checkout (.gitattributes), and actionlint wants the .git directory.
#     The repository is mounted read only, without network, exactly as the CI
#     job mounts its workspace; the images are the ones of workflow-lint.yml.
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

# The same digests as in 44-RESEARCH.md (composer:2, php:8.3-cli and
# php:8.2-cli, looked up for phase 44). A new digest is a new owner decision,
# not a silent refresh.
COMPOSER_IMAGE="composer:2@sha256:50ea4d33fdcde1adb0f045547295faa1548b33872e5f789dae5b02ce2fb5de93"
PHP83_IMAGE="php:8.3-cli@sha256:9e2a4e9b1704c05cc469fddbf9b0f0f205e2bb13efd249bbad177289ebdc5c7c"
PHP82_IMAGE="php:8.2-cli@sha256:842748bc4526d4c3c56501fd314e2d75d1005e8a45b7a40f9768ee820df0a6d6"
# The workflow tools, released by the owner with these digests (decision E-07
# of phase 44) and identical to the images of workflow-lint.yml.
ZIZMOR_IMAGE="ghcr.io/zizmorcore/zizmor:1.32.0@sha256:3014cc8f68f663935f69b3c3e0e41f5ce102b268d97db13db0f62208747f860d"
ACTIONLINT_IMAGE="rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667"

say() {
	echo "php_gates_docker: $*"
}

die() {
	echo "php_gates_docker: $*" >&2
	exit 1
}

usage() {
	echo "usage: scripts/dev/php_gates_docker.sh psalm|cs|workflows|all" >&2
	exit 2
}

[ "$#" -eq 1 ] || usage
case "$1" in
	psalm | cs | workflows | all) COMMAND="$1" ;;
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
	done < <(git -C "${REPO_ROOT}" ls-files -z --cached --others --exclude-standard -- php scripts/ci/psalm_taint_gate.sh scripts/ci/php_cs_gate.sh)
	[ -s "${list}" ] || die "git ls-files gave no file under php/"
	tar -C "${REPO_ROOT}" -cf - -T "${list}" | tar -C "${MIRROR}" -xf -
	# grep -I skips binary files, so only text files lose their carriage returns.
	# -U keeps the grep of Git for Windows from dropping the carriage return
	# before it matches (without it no CRLF file is ever found); elsewhere -U
	# changes nothing.
	local crlf="${GATES_BASE}/crlf.lst"
	grep -rlUI $'\r' "${MIRROR}" >"${crlf}" || true
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
	command -v jq >/dev/null 2>&1 || die "jq is required on the host; the psalm gate counts its findings with it"
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

# The style gate as a whole inside php:8.2-cli, the PHP of the job php-cs; the
# image carries bash, and the gate needs nothing else.
run_cs_gate() {
	say "php-cs-fixer gate (nextcloud/coding-standard)"
	build_mirror
	run_composer "${MIRROR}/php/tools/php-cs-fixer" install --no-interaction --no-progress --no-scripts
	if ! MSYS_NO_PATHCONV=1 docker run --rm \
		-v "${BASE_MOUNT}:${GATES_BASE}" -w "${MIRROR}" \
		"${PHP82_IMAGE}" bash scripts/ci/php_cs_gate.sh; then
		die "php-cs-fixer gate is red"
	fi
	say "php-cs-fixer gate green"
}

# The workflow gate, one container per tool, one after the other. The images
# carry sh but no bash, so the gate script is POSIX sh and is started with sh.
run_workflow_gate() {
	local repo_mount
	repo_mount=$(to_mount_path "${REPO_ROOT}")
	local tool image
	for tool in zizmor actionlint; do
		case "${tool}" in
			zizmor) image="${ZIZMOR_IMAGE}" ;;
			actionlint) image="${ACTIONLINT_IMAGE}" ;;
		esac
		say "workflow gate: ${tool}"
		if ! MSYS_NO_PATHCONV=1 docker run --rm --network none \
			-v "${repo_mount}:/repo:ro" -w /repo \
			--entrypoint sh "${image}" scripts/ci/workflow_lint_gate.sh "${tool}"; then
			die "workflow gate is red (${tool})"
		fi
	done
	say "workflow gate green (zizmor, actionlint)"
}

case "${COMMAND}" in
	psalm) run_psalm_gate ;;
	cs) run_cs_gate ;;
	workflows) run_workflow_gate ;;
	all)
		run_psalm_gate
		run_cs_gate
		run_workflow_gate
		;;
esac
