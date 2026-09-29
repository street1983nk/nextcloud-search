---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 07
subsystem: php-companion
tags: [php, probe, admin-routes, trust-boundary]
requires: [27-02, 27-04]
provides:
  - ProbeService::start, state, settle, result
  - ProbeService::START_* und STATE_* Antwortcodes
  - "POST /admin/profile/check, GET /admin/profile/check, POST /admin/profile"
  - Settings/Admin::getForm übernimmt ein fertiges Verdikt vor overview()
affects: [27-08, 27-10, 27-12, 27-14, 27-15]
tech-stack:
  added: []
  patterns: [echter SettingsService auf gedoubeltem IAppConfig, ExAppService-Double der drei Admin-Methoden, textuelle Mengen-Parität PHP gegen Python]
key-files:
  created:
    - php/lib/Service/ProbeService.php
    - php/lib/Controller/ProfileSettingsController.php
    - php/tests/Unit/ProbeServiceTest.php
    - php/tests/Unit/ProfileSettingsControllerTest.php
    - backend/tests/test_probe_php_parity.py
  modified:
    - php/lib/Settings/Admin.php
    - backend/tests/test_php_trust_boundary.py
decisions:
  - "Übernahme nur bei state done, verdict fits, hash_equals-Id gleich pending und gleichem Ziel; ein schon abgelegtes profile_check mit derselben Id wird nicht erneut übernommen (doppelte Idempotenz neben forgetPending)"
  - "Zeitpunkt des Verdikts = finishedAt des Containers, wenn plausibel (> 0 und nicht in der Zukunft), sonst Serverzeit"
  - "Ein unlesbarer pending-Datensatz wird verworfen, weil er nie zu einer Antwort passen kann"
  - "Bestätigung (D-27-12) nur nach erfolgreichem saveProfile, aus frischem /status, wenn guard.chosen gleich dem Ziel und der Token /D-gültig ist"
  - "start mit ok, aber ohne gültige 16-hex-Id antwortet unreachable und schreibt nichts"
  - "POST /admin/profile lehnt economy+fp32 ohne gespeichertes fp32 als invalid ab (400) statt als failed (500)"
metrics:
  duration: ca. 40 min
  completed: 2026-09-29
  tasks: 2
  files: 7
---

# Phase 27 Plan 07: ProbeService und Profil-Adminrouten Summary

PHP startet die Probe, liest ihren Stand und speichert Profil und Präzision ausschließlich bei einem eigenen, per hash_equals an die Probe-Id und an das Ziel gebundenen "passt"; drei admin-only Routen mit CSRF auf einem Plain Controller, Übernahme auch beim Seitenaufbau.

## Erledigt

| Task | Inhalt | Commits |
|------|--------|---------|
| 1 | ProbeService: start (Kind-Mapping auf started/busy/rebuilding/unsupported/unreachable, pending nur bei gültiger Id), state (Feldprüfung gegen PROBE_*-Mengen, Antwortform laut Vertrag), settle (fragt nur bei laufender Probe), Ablage jedes Verdikts, veraltete Probe (3000 s) als nofit/interrupted, Bestätigungs-Token serverseitig; PHPUnit je Behavior-Punkt; Python-Paritätstest | d19be3ba (test), edee2614 (feat) |
| 2 | ProfileSettingsController mit startCheck/checkState/saveProfile, strikte Mengen, needsProbe bzw. isDownward serverseitig; Admin::getForm ruft settle vor overview() in try/catch; Gate-B-Ratsche +3 | e759e4ce (test), ce2569a5 (feat) |

## Verifikation

- `php -l` (php:8.3-cli in Docker) für alle fünf PHP-Dateien: keine Syntaxfehler
- `test_probe_php_parity.py` 8 passed; `test_php_trust_boundary.py`, `test_readonly_gate.py`, `test_admin_ui_contract.py`, `test_php_acl_boundary.py`, `test_profile_wire.py` grün (132 passed)
- `ruff check .`, `ruff format --check`, `pyright` (latest): grün
- Voller Backend-Lauf: 3954 passed, 1 failed = erwarteter Baumhash-Pin in `test_measurement_scripts.py` (PHP-Baum geändert; Orchestrator pinnt nach dem Merge, nicht angefasst)
- Acceptance-Greps: hash_equals 3, PROBE_*-Konstanten 5, Logger mit token/$id 0, drei FrontpageRoute-Zeilen je 1, extends Controller 1, OCSController 0, verbotene Attribute 0, settle( in Admin.php 1
- PHPUnit: lokal nicht ausführbar (kein PHP, braucht nextcloud/server-Bootstrap), läuft in CI (php.yml) nach Push

## Deviations from Plan

**1. [Rule 3 - Blocking] Admin::getForm-Test textuell statt mit Doubles**
- **Found during:** Task 2
- **Issue:** Settings/Admin braucht einen echten AdminViewService (final, zwölf Abhängigkeiten); ProbeService ist ebenfalls final, ein Double ist nicht möglich.
- **Fix:** In ProfileSettingsControllerTest prüft ein Test den Quelltext von Admin.php: settle( genau einmal, vor overview() und innerhalb eines catch (\Throwable).
- **Commit:** e759e4ce

**2. [Rule 2 - Korrektheit] economy+fp32 im Speicherweg als invalid**
- **Found during:** Task 2
- **Issue:** SettingsService::saveProfile lehnt economy+fp32 ohne gespeichertes fp32 ab; der Controller hätte das als 500 failed gemeldet.
- **Fix:** Vorprüfung im Controller, Antwort 400 invalid.
- **Commit:** ce2569a5

Hinweis zur TDD-Reihenfolge: test-Commits liegen vor den feat-Commits, ein echter RED-Lauf der PHPUnit-Fälle war lokal nicht möglich; der Python-Paritätstest wurde gegen die fertige Klasse ausgeführt.

## TDD Gate Compliance

test-Commits (d19be3ba, e759e4ce) vor feat-Commits (edee2614, ce2569a5). RED nicht lokal gelaufen (kein PHPUnit lokal), Nachweis erst in CI.

## Known Stubs

Keine. Die Container-Seite (POST /probe, GET /probe/state) entsteht in 27-09/27-11; hier gegen Doubles nach dem Vertrag des Plans.

## Threat Flags

Keine neue Fläche außerhalb des Registers: die drei Routen sind T-27-17/T-27-18, der Token-Weg T-27-21, die Feldprüfung T-27-22.

## Self-Check: PASSED

- php/lib/Service/ProbeService.php, php/lib/Controller/ProfileSettingsController.php, php/tests/Unit/ProbeServiceTest.php, php/tests/Unit/ProfileSettingsControllerTest.php, backend/tests/test_probe_php_parity.py vorhanden
- Commits d19be3ba, edee2614, e759e4ce, ce2569a5 im Log
