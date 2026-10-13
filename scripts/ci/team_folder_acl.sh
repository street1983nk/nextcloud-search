#!/usr/bin/env bash
# Live regression test of issue #14, second round: a Team Folder file whose
# groupfolders ACL grants the members +read but -share has to be claimed,
# indexed, found by a member and diagnosed by the admin, over HTTP.
#
# Why HTTP and not occ: groupfolders builds a member's mount with in_share=true
# whenever the request is not a CLI run and the active user is somebody else,
# and in_share raises the ACL minimum from READ to READ plus SHARE. occ runs
# with OC::$CLI=true and never sets in_share, so a test driven through occ
# stays green with the bug. Every step that matters here is an HTTP request:
# the WebDAV upload, the ExApp claim it triggers, the unified search and the
# admin diagnosis.
#
# The same script runs in CI and against the local HaRP harness:
#
#   CI:      NC_URL=http://localhost:8080 OCC=./occ CRAWL=1 \
#            ADMIN_USER=admin ADMIN_PASS=password scripts/ci/team_folder_acl.sh
#   harness: NC_URL=http://localhost:8096 \
#            OCC="docker exec -e OC_PASS -u www-data -w /var/www/html findling-harp-nextcloud php occ" \
#            ADMIN_USER=admin ADMIN_PASS="$(cat .dev/probe-live/adminpass)" TAG=green \
#            scripts/ci/team_folder_acl.sh
#
# The -e OC_PASS in the harness prefix is required: user:add reads the password
# from that variable, and docker exec does not forward the environment itself.
#
# Inputs (environment):
#   NC_URL      base URL of the instance, without a trailing slash
#   OCC         command prefix that runs occ
#   ADMIN_USER  an administrator, for the diagnosis
#   ADMIN_PASS  the password of that administrator (never printed)
#   TAG         suffix of every object this run creates (default ci)
#   DEADLINE    seconds to wait for the verdicts (default 300)
#   CRAWL       1 = queue and run the crawl like the search-parity job
#   CLEANUP     1 = delete the users, groups and folders of this run at the end
#
# Exit code 0 means: both files were found by member 2 and by no outsider, and
# both the id and the path diagnosis found them. Anything else is a failure,
# reported as a ::error:: line together with the JSON answer behind it.

set -euo pipefail
shopt -s inherit_errexit

: "${NC_URL:?NC_URL is required}"
: "${OCC:?OCC is required}"
: "${ADMIN_USER:?ADMIN_USER is required}"
: "${ADMIN_PASS:?ADMIN_PASS is required}"
TAG="${TAG:-ci}"
DEADLINE="${DEADLINE:-300}"
CRAWL="${CRAWL:-0}"
CLEANUP="${CLEANUP:-0}"

WORK=$(mktemp -d)
MEMBERS=("acl-${TAG}-1" "acl-${TAG}-2" "acl-${TAG}-3")
OUTSIDER="outsider-${TAG}"
# Test only passwords of throwaway accounts, derived from the tag.
PASS="Findling-acl-${TAG}-2026-pw"
GROUPS_=("/a-${TAG}" "/u-${TAG}")
ACL_FOLDER="AclF-${TAG}"
PLAIN_FOLDER="NoAclF-${TAG}"
SUB="b_plus_m"
# Content only markers: they stand in the text and in no file name, so only an
# indexed text layer can match them.
MARKER_ACL="teamaclmarker${TAG}x"
MARKER_PLAIN="teamplainmarker${TAG}y"

occ() {
	# A SQLite instance with a background worker running beside this script
	# (the harness has one) answers a write now and then with "database is
	# locked". Such a command did nothing, so it is retried; any other failure
	# is passed on unchanged.
	#
	# MSYS_NO_PATHCONV only for occ: Git Bash on Windows rewrites arguments that
	# start with a slash ("/a-ci", "/") into Windows paths before docker sees
	# them, and set globally it would break /dev/null and the temp paths for
	# curl. No effect anywhere but Git Bash.
	local out rc try
	for try in 1 2 3 4 5; do
		rc=0
		# shellcheck disable=SC2086
		out=$(MSYS_NO_PATHCONV=1 ${OCC} "$@" 2>&1) || rc=$?
		if [ "${rc}" -ne 0 ] && [[ "${out}" == *"database is locked"* ]]; then
			sleep 2
			continue
		fi
		break
	done
	[ -z "${out}" ] || printf '%s\n' "${out}"
	return "${rc}"
}

log() {
	printf '%s\n' "$*"
}

folder_ids=()

cleanup() {
	if [ "${CLEANUP}" != "1" ]; then
		log "CLEANUP is not 1: users, groups and folders of tag ${TAG} stay on the instance"
		rm -rf "${WORK}"
		return
	fi
	for id in "${folder_ids[@]}"; do
		occ groupfolders:delete --force "${id}" >/dev/null 2>&1 || true
	done
	for user in "${MEMBERS[@]}" "${OUTSIDER}"; do
		occ user:delete "${user}" >/dev/null 2>&1 || true
	done
	for group in "${GROUPS_[@]}"; do
		occ group:delete "${group}" >/dev/null 2>&1 || true
	done
	log "removed the users, groups and folders of tag ${TAG}"
	rm -rf "${WORK}"
}
trap cleanup EXIT

dav() {  # $1 user, then curl arguments
	local user="$1"
	shift
	curl -sfS -u "${user}:${PASS}" "$@"
}

# -- 1. users and groups -----------------------------------------------------

# Idempotent, so a rerun with the same TAG after an interrupted run works: an
# account that is already there gets the password of this run instead.
for user in "${MEMBERS[@]}" "${OUTSIDER}"; do
	if occ user:info "${user}" >/dev/null 2>&1; then
		OC_PASS="${PASS}" occ user:resetpassword --password-from-env "${user}"
	else
		OC_PASS="${PASS}" occ user:add --password-from-env "${user}"
	fi
done
for group in "${GROUPS_[@]}"; do
	occ group:info "${group}" >/dev/null 2>&1 || occ group:add "${group}" >/dev/null
	for user in "${MEMBERS[@]}"; do
		occ group:adduser "${group}" "${user}"
	done
done
log "users ${MEMBERS[*]} and ${OUTSIDER}, groups ${GROUPS_[*]}"

# -- 2. and 3. the two team folders ------------------------------------------

log "--- groupfolders:permissions --help, for the syntax used below ---"
# Into a file first: a pipe into a reader that stops early would hand occ a
# broken pipe, and pipefail turns that into a failed run.
occ groupfolders:permissions --help > "${WORK}/permissions-help.txt"
sed -n '1,12p' "${WORK}/permissions-help.txt"

make_folder() {  # $1 mount point; prints the folder id
	local id
	id=$(occ groupfolders:create "$1" | tr -d '\r[:space:]')
	case "${id}" in
		''|*[!0-9]*)
			log "::error::groupfolders:create $1 answered '${id}' instead of a folder id" >&2
			exit 1
			;;
	esac
	for group in "${GROUPS_[@]}"; do
		occ groupfolders:group "${id}" "${group}" read write share delete >/dev/null
	done
	printf '%s' "${id}"
}

acl_id=$(make_folder "${ACL_FOLDER}")
folder_ids+=("${acl_id}")
plain_id=$(make_folder "${PLAIN_FOLDER}")
folder_ids+=("${plain_id}")

# Every account sets up its file system once, over WebDAV, before anything is
# uploaded or crawled. The access list a claim hands the container comes from
# the mount cache (QueueService::usersFor, getMountsForFileId), and a member
# gets a row there only when its file system is set up for the first time.
# Without this step only member 1, who uploads, stands in the list, the
# prefilter of the container never offers the file to member 2, and the search
# stays empty although the file is indexed (first CI runs of this job, 36620727811
# and 36622828171). The harness was green because there the claim followed the
# first search of member 2, which had registered the mount by then. The
# index-search-e2e job does the same with occ files:scan after its share.
for user in "${MEMBERS[@]}" "${OUTSIDER}"; do
	dav "${user}" -X PROPFIND -H 'Depth: 1' -o /dev/null \
		"${NC_URL}/remote.php/dav/files/${user}/"
done
log "file systems set up for ${MEMBERS[*]} and ${OUTSIDER}"

# The subfolder first, while the root still grants +create.
for folder in "${ACL_FOLDER}" "${PLAIN_FOLDER}"; do
	dav "${MEMBERS[0]}" -X MKCOL -o /dev/null \
		"${NC_URL}/remote.php/dav/files/${MEMBERS[0]}/${folder}/${SUB}"
done

occ groupfolders:permissions "${acl_id}" --enable
for group in "${GROUPS_[@]}"; do
	occ groupfolders:permissions "${acl_id}" --group="${group}" -- / +read -write -create -delete -share
	occ groupfolders:permissions "${acl_id}" --group="${group}" -- "${SUB}" +read +write +create +delete -share
done
log "--- the ACL of ${ACL_FOLDER} (id ${acl_id}) ---"
occ groupfolders:permissions "${acl_id}"

# -- 4. one file per folder, uploaded by member 1 ------------------------------

upload() {  # $1 folder, $2 marker; prints the file id
	local file="${WORK}/note-$2.txt"
	local url="${NC_URL}/remote.php/dav/files/${MEMBERS[0]}/$1/${SUB}/note.txt"
	printf 'Team folder ACL regression note. The marker is %s and nothing else.\n' "$2" > "${file}"
	dav "${MEMBERS[0]}" -T "${file}" -o /dev/null "${url}"
	dav "${MEMBERS[0]}" -X PROPFIND -H 'Depth: 0' \
		--data '<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><oc:fileid/></d:prop></d:propfind>' \
		"${url}" | sed -n 's|.*<oc:fileid>\([0-9]*\)</oc:fileid>.*|\1|p'
}

acl_file=$(upload "${ACL_FOLDER}" "${MARKER_ACL}")
plain_file=$(upload "${PLAIN_FOLDER}" "${MARKER_PLAIN}")
if [ -z "${acl_file}" ] || [ -z "${plain_file}" ]; then
	log "::error::the uploads did not report a file id (acl='${acl_file}', plain='${plain_file}')"
	exit 1
fi
log "uploaded: ACL file ${acl_file}, counter file ${plain_file}"

# -- 5. crawl, then poll -------------------------------------------------------

if [ "${CRAWL}" = "1" ]; then
	occ findling:index --restart --no-interaction
	timeout 60 ${OCC} background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once || true
	timeout 120 ${OCC} background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop_after 60 || true
	occ findling:index
fi

JAR="${WORK}/admin.jar"
admin_login() {
	# The login() pattern of the search-parity job: the form token, the POST
	# with the Origin header, then a fresh request token of the session.
	local token redirect
	rm -f "${JAR}"
	token=$(curl -sfS -c "${JAR}" "${NC_URL}/login" \
		| sed -n 's/.*data-requesttoken="\([^"]*\)".*/\1/p' | head -1)
	if [ -z "${token}" ]; then
		log "::error::the login form carried no request token"
		exit 1
	fi
	redirect=$(curl -sS -b "${JAR}" -c "${JAR}" -o /dev/null -w '%{redirect_url}' \
		-H "Origin: ${NC_URL}" \
		--data-urlencode "user=${ADMIN_USER}" \
		--data-urlencode "password=${ADMIN_PASS}" \
		--data-urlencode "requesttoken=${token}" \
		"${NC_URL}/login")
	case "${redirect}" in
		''|*/login|*/login\?*)
			log "::error::the admin login was refused"
			exit 1
			;;
	esac
	ADMIN_TOKEN=$(curl -sfS -b "${JAR}" -c "${JAR}" "${NC_URL}/index.php/csrftoken" | jq -r '.token' | tr -d '\r')
	if [ -z "${ADMIN_TOKEN}" ] || [ "${ADMIN_TOKEN}" = "null" ]; then
		log "::error::the admin session handed out no request token"
		exit 1
	fi
}

diagnose() {  # $1 reference; prints the JSON answer
	curl -sS -G -b "${JAR}" -c "${JAR}" \
		-H "requesttoken: ${ADMIN_TOKEN}" -H 'Accept: application/json' \
		--data-urlencode "ref=$1" \
		"${NC_URL}/index.php/apps/findling/admin/diagnose"
}

hits() {  # $1 user, $2 term; prints the number of findling entries
	curl -sfS -G -u "$1:${PASS}" \
		-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		--data-urlencode "term=$2" --data-urlencode 'limit=100' \
		"${NC_URL}/ocs/v2.php/search/providers/findling/search" \
		| jq -r '.ocs.data.entries | length' | tr -d '\r' || printf 'error'
}

admin_login

# One verdict per file: pending, ok or failed.
declare -A verdict=([acl]=pending [plain]=pending)
declare -A file_of=([acl]="${acl_file}" [plain]="${plain_file}")
declare -A marker_of=([acl]="${MARKER_ACL}" [plain]="${MARKER_PLAIN}")
declare -A answer_of=()

deadline=$(( $(date +%s) + DEADLINE ))
while :; do
	open=0
	for key in acl plain; do
		[ "${verdict[${key}]}" = "pending" ] || continue
		answer=$(diagnose "${file_of[${key}]}")
		answer_of[${key}]="${answer}"
		state=$(printf '%s' "${answer}" | jq -r '.state // ""' | tr -d '\r')
		reason=$(printf '%s' "${answer}" | jq -r '.reason // ""' | tr -d '\r')
		if [ "${state}" = "skipped" ] || [ "${reason}" = "unreadable" ]; then
			log "::error::${key} file ${file_of[${key}]}: verdict ${state}(${reason}), the member could not read it"
			log "${answer}"
			verdict[${key}]=failed
			continue
		fi
		count=$(hits "${MEMBERS[1]}" "${marker_of[${key}]}")
		if [ "${count}" = "1" ]; then
			log "${key} file ${file_of[${key}]}: state ${state}, member ${MEMBERS[1]} finds it (1 entry)"
			verdict[${key}]=ok
			continue
		fi
		open=$(( open + 1 ))
	done
	if [ "${open}" -eq 0 ]; then
		break
	fi
	if [ "$(date +%s)" -ge "${deadline}" ]; then
		for key in acl plain; do
			if [ "${verdict[${key}]}" = "pending" ]; then
				log "::error::${key} file ${file_of[${key}]}: no verdict and no hit within ${DEADLINE} seconds"
				log "${answer_of[${key}]:-}"
				log "the search of ${MEMBERS[1]} for ${marker_of[${key}]} answered:"
				curl -sS -G -u "${MEMBERS[1]}:${PASS}" -w '\nHTTP %{http_code}\n' \
					-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
					--data-urlencode "term=${marker_of[${key}]}" --data-urlencode 'limit=100' \
					"${NC_URL}/ocs/v2.php/search/providers/findling/search" || true
				verdict[${key}]=failed
			fi
		done
		break
	fi
	sleep 5
done

# -- 6. the boundary: an outsider finds nothing --------------------------------

for key in acl plain; do
	count=$(hits "${OUTSIDER}" "${marker_of[${key}]}")
	if [ "${count}" != "0" ]; then
		log "::error::${key}: the outsider ${OUTSIDER} finds ${count} entries, expected 0"
		verdict[${key}]=failed
	else
		log "${key}: the outsider finds nothing"
	fi
done

# -- 7. the admin path lookup --------------------------------------------------

for key in acl plain; do
	[ "${verdict[${key}]}" = "ok" ] || continue
	by_id=$(diagnose "${file_of[${key}]}")
	reference=$(printf '%s' "${by_id}" | jq -r '.reference // ""' | tr -d '\r')
	if [ -z "${reference}" ]; then
		log "::error::${key}: the id diagnosis carries no reference"
		log "${by_id}"
		verdict[${key}]=failed
		continue
	fi
	by_path=$(diagnose "${reference}")
	found=$(printf '%s' "${by_path}" | jq -r '.found' | tr -d '\r')
	path_id=$(printf '%s' "${by_path}" | jq -r '.fileId // 0' | tr -d '\r')
	if [ "${found}" != "true" ] || [ "${path_id}" != "${file_of[${key}]}" ]; then
		log "::error::${key}: the path diagnosis answered found=${found} fileId=${path_id}"
		log "${by_path}"
		verdict[${key}]=failed
	else
		log "${key}: the path diagnosis finds file ${path_id}"
	fi
done

# -- 8. the folder filter of the unified search (plan 32-06, assumption A1) ----
#
# The folder filter narrows the hits in PHP: SearchService resolves the folder
# in the tree of the asking user, drops candidates outside it cheaply over the
# raw coordinates (storage id plus internal path out of IFileAccess and the
# mount list) and rechecks the rest on the folder node. Assumption A1 of
# 32-RESEARCH is that those coordinates share one path space for a team folder
# (a jail on __groupfolders/<id>) and for a received share (the storage of the
# owner). If they did not, the preselection would drop the hits below exactly
# these two kinds of mount, and probes (a), (b) and (d) would be empty.
#
# Four probes, each with its own ::error:: line:
#   (a) the mount point of the plain team folder brings its file back
#   (b) the sub folder of the ACL team folder brings the ACL file back and not
#       the plain file, which lies in the other team folder
#   (c) a folder whose file is denied to member 2 by an ACL rule never brings
#       that file back to member 2; member 1 finds it there (the control)
#   (d) a folder member 1 shares with member 2 is filterable over its mount
#       point in the tree of member 2, read from the share answer, and a folder
#       of member 2's own does not bring the shared file back
#
# Every line logs the user, the folder, the expectation and the ids, never a
# file content.

MARKER_LOCKED="teamlockedmarker${TAG}z"
MARKER_SHARE="teamsharemarker${TAG}w"
LOCKED_DIR="locked"
SHARE_FOLDER="ShareF-${TAG}"
OWN_FOLDER="OwnF-${TAG}"
folder_failed=0

hits_in() {  # $1 user, $2 term, $3 folder; prints the sorted file ids of the findling entries
	curl -sfS -G -u "$1:${PASS}" \
		-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		--data-urlencode "term=$2" --data-urlencode 'limit=100' \
		--data-urlencode "folder=$3" \
		"${NC_URL}/ocs/v2.php/search/providers/findling/search" \
		| jq -r '[.ocs.data.entries[] | .attributes | objects | .fileId // empty | tonumber] | sort | map(tostring) | join(" ")' \
		| tr -d '\r' || printf 'error'
}

ids_of() {  # $1 user, $2 term; the same without a folder
	curl -sfS -G -u "$1:${PASS}" \
		-H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		--data-urlencode "term=$2" --data-urlencode 'limit=100' \
		"${NC_URL}/ocs/v2.php/search/providers/findling/search" \
		| jq -r '[.ocs.data.entries[] | .attributes | objects | .fileId // empty | tonumber] | sort | map(tostring) | join(" ")' \
		| tr -d '\r' || printf 'error'
}

fileid_of() {  # $1 user, $2 path below the files root; prints the file id
	dav "$1" -X PROPFIND -H 'Depth: 0' \
		--data '<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns"><d:prop><oc:fileid/></d:prop></d:propfind>' \
		"${NC_URL}/remote.php/dav/files/$1/$2" | sed -n 's|.*<oc:fileid>\([0-9]*\)</oc:fileid>.*|\1|p'
}

put_note() {  # $1 user, $2 path below the files root, $3 marker
	local file="${WORK}/note-$3.txt"
	printf 'Team folder ACL regression note. The marker is %s and nothing else.\n' "$3" > "${file}"
	dav "$1" -T "${file}" -o /dev/null "${NC_URL}/remote.php/dav/files/$1/$2"
}

expect_ids() {  # $1 probe, $2 user, $3 term, $4 folder, $5 expected ids ('' for none)
	local got
	got=$(hits_in "$2" "$3" "$4")
	if [ "${got}" = "$5" ]; then
		log "folder filter $1: user $2, folder $4, expected [$5], got [${got}]"
		return 0
	fi
	log "::error::folder filter $1: user $2, folder $4, expected [$5], got [${got}]"
	folder_failed=1
}

if [ "${verdict[acl]}" = "ok" ] && [ "${verdict[plain]}" = "ok" ]; then
	# The file for probe (c): uploaded by member 1 into a folder below SUB,
	# then denied to member 2 by a user rule on that folder. A deeper rule
	# overrides the +read of SUB, and no group rule stands on the same path,
	# where allow would win (groupfolders Rule::mergeRules).
	dav "${MEMBERS[0]}" -X MKCOL -o /dev/null \
		"${NC_URL}/remote.php/dav/files/${MEMBERS[0]}/${ACL_FOLDER}/${SUB}/${LOCKED_DIR}"
	put_note "${MEMBERS[0]}" "${ACL_FOLDER}/${SUB}/${LOCKED_DIR}/note.txt" "${MARKER_LOCKED}"
	locked_file=$(fileid_of "${MEMBERS[0]}" "${ACL_FOLDER}/${SUB}/${LOCKED_DIR}/note.txt")
	occ groupfolders:permissions "${acl_id}" --user="${MEMBERS[1]}" -- "${SUB}/${LOCKED_DIR}" -read
	# The lock measured rather than assumed: member 2 cannot see the file over
	# WebDAV, member 1 can.
	locked_code_2=$(curl -s -o /dev/null -w '%{http_code}' -u "${MEMBERS[1]}:${PASS}" -X PROPFIND -H 'Depth: 0' \
		"${NC_URL}/remote.php/dav/files/${MEMBERS[1]}/${ACL_FOLDER}/${SUB}/${LOCKED_DIR}/note.txt")
	locked_code_1=$(curl -s -o /dev/null -w '%{http_code}' -u "${MEMBERS[0]}:${PASS}" -X PROPFIND -H 'Depth: 0' \
		"${NC_URL}/remote.php/dav/files/${MEMBERS[0]}/${ACL_FOLDER}/${SUB}/${LOCKED_DIR}/note.txt")
	if [ "${locked_code_2}" != "404" ] || [ "${locked_code_1}" != "207" ]; then
		log "::error::folder filter (c): the ACL lock did not hold, PROPFIND answered ${locked_code_2} to ${MEMBERS[1]} and ${locked_code_1} to ${MEMBERS[0]} (expected 404 and 207)"
		folder_failed=1
	fi
	log "locked file ${locked_file}: PROPFIND ${locked_code_2} for ${MEMBERS[1]}, ${locked_code_1} for ${MEMBERS[0]}"

	# The share for probe (d): the folder first, shared, then the file of
	# member 2 set up, and only then the file uploaded. The access list a
	# claim hands the container comes from the mount cache, and member 2 gets
	# the share mount there when its file system is set up after the share
	# exists (the reason step 3 sets up every account first).
	dav "${MEMBERS[0]}" -X MKCOL -o /dev/null "${NC_URL}/remote.php/dav/files/${MEMBERS[0]}/${SHARE_FOLDER}"
	dav "${MEMBERS[1]}" -X MKCOL -o /dev/null "${NC_URL}/remote.php/dav/files/${MEMBERS[1]}/${OWN_FOLDER}"
	share_answer=$(dav "${MEMBERS[0]}" -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		--data-urlencode "path=/${SHARE_FOLDER}" --data-urlencode 'shareType=0' \
		--data-urlencode "shareWith=${MEMBERS[1]}" --data-urlencode 'permissions=1' \
		"${NC_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares")
	share_id=$(printf '%s' "${share_answer}" | jq -r '.ocs.data.id // ""' | tr -d '\r')
	if ! [[ "${share_id}" =~ ^[0-9]+$ ]]; then
		log "::error::folder filter (d): the share answer carries no id"
		log "${share_answer}"
		exit 1
	fi
	dav "${MEMBERS[1]}" -X PROPFIND -H 'Depth: 1' -o /dev/null "${NC_URL}/remote.php/dav/files/${MEMBERS[1]}/"
	received=$(dav "${MEMBERS[1]}" -G -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
		--data-urlencode 'shared_with_me=true' \
		"${NC_URL}/ocs/v2.php/apps/files_sharing/api/v1/shares")
	share_target=$(printf '%s' "${received}" | jq -r --arg id "${share_id}" \
		'[.ocs.data[] | select((.id | tostring) == $id) | .file_target][0] // ""' | tr -d '\r')
	if [[ "${share_target}" != /* ]]; then
		log "::error::folder filter (d): ${MEMBERS[1]} does not report share ${share_id} with a mount point"
		log "${received}"
		exit 1
	fi
	log "share ${share_id}: ${SHARE_FOLDER} of ${MEMBERS[0]} is mounted at ${share_target} for ${MEMBERS[1]}"
	put_note "${MEMBERS[0]}" "${SHARE_FOLDER}/note.txt" "${MARKER_SHARE}"
	share_file=$(fileid_of "${MEMBERS[0]}" "${SHARE_FOLDER}/note.txt")
	for pair in "locked=${locked_file}" "share=${share_file}"; do
		if ! [[ "${pair#*=}" =~ ^[0-9]+$ ]]; then
			log "::error::the upload of the ${pair%%=*} file reported no file id"
			exit 1
		fi
	done

	if [ "${CRAWL}" = "1" ]; then
		occ findling:index --restart --no-interaction
		timeout 60 ${OCC} background-job:worker 'OCA\Findling\BackgroundJobs\SchedulerJob' --once || true
		timeout 120 ${OCC} background-job:worker 'OCA\Findling\BackgroundJobs\StorageCrawlJob' --stop_after 60 || true
		occ findling:index
	fi

	# Both new files indexed before a folder is asked: member 1 finds the
	# locked file and member 2 the shared one, each without a folder.
	deadline=$(( $(date +%s) + DEADLINE ))
	while :; do
		got_locked=$(ids_of "${MEMBERS[0]}" "${MARKER_LOCKED}")
		got_share=$(ids_of "${MEMBERS[1]}" "${MARKER_SHARE}")
		if [ "${got_locked}" = "${locked_file}" ] && [ "${got_share}" = "${share_file}" ]; then
			log "indexed: ${MEMBERS[0]} finds the locked file, ${MEMBERS[1]} finds the shared file"
			break
		fi
		if [ "$(date +%s)" -ge "${deadline}" ]; then
			log "::error::within ${DEADLINE} seconds ${MEMBERS[0]} found [${got_locked}] for the locked file ${locked_file} and ${MEMBERS[1]} [${got_share}] for the shared file ${share_file}"
			exit 1
		fi
		sleep 5
	done

	# (a) the mount point of the plain team folder; the ACL folder as the
	# counter sample, because the plain file does not lie there.
	expect_ids "(a)" "${MEMBERS[1]}" "${MARKER_PLAIN}" "/${PLAIN_FOLDER}" "${plain_file}"
	expect_ids "(a) counter" "${MEMBERS[1]}" "${MARKER_PLAIN}" "/${ACL_FOLDER}" ""
	# (b) SUB inside the ACL team folder, and its mount point including SUB.
	expect_ids "(b)" "${MEMBERS[1]}" "${MARKER_ACL}" "/${ACL_FOLDER}/${SUB}" "${acl_file}"
	expect_ids "(b) mount point" "${MEMBERS[1]}" "${MARKER_ACL}" "/${ACL_FOLDER}" "${acl_file}"
	expect_ids "(b) outside" "${MEMBERS[1]}" "${MARKER_PLAIN}" "/${ACL_FOLDER}/${SUB}" ""
	# (c) the locked file, never for member 2, with any of the folders above
	# it; member 1 finds it in the same folder (the control).
	expect_ids "(c)" "${MEMBERS[1]}" "${MARKER_LOCKED}" "/${ACL_FOLDER}/${SUB}" ""
	expect_ids "(c) locked folder" "${MEMBERS[1]}" "${MARKER_LOCKED}" "/${ACL_FOLDER}/${SUB}/${LOCKED_DIR}" ""
	expect_ids "(c) control" "${MEMBERS[0]}" "${MARKER_LOCKED}" "/${ACL_FOLDER}/${SUB}" "${locked_file}"
	# (d) the received share over its mount point, and an own folder of
	# member 2 that does not hold it.
	expect_ids "(d)" "${MEMBERS[1]}" "${MARKER_SHARE}" "${share_target}" "${share_file}"
	expect_ids "(d) own folder" "${MEMBERS[1]}" "${MARKER_SHARE}" "/${OWN_FOLDER}" ""
	expect_ids "(d) outsider" "${OUTSIDER}" "${MARKER_SHARE}" "/${SHARE_FOLDER}" ""
else
	log "the folder filter probes did not run, because the verdicts above are not both ok"
	folder_failed=1
fi

log "verdicts: acl=${verdict[acl]} plain=${verdict[plain]} folder=$([ "${folder_failed}" = "0" ] && echo ok || echo failed)"
if [ "${verdict[acl]}" = "ok" ] && [ "${verdict[plain]}" = "ok" ] && [ "${folder_failed}" = "0" ]; then
	log "team folder ACL scenario passed"
	exit 0
fi
exit 1
