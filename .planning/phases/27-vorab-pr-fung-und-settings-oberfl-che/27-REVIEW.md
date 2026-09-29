---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
reviewed: 2026-09-29T00:00:00Z
depth: standard
files_reviewed: 76
files_reviewed_list:
  - .gitattributes
  - .github/workflows/deploy-harp.yml
  - .github/workflows/integration.yml
  - THIRD-PARTY.md
  - backend/appinfo/info.xml
  - backend/src/findling/api/probe.py
  - backend/src/findling/api/status.py
  - backend/src/findling/config.py
  - backend/src/findling/embed/model_probe.py
  - backend/src/findling/extract/pool.py
  - backend/src/findling/extract/probe_scan.pdf
  - backend/src/findling/guard.py
  - backend/src/findling/main.py
  - backend/src/findling/probe.py
  - backend/src/findling/worker/embedding.py
  - backend/src/findling/worker/poller.py
  - backend/src/findling/worker/probe_run.py
  - backend/src/findling/worker/watch.py
  - backend/tests/conftest.py
  - backend/tests/test_admin_ui_contract.py
  - backend/tests/test_embedding_runner.py
  - backend/tests/test_guard.py
  - backend/tests/test_measurement_scripts.py
  - backend/tests/test_model_probe.py
  - backend/tests/test_php_trust_boundary.py
  - backend/tests/test_poller.py
  - backend/tests/test_pool.py
  - backend/tests/test_probe.py
  - backend/tests/test_probe_endpoint.py
  - backend/tests/test_probe_php_parity.py
  - backend/tests/test_probe_run.py
  - backend/tests/test_sandbox.py
  - backend/tests/test_semantic_boundary.py
  - backend/tests/test_status_endpoint.py
  - backend/tests/test_watch.py
  - php/appinfo/info.xml
  - php/css/admin.css
  - php/js/admin.js
  - php/l10n/de.js
  - php/l10n/de.json
  - php/l10n/de_DE.js
  - php/l10n/de_DE.json
  - php/l10n/es.js
  - php/l10n/es.json
  - php/l10n/fr.js
  - php/l10n/fr.json
  - php/l10n/it.js
  - php/l10n/it.json
  - php/l10n/nl.js
  - php/l10n/nl.json
  - php/l10n/pt_BR.js
  - php/l10n/pt_BR.json
  - php/l10n/pt_PT.js
  - php/l10n/pt_PT.json
  - php/lib/BackgroundJobs/ScanRecountJob.php
  - php/lib/BackgroundJobs/StorageCrawlJob.php
  - php/lib/Controller/ProfileSettingsController.php
  - php/lib/Listener/FileEventListener.php
  - php/lib/Service/AdminViewService.php
  - php/lib/Service/CrawlAdvanceService.php
  - php/lib/Service/ExAppService.php
  - php/lib/Service/ProbeService.php
  - php/lib/Service/PurgeService.php
  - php/lib/Service/ScanStatsService.php
  - php/lib/Service/SettingsService.php
  - php/lib/Settings/Admin.php
  - php/templates/admin.php
  - php/tests/Unit/AdminViewServiceTest.php
  - php/tests/Unit/CrawlAdvanceServiceTest.php
  - php/tests/Unit/ExAppServiceTest.php
  - php/tests/Unit/ProbeServiceTest.php
  - php/tests/Unit/ProfileControllerTest.php
  - php/tests/Unit/ProfileSettingsControllerTest.php
  - php/tests/Unit/ScanRecountJobTest.php
  - php/tests/Unit/SettingsServiceTest.php
  - php/tests/Unit/StorageCrawlJobTest.php
findings:
  critical: 1
  warning: 11
  info: 7
  total: 19
status: issues_found
---

# Phase 27: Code Review Report

**Reviewed:** 2026-09-29
**Depth:** standard
**Files Reviewed:** 76
**Status:** issues_found

## Narrative Findings (AI reviewer)

## Summary

Reviewed the phase diff `3e2239a1..HEAD` (probe backend, PHP probe and profile routes, admin page, catalogues, quick task 260929-kii recount, CI route ratchet), plus `docs/l10n-*.md` and `FileStateService` for the owner merkers. The trust boundary holds: admin-only frontpage routes, closed sets on both sides, no token in the browser, and the SC3 CI step. The route ratchet in `deploy-harp.yml` is correct and matches `backend/appinfo/info.xml`.

The real defects are in the edges of the probe's life cycle: causes that lose their sentence, a start that times out, verdicts nobody takes over, fp32 files left behind, and a later save being overwritten. The recount has an ordering gap with the first crawl, and it now combines a fresh denominator with a stale state table.

Owner merkers, short answers:

1. **l10n docs:** confirmed, see WR-05. 72 phase 27 keys are missing from all five language tables. The note added by kii says the tables are complete, and they are not.
2. **638 > 637:** not a denominator bug. The Skipped tile counts the one deliberately left out file (skipped `too_large` or `mime_not_allowed`), and that file is taken out of the denominator. 608 + (24 - 1) + 6 = 637. The tile sum was never an invariant. Real ways for the two sources to disagree do exist (WR-02, WR-04), and the page's `recounting` sentence names only one of them.
3. **"Bewusst ausgelassen: 1" vs "Ausgeschlossen: 0":** both sources are right, but the labels are confusing. See WR-03.
4. **revokeFailures:** confirmed, see WR-04. A pre-existing defect, WARNING.

## Critical Issues

### CR-01: Two verdict paths lose their named cause (PRUEF-01 requires one)

**File:** `backend/src/findling/worker/probe_run.py:111-118, 630-631` (display gate in `php/js/admin.js` `PROBE_CAUSE_NEEDS` and `php/templates/admin.php` `$probeCauseNeeds`)

**Issue:** `_model_step` raises `_nofit(_MODEL_CAUSES.get(result.outcome, ...))` with no numbers. When the fp32 child hits `MemoryError`, the result is `model_memory`. When the child passes its deadline, the result is `timeout`. Both cause sentences need figures (`need`/`available`, or `seconds`). Both renderers deliberately hide a sentence that has a hole in it. So on the most likely fp32 failure on a tight box, the admin sees only "Does not fit" and no reason. PRUEF-01 and SC1 require a named cause.

**Fix:** carry the figures on the raise:

```python
if result.outcome != model_probe.MEASURE_OK:
    cause = _MODEL_CAUSES.get(result.outcome, "probe_failed")
    numbers: dict[str, int] = {}
    if cause == "timeout":
        numbers = {"seconds": _seconds(self._measure_seconds)}
    elif cause == probe.CAUSE_MODEL_MEMORY:
        numbers = {"need": MODEL_PROBE_CHILD_BYTES + GUARD_RESERVE_BYTES, "available": current or 0}
    raise _nofit(cause, numbers)
```

Add a probe_run test that checks every `(verdict, cause)` pair the orchestrator can emit against `PROBE_CAUSE_NEEDS`.

## Warnings

### WR-01: A recount can be planned ahead of the first crawl, and then the top-up route reports "nothing pending"

**File:** `php/lib/BackgroundJobs/ScanRecountJob.php:82-93`, `php/lib/Service/CrawlAdvanceService.php:66-77`

**Issue:** `ScanRecountJob` only checks for existing `StorageCrawlJob` rows. It ignores a pending `SchedulerJob`. On a fresh install, info.xml background jobs are registered before the install repair step adds `SchedulerJob`, so the recount job has the lower id and `scan_recounted_at` is 0 (due). The same window exists after `occ findling:index --restart`. The recount then plans chains before `SchedulerJob` plans the crawl, and recount rows and crawl rows end up side by side. That is exactly what `CrawlAdvanceService` says can never happen. While a recount row is first in `getJobsIterator`, `advance()` returns `pending: false`, so a starving container stops topping itself up during the first index (the 5.85 h dry-stock finding). Recount slices also hold `LOCK_NAME` for up to 30 s, delaying crawl slices.

**Fix:** in `ScanRecountJob::run`, also return while `SchedulerJob` has a row, or while `AppInstallStep::FIRST_INDEX_SCHEDULED` is set and `scanStats->totals()` shows `mountsFinished < mountsTotal` or `mountsTotal === 0`. In `CrawlAdvanceService::advance`, skip recount rows (`continue`) instead of returning, so a crawl row behind them is still found.

### WR-02: A fresh denominator minus stale state rows; the recounting sentence can name the wrong reason

**File:** `php/lib/Service/AdminViewService.php:600-607, 1726`, `php/templates/admin.php:424`

**Issue:** Since kii, `filesSeen`, `overCap` and `excluded` are re-measured, and they shrink when files are deleted. `$refusedByType` still comes from `findling_file_state`. No code path deletes a row of that table when a file is deleted (the only deletes are `revokeFailures` and migration 001300). A deleted `mime_not_allowed` file therefore still reduces a denominator that no longer contains it. `indexable` can then drop below `indexed` for good. The page then shows "Files were added since the last count" permanently, and the next recount does not fix it. The same sentence also appears when `indexed > indexable` for other reasons: after a mass delete before the container purged, or after a new exclusion before cleanup. "Files were added" is wrong in all of those cases.

**Fix:** count `mime_not_allowed` inside the recount walk (or join the state rows against `filecache` in `countByReason`) so both terms come from the same moment. Word the sentence neutrally, for example "The count of indexable files is being updated; the share is shown again afterwards." Before relying on the theory, check on the harness whether the container turns deleted refused files into `skipped(gone)`.

### WR-03: "Deliberately left out" and the "Excluded" tile are two numbers with near-identical names (merker 3)

**File:** `php/templates/admin.php:295-299, 428-431`, `php/lib/Service/AdminViewService.php:675, 1731`

**Issue:** The tile shows `scan.excluded` (folder rules only). "Deliberately left out" shows `overCap + excluded + refusedByType`. Both sources are correct. The harness value of 1 is one too-large or refused-type file, and that same file is also in the Skipped tile. In German, "Bewusst ausgelassen: 1" next to "Ausgeschlossen: 0" reads like a contradiction. The Skipped tile silently including the left-out file is what produced the "638 > 637" question.

**Fix:** break the line down, for example "Deliberately left out: 1 (too large 1, type not read 0, excluded by a rule 0)". Rename the tile to "Excluded by a rule". Or add a hint under the tiles that Skipped includes the deliberately left out files. All of these need new catalogue keys in all 16 files and in the docs tables.

### WR-04: revokeFailures never takes back a skip, so indexed files stay in the error list (merker 4, Issue #14)

**File:** `php/lib/Service/FileStateService.php:305-334`

**Issue:** Confirmed. The delete is limited to `state = 'failed'`. A file that was `skipped(unreadable)` or `skipped(too_large)`, and is indexed later (after a permission fix or a cap raise), keeps its row. It stays in the Skipped tile and the error list, and in the lookup it gets a remedy that contradicts a findable file. `skipped(no_text_layer)` is kept on purpose as the OCR memo, but that also means every OCR-indexed file is counted in both Indexed and Skipped. This is another reason the tile sum cannot be compared with the denominator. Pre-existing, not introduced by phase 27.

**Fix:** revoke every skip reason except `no_text_layer` when the container acknowledges the file as processed:

```php
->where($qb->expr()->orX(
    $qb->expr()->eq('state', $qb->createNamedParameter('failed')),
    $qb->expr()->andX(
        $qb->expr()->eq('state', $qb->createNamedParameter('skipped')),
        $qb->expr()->neq('reason', $qb->createNamedParameter('no_text_layer')),
    ),
))
```

Also filter `no_text_layer` rows of indexed files out of the Skipped tile, or show them in a group of their own.

### WR-05: docs/l10n-*.md tables are missing the phase 27 keys, and the kii note says the opposite (merker 1)

**File:** `docs/l10n-dutch.md`, `docs/l10n-french.md`, `docs/l10n-italian.md`, `docs/l10n-portuguese.md`, `docs/l10n-spanish.md`, `docs/l10n-catalogues.md:373-378`

**Issue:** Measured with `json.load` on `php/l10n/de.json`. At `3e2239a1` there were 216 keys, now there are 288. 73 were added and 1 removed ("To lift the reduction after checking the memory: %1$s"). Each of the five tables lacks 72 of the 73 new keys; only the kii sentence was added. They also lack 10 older keys (for example `Economy`, `Standard`, `Performance`, `Profile: chosen %1$s, in force %2$s (%3$s)`, `OCR slots: %1$s of %2$s, memory tight`, `Model: %1$s`), which were apparently already missing at the phase 26 close. The kii note in `l10n-catalogues.md` explains 288 as "the new one is the sentence...". That hides 72 keys and gives no account of the step from 205 to 216. The owner can no longer review the phase 27 wording in one pass, which is the purpose of these tables.

**Fix:** generate the missing 82 rows per document from the catalogues (DE plus target language). Rewrite the 29.09 count note as 216 plus 73 minus 1 equals 288, with the phase 27 breakdown. Consider a test that fails when a catalogue key has no row in each table.

### WR-06: Taking over a "fits" can overwrite a later downward save

**File:** `php/lib/Service/ProbeService.php:246-263`, `php/lib/Controller/ProfileSettingsController.php:94-119`

**Issue:** `takeOver` saves the probed pair whenever the snapshot matches the pending record. It does not check whether the stored profile changed since `startedAt`. If an admin stores Economy while the probe runs (through `occ` as D-27-13 documents, through a tab that has not yet polled, or through the PHP route, which does not refuse during a pending probe), the later "fits" raises the profile again. Nobody asked for that. It breaks D-27-09 (the way down is the safe way back).

**Fix:** store the `profile` and `model_precision` values in force in the pending record at start. In `takeOver`, commit only if both are unchanged, otherwise record the verdict with `committed: false`. Or refuse `saveProfile` with a `probe_running` code while a pending record exists.

### WR-07: A start that the 2 s admin timeout cuts off leaves a probe nobody takes over

**File:** `php/lib/Service/ExAppService.php:140, 674-676`, `php/lib/Service/ProbeService.php:107-139`, `backend/src/findling/worker/probe_run.py:396-416`

**Issue:** `adminSend('/probe')` uses `ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0`. Inside the container, `start()` awaits a state.db write (`_write_meta`, through a worker thread, while the poller may be holding the SQLite writer) before it answers. On a slow box the 202 can arrive after PHP gave up. PHP then answers "unreachable" and writes no pending record, while the container runs the probe. The next click gets `busy`. `ADMIN_BUSY` also writes no pending record, so this verdict is never taken over or shown. On "fits" with a fetched fp32 file, that file stays on the volume (see WR-08).

**Fix:** create the task first and persist in the background, or answer before the write. In PHP, when the answer is `ADMIN_BUSY` (or unreachable) and no pending record exists, read `/probe/state`. If it reports a running probe with the requested target, adopt its id as pending.

### WR-08: fp32 files a probe fetched can be orphaned or treated as placed by the admin

**File:** `backend/src/findling/worker/probe_run.py:405-411, 470-477, 506-517, 714-739`

**Issue:** Three paths lead to this.

- (a) After "fits", the fetched file stays and is only swept by `recover()`, which runs once at container start. If PHP never takes the verdict over (WR-07, a closed tab plus no later page view, or a newer probe replacing the pending record), 470 MB stays on the volume while the key says int8.
- (b) A new `start()` writes `probe_fp32_fetched = ""` without checking the previous done probe. The mark of a kept file is lost, and a later fp32 probe finds the file, takes the digest path, and on "nofit" never deletes it. That treats a file the check fetched as one the admin placed, against D-27-17.
- (c) After a restart between "fits" and the PHP take-over, `recover()` sees int8 in the companion and deletes the file. PHP then takes over the restored "fits" and stores fp32 without a file.

**Fix:** keep a per-file ownership mark that is independent of the probe id (for example `fp32_fetched_by_probe = 1` until the key reads fp32 or the file is removed). Do not clear it in `start()`. Run the sweep also after every done probe with a grace period, not only at start. In `recover()`, do not delete while the last snapshot is an unconsumed "fits" that is younger than `PENDING_STALE_SECONDS`.

### WR-09: The guard suspension covers the whole probe, including the real indexing pass during "pause"

**File:** `backend/src/findling/worker/watch.py:211-224`

**Issue:** `probe.held()` is true from the start of `_pause` (up to `PROBE_PAUSE_SECONDS` = 1800 s, the lease) through the download (600 s). During the pause the regular indexing pass is still running with its N slots. Every child kill of that pass is dropped by `guard.take_child_kills()`, and memory.events are rebased. So real OOM pressure of real indexing is invisible to the guard for up to about 40 minutes. D-27-15 only covers probe children, which do not report through `report_child_kill` anyway.

**Fix:** keep the lowering active until `_pause` has confirmed that the pass is parked. Set a separate "measuring" flag from the `model`/`ocr_one` steps onward and suspend only on that. Or keep counting kills reported by the poller (`guard.report_child_kill` comes only from poller children).

### WR-10: "digest_mismatch" tells the admin the file was deleted when a placed file is kept

**File:** `backend/src/findling/worker/probe_run.py:510-512`, `php/templates/admin.php:1062`, `php/js/admin.js` `probeCauseNames`

**Issue:** For a file the admin placed with the wrong digest, the check raises `digest_mismatch` and leaves the file in place, as D-27-17 requires. The only sentence for that cause says "The model file does not match its checksum and was deleted." The admin is told the file is gone while 470 MB of a wrong file stays in the offline location.

**Fix:** use two sentences: one for the downloaded case (deleted), and one for the placed case, such as "The model file placed on the volume does not match its checksum. Replace or remove it." Either split the cause code or choose the sentence from `fp32Deleted`/`fp32Fetched`.

### WR-11: The docs tables and the kii count note are not gated

**File:** `backend/tests/test_admin_ui_contract.py` (G2 completeness gate referenced at line 556)

**Issue:** The gates check the 16 catalogue files against each other, but nothing ties `docs/l10n-*.md` to the catalogues. That is how WR-05 went through a whole phase with the CI green.

**Fix:** add a test that parses the backticked first column of each language table and asserts it equals the key set of `de.json`, minus the named exception `Findling`.

## Info

### IN-01: Closed sets and the result judgement are written twice on the PHP side

**File:** `php/lib/Service/ProbeService.php:39-43, 198-225`, `php/lib/Service/AdminViewService.php:227-240, 275-309`

**Issue:** `PROBE_STEPS/VERDICTS/CAUSES/NUMBERS` and the judgement of the stored check exist in both classes. The rendered page formats `atText` with `formatDateTime($at)`, while the poll answer uses `formatDateTime($at, 'long', 'short')`. The date on the card changes format after the first poll.

**Fix:** make `ProbeService::result()` call `AdminViewService::judgedCheck()`. Use one format.

### IN-02: `overview()` docblock is missing `profileSaved`

**File:** `php/lib/Service/AdminViewService.php:554-568, 714`

**Fix:** add `profileSaved:string` to the array shape.

### IN-03: `markScanStale` can lose a mark

**File:** `php/lib/Service/SettingsService.php:251-256, 281-284`

**Issue:** A web request that read a non-zero value at request start skips the write, while cron sets the value back to 0. That event is then only caught by the 24 h floor.

**Fix:** acceptable as documented, or write the timestamp unconditionally when the value is older than the last recount start.

### IN-04: The `rebuilding` start code does not cover re-embedding

**File:** `backend/src/findling/main.py:390-394`, `backend/src/findling/worker/probe_run.py:401`

**Issue:** D-27-20 names `rebuilding` as "Neueinbettung läuft", but `_a_rebuild_may_start` only looks at the index-directory rebuild. A probe can therefore start during an fp32 re-embed. Also, an enable handler can start a directory rebuild while a probe holds the box, because nothing consults `probe.held()`.

**Fix:** decide whether that matches the intent, then either also answer `rebuilding` while `reembedRunning`, or document it.

### IN-05: The reindex estimate comes from one cold batch of 512-token passages

**File:** `backend/src/findling/embed/model_probe.py:219-226`, `php/lib/Service/AdminViewService.php:334-340`

**Issue:** The first batch after session creation includes graph warm-up, and real chunks are shorter than 512 tokens, so the "about N h" figure is strongly pessimistic. It is labelled as an estimate, so this is acceptable, but it is worth a line in `docs/admin-page.md`.

### IN-06: Hashing a placed fp32 file has no deadline

**File:** `backend/src/findling/worker/probe_run.py:508-511`

**Issue:** `fp32_verified` hashes 470 MB outside both the download cap and the measurement cap, while indexing is held.

**Fix:** put the digest step under `PROBE_DOWNLOAD_SECONDS`.

### IN-07: Workers are built before the `try`

**File:** `backend/src/findling/worker/probe_run.py:644`

**Issue:** If `_worker_factory()` raises for the k-th worker, the first k-1 workers are never stopped.

**Fix:** move the list comprehension inside the `try`.

---

_Reviewed: 2026-09-29_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
