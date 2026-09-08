---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 03
subsystem: ui
tags: [nextcloud-settings, iiconsection, isettings, initial-state, vanilla-js, appapi, admin-page, l10n, mdi]

# Dependency graph
requires:
  - phase: 04-01
    provides: "Gate B with two route classes, the admin route rules and the settings finding step in php.yml"
  - phase: 04-02
    provides: "the seventeen status fields of GET /status, including truncated, reasons, disk figures and maxFileBytes"
  - phase: 02
    provides: "FileStateService with counts(), QueueService with stats(), SchedulerJob::LAST_JOB_RUN, ExAppService"
provides:
  - "Verwaltung > Findling as a registered IIconSection with icon, German copy and icon attribution"
  - "AdminViewService: the single aggregation of findling_file_state, findling_queue, appconfig and GET /status"
  - "SettingsController with one admin-only frontpage route GET /apps/findling/admin/overview"
  - "ExAppService::adminGet, a reading GET path with its own two second ceiling"
  - "Block one of the admin page, server side rendered and refreshed by polling without a reload"
  - "Gate C (test_admin_ui_contract.py): the textually checkable prohibitions of the design contract"
affects: [04-04, 04-05, 04-06, 04-07, 04-08]

# Tech tracking
tech-stack:
  added: ["Material Design Icons path data (Pictogrammers, Apache-2.0), pinned at commit 9e04201d4557e729822fb57f62a316c3dea1d4a8"]
  patterns:
    - "One aggregation service, two consumers: the template renders it and the initial state carries it"
    - "Admin route protection by absence: no NoAdminRequired, no NoCSRFRequired, no PublicPage, no ExAppRequired"
    - "Pick, never add: indexedDisplay chooses between the container figure and the Nextcloud figure"
    - "Textual gate over PHP, CSS and JS sources, in the shape of Gate A and Gate B"

key-files:
  created:
    - php/lib/Settings/Section.php
    - php/lib/Settings/Admin.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Controller/SettingsController.php
    - php/templates/admin.php
    - php/css/admin.css
    - php/js/admin.js
    - php/img/app-dark.svg
    - php/l10n/de.json
    - php/l10n/de.js
    - backend/tests/test_admin_ui_contract.py
  modified:
    - php/appinfo/info.xml
    - php/lib/Service/ExAppService.php
    - backend/tests/test_php_trust_boundary.py
    - THIRD-PARTY.md

key-decisions:
  - "The Override attribute is deliberately absent from the two new Settings classes: it is PHP 8.3 and info.xml declares php min-version 8.2. Provider.php keeps it and the asymmetry is named in both new docblocks."
  - "The status line carries no estimate of the time left while indexing runs. The design contract forbids a guessed figure that looks like a measurement, and the throughput needed to estimate honestly is calibrated by a later plan; the sentence says what is known instead."
  - "indexedDisplay picks the container figure while the container answers and the findling_file_state figure while it does not, so the tile never reads zero because a request failed. Both sources stay visible separately under indexed and backend.indexed."
  - "The stall threshold is 1800 seconds: every job of this app is a QueuedJob, so the cadence of the indexing is the cadence of the cron, and half an hour is six missed rounds of the five minute system cron."
  - "SettingsController extends Controller and not OCSController, keeping the route out of the OCS space so the write allowlist of the read-only gate stays at three entries."
  - "The four forbidden attribute names are never spelled out in SettingsController.php, so a grep for them over that class stays at zero and the gate is the only place that names them."
  - "Reason codes from the container are filtered by shape and not against FileStateService::REASONS, so a legitimate new code of a newer container stays visible as the drift signal while a path or markup never reaches the page."

patterns-established:
  - "Banner slot: every banner is rendered and toggled with the hidden attribute, so the script owns no markup"
  - "Every element the script updates carries an id; the script only ever writes textContent"
  - "Server side and client side number formatting agree: NumberFormatter in PHP, Intl.NumberFormat in JS, same locale source"

requirements-completed: [ADM-01]

# Metrics
duration: 47 min
completed: 2026-09-02
---

# Phase 04 Plan 03: Admin section, aggregation route and coverage block Summary

**Verwaltung > Findling exists: an IIconSection with a server side rendered coverage block whose four tiles, work stock and run state come from one admin-only PHP route that merges findling_file_state, findling_queue, appconfig and the container status, and which refreshes itself by polling without ever resetting a number to zero.**

## Performance

- **Duration:** 47 min
- **Started:** 2026-09-02T16:15:00Z
- **Completed:** 2026-09-02T17:02:32Z
- **Tasks:** 3
- **Files modified:** 15 (11 created, 4 modified, 1771 insertions)

## Accomplishments

- The administration navigation carries a Findling section with an MDI magnify icon, at `/settings/admin/findling`, registered through the `<settings>` block of `info.xml` because `IRegistrationContext` has no `registerSettings()`.
- `AdminViewService::overview()` is the one place where the two number sources meet. Verified live on the dev instance: the route answers `indexedDisplay: 94` out of the container next to `failed: 1` out of `findling_file_state`, with `backendReachable: true` and the seventeen container fields under their own key.
- The page is legible without JavaScript: block one renders banners, the empty state, the status line, the work stock chips and the four tiles server side, in English and in German with real umlauts.
- `admin.js` polls one address at 5 s while work is waiting and 30 s at rest, pauses on a hidden tab, keeps exactly one request in flight through `AbortController`, throttles after 20 unchanged polls and writes only text nodes.
- Gate C is the third textual gate of this repository and pins seven prohibitions of the design contract over three files that have no tooling of their own.

## Task Commits

1. **Task 1: the section is registered and carries icon, translation and attribution** - `5edd729` (feat)
2. **Task 2: one admin-only route delivers the merged numbers** - `a1d6f05` (feat)
3. **Task 3: block one is legible server side and refreshes without a reload** - `57fb0ec` (feat)

## Files Created/Modified

- `php/appinfo/info.xml` - the `<settings>` block after `<commands>`, one line, with the reason it is the registration
- `php/lib/Settings/Section.php` - `IIconSection` with id `findling`, priority 75, the app icon
- `php/lib/Settings/Admin.php` - `ISettings::getForm()`, one aggregation into both the initial state and the template, `RENDER_AS_BLANK`
- `php/lib/Service/AdminViewService.php` - the aggregation, the run state derivation, and the field by field rebuild of the container answer
- `php/lib/Controller/SettingsController.php` - `GET /apps/findling/admin/overview`, protected by what it does not carry
- `php/lib/Service/ExAppService.php` - `adminGet()` with `ADMIN_REQUEST_TIMEOUT_SECONDS = 2.0` and the four failure cases, plus the shared pre-flight helper
- `php/templates/admin.php` - block one, every string through `$l->t()`, every value through `p()`
- `php/css/admin.css` - only what the server CSS lacks: block width, chips, tiles, the progress height override, path wrapping
- `php/js/admin.js` - initial state reader, fresh token per call, polling contract, text node updates
- `php/img/app-dark.svg` - MDI magnify, `currentColor`, no literal colour
- `php/l10n/de.json`, `php/l10n/de.js` - 24 German strings including three duration plurals
- `THIRD-PARTY.md` - Pictogrammers MDI, Apache-2.0, pinned commit, the three paths used and the command to check them
- `backend/tests/test_php_trust_boundary.py` - route floor raised from 8 to 9
- `backend/tests/test_admin_ui_contract.py` - Gate C, 13 tests

## Decisions Made

See `key-decisions` in the frontmatter. The three that shape later plans:

1. **`indexable` is zero and the empty state is therefore a live branch, not dead code.** The denominator of the coverage figure needs the metadata scan counter of plan 04-04. Until it exists the template renders "No numbers yet" and no percentage, which is the design contract's own edge case for `indexable == 0`, not a simplification. The percentage, the `<progress>` element and the subline are fully implemented behind that branch and switch on the day `overview()` returns a non zero `indexable`.
2. **The container view of `skipped` and `failed` is carried in the answer and not displayed.** Measured on the dev instance: `findling_file_state` holds 0 skipped rows while the container reports 22. The split is the one Pitfall 3 prescribes and the UI spec's deliberate deviation from research Open Question 5 (five blocks, no "advanced" area). Plan 04-05 owns the error list and should decide there whether the container view of the same two figures needs a second home, because the difference is a diagnostic signal and a reader of the page cannot see it today.
3. **Admin route protection is protection by absence, and the gate is the only place that names the four attributes.** Empirically confirmed against the dev instance below.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Copy for the never-run status line**
- **Found during:** Task 1 (l10n)
- **Issue:** The plan's `runState` has four values, the design contract's copy table has three status sentences. `never_run` had no text, and reusing the stalled sentence ("has not progressed for %s") would have claimed a duration for a run that never happened.
- **Fix:** Added `No background job of this app has run yet. Background jobs may not be running.` with the German translation, phrased from the existing `IndexCommand::status()` wording so both places say the same thing.
- **Files modified:** php/l10n/de.json, php/l10n/de.js, php/templates/admin.php
- **Verification:** rendered live in English and German
- **Committed in:** `5edd729`, `57fb0ec`

**2. [Rule 2 - Missing Critical] Copy for the work stock, which a must-have demands**
- **Found during:** Task 1 (l10n)
- **Issue:** "how many wait" is one of the plan's truths, and no copy row covered a queue count. The four tiles are fixed by the contract and none of them is the queue.
- **Fix:** Two chips using the German labels the contract's state inventory already fixes (`Wartet in der Warteschlange`, `Wird gerade verarbeitet`) with English source strings chosen to match, rendered in the chip build the contract specifies. The processing chip is hidden while nothing is processing, so the core spinner never spins over a zero.
- **Files modified:** php/l10n/de.json, php/l10n/de.js, php/templates/admin.php, php/css/admin.css, php/js/admin.js
- **Verification:** rendered live, chip hidden at `running == 0`
- **Committed in:** `5edd729`, `57fb0ec`

**3. [Rule 2 - Missing Critical] Duration plurals and the estimate-free running sentence**
- **Found during:** Task 3 (status line)
- **Issue:** `Indexing has not progressed for %s` needs a duration, and `IL10N::l()` has no number or duration case in Nextcloud 32 to 34 (checked in the container: only date, datetime, time and weekdayName). `Indexing, about %s left` needs a throughput estimate that does not exist in this phase, and the contract forbids a guessed figure that looks like a measurement.
- **Fix:** Three plural pairs (`%n minute`, `%n hour`, `%n day`) in both l10n files, formatted in PHP with `$l->n()` and in JS with `n()` so both halves agree, plus one estimate-free sentence `Indexing is running.` The contract string for the estimate stays in l10n unused until the plan that can fill it honestly.
- **Files modified:** php/l10n/de.json, php/l10n/de.js, php/templates/admin.php, php/js/admin.js
- **Verification:** German status line rendered live as "Aktuell, letzte Prüfung Gestern"
- **Committed in:** `57fb0ec`

**4. [Rule 2 - Missing Critical] Copy for a failed refresh of this page**
- **Found during:** Task 3 (polling)
- **Issue:** The contract's error text names the backend. A failed poll of this app's own route is a different failure, and saying "the backend does not answer" would be a guess about the cause.
- **Fix:** A second, distinct banner: `The numbers could not be refreshed. The figures below are the last ones this page received.` Numbers stay untouched and the polling continues at the slow cadence.
- **Files modified:** php/l10n/de.json, php/l10n/de.js, php/templates/admin.php, php/js/admin.js
- **Committed in:** `57fb0ec`

**5. [Rule 2 - Missing Critical] Attribution for the third icon**
- **Found during:** Task 3 (the queued chip)
- **Issue:** The chip build of the contract is icon plus label plus surface, so the queued chip needs `clock-outline`. THIRD-PARTY.md, written in task 1, listed only the two icons known then, and shipping path data without attribution is a licence defect.
- **Fix:** `clock-outline` moved into the used list and into the verification command; `information-outline` moved to the not-yet-rendered list, since no banner needed it (all four banners are warning or error, so they carry `alert-circle-outline`). All three used paths verified byte identical against the pinned upstream commit.
- **Files modified:** THIRD-PARTY.md (outside task 3's file list)
- **Committed in:** `57fb0ec`

**6. [Rule 3 - Blocking] The pre-flight of the container call was about to exist twice**
- **Found during:** Task 2 (ExAppService)
- **Issue:** `adminGet()` needs the same three checks as `call()` (real user, `app_api` enabled, AppAPI resolvable). Copying them would mean two places deciding what this app does without AppAPI.
- **Fix:** Extracted `publicFunctions()`; both callers use it. The four failure cases stay written out in both methods, as the plan requires, because their order is the load bearing part.
- **Verification:** `tests/test_php_trust_boundary.py`, `tests/test_readonly_gate.py`, `php -l` over the whole tree, and the live search path still answering on the dev instance
- **Committed in:** `a1d6f05`

**7. [Rule 1 - Bug] The two new Settings docblocks tripped their own acceptance grep**
- **Found during:** Task 1 (acceptance loop)
- **Issue:** The docblocks explained the decision by writing the Override attribute out verbatim, so `grep -r 'Override' php/lib/Settings/` matched the literal attribute the criterion requires to be absent.
- **Fix:** Both docblocks name the attribute in prose instead. The same rule applied to SettingsController.php, whose docblock originally named two of the four forbidden attributes and is now written so a grep for all four returns zero.
- **Committed in:** `5edd729`, `a1d6f05`

---

**Total deviations:** 7 auto-fixed (5 missing critical, 1 blocking, 1 bug)
**Impact on plan:** No scope creep. Five of the seven are copy the design contract left open for states this plan is the first to render; one is a de-duplication inside a file the plan already assigns to this task; one is a self inflicted grep collision. Nothing was added that the plan did not ask to be visible.

## Verification Results

| Check | Result |
|---|---|
| `pytest tests/test_php_trust_boundary.py tests/test_readonly_gate.py tests/test_extract_errors.py tests/test_admin_ui_contract.py -q` | 102 passed |
| `ruff check .` and `ruff format --check .` in `backend` | clean, 73 files formatted |
| `php -l` over `lib`, `appinfo` and `templates` in the dev container | no syntax errors in any file |
| `grep -c FrontpageRoute` in SettingsController.php | 1 |
| `grep -c 'NoAdminRequired\|NoCSRFRequired\|PublicPage\|ExAppRequired'` in SettingsController.php | 0 |
| `grep -c 'is_array($response)'` in ExAppService.php | 2 |
| Em dash or en dash in any of the 15 files | none |
| `/apps/findling/admin/overview` anonymous | **401** |
| `/apps/findling/admin/overview` as `testuser` (not an admin) | **403** (T-04-11 confirmed) |
| `/apps/findling/admin/overview` as `admin` without the token | **412 CSRF check failed** (T-04-13 confirmed) |
| `/apps/findling/admin/overview` as an admin session with the token | **200**, both sources separated: `indexedDisplay: 94`, `failed: 1`, `backendReachable: true`, seventeen fields under `backend` |
| `/settings/admin/findling` as an admin session | **200**, block one with real numbers: Indexed 94, Skipped 0, Failed 1, Excluded 0, run state "Up to date, last checked yesterday", reindex banner visible because `reindexRequired` is true, the other three banners rendered and hidden |
| Same page with the session language set to German | every string translated, real umlauts: "Deckungsgrad der Suche", "Aktuell, letzte Prüfung Gestern", "Übersprungen", "älteren Textanalyse" |
| MDI path data of `magnify`, `alert-circle-outline`, `clock-outline` | byte identical to the pinned commit `9e04201d…` (tag v7.4.47) |

## Issues Encountered

- **The route answered 404 until the app container was restarted.** Attribute routes are cached per app version, and this plan adds a route without bumping the version (the version bump belongs to the plan that adds a container route). Worth knowing for the next plan that adds an admin route: restart the container or clear the cache, otherwise the route looks unregistered.
- **`reasons` encodes as `[]` rather than `{}` when it is empty**, because it is a PHP array. Block one does not read it, so nothing is broken today; plan 04-05, which builds the error list out of that field, should decide the shape deliberately rather than discover it.

## Open Manual Checks

Two Sichtproben of the plan could not be run without a browser and a stoppable backend, and neither blocks the plan:

1. **Backend stopped:** error banner appears and the tile numbers stay instead of dropping to zero. The server side half of that branch is proven by the identical mechanism that renders the reindex banner out of a boolean live; the client side half is the `catch` in `poll()` that touches no number.
2. **Keyboard, dark theme and high contrast pass**, plus the browser console being free of errors. The stylesheet uses nothing but theme variables and removes no focus ring, both pinned by Gate C.

## User Setup Required

None. No external service configuration, no new dependency, no `package.json`.

## Next Phase Readiness

- Plan 04-04 has everything it needs for the coverage fraction: `overview()` returns `indexable` as a fixed key, the template branches on it, and the percentage plus the `<progress>` element are implemented behind that branch.
- Plan 04-05 inherits the page frame, the polling contract, Gate C and the `.findling-path` rule, plus the open question about the container view of `skipped` and `failed` written down above.
- Plans 04-06 to 04-08 inherit `SettingsController` as the place for further admin routes: a new route means one more attribute line, the floor in Gate B raised again, and nothing else.

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-02*

## Self-Check: PASSED

All eleven created files exist on disk and all four commits of this plan are in the history
(`5edd729`, `a1d6f05`, `57fb0ec`, `e3f95a8`).
