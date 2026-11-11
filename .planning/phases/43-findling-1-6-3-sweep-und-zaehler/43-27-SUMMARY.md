---
phase: 43-findling-1-6-3-sweep-und-zaehler
plan: 27
subsystem: Audit-Nachtrag (Security, Bugs, Performance) über das Delta 43-21 bis 43-26, backend/src/findling (store, api, worker), php/lib (Service, BackgroundJobs)
tags: [D-43-15, D-43-17, T-43-83, T-43-84, T-43-85, T-43-86, audit, tdd, e2e, crawl, retry]
requires: [43-26]
provides: [Audit-Nachtrag in 43-AUDIT.md, audited_head 2dacf753 mit grünem E2E-Lauf 43094681914, status_43_27 passed, d_43_15 behoben, vier LOW-Fixes]
affects: [43-29, 43-11, 43-12, 43-13, 43-14]
tech-stack:
  added: []
  patterns: [Wiederholung nur für Datenbankfehler und nur mit Obergrenze ohne Fortschritt, Cursor des letzten Commits statt des fehlgeschlagenen Eintrags, Gegenprobe gegen die Quelle ohne Fix vor dem GREEN-Commit]
key-files:
  created:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-27-SUMMARY.md
    - backend/tests/test_phase43_audit_roots.py
  modified:
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-AUDIT.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-E2E-WURZEL.md
    - .planning/phases/43-findling-1-6-3-sweep-und-zaehler/43-FREIGABEN.md
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/api/coverage.py
    - php/lib/Service/StorageService.php
    - php/lib/Service/DocKeyService.php
    - php/lib/BackgroundJobs/StorageCrawlJob.php
    - php/tests/Unit/StorageCrawlJobTest.php
    - backend/tests/test_measurement_scripts.py
    - CHANGELOG.md
    - CHANGELOG.de.md
    - CHANGELOG.fr.md
decisions:
  - "Owner-Entscheid A (11.11.2026): die drei LOW F-43B-01 bis -03 werden vor dem Release behoben, F-43B-04 bleibt akzeptiert"
  - "Owner-Entscheid A (11.11.2026) nach dem roten Lauf 43079756645: Produkt-Fix statt bloßer Wiederholung; F-43B-05, ein Datenbankfehler in einem Crawl-Abschnitt plant einen Nachfolger mit dem letzten committeten Cursor ein, höchstens fünfmal in Folge ohne Fortschritt"
  - "audited_head ist 2dacf753 (letzter Commit außerhalb von .planning); der belegende Lauf 43094681914 lief auf aabc17cc ohne Code-Unterschied dazu"
  - "Der Changelog-Satz zu F-43B-02 und der zu F-43B-05 sind Entwürfe für die Textrunde 43-12"
metrics:
  completed: 2026-11-11T22:10:00Z
  tasks: 3
  findings: 12
---

# Phase 43 Plan 27: Audit-Nachtrag, Fix-Runden und neuer audited_head

Der Audit-Nachtrag über das Delta von 43-21 bis 43-26 ist abgeschlossen: 0 CRITICAL, 0 HIGH, 0 MEDIUM, 5 LOW (4 behoben, 1 akzeptiert), 7 INFO. Der neue audited_head 2dacf753 ist an den grünen E2E-Lauf 43094681914 gebunden, d_43_15 steht auf behoben.

## Tasks

1. **Audit und Proben** (a2bc46ad, cdd16d05, f5739046): neun Audit-Proben, Nachtrag in 43-AUDIT.md, kein Produktcode geändert.
2. **Owner-Checkpoint**: Freigaben in 43-FREIGABEN.md (Push 43-27, Dispatch 43-27, Push und Dispatch 43-27 Fix 2, Wiederholung).
3. **Fix-Runden, Push, E2E, Beleg**:
   - Fix-Runde 1: F-43B-02 (0c7146b2, b1cddb8b), F-43B-03 (79a79466, c36ffc0e), Changelog (bdec190e), F-43B-01 (2b5bd60d, 9bf7dddf).
   - Lauf 43079756645 auf 57271f63: ein Bein rot (gate-queue / native), Ursache "database is locked" in einem StorageCrawlJob, der Crawl des Mounts endete ohne Nachfolger.
   - Fix 2: F-43B-05 (RED ae44f61d, GREEN 2dacf753), Doku 5a37961a.
   - Lauf 43094681914 auf aabc17cc: success, sieben Beine grün; sechs davon im zweiten Versuch nach einem Ausfall von GitHub Actions beim Artefakt-Upload.

## Belege

- PHPUnit lokal (Docker): Gegenprobe ohne Fix 2 rot (2 Errors, 1 Failure), mit Fix 12 von 12 im Filter, volle Suite 1205 Tests, 7719 Assertions.
- Python: ruff, ruff format, pyright, vulture grün; betroffene Module grün; die volle Suite lief im Workflow "Python gates" auf 2dacf753.
- Acht Workflows auf 2dacf753 grün (IDs in 43-AUDIT.md, "Läufe auf audited_head").
- `scripts/ci/e2e_head_proof.sh 2dacf753... 43-E2E-WURZEL.md`: Exit 0. Der verify-Befehl von Task 3: Exit 0.
- Werte des Laufs: failures=0 in allen Beinen, 85 von 95 Zeilen, hashedVerified 3, hashedUngrouped 2, k = 4, W5 15 von 15, keine Zeile "coverage count without a vector stock".

## Abweichungen vom Plan

- Zwei E2E-Läufe statt einem, dazu ein Neustart der fehlgeschlagenen Jobs: der erste Lauf deckte F-43B-05 auf, der zweite traf einen Ausfall von GitHub Actions. Jeder Schritt hat seine eigene Owner-Freigabe.
- F-43B-05 stammt nicht aus dem auditierten Delta, sondern aus dem roten Lauf; der Code stand so seit dem ersten Release.

## Offen, nicht Teil dieses Plans

- Der Wiederholungsweg von F-43B-05 ist durch PHPUnit belegt, nicht end to end: im grünen Lauf trat die Sperre in den Beinen mit Fix nicht auf.
- Wie lange der Abgleich in Produktion braucht, um einen abgebrochenen Mount nachzuholen, ist nicht gemessen.
- Aus 43-26 unverändert offen: Zeitreserve des Beins gate-queue / wrapped, gone_path=not_exercised.
- Im Ping an mbozem (43-14) erwähnen: nach dem Update bei sehr großen Instanzen stundenlang "wird gezählt", die Suche läuft normal.
