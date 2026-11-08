#!/usr/bin/env bash
# The run of the step "Store upgrade 1, both halves out of the release assets
# of the previous version" in .github/workflows/deploy-harp.yml, moved out of
# the workflow in plan 43-10 because the file stood 36 bytes under the 500 KB
# cap of GitHub Actions and the bounded wait of assurance 18 needed room.
# It runs from the workspace root, with the environment of that step and the
# shell options of a run block (bash -e -o pipefail).
set -eo pipefail

# The same URL shape store-submit.yml hands the store, built from
# GITHUB_REPOSITORY for the same reason as in "Store install 1 from the
# release": a second way of naming the same asset would be a second
# inventory, and the store fetches exactly this one. The tag comes out
# of UPGRADE_FROM_TAG at the top of this file, where the reason for its
# value stands.
base="https://github.com/${GITHUB_REPOSITORY}/releases/download/${UPGRADE_FROM_TAG}"
from="${RUNNER_TEMP}/upgrade-from"
rm -rf "${from}"
mkdir -p "${from}/dist" "${from}/extract"
for app in findling findling_backend; do
  url="${base}/${app}.tar.gz"
  echo "loading ${url}"
  # -f so that an HTML error page never lands in the file, and no
  # fallback of any kind: an upgrade proof that quietly starts from
  # something other than the released bytes would be worse than a red
  # run.
  if ! curl -sfL --retry 3 --retry-delay 5 --retry-connrefused \
       -o "${from}/dist/${app}.tar.gz" "${url}"; then
    echo "::error::${url} could not be loaded, so there is no ${UPGRADE_FROM_TAG} installation to upgrade from"
    exit 1
  fi
  if [ ! -s "${from}/dist/${app}.tar.gz" ]; then
    echo "::error::${url} answered with an empty file"
    exit 1
  fi
done
# Which bytes the upgrade starts from, on record, so that a reader of
# this run can say what was installed without trusting the tag to have
# stayed put.
ls -l "${from}/dist"
sha256sum "${from}/dist/findling.tar.gz" "${from}/dist/findling_backend.tar.gz"

# The companion half. The signature in this archive is the real one
# release.yml made with the app key of the Nextcloud Code Signing Root
# Authority, which the server checkout trusts out of the box, so this
# is the file list a user's instance verifies as well.
tar -xzf "${from}/dist/findling.tar.gz" -C apps
test -f apps/findling/appinfo/signature.json
old_companion=$(sed -n 's:.*<version>\(.*\)</version>.*:\1:p' apps/findling/appinfo/info.xml | head -1)
echo "the companion of the release carries version ${old_companion}"
# The navigation entry, and the assertion reads the other way round
# since 2026-09-21. Overhauled wording, kept on record: until that day
# this step demanded the ABSENCE of the <navigations> block, because
# php/appinfo/info.xml grew it in plan 09-06 after v1.0.3 was
# published, and a released archive that already carried it would have
# made assurance 6 of "Store upgrade 5" green for the wrong reason.
# v1.1.0 carries the block, so that sentence is about a release of the
# day before yesterday, and assurance 6 moved to the declared filters
# of the provider in plan 16-09.
#
# What is measured here now is the presence of the block, and it is
# not a formality: it is the cheapest assertion in this file that
# UPGRADE_FROM_TAG really points at a release this proof understands.
# A tag out of the 1.0.x line would answer without the block, and the
# whole block below would then measure a jump nobody claimed.
#
# The reasoning moved with the tag on 2026-09-24 (plan 18-12) and the
# assertion did not, which is why the two are written apart here. Until
# that day this paragraph said "a release of the 1.1.x line", because
# UPGRADE_FROM_TAG was v1.1.0 and 1.1.0 was the first release with the
# block. v1.2.0 carries it as well, so the assertion stays true without
# a byte of its own changing; what it rules out is now everything below
# v1.1.0 rather than everything outside 1.1.x, and that is still the
# cheap floor this step is here to put in.
if ! grep -q '<navigations>' apps/findling/appinfo/info.xml; then
  echo "the companion of ${UPGRADE_FROM_TAG} declares no navigation entry, so this is older than v1.1.0 and not a release this proof starts from"
  exit 1
fi
echo "the companion of ${UPGRADE_FROM_TAG} declares the navigation entry, as every release since v1.1.0 does"
"${RUNNER_TEMP}/nc-occ.sh" app:enable findling

# The container half, out of the info.xml of the released archive and
# out of nothing else: registry, image and image-tag are what a user
# of the previous version really runs.
# ghcr.io/street1983nk/findling_backend:1.5.0 is the image the release
# of 2026-10-12 pushed, as an OCI index with linux/amd64 and
# linux/arm64 (checked anonymously against ghcr.io on 2026-10-28, plan
# 40-03), and a missing tag would end this step rather than fall back
# to anything. The predecessors were checked the same way and are
# named so that the habit is visible rather than only its result:
# :1.3.2 on 2026-10-06, :1.2.0 on 2026-09-24, :1.1.0 against the
# manifest list on 2026-09-21, :1.0.3 on 2026-09-10. Whoever moves
# UPGRADE_FROM_TAG again does this check again, because a tag without
# an image turns the registration below into a red step with a
# confusing message.
tar -xzf "${from}/dist/findling_backend.tar.gz" -C "${from}/extract"
old_info="${from}/extract/findling_backend/appinfo/info.xml"
test -f "${old_info}"
grep -E '<version>|<registry>|<image>|<image-tag>' "${old_info}"
"${RUNNER_TEMP}/nc-occ.sh" app_api:app:register findling_backend harp_proxy_host \
  --info-xml "${old_info}" --wait-finish

container=$(docker ps --filter 'name=findling_backend' --format '{{.Names}}')
if [ -z "${container}" ]; then
  echo "the ${UPGRADE_FROM_TAG} registration created no running container"
  docker ps -a
  exit 1
fi
volume=$(docker volume ls --filter 'name=findling_backend' --format '{{.Name}}')
if [ -z "${volume}" ]; then
  echo "the ${UPGRADE_FROM_TAG} registration created no volume, and an upgrade that keeps nothing proves nothing"
  docker volume ls
  exit 1
fi
docker ps --filter "name=${container}" --format '{{.Names}}\t{{.Image}}\t{{.Status}}'
echo "the ${UPGRADE_FROM_TAG} installation runs as ${container} on the volume ${volume}"
{
  echo "UPGRADE_OLD_CONTAINER=${container}"
  echo "UPGRADE_VOLUME=${volume}"
  echo "UPGRADE_OLD_COMPANION=${old_companion}"
} >> "${GITHUB_ENV}"
