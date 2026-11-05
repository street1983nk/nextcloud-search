---
phase: 42-php-sicherheits-gates
plan: 04
subsystem: PHP-Testsuite (Routen-Attribut-Gate)
tags: [php-gates, route-security, reflection, oracle, gap-closure, G42-1]
requires:
  - 42-02 (RouteProfiles, Allowlist, JUnit-Schritt)
provides:
  - Router-gleiche Aufzählung (classesIn nur *Controller.php, getMethods() ohne Filter, strayEntries)
  - Server-Orakel ControllerMethodReflector mit Profilfeldern annotations, effective, visibility, static, declaredIn, outside
  - Regeln R3 (Docblock-Annotation) und R5 (static, nicht public, außerhalb deklariert, __call/__callStatic)
  - RouteProfiles::SERVER_ANNOTATION_NAMES (18 Namen, Quelle für 42-09)
  - Gleichschritt-Test Methodenzahl == ROUTE_GATE_MIN_TESTS == MIN_FLOOR
affects:
  - 42-05 bis 42-09
tech-stack:
  added: []
  patterns:
    - "Server-Semantik über das Orakel aus dem Checkout, nicht nachgebaut"
    - "Route-Beschreibung über Route::toArray() der Instanz"
key-files:
  created:
    - php/tests/RouteSecurity/Outside/BaseFixture.php
  modified:
    - php/tests/RouteSecurity/RouteProfiles.php
    - php/tests/RouteSecurity/Fixtures.php
    - php/tests/Unit/RouteSecurityTest.php
    - .github/workflows/php.yml
    - backend/tests/test_php_route_gate_presence.py
    - backend/tests/test_measurement_scripts.py
    - .gitattributes
decisions:
  - "effective führt die Attribut-Kurznamen der Orakel-Paare (StrictCookiesRequired, nicht StrictCookieRequired)"
  - "oracleThrottle bildet readLimitFromAnnotationOrAttribute nach: Annotation mit limit und period, sonst Attribut per IS_INSTANCEOF"
  - "strayEntries meldet auch Punktdateien auf .php (z. B. .XController.php), weil der Router sie mitzählen würde"
metrics:
  completed: 2026-11-05
  tasks: 3
  files: 8
---

# Phase 42 Plan 04: Router-gleiche Aufzählung und Server-Orakel Summary

Das Routen-Gate zählt Controller und Methoden genau wie Router::getAttributeRoutes auf und fragt für jede Routenmethode den echten ControllerMethodReflector des stable34-Checkouts; Docblock-Annotationen (R3), statische, nicht öffentliche oder außerhalb deklarierte Routenmethoden und __call/__callStatic (R5) sowie fremde Einträge in lib/Controller sind rot.

## Commits

| Task | Commit | Inhalt |
|------|--------|--------|
| 1-3 | 593e194c | test(42-04): route gate enumerates like the router and asks the server reflector |

## Server-Checkout

- Lokaler Cache vorher 5a4629ab; `git ls-remote ... refs/heads/stable34` am 05.11.2026: ec467246 (nicht fd576a89 wie im Plan vermerkt, stable34 ist seither weitergelaufen). Cache per `fetch --depth 1 origin stable34`, `checkout -f -B stable34 FETCH_HEAD`, `submodule update`, config.php und data gelöscht; danach Zweig stable34, HEAD ec467246fbbac624fe90163e4770ac01392639d8 = ls-remote. phpunit_docker.sh hat die Instanz beim nächsten Lauf neu installiert.
- Orakel-Stellen am aktualisierten Stand nachgelesen, keine Abweichung zum interfaces-Block: Reflector-Regex Z. 48, `hasAnnotationOrAttribute` (Attribut ohne IS_INSTANCEOF, dann Annotation), `getAnnotationParameter`, Konstruktor mit LoggerInterface; Paare in SecurityMiddleware, CORSMiddleware, PasswordConfirmationMiddleware, SameSiteCookieMiddleware, SessionMiddleware, TwoFactorMiddleware wie gelistet; RateLimitingMiddleware Z. 172 bis 187 (Annotation vor Attribut IS_INSTANCEOF); BruteForceMiddleware Z. 51 (Annotation verdrängt Attribute); Router::getAttributeRoutes Z. 474 bis 518; NullLogger unter 3rdparty/psr/log/src.

## Belege

- RED (`--filter RouteSecurity`, alter Leser): `Tests: 22, Assertions: 42, Errors: 4, Failures: 6, Warnings: 1.`, rc 2. Rot: die 7 neuen Tests, testTheReaderSeesEveryControllerAndEveryRoute (strayEntries fehlt), testTheGateFiresOnTheRealTree (Feld annotations wirkungslos) und testNoControllerRouteBreaksTheRules (siehe Abweichung 1); 12 alte grün.
- GREEN: `OK (22 tests, 64 assertions)` rc 0; volle Suite `OK (980 tests, 5915 assertions)`, `980 tests executed, floor 28`, rc 0, `git diff --exit-code php/lib` Exit 0.
- `php -l` (php:8.2-cli) über RouteProfiles.php, Fixtures.php, Outside/BaseFixture.php, RouteSecurityTest.php: No syntax errors.
- Echte Profile unverändert gegen route-security.json (20 Einträge, testEveryControllerRouteMatchesTheAllowlist grün ohne Änderung der Allowlist).
- Rot-Beweise am echten Baum (je per Python-Ersetzung, `--filter RouteSecurity` rc 1, danach `git checkout -- php/lib php/appinfo`, neue Dateien gelöscht, `git diff --exit-code php/lib php/appinfo` Exit 0 und `git status --porcelain` leer):
  - (a) Zeile "\t * @PublicPage" nach der setPause-Prosazeile: `R3 SettingsController::setPause: docblock annotation @publicpage`.
  - (b) `public static function setPause(`: lädt ohne Fatal, `R5 SettingsController::setPause: route method is static` (Ersatzweg nicht nötig).
  - (c) leere php/lib/Controller/Helper.php: strayEntries `Helper.php`, dazu testTheReaderSees... "actual size 7 matches expected size 8".
  - (c2) `__call` in SettingsController: `R5 SettingsController: defines __call`.
  - (c3) `protected function redProofHidden()` mit POST /red-proof-hidden: `R5 SettingsController::redProofHidden: route method is protected` und `unlisted route SettingsController::redProofHidden (FrontpageRoute POST /red-proof-hidden)`.
  - (d) php/lib/Service/RedProofRouteBase.php mit `leak()` und SettingsController `extends \OCA\Findling\Service\RedProofRouteBase`: `unlisted route SettingsController::leak (FrontpageRoute GET /leak)` und `R5 SettingsController::leak: route method is declared in lib/Service/RedProofRouteBase.php, outside the controller directory`; Autoload im Spiegel klappte, kein require_once nötig.
  - Danach grüner Filterlauf `OK (22 tests, 64 assertions)`.
- JUnit-Schritt lokal (Ausdruck und Untergrenze per yaml.safe_load aus php.yml, php:8.2-cli): `the route attribute gate ran 22 tests, the floor is 22`, Exit 0.
- Baumhash 06a082a0... -> 2ba29624... (117 Dateien), Rezept 40b-baumhash.py und unabhängig find/sort/tr/sha256sum gleich; `-k php_half` 2 passed.
- Zeilenenden: .gitattributes `php/tests/RouteSecurity/** text eol=lf`; nach Neu-Auschecken und `git add --renormalize php/tests/RouteSecurity` kein CR in Arbeitskopie und Index.
- Python-Gates grün (ruff check/format für backend und scripts, pyright 0 Fehler, vulture); pytest seriell: route_gate_presence 23 passed, trust_boundary 21, workflow_pins 14, workflow_tag_triggers 27, measurement `-k php_half` 2.

## CI-Beleg (Kopf 593e194c)

`scripts/ci/head_green.sh 593e194c... "PHP and store metadata gates" "Python gates"`: rc 0, acht Läufe success:
PHP and store metadata gates 41936951308 (`OK (980 tests, 5915 assertions)`, "the suite executed 980 tests, the floor is 28", "the route attribute gate ran 22 tests, the floor is 22"), Python gates 41936951259, Security scans 41936951183, Multi-arch image 41936951316, HaRP deploy 41936951199, Resilience 41936951178, Integration 41936951184, OpenSSF Scorecard 41936951158.

## Deviations from Plan

1. [Plan-Ungenauigkeit, kein Gate-Eingriff] Der Plan erwartete testNoControllerRouteBreaksTheRules im RED grün; da der Test laut Task 1 Schritt 4 zusätzlich `classViolationsOfDirectory()` prüft, das es vor Task 2 nicht gab, war er rot (Error). RED-Bild daher 12 grün, 10 rot statt 13/9.
2. [Hinweis] stable34 stand am 05.11. auf ec467246 statt der im Plan genannten fd576a89; Cache auf den tatsächlichen ls-remote-Stand gebracht, Orakel-Stellen unverändert.
3. [Rule 2, verschärft] testTheServerOracleTreatsTheAnnotationAsEffective prüft zusätzlich die Positivkontrolle `oracleThrottle(PublicFixture::class, 'limited', ...)` = limit 5/period 60 sowie effective für shouted, strict und throttled; der Stray-Test legt zusätzlich eine `.claude-active` ins Temp-Verzeichnis.
4. [Hinweis] SettingsController.php liegt in der Arbeitskopie mit CRLF; der Server-Regex erkennt die Annotation dort trotzdem (`.*` nimmt das CR in den Parameter), Rot-Beweis (a) belegt das.

## Known Stubs

Keine.

## Self-Check: PASSED

- php/tests/RouteSecurity/Outside/BaseFixture.php vorhanden, Commit 593e194c vorhanden, CI-Kopf grün.
