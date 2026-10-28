#!/bin/bash
# Open the HaRP tunnel, or step aside when there is no HaRP.
#
# Under HaRP the application binds a unix socket instead of a TCP port, so
# without frpc the container is running and completely unreachable at the same
# time. That failure looks like a healthy container in its own log, which is why
# this script exists from the very first image and not from the first deployment
# that happens to use HaRP.
#
# Under HaRP this script no longer replaces itself with frpc. It stays in front
# of it as a small watcher (ZERT-01, owner decision D-37-09):
#
#   - every frpc line is passed through unchanged;
#   - an x509 failure, or a run of failed logins that ends in no success (frps
#     may refuse the old client certificate before frpc ever sees the new
#     server one, run 40704387898), with unchanged certificate files is
#     reported with its remedy, on a slowing schedule, and never answered with
#     a restart: frpc
#     reads the files on every dial and retries on its own, a restart would read
#     the same files and fail the same way;
#   - when ca.crt, client.crt and client.key under /certs/frp change and stay
#     the same over two checks, frpc is restarted once in mutual TLS mode, with
#     a minimum gap and a cap per hour, so flapping files cannot cause a storm;
#   - the watcher never switches down: mutual TLS is never replaced by TLS
#     without a client certificate or by plaintext;
#   - it never exits 0 while HaRP is the deployment, because docker/init.sh
#     reads 0 as "no HaRP here".
#
# bash rather than sh: `read -t` on a file descriptor is what lets one loop both
# pass lines through and look at the files on a timer.
#
# `set -uo pipefail` instead of `set -eu`: `read -t` returns a status above 128
# on every timeout, and under -e that would end the watcher on its first quiet
# moment. Every step that can fail is checked explicitly instead.
set -uo pipefail

EXAPP_SOCK="${HP_EXAPP_SOCK:-/tmp/exapp.sock}"
# Not / any more: the container runs as an unprivileged user and only root can
# create a file in the root directory. /app/run is created for this in the image,
# owned by that user and mode 700, which matters because this file carries the
# HaRP shared key.
RUN_DIR="${FINDLING_RUN_DIR:-/app/run}"
FRPC_CONFIG="${RUN_DIR}/frpc.toml"
FIFO="${RUN_DIR}/frpc.fifo"
CERT_DIR="${HP_FRP_CERT_DIR:-/certs/frp}"

# Exit codes. 0 means "no HaRP here, this is fine", 78 is EX_CONFIG from
# sysexits.h and means "HaRP is meant to be used but the configuration is
# incomplete". docker/init.sh stops the container on the second one, which is the
# honest outcome: a half configured tunnel is an unreachable app.
EXIT_CONFIG=78
# 73 is EX_CANTCREAT: the configuration or the pipe to frpc cannot be written.
# Not 0, because docker/init.sh reads that as "no HaRP", and not 78, because the
# configuration is complete; the run directory is what is broken.
EXIT_CANTCREAT=73

if [ -z "${HP_SHARED_KEY:-}" ]; then
	# manual-install and plain "docker run" both land here. Exit code 0 tells
	# docker/init.sh that this was expected, so it keeps watching the application
	# alone instead of stopping the container over a missing tunnel.
	echo "harp_connect: HP_SHARED_KEY is not set, no HaRP tunnel is opened, the app listens on APP_PORT"
	exit 0
fi

# From here on HaRP is the deployment, so every value the configuration needs has
# to be present. Without these checks `set -u` aborts the script on the first
# unbound variable inside the heredoc: no useful message, a non zero exit, and a
# restart loop over something no restart can fix.
missing=""

require() {
	if [ -z "$2" ]; then
		missing="${missing} $1"
	fi
}

require HP_FRP_ADDRESS "${HP_FRP_ADDRESS:-}"
require HP_FRP_PORT "${HP_FRP_PORT:-}"
require APP_PORT "${APP_PORT:-}"
require APP_ID "${APP_ID:-}"

if [ -n "${missing}" ]; then
	echo "harp_connect: HP_SHARED_KEY is set, but these variables are empty or unset:${missing}" >&2
	echo "harp_connect: refusing to write a half configured tunnel, the app would be unreachable" >&2
	exit "${EXIT_CONFIG}"
fi

# Both ports are written into the configuration without quotes, so a value that is
# not a number produces invalid TOML and an frpc error that reads like a bug in
# this file.
check_port() {
	case "$2" in
	'' | *[!0-9]*)
		echo "harp_connect: $1 is '$2', which is not a port number" >&2
		exit "${EXIT_CONFIG}"
		;;
	esac
}

check_port HP_FRP_PORT "${HP_FRP_PORT}"
check_port APP_PORT "${APP_PORT}"

# The knobs of the watcher. They are deliberately not documented in docs/: they
# exist so that the tests can run the watcher against a stub frpc on a short
# clock. They open no new way in, because whoever can set the environment of the
# container controls the container anyway.
#
#   FINDLING_FRPC_BIN                      the frpc binary
#   FINDLING_HARP_CERT_POLL_SECONDS        how often /certs/frp is looked at, >= 1
#   FINDLING_HARP_RESTART_MIN_GAP_SECONDS  minimum gap between two frpc starts
#   FINDLING_HARP_RESTART_CAP              restarts per window, 0 means never
#   FINDLING_HARP_CAP_WINDOW_SECONDS       length of that window, >= 1
#   FINDLING_HARP_REMEDY_SCHEDULE          ascending whole seconds after the first
#                                          x509 since the last success at which
#                                          the remedy line is printed
#   FINDLING_HARP_REMEDY_REPEAT_SECONDS    interval after the last of those, >= 1
#   FINDLING_HARP_SUSPECT_AFTER_ERRORS     failed logins in a row without a
#                                          success that count like an x509, >= 1
FRPC_BIN="${FINDLING_FRPC_BIN:-/usr/local/bin/frpc}"
POLL_SECONDS="${FINDLING_HARP_CERT_POLL_SECONDS:-10}"
MIN_GAP="${FINDLING_HARP_RESTART_MIN_GAP_SECONDS:-60}"
CAP="${FINDLING_HARP_RESTART_CAP:-6}"
CAP_WINDOW="${FINDLING_HARP_CAP_WINDOW_SECONDS:-3600}"
REMEDY_SCHEDULE="${FINDLING_HARP_REMEDY_SCHEDULE:-0,300,900,3600}"
REMEDY_REPEAT="${FINDLING_HARP_REMEDY_REPEAT_SECONDS:-3600}"
# Six failed logins are about two minutes at the 20 s backoff of frpc.
SUSPECT_AFTER="${FINDLING_HARP_SUSPECT_AFTER_ERRORS:-6}"

# Same shape as check_port: a value that is not a whole number would break the
# arithmetic below in a way that reads like a bug in this file. Nine digits keep
# every value far inside the range of bash arithmetic.
check_count() {
	case "$2" in
	'' | *[!0-9]*)
		echo "harp_connect: $1 is '$2', which is not a whole number" >&2
		exit "${EXIT_CONFIG}"
		;;
	esac
	if ((${#2} > 9)); then
		echo "harp_connect: $1 is '$2', which is not a whole number of a sensible size" >&2
		exit "${EXIT_CONFIG}"
	fi
	if ((10#$2 < $3)); then
		echo "harp_connect: $1 is '$2', which is below the minimum of $3" >&2
		exit "${EXIT_CONFIG}"
	fi
}

check_count FINDLING_HARP_CERT_POLL_SECONDS "${POLL_SECONDS}" 1
check_count FINDLING_HARP_RESTART_MIN_GAP_SECONDS "${MIN_GAP}" 0
check_count FINDLING_HARP_RESTART_CAP "${CAP}" 0
check_count FINDLING_HARP_CAP_WINDOW_SECONDS "${CAP_WINDOW}" 1
check_count FINDLING_HARP_REMEDY_REPEAT_SECONDS "${REMEDY_REPEAT}" 1
check_count FINDLING_HARP_SUSPECT_AFTER_ERRORS "${SUSPECT_AFTER}" 1
POLL_SECONDS=$((10#${POLL_SECONDS}))
MIN_GAP=$((10#${MIN_GAP}))
CAP=$((10#${CAP}))
CAP_WINDOW=$((10#${CAP_WINDOW}))
REMEDY_REPEAT=$((10#${REMEDY_REPEAT}))
SUSPECT_AFTER=$((10#${SUSPECT_AFTER}))

bad_schedule() {
	echo "harp_connect: FINDLING_HARP_REMEDY_SCHEDULE is '${REMEDY_SCHEDULE}', which is not a list of whole seconds in ascending order" >&2
	exit "${EXIT_CONFIG}"
}

REMEDY_OFFSETS=()
case "${REMEDY_SCHEDULE}" in
'' | ,* | *, | *,,*)
	bad_schedule
	;;
esac
IFS=',' read -r -a schedule_items <<<"${REMEDY_SCHEDULE}"
for item in "${schedule_items[@]}"; do
	case "${item}" in
	'' | *[!0-9]*)
		bad_schedule
		;;
	esac
	if ((${#item} > 9)); then
		bad_schedule
	fi
	if ((${#REMEDY_OFFSETS[@]} > 0)) && ((10#${item} <= REMEDY_OFFSETS[${#REMEDY_OFFSETS[@]} - 1])); then
		bad_schedule
	fi
	REMEDY_OFFSETS+=("$((10#${item}))")
done

# The shared key ends up in the config file because frpc has no other way of
# receiving it. It never appears in a log line, and the file is readable by its
# owner only.
umask 077

cannot_create() {
	echo "harp_connect: cannot write the frpc configuration or its pipe in ${RUN_DIR}" >&2
}

# Three transport modes, in this order of preference. The order is the point of
# the block: the tunnel carries file content and the shared key, so unencrypted is
# the last resort and never the automatic one.
#
#   1. client certificates present and readable: mutual TLS, both ends verified.
#   2. no usable client certificates: TLS without a client certificate. The
#      traffic is encrypted, the server is not verified against our own CA. This
#      is the fallback, because the old one was plaintext.
#   3. FINDLING_HARP_PLAINTEXT=1: no encryption at all. Only on an explicit
#      decision by the admin, and it says so in the log every single start.
certs_readable() {
	[ -r "${CERT_DIR}/client.crt" ] && [ -r "${CERT_DIR}/client.key" ] && [ -r "${CERT_DIR}/ca.crt" ]
}

choose_mode() {
	if certs_readable; then
		echo "harp_connect: client certificates in ${CERT_DIR}, configuring the tunnel with mutual TLS"
		TLS_MODE=mtls
		TLS_BLOCK="transport.tls.enable = true
transport.tls.certFile = \"${CERT_DIR}/client.crt\"
transport.tls.keyFile = \"${CERT_DIR}/client.key\"
transport.tls.trustedCaFile = \"${CERT_DIR}/ca.crt\"
transport.tls.serverName = \"harp.nc\""
	elif [ "${FINDLING_HARP_PLAINTEXT:-0}" = "1" ]; then
		echo "harp_connect: WARNING, FINDLING_HARP_PLAINTEXT=1, the tunnel carries file content and the shared key UNENCRYPTED" >&2
		echo "harp_connect: unset that variable unless this instance keeps the tunnel inside a host you control end to end" >&2
		TLS_MODE=plaintext
		TLS_BLOCK="transport.tls.enable = false"
	else
		if [ -d "${CERT_DIR}" ]; then
			# The likely cause with an unprivileged container: the certificates are
			# mounted readable by root only. Named, because the difference between
			# "no certificates" and "certificates I may not read" is one chmod.
			echo "harp_connect: ${CERT_DIR} exists but client.crt, client.key or ca.crt is not readable by uid $(id -u)" >&2
		else
			echo "harp_connect: no ${CERT_DIR} directory" >&2
		fi
		echo "harp_connect: configuring the tunnel with TLS but without a client certificate" >&2
		TLS_MODE=tls
		TLS_BLOCK="transport.tls.enable = true"
	fi
}

# Written to a temporary file and moved over the old one, so frpc never reads a
# half written configuration.
write_config() {
	local temporary="${FRPC_CONFIG}.tmp"
	if ! cat >"${temporary}" <<EOF
serverAddr = "${HP_FRP_ADDRESS}"
serverPort = ${HP_FRP_PORT}
loginFailExit = false

${TLS_BLOCK}

metadatas.token = "${HP_SHARED_KEY}"

[[proxies]]
remotePort = ${APP_PORT}
type = "tcp"
name = "${APP_ID}"
[proxies.plugin]
type = "unix_domain_socket"
unixPath = "${EXAPP_SOCK}"
EOF
	then
		rm -f "${temporary}"
		cannot_create
		return 1
	fi
	if ! chmod 600 "${temporary}" || ! mv -f "${temporary}" "${FRPC_CONFIG}"; then
		rm -f "${temporary}"
		cannot_create
		return 1
	fi
	return 0
}

# A digest over the three files in a fixed order. It is only ever compared and
# never printed. sha256sum lists the readable files with their names, so a
# missing file and an empty one give different digests.
fingerprint() {
	local digest
	digest=$(cd "${CERT_DIR}" 2>/dev/null && sha256sum ca.crt client.crt client.key 2>/dev/null | sha256sum)
	printf '%s' "${digest%% *}"
}

frpc_pid=""
stopping=0
running_fp=""
running_mode=""
candidate_fp=""
missing_reported=0
last_start=0
last_check=0
restarts=0
window_start=${SECONDS}
cap_reported=0
x509_open=0
x509_since=0
remedy_sent=0
failed_logins=0

# docker stop reaches this script, not frpc, so the signal is passed on. After a
# stop the script exits 0, which docker/init.sh ignores while it is stopping.
# shellcheck disable=SC2317,SC2329 # invoked through the trap below
on_stop() {
	stopping=1
	if [ -n "${frpc_pid}" ]; then
		kill -TERM "${frpc_pid}" 2>/dev/null || true
	fi
}
trap on_stop TERM INT

# frpc writes into a FIFO and this script reads it on fd 3. A pipeline
# `frpc | while read` would hide the PID of frpc, lose its exit code and keep
# signals from reaching it.
start_frpc() {
	"${FRPC_BIN}" -c "${FRPC_CONFIG}" >"${FIFO}" 2>&1 &
	frpc_pid=$!
	exec 3<"${FIFO}"
	last_start=${SECONDS}
}

# TERM first, then up to five seconds in steps of 0.2 s, then KILL. bash reaps
# its background children as they exit, so kill -0 fails once frpc is gone.
stop_frpc() {
	local tries=0
	kill -TERM "${frpc_pid}" 2>/dev/null || true
	while kill -0 "${frpc_pid}" 2>/dev/null && ((tries < 25)); do
		sleep 0.2
		tries=$((tries + 1))
	done
	if kill -0 "${frpc_pid}" 2>/dev/null; then
		kill -KILL "${frpc_pid}" 2>/dev/null || true
	fi
	wait "${frpc_pid}" 2>/dev/null || true
	exec 3<&-
}

# Seconds after the first x509 of an episode at which remedy line number $1
# (counted from 0) is due.
remedy_due() {
	local index=$1 count=${#REMEDY_OFFSETS[@]}
	if ((index < count)); then
		printf '%s' "${REMEDY_OFFSETS[index]}"
	else
		printf '%s' "$((REMEDY_OFFSETS[count - 1] + (index - count + 1) * REMEDY_REPEAT))"
	fi
}

on_x509() {
	local elapsed
	if ((x509_open == 0)); then
		x509_open=1
		x509_since=${SECONDS}
		remedy_sent=0
	fi
	elapsed=$((SECONDS - x509_since))
	if ((elapsed < $(remedy_due "${remedy_sent}"))); then
		return 0
	fi
	# Changed files are not a case for the remedy: the restart below takes them
	# over, and the next x509 after it is judged on its own.
	if [ "$(fingerprint)" != "${running_fp}" ]; then
		return 0
	fi
	echo "harp_connect: the tunnel certificate is possibly no longer accepted by HaRP (x509 or repeated failed logins), most likely HaRP was restarted without its /certs volume and issued a new CA; frpc keeps retrying and picks up new files in ${CERT_DIR} by itself; copy them in or re-register the app, see https://github.com/street1983nk/nextcloud-search/blob/main/docs/harp-tunnel.md#repair-without-re-registering" >&2
	remedy_sent=$((remedy_sent + 1))
	# One line per x509, never a burst: offsets missed while the files were
	# changing are skipped.
	while ((elapsed >= $(remedy_due "${remedy_sent}"))); do
		remedy_sent=$((remedy_sent + 1))
	done
}

restart_frpc() {
	local fp=$1
	choose_mode
	# Never down: only a configuration in mutual TLS replaces the running one.
	if [ "${TLS_MODE}" != "mtls" ]; then
		return 0
	fi
	# Written before the old frpc is stopped. If that fails, the old frpc keeps
	# running on its old configuration.
	if ! write_config; then
		return 0
	fi
	restarts=$((restarts + 1))
	echo "harp_connect: the certificate files in ${CERT_DIR} changed, restarting frpc with mutual TLS (restart ${restarts} of at most ${CAP} this hour)" >&2
	stop_frpc
	running_fp=${fp}
	running_mode=mtls
	candidate_fp=""
	if ((stopping)); then
		return 0
	fi
	start_frpc
}

check_files() {
	local fp
	fp=$(fingerprint)
	if [ "${fp}" = "${running_fp}" ]; then
		candidate_fp=""
		missing_reported=0
		return 0
	fi
	if ! certs_readable; then
		candidate_fp=""
		if [ "${running_mode}" = "mtls" ] && ((missing_reported == 0)); then
			echo "harp_connect: client.crt, client.key or ca.crt in ${CERT_DIR} is missing or not readable, frpc keeps its current configuration" >&2
			missing_reported=1
		fi
		return 0
	fi
	missing_reported=0
	# Two checks in a row with the same digest: a copy that is still running
	# never triggers a restart with half a set of files.
	if [ "${fp}" != "${candidate_fp}" ]; then
		candidate_fp=${fp}
		return 0
	fi
	if ((SECONDS - last_start < MIN_GAP)); then
		return 0
	fi
	if ((SECONDS - window_start >= CAP_WINDOW)); then
		window_start=${SECONDS}
		restarts=0
		cap_reported=0
	fi
	if ((restarts >= CAP)); then
		if ((cap_reported == 0)); then
			echo "harp_connect: restart cap reached (${CAP} restarts this hour), no further frpc restarts until the hour is over, frpc keeps retrying on its own" >&2
			cap_reported=1
		fi
		return 0
	fi
	restart_frpc "${fp}"
}

if ! mkdir -p "${RUN_DIR}" 2>/dev/null; then
	cannot_create
	exit "${EXIT_CANTCREAT}"
fi
running_fp=$(fingerprint)
choose_mode
running_mode=${TLS_MODE}
if ! write_config; then
	exit "${EXIT_CANTCREAT}"
fi
rm -f "${FIFO}"
if ! mkfifo -m 600 "${FIFO}"; then
	cannot_create
	exit "${EXIT_CANTCREAT}"
fi

echo "harp_connect: starting frpc against ${HP_FRP_ADDRESS}:${HP_FRP_PORT} for socket ${EXAPP_SOCK}"
start_frpc
last_check=${SECONDS}

# What `read -t` had of an unfinished line when its timeout ran out. bash keeps
# that part in the variable and the next read starts after it, so without this
# carry the start of a line that arrives slower than the poll interval would be
# lost, its rest would stand as a line of its own, and an x509 in it would go
# unseen (finding F-40-02 of audit 40-01). Bounded: a carry above 64 KiB is
# passed through as a line of its own.
partial=""
PARTIAL_MAX=65536

while :; do
	if IFS= read -r -t "${POLL_SECONDS}" line <&3; then
		line="${partial}${line}"
		partial=""
		printf '%s\n' "${line}"
		if [[ "${line}" == *"connect to server error:"* ]]; then
			# A refused or unreachable dial means HaRP is not up; the
			# certificate never got a say, so it does not count.
			if [[ "${line}" != *"dial tcp"* ]]; then
				failed_logins=$((failed_logins + 1))
			fi
			if [[ "${line}" == *"x509: "* ]] || ((failed_logins >= SUSPECT_AFTER)); then
				on_x509
			fi
		elif [[ "${line}" == *"login to server success"* ]]; then
			failed_logins=0
			if ((x509_open)); then
				echo "harp_connect: the tunnel is connected again"
				x509_open=0
			fi
		fi
	else
		status=$?
		if ((status <= 128)); then
			# End of file: frpc is gone. A last line without a newline still
			# belongs in the log.
			line="${partial}${line:-}"
			if [ -n "${line}" ]; then
				printf '%s\n' "${line}"
			fi
			break
		fi
		# Above 128: a timeout or a signal. Either way a moment to look at the
		# files, unless the signal was a stop. Whatever the read had of an
		# unfinished line is carried over to the next one.
		partial="${partial}${line:-}"
		if ((${#partial} > PARTIAL_MAX)); then
			printf '%s\n' "${partial}"
			partial=""
		fi
	fi
	if ((stopping)); then
		break
	fi
	# Also after a line, not only on a timeout: frpc can print often enough that
	# the read never times out.
	if ((SECONDS - last_check >= POLL_SECONDS)); then
		last_check=${SECONDS}
		check_files
		# A stop that arrived during a restart leaves no frpc to read from.
		if ((stopping)); then
			break
		fi
	fi
done

while :; do
	wait "${frpc_pid}"
	rc=$?
	# A signal interrupting the wait also returns above 128; keep waiting while
	# frpc is still there.
	if ((rc > 128)) && kill -0 "${frpc_pid}" 2>/dev/null; then
		continue
	fi
	break
done

if ((stopping)); then
	exit 0
fi
# frpc ended on its own. Never exit 0 here: docker/init.sh reads 0 as "no HaRP",
# and the application would keep running unreachable behind a dead tunnel.
echo "harp_connect: frpc exited with status ${rc}" >&2
if ((rc == 0)); then
	rc=1
fi
exit "${rc}"
