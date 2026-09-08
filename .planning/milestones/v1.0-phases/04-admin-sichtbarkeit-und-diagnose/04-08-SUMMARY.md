---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 08
subsystem: api
tags: [php, nextcloud, appconfig, vanilla-js, settings, exclusions, appapi]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "the admin-only SettingsController and ExAppService::adminGet from plan 04-03"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "the excluded column of findling_scan_stats from plan 04-04 and the Excluded tile of block one"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "backend.maxFileBytes in the status answer from plan 04-02, which is the ceiling the cap is clamped at"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "AdminViewService::diagnose with the named excludedByAPrefix hook from plan 04-07"
  - phase: 02-indexpfad-und-zustand
    provides: "StorageService::MOUNT_PROVIDERS, StorageCrawlJob::MAX_SIZE and the event listener that both become configurable here"
provides:
  - "SettingsService: the four appconfig keys of ADM-04 with type, default, validation and the cap clamped at the container ceiling"
  - "SettingsService::rememberContainerCap: the last reported container ceiling, so the clamp holds while the container is silent"
  - "ExclusionService: prefix list, defensive normalisation, and isExcluded as the single exclusion comparison of the app"
  - "ExclusionService::mountRelativePath: the single exclusion path space, relative to the files folder of a user"
  - "StorageService::providers: the mount list composed from the home providers plus the two switches"
  - "StorageService::mountRootPath: the internal path of one mount root, cached per request"
  - "POST /apps/findling/admin/rules: the only writing route of this phase, validated as a whole"
  - "AdminViewService::rules: the four switches in force plus the ceiling of the cap"
  - "Block five of the admin page: exclusion list, size cap in MB, two toggles, one primary button, inline feedback"
  - "Gate D (backend/tests/test_exclusion_path_space.py): one helper, one path space, one mount list"
affects: [04-09-raeumung-und-bestaetigung, 04-10, verify-work]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One helper plus one path-space method for a comparison that two call paths make, with a textual gate over both call sites"
    - "Code constants become the documented default of a configurable value instead of moving into the database"
    - "A setting clamped at what the second enforcement point reported, so the page never shows a number that does not hold"
    - "validate() next to save(), so a write route can refuse a whole form before it changes one value"
    - "Error codes rather than sentences across the trust boundary, so an answer cannot carry a value somebody typed"
    - "A row that has to appear at runtime is cloned from a template element, never assembled from a string"

key-files:
  created:
    - php/lib/Service/SettingsService.php
    - php/lib/Service/ExclusionService.php
    - backend/tests/test_exclusion_path_space.py
  modified:
    - php/lib/AppInfo/Application.php
    - php/lib/Service/StorageService.php
    - php/lib/BackgroundJobs/StorageCrawlJob.php
    - php/lib/Listener/FileEventListener.php
    - php/lib/Controller/SettingsController.php
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/l10n/de.json
    - php/l10n/de.js
    - backend/tests/test_php_trust_boundary.py
    - THIRD-PARTY.md

key-decisions:
  - "The exclusion filter does not go into getFilesInMount or getFileSlice, against the letter of the plan: both callers read nothing behind the cursor from an empty result, the crawl has to see an excluded file in order to count it, and the clearing of plan 04-09 walks the excluded subtree through getFilesInMount itself"
  - "A filter in getFileSlice would have been an index wipe: ReconcileController derives its final mark from fewer rows than asked for, and a final page lets the deletion rule of the reconcile drop its upper bound"
  - "No config lexicon is registered: the interface was renamed inside the declared version window, and a class reference that resolves on some servers and not others is a fatal error while booting rather than a missing feature"
  - "The size cap is clamped at the remembered container ceiling rather than warned about, so the field can never show a limit the container ignores"
  - "The validation text of the cap carries the real range as placeholders instead of the fixed 1 to 2048 MB of the copy table, because the ceiling is what the container reported"
  - "Block five is never rendered from a poll: it is a form somebody may be halfway through, and the stored values are written back only out of the answer of a save"
  - "The event listener asks for the prefix list before it resolves a mount root, so an instance without exclusions pays nothing on the write path"
  - "A deletion skips the exclusion test, because an excluded file that gets deleted still has to leave the index"

patterns-established:
  - "Gate D: a textual gate over two PHP call sites that have to share one comparison, with comment lines skipped so the gate cannot report its own documentation"
  - "Prose may not name an attribute or a DOM property that a textual gate matches on, because the anti vacuity clause counts mentions"

requirements-completed: [ADM-04]

# Metrics
duration: 33 min
completed: 2026-09-02
---

# Phase 4 Plan 08: Ausschluesse und Regeln Summary

**Four admin switches in appconfig, enforced at the crawl, the event listener and the mount list through exactly one exclusion helper in exactly one path space, with the size cap clamped at the ceiling the container reported**

## Performance

- **Duration:** 33 min
- **Started:** 2026-09-02T18:49:05Z
- **Completed:** 2026-09-02T19:21:38Z
- **Tasks:** 3 (task 2 in RED and GREEN)
- **Files modified:** 16 (3 created, 13 modified)

## Accomplishments

- Folder exclusions, size cap, Team Folders and external storage are appconfig keys with types, defaults and validation, and the next run applies them with nothing restarted and no container touched.
- The exclusion is one comparison in one path space. The crawl walks with the overridden root of a mount (`files`), the event listener with the storage root (the empty string), and `ExclusionService::mountRelativePath` lands both at the same value for the same file. Proven live: both spellings answer `Archiv/2024/x.pdf` for the same input.
- The external storage provider, a commented out line since phase 2 with the note that it becomes a switch in ADM-04, is live code behind that switch.
- The size cap is clamped between one megabyte and the ceiling the container last reported, so the field on the page can only hold a number the container also enforces. Without a reported ceiling the upper end is the code default both sides ship with.
- Block five saves all four rules with one button, refuses the whole form on one bad field, and answers with the rules as they are in force so the clamped value is visible rather than silently substituted.
- Gate D pins the whole construction textually: a hand rolled prefix comparison in either call site, a call site that never asks the helper, a second mount list, and the constant used as the cap in force are all reported.

## Task Commits

Each task was committed atomically:

1. **Task 1: the four keys, their validation and the one exclusion helper** - `e1b07c5` (feat)
2. **Task 2 RED: the path space gate** - `b89283b` (test)
3. **Task 2 GREEN: crawl, event listener and mount list obey the switches** - `e6e9edb` (feat)
4. **Task 3: block five saves the rules** - `c8f330a` (feat)
5. **Deviation: icon attribution** - `47379d1` (docs)

_Task 2 carried `tdd="true"`: the gate was committed red with four failing real tree checks and nine passing self tests, then made green by the implementation. No refactor commit was needed._

## Files Created/Modified

- `php/lib/Service/SettingsService.php` - the four appconfig keys, the clamped cap, the remembered container ceiling, `validate()` and `save()`
- `php/lib/Service/ExclusionService.php` - the prefix list, `normalise`, `isExcluded` and `mountRelativePath`
- `backend/tests/test_exclusion_path_space.py` - Gate D, four real tree checks and nine self tests
- `php/lib/Service/StorageService.php` - three provider lists, `providers()`, `mountRootPath()`, and the docblocks that record why the exclusion is not filtered here
- `php/lib/BackgroundJobs/StorageCrawlJob.php` - cap and root read once per slice, exclusion test before the size check, `excluded` counted
- `php/lib/Listener/FileEventListener.php` - the fourth question, the same helper on the same space, cap from the settings
- `php/lib/Controller/SettingsController.php` - `POST /admin/rules`, validated as a whole, no attribute that would weaken it
- `php/lib/Service/AdminViewService.php` - the `rules` subtree, `rememberContainerCap`, and the cap in force in stage two
- `php/templates/admin.php` - block five with the list, the cap field, the two checkbox pairs, the one primary button and the row template
- `php/js/admin.js` - local edits until save, field validation with the focus moved, the POST, inline feedback, the named D-07 hook
- `php/css/admin.css` - block five styling, every distance a grid multiple and every colour a theme variable
- `php/l10n/de.json`, `php/l10n/de.js` - the nineteen German texts of block five
- `backend/tests/test_php_trust_boundary.py` - route lower bound raised to eleven
- `THIRD-PARTY.md` - every icon path the page renders, named

## Decisions Made

See `key-decisions` in the frontmatter. The two that shape the next plan:

**The exclusion is applied by the callers, not by the enumeration.** `getFilesInMount` and `getFileSlice` hand out every row, and the crawl and the event listener each ask the one helper. See the deviation below for the three reasons.

**The clearing of plan 04-09 has exactly one path, not two.** Research pattern 9 describes a way A (`SubtreeExpandJob` with `kind => KIND_DELETE`) and a way B (the files drop out of the reconcile page, `Store.gone_in_range` turns them into delete rows). Way B does not exist after this plan and must not be built by filtering the slice. Way A is untouched and is the whole clearing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The exclusion filter is not in `getFilesInMount`, and not in `getFileSlice` either**

- **Found during:** Task 2 (crawl, event listener and mount list)
- **Issue:** The plan says `getFilesInMount()` applies the exclusion and `getFileSlice()` does not. Implemented literally, that breaks three things, each of them on its own enough to stop it:
  1. **The crawl stalls.** `StorageCrawlJob` ends a mount when a batch came back empty (`$seen === 0`), and `SubtreeExpandJob` does the same. One excluded folder holding a full batch of 2000 would end the crawl in the middle of the id range, permanently.
  2. **The `Excluded` tile stays at nought forever.** The crawl has to see an excluded file in order to count it, and the scan counter is the only record of an excluded file, because no row is written to `findling_file_state`. A filter there would make the promise of IDX-06, that nothing disappears quietly, unkeepable by construction.
  3. **The clearing of plan 04-09 becomes a no-op against its own target.** `SubtreeExpandJob` resolves the subtree of a newly excluded folder through `getFilesInMount` itself, so a filter there would make the delete expansion find nothing in exactly the folder it was planned for.
  On top of that, moving the filter into `getFileSlice` instead would have been worse than a stall. `ReconcileController::filesSlice` derives its final mark from `count($files) < $size`, and a final page lets `_missing_of` in the container drop the upper bound of the deletion rule. A page that lost three rows to a prefix would be declared final, and every file the container knows above the cursor would be reported as deleted: one exclusion would empty the index of a whole mount.
- **Fix:** Both enumerations hand out every row. `StorageCrawlJob` and `FileEventListener` each call `ExclusionService::isExcluded` on `ExclusionService::mountRelativePath`, which is the single comparison in the single space that the plan's real requirement asks for, and Gate D holds that both of them do. All three docblocks carry the reasoning.
- **Files modified:** `php/lib/Service/StorageService.php`, `php/lib/BackgroundJobs/StorageCrawlJob.php`, `php/lib/Listener/FileEventListener.php`
- **Verification:** Live on the dev instance with `exclusions=["Archiv"]`: after a full crawl restart, 98 queue rows and none of them under `Archiv/`, `Archivar.md` queued (the prefix does not over-match), `excluded: 1` in the scan totals, and all three mounts reported `mountsFinished == mountsTotal`, so nothing stalled. A write through the file API into `Archiv/` queued nothing while a write next to it queued file id 291.
- **Committed in:** `e6e9edb`

**2. [Rule 1 - Bug] Stage two of the diagnosis read the constant instead of the cap in force**

- **Found during:** Task 3 (block five)
- **Issue:** `AdminViewService::stageTwoRulesOfToday` compared the file size against `StorageCrawlJob::MAX_SIZE`. That method answers "does this file break a rule of TODAY", and the moment the cap became configurable the constant stopped being today's rule: an admin who had just raised the cap would be told their file is still too large, which is the contradiction between page and behaviour this phase exists to remove.
- **Fix:** The comparison reads `SettingsService::maxFileBytes()`. The now unused import of `StorageCrawlJob` was removed.
- **Files modified:** `php/lib/Service/AdminViewService.php`
- **Verification:** `php -l` clean; the rules subtree of a live `overview()` reports the stored cap (`20971520` at the time of the probe) while the ceiling stays `52428800`.
- **Committed in:** `c8f330a`

**3. [Rule 2 - Missing Critical] The new icon had no attribution**

- **Found during:** Task 3 (block five)
- **Issue:** The remove button of an exclusion row is the only icon-only control of the page and needs a glyph. The design contract lists eight icons, all of them states, and none of them is a cross, so `close` is a tenth Material Design Icons path in this repository with no row in `THIRD-PARTY.md`. The file's own rule says the row goes in "in the plan that first renders one of them", and it was also two plans behind: the five icons of 04-06 and 04-07 were rendered without being named.
- **Fix:** The table names all nine paths the page renders, with where each one lands, and the check command at the end of the file iterates over all nine. The stale paragraph about "the remaining five icons" is gone.
- **Files modified:** `THIRD-PARTY.md`
- **Verification:** All nine paths fetched from `Templarian/MaterialDesign-SVG` at the pinned commit `9e04201d4557e729822fb57f62a316c3dea1d4a8` and found byte identical in `php/templates/admin.php` and `php/img/app-dark.svg`.
- **Committed in:** `47379d1`

**4. [Rule 2 - Missing Critical] Block five had no stylesheet**

- **Found during:** Task 3 (block five)
- **Issue:** `php/css/admin.css` is not in the plan's file list, but the design contract binds every block to `max-width: 900px` and every click target to `var(--default-clickable-area)`, and it prescribes the two paired surfaces of the save feedback. Without the rules an icon-only button would be a sixteen pixel target and the feedback would be unstyled text.
- **Fix:** A block five section in the same shape as the existing ones: `#findling-rules` joined to the width rule, minimum heights on every control including the checkbox labels, the two feedback surfaces as theme variable pairs, no literal colour and no `outline: none`.
- **Files modified:** `php/css/admin.css`
- **Verification:** Gate C (`test_admin_ui_contract.py`) green, which is what judges literal colours and removed focus rings.
- **Committed in:** `c8f330a`

**5. [Rule 1 - Bug] The cap validation text named a range that does not hold**

- **Found during:** Task 3 (block five)
- **Issue:** The copy table of the design contract fixes the text at `Enter a size between 1 and 2048 MB.` The actual upper end is the ceiling the container reported, which is 50 MB on a default installation, so the message would have named a range four decades wide while the field refuses anything above 50.
- **Fix:** The source string is `Enter a size between %1$s and %2$s MB.` and the script fills it from the `max` attribute of the field. Same sentence shape, real numbers.
- **Files modified:** `php/templates/admin.php` (the `max` attribute), `php/js/admin.js`, `php/l10n/de.json`, `php/l10n/de.js`
- **Verification:** The route refuses both `0` and `99999 MB` with `{"maxFileBytes":"out_of_range"}` and HTTP 400, and appconfig is unchanged afterwards.
- **Committed in:** `c8f330a`

### Deliberate omission, sanctioned by the plan

**No config lexicon is registered.** The plan offers the option and instructs to leave it out with a written reason if the interface is not safely available in the target window. It is not: the interface arrived in Nextcloud 31 as `OCP\Config\Lexicon\IConfigLexicon` and was renamed inside the 32 to 35 window this app declares. A registration against either spelling resolves on some of those servers and not on others, and because appconfig works without it the failure would not be a missing feature but a fatal error while booting the app. `SettingsService` and `ExclusionService` therefore validate defensively on the way out as well as on the way in, which is what makes `occ config:app:set findling ...` safe without a lexicon. The reason is written into the docblock of `Application::register`.

---

**Total deviations:** 5 auto-fixed (3 bugs, 2 missing critical) plus one sanctioned omission
**Impact on plan:** Deviation 1 is the substantial one and it made the plan's own requirement reachable rather than reducing it: one helper, one path space, both call paths, held by a gate. Everything else is a correction inside the plan's own scope. No scope creep, no new dependency, no package installed, `php/composer.json` untouched and no `package.json` created.

## Verification

Plan level checks, all run:

| Check | Result |
|---|---|
| `cd backend && uv run python -m pytest -q` | 766 passed, 11 skipped |
| `uv run ruff check .` and `ruff format --check .` in `backend/` | clean, 78 files formatted |
| `php -l` over `lib/`, `appinfo/` and `templates/` in the dev container | only "No syntax errors detected" |
| `node --check php/js/admin.js` | clean |
| Gate A (`test_readonly_gate.py`), write allowlist | unchanged at three entries, `test_write_allowlist_has_exactly_three_entries` green |
| Gate B (`test_php_trust_boundary.py`) | green, route lower bound now 11, `FrontpageRoute` appears exactly 3 times in `SettingsController.php`, forbidden attributes 0 times |
| Gate C (`test_admin_ui_contract.py`) | green, `grep -c innerHTML php/js/admin.js` is 0, exactly one `.primary` line in the template |
| Gate D (`test_exclusion_path_space.py`) | green, 13 tests |
| Em dash or en dash in any changed file | none |

Live sight checks on the dev instance (port 8090, `docs/dev-setup.md`), through CLI probes that bootstrap Nextcloud, because a browserless login cannot pass CSRF:

| Sight check | Result |
|---|---|
| Both path spellings for the same file | `space(files/Archiv/2024/x.pdf, root="files")` and `space(..., root="")` both answer `Archiv/2024/x.pdf`, both excluded |
| Prefix does not over-match | `files/Archivar.pdf` is not excluded, and `Archivar.md` is in the queue |
| `normalise` refusals | `Archiv/../..`, `..`, `files`, `""` and `"   "` all refused; `/Archiv/`, `files/Archiv` and `files//Archiv//` all normalise to `Archiv` |
| Crawl obeys the exclusion (acceptance) | after `occ config:app:set findling exclusions --value '["Archiv"]'` and a full restart: 98 queue rows, 0 under `Archiv/`, scan totals `excluded: 1`, all 3 mounts finished |
| Event listener obeys the same rule (acceptance) | a write into `Archiv/` queued nothing (file id 290 absent), a write next to it queued file id 291 |
| Team Folders switch (acceptance) | `index_team_folders=0` removes `OCA\GroupFolders\Mount\MountProvider` from the composed list; `index_external_storage=1` adds `OCA\Files_External\Config\ConfigAdapter`. The mount count stays 3 because this instance has neither kind of mount |
| Sight check 8 of the UI contract | cap `0` and cap `99999 MB` both answer HTTP 400 with `{"maxFileBytes":"out_of_range"}`, and appconfig is byte for byte unchanged after five consecutive refusals: no half state |
| Cap ceiling in the markup | `<input type="number" ... min="1" max="50" step="1" value="20">`, that is the container ceiling in MB and the stored cap in MB |
| Block five with the backend stopped | rendered in full with real values while `backendReachable` was `false`, because appconfig lives in PHP |
| A save writes all four and normalises | `saveRules(['/Archiv/', 'files/Backups'], 30 MB, false, true)` stored `cap=31457280 list=["Archiv","Backups"] team=false external=true` and answered with the rules in force |
| The three admin routes resolve | `findling.settings.overview`, `.diagnose` and `.saveRules` all generate a URL |
| German texts | all 19 block five strings resolve through `IL10N('de')`, none untranslated |

**Assumption A1 of the research, verified (acceptance criterion).** `grep -rn 'store.record\|writer.add_document' backend/src/findling` finds exactly two call sites: `index/writer.py:217` and `worker/poller.py:901`. Tracing both upwards, the poller reaches a document only through `queue.claim(...)` in `nc/queue.py`, which is the PHP OCS route `GET /queues/documents`, and the reconcile reaches one only through `files.mounts()` and `files.page()` in `nc/files.py`, which are the PHP routes `GET /mounts` and `GET /files/slice`. `index/bench.py` is a benchmark tool and not on any indexing path. There is no path on which the container puts a file into the index without a PHP answer, so enforcing all four switches PHP-side is complete. Had there been one, an exclusion would not have held there and this plan would have been half a plan.

## Known Stubs

**`AdminViewService::excludedByAPrefix()` still returns null, and plan 04-09 wires it (that plan's own task list says so, and it owns the method body).**

What that means right now: the aggregate is right and the single file answer is not. Block one counts an excluded file in the `Excluded` tile and takes it out of the coverage denominator, so nothing disappears quietly at the level the phase promises. But the per file diagnosis of an excluded file falls through stage two to stage six and says "Not seen yet. This file has not reached the queue. The next comparison run picks it up." The first half is wrong and the second half is a promise that will not be kept, because the next run will leave the file alone again.

The must-have of this plan, "an excluded file appears in the diagnosis with the reason `excluded` and does not disappear quietly", is therefore met for the tile and not yet for the card.

**The hazard plan 04-09 has to resolve when it wires the method, and the reason this plan did not wire it anyway:** the value the hook receives is `$facts['path']` out of `PathResolverService::inspect`, which is the absolute path of the owner minus the `/<uid>/files/` prefix. For a file in a home that is already the exclusion path space exactly, so the wiring is a two line body. For a file on a **Team Folder** mount it is not: the display path has the same `/<uid>/files/` prefix stripped, so a Team Folder file arrives as `TeamX/x.pdf`, while the crawl compares it in the space of its own mount root and sees `x.pdf`. Wiring the hook without deciding that case creates a second path space inside the diagnosis, which is the precise failure Gate D exists to prevent one layer down. D-06 says prefixes apply only in user homes, so the likely answer is to test the hook only for a home mount, but that decision belongs with the plan that owns the method rather than being made in passing here.

## Issues Encountered

**Two textual gates match on plain text and therefore forbid their own vocabulary in prose.** Gate B counts every line that mentions `FrontpageRoute` and compares the count with the number of routes it parsed, so one sentence in the class docblock of `SettingsController` naming the attribute broke the gate without a route having changed. Gate C searches for the markup assigning properties of an element as substrings, so naming one in a comment of `admin.js` broke it too. Both were rephrased, and both files now carry a sentence saying that the name may not appear, so the next reader does not rediscover it. Research pitfall 7 predicted the first of the two for an import line; it applies to prose in the same way.

**A probe bug, not a code bug.** The first run of the German l10n probe stopped after four strings: `IL10N::t()` runs `vsprintf`, and PHP 8 throws when a conversion has no argument, so `t('Remove exclusion %s')` without a parameter aborted the script. The probe was given as many placeholder arguments as each string has. The template itself always passes the parameter.

**The route cache caveat did not bite.** The hint from the previous wave was that a new admin route answers 404 until the app container restarts, because the attribute route cache is keyed by app version and the version is pinned at 0.3.0. On this instance all three routes generated a URL without a restart, presumably because the `occ` runs in between invalidated the cache. The caveat still stands for an installed app that is only updated on disk, and it is worth remembering for the browser sight checks of plan 04-10.

## User Setup Required

None - no external service configuration required. The dev container was left in the shipped default state: the four appconfig keys were deleted again after the sight checks, so `occ config:list findling` shows only `last_job_run` and `first_index_scheduled` as before. Two probe files remain in the container corpus at `data/testuser/files/Archiv/alte-notiz.md` and `data/testuser/files/Archivar.md`; they are the pair that proves a prefix matches the folder and not a file whose name merely starts the same way, and they are useful for the sight checks of plan 04-09.

## Next Phase Readiness

Ready for 04-09. What that plan finds in place:

- `ExclusionService` with `prefixes`, `normalise`, `validate`, `save`, `isExcluded` and `mountRelativePath`, plus `MAX_PREFIXES` and `MAX_PREFIX_LENGTH` as named constants.
- `SettingsController::saveRules` as the single write, with the whole form validated before anything is written. The confirmation of D-07 hangs in front of the write in `admin.js`, in the named function `confirmNewExclusions(exclusions)`, which already receives the list and whose comment points at 04-09.
- `AdminViewService::rules()` as the shape both the page and the write answer use.

Two things it has to be told, and both are in this summary above rather than only here:

1. **Way B of research pattern 9 does not exist.** The excluded files are still in the reconcile page, so `Store.gone_in_range` does not turn them into delete rows. Way A, `SubtreeExpandJob` with `kind => KIND_DELETE`, is the whole clearing. Do not build way B by filtering `getFileSlice`: `ReconcileController` reads its final mark off the row count, and a filtered page would be declared final, which drops the upper bound of the deletion rule and empties the index of the mount.
2. **The `excludedByAPrefix` hook needs the Team Folder path space decided**, see Known Stubs.

The `excluded` reason code is still absent from `FileStateService::REASONS`, and that is correct for this plan: no row is ever written with it. Plan 04-09 adds it together with `backend/src/findling/extract/errors.py` and `backend/src/findling/store/repo.py` if it needs to write one, and the three way parity test will hold it.

## Self-Check: PASSED

- `php/lib/Service/SettingsService.php` FOUND
- `php/lib/Service/ExclusionService.php` FOUND
- `backend/tests/test_exclusion_path_space.py` FOUND
- Commit `e1b07c5` FOUND
- Commit `b89283b` FOUND
- Commit `e6e9edb` FOUND
- Commit `c8f330a` FOUND
- Commit `47379d1` FOUND

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*
