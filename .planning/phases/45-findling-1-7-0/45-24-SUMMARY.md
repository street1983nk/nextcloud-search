---
phase: 45-findling-1-7-0
plan: 24
subsystem: backend-reconcile
tags: [issue-25, f2, reconcile, quiet-mark, backstop, admin-page, l10n, tdd]
requires: [45-23]
provides: [BACKSTOP_FACTOR 2 im Abgleich, Meta-Schlüssel reconcile_quiet_held_since (QUIET_HELD_MARK), warning-Zeile beim Öffnen des Rückhalts, Statusfeld reconcileHeldSince ab einem Intervall, Hinweis findling-reconcile-held in 18 Katalogen, Doku reconcile.md und admin-page.md, info.xml Text 4, CHANGELOG Text 2, Baumhashes Paket 6de76760 -> d45bc1d3 und PHP 976184c1 -> 05797073]
affects: [45-25, 45-20, 45-21, 45-10, 45-15, 45-16]
tech-stack:
  added: []
  patterns: [Gate liefert den Grund ohne Log, Rundenflag nur für die laufende Runde, Zeitpunkt im Meta-Speicher mit einem Schreibvorgang je Wartephase, optionaler Zähler über die Status-Route, Uhr als Modulfunktion für Tests]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-24-SUMMARY.md
  modified:
    - backend/src/findling/worker/reconcile.py
    - backend/src/findling/worker/catchup.py
    - backend/src/findling/store/repo.py
    - backend/src/findling/api/status.py
    - backend/appinfo/info.xml
    - backend/tests/test_reconcile.py
    - backend/tests/test_status_endpoint.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - php/lib/Service/AdminViewService.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/tests/Unit/AdminViewServiceTest.php
    - php/tests/Unit/SettingsControllerTest.php
    - php/l10n/*.js, php/l10n/*.json (18 Dateien)
    - docs/l10n-chinese.md, docs/l10n-dutch.md, docs/l10n-french.md, docs/l10n-italian.md, docs/l10n-portuguese.md, docs/l10n-spanish.md
    - docs/reconcile.md
    - docs/admin-page.md
    - CHANGELOG.md, CHANGELOG.de.md, CHANGELOG.fr.md
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
decisions:
  - "Rückhalt nach z1 (Owner 2026-11-22 18:37 UTC): BACKSTOP_FACTOR 2, kein eigener Schalter; Zeitpunkt reconcile_quiet_held_since nur bei fälligem Abgleich, den die Ruhemarke hält, gelöscht nur nach ROUND_WALKED; nie neben einem Crawl, nie bei unlesbarer Warteschlange"
  - "Gate geteilt in _gate (Grund ohne Log) und _quiet (Zustand und die zwei info-Zeilen byte-gleich); in einer Rückhalt-Runde keine Aussetz-Zeile vor einer Scheibe (W3)"
  - "reconcileHeldSince null bei ausgeschaltetem Abgleich, ohne Zustand, bei leerem, unlesbarem, nicht positivem oder jüngerem Zeitpunkt als ein Intervall; in der Backup-Pause von quietInPause auf null gesetzt"
metrics:
  duration: "ca. 55 min laut Systemzeit (ca. 05:45 bis 06:40 UTC), davon ca. 15 min Docker (PHP RED, GREEN, zwei volle Verify-Läufe Task 2)"
  completed: 2026-11-23
---

# Phase 45 Plan 24: #25 F2, die Ruhemarke hungert den Abgleich nicht mehr aus Summary

Ein fälliger Abgleich, den die Ruhemarke zweimal sein Mindestintervall lang (Standard 48 h) zurückhält, läuft trotzdem, nie neben einem Crawl; der Zeitpunkt steht unter `reconcile_quiet_held_since` im Zustandsspeicher, eine warning-Zeile nennt das Öffnen, und die Admin-Seite zeigt ab einem Intervall einen Hinweis in allen 18 Katalogen.

## Tasks

| Task | Inhalt | Commit |
|---|---|---|
| 1 | Rückhalt in reconcile.py (BACKSTOP_FACTOR, `_gate`/`_quiet`, `_held_since`, `_clear_held_since`, Rundenflag), QUIET_HELD_MARK in repo.py, catchup.py-Docstring, 15 neue Testfälle, sechs Mutationen M10 bis M15, Baumhash Paket | 0fc40005 |
| 2 | Statusfeld reconcileHeldSince, AdminViewService (optionaler Zähler, null in der Pause), Template und admin.js, Text 3 in 18 Katalogen und sechs Sprachtabellen, Schlüsselzahl 384, Mutation M16, Baumhashes Paket und PHP | bc98ec2b |
| 3 | docs/reconcile.md (Abschnitt Rückhalt, F1-Satz), docs/admin-page.md (Hinweis), info.xml Text 4, CHANGELOG Text 2 EN/DE/FR | 7d2d7a64 |

## Ergebnisse

- Task 1: RED `17 failed, 104 passed` (alle neuen Fälle, AttributeError der Konstante), zweiter RED mit nur der Konstante `11 failed, 110 passed`; GREEN `121 passed`. Verify wörtlich (`<scratchpad>/v24_t1.sh`) -> `VERIFY_EXIT=0`: ruff, ruff format (260), pyright latest 0/0/0, vulture ohne Fund, pytest inkl. aller 17 Dateien der Liste `Weitere Tests` `1749 passed, 1 skipped`.
- Task 2: RED Python `71 failed, 279 passed` (Feldmenge, `_now` fehlt, Contract, Schlüsselzahl), PHP gefiltert `Tests: 288, Assertions: 1713, Failures: 9.`; GREEN Python `672 passed, 12 skipped`, PHP `OK (288 tests, 1770 assertions)`. Verify wörtlich (`<scratchpad>/v24_t2.sh`) -> `VERIFY_EXIT=0`: PHPUnit voll `OK (1408 tests, 8847 assertions)`, Psalm-Taint 0 gegen v33.0.9/v34.0.6/v35.0.3, php-cs-fixer, zizmor, actionlint grün, Python-Gates grün, pytest `1244 passed, 12 skipped`, Docker danach leer.
- Task 3: Verify wörtlich (`<scratchpad>/v24_t3.sh`) -> `VERIFY_EXIT=0`, pytest `880 passed`; zusätzlich info.xml- und Doku-Gates `605 passed, 114 skipped`.
- Mutationen (je rot, Quelle danach byte-gleich): M10 Rückhalt ohne Crawl-Prüfung, M11 Faktor 1, M12 Zeitpunkt bei jeder offenen Runde gelöscht, M13 Rundenflag in `_walk` übergangen, M14 Zeitpunkt jeden Takt neu, M15 Zukunftswert nicht ersetzt, M16 Statusfeld ohne Ein-Intervall-Schwelle.
- Baumhash backend/src/findling: 9fa6c443 -> 6de76760 (Task 1) -> d45bc1d3 (Task 2), 83 Dateien; php/: 976184c1 -> 05797073 (Task 2), 143 Dateien; Positivkontrollen über git archive 3d18b701 und 0fc40005.
- Kein Push, kein Tag, kein Kommentar. Docker am Ende leer.

## Neue Katalogsätze (für die Bitte an foolfitz in 45-15)

1. `A long queue has held the comparison run back for longer than its interval. It runs anyway once it has waited twice as long, and this note stays until it has been through all files; until then, files that only this run finds, for example new files on external storages, may be missing from the search.` (zh_TW maschineller Entwurf: 佇列過長，比對作業被延後的時間已超過其間隔。等待時間達到兩倍後仍會執行，而此提示會保留到它檢查完所有檔案為止；在此之前，只有這項作業才會找到的檔案（例如外部儲存空間上的新檔案）可能不會出現在搜尋結果中。)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ruff E501 an der warning-Zeile und im catchup.py-Docstring**
- **Found during:** Task 1
- **Issue:** Die warning-Zeile muss nach verify wörtlich auf einer Zeile stehen (135 Zeichen); der umgeschriebene catchup.py-Satz brach eine Zeile über 120.
- **Fix:** `# noqa: E501` mit Begründung an der Log-Zeile (Muster wie vectors.py), Docstring neu umbrochen, Baumhash danach neu gerechnet.
- **Commit:** 0fc40005

**2. [Rule 3 - Blocking] php-cs-fixer am neuen Docblock des Test-Helfers**
- **Found during:** Task 2, erster Verify-Lauf
- **Issue:** mehrzeiliges @param mit Einzug, den nextcloud/coding-standard anders ausrichtet.
- **Fix:** Satz plus einzeiliges @param; PHP-Baumhash neu gerechnet, Verify ein zweites Mal ganz gelaufen.
- **Commit:** bc98ec2b

**3. [Hinweis] Status-Uhr als Modulfunktion `_now()`**
- Damit der Test die Ein-Intervall-Schwelle auf die Sekunde prüft, liest status.py die Zeit über `_now()` statt direkt `time.time()`.

**4. [Hinweis] RED nicht nur mit den neuen Fällen (Task 2)**
- 62 bestehende Fälle der geschlossenen Feldmenge wurden rot, weil FIELDS das neue Feld bewusst zuerst bekam (so verlangt der Plan es); `test_the_german_catalogue_covers_both_german_language_codes` war rot wegen der gehobenen Schlüsselzahl. Sechs neue Fälle aus Task 1 waren vor dem Fix schon grün (Wächter); M10 bis M12 belegen ihre Zweige.

**5. [Hinweis] test_store_metadata.py nicht geändert**
- Steht in `files_modified`, zählt aber keine Katalogschlüssel und hat keinen Digest auf die geänderte Beschreibung; seine Gates liefen grün.

## Offene Punkte

- IDX-10 bleibt in REQUIREMENTS.md offen wie IDX-09 aus 45-23: der echte Beleg folgt in 45-20 Task 2 (Live-Probe mit verkürztem Intervall, Messung ab `Zeitpunkt gesetzt:`).
- Die Übersetzungen es, it, nl, pt_BR, pt_PT, zh_TW des Hinweises sind maschinelle Entwürfe (Bitte an foolfitz in 45-15).

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche über das Register hinaus: das Statusfeld ist eine ganze Zahl (T-45-85), der Satz kommt aus dem Katalog über textContent, die warning-Zeile trägt nur Stunden, Zähler und Marke.

## Self-Check: PASSED

- Dateien vorhanden: reconcile.py, catchup.py, repo.py, status.py, info.xml, vier Python-Testdateien, AdminViewService.php, admin.php, admin.js, zwei PHP-Testdateien, 18 Kataloge, sechs Sprachdokus, reconcile.md, admin-page.md, drei CHANGELOGs, 45-AUDIT.md, dieses SUMMARY.
- Commits vorhanden: 0fc40005, bc98ec2b, 7d2d7a64.
