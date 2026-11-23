---
phase: 45-findling-1-7-0
plan: 23
subsystem: php-companion-crawl
tags: [issue-25, f1, crawl-marker, locking, recount, minimum-interval, tdd]
requires: [45-22]
provides: [Owner-Zeilen Texte 1 bis 4, r1, z1, 6h, l1 für 45-23 bis 45-25, Marker-Lock findling/crawl-active nur im Crawl-Modus, crawling() liest nur den Marker, isPassingLockError am Slice-Lock und am Marker (I-45-23-06 behoben), ext-redis im CI-Job phpunit, RECOUNT_MIN_INTERVAL_SECONDS 6 h mit Regelausnahme r1 und Zukunftsfall, Doku und CHANGELOG Text 1, Baumhash PHP 143/976184c1]
affects: [45-24, 45-25, 45-20, 45-21, 45-10, 45-15]
tech-stack:
  added: []
  patterns: [Marker-Lock neben dem Serialisierungs-Lock, Nehmen im try des äußeren Locks, verschachteltes finally, vorübergehende Fehler nur nach Klassenliste wiederholen, Nachfolger vor dem Log, Fake-ILockingProvider mit Protokoll im Test]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-23-SUMMARY.md
  modified:
    - php/lib/BackgroundJobs/StorageCrawlJob.php
    - php/lib/BackgroundJobs/ScanRecountJob.php
    - php/lib/Service/CrawlAdvanceService.php
    - php/lib/Service/SettingsService.php
    - php/tests/Unit/CrawlAdvanceServiceTest.php
    - php/tests/Unit/StorageCrawlJobTest.php
    - php/tests/Unit/SettingsServiceTest.php
    - php/tests/Unit/ScanRecountJobTest.php
    - .github/workflows/php.yml
    - backend/tests/test_measurement_scripts.py
    - docs/admin-page.md
    - CHANGELOG.md
    - CHANGELOG.de.md
    - CHANGELOG.fr.md
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
decisions:
  - "Owner 2026-11-22 18:37 UTC 'Go mit den Empfehlungen' (Antwort auf die im Chat vorgelegten Empfehlungen zu (1) bis (5)): Texte 1 bis 4 wörtlich wie im Plan, r1, z1 (mit der Änderung an D-03 und der Last nach T-45-84), Mindestabstand 6 h, Locking l1; Text 5 nicht in 45-23, getrennt über `Freigabe Text 5 45-25`"
  - "Marker 'findling/crawl-active' über denselben ILockingProvider wie der Slice-Lock (gleiche TTL), nur im Crawl-Modus, im try des Slice-Locks genommen, vor ihm freigegeben; ein fremder Marker hält keine Scheibe auf"
  - "isPassingLockError: nur OCP\\DB\\Exception, RedisException, RedisClusterException (Klassen als String); Nachfolger mit retries + 1 vor der warning-Zeile, ab MAX_RETRIES weiterwerfen; derselbe Weg beim Slice-Lock (I-45-23-06, vorbestehend seit v1.2.0)"
  - "Mindestabstand ab dem Start der letzten Runde, keine Pause (I4); Regelausnahme über rulesChangedAt() > scanRecountedAt, dieselbe Richtung wie AdminViewService::rulesPending"
metrics:
  duration: "ca. 85 min laut Systemzeit (ca. 03:58 bis 05:25 UTC), davon ca. 55 min Docker (RED, GREEN, 15 Mutationen, zwei volle Verify-Läufe)"
  completed: 2026-11-23
---

# Phase 45 Plan 23: #25 F1, eine Nachzählung hält den Abgleich nicht mehr auf Summary

Eine Nachzählung des Nenners meldet dem Container keinen unfertigen Crawl mehr (Marker-Lock 'findling/crawl-active' nur für Crawl-Scheiben, crawling() liest nur ihn), vorübergehende Fehler beim Nehmen der Locks beenden die Kette eines Mounts nicht mehr, und Nachzählungsrunden haben einen Mindestabstand von sechs Stunden, gespeicherte Regeln ausgenommen.

## Tasks

| Task | Inhalt | Commit |
|---|---|---|
| 1 | Owner-Zeilen in 45-FREIGABEN.md: `Freigabe Texte #25 45-23` (ja), `Entscheid Regeln Nachzählung 45-23` (r1), `Entscheid Rückhalt-Weg 45-23` (z1), `Entscheid Mindestabstand 45-23` (6h), `Entscheid Locking 45-23` (l1), Zitat "Go mit den Empfehlungen" 2026-11-22 18:37 UTC, Hinweiszeile zur Bezugnahme auf die Empfehlungen im Chat | 6227bdff |
| 2 | Marker-Lock, isPassingLockError an Slice-Lock und Marker, verschachtelte Freigabe, crawling() auf den Marker, ext-redis in php.yml, Quellen und INFO-Punkte I-45-23-01 bis -06 im Audit, elf Mutationen, Baumhash | 104bf781 |
| 3 | RECOUNT_MIN_INTERVAL_SECONDS 6 h, Regelausnahme r1, Zukunftsfall, Docblocks, docs/admin-page.md, CHANGELOG Text 1 EN/DE/FR, vier Mutationen, Baumhash | 941c68f0 |

## Ergebnisse

- Task 1 verify (`<scratchpad>/v1.sh`): grün; Gegenprobe: keine Zeile `Freigabe Text 5 45-25` geschrieben.
- Task 2 RED gefiltert `Tests: 38, Assertions: 128, Errors: 10, Failures: 3`; GREEN `OK (38 tests, 225 assertions)`. Verify wörtlich (`<scratchpad>/v23_t2.sh`) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1396 tests, 8796 assertions)`, Psalm-Taint 0 gegen v33.0.9/v34.0.6/v35.0.3 (Probe 3, keine Meldung zu `is_a(..., 'RedisException')`), php-cs-fixer, zizmor, actionlint grün, pytest `748 passed`.
- Task 3 RED gefiltert `Tests: 90, Assertions: 207, Errors: 5, Failures: 3`; GREEN `OK (90 tests, 222 assertions)`. Verify wörtlich (`<scratchpad>/v23_t3.sh`) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1403 tests, 8810 assertions)`, PHP-Gates grün, ruff, ruff format (260), pyright latest 0/0/0, vulture ohne Fund, pytest `808 passed`.
- Mutationen (je rot, Quellen danach byte-gleich): M1 crawling() auf LOCK_NAME, M2 Marker auch bei recount, M3 kein Marker, M4 keine Freigabe des Markers, M5 fremden Marker freigeben, M17 Marker vor dem try, M18 kein Nachfolger am Marker, M21 ohne MAX_RETRIES am Marker, M22 flaches finally, M23 kein Nachfolger am Slice-Lock, M24 jede Ausnahme vorübergehend; M6 ohne Mindestabstand, M7 `>` statt `>=`, M8 ohne Regelausnahme, M9 ohne Zukunftsfall.
- Quellen: ILockingProvider je OCP-Tag, Provider-Wahl und TTL je Server-Zweig stable33/34/35, Würfe von DBLockingProvider und Redis.php, APCu und Factory, Einrichtungsprüfungen; ext-redis 6.3.0 im Laufzeitbild nextcloud:32.0.15-apache belegt.
- Baumhash php/: ff141406/143 -> 41a8dc1f/143 (Task 2) -> 976184c1/143 (Task 3), Rezept und unabhängige Pipeline gleich; Positivkontrollen über git archive 6227bdff -> ff141406, 104bf781 -> 41a8dc1f, 941c68f0 -> 976184c1.
- Docker am Ende leer, kein Push, kein Tag, kein Kommentar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Bestehende Tests an die neue Regel angepasst**
- **Found during:** Task 2 und Task 3 (RED)
- **Issue:** `testADatabaseErrorInASliceReschedulesTheCursorItArrivedWith` und `testTheFifthFailureInARowWithoutProgressEndsTheChainLoudly` erwarteten genau ein releaseLock (jetzt zwei im Crawl-Modus); `ScanRecountJobTest::testAMarkPlansOneRecountChainPerMount` stand mit einer Runde vor einer Stunde auf der alten 15-Minuten-Regel.
- **Fix:** die beiden StorageCrawlJob-Fälle laufen auf dem Fake und prüfen Marker und Slice-Lock je genau einmal in der Reihenfolge; der ScanRecountJob-Fall setzt die letzte Runde genau RECOUNT_MIN_INTERVAL_SECONDS zurück. Aussage jeweils unverändert, im Audit vermerkt.
- **Commit:** 104bf781, 941c68f0

**2. [Hinweis] RED nicht nur mit den neuen Fällen**
- Die zwei angepassten StorageCrawlJob-Fälle und die ScanRecountJob-Grenze waren im RED-Lauf rot, weil sie die noch fehlende Konstante nennen (Error, keine geänderte Aussage). Vier neue Fälle aus Task 2 und einer aus Task 3 waren vor dem Fix schon grün (bewachen bestehendes Verhalten); die zugehörigen Zweige sind über M8, M23 und M24 rot belegt. Steht im Audit.

## Neue Befunde

- I-45-23-07 (INFO, kein Fix): Version001500Date20261012000000 setzt bei einem Update von vor 1.5 die Marke ("ScanRecountJob sees the mark within its interval"); mit dem Mindestabstand startet diese Runde bei einem Sprung von vor 1.5 auf 1.7.0 bis zu sechs Stunden später. Owner-Frage im Audit (sofort zählen wie gespeicherte Regeln oder hinnehmen und Docblock nachziehen).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche: kein neuer Endpunkt, kein neuer Pfad in Logs (beide warning-Zeilen tragen nur `storage_id`, `retries`, `exception`).

## Self-Check: PASSED

- Dateien vorhanden: StorageCrawlJob.php, CrawlAdvanceService.php, SettingsService.php, ScanRecountJob.php, vier Testdateien, php.yml, test_measurement_scripts.py, admin-page.md, drei CHANGELOGs, 45-AUDIT.md, 45-FREIGABEN.md, dieses SUMMARY.
- Commits vorhanden: 6227bdff, 104bf781, 941c68f0.
