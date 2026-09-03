# syntax=docker/dockerfile:1

# Findling ExApp backend.
#
# Three stages, one base image. The build stage owns uv and the compiler-adjacent
# noise, the frpc stage owns the one download this image needs, and the runtime
# stage gets the finished virtual environment plus that one binary and nothing
# else from either of them.
#
# The runtime stage installs exactly one package, and it is data, not a tool. It
# used to apt-get supervisor, curl and ca-certificates, which is 58 MB of apt
# layer measured, most of it a second complete python3 underneath supervisor. Two
# processes are watched by docker/init.sh instead, and the two build time tools
# now live in the stage that needs them. On the 4 GB ARM box this app targets,
# that is not cosmetic. The one exception is the German word list below: it has
# no executable part, it is what makes the search work without a download at
# first start, and it is argued for at the line that installs it.
#
# The base image is pinned by digest, not by tag: the tag moves, and every image
# we publish would move with it. The digest below is the multi platform index,
# so the very same line resolves to the amd64 and the arm64 manifest.
ARG BASE_IMAGE=python:3.13-slim-trixie@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a

FROM ${BASE_IMAGE} AS build

# uv arrives as a binary out of its own image, also pinned by digest. Version
# 0.11.7 is the one that produced backend/uv.lock, so --frozen means the same
# resolution here as in the Python gates.
COPY --from=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# The dependency layer is built before the sources are copied, so a change in
# our own code does not reinstall the whole environment.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-editable --no-install-project

COPY src ./src
# --no-editable puts the package itself into site-packages. The runtime stage
# then needs the virtual environment only, never the source tree.
RUN uv sync --frozen --no-dev --no-editable

# frpc is fetched in a stage of its own. curl and the CA bundle are needed to
# download the tarball and verify its checksum, and both are build time tools:
# nothing at runtime calls out to the internet, and the smoke test in CI runs its
# curl on the runner, not in the container.
FROM ${BASE_IMAGE} AS frpc

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY docker/install_frpc.sh /tmp/install_frpc.sh
RUN chmod 0755 /tmp/install_frpc.sh \
    && /tmp/install_frpc.sh \
    && rm -f /tmp/install_frpc.sh

FROM ${BASE_IMAGE} AS runtime

LABEL org.opencontainers.image.source="https://github.com/street1983nk/nextcloud-search" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.title="Findling Backend" \
      org.opencontainers.image.description="Zero-config search backend for Nextcloud, running as an External App"

WORKDIR /app

# The German word list, installed in the runtime stage and staying there.
#
# Measured in this very base image: /usr/share/dict/ngerman has 356010 lines and
# 4725887 bytes, and the package is Architecture: all, so amd64 and arm64 read
# byte identical data and no compound is split differently on the ARM box than on
# the x86 one.
#
# The version is pinned instead of taking whatever the archive currently holds.
# The list decides how a compound falls apart, so a silent change of it is a
# silent change of every search result of every German document. When trixie
# moves the package, this build fails loudly and somebody records the new
# numbers, which is the cheap moment to notice.
#
# Why it is not distilled in a build stage and thrown away: preparing the list is
# a start up step, not a build decision. findling.index.wordlist reduces it once
# to the length window, writes $APP_PERSISTENT_STORAGE/dict/de.txt and records
# its SHA-256 in the meta table, so the tokenisation hangs on an artifact whose
# digest can be checked against the index that was built with it. A file baked in
# at build time would hang on a build nobody can inspect afterwards (T-02-71).
#
# Nothing here is fetched at run time. The word list is the reason zero-config
# survives a firewall, a proxy and an offline installation, and it would be a
# poor one if the first start had to download it. curl and wget stay in the frpc
# stage where they belong.
#
# GPL-2+ obligation: the licence text has to travel with the image, not only with
# the repository, because the image is what is distributed. slim images drop most
# of /usr/share/doc (path-exclude in /etc/dpkg/dpkg.cfg.d), so the file is copied
# to a stable place of ours. Both tests below are the fail closed half: an image
# without the data or without its licence must not be built at all. THIRD-PARTY.md
# carries the same statement for readers of the repository.
RUN apt-get update \
    && apt-get install -y --no-install-recommends wngerman=20161207-15 \
    && rm -rf /var/lib/apt/lists/* \
    && test -s /usr/share/dict/ngerman \
    && test -s /usr/share/doc/wngerman/copyright \
    && install -D -m 0444 /usr/share/doc/wngerman/copyright \
        /usr/local/share/findling/COPYING.wngerman

# The OCR engine and its language data, installed in the runtime stage and
# staying there, for the same reason the word list above does: a scanned PDF has
# to become searchable on a box behind a firewall, and a first start that
# downloads a 15 MB model is not zero-config, it is a support case.
#
# Why the engine is NOT pinned to a version while the language packs are.
# Measured in this base image on 2026-09-01: apt installs tesseract-ocr
# 5.5.0-1+b1, not 5.5.0-1. The +b1 is a binary NMU, it is produced per
# architecture, and arm64 carries it as well. A hard =5.5.0-1 would therefore
# fail on both platforms of the multi-arch build, and a hard =5.5.0-1+b1 would
# fail the day one architecture is rebuilt without the other. The anchor for the
# engine is the digest of the base image at the top of this file, which is the
# same anchor the rest of the runtime stage already relies on.
#
# The three language packages are the opposite case: they are Architecture: all,
# they come from the tesseract-lang source package and they have not moved since
# bookworm. They are pinned hard, because the traineddata decides what the OCR
# reads, and a silent change of it is a silent change of the text of every
# scanned document in the index. When trixie moves them, this build fails loudly.
#
# osd is in the list although the call form uses --psm 3, not --psm 1: the
# orientation and script model is what makes a rotated scan recoverable at all,
# and installing it now costs nothing beyond the 10 MB it already weighs.
#
# The Fraktur option of D-09, deliberately left off by default. The language code
# is frk, not deu_frak: deu_frak died with tesseract 3, and the package
# tesseract-ocr-deu-frak does not exist in trixie ("No such package"). Switching
# it on means uncommenting the line and adding frk to the allowlist in
# backend/src/findling/config.py, which is the second half of the same change:
#         tesseract-ocr-frk=1:4.1.0-2 \
#
# Apache-2.0 obligation: the licence text has to travel with the image, not only
# with the repository, because the image is what is distributed. Measured, the
# engine and libtesseract5 share one copyright file and the three language packs
# share a second one (tessdata_fast), so two copies cover all five packages.
# Both tests below are the fail closed half: an image without the language data
# or without the licence texts must not be built at all. THIRD-PARTY.md carries
# the same statement for readers of the repository.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-deu=1:4.1.0-2 \
        tesseract-ocr-eng=1:4.1.0-2 \
        tesseract-ocr-osd=1:4.1.0-2 \
    && rm -rf /var/lib/apt/lists/* \
    && tesseract --list-langs 2>&1 | grep -qx deu \
    && tesseract --list-langs 2>&1 | grep -qx eng \
    && test -s /usr/share/doc/tesseract-ocr/copyright \
    && test -s /usr/share/doc/tesseract-ocr-deu/copyright \
    && install -D -m 0444 /usr/share/doc/tesseract-ocr/copyright \
        /usr/local/share/findling/COPYING.tesseract \
    && install -D -m 0444 /usr/share/doc/tesseract-ocr-deu/copyright \
        /usr/local/share/findling/COPYING.tesseract-langdata

COPY --from=build /app/.venv /app/.venv
COPY --from=frpc /usr/local/bin/frpc /usr/local/bin/frpc
COPY docker/init.sh docker/entrypoint.sh docker/harp_connect.sh /app/docker/
RUN chmod 0755 /app/docker/init.sh /app/docker/entrypoint.sh /app/docker/harp_connect.sh

# Everything below runs as an unprivileged user. root inside a container is one
# escape away from root on the host, and this process needs exactly two writable
# places: a small runtime directory and, from phase 2 on, its index.
#
# The uid and gid are fixed instead of "whatever the tool picks". A named volume
# keeps the ownership it was created with, so a uid that moves with a base image
# update would lock the app out of its own index on the next upgrade.
#
# Which paths need a chown, and why exactly these:
#   /app/run  the frpc configuration is written here at start up, mode 600,
#             because it carries the HaRP shared key. It used to be /frpc.toml,
#             which only root can create.
#   /nc_app_findling_backend_data  the mount point of the persistent volume that
#             AppAPI creates for this app id. Docker initialises a fresh named
#             volume from the image directory it is mounted over, ownership
#             included, so pre-creating it here is what makes the volume land
#             owned by the app user instead of by root. If AppAPI ever mounts
#             somewhere else, the volume arrives root owned; entrypoint.sh checks
#             for exactly that and says so in one line.
#   /certs/frp  where HaRP installs the client certificate, its key and the CA of
#             the tunnel. It creates the directory and writes the three files
#             through docker exec, and that exec runs as the image user, which is
#             the unprivileged one below. Without this line the installation
#             fails in a way that looks like something else entirely: HaRP logs
#             "mkdir: cannot create directory '/certs': Permission denied",
#             harp_connect.sh finds no readable certificate and falls back to TLS
#             without a client certificate, and the frp server then refuses every
#             login with EOF. The container is up, the app answers on its socket,
#             and it is unreachable. Measured on 2026-09-03 against
#             scripts/dev/compose-harp.yaml: with the directory pre-created and
#             owned by this user, the same run logs "client certificates in
#             /certs/frp, configuring the tunnel with mutual TLS" and "login to
#             server success". Mode 0700, because the private key of the tunnel
#             lands here.
#             What is deliberately NOT done: HaRP also runs
#             update-ca-certificates, which needs /etc/ssl/certs and fails with
#             exit 2 in this image. The trust store stays owned by root, because
#             frpc reads the CA through the trustedCaFile that
#             docker/harp_connect.sh writes and never from the OS bundle, and a
#             trust store the application can rewrite is a worse problem than a
#             log line.
#   /app itself stays owned by root and world readable. The process reads its
#             virtual environment and its scripts, it must not be able to
#             rewrite them.
#   /tmp      is 1777 in the base image already, which is where the HaRP unix
#             socket goes.
RUN groupadd --gid 1000 findling \
    && useradd --uid 1000 --gid 1000 --no-create-home --home-dir /app --shell /usr/sbin/nologin findling \
    && mkdir -p /app/run /nc_app_findling_backend_data /certs/frp \
    && chown findling:findling /app/run /nc_app_findling_backend_data /certs /certs/frp \
    && chmod 0700 /app/run /certs /certs/frp

USER findling

# Inside a container the client library's default of 127.0.0.1 means "reachable
# from nobody", so the published port would answer nothing. Under HaRP this
# value is ignored, because the app binds a unix socket there instead.
ENV APP_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

# No port is declared or fixed here on purpose. The port is whatever AppAPI
# hands over in APP_PORT, and under HaRP there is no TCP port at all. A grep for
# the port declaring instruction over this file has to come back empty.
ENTRYPOINT ["/app/docker/init.sh"]
