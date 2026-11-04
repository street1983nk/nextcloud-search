---
phase: 42-php-sicherheits-gates
verified: 2026-11-04T21:24:00Z
status: gaps_found
score: 2/3 Erfolgskriterien verifiziert (Kriterium 1 teilweise)
overrides_applied: 0
scope: "Erfolgskriterien 1, 2 und 4 der ROADMAP; Kriterium 3 (Psalm, php-cs-fixer, zizmor, actionlint) bewusst vertagt, geprüft wird nur die Vertagung"
gaps:
  - truth: "Routen-Attribut-Gate: eine neue oder geänderte Route ohne Allowlist-Eintrag macht CI rot (Ziel: keine Route versehentlich öffentlich oder ohne CSRF)"
    status: partial
    reason: "Der Leser RouteProfiles sieht nur PHP-Attribute. Nextcloud stable34 wertet für PublicPage, NoCSRFRequired, NoAdminRequired, ExAppRequired, AuthorizedAdminSetting und SubAdminRequired weiterhin auch Docblock-Annotationen aus (ControllerMethodReflector::hasAnnotationOrAttribute, Zeile 136 bis 147; SecurityMiddleware Zeile 123, 193, 232). Ein '* @PublicPage' oder '* @NoCSRFRequired' im Docblock einer Routenmethode macht die Route öffentlich bzw. CSRF-frei, ohne dass RouteSecurityTest, die Regeln R1/R2 oder test_php_trust_boundary.py rot werden. Zweite, kleinere Lücke derselben Art: ofClass() überspringt geerbte Methoden (getDeclaringClass() !== $class), Router::getAttributeRoutes registriert aber per getMethods() auch geerbte Routen; eine Routenmethode in einer Basisklasse außerhalb von lib/Controller wäre unsichtbar."
    artifacts:
      - path: "php/tests/RouteSecurity/RouteProfiles.php"
        issue: "ofClass() liest weder getDocComment() noch geerbte öffentliche Methoden"
      - path: "php/tests/RouteSecurity/Fixtures.php"
        issue: "keine Fixture mit Docblock-Annotation und keine mit geerbter Routenmethode"
      - path: "php/tests/Unit/RouteSecurityTest.php"
        issue: "kein Negativtest für Annotation oder Vererbung"
    missing:
      - "RouteProfiles::ofClass: Docblock jeder Routenmethode mit demselben Muster wie der Server lesen (preg_match_all('/^\\h+\\*\\h+@(?P<annotation>[A-Z]\\w+)/m', ...)) und jede der Annotationen PublicPage, NoCSRFRequired, NoAdminRequired, ExAppRequired, AuthorizedAdminSetting, SubAdminRequired, BruteForceProtection, UserRateThrottle, AnonRateThrottle, CORS, PasswordConfirmationRequired als eigenen Befund 'R3 <Key>: docblock annotation @<Name>' in violations() melden (Annotationen ganz verbieten statt erlauben)"
      - "Fixture 'AnnotationFixture' mit '/** @PublicPage */' und '/** @NoCSRFRequired */' über einer FrontpageRoute-Methode plus Negativtest, der genau diese Befunde erwartet"
      - "RouteProfiles::ofClass: den Filter getDeclaringClass() !== $class entfernen (oder geerbte Routenmethoden unter dem Kurznamen der konkreten Klasse profilieren), plus Fixture 'InheritedFixture extends BaseFixture' und Negativtest 'unlisted route InheritedFixture::...'"
      - "ROUTE_GATE_MIN_TESTS in php.yml auf die neue Zahl der Testmethoden anheben; MIN_FLOOR in backend/tests/test_php_route_gate_presence.py mitziehen"
      - "Optional im selben Zug: in test_php_trust_boundary.py oder test_php_route_gate_presence.py eine Textsperre gegen '@PublicPage', '@NoCSRFRequired', '@NoAdminRequired' unter php/lib/Controller, damit der Schutz auch bei reinen Backend-Commits greift"
deferred:
  - truth: "Erfolgskriterium 3: Psalm mit Taint gegen ocp 33/34/35, php-cs-fixer dry-run, zizmor, actionlint"
    addressed_in: "eigene Phase vor Findling 1.7 (noch ohne Phasennummer)"
    evidence: "ROADMAP.md Zeile 251: 'Kriterium 3 (Psalm mit Taint, php-cs-fixer, zizmor, actionlint) ist nicht Teil dieser Phase und kommt als eigene Phase vor Findling 1.7.'; docs/testing.md nennt dieselbe Vertagung"
human_verification:
  - test: "scripts/dev/phpunit_docker.sh einmal ohne Argumente und einmal mit --filter RouteSecurity lokal laufen lassen"
    expected: "ohne Argumente 'OK (973 tests, ...)' und 'phpunit_docker: 973 tests executed, floor 28', rc 0; mit Filter 15 Tests und der Hinweis, dass die Untergrenze übersprungen wird"
    why_human: "Docker war für diese Verifikation ausgeschlossen; das Skript ist nur statisch geprüft (bash -n, Schlüssel-Extraktion, Logik)"
---

# Phase 42: PHP-Sicherheits-Gates für die Companion-App, Verifikationsbericht

**Phasenziel:** Die PHP-Hälfte von Findling bekommt Gates auf dem Niveau der Python-Seite, damit keine Route versehentlich öffentlich oder ohne CSRF wird und verwundbare Abhängigkeiten auffallen.
**Umfang (vereinbart):** nur Erfolgskriterien 1, 2 und 4; Kriterium 3 ist vertagt, geprüft wird nur, dass die Vertagung in der ROADMAP steht.
**Verifiziert:** 2026-11-04T21:24:00Z
**Status:** gaps_found
**Re-Verifikation:** Nein, Erstverifikation

## Zielerreichung

### Beobachtbare Wahrheiten

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| 1 | SK1: ein Test vergleicht jede Controller-Methode und ihre Attribute mit einer committeten Allowlist; neue oder geänderte Route ohne Eintrag macht CI rot, mit Negativtest | TEILWEISE (Lücke) | Attribut-Seite trägt: RouteSecurityTest liest per Reflection Methoden- und Klassenattribute aus `OCP\AppFramework\Http\Attribute` inklusive Ratelimit-Argumenten; `compare()` meldet unlisted, changed (Attribut, Verb, URL, weitere Routenargumente) und stale; `violations()` R1/R2; Negativtests gegen Fixtures (unlisted, added attribute, verb/url, stale, Ratelimit-Argumente, Klassenattribut, R1, R2, Fremdattribut) und gegen den echten Baum (setPause fehlt, PublicPage an requeue). Allowlist von mir unabhängig per grep gegen die 7 Controller abgeglichen: 20 Routen, deckungsgleich, keine Klassenattribute. Lücke: Docblock-Annotationen (`@PublicPage`, `@NoCSRFRequired`, ...) wertet Nextcloud stable34 weiterhin aus, das Gate sieht sie nicht; geerbte Routenmethoden werden übersprungen, der Router registriert sie. |
| 2 | SK2: `composer validate --strict` und `composer audit --locked` in php.yml, Dependabot-Eintrag für composer | VERIFIZIERT | Job `composer-hygiene` (timeout 10, persist-credentials false, kein `|| true`, kein continue-on-error, `working-directory: php`); dependabot.yml: composer, `/php`, weekly Montag 05:00 Europe/Berlin, Gruppe minor/patch, phpunit-Majors ignoriert; php.yml schedule `50 5 * * 1`, concurrency-Gruppe mit `github.event_name`. CI 41909998607 (a0cb12c5): `./composer.json is valid`, `No security vulnerability advisories found.`; Dependabot-Lauf `composer in /php` 41910010415 success. |
| 3 | SK4: PHPUnit läuft lokal über Docker und in CI; alle Gates lokal grün vor Commit | VERIFIZIERT (lokaler Lauf nur statisch, siehe menschliche Prüfung) | `scripts/dev/phpunit_docker.sh` (100755) liest SERVER_VERSION (`stable34`) und MINIMUM_TESTS (`28`) per sed aus php.yml, von mir nachgestellt; `bash -n` ok; Untergrenze nur ohne Argumente, mit Argumenten ausdrücklich übersprungen; Exit-Code von PHPUnit bzw. 1 unter der Untergrenze. "CI only" aus php.yml-Kommentar, bootstrap.php und docs/testing.md für PHPUnit entfernt (Rest betrifft nur Integrationsjobs). CI-PHPUnit auf allen drei Code-Commits grün: 41897060856, 41905206023, 41909998607 (`OK (973 tests, 5887 assertions)`, `the suite executed 973 tests, the floor is 28`). |

**Score:** 2/3 vollständig, 1 teilweise.

### Vertagte Punkte

| # | Punkt | Wo | Beleg |
|---|---|---|---|
| 1 | SK3: Psalm mit Taint, php-cs-fixer, zizmor, actionlint | eigene Phase vor Findling 1.7 | ROADMAP.md Zeile 251, ebenso docs/testing.md. Hinweis: eine eigene Phasenzeile existiert in der ROADMAP noch nicht, nur der Satz. |

### Artefakte

| Artefakt | Erwartet | Status | Details |
|---|---|---|---|
| `php/tests/Unit/RouteSecurityTest.php` | Gate mit Negativtests | VERIFIZIERT, Lücke s. o. | 15 Testmethoden, `final class`, kein Skip-Marker |
| `php/tests/RouteSecurity/RouteProfiles.php` | Leser, Vergleich, Regeln | TEILWEISE | Attribute korrekt; Docblock und geerbte Methoden nicht gelesen |
| `php/tests/RouteSecurity/Fixtures.php` | Fixtures für R1, R2, Klassenattribut, Fremdattribut | VERIFIZIERT | per require_once, PSR-4-Warnung beim dump-autoload dokumentiert |
| `php/tests/route-security.json` | 20 Einträge | VERIFIZIERT | unabhängig gegen grep der Controller abgeglichen |
| `.github/workflows/php.yml` | composer-hygiene, schedule, JUnit-Schritt | VERIFIZIERT | in CI 41909998607 alle vier Jobs success |
| `.github/dependabot.yml` | composer-Eintrag | VERIFIZIERT | |
| `backend/tests/test_php_route_gate_presence.py` | Python-Strukturgate | VERIFIZIERT | |
| `backend/tests/test_php_supply_chain_gates.py` | Python-Strukturgate | VERIFIZIERT | |
| `scripts/dev/phpunit_docker.sh` | lokales Rezept | VERIFIZIERT (statisch) | |
| `docs/testing.md` | Doku ohne "CI only" für PHPUnit | VERIFIZIERT | |

### Schlüsselverbindungen

| Von | Nach | Über | Status | Details |
|---|---|---|---|---|
| RouteSecurityTest | php/lib/Controller | `RouteProfiles::ofDirectory` + Untergrenze 7 Klassen, mindestens 20 Routen | VERDRAHTET | Anti-Vakuität im Test |
| RouteSecurityTest | route-security.json | `loadAllowlist` | VERDRAHTET | |
| php.yml phpunit | RouteSecurityTest | JUnit-Schritt "The route attribute gate ran", Suite-Name, Untergrenze 15, skipped/failures/errors = 0 | VERDRAHTET | CI-Log: `the route attribute gate ran 15 tests, the floor is 15` |
| python.yml | php.yml / dependabot.yml | zwei Python-Strukturgates | VERDRAHTET | Mutationsprobe unten |
| phpunit_docker.sh | php.yml | sed-Extraktion SERVER_VERSION, MINIMUM_TESTS | VERDRAHTET | liefert `stable34`, `28` |
| appinfo/routes.php | Gate | `testAppinfoRoutesDeclaresNoRoute` | VERDRAHTET | Datei leer bis auf zwei leere Arrays |

### Verhaltens-Stichproben

| Verhalten | Befehl | Ergebnis | Status |
|---|---|---|---|
| Python-Gates grün | `uv run --frozen pytest -q tests/test_php_route_gate_presence.py tests/test_php_supply_chain_gates.py tests/test_measurement_scripts.py tests/test_php_trust_boundary.py` | 630 passed | PASS |
| Strukturgates werden rot auf echter, mutierter Datei (eigenes Skript im Scratchpad, nicht die Testproben) | Untergrenze 14, Schritt umbenannt, markTestSkipped eingefügt, `|| true` am Audit, schedule entfernt, composer-Eintrag entfernt | je genau ein Befund, unverändert 0 Befunde | PASS |
| SERVER_VERSION/MINIMUM_TESTS-Extraktion des Skripts | sed-Ausdruck des Skripts gegen php.yml | `stable34`, `28` | PASS |
| PHP-Lauf in CI auf a0cb12c5 | `gh run view 41909998607` | 4 Jobs success, Schritt "The route attribute gate ran" success | PASS |
| Server wertet Docblock-Annotationen aus | Lesen von stable34 (lokaler Checkout, nur gelesen) `ControllerMethodReflector.php` Z. 136 bis 147, `SecurityMiddleware.php` Z. 123, 193, 232 | Annotation reicht für PublicPage/NoCSRFRequired, nur Debug-Log | FAIL für SK1 |
| Router registriert geerbte Routen | `lib/private/Route/Router.php` Z. 493 bis 515 (`$class->getMethods()`) | auch geerbte Methoden | FAIL für SK1 (Randfall) |

### CI-Läufe (selbst abgefragt)

Alle in den Summaries genannten Läufe per `gh run view` geprüft, alle `completed success`: 80d819f3 (8 Läufe, PHP 41897060856), e0ea3179 (8 Läufe, PHP 41905206023), a0cb12c5 (8 Läufe, PHP 41909998607, plus 4 Dependabot-Läufe 41910010415, 41910010567, 41910011173, 41910011569). Der wöchentliche Lauf von php.yml ist noch nicht angefallen (erster Montag nach dem Commit).

### Produktcode und Version

`git diff --stat 2b7d4962 HEAD -- php/lib php/appinfo php/templates php/js php/css php/l10n php/composer.json php/composer.lock backend/src backend/appinfo CHANGELOG.md`: leer. Kein Tag seit 2b7d4962. Geändert sind nur Tests, Workflows, dependabot.yml, Doku, Skript und Planung. Alle sechs Commits seit 2b7d4962 von street1983nk.

### Anti-Pattern

| Datei | Zeile | Muster | Schwere | Wirkung |
|---|---|---|---|---|
| keine | | TBD/FIXME/XXX in den geänderten Dateien | | keine Funde |
| scripts/dev/phpunit_docker.sh | RUNTIME_IMAGE | lokal PHP 8.3 (nextcloud:32.0.15-apache), CI PHP 8.2 | Info | dokumentiert in docs/testing.md; ein 8.3-only-Konstrukt fiele lokal nicht auf, aber in CI und `php -l` |

### Menschliche Prüfung

1. **Lokales PHPUnit-Rezept:** `bash scripts/dev/phpunit_docker.sh` und `bash scripts/dev/phpunit_docker.sh --filter RouteSecurity`. Erwartet: 973 Tests, `floor 28`, rc 0; gefiltert 15 Tests mit dem Hinweis auf die übersprungene Untergrenze. Grund: Docker war für diese Prüfung ausgeschlossen.

### Zusammenfassung der Lücke

Kriterien 2 und 4 sind im Code und in CI belegt, nicht nur in den Summaries. Kriterium 1 hält für alles, was als PHP-Attribut geschrieben ist, und ist dort sauber mit Negativtests auf Fixtures und auf dem echten Baum abgesichert. Das Phasenziel "keine Route versehentlich öffentlich oder ohne CSRF" hat aber einen offenen Seiteneingang: Nextcloud stable34 akzeptiert `@PublicPage` und `@NoCSRFRequired` weiterhin als Docblock-Annotation, und weder RouteSecurityTest noch test_php_trust_boundary.py sehen sie. Heute steht keine solche Annotation unter php/lib (grep leer), es gibt also keine aktuelle Exposition, nur eine Lücke im Gate. Daneben überspringt der Leser geerbte Routenmethoden, die der Router registriert. Beides hat dieselbe Wurzel (der Leser liest weniger als der Server auswertet) und lässt sich in einem kleinen Folgeplan schließen, Schritte stehen im Frontmatter unter `gaps.missing`.

---

_Verifiziert: 2026-11-04T21:24:00Z_
_Verifier: Claude (gsd-verifier)_
