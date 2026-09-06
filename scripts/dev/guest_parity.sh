#!/bin/sh
# The guest user probe: the second half of scenario 6, as a tool.
#
# Decision D-22 gives scenario 6 two bodies. The CI job search-parity carries
# the first one, a groupless minimal user with exactly one received view only
# share, and it has done so since plan 05-09. The second one is a real guest
# user over the guests app, and the same decision says that app must NOT become
# a dependency of the CI matrix. This script is that second body.
#
# Why it lives under scripts/dev and not under scripts/ci: scripts/ci is the
# place of the things CI runs, and nobody runs this one in CI. The guests app is
# a foreign app with a release window of its own, and a red matrix caused by a
# foreign app says nothing at all about Findling. The promise that it stays out
# is not left to good intentions either: backend/tests/test_guest_parity.py
# counts the mentions of that app over every workflow and every composite
# action, and a single one turns the suite red.
#
# What a probe without a tool would be is the other reason this file exists. A
# sentence like "checked by hand, fine" is exactly what this hardening phase
# refuses to accept as evidence, so the probe runs as a script, compares with
# the same judge the CI job uses, and its result is a file.
#
# The judge is scripts/ci/parity_diff.py, and it is called rather than copied.
# Two ways of answering one question sooner or later answer it in two ways, and
# on the day they disagree nobody can say which of them is right. So this script
# asks, writes both answers to disk and hands them over. It never decides.
#
# The one content of the guest is a single shared file with a marker of its own,
# which makes the expected set a set of size one and turns every deviation into
# a finding in a named direction. A missing hit means the guest does not find a
# document he is allowed to see, which is a functional defect. An extra hit
# means he is shown something the native search does not show him, and that is
# the one case of this phase that would be a security finding (T-06.1-62).
#
# Two pitfalls of the CI job apply here word for word and are handled the same
# way. SearchQuery::LIMIT_DEFAULT is five and the instance cap
# unified_search_max_results_per_request is twenty five, so the cap is raised
# before the first question and every question carries an explicit limit.
# Without both halves this probe would hold two truncated lists side by side and
# report agreement (pitfall 6, T-06.1-63).
#
# The limit of the method, stated rather than left to be found: the throwaway
# password of the guest travels as an environment assignment into the instance,
# so it is visible in the process list of that container for the moment the
# account is created. The account is generated per run, it exists for the length
# of the run and the cleanup removes it, and the probe belongs on a test
# instance and not on a production one.
#
# POSIX sh. Beyond curl and python3 it needs nothing that the instance does not
# already have. The protocol is written in German because a person reads it; the
# script, its identifiers and its comments are English like the rest of the
# repository.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PARITY_DIFF="${SCRIPT_DIR}/../ci/parity_diff.py"

INSTANCE_URL=""
EXEC_PREFIX=""
CREATOR_CREDENTIALS=""
GUEST_UID="findling-guest-probe"
GUEST_MAIL="findling-guest-probe@example.invalid"
LOG_FILE=""
KEEP=0
CRAWL_SECONDS=120
DRAIN_TIMEOUT=300

# One marker per direction of the probe, lower case and ASCII for the reason the
# CI job names: the native term filter becomes a LIKE over the name column, and
# an umlaut in a marker would turn a question about permissions into a question
# about collations. Every marker stands in the file name AND in the content,
# because the native side is a name search and Findling reads both.
MARKER_SHARED="parityguest"
MARKER_PRIVATE="parityhidden"

# The result cap of the instance and the limit of every question are one
# decision and have to move together. See the header, pitfall 6.
RESULT_LIMIT=100

usage() {
	cat <<'USAGE'
guest_parity.sh, the guest user probe of decision D-22.

It creates a guest user over the guests app, gives him exactly one file with a
marker, asks the native provider and Findling the same questions as that guest,
and lets scripts/ci/parity_diff.py decide whether the two answers describe the
same set of files. It removes the guest, the share and the two files again, and
it writes a protocol.

This script is deliberately not run in CI: D-22 keeps the guests app out of the
matrix, and a gate in backend/tests/test_guest_parity.py holds that promise.

Required:
  --url URL             address of the instance, for example http://localhost:8080
  --exec CMD            how to run a command inside the instance, as the web
                        server user and with the Nextcloud web root as the
                        working directory. Example:
                          "docker exec -i -u www-data -w /var/www/html findling-nc"
  --creator USER:PASS   an ordinary user of the instance. He owns the two marker
                        files, he creates the guest and he shares one file with
                        him. Not the administrator, unless the instance has no
                        other account.

Options:
  --guest-uid UID       account name of the guest (default: findling-guest-probe)
  --guest-mail MAIL     mail address of the guest, which the guests app requires
                        (default: findling-guest-probe@example.invalid)
  --crawl-seconds SEC   upper bound of the crawl pass that indexes the two files
                        (default: 120)
  --drain-timeout SEC   upper bound of the wait for an empty work stock
                        (default: 300)
  --keep                leave guest, share and files in place at the end. The
                        result cap is put back either way.
  --log FILE            protocol file (default: a file in the current directory)
  -h, --help            this text

Exit codes: 0 the probe passed, 1 the probe found something, 2 it was called
wrongly. A finding is never healed by lowering an expectation.
USAGE
}

while [ "$#" -gt 0 ]; do
	case "$1" in
		--url) INSTANCE_URL="$2"; shift 2 ;;
		--exec) EXEC_PREFIX="$2"; shift 2 ;;
		--creator) CREATOR_CREDENTIALS="$2"; shift 2 ;;
		--guest-uid) GUEST_UID="$2"; shift 2 ;;
		--guest-mail) GUEST_MAIL="$2"; shift 2 ;;
		--crawl-seconds) CRAWL_SECONDS="$2"; shift 2 ;;
		--drain-timeout) DRAIN_TIMEOUT="$2"; shift 2 ;;
		--keep) KEEP=1; shift ;;
		--log) LOG_FILE="$2"; shift 2 ;;
		-h|--help) usage; exit 0 ;;
		*) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
	esac
done

for required in INSTANCE_URL EXEC_PREFIX CREATOR_CREDENTIALS; do
	eval "value=\${$required}"
	if [ -z "${value}" ]; then
		echo "missing argument for ${required}" >&2
		usage >&2
		exit 2
	fi
done

CREATOR_UID=${CREATOR_CREDENTIALS%%:*}
[ -n "${LOG_FILE}" ] || LOG_FILE="./guest-parity-$(date -u +%Y%m%dT%H%M%SZ).log"
WORK_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t findling-guest-parity)
: > "${LOG_FILE}"

# A per run throwaway password. Sixteen bytes out of the kernel where openssl is
# missing, which is the same fallback register-exapp.sh uses.
if command -v openssl >/dev/null 2>&1; then
	GUEST_PASSWORD=$(openssl rand -hex 16)
else
	GUEST_PASSWORD=$(od -vAn -N16 -tx1 /dev/urandom | tr -d ' \n')
fi

# ---------------------------------------------------------------------------
# Protocol. German, because a person reads it, and a run without a file is a
# memory rather than a result.
# ---------------------------------------------------------------------------
stamp() { date -u +%Y-%m-%dT%H:%M:%SZ; }
log() { printf '%s %s\n' "$(stamp)" "$*" | tee -a "${LOG_FILE}"; }
finding() { log "BEFUND: $*"; }
die() { finding "$*"; log "Der Lauf wurde abgebrochen."; exit 1; }

# EXEC_PREFIX is expanded unquoted on purpose: it is a command prefix of several
# words, and this is the one place in this script where word splitting is meant.
occ() { $EXEC_PREFIX php occ "$@"; }

# occ with the throwaway password in the environment of the instance side call.
# See the limit named in the header.
occ_with_password() { $EXEC_PREFIX env OC_PASS="${GUEST_PASSWORD}" php occ "$@"; }

# ---------------------------------------------------------------------------
# The two questions, in one function, so that the only thing that changes
# between the two calls is the provider id. A copy per provider is how two
# questions start to drift apart without anybody seeing it.
#
# The limit is sent on every call, and it is the same number the cap is raised
# to below.
# ---------------------------------------------------------------------------
ask() {  # $1 provider, $2 user, $3 password, $4 term, $5 output file
	curl -sfS -G -u "$2:$3" \
		-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		--data-urlencode "term=$4" \
		--data-urlencode "limit=${RESULT_LIMIT}" \
		"${INSTANCE_URL}/ocs/v2.php/search/providers/$1/search" -o "$5"
}

# The fileids of one answer, for the protocol and for nothing else.
#
# This is an extraction and not a comparison. The verdict of this script comes
# from parity_diff.py alone, and this line exists so that the protocol carries
# both sets in readable form instead of only a count. A narrow pattern rather
# than a JSON reader, because a reader here would be a second way of reading an
# answer whose one canonical reader already exists.
answer_ids() {  # $1 answer file
	grep -Eo '"fileId":[ ]*"?[0-9]+"?' "$1" 2>/dev/null | sed 's/[^0-9]//g' | tr '\n' ' '
}

FINDINGS=0

compare() {  # $1 scenario, $2 user, $3 password, $4 term, $5 expected minimum
	ask files "$2" "$3" "$4" "${WORK_DIR}/native-$1.json"
	ask findling "$2" "$3" "$4" "${WORK_DIR}/findling-$1.json"
	log "Szenario $1, Begriff $4, Konto $2"
	log "  fileids nativ:   $(answer_ids "${WORK_DIR}/native-$1.json")"
	log "  fileids Findling: $(answer_ids "${WORK_DIR}/findling-$1.json")"
	if python3 "${PARITY_DIFF}" \
		--scenario "$1" \
		--native "${WORK_DIR}/native-$1.json" \
		--findling "${WORK_DIR}/findling-$1.json" \
		--expect-min "$5" >>"${LOG_FILE}" 2>&1; then
		log "  Urteil: bestanden"
	else
		FINDINGS=$((FINDINGS + 1))
		finding "Szenario $1 hat den Vergleich nicht bestanden, die Meldung des Werkzeugs steht im Protokoll"
	fi
}

# Waits for an empty work stock, with a running line, and never sleeps on
# suspicion: the number it waits for is a fact out of the queue table of
# Nextcloud. Same shape as the drain of the CI job.
drain() {  # $1 seconds until the deadline
	deadline=$(( $(date +%s) + $1 ))
	while :; do
		open=$(occ findling:index | awk '
			$1 == "scheduled" { scheduled = $2 }
			/^  handed to the worker/ { running = $NF }
			END { print (scheduled + 0) + (running + 0) }')
		log "Warteschlange: offen=${open}"
		if [ "${open}" -eq 0 ]; then
			break
		fi
		if [ "$(date +%s)" -ge "${deadline}" ]; then
			die "Der Arbeitsvorrat war nach $1 Sekunden nicht leer"
		fi
		sleep 5
	done
	# The index is committed in batches, so the last commit may be a moment
	# behind an empty queue.
	sleep 5
}

# ---------------------------------------------------------------------------
# Cleanup. It runs on every way out, because an aborted probe would otherwise
# leave a guest account standing on the very instance somebody is about to walk
# through by hand, and it would leave the instance with a raised result cap.
# ---------------------------------------------------------------------------
GUEST_CREATED=0
SHARE_ID=""
FILES_CREATED=0
CAP_TOUCHED=0
OLD_CAP=""

cleanup() {
	status=$?
	set +e
	if [ "${KEEP}" -eq 1 ]; then
		log "Aufraeumen: --keep war gesetzt, Gastkonto und Freigabe bleiben stehen"
	else
		if [ -n "${SHARE_ID}" ]; then
			curl -s -u "${CREATOR_CREDENTIALS}" -X DELETE \
				-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
				"${INSTANCE_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares/${SHARE_ID}" >/dev/null 2>&1
			log "Aufraeumen: Freigabe ${SHARE_ID} entfernt"
		fi
		if [ "${GUEST_CREATED}" -eq 1 ]; then
			occ user:delete "${GUEST_UID}" >/dev/null 2>&1
			log "Aufraeumen: Gastkonto ${GUEST_UID} entfernt"
		fi
		if [ "${FILES_CREATED}" -eq 1 ]; then
			for name in "${MARKER_SHARED}-1.txt" "${MARKER_PRIVATE}-1.txt"; do
				curl -s -u "${CREATOR_CREDENTIALS}" -X DELETE \
					"${INSTANCE_URL}/remote.php/dav/files/${CREATOR_UID}/${name}" >/dev/null 2>&1
			done
			log "Aufraeumen: die beiden Markerdateien entfernt"
		fi
	fi
	# The cap is instance state and is put back in every case, including --keep.
	if [ "${CAP_TOUCHED}" -eq 1 ]; then
		if [ -n "${OLD_CAP}" ]; then
			occ config:app:set core unified_search_max_results_per_request --value="${OLD_CAP}" >/dev/null 2>&1
			log "Aufraeumen: Trefferdeckel wieder auf ${OLD_CAP}"
		else
			occ config:app:delete core unified_search_max_results_per_request >/dev/null 2>&1
			log "Aufraeumen: Trefferdeckel wieder ohne gesetzten Wert"
		fi
	fi
	rm -rf "${WORK_DIR}"
	log "Das Protokoll dieses Laufs ist ${LOG_FILE}"
	exit "${status}"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# ---------------------------------------------------------------------------
# Step 0, the ground this run stands on
# ---------------------------------------------------------------------------
log "Gastnutzer-Probe zu D-22"
log "Instanz ${INSTANCE_URL}"
log "Instanzzugriff ${EXEC_PREFIX}"
log "Anlegendes Konto ${CREATOR_UID}, Gastkonto ${GUEST_UID}"

for tool in curl python3; do
	command -v "${tool}" >/dev/null 2>&1 || die "${tool} liegt nicht im Pfad, und diese Probe braucht es"
done
[ -f "${PARITY_DIFF}" ] || die "Der Richter ${PARITY_DIFF} fehlt, und ohne ihn faellt hier kein Urteil"

INSTANCE_VERSION=$(occ status --output=json 2>/dev/null | grep -Eo '"versionstring":"[^"]+"' | sed 's/.*:"//;s/"//' || true)
[ -n "${INSTANCE_VERSION}" ] || INSTANCE_VERSION="unbekannt"
log "Nextcloud-Fassung ${INSTANCE_VERSION}"

# The version of the foreign app is part of the result, because the probe is a
# snapshot and a snapshot without the version of the thing it looked at cannot
# be repeated. A8 of the research says as much: while the app has no release for
# the newest server, the probe runs on the one it does have and names it.
GUESTS_VERSION=$(occ app:list 2>/dev/null | grep -E '^  - guests:' | sed 's/.*: *//' || true)
if [ -z "${GUESTS_VERSION}" ]; then
	log "Die App fuer Gastkonten ist auf dieser Instanz nicht aktiv."
	log "Sie wird von dieser Probe bewusst nicht selbst nachinstalliert: eine fremde"
	log "App wird nicht von einem Testwerkzeug in eine Instanz gebracht. Der Weg ist"
	log "  occ app:install guests && occ app:enable guests"
	die "Ohne aktive App fuer Gastkonten gibt es keinen Gastnutzer und damit keine Probe"
fi
log "Fassung der App fuer Gastkonten: ${GUESTS_VERSION}"

# ---------------------------------------------------------------------------
# Step 1, the result cap. A step of its own with a read back, exactly as in the
# CI job: without it the server cuts both answers down and two truncated lists
# agree without saying anything.
# ---------------------------------------------------------------------------
OLD_CAP=$(occ config:app:get core unified_search_max_results_per_request 2>/dev/null | tr -d ' \r\n' || true)
log "Trefferdeckel vor der Probe: ${OLD_CAP:-nicht gesetzt}"
CAP_TOUCHED=1
occ config:app:set core unified_search_max_results_per_request --value="${RESULT_LIMIT}" --type=integer >/dev/null 2>&1 \
	|| occ config:app:set core unified_search_max_results_per_request --value="${RESULT_LIMIT}" >/dev/null
CAP_NOW=$(occ config:app:get core unified_search_max_results_per_request | tr -d ' \r\n')
log "Trefferdeckel jetzt: ${CAP_NOW}"
[ "${CAP_NOW}" = "${RESULT_LIMIT}" ] \
	|| die "Der Trefferdeckel steht auf ${CAP_NOW} statt auf ${RESULT_LIMIT}, jeder Vergleich unten waere gekuerzt"

# ---------------------------------------------------------------------------
# Step 2, the guest
# ---------------------------------------------------------------------------
occ_with_password guests:add --uid "${GUEST_UID}" --password-from-env "${CREATOR_UID}" "${GUEST_MAIL}" \
	|| die "Das Gastkonto konnte nicht angelegt werden"
GUEST_CREATED=1
log "Gastkonto ${GUEST_UID} angelegt, angelegt von ${CREATOR_UID}"
occ user:info "${GUEST_UID}" >>"${LOG_FILE}" 2>&1 || true

# ---------------------------------------------------------------------------
# Step 3, exactly one content for the guest, and one that is not for him
#
# Both markers stand in the name and in the content. The second file is what
# makes the security direction askable at all: without something the guest may
# not see, an extra hit has nothing to be extra about.
# ---------------------------------------------------------------------------
printf '%s Markerdatei der Gastprobe, im Namen und im Inhalt.\n' "${MARKER_SHARED}" \
	> "${WORK_DIR}/${MARKER_SHARED}-1.txt"
printf '%s Markerdatei der Gastprobe, im Namen und im Inhalt.\n' "${MARKER_PRIVATE}" \
	> "${WORK_DIR}/${MARKER_PRIVATE}-1.txt"
for name in "${MARKER_SHARED}-1.txt" "${MARKER_PRIVATE}-1.txt"; do
	curl -sfS -u "${CREATOR_CREDENTIALS}" -T "${WORK_DIR}/${name}" \
		"${INSTANCE_URL}/remote.php/dav/files/${CREATOR_UID}/${name}" \
		|| die "Die Datei ${name} konnte nicht hochgeladen werden"
done
FILES_CREATED=1
log "Zwei Markerdateien im Heimatverzeichnis von ${CREATOR_UID} angelegt"

# permissions=1 is read only, shareType=0 is a share with a single account, and
# a guest is an account. Without -f on purpose: a refused share answers with a
# body that says why, and -f would throw exactly that body away.
curl -s -u "${CREATOR_CREDENTIALS}" \
	-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
	-d "path=/${MARKER_SHARED}-1.txt" \
	-d 'shareType=0' \
	-d "shareWith=${GUEST_UID}" \
	-d 'permissions=1' \
	"${INSTANCE_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares" > "${WORK_DIR}/share.json"
grep -q '"statuscode":200' "${WORK_DIR}/share.json" \
	|| { cat "${WORK_DIR}/share.json" >> "${LOG_FILE}"; die "Die Freigabe an den Gast wurde nicht angelegt"; }
# A narrow pattern and the FIRST match: the id of the new share is the first id
# of the data object, and a greedy pattern would quietly report the last number
# of the answer instead.
SHARE_ID=$(grep -Eo '"id":[ ]*"?[0-9]+"?' "${WORK_DIR}/share.json" | head -n 1 | sed 's/[^0-9]//g')
[ -n "${SHARE_ID}" ] || die "Die Kennung der Freigabe war nicht lesbar"
log "Freigabe ${SHARE_ID} auf ${MARKER_SHARED}-1.txt an ${GUEST_UID}, nur lesend"

# ---------------------------------------------------------------------------
# Step 4, the crawl
#
# The access list of a file is written while the file is indexed, which is why
# the share above is created before this step and not after it. The crawl is
# driven explicitly and the work stock is waited for, because a probe that
# compared before the index knew the files would report a missing hit that says
# nothing about permissions.
# ---------------------------------------------------------------------------
occ files:scan --all >>"${LOG_FILE}" 2>&1 || true
occ findling:index --restart --no-interaction >>"${LOG_FILE}" 2>&1
occ background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once >>"${LOG_FILE}" 2>&1
occ background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop_after "${CRAWL_SECONDS}" \
	>>"${LOG_FILE}" 2>&1
drain "${DRAIN_TIMEOUT}"

# ---------------------------------------------------------------------------
# Step 5, the three questions
#
# One statement needs all three. The first alone would also be satisfied by an
# instance that shows everything to everybody, the second alone by a search that
# stopped working, and the third is what keeps the second honest.
# ---------------------------------------------------------------------------
compare guest-received-share "${GUEST_UID}" "${GUEST_PASSWORD}" "${MARKER_SHARED}" 1
compare guest-denied "${GUEST_UID}" "${GUEST_PASSWORD}" "${MARKER_PRIVATE}" 0
compare owner-still-finds "${CREATOR_UID}" "${CREATOR_CREDENTIALS#*:}" "${MARKER_PRIVATE}" 1

# ---------------------------------------------------------------------------
# Step 6, the verdict
# ---------------------------------------------------------------------------
log "Instanz ${INSTANCE_VERSION}, App fuer Gastkonten ${GUESTS_VERSION}, Gastkonto ${GUEST_UID}"
if [ "${FINDINGS}" -eq 0 ]; then
	log "Ergebnis: bestanden. Der Gast findet genau seinen einen freigegebenen Inhalt,"
	log "in beiden Providern dieselbe Menge, und den fremden Marker in keinem von beiden."
	log "Was diese Probe NICHT belegt: sie ist eine Momentaufnahme und kein Dauergate,"
	log "und sie gilt fuer die oben genannte Fassung der App fuer Gastkonten."
	exit 0
fi
log "Ergebnis: NICHT bestanden, ${FINDINGS} Befund(e). Ein Befund wird nicht durch eine"
log "angepasste Erwartung geheilt: fehlt ein Treffer, sieht der Gast zu wenig; kommt einer"
log "hinzu, sieht er zu viel, und das ist ein Sicherheitsbefund."
exit 1
