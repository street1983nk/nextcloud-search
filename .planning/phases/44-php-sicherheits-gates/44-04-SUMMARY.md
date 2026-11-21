---
phase: 44-php-sicherheits-gates
plan: 04
subsystem: ci-sicherheits-gates
tags: [php-cs-fixer, coding-standard, stil-gate, positivkontrolle, php-yml]
requires:
  - "44-03 (scripts/dev/php_gates_docker.sh)"
  - "44-OWNER-DECISIONS.md E-07"
provides:
  - "Tool-Projekt php/tools/php-cs-fixer (coding-standard v1.5.0, shim v3.95.29, custom-fixers v3.37.4), gelockt und auditiert"
  - "php/.php-cs-fixer.dist.php ohne eigene Regeln"
  - "scripts/ci/php_cs_gate.sh mit dry-run und Positivkontrolle"
  - "Job php-cs in php.yml, composer-hygiene um php-cs-fixer-Tools ergänzt"
  - "php_gates_docker.sh Unterbefehle cs und all (psalm, dann cs)"
affects: [44-07, 44-08, 44-09, 44-10]
tech-stack:
  added: ["nextcloud/coding-standard v1.5.0, php-cs-fixer/shim v3.95.29, kubawerlos/php-cs-fixer-custom-fixers v3.37.4 (nur CI/Dev)"]
  patterns: ["Formatierung nur auf LF-Spiegel, Rückkopie nur geänderter Dateien", "Token-Vergleich als Verhaltensbeleg", "Positivkontrolle mit --path-mode=intersection"]
key-files:
  created:
    - php/tools/php-cs-fixer/composer.json
    - php/tools/php-cs-fixer/composer.lock
    - php/.php-cs-fixer.dist.php
    - scripts/ci/php_cs_gate.sh
  modified:
    - php/templates/search.php
    - php/templates/admin.php
    - php/lib/Listener/FileEventListener.php
    - php/lib/Service/AdminViewService.php
    - php/lib/Service/ProbeService.php
    - php/lib/Service/SearchOutcome.php
    - php/tests/RouteSecurity/Fixtures.php
    - php/tests/Unit/ProviderTest.php
    - php/tests/Unit/RouteSecurityTest.php
    - php/tests/Unit/SettingsControllerTest.php
    - php/tests/Unit/Version001603Date20261108000000Test.php
    - scripts/dev/php_gates_docker.sh
    - .github/workflows/php.yml
    - backend/tests/test_workflow_tag_triggers.py
    - backend/tests/test_measurement_scripts.py
    - docs/testing.md
decisions:
  - "Baumhash-Anpassung als eigener Commit direkt nach dem Formatierungs-Commit, damit dieser nur Pfade unter php/ nennt"
  - "Lokaler Stil-Gate-Lauf vollständig in php:8.2-cli (kein jq nötig), Psalm-Gate bleibt bei Host-jq per Shim (E-09)"
metrics:
  duration: "ca. 110 min"
  completed: 2026-11-21
  tasks: 2
  files: 20
---

# Phase 44 Plan 04: Stil-Gate php-cs-fixer Summary

php-cs-fixer mit nextcloud/coding-standard v1.5.0 als dry-run-Job php-cs mit Positivkontrolle; der Baum ist nach einem reinen Formatierungs-Commit (11 Dateien, Verhalten belegt unverändert) stilgrün, lokal über `php_gates_docker.sh cs` auf einem LF-Spiegel.

## Task 1: Tool-Projekt, Konfiguration, Formatierungs-Commit

- composer.lock per composer:2 (Digest 50ea4d33): kubawerlos/php-cs-fixer-custom-fixers v3.37.4, nextcloud/coding-standard v1.5.0, php-cs-fixer/shim v3.95.29 (genau E-07). `composer validate --strict --no-check-publish` Exit 0, `composer audit --locked` Exit 0 (keine Advisories). Erzeugt im Spiegel, kein vendor im Repo.
- php/.php-cs-fixer.dist.php: `Nextcloud\CodingStandard\Config`, Finder lib, appinfo, templates, tests, kein `setRules`.
- Docblocks vorab (nur Kommentar): SearchOutcome.php, Beschreibung von `$excerpts` als Absatz über die @param-Zeilen; AdminViewService.php, die drei @param-Zeilen `$scan`, `$backend`, `$indexable` aus der Mitte des Prosablocks zu den übrigen @param-Zeilen verschoben (vorher hing der ``recounting``-Absatz als Fortsetzung an `$indexable`).
- Erster dry-run auf dem LF-Spiegel (php:8.2-cli, Digest 842748bc): Exit 8, **11 Dateien, genau die aus RESEARCH**: FileEventListener.php, SearchOutcome.php, ProbeService.php, Version001603Date20261108000000Test.php, AdminViewService.php, templates/admin.php, templates/search.php, RouteSecurity/Fixtures.php, ProviderTest.php, RouteSecurityTest.php, SettingsControllerTest.php. Nach den Docblock-Anpassungen meldet fix 9 Dateien (die zwei Docblock-Dateien sind sauber). Regeln: Einrückung der Templates, Importreihenfolge (FileEventListener, Fixtures, RouteSecurityTest, Version001603…Test), ein Anführungszeichen (ProviderTest), Leerzeilen nach `return` im switch (ProbeService) und doppelte Leerzeile (SettingsControllerTest). Alles reine Stilregeln.
- Zweiter dry-run: Exit 0, "Found 0 of 130 files" (idempotent).
- Fixtures.php: Diff nur Importreihenfolge (UseSession hinter UserRateLimit), Docblocks unverändert.

Verhaltensbeleg (D-08):

| Prüfung | Ergebnis |
|---------|----------|
| Token-Vergleich templates/search.php | T_INLINE_HTML/T_CLOSE_TAG 391 Tokens **identical** (samt Text), Code-Tokens 2908 identisch, Gesamt 4141 -> 4141 |
| Token-Vergleich templates/admin.php | T_INLINE_HTML/T_CLOSE_TAG 823 Tokens **identical** (samt Text), Code-Tokens 9221 identisch, Gesamt 13242 -> 13236 (nur Whitespace) |
| Code-Tokens (ohne Whitespace/Kommentare) übrige Dateien | identisch: ProbeService, SettingsControllerTest, SearchOutcome, AdminViewService (auch gegen HEAD); verschieden nur Importreihenfolge (4 Dateien) und das Anführungszeichen in ProviderTest |
| php -l (lib, appinfo, templates, tests) | 130 Dateien, 0 Fehler |
| PHPUnit vorher (Stand 8f5aca31) | OK (1222 tests, 7765 assertions) |
| PHPUnit nachher | OK (1222 tests, 7765 assertions), rc 0 |
| git show --stat (Commit 1) | nur php/lib, php/templates, php/tests, php/tools/php-cs-fixer, php/.php-cs-fixer.dist.php |

- Commit **fa1836f5** `style(44-04): PHP-Quellen nach nextcloud/coding-standard formatiert, ohne Verhaltensänderung`.
- Commit **fb231ba1** `test(44-04): Baumhash der PHP-Hälfte nach dem Formatierungs-Commit`: PHP_FILES_TODAY 133, PHP_TREE_HASH_TODAY 033cb708. Gegenprobe mit unabhängiger Pipeline (find, sort, sed, sha256sum): 033cb708; Positivkontrolle Rezept über git archive von def59579: ab283cdd mit 132 Dateien (alter Wert).
- Index-Zeilenenden: `git ls-files --eol` i/lf für die formatierten Dateien.

## Task 2: Gate, Job, Rezept

- scripts/ci/php_cs_gate.sh: echter Lauf `fix --dry-run --diff --using-cache=no --show-progress=none` mit `set +e`, 0 grün, 8 rot mit Diff, sonst "php-cs-fixer failed to run (exit N)"; danach Positivkontrolle `lib/CsProbe.php` (SPDX-Kopf, `if(true){echo 1;}`), `--path-mode=intersection`, muss Exit 8 geben, sonst "the style gate is blind"; trap entfernt nur Selbstangelegtes, verweigert eine schon vorhandene Probe. Kriterien: `--dry-run` 2, `--path-mode=intersection` 1, `|| true`/`continue-on-error` 0.
- php.yml: Job `php-cs` (ubuntu-24.04, timeout 10, checkout-Pin mit `persist-credentials: false`, setup-php-Pin 8.2, composer install in php/tools/php-cs-fixer, `bash scripts/ci/php_cs_gate.sh`), composer-hygiene um validate/audit für php/tools/php-cs-fixer ergänzt, paths (push und pull_request) um scripts/ci/php_cs_gate.sh; PATHS_BEFORE mit Kommentar "Added with the job php-cs (phase 44)". Zählungen: "bash scripts/ci/php_cs_gate.sh" 1, "scripts/ci/php_cs_gate.sh" 3, "working-directory: php/tools/php-cs-fixer" 3.
- php_gates_docker.sh: Unterbefehl `cs` (Spiegel, composer install, php:8.2-cli `bash scripts/ci/php_cs_gate.sh`), `all` = psalm, dann cs.
- `bash scripts/dev/php_gates_docker.sh cs`: Exit 0, "Found 0 of 130 files", "php cs gate: 0 violations, probe seen".
- `bash scripts/dev/php_gates_docker.sh all`: Exit 0; psalm dreimal "taint findings: 0" und "probe found 3" (v33.0.9, v34.0.6, v35.0.3), danach cs "php cs gate: 0 violations, probe seen".

Lokaler Rot-Beweis (Kopien des cs-Spiegels im Scratchpad, danach gelöscht):

| Fall | Änderung | Exit | Meldung |
|------|----------|------|---------|
| a | lib/Settings/Section.php Z. 59 mit Leerzeichen statt Tabs eingerückt | 1 | Diff "-        return 75; / +\t\treturn 75;", "Found 1 of 130 files", "php cs gate: files break nextcloud/coding-standard (diff above); ..." |
| b | `__DIR__ . '/lib'` aus dem Finder der Kopie entfernt | 1 | echter Lauf "Found 0 of 61 files", dann "php cs gate: the style gate is blind: php-cs-fixer gave exit 0 on lib/CsProbe.php, expected 8" |

Erster Versuch für a mit `return 75 ;` (Leerzeichen vor Semikolon) blieb grün: coding-standard v1.5.0 enthält keine Regel dafür. Kein Gate-Fehler, nur ein Verstoß außerhalb des Regelsatzes; Fall a deshalb mit falscher Einrückung.

- pytest test_workflow_pins, test_workflow_tag_triggers, test_workflow_size, test_workflow_contexts, test_php_supply_chain_gates, test_php_surface_bans, test_public_artifacts, test_php_route_gate_presence, test_measurement_scripts: 814 passed. Volle Backend-Suite nach beiden Änderungen: 7167 passed, 303 skipped.
- shellcheck 0.11.0 `--severity=style` über php_cs_gate.sh und php_gates_docker.sh: 0 Befunde. actionlint 1.7.12 über php.yml: nur die zwei bekannten SC2016 der `php -r`-Blöcke (jetzt Z. 538 und 572, Umbau in 44-06), keiner im Job php-cs. zizmor 1.32.0 `--persona auditor --min-severity medium` über php.yml: die 5 bekannten artipacked (Z. 102, 145, 460, 467, 627, Behebung 44-05), keiner im Job php-cs.
- `git ls-files php/lib | grep -c CsProbe`: 0.
- Commit **1983d958** `ci(44-04): php-cs-fixer mit nextcloud/coding-standard als dry-run-Gate`, kein Push.

## Deviations from Plan

**1. [Rule 1 - Bug] CR-Entfernung im Spiegel von 44-03 griff nicht**
- **Found during:** Task 1 (erster dry-run meldete 75 Dateien, alle mit ganzem Dateiinhalt als Diff)
- **Issue:** `grep -rlI $'\r'` in Git for Windows entfernt das CR vor dem Vergleich und findet nie eine CRLF-Datei; der Spiegel blieb CRLF. Für Psalm folgenlos, für den Stil-Gate (Regel line_ending) falsch rot.
- **Fix:** `grep -rlUI` (-U behält das CR; auf Linux ohne Wirkung), mit Kommentar. Danach 0 CR-Dateien im Spiegel und genau die 11 Dateien aus RESEARCH.
- **Files modified:** scripts/dev/php_gates_docker.sh
- **Commit:** 1983d958

**2. Baumhash in eigenem Commit**
Plan nennt für Commit 1 nur Pfade unter php/; die neue .php-cs-fixer.dist.php ändert aber Zahl und Hash im Messtest. Anpassung deshalb im direkt folgenden Commit fb231ba1, mit Gegenprobe wie in 44-02.

**3. docs/testing.md im Gate-Commit**
Abschnitt aus 44-03 um `cs` und die LF-Pflicht des Stil-Gates ergänzt (Plan nannte die Datei nicht).

**4. SPDX-Kopf**
Der Plan sagt "SPDX-Kopf wie andere PHP-Dateien der App"; die App-Dateien tragen keinen. .php-cs-fixer.dist.php und die Probe tragen trotzdem einen AGPL-3.0-or-later-Kopf wie vom Plan verlangt.

## Threat Flags

Keine neue Oberfläche: Job php-cs mit `contents: read` (Workflow-Ebene), keine Secrets, kein Schreiben.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: php/tools/php-cs-fixer/composer.json, composer.lock, php/.php-cs-fixer.dist.php, scripts/ci/php_cs_gate.sh
- FOUND: fa1836f5, fb231ba1, 1983d958
