---
phase: 42-php-sicherheits-gates
plan: 02
subsystem: PHP-Testsuite (Routen-Attribut-Gate)
tags: [php-gates, route-security, reflection, allowlist, junit, tree-hash, G42-1]
requires:
  - 42-01 (scripts/dev/phpunit_docker.sh, JUnit-Datei im Server-Verzeichnis)
provides:
  - php/tests/RouteSecurity/RouteProfiles.php (ofClass, classesIn, ofDirectory, compare, violations, loadAllowlist)
  - php/tests/route-security.json (20 Einträge, von Hand geschrieben)
  - php/tests/Unit/RouteSecurityTest.php (10 Fixture-Fälle, 5 Fälle am echten Baum)
  - php.yml Schritt "The route attribute gate ran" (JUNIT_FILE, ROUTE_GATE_MIN_TESTS 15)
  - backend/tests/test_php_route_gate_presence.py (Strukturgate, 21 Tests)
affects:
  - 42-03 (Schlussprüfung, Testanzahl 973)
tech-stack:
  added: []
  patterns:
    - "Attribute nur über ReflectionAttribute::getName()/getArguments(), nie instanziiert"
    - "Allowlist von Hand, Leser nur zur Gegenprobe"
    - "CI-Ausdruck lokal aus demselben YAML-Schritt extrahiert statt kopiert"
key-files:
  created:
    - php/tests/RouteSecurity/RouteProfiles.php
    - php/tests/RouteSecurity/Fixtures.php
    - php/tests/Unit/RouteSecurityTest.php
    - php/tests/route-security.json
    - backend/tests/test_php_route_gate_presence.py
  modified:
    - .github/workflows/php.yml
    - docs/testing.md
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Profilformat: route = '<Kurzname Routen-Attribut> <VERB> <url>' plus kanonisches JSON weiterer Routen-Argumente; attributes = sortierte Kurznamen, Argumente als Name(key=value, ...)"
  - "Basisklasse Route (Konstruktor mit type an Position 0) wird bei Positionsargumenten um eins verschoben gelesen; ApiRoute/FrontpageRoute beginnen mit verb"
  - "ROUTE_GATE_MIN_TESTS = 15 = Anzahl Testmethoden von RouteSecurityTest"
metrics:
  completed: 2026-11-04
  tasks: 2
  files: 8
---

# Phase 42 Plan 02: Routen-Attribut-Gate Summary

Jede Controller-Route samt Attributen (Methode und Klasse, Ratelimit-Argumente inklusive) ist per Reflection gegen die handgeschriebene Allowlist php/tests/route-security.json festgenagelt; unlisted/changed/stale und die Regeln R1 (PublicPage braucht Ratelimit/BruteForce) und R2 (NoCSRFRequired nur GET oder ExAppRequired) machen PHPUnit rot, ein JUnit-Schritt in php.yml beweist, dass das Gate lief.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1+2 | e0ea3179 | test(42-02): pin every controller route and its attributes to an allowlist |

## Belege

- Basisklasse im Server-Checkout bestätigt: `OCP\AppFramework\Http\Attribute\Route` (Konstruktor type, verb, url, requirements, defaults, root, postfix); ApiRoute/FrontpageRoute erben; ARateLimit(limit, period); BruteForceProtection(action).
- RED (`phpunit_docker.sh --filter RouteSecurity` vor RouteProfiles): `Tests: 10, Assertions: 0, Errors: 10.`, je `Error: Class "OCA\Findling\Tests\RouteSecurity\RouteProfiles" not found`, rc 2.
- GREEN Fixtures: `OK (10 tests, 24 assertions)`; mit echtem Baum: `OK (15 tests, 36 assertions)`.
- Allowlist: 20 Einträge von Hand aus den Quellen; beim ersten Lauf deckungsgleich mit dem Leser, keine Abweichung zu klären.
- Voll lokal: `OK (973 tests, 5887 assertions)`, `phpunit_docker: 973 tests executed, floor 28`, rc 0.
- Manueller Rot-Beweis: `#[\OCP\AppFramework\Http\Attribute\PublicPage]` temporär an SettingsController::setPause; `--filter RouteSecurity` rc 1, `Tests: 15, Assertions: 35, Failures: 3.` mit
  `changed route SettingsController::setPause: expected FrontpageRoute POST /admin/pause [], actual FrontpageRoute POST /admin/pause [PublicPage]` und
  `R1 SettingsController::setPause: PublicPage without AnonRateLimit or BruteForceProtection`; danach `git checkout -- php/lib/Controller/SettingsController.php`, `git diff --exit-code php/lib` Exit 0.
- JUnit-Schritt lokal (Ausdruck und Untergrenze per yaml.safe_load aus php.yml extrahiert, gelesener Wert ROUTE_GATE_MIN_TESTS = 15), Befehl je Lauf:
  `MSYS_NO_PATHCONV=1 docker run --rm -v "C:/Users/Student/.cache/findling-phpunit/server:/srv/server:ro" -v "<scratchpad>:/work:ro" <ENV> php:8.2-cli sh -c 'php -r "$(cat /work/route_gate_expr.txt)"'`
  - Lauf 1, `-e JUNIT_FILE=/srv/server/findling-junit.xml -e ROUTE_GATE_MIN_TESTS=15`: `the route attribute gate ran 15 tests, the floor is 15`, Exit 0.
  - Lauf 2, `-e JUNIT_FILE=/work/findling-junit-skipped.xml -e ROUTE_GATE_MIN_TESTS=15` (skipped="1" am Knoten RouteSecurityTest): `the route attribute gate has 1 skipped, 0 failures and 0 errors`, Exit 1.
  - Lauf 3, nur `-e JUNIT_FILE=/srv/server/findling-junit.xml`: `ROUTE_GATE_MIN_TESTS is missing or not a positive integer`, Exit 1.
- `php -l` (php:8.2-cli) über die drei neuen Dateien: No syntax errors.
- PHP-Baumhash e7289079... -> 06a082a0... (116 Dateien), Rezept und find/sort/tr/sha256sum gleich; `-k php_half` 2 passed.
- pytest trust_boundary, route_gate_presence, public_artifacts, workflow_pins/tag_triggers/size: 140 passed. Alle Tests mit `"php"`: 2298 passed, 243 skipped.
- Sechs Python-Gates grün.
- `git diff HEAD~2 --stat -- php/lib php/appinfo`: leer.

## CI-Beleg (Kopf e0ea3179)

`scripts/ci/head_green.sh e0ea3179... "PHP and store metadata gates" "Python gates"`: rc 0, acht Läufe success:
PHP and store metadata gates 41905206023 (`OK (973 tests, 5887 assertions)`, "the suite executed 973 tests, the floor is 28", "the route attribute gate ran 15 tests, the floor is 15"), Python gates 41905206010, Security scans 41905205943, HaRP deploy 41905205829, Resilience 41905205817, OpenSSF Scorecard 41905205848, Integration 41905205768, Multi-arch image 41905205765.

## Deviations from Plan

1. [Rule 3 - Blocking] Docker Desktop stürzte während der Gates ab (Backend Exit 1 um 19:40:13Z, Engine antwortete 30 min nicht, auch nach `docker desktop restart`). Behoben durch Beenden von Docker Desktop, `wsl --shutdown` und Neustart. Der php-Baum-pytest-Satz lief zunächst mit Docker aus (2270 passed, 271 skipped) und wurde nach dem Neustart wiederholt (2298 passed, 243 skipped = Basis). Keine Gate-Änderung.
2. [Hinweis, keine Änderung] composer dump-autoload meldet für tests/RouteSecurity/Fixtures.php "does not comply with psr-4 autoloading standard. Skipping." (je Fixture-Klasse). Vom Plan so vorgesehen (Fixtures per require_once, mehrere Klassen in einer Datei); Exit 0, kein Einfluss auf den Lauf.
3. [Hinweis] Der erste Versuch des Rot-Beweises per sed/perl traf die Zeile nicht (Quoting der Backslashes), der Lauf blieb grün und wurde nicht gewertet; der gewertete Beweis lief per Python-Ersetzung.

## Known Stubs

Keine.

## Self-Check: PASSED

- Fünf neue Dateien vorhanden, Commit e0ea3179 vorhanden.
