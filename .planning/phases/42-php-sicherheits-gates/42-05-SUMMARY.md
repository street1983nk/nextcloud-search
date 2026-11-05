---
phase: 42-php-sicherheits-gates
plan: 05
subsystem: PHP-Testsuite (Routen-Attribut-Gate)
tags: [php-gates, route-security, canonicalisation, foreign-attributes, gap-closure, G42-1]
requires:
  - 42-04 (Orakel, Profilfelder, Gleichschritt der Untergrenzen)
provides:
  - Kanonische Attributnamen (Tabelle der OCP-Attributklassen aus dem Checkout, sonst ReflectionClass::getName)
  - Regel R6 (fremdes Attribut, nicht ladbares Attribut); harmlose PHP-Attribute Override, ReturnTypeWillChange, Deprecated
  - Profilfelder foreign und unknown
affects:
  - 42-06 (R1/R2 auf effective, R1-Text ändert sich)
tech-stack:
  added: []
  patterns:
    - "Attributname nie aus der Quelltext-Schreibweise, immer kanonisch"
key-files:
  created: []
  modified:
    - php/tests/RouteSecurity/RouteProfiles.php
    - php/tests/RouteSecurity/Fixtures.php
    - php/tests/Unit/RouteSecurityTest.php
    - .github/workflows/php.yml
    - backend/tests/test_php_route_gate_presence.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Ein fremdes Attribut steht mit vollem kanonischen Namen in der Attributliste (sichtbar als changed route) und zusätzlich in foreign (R6)"
  - "Ein nicht ladbares Attribut steht mit Rohnamen in der Attributliste und in unknown (R6)"
metrics:
  completed: 2026-11-05
  tasks: 2
  files: 6
---

# Phase 42 Plan 05: Kanonische Attributnamen und fremde Attribute Summary

Jedes Attribut einer Routenmethode wird über seinen kanonischen Klassennamen gelesen, sodass klein geschriebene Namespaces oder Kurznamen als PublicPage erscheinen; jedes Attribut außerhalb von OCP\AppFramework\Http\Attribute (auch eine Unterklasse von AnonRateLimit) und jedes nicht ladbare Attribut ist R6.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1+2 | c26beb3a | test(42-05): route gate canonicalises attribute names and rejects foreign attributes |

## Belege

- RED (`--filter RouteSecurity`, Leser aus 42-04): `Tests: 25, Assertions: 68, Failures: 3.`, rc 1. Rot: testALowercaseAttributeNamespaceIsCanonicalisedAndEffective (Profil führte für beide Schreibweisen `attributes []`, das Gate übersah PublicPage), testAForeignOrUnknownAttributeIsAViolation (keine R6-Befunde), testARateLimitSubclassIsAViolation (R1 vorhanden, R6 fehlte). testMethodsWithoutARouteStayOut grün.
- Recherchebehauptung zur Schreibweise belegt, nicht widerlegt: der Einzeltest `--filter testALowercaseAttributeNamespaceIsCanonicalisedAndEffective` ist nach der Kanonisierung `OK (1 test, 5 assertions)`, rc 0; das Feld effective stammt unverändert aus dem Orakel (`hasAnnotationOrAttribute` des Server-Reflectors) und enthält PublicPage für `#[\ocp\appframework\http\attribute\PublicPage]` und für `#[\OCP\AppFramework\Http\Attribute\publicpage]`. Der Server wertet beide Schreibweisen also als PublicPage aus, während der Leser aus 42-04 sie verwarf.
- Ebenso über das Orakel: LooseLimitFixture::open hat AnonRateLimit in effective (IS_INSTANCEOF nimmt die Unterklasse).
- GREEN: `OK (25 tests, 73 assertions)` rc 0; volle Suite `OK (983 tests, 5924 assertions)`, `983 tests executed, floor 28`, rc 0; `git diff --exit-code php/lib` Exit 0. Echte Profile und route-security.json unverändert.
- `php -l` (php:8.2-cli) über RouteProfiles.php, Fixtures.php, RouteSecurityTest.php: No syntax errors.
- Rot-Beweise am echten Baum (Python-Ersetzung, `--filter RouteSecurity` rc 1, Rücknahme mit `git checkout -- php/lib php/appinfo`, `git diff --exit-code` Exit 0, `git status --porcelain` leer):
  - `#[\ocp\appframework\http\attribute\PublicPage]` über der ApiRoute von QueueController::requeue: `changed route QueueController::requeue: expected ApiRoute POST /queues/documents/requeue [ExAppRequired, NoCSRFRequired], actual ApiRoute POST /queues/documents/requeue [ExAppRequired, NoCSRFRequired, PublicPage]` und `R1 QueueController::requeue: PublicPage without AnonRateLimit or BruteForceProtection`.
  - `#[\OCA\Findling\RedProofMissing]` über der Route von setPause: `R6 SettingsController::setPause: attribute OCA\Findling\RedProofMissing cannot be loaded` plus `changed route SettingsController::setPause: ... actual FrontpageRoute POST /admin/pause [OCA\Findling\RedProofMissing]`.
  - `#[\OCA\Findling\Tests\RouteSecurity\Fixture\Foreign]` über der Route von setPause: `R6 SettingsController::setPause: attribute OCA\Findling\Tests\RouteSecurity\Fixture\Foreign is not an OCP attribute` plus changed route.
  - Danach grüner Filterlauf `OK (25 tests, 73 assertions)`.
- JUnit-Schritt lokal (php:8.2-cli, Ausdruck aus php.yml): `the route attribute gate ran 25 tests, the floor is 25`, Exit 0.
- Baumhash 2ba29624... -> a5fd4a1c... (117 Dateien), Rezept und find/sort/tr/sha256sum gleich; `-k php_half` 2 passed.
- Python-Gates grün; pytest seriell: route_gate_presence 23, trust_boundary 21, workflow_pins 14, workflow_tag_triggers 27, measurement `-k php_half` 2.

## CI-Beleg

`scripts/ci/head_green.sh c26beb3aa756... "PHP and store metadata gates" "Python gates"`: rc 0, acht Läufe success:
PHP and store metadata gates 41941138211 (`OK (983 tests, 5924 assertions)`, "the suite executed 983 tests, the floor is 28", "the route attribute gate ran 25 tests, the floor is 25"), Python gates 41941138404, Security scans 41941138242, Resilience 41941138311, Integration 41941138307, HaRP deploy 41941138153, Multi-arch image 41941138373, OpenSSF Scorecard 41941138343.

Hinweis: ein erster head_green-Aufruf mit dem kurzen SHA c26beb3a fand keinen Lauf (`gh run list --commit` verlangt den vollen SHA) und endete mit rc 1, ohne etwas zu prüfen; der gewertete Aufruf lief mit dem vollen SHA.

## Deviations from Plan

1. [Hinweis] Im RED scheiterte der Schreibweisen-Test schon an der Attributliste, bevor er effective prüfte; die Orakel-Aussage ist deshalb über den grünen Einzellauf nach der Kanonisierung belegt (effective wird von der Kanonisierung nicht berührt, es kommt allein aus dem Server-Reflector).
2. [Rule 2, verschärft] testMethodsWithoutARouteStayOut prüft zusätzlich `violations(PlainFixture) === []` (der harmlose ReturnTypeWillChange meldet nichts).

## Known Stubs

Keine.

## Self-Check: PASSED

- Commit c26beb3a vorhanden, CI-Kopf grün, keine neue Datei.
