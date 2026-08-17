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
FRPC_CONFIG="/frpc.toml"

if [ -z "${HP_SHARED_KEY:-}" ]; then
	# manual-install and plain "docker run" both land here. Exit code 0 tells
	# docker/init.sh that this was expected, so it keeps watching the application
	# alone instead of stopping the container over a missing tunnel.
	echo "harp_connect: HP_SHARED_KEY is not set, no HaRP tunnel is opened, the app listens on APP_PORT"
	exit 0
fi

# The shared key ends up in the config file because frpc has no other way of
# receiving it. It never appears in a log line, and the file is readable by its
# owner only.
umask 077

if [ -d /certs/frp ]; then
	echo "harp_connect: /certs/frp found, configuring the tunnel with TLS"
	cat > "$FRPC_CONFIG" <<EOF
serverAddr = "${HP_FRP_ADDRESS}"
serverPort = ${HP_FRP_PORT}
loginFailExit = false

transport.tls.enable = true
transport.tls.certFile = "/certs/frp/client.crt"
transport.tls.keyFile = "/certs/frp/client.key"
transport.tls.trustedCaFile = "/certs/frp/ca.crt"
transport.tls.serverName = "harp.nc"

metadatas.token = "${HP_SHARED_KEY}"

[[proxies]]
remotePort = ${APP_PORT}
type = "tcp"
name = "${APP_ID}"
[proxies.plugin]
type = "unix_domain_socket"
unixPath = "${EXAPP_SOCK}"
EOF
else
	echo "harp_connect: no /certs/frp directory, configuring the tunnel without TLS"
	cat > "$FRPC_CONFIG" <<EOF
serverAddr = "${HP_FRP_ADDRESS}"
serverPort = ${HP_FRP_PORT}
loginFailExit = false

transport.tls.enable = false

metadatas.token = "${HP_SHARED_KEY}"

[[proxies]]
remotePort = ${APP_PORT}
type = "tcp"
name = "${APP_ID}"
[proxies.plugin]
type = "unix_domain_socket"
unixPath = "${EXAPP_SOCK}"
EOF
fi

chmod 600 "$FRPC_CONFIG"

echo "harp_connect: starting frpc against ${HP_FRP_ADDRESS}:${HP_FRP_PORT} for socket ${EXAPP_SOCK}"
exec /usr/local/bin/frpc -c "$FRPC_CONFIG"
