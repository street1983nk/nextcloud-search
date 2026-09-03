---
phase: 04-admin-sichtbarkeit-und-diagnose
plan: 10
subsystem: ui
tags: [php, nextcloud, occ, symfony-console, documentation, acceptance, css, l10n]

# Dependency graph
requires:
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "AdminViewService::diagnose with the six stage precedence rule and its thirteen keys, from plan 04-07"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "the five blocks of the admin page, the coverage denominator, the estimate, the error list and the four switches, from plans 04-03 to 04-09"
  - phase: 04-admin-sichtbarkeit-und-diagnose
    provides: "IndexCommand as the shape of an occ command of this app and the one line commands block in info.xml, from phase 3"
provides:
  - "occ findling:diagnose: the diagnosis without a browser and without a session, through the same AdminViewService::diagnose the route calls"
  - "docs/admin-page.md: the operating documentation of the page, the coverage denominator, the six precedence stages, the four switches and the exclusion path space"
  - "docs/testing.md carries the four gates of this phase and the three endpoint test files"
  - "SettingsService::rememberIndexedCount and lastIndexedCount: the indexed figure survives a silent container"
  - "a scoped [hidden] rule per block, so the attribute means what it says under the display rules of the page"
  - "the owner acceptance of the four roadmap success criteria and the twelve UI sight checks of phase 4"
affects: [verify-work, 05-haertung-und-store-einreichung, gap-closure]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "A second access to the same answer is a command that calls the same service method, so there is no second precedence rule that could drift"
    - "A figure the page promises to hold is remembered where it was true, in appconfig on change, instead of being recomputed from a table that cannot hold it"
    - "Every block that owns display rules owns its own [hidden] rule, because a specific display rule beats the user agent rule for the attribute"
    - "A help text teaches a value in the path space the code compares in, not in the space the user reads elsewhere"

key-files:
  created:
    - php/lib/Command/DiagnoseCommand.php
    - docs/admin-page.md
  modified:
    - php/appinfo/info.xml
    - docs/testing.md
    - php/css/admin.css
    - php/templates/admin.php
    - php/l10n/de.json
    - php/l10n/de.js
    - php/lib/Service/SettingsService.php
    - php/lib/Service/AdminViewService.php

key-decisions:
  - "Success criterion 3 is accepted although the page does not carry the literal wording of D-05: the page says \"Vorlaeufige Zahl, X von Y Speicherorten sind durchgezaehlt\" and \"Findling wartet auf keine Bestaetigung. Der Erstindex laeuft bereits.\", which is the substance D-05 asks for, said in numbers instead of in the quoted phrase. Owner decision of the walkthrough"
  - "Sight check 4 is closed by a gap closure plan and not inside this phase: skip verdicts of the container are not handed over per file, only failures are, and building that channel is a change of the acknowledgement contract rather than a fix of the page"
  - "Sight check 7 reading \"the files appear with a reason\" is accepted as design: an exclusion is not an error, so the tile Ausgeschlossen, the lowered denominator and the per file diagnosis are the record, and the error list stays a list of errors"
  - "The reindex banner names a remedy that cannot work today; the finding is recorded as a gap closure item rather than fixed inside a plan whose file list ends at the PHP half"
  - "The indexed figure is remembered in appconfig on change instead of being read from findling_file_state, because that table holds no indexed rows by construction"
  - "Sight check 1 is accepted as an approximation: no fresh installation was available, and the literal probe is bound to the target hardware installation test of v1.0"

patterns-established:
  - "An owner walkthrough is run against the page and its findings are fixed as their own commits during the walkthrough, so the acceptance and the fixes stay separable in the history"
  - "A finding that cannot be fixed inside the plan's file list is written into deferred-items.md with its closing shape, so the gap planner needs no second investigation"

requirements-completed: [ADM-01, ADM-02, ADM-03, ADM-04]

# Metrics
duration: 19 min build, plus the owner walkthrough and its four fixes
completed: 2026-09-03
---

# Phase 4 Plan 10: Abnahme, occ-Zweitzugang und Betriebsdokumentation Summary

**The support case is answerable without a browser through `occ findling:diagnose`, the page is documented down to the denominator and the path space, all gates run green over the whole repository, and the owner has seen the page: four success criteria and twelve sight checks accepted, with five findings named, four of them fixed on the spot**

## Performance

- **Duration:** 19 min for tasks 1 and 2, plus the owner walkthrough with its four fixes
- **Started:** 2026-09-02T21:52:15+02:00
- **Completed:** 2026-09-03T05:05:35+02:00
- **Tasks:** 3
- **Files modified:** 11 (2 created, 9 modified, counting `deferred-items.md`)

## Accomplishments

- `occ findling:diagnose` answers a path as well as a fileid with state, reason code, label, remedy, path, owner, file id, last check and whether the container answered, through the same `AdminViewService::diagnose()` the route calls. The command holds no state logic of its own, so there is exactly one precedence rule in this app.
- `docs/admin-page.md` explains the page rather than listing it: where the coverage denominator comes from and what is deliberately not in it, which figure comes from which of the two halves and why a difference between them is a diagnostic signal and not a defect, the six precedence stages including what a tombstone means, the estimate and its explicit non promise, the four switches with default, moment and place of effect, the exclusion path space with examples, the double enforcement of the size cap, the occ second access, and what the page deliberately cannot do.
- All gates of the project run green over the whole repository: five Python gates, `php -l` over 35 files in `lib`, `appinfo` and `templates`, and the gates this phase created.
- **The owner has seen the page.** All four roadmap success criteria were seen on a running instance, and all twelve UI sight checks were run, including dark theme, high contrast, keyboard only and disabled JavaScript. Verdict: approved, with four named decisions.
- Five real findings surfaced during the walkthrough, and four of them were fixed while the owner watched, each as its own commit. The page that was accepted is the page after those fixes, not before them.

## Task Commits

1. **Task 1: occ findling:diagnose as the second access without a browser** - `57253db` (feat)
2. **Task 2: the operating documentation and the full gate run** - `8422698` (docs), plus `1b090b1` (docs, the two out of scope findings of the dev setup)
3. **Task 3: the owner walkthrough** - four fixes, each committed on its own:
   - `d17c72b` (fix) the meaning of `hidden` under the block display rules
   - `6ceeacb` (fix) the lookup gets a path in its own path space
   - `ca7929c` (fix) the exclusion help teaches the prefix in its own path space
   - `fb8a49c` (fix) the indexed count the banner promises is recorded

**Plan metadata:** the docs commit of this plan.

## Files Created/Modified

- `php/lib/Command/DiagnoseCommand.php` - the second access: one required argument, the column output of `IndexCommand`, `Command::SUCCESS` also for a file that was not found because that is an answer and not an error of the command, `Command::INVALID` for a rejected argument, and a docblock that says why the command exists next to a page and that it shares the one precedence rule
- `php/appinfo/info.xml` - the `<commands>` block with two entries, both on one line, so the store schema keeps validating
- `docs/admin-page.md` - the operating documentation, 427 lines, German prose with real umlauts
- `docs/testing.md` - the gate table extended by Gate B with its two route classes, the UI contract gate, the path space gate and the three endpoint test files
- `php/css/admin.css` - a scoped `[hidden] { display: none !important; }` rule per block
- `php/templates/admin.php` - the example buttons carry a resolvable reference, and the exclusion help teaches the prefix in the space the code compares in
- `php/l10n/de.json`, `php/l10n/de.js` - the corrected German exclusion help
- `php/lib/Service/SettingsService.php` - `rememberIndexedCount` and `lastIndexedCount`, appconfig, written on change
- `php/lib/Service/AdminViewService.php` - the silent container fallback reads the remembered figure instead of the state table
- `.planning/phases/04-admin-sichtbarkeit-und-diagnose/deferred-items.md` - four out of scope findings, two from the preparation and two from the walkthrough

## The owner walkthrough

Run live in the browser on the dev instance, owner and orchestrator together, 2026-09-03. Verdict: **approved**, with the four decisions below.

### The four roadmap success criteria

| # | Criterion | Seen |
|---|---|---|
| 1 | Status page with progress, coverage and error list, without reading a log | **yes**. Coverage 83 percent with the named denominator 139 of 166, the error list with reasons and remedies, no log opened at any point |
| 2 | Any file, the reason of its state named | **yes**. By path and by fileid on the page, and the same answer out of `occ findling:diagnose` |
| 3 | Estimate before the first index: number of files, OCR share, duration, space | **yes, accepted**. "168 Dateien, davon 33 mit OCR. Etwa 1 Minute und etwa 1,4 MB Index." Wording deviation against the D-05 quote, accepted by the owner, see deviation 5 below |
| 4 | Exclusions, size cap, Team Folders and External Storage, and the next run obeys | **yes**. All four switches present, the cap validated, and the next run obeyed the new exclusion |

### The twelve UI sight checks

| # | Check | Result |
|---|---|---|
| 1 | Fresh installation, first minute | **approximation, owner accepted**. No fresh installation was available. Covered by the headless empty state renders of plan 04-04 and by the first minute counting state seen live during the reindex. The literal probe is bound to the target hardware installation test of v1.0 |
| 2 | First index running | **pass**. The head figure rose from 81 to 83 percent without a reload, the queue chips were live (136 waiting, 32 processing), the status line said "Die Indexierung laeuft." |
| 3 | Backend stopped | **pass after fix 4**. Error banner, honest refusal of the percentage ("Der Anteil ist im Moment nicht berechenbar..."), the tile held 139 instead of jumping to 0, block 5 fully operable with all seven controls enabled |
| 4 | Corpus with four error kinds, four groups | **partial, gap closure plan**. See finding 5 and decision (b) |
| 5 | Click an example path | **pass after fix 2**. The click fills `testuser/files/99-riesenprotokoll.txt`, the card answers Uebersprungen, Zu gross, the remedy and file id 285, the same reason the list gave |
| 6 | Diagnosis with a number, a path and nonsense | **pass**. fileid 285 answers Uebersprungen, the path `corpus/09-bescheid.pdf` answers Indexiert, nonsense answers "Unter diesem Pfad liegt keine Datei, und keine Datei hat diese ID." and leaks nothing |
| 7 | Add an exclusion over indexed documents | **pass after fix 3**. The inline confirmation named 2 documents, the cancel button read "Dateien indexiert lassen", after the confirmation the SubtreeExpandJobs wrote 2 delete rows, the tile Ausgeschlossen showed 2, the denominator fell from 168 to 166, and the diagnosis answered skipped(excluded) with label and remedy. Reading of "appear with a reason" per decision (c) |
| 8 | Size cap 0 and 99999 | **pass**. "Eine Groesse zwischen 1 und 50 MB eingeben.", focus stays in the field, nothing is saved |
| 9 | Dark theme and high contrast | **pass**. Both themes legible, no invisible chip, theme variables only |
| 10 | Keyboard alone | **pass**. All controls native (button, input, form), no negative tabindex, Enter submits the diagnosis form, the focus lands in the cap field on a validation error |
| 11 | JavaScript disabled | **pass**. The server HTML renders blocks 1 to 3 with real figures (83 percent), all error groups open because the toggle buttons stay hidden without JavaScript, and the diagnosis names its JavaScript requirement |
| 12 | English and German | **pass**. The full English page with zero German leftovers, and German seen throughout the whole session |

### The five findings

Four were fixed during the walkthrough, each as its own commit, all pushed.

**1. `hidden` had lost its meaning under the block display rules** (`d17c72b`)
Every display rule in `admin.css` was more specific than the user agent rule for `[hidden]`, so banners and chips stayed visible with the attribute set. Fixed with a scoped `[hidden] { display: none !important; }` rule per block. This is the finding that made three other checks readable in the first place.

**2. The example buttons handed the lookup a path it could not resolve** (`6ceeacb`)
The buttons carried the `files/` relative display path, which the lookup rejects with "no such file". Now they carry `uid/files/rest` for a resolvable live file and the bare fileid for a trashed or vanished row.

**3. The exclusion help taught a prefix in the wrong path space** (`ca7929c`)
The help line taught `alice/files/Backups`, which can never match, because the exclusion space is relative to the mount root. Now "Beispiel: Backups" and "wie ihn die Listen dieser Seite zeigen", in the template and in both German translation files.

**4. The tile did not hold the figure the banner promises** (`fb8a49c`)
With the container silent the fallback read the Nextcloud state table, which holds no indexed rows by construction, so the tile jumped to 0 while the banner promised the figures would stand. Now `SettingsService::rememberIndexedCount` and `lastIndexedCount` in appconfig, written on change. Proven live: with the backend unregistered the tile held 139.

**5. Open finding, not fixed: the reindex banner names a remedy that cannot work.**
The banner appears when the stored version marks differ from the versions the current code expects, and its remedy sentence names `occ findling:index --restart`. That command can never clear the flag: `_seed_meta` in `store/repo.py` writes a meta key only when it is missing, and no code path re-stamps the marks after a completed rebuild. The dev instance was stamped by hand after the full rebuild, which is factually correct there because all 139 documents were re-ingested with the current code. Recorded as DI-04-04.

### The four owner decisions, verbatim

**(a)** Success criterion 3 is accepted despite the wording deviation. It is documented as a deviation, it concerns block 2, and D-05 is met in substance.
**(b)** Sight check 4 goes into a gap closure plan: the handover of skip verdicts per fileid.
**(c)** The reading of sight check 7, "appear with a reason", is accepted as design: the tile, the lowered denominator and the diagnosis are the record, an exclusion is not an error.
**(d)** Finding 5 goes into a gap closure plan: re-stamp the version marks after a completed rebuild.

## Decisions Made

See `key-decisions` in the frontmatter. The two that decide what the next plan reads:

**The error list is a list of what the Nextcloud half decided.** It holds `too_large` and `empty_file` because those verdicts are written there per file. The container side skip verdicts, `encrypted`, `no_text_layer`, `empty_text` and `image_not_ocrable`, are not handed over per file at all: the acknowledgement channel carries a `failureList` and nothing equivalent for skips. The per file answer exists anyway, through the diagnosis and through the command. Closing the gap means extending the acknowledgement contract, which is a plan of its own and not a fix of the page.

**A figure the page promises to hold is remembered where it was true.** The banner tells the admin the figures will stand while the container is silent. That promise cannot be kept by recomputing the figure from a table that cannot contain it. So the indexed count is written into appconfig at the moment the container reports it and read back when it does not answer. It is a remembered measurement and the page says so, not a second source of truth.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `hidden` did not hide under the block display rules**

- **Found during:** Task 3 (walkthrough, sight checks 2, 3 and 7)
- **Issue:** Every block in `admin.css` sets a display value on its containers, and a class selector with a display value beats the user agent rule `[hidden] { display: none }`. Banners, chips and the confirmation therefore stayed on screen while the attribute said they were hidden. Since plan 04-03 the whole page relies on that attribute as its one switching mechanism, so this silently affected every state the page has.
- **Fix:** One scoped `[hidden] { display: none !important; }` rule per block, next to the display rules it has to beat, rather than one global rule far away from them.
- **Files modified:** `php/css/admin.css`
- **Verification:** Live: the error banner appears and disappears with the backend, the queue chips switch, the confirmation returns to its ground state. Gate C green, so no literal colour and no removed focus ring came in with it.
- **Committed in:** `d17c72b`

**2. [Rule 1 - Bug] The example buttons handed the lookup a path in a foreign path space**

- **Found during:** Task 3 (walkthrough, sight check 5)
- **Issue:** The example paths of the error list are display paths inside the home of the owner, that is `files/` relative. The lookup of block 4 resolves in the Nextcloud path space, `uid/files/rest`. Every click therefore answered "no such file", which made the one bridge between the list and the diagnosis useless.
- **Fix:** The button carries the resolvable reference: `uid/files/rest` for a live file, and the bare fileid for a row whose file is in the trash or gone, because a fileid resolves in both cases and a path does not.
- **Files modified:** `php/templates/admin.php`
- **Verification:** Live: the click fills `testuser/files/99-riesenprotokoll.txt` and the card answers with the same reason and the same file id 285 the list showed.
- **Committed in:** `6ceeacb`

**3. [Rule 1 - Bug] The exclusion help taught a value that can never match**

- **Found during:** Task 3 (walkthrough, sight check 7)
- **Issue:** The help line under the exclusion field taught `alice/files/Backups`. The enforcement compares a prefix relative to the root of every mount, so a value in that shape never matches anything. The one documentation an admin reads at the moment he types was teaching the wrong space.
- **Fix:** "Beispiel: Backups" plus the sentence that the path is the one the lists of this page show, in the template and in both German translation files, in the wording `docs/admin-page.md` uses for the same space.
- **Files modified:** `php/templates/admin.php`, `php/l10n/de.json`, `php/l10n/de.js`
- **Verification:** Live: `Archiv` typed as the help teaches it matched, cleared two documents and lowered the denominator. `de.json` valid JSON, both German strings resolve.
- **Committed in:** `ca7929c`

**4. [Rule 1 - Bug] The tile did not hold the figure the error banner promises**

- **Found during:** Task 3 (walkthrough, sight check 3)
- **Issue:** With the container silent, `AdminViewService` fell back to counting indexed rows in `findling_file_state`. That table holds `skipped` and `failed` rows by construction and never an `indexed` row, so the fallback was always 0 and the tile jumped to 0 exactly in the moment the banner said the figures would stand. That is the failure decision "indexedDisplay chooses instead of computing" exists to prevent, one layer further down.
- **Fix:** `SettingsService::rememberIndexedCount` writes the figure into appconfig whenever the container reports a different one, and `lastIndexedCount` reads it back. The fallback uses the remembered figure. Write on change, so a poll every few seconds does not write every few seconds.
- **Files modified:** `php/lib/Service/SettingsService.php`, `php/lib/Service/AdminViewService.php`
- **Verification:** Live: backend unregistered, the tile held 139 and the percentage refused itself honestly, block 5 stayed operable.
- **Committed in:** `fb8a49c`

**5. [Wording deviation, owner accepted] Success criterion 3 does not carry the quoted phrase of D-05**

- **Found during:** Task 3 (walkthrough, criterion 3, block 2)
- **Issue:** D-05 and the plan expect the label "vorlaeufig, Scan laeuft". The page says "Vorlaeufige Zahl, X von Y Speicherorten sind durchgezaehlt" and, next to it, "Findling wartet auf keine Bestaetigung. Der Erstindex laeuft bereits."
- **Assessment:** The substance D-05 asks for is present twice over. The figure is labelled as provisional, the progress of the scan is named in numbers instead of in the word "laeuft", and the sentence that no confirmation is awaited is explicit rather than implied. The page says more than the quote, not less.
- **Owner decision (a):** accepted, documented as a deviation, D-05 met in substance.
- **Files modified:** none

**6. [Reading, owner accepted] Sight check 7, "the files appear with a reason"**

- **Found during:** Task 3 (walkthrough, sight check 7)
- **Issue:** The literal reading would put excluded files into the error list of block 3. They do not appear there.
- **Assessment:** An exclusion is not an error. What was seen instead: the tile Ausgeschlossen counts them, the coverage denominator drops by exactly that number, and the per file diagnosis answers `skipped(excluded)` with label and remedy. That is a complete record of the consequence in three places, and putting the same files into a list titled errors would teach the admin that his own rule broke something.
- **Owner decision (c):** accepted as design.
- **Files modified:** none

---

**Total deviations:** 4 auto-fixed bugs, 2 accepted readings, 0 architectural.
**Impact on plan:** All four fixes are corrections inside the file list of this phase, found by the one method that finds them, a human in front of the page. No new dependency, no package installed, no new container route, no change to the write allowlist of the read only gate. The two remaining findings are recorded as gap closure items rather than fixed, because both cross into the container half and the acknowledgement contract.

## Verification

Full gate run, over the whole repository, after all fixes:

| Gate | Result |
|---|---|
| `cd backend && uv run ruff check .` | All checks passed |
| `cd backend && uv run ruff format --check .` | 78 files already formatted |
| `cd backend && uv run pyright` | 0 errors, 0 warnings, 0 informations |
| `cd backend && uv run vulture src tests --min-confidence 80` | no findings |
| `cd backend && uv run python -m pytest -q` | 766 passed, 11 skipped, 1 warning, 32.36s |
| `php -l` over `lib`, `appinfo`, `templates` in the dev container | 35 files, 35 times "No syntax errors detected", nothing else |
| `node --check php/js/admin.js` | clean |
| `php/l10n/de.json` parses as JSON | valid |
| Gate A (`test_readonly_gate.py`) and Gate B (`test_php_trust_boundary.py`) after the walkthrough fixes | 39 passed |
| Em dash or en dash in the changed files | none |

Command level checks of task 1, on the dev instance:

| Check | Result |
|---|---|
| `occ list \| grep findling` | lists `findling:index` and `findling:diagnose` |
| `occ findling:diagnose <fileid>` | state, reason code, label, remedy and file id, exit code 0 |
| `occ findling:diagnose <path>` | the same state the diagnosis card of the page gives for the same file |
| `occ findling:diagnose ../etc/passwd` | rejected, and the value appears in no log line |
| `grep -c 'pending_crawl' php/lib/Command/DiagnoseCommand.php` | 0, so the precedence rule lives only in `AdminViewService` |

**Port discrepancy, as the plan asked to record it:** the UI contract and `04-RESEARCH.md` name port 8090, while `docs/dev-setup.md` and `scripts/dev/compose.yaml` name 8080 through `FINDLING_PORT`. `docs/dev-setup.md` is the truth. The summary of plan 04-09 quotes 8090 as well, which comes from the same source.

## Known Stubs

None.

## Threat Flags

None beyond the register of the plan. `occ findling:diagnose` outputs metadata and verdicts and no file content, in line with T-04-61 and T-04-65, and it resolves its argument through the same `PathResolverService::resolveReference` the route uses, which is T-04-62.

## Issues Encountered

**The checksum gate over the reference corpus was not run as the closing step of the walkthrough.** The plan asks for it after the whole run, and specifically after the clearing caused by an exclusion. The read only gate (`test_readonly_gate.py`) is green as a source level gate, the write allowlist is unchanged at three entries, and no code path of this plan writes to a user file. The corpus level checksum comparison after the live clearing is outstanding and belongs to the phase verification that runs next.

**The dev backend has to be restarted for a route added by a later plan**, and the local ExApp registration declares one route out of five. Both were found while preparing the walkthrough and are recorded as DI-04-01 and DI-04-02 in `deferred-items.md`. Both cost time before the first successful `occ findling:diagnose` call, because a container answering 404 looks exactly like a defect of the PHP half.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 4 has built what it promised, and a human has seen it. What phase 5 and the verification find in place:

- Five blocks on one page, all four requirements ADM-01 to ADM-04 covered, and the acceptance is a walkthrough record rather than a claim.
- A second access without a browser, sharing the one precedence rule with the page.
- Operating documentation an admin can recompute the numbers from and set the switches by.
- Four gates of this phase, plus the gates of the earlier phases, all green over the whole repository.

Two named gaps, both with their closing shape written down in `deferred-items.md`:

1. **DI-04-03**, the handover of skip verdicts per fileid, which turns the four container side verdicts into groups of the error list. Owner decision (b).
2. **DI-04-04**, the re-stamping of the version marks after a completed rebuild, so the reindex banner and the remedy it names agree. Owner decision (d).

And two carried over from the preparation: DI-04-01, the route list of `register-exapp.sh`, and DI-04-02, the dev backend restart.

One thing the verification has to close rather than repeat: the checksum comparison over the reference corpus after the live clearing.

## Self-Check: PASSED

- `php/lib/Command/DiagnoseCommand.php` FOUND
- `docs/admin-page.md` FOUND
- `docs/testing.md` FOUND
- `php/lib/Service/SettingsService.php` FOUND
- `php/css/admin.css` FOUND
- `php/templates/admin.php` FOUND
- `deferred-items.md` FOUND, four items
- Commits `57253db`, `8422698`, `1b090b1`, `d17c72b`, `6ceeacb`, `ca7929c`, `fb8a49c` FOUND
- No em dash and no en dash in the documents of this plan

---
*Phase: 04-admin-sichtbarkeit-und-diagnose*
*Completed: 2026-09-03*
