---
phase: 45-findling-1-7-0
plan: 19
subsystem: php-companion-admin-page
tags: [v-45-10-02, v-45-10-03, external-storage, confirmation, l10n, tdd]
requires: [45-18]
provides: [Regel c für das duplicate-Merkmal (nur Einhängepunkt), data-mount-duplicate an der Checkbox, Bestätigung mit ID in Form i, Platzhalter der Diagnose aus dem Katalog in 18 Dateien, Schlüsselzahl 383]
affects: [45-22, 45-20, 45-21, 45-10]
tech-stack:
  added: []
  patterns: [Merkmal vom Server als data-Attribut unter genau einer Bedingung, eine Regex-Ersetzung mit Callback statt verketteter String-Replacements, node-Harness mit ausgeschnittenen admin.js-Funktionen und Text-only-Element]
key-files:
  created:
    - .planning/phases/45-findling-1-7-0/45-19-SUMMARY.md
  modified:
    - php/lib/Service/ExternalMountService.php
    - php/tests/Unit/ExternalMountServiceTest.php
    - php/templates/admin.php
    - php/js/admin.js
    - php/l10n/*.js und *.json (18 Dateien)
    - docs/l10n-chinese.md, l10n-dutch.md, l10n-french.md, l10n-italian.md, l10n-portuguese.md, l10n-spanish.md
    - backend/tests/test_admin_locale.py
    - backend/tests/test_admin_ui_contract.py
    - backend/tests/test_measurement_scripts.py
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
    - .planning/phases/45-findling-1-7-0/45-AUDIT.md
decisions:
  - "Owner 2026-11-22 18:37 UTC 'Go mit den Empfehlungen': V-02-Regel c, ein duplicate-Merkmal nur nach dem Einhängepunkt in ExternalMountService, Liste und Bestätigung lesen es"
  - "Der Skript-Gate lässt im Speicherteil genau `dataset.mountDuplicate === 'true'` zu, jedes andere dataset bleibt ein Befund"
  - "Der Platzhalter-Gate prüft nur das Feld der Diagnose; die festen Platzhalter 'Backups' und '*.photoslibrary' der Regelfelder liegen außerhalb des Plans"
metrics:
  duration: "ca. 40 min laut Systemzeit (ca. 19:05 bis 19:45 UTC), davon ca. 25 min zwei volle Docker-Läufe, dazu die Pause nach dem Abbruch des ersten Laufs wegen Speichermangel"
  completed: 2026-11-22
---

# Phase 45 Plan 19: ID in der Bestätigung und Platzhalter aus dem Katalog Summary

Speicher mit gleichem Einhängepunkt tragen in Liste und Bestätigung dieselbe ID-Regel (Merkmal vom Server, nur nach dem Einhängepunkt, Bestätigung "/Share (ID 5), /Share (ID 8), /Share (ID 17)"); der Beispielpfad der Diagnose kommt aus dem Katalog (DE "alice/files/Verträge/Miete.pdf") in allen 18 Dateien.

## Tasks

| Task | Inhalt | Commit |
|---|---|---|
| 0 | Owner-Entscheid V-02-Regel c in 45-FREIGABEN.md, Hinweis UTC und Bezug auf die Empfehlungen im Chat | cf53cfd8 |
| 1 | V-45-10-02: Regel c in ExternalMountService, `data-mount-duplicate` im Template, `mountDuplicateOf` und `confirmedMounts` in admin.js, drei node-Fälle, zwei Gates, neuer PHP-Fall, Baumhash | c33103fe |
| 2 | V-45-10-03: Platzhalter über `$l->t('alice/files/Contracts/Rent.pdf')`, Schlüssel in 18 Katalogen und sechs Sprachtabellen, Schlüsselzahl 383, Baumhash | 1b31b281 |

## Ergebnisse

- Task 0 verify (aus Skriptdatei): `T0_OK`.
- RED Task 1: Python `5 failed, 1 passed, 231 deselected` (der grüne Fall ist ein bestehender, vom Filter erfasster), PHP gefiltert `Tests: 11, Assertions: 52, Failures: 1`.
- GREEN Task 1: verify-Zeile `<scratchpad>/v19_t1.sh` bis einschließlich ruff format grün (PHPUnit `OK (1347 tests, 8616 assertions)`, PHP-Gates grün, pytest `809 passed`); der Hintergrundlauf wurde danach wegen Speichermangel beendet; pyright latest `0 errors` und vulture ohne Fund liefen auf Freigabe des Koordinators im Vordergrund, Baum dazwischen unverändert.
- RED Task 2: `1 failed, 226 deselected`. GREEN Task 2: verify-Zeile `<scratchpad>/v19_t2.sh` -> `VERIFY_EXIT=0` (PHPUnit `OK (1347 tests, 8616 assertions)`, PHP-Gates grün, pytest `810 passed`, ruff, format, pyright 0/0/0, vulture).
- Mutationen (je rot, Datei danach byte-gleich): V1 Bestätigung ohne ID (drei node-Fälle rot), V2 zwei String-Replacements (`..._keeps_markup_and_replacement_patterns_as_text` und Skript-Gate rot), V3 Typ zurück im Schlüssel (`testMountsThatShareAMountPointAreDuplicatesWhateverTheBackend` rot), V4 Attribut ohne Bedingung (`test_the_duplicate_mark_only_follows_the_server_flag` rot); Task 2 fester Text zurück (`test_the_example_path_of_the_lookup_comes_from_the_catalogue` rot).
- Baumhash php/: 34d00c1f -> 233c6ab1 (Task 1, Positivkontrolle cf53cfd8) -> a6c5f8d1 (Task 2, Positivkontrolle c33103fe), je 141 Dateien, Rezept und unabhängige Pipeline gleich.
- Docker am Ende leer, kein Push, kein Tag, kein Kommentar.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Bestehender Gate verbot jedes dataset im Speicherteil**
- **Found during:** Task 1
- **Issue:** `scan_mount_script` meldete jedes `dataset`; der Plan verlangt `box.dataset.mountDuplicate === 'true'`.
- **Fix:** Regex lässt genau diesen Ausdruck zu; Fehl-Sample mit `!== undefined` bleibt rot.
- **Files modified:** backend/tests/test_admin_ui_contract.py
- **Commit:** c33103fe

**2. [Rule 1 - Bug im Test] Harness mit überzähligem `return element`**
- **Found during:** Task 1, erster GREEN-Lauf
- **Issue:** ReferenceError im node-Harness; im RED nicht erreicht, weil der Ausschnitt vorher scheiterte.
- **Fix:** Zeile entfernt, Erwartungen unverändert; im Audit vermerkt.
- **Commit:** c33103fe

**3. [Rule 3 - Tooling] RUF001 bei vollbreiten Klammern**
- Die zh_TW-Probe schreibt `（`/`）` als Escape (per Skriptdatei, weil das Werkzeug Escapes zurückwandelt).

**4. [Hinweis] Unterbrochener verify-Lauf von Task 1**
- Claude Code beendete den Hintergrundlauf wegen Speichermangel nach ruff format; Checkpoint an den Koordinator, der den Rest (pyright, vulture) im Vordergrund freigab. Keine Änderung am Baum zwischen Lauf und Commit.

**5. [Hinweis] Kein AdminSettingsTest-Fall in Task 2**
- AdminSettingsTest rendert das Template nicht; DE, EN (Schlüssel) und FR deckt der Katalogtest `test_the_example_path_of_the_lookup_comes_from_the_catalogue` über alle 18 Dateien ("Render- oder Katalogtest" im Plan).

## Befunde

- I-45-19-01 (INFO): Die Regelfelder tragen weiter feste Platzhalter (`placeholder="Backups"`, `placeholder="*.photoslibrary"`, admin.php Z. ~1562 und ~1606). "*.photoslibrary" ist sprachneutral; "Backups" ist ein englisches Wort, das im Deutschen ebenso üblich ist. Kein Fix in diesem Plan; ob der Neulauf von 45-10 das als Befund führt, entscheidet der Koordinator.

## Threat Flags

Keine neue Fläche außerhalb des Threat-Registers: T-45-65 (Bestätigungszeile) mit node-Proben (Markup, '$&', '%2$s', '%1$s$''), Text-only-Element, Gates und V2/V4; T-45-66 (Katalogwert im Attribut) über p() und `test_no_catalogue_value_can_break_the_page`.

## Known Stubs

Keine.

## Offene Punkte

- Sichtprüfung von Liste, Bestätigung (drei Speicher auf einem Einhängepunkt, zwei Typen) und Platzhalter im Browser im Neulauf von 45-10.
- CHANGELOG-Zeile zu V-45-10-03 (Text 7 aus 45-17) folgt in 45-20.
- EXCL-04 und REL-07 bleiben Pending bis zum Neulauf von 45-10 und zum Release.
- Nächster Plan: 45-22.

## Self-Check: PASSED

Commits vorhanden: cf53cfd8, c33103fe, 1b31b281. Dateien vorhanden: 45-19-SUMMARY.md, ExternalMountService.php (Schlüssel nur Einhängepunkt), admin.php (`data-mount-duplicate`, Platzhalter über `$l->t`), admin.js (`confirmedMounts`). Docker leer.
