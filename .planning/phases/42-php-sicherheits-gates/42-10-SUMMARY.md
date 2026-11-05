---
phase: 42-php-sicherheits-gates
plan: 10
subsystem: PHP- und Python-Gates (Router- und Containersperre, Groß-/Kleinschreibung)
tags: [phpunit, python-gates, text-bans, gap-closure, re-verification]
requires:
  - 42-08 (AppSurface::sourceFindings)
  - 42-09 (test_php_surface_bans.py, LIB_BANS)
provides:
  - Router- und Containersperre unabhängig von Groß-/Kleinschreibung, in PHPUnit und in Python
  - python.yml startet auch auf php/**
affects:
  - Phasenverifikation 42 (Lücke der Vektoren 3 und 6)
key-files:
  created: []
  modified:
    - php/tests/RouteSecurity/AppSurface.php
    - php/tests/Unit/RouteSecurityTest.php
    - backend/tests/test_php_surface_bans.py
    - backend/tests/test_php_route_gate_presence.py
    - backend/tests/test_measurement_scripts.py
    - backend/tests/test_workflow_tag_triggers.py
    - .github/workflows/php.yml
    - .github/workflows/python.yml
decisions:
  - "Lückenschluss ohne eigenen PLAN.md, auf Owner-Auftrag als kleine Lückennotiz"
  - "Eine neue PHPUnit-Testmethode, deshalb ROUTE_GATE_MIN_TESTS und MIN_FLOOR im Gleichschritt auf 40"
  - "python.yml: php/l10n/** auf php/** erweitert, weil die Textsperren die ganze PHP-Hälfte lesen; PATHS_BEFORE in test_workflow_tag_triggers.py zieht mit"
metrics:
  completed: 2026-11-05
  tasks: 1
  files: 8
---

# Phase 42 Plan 10: Lückenschluss Groß-/Kleinschreibung der Router- und Containersperre

Beide Sperren vergleichen die verbotenen Namen jetzt ohne Rücksicht auf Groß-/Kleinschreibung, so wie PHP Klassen-, Funktions- und Methodennamen auflöst. Meldungen bleiben unverändert: PHPUnit nennt den Namen wie geschrieben, Python den Bann in kanonischer Schreibweise.

## Lücke (aus 42-VERIFICATION.md)

`use OCP\Route\irouter;`, `->actioninclude(`, `->getrouter()` und `$this->getcontainer()->registerservice(...)` im Konstruktor von Application ließen PHPUnit (39 Tests) und pytest (86) grün.

## Änderungen

- `AppSurface::sourceFindings`: `strtolower($last)` gegen die kleingeschriebene BANNED_NAMES-Liste.
- `test_php_surface_bans.py`: `ban.lower() in line.lower()` für alle LIB_BANS; die Sonderbehandlung von `OC\Route\` entfällt, weil sie jetzt die Regel ist.
- Negativproben: PHPUnit `testABannedNameInAnyCaseIsReported` (irouter-use, actioninclude, getrouter, IROUTER, REGISTERMIDDLEWARE, registerservicealias, RegisterParameter, getcontainer()->registerservice, plus Kommentar/String/registerservices ohne Befund); Python `test_a_lib_ban_in_any_case_is_reported` (9 Fälle).
- Untergrenzen 39 auf 40: `ROUTE_GATE_MIN_TESTS` in php.yml, `MIN_FLOOR` in test_php_route_gate_presence.py.
- PHP-Baumhash eb5b2dc1 (118 Dateien), zweimal unabhängig mit find, sort, tr und sha256sum nachgerechnet.
- python.yml: `php/**` statt `php/l10n/**` in push und pull_request.

## Rotbeleg am echten Baum

- (a) neue Datei `php/lib/Service/RedRouterProbe.php` mit `use OCP\Route\irouter;`, `->actioninclude(`, `->getrouter()`: PHPUnit `Tests: 40, Failures: 1` mit `lib/Service/RedRouterProbe.php:7: OCP\Route\irouter`, `:10: irouter`, `:11: actioninclude`, `:12: getrouter`; pytest 1 failed (`php/lib/Service/RedRouterProbe.php:7: IRouter`, 4 Befunde).
- (b) `$this->getcontainer()->registerservice(PageController::class, fn () => null);` im Konstruktor von Application: PHPUnit `Tests: 40, Failures: 1` mit `lib/AppInfo/Application.php:31: getcontainer` und `:31: registerservice`; pytest 1 failed (2 Befunde, `registerService(` und `getContainer(`).
- Beide Proben zurückgenommen, `git status` sauber, danach grün.

## Verifikation

- PHPUnit voll über `scripts/dev/phpunit_docker.sh`: `OK (998 tests, 6049 assertions)`, RouteSecurityTest 40 Tests, rc 0.
- pytest (test_php_surface_bans, test_php_route_gate_presence, test_workflow_tag_triggers, test_measurement_scripts, test_exapp_surface): 724 passed; ruff, ruff format, pyright, vulture grün.

## Deviations from Plan

Kein PLAN.md, Lückenschluss auf direkten Auftrag. Zusätzlich zum Auftrag mitgezogen, weil sonst rot: PHP-Baumhash in test_measurement_scripts.py und PATHS_BEFORE in test_workflow_tag_triggers.py.
