---
phase: 42-php-sicherheits-gates
plan: 06
subsystem: PHP-Testsuite (Routen-Attribut-Gate)
tags: [php-gates, route-security, oracle-rules, class-attributes, gap-closure, G42-1]
requires:
  - 42-05 (kanonische Attributnamen, R6)
provides:
  - R1 und R2 auf dem Orakel (Profilfeld effective), R1 nur mit exaktem AnonRateLimit an der Methode
  - R4 (Klassenattribute verboten, zählen für nichts)
  - R7 (defaults, root, postfix verboten, Ausnahmen nur über die leere Konstante ALLOWED_ROUTE_EXTRAS)
  - R8 (Verbotsliste lockernder Attribute, PublicPage mit ExAppRequired)
  - Profilfelder verb und extras aus Route::toArray()
  - docs/testing.md Absatz zum Gate mit allen Regeln
affects:
  - 42-07 (classViolations erweitert um C1)
tech-stack:
  added: []
  patterns:
    - "Regeln bewerten, was der Server tut (effective), nicht die Attributliste"
key-files:
  created: []
  modified:
    - php/tests/RouteSecurity/RouteProfiles.php
    - php/tests/RouteSecurity/Fixtures.php
    - php/tests/Unit/RouteSecurityTest.php
    - .github/workflows/php.yml
    - backend/tests/test_php_route_gate_presence.py
    - backend/tests/test_measurement_scripts.py
    - docs/testing.md
decisions:
  - "R4 meldet jedes Klassenattribut, auch ein Routenattribut an der Klasse (readAttributes führt Routenattribute dafür in einer eigenen Liste routes)"
  - "ExtrasFixture::positional setzt positional nur root (übrige Argumente null); R7 je gesetztem Argument"
  - "ALLOWED_ROUTE_EXTRAS wird über den Schlüssel ohne #n-Suffix nachgeschlagen"
metrics:
  completed: 2026-11-05
  tasks: 2
  files: 7
---

# Phase 42 Plan 06: Regeln auf dem Server-Orakel Summary

Klassenattribute zählen für keine Route mehr und sind selbst rot (R4); R1 und R2 lesen die wirksamen Marker des Server-Reflectors, R1 verlangt ein exaktes AnonRateLimit an der Methode; root, postfix und defaults (R7) sowie lockernde Attribute und PublicPage mit ExAppRequired (R8) sind rot; docs/testing.md beschreibt das ganze Regelwerk.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1+2 | 587c758c | test(42-06): route gate rules read the server oracle and forbid class attributes |

## Belege

- RED (`--filter RouteSecurity`, Leser aus 42-05): `Tests: 29, Assertions: 67, Failures: 15.`, rc 1. Rot: die vier neuen Tests, die zwei umbenannten (testAClassAttributeIsAViolationAndCountsForNothing, testPublicPageNeedsAnAnonRateLimit), die vier Tests aus 42-04/42-05 mit geänderten exakten Listen (Annotation, Inherited, Lowercase, RateLimitSubclass) und fünf Allowlist-Tests (testAnExactAllowlistReportsNothing, testARouteWithoutAnAllowlistEntryIsReported, testAnAddedAttributeIsAChange, testAnAllowlistEntryWithoutAMethodIsStale, testTheArgumentsOfARateLimitArePartOfTheProfile), weil die Fixture-Allowlist für ClassLevelFixture schon den Zielstand `attributes []` trägt, den der alte Leser noch nicht lieferte.
- GREEN: `OK (29 tests, 79 assertions)` rc 0; volle Suite `OK (987 tests, 5930 assertions)`, `987 tests executed, floor 28`, rc 0; `git diff --exit-code php/lib` Exit 0. Echte Profile und route-security.json unverändert.
- `php -l` (php:8.2-cli) über RouteProfiles.php, Fixtures.php, RouteSecurityTest.php: No syntax errors.
- Rot-Beweise am echten Baum (Python-Ersetzung, `--filter RouteSecurity` rc 1, Rücknahme laut gemeinsamen Vorgaben, `ROLLBACK-CLEAN` je Beweis):
  - `#[\OCP\AppFramework\Http\Attribute\NoAdminRequired]` an der Klasse SettingsController: `R4 SettingsController: class attribute NoAdminRequired has no effect on routes` (allein, kein changed route mehr, weil Klassenattribute nicht ins Profil gehen).
  - `root: '/cloud'` an der ApiRoute von QueueController::requeue: `R7 QueueController::requeue: route argument root is not allowed` und `changed route QueueController::requeue: ... actual ApiRoute POST /queues/documents/requeue {"root":"/cloud"} [ExAppRequired, NoCSRFRequired]`.
  - `#[\OCP\AppFramework\Http\Attribute\UseSession]` an setPause: `R8 SettingsController::setPause: UseSession is not allowed in Findling` und `changed route ... [UseSession]`.
  - `#[...\PublicPage]` und `#[...\BruteForceProtection(action: 'red')]` an PageController::index: genau `R1 PageController::index: PublicPage without AnonRateLimit` und `changed route PageController::index: ... actual FrontpageRoute GET / [BruteForceProtection(action="red"), NoAdminRequired, NoCSRFRequired, PublicPage]`.
  - Danach grüner Filterlauf `OK (29 tests, 79 assertions)`.
- JUnit-Schritt lokal (php:8.2-cli, Ausdruck aus php.yml): `the route attribute gate ran 29 tests, the floor is 29`, Exit 0.
- Baumhash a5fd4a1c... -> ca8905b5... (117 Dateien), beide Wege gleich; `-k php_half` 2 passed.
- Python-Gates grün; pytest seriell: route_gate_presence 23, trust_boundary 21, public_artifacts 55, workflow_pins 14, workflow_tag_triggers 27, measurement `-k php_half` 2.

## CI-Beleg

`scripts/ci/head_green.sh 587c758ca7d5... "PHP and store metadata gates" "Python gates"`: rc 0, acht Läufe success:
PHP and store metadata gates 41944202656 (`OK (987 tests, 5930 assertions)`, "the suite executed 987 tests, the floor is 28", "the route attribute gate ran 29 tests, the floor is 29"), Python gates 41944202644, Security scans 41944202646, Resilience 41944202585, Integration 41944202626, HaRP deploy 41944202609, Multi-arch image 41944202636, OpenSSF Scorecard 41944202633.

## Deviations from Plan

1. [Hinweis] Im RED waren zusätzlich fünf Allowlist-Tests rot, weil der Plan die Fixture-Allowlist für ClassLevelFixture schon in Task 1 auf `attributes []` setzt; nach GREEN alle grün, wie verlangt.
2. [Rule 2, verschärft] R4 meldet auch ein Routenattribut an einer Controllerklasse (der Server liest es nicht); testBruteForceProtectionAloneDoesNotSatisfyR1 prüft zusätzlich, dass PublicFixture::limited (exaktes AnonRateLimit) kein R1 meldet.
3. Der Plan nennt in verification "drei Rot-Beweise", in behavior und Task 2 vier; ausgeführt wurden alle vier.

## Known Stubs

Keine.

## Self-Check: PASSED

- Commit 587c758c vorhanden, CI-Kopf grün, docs/testing.md enthält ControllerMethodReflector.
