---
phase: 42-php-sicherheits-gates
plan: 07
subsystem: PHP-Testsuite (Routen-Attribut-Gate) und vier Controller
tags: [php-gates, route-security, final, class-pins, delegated-settings, gap-closure, G42-1]
requires:
  - 42-06 (Regeln auf dem Orakel, classViolations mit R4/R5)
provides:
  - final an GatewayController, ProfileController, QueueController, ReconcileController (Owner-Entscheid)
  - C1 (Controller nicht final), C3 (IDelegatedSettings unter lib/Settings)
  - Klassen-Pins im Objekt classes von route-security.json (final, Elternkette, Traits, Interfaces)
  - RouteProfiles::classesOf, classProfiles, compareClasses, loadClassAllowlist, delegatedSettings
  - Strukturgate prüft classes (Anzahl wie Controller-Dateien, alle final)
affects:
  - 42-08 (Untergrenzen 39)
tech-stack:
  added: []
  patterns:
    - "Allowlist classes von Hand, Leser nur Gegenprobe"
key-files:
  created: []
  modified:
    - php/lib/Controller/GatewayController.php
    - php/lib/Controller/ProfileController.php
    - php/lib/Controller/QueueController.php
    - php/lib/Controller/ReconcileController.php
    - php/tests/RouteSecurity/RouteProfiles.php
    - php/tests/RouteSecurity/Fixtures.php
    - php/tests/Unit/RouteSecurityTest.php
    - php/tests/route-security.json
    - .github/workflows/php.yml
    - backend/tests/test_php_route_gate_presence.py
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Owner-Entscheid 04.11.2026: final setzen."
  - "Klassenprofil: parents von get_parent_class bis zur Wurzel in Kettenreihenfolge, traits der Klasse und aller Eltern sortiert, interfaces sortiert; Vergleich über kanonisches JSON"
  - "Klassen unter php/lib/Settings über die neue Funktion classesOf (glob *.php), weil classesIn nur Controller-Dateien aufzählt"
metrics:
  completed: 2026-11-05
  tasks: 3
  files: 11
---

# Phase 42 Plan 07: Controller final und Klassen-Pins Summary

Owner-Entscheid 04.11.2026: final setzen. Alle sieben Controller sind jetzt final (vier Kopfzeilen, kein Verhalten), ein nicht finaler Controller ist C1, Elternkette, Traits und Interfaces jedes Controllers stehen von Hand im neuen Objekt classes von route-security.json, und keine Klasse unter lib/Settings darf IDelegatedSettings implementieren (C3).

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1-3 | 9a234b94 | test(42-07): pin controller classes and their base chain |

## Belege

- Task 1: Ausgangsstand bestätigt, `grep -lE '^class [A-Za-z]+Controller extends' php/lib/Controller/*.php` ergab genau 4 Dateien (Gateway, Profile, Queue, Reconcile; alle `extends OCSController`), Page, ProfileSettings und Settings schon final.
- RED (Tests und Fixtures zuerst, Leser aus 42-06): `Tests: 34, Assertions: 81, Errors: 3, Failures: 2.`, rc 2; rot genau die fünf neuen Tests.
- Rot-Beweise am noch unveränderten Produktstand, mit dem neuen Leser (`--filter RouteSecurity` rc 1):
  - (a) ohne Änderung: `C1 GatewayController: controller is not final`, ebenso Profile-, Queue-, ReconcileController, und je `changed class <X>: expected {"final":true,...}, actual {"final":false,...}`; die von Hand geschriebene Elternkette (OCSController, ApiController, Controller) stimmte bis auf final mit dem Leser überein.
  - (b) SettingsController `extends \OCP\AppFramework\OCSController`: lädt ohne Fatal, `changed class SettingsController: expected {"final":true,"interfaces":[],"parents":["OCP\\AppFramework\\Controller"],"traits":[]}, actual {...,"parents":["OCP\\AppFramework\\OCSController","OCP\\AppFramework\\ApiController","OCP\\AppFramework\\Controller"],...}` (Ersatzweg über einen Trait nicht nötig).
  - (c) Admin `implements ISettings, \OCP\Settings\IDelegatedSettings` mit getName und getAuthorizedAppConfig: genau `C3 Admin: implements IDelegatedSettings`.
  - Je `git checkout -- php/lib php/appinfo`, `git diff --exit-code` Exit 0, `git status --porcelain` leer.
- final gesetzt per Python-Ersetzung mit Zählprüfung (je genau 1); `git diff --numstat php/lib`: vier Dateien je `1 1`. `php -l` (php:8.2-cli) für die vier Controller und die drei Testdateien: No syntax errors.
- GREEN: `OK (34 tests, 100 assertions)` rc 0; volle Suite `OK (992 tests, 5951 assertions)`, `992 tests executed, floor 28`, rc 0; Verify-Kette (vier Dateien je eine Zeile, keine weitere Änderung unter php/lib) Exit 0.
- JUnit-Schritt lokal: `the route attribute gate ran 34 tests, the floor is 34`, Exit 0.
- Baumhash ca8905b5... -> 04f4443d... (117 Dateien), beide Wege gleich; `-k php_half` 2 passed.
- Python-Gates grün (ruff E501 einmal im neuen Presence-Helfer umgebrochen, vor dem Commit). pytest seriell: route_gate_presence 28, trust_boundary 21, acl_boundary 11, embedding_track 72, files_client 26, profile_wire 11, queue_client 134, reconcile 92, phase33_audit 23 passed und 93 skipped (keine Audit-Instanz, wie bisher), phase36_audit 18, workflow_pins 14, workflow_tag_triggers 27, measurement `-k php_half` 2.

## CI-Beleg

Erster Aufruf `scripts/ci/head_green.sh 9a234b94bff2... "PHP and store metadata gates" "Python gates"`: rc 1, sieben Läufe success, HaRP deploy 41947587646 failure in genau einem Job (stable34, 8.2, ubuntu-24.04) im Schritt "Store upgrade 2b, the seed of the released installation, judged by the released version": `the acceptance left the lines short=1 accepted=1 stayed-short-twice=0 and 1 queue row(s)`. Dieser Schritt prüft die freigegebene Installation v1.5.0 (beide Hälften aus den Release-Assets), nicht den Stand dieses Commits; die drei anderen Matrix-Jobs (stable33, stable35, stable34 arm) waren grün. Gewertet als Zeitfehler (die Queue-Zeile war beim Zählen noch nicht entfernt, der Pass meldete requeued=1); `gh run rerun 41947587646 --failed`, Versuch 2 success.

Zweiter Aufruf nach dem Rerun: rc 0, acht Läufe success:
PHP and store metadata gates 41947587570 (`OK (992 tests, 5951 assertions)`, "the suite executed 992 tests, the floor is 28", "the route attribute gate ran 34 tests, the floor is 34"), Python gates 41947587501, Security scans 41947587572, Resilience 41947587575, Integration 41947587480, HaRP deploy 41947587646 (Versuch 2), Multi-arch image 41947587486, OpenSSF Scorecard 41947587516.

## Deviations from Plan

1. [Rule 2, verschärft] testNoSettingsClassIsDelegated verlangt zusätzlich mindestens zwei Klassen unter lib/Settings (Anti-Vakuität); loadClassAllowlist weist ein leeres classes-Objekt ab.
2. [Hinweis] Für lib/Settings kam die öffentliche Hilfsfunktion classesOf hinzu (glob *.php), weil classesIn nach 42-04 bewusst nur *Controller.php liest.

3. [Hinweis CI] HaRP-Job stable34/x86 einmal rot im Upgrade-Schritt der freigegebenen v1.5.0 (siehe CI-Beleg), per Rerun der fehlgeschlagenen Jobs grün; kein Gate geändert.

## Known Stubs

Keine.

## Self-Check: PASSED

- Commit 9a234b94 vorhanden, vier Controller final, route-security.json mit 7 Klassen-Einträgen, CI-Kopf grün (nach Rerun).
