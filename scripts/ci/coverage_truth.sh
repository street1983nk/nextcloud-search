#!/usr/bin/env bash
# The independent truth of the coverage end to end proof (plan 43-07, D-43-08).
#
# Sourced by scripts/ci/coverage_e2e.sh and never run on its own. Everything in
# here is written against the two things the product does not own: the Samba
# file system on the runner and the database of Nextcloud. It reads the state
# database of the container only for the list of file ids and their verdicts,
# and it resolves every id through oc_filecache (internal path) and oc_storages
# (share out of the storage id string), in shell and SQL. No line of Findling
# code runs here and the reader path the container stores is never read, so a
# wrong key in the product cannot hide behind the same wrong key in the proof
# (owner rule "Gegenprobe nie mit dem Muster der Umsetzung", T-43-20).
#
# Keys. Every document is one line "<space>\t<internal path>": the space of a
# share is "smb:<share>", the space of any other storage is its storage id
# string (home::alice, local::/srv/lokal/). One file on two shares is two
# lines, one file seen through two mounts of the same share is one line.
#
# Expected by the caller: NC_DB (the sqlite database of Nextcloud), STATE_DB
# (the state database of the container), WORK (scratch), NC_URL, and the
# helpers fail, password_of. Nothing here prints a file content.

# The fixed type list of this proof. It is deliberately not the allowlist of
# Findling: the corpus of the harness only uses these two kinds of document,
# and every other file of the corpus (.bin) is a type nobody reads.
TRUTH_TYPES_REGEX='\.(txt|png)$'

# -- snapshots ------------------------------------------------------------------

# snapshot_dbs <label>: consistent copies of both databases, through the
# online backup of sqlite3, so neither a WAL nor a writer in the middle of a
# transaction can tear the reading. Prints nothing; sets SNAP_NC and SNAP_ST.
snapshot_dbs() {
  SNAP_NC="${WORK}/snap-$1-nc.db"
  SNAP_ST="${WORK}/snap-$1-state.db"
  rm -f "${SNAP_NC}" "${SNAP_ST}"
  sqlite3 "${NC_DB}" ".backup '${SNAP_NC}'" || fail "the Nextcloud database could not be copied"
  sqlite3 "${STATE_DB}" ".backup '${SNAP_ST}'" || fail "the state database could not be copied"
}

# sql <query>: one query over the Nextcloud snapshot with the state snapshot
# attached as st. Tab separated, no header.
sql() {
  sqlite3 -readonly -separator $'\t' "${SNAP_NC}" "ATTACH DATABASE '${SNAP_ST}' AS st; $1"
}

# space_of: storage id string to document space, on stdin, "<id>\t<path>".
# An SMB storage id reads smb::<user>@<host>//<share>/<root>, so the share is
# the text between the double slash and the next slash.
space_of() {
  sed -E 's#^smb::[^@]*@[^/]*//([^/]+)/[^\t]*\t#smb:\1\t#'
}

# -- numerator ------------------------------------------------------------------

# truth_numerator_list: every searchable document, one key per line, sorted
# and unique. Living indexed rows of the container, resolved through the file
# cache, on a storage that is in oc_mounts. Needs a fresh snapshot_dbs.
truth_numerator_list() {
  sql "SELECT s.id, fc.path
         FROM st.files AS sf
         JOIN oc_filecache AS fc ON fc.fileid = sf.file_id
         JOIN oc_storages AS s ON s.numeric_id = fc.storage
        WHERE sf.deleted_at IS NULL
          AND sf.state = 'indexed'
          AND fc.storage IN (SELECT storage_id FROM oc_mounts);" \
    | space_of | sort -u
}

# -- denominator ----------------------------------------------------------------

# truth_denominator_list "<share>:<user> <user>;<share>:<user> ..." "<home user> ...":
# the union of what the still mounted users see on each share, read with the
# rights of each user on the Samba server itself (sudo -u <user> find), plus
# the files of every mounted home, filtered by the fixed type list. A file
# whose content is locked is listed by find all the same, so unreadable files
# stay in (D-43-11), and a file locked for one user only counts once (N1).
truth_denominator_list() {
  local plan="$1" homes="$2" entry share users user
  {
    IFS=';' read -r -a entries <<< "${plan}"
    for entry in "${entries[@]}"; do
      share="${entry%%:*}"
      users="${entry#*:}"
      for user in ${users}; do
        # find returns non-zero for every directory the user may not enter;
        # that is the point, not an error.
        sudo -u "${user}" find "/srv/${share}" -type f 2> /dev/null \
          | sed -E "s#^/srv/${share}/#smb:${share}\t#" || true
      done
    done
    for user in ${homes}; do
      if [ -d "${NC_DATA}/${user}/files" ]; then
        (cd "${NC_DATA}/${user}" && find files -type f) | sed -E "s#^#home::${user}\t#"
      fi
    done
  } | grep -E "${TRUTH_TYPES_REGEX}" | sort -u
}

# truth_not_readable <list file of "space\tpath"> <denominator list file>:
# the unreadable files of the own list that are still in the denominator.
# Only the files locked for every user belong in it; the file locked for one
# user only is NOT in the list file (N1).
truth_not_readable() {
  sort -u "$1" | comm -12 - "$2" | wc -l
}

# -- the denominator of state A ---------------------------------------------------

# expected_denominator_phase_a: the denominator of the per document count
# while the crawl is unfinished or the queue is busy (D-43-11), rewritten in
# SQL from its definition and not from the PHP code:
#
#   denominator = sum over share groups and single storages of
#                 max(PHP part, judged documents + PHP only documents)
#
#   PHP part:     files_seen - over_cap - excluded - refused by type of the
#                 representative, the member with the most files_seen
#                 (finished first, then the lower id), never below nought.
#   judged:       distinct internal paths of living container rows with a
#                 verdict that is a document (not mime_not_allowed, excluded,
#                 gone, unreadable); a row the file cache cannot resolve counts
#                 on its own. In a single storage every row counts.
#                 unreadable is left out since D-43-16 (plan 43-18): a file the
#                 gateway refused with 422 is judged skipped/unreadable by the
#                 container and acknowledged, and the PHP side counts it out of
#                 oc_findling_file_state (PHP only below), not the container.
#                 A 1.6.2 container never writes that pair, so the expectation
#                 of the variant v1.6.2 does not move.
#   PHP only:     verdicts only Nextcloud writes (skipped/unreadable,
#                 failed/repeatedly_stuck, skipped/gone) on a file that still
#                 has a file cache row; in a group distinct by internal path and
#                 without a path that another member holds without such a
#                 verdict (N1).
#
# A group is every SMB storage id with the user taken out, mounted at least
# twice. Mounted is oc_mounts. The phase A figure cannot be known from the
# outside any other way, because during a crawl neither the file system nor
# the file cache says which files the crawl has seen yet; this is the one
# place where the proof follows the rule of the product, and it follows the
# rule as written in 43-CONTEXT.md, not the code.
expected_denominator_phase_a() {
  sql "
WITH mounted(sid) AS (SELECT DISTINCT storage_id FROM oc_mounts),
     ids(sid, txt) AS (SELECT numeric_id, id FROM oc_storages WHERE numeric_id IN (SELECT sid FROM mounted)),
     keyed(sid, gkey) AS (
       SELECT sid, CASE WHEN txt LIKE 'smb::%' AND instr(txt, '@') > 0
                        THEN 'smb::' || substr(txt, instr(txt, '@') + 1) END
         FROM ids),
     grouped(gkey) AS (SELECT gkey FROM keyed WHERE gkey IS NOT NULL GROUP BY gkey HAVING COUNT(*) >= 2),
     part(sid, pkey) AS (
       SELECT m.sid,
              COALESCE((SELECT k.gkey FROM keyed AS k WHERE k.sid = m.sid AND k.gkey IN (SELECT gkey FROM grouped)),
                       'single:' || m.sid)
         FROM mounted AS m),
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
       SELECT p.pkey, sf.file_id, fc.path
         FROM st.files AS sf
         JOIN part AS p ON p.sid = sf.storage_id
         LEFT JOIN oc_filecache AS fc ON fc.fileid = sf.file_id
        WHERE sf.deleted_at IS NULL
          AND NOT (sf.state = 'skipped' AND sf.reason IN ('mime_not_allowed', 'excluded', 'gone', 'unreadable'))),
     judged(pkey, n) AS (
       SELECT pkey, COUNT(DISTINCT CASE WHEN pkey LIKE 'single:%' OR path IS NULL
                                        THEN 'id:' || file_id ELSE 'p:' || path END)
         FROM judged_rows GROUP BY pkey),
     php_only AS (
       SELECT p.pkey, fc.fileid, fc.path
         FROM oc_findling_file_state AS r
         JOIN oc_filecache AS fc ON fc.fileid = r.file_id
         JOIN part AS p ON p.sid = fc.storage
        WHERE (r.state = 'skipped' AND r.reason IN ('unreadable', 'gone'))
           OR (r.state = 'failed' AND r.reason = 'repeatedly_stuck')),
     php_only_kept AS (
       SELECT o.* FROM php_only AS o
        WHERE o.pkey LIKE 'single:%'
           OR NOT EXISTS (
                SELECT 1 FROM oc_filecache AS other JOIN part AS q ON q.sid = other.storage AND q.pkey = o.pkey
                 WHERE other.path = o.path
                   AND other.fileid NOT IN (SELECT fileid FROM php_only))),
     php_only_n(pkey, n) AS (
       SELECT pkey, CASE WHEN pkey LIKE 'single:%' THEN COUNT(*) ELSE COUNT(DISTINCT path) END
         FROM php_only_kept GROUP BY pkey)
SELECT COALESCE(SUM(MAX(COALESCE(a.n, 0), COALESCE(j.n, 0) + COALESCE(o.n, 0))), 0)
  FROM (SELECT DISTINCT pkey FROM part) AS k
  LEFT JOIN php_part AS a ON a.pkey = k.pkey
  LEFT JOIN judged AS j ON j.pkey = k.pkey
  LEFT JOIN php_only_n AS o ON o.pkey = k.pkey;"
}

# -- the reshare case (A1, N2, D-43-14) -------------------------------------------

# a1_rows_checked <internal path> ...: for every file of the reshared folder,
# whether the state database holds two living rows on two storages under two
# different reader paths and with one and the same key. The key is computed
# here from the internal path (printf | sha256sum), not read from the product.
# Prints the number of files for which that holds.
a1_rows_checked() {
  local checked=0 internal key pairs
  for internal in "$@"; do
    key=$(printf '%s' "${internal}" | sha256sum | cut -d' ' -f1)
    pairs=$(sql "SELECT COUNT(DISTINCT r.storage_id) || ' ' || COUNT(DISTINCT r.path)
                   FROM st.files AS r
                  WHERE r.deleted_at IS NULL AND r.doc_key = '${key}';")
    if [ "${pairs%% *}" -ge 2 ] && [ "${pairs##* }" -ge 2 ]; then
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
        --data-urlencode "term=${word}" \
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
