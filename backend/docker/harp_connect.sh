#!/bin/sh
# Open the HaRP tunnel, or step aside when there is no HaRP.
#
# Under HaRP the application binds a unix socket instead of a TCP port, so
# without frpc the container is running and completely unreachable at the same
# time. That failure looks like a healthy container in its own log, which is why
# this script exists from the very first image and not from the first deployment
# that happens to use HaRP.
set -eu

EXAPP_SOCK="${HP_EXAPP_SOCK:-/tmp/exapp.sock}"
# Not / any more: the container runs as an unprivileged user and only root can
# create a file in the root directory. /app/run is created for this in the image,
# owned by that user and mode 700, which matters because this file carries the
# HaRP shared key.
FRPC_CONFIG="${FINDLING_RUN_DIR:-/app/run}/frpc.toml"
CERT_DIR="${HP_FRP_CERT_DIR:-/certs/frp}"

# Exit codes. 0 means "no HaRP here, this is fine", 78 is EX_CONFIG from
# sysexits.h and means "HaRP is meant to be used but the configuration is
# incomplete". docker/init.sh stops the container on the second one, which is the
# honest outcome: a half configured tunnel is an unreachable app.
EXIT_CONFIG=78

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
if [ -r "${CERT_DIR}/client.crt" ] && [ -r "${CERT_DIR}/client.key" ] && [ -r "${CERT_DIR}/ca.crt" ]; then
	echo "harp_connect: client certificates in ${CERT_DIR}, configuring the tunnel with mutual TLS"
	TLS_BLOCK="transport.tls.enable = true
transport.tls.certFile = \"${CERT_DIR}/client.crt\"
transport.tls.keyFile = \"${CERT_DIR}/client.key\"
transport.tls.trustedCaFile = \"${CERT_DIR}/ca.crt\"
transport.tls.serverName = \"harp.nc\""
elif [ "${FINDLING_HARP_PLAINTEXT:-0}" = "1" ]; then
	echo "harp_connect: WARNING, FINDLING_HARP_PLAINTEXT=1, the tunnel carries file content and the shared key UNENCRYPTED" >&2
	echo "harp_connect: unset that variable unless this instance keeps the tunnel inside a host you control end to end" >&2
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
	TLS_BLOCK="transport.tls.enable = true"
fi

# The shared key ends up in the config file because frpc has no other way of
# receiving it. It never appears in a log line, and the file is readable by its
# owner only.
umask 077
mkdir -p "$(dirname "${FRPC_CONFIG}")"

cat > "${FRPC_CONFIG}" <<EOF
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

chmod 600 "${FRPC_CONFIG}"

echo "harp_connect: starting frpc against ${HP_FRP_ADDRESS}:${HP_FRP_PORT} for socket ${EXAPP_SOCK}"
exec /usr/local/bin/frpc -c "${FRPC_CONFIG}"
