# syntax=docker/dockerfile:1

# Findling ExApp backend.
#
# Four stages, one base image. The build stage owns uv and the compiler-adjacent
# noise, the frpc stage and the model stage own the two downloads this image
# needs, and the runtime stage gets the finished virtual environment plus that
# one binary, the quantised model and nothing else from any of them.
#
# The second download is the embedding model, and it is fetched at build time on
# purpose rather than at first start. A first start that pulls 470 MB from
# HuggingFace is not zero-config: it fails behind a firewall, it fails behind a
# proxy, it fails on an offline installation, and it fails on exactly the small
# self hosted boxes this app is for. The model is baked in, HF_HUB_OFFLINE is
# set in the runtime stage, and nothing in the running container ever resolves a
# name. The same argument the German word list below is installed with.
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

# The embedding model, fetched and quantised in a stage of its own.
#
# It starts FROM build rather than from the base image, because everything this
# stage needs is already standing there: uv, the lock file and a virtual
# environment that carries onnxruntime. Only two things are added, and both are
# build time only. curl and the CA bundle, for the same reason the frpc stage
# has them. And onnx, which onnxruntime.quantization imports and onnxruntime
# itself does not depend on; it is a group of its own in pyproject.toml so that
# 19 MB of graph manipulation library cannot end up in the runtime image, which
# copies its virtual environment from the build stage and not from this one.
#
# Why the build quantises at all, in one line, because the long version is in
# scripts/dev/quantize_model.py: the int8 file upstream ships is
# model_qint8_avx512_vnni.onnx, AVX512-VNNI is x86 only, and the target hardware
# of this app is an ARM board.
FROM build AS model

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN uv sync --frozen --no-dev --no-editable --group quantize

# The model is addressed by the commit of its repository, never by a branch
# name. main moves, and a model that moves is a search that silently answers
# differently after a rebuild. Read on 2026-09-04, together with every checksum
# below.
ARG MODEL_REPO=intfloat/multilingual-e5-small
ARG MODEL_REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3

# The script lives at scripts/dev/quantize_model.py in the repository, which is
# outside this build context: the context is backend/. It arrives through an
# additional named build context instead of being duplicated here, so there is
# one implementation of the size gate and not two that can drift apart. Every
# caller passes it:
#
#     docker build --build-context scripts=./scripts -f backend/Dockerfile backend
#
# and .github/workflows/docker.yml, .github/workflows/resilience.yml and
# .github/workflows/deploy-harp.yml do exactly that. A build without the flag
# fails here rather than somewhere later, which is the behaviour we want.
COPY --from=scripts dev/quantize_model.py /tmp/quantize_model.py

# Six files, each checked against a sha256 written down here, fail closed inside
# the same RUN as the download. The wngerman block below is the pattern: a
# fetched artifact that nobody checks is a fetched artifact anybody can replace,
# and after the build there is nobody left to notice (T-06-01).
#
# Which files, and why exactly these. The mandatory set is not guessed, it is
# read out of fastembed 0.8.0: fastembed/common/preprocessor_utils.py::
# load_tokenizer raises unless config.json, tokenizer.json, tokenizer_config.json
# and special_tokens_map.json all sit next to each other in the model directory
# (preprocessor_config.json is asked for by the image models only). They are
# taken from the onnx/ subfolder, which carries its own complete set, so that
# every file comes from one place and one revision. sentencepiece.bpe.model is
# not in that contract, because the tokenizer is driven by tokenizer.json; it
# travels along as the source artifact that tokenizer.json was built from, at
# 4.8 MB, and it is the one file here a later plan may drop again.
#
# The fp32 original is the input of the quantisation and never leaves this
# stage. It is deleted in this very RUN, so that no later COPY can pick up
# 470 MB by accident: the runtime stage takes /model, and /model holds the int8
# result only.
RUN set -eu; \
    base="https://huggingface.co/${MODEL_REPO}/resolve/${MODEL_REVISION}"; \
    mkdir -p /tmp/fp32 /model; \
    fetch() { \
        curl -fsSL --retry 3 --retry-delay 2 -o "$2" "${base}/$1"; \
        echo "$3  $2" | sha256sum -c -; \
    }; \
    fetch onnx/model.onnx /tmp/fp32/model.onnx \
        ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665; \
    fetch onnx/tokenizer.json /model/tokenizer.json \
        0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39; \
    fetch onnx/sentencepiece.bpe.model /model/sentencepiece.bpe.model \
        cfc8146abe2a0488e9e2a0c56de7952f7c11ab059eca145a0a727afce0db2865; \
    fetch onnx/config.json /model/config.json \
        bbb7c1333fc4b3e27fbc9cd5d2070aabcc1d4dfb99917c3633e772f97545a6b6; \
    fetch onnx/tokenizer_config.json /model/tokenizer_config.json \
        a1d6bc8734a6f635dc158508bef000f8e2e5a759c7d92f984b2c86e5ff53425b; \
    fetch onnx/special_tokens_map.json /model/special_tokens_map.json \
        d05497f1da52c5e09554c0cd874037a083e1dc1b9cfd48034d1c717f1afc07a7; \
    /app/.venv/bin/python /tmp/quantize_model.py \
        --input /tmp/fp32/model.onnx \
        --output /model/model.onnx; \
    rm -rf /tmp/fp32 /tmp/quantize_model.py; \
    test -s /model/model.onnx; \
    ls -l /model

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

# The quantised model, the tokenizer and the four configuration files fastembed
# insists on. The fp32 original is not here and cannot be: the model stage
# deletes it before this COPY can see it.
COPY --from=model /model /usr/local/share/findling/model

# Two licence texts that no upstream artifact carries, which is why they are
# committed to this repository instead of copied out of a package. sqlite-vec is
# dual licensed and ships neither text in its wheel; the Apache-2.0 half is
# taken verbatim from LICENSE-APACHE at the tag v0.1.9. The model declares MIT
# in the metadata of its model card and ships no licence file at all, so that
# file says where the declaration comes from and then reproduces the MIT text.
# Both obligations attach to the image, because the image is what is
# distributed, and THIRD-PARTY.md carries the same statement for readers of the
# repository (D-09).
COPY docker/licenses/COPYING.sqlite-vec docker/licenses/COPYING.multilingual-e5-small \
     /usr/local/share/findling/

# The vec0 extension, lifted out of the wheel and put at a path of our own.
#
# Why the copy, when the file is already in site-packages: enable_load_extension
# hands SQLite a path and SQLite loads whatever machine code it finds there, so
# that path is the most security relevant constant in this image (T-06-03). As a
# constant of the image it can be checked here, once, at build time. As a
# property of a package layout it would move whenever sqlite-vec changes its
# packaging, and the code would have to go looking at run time, in the process
# that holds the index. The path is exported as FINDLING_VEC0_PATH below, it
# never comes from a request, and /usr/local is not writable by the user this
# container runs as.
#
# The location inside the wheel is asked for rather than guessed:
# sqlite_vec.loadable_path() returns the path without the platform suffix, which
# is what SQLite itself would append.
#
# The checksum is per architecture, and that is not a weakness of the pin but
# the shape of the artifact: the wheel is py3-none, so there is no ABI to it,
# but it carries a compiled shared object and amd64 and arm64 therefore hold
# different bytes. Both were read on 2026-09-04 out of the two manylinux wheels
# of sqlite-vec 0.1.9, whose own sha256 matches the one uv.lock records. An
# architecture nobody recorded a sum for fails the build instead of skipping the
# check, which is the difference between a gate and a decoration.
ARG TARGETARCH
RUN set -eu; \
    case "${TARGETARCH}" in \
        amd64) want=5923730861b86c707cca5602b5f91092f9e52a46706dbc6e269fd4bb9c4498e8 ;; \
        arm64) want=0b84cbd06418ca3040827deddd650539be05be0f657952426b926c8606217437 ;; \
        *) echo "no vec0 checksum is recorded for TARGETARCH=${TARGETARCH}"; exit 1 ;; \
    esac; \
    src="$(/app/.venv/bin/python -c 'import sqlite_vec; print(sqlite_vec.loadable_path())').so"; \
    test -s "${src}"; \
    install -D -m 0444 "${src}" /usr/local/lib/findling/vec0.so; \
    echo "${want}  /usr/local/lib/findling/vec0.so" | sha256sum -c -; \
    test -s /usr/local/share/findling/COPYING.sqlite-vec; \
    test -s /usr/local/share/findling/COPYING.multilingual-e5-small; \
    chmod 0444 /usr/local/share/findling/COPYING.sqlite-vec \
        /usr/local/share/findling/COPYING.multilingual-e5-small; \
    test -s /usr/local/share/findling/model/model.onnx; \
    test -s /usr/local/share/findling/model/tokenizer.json

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
#
# HF_HUB_OFFLINE is a net, not a proof, and the difference is worth one line.
# What it does: huggingface-hub and requests arrive in this image through
# fastembed, and with this variable set the library refuses to resolve a name
# instead of quietly reaching for the network when it misses something in its
# cache. What it does not do: it does not stop any other code from opening a
# socket, and it is not evidence that nothing does. The evidence is the offline
# test of plan 06-10, which starts this container with --network none and runs a
# real semantic search through it, and the probe of plan 06-01, which loads the
# extension with the network cut as well.
#
# The two paths are constants of the image and are read as such: the model
# directory and the extension are where this Dockerfile put them, they are not
# writable by the user below, and no request ever supplies either of them.
ENV APP_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}" \
    HF_HUB_OFFLINE=1 \
    FINDLING_EMBED_MODEL_DIR=/usr/local/share/findling/model \
    FINDLING_VEC0_PATH=/usr/local/lib/findling/vec0.so

# No port is declared or fixed here on purpose. The port is whatever AppAPI
# hands over in APP_PORT, and under HaRP there is no TCP port at all. A grep for
# the port declaring instruction over this file has to come back empty.
ENTRYPOINT ["/app/docker/init.sh"]
