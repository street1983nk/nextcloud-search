---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
fixed_at: 2026-09-29T00:00:00Z
review_path: .planning/phases/27-vorab-pr-fung-und-settings-oberfl-che/27-REVIEW.md
iteration: 1
findings_in_scope: 12
fixed: 12
skipped: 0
status: all_fixed
---

# Phase 27: Code Review Fix Report

**Fixed at:** 2026-09-29
**Source review:** .planning/phases/27-vorab-pr-fung-und-settings-oberfl-che/27-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 12 (CR-01, WR-01 to WR-11)
- Fixed: 12 (WR-04 with one sub-part left for the owner, see there)
- Skipped: 0

Worked directly on `main` in the main tree as instructed, everything local, nothing pushed.
Commit identity street1983nk, no trailers. Python gates (ruff check, ruff format --check,
pyright latest, vulture 80) green before every commit. PHP: `php -l` in
`findling-harp-nextcloud` on every touched file; the PHPUnit suite is CI only (no server
checkout, no vendor dir in the harness), so the new PHPUnit cases are written but not run
locally. For WR-02 and WR-04 the SQL was proven RED/GREEN live against the harness database
instead, inside a transaction that is rolled back. Both tree hash pins in
`backend/tests/test_measurement_scripts.py` were measured again with the recipe after every
fix that moved them.

Full suite at the end: 4130 passed, 25 skipped (before: 4107 passed, 25 skipped; +23 new
cases).

## Fixed Issues

### CR-01: Two verdict paths lose their named cause

**Files modified:** `backend/src/findling/worker/probe_run.py`, `backend/tests/test_probe_run.py`, `backend/tests/test_measurement_scripts.py`
**Commit:** 918f340d
**Applied fix:** `_model_step` now carries `seconds` for `timeout` and `need`/`available` for
`model_memory` when a model child ends that way. New tests read `$probeCauseNeeds` out of the
template and check every nofit the orchestrator can emit (4 model outcomes x int8/fp32 child,
plus memory_unknown, first slot gate, model gate, OCR cap timeout, sandbox timeout, killed
child, digest, download_slow) for the figures of its sentence.
**RED:** 4 of the new cases failed before the fix (timeout-int8, timeout-fp32,
no_memory-int8, no_memory-fp32: `('model_memory', ['need', 'available'])` missing); all green
after.
**Status:** fixed: requires human verification (logic: which `available` a child MemoryError reports is the headroom before that child).

### WR-01: A recount can be planned ahead of the first crawl

**Files modified:** `php/lib/BackgroundJobs/ScanRecountJob.php`, `php/lib/Service/CrawlAdvanceService.php`, `php/tests/Unit/ScanRecountJobTest.php`, `php/tests/Unit/CrawlAdvanceServiceTest.php`, `backend/tests/test_measurement_scripts.py`
**Commit:** 37c7b1d8
**Applied fix:** `ScanRecountJob::run` also returns while a `SchedulerJob` row exists (fresh
install and `--restart` window). `CrawlAdvanceService::advance` walks all rows, passes over
recount rows with `continue`, runs exactly one crawl slice, and reports `pending` only for
crawl rows.
**RED:** PHPUnit cases written (`testNothingIsPlannedWhileTheSchedulerIsStillPending`,
`testACrawlRowBehindARecountRowStillRuns`, `testOnlyRecountRowsLeftIsNotPending`); against the
old code the first would see `add` called, the second would get `ran:false, pending:false`.
Not run locally (CI only); `php -l` green.
**Status:** fixed: requires human verification (CI PHPUnit run).

### WR-02: A fresh denominator minus stale state rows; wrong recount reason

**Files modified:** `php/lib/Service/FileStateService.php`, `php/lib/Service/AdminViewService.php`, `php/templates/admin.php`, `php/js/admin.js`, all 16 `php/l10n/*`, the five `docs/l10n-*.md`, `docs/l10n-catalogues.md`, `backend/tests/test_admin_ui_contract.py`, `backend/tests/test_measurement_scripts.py`
**Commit:** 1389dc8c
**Applied fix:** `countByReason` inner joins `filecache` and leaves out `files_trashbin/%` and
`__groupfolders/trash/%`, so a deleted or trashed refused file no longer lowers the
denominator. The recount sentence is neutral now (new key `%s files are searchable. The count
of indexable files is being updated, and the share is shown again afterwards.`, DE "Die Zahl
der indexierbaren Dateien wird gerade neu ermittelt, danach erscheint der Anteil wieder."),
renamed in all 16 catalogues and the five tables; count stays 288.
**RED:** live on the harness (rolled back): one live file, one id absent from filecache, one
file moved to `files_trashbin/files/` inside the transaction, each recorded as
skipped(mime_not_allowed): counted 3 before, 1 after. Sentence gate failed before, green after.
Harness finding for the review question: the harness has no skipped(mime_not_allowed) row at
all and no state row of a file missing from filecache, so "Bewusst ausgelassen: 1" there is a
too_large file (2 skipped(too_large) rows); whether the container turns a deleted refused file
into skipped(gone) could not be observed there, and the join makes the count right either way.
**Status:** fixed: requires human verification (logic; translations outside DE/EN are machine translations, not yet read by the owner).

### WR-03: "Deliberately left out" and the "Excluded" tile

**Files modified:** `php/templates/admin.php`, `backend/tests/test_admin_ui_contract.py`, `backend/tests/test_measurement_scripts.py`
**Commit:** 6e793acd
**Applied fix:** per owner decision the tile reads "Excluded by a rule" / "Durch Regel
ausgeschlossen". The key already existed in all 16 catalogues (the name of the reason group
`excluded` in the error list) with exactly that wording in all eight languages, so no
catalogue and no docs table moved. The chips of the error list and the lookup keep
"Excluded". No breakdown variant.
**RED:** new contract test failed before, green after.

### WR-04: revokeFailures never takes back a skip

**Files modified:** `php/lib/Service/FileStateService.php`, `php/lib/Service/QueueService.php`, `php/lib/Migration/Version001300Date20260927000000.php` (comment only), `backend/tests/test_admin_ui_contract.py`, `backend/tests/test_measurement_scripts.py`
**Commit:** 986ba086
**Applied fix:** the delete of `revokeFailures` covers `failed` and every `skipped` reason
except `no_text_layer` (the OCR memo). Docblocks and the two log lines follow; a textual gate
holds the query shape.
**RED:** live on the harness (rolled back): failed(corrupt), skipped(too_large),
skipped(unreadable), skipped(no_text_layer) on four fresh ids, then `revokeFailures`: before
revoked=1 with too_large, unreadable, no_text_layer left; after revoked=3 with only
skipped(no_text_layer) left.
**Not done, owner decision needed:** the second half of the review suggestion, filtering
`no_text_layer` rows of OCR-indexed files out of the Skipped tile or giving them a group of
their own. That changes what the tile and the error list count and needs new wording; this
side cannot tell an OCR-indexed file from one still waiting for OCR without asking the
container. Left as is.
**Status:** fixed: requires human verification (logic, and the open sub-part above).

### WR-05: docs/l10n-*.md tables were missing keys, the kii note said the opposite

**Files modified:** `docs/l10n-french.md`, `docs/l10n-spanish.md`, `docs/l10n-italian.md`, `docs/l10n-dutch.md`, `docs/l10n-portuguese.md`, `docs/l10n-catalogues.md`
**Commit:** 2430f77c
**Applied fix:** the missing rows were cast mechanically from the catalogues (DE plus the
target columns) and put right after the row of the key that precedes them in `de.json`: 82
per document, 83 in French (also `File contents`). Every table now carries every key of the
288 (French without `Findling`, its named G2 exception). The existing rows matched the
catalogues cell for cell before (checked), so nothing else moved. The kii count note in
`l10n-catalogues.md` is rewritten as a table 205, 207 (25-04, +2), 216 (26-05, +9, start of
phase 27), 287 (27-13, +72 -1), 288 (kii, +1), "216 + 73 - 1 = 288". Each language document
has a dated note after its table.
**RED:** see WR-11 (the gate went red with 83 missing keys in l10n-french.md before this commit).

### WR-06: Taking over a "fits" can overwrite a later downward save

**Files modified:** `php/lib/Service/ProbeService.php`, `php/tests/Unit/ProbeServiceTest.php`, `backend/tests/test_measurement_scripts.py`
**Commit:** 52e1cfb7
**Applied fix:** the pending record stores `inForce` (profile, precision, whether a profile
was ever stored) at start. `takeOver` commits a "fits" only when `inForce` is unchanged;
otherwise the verdict is remembered with `committed: false` and a static log line. A record
without `inForce` (from before this change) keeps the old take-over; an unreadable one never
commits.
**RED:** PHPUnit cases written (unchanged commits, economy stored over the default, precision
lowered, unreadable inForce, and the start record carries inForce); not run locally (CI only);
`php -l` green.
**Status:** fixed: requires human verification (logic, CI PHPUnit run).

### WR-07: A start the 2 s timeout cuts off leaves a probe nobody takes over

**Files modified:** `backend/src/findling/worker/probe_run.py`, `backend/tests/test_probe_run.py`, `php/lib/Service/ProbeService.php`, `php/tests/Unit/ProbeServiceTest.php`, `backend/tests/test_measurement_scripts.py`
**Commit:** 5c2c7edf
**Applied fix:** `ProbeRun.start` no longer awaits the state.db write; the task writes the
running state before its first step. PHP: on `ADMIN_BUSY` (not rebuilding) or
`ADMIN_UNREACHABLE` with no pending record, `ProbeService::adopt` reads `/probe/state` once
and adopts a running probe with exactly the requested target and a well formed id as pending;
another target stays busy.
**RED:** `test_the_start_answers_before_the_state_is_written` (write blocked behind an event)
failed before, green after; two meta tests now wait for the task's write. PHPUnit cases for
the adoption written, not run locally.
**Status:** fixed: requires human verification (CI PHPUnit run).

### WR-08: fp32 files a probe fetched can be orphaned or treated as placed

**Files modified:** `backend/src/findling/worker/probe_run.py`, `backend/src/findling/config.py`, `backend/tests/test_probe_run.py`, `backend/tests/test_measurement_scripts.py`
**Commit:** 168fa999
**Applied fix:** `probe_fp32_fetched` is now the ownership mark of the file, not of a probe
id: no start clears it, `_finish` touches it only when the check handled a fetched file, and a
later check that finds the file under the mark treats it as fetched (nofit removes it). (a)
After every check that kept a fetched file a sweeper task runs `recover` with the remembered
companion reader, not only at container start. (c) `recover` leaves a "fits" for fp32 alone
while it is younger than `PROBE_TAKEOVER_SECONDS` = 3000 (the `PENDING_STALE_SECONDS` of
ProbeService.php, held equal by a test) and reads the companion every 60 s meanwhile. A lock
keeps the lifespan sweep and the sweeper from running twice; `close` cancels the sweeper.
**RED:** 4 of 5 new tests failed before (b as behaviour; a and c also on the new keyword
arguments), the control test for a placed file passed before and after.
**Status:** fixed: requires human verification (logic of the ownership and the grace).

### WR-09: The guard suspension covers the whole probe

**Files modified:** `backend/src/findling/probe.py`, `backend/src/findling/worker/probe_run.py`, `backend/src/findling/worker/watch.py`, `backend/tests/test_watch.py`, `backend/tests/test_probe_run.py`, `backend/tests/test_measurement_scripts.py`
**Commit:** 20041463
**Applied fix:** new flag `probe.measure()` / `probe.measuring()`, set at the start of the
measuring part (model, ocr_one, calc, ocr_n) and cleared by `release`. The guard suspends on
`measuring()` instead of `held()`, so a kill in the regular pass the pause waits for lowers the
profile as before.
**RED:** 3 new or extended tests failed before (kill during the pause lowers; not measuring
during the pause; measuring while the children run), green after.
**Status:** fixed: requires human verification (logic).

### WR-10: "digest_mismatch" says the file was deleted when a placed file is kept

**Files modified:** `php/templates/admin.php`, `php/js/admin.js`, all 16 `php/l10n/*`, the five `docs/l10n-*.md`, `docs/l10n-catalogues.md`, `backend/tests/test_admin_ui_contract.py`, `backend/tests/test_measurement_scripts.py`
**Commit:** d25c85e8
**Applied fix:** both halves choose the sentence from `fp32Deleted`: deleted keeps the
existing sentence, otherwise the new key `The model file placed on the volume does not match
its checksum. Replace or remove it.` (DE "Die auf dem Volume abgelegte Modelldatei passt nicht
zu ihrer Prüfsumme. Die Datei ersetzen oder entfernen."). 289 keys now; the hard count gate
and the count note are moved.
**RED:** new contract test failed before, green after.
**Status:** fixed (translations outside DE/EN are machine translations, not yet read by the owner).

### WR-11: The docs tables and the kii count note were not gated

**Files modified:** `backend/tests/test_admin_ui_contract.py`
**Commit:** fdd43a3a
**Applied fix:** `test_every_language_table_carries_every_key_with_the_catalogue_wording`
parses the backticked first column of each language table and holds it against `de.json`
both ways (no missing key, no stale row, `Findling` the one allowed absence), and every cell
against the catalogues of its columns, plural forms joined with " / ".
**RED:** failed before WR-05 with `('l10n-french.md', 83, ['File contents', 'Model: %1$s', ...])`,
green after; it then carried WR-02 and WR-10 through the tables.

---

_Fixed: 2026-09-29_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
