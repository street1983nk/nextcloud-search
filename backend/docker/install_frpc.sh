#!/bin/sh
# Install the FRP client that HaRP needs in order to reach this container.
#
# frpc is the only part of this image that does not come from a package manager,
# so it is the only part where the supply chain has to be spelled out by hand:
# a fixed version, a pinned commit as the source, and a checksum per
# architecture that is compared before the binary is installed. A moving ref
# such as a branch or "the newest release" would let a change upstream reach
# every image we publish afterwards without anybody noticing.
#
# The tarballs vendored in nextcloud/HaRP are byte identical to the upstream
# release fatedier/frp v0.61.1; both checksums below were confirmed against
# both sources on 2026-08-15.
set -eu

FRP_VERSION="0.61.1"

# Pinned commit in nextcloud/HaRP, not a branch.
HARP_COMMIT="d9d364389e430e201af7f49f7af5d4448baabae6"

ARCH="$(uname -m)"
case "$ARCH" in
	aarch64 | arm64)
		FRP_ARCH="arm64"
		FRP_SHA256="af6366f2b43920ebfe6235dba6060770399ed1fb18601e5818552bd46a7621f8"
		;;
	x86_64 | amd64)
		FRP_ARCH="amd64"
		FRP_SHA256="bff260b68ca7b1461182a46c4f34e9709ba32764eed30a15dd94ac97f50a2c40"
		;;
	*)
		echo "install_frpc: unsupported architecture ${ARCH}" >&2
		exit 1
		;;
esac

FRP_DIR="frp_${FRP_VERSION}_linux_${FRP_ARCH}"
FRP_URL="https://raw.githubusercontent.com/nextcloud/HaRP/${HARP_COMMIT}/exapps_dev/${FRP_DIR}.tar.gz"

echo "install_frpc: architecture ${ARCH}, downloading ${FRP_URL}"
curl -fsSL "$FRP_URL" -o /tmp/frp.tar.gz

# The build stops here on any mismatch, which is the whole point of the file.
echo "${FRP_SHA256}  /tmp/frp.tar.gz" | sha256sum -c -

# Only frpc is extracted. frps is the server half and has no business being in
# an application image.
tar -C /tmp -xzf /tmp/frp.tar.gz "${FRP_DIR}/frpc"
install -m 0755 "/tmp/${FRP_DIR}/frpc" /usr/local/bin/frpc
rm -rf /tmp/frp.tar.gz "/tmp/${FRP_DIR}"

/usr/local/bin/frpc --version
