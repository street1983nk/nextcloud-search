# Phase 44: PHP-Sicherheits-Gates - Research

**Researched:** 21.11.2026
**Domain:** Statische Analyse PHP (Psalm-Taint, php-cs-fixer) und GitHub-Actions-Härtung (zizmor, actionlint)
**Confidence:** HIGH (alle vier Werkzeuge heute lokal gegen den echten Baum gelaufen, Versionen an Packagist/PyPI/GitHub geprüft)

Kennzeichnung: **[geprüft]** = heute an Primärquelle, per Lauf oder im Repo belegt; **[zitiert: URL]** = offizielle Doku; **[Annahme]** = Fachwissen oder Schluss, heute nicht belegt.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
#### Gates
- D-01: Psalm mit Taint-Analyse läuft in CI als Matrix gegen nextcloud/ocp 33, 34 und 35. Der Job zählt die Befunde selbst aus der SARIF-Ausgabe und wird bei mindestens einem offenen Befund rot, weil Psalm mit Report-Datei sonst mit 0 endet (PRUEF-02).
- D-02: php-cs-fixer mit nextcloud/coding-standard läuft in CI als dry-run (`--dry-run --diff`) und ist auf dem Phasenkopf grün (PRUEF-03).
- D-03: zizmor und actionlint prüfen jeden Workflow unter .github/workflows in CI; ein neuer Befund ab Medium macht den Job rot (PRUEF-04).
- D-04: Jedes neue Gate braucht einen Negativtest bzw. eine Positivkontrolle: das Gate muss nachweislich rot werden (eingebaute Taint-Strecke, Stilverstoß, Workflow-Befund ab Medium), danach zurückgesetzt.
- D-05: Alle neuen Gates laufen auch lokal grün; das lokale Rezept ist dokumentiert. Ein Strukturgate verhindert das stille Entfernen der Gates aus den Workflows (Muster wie die Gate-Präsenz-Tests aus Phase 42).

#### Befunde
- D-06: Security hat höchste Priorität. Befunde werden bevorzugt echt behoben. Akzeptieren (Baseline, Suppression, zizmor-Ignore) nur mit dokumentierter Owner-Entscheidung; dafür steht im Plan ein Checkpoint (autonomous: false), keine Annahme durch den Executor.
- D-07: Keine Änderung des Produktverhaltens außer echten Sicherheitsfixes. Jede Codeänderung an der PHP-App (php/lib, php/appinfo) bekommt einen Test.
- D-08: Der einmalige Formatierungs-Commit durch php-cs-fixer ist reine Stiländerung ohne Verhaltensänderung und wird durch die vorhandene PHPUnit-Suite abgesichert.

#### Arbeitsregeln
- D-09: Commits nur als street1983nk <k.cherif@outlook.de> (`git -c user.name=street1983nk -c user.email=k.cherif@outlook.de commit`), ohne Claude- oder Session-Trailer, ohne closes/fixes #N. `gsd-sdk query commit` wird nicht verwendet.
- D-10: Push nur nach Owner-Frage: jeder Plan, der CI-Läufe auf GitHub braucht, enthält vor dem Push einen Checkpoint.
- D-11: Kein `python -c` und kein `python -` (Skripte als Dateien). Docker strikt seriell, fremde Container nie anfassen.
- D-12: Texte (Doku, Kommentare in Prosa, Commit-Texte) auf Deutsch mit echten Umlauten, keine Gedankenstriche U+2013/U+2014, keine Emojis. Vor jedem Commit auf Gedankenstriche prüfen.
- D-13: secure-phase schließt die Phase ohne offene Threats.

### Claude's Discretion
- Wahl der genauen Werkzeugversionen (gepinnt, mindestens zwei Wochen alt), Psalm-Level, Plugin-Auswahl, Stubs für OCA\AppAPI, Aufteilung in Jobs und Workflows, Form des SARIF-Zählers (Skriptdatei, jq oder PHP), Ort der Doku.

### Deferred Ideas (OUT OF SCOPE)
- PHPStan, Rector, Infection (laut Recherche 42 erst bei Bedarf).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRUEF-02 | Psalm mit Taint-Analyse gegen OCP 33, 34, 35; Befunde aus SARIF selbst gezählt; rot bei >=1; zum Abschluss 0 offene Befunde oder Owner-Entscheidung je Befund | Abschnitte "Ist-Befundlage Psalm", "Muster 1 bis 3", Pitfalls 1 bis 5. Ist-Stand: 0 Taint-Befunde gegen v33.0.9, v34.0.6, v35.0.3 [geprüft] |
| PRUEF-03 | php-cs-fixer mit nextcloud/coding-standard als dry-run in CI, grün | Abschnitt "Ist-Befundlage php-cs-fixer", Muster 4, Pitfalls 6 und 7. Ist-Stand: 11 Dateien, nach `fix` idempotent grün, Template-Ausgabe unverändert [geprüft] |
| PRUEF-04 | zizmor und actionlint über alle Workflows; Befunde ab Medium behoben oder begründet akzeptiert | Abschnitte "Ist-Befundlage zizmor/actionlint", Muster 5 und 6, Pitfalls 8 bis 12. Ist-Stand: 55 zizmor-Befunde ab Medium (Repo-Wurzel), 19 actionlint-Befunde (alle shellcheck info/style) [geprüft] |
</phase_requirements>

## Summary

Die Werkzeugkette ist heute vollständig lokal per Docker gegen den echten Baum gelaufen (Kopie in Scratch, Repo unverändert). Ergebnis: **Psalm-Taint ist bereits grün** (0 Befunde gegen alle drei OCP-Versionen, mit dem AppFrameworkTainter-Plugin des Servers und einer AppAPI-Stub-Datei), und die Positivkontrolle beweist, dass dieselbe Konfiguration eine eingebaute Taint-Strecke findet (TaintedHtml über Routenparameter, TaintedSql über `IRequest::getParam`). **php-cs-fixer** meldet 11 Dateien, fast alles Einrückung in den zwei Templates; nach einem `fix` ist der Baum idempotent grün, alle Dateien bestehen `php -l`, und die ausgabewirksamen Tokens der Templates (Inline-HTML, Close-Tags) sind byte-gleich. **zizmor** (Persona regular, Repo-Wurzel) meldet 55 Befunde ab Medium: 49 x `artipacked` (fehlendes `persist-credentials: false`), 4 x `dependabot-cooldown`, 2 x `cache-poisoning` (High) in python.yml; alle drei Arten sind mit kleinen YAML-Änderungen echt behebbar, Fix jeweils lokal bestätigt. **actionlint** meldet 19 Befunde, ausschließlich shellcheck-Hinweise der Stufen info/style; eigene actionlint-Fehler (Expressions, Syntax) gibt es keine.

Zwei Befunde der Recherche ändern die Annahmen aus CONTEXT.md bzw. Phase 42: (1) **Psalm 6.20.10 endet mit `--report` bei Befunden mit Exit-Code 2**, nicht 0 [geprüft]; die Selbstzählung bleibt trotzdem Pflicht (D-01), der Schritt darf aber nicht vor dem Zählen abbrechen und muss einen Absturz (Exit 1, keine SARIF-Datei) als rot werten. (2) **Psalm 7 ist ungeeignet**: 7.0.0 erschien am 02.11.2026 als großer Umbau mit täglichen Releases, und das AppFrameworkTainter-Plugin stürzt darunter ab (`Class "Psalm\Type\TaintKindGroup" not found`) [geprüft]. Der Nextcloud-Server selbst steht auf `vimeo/psalm ^6.20` [geprüft]. Empfehlung: **Psalm 6.20.10**.

Die größten Planungsrisiken liegen nicht in den Werkzeugen, sondern in den bestehenden Repo-Gates: deploy-harp.yml hat nur noch 6010 Byte Luft bis zur 500-KB-Grenze (test_workflow_size.py), `test_workflow_tag_triggers.py` friert die `paths`-Listen von php.yml und python.yml in `PATHS_BEFORE` ein, `test_workflow_pins.py` verlangt eine einzige SHA je Action und `timeout-minutes` an jedem Job, und auf dem Windows-Arbeitsbaum liegen PHP-Dateien mit CRLF, die die Regel `line_ending` von php-cs-fixer lokal rot färben würden.

**Primary recommendation:** Psalm 6.20.10 + AppFrameworkTainter (MIT, aus dem Server kopiert) + eigene AppAPI-Stub mit `@psalm-taint-sink ssrf $route`, in einem eigenen Tool-Composer-Projekt `php/tools/psalm` (nicht in php/composer.json); php-cs-fixer über `php/tools/php-cs-fixer`; zizmor und actionlint als digest-gepinnte Container-Images, CI und lokales Rezept rufen dieselben Skripte unter `scripts/ci/` auf.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Taint-Analyse der PHP-App | CI-Runner (php.yml, Job je OCP-Version) | Lokales Docker-Rezept | Statische Analyse, kein Laufzeitbezug; Ergebnis nur im Runner, SARIF verlässt ihn nicht (außer optionalem Upload an GitHub) |
| SARIF-Auszählung und Rot-Entscheidung | Skriptdatei unter scripts/ci/ | CI-Schritt ruft sie auf | Eine Logik für CI und lokal, kein Inline-Code, der driften kann |
| Stilprüfung PHP | CI-Runner (php.yml) | Lokales Docker-Rezept | Reine Quelltextprüfung |
| Workflow-Audit (zizmor, actionlint) | CI-Runner (eigener Workflow, startet auf .github/**) | Lokales Docker-Rezept | Muss bei jeder Workflow-Änderung laufen, nicht nur bei php/** |
| Strukturgate gegen stilles Entfernen | backend/tests (pytest in python.yml) | Wöchentlicher Lauf | Muster aus test_php_supply_chain_gates.py und test_php_route_gate_presence.py |
| Echte Fixes (persist-credentials, cooldown, cache) | Workflow-/Konfig-Dateien | - | Keine Änderung am Produktcode nötig nach Ist-Lage |

## Standard Stack

Stichtag für "mindestens zwei Wochen alt": Veröffentlichung am oder vor 07.11.2026.

### Core
| Werkzeug | Version | Datum | Zweck | Warum |
|---------|---------|-------|-------|-------|
| vimeo/psalm | **6.20.10** | 07.11.2026 | Taint-Analyse | Server nutzt `^6.20` [geprüft: server/vendor-bin/psalm/composer.json]; AppFrameworkTainter läuft darunter [geprüft]; PHP `~8.1.31 \|\| ~8.2.27 \|\| ~8.3.16 \|\| ~8.4.3 \|\| ~8.5.0` [geprüft Packagist] |
| nextcloud/ocp | **v33.0.9**, **v34.0.6**, **v35.0.3** | 02.09. / 31.10. / 06.11.2026 | API-Definitionen je NC-Version | jeweils neueste Tags, alle >= 14 Tage [geprüft Packagist]. ocp 35.x verlangt PHP `~8.3` [geprüft] |
| AppFrameworkTainter.php | Server master | - | macht öffentliche Controller-Methodenparameter zu Taint-Quellen | MIT (SPDX-Kopf in der Datei) [geprüft]; ohne Plugin wird TaintedHtml über Routenparameter nicht gefunden [geprüft] |
| nextcloud/coding-standard | **v1.5.0** | 19.05.2026 | Nextcloud-Regelwerk | verlangt `php-cs-fixer/shim ^3.17`, `kubawerlos/php-cs-fixer-custom-fixers ^3.22` [geprüft] |
| php-cs-fixer/shim | **v3.95.29** | 06.11.2026 | php-cs-fixer als PHAR-Shim (vom Standard verlangt) | 3.95.30 bis .32 sind jünger als 14 Tage [geprüft] |
| kubawerlos/php-cs-fixer-custom-fixers | **v3.37.4** | 19.09.2026 | Zusatzregeln des Standards | **3.37.5 vom 08.11.2026 ist zu jung** (13 Tage) [geprüft] |
| zizmor | **1.32.0** | 02.11.2026 | Workflow-Sicherheitsaudit | Image `ghcr.io/zizmorcore/zizmor:1.32.0@sha256:3014cc8f68f663935f69b3c3e0e41f5ce102b268d97db13db0f62208747f860d` [geprüft per Pull]; PyPI-Wheel-Hashes ebenfalls verfügbar |
| actionlint | **1.7.12** | 30.03.2026 | Workflow-Syntax/Expressions + shellcheck | Image `rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667` bringt shellcheck 0.11.0 und pyflakes mit [geprüft]; Tarball-SHA256 linux_amd64 `8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8` [geprüft checksums.txt] |

### Supporting (Laufzeit-Images, lokal und CI)
| Image | Digest heute | Zweck |
|-------|--------------|-------|
| composer:2 (Composer 2.11.2, PHP 8.5.13) | `sha256:50ea4d33fdcde1adb0f045547295faa1548b33872e5f789dae5b02ce2fb5de93` | `composer install/require/dump-autoload` lokal |
| php:8.3-cli (PHP 8.3.37) | `sha256:9e2a4e9b1704c05cc469fddbf9b0f0f205e2bb13efd249bbad177289ebdc5c7c` | Psalm lokal (wie CI-Laufzeit 8.3) |
| php:8.2-cli (PHP 8.2.36) | `sha256:842748bc4526d4c3c56501fd314e2d75d1005e8a45b7a40f9768ee820df0a6d6` | php-cs-fixer lokal (App-Untergrenze 8.2) |

In CI bleibt PHP über das schon gepinnte `shivammathur/setup-php@eb7c497e18156a6bbabfef1d3a82760b9eda3962 # 2.40.0` (aktuellste Version [geprüft]); Regel "eine SHA je Action" aus test_workflow_pins.py beachten, also exakt diese SHA wiederverwenden.

### Alternatives Considered
| Statt | Möglich | Abwägung |
|-------|---------|----------|
| Psalm 6.20.10 | Psalm 7.0.5 (06.11.2026) | Tiefere Taint-Analyse (URL/NoSQL/LLM-Senken, Taint standardmäßig an), aber Tainter-Plugin stürzt ab [geprüft], Plugin-API umgebaut, tägliche Releases seit 02.11. Ohne Plugin fand 7.0.5 im Baum ebenfalls 0 Taint-Befunde [geprüft]. Später neu bewerten, wenn der Server umsteigt. |
| Tool-Composer-Projekte unter php/tools | psalm/ocp/cs in php/composer.json require-dev (wie Nextcloud-Vorlage) | Gefahr: `nextcloud/ocp` im App-vendor kollidiert im PHPUnit-Job mit den OCP-Klassen des Server-Checkouts (gleicher Prozess, gleiche Namen) [Annahme, nicht ausprobiert]; außerdem Abhängigkeitskonflikte mit dem exakt gepinnten phpunit 11.5.57. Getrennte Projekte vermeiden beides. |
| Container-Images für zizmor/actionlint | `zizmorcore/zizmor-action@v0.8.1` | Action-Default `advanced-security: true` lädt SARIF hoch und unterdrückt damit die Exit-Codes 11 bis 14 (SARIF-Modus), Default `version: latest` [geprüft action.yml]. Nur mit `advanced-security: false`, `version: 1.32.0` brauchbar; Image ist einfacher und lokal identisch. |
| actionlint-Image | Release-Tarball + `sha256sum -c` + Runner-shellcheck | Runner ubuntu-24.04 hat shellcheck 0.9.0, das Image 0.11.0 [geprüft Runner-Readme]; unterschiedliche shellcheck-Versionen = lokal und CI können auseinanderlaufen. |

**Installation (Vorschlag, Tool-Projekte, Lockfiles committen):**
```bash
# php/tools/psalm/composer.json
#   require-dev: vimeo/psalm 6.20.10, nextcloud/ocp v35.0.3
#   config.platform.php: 8.3.16
# php/tools/php-cs-fixer/composer.json
#   require-dev: nextcloud/coding-standard v1.5.0, php-cs-fixer/shim v3.95.29,
#                kubawerlos/php-cs-fixer-custom-fixers v3.37.4
#   config.platform.php: 8.2.27
composer update --no-interaction --no-scripts   # einmalig, erzeugt composer.lock
```

## Package Legitimacy Audit

slopcheck wurde nicht ausgeführt (Python-Aufrufe laut Owner-Regel nur via uv und Skriptdatei; `pip install` widerspricht der Projektregel "lokales System-Python defekt"). Die Pakete stammen aber ausnahmslos aus Primärquellen (Nextcloud-Server-Repo, Nextcloud-Vorlagen, Herstellerdokumentation) und wurden heute an Packagist/PyPI/GitHub geprüft.

| Paket | Registry | Alter | Quelle | Herkunftsbeleg | slopcheck | Disposition |
|-------|----------|-------|--------|----------------|-----------|-------------|
| vimeo/psalm 6.20.10 | Packagist | Projekt seit 2016, Version 14 Tage | github.com/vimeo/psalm | Server vendor-bin/psalm [geprüft] | nicht gelaufen | Freigabe durch Owner-Checkpoint |
| nextcloud/ocp | Packagist | seit Jahren | github.com/nextcloud-deps/ocp | Nextcloud-Vorlage psalm-matrix.yml [geprüft] | nicht gelaufen | Freigabe durch Owner-Checkpoint |
| nextcloud/coding-standard | Packagist | seit 2021 | github.com/nextcloud/coding-standard | Vorlage lint-php-cs.yml [geprüft] | nicht gelaufen | Freigabe durch Owner-Checkpoint |
| php-cs-fixer/shim | Packagist | | github.com/PHP-CS-Fixer/shim | Pflichtabhängigkeit von coding-standard [geprüft] | nicht gelaufen | Freigabe durch Owner-Checkpoint |
| kubawerlos/php-cs-fixer-custom-fixers | Packagist | | github.com/kubawerlos/php-cs-fixer-custom-fixers | Pflichtabhängigkeit von coding-standard [geprüft] | nicht gelaufen | Freigabe durch Owner-Checkpoint |
| zizmor (Image ghcr.io/zizmorcore/zizmor) | GHCR / PyPI | seit 2024 | github.com/zizmorcore/zizmor | docs.zizmor.sh [zitiert] | nicht gelaufen | Freigabe durch Owner-Checkpoint |
| actionlint (Image rhysd/actionlint) | Docker Hub / GitHub Releases | seit 2021 | github.com/rhysd/actionlint | Releases + checksums.txt [geprüft] | nicht gelaufen | Freigabe durch Owner-Checkpoint |

**Packages removed due to slopcheck [SLOP] verdict:** keine
**Packages flagged as suspicious [SUS]:** keine; mangels slopcheck-Lauf aber alle als [Annahme] im Sinne des Protokolls: der Planner setzt vor der ersten Installation im Repo einen `checkpoint:human-verify` (passt zum bestehenden Muster aus 05-15, wo der Owner phpunit vor dem Abruf freigab).

## Ist-Befundlage (heute gemessen, Repo-Kopie in Scratch)

### Psalm 6.20.10, Taint-Analyse, phpVersion 8.2, Laufzeit PHP 8.3.37 [geprüft]
| OCP | Taint-Befunde | Exit | Laufzeit |
|-----|---------------|------|----------|
| v33.0.9 | 0 | 0 | ca. 27 s |
| v34.0.6 | 0 | 0 | ca. 27 s |
| v35.0.3 | 0 | 0 | ca. 27 s |

- Positivkontrolle (Probe-Controller temporär in lib/): 3 Befunde, Exit 2: `TaintedHtml` + `TaintedTextWithQuotes` (Routenparameter -> `echo`, nur mit Plugin), `TaintedSql` (`$this->request->getParam()` -> `$qb->expr()->eq()`, über OCP-Annotationen auch ohne Plugin).
- Zusatzsenke `@psalm-taint-sink ssrf $route` an `PublicFunctions::exAppRequest` (Stub): 0 Befunde, also erreicht keine Nutzereingabe den Routenpfad zur ExApp. Als Senke auch `$params` markiert: 1 Befund `TaintedSSRF` (ProfileSettingsController::startCheck `$profile` -> ProbeService::start -> ExAppService::adminSend -> proxyRequest -> exAppRequest). Das ist der beabsichtigte Request-Body eines Admin-Endpunkts, kein SSRF; `$params` deshalb **nicht** als Senke markieren.
- Psalm 7.0.5 mit Plugin: Absturz Exit 1, keine SARIF-Datei. Ohne Plugin: 0 Taint-Befunde.
- Nur zur Information (nicht Phasenumfang): eine normale Typprüfung auf Level 4 meldet 410 Fehler und 190 Hinweise, davon 277 `UndefinedFunction` in den Templates (`p()`, `print_unescaped()` fehlen, da nicht in OCP), 47 `UndefinedDocblockClass` in Migrationen, Rest verstreut. Kein Gate in dieser Phase.

### php-cs-fixer 3.95.29 + coding-standard 1.5.0, PHP 8.2.36 [geprüft]
- Finder lib, appinfo, templates, tests: **11 Dateien**, Exit 8. Diff-Zeilen: templates/search.php 300, templates/admin.php 158, Rest 2 bis 8 je Datei (Import-Sortierung in 4 Dateien, ein Anführungszeichen in ProviderTest.php, `phpdoc_align` in SearchOutcome.php und AdminViewService.php).
- Nach `fix`: zweiter dry-run Exit 0 (idempotent), alle Dateien `php -l` sauber, Inline-HTML/Close-Tag-Tokens beider Templates identisch (823 bzw. 391 Tokens).
- Kosmetik: `phpdoc_align` schiebt in SearchOutcome.php (Z. 88 f.) und AdminViewService.php (Z. 2075 ff.) Folgezeilen weit nach rechts; vor dem Formatierungs-Commit diese zwei Docblocks so umstellen, dass das Ergebnis lesbar bleibt.
- tests/RouteSecurity/Fixtures.php: nur Importreihenfolge, keine Docblock-Änderung (wichtig, weil der ControllerMethodReflector diese Docblocks zeilenweise liest).

### zizmor 1.32.0, offline, Persona regular [geprüft]
Eingabe `.` (Repo-Wurzel, erfasst Workflows, `.github/actions/setup-test-nc/action.yml` und `.github/dependabot.yml`), Exit 14:

| Audit | Schwere/Konfidenz | Anzahl | Ort | Behebung |
|-------|-------------------|--------|-----|----------|
| artipacked | Medium/Low | 49 | coverage-e2e 5, deploy-harp 2, docker 1, integration 12, measure 2, php 5, probe-92d 1, python 2, rc-version-proof 4, release 2, resilience 5, security 3, smb-acl-measure 2, store-release-delete 1, store-submit 1, setup-test-nc/action.yml 1 | `persist-credentials: false` am checkout; kein Workflow pusht per git; einzige git-Netzoperation ist `git fetch` eines Tags im öffentlichen Repo (probe-92d.yml Z. 112), braucht keine Zugangsdaten [geprüft grep; Repo öffentlich laut CLAUDE.md] |
| dependabot-cooldown | Medium/High | 4 | dependabot.yml, alle vier Einträge | `cooldown: default-days: N` mit N >= 7 je Eintrag |
| cache-poisoning | High/Low | 2 | python.yml Z. 125 und 247 (setup-uv `enable-cache: true` in einem Workflow mit Release-Tag-Trigger) | `enable-cache: false` beseitigt den Befund [geprüft]; Zeile nur löschen ebenfalls [geprüft], aber setup-uv cacht dann womöglich per Default [Annahme], daher explizit `false` |

- Nur `.github/workflows` als Eingabe: 48 artipacked + 2 cache-poisoning (ohne action.yml und dependabot.yml).
- Unter Persona `auditor` kämen zusätzlich ab Medium: 10 x `secrets-outside-env` (issue-notify, release, store-release-delete, store-submit), 2 x `unpinned-images` High (integration.yml Z. 1101, 1116), 1 x `excessive-permissions` (scorecard.yml `read-all`). Nicht vom Gate verlangt; als Information für den Owner.
- "suppressed" in der zizmor-Zusammenfassung = durch Persona/Mindestschwere ausgeblendete Befunde, keine Ignore-Kommentare (im Repo gibt es weder `zizmor.yml` noch `# zizmor:`-Kommentare) [geprüft].

### actionlint 1.7.12 (Image, shellcheck 0.11.0) [geprüft]
- 19 Befunde, Exit 1, **alle** `[shellcheck]`, Stufen info/style: SC2086 x12 (deploy-harp 7, measure 4, ...), SC2016 x3 (php.yml Z. 399 und 433 sind die absichtlichen `php -r '...'`-Blöcke; integration.yml Z. 3723), SC2012, SC2015, SC2129, SC2329 je 1. Dateien: deploy-harp 9, measure 5, integration 2, php 2, probe-92d 1.
- Mit `SHELLCHECK_OPTS=--severity=warning`: 0 Befunde, Exit 0. Ohne shellcheck (`-shellcheck=`): 0 Befunde. Es gibt also keinen einzigen Expression-, Syntax- oder Typfehler.

## Architecture Patterns

### System Architecture Diagram

```
 push/PR auf php/**          push/PR auf .github/**          push/PR auf backend/** + wöchentlich
        |                              |                                  |
        v                              v                                  v
 php.yml                        workflow-lint (neu)                 python.yml (pytest)
   |                               |                                      |
   +-> psalm-taint [Matrix 33/34/35]  +-> zizmor (Image, offline,         +-> Strukturgate:
   |     composer install tools/psalm |     --min-severity medium, .)     |   Jobs/Schritte/Floors
   |     composer require ocp:<tag>   |     Exit 0 grün, 13/14 rot        |   der neuen Gates sind
   |     composer dump-autoload (php) |   Positivkontrolle: Fixture-Datei |   vorhanden und nicht
   |     psalm --taint-analysis       |     -> Exit >= 13 erwartet        |   entschärft
   |        --report=taint.sarif      +-> actionlint (Image)              v
   |     scripts/ci/sarif_count -> rot bei >0, Absturz, fehlende Datei   grün/rot
   |     Positivkontrolle: Probe nach lib/ kopieren, erneut laufen,
   |        >= 2 Befunde in der Probe erwartet, sonst rot ("Gate blind")
   +-> php-cs (dry-run --diff, Exit 8 = rot)
         Positivkontrolle: Verstoß-Datei, --path-mode=intersection, Exit 8 erwartet
```

### Recommended Project Structure
```
php/
├── psalm.xml                        # projectFiles lib, templates, appinfo/routes.php; phpVersion 8.2
├── .php-cs-fixer.dist.php           # Nextcloud\CodingStandard\Config, Finder lib/appinfo/templates/tests
├── tools/
│   ├── psalm/
│   │   ├── composer.json, composer.lock
│   │   ├── AppFrameworkTainter.php  # Kopie aus nextcloud/server build/psalm, MIT, Quelle+SHA im Kopf
│   │   ├── stubs/app_api.phpstub    # OCA\AppAPI\PublicFunctions, OCA\Files_Trashbin\Events\*
│   │   └── taint-probe/ProbeController.php   # Positivkontrolle, außerhalb lib/ und tests/
│   └── php-cs-fixer/
│       └── composer.json, composer.lock
scripts/ci/
├── psalm_taint_gate.sh              # ein Aufruf je OCP-Version, inkl. Zählung und Probe
├── php_cs_gate.sh                   # dry-run + Positivkontrolle
└── workflow_lint_gate.sh            # zizmor + actionlint + Positivkontrollen
scripts/dev/
└── php_gates_docker.sh              # lokales Rezept, ruft die drei scripts/ci-Skripte in Containern
.github/fixtures/
└── workflow-lint-probe.yml          # absichtlich unsicherer Workflow, von GitHub nie ausgeführt
backend/tests/
└── test_php_static_gates.py         # Strukturgate (Muster test_php_supply_chain_gates.py)
```
Begründung für `php/tools/` statt `php/tests/`: composer.json hat `autoload-dev` PSR-4 `OCA\Findling\Tests\ -> tests/` mit `optimize-autoloader`; eine Stub-Klasse `OCA\AppAPI\PublicFunctions` darf nie in den Autoload-Raum der PHPUnit-Suite geraten, denn ExAppService ist ausdrücklich darauf gebaut, dass diese Klasse dort fehlt (Kommentar Z. 868 ff.). Heute würde Composer sie zwar nicht in die Classmap aufnehmen [geprüft: 0 Treffer nach dump-autoload], aber außerhalb von tests/ und mit Endung `.phpstub` ist das konstruktiv ausgeschlossen. Store-Archiv: Include-Liste ist explizit `appinfo lib templates js css img l10n` [geprüft scripts/release/store-archive.sh Z. 76], php/tools, psalm.xml und .php-cs-fixer.dist.php reisen also nicht mit.

### Pattern 1: Psalm-Konfiguration (heute so getestet)
```xml
<!-- php/psalm.xml; Pfade relativ zur Datei -->
<psalm errorLevel="4" resolveFromConfigFile="true" phpVersion="8.2"
	findUnusedBaselineEntry="true" findUnusedCode="false"
	xmlns="https://getpsalm.org/schema/config">
	<plugins>
		<plugin filename="tools/psalm/AppFrameworkTainter.php" />
	</plugins>
	<projectFiles>
		<directory name="lib" />
		<directory name="templates" />
		<file name="appinfo/routes.php" />
		<ignoreFiles><directory name="vendor" /><directory name="tools" /></ignoreFiles>
	</projectFiles>
	<extraFiles>
		<directory name="tools/psalm/vendor/nextcloud/ocp" />
	</extraFiles>
	<stubs>
		<file name="tools/psalm/stubs/app_api.phpstub" />
	</stubs>
</psalm>
```
Psalm verlangt einen Composer-Autoloader im Projektwurzelverzeichnis ("Could not find any composer autoloaders in /w/php") [geprüft]. Lösung ohne Netz und ohne Installation: `composer dump-autoload --no-scripts` in php/ vor dem Lauf [geprüft]. Psalm selbst kommt aus `tools/psalm/vendor/bin/psalm`.

### Pattern 2: AppAPI-Stub mit Zusatzsenke
```php
<?php
// tools/psalm/stubs/app_api.phpstub: nur Signaturen, Vorlage server/build/stubs/app_api.php
namespace OCA\AppAPI {
	use OCP\Http\Client\IResponse;
	use OCP\IRequest;
	class PublicFunctions {
		/**
		 * @psalm-taint-sink ssrf $route
		 * @return array|IResponse
		 */
		public function exAppRequest(string $appId, string $route, ?string $userId = null,
			string $method = 'POST', array $params = [], array $options = [],
			?IRequest $request = null): array|IResponse {}
		public function getExApp(string $appId): ?array {}
	}
}
namespace OCA\Files_Trashbin\Events {
	use OCP\EventDispatcher\Event;
	use OCP\Files\Node;
	class MoveToTrashEvent extends Event { public function getNode(): Node {} }
	class NodeRestoredEvent extends Event { public function getSource(): Node {} public function getTarget(): Node {} }
}
```
Die Server-Stub-Datei hat keinen SPDX-Kopf (Server-Repo AGPL); Findling ist AGPL, eine eigene Signatur-Stub ist unkritisch. Die Signatur von `exAppRequest` vor dem Commit gegen nextcloud/app_api `lib/PublicFunctions.php` prüfen [Annahme: Server-Stub entspricht AppAPI-Stand].

### Pattern 3: SARIF-Zählung mit Absturzschutz (Skriptdatei)
```bash
# scripts/ci/psalm_taint_gate.sh (Ausschnitt). Psalm-Exit: 0 sauber, 2 Befunde, 1 Absturz/Konfig [geprüft 6.20.10]
set +e
"${PSALM}" --no-cache --threads="${THREADS}" --no-progress --monochrome \
  --taint-analysis --report="${SARIF}" --report-show-info=false --output-format=github
rc=$?
set -e
case "${rc}" in 0|2) ;; *) echo "psalm crashed or refused its config (exit ${rc})"; exit 1 ;; esac
test -s "${SARIF}" || { echo "no SARIF written"; exit 1; }
count=$(jq -e '[.runs[].results[]] | length' "${SARIF}")   # Server-Ausdruck, static-code-analysis.yml
echo "taint findings: ${count}"
[ "${count}" -eq 0 ] || exit 1
[ "${rc}" -eq 0 ] || { echo "psalm said 2 but the SARIF holds nothing"; exit 1; }
```
Quelle der Zählung: nextcloud/server `.github/workflows/static-code-analysis.yml` (`count=$(jq '[.runs[].results[]] | length' results.sarif)`, `test "$count" -eq 0`) [geprüft]. jq ist auf ubuntu-24.04 vorinstalliert (1.7.1) [geprüft Runner-Readme] und lokal vorhanden.

### Pattern 4: Positivkontrolle ohne Produktcode-Änderung
- **Psalm:** `tools/psalm/taint-probe/ProbeController.php` (Klasse `final class ProbeController extends \OCP\AppFramework\Controller`, Methode mit `string $needle` -> `echo $needle;` und `$this->request->getParam('column')` -> `$qb->expr()->eq(...)`). Im CI-Schritt nach dem echten Lauf: Datei nach `lib/TaintProbe/` kopieren (nur im Runner-Workspace), gleiche Psalm-Zeile mit der echten psalm.xml, erwarten: Exit 2, SARIF-Treffer >= 2, alle Treffer-URIs in `lib/TaintProbe/`, darunter `TaintedHtml` (beweist das Plugin) und `TaintedSql` (beweist die OCP-Annotationen); danach Datei löschen. Das prüft bei jedem Lauf und je OCP-Version, dass Konfiguration, Plugin, OCP-Annotationen und Zähler nicht blind geworden sind. Heute so gemessen: 3 Treffer.
- **php-cs-fixer:** Verstoß-Datei temporär nach `lib/CsProbe.php` schreiben (`if(true){echo 1;}`), `php-cs-fixer fix --dry-run --path-mode=intersection lib/CsProbe.php` muss Exit 8 liefern (heute für Verstöße gemessen); `intersection` beweist zugleich, dass der Finder lib/ abdeckt.
- **zizmor/actionlint:** `.github/fixtures/workflow-lint-probe.yml` (checkout ohne persist-credentials und `run: echo "${{ github.event.issue.title }}"`): zizmor auf diese Datei muss Exit >= 13 liefern (heute 14, template-injection High), actionlint Exit 1 (heute: untrusted input + undefinierte steps-Property). Bei Eingabe `.` sammelt zizmor `.github/fixtures` nicht ein [geprüft], die Probe stört das echte Gate also nicht.
- **Einmaliger Beweis am echten Gate (D-04):** Zusätzlich ein Wegwerf-Commit, der die Probe tatsächlich unter php/lib bzw. einen Stilverstoß bzw. einen unsicheren checkout committet, CI rot zeigt, dann per Revert zurück. Braucht Push, also Owner-Checkpoint (D-10). Achtung: eine Probe unter php/lib/Controller würde zusätzlich RouteSecurityTest/AppSurface rot färben; deshalb `lib/TaintProbe/` und nicht `lib/Controller/`.

### Pattern 5: OCP-Matrix ohne drei Lockfiles
Nach Nextcloud-Vorlage psalm-matrix.yml [geprüft]: `composer install` aus dem committeten `tools/psalm/composer.lock` (ocp v35.0.3), dann je Matrix-Bein `composer require --dev "nextcloud/ocp:${OCP_VERSION}" --no-interaction --no-scripts -W` mit exaktem Tag aus der Matrix (`v33.0.9`, `v34.0.6`, `v35.0.3`). Lokal heute genau so gefahren [geprüft]. Die Vorlage nutzt zusätzlich `--ignore-platform-reqs`; nicht nötig, wenn die Laufzeit PHP 8.3 ist und `config.platform.php` 8.3.x sagt (ocp 35 verlangt `~8.3`). Die Matrix-Tags als Liste im Workflow-`env` bzw. `strategy.matrix` führen, damit das Strukturgate sie lesen kann (drei Einträge, Majors 33/34/35, gleich `min-version`/`max-version` aus php/appinfo/info.xml).

### Pattern 6: zizmor- und actionlint-Aufruf
```bash
# zizmor: offline (kein Token, keine Online-Audits), Repo-Wurzel, Persona regular
docker run --rm -v "$PWD:/repo:ro" -w /repo "${ZIZMOR_IMAGE}" \
  --offline --no-progress --min-severity medium --format plain .
# Exit: 0 keine Befunde >= Medium, 13 höchster Befund Medium, 14 High, 1 Fehler, 3 keine Eingaben
# actionlint: Repo muss .git enthalten (sonst "no project was found", Exit 3) oder Dateien explizit nennen
docker run --rm -v "$PWD:/repo:ro" -w /repo "${ACTIONLINT_IMAGE}" -no-color -oneline
# Exit: 0 sauber, 1 Befunde, 3 Aufruffehler
```
Exit-Codes zizmor [zitiert: https://docs.zizmor.sh/usage/] und für `--min-severity` [geprüft: php.yml mit `--min-severity high` Exit 0, mit `medium` Exit 13]. `--format sarif` unterdrückt die Exit-Codes 11 bis 14 [zitiert], also kein SARIF-Format für das Gate verwenden (oder SARIF zusätzlich in einem zweiten Lauf).

### Anti-Patterns to Avoid
- **psalm/ocp/cs in php/composer.json:** riskiert OCP-Doppelklassen im PHPUnit-Prozess und Konflikte mit phpunit 11.5.57.
- **`|| true`, `continue-on-error`, `--no-exit-codes`, `--format sarif` am Gate:** entschärft das Gate still; das Strukturgate muss genau diese Formen melden (wie test_php_supply_chain_gates.py `DEFUSERS`).
- **zizmor-Ignores über `zizmor.yml` mit `datei:zeile`:** verrutschen bei jeder Zeilenänderung. Wenn der Owner etwas akzeptiert, dann Inline `# zizmor: ignore[regel] Begründung` am Fundort; für Composite Actions sind Inline-Kommentare der einzige Weg [zitiert: https://docs.zizmor.sh/configuration/].
- **Psalm-Baseline anlegen, obwohl 0 Befunde:** unnötig; eine leere Baseline ist eine Einladung, künftige Befunde wegzuschreiben.
- **`$params` als SSRF-Senke markieren:** erzeugt einen gewollten Befund (Admin-Request-Body), also Lärm statt Signal.

## Don't Hand-Roll

| Problem | Nicht bauen | Stattdessen | Warum |
|---------|-------------|-------------|-------|
| Controller-Parameter als Taint-Quellen | eigenes Psalm-Plugin | AppFrameworkTainter.php aus nextcloud/server (MIT) | Server-erprobt, 30 Zeilen, heute nachweislich wirksam |
| SARIF-Zählung | eigener SARIF-Parser | `jq '[.runs[].results[]] \| length'` wie im Server | ein Ausdruck, Server-Muster |
| AppAPI-Typen | Psalm-Suppressions für UndefinedClass | Stub-Datei nach server/build/stubs/app_api.php | Taint-Fluss über die Grenze bleibt sichtbar, Zusatzsenke möglich |
| OCP-Versionsmatrix | drei eigene ocp-Kopien | `composer require nextcloud/ocp:<tag>` je Bein | Nextcloud-Vorlage psalm-matrix.yml |
| Workflow-Sicherheitsregeln | eigene Python-Textgates für persist-credentials etc. | zizmor | deckt artipacked, cache-poisoning, template-injection, dependabot u. a. ab |

**Key insight:** Alle Werkzeuge liefern die Logik; der Eigenanteil sind nur Zähler, Positivkontrollen und Strukturgate, und genau die müssen wasserdicht sein, weil ein stilles Grün hier schlimmer ist als kein Gate.

## Common Pitfalls

### Pitfall 1: Psalm-Exit-Code wird anders als erwartet
**What goes wrong:** CONTEXT nimmt Exit 0 bei Befunden mit `--report` an; 6.20.10 endet heute mit 2 [geprüft], bei Absturz mit 1 ohne SARIF-Datei [geprüft mit 7.0.5].
**How to avoid:** `set +e`, Exit merken, 0/2 zulassen, alles andere rot; SARIF-Existenz prüfen; zählen; Widerspruch (2 aber 0 Treffer) rot. Der Kommentar im Server-Workflow ("Psalm exits 0 on taint findings when a report file is generated") ist für 6.20.10 nicht belegbar; Selbstzählung bleibt trotzdem, weil sich das Verhalten zwischen Versionen ändert.

### Pitfall 2: Taint ohne Plugin übersieht Routenparameter
**What goes wrong:** OCP annotiert nur `IRequest`-Getter als Quelle (`@psalm-taint-source input`, in allen drei ocp-Tags) [geprüft]. Per Dependency Injection gelieferte Methodenparameter (`string $needle`) sind ohne Plugin nicht tainted: Probe ohne Plugin fand nur TaintedSql, nicht TaintedHtml [geprüft].
**How to avoid:** Plugin einbinden und die Positivkontrolle auf `TaintedHtml` bestehen lassen.

### Pitfall 3: Psalm 7 oder ein Psalm-Update bricht das Plugin
**What goes wrong:** 7.x entfernt `Psalm\Type\TaintKindGroup`; Absturz [geprüft]. Dependabot würde ein Major-Update als PR anbieten.
**How to avoid:** Exakter Pin 6.20.10; Dependabot-Eintrag für `/php/tools/psalm` mit `ignore` für semver-major von vimeo/psalm (wie bei phpunit); Positivkontrolle fängt einen stillen Plugin-Ausfall ab.

### Pitfall 4: ocp 35 auf PHP 8.2
**What goes wrong:** `nextcloud/ocp` v35.x verlangt `php ~8.3` [geprüft], `composer require` scheitert auf 8.2.
**How to avoid:** Psalm-Job auf PHP 8.3, `config.platform.php` 8.3.16 im Tool-Projekt, `phpVersion="8.2"` in psalm.xml (analysiert für die App-Untergrenze).

### Pitfall 5: Templates sind für Taint fast blind
**What goes wrong:** `p()`/`print_unescaped()` sind nicht in OCP (277 UndefinedFunction), und Template-Variablen kommen über `$_` aus `TemplateResponse`, was Psalm nicht mit Controllern verbindet. Eine Taint-Strecke Controller -> Template wird also nicht gefunden [Annahme aus Psalm-Funktionsweise, nicht mit Probe belegt].
**How to avoid:** Als bekannte Grenze dokumentieren (wie die "limit"-Abschnitte der bestehenden Gates). Optional Stub mit `@psalm-taint-escape html` für `p()` und `@psalm-taint-sink html` für `print_unescaped()`; Nutzen gering, weil `$_` keine Quelle ist.

### Pitfall 6: CRLF auf dem Windows-Arbeitsbaum
**What goes wrong:** `core.autocrlf=true`, `.gitattributes` pinnt php/ bewusst nicht (außer tests/RouteSecurity/**), z. B. php/lib/AppInfo/Application.php liegt im Arbeitsbaum als CRLF, im Index als LF [geprüft `git ls-files --eol`]. coding-standard enthält `line_ending` [geprüft Config.php], ein lokaler dry-run direkt auf dem Arbeitsbaum würde massenhaft rot.
**How to avoid:** Lokales Rezept spiegelt `git ls-files php` in ein Cache-Verzeichnis und entfernt CR (so heute gemacht), oder arbeitet auf einem `git worktree`/`git archive`. Keine neue `.gitattributes`-Regel für php/ ohne Owner (store-archive.sh begründet das Gegenteil).

### Pitfall 7: phpdoc_align macht zwei Docblocks unleserlich
**How to avoid:** SearchOutcome.php und AdminViewService.php Docblocks vor dem Formatierungslauf umstellen; danach PHPUnit lokal (`scripts/dev/phpunit_docker.sh`) und der Template-Token-Vergleich als Beleg der Verhaltensgleichheit (D-08).

### Pitfall 8: deploy-harp.yml an der 500-KB-Grenze
**What goes wrong:** 505990 Byte, Grenze 512000 (test_workflow_size.py `CAP_BYTES = 500 * 1024`) [geprüft]. Zwei `persist-credentials: false` brauchen ca. 100 Byte; ausführliche Kommentare im Stil des Repos können die Grenze reißen.
**How to avoid:** In deploy-harp.yml nur Minimalzeilen, Begründung einmal zentral (z. B. Kopf von php.yml oder docs/testing.md); shellcheck-Hinweise dort, falls behoben, ebenfalls knapp.

### Pitfall 9: Eingefrorene paths-Listen
**What goes wrong:** test_workflow_tag_triggers.py `PATHS_BEFORE` hält die exakten paths von php.yml und python.yml [geprüft]. Neue Pfade (z. B. `scripts/ci/psalm_taint_gate.sh` in php.yml, `.github/**` in python.yml) machen den Test rot.
**How to avoid:** `PATHS_BEFORE` im selben Plan mit Kommentar erweitern (Präzedenz: Plan 42-10 und der Job "Store update in one process").

### Pitfall 10: Neuer Workflow verletzt bestehende Workflow-Gates
**How to avoid:** Jeder Job `timeout-minutes` (test_workflow_pins Regel 4); `uses:` nur mit 40-stelliger SHA und exakter Versionsangabe, dieselbe SHA wie anderswo (Regel 5); Push-Block mit `branches: ['**']` und Tag-Muster `v[0-9]+.[0-9]+.[0-9]+` (test_workflow_tag_triggers); `permissions: contents: read`; `persist-credentials: false` von Anfang an.

### Pitfall 11: Strukturgate läuft nicht bei reinen Workflow-Commits
**What goes wrong:** python.yml startet nur auf backend/**, scripts/**, php/**, python.yml, docs/... [geprüft]. Ein Commit, der nur php.yml oder den neuen Lint-Workflow ändert und dabei ein Gate entfernt, startet das Strukturgate nicht (erst der Montagslauf).
**How to avoid:** `.github/workflows/**` in python.yml-paths aufnehmen (PATHS_BEFORE nachziehen) oder das Strukturgate zusätzlich im neuen Lint-Workflow laufen lassen. Bewusst entscheiden und dokumentieren.

### Pitfall 12: security.yml läuft nicht auf Branch-Pushes
**What goes wrong:** `on: push: branches: [main]` + pull_request [geprüft]. Ein zizmor-Job dort sieht Branch-Commits ohne PR nicht.
**How to avoid:** Eigener Workflow mit Trigger auf `.github/**` (plus Branches/Release-Tags/Schedule), nicht in security.yml.

### Pitfall 13: zizmor-Persona und Eingabebereich
**What goes wrong:** Nur `.github/workflows` als Eingabe übersieht die Composite Action (1 artipacked) und dependabot.yml (4 Befunde). Persona `auditor` würde 13 weitere Befunde ab Medium bringen, Persona `regular` ist Default.
**How to avoid:** Eingabe `.` (Repo-Wurzel), Persona regular explizit setzen, `--offline` (kein Token im Job, reproduzierbar lokal). Online-Audits (z. B. bekannte verwundbare Actions) entfallen damit; das als bewusste Grenze dokumentieren [Annahme: welche Audits online-only sind, nennt die Usage-Seite nicht].

## Code Examples

### php-cs-fixer-Konfiguration (heute so getestet)
```php
<?php
// php/.php-cs-fixer.dist.php; Vorlage: README nextcloud/coding-standard v1.5.0
declare(strict_types=1);
require_once __DIR__ . '/tools/php-cs-fixer/vendor/autoload.php';
use Nextcloud\CodingStandard\Config;
$config = new Config();
$config->getFinder()->in([__DIR__ . '/lib', __DIR__ . '/appinfo', __DIR__ . '/templates', __DIR__ . '/tests']);
return $config;
```
Aufruf: `php tools/php-cs-fixer/vendor/bin/php-cs-fixer fix --dry-run --diff --using-cache=no --show-progress=none` (Exit 0 sauber, 8 Verstöße [geprüft]). `.php-cs-fixer.cache` in .gitignore, falls ohne `--using-cache=no` gearbeitet wird [zitiert README].

### Lokales Muster (Docker, seriell, Git Bash)
```bash
# wie scripts/dev/phpunit_docker.sh: cygpath -m für Mounts, MSYS_NO_PATHCONV=1, --rm, kein Port
MSYS_NO_PATHCONV=1 docker run --rm -v "${MIRROR}:/w" -w /w/tools/psalm "${COMPOSER_IMAGE}" \
  composer require --dev "nextcloud/ocp:${OCP}" --no-interaction --no-progress --no-scripts -W
MSYS_NO_PATHCONV=1 docker run --rm -v "${MIRROR}:/w" -w /w "${PHP83_IMAGE}" \
  bash /w/scripts/ci/psalm_taint_gate.sh
```
Die Versionen (OCP-Tags, Image-Digests) liest das lokale Skript aus dem Workflow, wie phpunit_docker.sh `SERVER_VERSION`/`MINIMUM_TESTS` aus php.yml liest, damit lokal und CI nicht driften.

### Strukturgate (Muster)
```python
# backend/tests/test_php_static_gates.py, Form wie test_php_supply_chain_gates.py
# Prüft u. a.: php.yml hat einen Job mit Matrix genau {v33.*, v34.*, v35.*}, der
# scripts/ci/psalm_taint_gate.sh aufruft; Job/Schritt ohne continue-on-error und
# ohne "|| true"; timeout-minutes gesetzt; psalm.xml nennt lib als projectFile,
# bindet AppFrameworkTainter ein, hat keine issueHandlers/suppress für Tainted*;
# kein psalm-baseline; der cs-Schritt enthält "--dry-run"; der Lint-Workflow ruft
# zizmor mit "--min-severity medium" und ohne "--no-exit-codes"/"--format sarif",
# actionlint ohne "-ignore"; die Positivkontrollen-Schritte existieren.
# Jede Regel bekommt eine gestellte Negativprobe (Selbsttest), wie test_workflow_pins.py.
```

## State of the Art

| Alt | Aktuell | Seit | Auswirkung |
|-----|---------|------|------------|
| Psalm 6, Taint per `--taint-analysis` separat | Psalm 7: Taint standardmäßig im selben Lauf, Bitmasken-Taints, neue Senken | 7.0.0, 02.11.2026 [geprüft Release-Notes] | Für diese Phase nicht übernehmen (Plugin-Bruch); in einer späteren Phase neu bewerten |
| zizmor `rules.<id>.ignore` nur per Datei | auch `disable`, `remap.severity`, Konfig-Suche bis Submodul-/Worktree-Wurzel | 1.13.0 / 1.25.0 / 1.32.0 [zitiert] | Ignores bevorzugt inline |
| ocp 35 mit PHP 8.2 | ocp 35.0.x verlangt PHP ~8.3 | spätestens v35.0.0 [geprüft] | Psalm-Laufzeit 8.3 |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `nextcloud/ocp` im App-vendor würde im PHPUnit-Job mit Server-OCP kollidieren | Alternatives | Gering; Empfehlung (getrennte Tool-Projekte) ist ohnehin sicherer |
| A2 | Server-Stub für `exAppRequest` entspricht der aktuellen AppAPI-Signatur | Pattern 2 | Mittel: falsche Signatur kann Taint-Fluss verfälschen; vor Commit gegen nextcloud/app_api prüfen |
| A3 | Controller -> Template-Taint wird nicht erkannt | Pitfall 5 | Gering; dokumentierte Grenze |
| A4 | setup-uv cacht ohne `enable-cache`-Zeile per Default | Ist-Befund zizmor | Gering; Empfehlung ist ohnehin explizit `false` |
| A5 | Welche zizmor-Audits nur online laufen | Pitfall 13 | Gering; `--offline` ist bewusste Wahl |
| A6 | Repo ist öffentlich, `git fetch` in probe-92d.yml braucht keine Zugangsdaten | Ist-Befund zizmor | Mittel: sonst bricht probe-92d nach `persist-credentials: false`; CI-Lauf nach Push zeigt es |
| A7 | Dependabot-Cooldown gilt nicht für Sicherheitsupdates | Open Questions | Gering |
| A8 | Paketlegitimität ohne slopcheck-Lauf | Package Legitimacy Audit | Gering (alle Pakete aus Nextcloud-/Hersteller-Primärquellen); Owner-Checkpoint vor Installation |

## Open Questions (RESOLVED)

1. **cache-poisoning in python.yml (High, Konfidenz Low):** Fix `enable-cache: false` (verlangsamt `uv sync` in zwei Jobs) oder begründet akzeptieren (python.yml veröffentlicht nichts, ein Tag-Lauf baut aber auch kein Artefakt). Empfehlung: Fix, weil D-06 Fix bevorzugt und der Preis nur Laufzeit ist. Alternative ohne Laufzeitverlust: Cache nur, wenn kein Tag-Lauf (`enable-cache: ${{ !startsWith(github.ref, 'refs/tags/') }}`), ob zizmor das erkennt, ist nicht geprüft.
   RESOLVED: siehe E-01 in 44-OWNER-DECISIONS.md (option-a, `enable-cache: false`)
2. **dependabot-cooldown:** Wert von `default-days`. zizmor verlangt >= 7. Empfehlung 14, passend zur Owner-Regel "Werkzeugversionen mindestens zwei Wochen alt".
   RESOLVED: siehe E-02 in 44-OWNER-DECISIONS.md (14 Tage)
3. **actionlint und shellcheck info/style (19 Befunde):** Variante a) alle 19 beheben bzw. mit `# shellcheck disable=SCxxxx` plus Begründung im Skript markieren (SC2016 in php.yml ist Absicht) und dann jeder shellcheck-Befund rot. Variante b) `SHELLCHECK_OPTS=--severity=warning` (heute 0 Befunde), info/style gelten als unter Medium. Empfehlung: b) als Gate-Schwelle (deckt "ab Medium" aus D-03 ab, shellcheck-"warning" ist die erste echte Fehlerklasse) und die 19 info-Befunde als einmaliges Aufräumen nur dort, wo es echte Quoting-Lücken sind; die Schwelle selbst ist eine Owner-Entscheidung.
   RESOLVED: siehe E-03 in 44-OWNER-DECISIONS.md (strenger als Empfehlung: Schwelle inkl. info und style, alle 19 echt behoben, kein disable ohne Owner-Wort)
4. **zizmor-Persona:** regular (Default, 55 Befunde, alle behebbar) oder auditor (zusätzlich secrets-outside-env, unpinned-images High, excessive-permissions). Empfehlung: regular als Gate, auditor-Befunde als Liste an den Owner.
   RESOLVED: siehe E-04 in 44-OWNER-DECISIONS.md (strenger als Empfehlung: Persona auditor als Gate, 13 Zusatzbefunde behoben, secrets-outside-env als Owner-Frage)
5. **SARIF-Upload an GitHub Code Scanning:** Server macht das (`security-events: write`). Nicht nötig für das Gate; Empfehlung: weglassen, Rechte minimal halten.
   RESOLVED: siehe E-05 in 44-OWNER-DECISIONS.md (kein Upload)
6. **Strukturgate-Trigger (Pitfall 11):** `.github/workflows/**` in python.yml aufnehmen ja/nein.
   RESOLVED: siehe E-06 in 44-OWNER-DECISIONS.md (option-a, paths von python.yml erweitert)

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker Desktop | lokales Rezept | ja | Server 29.5.2, ca. 5,8 GB RAM | keins (CI) |
| Image composer:2 | Tool-Installation lokal | ja (heute gezogen) | 2.11.2 / PHP 8.5.13 | - |
| Image php:8.3-cli, php:8.2-cli | Psalm, php-cs-fixer lokal | ja (heute gezogen) | 8.3.37 / 8.2.36 | - |
| Image ghcr.io/zizmorcore/zizmor:1.32.0 | zizmor lokal/CI | ja (heute gezogen) | 1.32.0 | `uvx zizmor@1.32.0` (heute ebenfalls gelaufen) |
| Image rhysd/actionlint:1.7.12 | actionlint lokal/CI | ja (heute gezogen) | 1.7.12, shellcheck 0.11.0 | Tarball mit SHA256 |
| jq | SARIF-Zählung | lokal ja (winget), Runner ja (1.7.1) | - | PHP `json_decode` |
| uv/uvx | pytest-Strukturgate, zizmor-Fallback | ja | 0.11.7 | - |
| PHP lokal | - | nein (Projektregel) | - | Docker |

Fremde Container: `docker ps -a` zeigt 36 Container anderer Projekte; heute keiner angefasst, alle eigenen Läufe mit `--rm`. Gezogene Images bleiben im lokalen Cache.

## Security Domain

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | ja | Psalm-Taint (Quellen: IRequest-Annotationen + Controller-Parameter; Senken: HTML, SQL über IExpressionBuilder, Shell, Datei, SSRF am ExApp-Routenpfad) |
| V14 Configuration / Build Pipeline | ja | zizmor (artipacked, cache-poisoning, template-injection, dependabot-cooldown), actionlint, SHA-Pins, digest-gepinnte Images, gelockte Tool-Abhängigkeiten, composer audit auch über die Tool-Lockfiles |
| V2/V3/V4 | nein (keine Produktänderung) | Routen-Gate aus Phase 42 bleibt |
| V6 Cryptography | nein | - |

### Known Threat Patterns
| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Gate wird still entschärft (`\|\| true`, continue-on-error, `--no-exit-codes`, SARIF-Modus) | Tampering | Strukturgate mit Selbsttests; Positivkontrolle bei jedem Lauf |
| Werkzeug wird blind (Plugin-Bruch, OCP ohne Annotationen, Finder deckt lib nicht ab) | Repudiation/Tampering | Positivkontrollen Psalm/cs/zizmor/actionlint im selben Job |
| Token im Arbeitsbaum landet in Artefakt/Cache (artipacked) | Information Disclosure | `persist-credentials: false` an allen 49 Checkouts |
| Cache-Vergiftung über Tag-Läufe | Tampering | `enable-cache: false` in python.yml |
| Lieferkette der Analysewerkzeuge selbst (Code läuft im Runner) | Tampering | exakte Versionen, Lockfiles committen, `composer audit --locked` auch für php/tools/*, Images per Digest, Dependabot-Einträge für php/tools/* mit Major-Ignore für psalm |
| Template-Injection in Workflows | Elevation of Privilege | zizmor template-injection (heute nur 1 Informational-Treffer) |

## Sources

### Primary (HIGH confidence)
- Lokale Läufe 21.11.2026 (Scratch-Kopie aus `git ls-files php`, CR entfernt): Psalm 6.20.10 gegen ocp v33.0.9/v34.0.6/v35.0.3, Psalm 7.0.5, php-cs-fixer 3.95.29, zizmor 1.32.0 (uvx und Image), actionlint 1.7.12 (Image)
- Packagist p2-API: vimeo/psalm, nextcloud/ocp, nextcloud/coding-standard, php-cs-fixer/shim, kubawerlos/php-cs-fixer-custom-fixers, psalm/plugin-phpunit
- PyPI JSON zizmor; GitHub Releases zizmorcore/zizmor, rhysd/actionlint (inkl. checksums.txt), vimeo/psalm (Release-Notes 7.0.0, 7.0.5, 6.20.10), zizmorcore/zizmor-action v0.8.1 action.yml
- nextcloud/.github workflow-templates: psalm-matrix.yml, lint-php-cs.yml
- nextcloud/server master: .github/workflows/static-code-analysis.yml, psalm.xml, vendor-bin/psalm/composer.json, build/psalm/AppFrameworkTainter.php, build/stubs/app_api.php
- nextcloud-deps/ocp Tags v33.0.9, v34.0.6, v35.0.3: OCP/IRequest.php (`@psalm-taint-source input`)
- nextcloud/coding-standard v1.5.0: README.md, src/Config.php
- actions/runner-images Ubuntu2404-Readme.md (jq 1.7.1, shellcheck 0.9.0, PHP 8.3.6)
- Repo: .github/workflows/*.yml, .github/dependabot.yml, .gitattributes, php/composer.json, php/phpunit.xml, php/lib/Service/ExAppService.php, scripts/dev/phpunit_docker.sh, scripts/release/store-archive.sh, backend/tests/test_php_route_gate_presence.py, test_php_supply_chain_gates.py, test_workflow_pins.py, test_workflow_size.py, test_workflow_tag_triggers.py, test_php_surface_bans.py

### Secondary (MEDIUM confidence)
- https://docs.zizmor.sh/usage/ (Exit-Codes, Offline, Personas, Formate), https://docs.zizmor.sh/configuration/ (Konfig-Suche, ignore/disable/remap)

### Tertiary (LOW confidence)
- keine

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH, Versionen und Kompatibilität heute geprüft und ausgeführt
- Architecture: HIGH für Werkzeugaufrufe und Positivkontrollen (ausgeführt), MEDIUM für Workflow-Aufteilung (Ermessen)
- Pitfalls: HIGH, fast alle per Lauf oder Repo-Grep belegt

**Research date:** 21.11.2026
**Valid until:** ca. 05.12.2026 (Psalm 7 und php-cs-fixer releasen sehr häufig; Pins gelten unabhängig davon)
