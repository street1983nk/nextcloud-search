#!/usr/bin/env bash
# The Psalm taint gate of the companion app (phase 44, requirement PRUEF-02).
#
# Psalm 6.20.10 runs its taint analysis over php/lib, php/templates and
# php/appinfo/routes.php with the configuration in php/psalm.xml: the
# AppFrameworkTainter plugin of nextcloud/server turns every parameter of a
# public controller method into user input, nextcloud/ocp contributes the
# sources and sinks of the public API, and a stub adds the path of
# exAppRequest as an SSRF sink. The script runs two passes:
#
#   real   the app as it is. Every finding in the SARIF report makes the gate
#          red. The script counts the findings itself with jq and does not
#          trust the exit code: Psalm 6.20.10 ends with 2 on findings, other
#          versions behaved differently, and a crash (any exit besides 0 and 2,
#          or no report) must never read as "no findings". Exit 2 with an
#          empty report is red as well, because then the count is wrong.
#   probe  the positive control. tools/psalm/taint-probe/ProbeController.php
#          is copied to lib/TaintProbe/, Psalm runs again, and the report
#          MUST hold at least two findings, all of them in lib/TaintProbe/,
#          among them TaintedHtml (proves the plugin works) and TaintedSql
#          (proves this nextcloud/ocp still carries its taint annotations).
#          A gate that cannot see these two flows is blind and proves nothing
#          about the app, so that is red too. The copy is removed again.
#
# Usage:
#
#     scripts/ci/psalm_taint_gate.sh
#
# Environment:
#
#     PHP_DIR   the companion app directory with psalm.xml (default "php",
#               relative to the repository root; an absolute path is used as
#               it is)
#
# Needs php, jq, and composer install plus composer dump-autoload done before:
# Psalm from php/tools/psalm/vendor and a composer autoloader in php/. The job
# psalm-taint of .github/workflows/php.yml does both. Exit code 0 only when the
# real pass has no finding and the probe was seen.
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)

PHP_DIR="${PHP_DIR:-php}"
case "${PHP_DIR}" in
	/*) ;;
	*) PHP_DIR="${REPO_ROOT}/${PHP_DIR}" ;;
esac

PSALM="tools/psalm/vendor/bin/psalm"
PROBE_SOURCE="tools/psalm/taint-probe/ProbeController.php"
PROBE_DIR="lib/TaintProbe"

fail() {
	echo "psalm taint gate: $1" >&2
	exit 1
}

blind() {
	fail "the taint gate is blind: $1"
}

command -v jq >/dev/null 2>&1 || fail "jq is required to count the findings"
cd "${PHP_DIR}" || fail "no such directory: ${PHP_DIR}"
[ -f psalm.xml ] || fail "no psalm.xml in ${PHP_DIR}"
[ -f "${PSALM}" ] || fail "${PSALM} is missing; run composer install in tools/psalm first"
[ -f "${PROBE_SOURCE}" ] || fail "${PROBE_SOURCE} is missing; without it there is no positive control"

WORK=$(mktemp -d)
PROBE_CREATED=0
cleanup() {
	if [ "${PROBE_CREATED}" -eq 1 ]; then
		rm -rf "${PROBE_DIR}"
	fi
	rm -rf "${WORK}"
}
trap cleanup EXIT

run_psalm() {
	php "${PSALM}" --no-cache --threads=1 --no-progress --monochrome \
		--taint-analysis --report="$1" --report-show-info=false
}

# Prints the number of results in a SARIF report, or fails the gate when the
# report is not JSON of the expected shape.
count_findings() {
	local n
	n=$(jq '[.runs[].results[]] | length' "$1") || fail "$1 is not a readable SARIF report"
	case "${n}" in
		'' | *[!0-9]*) fail "$1 gave no count (${n})" ;;
	esac
	printf '%s\n' "${n}"
}

# Psalm writes the numeric shortcode of an issue as ruleId (245) and its name
# (TaintedHtml) only in the rules of the tool driver, so every result is
# resolved through that table. A result whose id is not in the table keeps the
# id, which can never be mistaken for a name. Double quotes with an escaped
# dollar: the jq variable is for jq, not for the shell.
NAMED_RESULTS=".runs[] | ((.tool.driver.rules // []) | map({key: .id, value: .name}) | from_entries) as \$names | .results[] | . + {rule: (\$names[.ruleId] // .ruleId)}"

list_findings() {
	jq -r "${NAMED_RESULTS}"' | "  \(.rule) \(.locations[0].physicalLocation.artifactLocation.uri // "?"):\(.locations[0].physicalLocation.region.startLine // "?")"' "$1"
}

# Pass 1: the app as it is.
REAL_SARIF="${WORK}/taint.sarif"
set +e
run_psalm "${REAL_SARIF}"
rc=$?
set -e
case "${rc}" in
	0 | 2) ;;
	*) fail "psalm crashed or refused its config (exit ${rc})" ;;
esac
[ -s "${REAL_SARIF}" ] || fail "psalm wrote no SARIF report (exit ${rc})"
count=$(count_findings "${REAL_SARIF}")
echo "taint findings: ${count}"
if [ "${count}" -gt 0 ]; then
	list_findings "${REAL_SARIF}"
	fail "${count} taint finding(s); fix each one, or bring it to the owner, never suppress it silently"
fi
if [ "${rc}" -ne 0 ]; then
	fail "psalm exited ${rc} but the SARIF report holds no finding, so the count cannot be trusted"
fi

# Pass 2: the positive control. The directory must not exist yet: the gate
# only ever removes what it created itself.
[ ! -e "${PROBE_DIR}" ] || fail "${PROBE_DIR} exists already; refusing to mix the probe with it"
PROBE_CREATED=1
mkdir -p "${PROBE_DIR}"
cp "${PROBE_SOURCE}" "${PROBE_DIR}/ProbeController.php"
PROBE_SARIF="${WORK}/probe.sarif"
PROBE_LOG="${WORK}/probe.log"
# The output of this pass goes to a file: its findings are wanted, and on a
# runner they must not show up as annotations of the commit.
set +e
run_psalm "${PROBE_SARIF}" >"${PROBE_LOG}" 2>&1
probe_rc=$?
set -e
rm -rf "${PROBE_DIR}"
PROBE_CREATED=0

if [ "${probe_rc}" -ne 2 ]; then
	cat "${PROBE_LOG}" >&2
	blind "psalm exited ${probe_rc} on the probe, expected 2"
fi
[ -s "${PROBE_SARIF}" ] || blind "psalm wrote no SARIF report for the probe"
probe_count=$(count_findings "${PROBE_SARIF}")
list_findings "${PROBE_SARIF}"
[ "${probe_count}" -ge 2 ] || blind "the probe gave ${probe_count} finding(s), expected at least 2"
outside=$(jq '[.runs[].results[] | select((.locations[0].physicalLocation.artifactLocation.uri // "") | contains("lib/TaintProbe/") | not)] | length' "${PROBE_SARIF}") || blind "the probe report is not readable"
[ "${outside}" = "0" ] || blind "${outside} probe finding(s) outside lib/TaintProbe/; the probe run saw something else"
for rule in TaintedHtml TaintedSql; do
	if ! jq -e --arg rule "${rule}" "any(${NAMED_RESULTS}; .rule == \$rule)" "${PROBE_SARIF}" >/dev/null; then
		blind "the probe gave no ${rule}"
	fi
done

echo "psalm taint gate: 0 findings, probe found ${probe_count}"
