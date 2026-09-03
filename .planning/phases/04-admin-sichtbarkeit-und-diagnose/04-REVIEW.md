---
phase: 04-admin-sichtbarkeit-und-diagnose
reviewed: 2026-09-03T03:32:15Z
depth: standard
files_reviewed: 43
files_reviewed_list:
  - .github/workflows/php.yml
  - backend/appinfo/info.xml
  - backend/src/findling/api/diagnose.py
  - backend/src/findling/api/rates.py
  - backend/src/findling/api/resources.py
  - backend/src/findling/api/status.py
  - backend/src/findling/extract/errors.py
  - backend/src/findling/main.py
  - backend/src/findling/store/repo.py
  - backend/src/findling/store/schema.sql
  - backend/tests/test_admin_ui_contract.py
  - backend/tests/test_diagnose_endpoint.py
  - backend/tests/test_exclusion_path_space.py
  - backend/tests/test_php_trust_boundary.py
  - backend/tests/test_rates_endpoint.py
  - backend/tests/test_status_endpoint.py
  - backend/tests/test_store_repo.py
  - docs/admin-page.md
  - docs/testing.md
  - php/appinfo/info.xml
  - php/css/admin.css
  - php/img/app-dark.svg
  - php/js/admin.js
  - php/l10n/de.js
  - php/l10n/de.json
  - php/lib/AppInfo/Application.php
  - php/lib/BackgroundJobs/StorageCrawlJob.php
  - php/lib/Command/DiagnoseCommand.php
  - php/lib/Controller/SettingsController.php
  - php/lib/Db/QueueMapper.php
  - php/lib/Listener/FileEventListener.php
  - php/lib/Migration/Version001000Date20260903000000.php
  - php/lib/Migration/Version001000Date20260904000000.php
  - php/lib/Service/AdminViewService.php
  - php/lib/Service/ExAppService.php
  - php/lib/Service/ExclusionService.php
  - php/lib/Service/FileStateService.php
  - php/lib/Service/PathResolverService.php
  - php/lib/Service/QueueService.php
  - php/lib/Service/ScanStatsService.php
  - php/lib/Service/SettingsService.php
  - php/lib/Service/StorageService.php
  - php/lib/Settings/Admin.php
  - php/lib/Settings/Section.php
  - php/templates/admin.php
findings:
  critical: 1
  warning: 6
  info: 7
  total: 14
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-09-03T03:32:15Z
**Depth:** standard
**Files Reviewed:** 43
**Status:** issues_found

## Summary

Reviewed the admin visibility and diagnosis phase: the three new container routes (`/status`, `/rates`, `/diagnose`), the admin settings page (controller, view service, template, script, stylesheet), the exclusion rules (service, crawl and listener call sites), the occ diagnose command, the scan stats migration and the four textual gates.

The security posture of the admin routes is sound: all four `FrontpageRoute` methods carry none of the four forbidden attributes, so SecurityMiddleware demands a logged-in admin plus the CSRF token; the gate in `test_php_trust_boundary.py` locks that in. The privacy contract of the container routes holds in the code reviewed: every response model is built field by field, no path, title or text travels, and the endpoint tests pin the field sets. `PathResolverService` refuses `..` segments and resolves paths only through `getUserFolder()`, and the appconfig writes on the read path (`rememberContainerCap`, `rememberIndexedCount`) are change-guarded.

One critical defect was found by tracing the exclusion feature across the reconcile path: the nightly reconcile undoes the clearing of D-07 and re-indexes excluded content, because the reconcile is a third way into the queue that never passes `ExclusionService::isExcluded`. Six warnings and seven informational items follow.

**Fix pass (2026-09-03):** the critical finding and all six warnings were fixed, one commit per finding; each finding below carries its Behebungsvermerk with the commit hash. The seven informational items stay documented and deliberately unfixed. All gates green after the pass: ruff, ruff format, pyright, vulture, pytest (775 passed, 11 skipped), `php -l` over 35 files in the dev container, `node --check php/js/admin.js`.

## Narrative Findings (AI reviewer)

## Critical Issues

### CR-01: Exclusion rules do not hold: the nightly reconcile re-indexes excluded content and undoes the D-07 clearing

**File:** `php/lib/Service/QueueService.php:339-497` (describe, no exclusion check), `php/lib/Service/StorageService.php:405-421` (getFileSlice serves excluded files with no marker), `backend/src/findling/worker/reconcile.py:379-388` (`_stale_of` treats tombstoned rows as restores), `backend/src/findling/store/repo.py:699-728` (`known_etags` omits tombstoned rows)

**Issue:** `isExcluded` is called from exactly three places in the app: the crawl, the event listener and the diagnosis (verified by grep). The reconcile path is a fourth way into the queue and applies the exclusion nowhere:

1. `StorageService::getFileSlice` deliberately does not filter excluded files out of the reconcile slice (documented, for the final-mark reason), and the slice carries no path, so the container cannot apply the prefix rules either.
2. The container's `_stale_of` requeues as `KIND_CONTENT` every file whose etag it cannot match, and `known_etags` deliberately omits tombstoned rows so that a tombstoned file appearing in a page reads as a restore.
3. `QueueService::describe` builds the work order for a `content` row without any exclusion check, and the container then downloads and indexes the file; `Store.record()` lifts the tombstone.

Two concrete failure sequences follow:

(a) **The clearing is reverted within one reconcile interval.** Admin saves a new exclusion; `SubtreeExpandJob` clears the subtree (delete rows, tombstones) as designed. The next reconcile round (default within 24 h) serves the same files in its slices, `_stale_of` reads every tombstoned row as a restore, requeues them as `content`, and the container re-fetches and re-indexes the whole excluded subtree. The documents the admin ordered out of the index are searchable again, permanently (each subsequent round keeps them fresh), while the page's Excluded tile and the stage-two diagnosis ("Excluded by a rule") both claim the opposite.

(b) **A file moved into an already excluded folder keeps and refreshes its index entry.** The rename changes the etag; the listener drops the metadata job at the exclusion check (correct in itself) but queues no delete, so the old text stays searchable; the next reconcile sees the stale etag, requeues it as `content`, and the file inside the excluded folder is re-indexed with its current content.

This is exactly the quiet failure class pitfall 4 describes ("the index fills up with exactly what was supposed to be left out, and nothing on the page says so"), reached through the one call path the gate `test_exclusion_path_space.py` does not cover.

**Fix:** Give the reconcile-to-index path an exclusion check with a delete outcome. The most contained option is in `QueueService::describe()`, which is the last point on the PHP side that has both a resolved node and the mount context:

```php
// in describe(), after resolving $node and repairing storageId/rootId,
// before building the content/metadata/ocr work order:
$relative = $this->exclusionService->mountRelativePath(
    $node->getInternalPath(),
    $this->storageService->mountRootPath($storageId, $rootId),
);
if ($this->exclusionService->isExcluded($relative)) {
    // The rule of today says this file is not in the index. Turn the row
    // into the delete order the container needs to clear/keep-clear it,
    // instead of handing out its bytes.
    return [
        'fileId' => $fileId,
        'storageId' => $storageId,
        'kind' => QueueMapper::KIND_DELETE,
    ];
}
```

(Requires `ExclusionService` and access to the mount root in `QueueService`; alternatively mark excluded rows in the `getFileSlice` payload, e.g. `'excluded' => true`, and let the container skip the stale/restore logic for them without dropping them from the page, which preserves the final-mark semantics.) Whichever variant is chosen, add a regression test: exclude a folder, run the clearing, run one reconcile cycle, and assert the documents are still out of the index. Also extend `test_exclusion_path_space.py` so the reconcile/requeue path counts as a call site that must consult the helper.

**Behebung:** fixed in commit `e91b409`. The first variant, in `QueueService::describe()`: after the storage/root repair and before the work order is built, the one helper is asked on the one path space (`mountRelativePath` over `mountRootPath`), and an excluded row is answered as a `KIND_DELETE` work order instead of its bytes, so a tombstoned excluded file the reconcile requeued as a restore is re-deleted (the container's `_forget` is idempotent). `getFileSlice` stays unfiltered, so the final-mark semantics and the reconcile deletion limits are untouched, and the clearing path (`SubtreeExpandJob` with kind delete) is unchanged. Gate D now holds the third call site (`test_the_reconcile_requeue_path_consults_the_helper`) and the delete outcome (`test_an_excluded_row_is_handed_out_as_a_delete_order`); a live PHP reconcile cycle is not runnable in this repository's test environment, so the contract is pinned textually the way the other three gates pin theirs.

## Warnings

### WR-01: A corrupt or half-created state database turns the three admin routes into HTTP 500s

**File:** `backend/src/findling/api/status.py:204-208`, `backend/src/findling/api/rates.py:168-172`, `backend/src/findling/api/diagnose.py:86-98`
**Issue:** All three handlers catch only `OSError` around `open_read_only`. Two realistic failure shapes escape: (1) a file that is not a SQLite database raises `sqlite3.DatabaseError` from the first PRAGMA inside `_connect()`; (2) a zero-byte `state.db` (a kill between `sqlite3.connect` and `executescript` in `open_store` leaves exactly this) opens fine, and the first query (`store.counts()`, `store.throughput()`, `store.file_row()`) raises `sqlite3.OperationalError: no such table`. Both escape the `except OSError` and end as a 500, which breaks the documented contract of these routes ("a missing/unreadable state is an answer, never a server error") and lights the wrong banner on the admin page. The `diagnose._report` docstring even claims "never raises".
**Fix:** Broaden the guards to `except (OSError, sqlite3.Error)` around both the open and the read section, answering with the existing `STATE_UNREADABLE` / `NOT_JUDGED` shapes:

```python
try:
    store = open_read_only(resolved.state_db)
except (OSError, sqlite3.Error):
    return volume.model_copy(update={"note": STATE_UNREADABLE})
try:
    return _of(store, volume)
except sqlite3.Error:
    return volume.model_copy(update={"note": STATE_UNREADABLE})
finally:
    store.close()
```

**Behebung:** fixed in commit `4efd6fe`. All three routes catch `(OSError, sqlite3.Error)` on the open and `sqlite3.Error` on the read, answering with the existing `STATE_UNREADABLE` / `NOT_JUDGED` shapes. Both failure shapes (zero-byte `state.db`, non-SQLite file) are pinned per route in the three endpoint test files.

### WR-02: FileStateService validates state and reason independently, not as a pair, and a mismatched pair produces duplicate DOM ids

**File:** `php/lib/Service/FileStateService.php:160-206`, `php/templates/admin.php:438,443,458`
**Issue:** `record()` checks `$state` against `STATES` and `$reason` against `REASONS` separately. Unlike the Python side (`STATE_REASONS` pair validation in `repo.py` and `errors.py`), the PHP boundary accepts pairs that do not exist, e.g. `failed` + `too_large` from a defective or newer container via the acknowledgement route. Downstream, `AdminViewService::errors()` would then emit two groups with the same reason under two states, and the template keys both the count element (`findling-errors-count-<reason>`) and the examples region (`findling-errors-<reason>`) by reason alone: duplicate ids, `aria-controls` pointing at the first region only, and the JS `errorsBlock()` updating the wrong count. The class docblock claims this table is the defence against "a trusted component with a defect", so the pair check belongs here.
**Fix:** Port the pair mapping: `private const STATE_REASONS = ['indexed' => [null,'truncated'], 'skipped' => [...], 'failed' => [...]]` and reject a pair outside it in `record()`. Independently, key the DOM ids by `state . '-' . reason` in the template and in `admin.js`.

**Behebung:** fixed in commit `b3220f6`. `STATE_REASONS` ported to `FileStateService`, `record()` judges the pair (a reasonless skipped/failed row is refused as well), and `test_extract_errors.py` now compares the PHP pair mapping against the Python one per state and in both directions (`test_php_pair_mapping_matches_python`). The count and region ids of the error list are keyed by `state . '-' . reason` in `templates/admin.php` and `admin.js`.

### WR-03: saveRules ignores the error return of both save() calls and can answer "saved" for a write that was refused

**File:** `php/lib/Controller/SettingsController.php:345-371`
**Issue:** `SettingsService::save()` and `ExclusionService::save()` both revalidate and return error-code arrays; the controller discards both return values and answers `['saved' => true, ...]` whenever no exception was thrown. The double validation is not guaranteed to agree with the controller's own: `SettingsService::clamped()` depends on `containerCap()`, and `rememberContainerCap()` can be written concurrently by an overview poll of a second admin tab between the controller's `validate()` and `save()`. In that window `save()` returns `ERROR_OUT_OF_RANGE`, writes nothing, and the route still reports success with `rules()` echoing the old cap. The page then tells the admin the rules were saved when the cap was not.
**Fix:**

```php
$fieldErrors = $this->settingsService->save([...]);
$listErrors = $this->exclusionService->save($list);
if ($fieldErrors !== [] || $listErrors !== []) {
    return new DataResponse(
        ['saved' => false, 'fields' => $fieldErrors, 'exclusions' => $listErrors, 'error' => 'The rules were not saved.'],
        Http::STATUS_BAD_REQUEST,
    );
}
```

**Behebung:** fixed in commit `629fdcc`. Both `save()` returns are judged and answered as 400 with the codes. The list is written only after the fields held, so a cap that a concurrent poll moved leaves appconfig untouched as a whole and "nothing changed" stays true.

### WR-04: admin.js templating via String.replace mangles user-controlled values containing `$` patterns, including the destructive confirmation

**File:** `php/js/admin.js:560-566` (diagnosis path), `php/js/admin.js:745` (remove aria-label), `php/js/admin.js:877-885` (confirmation message)
**Issue:** `t(...).replace('%s', value)` and the chained `%1$s`/`%2$s` replaces use the value as a replacement *pattern*: `$&`, `` $` ``, `$'`, `$$` and `$n` in a folder name or path are expanded by `String.prototype.replace`. A folder named `Archiv$&2024` renders as `Archiv%1$s2024` inside the D-07 confirmation, and a prefix containing the literal text `%2$s` shifts the second substitution into the middle of the path. No XSS (all sinks are text nodes), but the inline confirmation of a destructive action can name a path that is not the one about to be cleared, which is the one sentence on this page that must be exact.
**Fix:** Use a function replacement everywhere a non-literal value is substituted:

```js
text.replace('%1$s', function () { return prefixes.join(', ') })
    .replace('%2$s', function () { return documents })
```

**Behebung:** fixed in commit `82e289c`. The three sites that substitute user-controlled values (diagnosis path, remove aria-label, confirmation message) use function replacements. The two-placeholder confirmation additionally substitutes the figure first and the folder names last, because a function only guards the dollar patterns of its own insertion: user text containing the literal other placeholder must never be scanned by a later replace. The remaining `.replace` chains substitute `numbers.format` output and translated duration phrases, which cannot carry `$` patterns.

### WR-05: The diagnosis chip shows "Not seen yet" for a file whose state is unknown because the backend is silent

**File:** `php/js/admin.js:478-523` (chipOf/chipLabel)
**Issue:** `AdminViewService` distinguishes `pending_crawl` (stage six, an honest "the crawl has not arrived") from `unknown` (stage five with an unreachable backend, "we cannot say right now"). `chipOf()` maps both to the `unknown` chip, and `chipLabel()`'s default returns `'Not seen yet'` for it. A lookup answered while the container is down therefore shows the chip "Noch nicht gesehen", a positive claim about the crawl that the page cannot back; only the smaller note underneath says the backend did not answer. That collapses exactly the distinction this phase exists for ("never claim a state when 'I do not know right now' is the truth"); the design contract's own state inventory has eight chips, so `unknown` and `pending_crawl` were meant to read differently.
**Fix:** Branch on `view.state` in `chipLabel` (the state travels in the answer): `pending_crawl` keeps `'Not seen yet'`, `unknown` with `found === true` gets its own sentence, e.g. `t('findling', 'State unknown right now')`, with the matching key added to `l10n/de.json` and `de.js`.

**Behebung:** fixed in commit `a4fdf2e`. `chipLabel` receives the view and branches on `view.state`: `pending_crawl` keeps "Not seen yet", `unknown` answers "State unknown right now" ("Zustand im Moment unbekannt"), key added to both l10n files.

### WR-06: Exclusion entries beyond the 64-entry cap are silently dropped and therefore silently not enforced

**File:** `php/lib/Service/ExclusionService.php:179-189`
**Issue:** `prefixes()` breaks out of the loop at `MAX_PREFIXES` without calling `reject()` or logging. The UI cannot produce more than 64 entries, but `occ config:app:set findling exclusions` is the documented second writer and has no such bound. Entry 65 onward is then not compared anywhere: files the admin excluded get crawled, queued and indexed, with no signal in any log. That is fail-open in precisely the direction this feature promises not to fail, and it is invisible (the page also only shows the first 64, so the list looks like what is enforced, while the stored list is longer).
**Fix:** Count and log the truncation the way malformed entries are handled:

```php
if (count($prefixes) >= self::MAX_PREFIXES) {
    if (count($stored) > self::MAX_PREFIXES) {
        $this->reject(); // or a dedicated warning naming the dropped count
    }
    break;
}
```

**Behebung:** fixed in commit `2ab18a7`. The break at the ceiling logs a dedicated warning naming the dropped count and the ceiling when entries remain behind it, values never written out. The rejection counter of malformed entries is untouched.

## Info

### IN-01: index_bytes logs a warning for the ordinary fresh-container state, once per poll

**File:** `backend/src/findling/store/repo.py:915-917`, called from `backend/src/findling/api/status.py:151` and `rates.py:138`
**Issue:** A container that has not indexed anything yet has no index directory; `_volume()` and `/rates` call `index_bytes()` on every admin-page poll (every 5 s), producing a steady stream of "the index directory cannot be read" warnings in exactly the phase every new install goes through.
**Fix:** Log the missing-directory case at debug (keep the warning for the OSError branch), or log it once per process.

### IN-02: Dead translation key "Indexing, about %s left"

**File:** `php/l10n/de.json:10`, `php/l10n/de.js:11`
**Issue:** The key has no caller in `admin.js` or `templates/admin.php` (the running state deliberately carries no time estimate). Dead entries in hand-maintained translation files invite drift.
**Fix:** Remove the key from both files, or add a comment marker if it is reserved for a later plan.

### IN-03: Percent figure changes from NBSP to plain space after the first poll

**File:** `php/templates/admin.php:191` (`"\u{00A0}%"`), `php/js/admin.js:318` (`+ ' %'`)
**Issue:** The template renders the coverage figure with a non-breaking space before `%`, the script rewrites it with a normal space. The figure can re-wrap after the first poll, contradicting the stated rule that values do not change shape when the script takes over.
**Fix:** Use `' %'` in `coverageBlock()`.

### IN-04: Path lookup converts backslashes to slashes, so files with a backslash in the name cannot be diagnosed

**File:** `php/lib/Service/PathResolverService.php:204`
**Issue:** `str_replace('\\', '/', $input)` reinterprets a legal Nextcloud filename character as a separator; `ExclusionService` explicitly preserves backslashes for that reason. A file named `a\b.pdf` is unfindable by path (id lookup still works). Inconsistent with the exclusion path space.
**Fix:** Drop the backslash conversion, or document the convenience trade-off next to it.

### IN-05: Section.php docblock justifies omitting #[\Override] with a wrong claim

**File:** `php/lib/Settings/Section.php:22-27`
**Issue:** The comment states the attribute "is a parse error" on PHP 8.2. It is not: attributes are resolved lazily, and `#[\Override]` is engine-checked only from 8.3 on; the same file notes that `Provider.php` carries it and runs on 8.2, which contradicts the claim in the same paragraph. The decision (omit it) is harmless, but the recorded reason will steer future edits wrongly.
**Fix:** Correct the comment (e.g. "omitted for consistency until the floor is 8.3; on 8.2 it is ignored, not enforced").

### IN-06: Module-level read-side cache is mutated from worker threads without a lock

**File:** `backend/src/findling/api/resources.py:58-59, 156-194`
**Issue:** `_OPEN` and `_MARKS` are globals written from `asyncio.to_thread` workers. Two concurrent first searches can both find `_OPEN is None`, both open index and store, and the loser's `Store` connection is never closed (leaks until GC). Correctness is unaffected (last writer wins, key check guards staleness).
**Fix:** Guard `read_side()` with a `threading.Lock`, or close the losing store before overwriting.

### IN-07: A `.` segment in an exclusion prefix is stored but can never match

**File:** `php/lib/Service/ExclusionService.php:207-225`
**Issue:** `normalise()` refuses `..` but keeps `.` segments (`./Archiv`, `Archiv/./x`). Cache paths never carry `.` segments, so such a prefix is stored, shown in the list as in force, and matches nothing: a silently ineffective rule, the same quiet-failure class the refusal of `..` exists to avoid.
**Fix:** Refuse `.` segments alongside `..` in `normalise()` (same `ERROR_TRAVERSAL` bucket, or a dedicated code).

---

_Reviewed: 2026-09-03T03:32:15Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
