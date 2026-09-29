---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 04
subsystem: php-companion
tags: [php, appconfig, probe, transport]
requires: []
provides:
  - SettingsService::profileStored, needsProbe, isDownward, saveProfile, saveConfirmation
  - SettingsService::profileCheck, rememberProfileCheck, profileCheckPending, rememberPending, forgetPending
  - SettingsService::KEY_PROFILE_CHECK, KEY_PROFILE_CHECK_PENDING
  - ExAppService::adminSend, adminState (kind ok|unreachable|missing|busy|refused)
affects: [27-07, 27-08]
tech-stack:
  added: []
  patterns: [echter SettingsService auf gedoubeltem IAppConfig, proxyRequest-Double]
key-files:
  created:
    - php/tests/Unit/SettingsServiceTest.php
  modified:
    - php/lib/Service/SettingsService.php
    - php/lib/Service/ExAppService.php
    - php/tests/Unit/ExAppServiceTest.php
decisions:
  - "saveProfile schreibt zuerst das Profil, dann die Präzision: scheitert der zweite Schreibvorgang, bleibt nie ein schwereres Paar als das geprüfte"
  - "Keine Änderung (Ziel = gespeicherter Stand) braucht nach D-27-09 wörtlich die Probe; nur Sparsam und reines fp32 zu int8 sind Abwärtswege"
  - "409 mit unlesbarem Körper bleibt busy (body null); ein JSON-Array statt Objekt ist refused"
  - "Transport-Logs ohne Pfad und ohne AppAPI-Fehlertext, weil der die URL trägt (T-27-10)"
metrics:
  duration: ca. 25 min
  completed: 2026-09-29
  tasks: 2
  files: 4
---

# Phase 27 Plan 04: PHP-Grundlagen für Profil-Schreibweg und Probe-Transport Summary

SettingsService liest und schreibt Profil, Präzision, Bestätigungs-Token und Probe-Ergebnis in appconfig und entscheidet D-27-09 serverseitig; ExAppService bekommt mit adminSend/adminState einen Container-Transport, der unerreichbar, alte Version (404), belegt (409) und abgelehnt unterscheidet.

## Erledigt

| Task | Inhalt | Commits |
|------|--------|---------|
| 1 | SettingsService: profileStored (hasKey), needsProbe/isDownward, saveProfile (strict, fp32 in economy nur als Bestand, Throwable gefangen), saveConfirmation (/D-Anker), Probe-Ablage über setValueArray/getValueArray/deleteKey; occ-Docblocks auf D-27-13 umgeschrieben | aeef83be (test), 98d93f8d (feat) |
| 2 | ExAppService: adminSend (POST, Body), adminState (GET, leere Parameter), beide mit ADMIN_REQUEST_TIMEOUT_SECONDS über proxyRequest; gemeinsame Auswertung adminOutcome + boundedObject (Größe, Objektform, JSON_THROW_ON_ERROR); adminGet unverändert | 60a1382a (test), f82ad6d6 (feat) |

## Verifikation

- `php -l` (php:8.3-cli in Docker) für alle vier Dateien: keine Syntaxfehler
- Acceptance-Greps: hasKey( 2, `[0-9a-f]{32}$/D` 2, adminSend/adminState 2, Kind-Literale 4
- Verhaltens-Smoke von SettingsService (eval mit gestubbten OCP-Klassen, in Docker, danach gelöscht): alle 9 needsProbe-Fälle und 12 Schreib-/Lese-Prüfungen grün
- `uv run pytest -q tests/test_php_trust_boundary.py`: 21 passed
- PHPUnit: lokal nicht ausführbar (braucht nextcloud/server-Bootstrap), läuft in CI (php.yml) nach Push

## Deviations from Plan

None - plan executed exactly as written. Hinweis zur TDD-Reihenfolge: In Task 2 entstand der Code vor dem Test, committet wurde trotzdem test vor feat; ein echter RED-Lauf war mangels lokalem PHPUnit in beiden Tasks nicht möglich.

## TDD Gate Compliance

test-Commits (aeef83be, 60a1382a) liegen jeweils vor den feat-Commits (98d93f8d, f82ad6d6). RED nicht lokal gelaufen (kein PHPUnit lokal), Nachweis erst in CI.

## Known Stubs

Keine.

## Self-Check: PASSED

- php/tests/Unit/SettingsServiceTest.php vorhanden
- Commits aeef83be, 98d93f8d, 60a1382a, f82ad6d6 im Log
