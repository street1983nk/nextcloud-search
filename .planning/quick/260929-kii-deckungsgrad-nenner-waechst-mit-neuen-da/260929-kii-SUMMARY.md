---
phase: quick-260929-kii
plan: 01
status: complete
subsystem: php-companion / admin page coverage figure
tags: [coverage, denominator, recount, admin-page, l10n, ADM-01]
requires: []
provides:
  - "ScanRecountJob (TimedJob, 15 min) plus StorageCrawlJob mode recount"
  - "ScanStatsService::replaceStorage (absolute counters, finished rows only)"
  - "SettingsService markScanStale / scanRecountDue / beginRecount"
  - "coverage.recounting and a null share when indexed > indexable"
affects: [php/lib, php/templates/admin.php, php/js/admin.js, php/l10n, docs]
tech-stack:
  added: []
  patterns: ["mark in the listener, measure in a recount (no increments)", "one verdict method shared by crawl and recount"]
key-files:
  created:
    - php/lib/BackgroundJobs/ScanRecountJob.php
    - php/tests/Unit/ScanRecountJobTest.php
  modified:
    - php/lib/BackgroundJobs/StorageCrawlJob.php
    - php/lib/Service/ScanStatsService.php
    - php/lib/Service/SettingsService.php
    - php/lib/Service/CrawlAdvanceService.php
    - php/lib/Service/PurgeService.php
    - php/lib/Listener/FileEventListener.php
    - php/lib/Service/AdminViewService.php
    - php/appinfo/info.xml
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/*.json, php/l10n/*.js (16 files)
    - php/tests/Unit/StorageCrawlJobTest.php, CrawlAdvanceServiceTest.php, SettingsServiceTest.php, AdminViewServiceTest.php, ProbeServiceTest.php, ProfileControllerTest.php, ProfileSettingsControllerTest.php
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - docs/admin-page.md, docs/l10n-catalogues.md, docs/l10n-{french,spanish,italian,dutch,portuguese}.md
decisions:
  - "Option c: Nachzählung im Zählmodus des Crawls (dieselbe Abfrage, dieselbe Einzelentscheidung), Zuweisung statt Addition"
  - "SettingsService bekommt ITimeFactory als dritten Konstruktorparameter (markScanStale ohne time())"
  - "Zeilen verschwundener Mounts bleiben stehen (Grenze in docs/admin-page.md)"
metrics:
  duration: "ca. 45 min"
  completed: 2026-09-29
  tasks: 3
  commits: 3
---

# Quick 260929-kii: Nenner des Deckungsgrads zählt nach Summary

Der Nenner des Deckungsgrads wird nach dem Crawl periodisch neu gemessen (ScanRecountJob startet StorageCrawlJob im Zählmodus, das Ergebnis ersetzt die Zeile des Mounts), und im Zeitfenster "Zähler größer Nenner" zeigt die Seite weder Prozent noch unmöglichen Bruch, sondern einen eigenen Satz in 8 Sprachen.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1 | f5953fbd | fix(quick-260929-kii): recount the coverage denominator after the crawl |
| 2 | e3af082c | fix(quick-260929-kii): no share and no impossible fraction while the count is behind |
| 3 | 65e860c8 | docs(quick-260929-kii): recount of the denominator, tree hash measured again |

Alle drei als street1983nk <k.cherif@outlook.de>, ohne Trailer, nicht gepusht.

## Was gebaut wurde

- `StorageCrawlJob`: `MODE_RECOUNT`, private `verdict()` (Ausschluss vor Cap, der einzige `isExcluded(`-Aufruf der Datei) und `countSighting()` werden von `crawlSlice()` und der neuen `recountSlice()` gemeinsam genutzt. Der Zählmodus stellt nichts ein, schreibt kein Urteil, öffnet keine Transaktion, schreibt kein LAST_JOB_RUN, prüft die Deadline nur zwischen Seiten, trägt seine sechs Summen im Jobargument und ruft am Ende genau einmal `replaceStorage()`. Bei einer Zeile ohne `finished_at` (laufender Crawl) bricht er ohne Nachfolger ab. Der Lock-Verlust plant im Crawl-Modus weiterhin exakt die vier kanonischen Schlüssel.
- `ScanStatsService::replaceStorage()`: ein UPDATE mit absoluten Werten, `WHERE storage_id = ? AND finished_at IS NOT NULL`; bei 0 Zeilen `forStorage()`, bei fehlender Zeile `insertIgnoreConflict` (neuer Mount).
- `ScanRecountJob`: TimedJob 15 min; tut nichts, solange eine StorageCrawlJob-Zeile existiert oder die Nachzählung nicht fällig ist; sonst `beginRecount(now)` und je Mount ein `jobList->add(StorageCrawlJob, mode recount, Summen 0)`. In `info.xml` registriert, in `PurgeService::JOBS` aufgenommen.
- `SettingsService`: `KEY_SCAN_STALE_SINCE`, `KEY_SCAN_RECOUNTED_AT`, `RECOUNT_FLOOR_SECONDS = 86400`, `markScanStale()` (schreibt nur beim Übergang von 0), `scanRecountDue()`, `beginRecount()`; `save()` markiert.
- `FileEventListener`: `markScanStale()` nach der Mount-Frage in `queue()`, in `expandFolder()` nach `isIndexedStorage`, und in `expandMovedFolder()` bei gleichem Mount (nur indexierter Mount).
- `CrawlAdvanceService`: eine Nachzählzeile an erster Stelle ergibt `ran=false, pending=false` ohne Ausführung.
- `AdminViewService::coverageShare()` liefert `null` bei `counted > indexable` (vorher 100); `coverage.recounting`. Template und Script zeigen dann `findling-coverage-recounting` statt Figur, Balken, Bruch, "backend does not answer" und "semantic share cannot be worked out".
- Neuer Katalogsatz in allen 16 Dateien (288 Schlüssel, 5 Plural), Zeilen in den fünf Sprachdokumenten, datierte Notiz in `docs/l10n-catalogues.md`, neuer Kontrakttest für beide Hälften.
- `docs/admin-page.md`: Unterabschnitte "Wie der Nenner aktuell bleibt" und "Wenn der Zähler über dem Nenner steht", Grenze verschwundener Mounts, Registrierung mit dem Update auf 1.4.0.
- Baumhash-Pins: `PHP_FILES_TODAY` 80 auf 82, `PHP_TREE_HASH_TODAY` = `b06c30e2dc90a3a93ba9c671c9e3980089e8c36d078b514c35bcddae8691fcc1` (Pin war seit 9d6a11c3 rot); Python-Hälfte unverändert grün.

## Gates

- `php -l` (PHP 8.5.9 im Harness-Container, per stdin) für alle 17 geänderten/neuen PHP-Dateien: sauber. `node --check php/js/admin.js`: sauber.
- `info.xml` über den Store-Pfad (`scripts/dev/validate_info_xml.sh`, Transform plus Schema): passes.
- `ruff check .`: All checks passed. `ruff format --check .`: 183 files already formatted. `pyright` (PYRIGHT_PYTHON_FORCE_VERSION=latest): 0 errors, 0 warnings. `vulture src tests --min-confidence 80`: sauber.
- `pytest -q`: **4107 passed, 25 skipped** (inklusive beider Baumhash-Pins).
- grep-Gates: `self::coverageShare(` = 2; `isExcluded(` außerhalb von Kommentaren in StorageCrawlJob.php = 1; `ScanRecountJob` in info.xml = 1.
- PHPUnit läuft nur in CI (keine Server-Checkout lokal); neue Fälle: StorageCrawlJobTest +4, ScanRecountJobTest 5, CrawlAdvanceServiceTest +1, SettingsServiceTest +8, AdminViewServiceTest 2 Provider-Zeilen.

## Live-Beleg auf dem Harness (findling-harp-nextcloud, SQLite)

Der Harness bindet `php/` des Haupt-Checkouts ein, nicht diesen Worktree. Der Beleg lief deshalb mit dem Worktree-Code aus `/tmp/kii/lib` im Container (vorangestellter Autoloader, Herkunft jeder geladenen Findling-Klasse geprüft: alle "worktree"), gegen die echte DB und den echten Container, mit einer JobList-Unterklasse, die StorageCrawlJob-Zeilen nur im Speicher hält (damit der laufende Harness-Cron mit altem Code nie eine Nachzählzeile als Crawl ausführt). Danach `/tmp/kii` gelöscht; `oc_jobs` enthält keine Findling-Zeile.

| Zeit (UTC) | Zustand | scan_stats | coverage |
|---|---|---|---|
| 13:37:13 | vorher (Befund) | storage 2: files_seen 588, over_cap 1, finished 11:01:34; storage 3: files_seen 0 | indexed 607, indexable 587, percent **null**, recounting **true** (alter Code: 100 Prozent, "607 von 587") |
| 13:37:18 | nach Nachzählung 1 (2 Ketten, 2 Scheiben) | storage 2: 588, finished 13:37:18; storage 3: **49** (cursor 693) | indexed 607, indexable **636**, percent 95, recounting false |
| 13:37:52 | neue Datei über die Files-API angelegt (id 703) | | |
| 13:39:41 | Datei indexiert | unverändert | indexed 608, indexable 636, percent 95 (korrekter Bruch, nie X > Y) |
| 13:39:49 | `scan_stale_since` gesetzt, Nachzählung 2 | storage 2: **589** (cursor 703), storage 3: 49 | indexed 608, indexable **637**, percent 95 |

Befund dazu: der alte Nenner war nicht nur um neue Dateien zu klein, der Home von `testuser` (storage 3) war beim ersten Crawl leer und hatte seither 49 Dateien bekommen. Die Differenz 637 zu 608 sind Dateien mit Endurteil (5 corrupt, 1 empty_file, 16 empty_text, 2 encrypted, 4 image_not_ocrable), also ehrliche 95 Prozent. Die zweite Nachzählung hat zugewiesen und nicht addiert (589, nicht 1177).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] SettingsService-Konstruktor in drei weiteren Tests nachgezogen**
- **Found during:** Task 1
- **Issue:** ITimeFactory als dritter Konstruktorparameter (vom Plan vorgesehen) bricht `new SettingsService($appConfig, $logger)` in ProbeServiceTest, ProfileControllerTest, ProfileSettingsControllerTest (nicht in der Dateiliste).
- **Fix:** ITimeFactory-Mock als drittes Argument. Commit f5953fbd.

**2. [Rule 1 - Bug] Kontrakttest auf die neue Sichtbarkeitsregel des semantischen Satzes gehoben**
- **Found during:** Task 2
- **Issue:** `test_the_engine_line_is_not_hidden_behind_a_denominator_that_does_not_exist_yet` hielt die alte Bedingung wörtlich fest.
- **Fix:** Assertion auf `... || $recounting)` bzw. `... && coverage.recounting !== true` gehoben, Absicht im Kommentar; zusätzlich neuer Test `test_a_numerator_above_its_denominator_shows_the_recount_sentence_in_both_halves`. Commit e3af082c.

**3. Platzierung in info.xml:** die `<background-jobs>`-Zeile steht direkt nach dem Kommentar und vor `<repair-steps>` (statt vor dem Kommentar), damit "The three blocks below" stimmt; Schema-Reihenfolge unverändert, Store-Validierung grün.

**4. Live-Beleg abweichend vom Plan:**
- TimedJob NICHT in `oc_jobs` des Harness registriert: der Harness läuft mit dem Code des Haupt-Checkouts, der `ScanRecountJob` noch nicht kennt, und der Harness-Cron ist aktiv (lastcron wenige Sekunden alt); eine registrierte Zeile bzw. echte StorageCrawlJob-Nachzählzeilen würde der alte Code als Crawl ab Cursor 0 ausführen (beginStorage, Neueinreihen). Stattdessen der In-Prozess-Lauf oben.
- WebDAV-Upload mit `NEXTCLOUD_ADMIN_PASSWORD` gab 401 (Passwort auf dem Harness geändert); die Datei wurde über `IRootFolder::getUserFolder('admin')->newFile()` angelegt, das dieselben Node-Events auslöst. Die Datei `kii-recount-probe.txt` bleibt im Home von admin liegen.
- Kein Playwright-Seitenblick: in dieser Umgebung kein Browser-Werkzeug, und die ausgelieferte Seite ist noch der alte Code. Die Seitenwerte oben sind `AdminViewService::overview()` des neuen Codes, also genau das, was Template und Script rendern. **Offen für Orchestrator/Owner nach dem Merge:** http://localhost:8096/settings/admin/findling öffnen (erwartet 608 von 637, 95 Prozent) und `ScanRecountJob` registrieren (`occ background-job:list` / Update auf 1.4.0).

## Known Stubs

Keine.

## Threat Flags

Keine neue Oberfläche außerhalb des Threat-Models (T-kii-01 bis 06 umgesetzt: Sperre gegen laufende Crawls plus `finished_at IS NOT NULL`, Budget je Scheibe, gecachter Lesezugriff vor dem Schreiben, Klemmung der Summen per `(int)`/`max(0)`, Logzeilen nur mit storage_id und Zahlen, Ausgabe über `p()`/`t()` bzw. Textknoten).

## Self-Check: PASSED

- FOUND: php/lib/BackgroundJobs/ScanRecountJob.php
- FOUND: php/tests/Unit/ScanRecountJobTest.php
- FOUND: f5953fbd, e3af082c, 65e860c8
