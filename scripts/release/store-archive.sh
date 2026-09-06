#!/bin/sh
# The one place that decides what ships in the two store archives.
#
# Why this file exists at all. Until plan 06.1-12 the staging, the packing and
# the content proof lived inline in .github/workflows/release.yml, and that was
# fine while release.yml was the only caller. It is not any more: the HaRP
# deploy job installs both halves out of the very archives a stranger would
# download, so it has to build them, and it cannot reach the signing secrets
# because it carries a pull_request trigger (docs/certificates.md). A second
# packing path in that workflow would be a second way to ship a tests directory,
# which is exactly the class of mistake the content proof below was written to
# catch. So the rules move here and both workflows call them.
#
# What deliberately did NOT move: the two signatures. The code signature belongs
# INSIDE the companion archive and the release signature belongs OVER it, so the
# order is stage, code sign, pack, release sign, and the two signing steps stay
# in release.yml next to the secrets they read. This script therefore has stage
# and pack as separate subcommands rather than one build command, so that a
# caller can sign in between.
#
# POSIX sh, no bashisms: the callers are GitHub runners today, and the ARM box
# of this phase runs whatever /bin/sh is there.
#
# Usage:
#   store-archive.sh stage-companion <stage-dir>
#   store-archive.sh stage-backend   <stage-dir>
#   store-archive.sh pack            <stage-dir> <app-id> <archive>
#   store-archive.sh assert-contents <archive> <app-id> <wants-signature 0|1>
#
# Every subcommand is run from the root of this repository, except
# assert-contents, which only reads the archive it is given.

set -eu

usage() {
	echo "usage: store-archive.sh stage-companion <stage-dir>"
	echo "       store-archive.sh stage-backend   <stage-dir>"
	echo "       store-archive.sh pack            <stage-dir> <app-id> <archive>"
	echo "       store-archive.sh assert-contents <archive> <app-id> <wants-signature 0|1>"
}

# Exactly one top level directory, named after the app id in lowercase ASCII,
# with appinfo/info.xml inside it. That is a store requirement and it is also
# what integrity:sign-app derives the app id from, so the directory name is load
# bearing twice.
#
# The include list is explicit, and an include list rather than an exclude list
# on purpose: a new directory in php/ then has to be named here before it ships,
# instead of shipping because nobody remembered to exclude it.
#
# What is left out and why:
#   tests, phpunit.xml    the unit suite. An archive with test code in it is a
#                         different product from the one that was reviewed.
#   composer.json/.lock   plan 05-15 added phpunit as a require-dev dependency.
#                         The app has no runtime composer dependency at all,
#                         Nextcloud autoloads OCA\Findling from lib/ by
#                         convention, and a composer.json in a released app
#                         invites a composer install on a production instance.
#   vendor                never built here, and named anyway, because the day
#                         somebody runs composer install before this step the
#                         silence would be the bug.
#   .gitkeep, .git        repository plumbing.
#
# LICENSE and THIRD-PARTY.md travel with the archive because their subject
# travels with it: php/img/app-dark.svg and php/templates/admin.php carry nine
# icon paths from Material Design Icons under Apache-2.0, and THIRD-PARTY.md is
# the attribution for them. Shipping the icons without the attribution is the one
# licence mistake this archive could make.
stage_companion() {
	stage="$1"
	app="${stage}/findling"
	mkdir -p "${app}"
	for d in appinfo lib templates js css img l10n; do
		cp -R "php/${d}" "${app}/${d}"
	done
	cp LICENSE THIRD-PARTY.md "${app}/"
	find "${app}" -name '.gitkeep' -delete
	echo "staged tree:"
	find "${app}" -maxdepth 1 -mindepth 1 -printf '  %P\n' | sort
}

# info.xml is copied byte for byte and is never filtered or rewritten, and that
# is a hard requirement rather than tidiness. pre-info.xslt drops the routes
# block silently, so the store database never sees the five routes of this
# container; AppAPI reads them back out of this archive at installation time and
# writes them into oc_ex_apps_routes. An archive with a rewritten info.xml
# installs an app whose route table is empty, and nothing anywhere says so. The
# app-metadata job of php.yml holds that finding as a step that goes red if the
# transform ever stops dropping them, and the HaRP deploy job holds the other
# end: it registers the ExApp out of this very file and counts the rows the
# registration produced, once with a stripped copy and once with this one.
#
# It counts rows and not search hits, and that correction is from 07.09.2026:
# HaRP 0.4.5 skips route checking for AppAPI signed requests, which is the path
# the companion uses, so the search answers with the block and without it. The
# route table is the only place where the two archives differ.
#
# This archive carries metadata and not code. The container image is not in it:
# info.xml names it, and AppAPI pulls it from ghcr at installation time. LICENSE
# and THIRD-PARTY.md travel along for the same reason they do on the other side,
# and because THIRD-PARTY.md is where the licences of everything inside that
# image are written down.
stage_backend() {
	stage="$1"
	app="${stage}/findling_backend"
	mkdir -p "${app}/appinfo"
	cp backend/appinfo/info.xml "${app}/appinfo/info.xml"
	cp LICENSE THIRD-PARTY.md "${app}/"
	cmp backend/appinfo/info.xml "${app}/appinfo/info.xml"
	echo "info.xml is byte identical to the working tree, so AppAPI will read the routes it expects"
}

# --numeric-owner with owner and group zero because the uid of a GitHub runner
# has no business inside a public artefact, and because it removes one source of
# difference between two builds of the same commit.
#
# A tar.gz is not byte reproducible, which has one consequence for the caller
# that signs: the archive that gets signed has to be the archive that gets
# uploaded, and no later step may rebuild it.
pack() {
	stage="$1"
	app="$2"
	archive="$3"
	mkdir -p "$(dirname "${archive}")"
	tar --numeric-owner --owner=0 --group=0 \
		-czf "${archive}" -C "${stage}" "${app}"
	ls -l "${archive}"
}

# The claims of the two staging functions above, turned into something that can
# fail. Every one of them is a promise made somewhere else in the repository: the
# single top level directory to the store API, the absent test code to
# php/composer.json, signature.json to the integrity check, and its absence on
# the backend side to the comment in stage_backend. A promise nobody checks is a
# sentence, and this is the difference.
#
# The archive is listed exactly ONCE, into a file, and every check reads that
# file. Not a matter of taste: "tar -tzf x | grep -q pattern" makes grep exit on
# the first hit, tar takes SIGPIPE while it is still writing, and with pipefail
# in force the whole pipeline reports failure. It is worse than a plain bug,
# because it depends on the size of the archive: the small backend listing
# finishes before grep leaves and looks fine, the larger companion one does not.
# The rehearsal of plan 05-18 found it exactly that way, with two present files
# reported as missing.
assert_contents() {
	archive="$1"
	app="$2"
	wants_signature="$3"
	listing="${archive}.listing"
	fail=0

	tar -tzf "${archive}" > "${listing}"
	echo "${archive}, $(wc -l < "${listing}") entries"
	cat "${listing}"

	tops=$(cut -d/ -f1 "${listing}" | sort -u)
	if [ "${tops}" != "${app}" ]; then
		echo "${archive}: the top level is '${tops}' and the store needs exactly one directory named ${app}"
		fail=1
	fi

	if grep -qx "${app}/appinfo/info.xml" "${listing}"; then
		echo "${archive}: appinfo/info.xml is present"
	else
		echo "${archive}: appinfo/info.xml is missing and the store cannot read the app at all"
		fail=1
	fi

	if grep -qx "${app}/appinfo/signature.json" "${listing}"; then
		if [ "${wants_signature}" = "0" ]; then
			echo "${archive}: carries a code signature, and this half has no PHP for the integrity check to see"
			fail=1
		else
			echo "${archive}: carries appinfo/signature.json, as the integrity check of the instance requires"
		fi
	elif [ "${wants_signature}" = "1" ]; then
		echo "${archive}: has no appinfo/signature.json, so the integrity check of every instance would report it as modified"
		fail=1
	else
		echo "${archive}: carries no code signature, which is correct for a container half"
	fi

	# The exclusion list of the staging step, as a test. Anchored on the top
	# level directory so that a file named tests somewhere inside l10n could not
	# be mistaken for the suite, and matched case sensitively because that is how
	# the names are written.
	for forbidden in tests vendor phpunit.xml composer.json composer.lock; do
		if grep -q "^${app}/${forbidden}\(/\|$\)" "${listing}"; then
			echo "${archive}: contains ${forbidden}, which is development material and must not be released"
			fail=1
		fi
	done

	return "${fail}"
}

command="${1:-}"
if [ "$#" -gt 0 ]; then
	shift
fi

case "${command}" in
	stage-companion)
		[ "$#" -eq 1 ] || { usage; exit 1; }
		stage_companion "$1"
		;;
	stage-backend)
		[ "$#" -eq 1 ] || { usage; exit 1; }
		stage_backend "$1"
		;;
	pack)
		[ "$#" -eq 3 ] || { usage; exit 1; }
		pack "$1" "$2" "$3"
		;;
	assert-contents)
		[ "$#" -eq 3 ] || { usage; exit 1; }
		assert_contents "$1" "$2" "$3"
		;;
	*)
		usage
		exit 1
		;;
esac
