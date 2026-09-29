---
phase: quick-260929-s7p
verified: 2026-09-29T21:40:00Z
status: human_needed
score: 5/5 must-have truths verified (code + live evidence); PHPUnit/CI job execution pending owner push
overrides_applied: 0
human_verification:
  - test: "Owner pushes the branch, watches php.yml (phpunit job) and integration.yml (team-folder-acl job) run green in GitHub Actions"
    expected: "phpunit job: ReaderContextTest (5 cases), QueueServiceReaderTest/GatewayControllerTest/PathResolverServiceTest ordering cases all pass on a real server checkout. team-folder-acl job: script exits 0, member 2 finds both markers, outsider finds 0, admin path diagnose finds both files."
    why_human: "PHPUnit needs a full nextcloud/server checkout with vendor-bin/phpunit (composer install), which only exists in CI, not on this machine or the HaRP harness container (no vendor/ dir there). The new CI job has never run in GitHub Actions (nothing pushed yet, per project rule 'main, never push'). SUMMARY.md's RED/GREEN claim is a local harness run that already happened before this verification and cannot be independently re-run here without disturbing live harness state under a RAM-constrained machine."
---

# Quick Task 260929-s7p: Issue #14 ACL ReaderContext Verification Report

**Task Goal:** Team Folder files with groupfolders ACL (-share) are readable for Findling again by reading as the member (ReaderContext with setVolatileActiveUser, restored in finally) in QueueService readerOf, GatewayController byte read, PathResolverService; searcher filtering unchanged; admin error list shows file id and diagnoses by id; PHPUnit + live HTTP CI test.

**Verified:** 2026-09-29T21:40:00Z
**Status:** human_needed
**Repo:** C:\Users\Student\nextcloud-search, main, HEAD 0556d06d, local only

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Previous user restored after every switch, incl. exceptions; switch is the one place | VERIFIED | `php/lib/Service/ReaderContext.php` L72-89: `try { return $work(); } finally { $this->userSession->setVolatileActiveUser($previous); }`. `ReaderContextTest::testAThrowingWorkStillRestoresThePreviousUser` asserts `$admin` is active again and the exception propagates. Boundary ratchet `test_php_acl_boundary.py` (32/32 passed locally) enforces `setVolatileActiveUser` appears only in `Service/ReaderContext.php`, exactly twice, with a `finally`, and fails a synthetic second caller (`test_a_second_switch_owner_is_reported`) and a missing-finally case. |
| 2 | Unknown user: no switch, identical answer (no enumeration) | VERIFIED | `ReaderContext::actAs` returns `$work()` unchanged when `userManager->get($uid)` is null (L78-81). `GatewayControllerTest::testAnUnknownUserStillGetsTheNotFoundBodyAndIsNotSwitchedTo` asserts `setVolatileActiveUser` is never called and the 404 body is unchanged. `ReaderContextTest::testAnUnknownUserIsNotSwitchedToAndTheWorkStillRuns` confirms the same at the unit level. |
| 3 | GatewayController: byte read (fopen) happens after the restore | VERIFIED | Code: `php/lib/Controller/GatewayController.php` L83-102, `fopen('r')` is outside/after `readerContext->actAs(...)`. Test proof: `GatewayControllerTest::testTheFolderAndTheLookupRunAsTheUserAndTheOpenAfterTheRestore` asserts the exact step order `[['folder','alice'],['lookup','alice'],['fopen', null]]` , fopen observes the *restored* (null) active user, not alice. |
| 4 | QueueService readerOf and PathResolverService resolve nodes as the member | VERIFIED | `QueueService.php` L960 wraps `userFolder()` + `SearchService::readableFile()` in `readerContext->actAs($userId, ...)`. `PathResolverService.php` L354 (`fileIdForUser`) and L464 (`fileIdOverMounts` loop) both wrap the `getUserFolder(uid)->get(...)` lookup the same way. `grep -c readerContext->actAs`: QueueService=1, GatewayController=1, PathResolverService=2, matching the plan's key_links. |
| 5 | Searcher filtering (SearchService::run) unchanged | VERIFIED | `SearchService::run()` has no reference to `readerContext` (grep confirms only `getFileContents`/`readerOf`/`fileIdFor*` call `actAs`); the per-searcher permission path is untouched as the plan required. |
| 6 | Admin: error list shows file id, diagnoses by id | VERIFIED | `admin.php` L766-778: button carries only `data-findling-file-id`; text is `%1$s (ID %2$s)` / `%1$s (in the trash bin, ID %2$s)`. `admin.js` L870-877: selector `button[data-findling-file-id]`, `reference = button.dataset.findlingFileId`. `grep -n data-findling-path` on both files returns no match (exit 1). All 8 l10n catalogues (.json, both new keys) verified programmatically , all `True`. |
| 7 | Admin diagnose (by id and by path/reference) actually finds a real ACL-blocked file on the live harness | VERIFIED (live) | Direct HTTP call against the running harness (http://localhost:8096, admin session), file 953 (`I14SlashAcl`, +read -share, previously proven `found:false` for the path form in the debug file): `GET diagnose?ref=953` -> `{"found":true,...}`; `GET diagnose?ref=i14u2/files/I14SlashAcl/.../probe-I14SlashAcl.txt` (the exact reference string) -> `{"found":true,...}`. This flips the debug file's documented pre-fix answer (`found:false`) to `found:true`, live, independent of the SUMMARY narrative. |
| 8 | Live HTTP RED/GREEN regression script + CI job exist and are wired for issue #14 | VERIFIED (structure); NOT independently re-executed | `scripts/ci/team_folder_acl.sh` (347 lines): creates users/groups, ACL folder, uploads via WebDAV, polls diagnose, asserts member finds it, outsider finds 0, admin path diagnose finds it (`bash -n` clean). `.github/workflows/integration.yml` job `team-folder-acl` (L4343-4409+) runs it with `install-groupfolders: 'true'`, CRAWL=1, modeled on `search-parity`. Not re-run here (would mutate live harness state and is a heavy live-HTTP scenario on a RAM-constrained machine); SUMMARY's RED/GREEN transcript is plausible and consistent with the debug file and code, but is not itself proof , see human_verification. |
| 9 | PHPUnit tests (ReaderContextTest + 4 updated classes) are real, substantive, cover the ordering contract | VERIFIED (content); NOT executed | Read in full / grepped: `ReaderContextTest.php` (5 stateful cases, real assertions on switch order, not just call counts). `QueueServiceReaderTest`, `GatewayControllerTest`, `PathResolverServiceTest` all construct a real `ReaderContext` and add ordering assertions (`testEveryMemberIsTheActiveUserWhileTheirFolderIsSetUpAndTheNodeIsLookedUp`, `testTheFolderAndTheLookupRunAsTheUserAndTheOpenAfterTheRestore`, etc.). Cannot run: no `vendor/` in the HaRP container (no composer install of a full server checkout) , matches the plan's own statement that PHPUnit needs a server checkout only CI has. |

**Score:** 9/9 observable checks either directly VERIFIED or VERIFIED-with-live-evidence; 2 of them (live RED/GREEN re-run, actual CI/PHPUnit execution) are legitimately deferred to CI/owner push, not code gaps.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `php/lib/Service/ReaderContext.php` | switch + restore in finally | VERIFIED | Exists, `php -l` clean, contains `finally`, docblock covers in_share mechanism, incognito caveat, restore-with-previous-object rationale. |
| `php/tests/Unit/ReaderContextTest.php` | switch/restore/exception/unknown/same-user cases | VERIFIED | 5 test methods, all behaviors from the plan's `<behavior>` block present. |
| `scripts/ci/team_folder_acl.sh` | live HTTP scenario, CI + harness runnable | VERIFIED (exists, substantive, `bash -n` clean) | 347 lines, env-driven (NC_URL/OCC/TAG/CRAWL/CLEANUP), 7 steps matching the plan's spec. |
| `.github/workflows/integration.yml` | job `team-folder-acl` | VERIFIED | Job present, contains `team_folder_acl.sh`, `install-groupfolders: 'true'`, modeled on `search-parity`. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `QueueService.php readerOf()` | `ReaderContext::actAs` | wraps `userFolder()` + `readableFile()` | WIRED | L960, 1 occurrence, matches plan. |
| `GatewayController.php getFileContents()` | `ReaderContext::actAs` | wraps folder+lookup, `fopen` after restore | WIRED | L83-102; test proves ordering directly (see truth #3). |
| `PathResolverService.php fileIdForUser/fileIdOverMounts` | `ReaderContext::actAs` | wraps `getUserFolder(uid)->get(path)` | WIRED | L354 and L464, 2 occurrences, matches plan (>= 2 required). |
| `backend/tests/test_php_acl_boundary.py` | `ReaderContext.php` | ratchet: exactly 2 `setVolatileActiveUser` calls, 1 owner file, `finally` required | WIRED | 32/32 boundary+trust tests pass locally; ratchet logic read and confirmed to match the plan's spec, incl. red-sample tests. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `php -l` on all 6 changed/relevant PHP files | `docker exec findling-harp-nextcloud php -l ...` (MSYS_NO_PATHCONV=1) | "No syntax errors detected" x6 | PASS |
| `node --check php/js/admin.js` | local | clean | PASS |
| Boundary + trust-boundary pytest | `uv run pytest tests/test_php_acl_boundary.py tests/test_php_trust_boundary.py` | 32 passed | PASS |
| Admin UI contract, public artifacts, store metadata, measurement scripts pytest | `uv run pytest tests/test_admin_ui_contract.py tests/test_public_artifacts.py tests/test_store_metadata.py tests/test_measurement_scripts.py` | 651 passed | PASS |
| Live admin diagnose by id, file 953 (ACL, -share, documented pre-fix `found:false`) | `curl` against harness, admin session | `{"found":true,...}` | PASS |
| Live admin diagnose by exact path/reference, file 953 | `curl` against harness, admin session | `{"found":true,...}` | PASS |
| Dash scan (U+2014/U+2013) over 15 changed files | python scan | empty | PASS |
| `git status --short` | only the SUMMARY.md itself untracked, no stray diffs, no foreign hunks | clean | PASS |

### Requirements Coverage

Quick task, no `.planning/REQUIREMENTS.md` entry for `issue-14` (expected , quick tasks are not tracked in the phase requirements register). Requirement is self-contained in the PLAN frontmatter (`requirements: [issue-14]`) and covered by the truths above.

### Anti-Patterns Found

None. No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in the reviewed files; no empty handlers, no hardcoded-empty stubs in the changed PHP/JS. `Known Stubs: None` in SUMMARY.md is accurate.

### Human Verification Required

### 1. PHPUnit suite runs green in CI

**Test:** Push the branch (or trigger `php.yml`) and watch the `phpunit` job.
**Expected:** `ReaderContextTest` (5 cases) and the new ordering cases in `QueueServiceReaderTest`, `GatewayControllerTest`, `PathResolverServiceTest` all pass on a real `nextcloud/server` checkout.
**Why human:** No `vendor/` directory exists in the local HaRP container or on this machine; PHPUnit requires a full server checkout with `composer install`, which only CI has. This is expected and stated by the plan itself, not a gap , but it is unverified until it actually runs.

### 2. New `team-folder-acl` CI job runs green

**Test:** Push and watch `.github/workflows/integration.yml` job `team-folder-acl`.
**Expected:** Script exits 0; member 2 finds both markers (1 entry each); outsider finds 0 for both; admin path diagnose finds both files (`found:true`).
**Why human:** The job has never executed in GitHub Actions (nothing has been pushed , repo rule: local only, never push). SUMMARY.md's RED/GREEN transcript describes a prior local harness run, not a CI run of the actual new job definition; the job YAML was reviewed and looks correct (modeled closely on the existing `search-parity` job) but its first real execution is still pending.

### Gaps Summary

No code-level gaps found. Every artifact, key link, and truth that can be checked without a full CI/PHPUnit environment was independently re-derived (not trusted from SUMMARY.md): ReaderContext's finally-restore, the fopen-after-restore ordering (verified via a PHPUnit test that asserts exact call order, itself read and reasoned about rather than executed), the unknown-user no-switch path, the three call sites' wiring, the boundary ratchet (executed and green), the admin UI id-only wiring (executed contract tests green), and , going beyond the plan's own verification steps , a live curl against the running harness confirming that a real groupfolders-ACL file that the debug file documented as `found:false` before the fix now answers `found:true` after it.

The only reason this is not `passed` is that two things the task explicitly cannot self-certify locally (PHPUnit, the new CI job) have genuinely not run yet, exactly as SUMMARY.md honestly states. This is a legitimate `human_needed`, not a disguised `gaps_found`.

---

_Verified: 2026-09-29T21:40:00Z_
_Verifier: Claude (gsd-verifier)_
