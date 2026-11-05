---
phase: 42-php-sicherheits-gates
verified: 2026-11-05T12:00:00Z
status: passed
score: "SK1, SK2 und SK4 verifiziert; Vektoren 14/14 voll"
overrides_applied: 0
scope: "Erfolgskriterien 1, 2 und 4 der ROADMAP plus die 14 Vektoren aus 42-04 bis 42-10; Kriterium 3 (Psalm, php-cs-fixer, zizmor, actionlint) bewusst vertagt"
re_verification:
  previous_status: gaps_found
  previous_score: "SK1 teilweise; Vektoren 12/14 voll, 2/14 teilweise (3 und 6, Groß-/Kleinschreibung)"
  gaps_closed:
    - "Vektoren 3 und 6, Textseite: Router- und Containernamen werden in AppSurface::sourceFindings und LIB_BANS jetzt ohne Rücksicht auf Groß-/Kleinschreibung gesperrt (42-10, dca4478d)"
  gaps_remaining: []
  regressions: []
---

## Finale Re-Verifikation nach 42-10 (2026-11-05)

Frühere Läufe: Lauf 1 fand vier Lücken (Docblocks, geerbte Methoden, Untergrenzen, Textsperre), 42-09 schloss sie. Lauf 2 fand nur noch die case-sensitive Textsperre (Vektoren 3 und 6). Dieser Lauf prüft nur diese Lücke.

Unabhängige Rotproben am echten Baum (andere Dateien und Methoden als der Executor, danach zurückgesetzt, git status sauber bis auf fremde untracked Dateien):

| Probe | PHPUnit (scripts/dev/phpunit_docker.sh) | pytest test_php_surface_bans.py |
| ----- | ---------------------------------------- | ------------------------------- |
| Neue Datei php/lib/Db/ZzProbe.php: `use OCP\Route\IrOuTeR as R;` und `$s->GetRouter();` | rot: testNoSourceUnderLibTouchesTheRouterOrTheContainer meldet `ZzProbe.php:4: OCP\Route\IrOuTeR` und `:6: GetRouter` | rot: `php/lib/Db/ZzProbe.php:4: IRouter` (plus getRouter) |
| Application::register: `$context->registerSERVICE("x", fn () => \oc::$server->get(\ocp\route\irouter::class));` | rot: dieselbe Methode meldet `Application.php:55: registerSERVICE` und `\ocp\route\irouter` | rot: `Application.php:55: registerService(` und `IRouter` |

Baseline ohne Probe: `OK (998 tests, 6049 assertions)`; pytest (Textsperren + Gate-Präsenz) 106 passed. Gate-Untergrenze ROUTE_GATE_MIN_TESTS: 40 in php.yml, MIN_FLOOR = 40 in test_php_route_gate_presence.py.

CI auf main HEAD c99f499738c78fa26c5cca07f3cf9aaf59c5c332: alle acht Workflows success (u. a. PHP and store metadata gates, Python gates). python.yml triggert jetzt auf `php/**` (push und pull_request).

Ergebnis: Lücke geschlossen, Status passed.


# Phase 42: PHP-Sicherheits-Gates für die Companion-App, Verifikationsbericht (Re-Verifikation)

**Phasenziel:** Die PHP-Hälfte von Findling bekommt Gates auf dem Niveau der Python-Seite, damit keine Route versehentlich öffentlich oder ohne CSRF wird und verwundbare Abhängigkeiten auffallen.
**Umfang:** Erfolgskriterien 1, 2 und 4 sowie die 14 Vektoren der Lückenschluss-Pläne 42-04 bis 42-09. Kriterium 3 ist vertagt.
**Verifiziert:** 2026-11-05T03:30:15Z auf main `1a9e6998e54d83479dceaee1025ab2f3141d3b6b`
**Status:** gaps_found (eine Lücke, klein und eng umrissen)
**Re-Verifikation:** Ja, nach dem Lückenschluss 42-04 bis 42-09

## Vorheriger Lauf (2026-11-04T21:24:00Z)

Status gaps_found, 2/3: SK1 teilweise, weil der Leser Docblock-Annotationen und geerbte Routenmethoden nicht sah. Die damals offene menschliche Prüfung (lokales PHPUnit-Rezept) ist mit diesem Lauf erledigt: lokal `OK (997 tests, 6040 assertions)`, `phpunit_docker: 997 tests executed, floor 28`, rc 0. Beide alten Lücken sind geschlossen und am echten Baum mit eigenen Proben rot belegt (Vektoren 1 und 5 unten).

## Zielerreichung

### Erfolgskriterien

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| SK1 | Routen-Attribut-Gate mit Allowlist und Negativtests; neue oder geänderte Route ohne Eintrag macht CI rot | TEILWEISE | Routen-, Klassen- und Registrierungsseite trägt für alle 14 Vektoren (Tabelle unten), 39 Testmethoden, CI-Log `the route attribute gate ran 39 tests, the floor is 39`. Lücke: die Namenssperren gegen Router- und Container-Zugriff (Vektoren 3 und 6, Textseite) sind case-sensitiv und lassen sich mit Kleinschreibung umgehen. |
| SK2 | `composer validate --strict` und `composer audit --locked` in php.yml, Dependabot composer | VERIFIZIERT | Job `composer-hygiene` (php.yml Z. 225 ff.): `composer validate --strict --no-check-publish`, `composer audit --locked --no-interaction`, `working-directory: php`, `persist-credentials: false`, kein `|| true`. dependabot.yml Z. 133: `package-ecosystem: composer`, `/php`, weekly. CI 41953527552: `./composer.json is valid`, `No security vulnerability advisories found.` |
| SK4 | PHPUnit lokal über Docker und in CI | VERIFIZIERT | Lokal selbst ausgeführt: `bash scripts/dev/phpunit_docker.sh` rc 0, `OK (997 tests, 6040 assertions)`. CI 41953527552 (4798b5dc, letzter PHP-Commit): `OK (997 tests, 6040 assertions)`, `the suite executed 997 tests, the floor is 28`. |

### Die 14 Vektoren, je mit eigener Rot-Probe am echten Baum

Alle Proben sind eigene Muster, bewusst andere Dateien, Methoden und Formen als die Rot-Beweise der Executor-Summaries. Ablauf je Probe: Python-Ersetzung, `scripts/dev/phpunit_docker.sh --filter RouteSecurity`, danach `pytest tests/test_php_surface_bans.py tests/test_exapp_surface.py`, danach `git checkout -- <pfad>`, neue Dateien gelöscht; nach jeder Probe `git status --porcelain` gleich dem Ausgangszustand und `git diff --stat` leer (`clean_after_revert=True` in allen 19 Läufen).

| V | Vektor | Test, der ihn fängt | Eigene Probe | Ergebnis | Status |
|---|---|---|---|---|---|
| 1 | Docblock-Annotationen | testADocblockAnnotation..., testTheServerOracle..., Python scan_annotations | `* @NoCSRFRequired` im Docblock von ProfileSettingsController::saveProfile (POST), `* @UserRateThrottle(limit=1000, period=1)` an checkState | `R3 ...saveProfile: docblock annotation @nocsrfrequired`, `R2 ...saveProfile: NoCSRFRequired on POST without ExAppRequired` (Orakel sieht die Annotation als wirksam), `R3 ...checkState: ... @userratethrottle`; pytest 1 failed mit Datei und Zeile | VERIFIZIERT |
| 2 | Schreibweise von Attributnamen | testALowercaseAttributeNamespace... | `#[\OCP\AppFramework\Http\Attribute\noadminrequired]` an SettingsController::overview | `changed route SettingsController::overview: ... actual ... [NoAdminRequired]` (kanonisiert) | VERIFIZIERT |
| 3 | Legacy-Routen über routes.php oder IRouter | testAppinfoRoutesDeclaresNoRoute, testAppinfoRoutesUsesOnlyLiteralTokens, testNoSourceUnderLib..., Python LIB_BANS/ROUTES_BANS | (a) reine Literal-Route `'routes' => [['name' => 'page#index', 'url' => '/legacy', 'verb' => 'GET']]`; (b) `use OCP\Route\irouter;`, `->actioninclude(`, `->getrouter()` in neuer Service-Datei | (a) rot, 1 Failure (testAppinfoRoutesDeclaresNoRoute); (b) **PHPUnit OK (39 tests), pytest 86 passed** | TEILWEISE |
| 4 | static, nicht public, __call/__callStatic | testAStaticOrNonPublicRouteMethod... | private Routenmethode `redPrivate` in ProfileController, `__callStatic` in PageController | `R5 ProfileController::redPrivate: route method is private`, `unlisted route ProfileController::redPrivate`, `R5 PageController: defines __callStatic` | VERIFIZIERT |
| 5 | Vererbung, Trait | testAnInheritedRoute..., testARouteMethodDeclaredOutside... | Trait `OCA\Findling\Service\RedRouteTrait` mit FrontpageRoute, per `use` in PageController | `unlisted route PageController::redTrait`, `R5 ... declared in lib/Service/RedRouteTrait.php, outside the controller directory`, `changed class PageController: ... traits` | VERIFIZIERT |
| 6 | Controller-Austausch (Unterklasse, DI) | testANonFinalControllerIsReported, testEveryControllerIsFinal, Container-Namenssperre | (a) `final` an PageController entfernt; (b) `$this->getcontainer()->registerservice(PageController::class, ...)` im Application-Konstruktor; (c) Kontrolle mit exakter Schreibweise | (a) `C1 PageController: controller is not final` plus changed class; (b) **PHPUnit OK (39 tests), pytest 86 passed**; (c) Tokenprüfung rot, pytest `registerService(`/`getContainer(` rot | TEILWEISE |
| 7 | Klassenattribute | testAClassAttributeIsAViolation... | `#[...\PublicPage]` an der Klasse GatewayController | `R4 GatewayController: class attribute PublicPage has no effect on routes` | VERIFIZIERT |
| 8 | fremde Attribute, Rate-Limit-Unterklasse | testAForeignOrUnknown..., testARateLimitSubclass... | neue Klasse `OCA\Findling\Service\RedLimit extends UserRateLimit` an ProfileSettingsController::startCheck | `R6 ...startCheck: attribute OCA\Findling\Service\RedLimit is not an OCP attribute` plus changed route | VERIFIZIERT |
| 9 | ExApp-Routentabelle, Laufzeitregistrierung | test_exapp_surface.py | `bruteforce_protection` von `^/diagnose$` auf `[]`; f-String `/ocs/v1.php/cloud/apps/{app}` in nc/client.py | Tabellenbefund an Index 2 und `OCS path outside /ocs/v2.php/apps/findling/`, 2 failed | VERIFIZIERT |
| 10 | Basisklassenwechsel | testTheParentChainAndTraitsMatchTheAllowlist | ProfileSettingsController `extends \OCP\AppFramework\ApiController` | `changed class ProfileSettingsController: ... parents [ApiController, Controller]` | VERIFIZIERT |
| 11 | Registrierungen in IBootstrap | testTheApplicationRegistersExactly..., testAnUnlistedOrMissing... | (a) `registerDeclarativeSettings(Admin::class)` in register(); (b) nur `injectFn(...)` in boot() | (a) `unlisted registration registerDeclarativeSettings(OCA\Findling\Settings\Admin)`; (b) rot, 1 Failure (boot zeichnet etwas auf) | VERIFIZIERT |
| 12 | R1 mit falschem Limit | testBruteForceProtectionAlone..., testAClassRateLimitDoesNotSatisfyR1 | `PublicPage` plus `UserRateLimit(limit: 5, period: 60)` an PageController::index | `R1 PageController::index: PublicPage without AnonRateLimit` plus changed route | VERIFIZIERT |
| 13 | IDelegatedSettings, info.xml | testNoSettingsClassIsDelegated, Python scan_info_xml | neue Klasse `OCA\Findling\Settings\Personal implements IDelegatedSettings`; `<personal>` in den settings von php/appinfo/info.xml | `C3 Personal: implements IDelegatedSettings`; pytest `info.xml settings are (...) expected (...)` | VERIFIZIERT |
| 14 | root, postfix, defaults | testRootPostfixOrDefaults... | `defaults: ['n' => 5]` an QueueController::getDocuments | `R7 QueueController::getDocuments: route argument defaults is not allowed` plus changed route | VERIFIZIERT |

**Score:** SK2 und SK4 verifiziert, SK1 teilweise; Vektoren 12 von 14 voll, 3 und 6 teilweise (nur die Groß-/Kleinschreibungs-Umgehung der Namenssperren).

### Artefakte

| Artefakt | Status | Details |
|---|---|---|
| `php/tests/RouteSecurity/RouteProfiles.php` | VERIFIZIERT | Aufzählung per `getMethods()` ohne Filter, Orakel `OC\AppFramework\Utility\ControllerMethodReflector` fail closed, R1 bis R8, C1, C3, Klassenprofile |
| `php/tests/RouteSecurity/AppSurface.php` | TEILWEISE | Token-Whitelist routes.php und Registrierungs-Recorder tragen; `sourceFindings()` case-sensitiv |
| `php/tests/RouteSecurity/Fixtures.php`, `Outside/BaseFixture.php` | VERIFIZIERT | je Regel eine rote Fixture |
| `php/tests/Unit/RouteSecurityTest.php` | VERIFIZIERT | 39 Testmethoden (`grep -cE '^\s*public function test'`), keine Skip-Marker |
| `php/tests/route-security.json`, `php/tests/app-surface.json` | VERIFIZIERT | echte Läufe grün, jede Abweichung in den Proben rot |
| `backend/tests/test_php_surface_bans.py` | TEILWEISE | Annotationen case-insensitiv, LIB_BANS case-sensitiv |
| `backend/tests/test_exapp_surface.py` | VERIFIZIERT | |
| `.github/workflows/php.yml` | VERIFIZIERT | `ROUTE_GATE_MIN_TESTS: 39`, `MINIMUM_TESTS: 28`, composer-hygiene |
| `.github/dependabot.yml` | VERIFIZIERT | composer `/php` |
| `backend/tests/test_php_route_gate_presence.py` | VERIFIZIERT | `MIN_FLOOR = 39` |

### Schlüsselverbindungen

| Von | Nach | Status | Details |
|---|---|---|---|
| RouteSecurityTest | Server-Checkout stable34 (Orakel) | VERDRAHTET | Probe V1: R2 entsteht aus dem Orakel, nicht aus Attributen |
| RouteSecurityTest | php/lib/Controller | VERDRAHTET | 7 Klassen, mindestens 20 Routen, keine Fremdeinträge |
| php.yml phpunit | RouteSecurityTest | VERDRAHTET | CI-Log `the route attribute gate ran 39 tests, the floor is 39` |
| Untergrenzen | Testanzahl | VERDRAHTET | 39 Methoden = ROUTE_GATE_MIN_TESTS = MIN_FLOOR |
| python.yml | test_php_surface_bans.py | TEILWEISE (Info) | python.yml startet auf backend/**, scripts/** und montags, nicht auf php/**; die Textseite greift bei reinen PHP-Commits erst im Wochenlauf. Die PHPUnit-Seite deckt dieselben Vektoren in php.yml ab, außer der Lücke oben. |

### Verhaltens-Stichproben

| Verhalten | Befehl | Ergebnis | Status |
|---|---|---|---|
| Volle PHPUnit-Suite lokal | `bash scripts/dev/phpunit_docker.sh` | rc 0, `OK (997 tests, 6040 assertions)`, floor 28 | PASS |
| Python-Tests aus 42-09 | `uv run --frozen pytest -q tests/test_php_surface_bans.py tests/test_exapp_surface.py tests/test_info_xml_defaults.py tests/test_phase40_audit.py` | 160 passed, 7 skipped (67 + 19 + 9 + 65) | PASS |
| Struktur- und Grenzgates | `pytest tests/test_php_route_gate_presence.py tests/test_php_supply_chain_gates.py tests/test_php_trust_boundary.py`; `test_measurement_scripts.py -k php_half` | 67 passed; 2 passed | PASS |
| 19 Rot-Proben (Tabelle oben) | eigenes Skript im Scratchpad | 17 rot aus dem erwarteten Grund, 2 grün (Lücke) | siehe Lücke |

### CI auf main (selbst abgefragt, volle SHA)

- `1a9e6998e54d83479dceaee1025ab2f3141d3b6b` (HEAD = origin/main, nur Planung): Security scans 41959864516 success, OpenSSF Scorecard 41959864544 success; die übrigen Workflows starten wegen ihrer Pfadfilter nicht.
- `0aed7906d0d8cfaffae3f644a544c76ce635edea` (42-09, Python): 7 Läufe success, darunter Python gates 41956536303.
- `4798b5dc6ee8a1d196aaf573a7b6d9728090f0ea` (42-08, letzter PHP-Commit): 8 Läufe success, PHP and store metadata gates 41953527552 (997 Tests, Routen-Gate 39/39, composer valid, keine Advisories).
- Ebenso grün: 9a234b94 (42-07), 587c758c (42-06), c26beb3a (42-05), 593e194c (42-04), je 8 Läufe success.

### Produktcode, Commits

`git diff a0cb12c5 HEAD` unter php/lib, php/appinfo, backend/src, backend/appinfo, composer.*, CHANGELOG.md: genau vier Zeilen, `class` zu `final class` in Gateway-, Profile-, Queue- und ReconcileController (Owner-Entscheid 42-07). Kein Tag. Alle 19 Commits seit a0cb12c5 von `street1983nk <k.cherif@outlook.de>`, keine Trailer, kein close/fix/resolve vor `#N`.

### Anti-Pattern

| Datei | Muster | Schwere | Wirkung |
|---|---|---|---|
| geänderte Dateien seit a0cb12c5 | TBD/FIXME/XXX | | keine Funde |
| `backend/tests/test_php_surface_bans.py` | Kommentar "case-sensitiv wie PHP-Bezeichner" | Warnung | sachlich falsch für PHP, Ursache der Lücke |
| `RouteSecurityTest::testTheGateFiresOnTheRealTree` | setzt Annotationen ins Profil und erwartet genau einen Befund | Info | bei einer echten Annotation an anderer Stelle fällt zusätzlich dieser Test, harmlos (rot bleibt rot) |
| `backend/tests/test_exapp_surface.py` | AST-Prüfung von Attributnamen | Info | `getattr(nc, "web" + "hooks")` oder zusammengesetzte Pfade sieht eine statische Prüfung grundsätzlich nicht; gezielte Verschleierung, kein versehentlicher Fall |

### Menschliche Prüfung

Keine. Docker-Lauf und alle Proben wurden in diesem Lauf selbst ausgeführt.

### Zusammenfassung der Lücke

Die beiden Lücken des Vorlaufs sind geschlossen, und von den 14 Vektoren tragen 12 vollständig: jede eigene Probe wurde aus dem erwarteten Grund rot, oft doppelt (Allowlist und Regel). Offen ist eine einzige, eng umrissene Lücke: die Namenssperren gegen Router- und Container-Zugriff (AppSurface::sourceFindings und LIB_BANS in test_php_surface_bans.py) vergleichen case-sensitiv. Da PHP Klassen- und Methodennamen ohne Rücksicht auf Groß-/Kleinschreibung auflöst, laufen `use OCP\Route\irouter;`, `->actioninclude(` und `$this->getcontainer()->registerservice(...)` durch beide Gates (PHPUnit 39/39 grün, pytest grün). Damit sind die Textseiten von Vektor 3 (Route ohne Middleware über den Router) und Vektor 6 (Controller-Austausch per DI, den `final` nicht verhindert) umgehbar. Heute steht keine solche Zeile im Baum, es gibt also keine aktuelle Exposition. Der Fix ist klein: Namen kleingeschrieben vergleichen, je eine Negativprobe in Kleinschreibung. Wer das als bewusste Verschleierung außerhalb des Ziels "versehentlich" einstuft, kann es per Override annehmen; der Verifier empfiehlt den Fix, weil das Gate dieselbe Regel für Attribute (Vektor 2) bereits selbst umsetzt.

---

_Verifiziert: 2026-11-05T03:30:15Z_
_Verifier: Claude (gsd-verifier)_
