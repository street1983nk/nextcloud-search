---
phase: 44-php-sicherheits-gates
plan: 08
subsystem: ci
tags: [structural-gate, pytest, docs, triggers, e-06]
requires: [44-07]
provides: [Strukturgate test_php_static_gates.py, python.yml-Trigger auf Workflow- und dependabot-Commits, Doku der Phase-44-Gates]
affects: [44-09, 44-10]
key-files:
  created:
    - backend/tests/test_php_static_gates.py
  modified:
    - .github/workflows/python.yml
    - backend/tests/test_workflow_tag_triggers.py
    - docs/testing.md
decisions:
  - "Owner-Ausnahmen sind an E-ID, Datei und Regel gebunden (OWNER_EXCEPTIONS E-13: php.yml, SC2016); dieselbe E-ID in einer anderen Datei oder für eine andere Regel wird gemeldet"
  - "Zusatzregel: @psalm-suppress und @psalm-taint-escape in den von Psalm analysierten Dateien verboten (heute keine Ausnahme)"
requirements: [PRUEF-02, PRUEF-03, PRUEF-04]
completed: 2026-11-21
---

# Phase 44 Plan 08: Strukturgate und Doku Summary

backend/tests/test_php_static_gates.py hält die vier Gates der Phase (psalm-taint mit OCP-Matrix gleich dem Versionsfenster aus info.xml, php-cs, zizmor, actionlint), ihre Skripte, Schwellen und Positivkontrollen sowie psalm.xml und die Ausnahmen unter .github fest; python.yml startet nach E-06 auch bei reinen Workflow- und dependabot-Commits; docs/testing.md beschreibt je Gate Prüfung, Positivkontrolle, Grenze und das lokale Rezept.

Stand: 21.11.2026. Kein Push.

## Task 1: Strukturgate (TDD)

- Scanner: `expected_ocp_majors(info_xml)`, `scan_php_workflow(text, info_xml)`, `scan_lint_workflow(text)`, `scan_gate_script(name, text)`, `scan_psalm_config(text, baseline_exists)`, `scan_psalm_sources(texts)` (zusätzlich, siehe Abweichungen), `scan_lint_exceptions(texts, zizmor_config_exists)`. XML über ElementTree mit `noqa: S314` nach dem Muster von test_exapp_surface.py (Dateien des Repos), Namespace von psalm.xml beachtet.
- Regeln laut Modul-Docstring 1 bis 7, Abschnitt "**The limit.**".
- Pflicht im Gate-Skript: `--min-severity medium`, `auditor`, `unset SHELLCHECK_OPTS`, `SC2086`, Probe-Name; `--min-severity medium`, `--offline`, `--persona` und Probe je mindestens zweimal (echter Lauf und Probe). Verboten: `--no-exit-codes`, `--format sarif`, `--format=sarif`, `-ignore`, `|| true`, Personas regular und pedantic, jeder `--persona`-Wert außer auditor oder `${ZIZMOR_PERSONA}` mit `ZIZMOR_PERSONA="auditor"`, `--severity`, Zuweisung an SHELLCHECK_OPTS. workflow-lint.yml darf SHELLCHECK_OPTS und `--severity` gar nicht nennen.
- RED: temporäre Kopie mit leeren Scanner-Stubs (`return []`, `return set()`, per sed erzeugt, danach gelöscht): `50 failed, 14 passed` (die 14 sind die sauberen Proben und die Tests, die ohne Befund grün sein müssen).
- GREEN: `64 passed`. `-k matrix_majors_match_info_xml`: 1 Test; `-k "max_version or min_version"`: 2 Tests (Probe max-version 36 meldet "the ocp matrix lacks major 36 of info.xml", Probe min-version 34 meldet "the ocp matrix has major 33 outside info.xml"); `-k unset_shellcheck_opts`: 1; `-k sc2086`: 1. `grep -c "def expected_ocp_majors"`: 1.
- Echter Baum: genau eine Ausnahmezeile unter .github, E-13 SC2016 in php.yml (eigener Test).
- ruff check, ruff format --check, pyright basic (latest) und vulture (`src tests --min-confidence 80`) grün.

## Task 2: Trigger, Doku, volle Runde

- E-06 option-a: python.yml push und pull_request um `.github/workflows/**` und `.github/dependabot.yml` erweitert (englischer Kommentar), PATHS_BEFORE["python.yml"] mit Kommentar "Widened by phase 44 (owner decision E-06)". Zählung `'.github/workflows/**'` in python.yml: 2; in test_workflow_tag_triggers.py: 1.
- docs/testing.md: neuer Abschnitt "## The gates of phase 44, and the boundary of each one" nach Phase 13 (Tabelle je Gate mit Rot, Positivkontrolle, Grenze; zwei Grenzen aus 44-06: Digest-Erneuerung per `docker buildx imagetools inspect`, secrets-outside-env nur per Namens-Lesebeleg aus 44-09; Trigger; E-01 bis E-14 je ein Satz; Unterabschnitt "Running the phase 44 gates locally"). Der lokale Abschnitt nennt `workflows`, der Satz aus Phase 42 ist auf den heutigen Stand gebracht, die Tabelle der textuellen Gates hat eine Zeile für test_php_static_gates.py. Zählungen: Abschnitt 1, `php_gates_docker.sh` 9, `E-0[1-8]` 9, `imagetools` 1. Gedankenstriche vorher 0, nachher 0.
- test_public_artifacts fand im ersten Entwurf "pass:" (Familie schluesselwort-mit-wert); umformuliert zu "in the same run, a probe", danach grün.

### Volle lokale Runde (seriell, RAM vor jedem Docker-Start über 4194304 KiB, keine fremden Container)

- 11 Gate-Testdateien gemeinsam: `341 passed`.
- `bash scripts/dev/php_gates_docker.sh all` (MemFree 5151792 KiB): Exit 0. Psalm je OCP v33.0.9, v34.0.6, v35.0.3 "0 findings, probe found 3"; php-cs "0 violations, probe seen"; zizmor "No findings ... (238 ignored)", Probe Exit 14; actionlint "no finding", Probe Exit 1 mit SC2086.
- `bash scripts/dev/phpunit_docker.sh` (MemFree 5183556 KiB): `OK (1222 tests, 7765 assertions)`, Exit 0.
- ruff check backend: "All checks passed!"; ruff format --check: 259 files already formatted; pyright basic: 0 errors; vulture: Exit 0.
- Volle Python-Suite (`PYTHONUTF8=1 uv run --no-sync python -m pytest -q` in backend): `7234 passed, 303 skipped, 3 warnings in 812.40s`, Exit 0 (vor 44-07/44-08: 7167 passed).

## Deviations from Plan

1. [Rule 2] Zusätzlicher Scanner `scan_psalm_sources`: `@psalm-suppress` und `@psalm-taint-escape` in php/lib, php/templates und php/appinfo/routes.php werden gemeldet (Interfaces nennen "suppress für Tainted*" als Entschärfungsform; ohne diese Regel ginge eine Suppression im Code am Gate vorbei). Heute keine Fundstelle, keine Ausnahme.
2. [Rule 2] Ausnahmen sind nicht nur an die E-ID gebunden, sondern auch an Datei und Regel (E-13 gilt nur für SC2016 in php.yml), mit Proben für fremde Datei und fremde Regel; dazu ein Test "genau eine Ausnahme heute" nach Vorgabe des Koordinators.
3. Die Änderungen dieses Plans lagen während 44-07 bereits im Arbeitsbaum (Wartezeit auf RAM); der 44-07-Commit enthielt sie nicht (explizite Pfade).

## TDD Gate Compliance

RED wurde gegen eine temporäre Stub-Kopie belegt (50 failed), nicht als eigener test-Commit: der Plan sieht einen gemeinsamen Commit `test(44-08): ...` vor, und Testdatei und Implementierung sind dieselbe Datei.

## Threat Flags

Keine neue Angriffsfläche. T-44-24 (jede Entschärfungsform mit Regel und Negativprobe), T-44-25 (Trigger nach E-06) und T-44-26 (Matrix gegen info.xml, beide Richtungen) wie geplant behandelt.

## Commits

- c6142abb test(44-08): Strukturgate gegen stilles Entfernen der PHP- und Workflow-Gates, Doku
- SUMMARY, STATE und ROADMAP im Abschluss-Commit docs(44-08)

## Self-Check: PASSED

Commit c6142abb vorhanden mit den vier Dateien aus files_modified (workflow-lint.yml unverändert, option-b nicht gewählt); Strukturgate 64 passed; php_gates_docker.sh all, phpunit_docker.sh und volle Suite grün.
