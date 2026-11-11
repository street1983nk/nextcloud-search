#!/usr/bin/env bash
# Self test of scripts/ci/e2e_head_proof.sh (plan 43-25): the proof script has
# to be able to turn red, with the right exit code and message for each
# reason, before anybody trusts its green.
#
# usage: scripts/ci/e2e_head_proof_selftest.sh
#
# Runs from anywhere inside the repository, needs its history (no shallow
# clone). The evidence files are written to a scratch directory that goes at
# the end. Two kinds of case:
#
#   - Against the real gh: the evidence of plan 43-07 (43-E2E.md) names a run
#     with five legs, so the script must answer exit 4 with "the run has 5
#     successful jobs, 7 are required". Reads one run, starts nothing. Set
#     E2E_HEAD_PROOF_OFFLINE=1 to leave this one case out; it is then printed
#     as skipped and the self test says so in its last line.
#   - Against a stand-in for gh in front of PATH that answers what the case
#     says: the choice of the pair and every exit code, without the network.
#     git is always the real one.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
proof="${here}/e2e_head_proof.sh"
root=$(git -C "${here}" rev-parse --show-toplevel)
cd "${root}"

scratch=$(mktemp -d)
trap 'rm -rf "${scratch}"' EXIT

failures=0
cases=0
skipped=0

# expect <name> <exit code> <text the output must contain> <text it must not
# contain, or ''> -- <command ...>
expect() {
	local name=$1 want=$2 part=$3 absent=$4 out code=0
	shift 5
	cases=$((cases + 1))
	out=$("$@" 2>&1) || code=$?
	if [ "${code}" != "${want}" ]; then
		echo "RED  ${name}: exit ${code}, expected ${want}: ${out}"
		failures=$((failures + 1))
	elif ! printf '%s\n' "${out}" | grep -qF -- "${part}"; then
		echo "RED  ${name}: exit ${code}, but the output lacks '${part}': ${out}"
		failures=$((failures + 1))
	elif [ -n "${absent}" ] && printf '%s\n' "${out}" | grep -qF -- "${absent}"; then
		echo "RED  ${name}: the output carries '${absent}': ${out}"
		failures=$((failures + 1))
	else
		echo "ok   ${name}: exit ${code}, '${part}'"
	fi
}

# -- the real run of plan 43-07 ----------------------------------------------------

old_head=17f819181229299676afce90c37d1d05345032ad
old_evidence=.planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-E2E.md
if [ "${E2E_HEAD_PROOF_OFFLINE:-0}" = "1" ]; then
	echo "skip the five leg run of 43-E2E.md against the real gh (E2E_HEAD_PROOF_OFFLINE=1)"
	skipped=1
else
	expect "the five leg run of 43-E2E.md is no proof" 4 "the run has 5 successful jobs, 7 are required" "" -- \
		"${proof}" "${old_head}" "${old_evidence}"
fi

# -- a stand-in for gh ---------------------------------------------------------------

# It answers `gh auth status` by GH_FAKE_AUTH (0 or 1) and `gh run view <id>
# ... --jq <filter>` with the fields of GH_FAKE_<field>, in the form the proof
# script asks for (four fields, bar separated). GH_FAKE_VIEW=1 makes the view
# fail. The run id it was asked for goes to GH_FAKE_ASKED.
mkdir -p "${scratch}/bin"
cat >"${scratch}/bin/gh" <<'EOF'
#!/usr/bin/env bash
if [ "$1" = "auth" ]; then
	exit "${GH_FAKE_AUTH:-0}"
fi
if [ "$1" = "run" ] && [ "$2" = "view" ]; then
	printf '%s\n' "$3" >>"${GH_FAKE_ASKED}"
	[ "${GH_FAKE_VIEW:-0}" = "0" ] || exit 1
	printf '%s|%s|%s|%s\n' "${GH_FAKE_CONCLUSION-success}" "${GH_FAKE_WORKFLOW-Coverage end to end}" \
		"${GH_FAKE_SHA}" "${GH_FAKE_GREEN-7}"
	exit 0
fi
exit 1
EOF
chmod +x "${scratch}/bin/gh"
export GH_FAKE_ASKED="${scratch}/asked.txt"
: >"${GH_FAKE_ASKED}"

# with_fake <NAME=value ...> -- <command ...>: the command with the stand-in
# in front of PATH and the given answers.
with_fake() {
	local settings=()
	while [ "$1" != "--" ]; do
		settings+=("$1")
		shift
	done
	shift
	env PATH="${scratch}/bin:${PATH}" "${settings[@]}" "$@"
}

# Two commits of this repository: tip, the last one that changed something
# below the paths the proof compares, and its parent, which therefore differs
# from it in exactly those paths.
tip=$(git log -1 --format=%H -- backend/src backend/docker backend/appinfo php/appinfo php/lib php/js php/templates php/l10n scripts .github/workflows)
before=$(git rev-parse --verify --quiet "${tip}^" || true)
if [ -z "${tip}" ] || [ -z "${before}" ]; then
	echo "RED  the self test needs the history of the repository (two commits that differ in code)"
	exit 1
fi
other=0000000000000000000000000000000000000001

# -- the choice of the pair ----------------------------------------------------------

cat >"${scratch}/two-fixes.md" <<EOF
# Evidence

Lauf-ID: 1001
Kopf-SHA: ${before}

## Fix 1

Lauf-ID-Fix: 2002
Kopf-SHA-Fix: ${before}

## Fix 2

Lauf-ID-Fix: 3003
Kopf-SHA-Fix: ${tip}

## Closing words

Nothing here.
EOF
expect "two fix sections, the second pair is chosen and proves the tip" 0 "chosen pair: 3003" "chosen pair: 2002" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/two-fixes.md"
expect "the stand-in was asked for the run of the second pair" 0 "3003" "2002" -- tail -n 1 "${GH_FAKE_ASKED}"
expect "the chosen pair is printed also when a later check fails" 4 "chosen pair: 3003" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_GREEN=5 -- "${proof}" "${tip}" "${scratch}/two-fixes.md"

cat >"${scratch}/head-only.md" <<EOF
# Evidence

Lauf-ID: 1001
Kopf-SHA: ${tip}

## Later

Lauf-ID 4004 in a sentence is no pair.
EOF
expect "without a fix section the pair of the head counts" 0 "chosen pair: 1001" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/head-only.md"

# -- exit 3 ---------------------------------------------------------------------------

cat >"${scratch}/split.md" <<EOF
# Evidence

Lauf-ID: 1001
Kopf-SHA: ${tip}

## Fix 1

Lauf-ID-Fix: 2002

## Fix 2

Kopf-SHA-Fix: ${tip}
EOF
expect "a pair spread over two sections" 3 "the evidence has an incomplete pair" "chosen pair" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/split.md"

cat >"${scratch}/torn-earlier.md" <<EOF
# Evidence

Lauf-ID: 1001
Kopf-SHA: ${tip}

## Fix 1

Lauf-ID-Fix: 2002

## Fix 2

Lauf-ID-Fix: 3003
Kopf-SHA-Fix: ${tip}
EOF
expect "a whole last pair behind a torn earlier one" 3 "the evidence has an incomplete pair" "chosen pair" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/torn-earlier.md"

cat >"${scratch}/twice.md" <<EOF
# Evidence

## Fix 1

Lauf-ID-Fix: 2002
Lauf-ID-Fix: 3003
Kopf-SHA-Fix: ${tip}
EOF
expect "two run ids in one section" 3 "the evidence has an incomplete pair" "chosen pair" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/twice.md"

cat >"${scratch}/short-sha.md" <<EOF
# Evidence

## Fix 1

Lauf-ID-Fix: 2002
Kopf-SHA-Fix: ${tip:0:12}
EOF
expect "a short commit in a fix pair" 3 "the evidence has an incomplete pair" "chosen pair" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/short-sha.md"

cat >"${scratch}/no-head-sha.md" <<EOF
# Evidence

Lauf-ID: 1001

## Later

Kopf-SHA: ${tip}
EOF
expect "the head pair with its commit below a heading" 3 "the evidence has an incomplete pair" "chosen pair" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/no-head-sha.md"

printf '# Evidence\n\nNo pair at all.\n' >"${scratch}/empty.md"
expect "no pair at all" 3 "the evidence has an incomplete pair" "chosen pair" -- \
	with_fake "GH_FAKE_SHA=${tip}" -- "${proof}" "${tip}" "${scratch}/empty.md"

# -- exit 2 ---------------------------------------------------------------------------

expect "gh is not logged in" 2 "gh is not ready" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_AUTH=1 -- "${proof}" "${tip}" "${scratch}/head-only.md"
expect "gh cannot read the run" 2 "gh is not ready" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_VIEW=1 -- "${proof}" "${tip}" "${scratch}/head-only.md"

# -- exit 4 ---------------------------------------------------------------------------

expect "six green jobs" 4 "the run has 6 successful jobs, 7 are required" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_GREEN=6 -- "${proof}" "${tip}" "${scratch}/head-only.md"
expect "eight green jobs" 4 "the run has 8 successful jobs, 7 are required" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_GREEN=8 -- "${proof}" "${tip}" "${scratch}/head-only.md"
expect "no green job" 4 "the run has 0 successful jobs, 7 are required" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_GREEN=0 GH_FAKE_CONCLUSION=failure -- "${proof}" "${tip}" "${scratch}/head-only.md"

# -- exit 5 ---------------------------------------------------------------------------

expect "seven green jobs and a run that failed all the same" 5 "ended failure, not success" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_CONCLUSION=failure -- "${proof}" "${tip}" "${scratch}/head-only.md"
expect "a run without a conclusion" 5 "ended without a conclusion, not success" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" GH_FAKE_CONCLUSION= -- "${proof}" "${tip}" "${scratch}/head-only.md"
expect "another workflow" 5 "is not a run of 'Coverage end to end'" "" -- \
	with_fake "GH_FAKE_SHA=${tip}" "GH_FAKE_WORKFLOW=Python gates" -- "${proof}" "${tip}" "${scratch}/head-only.md"
expect "the run ran on another commit than the evidence names" 5 "the evidence names ${tip}" "" -- \
	with_fake "GH_FAKE_SHA=${before}" -- "${proof}" "${tip}" "${scratch}/head-only.md"

cat >"${scratch}/before.md" <<EOF
# Evidence

Lauf-ID: 1001
Kopf-SHA: ${before}
EOF
expect "code differs between the commit of the run and the head" 5 "the code of ${tip} differs from ${before}" "" -- \
	with_fake "GH_FAKE_SHA=${before}" -- "${proof}" "${tip}" "${scratch}/before.md"
expect "the same evidence proves its own commit" 0 "no code difference to ${before}" "" -- \
	with_fake "GH_FAKE_SHA=${before}" -- "${proof}" "${before}" "${scratch}/before.md"

cat >"${scratch}/unknown.md" <<EOF
# Evidence

Lauf-ID: 1001
Kopf-SHA: ${other}
EOF
expect "a commit git does not know" 5 "git cannot compare" "" -- \
	with_fake "GH_FAKE_SHA=${other}" -- "${proof}" "${tip}" "${scratch}/unknown.md"

# -- usage ----------------------------------------------------------------------------

expect "no evidence file" 64 "usage:" "" -- "${proof}" "${tip}" "${scratch}/missing.md"

echo "cases=${cases} failures=${failures} skipped=${skipped}"
[ "${failures}" = "0" ]
