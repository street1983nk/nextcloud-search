---
phase: 42-php-sicherheits-gates
plan: 03
subsystem: CI-Lieferkette der PHP-Hälfte (composer, Dependabot)
tags: [php-gates, composer-audit, composer-validate, dependabot, schedule, G42-2, G42-4]
requires:
  - 42-02 (Routen-Gate, Testanzahl 973)
provides:
  - php.yml Job composer-hygiene (composer validate --strict --no-check-publish, composer audit --locked --no-interaction)
  - php.yml schedule Montag 05:50 UTC, concurrency php-${{ github.event_name }}-${{ github.ref }}
  - dependabot.yml Eintrag composer /php, wöchentlich, phpunit/phpunit semver-major ignoriert
  - backend/tests/test_php_supply_chain_gates.py (16 Tests)
affects:
  - spätere Phase vor 1.7 (Psalm/Taint, php-cs-fixer, zizmor, actionlint)
tech-stack:
  added: []
  patterns:
    - "audit --locked ohne install: kein Paketcode im Job"
    - "Strukturgate erkennt Entschärfung (|| true, continue-on-error) an Schritt und Job"
key-files:
  created:
    - backend/tests/test_php_supply_chain_gates.py
  modified:
    - .github/workflows/php.yml
    - .github/dependabot.yml
    - docs/testing.md
decisions:
  - "composer-hygiene steht zwischen app-metadata und phpunit, checkout mit persist-credentials: false"
  - "Strukturgate prüft zusätzlich weekly und den phpunit-Major-Ausschluss im Dependabot-Eintrag (verschärft, nicht abgeschwächt)"
metrics:
  completed: 2026-11-04
  tasks: 2
  files: 4
---

# Phase 42 Plan 03: Composer-Lieferkette als Gate Summary

composer validate --strict und composer audit --locked laufen als Job composer-hygiene in php.yml (bei php/** und wöchentlich), Dependabot pflegt composer unter /php ohne PHPUnit-Majors, ein Python-Strukturgate verhindert stilles Entfernen oder Entschärfen; alle Gates der Phase lokal und im CI grün.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1+2 | a0cb12c5 | ci(42-03): validate and audit the composer lock of the companion app |

## Belege

- RED (Strukturgate gegen den Baum vor der Änderung): 2 failed, 14 passed; Befunde: "php.yml has no schedule with a cron entry", "the concurrency group of php.yml does not contain github.event_name", "no step of php.yml runs 'composer validate --strict' with working-directory: php", "no step of php.yml runs 'composer audit --locked' with working-directory: php", "dependabot.yml has no entry for the composer ecosystem".
- GREEN: test_php_supply_chain_gates, workflow_pins, workflow_tag_triggers, workflow_size: 59 passed (tag_triggers vor dem Edit grün im 42-02-Lauf, danach grün).
- cron-Zeiten vor dem Schreiben gelesen: docker 17 4 1 * *, python 17 4 * * 1, resilience 31 4 * * 1, security 30 5 * * 1, scorecard 45 5 * * 1; neu php 50 5 * * 1, kein Doppel.
- actionlint lokal nicht vorhanden (nur Information, kein Gate).
- Composer grün lokal (composer:2, Composer 2.10.3), exakt die CI-Befehle: `./composer.json is valid`, `No security vulnerability advisories found.`, Exit 0.
- Rot (a), Wegwerf-Verzeichnis mit `guzzlehttp/guzzle` 7.4.0: `composer audit --locked` mit `Found 14 security vulnerability advisories affecting 1 package`, darunter CVE-2022-29248 (PKSA-6d8m-6kgw-18zr), Exit 1.
- Rot (b), Kopie von composer.json/lock mit phpunit 11.5.55 in composer.json: `./composer.json is valid but your composer.lock has some errors ... "phpunit/phpunit" is in the lock file as "11.5.56" but that does not satisfy your constraint "11.5.55"`, Exit 2. Beide Wegwerf-Verzeichnisse danach gelöscht.
- Schlussprüfung der Phase lokal, seriell:
  - `bash scripts/dev/phpunit_docker.sh`: `OK (973 tests, 5887 assertions)`, `973 tests executed, floor 28`, rc 0.
  - `php -l` über php/lib php/appinfo php/templates php/tests in php:8.2-cli: 116 Dateien, 0 Fehler, rc 0.
  - Sechs Python-Gates grün (pyright erst 2 Fehler im neuen Test, `dict.get(True)` auf `dict[str, Any]`, auf `dict[Any, Any]` korrigiert; ruff E501 einmal umgebrochen; beides vor dem Commit).
  - `-k php_half`: 2 passed; Satz supply_chain, trust_boundary, route_gate_presence, workflow_pins/tag_triggers/size, public_artifacts: 156 passed; alle Tests mit `"php"`: 2314 passed, 243 skipped.
  - `git diff --stat 2b7d4962..HEAD -- php/lib php/appinfo php/templates php/js php/css php/l10n backend/src backend/appinfo`: leer. Kein Versions-Diff (info.xml, CHANGELOG), kein Tag.
- Dependabot-Annahme: nach dem Push vier Läufe "Dependabot Updates", alle success, darunter "composer in /php - Update #1681515205" (41910010415). Dependabot öffnete daraufhin PR #46 (phpunit/phpunit 11.5.56 auf 11.5.57, Gruppe php-minor-and-patch) sowie PR #47 und #48 aus dem bestehenden uv-Eintrag; keine PR gemergt, keine Repo-Einstellung geändert.

## CI-Beleg (Kopf a0cb12c5)

`scripts/ci/head_green.sh a0cb12c5... "PHP and store metadata gates" "Python gates"`: rc 0, zwölf Läufe success:
PHP and store metadata gates 41909998607 (Jobs php -l, info.xml, composer validate and audit, PHPUnit alle success; `./composer.json is valid`, `No security vulnerability advisories found.`, `OK (973 tests, 5887 assertions)`, "the route attribute gate ran 15 tests, the floor is 15"), Python gates 41909998535, Security scans 41909998853, Resilience 41909998754, OpenSSF Scorecard 41909998551, Integration 41909998637, Multi-arch image 41909998653, HaRP deploy 41909998673, Dependabot Updates 41910010415, 41910010567, 41910011173, 41910011569.

Hinweis: setup-php setzt im Job `COMPOSER_NO_AUDIT: 1`; das schaltet nur das automatische Audit nach install/update ab, der ausdrückliche Befehl `composer audit` läuft (Ausgabe oben belegt).

## Deviations from Plan

1. [Hinweis] Rot-Probe (a): Composer 2.10.3 verweigert schon beim `composer update` Pakete mit Advisories (`policy.advisories.block`, "these were not loaded, because they are affected by security advisories"). Für die Wegwerf-Probe daher `"config": {"audit": {"block-insecure": false}}` im Wegwerf-composer.json gesetzt, danach Lock erzeugt und `composer audit --locked` rot belegt. Nur im Scratchpad, nichts im Repo; das Gate selbst ist unverändert.
2. [Rule 2] Strukturgate etwas strenger als die behavior-Liste: prüft zusätzlich weekly und den semver-major-Ausschluss für phpunit/phpunit im Dependabot-Eintrag sowie "beide Befehle im selben Job" (deckt die must_haves-Wahrheit zum phpunit-Ausschluss ab).
3. Kopfkommentar von dependabot.yml von "three" auf "four dependency surfaces" korrigiert (sonst falsch).

## Known Stubs

Keine.

## Self-Check: PASSED

- backend/tests/test_php_supply_chain_gates.py vorhanden, Commit a0cb12c5 vorhanden.
