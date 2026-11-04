---
phase: 42-php-sicherheits-gates
plan: 01
subsystem: PHP-Testinfrastruktur (lokales PHPUnit über Docker)
tags: [php-gates, phpunit, docker, tree-hash, G42-4]
requires: []
provides:
  - scripts/dev/phpunit_docker.sh (lokales PHPUnit-Rezept, liest SERVER_VERSION und MINIMUM_TESTS aus php.yml)
  - JUnit-Datei <SERVER_DIR>/findling-junit.xml für spätere Gates (42-02 Schritt 3a)
affects:
  - 42-02 (Routen-Gate lokal grün vor Commit)
  - 42-03 (Schlussprüfung der Phase)
tech-stack:
  added: []
  patterns:
    - "Werte aus dem Workflow lesen statt duplizieren (sed mit Anker, ohne Pipe)"
    - "Spiegel php/ -> apps/findling bei jedem Lauf frisch, vendor bleibt, Stempel über composer.lock"
key-files:
  created:
    - scripts/dev/phpunit_docker.sh
  modified:
    - docs/testing.md
    - .github/workflows/php.yml
    - php/tests/bootstrap.php
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Server-Checkout mit core.autocrlf=false geklont (nur Linux-PHP liest ihn)"
  - "occ maintenance:install läuft als root im Container; auf dem Bind-Mount gehört config/ ebenfalls root, keine Sonderlösung nötig"
metrics:
  completed: 2026-11-04
  tasks: 2
  files: 5
---

# Phase 42 Plan 01: Lokales PHPUnit über Docker Summary

PHPUnit-Suite der Companion-App läuft lokal per `scripts/dev/phpunit_docker.sh` in nextcloud:32.0.15-apache (PHP 8.3) gegen einen stable34-Checkout, mit derselben Mindestanzahl wie der CI-Job; "CI only" ist aus Doku, Workflow-Kommentar und Bootstrap-Meldung verschwunden.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1+2 | 80d819f3 | test(42-01): run the PHPUnit suite locally through docker |

Mitgepusht: der lokale Docs-Commit 2b7d4962 (Wortlaut 42-02 Schritt 3a).

## Lokale Belege

- Lauf 1 (Clone, Install, composer install): `OK (958 tests, 5851 assertions)`, `phpunit_docker: 958 tests executed, floor 28`, rc 0, PHP 8.3.35.
- Lauf 2 direkt danach (nach Änderung von bootstrap.php): ohne Clone, ohne Install, ohne composer install; nur `dump-autoload`; `OK (958 tests, 5851 assertions)`, rc 0. Idempotent.
- Lauf 3 `--filter BootstrapTest`: `OK (3 tests, 10 assertions)`, "arguments given, the floor check is skipped for this filtered run", rc 0.
- shellcheck (koalaman/shellcheck:stable): erst 2x SC1007 (`CDPATH= cd`), auf `CDPATH=''` korrigiert, danach ohne Befund.
- `git ls-files -s scripts/dev/phpunit_docker.sh`: 100755, LF.
- `grep -n "SERVER_VERSION:\|MINIMUM_TESTS:" php.yml`: genau die zwei env-Zeilen (232, 248).
- `php -l` bootstrap.php in php:8.2-cli: No syntax errors.
- PHP-Baumhash 54627d39... -> e7289079... (113 Dateien), Rezept 40b-baumhash.py und find/sort/tr/sha256sum gleich; `-k php_half` 2 passed.
- pytest test_workflow_pins/tag_triggers/size/public_artifacts: 98 passed. Alle Tests mit `"php"` (33 Dateien): 2277 passed, 243 skipped.
- Sechs Python-Gates grün (ruff, ruff format, ruff scripts, ruff format scripts, pyright 0 errors, vulture).

## CI-Beleg (Kopf 80d819f3)

- PHP and store metadata gates 41897060856 success, CI-Zeile `OK (958 tests, 5851 assertions)`, "the suite executed 958 tests, the floor is 28".
- Python gates 41897061088 success; Security scans 41897060798, Multi-arch image 41897060603, OpenSSF Scorecard 41897060552, Resilience 41897060575, Integration 41897060153 success; HaRP deploy 41897060193 (Ergebnis siehe 42-03-SUMMARY, head_green-Lauf).

## Deviations from Plan

None - plan executed exactly as written. Kleinigkeit: shellcheck-Befund SC1007 im eigenen Skript sofort behoben (vor Commit).

## Known Stubs

Keine.

## Self-Check: PASSED

- scripts/dev/phpunit_docker.sh vorhanden, Commit 80d819f3 vorhanden.
