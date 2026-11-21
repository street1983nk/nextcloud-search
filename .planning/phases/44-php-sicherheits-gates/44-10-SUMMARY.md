---
phase: 44-php-sicherheits-gates
plan: 10
subsystem: ci
tags: [rot-beweis, gate-proof, schlusspruefung, threat-liste, secure-phase]
requires: [44-09]
provides: [Rot-Beweis aller vier Gates am echten CI-Gate mit Lauf-IDs, Phasen-Schlussprüfung lokal und in CI, Threat-Liste T-44-* (39 IDs) als Eingabe für /gsd:secure-phase 44]
affects: [secure-phase 44]
key-files:
  created:
    - .planning/phases/44-php-sicherheits-gates/44-10-SUMMARY.md
  modified: []
decisions:
  - "E-15 (Owner, 21.11.2026, Antwort \"a\"): zweiter Rot-Beweis nur für php-cs mit anderem Reiz (php/lib/StyleProof.php mit `if(true){echo 1;}`) auf Branch gate-proof-44-cs, weil der Plan-Reiz `APP_ID = 'findling' ;` von nextcloud/coding-standard v1.5.0 nicht geprüft wird"
  - "Workflow security lint hat auf fd48fd0a keinen Lauf (paths-Filter); maßgeblich bleibt 44889090612 auf d2c07dad, .github-Baum und Gate-Skript beider Köpfe identisch (git diff --quiet Exit 0)"
requirements: [PRUEF-02, PRUEF-03, PRUEF-04]
completed: 2026-11-21
---

# Phase 44 Plan 10: Rot-Beweis und Schlussprüfung Summary

Alle vier neuen Gates (psalm-taint in drei OCP-Beinen, php-cs, zizmor, actionlint) sind am echten CI-Gate nachweislich rot geworden und wieder zurückgesetzt; die Phase ist lokal und in CI grün, der Produkt-Diff ist nur der Formatierungs-Commit, und die Threat-Liste mit 39 IDs liegt für secure-phase bereit.

Stand: 21.11.2026. main lokal b4089a55 (nur Doku-Commit über origin/main), origin/main fd48fd0a.

## Task 1: Owner-Freigabe (erledigt vor diesem Abschluss)

Freigabe des Rot-Beweises nach E-08 option-a (Push des Wegwerf-Branches und sein Löschen) lag vor; Lauf 2 nach Owner-Antwort "a" (E-15, siehe unten).

## Task 2: Rot-Beweis am echten Gate

### Lauf 1: Branch gate-proof-44 (gelöscht)

Inhalt nach Plan: Taint-Probe unter php/lib/TaintProbe/, Stilverstoß `public const APP_ID = 'findling' ;` in php/lib/AppInfo/Application.php, .github/workflows/gate-proof.yml (nur `workflow_dispatch`, checkout ohne persist-credentials, `${{ steps.nonexistent-step.outputs.value }}`, SC2086-Zeile).

| Gate | Lauf-ID | Ergebnis | Beleg |
|------|---------|----------|-------|
| zizmor | 44902366560 (Workflow security lint) | rot | exit 13, artipacked in gate-proof.yml |
| actionlint | 44902366560 (Workflow security lint) | rot | exit 1, undefinierte steps-Property und SC2086 in gate-proof.yml |
| psalm-taint v33.0.9 | 44902366566 (PHP and store metadata gates) | rot | 3 Funde in lib/TaintProbe/ |
| psalm-taint v34.0.6 | 44902366566 | rot | 3 Funde in lib/TaintProbe/ |
| psalm-taint v35.0.3 | 44902366566 | rot | 3 Funde in lib/TaintProbe/ |
| php-cs | 44902366566 | **grün** | "0 of 131 files can be fixed" |

php-cs blieb grün, weil der Reiz aus dem Plan (Leerzeichen vor Semikolon in einer Konstanten-Deklaration) von nextcloud/coding-standard v1.5.0 nicht geprüft wird. Befund: Gate blind wegen Reizwahl, nicht wegen des Gates. Gemeldet, Owner-Entscheidung E-15.

Beifang Lauf 1: Python gates 44902366584 mit 1 Fehler (Baumhash-Test der PHP-Hälfte, 134 statt 133 Dateien durch die Probe, erwartet). Resilience, Integration, HaRP abgebrochen.

### E-15 (neue Owner-Entscheidung)

Frage: php-cs blieb im Rot-Beweis grün, weil der Plan-Reiz nicht in der Regelmenge von nextcloud/coding-standard v1.5.0 liegt. Wie weiter?

Owner-Wortlaut (21.11.2026): "a".

Gewählt: zweiter Rot-Beweis nur für php-cs mit einem anderen Reiz, auf eigenem Wegwerf-Branch, vorher lokal rot verifiziert. Kein Gate-Umbau.

### Lauf 2: Branch gate-proof-44-cs (gelöscht)

- Kopf 1fc9232b5b27494c3e7289727daeb4199f892fd0, Datei php/lib/StyleProof.php mit `if(true){echo 1;}`.
- Vorher lokal rot: `bash scripts/dev/php_gates_docker.sh cs`.
- CI-Lauf 44909755992 (PHP and store metadata gates), Schritt "php-cs-fixer dry run" failure:

```
1) lib/StyleProof.php
Found 1 of 131 files that can be fixed
php cs gate: files break nextcloud/coding-standard
exit code 1
```

- Alle anderen Jobs des Laufs grün (psalm-taint drei Beine, PHPUnit, composer, info.xml, php -l, Store update). Integration, HaRP, Resilience, Python abgebrochen.

### Zurücksetzen

Beide Branches remote und lokal gelöscht, Worktree entfernt, main unverändert. Prüfung am 21.11.2026:

```
git ls-files php/lib | grep -c TaintProbe     -> 0
git ls-files php/lib | grep -c StyleProof     -> 0
git ls-files .github/workflows | grep -c gate-proof -> 0
git ls-remote --heads origin 'gate-proof-44*' -> leer
git branch -a | grep -c gate-proof            -> 0
```

Ergebnis: Alle vier Gates am echten Gate rot (php-cs erst mit Reiz aus E-15), main sauber.

## Task 3: Schlussprüfung

### Lokal (seriell, freier RAM vorher 5,1 GB bzw. 5,25 GB, kein fremder Container)

| Prüfung | Ergebnis |
|---------|----------|
| `bash scripts/dev/php_gates_docker.sh all` | Exit 0: psalm "taint findings: 0" und "probe found 3" je OCP v33.0.9, v34.0.6, v35.0.3; "php cs gate: 0 violations, probe seen"; zizmor "No findings to report (238 ignored)", "probe seen (exit 14)"; actionlint "no finding", "probe seen (exit 1, SC2086 reported)" |
| `bash scripts/dev/phpunit_docker.sh` | Exit 0, OK (1222 tests, 7765 assertions) |
| pytest backend (`PYTHONUTF8=1 uv run --no-sync python -m pytest -q`) | Exit 0, 7235 passed, 303 skipped, 0 failed (3 Warnungen, 13:07 min) |
| ruff check (backend) | All checks passed |
| ruff format --check (backend) | 259 files already formatted |
| ruff check und format --check auf ../scripts (wie python.yml) | All checks passed, 21 files already formatted |
| pyright (`PYRIGHT_PYTHON_FORCE_VERSION=latest`) | 0 errors, 0 warnings, 0 informations |
| vulture src tests --min-confidence 80 | Exit 0, keine Ausgabe |

### CI-Kopf

origin/main = fd48fd0a723be9b0d9cdbe1bbb740175b759ecf1, seit 44-09 unverändert (lokal nur der Doku-Commit b4089a55 darüber).

- `head_green.sh fd48fd0a "PHP and store metadata gates" "Python gates"`: Exit 0, acht Läufe success (44892647726 Scorecard, 44892647717 PHP and store metadata gates, 44892647684 Multi-arch image, 44892647708 Security scans, 44892647685 HaRP deploy, 44892647679 Python gates, 44892647711 Integration, 44892647752 Resilience).
- "Workflow security lint" hat auf fd48fd0a keinen Lauf (paths-Filter), der Plan-Aufruf mit diesem Namen endet deshalb mit Exit 1. Maßgeblich: Lauf 44889090612 auf d2c07dad success; `git diff --quiet d2c07dad fd48fd0a -- .github scripts/ci/workflow_lint_gate.sh` Exit 0. (head_green.sh auf d2c07dad insgesamt Exit 1 wegen der in fd48fd0a behobenen roten Läufe 44889090525 und 44889090488, siehe 44-09.)

### Produkt-Diff

`git diff --stat 0ec53fef..origin/main -- php/lib php/appinfo php/templates php/js php/css php/l10n backend/src backend/appinfo` (0ec53fef = Kopf vor 07039f0e, dem ersten Commit der Phase):

```
php/lib/Listener/FileEventListener.php |   4 +-
php/lib/Service/AdminViewService.php   |   6 +-
php/lib/Service/ProbeService.php       |   2 -
php/lib/Service/SearchOutcome.php      |   5 +-
php/templates/admin.php                | 158 ++++++++--------
php/templates/search.php               | 320 ++++++++++++++++-----------------
6 files changed, 247 insertions(+), 248 deletions(-)
```

Einziger Commit auf diesen Pfaden: fa1836f5 (Formatierungs-Commit 44-04), `git show --stat fa1836f5 -- php/lib php/templates` zeigt dieselben sechs Dateien mit denselben Zahlen. Keine Owner-Fixes am Produkt aus 44-02 (keine Taint-Befunde). Kein `<version>`-Diff in beiden info.xml, kein neuer Tag.

### Erfolgskriterien Phase 44 (ROADMAP)

1. [x] Psalm-Taint gegen OCP 33, 34, 35 mit eigener SARIF-Zählung, rot ab einem Befund, Negativtest färbt rot: scripts/ci/psalm_taint_gate.sh, Job psalm-taint in php.yml (4f51f090, fd48fd0a); Rot-Beweis Lauf 44902366566 alle drei Beine rot; Positivkontrolle in jedem Lauf ("probe found 3", 44892647717).
2. [x] Psalm meldet 0 offene Befunde: "taint findings: 0" je Bein in 44892647717 und lokal; keine Ausnahmen nötig.
3. [x] php-cs-fixer mit nextcloud/coding-standard als dry-run grün auf dem Phasenkopf (44892647717 "0 violations, probe seen"), ein Stilverstoß macht ihn rot (44909755992, E-15).
4. [x] zizmor (auditor, ab Medium) und actionlint (shellcheck alle Stufen) über alle Workflows (8e4ae166), alle Befunde behoben (E-01 bis E-04, E-11, E-13), neuer Befund macht den Job rot (44902366560: zizmor exit 13, actionlint exit 1); grün auf 44889090612.
5. [ ] teilweise: lokale Rezepte grün und dokumentiert (scripts/dev/php_gates_docker.sh, docs/testing.md, 8f5aca31, c6142abb), Strukturgate backend/tests/test_php_static_gates.py (c6142abb) in Python gates grün; **secure-phase 44 steht noch aus** (nächster Schritt, Eingabe ist die Liste unten).

## Threat-Liste für /gsd:secure-phase 44

Zählung: `grep -ohE "T-44-([0-9]+|SC)" .planning/phases/44-php-sicherheits-gates/44-*-PLAN.md | sort -u | wc -l` = **39**. Tabellenzeilen unten: **39** (T-44-01 bis T-44-38 und T-44-SC; T-44-SC steht in 44-01, 44-02 und 44-04, T-44-16 in 44-06 und 44-09, je eine Zeile).

| ID | Kategorie | Komponente | Disposition | Beleg | E-ID / Begründung |
|----|-----------|-----------|-------------|-------|-------------------|
| T-44-01 | Repudiation | Akzeptieren eines Befunds ohne Owner | mitigate | 44-OWNER-DECISIONS.md E-01 bis E-15 mit Wortlaut und Datum (e71886fe, 1211162d, 6e956930) | |
| T-44-02 | Tampering | Taint-Strecke Nutzereingabe -> HTML/SQL/SSRF in php/lib | mitigate | Job psalm-taint je OCP, 0 Befunde (44892647717), Rot-Beweis 44902366566; SSRF-Stub php/tools/psalm/stubs/app_api.phpstub (4f51f090) | |
| T-44-03 | Repudiation | Psalm mit falschem Exit-Code | mitigate | psalm_taint_gate.sh: Exit nur 0/2, SARIF-Pflicht, Selbstzählung per jq (4f51f090); `env -u GITHUB_WORKFLOW` (fd48fd0a) | |
| T-44-04 | Tampering | Gate wird blind (Plugin, ocp) | mitigate | Positivkontrolle "probe found 3" je Bein in CI (44892647717) und lokal | |
| T-44-05 | Elevation of Privilege | AppAPI-Stub in PHPUnit-Autoload | mitigate | Stub als .phpstub unter php/tools, außerhalb autoload-dev (4f51f090); PHPUnit 1222 Tests grün lokal | |
| T-44-06 | Information Disclosure | SARIF verlässt den Runner | accept | kein Upload-Schritt, workflow-lint.yml und php.yml nur `contents: read` | E-05 |
| T-44-07 | Tampering | Templates für Taint fast blind | accept | bekannte Grenze, in docs/testing.md benannt (c6142abb); Escaping über bestehende Textgates | Begründung: Psalm-Grenze (Pitfall 5), Ausgleich durch Textgates |
| T-44-08 | Tampering | Formatierungs-Commit ändert Logik oder Ausgabe | mitigate | 44-04-SUMMARY Token-Vergleich T_INLINE_HTML/T_CLOSE_TAG identisch; Produkt-Diff oben nur fa1836f5 | |
| T-44-09 | Tampering | Docblocks der RouteSecurity-Fixtures verändert | mitigate | Fixtures.php nur Importreihenfolge (44-04-SUMMARY); RouteSecurityTest in PHPUnit grün | |
| T-44-10 | Repudiation | Stil-Gate blind | mitigate | Positivkontrolle "probe seen" (Exit 8) in 44892647717 und lokal; Rot-Beweis 44909755992 | |
| T-44-11 | Information Disclosure | checkout ohne persist-credentials (artipacked) | mitigate | 325fb97a, 53 von 53 checkouts mit `persist-credentials: false`; zizmor grün 44889090612 | |
| T-44-12 | Tampering | setup-uv-Cache in python.yml | mitigate | `enable-cache: false` (ec3b3743) | E-01 |
| T-44-13 | Tampering | Dependabot ohne Wartezeit | mitigate | `cooldown: default-days: 14` an allen Einträgen (ec3b3743) | E-02 |
| T-44-14 | Tampering | Psalm-Major bricht Plugin still | mitigate | Dependabot ignore semver-major vimeo/psalm (ec3b3743), Positivkontrolle | |
| T-44-15 | Tampering | shellcheck-Hinweise in run-Blöcken | mitigate | 19 Fundstellen behoben (ec3b3743), actionlint "no finding" lokal und 44889090612 | E-03; einzige Ausnahmezeile E-13 |
| T-44-16 | Elevation of Privilege | Secrets außerhalb Environment, Repo-Secrets nach Umzug | mitigate | `environment:` an vier Jobs (ec3b3743); Namens-Lesebeleg 44-09 Task 3: Repo nur noch NTFY_TOPIC, Environments mit Policy main und `v*` | E-04, E-11, E-12, E-14; Restpunkt NTFY_TOPIC bleibt Repo-Secret (E-12, offen bis Owner es einrichtet) |
| T-44-17 | Denial of Service | probe-92d git fetch ohne Zugangsdaten | mitigate | probe-92d.yml startet nur per workflow_dispatch, daher kein CI-Lauf in 44-09; Ersatzbeleg 21.11.2026 lokal: leeres Repo, `git -c credential.helper= fetch --no-tags --depth 1 origin refs/tags/v1.1.0` gegen https://github.com/street1983nk/nextcloud-search mit GIT_TERMINAL_PROMPT=0 Exit 0, v1.1.0 = 891bc6d2 | Restpunkt: CI-Beleg erst beim nächsten manuellen Lauf von probe-92d |
| T-44-18 | Elevation of Privilege | template-injection, artipacked, cache-poisoning künftig | mitigate | Job zizmor (8e4ae166), Rot-Beweis 44902366560 exit 13 | E-04 |
| T-44-19 | Tampering | Expressions-, Syntax-, Shell-Fehler in Workflows | mitigate | Job actionlint mit `unset SHELLCHECK_OPTS` (8e4ae166), Rot-Beweis 44902366560 exit 1 | E-03 |
| T-44-20 | Repudiation | Workflow-Gate blind | mitigate | Positivkontrollen "probe seen (exit 14)" und "probe seen (exit 1, SC2086 reported)" in 44889090612 und lokal | |
| T-44-21 | Tampering | Werkzeug-Images ausgetauscht | mitigate | zizmor und actionlint per sha256-Digest (8e4ae166) | E-07 |
| T-44-22 | Information Disclosure | zizmor online mit Token | mitigate | `--offline`, kein Token, `contents: read` (8e4ae166) | |
| T-44-23 | Repudiation | Online-only-Audits entfallen | accept | im Workflow-Kopf und docs/testing.md benannt (8e4ae166, c6142abb) | Begründung: bewusste Grenze (Pitfall 13), offline statt Token im Job |
| T-44-24 | Tampering | Gate per Entschärfung entfernt | mitigate | backend/tests/test_php_static_gates.py mit Regel und Negativprobe je Form (c6142abb), Python gates grün 44892647679 | |
| T-44-25 | Repudiation | Workflow-Commit ändert Gate ohne Strukturgate-Lauf | mitigate | python.yml paths um `.github/workflows/**` und `.github/dependabot.yml` erweitert (c6142abb) | E-06 |
| T-44-26 | Tampering | OCP-Matrix driftet vom Versionsfenster | mitigate | Strukturgate liest min/max aus info.xml, Proben beide Richtungen (c6142abb) | |
| T-44-27 | Spoofing | Commit-Autor und Trailer | mitigate | Owner-Freigaben "Push" und "go für push" nach Sicht auf Autor und Trailer (44-09); Autor street1983nk in allen Phase-Commits | |
| T-44-28 | Repudiation | rote CI durch Gate-Schwächung grün | mitigate | fd48fd0a echter Fix, Probe weiterhin Pflicht, Strukturtest ergänzt | |
| T-44-29 | Denial of Service | Push startet viele lange Workflows | accept | einmalig, Owner im Checkpoint 44-09 informiert; Rot-Beweis-Läufe mit unnötigen Jobs abgebrochen | Begründung: einmaliger Phasen-Push, Owner informiert |
| T-44-30 | Elevation of Privilege | gate-proof.yml mit unsicherem checkout | mitigate | nur `workflow_dispatch`, nie gestartet, Branch gelöscht, nie auf main (`git ls-files .github/workflows \| grep -c gate-proof` = 0) | |
| T-44-31 | Tampering | Taint-Probe gelangt in ein Release | mitigate | nur auf gelöschten Wegwerf-Branches; `git ls-files php/lib \| grep -c TaintProbe` = 0, StyleProof = 0; kein neuer Tag | |
| T-44-32 | Repudiation | Gate bleibt im Rot-Beweis grün | mitigate | php-cs blieb in Lauf 1 grün: als "Gate blind wegen Reizwahl" gemeldet, nicht schöngeredet; Owner E-15, Lauf 44909755992 rot | E-15 |
| T-44-33 | Repudiation | unbekannter Taint-Befund still gefixt | mitigate | 0 Befunde, kein Fix und keine Unterdrückung am Produkt (Produkt-Diff nur fa1836f5) | |
| T-44-34 | Tampering | lokales Rezept und CI driften | mitigate | Rezept liest OCP-Tags aus php.yml und ruft dieselben scripts/ci-Skripte (8f5aca31); lokal und CI gleiche Ausgabe | |
| T-44-35 | Denial of Service | fremde Container auf dem Host | mitigate | nur `docker run --rm`, keine Namen, keine Ports, seriell; vor jedem Lauf `docker ps` leer | |
| T-44-36 | Tampering | Probe im Arbeitsbaum unter php/lib | mitigate | Probe nur in Spiegel-Kopien bzw. gelöschten Branches; Zählung TaintProbe = 0 | |
| T-44-37 | Repudiation | Workflow-Befund oder secrets-outside-env still gefixt oder ignoriert | mitigate | Checkpoint 44-05 Task 2, Owner-Antworten E-11, E-12; Ist-Lauf deckungsgleich mit RESEARCH (6b384a00) | E-11, E-12 |
| T-44-38 | Tampering | Umbau eines run-Blocks ändert Verhalten | mitigate | Checkpoint 44-06 Task 2, Ausgabevergleich `php -r`, Route-Gate-Schritt nach E-13 unverändert, volle Suite, CI grün 44892647717 | E-13 |
| T-44-SC | Tampering | composer-Pakete und Werkzeug-Images | mitigate | exakte Pins, Lockfiles, composer validate und audit "No security vulnerability advisories found" (3x, 44892647717), Images per Digest | E-07 |

Accept-Zeilen: T-44-06 (E-05), T-44-07 (Begründung), T-44-23 (Begründung), T-44-29 (Begründung); jede mit E-ID oder Begründung.

Offene Punkte für secure-phase (ausdrücklich, keine stillen Annahmen):
- T-44-16 Restpunkt: NTFY_TOPIC bleibt nach E-12 Repo-Secret, bis der Owner es ins Environment notify einrichtet; zizmor ist durch `environment:` bereits grün.
- T-44-17 Restpunkt: kein CI-Lauf von probe-92d (nur workflow_dispatch); lokaler anonymer Fetch-Beleg liegt vor.
- Erfolgskriterium 5: secure-phase selbst steht noch aus.

## Deviations from Plan

1. [Plan-Reiz ungeeignet, Owner E-15] php-cs blieb in Lauf 1 grün ("0 of 131 files can be fixed"), weil nextcloud/coding-standard v1.5.0 Leerzeichen vor Semikolon in einer Konstanten-Deklaration nicht prüft. Kein Gate-Umbau; zweiter Rot-Beweis mit `if(true){echo 1;}` in php/lib/StyleProof.php, Lauf 44909755992 rot.
2. [Plan-Verify nicht wörtlich erfüllbar] `head_green.sh "$(git rev-parse origin/main)" ... "Workflow security lint" ...` endet auf fd48fd0a mit Exit 1, weil workflow-lint.yml dort mangels Pfadänderung nicht lief (bekannt aus 44-09). Ersatz: head_green.sh auf fd48fd0a mit den zwei übrigen Namen Exit 0 (alle acht Läufe success), Workflow security lint 44889090612 auf d2c07dad success bei identischem .github-Baum.
3. [T-44-17 Beleg] Der im Plan 44-05 erwartete CI-Beleg aus 44-09 entstand nicht (probe-92d nur workflow_dispatch). Ersatzbeleg: lokaler anonymer Tag-Fetch Exit 0.
4. E-15 steht in dieser SUMMARY; in 44-OWNER-DECISIONS.md ist sie noch nicht eingetragen (Auftrag: nur SUMMARY).

## Threat Flags

Keine neue Angriffsfläche. Die Wegwerf-Branches waren kurzzeitig öffentlich (Trust Boundary des Plans) und sind gelöscht.

## Commits

- keine Code-Commits in diesem Abschluss
- docs(44-10) SUMMARY (lokal, kein Push)

## Self-Check: PASSED

Lauf-IDs aus den Auftragsangaben bzw. aus head_green.sh; lokale Zahlen aus den Logs dieses Abschlusses; 39 Tabellenzeilen gleich 39 IDs per grep; TaintProbe, StyleProof, gate-proof je 0, kein Remote-Branch gate-proof-44*; alle 30 Phase-Commits mit Autor street1983nk, ohne Claude- oder Co-Authored-Zeilen; keine Gedankenstriche in dieser Datei.
