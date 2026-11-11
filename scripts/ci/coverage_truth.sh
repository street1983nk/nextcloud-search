#!/usr/bin/env bash
# The independent truth of the coverage end to end proof (plan 43-07, D-43-08),
# physical since plan 43-25.
#
# Sourced by scripts/ci/coverage_e2e.sh and never run on its own. Everything in
# here is written against the things the product does not own: the file system
# of the Samba host, what Samba itself says about its shares, the log the
# harness wrote when it created the mounts, and the mount and file cache tables
# of Nextcloud. It reads the state database of the container only for the list
# of file ids and their verdicts. No line of Findling code runs here.
#
# What a document is. One file on the Samba host, named by device and inode
# (stat, format %d:%i). Not a storage id, not a share name, not a path: the
# product builds its document key out of host, share, root and path, with
# rules for spelling and for roots, and a truth that computed "share in lower
# case plus root plus path" would be the same rule a second time and could not
# find a mistake in it (owner rule "Gegenprobe nie mit dem Muster der
# Umsetzung", T-43-20, T-43-76). So nothing in here folds a spelling, parses a
# storage id or knows an owner decision; the storage table of Nextcloud and the
# configuration tables of files_external are not read at all.
#
# How a file cache row finds its file, step by step:
#   1. oc_mounts says at which mount point a storage is mounted for a user.
#   2. The mount log of the harness (MOUNTS, one line per configuration as it
#      was created: mount point, share as written, root as written, users,
#      mechanism, login) says which share and root were typed in for that
#      mount point and which account logs in at the Samba server.
#   3. Samba says where that share lies: testparm prints the path of the
#      section, whatever the spelling of the name; for a section without a path
#      (homes) it is the home directory of the login, from getent passwd.
#   4. Server path = share path / root / internal path of the file cache row.
#   5. stat of that path gives device and inode.
# A home storage is the data directory of its user, a local storage its
# directory from the mount log.
#
# Expected by the caller: NC_DB, STATE_DB, NC_DATA, WORK (scratch), MOUNTS (the
# mount log), NC_URL, and the helpers fail, password_of. Nothing here prints a
# file content.

# The fixed type list of this proof. It is deliberately not the allowlist of
# Findling: the corpus of the harness only uses these two kinds of document,
# and every other file of the corpus (.bin) is a type nobody reads.
TRUTH_TYPES_REGEX='\.(txt|png)$'

# The expected difference between the figure shown and the physical truth, by
# hand. Two storages of the topology have an id of more than 64 characters,
# which Nextcloud stores as an md5, and credentials Nextcloud keeps encrypted
# (the global ones of the admin and the ones a user entered for this storage),
# so nothing outside the credentials store can tell which share they are. The
# product counts such a storage on its own (known limitation of 1.6.3). Each
# of the two is mounted on the folder sicherheit, which holds two text files,
# sicherheit-1.txt and sicherheit-2.txt, both readable by every account and
# both seen by the mounts with the root / as well. So each of the two storages
# shows 2 documents a second time: k = 2 storages x 2 files = 4, in the
# numerator and, by the same rule, in the denominator. Nothing else may differ.
EXPECTED_SEPARATE_K=4

# What a naive truth with the keys of 1.6.3-rc.1 counts too much in phase B
# (positive control 3). The naive key is the share as written plus the root as
# written as the space, and the path below the root. Indexed files of the
# share daten that the still mounted accounts see, 17 inodes:
#   gemeinsam 7 (daten-gemeinsam-1..3, gleich, Bericht, bericht, gesperrt-bob),
#   projekt 3, nur-alice 4, nur-bob 1, sicherheit 2.
# The naive spaces count them as
#   daten with root /            17 (alice and bob together)
#   Daten with root /            12 (bob: gemeinsam 6 without the file locked
#                                    for him, projekt 3, nur-bob 1, sicherheit 2)
#   daten with root sicherheit    2
#   daten with root projekt       3
# which is 34, 17 more than there are files. The two privat.txt of the homes
# share are two files in two home directories and one naive key (same share
# name, same path), one less. Every other space holds each file once.
# 17 - 1 = 16.
NAIVE_SURPLUS=16

# -- snapshots ------------------------------------------------------------------

# snapshot_dbs <label>: consistent copies of both databases, through the
# online backup of sqlite3, so neither a WAL nor a writer in the middle of a
# transaction can tear the reading. Prints nothing; sets SNAP_NC and SNAP_ST.
# The physical table of an older snapshot goes, truth_physical builds the next.
snapshot_dbs() {
  SNAP_NC="${WORK}/snap-$1-nc.db"
  SNAP_ST="${WORK}/snap-$1-state.db"
  rm -f "${SNAP_NC}" "${SNAP_ST}" "${WORK}/truth-phys.db"
  # Waits up to 10 s for a writer, like ncdb and statedb in coverage_e2e.sh.
  sqlite3 -cmd ".timeout 10000" "${NC_DB}" ".backup '${SNAP_NC}'" || fail "the Nextcloud database could not be copied"
  sqlite3 -cmd ".timeout 10000" "${STATE_DB}" ".backup '${SNAP_ST}'" || fail "the state database could not be copied"
}

# sql <query>: one query over the Nextcloud snapshot with the state snapshot
# attached as st and the physical table of truth_physical as ph. Tab
# separated, no header.
sql() {
  [ -f "${WORK}/truth-phys.db" ] || fail "truth_physical did not run for this snapshot" >&2
  sqlite3 -readonly -separator $'\t' "${SNAP_NC}" \
    "ATTACH DATABASE '${SNAP_ST}' AS st; ATTACH DATABASE '${WORK}/truth-phys.db' AS ph; $1"
}

# -- from a file cache row to a file ----------------------------------------------

# truth_share_path <share as written> <login>: where Samba keeps the share.
# testparm is asked with the name exactly as it was typed into the mount; a
# section without a path of its own is the home directory of the login.
truth_share_path() {
  local share="$1" login="$2" path
  path=$(testparm -s --section-name="${share}" --parameter-name=path 2> /dev/null) \
    || fail "testparm knows no section for a share of the mount log" >&2
  path=$(printf '%s\n' "${path}" | tail -n 1)
  if [ -z "${path}" ]; then
    path=$(getent passwd "${login}" | cut -d: -f6)
  fi
  [ -n "${path}" ] || fail "a share of the mount log has no path on the Samba host" >&2
  printf '%s' "${path%/}"
}

# truth_mount_table: the mount log, one line per user of a configuration:
# "<mount point in oc_mounts>\t<login>\t<server path of the root>\t<server path
# of the share>\t<share and root as written>". The fourth column is the tree
# the root lies in, the fifth the space of the naive truth.
truth_mount_table() {
  local point share root users login user who tree base below
  : > "${WORK}/truth-mounts.tsv"
  while IFS=$'\t' read -r point share root users _ login; do
    for user in ${users}; do
      who="${login}"
      [ "${who}" = "-" ] && who="${user}"
      if [ "${share}" = "-" ]; then
        # A local storage: the root is its directory.
        tree="${root%/}"
        base="${tree}"
      else
        tree=$(truth_share_path "${share}" "${who}") || exit 1
        below=$(printf '%s' "${root}" | sed -E 's#^/+##; s#/+$##')
        base="${tree}"
        [ -z "${below}" ] || base="${tree}/${below}"
      fi
      printf '/%s/files%s/\t%s\t%s\t%s\t%s|%s\n' "${user}" "${point}" "${who}" "${base}" "${tree}" "${share}" "${root}" \
        >> "${WORK}/truth-mounts.tsv"
    done
  done < "${MOUNTS}"
}

# insert_rows <table> [n]: tab separated lines on stdin to one INSERT per line
# in one transaction; the first n columns are numbers, the others text with
# the quote character doubled.
insert_rows() {
  awk -F'\t' -v table="$1" -v numeric="${2:-0}" -v q="'" '
    function text(value) { gsub(q, q q, value); return q value q }
    BEGIN { print "BEGIN;" }
    {
      line = ""
      for (i = 1; i <= NF; i++) {
        line = line (i > 1 ? "," : "") (i <= numeric ? $i + 0 : text($i))
      }
      print "INSERT INTO " table " VALUES(" line ");"
    }
    END { print "COMMIT;" }'
}

# truth_physical: builds ${WORK}/truth-phys.db for the current snapshot.
#   mount_roots  the mount table above
#   sroot        per mounted storage its server path, its tree and its naive
#                space; a storage mounted at '/<user>/' is the home of that
#                user in the data directory
#   phys         per file cache row of a mounted storage that is a file and
#                exists on the host: device:inode and server path
# A storage that is mounted and has no line in the mount log, or two different
# server paths, makes the run invalid: the truth would silently leave files
# out. The corpus must have no hard links, otherwise two names would be one
# document here and two for every reader.
truth_physical() {
  local phys="${WORK}/truth-phys.db" torn unmapped links tree
  [ -n "${SNAP_NC:-}" ] && [ -f "${SNAP_NC}" ] || fail "truth_physical needs a snapshot"
  truth_mount_table
  rm -f "${phys}"
  sqlite3 "${phys}" "CREATE TABLE mount_roots(mount_point TEXT, login TEXT, root TEXT, tree TEXT, space TEXT);
                     CREATE TABLE sroot(storage INTEGER PRIMARY KEY, root TEXT, tree TEXT, space TEXT);
                     CREATE TABLE phys(fileid INTEGER PRIMARY KEY, inode TEXT, spath TEXT);" \
    || fail "the physical table could not be created"
  insert_rows mount_roots < "${WORK}/truth-mounts.tsv" | sqlite3 "${phys}" \
    || fail "the mount table could not be stored"

  torn=$(sqlite3 "${SNAP_NC}" "ATTACH DATABASE '${phys}' AS ph;
    SELECT COUNT(*) FROM (
      SELECT m.storage_id FROM oc_mounts AS m JOIN ph.mount_roots AS r ON r.mount_point = m.mount_point
       GROUP BY m.storage_id HAVING COUNT(DISTINCT r.root) > 1);")
  [ "${torn}" = "0" ] || fail "${torn} storages have two server paths in the mount log, the run is invalid"
  sqlite3 "${SNAP_NC}" "ATTACH DATABASE '${phys}' AS ph;
    INSERT INTO ph.sroot
      SELECT m.storage_id, MIN(r.root), MIN(r.tree), MIN(r.space)
        FROM oc_mounts AS m JOIN ph.mount_roots AS r ON r.mount_point = m.mount_point
       GROUP BY m.storage_id;
    INSERT OR IGNORE INTO ph.sroot
      SELECT m.storage_id, '${NC_DATA}/' || MIN(m.user_id), '${NC_DATA}/' || MIN(m.user_id), '${NC_DATA}/' || MIN(m.user_id)
        FROM oc_mounts AS m
       WHERE m.mount_point = '/' || m.user_id || '/'
       GROUP BY m.storage_id;" \
    || fail "the storages could not be mapped to their server paths"
  unmapped=$(sqlite3 "${SNAP_NC}" "ATTACH DATABASE '${phys}' AS ph;
    SELECT COALESCE(group_concat(DISTINCT storage_id), '') FROM oc_mounts
     WHERE storage_id NOT IN (SELECT storage FROM ph.sroot);")
  [ -z "${unmapped}" ] || fail "mounted storages without a line in the mount log (${unmapped}), the run is invalid"

  sqlite3 -separator $'\t' "${SNAP_NC}" "ATTACH DATABASE '${phys}' AS ph;
    SELECT fc.fileid, s.root || '/' || fc.path
      FROM oc_filecache AS fc JOIN ph.sroot AS s ON s.storage = fc.storage
     WHERE fc.path <> ''
       AND fc.mimetype NOT IN (SELECT id FROM oc_mimetypes WHERE mimetype = 'httpd/unix-directory');" \
    > "${WORK}/truth-files.tsv"
  # stat as root: a folder closed to the runner still has files in it. A row
  # without a file on the host gets no line here and no inode.
  cut -f2 "${WORK}/truth-files.tsv" | sort -u > "${WORK}/truth-paths.txt"
  sudo xargs -r -d '\n' -a "${WORK}/truth-paths.txt" stat --printf='%d:%i\t%n\n' \
    > "${WORK}/truth-inodes.tsv" 2> /dev/null < /dev/null || true
  awk -F'\t' 'FILENAME == ARGV[1] { inode[$2] = $1; next }
              ($2 in inode) { print $1 "\t" inode[$2] "\t" $2 }' \
    "${WORK}/truth-inodes.tsv" "${WORK}/truth-files.tsv" \
    | insert_rows phys 1 | sqlite3 "${phys}" \
    || fail "the inodes could not be stored"

  links=0
  while IFS= read -r tree; do
    if sudo test -d "${tree}" < /dev/null; then
      links=$((links + $(sudo find "${tree}" -type f -links +1 2> /dev/null < /dev/null | wc -l)))
    fi
  done < <(sqlite3 "${phys}" "SELECT DISTINCT tree FROM sroot;")
  [ "${links}" = "0" ] || fail "the corpus has hard links, the run is invalid"
}

# -- numerator ------------------------------------------------------------------

# truth_numerator_list: every searchable document, "<device:inode>\t<server
# path>", one line per inode. Living indexed rows of the container, resolved
# through the file cache, on a storage that is in oc_mounts. A row whose file
# is not on the host keeps a key of its own, so it is counted and shows up as
# a document outside the denominator instead of vanishing. Needs truth_physical.
truth_numerator_list() {
  sql "SELECT COALESCE(p.inode, 'nofile:' || sf.file_id), COALESCE(p.spath, '-')
         FROM st.files AS sf
         JOIN oc_filecache AS fc ON fc.fileid = sf.file_id
         LEFT JOIN ph.phys AS p ON p.fileid = sf.file_id
        WHERE sf.deleted_at IS NULL
          AND sf.state = 'indexed'
          AND fc.storage IN (SELECT storage_id FROM oc_mounts);" \
    | sort -t $'\t' -k1,1 -u
}

# truth_numerator_naive: the same rows under the keys of 1.6.3-rc.1, "<share
# and root as written>\t<path below the root>" (positive control 3). Not a
# truth: it counts one file once per root and per spelling it is reached by.
truth_numerator_naive() {
  sql "SELECT DISTINCT s.space, fc.path
         FROM st.files AS sf
         JOIN oc_filecache AS fc ON fc.fileid = sf.file_id
         JOIN ph.sroot AS s ON s.storage = fc.storage
        WHERE sf.deleted_at IS NULL
          AND sf.state = 'indexed'
          AND fc.storage IN (SELECT storage_id FROM oc_mounts);" \
    | sort -u
}

# positive_control_naive <naive count> <physical count>: positive control 3.
# The naive count has to lie above the physical truth by exactly the planted
# number. If it does not, the topology holds no file that is reached through
# two roots or two spellings, or holds other ones than planned, and a green
# run would prove nothing about roots and spellings.
positive_control_naive() {
  if [ "$(($1 - $2))" != "${NAIVE_SURPLUS}" ]; then
    fail "a naive truth counts $1, the physical truth $2, planted are ${NAIVE_SURPLUS} more: the topology does not exercise roots and spellings, the run is invalid"
  fi
  echo "positive control 3: the naive truth counts $1, the physical truth $2, the planted ${NAIVE_SURPLUS} apart"
}

# with_separate_k <truth>: the figure the product has to show, see
# EXPECTED_SEPARATE_K.
with_separate_k() {
  echo "$(($1 + EXPECTED_SEPARATE_K))"
}

# -- denominator ----------------------------------------------------------------

# truth_denominator_list "<home user> ...": every file a mounted configuration
# reaches, "<device:inode>\t<server path>", one line per inode. Per mount of
# oc_mounts that the mount log knows, find runs below the server path of its
# root with the rights of the account that logs in there (sudo -u), so a
# folder that account may not enter stays out; then the files of every home,
# then the fixed type list. A file whose content is locked is listed by find
# all the same, so unreadable files stay in (D-43-11), and a file reached by
# three mounts is one inode and one line (N1 included).
truth_denominator_list() {
  local homes="$1" login root user
  {
    while IFS=$'\t' read -r login root <&3; do
      # find returns non-zero for every directory the account may not enter;
      # that is the point, not an error.
      sudo -u "${login}" find "${root}" -type f -exec stat --printf='%d:%i\t%n\n' {} + 2> /dev/null < /dev/null || true
    done 3< <(sql "SELECT DISTINCT r.login, r.root
                     FROM oc_mounts AS m JOIN ph.mount_roots AS r ON r.mount_point = m.mount_point;")
    for user in ${homes}; do
      if [ -d "${NC_DATA}/${user}/files" ]; then
        find "${NC_DATA}/${user}/files" -type f -exec stat --printf='%d:%i\t%n\n' {} + < /dev/null
      fi
    done
  } | { grep -E "${TRUTH_TYPES_REGEX}" || true; } | sort -t $'\t' -k1,1 -u
}

# truth_not_readable <list file of server paths> <denominator list file>:
# the unreadable files of the own list that are still in the denominator, by
# inode. Only the files locked for every user belong in the list; the file
# locked for one user only is NOT in it (N1).
truth_not_readable() {
  sort -u "$1" > "${WORK}/truth-locked.txt"
  { sudo xargs -r -d '\n' -a "${WORK}/truth-locked.txt" stat --printf='%d:%i\n' 2> /dev/null < /dev/null || true; } \
    | sort -u | comm -12 - <(cut -f1 "$2") | wc -l
}

# -- the denominator of state A ---------------------------------------------------

# expected_denominator_phase_a: the denominator of the per document count
# while the crawl is unfinished or the queue is busy (D-43-11), rewritten in
# SQL from its definition and not from the PHP code:
#
#   denominator = sum over the trees of
#                 max(PHP part, judged documents + PHP only documents)
#
#   tree:         the directory a share lies in on the Samba host (from
#                 testparm or the home directory, see truth_mount_table), the
#                 directory of a local storage, the data directory of a home.
#                 Every mounted storage belongs to the tree its root lies in.
#   document:     an inode. A row without a file on the host counts on its own.
#   PHP part:     files_seen - over_cap - excluded - refused by type of the
#                 representative, the storage of the tree with the most
#                 files_seen (finished first, then the lower id), never below
#                 nought.
#   judged:       distinct inodes of living container rows with a verdict that
#                 is a document (not mime_not_allowed, excluded, gone,
#                 unreadable). unreadable is left out since D-43-16 (plan
#                 43-18): a file the gateway refused with 422 is judged
#                 skipped/unreadable by the container and acknowledged, and
#                 the PHP side counts it out of oc_findling_file_state (PHP
#                 only below), not the container. A 1.6.2 container never
#                 writes that pair.
#   PHP only:     verdicts only Nextcloud writes (skipped/unreadable,
#                 failed/repeatedly_stuck, skipped/gone) on a file that still
#                 has a file cache row; distinct inodes, and without an inode
#                 that another row of the tree holds without such a verdict
#                 (N1: a file locked for one account that another one reads is
#                 one inode, and it is judged through the one who reads it).
#
# The phase A figure cannot be known from the outside any other way, because
# during a crawl neither the file system nor the file cache says which files
# the crawl has seen yet; this is the one place where the proof reads counters
# of the product (oc_findling_scan_stats), and it follows the rule as written
# in 43-CONTEXT.md, not the code. What a document is and which storages belong
# together it takes from the host, like everything else in here. The figure
# shown lies above it by EXPECTED_SEPARATE_K.
expected_denominator_phase_a() {
  sql "
WITH mounted(sid) AS (SELECT DISTINCT storage_id FROM oc_mounts),
     part(sid, pkey) AS (
       SELECT s.storage, s.tree FROM ph.sroot AS s WHERE s.storage IN (SELECT sid FROM mounted)),
     stats AS (
       SELECT p.pkey, p.sid,
              ss.files_seen AS seen, ss.over_cap AS cap, ss.excluded AS excl,
              CASE WHEN ss.finished_at IS NULL THEN 1 ELSE 0 END AS unfinished,
              (SELECT COUNT(*) FROM oc_findling_file_state AS r JOIN oc_filecache AS rf ON rf.fileid = r.file_id
                WHERE rf.storage = p.sid AND r.state = 'skipped' AND r.reason = 'mime_not_allowed') AS refused
         FROM part AS p JOIN oc_findling_scan_stats AS ss ON ss.storage_id = p.sid),
     ranked AS (
       SELECT pkey, MAX(0, seen - cap - excl - refused) AS php,
              ROW_NUMBER() OVER (PARTITION BY pkey ORDER BY seen DESC, unfinished ASC, sid ASC) AS rn
         FROM stats),
     php_part(pkey, n) AS (SELECT pkey, php FROM ranked WHERE rn = 1),
     judged_rows AS (
       SELECT p.pkey, COALESCE('i:' || x.inode, 'id:' || sf.file_id) AS doc
         FROM st.files AS sf
         JOIN part AS p ON p.sid = sf.storage_id
         LEFT JOIN ph.phys AS x ON x.fileid = sf.file_id
        WHERE sf.deleted_at IS NULL
          AND NOT (sf.state = 'skipped' AND sf.reason IN ('mime_not_allowed', 'excluded', 'gone', 'unreadable'))),
     judged(pkey, n) AS (SELECT pkey, COUNT(DISTINCT doc) FROM judged_rows GROUP BY pkey),
     php_only AS (
       SELECT p.pkey, fc.fileid, COALESCE('i:' || x.inode, 'id:' || fc.fileid) AS doc
         FROM oc_findling_file_state AS r
         JOIN oc_filecache AS fc ON fc.fileid = r.file_id
         JOIN part AS p ON p.sid = fc.storage
         LEFT JOIN ph.phys AS x ON x.fileid = fc.fileid
        WHERE (r.state = 'skipped' AND r.reason IN ('unreadable', 'gone'))
           OR (r.state = 'failed' AND r.reason = 'repeatedly_stuck')),
     php_only_kept AS (
       SELECT o.* FROM php_only AS o
        WHERE NOT EXISTS (
                SELECT 1 FROM ph.phys AS other
                  JOIN oc_filecache AS ofc ON ofc.fileid = other.fileid
                  JOIN part AS q ON q.sid = ofc.storage AND q.pkey = o.pkey
                 WHERE 'i:' || other.inode = o.doc
                   AND other.fileid NOT IN (SELECT fileid FROM php_only))),
     php_only_n(pkey, n) AS (SELECT pkey, COUNT(DISTINCT doc) FROM php_only_kept GROUP BY pkey)
SELECT COALESCE(SUM(MAX(COALESCE(a.n, 0), COALESCE(j.n, 0) + COALESCE(o.n, 0))), 0)
  FROM (SELECT DISTINCT pkey FROM part) AS k
  LEFT JOIN php_part AS a ON a.pkey = k.pkey
  LEFT JOIN judged AS j ON j.pkey = k.pkey
  LEFT JOIN php_only_n AS o ON o.pkey = k.pkey;"
}

# -- the reshare case (A1, N2, D-43-14) -------------------------------------------

# a1_rows_checked <server path> ...: for every file of the reshared folder,
# whether the state database holds living rows of that inode on at least two
# storages and all of them carry one and the same key, none without. Which key
# that is, is the business of the product; that the rows of one file agree on
# it is what a count per document needs. Prints the number of files for which
# that holds.
a1_rows_checked() {
  local checked=0 spath inode storages keys bare
  for spath in "$@"; do
    inode=$(sudo stat -c '%d:%i' "${spath}" 2> /dev/null < /dev/null || true)
    [ -n "${inode}" ] || continue
    IFS=$'\t' read -r storages keys bare < <(sql "
      SELECT COUNT(DISTINCT r.storage_id), COUNT(DISTINCT r.doc_key), COALESCE(SUM(r.doc_key IS NULL), 0)
        FROM st.files AS r JOIN ph.phys AS p ON p.fileid = r.file_id
       WHERE r.deleted_at IS NULL AND p.inode = '${inode}';")
    if [ "${storages:-0}" -ge 2 ] && [ "${keys:-0}" = "1" ] && [ "${bare:-1}" = "0" ]; then
      checked=$((checked + 1))
    fi
  done
  echo "${checked}"
}

# -- the search cross check (W4) ----------------------------------------------------

# search_crosscheck <words file "word\tfile name"> <user> ...: every unique word
# is asked through the unified search with the Findling provider, once per user
# that still exists; a word counts as found when one entry carries the file
# name the word was written into. Prints the number of words found and writes
# the missing ones to ${WORK}/crosscheck-missing.txt. For every missing name
# ${WORK}/crosscheck-raw.txt gets one line "<name>\t<short form>" with the
# answer for the first user: the number of entries and their titles (file
# names of the test topology, never content), or what came back instead of a
# result list. Nothing of it goes to stdout, the caller reads the count there.
# limit=25: without it the route answers SearchQuery::LIMIT_DEFAULT (5) entries,
# and 25 is the cap unified-search.max-results-per-request sets by default
# (core/Controller/UnifiedSearchController.php::search, stable34), so a rank
# below the fifth never counts as a miss.
search_crosscheck() {
  local words="$1" word name user first found=0
  shift
  first="${1:-}"
  : > "${WORK}/crosscheck-missing.txt"
  : > "${WORK}/crosscheck-raw.txt"
  while IFS=$'\t' read -r word name; do
    local hit=0
    rm -f "${WORK}/first-hit.json"
    for user in "$@"; do
      curl -s -G -u "${user}:$(password_of "${user}")" \
        -H 'OCS-APIRequest: true' -H 'Accept: application/json' \
        --data-urlencode "term=${word}" --data-urlencode "limit=25" \
        "${NC_URL}/ocs/v2.php/search/providers/findling/search" -o "${WORK}/hit.json" || true
      if [ "${user}" = "${first}" ]; then
        cp "${WORK}/hit.json" "${WORK}/first-hit.json" 2> /dev/null || true
      fi
      if jq -e --arg name "${name}" '[.ocs.data.entries[]? | select(.title == $name)] | length > 0' \
        "${WORK}/hit.json" > /dev/null 2>&1; then
        hit=1
        break
      fi
    done
    if [ "${hit}" = 1 ]; then
      found=$((found + 1))
    else
      printf '%s\n' "${name}" >> "${WORK}/crosscheck-missing.txt"
      printf '%s\t%s\n' "${name}" "$(crosscheck_short_form "${first}" "${WORK}/first-hit.json")" \
        >> "${WORK}/crosscheck-raw.txt"
    fi
  done < "${words}"
  echo "${found}"
}

# crosscheck_short_form <user> <answer file>: "<user>: <n> entries [titles]",
# or the OCS status and the first bytes when the answer is no result list.
crosscheck_short_form() {
  local user="$1" answer="$2" short
  if [ ! -s "${answer}" ]; then
    printf '%s: no answer' "${user}"
    return 0
  fi
  if short=$(jq -er '.ocs.data.entries | if type == "array" then "\(length) entries [\(map(.title // "?") | join(", "))]" else empty end' \
    "${answer}" 2> /dev/null); then
    printf '%s: %s' "${user}" "${short}"
    return 0
  fi
  printf '%s: no entry list, ocs status %s, %s' "${user}" \
    "$(jq -r '.ocs.meta.statuscode // "none"' "${answer}" 2> /dev/null || echo unparsable)" \
    "$(head -c 120 "${answer}" | tr -d '\r\n')"
}

# -- comparison --------------------------------------------------------------------

# compare <name> <expected> <shown>: returns 1 on any difference, and the
# caller turns that into the exit code. No tolerance anywhere.
compare() {
  local name="$1" expected="$2" shown="$3"
  if [ "${expected}" = "${shown}" ]; then
    echo "compare ${name}: expected ${expected}, shown ${shown}, equal"
    return 0
  fi
  echo "::warning::compare ${name}: expected ${expected}, shown ${shown}, different"
  return 1
}

# positive_control_compare <name> <expected> <shown>: the comparison must fail
# against an expectation moved by one, in this very run (positive control 1).
positive_control_compare() {
  local name="$1" expected="$2" shown="$3"
  if compare "${name} (positive control, expectation plus one)" "$((expected + 1))" "${shown}" > /dev/null; then
    fail "the comparison cannot fail, the run is invalid"
  fi
  echo "positive control 1 for ${name}: the comparison fails against ${expected} + 1, as it has to"
}

# positive_control_reference <truth numerator> <shown numerator> <truth
# denominator> <shown denominator>: positive control 2, the variant v1.6.2.
# The released 1.6.2 has to miss the truth on this topology in at least one of
# the two figures; if it hits both, the topology does not contain the cases
# 1.6.3 was built for, and a green 1.6.3 run would prove nothing.
positive_control_reference() {
  if [ "$1" = "$2" ] && [ "$3" = "$4" ]; then
    fail "the topology does not tell 1.6.2 and 1.6.3 apart, the run is invalid"
  fi
  echo "positive control 2: 1.6.2 shows ${2} of ${4}, the truth is ${1} of ${3}"
}
