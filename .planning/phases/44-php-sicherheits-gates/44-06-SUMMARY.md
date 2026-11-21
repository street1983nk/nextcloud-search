---
phase: 44-php-sicherheits-gates
plan: 06
subsystem: ci
tags: [zizmor, actionlint, shellcheck, dependabot, environments, digest-pins]
requires: [44-05]
provides: [zizmor auditor lokal grün, actionlint inkl. info/style lokal grün, dependabot cooldown 14 und Tool-Einträge]
affects: [44-07, 44-08, 44-09]
key-files:
  modified:
    - .github/dependabot.yml
    - .github/workflows/python.yml
    - .github/workflows/deploy-harp.yml
    - .github/workflows/measure.yml
    - .github/workflows/integration.yml
    - .github/workflows/php.yml
    - .github/workflows/probe-92d.yml
    - .github/workflows/scorecard.yml
    - .github/workflows/docker.yml
    - .github/workflows/issue-notify.yml
    - .github/workflows/release.yml
    - .github/workflows/store-release-delete.yml
    - .github/workflows/store-submit.yml
    - backend/tests/test_upgrade_seed_steps.py
    - .planning/phases/44-php-sicherheits-gates/44-OWNER-DECISIONS.md
decisions:
  - "E-13: route-a, eine Ausnahmezeile `# shellcheck disable=SC2016 # E-13: ...` nur vor dem Route-Gate-Ausdruck in php.yml; test_php_route_gate_presence.py unverändert"
  - "E-14: Environment-Secret APPSTORE_TOKEN gleich dem Repo-Secret und gültig, keine weitere Secret-Arbeit in 44-06"
requirements: [PRUEF-04]
completed: 2026-11-21
---

# Phase 44 Plan 06: Workflow-Befunde Teil 2 Summary

zizmor 1.32.0 (Persona auditor, ab Medium) und actionlint 1.7.12 (ohne SHELLCHECK_OPTS, also inklusive info/style) enden lokal mit Exit 0: cooldown 14 Tage an allen sechs Dependabot-Einträgen samt den neuen Tool-Einträgen, kein uv-Cache mehr in python.yml, alle 19 shellcheck-Hinweise verhaltensgleich behoben (eine Owner-Ausnahme E-13), Service-Images per Digest gepinnt, scorecard ohne read-all, vier Jobs in ihren Environments.

Stand: 21.11.2026. Commits: siehe Abschnitt Commits. Kein Push.

## Task 1: dependabot und cache-poisoning

- dependabot.yml: `cooldown: default-days: 14` an allen sechs Einträgen (E-02), ein Kopfkommentar. Laut docs.github.com (Dependabot options reference, abgerufen 21.11.2026): "The cooldown option is only available for version updates, not security updates." Der Kommentar gibt das so wieder (Annahme A7 bestätigt).
- Zwei neue composer-Einträge nach /php: `/php/tools/psalm` mit `ignore` vimeo/psalm semver-major (Psalm 7 bricht AppFrameworkTainter, Pitfall 3) und `/php/tools/php-cs-fixer`; Zeitplan, Gruppen, Limit und commit-message wie bei /php.
- python.yml: `enable-cache: false` an beiden setup-uv-Schritten (E-01). `cache-dependency-glob` entfernt: laut action.yml und README der gepinnten setup-uv 68559e99 (v10.3.3) bildet die Option nur den Cache-Schlüssel ("The cache key gets computed by using the cache-dependency-glob"), ohne Cache ist sie bedeutungslos.
- test_php_supply_chain_gates.py unverändert: composer[0] bleibt /php.
- Zählungen: `cooldown:` 6, `package-ecosystem:` 6, `/php/tools/psalm` 1, `/php/tools/php-cs-fixer` 1, `enable-cache: true` 0, `enable-cache: false` 2.
- pytest test_php_supply_chain_gates, test_workflow_pins, test_workflow_tag_triggers: 57 passed.

## Task 2: Tabelle der Fundstellen und Owner-Antworten

Zeilen laut actionlint-Lauf nach 44-05 (Zeile des `run:`, in Klammern die Fundzeile im File vor dem Edit).

| Nr. | Regel | Datei:Zeile | Stelle | Fix | verhaltensgleich |
|-----|-------|-------------|--------|-----|------------------|
| 1 | SC2086 | deploy-harp.yml:1640 (1773) | `want=$(sorted $2)` | `read -ra want_ids <<< "$2"`, `sorted "${want_ids[@]}"` | ja, gleiche Wörter ohne Globbing |
| 2 | SC2086 | deploy-harp.yml:3594 (3614) | `docker rm -f ${leftover}` | `mapfile -t leftover_ids <<< "${leftover}"`, Array quotiert | ja, `docker ps -q` liefert eine ID je Zeile |
| 3 | SC2129 | deploy-harp.yml:3927 (4794) | vier `echo ... >> "${GITHUB_ENV}"` | `{ ...; } >> "${GITHUB_ENV}"` | ja, gleicher Inhalt; test_upgrade_seed_steps._env_writes liest die Gruppenform |
| 4 | SC2086 | deploy-harp.yml:5265 (5340) | `printf '%s\n' ${missing}` | `read -ra missing_ids`, Array quotiert | ja |
| 5 | SC2086 | deploy-harp.yml:5380 (5586) | `printf '%s\n' ${found}` | `read -ra found_ids`, Array quotiert | ja |
| 6, 7 | SC2086 | deploy-harp.yml:5380 (5587) | `${expected_candidates//,/ }`, `${expected_changed//,/ }` | `read -ra candidate_ids/changed_ids <<< "${...//,/ }"`, Arrays quotiert | ja, Werte sind Konstanten aus Ziffern und Kommas |
| 8, 9 | SC2086 | deploy-harp.yml:5380 (5619) | dieselben zwei Listen in `comm` | dieselben Arrays | ja |
| 10 | SC2016 | integration.yml:3734 (3764) | `expected=$(php -r '...' "$cat" "$sentence")` | quotiertes Heredoc `php -- "$cat" "$sentence" <<'PHP'` mit `<?php` | ja, Ausgabevergleich unten |
| 11 | SC2329 | integration.yml:3734 (3742) | `restore_language` (Aufruf per trap) | letzte Zeile `exit "${failed}"` durch `if [ "${failed}" != "0" ]; then exit "${failed}"; fi` ersetzt | ja, siehe Hinweis |
| 12 bis 15 | SC2086 | measure.yml:260, 579, 611, 681 | `set -- ${combination}` | `read -ra parts <<< "${combination}"`, `set -- "${parts[@]}"` | ja |
| 16 | SC2012 | measure.yml:547 (566) | `ls "${RUNNER_TEMP}/ladder" \| wc -l` | `find ... -mindepth 1 -maxdepth 1 -not -name '.*' \| wc -l` | ja, ls ohne -a zählt dieselben Einträge |
| 17 | SC2016 | php.yml:545 (546) | Schritt "State how many tests actually ran" | quotiertes Heredoc `php <<'PHP'` mit `<?php`, Ergebnis weiter in `count` | ja, Ausgabevergleich unten |
| 18 | SC2016 | php.yml:579 (580) | Schritt "The route attribute gate ran" | E-13 route-a: Zeile `# shellcheck disable=SC2016 # E-13: PHP-Code im Einzelzitat, $ ist gewollt` direkt vor `php -r '` | Ausdruck unverändert |
| 19 | SC2015 | probe-92d.yml:337 (351) | `A && B \|\| { error; exit 1; }` | `if ! { A && B; }; then error; exit 1; fi` | ja |
| a | unpinned-images | integration.yml:1101 | `mariadb:11.4` | `mariadb:11.4@sha256:a8992b5e...309b` (Index-Digest per `docker buildx imagetools inspect`) | ja, heutiger Stand der Serie |
| b | unpinned-images | integration.yml:1116 | `postgres:16` | `postgres:16@sha256:3950ad7c...382f` | ja |
| c | excessive-permissions | scorecard.yml:18 | `permissions: read-all` | `permissions: {}` | ja, der einzige Job hat einen eigenen Block, der den Workflow-Block vollständig ersetzt |
| d | secrets-outside-env | release.yml/archives, store-submit.yml/submit, store-release-delete.yml/remove, issue-notify.yml/notify | Repo-Secrets ohne Environment | `environment:` release, app-store, app-store-delete, notify (E-11, E-12) | Owner-Entscheidung, Folgen unten |

Owner-Antworten:

- Route-Gate-Schritt: E-13 "route-a: Ausnahmezeile" (Wortlaut in 44-OWNER-DECISIONS.md).
- Store-Token: E-14, Environment-Secret gleich dem Repo-Secret und gültig.
- Keine weitere Fundstelle ohne verhaltensgleichen Fix, daher keine weitere Owner-Frage.

Hinweis zu Nr. 11: shellcheck 0.11.0 (im actionlint-Image) meldet SC2329 fälschlich, sobald ein Skript nach `trap f EXIT` mit einem unbedingten `exit` endet. Minimalbeweis im Image: `f(){ echo hi; }; trap f EXIT; exit 0` meldet SC2329, ohne das `exit` oder mit `exit` in einem `if` nicht. Die bedingte Form endet bei `failed=0` mit Status 0 und ruft den trap wie zuvor; der Vergleich unten belegt beides.

### Ausgabevergleich der umgebauten PHP-Blöcke (php:8.3-cli, `--rm`)

Skript im Scratchpad, alte Form `php -r '...'` gegen neue Heredoc-Form, gleiche Eingaben:

| Fall | alt | neu | gleich |
|------|-----|-----|--------|
| count, zwei Suiten (40 + 117) | `count=[157] rc=0` | `count=[157] rc=0` | ja |
| count, kein XML | Meldung "junit.xml is not readable", rc=1 | dieselbe Meldung, rc=1 | Ergebnis ja; PHP-Warnungen nennen "Standard input code" statt "Command line code" |
| count, Datei fehlt | rc=1 | rc=1 | wie oben |
| expected, Übersetzung mit Apostroph, Anführungszeichen, `<`, `&`, Umlaut | `Busca l&#039;contenido &quot;de&quot; &lt;tus&gt; archivos &amp; más`, rc=0 | identisch, rc=0 | ja |
| expected, Schlüssel fehlt | leer, rc=3 | leer, rc=3 | ja |
| expected, Wert gleich Schlüssel | leer, rc=3 | leer, rc=3 | ja |

Der einzige Unterschied ist die Herkunftsbezeichnung in PHP-Warnungen auf dem Fehlerpfad (nur Log-Text auf stderr); stdout, Exit-Code und damit das Gate-Verhalten sind gleich.

### Vergleich der Shell-Umformungen (Git Bash, Scratchpad)

Alle Fälle "SAME": probe-Erwartung für "12 3 7", "" und "5"; docker-rm-Argumente aus zwei Zeilen; missing mit doppelten Leerzeichen; found, expected und shared für vier Kombinationen inklusive leerer Listen; `set --` für drei Kombinationen; ladder-Zählung mit Leerzeichen im Namen, versteckter Datei und Unterordner; probe-92d für HTTP 200/500 mal jq wahr/falsch; Endstatus mit trap bei failed 0 und 1; Manifest-Quellen in docker.yml (siehe Abweichungen).

## Task 3: Ergebnis

- actionlint 1.7.12 ohne SHELLCHECK_OPTS: keine Ausgabe, Exit 0.
- zizmor 1.32.0 `--persona auditor --min-severity medium --format plain .`: "No findings to report. Good job! (238 ignored)", Exit 0 (die 238 ignorierten liegen unter Medium bzw. sind Persona-gefiltert, Zahl wie in 44-05).
- `grep -c "image: mariadb:11.4@sha256:\|image: postgres:16@sha256:" .github/workflows/integration.yml`: 2. `grep -c "read-all" .github/workflows/scorecard.yml`: 0.
- `grep -rn "zizmor: ignore\|shellcheck disable" .github`:

```
.github/workflows/php.yml:585:          # shellcheck disable=SC2016 # E-13: PHP-Code im Einzelzitat, $ ist gewollt
```

- `grep -c "shellcheck disable=SC2016" .github/workflows/php.yml`: 1, mit E-13. `git diff --quiet HEAD -- backend/tests/test_php_route_gate_presence.py`: Exit 0.
- scorecard.yml, jeder Job mit eigenem `permissions:`-Block (`grep -n "permissions:\|^  [a-z-]*:$"`):

```
13:  push:
15:  schedule:
23:permissions: {}
26:  analysis:
30:    permissions:
```

  Einziger Job `analysis` (Z. 26) mit eigenem Block (Z. 30: security-events write, id-token write), Workflow-Ebene leer.
- `wc -c < .github/workflows/deploy-harp.yml`: 506374 (Grenze 512000), keine zusätzlichen Kommentare dort.
- pytest test_workflow_pins, test_workflow_size, test_workflow_tag_triggers, test_workflow_contexts, test_php_supply_chain_gates, test_public_artifacts, test_php_route_gate_presence: 166 passed.
- Volle Backend-Suite, erster Lauf: `1 failed, 7166 passed, 303 skipped` (test_upgrade_seed_steps.py::test_the_two_candidate_lists_are_disjoint_before_the_environment, siehe Testanpassung). Zweiter Lauf nach der Anpassung (und nach dem docker.yml-Fix): `7167 passed, 303 skipped, 3 warnings in 724.72s`, Exit 0.
- Reihenfolge der Läufe: zizmor Exit 0 und actionlint Exit 0 nach allen Workflow-Änderungen außer docker.yml; nach dem docker.yml-Fix lief actionlint erneut mit Exit 0. Ein zizmor-Lauf nach dem docker.yml-Fix steht aus: der freie RAM lag danach dauerhaft bei etwa 3,75 bis 3,9 GB, unter der Schwelle 4194304 KiB für Docker. Die Änderung in docker.yml enthält keinen Ausdruck `${{ }}`, keinen uses-, permissions- oder Secret-Bezug (nur Shell-Array statt Wortzerlegung); der Lauf wird in 44-07 vor dem Scharfschalten nachgeholt.

### Testanpassung (je Test begründet)

`backend/tests/test_upgrade_seed_steps.py::test_the_two_candidate_lists_are_disjoint_before_the_environment`

- Was der Test hält: im Schritt RECORD_STEP von deploy-harp.yml prüft eine `comm -12`-Zeile, dass die Listen UPGRADE_CATCHUP_CANDIDATES und UPGRADE_CATCHUP_CHANGED keine ID teilen, danach bricht `if [ -n "${shared}" ]` ab, und beides steht vor dem Schreiben nach GITHUB_ENV.
- Warum rot: der Anker war der wörtliche Text `printf '%s\n' ${expected_candidates//,/ }`, also genau die SC2086-Fundstelle Nr. 8 (Spalte 35). Jeder echte Fix dieser Fundstelle ändert diesen Text; ein Workflow-Fix, der den Anker erhält, ist nicht möglich.
- Neue Form: Anker `shared=$(comm -12 <(printf '%s\n' "${candidate_ids[@]}" | sort)`, dazu drei neue Zusicherungen: `read -ra candidate_ids <<< "${expected_candidates//,/ }"` und `read -ra changed_ids <<< "${expected_changed//,/ }"` stehen vor der Prüfung, und die zweite Prozess-Substitution nutzt `"${changed_ids[@]}"`. Die Reihenfolge-Zusicherungen (vor `} >> "${GITHUB_ENV}"` und vor `echo "UPGRADE_CATCHUP_CANDIDATES=`) sind unverändert. Der Test hält damit dasselbe wie zuvor und zusätzlich, dass die Arrays aus denselben Kommalisten entstehen.
- test_php_route_gate_presence.py und alle übrigen Testdateien unverändert.

## Deviations from Plan

1. [Rule 2, E-03] docker.yml enthielt seit Plan 01-07 eine Zeile `# shellcheck disable=SC2046` ohne E-ID vor `docker buildx imagetools create ... $(printf "${IMAGE}@sha256:%s " *)`. Sie hätte das Abnahmekriterium (jede Disable-Zeile mit E-ID) und das Strukturgate aus 44-08 gebrochen. Verhaltensgleich behoben: die Quellen werden in einer Schleife über `*` in ein Array gesammelt und quotiert übergeben, die Disable-Zeile ist weg. Vergleich mit zwei Digest-Dateien: identische Argumentliste. docker.yml stand nicht in files_modified.
2. Nr. 11 (SC2329) ist ein Fehlalarm von shellcheck 0.11.0; behoben durch bedingtes `exit` statt einer Disable-Zeile (Begründung als Kommentar im Workflow). Das Wort "shellcheck" steht dort bewusst nicht am Kommentaranfang, weil shellcheck eine Kommentarzeile, die mit "shellcheck" beginnt, als Direktive liest (erster Versuch ergab SC1072/SC1073).
3. Der Kommentar über den Service-Images in integration.yml sagte, Patch-Releases der Serie seien erwünscht; er beschreibt jetzt den Digest-Pin, die fehlende Dependabot-Erneuerung und den manuellen Refresh (Verweis docs/testing.md, Eintrag folgt in 44-08).
4. Eine Testanpassung in test_upgrade_seed_steps.py, begründet im Abschnitt Testanpassung.
5. E-13 und E-14 wurden vor dem Commit in 44-OWNER-DECISIONS.md eingetragen; der Checkpoint Task 2 war damit durch die Owner-Antwort vorab beantwortet.

## Hinweise für 44-09

- release.yml läuft auch per workflow_dispatch (Probelauf). Mit `environment: release` und der Policy "main und v*" kann ein Probelauf nur noch von main oder einem Tag v* starten, nicht mehr von einem anderen Branch.
- issue-notify.yml legt je Issue-Ereignis eine Deployment-Zeile im Environment notify an (Folge von `environment:`), NTFY_TOPIC kommt weiter aus den Repo-Secrets (E-12).
- store-release-delete.yml wartet vor dem Job auf die Freigabe durch street1983nk.
- zizmor wird schon durch `environment:` grün; der Beleg des Umzugs bleibt der Namens-Lesebeleg in 44-09 Task 3.

## Threat Flags

Keine neue Angriffsfläche. T-44-12 (Cache), T-44-13 (cooldown), T-44-14 (Psalm-Major), T-44-15 (shellcheck), T-44-16 (auditor) und T-44-38 (Ausgabevergleich, volle Suite) wie geplant behandelt.

## Commits

- 6e956930 docs(44-06): Owner-Entscheidungen E-13 und E-14 zu SC2016 und Store-Token
- ec3b3743 ci(44-06): cooldown, Cache, shellcheck und auditor-Befunde nach Owner-Entscheidung
- SUMMARY, STATE und ROADMAP im Abschluss-Commit docs(44-06)

## Self-Check: PASSED

Commits 6e956930 und ec3b3743 vorhanden; alle geänderten Dateien vorhanden; test_php_route_gate_presence.py unverändert; einzige Disable-Zeile unter .github trägt E-13. Offen: zizmor-Wiederholung nach dem docker.yml-Fix (RAM-Schwelle).
