#!/usr/bin/env bash
# The style gate of the companion app (phase 44, requirement PRUEF-03).
#
# php-cs-fixer runs with the rule set of nextcloud/coding-standard, configured
# in php/.php-cs-fixer.dist.php over lib, appinfo, templates and tests, as a
# dry run: it changes no file, it only reports. The script runs two passes:
#
#   real   the app as it is. Exit 0 of php-cs-fixer is green, exit 8 means at
#          least one file breaks the standard and is red with the diff. Any
#          other exit code is red as well: a crash or a configuration error
#          must never read as "no violation".
#   probe  the positive control. A file with one plain violation is written to
#          lib/CsProbe.php and checked in the path mode intersection, which
#          keeps the finder of the configuration in charge. php-cs-fixer MUST
#          answer with exit 8. Anything else means the gate cannot see a
#          violation under lib/ (finder lost the directory, rule set empty,
#          tool broken), so the gate is blind and that is red too. The probe is
#          removed again and never committed.
#
# Usage:
#
#     scripts/ci/php_cs_gate.sh
#
# Environment:
#
#     PHP_DIR   the companion app directory with .php-cs-fixer.dist.php
#               (default "php", relative to the repository root; an absolute
#               path is used as it is)
#
# Needs php and composer install in php/tools/php-cs-fixer done before; the job
# php-cs of .github/workflows/php.yml does that. Exit code 0 only when the real
# pass found nothing and the probe was seen.
set -euo pipefail

SCRIPT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH='' cd -- "${SCRIPT_DIR}/../.." && pwd)

PHP_DIR="${PHP_DIR:-php}"
case "${PHP_DIR}" in
	/*) ;;
	*) PHP_DIR="${REPO_ROOT}/${PHP_DIR}" ;;
esac

FIXER="tools/php-cs-fixer/vendor/bin/php-cs-fixer"
PROBE="lib/CsProbe.php"

fail() {
	echo "php cs gate: $1" >&2
	exit 1
}

cd "${PHP_DIR}" || fail "no such directory: ${PHP_DIR}"
[ -f .php-cs-fixer.dist.php ] || fail "no .php-cs-fixer.dist.php in ${PHP_DIR}"
[ -f "${FIXER}" ] || fail "${FIXER} is missing; run composer install in tools/php-cs-fixer first"

PROBE_CREATED=0
cleanup() {
	if [ "${PROBE_CREATED}" -eq 1 ]; then
		rm -f "${PROBE}"
	fi
}
trap cleanup EXIT

# Pass 1: the app as it is.
set +e
php "${FIXER}" fix --dry-run --diff --using-cache=no --show-progress=none
rc=$?
set -e
case "${rc}" in
	0) echo "php-cs-fixer: no violation" ;;
	8) fail "files break nextcloud/coding-standard (diff above); run php-cs-fixer fix on an LF checkout and commit the result" ;;
	*) fail "php-cs-fixer failed to run (exit ${rc})" ;;
esac

# Pass 2: the positive control. The gate only ever removes what it created.
[ ! -e "${PROBE}" ] || fail "${PROBE} exists already; refusing to overwrite it"
PROBE_CREATED=1
cat >"${PROBE}" <<'EOF'
<?php

/**
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */

declare(strict_types=1);

if(true){echo 1;}
EOF
set +e
php "${FIXER}" fix --dry-run --using-cache=no --show-progress=none --path-mode=intersection "${PROBE}" >/dev/null 2>&1
probe_rc=$?
set -e
rm -f "${PROBE}"
PROBE_CREATED=0
if [ "${probe_rc}" -ne 8 ]; then
	fail "the style gate is blind: php-cs-fixer gave exit ${probe_rc} on ${PROBE}, expected 8"
fi

echo "php cs gate: 0 violations, probe seen"
