---
phase: quick-260929-s7p
plan: 01
status: complete
subsystem: php-companion
tags: [issue-14, groupfolders, acl, permissions, admin-ui, ci]
requires: []
provides:
  - "ReaderContext: request scoped switch of the active user (setVolatileActiveUser) with restore in finally"
  - "queue reader choice, content gateway and admin path lookup resolve as the member"
  - "admin error list shows the file id and diagnoses by id"
  - "live HTTP regression test scripts/ci/team_folder_acl.sh + CI job team-folder-acl"
affects: [php/lib/Service/QueueService.php, php/lib/Controller/GatewayController.php, php/lib/Service/PathResolverService.php, php/templates/admin.php, php/js/admin.js]
tech-stack:
  added: []
  patterns: ["one owner file for identity switches, pinned by a source ratchet"]
key-files:
  created:
    - php/lib/Service/ReaderContext.php
    - php/tests/Unit/ReaderContextTest.php
    - scripts/ci/team_folder_acl.sh
  modified:
    - php/lib/Service/QueueService.php
    - php/lib/Controller/GatewayController.php
    - php/lib/Service/PathResolverService.php
    - php/tests/Unit/QueueServiceReaderTest.php
    - php/tests/Unit/QueueServiceTest.php
    - php/tests/Unit/GatewayControllerTest.php
    - php/tests/Unit/PathResolverServiceTest.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/*.js, php/l10n/*.json (16 files)
    - docs/l10n-french.md, docs/l10n-spanish.md, docs/l10n-italian.md, docs/l10n-dutch.md, docs/l10n-portuguese.md
    - backend/tests/test_php_acl_boundary.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - .github/workflows/integration.yml
decisions:
  - "Findling resolves a node for a member with that member as volatile active user (IUserSession::setVolatileActiveUser), restored in finally with the object getUser() returned before; setUser is never used"
  - "The gateway opens the stream after the restore, so read hooks see the same identity as before the fix"
  - "Unknown uid: no switch, the unchanged NoUserException / null path answers (no user enumeration)"
  - "Admin error list diagnoses by file id only; the path lookup is no longer used from the list"
  - "'%1$s (ID %2$s)' equals its key in every language and is argued as a G2 exception per language"
metrics:
  duration: "about 95 min"
  completed: 2026-09-29
---

# Quick 260929-s7p: Team Folder files are read as the member (issue #14) Summary

Team Folder files under a groupfolders ACL with +read and -share are now claimed, fetched and diagnosed as the member: a new `ReaderContext` sets the member as the volatile active user around the first mount setup and the lookup, so groupfolders no longer builds the mount with in_share=true (READ+SHARE minimum). The admin error list shows every file id and diagnoses by id. A live HTTP scenario is RED on the HaRP harness without the fix and GREEN with it.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | cb82c05b | fix(php): read team folder files as the member (issue #14) |
| 2 | ff1bf2fa | feat(admin): error list shows the file id and diagnoses by id (issue #14) |
| 3 | 0556d06d | test(ci): live team folder ACL scenario over HTTP (issue #14) |

All as street1983nk <k.cherif@outlook.de>, no trailers, nothing pushed.

## RED/GREEN on the HaRP harness (http://localhost:8096)

opcache: validate_timestamps On, revalidate_freq 60; after every code swap `apachectl -k graceful` in findling-harp-nextcloud (clears opcache).

- **RED** (QueueService.php, GatewayController.php, PathResolverService.php checked out from fd7a26a3, ReaderContext.php unused), TAG=red, exit 1:
  - `::error::acl file 1395: verdict skipped(unreadable), the member could not read it` (diagnose answer: state skipped, reason unreadable, label "Für die gefragten Nutzer nicht lesbar")
  - `plain file 1396: state queued, member acl-red-2 finds it (1 entry)`, outsider 0 for both, path diagnosis of 1396 found
  - `verdicts: acl=failed plain=ok`
- **GREEN** (fix restored with `git checkout --` of the three files), TAG=green, exit 0:
  - `acl file 1633: ... member acl-green-2 finds it (1 entry)`, `plain file 1634: ... finds it (1 entry)`
  - outsider finds nothing for both
  - `acl: the path diagnosis finds file 1633`, `plain: the path diagnosis finds file 1634`
  - `team folder ACL scenario passed`
- Admin page check after GREEN: error rows render as `Photos/Frog.jpg (ID 1691)` / `Datei existiert nicht mehr (ID 1294)`, no `data-findling-path` left.

## Gates

- php -l (in findling-harp-nextcloud): all 9 PHP files of Task 1 and templates/admin.php clean
- node --check php/js/admin.js clean
- ruff check, ruff format --check (183 files), pyright latest 0 errors, vulture 80 clean
- full pytest: **4133 passed, 25 skipped** (4130 before + 3 new switch ratchet tests)
- PHP tree hash pin re-measured: 84 files, 5f8f41ef2b29f921ccba5d4f7337c69c1586c2db894c0e8dab6a6c8c9337556c (only PHP lines touched)
- Dash scan (U+2014/U+2013) over all changed files: empty
- **PHPUnit has NOT run.** ReaderContextTest (5 cases) and the new ordering cases in QueueServiceReaderTest (3), GatewayControllerTest (2), PathResolverServiceTest (2) are written and lint clean; they run in CI (php.yml phpunit) on the next owner push. The new CI job team-folder-acl has not run either.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] groupfolders:group does not accept "create"**
- **Found during:** Task 3 (first RED attempt)
- **Issue:** The plan named `read write create delete share`; groupfolders 22.0.6 answers "Unable to parse permissions input". Accepted names: read, write, share, delete (write covers create).
- **Fix:** script uses `read write share delete`; ACL rules via `groupfolders:permissions <id> --group=<g> -- <path> +read ...` (syntax from `--help`, printed into the log).

**2. [Rule 3 - Blocking] Harness robustness of the script**
- SQLite "database is locked" (a long running `background-job:worker` of the harness sits beside the script): occ() retries a locked command up to 5 times.
- `MSYS_NO_PATHCONV=1` only for the occ calls (set globally it broke `-o /dev/null` and temp paths for the native curl in Git Bash, curl exit 23).
- Users and groups are created idempotently (rerun with the same TAG after an interrupted run), `inherit_errexit`, a non numeric folder id stops the run, the help output goes through a file (pipe plus pipefail aborted the run).

**3. [Rule 3 - Blocking] Catalogue gates in test_admin_ui_contract.py**
- Two new keys raised the de.json key count 289 -> 291 (constant and comment updated); "%1$s (ID %2$s)" equals its key and was added to `VALUES_THAT_MAY_EQUAL_THEIR_KEY` for de, es, it, nl, pt_PT, pt_BR, fr with a reason; the five language tables in docs/l10n-*.md got rows for both keys (the table gate requires it) plus one bullet in each G2 exception list. Existing count sentences in those docs were not rewritten (they were already behind since plan 26-05).
- `%s (in the trash bin)` stays in all catalogues: php/js/admin.js still uses it in the diagnosis card.

**4. [Plan wording] No git stash for RED**
- Instead of `git stash push -- php/lib` (stash is shared across worktrees and forbidden by the executor rules), the three pre-fix files were written from `git show fd7a26a3:<file>` and restored with `git checkout -- <file>`.

**5. Task 3 was not split**; it ran through, with the fixes above.

## Harness state

- Red and green objects removed by hand after the runs (users acl-red-*, acl-green-*, outsider-*, groups /a-red /u-red /a-green /u-green, team folders 4 to 13 of the attempts). groupfolders:list shows only 1 I14SlashAcl, 2 I14PlainAcl, 3 I14SlashNoAcl.
- Unchanged from the debug file: users i14u1..3, groups /a-test /u-test a-plain u-plain, folders 1 to 3, files 735-744 and 953-956 (953/954 keep their old skipped/unreadable state from before the fix; a re-upload or reindex would pick them up now).
- File state rows of the test files 1395, 1396, 1633, 1634 (deleted with their folders) may remain in oc_findling_file_state / the backend until the reconcile removes them.
- The harness PHP tree is HEAD (0556d06d, fix active); apache was reloaded twice (graceful). The admin.js change is served under the app version cache key `?v=`, a browser may need a hard reload.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat model (T-s7p-01 to T-s7p-08 mitigated or accepted as written).

## Self-Check: PASSED

- php/lib/Service/ReaderContext.php, php/tests/Unit/ReaderContextTest.php, scripts/ci/team_folder_acl.sh: present
- commits cb82c05b, ff1bf2fa, 0556d06d: present in git log
