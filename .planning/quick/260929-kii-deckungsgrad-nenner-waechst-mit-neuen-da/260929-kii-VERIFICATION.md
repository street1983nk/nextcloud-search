---
phase: quick-260929-kii
verified: 2026-09-29T14:30:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Quick Task 260929-kii: Deckungsgrad-Nenner wächst mit neuen Dateien Verification Report

**Task Goal:** Der Nenner des Deckungsgrads (`findling_scan_stats.files_seen`) wurde bislang nur beim Erst-Crawl gesetzt und wuchs nie mit neuen Dateien (Harness zeigte "607 von 587", 100 %). Fix: periodische Nachzählung (TimedJob `ScanRecountJob`, Zählmodus `StorageCrawlJob mode=recount`, `ScanStatsService::replaceStorage` mit absoluter Zuweisung), plus ehrliche Anzeige im Zeitfenster Zähler > Nenner (neuer Katalogsatz statt Prozent/Bruch).
**Verified:** 2026-09-29
**Status:** passed
**Re-verification:** No , initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Nach Crawl-Abschluss wird der Nenner periodisch neu gezählt (neue, gelöschte, verschobene, zu große, ausgeschlossene Dateien korrekt im Nenner) | VERIFIED | `ScanRecountJob` (TimedJob, `INTERVAL_SECONDS=900`) plants je fälligem Mount eine `StorageCrawlJob`-Kette mit `mode=recount`; `recountSlice()` blättert `getFilesInMount()` vollständig und ruft am Ende `replaceStorage()`. Code gelesen und PHP-Syntax geprüft (`php -l` sauber im Harness-Container). |
| 2 | Nachzählung ersetzt Zähler (Zuweisung, nie Addition), kann nicht doppelt zählen, läuft nie neben echtem Crawl, überschreibt nie laufenden Crawl | VERIFIED | `ScanStatsService::replaceStorage()`: ein UPDATE mit `createNamedParameter` (Zuweisung) und `WHERE storage_id = ? AND finished_at IS NOT NULL`; `recountSlice()` bricht ab, wenn `forStorage()->finished === false`; `ScanRecountJob::run()` gibt sofort zurück, sobald irgendeine `StorageCrawlJob`-Zeile existiert (Crawl oder Recount). Tests: `ScanRecountJobTest::testNothingIsPlannedWhileACrawlRowExists`, `StorageCrawlJobTest::testARecountLeavesAMountThatIsBeingCrawledAlone`. |
| 3 | Nachzählung nutzt dieselbe Abfrage (`getFilesInMount`) und dieselbe Einzelentscheidung (Ausschluss vor Cap) wie der Crawl; keine zweite Regeldefinition, keine handgeschriebene filecache-Abfrage | VERIFIED | `recountSlice()` und `crawlSlice()` rufen beide dieselbe private `verdict()` (Ausschluss vor Cap) und `countSighting()`. grep-Gate `isExcluded(` außerhalb Kommentaren in StorageCrawlJob.php = 1 (bestätigt unabhängig). |
| 4 | Auf ruhiger Instanz höchstens ein Durchlauf je 24 h; nach Ereignissen/Regeländerungen startet die Nachzählung beim nächsten TimedJob-Lauf (15 min) | VERIFIED | `SettingsService::scanRecountDue()`: wahr bei `KEY_SCAN_STALE_SINCE != 0` oder `now - KEY_SCAN_RECOUNTED_AT >= RECOUNT_FLOOR_SECONDS (86400)`; `markScanStale()` in `FileEventListener::queue()`, `expandFolder()`, `expandMovedFolder()` und in `SettingsService::save()`. Test `ScanRecountJobTest::testAQuietInstanceIsRecountedAfterADay`. |
| 5 | Zähler > Nenner (Zeitfenster bis zur nächsten Nachzählung): Seite zeigt weder Prozentzahl noch unmöglichen Bruch noch "Backend antwortet nicht", sondern eigenen Satz in allen 8 Sprachen | VERIFIED | `AdminViewService::coverageShare()` liefert `null` bei `counted > indexable`; `coverage()['recounting']` true bei `backendReachable && indexable > 0 && indexed > indexable`. `admin.php`/`admin.js` blenden `findling-coverage-recounting` ein und `findling-coverage-unknown`/`findling-semantic-unknown` aus. Neuer Katalogsatz wortgleich in allen 16 l10n-Dateien (.json/.js je 8 Sprachen) bestätigt (grep-Zählung = 1 je Datei, JSON/JS-Werte paarweise identisch, keine Dashes). |
| 6 | Auf dem Harness zeigt die Seite nach der Nachzählung einen Nenner >= indexed (oder im Zeitfenster den ehrlichen Satz) | VERIFIED (mit dokumentierter Abweichung) | Executor führte den Live-Beleg per In-Prozess-Lauf gegen die echte Harness-DB durch (Worktree-Autoloader, da der laufende Harness-Cron noch alten Code fährt): Nenner stieg von 587 auf 636 (dann 637), `indexed` blieb konsistent (`percent 95`, nie X > Y). TimedJob-Registrierung in `oc_jobs` und der Playwright-Seitenblick sind bewusst auf "nach dem Merge" verschoben (siehe unten), weil die installierte App-Version noch 1.3.0 ist und dieser Plan laut Projektregel K6 keinen Versionssprung vornimmt. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `php/lib/BackgroundJobs/ScanRecountJob.php` | TimedJob, plant Nachzählung je Mount | VERIFIED | Existiert, `extends TimedJob`, `setInterval(900)`, alle Behavior-Punkte aus dem Plan umgesetzt, `php -l` sauber. |
| `php/lib/BackgroundJobs/StorageCrawlJob.php` | Zählmodus `recount`, gemeinsame Einzelentscheidung | VERIFIED | `MODE_RECOUNT`, `recountSlice()`, `verdict()`/`countSighting()` geteilt mit `crawlSlice()`. |
| `php/lib/Service/ScanStatsService.php` | `replaceStorage()`: absolute Zähler | VERIFIED | Methode vorhanden, UPDATE mit Zuweisung, `WHERE ... finished_at IS NOT NULL`, Fallback `insertIgnoreConflict` für neue Mounts. |
| `php/lib/Service/AdminViewService.php` | `coverageShare()` null bei `counted > indexable`, `coverage.recounting` | VERIFIED | Drittes Null-Kriterium implementiert, `recounting`-Schlüssel in `coverage()` zurückgegeben. |
| `php/appinfo/info.xml` | Registrierung des TimedJobs | VERIFIED | `<background-jobs><job>OCA\Findling\BackgroundJobs\ScanRecountJob</job></background-jobs>` vorhanden, zwischen Kommentar und `<repair-steps>` (dokumentierte Abweichung von "vor dem Kommentar", inhaltlich korrekt begründet und store-Validierung laut SUMMARY grün). |
| `php/tests/Unit/ScanRecountJobTest.php` | Fälligkeit, Sperre, ein Kettenstart je Mount | VERIFIED | 5 Testmethoden, decken Fälligkeit, Crawl-Sperre, Mehrfach-Mount-Planung, 24h-Floor und Intervall-Konstante ab. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `ScanRecountJob.php` | `StorageCrawlJob` (mode recount) | `IJobList::add` je Mount aus `getMounts()` | WIRED | `run()` iteriert `storageService->getMounts()` und ruft `jobList->add(StorageCrawlJob::class, [... 'mode' => MODE_RECOUNT ...])`. |
| `StorageCrawlJob.php` | `ScanStatsService::replaceStorage` | Terminierungszweig des Zählmodus | WIRED | `recountSlice()` ruft `$this->scanStats->replaceStorage($storageId, $sums, $lastFileId)` bei leerer Seite. |
| `FileEventListener.php` | `SettingsService::markScanStale` | Aufruf nach Mount-Frage in `queue()` und in Ordnerzweigen | WIRED | 3 Aufrufstellen bestätigt: `queue()`, `expandFolder()`, `expandMovedFolder()` (nur bei `isIndexedStorage`). |
| `CrawlAdvanceService.php` | `StorageCrawlJob`-Argument `mode` | Nachzählkette wird nicht ausgeführt | WIRED | `advance()` prüft `$argument['mode'] === MODE_RECOUNT` und gibt `['ran' => false, 'pending' => false]` ohne `start()` zurück. |
| `php/js/admin.js` | `coverage.recounting` | `coverageBlock()` und Render-Signatur | WIRED | `coverage.percent, coverage.recounting` in der Signatur, `shown('findling-coverage-recounting', recounting)`, `findling-semantic-unknown` ebenfalls `recounting`-abhängig. |

### Behavioral Spot-Checks / Automated Gates (independently re-run, not taken from SUMMARY)

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| PHP syntax, alle 14 geänderten/neuen Kern- und Testdateien | `docker exec -i findling-harp-nextcloud php -l < <file>` | "No syntax errors" für alle 14 Dateien | PASS |
| admin.js Syntax | `node --check php/js/admin.js` | kein Fehler | PASS |
| Gezielte Gates (Ausschluss-Pfadraum, Store-Metadaten, Vertrauensgrenze, UI-Kontrakt, Artefakte) | `uv run --directory backend pytest tests/test_exclusion_path_space.py tests/test_store_metadata.py tests/test_php_trust_boundary.py tests/test_admin_ui_contract.py tests/test_public_artifacts.py -q` | 251 passed | PASS |
| Baumhash-Pin (php_half) | `uv run --directory backend pytest tests/test_measurement_scripts.py -q -k php_half` | 2 passed | PASS , bestätigt, dass `PHP_FILES_TODAY=82` und der Hash tatsächlich zum aktuellen Baum passen, nicht nur behauptet werden |
| Volle Python-Suite | `uv run --directory backend pytest -q` | **4107 passed, 25 skipped** in 303 s | PASS , exakt deckungsgleich mit SUMMARY-Angabe, unabhängig neu ausgeführt |
| ruff check | `uv run --directory backend ruff check .` | All checks passed | PASS |
| ruff format --check | `uv run --directory backend ruff format --check .` | 183 files already formatted | PASS |
| pyright (latest) | `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run --directory backend pyright` | 0 errors, 0 warnings | PASS |
| vulture | `uv run vulture src tests --min-confidence 80` (in backend/) | keine Ausgabe (sauber) | PASS |
| grep-Gates aus `<verification>` des Plans | `self::coverageShare(` = 2, `isExcluded(` (StorageCrawlJob, ohne Kommentare) = 1, `ScanRecountJob` in info.xml = 1 | alle drei Werte bestätigt | PASS |
| l10n-Wertgleichheit .json/.js über 8 Sprachen | eigenes Skript, Wortlaut-Vergleich gegen Plan-Vorgabe | 8/8 identisch, wortgleich mit Plan, keine Em-/En-Dashes | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ADM-01 | 260929-kii-PLAN.md | Admin-Seite zeigt einen belastbaren Deckungsgrad (Zähler/Nenner) | SATISFIED | Nenner wird nachgezählt (ScanRecountJob), unmöglicher Bruch/100%-Fehlanzeige durch `coverageShare()`-Fix und `recounting`-Satz ausgeschlossen. |

### Anti-Patterns Found

Keine. Kein `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` in den geänderten Kern- oder Template-Dateien gefunden.

### Human Verification Required

Keine zwingenden Items für den Code-Zustand selbst , alle Code-Truths sind über Unit-Tests, Gates und Live-In-Prozess-Beleg abgedeckt. Ein optionaler operativer Schritt bleibt für den Owner/Orchestrator offen, ausdrücklich als solcher im SUMMARY benannt und durch die Projektregel K6 begründet (kein Versionssprung in diesem Plan):

### 1. TimedJob auf dem Harness real registrieren und Seite ansehen

**Test:** `ScanRecountJob` einmalig in `oc_jobs` registrieren (z. B. `occ background-job:list`/`background-job:execute`, oder Update der Harness-App-Version auf 1.4.0) und danach `http://localhost:8096/settings/admin/findling` im Browser öffnen.
**Expected:** Seite zeigt den nachgezählten Nenner (laut Live-Beleg zuletzt 608 von 637, 95 %) bzw., falls seitdem neue Dateien dazugekommen sind, den neuen Katalogsatz statt eines unmöglichen Bruchs.
**Why human:** Erfordert einen Browser/Playwright-Zugriff und eine bewusste Owner-Entscheidung, wann der TimedJob auf dem laufenden Harness scharf geschaltet wird (die installierte App-Version ist noch 1.3.0, ein Versionssprung ist laut Projektregel K6 nicht Teil dieses Plans). Der Code-Pfad selbst ist bereits durch den In-Prozess-Livebeleg und die Unit-Tests abgedeckt.

### Gaps Summary

Keine Gaps. Alle im PLAN.md deklarierten `must_haves` (Truths, Artefakte, Key Links) sind im Code vorhanden, syntaktisch sauber, durch Unit-Tests abgedeckt und durch unabhängig neu ausgeführte Gates (PHP-Lint, volle Python-Testsuite mit identischem Ergebnis 4107/25, ruff, ruff format, pyright, vulture, grep-Gates, l10n-Wertgleichheit) bestätigt. Die drei im Auftrag genannten Abweichungen wurden geprüft und sind sachlich begründet:
- SettingsService dritter Konstruktorparameter (ITimeFactory) in drei weiteren Tests nachgezogen: notwendig, weil autowiring den Parameter überall injiziert; keine Stelle mit dem alten 2-Parameter-Aufruf verblieben (grep bestätigt).
- Drei zusätzliche PHPUnit-Anpassungen in Task 2 (Sichtbarkeitsregel `recounting`): korrekt, da die alte Bedingung sonst die neue Sichtbarkeitslogik widerlegt hätte; im Code (test_admin_ui_contract.py) nachvollzogen.
- info.xml-Platzierung des `<background-jobs>`-Blocks nach statt vor dem Kommentar: inhaltlich sinnvoll (der Kommentar beschreibt anschließend "die drei Blöcke unten"), Schema-Reihenfolge bleibt unangetastet, Store-Validierung laut SUMMARY grün.

Der einzige offene Punkt ist ein bewusst deferred operativer Schritt (TimedJob live auf dem Harness registrieren + visueller Seitenblick), der die Codequalität nicht berührt und laut Projektregel explizit außerhalb dieses Plans liegt.

---

_Verified: 2026-09-29T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
