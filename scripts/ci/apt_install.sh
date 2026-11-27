#!/usr/bin/env bash
# Install Debian packages on a CI runner, with a time limit and retries
# (plan 46-04, I-45-10-07 of 45-AUDIT.md).
#
# usage: scripts/ci/apt_install.sh <package>...
#
# A plain "apt-get update && apt-get install" has no limit of its own: on
# 2026-11-26 one download hung for 24 minutes without a line of output and
# took the whole job limit of team-folder-acl with it (run 45741403207). Here
# every attempt, update and install together, gets one time budget, apt itself
# retries a broken fetch and gives up on a silent mirror, and a failed attempt
# is tried again after a pause. The worst case with the defaults is
# 3 x 120 s + 2 x 10 s, a little over six minutes, which is well under the
# smallest job limit of the jobs that call this script (a gate in
# backend/tests/test_ci_apt_timeouts.py holds that sum against them).
#
# Settings, each from the environment and each checked:
#   APT_INSTALL_TIMEOUT   seconds per attempt, update and install together
#                         (default 120, 1 to 300)
#   APT_INSTALL_ATTEMPTS  attempts (default 3, 1 to 3)
#   APT_INSTALL_PAUSE     seconds between two attempts (default 10, 0 to 60)
#   APT_GET               the command run as apt-get (default "sudo apt-get");
#                         the self test puts a stand-in here
#
# The log carries the attempt, its exit code and its duration, nothing else.
set -euo pipefail

timeout_s="${APT_INSTALL_TIMEOUT:-120}"
attempts="${APT_INSTALL_ATTEMPTS:-3}"
pause_s="${APT_INSTALL_PAUSE:-10}"
read -r -a apt_get <<< "${APT_GET:-sudo apt-get}"

in_range() {
	# $1 value, $2 lowest, $3 highest; whole numbers only.
	[[ "$1" =~ ^[0-9]+$ ]] && [ "$1" -ge "$2" ] && [ "$1" -le "$3" ]
}

if ! in_range "${timeout_s}" 1 300 || ! in_range "${attempts}" 1 3 || ! in_range "${pause_s}" 0 60; then
	echo "::error::apt_install: APT_INSTALL_TIMEOUT 1..300, APT_INSTALL_ATTEMPTS 1..3 and APT_INSTALL_PAUSE 0..60 are the allowed values"
	exit 2
fi
if [ "${#apt_get[@]}" -eq 0 ]; then
	echo "::error::apt_install: APT_GET names no command"
	exit 2
fi
if [ "$#" -eq 0 ]; then
	echo "::error::apt_install: no package named"
	exit 2
fi
for package in "$@"; do
	if ! [[ "${package}" =~ ^[a-z0-9][a-z0-9.+-]*$ ]]; then
		echo "::error::apt_install: a package name may hold a-z, 0-9, '.', '+' and '-' only"
		exit 2
	fi
done

apt_options=(-o Acquire::Retries=3 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30)

# One attempt: update, then install, both inside the same deadline. timeout
# ends with 124 when the budget runs out.
attempt_once() {
	local deadline=$(( $(date +%s) + timeout_s ))
	local left=$(( deadline - $(date +%s) ))
	timeout --kill-after=10 "${left}" "${apt_get[@]}" "${apt_options[@]}" -qq update || return $?
	left=$(( deadline - $(date +%s) ))
	if [ "${left}" -le 0 ]; then
		return 124
	fi
	timeout --kill-after=10 "${left}" "${apt_get[@]}" "${apt_options[@]}" install -y -qq "$@" || return $?
}

attempt=1
while true; do
	started=$(date +%s)
	status=0
	attempt_once "$@" || status=$?
	took=$(( $(date +%s) - started ))
	echo "apt_install: attempt ${attempt} of ${attempts} ended with exit ${status} after ${took}s"
	if [ "${status}" -eq 0 ]; then
		exit 0
	fi
	if [ "${attempt}" -ge "${attempts}" ]; then
		echo "::error::apt_install: ${attempts} attempt(s) of ${timeout_s}s each did not install the packages, the last one ended with exit ${status}"
		exit 1
	fi
	attempt=$(( attempt + 1 ))
	sleep "${pause_s}"
done
