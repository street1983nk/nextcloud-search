# PHP-Qualitäts- und Sicherheits-Gates für unsere Nextcloud-Projekte

Stand: 04.11.2026. Kennzeichnung: **[geprüft]** = heute an Primärquelle oder im Repo nachgesehen, **[Annahme]** = Fachwissen bzw. Schluss, nicht heute belegt.

## 1. Kurzfazit

- Nur Findling hat PHP-Code (php/, 7 Controller). Connector und Gameworld sind reine Python-Projekte ohne eigenen PHP-Code **[geprüft]**. Alle PHP-Gates betreffen also vorerst nur Findling.
- CodeQL kann kein PHP **[geprüft]**. Das PHP-Gegenstück zu ruff+pyright+vulture ist: Psalm (inkl. Taint) + php-cs-fixer mit nextcloud/coding-standard + composer audit, optional PHPStan.
- Nextcloud selbst setzt auf Psalm (Level 4, eigene Plugins, separater Taint-Job mit SARIF-Upload) **[geprüft]**; App-Vorlagen gibt es für psalm, psalm-matrix, phpstan, lint-php-cs, rector-apply, openapi, phpunit-* **[geprüft]**.

### Top 5 für Findling (Nutzen/Aufwand)

1. **Routen-Attribut-Gate (eigenes Skript, ca. 50 Zeilen PHP oder Python)**: jede Controller-Methode mit Route muss ein explizites Sicherheitsprofil haben (Allowlist-Datei: Methode -> erwartete Attribute). Verhindert versehentliches #[PublicPage]/#[NoCSRFRequired]/#[NoAdminRequired]. Höchster Sicherheitsnutzen, kein Fremdtool, kein Datenabfluss.
2. **Psalm mit nextcloud/ocp + `--taint-analysis`**: Typfehler gegen die OCP-API je NC-Version (33/34/35 als Matrix) und XSS/SQLi/SSRF-Pfade (Proxy zur ExApp!). Aufwand mittel (Baseline), Lärm anfangs mittel.
3. **composer validate --strict + composer audit** (plus Dependabot-Eintrag `composer` für php/): Minuten Aufwand, fast kein Lärm. Heute fehlt composer in dependabot.yml **[geprüft]**.
4. **php-cs-fixer mit nextcloud/coding-standard** im Prüfmodus (`--dry-run --diff`): Store-/Review-Konformität, Aufwand gering, einmaliger Formatierungs-Commit.
5. **zizmor + actionlint** über alle Workflows (auch php.yml): findet Template-Injection, fehlendes `persist-credentials: false` (heute nur in 1 Workflow gesetzt **[geprüft]**), zu breite Rechte. Aufwand gering, Vorteil für alle drei Repos.

Danach: PHPStan (nur wenn Psalm zu wenig fängt), Infection (erst wenn Suite größer), Rector (einmalig, nicht als Gate). Semgrep nur lokal/CLI ohne Login. Snyk und Ähnliche: nicht empfohlen (Code-Upload).

## 2. Ist-Stand je Projekt [geprüft]

### Findling (C:\Users\Student\nextcloud-search)
- PHP: php/lib mit AppInfo, BackgroundJobs, Command, Controller (Gateway, Page, Profile, ProfileSettings, Queue, Reconcile, Settings), Db, Listener, Migration, Repair, Search, Service, Settings, Text. Routen ausschließlich per Attribut (routes.php leer).
- Attribut-Lage: ExApp-Endpunkte tragen `#[ExAppRequired]` + `#[NoCSRFRequired]` + `#[ApiRoute]`; PageController `#[NoAdminRequired]` + `#[NoCSRFRequired]` (GET /); ProfileSettingsController-Routen ohne Ausnahme-Attribute, also Admin + CSRF per Default. Gutes Muster, aber nichts verhindert per Gate, dass es kippt.
- php.yml: `php -l` (PHP 8.2), info.xml gegen Store-Schema (gepinnter appstore-SHA), PHPUnit 11.5.56 gegen server stable34 mit Mindest-Testanzahl 28 aus JUnit. `permissions: contents: read`, Timeouts, SHA-Pins vorhanden.
- security.yml: CodeQL nur Python, REUSE-Lint, pip-audit. Kein PHP-Scanner.
- composer.json: nur phpunit als require-dev, Lockfile committed, `--no-scripts` im Install. Kein composer audit/validate.
- dependabot.yml: github-actions, docker, uv. **composer fehlt.**
- Kein zizmor/actionlint/harden-runner in irgendeinem der drei Repos.

### MCP-Connector (C:\Users\Student\nextcloud-mcp-connector)
- Keine .php-Dateien. Python-ExApp (pyproject, uv.lock). Workflows: ci, issue-notify, release, scorecard, security. PHP-Gates nicht anwendbar; nur Abschnitt 7 (Actions-Härtung) relevant.

### Gameworld (C:\Users\Student\gameworld)
- Keine eigenen .php-Dateien (ein vendor/games-Ordner ohne PHP). Workflows: image.yml, luanti-wasm.yml, SHA-gepinnt. PHP-Gates nicht anwendbar; Abschnitt 7 relevant. Falls später eine PHP-Companion-App wie bei Findling entsteht, gilt der Findling-Aufbau 1:1.

## 3. Bewertung je Werkzeug

### 3.1 Psalm
- Version 7.0.2 (03.11.2026), MIT **[geprüft, Packagist]**. Aktiv entwickelt.
- Findet: Typfehler, falsche OCP-Nutzung, tote Pfade, mit `--taint-analysis` Datenflüsse von Request-Eingaben zu HTML-Ausgabe (XSS), SQL (SQLi), HTTP-Client-URLs (SSRF), Shell, Dateipfaden.
- Nextcloud-Bezug: server/psalm.xml `errorLevel="4"` mit Plugins AppFrameworkTainter, AttributeNamedParameters, UnstrictComparisonChecker, InArrayStrictChecker u. a. **[geprüft]**. Server fährt einen eigenen Job "Psalm taint analysis" (`composer run psalm:security`), wertet SARIF selbst aus, weil Psalm bei Report-Datei mit 0 endet, und lädt SARIF per upload-sarif hoch **[geprüft]**. Wichtig für uns: diese Exit-Code-Falle übernehmen.
- AppFrameworkTainter markiert laut Name die AppFramework-Request-Parameter als Taint-Quellen **[Annahme, Datei nicht vollständig gelesen]**; für Apps nicht als Paket verfügbar, müsste ggf. kopiert werden (AGPL, passt zu Findling-Lizenz).
- Vorlage psalm-matrix.yml: ermittelt min. PHP und NC-Versionen aus info.xml, `composer require --dev nextcloud/ocp:<ver>`, prüft `phpVersion` in psalm.xml **[geprüft]**. nextcloud/ocp v35.0.2, AGPL **[geprüft]**.
- Aufwand: mittel (psalm.xml, Baseline, Stubs für OCA\AppAPI). Lärm: anfangs mittel, mit Baseline beherrschbar. Datenabfluss: keiner (läuft im Runner; SARIF-Upload geht nur an GitHub).

### 3.2 PHPStan
- 2.3.5 (03.11.2026), MIT; phpstan-strict-rules 2.1.1, MIT **[geprüft]**. Level 0 bis 10, Bleeding Edge über `includes: vendor/phpstan/phpstan/conf/bleedingEdge.neon` **[Annahme, Fachwissen]**.
- Findet: Typ- und Logikfehler, oft strenger und schneller als Psalm; **keine Taint-Analyse** im Kern **[Annahme]**.
- Nextcloud bietet eine phpstan.yml-Vorlage **[geprüft]**, der Server selbst nutzt Psalm.
- Empfehlung: **Psalm zuerst** (Nextcloud-Standard, Taint). PHPStan nur zusätzlich, wenn man Level 8+ als ruff/pyright-Gegenstück will; beides parallel kostet doppelte Baseline-Pflege.

### 3.3 php-cs-fixer + nextcloud/coding-standard
- php-cs-fixer v3.95.27, MIT; nextcloud/coding-standard v1.5.0, MIT **[geprüft]**. Vorlage lint-php-cs.yml **[geprüft]**.
- Findet: Stil, nicht Sicherheit. Gering Aufwand, null Lärm nach Erstformatierung.

### 3.4 Rector
- rector/rector 2.8.4, MIT **[geprüft]**; Vorlage rector-apply.yml (wendet an, erzeugt PR) **[geprüft]**.
- Sicherheitsnutzen indirekt: `declare(strict_types=1)`, strikte Vergleiche/`in_array(..., true)`, Typdeklarationen, Annotation-zu-Attribut-Umstellung **[Annahme, Regelnamen nicht einzeln geprüft]**. Als Gate nur `--dry-run`; besser einmalig anwenden.

### 3.5 Composer-Lieferkette
- Composer 2.11.1 (30.10.2026) **[geprüft]**. `composer validate --strict` (Schema, Lock passt zu json), `composer audit --locked` (Packagist-Advisory-DB, GitHub-Advisories) **[Annahme zur Datenquelle]**. Neuere Composer-Versionen blockieren unsichere Pakete bei update (`audit.block-insecure`) **[Annahme]**.
- roave/security-advisories (nur dev-latest, kein Release) **[geprüft]**: Konflikt-Paket, verhindert Installation bekannter verwundbarer Versionen. Neben composer audit redundant; nur sinnvoll, wenn man auch lokal ohne audit installiert.
- Dependabot `package-ecosystem: composer`, `directory: /php` ergänzen.
- Findling hat nur require-dev; Laufzeit-Risiko gering, CI-Risiko (Code im Runner) real.

### 3.6 Sicherheitsscanner
- **CodeQL**: PHP nicht unterstützt (Liste: C/C++, C#, Actions, Go, Java, Kotlin, JS/TS, Python, Ruby, Rust, Swift) **[geprüft]**. Aber: CodeQL-Sprache `actions` für Workflows lohnt sich zusätzlich.
- **Semgrep**: CLI v1.183.0 (29.10.2026) **[geprüft]**; Engine LGPL-2.1 **[Annahme]**; Community-Regeln unter "Semgrep Rules License v1.0" **[geprüft]** (keine OSI-Lizenz, Nutzung erlaubt, Weitervertrieb/Angebot als Dienst eingeschränkt). Ohne `semgrep login` laufen Regeln lokal, Code verlässt den Runner nicht **[Annahme]**; mit AppSec Platform/`semgrep ci` gehen Befunde an semgrep.dev. Nutzen für PHP: generische Muster (eval, unserialize, shell_exec), kein Nextcloud-Wissen. Lärm mittel. Einstufung: optional.
- **Snyk / SonarCloud / DeepSource**: verlangen Code- oder Analyse-Upload an Dritte. Für das Produkt irrelevant (läuft nicht auf dem Server), für CI trotzdem kritisch: Quellcode und Befunde liegen beim Anbieter, Token im Repo. Nicht empfohlen.

### 3.7 Tests als Gate
- Mindest-Testanzahl: bereits umgesetzt (28 aus JUnit), gutes Muster.
- Infection 0.35.9, BSD-3-Clause **[geprüft]**: Mutationstests, braucht Coverage-Treiber (pcov/xdebug), läuft im Server-Autoload-Raum; Aufwand mittel, Laufzeit hoch. Empfehlung: erst manuell/nightly mit `--min-msi` als Information, nicht als PR-Gate.
- Coverage-Schranke: eher nein. Bei Mock-Suite mit wenigen Klassen erzeugt eine Prozentschranke Druck auf Alibi-Tests; Mindestanzahl + Integration-Jobs sind aussagekräftiger.

### 3.8 Nextcloud-spezifische Prüfungen
- Attribute (OCP\AppFramework\Http\Attribute): NoCSRFRequired, PublicPage, NoAdminRequired, AuthorizedAdminSetting, SubAdminRequired, PasswordConfirmationRequired, UserRateLimit, AnonRateLimit, BruteForceProtection, ExAppRequired, ApiRoute, FrontpageRoute **[geprüft für die in Findling genutzten; Rest Annahme]**.
- Kein fertiges Tool, das Routen-Sicherheit prüft **[Annahme, nichts gefunden]**. Vorschlag: eigenes Gate.
  - Per Reflection (PHP im CI-Job nach composer install) alle public Methoden in lib/Controller mit ApiRoute/FrontpageRoute/OCSRoute sammeln.
  - Gegen eine committete Datei `php/tests/route-security.json` vergleichen (Methode -> erwartete Attributmenge). Abweichung = rot. Jede neue Route erzwingt eine bewusste Eintragung im Review.
  - Zusatzregeln: `NoCSRFRequired` nur mit `ExAppRequired` oder auf GET; `PublicPage` nur mit `AnonRateLimit`/`BruteForceProtection`; Mutationen (POST/DELETE) ohne `ExAppRequired` dürfen kein NoCSRFRequired haben.
  - Alternative: Psalm-Plugin (gleiche Logik, aufwändiger). Ein PHPUnit-Test mit Reflection ist am billigsten und läuft im vorhandenen Job.
- Code-Signing: `occ integrity:check-app findling` gegen das gebaute Release-Archiv in einer Testinstanz; sinnvoll im release.yml nach dem Signieren, prüft dass keine Datei fehlt/zuviel ist **[Annahme zur genauen Ausgabe]**. Für unsignierte Dev-Builds nicht anwendbar.
- openapi-extractor v1.9.1, AGPL **[geprüft]**: erzeugt openapi.json aus Controllern; Diff-Gate macht API-Änderungen sichtbar. Optional.

### 3.9 GitHub-Actions-Härtung
- SHA-Pins: vorhanden **[geprüft]**.
- zizmor v1.32.0 (02.11.2026), MIT **[geprüft Version; Lizenz Annahme]**: statische Workflow-Audits (Template-Injection, artipacked/persist-credentials, excessive-permissions, unpinned-uses, cache-poisoning). Offline-Modus ohne Token möglich. Hoher Nutzen, null Datenabfluss.
- actionlint v1.7.12 (30.03.2026), MIT **[geprüft Version; Lizenz Annahme]**: Syntax/Expression/shellcheck in run-Blöcken.
- harden-runner v2.22.3 (27.10.2026), Apache-2.0 **[geprüft Version; Lizenz Annahme]**: Egress-Überwachung/Blockade. Achtung Datenabfluss: im Audit-Modus gehen Netzwerk-Telemetrie an StepSecurity (Dashboard) **[Annahme]**; für php.yml interessant, weil composer und GitHub-Klone Netz brauchen, `egress-policy: block` mit Allowlist (github.com, packagist, raw.githubusercontent.com). Kritisch abwägen.
- `persist-credentials: false` an jedem checkout (heute nur 1 Workflow) **[geprüft]**.

## 4. Vorschlag Job-Aufbau php.yml

- **lint** (bleibt): php -l auf 8.2; zusätzlich Matrix 8.2/8.4 für Vorwärts-Syntax.
- **composer-hygiene** (neu, ca. 30 s): setup-php, `composer validate --strict --no-check-publish`, `composer install --no-scripts`, `composer audit --locked`.
- **cs** (neu): php-cs-fixer mit nextcloud/coding-standard, `--dry-run --diff`.
- **psalm** (neu, Matrix nextcloud/ocp 33/34/35 nach Vorlage psalm-matrix): psalm.xml mit `phpVersion="8.2"`, errorLevel zunächst 4 wie Server, später schärfen; Baseline committen; Stubs für AppAPI.
- **psalm-taint** (neu): `psalm --taint-analysis --report=results.sarif`, danach SARIF zählen und bei >0 rot (Exit-Code-Falle wie im Server), upload-sarif mit `security-events: write` nur in diesem Job.
- **phpunit** (bleibt): Server stable34, Mindestanzahl; neu: Routen-Sicherheitstest per Reflection gegen route-security.json als Teil der Suite.
- **app-metadata** (bleibt).
- Querschnitt: `persist-credentials: false` an allen checkouts; jobweise permissions; zizmor + actionlint als eigener Job in security.yml für alle Workflows; dependabot composer für /php.
- Später/optional: PHPStan Level 6+ mit strict-rules; Infection nightly; integrity:check-app in release.yml; openapi-Diff.
- Lokal (kein PHP): alle Gates über `docker run --rm -v ...:/app composer:2` bzw. ein php:8.2-cli-Image ausführbar; sonst nur CI.

## 5. Quellen

- CodeQL Sprachen: https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/
- Nextcloud Workflow-Vorlagen: https://github.com/nextcloud/.github/tree/master/workflow-templates
- psalm-matrix Vorlage: https://raw.githubusercontent.com/nextcloud/.github/master/workflow-templates/psalm-matrix.yml
- Server psalm.xml: https://github.com/nextcloud/server/blob/master/psalm.xml
- Server Psalm-/Taint-Workflow: https://github.com/nextcloud/server/blob/master/.github/workflows/static-code-analysis.yml
- Packagist (Versionen/Lizenzen): https://packagist.org/packages/vimeo/psalm, /phpstan/phpstan, /phpstan/phpstan-strict-rules, /friendsofphp/php-cs-fixer, /rector/rector, /infection/infection, /nextcloud/coding-standard, /nextcloud/ocp, /roave/security-advisories, /nextcloud/openapi-extractor
- Composer Releases: https://github.com/composer/composer/releases
- Semgrep: https://github.com/semgrep/semgrep/releases, Regel-Lizenz https://semgrep.dev/legal/rules-license
- zizmor: https://github.com/zizmorcore/zizmor
- actionlint: https://github.com/rhysd/actionlint
- harden-runner: https://github.com/step-security/harden-runner
- Lokale Repos: nextcloud-search/.github/workflows/php.yml, security.yml, .github/dependabot.yml, php/composer.json, php/lib/Controller/*
