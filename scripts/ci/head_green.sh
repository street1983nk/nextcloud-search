#!/usr/bin/env bash
# The CI gate on one commit (plan 40-01): wait for every workflow run of the
# commit and fail on anything but success.
#
# usage: scripts/ci/head_green.sh <sha> [<workflow name>...]
#
#   - lists the runs of the commit with gh run list --commit (up to 50)
#   - exit 1 when that list is empty, when a named workflow has no run on the
#     commit, or when any run ends with a conclusion other than success
#   - waits for each run with gh run watch --exit-status
#   - prints "<id> <workflow name> success" for every run
#
# The names are the ones a path filter can skip. A workflow that is not named
# still counts when it ran: every run of the commit has to be green, never
# only the named ones.
set -euo pipefail

if [ "$#" -lt 1 ] || [ -z "$1" ]; then
	echo "usage: $0 <sha> [<workflow name>...]" >&2
	exit 2
fi
sha=$1
shift

runs=$(gh run list --commit "${sha}" --limit 50 --json databaseId,workflowName \
	--jq '.[] | "\(.databaseId)\t\(.workflowName)"' </dev/null | tr -d '\r')
if [ -z "${runs}" ]; then
	echo "head_green: no workflow run on ${sha}" >&2
	exit 1
fi

for name in "$@"; do
	if ! printf '%s\n' "${runs}" | cut -f2 | grep -qxF -- "${name}"; then
		echo "head_green: no run of '${name}' on ${sha}" >&2
		exit 1
	fi
done

failed=0
while IFS=$'\t' read -r id name; do
	# stdin of both gh calls is /dev/null, so neither of them eats the list.
	gh run watch "${id}" --exit-status --interval 30 >/dev/null 2>&1 </dev/null || true
	conclusion=$(gh run view "${id}" --json conclusion --jq .conclusion </dev/null | tr -d '\r')
	if [ "${conclusion}" = "success" ]; then
		printf '%s %s success\n' "${id}" "${name}"
	else
		printf '%s %s %s\n' "${id}" "${name}" "${conclusion:-none}" >&2
		failed=1
	fi
done <<<"${runs}"

exit "${failed}"
