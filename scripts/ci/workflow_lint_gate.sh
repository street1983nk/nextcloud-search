#!/bin/sh
# The workflow security gate (phase 44, requirement PRUEF-04).
#
# Two tools judge every workflow, the composite action and dependabot.yml:
#
#   zizmor      security audit, offline, persona auditor (owner decision E-04),
#               every finding of severity medium or above is red. Exit 0 is
#               green, exit 13 (highest finding medium) and 14 (high) are red
#               with the findings, any other exit code means zizmor did not run
#               and is red as well. Online audits (known vulnerable actions and
#               the like) are left out on purpose: the gate needs no token and
#               runs the same way locally.
#   actionlint  syntax, expressions and the shellcheck pass over every run
#               block, with shellcheck findings of every severity, including
#               info and style (owner decision E-03). Exit 0 is green, exit 1
#               is red with the findings, any other exit code is red too.
#
# Each tool has its positive control, run in the same pass against
# .github/fixtures/workflow-lint-probe.yml, a workflow that is unsafe on
# purpose:
#
#   zizmor      MUST answer with exit 13 or 14. Anything else means the audit
#               cannot see a template injection any more, so the gate is blind.
#   actionlint  MUST answer with exit 1 AND name SC2086 in its output. Exit 1
#               alone already comes from the undefined steps property of the
#               probe; SC2086 is an info finding of shellcheck and is only
#               reported while shellcheck runs at all (actionlint skips it
#               silently when the binary is missing) and while its threshold
#               still includes info. Without it the gate is blind.
#
# An inherited SHELLCHECK_OPTS variable is removed before actionlint runs:
# shellcheck reads it, and a value from the calling environment would lower
# the threshold without a trace in this file.
#
# Usage:
#
#     scripts/ci/workflow_lint_gate.sh            both tools
#     scripts/ci/workflow_lint_gate.sh zizmor     zizmor and its control
#     scripts/ci/workflow_lint_gate.sh actionlint actionlint and its control
#
# Environment: none is read. zizmor and actionlint must be on PATH, as they are
# in their pinned images (ghcr.io/zizmorcore/zizmor 1.32.0 and
# rhysd/actionlint 1.7.12, both by digest in .github/workflows/workflow-lint.yml
# and scripts/dev/php_gates_docker.sh). The script is POSIX sh and uses shell
# builtins only, because the actionlint image has no bash and neither image is
# guaranteed to carry grep. It runs from the repository root, which it finds
# relative to its own path; actionlint needs the .git directory there.
#
# Exit code 0 only when every requested tool found nothing and saw its probe.
set -eu

# Owner decision E-04: the gate audits with the persona auditor.
ZIZMOR_PERSONA="auditor"
PROBE=".github/fixtures/workflow-lint-probe.yml"

fail() {
	echo "workflow lint gate: $1" >&2
	exit 1
}

case "$0" in
	*/*) SCRIPT_DIR=${0%/*} ;;
	*) SCRIPT_DIR=. ;;
esac
cd "${SCRIPT_DIR}/../.." || fail "cannot change to the repository root"
[ -d .github/workflows ] || fail "no .github/workflows below $(pwd)"
[ -f "${PROBE}" ] || fail "the probe ${PROBE} is missing, so the gate is blind"

run_zizmor() {
	command -v zizmor >/dev/null 2>&1 || fail "zizmor is not on PATH"
	set +e
	zizmor --offline --no-progress --persona "${ZIZMOR_PERSONA}" --min-severity medium --format plain .
	rc=$?
	set -e
	case "${rc}" in
		0) echo "zizmor: no finding of severity medium or above" ;;
		13 | 14) fail "zizmor reports findings of severity medium or above (exit ${rc}, list above)" ;;
		*) fail "zizmor failed to run (exit ${rc})" ;;
	esac

	set +e
	zizmor --offline --no-progress --persona "${ZIZMOR_PERSONA}" --min-severity medium --format plain "${PROBE}" >/dev/null 2>&1
	probe_rc=$?
	set -e
	case "${probe_rc}" in
		13 | 14) echo "zizmor: probe seen (exit ${probe_rc})" ;;
		*) fail "the zizmor gate is blind: exit ${probe_rc} on ${PROBE}, expected 13 or 14" ;;
	esac
}

run_actionlint() {
	command -v actionlint >/dev/null 2>&1 || fail "actionlint is not on PATH"
	# Owner decision E-03: shellcheck findings of every severity count.
	unset SHELLCHECK_OPTS
	set +e
	actionlint -no-color -oneline
	rc=$?
	set -e
	case "${rc}" in
		0) echo "actionlint: no finding" ;;
		1) fail "actionlint reports findings (list above)" ;;
		*) fail "actionlint failed to run (exit ${rc})" ;;
	esac

	set +e
	probe_out=$(actionlint -no-color -oneline "${PROBE}" 2>&1)
	probe_rc=$?
	set -e
	if [ "${probe_rc}" -ne 1 ]; then
		printf '%s\n' "${probe_out}"
		fail "the actionlint gate is blind: exit ${probe_rc} on ${PROBE}, expected 1"
	fi
	case "${probe_out}" in
		*SC2086*) echo "actionlint: probe seen (exit 1, SC2086 reported)" ;;
		*)
			printf '%s\n' "${probe_out}"
			fail "the actionlint gate is blind: no SC2086 on ${PROBE}, shellcheck did not run or its threshold excludes info"
			;;
	esac
}

case "$#" in
	0) MODE=both ;;
	1) MODE=$1 ;;
	*) fail "usage: scripts/ci/workflow_lint_gate.sh [zizmor|actionlint]" ;;
esac

case "${MODE}" in
	zizmor) run_zizmor ;;
	actionlint) run_actionlint ;;
	both)
		run_zizmor
		run_actionlint
		;;
	*) fail "unknown mode ${MODE}; expected zizmor or actionlint" ;;
esac

echo "workflow lint gate: green (${MODE})"
