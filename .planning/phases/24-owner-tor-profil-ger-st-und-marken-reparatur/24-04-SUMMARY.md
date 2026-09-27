---
phase: 24-owner-tor-profil-ger-st-und-marken-reparatur
plan: 04
subsystem: php-companion
tags: [profile, appconfig, ocs, exapp-guard, PROF-03]
requires: []
provides:
  - "SettingsService::profile() mit geschlossener Menge economy/standard/performance, Default economy"
  - "OCS-Route GET /ocs/v2.php/apps/findling/profile, nur für das Findling-Backend"
affects:
  - "Plan 24-05 (Container-Seite: liest die Route, Gleichstandstest PROFILES <-> PROFILE_NAMES)"
tech-stack:
  added: []
  patterns: ["ReconcileController-Muster (Attribut-Trio, rejectForeignCaller als erste Anweisung)", "Validierung beim Lesen wegen ungeprüftem occ-Schreibweg"]
key-files:
  created:
    - php/lib/Controller/ProfileController.php
    - php/tests/Unit/ProfileControllerTest.php
  modified:
    - php/lib/Service/SettingsService.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "rejectForeignCaller als private Kopie statt Trait (kleinster Eingriff in freigegebenen Code)"
  - "Lesefehler in der Route antworten mit PROFILE_DEFAULT statt 500 (fail-safe Sparsam)"
metrics:
  duration: "ca. 25 min"
  completed: 2026-09-27
  tasks: 2
  files: 4
---

# Phase 24 Plan 04: Profil-Route PHP-Seite Summary

appconfig-Leser `SettingsService::profile()` mit geschlossener Menge (Unbekanntes wird economy, gezählt, Wert nie geloggt) und ExApp-geschützte OCS-Route `GET /profile` in neuem `ProfileController` nach ReconcileController-Muster.

## Tasks

| Task | Name | Commit | Dateien |
|------|------|--------|---------|
| 1 | SettingsService::profile() mit geschlossener Menge | 9a59a88 | php/lib/Service/SettingsService.php |
| 2 (RED) | Failing Test für die Profil-Route | fb2cc94 | php/tests/Unit/ProfileControllerTest.php |
| 2 (GREEN) | ProfileController mit GET /profile | 001cf99 | php/lib/Controller/ProfileController.php, php/tests/Unit/ProfileControllerTest.php, backend/tests/test_measurement_scripts.py |

## Verifikation

- `php -l` (Docker php:8.3-cli) für alle drei PHP-Dateien: keine Syntaxfehler
- Gate B (`test_php_trust_boundary.py`) und `test_uninstall_contract.py`: 36 passed, neue Route mitgezählt
- Volle Backend-Suite: 3349 passed, 1 flakiger Fehlschlag (siehe unten)
- Alle Acceptance-Greps erfüllt (KEY_PROFILE, PROFILES einzeilig, profile(): string, kein saveProfile, ApiRoute, rejectForeignCaller)
- PHPUnit: nur CI (php.yml); lokal braucht der Bootstrap einen nextcloud/server-Checkout. PHPUnit-Version 11.5.56 per Composer geprüft, deshalb `isString()` statt des dort deprecateten `isType()`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] PHP-Baumhash-Ratchet nachgezogen**
- **Found during:** Task 2
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half` hält Dateizahl und Baumhash der PHP-Hälfte fest (72 -> jetzt 74, Hash geändert)
- **Fix:** `PHP_FILES_TODAY = 74` und neuer Hash `170f144a...` mit Kommentarzeile nach bestehendem Muster; Hash mit dem Rezept `40b-baumhash.py` selbst berechnet
- **Hinweis für den Merge:** Andere Pläne der Welle, die PHP-Dateien ändern, bewegen dieselbe Konstante; nach dem Merge den Hash einmal neu berechnen
- **Commit:** 001cf99

**2. [Rule 1 - Bug] PHPUnit-Deprecation vermieden**
- `self::isType('string')` ist in PHPUnit 11.5 deprecated, ersetzt durch `self::isString()` (Commit 001cf99)

## Deferred Issues

- `tests/test_embedding_track.py::test_the_delete_job_of_the_poller_takes_the_vectors_with_it` schlug im Vollauf einmal fehl, isoliert grün; flakig, ohne Bezug zur PHP-Änderung, nicht angefasst.
- PROF-03 nicht als erledigt markiert: dieser Plan liefert nur die PHP-Hälfte, die Container-Seite folgt in Plan 05.

## Threat Model

- T-24-12: ExAppRequired + rejectForeignCaller als erste Anweisung, fremder Aufrufer 403 ohne Profilnamen (Test 4)
- T-24-13: geschlossene Menge, Unbekanntes wird economy plus reject() (Test 3)
- T-24-15: statische Log-Sätze, Profilwert nie im Kontext (Test 3 prüft das)

## TDD Gate Compliance

RED (fb2cc94, test) vor GREEN (001cf99, feat) vorhanden. RED konnte lokal nicht ausgeführt werden (kein PHP-Stack); die Klasse existierte zum RED-Zeitpunkt nicht.

## Self-Check: PASSED

- FOUND: php/lib/Controller/ProfileController.php
- FOUND: php/tests/Unit/ProfileControllerTest.php
- FOUND: 9a59a88, fb2cc94, 001cf99
