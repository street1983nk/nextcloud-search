---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 09
subsystem: api
tags: [php, nextcloud, background-jobs, queue, vanilla-js, exclusions, taxonomy]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "ExclusionService with prefixes, normalise, validate, save, isExcluded and mountRelativePath from plan 04-08, plus POST /admin/rules and the named confirmation hook in admin.js"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "AdminViewService::diagnose with the six stage precedence rule and the named excludedByAPrefix hook from plan 04-07"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "the reason label and remedy table of plan 04-06, which already carried the excluded row"
  - phase: 03-container-und-index
    provides: "SubtreeExpandJob with EXPANDABLE_KINDS including KIND_DELETE, QueueMapper::KIND_RANK and the _forget path of the poller"
provides:
  - "the reason code excluded in all three reason lists at once, so a verdict carrying it can be written and read on both sides"
  - "ExclusionService::scheduleCleanup: one SubtreeExpandJob with kind delete per new prefix and per mount it resolves in, and no new clearing code"
  - "ExclusionService::affectedDocuments: the preview figure of D-07, capped at a named ceiling"
  - "ExclusionService::newPrefixes: the one place a prefix counts as new, with nested entries reduced to their shortest member"
  - "ExclusionService::mountRelativePathInStorage: the exclusion path space for a caller that holds a storage instead of a mount root"
  - "StorageService::folderIdAtPath: a prefix as the ancestor file id the expansion job needs"
  - "PathResolverService::inspect carries internalPath, the space the exclusion is compared in"
  - "AdminViewService stage two answers skipped(excluded), which completes the precedence rule"
  - "AdminViewService::rules reports cleanupLatencyHours and restartCommand"
  - "GET /apps/findling/admin/rules/preview: the reading route the confirmation reads its number from"
  - "the inline destructive confirmation of block five, with the path, the document count and the sentence that the files stay on disk"
affects: [04-10, verify-work]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A destructive consequence is planned through an existing background job rather than a new write route, so a security allowlist does not have to grow for a feature"
    - "A preview is a reading route of its own, so the writing route never has a branch in which it does not write"
    - "A figure shown while somebody waits is capped at a named ceiling and reported as capped, so the page can say at least"
    - "A verdict that would cost one row per file is computed at the moment it is asked instead of being stored"
    - "An inline confirmation with the focus on the harmless choice, discarded by Escape and by any further edit of the form"

key-files:
  created: []
  modified:
    - php/lib/Service/FileStateService.php
    - backend/src/findling/extract/errors.py
    - backend/src/findling/store/repo.py
    - php/lib/Service/ExclusionService.php
    - php/lib/Service/StorageService.php
    - php/lib/Service/PathResolverService.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Controller/SettingsController.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/css/admin.css
    - php/l10n/de.json
    - php/l10n/de.js
    - backend/tests/test_php_trust_boundary.py

key-decisions:
  - "The clearing covers every mount the app walks and not only home mounts, against the letter of the plan: the enforcement of plan 04-08 compares a prefix relative to the root of every mount in the list, and clearing fewer mounts than the crawl excludes would leave index content that nothing removes, because way B of research pattern 9 does not exist"
  - "The docblock claim that prefixes apply in user homes only was corrected rather than made true in code: making it true would mean a home test in the crawl and in the event listener, which is a second condition in two call sites for a rule nobody asked to narrow"
  - "The diagnosis is fed the internal path plus the storage and not the display path, which is the hazard plan 04-08 wrote down: a Team Folder file arrives as TeamX/x.pdf in the display space and as x.pdf in the space the crawl compares"
  - "excluded is in FileStateService::REASONS although no writer of this app ever produces a row with it: the list is the vocabulary the reader validates against as well as the one the writer may use"
  - "affectedDocuments counts the documents the crawl would index under the path rather than reading the index itself, so the preview does not depend on the container answering; it is an upper bound and the sentence says nothing the count cannot support"
  - "A nested pair of new prefixes is reduced to its shortest member, so the preview does not count the same documents twice and the clearing does not plan a job over ground another job already walks"
  - "The capped signal is derived by the caller from the public PREVIEW_CAP constant, so affectedDocuments keeps the plain integer signature the plan gave it"
  - "A failed preview shows the confirmation without a figure instead of claiming nought documents, and it does not block the save"

patterns-established:
  - "One inverse pair per path space: mountRelativePath turns a path into the space, subtreesOfPrefix turns the space back into a node, and both live in the class that owns the space"
  - "A reason code may be added to the three lists only in one commit, and the parity gate is verified to go red on a partial edit before the full edit is made"

requirements-completed: [ADM-02, ADM-04]

# Metrics
duration: 22 min
completed: 2026-09-02
---

# Phase 4 Plan 09: Raeumung und Bestaetigung Summary

**A new exclusion clears the index through the existing band walker with kind delete, one job per prefix and mount, and the admin sees the path and the document count in an inline confirmation before the write happens**

## Performance

- **Duration:** 22 min
- **Started:** 2026-09-02T19:26:36Z
- **Completed:** 2026-09-02T19:49:06Z
- **Tasks:** 3
- **Files modified:** 14

## Accomplishments

- The reason `excluded` is in all three reason lists in one commit, and the parity gate was verified to catch a partial edit before the edit was made: adding one entry to `errors.py` alone turns `test_extract_errors.py` red.
- A new exclusion clears the index with no new clearing code at all. `ExclusionService::scheduleCleanup` plans one `SubtreeExpandJob` with `kind => delete` per new prefix and per mount the prefix resolves in, and the mechanism from phase 3 does the rest. Proven live: saving `Archiv` planned one job, executing that job wrote two delete rows for the two documents under the folder and planned its own successor with the cursor at the last id.
- The write allowlist of the read only gate is untouched at three entries. Nothing about the clearing crosses the HTTP boundary; it is PHP writing a job argument into the Nextcloud job list.
- Stage two of the precedence rule is complete. An excluded file that exists answers `skipped(excluded)` with the label and remedy of the closed table, ahead of stage five, so a tombstone left behind by the clearing is never read as a deleted file. Proven live: `testuser/files/Archiv/alte-notiz.md` answers "Excluded by a rule" while `Archivar.md` next to it does not.
- The hazard plan 04-08 left open is resolved rather than avoided: `mountRelativePathInStorage` looks the mount up and lands the diagnosis in the same space the crawl compares in, so there is no second path space in the diagnosis and a Team Folder file is judged by the rule that really applies to it.
- The confirmation names the consequence with a figure: path, document count, and the sentence that the files themselves stay on disk. The count is capped at 5000 and reported as capped, so the page says "at least" rather than making somebody wait for an exact number.
- The page names the one thing this phase cannot make immediate: taking an exclusion back heals itself through the comparison run, which takes up to 24 hours, and the sentence gives `occ findling:index --restart` as the way around the wait.

## Task Commits

Each task was committed atomically:

1. **Task 1: the reason excluded in all three lists, in one operation** - `ea244d3` (feat)
2. **Task 2: the clearing, the preview and stage two of the precedence rule** - `9aa8333` (feat)
3. **Task 3: the inline confirmation and the latency sentence** - `d2bb764` (feat)

**Plan metadata:** see the docs commit of this plan.

_Task 1 carried `tdd="true"`. There was no new test to write: the two parity comparisons exist since phase 3 and are red for any partial edit by construction. That property was measured rather than assumed, by adding one entry to `errors.py` alone and watching `test_extract_errors.py` fail, and the tree was restored before the real edit. Committing that red state would have contradicted the plan's own instruction that the three lists change in one operation._

## Files Created/Modified

- `php/lib/Service/FileStateService.php` - `'excluded'` in the skipped block, plus the docblock paragraph saying it is never written per file and why
- `backend/src/findling/extract/errors.py` - `Reason.EXCLUDED` and its entry in `STATE_REASONS[State.SKIPPED]`
- `backend/src/findling/store/repo.py` - `"excluded"` in `STATE_REASONS["skipped"]`, same order
- `php/lib/Service/ExclusionService.php` - `newPrefixes`, `affectedDocuments`, `scheduleCleanup`, `subtreesOfPrefix`, `withoutNested`, `mountRelativePathInStorage`, `PREVIEW_CAP`, `PREVIEW_BAND`, and the corrected paragraph about where prefixes apply
- `php/lib/Service/StorageService.php` - `folderIdAtPath`, the inverse of `mountRootPath`
- `php/lib/Service/PathResolverService.php` - `inspect` carries `internalPath`, out of the cache entry it already holds
- `php/lib/Service/AdminViewService.php` - stage two answers `skipped(excluded)`, `rules()` reports the latency and the command, two container constants named
- `php/lib/Controller/SettingsController.php` - `GET /admin/rules/preview`, and the class docblock rewritten from three routes to four
- `php/templates/admin.php` - the confirmation area over the save button, the latency sentence, the two buttons
- `php/js/admin.js` - the preview call, the confirmation, the focus rules, Escape, and `saveRules(confirmed)`
- `php/css/admin.css` - the one destructive surface of the page and its accept button
- `php/l10n/de.json`, `php/l10n/de.js` - six German strings: the destructive text in both variants, "mindestens", both buttons, the latency sentence
- `backend/tests/test_php_trust_boundary.py` - route lower bound raised to twelve

## Decisions Made

See `key-decisions` in the frontmatter. The two that matter for the next plan:

**The clearing follows the enforcement, not the documentation.** Plan 04-08 applies a prefix relative to the root of every mount the app walks; its docblock said homes only. This plan made all three places agree by taking the code as the rule: the crawl leaves out, `scheduleCleanup` removes and the diagnosis explains the same set of files. The docblock now says so.

**The preview figure is an upper bound and says nothing more.** It counts what `getFilesInMount` hands out under the folder, so the mimetype filter of the crawl is part of it, and a document under the path that was skipped or never reached is counted although it has nothing to remove. The exact number lives in the container, and a confirmation that needs the container to answer is a confirmation that fails when the container is down.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `StorageService::folderIdAtPath` had to exist, in a file the plan does not list**

- **Found during:** Task 2 (the clearing)
- **Issue:** `scheduleCleanup` needs the file id of the folder a prefix names, and the plan says to resolve it without saying where. `ExclusionService` cannot: the file cache is reached through `IFileAccess`, and the class docblock of `StorageService` says it is the only place in this app that touches it. Building a second cache access inside `ExclusionService` would have been a second answer to "what is at this path".
- **Fix:** `StorageService::folderIdAtPath` using `IFileAccess::getByPathInStorage`, nought for anything that is not a folder and nought for a path that does not exist on that storage. It is the documented inverse of `mountRootPath`, next to it in the same file.
- **Files modified:** `php/lib/Service/StorageService.php`
- **Verification:** Live on the dev instance: `files/Archiv` resolves to 288 on the storage of `testuser` and to nought on the two other home storages. Gate D still reports exactly one mount list.
- **Committed in:** `9aa8333`

**2. [Rule 3 - Blocking] The diagnosis needed the internal path, so `PathResolverService::inspect` carries it**

- **Found during:** Task 2 (stage two of the precedence rule)
- **Issue:** The hook received `$facts['path']`, which is the display path in the home of the owner. For a home file that is the exclusion space exactly and for a Team Folder file it is not: the display path carries the name of the mount point, the crawl compares under the mount root. Wiring the hook to that value would have put a second path space inside the diagnosis, which is precisely the failure Gate D exists to prevent one layer down, and it would have produced both false hits and false misses.
- **Fix:** `inspect()` also returns `internalPath` out of the cache entry it already holds, so it costs no query, and `ExclusionService::mountRelativePathInStorage` turns storage plus internal path into the one space by looking up the deepest mount root of this app that the path lies under. The three phpdoc shapes of the facts array were widened with it.
- **Files modified:** `php/lib/Service/PathResolverService.php`, `php/lib/Service/AdminViewService.php`, `php/lib/Service/ExclusionService.php`
- **Verification:** Live: a file under `files/Archiv` answers `skipped(excluded)`, `Archivar.md` next to it does not, and the answer holds with the container unreachable because stage two needs no container.
- **Committed in:** `9aa8333`

**3. [Rule 1 - Bug] The clearing covers every mount of the list, not only home mounts**

- **Found during:** Task 2 (the clearing)
- **Issue:** The plan says "per new prefix and per home mount". The enforcement of plan 04-08 does not work that way: the crawl compares `mountRelativePath(entry, mountRoot)` for every mount of the composed list, so a prefix also names a folder at the top of a Team Folder. Clearing home mounts only would leave the documents of such a folder in the index for good, because way B of research pattern 9 does not exist after plan 04-08 and nothing else would remove them. That is the ghost content D-07 exists to prevent.
- **Fix:** `subtreesOfPrefix` walks `StorageService::getMounts()`, which is the one mount list, and yields one subtree per mount the prefix resolves in. The paragraph in the class docblock that claimed homes only was replaced by what actually holds, with the reason written next to it.
- **Files modified:** `php/lib/Service/ExclusionService.php`
- **Verification:** Live: three home mounts on the instance, the prefix resolves in one of them, one job planned. Gate D green, so both call sites still share the one comparison and the one space.
- **Committed in:** `9aa8333`

**4. [Rule 1 - Bug] The placeholders of the destructive text are numbered, and there is a second variant without a figure**

- **Found during:** Task 3 (the confirmation)
- **Issue:** The copy table spells the sentence with `%s` for the path and `%n` for the count. `%n` is the plural placeholder of the Nextcloud translation API, and this sentence is filled by the script with a value that is not always a number: when the count ran into its ceiling the figure is the phrase "at least 5000", so a plural form would be selected from a number that is not the one on the screen. And when the preview request fails there is no number at all.
- **Fix:** Two source strings with numbered placeholders, `%1$s` for the path and `%2$s` for the figure, and a second variant that names the consequence without a figure for the failed preview. Same sentence shape, same German wording, including "Die Dateien selbst bleiben unverändert auf der Platte." word for word. The same reasoning as deviation 5 of plan 04-08.
- **Files modified:** `php/js/admin.js`, `php/l10n/de.json`, `php/l10n/de.js`
- **Verification:** All six new strings resolve through `IL10N('de')` on the live instance, none untranslated.
- **Committed in:** `d2bb764`

**5. [Rule 2 - Missing Critical] The confirmation area needed its own stylesheet rules**

- **Found during:** Task 3 (the confirmation)
- **Issue:** The plan allows this explicitly ("braucht der Bestaetigungsbereich eigene Regeln"), and it does: without them the destructive surface, the container radius, the sixteen pixels of padding and the minimum height of both buttons would not exist, and the accept button would look like the cancel button.
- **Fix:** A section in the same shape as the existing ones: the error surface with its paired text colour, `--color-element-error` on the icon and on the accept button with `--color-primary-element-text` on top of it, every distance a grid multiple, no literal colour, no removed focus ring.
- **Files modified:** `php/css/admin.css`
- **Verification:** Gate C green, which is what judges literal colours and removed focus rings.
- **Committed in:** `d2bb764`

**6. [Rule 2 - Missing Critical] A standing confirmation is discarded when the form changes**

- **Found during:** Task 3 (the confirmation)
- **Issue:** Not in the plan and needed: the box states a number for one list, and the list stays editable while it stands. Accepting a confirmation that was computed for a different list would write a rule nobody was shown the consequence of.
- **Fix:** `touched()`, which every field change and every list edit already calls, hides the confirmation and gives the save button back.
- **Files modified:** `php/js/admin.js`
- **Verification:** `node --check` clean; the mechanism is one call in the existing handler and is listed for the browser sight check below.
- **Committed in:** `d2bb764`

---

**Total deviations:** 6 auto-fixed (3 blocking or bug, 3 missing critical)
**Impact on plan:** Deviations 1 to 3 are what made the plan's own requirement reachable: one rule for enforcement, clearing and diagnosis, in one path space, with no second cache access and no second mount list. The rest are corrections inside the plan's own scope. No new dependency, no package installed, no new writing container route, and the write allowlist of the read only gate is byte for byte unchanged.

## Verification

Plan level checks, all run:

| Check | Result |
|---|---|
| `cd backend && uv run python -m pytest -q` | 766 passed, 11 skipped |
| `uv run ruff check .`, `ruff format --check .`, `pyright`, `vulture src tests --min-confidence 80` | all clean, 78 files formatted, 0 errors |
| `php -l` over `lib/`, `appinfo/` and `templates/` in the dev container | only "No syntax errors detected" |
| `node --check php/js/admin.js` | clean |
| Gate A (`test_readonly_gate.py`) | green, write allowlist unchanged at three entries |
| Gate B (`test_php_trust_boundary.py`) | green, lower bound now 12, `FrontpageRoute` exactly 4 times in `SettingsController.php`, forbidden attributes 0 times |
| Gate C (`test_admin_ui_contract.py`) | green, `confirmDestructive` 0 times and `innerHTML` 0 times in `admin.js` |
| Gate D (`test_exclusion_path_space.py`) | green, one mount list, both call sites through the one helper |
| Parity gate red on a partial edit | measured: one entry added to `errors.py` alone fails `test_the_taxonomy_is_identical_to_the_one_the_state_store_enforces` |
| `grep -c "'excluded'" FileStateService.php` / `EXCLUDED errors.py` / `"excluded" repo.py` | 1 / 2 / 1, and `const REASONS = [` still exactly once |
| Em dash or en dash in any changed file | none |

Live checks on the dev instance (port 8090, `docs/dev-setup.md`), through CLI probes that bootstrap Nextcloud, because a browserless login cannot pass CSRF:

| Check | Result |
|---|---|
| Prefix resolves to an ancestor id | `files/Archiv` is 288 on storage 3, nought on the two other home storages |
| `newPrefixes` normalises and reduces | `['/Archiv/', 'files/Archiv/2024', 'Archiv']` becomes `['Archiv']`: one rule, nested entry dropped |
| `affectedDocuments` | 2 for `Archiv`, which is the two markdown documents under it, ceiling 5000 |
| A save plans the clearing (acceptance) | `save(['Archiv'])` planned exactly one job: `{"storage_id":3,"root_id":80,"ancestor_id":288,"kind":"delete","last_file_id":0}` |
| Saving the same list again | no second job and no second prefix, so a repeated save is free |
| The planned job clears (acceptance) | executing it wrote `delete` rows for file 289 and 290 and planned its successor with `last_file_id: 290`. Those two rows are the whole queue afterwards, so nothing else was touched |
| Diagnosis of an excluded file (acceptance) | `testuser/files/Archiv/alte-notiz.md` answers `skipped` / `excluded` / "Excluded by a rule" / "Remove the matching entry under \"Excluded folders\".", with the container unreachable |
| The prefix does not over-match in the diagnosis | `testuser/files/Archivar.md` is not excluded |
| `rules()` subtree | carries `cleanupLatencyHours: 24` and `restartCommand: occ findling:index --restart` next to the four switches |
| The preview route answers | `previewRules(['/Archiv/', 'Archiv/2024'])` with `Archiv` in force answers `{"newPrefixes":["Archiv\/2024"],"affectedDocuments":0,"capped":false}` |
| The preview refuses what the write refuses | `['Archiv/../..']` answers 400 with `{"exclusions":["traversal"]}` |
| The rendered page | the confirmation area is present and `hidden` in the ground state, with `role="group"`, `aria-labelledby` on its text, the `alert-circle-outline` path, both buttons, and the latency sentence naming 24 hours and the command |
| German texts | all six new strings resolve through `IL10N('de')`, including "Ausschließen und entfernen", "Dateien indexiert lassen", "mindestens %s" and both destructive variants |

**The instance was left in the shipped default state.** The `exclusions` key was deleted again, the expansion job was removed and the two `delete` queue rows were deleted, so `findling_queue` is empty and `config:list findling` shows what it showed before. The two probe files `Archiv/alte-notiz.md` and `Archivar.md` stay in the corpus, as they did after plan 04-08.

## Known Stubs

None. `AdminViewService::excludedByAPrefix`, the stub plan 04-08 handed over, has a body and answers.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: information_disclosure | php/lib/Controller/SettingsController.php | The preview answer carries the normalised new prefixes back, which is the one value of this page that travels outwards. It is the value the same admin session sent in the same request, it is needed because a confirmation has to name the path it is about, and it goes into a text node and never into the log. Named here so the phase verifier judges it rather than discovering it. |

## Issues Encountered

**The two sight checks that need a browser were not run.** Sight check 7 (add an exclusion, confirm, find the files with the reason afterwards) and sight check 10 (confirm and discard with the keyboard alone, Escape discards) are judgements about a rendered page and a focus ring, and this executor has no browser session: a browserless login cannot pass CSRF, which is why every live check above runs as a CLI probe. What was verified instead: every server side half of check 7 end to end, including the number the box shows, the job the confirmation causes, the delete rows that job writes and the diagnosis afterwards; and for check 10 the markup, the `hidden` ground state, the labelled group, the two real buttons and the handlers that move the focus to the harmless one and listen for Escape. The remaining part is the visual and keyboard pass of plan 04-10 and of `/gsd:verify-work`, in light, dark and high contrast.

**A comparison that reduces itself.** `newPrefixes` compares against the stored list, and the script has to hold that list in a variable rather than reading it off the page: the list on the page IS the input, so comparing it with itself finds nothing new ever. The snapshot is taken before any handler is wired and replaced out of the answer of a save, so the same prefix cannot ask for a confirmation twice for a clearing that already happened.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for 04-10. What that plan finds in place:

- `excluded` is a first class reason: in the three lists, in the label table, in the chip inventory of the template and in the diagnosis. Nothing on the page can show it as a raw code.
- Four admin routes, three reading and one writing, and the write allowlist of the read only gate still at three entries. Gate B stands at twelve routes.
- The confirmation is wired in `admin.js` in `confirmNewExclusions`, and `saveRules(confirmed)` is the one entry point of the write, called once from the button and once from the accept button.
- The destructive surface exists exactly once in `admin.css`, which is the contract's rule for it.

Two things to carry forward:

1. **The browser sight checks of the design contract are outstanding for block five**, checks 7 and 10 above, and they are cheap to run once a browser session exists.
2. **The preview figure is an upper bound of what leaves the index**, not a reading of the index. If a later plan wants the exact figure it has to come from the container, and then the confirmation has to keep working while the container is silent.

## Self-Check: PASSED

- `php/lib/Service/ExclusionService.php` FOUND
- `php/lib/Service/StorageService.php` FOUND
- `php/lib/Controller/SettingsController.php` FOUND
- `php/templates/admin.php` FOUND
- `php/js/admin.js` FOUND
- `php/l10n/de.json` FOUND
- Commit `ea244d3` FOUND
- Commit `9aa8333` FOUND
- Commit `d2bb764` FOUND

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*
