---
phase: 44-php-sicherheits-gates
plan: 01
subsystem: ci-sicherheits-gates
tags: [owner-entscheidungen, zizmor, actionlint, shellcheck, psalm, php-cs-fixer]
requires: []
provides:
  - "44-OWNER-DECISIONS.md mit E-01 bis E-08"
  - "Open Questions in 44-RESEARCH.md als RESOLVED"
  - "Pläne 44-05 bis 44-08 und 44-10 an E-03 (info/style) und E-04 (auditor) angepasst"
affects: [44-02, 44-03, 44-04, 44-05, 44-06, 44-07, 44-08, 44-09, 44-10]
tech-stack:
  added: []
  patterns: ["Owner-Entscheidung als E-ID, Ausnahmen nur ab E-09 mit Owner-Wortlaut"]
key-files:
  created:
    - .planning/phases/44-php-sicherheits-gates/44-OWNER-DECISIONS.md
  modified:
    - .planning/phases/44-php-sicherheits-gates/44-RESEARCH.md
    - .planning/phases/44-php-sicherheits-gates/44-05-PLAN.md
    - .planning/phases/44-php-sicherheits-gates/44-06-PLAN.md
    - .planning/phases/44-php-sicherheits-gates/44-07-PLAN.md
    - .planning/phases/44-php-sicherheits-gates/44-08-PLAN.md
    - .planning/phases/44-php-sicherheits-gates/44-10-PLAN.md
decisions:
  - "E-01: cache-poisoning in python.yml mit enable-cache: false beheben"
  - "E-02: Dependabot-cooldown 14 Tage an allen Einträgen"
  - "E-03: shellcheck-Schwelle inkl. info und style, alle 19 Befunde echt beheben, Gate ohne Abschwächung"
  - "E-04: zizmor-Persona auditor als Gate, 13 Zusatzbefunde beheben, secrets-outside-env als Owner-Frage"
  - "E-05: kein SARIF-Upload zu GitHub Code Scanning"
  - "E-06: .github/workflows/** in die paths von python.yml"
  - "E-07: Psalm 6.20.10 + Taint-Plugin, php-cs-fixer + coding-standard, zizmor, actionlint freigegeben (nur CI/Dev)"
  - "E-08: Rot-Beweis auf Wegwerf-Branch gate-proof-44, Löschung erst nach Owner-Freigabe"
metrics:
  duration: "ca. 25 min"
  completed: 2026-11-21
  tasks: 3
  files: 7
---

# Phase 44 Plan 01: Owner-Entscheidungen zu den Sicherheits-Gates Summary

Owner-Entscheide E-01 bis E-08 vom 21.11.2026 im Wortlaut festgehalten (strenger als die Empfehlung: zizmor-Persona auditor, shellcheck inkl. info/style), Open Questions der Recherche aufgelöst und die Folgepläne 44-05 bis 44-08 an die strengeren Schwellen angepasst.

## Tasks

| Task | Name | Ergebnis | Commit |
|------|------|----------|--------|
| 1 | Checkpoint E-01 bis E-06, E-08 | Owner-Antwort "Strenger: auditor + info" (AskUserQuestion, 21.11.2026), vom Orchestrator übermittelt | - |
| 2 | Checkpoint E-07 Paketfreigabe | freigegeben, nur CI/Dev | - |
| 3 | Entscheidungen festhalten, Open Questions auflösen | 44-OWNER-DECISIONS.md, 44-RESEARCH.md | e71886fe |
| Zusatz | Pläne 44-05 bis 44-08 (und 44-10) an E-03/E-04 anpassen | Auftrag des Orchestrators | 124a13e6 |

Abnahme Task 3: `grep -c "^## E-0[1-8]"` liefert 8, `## Open Questions (RESOLVED)` 1, `RESOLVED: siehe E-0` 6, Gedankenstriche 0, Autor street1983nk, kein Push (main ahead).

## Planänderungen durch E-03 (info/style) und E-04 (auditor)

Die geprüfte Fassung ging von E-03 option-b (`SHELLCHECK_OPTS=--severity=warning`, nur SC2086-Quoting-Lücken) und E-04 option-a (Persona regular, 13 auditor-Befunde nur als Liste) aus.

- **44-05:** zizmor-Ist-Lauf und Verify mit `--persona auditor` (erwartet 68 Befunde ab Medium statt 55). Checkpoint Task 2 ist nicht mehr nur bedingt: die 10 secrets-outside-env-Befunde (issue-notify, release, store-release-delete, store-submit) gehen immer an den Owner (Environment mit Secret-Umzug durch den Owner oder begründet akzeptieren, E-09 ff.), weil der Fix eine Repo-Einstellung braucht. Lesebeleg der Environments mit einem `gh api`-Aufruf.
- **44-06:** größter Mehraufwand. Alle 19 shellcheck-Hinweise werden echt behoben, auch die zwei absichtlichen `php -r '...'`-Blöcke (SC2016) mit Ausgabevergleich; Digest-Pins für `mariadb:11.4` und `postgres:16` in integration.yml; scorecard.yml ohne `read-all`; `environment:` nach E-09 ff. Neuer bedingter Checkpoint Task 2 (Fundstelle ohne verhaltensgleichen Fix), alter Task 2 wird Task 3; `autonomous: false`; files_modified um issue-notify, release, store-release-delete, store-submit erweitert; neuer Threat T-44-38; T-44-16 jetzt mitigate.
- **44-07:** Gate-Skript fest mit Persona auditor, actionlint ohne SHELLCHECK_OPTS und mit `unset SHELLCHECK_OPTS`; vierter lokaler Rotlauf (ungequotete Variable, nur SC2086 info, muss rot sein, auch mit geerbtem `--severity=warning`); neue Grep-Abnahmen.
- **44-08:** Strukturgate meldet zusätzlich: Gate-Skript ohne auditor oder mit regular, `--severity` oder `SHELLCHECK_OPTS=`-Zuweisung, SHELLCHECK_OPTS in workflow-lint.yml, eine zizmor-Konfigurationsdatei und `# shellcheck disable`/`# zizmor: ignore` unter .github ohne Owner-E-ID; neue reine Funktion `scan_lint_exceptions` mit Proben; Doku nennt die shellcheck-Version aus dem Image.
- **44-10:** nur das Beispiel offener Punkte (statt "auditor-Befunde bei E-04 option-a" jetzt akzeptierte secrets-outside-env E-09 ff.).
- **Unverändert:** 44-02, 44-03, 44-04, 44-09.

## Deviations from Plan

- Task 1 und 2 wurden nicht vom Executor gefragt, sondern vom Orchestrator per AskUserQuestion beantwortet und übergeben; Wortlaut und Datum stehen in 44-OWNER-DECISIONS.md.
- Zusätzlich zum Plan (Auftrag des Orchestrators): Anpassung der Pläne 44-05 bis 44-08 und 44-10 in einem eigenen Commit 124a13e6.
- E-07: der Owner-Wortlaut nennt nextcloud/ocp, php-cs-fixer/shim und kubawerlos/php-cs-fixer-custom-fixers nicht einzeln; sie sind als Analysegrundlage von Psalm bzw. Pflichtabhängigkeiten von coding-standard unter die Freigabe gefasst und so in E-07 vermerkt. Falls der Owner das anders sieht, vor 44-02 klären.

## Offene Punkte für den Owner

- secrets-outside-env (10 Befunde) kommt in 44-05 Task 2 als Frage; ein Environment mit Freigaberegeln kann Release- und Store-Läufe anhalten.
- Neue Jobs aus 44-02/44-04 (psalm-taint, php-cs) müssen jetzt auch shellcheck info/style bestehen; Befunde dort erscheinen in 44-05 Task 1 als "unbekannt" und gehen in den Checkpoint.

## Self-Check: PASSED

- FOUND: .planning/phases/44-php-sicherheits-gates/44-OWNER-DECISIONS.md
- FOUND: e71886fe, 124a13e6
