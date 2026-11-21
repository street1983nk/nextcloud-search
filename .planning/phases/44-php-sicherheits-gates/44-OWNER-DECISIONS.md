# Phase 44: Owner-Entscheidungen

Stand: 21.11.2026

Quelle: Checkpoint von Plan 44-01 (Task 1 und Task 2), beantwortet am 21.11.2026 per AskUserQuestion. Antwort des Owners im Wortlaut: "Strenger: auditor + info". Das ist strenger als die Empfehlung aus 44-RESEARCH.md (dort E-03 option-b und E-04 option-a). Die Einzelentscheidungen unten sind die vom Owner bestätigte Auflösung dieser Antwort, je Punkt im übermittelten Wortlaut.

Grundregel für alle Entscheidungen (D-06): Kein Executor akzeptiert einen Befund selbst. Wo ein Fix nicht sinnvoll ist, geht der Befund als Owner-Frage in den bedingten Checkpoint des umsetzenden Plans und bekommt bei Annahme eine neue ID ab E-09.

## E-01

Frage: Wie wird der zizmor-Befund cache-poisoning (High, 2 Fundstellen in python.yml, setup-uv `enable-cache: true` in einem Workflow mit Release-Tag-Trigger) behandelt?

Owner-Wortlaut: "cache-poisoning (High) in python.yml beheben (enable-cache: false)."

Gewählt: option-a.

Konsequenz: Plan 44-06 Task 1 setzt in .github/workflows/python.yml an beiden setup-uv-Schritten `enable-cache: false` (englischer Kommentar: Workflow läuft auch auf Release-Tags, Preis ist nur Laufzeit) und entfernt `cache-dependency-glob`, falls es ohne Cache laut README der gepinnten setup-uv-Version bedeutungslos ist. Kein Ignore. Bei E-06 option-a und einem späteren Strukturgate-Job gilt derselbe Wert.

## E-02

Frage: Welcher Wert gilt für `cooldown.default-days` in jedem Eintrag von .github/dependabot.yml (zizmor dependabot-cooldown, 4 Befunde Medium)?

Owner-Wortlaut: "Dependabot-cooldown 14 Tage."

Gewählt: 14.

Konsequenz: Plan 44-06 Task 1 setzt `cooldown: default-days: 14` an alle vier bestehenden Einträge und an die zwei neuen composer-Einträge für /php/tools/psalm und /php/tools/php-cs-fixer (zusammen 6).

## E-03

Frage: Welche Schwelle gilt für die shellcheck-Hinweise, die actionlint meldet (19 Befunde, alle shellcheck info/style, 0 eigene actionlint-Fehler)?

Owner-Wortlaut: "shellcheck-Schwelle inkl. info und style (die 19 info/style-Befunde werden behoben, Gate ohne Abschwächung)."

Gewählt: option-a in der strengen Form: alle 19 Befunde werden echt behoben, keine `# shellcheck disable=`-Markierung als Ausweg und kein `SHELLCHECK_OPTS` am Gate.

Konsequenz:
- Plan 44-06 Task 2 behebt alle 19 Fundstellen (SC2086 x12, SC2016 x3, SC2012, SC2015, SC2129, SC2329 je 1; Dateien deploy-harp 9, measure 5, integration 2, php 2, probe-92d 1), ohne das Verhalten der run-Blöcke zu ändern. Das gilt auch für die zwei absichtlichen `php -r '...'`-Blöcke in php.yml (SC2016): sie werden so umgebaut, dass shellcheck nicht mehr anschlägt und die Ausgabe gleich bleibt.
- Lässt sich eine Fundstelle nicht ohne Verhaltensänderung beheben, stoppt der Executor und legt sie dem Owner vor (neue E-ID ab E-09). Eine `# shellcheck disable=`-Zeile entsteht nur mit Owner-Wort.
- Plan 44-07: actionlint läuft ohne `SHELLCHECK_OPTS`; das Gate-Skript entfernt eine geerbte `SHELLCHECK_OPTS`-Variable vor dem Lauf, damit die Schwelle nicht still sinkt. Jeder shellcheck-Befund, auch info und style, macht den Job rot.
- Plan 44-08: das Strukturgate meldet `SHELLCHECK_OPTS` im Gate-Skript und in workflow-lint.yml sowie jede `shellcheck disable`-Zeile unter .github ohne E-ID.

## E-04

Frage: Mit welcher zizmor-Persona läuft das Gate?

Owner-Wortlaut: "zizmor-Persona auditor als Gate (die 13 zusätzlichen auditor-Befunde werden behoben; wo ein Fix nicht sinnvoll ist, nicht selbst akzeptieren, sondern als Owner-Frage melden)."

Gewählt: option-b, `--persona auditor`, weiterhin mit `--min-severity medium` über die Repo-Wurzel.

Die 13 zusätzlichen auditor-Befunde aus 44-RESEARCH.md (Zeilen nach grep am 21.11.2026; zizmor kann auf die Zeile des Schlüssels oder des Jobs zeigen):

| Nr. | Audit | Schwere | Datei | Zeile | Behandlung |
|-----|-------|---------|-------|-------|------------|
| 1 | secrets-outside-env | Medium | .github/workflows/issue-notify.yml | 22 (NTFY_TOPIC) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 2 | secrets-outside-env | Medium | .github/workflows/release.yml | 316 (APP_PRIVATE_KEY) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 3 | secrets-outside-env | Medium | .github/workflows/release.yml | 371 (APP_PRIVATE_KEY) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 4 | secrets-outside-env | Medium | .github/workflows/release.yml | 437 (BACKEND_PRIVATE_KEY) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 5 | secrets-outside-env | Medium | .github/workflows/store-release-delete.yml | 71 (APPSTORE_TOKEN) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 6 | secrets-outside-env | Medium | .github/workflows/store-submit.yml | 83 (APPSTORE_TOKEN) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 7 | secrets-outside-env | Medium | .github/workflows/store-submit.yml | 84 (APP_PRIVATE_KEY) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 8 | secrets-outside-env | Medium | .github/workflows/store-submit.yml | 85 (BACKEND_PRIVATE_KEY) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 9 | secrets-outside-env | Medium | .github/workflows/store-submit.yml | 117 (APPSTORE_TOKEN) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 10 | secrets-outside-env | Medium | .github/workflows/store-submit.yml | 171 (APPSTORE_TOKEN) | Owner-Frage in 44-05 Task 2, Umsetzung 44-06 |
| 11 | unpinned-images | High | .github/workflows/integration.yml | 1101 (`mariadb:11.4`) | 44-06 Task 2: Digest-Pin, Tag als Kommentar |
| 12 | unpinned-images | High | .github/workflows/integration.yml | 1116 (`postgres:16`) | 44-06 Task 2: Digest-Pin, Tag als Kommentar |
| 13 | excessive-permissions | Medium | .github/workflows/scorecard.yml | 18 (`permissions: read-all`) | 44-06 Task 2: minimale Rechte laut README der gepinnten scorecard-action |

Konsequenz:
- Keiner der 13 Befunde bleibt außerhalb des Gates. Nr. 11 bis 13 behebt 44-06 Task 2 direkt.
- Nr. 1 bis 10 (secrets-outside-env) verlangen GitHub-Environments, also eine Repo-Einstellung, die nur der Owner ändert, und je nach Lösung das Umziehen von Secrets. Das ist kein Fix, den der Executor allein sinnvoll setzen kann; deshalb legt 44-05 Task 2 diese zehn Befunde dem Owner vor (Environments anlegen und Secrets umziehen, oder je Befund begründet akzeptieren). Die Antworten bekommen IDs ab E-09 und werden in 44-06 umgesetzt.
- Plan 44-07: Gate-Skript und Positivkontrolle laufen mit `--persona auditor`.
- Plan 44-08: das Strukturgate meldet ein Gate-Skript ohne `--persona auditor`.
- Tritt ein weiterer auditor-Befund auf, den diese Liste nicht kennt, gilt der bedingte Checkpoint aus 44-05 Task 2.

## E-05

Frage: Werden zizmor-Ergebnisse als SARIF an GitHub Code Scanning hochgeladen?

Owner-Wortlaut: "kein SARIF-Upload zu GitHub Code Scanning."

Gewählt: nein.

Konsequenz: workflow-lint.yml (44-07) bekommt kein `security-events: write` und keinen Upload-Schritt; die Rechte bleiben `contents: read`. Das Gate nutzt nie das SARIF-Format (unterdrückt die Exit-Codes).

## E-06

Frage: Wie läuft das Strukturgate bei reinen Workflow-Commits (Pitfall 11, python.yml startet heute nicht auf .github/workflows/**)?

Owner-Wortlaut: "`.github/workflows/**` in die paths von python.yml."

Gewählt: option-a.

Konsequenz: Plan 44-08 Task 2 nimmt `.github/workflows/**` und `.github/dependabot.yml` in die paths von python.yml auf (push und pull_request) und zieht PATHS_BEFORE["python.yml"] in backend/tests/test_workflow_tag_triggers.py mit dem Kommentar "Widened by phase 44 (owner decision E-06)" nach. `.github/dependabot.yml` gehört zur Vorlage von option-a aus 44-01 und ist von der Antwort gedeckt.

## E-07

Frage: Gibt der Owner die neuen Entwicklungswerkzeuge vor der ersten Installation frei (Package Legitimacy Gate, slopcheck lief nicht)?

Owner-Wortlaut: "neue Entwicklungswerkzeuge freigegeben (Psalm 6.20.10 + Taint-Plugin, php-cs-fixer + nextcloud/coding-standard, zizmor, actionlint; nur CI/Dev)."

Gewählt: freigegeben, ausschließlich für CI und Entwicklung, nicht für das ausgelieferte App-Paket.

Freigegebene Versionen und Digests (Liste aus 44-01 Task 2; nextcloud/ocp ist die Analysegrundlage von Psalm, php-cs-fixer/shim und kubawerlos/php-cs-fixer-custom-fixers sind Pflichtabhängigkeiten von nextcloud/coding-standard):

| Eintrag | Version bzw. Digest | Herkunft |
|---------|---------------------|----------|
| vimeo/psalm | 6.20.10 | github.com/vimeo/psalm |
| nextcloud/ocp | v33.0.9, v34.0.6, v35.0.3 | github.com/nextcloud-deps/ocp |
| nextcloud/coding-standard | v1.5.0 | github.com/nextcloud/coding-standard |
| php-cs-fixer/shim | v3.95.29 | github.com/PHP-CS-Fixer/shim |
| kubawerlos/php-cs-fixer-custom-fixers | v3.37.4 (nicht 3.37.5, jünger als 14 Tage) | github.com/kubawerlos/php-cs-fixer-custom-fixers |
| zizmor (Image) | `ghcr.io/zizmorcore/zizmor:1.32.0@sha256:3014cc8f68f663935f69b3c3e0e41f5ce102b268d97db13db0f62208747f860d` | github.com/zizmorcore/zizmor |
| actionlint (Image) | `rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667` | github.com/rhysd/actionlint |
| Taint-Plugin | Kopie von `build/psalm/AppFrameworkTainter.php` aus nextcloud/server (MIT laut SPDX-Kopf) | github.com/nextcloud/server |

Owner-Zusatz vom 21.11.2026 (AskUserQuestion vor 44-02, Antwort "Ja, mit frei"): nextcloud/ocp, php-cs-fixer/shim und kubawerlos/php-cs-fixer-custom-fixers sind ausdrücklich mit freigegeben. Damit ist die Zusammenfassung dieser drei Pakete unter die Freigabe (Hinweis in 44-01-SUMMARY.md) vom Owner bestätigt.

Konsequenz: 44-02 bis 44-07 installieren genau diese Versionen und Digests. Jede andere Version, jedes weitere Paket oder Image braucht eine neue Owner-Freigabe.

## E-08

Frage: In welcher Form wird der einmalige Rot-Beweis am echten CI-Gate geführt (D-04)?

Owner-Wortlaut: "Rot-Beweis auf Wegwerf-Branch gate-proof-44, Löschung erst nach Owner-Freigabe."

Gewählt: option-a.

Konsequenz: Plan 44-10 legt den Wegwerf-Branch `gate-proof-44` mit Taint-Probe, Stilverstoß und Wegwerf-Workflow an. Push nur nach Owner-Frage (D-10); CI muss in psalm-taint (drei Beine), php-cs, zizmor und actionlint rot sein. Das Löschen des Branches (remote und lokal) erfolgt erst nach ausdrücklicher Owner-Freigabe. main bleibt unberührt.

## E-09

Frage (vor 44-03, aus Abweichung 3 von 44-02): Wie kommt jq in das lokale Rezept, wenn weder php:8.3-cli noch composer:2 jq enthalten?

Owner-Wortlaut (21.11.2026, AskUserQuestion): "Host-jq per Shim".

Gewählt: Im lokalen Rezept scripts/dev/php_gates_docker.sh läuft PHP im Container, jq auf dem Host. Ein php-Shim auf dem PATH reicht jeden php-Aufruf des Gate-Skripts an den Container weiter, der Spiegel liegt dort unter identischem Pfad (Form wie im Testlauf von 44-02). Keine Paketinstallation im Container, kein Schalter im Gate-Skript.

Konsequenz: 44-03 baut das Rezept so und dokumentiert es in docs/testing.md (Englisch, wie die Datei). In CI ändert sich nichts, jq ist auf dem Runner vorhanden.

## E-10

Frage (vor 44-03, aus deferred-items.md von 44-02): Wie wird `test_the_store_listing_document_avoids_the_blocked_term_counting_every_line` wieder grün, der wegen zwei Stellen im 1.6.5-Abschnitt von docs/store-listing.md rot ist?

Owner-Wortlaut (21.11.2026, AskUserQuestion): "Umformulieren".

Gewählt: Die zwei Stellen werden mit gleicher Bedeutung umformuliert (Workflow-Name als "Release-Läufe für den App Store", "Quellpakete"); der Test bleibt unverändert.

Konsequenz: eigener Commit `docs(store-listing): ...` vor 44-03; der Test ist danach grün, der Eintrag in deferred-items.md ist erledigt.

## E-11

Frage (44-05 Task 2, Teil A): Wie werden die 10 zizmor-Befunde secrets-outside-env (Persona auditor, E-04 Nr. 1 bis 10) behandelt?

Owner-Wortlaut (21.11.2026, AskUserQuestion): "4 Environments (Empf.)".

Gewählt: echter Fix per GitHub-Environment für alle vier betroffenen Jobs, kein Ignore:

| Workflow/Job | Environment | Secrets im Environment | E-04 Nr. |
|--------------|-------------|------------------------|----------|
| release.yml/archives | `release` | APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY | 2, 3, 4 |
| store-submit.yml/submit | `app-store` | APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY | 6 bis 10 |
| store-release-delete.yml/remove | `app-store-delete` (Required reviewer street1983nk) | APPSTORE_TOKEN | 5 |
| issue-notify.yml/notify | `notify` | keine, siehe E-12 | 1 |

Alle vier Environments mit "Selected branches and tags": Branch `main`, Tag `v*`.

Lesebeleg des Executors (21.11.2026, `gh api`, nur Namen, keine Werte): vier Environments mit `custom_branch_policies: true`, `protected_branches: false`; je Environment die Regeln `main` (branch) und `v*` (tag); Secrets wie in der Tabelle; `app-store-delete` mit `required_reviewers` [street1983nk]; die Repo-Secrets APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY und NTFY_TOPIC bestehen unverändert.

Konsequenz: 44-06 setzt `environment: <Name>` an die vier Jobs. 44-09 pusht nach Owner-Freigabe und belegt grüne CI; erst danach löscht der Owner die Repo-Secrets APPSTORE_TOKEN, APP_PRIVATE_KEY und BACKEND_PRIVATE_KEY (44-09 Task 3), danach Namens-Lesebeleg. Ein Lauf von store-release-delete.yml wartet ab jetzt auf die Freigabe durch street1983nk.

## E-12

Frage (44-05 Task 2, Teil A, Nr. 1): Was passiert mit NTFY_TOPIC in issue-notify.yml?

Owner-Wortlaut (21.11.2026, AskUserQuestion): "Behalten, später einrichten".

Gewählt: issue-notify.yml bleibt. Der Job notify bekommt in 44-06 `environment: notify`; das Environment `notify` hat vorerst kein eigenes Secret, der Job nutzt weiter das Repo-Secret NTFY_TOPIC.

Konsequenz: NTFY_TOPIC wird in 44-09 Task 3 nicht gelöscht und nicht als "umgezogen" geprüft; die Abnahme in 44-09 umfasst nur APPSTORE_TOKEN, APP_PRIVATE_KEY und BACKEND_PRIVATE_KEY. Hinweis: zizmor wertet den Befund schon durch die Zeile `environment:` als behoben; der Umzug von NTFY_TOPIC ins Environment bleibt offen, bis der Owner ihn einrichtet.

## E-13

Frage (44-06 Task 2, Checkpoint Route-Gate-Schritt): Wie wird SC2016 im php.yml-Schritt "The route attribute gate ran" behandelt, dessen `php -r '...'`-Form backend/tests/test_php_route_gate_presence.py Regel 4 und der lokale Beweis aus 42-02 festhalten?

Owner-Wortlaut (21.11.2026, AskUserQuestion): "route-a: Ausnahmezeile".

Gewählt: route-a. Je betroffenem `php -r '`-Schritt eine eigene Zeile im run-Block direkt vor `php -r '` im Format `# shellcheck disable=SC2016 # E-13: PHP-Code im Einzelzitat, $ ist gewollt` (das zweite `#` ist nötig, sonst ist die Direktive ungültig). Ausdruck, Schrittname, env und backend/tests/test_php_route_gate_presence.py bleiben unverändert.

Konsequenz: 44-06 setzt die Zeile vor dem Route-Gate-Ausdruck. Der Schritt "State how many tests actually ran" wird nach E-03 echt behoben (quotiertes Heredoc, Ausgabe vorher und nachher gleich) und braucht keine Ausnahmezeile. Abnahme: mindestens eine Disable-Zeile unter .github, jede mit E-ID; `git diff --quiet HEAD -- backend/tests/test_php_route_gate_presence.py` Exit 0. Das Strukturgate aus 44-08 lässt genau diese Zeile mit E-ID zu.

## E-14

Frage (vor 44-06, Store-Token im Environment): Ist das Environment-Secret APPSTORE_TOKEN gültig und gleich dem Repo-Secret?

Owner-Wortlaut (21.11.2026, AskUserQuestion): Owner hat den bestehenden Token kopiert; Repo-Secret und Environment-Secret APPSTORE_TOKEN sind gleich und gültig.

Gewählt: kein neuer Token, die Environments app-store und app-store-delete tragen denselben gültigen Wert wie das Repo-Secret.

Konsequenz: 44-06 setzt `environment:` an die Jobs nach E-11 ohne weitere Secret-Arbeit. Das Löschen des Repo-Secrets bleibt bei 44-09 Task 3 nach grüner CI.
