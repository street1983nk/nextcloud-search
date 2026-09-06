#!/bin/sh
# Validate an info.xml the way the store does, without waiting for a CI run.
#
# The store does not validate the file as it stands. It runs pre-info.xslt over
# the document first and validates the RESULT against info.xsd, so the order of
# the two stages below is the whole point of this script. A direct check against
# info.xsd rejects the routes block that the store accepts and misses whatever
# the transform changes, which means it answers a question nobody asked.
#
# This is the local half of the app-metadata job in .github/workflows/php.yml:
# same two stages, same order, same pinned pair of files. It exists because of
# DI-05-25 of phase 5: there is neither xsltproc nor xmllint on the development
# machine of this project, so until now a schema error surfaced on the runner at
# the earliest, and at a submission it would have been expensive.
#
# Usage:
#
#     scripts/dev/validate_info_xml.sh backend/appinfo/info.xml
#     scripts/dev/validate_info_xml.sh php/appinfo/info.xml backend/appinfo/info.xml
#     scripts/dev/validate_info_xml.sh --check-pins
#
# The pinned commit is deliberately NOT written down here. It is read out of the
# two workflow files, and that is also the only reason this script can prove the
# two agree: a third copy of the value would be the very construction the check
# below exists to keep out. The check runs before every validation, so a run that
# validates anything has already proven the pin is one value and not two.
#
# If xsltproc and xmllint are both on PATH they are used directly. If they are
# not, the two stages run inside a throwaway container that carries them, which
# is what makes this usable on the machine that has neither. The container is a
# convenience and never the gate: the gate is the job in php.yml, on a runner
# where both tools are installed from the distribution.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "${SCRIPT_DIR}/../.." && pwd)

PHP_WORKFLOW="${REPO_ROOT}/.github/workflows/php.yml"
RELEASE_WORKFLOW="${REPO_ROOT}/.github/workflows/release.yml"

# The image that stands in for xsltproc and xmllint on a machine without them.
# Pinned by digest rather than by tag for the reason every action in this
# repository is pinned by commit: a tag can be repointed at anything. Override it
# with FINDLING_VALIDATOR_IMAGE if a different base is needed.
VALIDATOR_IMAGE="${FINDLING_VALIDATOR_IMAGE:-alpine@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce}"

# Which of the two stages failed, as an exit code, so that the native path and
# the container path report a failure in the same words. Both are outside the
# range curl, xsltproc and xmllint use for their own errors.
STAGE_TRANSFORM=21
STAGE_SCHEMA=22

usage() {
	cat <<'TEXT'
usage: validate_info_xml.sh [--check-pins] [<info.xml> ...]

  --check-pins   only prove that both workflow files carry the same
                 APPSTORE_SHA and that no third copy of it exists
  <info.xml>     a file to send through the store validation path

TEXT
}

# The pinned commit of one workflow file, or nothing if the file has none.
read_pin() {
	sed -n 's/^[[:space:]]*APPSTORE_SHA:[[:space:]]*\([0-9a-f]\{40\}\).*$/\1/p' "$1" | head -n 1
}

# Both occurrences of the pin, held against each other, and counted.
#
# The count is the second half and not decoration. Two files with the same value
# are what the store validation path rests on; a third file with the same value
# is how they start to disagree, because the next person to move the pin moves
# the two they know about.
#
# .planning is left out of the count on purpose. Those files are prose about the
# repository rather than part of it: a plan or a summary quotes the value it
# moved, which is exactly what a record is for, and none of them is read by any
# job.
check_pins() {
	php_pin=$(read_pin "${PHP_WORKFLOW}")
	release_pin=$(read_pin "${RELEASE_WORKFLOW}")

	if [ -z "${php_pin}" ]; then
		echo "validate_info_xml: no APPSTORE_SHA in ${PHP_WORKFLOW}" >&2
		exit 1
	fi
	if [ -z "${release_pin}" ]; then
		echo "validate_info_xml: no APPSTORE_SHA in ${RELEASE_WORKFLOW}" >&2
		exit 1
	fi

	if [ "${php_pin}" != "${release_pin}" ]; then
		echo "validate_info_xml: the two APPSTORE_SHA values disagree." >&2
		echo "  php.yml     ${php_pin}" >&2
		echo "  release.yml ${release_pin}" >&2
		echo "What that means: the pull request validation and the release validation" >&2
		echo "check against two different versions of pre-info.xslt and info.xsd, so a" >&2
		echo "green run of either says nothing about the other. Raise both or neither." >&2
		exit 1
	fi

	occurrences=$(git -C "${REPO_ROOT}" grep -F "${php_pin}" -- . ':(exclude).planning' | wc -l | tr -d ' ')
	if [ "${occurrences}" != "2" ]; then
		echo "validate_info_xml: the pin stands at ${occurrences} places outside .planning, and it may stand at two." >&2
		git -C "${REPO_ROOT}" grep -F "${php_pin}" -- . ':(exclude).planning' >&2 || true
		echo "What that means: the next person to raise the pin raises the copies they" >&2
		echo "know about, and the ones they do not know about keep validating against" >&2
		echo "yesterday. Two places, both of them a workflow file, is the whole rule." >&2
		exit 1
	fi

	APPSTORE_SHA="${php_pin}"
}

# The pinned pair, fetched next to the document that is about to be judged.
fetch_pinned_pair() {
	base="https://raw.githubusercontent.com/nextcloud/appstore/${APPSTORE_SHA}/nextcloudappstore/api/v1/release"
	curl -fsSL "${base}/pre-info.xslt" -o "${WORK}/pre-info.xslt"
	curl -fsSL "${base}/info.xsd" -o "${WORK}/info.xsd"
}

validate_natively() {
	xsltproc "${WORK}/pre-info.xslt" "$1" > "${WORK}/normalised.xml" || return "${STAGE_TRANSFORM}"
	xmllint --noout --schema "${WORK}/info.xsd" "${WORK}/normalised.xml" || return "${STAGE_SCHEMA}"
}

# The same two stages inside a container, with the document handed over on stdin
# so that no path of this machine has to be mounted. Path translation between a
# Windows shell and a Linux container is the kind of detail that turns a five
# line helper into a support case, and stdin has none of it.
validate_in_a_container() {
	docker run --rm -i \
		-e APPSTORE_SHA="${APPSTORE_SHA}" \
		-e STAGE_TRANSFORM="${STAGE_TRANSFORM}" \
		-e STAGE_SCHEMA="${STAGE_SCHEMA}" \
		"${VALIDATOR_IMAGE}" \
		sh -c '
			set -eu
			apk add --no-cache libxslt libxml2-utils curl >/dev/null
			base="https://raw.githubusercontent.com/nextcloud/appstore/${APPSTORE_SHA}/nextcloudappstore/api/v1/release"
			curl -fsSL "${base}/pre-info.xslt" -o /tmp/pre-info.xslt
			curl -fsSL "${base}/info.xsd" -o /tmp/info.xsd
			cat > /tmp/info.xml
			xsltproc /tmp/pre-info.xslt /tmp/info.xml > /tmp/normalised.xml || exit "${STAGE_TRANSFORM}"
			xmllint --noout --schema /tmp/info.xsd /tmp/normalised.xml || exit "${STAGE_SCHEMA}"
		' < "$1"
}

validate_one() {
	document="$1"

	if [ ! -f "${document}" ]; then
		echo "validate_info_xml: ${document} is not a file" >&2
		return 1
	fi

	status=0
	"${RUNNER}" "${document}" || status=$?

	if [ "${status}" -eq 0 ]; then
		echo "validate_info_xml: ${document} passes the store path, transform then schema, against appstore ${APPSTORE_SHA}"
		return 0
	fi
	if [ "${status}" -eq "${STAGE_TRANSFORM}" ]; then
		echo "validate_info_xml: ${document} failed at stage 1, pre-info.xslt, before the schema was ever reached" >&2
		return 1
	fi
	if [ "${status}" -eq "${STAGE_SCHEMA}" ]; then
		echo "validate_info_xml: ${document} failed at stage 2, info.xsd, over the document AFTER the transform" >&2
		echo "  the message above is about the normalised document, so a line number in it is not a line of ${document}" >&2
		return 1
	fi

	echo "validate_info_xml: ${document} could not be judged, the validator exited ${status}" >&2
	return 1
}

only_pins=false
documents=""
for argument in "$@"; do
	case "${argument}" in
		--check-pins)
			only_pins=true
			;;
		-h|--help)
			usage
			exit 0
			;;
		-*)
			echo "validate_info_xml: unknown option ${argument}" >&2
			usage >&2
			exit 1
			;;
		*)
			documents="${documents} ${argument}"
			;;
	esac
done

check_pins
echo "validate_info_xml: both workflow files pin appstore ${APPSTORE_SHA}, and nothing else does"

if [ "${only_pins}" = true ]; then
	exit 0
fi

if [ -z "${documents}" ]; then
	echo "validate_info_xml: no file given" >&2
	usage >&2
	exit 1
fi

WORK=$(mktemp -d)
trap 'rm -rf "${WORK}"' EXIT

if command -v xsltproc >/dev/null 2>&1 && command -v xmllint >/dev/null 2>&1; then
	RUNNER=validate_natively
	fetch_pinned_pair
elif command -v docker >/dev/null 2>&1; then
	RUNNER=validate_in_a_container
	echo "validate_info_xml: no xsltproc and no xmllint here, running the two stages in ${VALIDATOR_IMAGE}"
else
	echo "validate_info_xml: this needs either xsltproc and xmllint on PATH or a docker that can run a container" >&2
	exit 1
fi

failures=0
for document in ${documents}; do
	validate_one "${document}" || failures=$((failures + 1))
done

if [ "${failures}" -ne 0 ]; then
	echo "validate_info_xml: ${failures} file(s) would not pass the store" >&2
	exit 1
fi
