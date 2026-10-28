---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 12
subsystem: Launch-Audit 1.5.0 (Security, Bugs, Performance)
tags: [hart-06, launch-audit, security, performance, php-regex, id-parser, reconcile-log]
requires: [36-11]
provides:
  - "36-AUDIT.md: milestone-weites Audit 17363bb2..HEAD, S1 bis S8, B1 bis B5, P1 bis P5, Status fixed, 0 CRIT / 0 HIGH"
  - "backend/tests/test_phase36_audit.py: Syntaxbaum-Proben S4/S5/S6 mit Positivkontrollen, ein Regressionstest je Befund, Wächter F2/F6, kein xfail"
  - "Fix L-36-01: D-Modifikator an fünf verankerten PHP-Formprüfungen"
  - "Fix L-36-02: kanonische Ziffern in ReconcileController::storageIdList und QueueController::positiveId"
  - "Fix L-36-03: Nachlauf-Logzeile nennt höchstens 20 Storage-IDs je Liste"
affects: [36-13, 36-15]
tech-stack:
  added: []
  patterns:
    - "Quelltextprobe über den Syntaxbaum (ast) statt grep, jeweils mit Positivkontrolle"
    - "PHP-preg-Muster in Python mit PCRE-Semantik ausgewertet ($ ohne D vor finalem Newline)"
    - "OCS-Aufrufe eines Abgleich-Zyklus an nc_py_api._session gezählt, nicht geschätzt"
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-AUDIT.md
    - backend/tests/test_phase36_audit.py
  modified:
    - php/lib/Controller/PageController.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/ExAppService.php
    - php/lib/Controller/ReconcileController.php
    - php/lib/Controller/QueueController.php
    - php/tests/Unit/ReconcileControllerTest.php
    - php/tests/Unit/QueueControllerTest.php
    - backend/src/findling/worker/reconcile.py
    - backend/tests/test_measurement_scripts.py
    - docs/reconcile.md
decisions:
  - "L-36-04 (ein requeue je gelöschtem Storage, 300 Storages = 19 s) akzeptiert: einmalig, nachts hinter dem Ruhetor; Bündeln über Storages würde die Zusage 'Lesezeichen erst nach dem letzten Band' koppeln"
  - "P5: 169 Abfragen je Poll (34-AUDIT: 186), gedeckelt durch EXAMPLES_PER_GROUP, kein Release-Blocker, Deferred v1.6, keine Owner-Frage"
  - "F2 bleibt an 36-13 übergeben (Bump vor UPGRADE_FROM_TAG v1.4.3), mit Wächtertest statt Umstellung in 36-12"
  - "QueueController::positiveId (Bestand) im selben Fix wie die neue Route, weil dieselbe Form an derselben Vertrauensgrenze steht"
metrics:
  duration: "ca. 110 min (10:00 bis 11:50 Ortszeit), davon 13 min volle Suite, 3,5 min test_v14_zelle und ca. 30 min CI"
  completed: 2026-10-21
  tasks: 3
  files: 12
requirements: [HART-06]
---

# Phase 36 Plan 12: Launch-Audit 1.5.0 Summary

Milestone-weites Security-, Bug- und Performance-Audit über 76 Dateien des Diffs seit v1.4.2/v1.4.3, jede Prüfung per Befehl und mit Gegenprobe: **0 CRIT / 0 HIGH / 0 MEDIUM**, vier LOW, davon drei im Produkt gefixt (verankerte PHP-Muster ohne `D`, nicht kanonische IDs an der neuen Storage-Route, unbegrenzte Nachlauf-Logzeile) und einer begründet akzeptiert.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Security und Bugs milestone-weit, Proben, Befunde als strict xfail | 884c8554 |
| 2 | Performance P1 bis P5 | 1e356119 |
| 3 | Fix L-36-01 | 69815132 |
| 3 | Fix L-36-02 | 38e54d32 |
| 3 | Fix L-36-03 | 6dee66f4 |
| 3 | Bericht geschlossen, SUMMARY, STATE, ROADMAP | docs(36-12): launch audit 1.5.0 closed (letzter Commit des Plans) |

## Befunde nach Schwere

- CRITICAL 0, HIGH 0, MEDIUM 0.
- **L-36-01** (fix): `?similar=14%0A` öffnete die Ähnlich-Ansicht; fünf Muster ohne `D`. Live danach Startseite.
- **L-36-02** (fix): `GET /storages/gone` mit 20 Ziffern antwortete 200 mit `PHP_INT_MAX`, `014` las als 14. Live danach beide 400.
- **L-36-03** (fix): Sweep-Zeile mit allen 300 IDs; jetzt höchstens 20 je Liste und "and N more".
- **L-36-04** (accept): ein Löschauftrag je Storage (P3).
- Neubewertet: L-32-01/03/04/05 accept bleibt, L-32-07 durch Owner-Abnahme erledigt, L-35-02 accept bleibt, L-35-06 geschlossen (S3 live mit Positivkontrolle).

## Messwerte (Auszug)

- P1: langsamster Korpusfall lokal 0,71 s gegen 30 s.
- P2: Vorzählung p95 0,10 bis 0,39 ms auf echten Dateien und dem 1-Mio.-Paket, +0,3 MiB; vorher `ZipFile()` 447 MiB und 3,7 s.
- P3: Abgleich 0,4 s / 8 OCS-Aufrufe ohne, 0,69 s / 10 mit je einem verschwundenen und gelöschten Storage; Storage-Frage 2 Bänder für 301.
- P4: zweites `Image.open` nur im Bomben-Zweig, png_bomb p50 0,32 ms.
- P5: 169 Abfragen je Poll, Urteil kein Blocker.

## Gates und CI

- Lokal auf dem Endstand 6dee66f4: ruff check (src, tests, scripts) und ruff format (233 Dateien) grün, pyright latest 0 Fehler, vulture sauber; `php -l` im Container auf allen sieben geänderten PHP-Dateien; Reflexionsprobe der zwei Parser im echten PHP des Containers.
- Volle Suite: 6135 passed, 264 skipped in 13:02 (ohne `test_v14_zelle.py`), danach `test_v14_zelle.py` allein 72 passed. `reuse lint` lokal nicht lauffähig (libmagic), in CI grün.
- Alle `test_phase3*_audit.py` (30 bis 36) gemeinsam: 241 passed, 233 skipped (Instanzproben ohne Umgebung), `grep -c xfail tests/test_phase36_audit.py` = 0.
- Baumhash-Ratschen je Fix doppelt gerechnet (40b-baumhash.py und unabhängig find/sort/tr/sha256sum): PHP 60821e1a auf f830ac26 (L-36-01) auf f8eaf591 (L-36-02), Paket 73e0501d auf 569925a1 (L-36-03), Dateizahlen 107 / 80 unverändert.
- CI-Block für 6dee66f4 (Push mit allen fünf Commits), alle acht Läufe success: Python gates 39575471591, PHP and store metadata gates 39575471553 (PHPUnit 856 Tests, 3507 Assertions; vorher 854), Integration 39575471563, Security scans 39575471560, Multi-arch image 39575471596, OpenSSF Scorecard 39575471554, Resilience 39575471601, HaRP deploy 39575471666.
- Kein Tag, kein Versionsbump, keine Store-Einreichung; `UPGRADE_FROM_TAG` bleibt v1.4.2.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] QueueController::positiveId mitgezogen**
- **Found during:** Task 3 (L-36-02)
- **Issue:** dieselbe Parserform wie die neue Route, ebenfalls Container-seitig.
- **Fix:** gleiche Rundreise-Prüfung, PHPUnit-Fall mit Positivkontrolle.
- **Commit:** 38e54d32

**2. [Rule 2] Wächtertests für F2 und F6**
- Der Plan verlangt F1 bis F6 "je mit Commit und Test". F2 und F6 hatten keinen eigenen Test; F2 kann in 36-12 nicht umgestellt werden (kein Bump erlaubt). Ergänzt: `test_the_upgrade_start_is_never_ahead_of_the_tree` (Reihenfolge-Wächter, Pitfall 8) und `test_the_similar_documents_line_stands_in_all_six_descriptions_and_the_changelog`.
- **Commit:** 884c8554

**3. P2 ohne echte PPTX/XLSX in testdata**
- `testdata/` enthält keine PPTX/XLSX; gemessen an den größten Dateien des Lastkorpus `.dev/probe-live/loadcorpus` (wie 36-08) plus testdata `34-zip-bombe.docx`. Spitzen-RSS unter Windows über `GetProcessMemoryInfo` statt `/proc`.

**4. P1 aus dem CI-Log**
- `python.yml` schreibt keine Einzelzeiten (`--durations` fehlt); belegt über die Fristprüfung im Test selbst und die grünen ubuntu-Läufe.

## Known Stubs

Keine.

## Threat Flags

Keine neue Fläche. T-36-42 (S1 live und Gate), T-36-43 (S3 mit Positivkontrolle), T-36-44 (S5, P1, P3), T-36-45 (Bericht mit "0 CRIT / 0 HIGH") gemindert.

## Self-Check: PASSED

- FOUND: 36-AUDIT.md (`status: fixed`, "0 CRIT / 0 HIGH"), backend/tests/test_phase36_audit.py (kein xfail), 36-12-SUMMARY.md
- FOUND: Commits 884c8554, 1e356119, 69815132, 38e54d32, 6dee66f4 (auf origin/main)
- CI für 6dee66f4: acht Läufe success
