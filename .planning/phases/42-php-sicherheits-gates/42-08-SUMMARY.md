---
phase: 42-php-sicherheits-gates
plan: 08
subsystem: PHP-Testsuite (App-Flächen ohne Controller-Route)
tags: [php-gates, routes-file, tokens, registrations, bootstrap, gap-closure, G42-1]
requires:
  - 42-07 (Controller final, Klassen-Pins)
provides:
  - php/tests/RouteSecurity/AppSurface.php (routesFileFindings, sourceFindings, register/boot, describeCall, compareRegistrations, loadRegistrations)
  - php/tests/app-surface.json (16 Registrierungen, von Hand)
  - fünf Tests, Untergrenzen 39, Strukturgate kennt app-surface.json
affects:
  - 42-09 (Textseite derselben Sperren in Python)
tech-stack:
  added: []
  patterns:
    - "Token-Whitelist statt Textsuche für routes.php"
    - "aufzeichnender Stub aus der Methodenliste des Interfaces im Checkout"
key-files:
  created:
    - php/tests/RouteSecurity/AppSurface.php
    - php/tests/app-surface.json
  modified:
    - php/tests/Unit/RouteSecurityTest.php
    - .github/workflows/php.yml
    - backend/tests/test_php_route_gate_presence.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Aufzeichnung über createStub (nicht createMock), damit PHPUnit 11 keine Hinweise zu Mocks ohne Erwartung ausgibt; Rückgabewerte nach Rückgabetyp (void/nullable null, Klasse als Stub, Skalare leer)"
  - "PHPUnit reicht dem Stub jeden deklarierten Parameter weiter, auch Vorgabewerte; app-surface.json führt registerEventListener deshalb mit Priorität 0 (pinnt die Priorität mit)"
  - "routesFileFindings meldet Einzelzeichen als 'char <c> at line N'"
metrics:
  completed: 2026-11-05
  tasks: 2
  files: 6
---

# Phase 42 Plan 08: routes.php-Tokens und App-Registrierungen Summary

appinfo/routes.php darf nur noch literale Tokens enthalten (kein $this, kein Aufruf, kein include/require/eval), kein Quelltext unter php/lib nennt Router- oder Container-Zugriffe (Tokenprüfung), und Application::register zeichnet an einem Stub des Server-Interfaces exakt die 16 von Hand gelisteten Registrierungen aus php/tests/app-surface.json auf, boot() nichts.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1+2 | 4798b5dc | test(42-08): pin the routes file tokens and the app registrations |

## Belege

- RED (Tests zuerst, ohne AppSurface): `Tests: 39, Assertions: 102, Errors: 5.`, rc 2; rot genau die fünf neuen Tests (Klasse AppSurface fehlt).
- GREEN: `OK (39 tests, 189 assertions)` rc 0 beim ersten Lauf; die von Hand aus Application.php geschriebene Liste (2 registerSearchProvider, 8 + 3 + 2 registerEventListener aus den drei Schleifen, 1 für BeforeTemplateRenderedEvent) stimmte mit der Aufzeichnung überein. Volle Suite `OK (997 tests, 6040 assertions)`, `997 tests executed, floor 28`, rc 0; `git diff --exit-code php/lib php/appinfo` Exit 0.
- `php -l` (php:8.2-cli) über AppSurface.php und RouteSecurityTest.php: No syntax errors.
- Rot-Beweise am echten Baum (Python-Ersetzung, `--filter RouteSecurity` rc 1, Rücknahme mit `git checkout -- php/lib php/appinfo`, `git status --porcelain php/lib php/appinfo` leer):
  - (a) in php/appinfo/routes.php vor dem return `if ($this instanceof \OC\Route\Router) { $this->create('findling_x', '/apps/findling/x'); }`: nur testAppinfoRoutesUsesOnlyLiteralTokens rot (`Failures: 1`) mit `T_IF if at line 11`, `T_VARIABLE $this at line 11`, `T_INSTANCEOF ...`, `T_NAME_FULLY_QUALIFIED \OC\Route\Router at line 11`, `T_OBJECT_OPERATOR -> ...`, `T_STRING create at line 11`; der alte testAppinfoRoutesDeclaresNoRoute blieb grün, genau die Lücke.
  - (b) `$context->registerCapability(\OCA\Findling\Search\Provider::class);` in register(): `unlisted registration registerCapability(OCA\Findling\Search\Provider)`.
  - (c) `use OCP\Route\IRouter;` in php/lib/Service/SettingsService.php: `lib/Service/SettingsService.php:8: OCP\Route\IRouter`.
  - Danach grüner Filterlauf `OK (39 tests, 189 assertions)`.
- JUnit-Schritt lokal: `the route attribute gate ran 39 tests, the floor is 39`, Exit 0.
- Baumhash 04f4443d... -> 2efff5b9... (118 Dateien), beide Wege gleich; `-k php_half` 2 passed.
- Python-Gates grün; pytest seriell: route_gate_presence 30, trust_boundary 21, workflow_pins 14, workflow_tag_triggers 27, measurement `-k php_half` 2.

## CI-Beleg

`scripts/ci/head_green.sh "$(git rev-parse HEAD)" "PHP and store metadata gates" "Python gates"` auf 4798b5dc6ee8...: rc 0, acht Läufe success:
PHP and store metadata gates 41953527552 (`OK (997 tests, 6040 assertions)`, "the suite executed 997 tests, the floor is 28", "the route attribute gate ran 39 tests, the floor is 39"), Python gates 41953527559, Security scans 41953527487, Resilience 41953527519, Integration 41953527653, HaRP deploy 41953527547, Multi-arch image 41953527598, OpenSSF Scorecard 41953527576.

## Deviations from Plan

1. [Hinweis] app-surface.json enthält bei registerEventListener die Vorgabe-Priorität 0, weil PHPUnit dem Stub alle deklarierten Parameter übergibt (doubled_method.tpl baut die Argumentliste aus der Signatur); das pinnt die Priorität zusätzlich.
2. [Rule 2, verschärft] Strukturgate: neben dem verlangten Test eine eigene Probenfunktion für leere Liste, fehlenden Schlüssel, Nicht-String und ungültiges JSON; sourceFindings-Test prüft zusätzlich, dass Kommentar, String und `$this->container` nichts melden.

## Known Stubs

Keine.

## Self-Check: PASSED

- php/tests/RouteSecurity/AppSurface.php und php/tests/app-surface.json vorhanden, Commit 4798b5dc vorhanden, CI-Kopf grün.
