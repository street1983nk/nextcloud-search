# syntax=docker/dockerfile:1

# Findling ExApp backend.
#
# Two stages, one base image. The build stage owns uv and the compiler-adjacent
# noise, the runtime stage gets the finished virtual environment and nothing
# else from it.
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

FROM ${BASE_IMAGE} AS runtime

LABEL org.opencontainers.image.source="https://github.com/street1983nk/nextcloud-search" \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.title="Findling Backend" \
      org.opencontainers.image.description="Zero-config search backend for Nextcloud, running as an External App"

# supervisor runs the two program process tree, curl and ca-certificates are
# needed to fetch and verify frpc below and stay in for diagnosis.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        supervisor \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY docker/install_frpc.sh /tmp/install_frpc.sh
RUN chmod 0755 /tmp/install_frpc.sh \
    && /tmp/install_frpc.sh \
    && rm -f /tmp/install_frpc.sh

WORKDIR /app

COPY --from=build /app/.venv /app/.venv
COPY docker/entrypoint.sh docker/harp_connect.sh /app/docker/
COPY docker/supervisord.conf /etc/supervisor/supervisord.conf
RUN chmod 0755 /app/docker/entrypoint.sh /app/docker/harp_connect.sh

# Inside a container the client library's default of 127.0.0.1 means "reachable
# from nobody", so the published port would answer nothing. Under HaRP this
# value is ignored, because the app binds a unix socket there instead.
ENV APP_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

# No port is declared or fixed here on purpose. The port is whatever AppAPI
# hands over in APP_PORT, and under HaRP there is no TCP port at all. A grep for
# the port declaring instruction over this file has to come back empty.
ENTRYPOINT ["supervisord", "-c", "/etc/supervisor/supervisord.conf"]
