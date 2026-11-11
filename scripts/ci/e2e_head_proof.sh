#!/usr/bin/env bash
# The end to end proof bound to a head (plan 43-25, D-43-08, T-43-80).
#
# usage: scripts/ci/e2e_head_proof.sh <head> <evidence.md>
#
# An evidence document names a run of "Coverage end to end" and the commit the
# run was started on. This script says whether that run proves <head>: the run
# is the right workflow, green in all seven legs, was started on the commit the
# document names, and no code differs between that commit and <head>.
#
# Which pair of the document counts:
#   - Sections are split by lines that start with "## ".
#   - A section with a line "Lauf-ID-Fix: <id>" or "Kopf-SHA-Fix: <40 hex>"
#     must hold exactly one of each. The pair of the LAST such section counts.
#   - Without any such line the pair "Lauf-ID: <id>" and "Kopf-SHA: <40 hex>"
#     of the head of the document counts, the part before the first section,
#     exactly one of each.
#   - Anything else is an incomplete pair. A run id and a commit that stand in
#     two different sections are never put together.
#
# Prints "chosen pair: <run id>" as soon as the pair is chosen, also when a
# later check fails, and nothing but ids, counts and states.
#
# Exit codes:
#   0   the run proves the head
#   2   "gh is not ready": not logged in, or gh could not read the run
#   3   "the evidence has an incomplete pair"
#   4   "the run has <n> successful jobs, 7 are required"
#   5   any other finding, each with its own message: another workflow, a run
#       on another commit, a run that did not succeed, code that differs
#   64  wrong usage
#
# Uses gh and git only, reads only, starts nothing.
set -euo pipefail

REQUIRED_JOBS=7
WORKFLOW_NAME='Coverage end to end'
# Everything that ships or tests: a difference below one of these paths
# between the commit of the run and the head means the run saw other code.
CODE_PATHS=(backend/src backend/docker backend/appinfo php/appinfo php/lib php/js php/templates php/l10n scripts .github/workflows)

if [ "$#" -ne 2 ] || [ -z "$1" ] || [ ! -f "$2" ]; then
	echo "usage: $0 <head> <evidence.md>" >&2
	exit 64
fi
head=$1
evidence=$2

# One line per pair candidate: "<kind>\t<section number>\t<run ids>\t<commits>"
# where kind is fix or head, and the two counts say how many lines of each
# sort the section holds; the last run id and the last commit ride along.
pairs=$(tr -d '\r' <"${evidence}" | awk '
	function flush() {
		if (fix_ids + fix_shas > 0) {
			printf "fix\t%d\t%d\t%d\t%s\t%s\n", section, fix_ids, fix_shas, fix_id, fix_sha
		}
		if (section == 0) {
			printf "head\t0\t%d\t%d\t%s\t%s\n", head_ids, head_shas, head_id, head_sha
		}
		fix_ids = 0; fix_shas = 0; fix_id = "-"; fix_sha = "-"
	}
	BEGIN { section = 0; fix_id = "-"; fix_sha = "-"; head_id = "-"; head_sha = "-" }
	/^## / { flush(); section++; next }
	/^Lauf-ID-Fix: [0-9]+$/ { fix_ids++; fix_id = $2; next }
	/^Kopf-SHA-Fix: [0-9a-f]+$/ && length($2) == 40 { fix_shas++; fix_sha = $2; next }
	# A fix line that is no run id or no 40 hex commit tears its section.
	/^Lauf-ID-Fix:/ || /^Kopf-SHA-Fix:/ { fix_ids += 2; next }
	section == 0 && /^Lauf-ID: [0-9]+$/ { head_ids++; head_id = $2; next }
	section == 0 && /^Kopf-SHA: [0-9a-f]+$/ && length($2) == 40 { head_shas++; head_sha = $2; next }
	END { flush() }')

incomplete() {
	echo "the evidence has an incomplete pair" >&2
	exit 3
}

run_id=""
run_sha=""
fix_sections=$(printf '%s\n' "${pairs}" | awk -F'\t' '$1 == "fix"' | wc -l)
if [ "${fix_sections}" -gt 0 ]; then
	# Every section with a fix line has to be whole, not only the last one: a
	# torn pair anywhere means the document was not written by the rule.
	while IFS=$'\t' read -r kind _ ids shas id sha; do
		[ "${kind}" = "fix" ] || continue
		if [ "${ids}" != "1" ] || [ "${shas}" != "1" ]; then
			incomplete
		fi
		run_id=${id}
		run_sha=${sha}
	done <<<"${pairs}"
else
	IFS=$'\t' read -r _ _ ids shas id sha <<<"$(printf '%s\n' "${pairs}" | awk -F'\t' '$1 == "head"')"
	if [ "${ids:-0}" != "1" ] || [ "${shas:-0}" != "1" ]; then
		incomplete
	fi
	run_id=${id}
	run_sha=${sha}
fi
echo "chosen pair: ${run_id}"

if ! gh auth status >/dev/null 2>&1 </dev/null; then
	echo "gh is not ready" >&2
	exit 2
fi
if ! view=$(gh run view "${run_id}" --json conclusion,workflowName,headSha,jobs \
	--jq '[.conclusion // "", .workflowName // "", .headSha // "", ([.jobs[] | select(.conclusion == "success")] | length | tostring)] | join("|")' \
	2>/dev/null </dev/null); then
	echo "gh is not ready" >&2
	exit 2
fi
# A bar and not a tab between the fields: a tab is white space for read, and a
# run without a conclusion would shift every field to the left.
IFS='|' read -r conclusion workflow sha_of_run green <<<"$(printf '%s' "${view}" | tr -d '\r')"

if [ "${workflow}" != "${WORKFLOW_NAME}" ]; then
	echo "run ${run_id} is not a run of '${WORKFLOW_NAME}'" >&2
	exit 5
fi
if [ "${sha_of_run}" != "${run_sha}" ]; then
	echo "run ${run_id} ran on ${sha_of_run:-none}, the evidence names ${run_sha}" >&2
	exit 5
fi
if [ "${green:-0}" != "${REQUIRED_JOBS}" ]; then
	echo "the run has ${green:-0} successful jobs, ${REQUIRED_JOBS} are required" >&2
	exit 4
fi
if [ "${conclusion}" != "success" ]; then
	echo "run ${run_id} ended ${conclusion:-without a conclusion}, not success" >&2
	exit 5
fi

# git diff --quiet: 0 no difference, 1 a difference, anything else an error
# (an unknown commit, a shallow clone).
differs=0
git diff --quiet "${run_sha}" "${head}" -- "${CODE_PATHS[@]}" >/dev/null 2>&1 || differs=$?
if [ "${differs}" = "1" ]; then
	echo "the code of ${head} differs from ${run_sha}, the commit of run ${run_id}" >&2
	exit 5
fi
if [ "${differs}" != "0" ]; then
	echo "git cannot compare ${run_sha} with ${head}" >&2
	exit 5
fi

echo "run ${run_id} success, ${green} jobs, on ${run_sha}, no code difference to ${head}"
