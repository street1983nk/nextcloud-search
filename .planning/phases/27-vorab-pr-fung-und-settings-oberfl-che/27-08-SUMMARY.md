---
phase: 27-vorab-pr-fung-und-settings-oberfl-che
plan: 08
subsystem: php-companion
tags: [php, admin-view, probe, profile, security]
requires: [27-04]
provides:
  - AdminViewService Overview-Schlüssel guardConfirmable, profileStored, profileChosen, profileSuggested, profileEffective, hardwareCores, hardwareMemory, storedPrecision, probeSupported, probeRunning, probeStep, profileCheck, profileEnv, reindexDocuments, reindexSecondsInt8, reindexSecondsFp32, fp32DownloadBytes
  - AdminViewService statisch public profileField, probeField, stepCode, nonNegativeInt, judgedCheck, checkRate, reindexSeconds, profileEnv, hardwareCores, hardwareMemory
  - AdminViewService::FP32_DOWNLOAD_BYTES
affects: [27-10, 27-12]
tech-stack:
  added: []
  patterns: [Richter je Feld aus geschlossenen Mengen, Paritätstest PHP-Konstante gegen Python-Menge]
key-files:
  created: []
  modified:
    - php/lib/Service/AdminViewService.php
    - php/tests/Unit/AdminViewServiceTest.php
    - backend/tests/test_admin_ui_contract.py
decisions:
  - "guardConfirmable steht in backend() neben den übrigen Wächterfeldern, alle anderen neuen Schlüssel auf oberster Ebene der Overview"
  - "hardwareCores aus coresWhole, hardwareMemory = min(memoryLimitBytes, memoryTotalBytes), dieselbe Größe wie threshold_memory_bytes des Vorschlags"
  - "reindexSeconds rundet auf (intdiv), Rate in Tausendstel Chunk pro Sekunde; ohne Rate > 0 null"
  - "Gespeichertes profile_check: ungültiges Profil, Präzision oder Verdikt verwirft das Ganze; fremde Ursache wird '', fremde Zahlen fallen weg, Flags nur als echte Booleans"
  - "Zusätzlich zu PROBE_STEPS auch PROBE_VERDICTS, PROBE_CAUSES, PROBE_NUMBERS in AdminViewService, mit Paritätstest gegen probe.py"
metrics:
  duration: ca. 30 min
  completed: 2026-09-29
  tasks: 2
  files: 3
---

# Phase 27 Plan 08: Datenseite der Profilfläche in AdminViewService Summary

Der Bestätigungs-Token verlässt den Server nicht mehr (guardConfirmable als bool statt guardToken); die Overview liefert Profil, Hardware, Probe-Stand, Env-Überstimmungen mit Variablennamen aus einer PHP-Map, das erneut geprüfte letzte Verdikt samt atText und eine Reindex-Schätzung nur aus gemessener Rate.

## Erledigt

| Task | Inhalt | Commits |
|------|--------|---------|
| 1 | backend(): guardConfirmable statt guardToken (D-27-12). Neue Konstanten PROBE_STEPS/VERDICTS/CAUSES/NUMBERS, ENV_VARIABLES, ENV_WIRE_KEYS, FP32_DOWNLOAD_BYTES. overview(): 17 neue Schlüssel, profileCheck über judgedCheck + IDateTimeFormatter (neu injiziert). PHPUnit-Fälle je Behavior-Punkt, Wächter-Helfer auf guardConfirmable umgestellt | b591f5dd (test), 96e38b10 (feat) |
| 2 | Wächter-Gate auf guardConfirmable (mit `!== null`-Endung); neue Tests test_the_token_never_reaches_the_browser, test_every_profile_key_of_the_overview_has_one_line, test_the_env_variables_are_the_variables_of_the_profile, test_the_fp32_download_size_is_the_release_size, test_the_view_knows_the_probe_steps | c61b0472 |

## Verifikation

- `php -l` (php:8.3-cli in Docker) für AdminViewService.php und AdminViewServiceTest.php: keine Syntaxfehler
- Wegwerf-Smoke in Docker (Mini-TestCase-Shim, danach gelöscht): 70 von 71 Testfällen grün, der eine Ausfall ist nur eine fehlende Shim-Methode (assertLessThanOrEqual) in einem Bestandstest
- Acceptance-Greps: `'guardToken'` 0, `'guardConfirmable' => ` 1, jeder der 17 Schlüssel genau einmal, FINDLING_*-Namen 5 Treffer
- `uv run pytest -q tests/test_admin_ui_contract.py`: 64 passed; ruff check, ruff format --check, pyright (latest) 0 Fehler, vulture sauber
- PHPUnit: lokal nicht ausführbar, läuft in CI (php.yml) nach Push
- `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_php_half` rot wie erwartet (PHP-Baum geändert); Pin bewusst nicht angefasst, der Orchestrator misst nach dem Merge

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Sicherheit] Weitere Probe-Mengen in AdminViewService**
- **Found during:** Task 1
- **Issue:** Das erneute Prüfen von profile_check (T-27-25) braucht Verdikt-, Ursachen- und Zahlenmengen, der Plan nannte nur PROBE_STEPS
- **Fix:** PROBE_VERDICTS, PROBE_CAUSES, PROBE_NUMBERS als Einzeilen-Konstanten, Parität in test_the_view_knows_the_probe_steps mitgeprüft
- **Commits:** 96e38b10, c61b0472

**2. [Rule 2] Zusätzlicher Test für die Env-Map**
- test_the_env_variables_are_the_variables_of_the_profile prüft, dass die Wire-Schlüssel der Map in PROFILE_VALUE_KEYS der Statusroute stehen (c61b0472)

Hinweis: Das Template (php/templates/admin.php Zeilen 283-290) liest noch `$backend['guardToken']`; ohne den Schlüssel bleibt die alte occ-Zeile verborgen. Der Umbau gehört laut Plan zu 27-10.

## TDD Gate Compliance

test-Commit b591f5dd liegt vor feat-Commit 96e38b10. Ein echter RED-Lauf mit PHPUnit war lokal nicht möglich, Nachweis erst in CI.

## Known Stubs

Keine. model.chunks und der Block probe kommen erst mit 27-11; bis dahin liefern sie defensiv 0 bzw. probeSupported false (so vorgesehen, Z15).

## Self-Check: PASSED

- php/lib/Service/AdminViewService.php, php/tests/Unit/AdminViewServiceTest.php, backend/tests/test_admin_ui_contract.py geändert
- Commits b591f5dd, 96e38b10, c61b0472 im Log
