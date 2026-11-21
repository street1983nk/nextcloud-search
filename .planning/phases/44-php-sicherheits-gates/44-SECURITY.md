---
phase: 44
slug: php-sicherheits-gates
status: verified
threats_open: 0
asvs_level: 1
created: 2026-11-21
---

# Phase 44: Security

> Sicherheitsvertrag der Phase: Threat-Register, akzeptierte Risiken und Audit-Trail.
> Register aus den `<threat_model>`-Blöcken von 44-01 bis 44-10 (register_authored_at_plan_time: true), jede ID genau einmal.
> Geprüfter Stand: main = origin/main = 4cdde0d8 (Code-Kopf fd48fd0a, danach nur Doku-Commits).

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Packagist, GHCR, Docker Hub -> Repo und CI-Runner | Analysewerkzeuge (Psalm, ocp, php-cs-fixer, zizmor, actionlint) laufen als Code im Runner und lokal | Fremdcode, Integrität |
| HTTP-Anfrage -> PHP-Controller | IRequest und Routenparameter erreichen Senken (HTML, SQL, ExApp-Route) | Nutzereingaben |
| Executor -> Gate-Schwellen und Befunde | ein Executor könnte Befunde still akzeptieren oder Gates entschärfen | Entscheidungshoheit des Owners |
| Commit / Workflow-Änderung -> Gate-Definition | jede Änderung an Workflows, Skripten oder Konfigurationen kann ein Gate entschärfen | Gate-Wirksamkeit |
| GITHUB_TOKEN -> Arbeitsbaum, Artefakte | persistierte Zugangsdaten in .git/config | Token |
| Tag-Lauf -> Cache, Dependabot -> Repo | vergifteter Cache, frische Paketversionen ohne Wartezeit | Integrität des Release-Pfads |
| Formatierungswerkzeug -> Produktcode | automatische Änderung an ausgelieferten PHP-Dateien | Produktverhalten |
| lokales Rezept -> Docker-Host | Container auf einer Maschine mit fremden Containern | Host-Ressourcen |
| lokaler Arbeitsbaum, Wegwerf-Branch -> öffentliches Repo | Push startet Workflows mit Token, absichtlich unsicherer Code kurzzeitig öffentlich | Code, Secrets im Environment |

---

## Threat Register

Beleg-Konvention: Datei:Zeile im Stand 4cdde0d8; Lauf-IDs per `gh run view` am 21.11.2026 gegengeprüft.

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-44-SC | Tampering | composer-Pakete und Werkzeug-Images | mitigate | Exakte Pins: php/tools/psalm/composer.json (vimeo/psalm 6.20.10, nextcloud/ocp v35.0.3), php/tools/php-cs-fixer/composer.json (coding-standard v1.5.0, shim v3.95.29, custom-fixers v3.37.4); beide composer.lock mit identischen Versionen; composer validate und audit für beide Tool-Projekte in php.yml:281-301 (Job composer-hygiene); Images per Digest in workflow-lint.yml:74 und :96; Freigabe E-07 in 44-OWNER-DECISIONS.md. Lauf 44892647717 success. | closed |
| T-44-01 | Repudiation | Akzeptieren eines Befunds ohne Owner | mitigate | 44-OWNER-DECISIONS.md E-01 bis E-14 mit Frage, Owner-Wortlaut und Datum 21.11.2026; E-15 mit Wortlaut und Datum in 44-10-SUMMARY.md (siehe Hinweis 1). Keine Ausnahme ohne E-ID: einzige `shellcheck disable` unter .github ist php.yml:585 mit E-13, keine zizmor-Konfiguration, keine `zizmor:`-Inline-Ausnahme. | closed |
| T-44-02 | Tampering | Taint-Strecke Nutzereingabe -> HTML/SQL/SSRF in php/lib | mitigate | Job psalm-taint php.yml:324-376 mit Matrix v33.0.9/v34.0.6/v35.0.3, Aufruf scripts/ci/psalm_taint_gate.sh; rot bei jedem SARIF-Treffer (psalm_taint_gate.sh:121-126); SSRF-Senke `@psalm-taint-sink ssrf $route` in php/tools/psalm/stubs/app_api.phpstub, eingebunden in php/psalm.xml `<stubs>`. Grün mit 0 Befunden 44892647717, rot in allen drei Beinen 44902366566. | closed |
| T-44-03 | Repudiation | Psalm mit falschem Exit-Code | mitigate | psalm_taint_gate.sh:116-119 (nur 0/2 zulässig), :120 (fehlende SARIF rot), :90-97 (Selbstzählung per jq), :127-129 (Exit 2 mit 0 Treffern rot), :84 `env -u GITHUB_WORKFLOW` (fd48fd0a). | closed |
| T-44-04 | Tampering | Gate wird blind (Plugin-Bruch, ocp ohne Annotationen) | mitigate | Positivkontrolle in jedem Lauf und jedem Bein: psalm_taint_gate.sh:131-162 (Probe muss Exit 2, mindestens 2 Funde, alle in lib/TaintProbe/, TaintedHtml und TaintedSql liefern). Plugin in php/psalm.xml `<plugins>`. | closed |
| T-44-05 | Elevation of Privilege | Stub OCA\AppAPI\PublicFunctions im PHPUnit-Autoload | mitigate | Stub mit Endung .phpstub unter php/tools/psalm/stubs/; php/composer.json autoload nur `lib/`, autoload-dev nur `tests/`; PHPUnit-Job in 44892647717 success. | closed |
| T-44-06 | Information Disclosure | SARIF verlässt den Runner | accept | Kein Upload-Schritt in php.yml und workflow-lint.yml, beide `permissions: contents: read` (php.yml:58-59, workflow-lint.yml:53-54); SARIF nur in mktemp-Verzeichnis (psalm_taint_gate.sh:69-77). Accepted Risks R-44-01, E-05. | closed |
| T-44-07 | Tampering | Templates für Taint fast blind | accept | Grenze benannt in docs/testing.md:334 (`$_` ist keine Quelle, `p()`/`print_unescaped()` nicht in OCP). Accepted Risks R-44-02. | closed |
| T-44-08 | Tampering | Formatierungs-Commit ändert Template-Ausgabe oder Logik | mitigate | fa1836f5 eigener Stil-Commit; `git diff -w fa1836f5^ fa1836f5 -- php/templates` leer (nur Whitespace), php/lib ohne Whitespace nur Importreihenfolge, Docblocks und Leerzeilen; Token-Vergleich T_INLINE_HTML/T_CLOSE_TAG identisch (44-04-SUMMARY.md:69-70); PHPUnit 1222 Tests. | closed |
| T-44-09 | Tampering | Docblocks der RouteSecurity-Fixtures verändert | mitigate | `git show fa1836f5 -- php/tests/RouteSecurity/Fixtures.php`: nur Tausch zweier `use`-Zeilen (UseSession/UserRateLimit); PHPUnit inkl. RouteSecurityTest grün in 44892647717. | closed |
| T-44-10 | Repudiation | Stil-Gate blind | mitigate | Positivkontrolle bei jedem Lauf: scripts/ci/php_cs_gate.sh:75-97 (Probe lib/CsProbe.php, `--path-mode=intersection`, Exit 8 Pflicht); Exit-Code-Prüfung :69-73. Rot-Beweis 44909755992 (Job php-cs failure). | closed |
| T-44-11 | Information Disclosure | actions/checkout mit persistierten Zugangsdaten (artipacked) | mitigate | 55 von 55 echten checkout-Schritten unter .github mit `persist-credentials: false` (Zählung je Datei, alle 18 Workflow-/Action-Dateien deckungsgleich); einzige Ausnahme ist die absichtlich unsichere Probe .github/fixtures/workflow-lint-probe.yml (kein Workflow-Verzeichnis, läuft nie). zizmor grün 44889090612. | closed |
| T-44-12 | Tampering | setup-uv-Cache in python.yml (cache-poisoning) | mitigate | `enable-cache: false` an beiden setup-uv-Schritten python.yml:152 und :274; E-01. | closed |
| T-44-13 | Tampering | Dependabot-Updates ohne Wartezeit | mitigate | `cooldown: default-days: 14` an allen sechs Einträgen .github/dependabot.yml:39-40, 67-68, 95-96, 152-153, 182-183, 209-210; E-02. | closed |
| T-44-14 | Tampering | Psalm-Major-Update bricht Plugin still | mitigate | dependabot.yml:195-198 ignore semver-major für vimeo/psalm; Positivkontrolle T-44-04 fängt Plugin-Bruch. | closed |
| T-44-15 | Tampering | shellcheck-Hinweise in run-Blöcken | mitigate | actionlint mit Schwelle inkl. info/style ohne Befund in 44889090612 (success); einzige Disable-Zeile unter .github ist php.yml:585 mit E-13; Strukturtest test_the_only_exception_today_is_e13_in_php_yml. | closed |
| T-44-16 | Elevation of Privilege | auditor-Befunde (secrets-outside-env, unpinned-images, read-all), Repo-Secrets nach Umzug | mitigate | `environment:` an release.yml:91, store-submit.yml:68, store-release-delete.yml:52, issue-notify.yml:22; Digest-Pins integration.yml:1113 und :1129; scorecard.yml:23 `permissions: {}`, Job-Block :30-35. Namens-Lesebeleg 21.11.2026 (gh api, nur Namen): Repo-Secrets nur noch NTFY_TOPIC; release {APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY}, app-store {APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY}, app-store-delete {APPSTORE_TOKEN}, notify {}; alle vier Environments mit Policy branch main und tag v*. NTFY_TOPIC als Restpunkt nach E-12, siehe R-44-05. | closed |
| T-44-17 | Denial of Service | probe-92d git fetch ohne Zugangsdaten | mitigate | Vorbedingung direkt geprüft: Repo öffentlich (`gh api` private=false); anonymer Abruf `GIT_TERMINAL_PROMPT=0 git -c credential.helper= ls-remote ... refs/tags/v1.1.0` Exit 0, 891bc6d2 (21.11.2026, unabhängig vom Fetch-Beleg in 44-10-SUMMARY.md). probe-92d.yml:43-44 nur workflow_dispatch, Fetch in :115. Der im Plan genannte CI-Beleg fehlt, siehe R-44-06. | closed |
| T-44-18 | Elevation of Privilege | template-injection, artipacked, cache-poisoning in künftigen Workflows | mitigate | Job zizmor workflow-lint.yml:61-78; workflow_lint_gate.sh:72 `--persona auditor --min-severity medium`, :75-79 Exit 13/14 rot; Rot-Beweis 44902366560 (Job zizmor failure). | closed |
| T-44-19 | Tampering | Expressions-, Syntax- und Shell-Fehler in Workflows | mitigate | Job actionlint workflow-lint.yml:80-100; workflow_lint_gate.sh:94 `unset SHELLCHECK_OPTS`, :96-103 Exit-Prüfung; kein SHELLCHECK_OPTS sonst unter .github oder scripts/ci. Rot-Beweis 44902366560 (Job actionlint failure). | closed |
| T-44-20 | Repudiation | Workflow-Gate blind | mitigate | Positivkontrollen gegen .github/fixtures/workflow-lint-probe.yml: zizmor :81-88 (Exit 13/14 Pflicht), actionlint :105-119 (Exit 1 und SC2086 Pflicht); kein `--no-exit-codes`, kein SARIF-Format im Skript; Strukturtests test_a_lint_gate_with_no_exit_codes_is_reported, test_a_lint_gate_with_the_sarif_format_is_reported, test_a_lint_gate_without_sc2086_is_reported. | closed |
| T-44-21 | Tampering | Werkzeug-Images ausgetauscht | mitigate | sha256-Digests workflow-lint.yml:74 und :96, identisch zu E-07 und zu scripts/dev/php_gates_docker.sh:66-67. | closed |
| T-44-22 | Information Disclosure | zizmor online mit Token | mitigate | `--offline` workflow_lint_gate.sh:72 und :82; `docker run --rm --network none`, Workspace read-only (workflow-lint.yml:76-78); kein Token in env; `contents: read` :53-54. | closed |
| T-44-23 | Repudiation | Online-only-Audits entfallen | accept | Benannt im Workflow-Kopf workflow-lint.yml:8-12 und docs/testing.md:336. Accepted Risks R-44-03. | closed |
| T-44-24 | Tampering | Gate per Entschärfung entfernt | mitigate | backend/tests/test_php_static_gates.py (863 Zeilen) mit Regel und Negativprobe je Form: `|| true` :465, continue-on-error :472/:482, `--no-exit-codes` :667, SARIF :672, ignore :677, Persona :684/:693, shellcheck-Severity :572/:701, SHELLCHECK_OPTS :564/:710, fehlendes unset :715, SC2086 :722, Baseline :757/:780, Suppression :762/:784, zizmor-Konfig :811, Ausnahmen ohne E-ID :816/:825/:832. Python gates 44892647679 success. | closed |
| T-44-25 | Repudiation | Workflow-Commit ändert Gate ohne Strukturgate-Lauf | mitigate | python.yml paths um `.github/workflows/**` und `.github/dependabot.yml` erweitert (push :79-80, pull_request :100-101); E-06. | closed |
| T-44-26 | Tampering | OCP-Matrix driftet vom Versionsfenster | mitigate | test_php_static_gates.py:73 liest php/appinfo/info.xml zur Laufzeit, :126-132 min/max, :182-183 beide Richtungen; Proben :429, :437, :453, :459. | closed |
| T-44-27 | Spoofing | Commit-Autor und Trailer | mitigate | Owner-Freigaben "Push" und "go für push" (44-09-SUMMARY.md:31-32); `git log 0ec53fef..HEAD`: 31 Commits, alle street1983nk <k.cherif@outlook.de>, 0 Zeilen Claude-Session oder Co-Authored-By. | closed |
| T-44-28 | Repudiation | rote CI durch Gate-Schwächung grün | mitigate | fd48fd0a ändert nur psalm_taint_gate.sh (`env -u GITHUB_WORKFLOW`, macht das Gate auf Runnern scharf), den Strukturtest (+Regel test_a_psalm_gate_that_keeps_github_workflow_is_reported :629) und LICENSES/MIT.txt; Probe weiter Pflicht. | closed |
| T-44-29 | Denial of Service | Push startet viele lange Workflows | accept | Einmalig für die Phase; Rot-Beweis-Läufe mit unnötigen Jobs abgebrochen (44-10-SUMMARY.md). Accepted Risks R-44-04. | closed |
| T-44-30 | Elevation of Privilege | gate-proof.yml mit unsicherem checkout | mitigate | `git ls-files .github/workflows | grep -c gate-proof` = 0; `git ls-remote --heads origin 'gate-proof*'` leer (21.11.2026); Datei lebte nur auf gelöschten Wegwerf-Branches (Köpfe 0746f0e7, 1fc9232b). | closed |
| T-44-31 | Tampering | Taint-Probe gelangt in ein Release | mitigate | `git ls-files php/lib` ohne TaintProbe, StyleProof, CsProbe (Zählung 0); kein Tag enthält Phase-Commits (`git tag --contains 07039f0e` leer); release.yml:32-35 startet nur auf Tags `v*.*.*`. | closed |
| T-44-32 | Repudiation | Gate bleibt im Rot-Beweis grün | mitigate | Lauf 1 php-cs grün offen gemeldet, Owner E-15, Lauf 44909755992 php-cs failure; psalm-taint drei Beine failure 44902366566; zizmor und actionlint failure 44902366560. Alle vier Gates nachweislich rot. | closed |
| T-44-33 | Repudiation | unbekannter Taint-Befund still gefixt oder unterdrückt | mitigate | 0 Taint-Befunde (44892647717); php/psalm.xml ohne Baseline und ohne issueHandlers; keine `@psalm-suppress` im Analysebereich (Strukturtest test_the_analysed_php_files_suppress_nothing); Produkt-Diff nur fa1836f5. | closed |
| T-44-34 | Tampering | lokales Rezept und CI driften | mitigate | scripts/dev/php_gates_docker.sh:56 und :100-177 liest die OCP-Tags aus php.yml (mindestens 3 Pflicht); ruft dieselben Skripte scripts/ci/psalm_taint_gate.sh (:190), php_cs_gate.sh (:205), workflow_lint_gate.sh (:225). Siehe Hinweis 2. | closed |
| T-44-35 | Denial of Service | fremde Container auf dem Host | mitigate | php_gates_docker.sh: alle `docker run` mit `--rm` (:150, :165, :203, :223), kein `--name`, kein `-p`/`--publish`; Tags seriell in Schleife. | closed |
| T-44-36 | Tampering | Probe im Arbeitsbaum unter php/lib | mitigate | Rezept arbeitet in Spiegel-Kopie (php_gates_docker.sh:121-130, MIRROR aus `git ls-files`); `git ls-files php/lib | grep -c TaintProbe` = 0. | closed |
| T-44-37 | Repudiation | Workflow-Befund oder secrets-outside-env still gefixt oder ignoriert | mitigate | Checkpoint 44-05 Task 2: Owner-Antworten E-11 und E-12 mit Wortlaut in 44-OWNER-DECISIONS.md; Ist-Lauf deckungsgleich mit RESEARCH (44-05-SUMMARY.md:23); keine zizmor-Konfig, keine Inline-Ignores. | closed |
| T-44-38 | Tampering | Umbau eines run-Blocks ändert still das Verhalten | mitigate | Route-Gate-Schritt als Owner-Frage E-13, php.yml:585 nur Ausnahmezeile, Ausdruck unverändert; PHPUnit und Store-Jobs grün 44892647717, Python gates grün 44892647679. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### Hinweise (informativ, kein Blocker)

1. E-15 (zweiter Rot-Beweis php-cs, Owner-Wortlaut "a", 21.11.2026) steht nur in 44-10-SUMMARY.md, nicht in 44-OWNER-DECISIONS.md. Die Beleg-Spalte von T-44-01 in 44-10-SUMMARY.md ("E-01 bis E-15" in OWNER-DECISIONS) ist insoweit ungenau. Empfehlung: E-15 nachtragen.
2. Die Image-Digests von zizmor und actionlint stehen doppelt (workflow-lint.yml:74/:96 und php_gates_docker.sh:66-67) und sind heute identisch; ein automatischer Gleichlauf-Test existiert nicht. Der Plan von T-44-34 verlangte nur die OCP-Tags aus php.yml und dieselben Skripte, das ist erfüllt.
3. 44-05-SUMMARY und 44-10-SUMMARY nennen 53 checkouts; Stand 4cdde0d8 sind es 55 echte (plus Probe), alle mit `persist-credentials: false`.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| R-44-01 | T-44-06 | Kein SARIF-Upload zu Code Scanning; Bericht bleibt im Runner (mktemp), Jobs nur `contents: read`. | Owner, E-05 | 2026-11-21 |
| R-44-02 | T-44-07 | Psalm-Grenze (Pitfall 5): Template-Variablen über `$_` sind keine Taint-Quelle. Ausgleich durch bestehende Escaping-Textgates; benannt in docs/testing.md:334. | Plan 44-02 (register_authored_at_plan_time), Owner-Planabnahme | 2026-11-21 |
| R-44-03 | T-44-23 | zizmor läuft offline ohne Token; Online-Audits (bekannt verwundbare Action-Versionen) entfallen bewusst (Pitfall 13). Benannt in workflow-lint.yml:8-12 und docs/testing.md:336. | Plan 44-07, Owner-Planabnahme | 2026-11-21 |
| R-44-04 | T-44-29 | Einmaliger Phasen-Push startet viele Workflows; Owner im Push-Checkpoint 44-09 informiert, Rot-Beweis-Läufe mit unnötigen Jobs abgebrochen. | Plan 44-09, Owner-Freigaben "Push", "go für push" | 2026-11-21 |
| R-44-05 | T-44-16 (Restpunkt) | NTFY_TOPIC bleibt Repo-Secret; Environment notify hat noch kein eigenes Secret. Umzug offen, bis der Owner ihn einrichtet. Alle Signatur- und Store-Secrets liegen nur noch in Environments (Namens-Lesebeleg 21.11.2026). | Owner, E-12 ("Behalten, später einrichten") | 2026-11-21 |
| R-44-06 | T-44-17 (Restpunkt) | Kein CI-Lauf von probe-92d (nur workflow_dispatch). Ersatz: Repo öffentlich und anonymer Tag-Abruf Exit 0 (44-10-SUMMARY.md und Gegenprobe dieses Audits). CI-Beleg beim nächsten manuellen Lauf. | Abweichung 3 in 44-10-SUMMARY.md, zur Owner-Kenntnis | 2026-11-21 |

---

## Unregistered Flags

Keine. Alle `## Threat Flags` in 44-02 bis 44-10 melden keine neue Angriffsfläche oder verweisen auf registrierte IDs (44-03: T-44-34 bis T-44-36; 44-06: T-44-12 bis T-44-16, T-44-38; 44-07: T-44-18 bis T-44-23; 44-08: T-44-24 bis T-44-26; 44-09: T-44-16, T-44-27, T-44-28; 44-10: Trust Boundary Wegwerf-Branch, T-44-30). 44-01 hat keinen Abschnitt Threat Flags. Der Hinweis in 44-05 (store-release-delete.yml wartet auf Required reviewer) ist eine Härtung, keine neue Fläche.

---

## Security Audit Trail

### Security Audit 2026-11-21

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-11-21 | 39 | 39 | 0 | gsd-security-auditor |

- Zählung: 39 IDs (T-44-01 bis T-44-38 und T-44-SC); 35 mitigate, 4 accept (T-44-06, T-44-07, T-44-23, T-44-29), 0 transfer.
- ASVS-Level 1 (in .planning/config.json nicht gesetzt), block_on: open.
- CI-Belege gegengeprüft: 44902366560 Workflow security lint, Branch gate-proof-44, failure (zizmor und actionlint failure); 44902366566 PHP and store metadata gates, gate-proof-44, failure (psalm-taint v33.0.9, v34.0.6, v35.0.3 failure, php-cs success); 44909755992 PHP and store metadata gates, gate-proof-44-cs, failure (nur php-cs failure); fd48fd0a acht Läufe success (u. a. 44892647717 PHP, 44892647679 Python gates); 44889090612 Workflow security lint auf d2c07dad success, `git diff --quiet d2c07dad fd48fd0a -- .github scripts/ci/workflow_lint_gate.sh` Exit 0.
- Implementierungsdateien nicht verändert.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-11-21
