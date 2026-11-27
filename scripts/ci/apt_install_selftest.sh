#!/usr/bin/env bash
# Self test of scripts/ci/apt_install.sh (plan 46-04): the time limit, the
# retries and the refusals have to be seen working before a CI job relies on
# them. No network, no sudo: APT_GET points at a stand-in written to a scratch
# directory, which hangs, fails or succeeds as each case asks.
#
# usage: scripts/ci/apt_install_selftest.sh
#
# Needs GNU coreutils timeout. Exit 0 when every case holds, 1 otherwise.
set -euo pipefail

here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
script="${here}/apt_install.sh"

scratch=$(mktemp -d)
trap 'rm -rf "${scratch}"' EXIT

# The stand-in for apt-get. FAKE_MODE says what it does, every call is
# written to the calls file, and "hang" replaces itself with sleep so that
# timeout ends the very process that hangs.
fake="${scratch}/fake-apt-get"
cat > "${fake}" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> "${FAKE_CALLS}"
case "${FAKE_MODE}" in
	ok) exit 0 ;;
	hang) exec sleep 30 ;;
	flaky)
		count=$(( $(cat "${FAKE_COUNT}" 2>/dev/null || echo 0) + 1 ))
		echo "${count}" > "${FAKE_COUNT}"
		if [ "${count}" -le 2 ]; then
			exit 100
		fi
		exit 0
		;;
esac
exit 99
EOF
chmod +x "${fake}"

failures=0
check() {
	# $1 name, $2 expected exit, $3 actual exit, $4 condition text, $5 condition result (0 holds)
	if [ "$2" = "$3" ] && [ "$5" = "0" ]; then
		echo "ok   $1"
	else
		echo "FAIL $1: exit $3 (expected $2), $4"
		failures=$(( failures + 1 ))
	fi
}

run_case() {
	# $1 mode, then the packages; sets out, status, calls.
	local mode="$1"
	shift
	: > "${scratch}/calls"
	rm -f "${scratch}/count"
	status=0
	out=$(FAKE_MODE="${mode}" FAKE_CALLS="${scratch}/calls" FAKE_COUNT="${scratch}/count" \
		APT_GET="${fake}" APT_INSTALL_TIMEOUT=2 APT_INSTALL_PAUSE=0 \
		bash "${script}" "$@" 2>&1) || status=$?
	calls=$(wc -l < "${scratch}/calls" | tr -d ' ')
}

# 1. A mirror that never answers: three attempts, each ended by the limit.
start=$(date +%s)
run_case hang wngerman
took=$(( $(date +%s) - start ))
attempts=$(grep -c '^apt_install: attempt .* ended with exit 124' <<< "${out}" || true)
cond=1
if [ "${attempts}" = "3" ] && grep -q '::error::apt_install: 3 attempt' <<< "${out}" && [ "${took}" -lt 20 ]; then
	cond=0
fi
check "hang: three attempts of the limit, then red" 1 "${status}" "attempts ${attempts}, ${took}s" "${cond}"

# 2. A fetch that breaks twice and then works: green after the third attempt.
run_case flaky tesseract-ocr tesseract-ocr-deu
attempts=$(grep -c '^apt_install: attempt' <<< "${out}" || true)
cond=1
if [ "${attempts}" = "3" ] && grep -q 'attempt 3 of 3 ended with exit 0' <<< "${out}" \
	&& grep -q 'install -y -qq tesseract-ocr tesseract-ocr-deu' "${scratch}/calls"; then
	cond=0
fi
check "flaky: green after the third attempt" 0 "${status}" "attempts ${attempts}" "${cond}"

# 3. One attempt that works: update first, then install, with the apt options.
run_case ok wngerman
cond=1
if [ "${calls}" = "2" ] && head -n 1 "${scratch}/calls" | grep -q 'Acquire::Retries=3.*-qq update$' \
	&& tail -n 1 "${scratch}/calls" | grep -q 'install -y -qq wngerman$'; then
	cond=0
fi
check "ok: one update, one install" 0 "${status}" "calls ${calls}" "${cond}"

# 4. A package name that is shell code: refused before any call.
run_case ok 'wngerman;touch /tmp/x'
cond=1
if [ "${calls}" = "0" ]; then cond=0; fi
check "refuse: a name outside [a-z0-9.+-]" 2 "${status}" "calls ${calls}" "${cond}"

# 5. No package at all: refused before any call.
run_case ok
cond=1
if [ "${calls}" = "0" ]; then cond=0; fi
check "refuse: no package" 2 "${status}" "calls ${calls}" "${cond}"

# 6. A limit out of range: refused before any call.
: > "${scratch}/calls"
status=0
out=$(FAKE_MODE=ok FAKE_CALLS="${scratch}/calls" APT_GET="${fake}" APT_INSTALL_TIMEOUT=900 \
	bash "${script}" wngerman 2>&1) || status=$?
calls=$(wc -l < "${scratch}/calls" | tr -d ' ')
cond=1
if [ "${calls}" = "0" ]; then cond=0; fi
check "refuse: APT_INSTALL_TIMEOUT above 300" 2 "${status}" "calls ${calls}" "${cond}"

if [ "${failures}" -ne 0 ]; then
	echo "apt_install self test: ${failures} case(s) failed"
	exit 1
fi
echo "apt_install self test: all 6 cases hold"
