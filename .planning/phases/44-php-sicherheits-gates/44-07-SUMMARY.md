---
phase: 44-php-sicherheits-gates
plan: 07
subsystem: ci
tags: [zizmor, actionlint, shellcheck, positive-control, workflow-gate]
requires: [44-06]
provides: [workflow-lint.yml mit Jobs zizmor und actionlint, Gate-Skript mit Positivkontrollen, Probe-Workflow, lokales Rezept workflows]
affects: [44-08, 44-09, 44-10]
key-files:
  created:
    - scripts/ci/workflow_lint_gate.sh
    - .github/fixtures/workflow-lint-probe.yml
    - .github/workflows/workflow-lint.yml
  modified:
    - scripts/dev/php_gates_docker.sh
decisions:
  - "Werkzeuge laufen per docker run (Digest, --network none, Workspace read-only, --entrypoint sh) statt als Job-Container: actionlint-Image ist Alpine ohne bash mit USER guest, zizmor-Image minimal"
  - "Gate-Skript ist POSIX sh und nutzt nur eingebaute Shell-Befehle (kein bash, kein grep in den Images vorausgesetzt)"
requirements: [PRUEF-04]
completed: 2026-11-21
---

# Phase 44 Plan 07: Workflow-Sicherheits-Gate Summary

Neuer Workflow workflow-lint.yml mit den Jobs zizmor (1.32.0, Persona auditor, ab Medium, offline) und actionlint (1.7.12, shellcheck inklusive info und style); beide rufen scripts/ci/workflow_lint_gate.sh, das bei jedem Lauf gegen eine absichtlich unsichere Probe prüft, ob das Werkzeug noch sieht. Lokal grün, fünf Rotläufe belegt.

Stand: 21.11.2026. Kein Push.

## Task 1: Gate-Skript, Probe, lokales Rezept

- Shell der Images (ohne Containerstart, `docker image inspect` und `docker history`, RAM lag zu dem Zeitpunkt unter der Schwelle): zizmor-Image ist ein apko-Image mit `/bin/sh` (Build-Schritt `RUN /bin/sh -c ...`), Entrypoint `/usr/bin/zizmor`; actionlint-Image ist alpine-minirootfs 3.23.3 mit busybox-sh, `USER guest`, shellcheck unter /usr/local/bin. Entscheidung: Skript POSIX sh (`#!/bin/sh`, `set -eu`, kein pipefail), Aufruf überall mit `sh`, nur eingebaute Befehle (`case` statt grep für den SC2086-Nachweis, `${0%/*}` statt dirname).
- `.github/fixtures/workflow-lint-probe.yml`: Trigger issues, checkout ohne persist-credentials, `run: echo "${{ github.event.issue.title }}"`, undefinierte Property `steps.missing.outputs.value`, Schritt mit `env: PROBE_VALUE: probe` und `run: echo $PROBE_VALUE`. actionlint meldet dafür SC2086 (info), also keine Ersatzzeile nötig.
- workflow_lint_gate.sh: Modi `zizmor`, `actionlint`, ohne Argument beide; Persona als Konstante `ZIZMOR_PERSONA="auditor"` (E-04); `unset SHELLCHECK_OPTS` vor actionlint (E-03); zizmor 0 grün, 13/14 rot, sonst "failed to run"; Probe muss 13 oder 14 liefern; actionlint 0 grün, 1 rot, sonst rot; Probe muss Exit 1 und SC2086 liefern.
- php_gates_docker.sh: Unterbefehl `workflows` (je Werkzeug ein `docker run --rm --network none -v <repo>:/repo:ro -w /repo --entrypoint sh <Image@Digest>`, seriell), `all` läuft psalm, cs, workflows.
- Zählungen: `--min-severity medium` 2, `--offline` 2, Verbotsliste (`--no-exit-codes`, SARIF-Format, `-ignore`, `|| true`) 0, `workflow-lint-probe.yml` 2, `--persona` 2, `auditor` 3, `regular` 0, `unset SHELLCHECK_OPTS` 1, `--severity` 0, `SC2086` 4; Probe: `github.event.issue.title` 1, `echo $PROBE_VALUE` 1.

### Lokaler Grünlauf

RAM vor dem Docker-Start 5208500 KiB, keine fremden Container.

```
php_gates_docker: workflow gate: zizmor
No findings to report. Good job! (238 ignored)
zizmor: no finding of severity medium or above
zizmor: probe seen (exit 14)
workflow lint gate: green (zizmor)
php_gates_docker: workflow gate: actionlint
actionlint: no finding
actionlint: probe seen (exit 1, SC2086 reported)
workflow lint gate: green (actionlint)
php_gates_docker: workflow gate green (zizmor, actionlint)
```

Exit 0.

### Rotläufe (D-04), je in einer Scratch-Kopie (.github, Gate-Skript, leeres .git)

zizmor-Teile von a bis c liefen vor der RAM-Freigabe ohne Container mit `uvx zizmor==1.32.0` (gleiche Version), alle actionlint-Teile im gepinnten Image, seriell, RAM vor jedem Start über 4194304 KiB.

| Lauf | Änderung in der Kopie | Ergebnis |
|------|-----------------------|----------|
| a | workflow-lint.yml, erster checkout ohne `with: persist-credentials: false` | zizmor `warning[artipacked]` workflow-lint.yml:66, "zizmor reports findings of severity medium or above (exit 13, list above)", rc 1 |
| b | php.yml, Schritt php-cs: `run: echo "${{ github.event.pull_request.title }}"` | zizmor `error[template-injection]` php.yml:414, exit 14, rc 1; actionlint `"github.event.pull_request.title" is potentially untrusted ... [expression]`, "actionlint reports findings", rc 1 |
| c | Probe geleert | "the zizmor gate is blind: exit 3 on .github/fixtures/workflow-lint-probe.yml, expected 13 or 14", rc 1 |
| d | php.yml: `env: PROBE_VALUE: probe`, `run: echo $PROBE_VALUE` | actionlint `SC2086:info:1:6: Double quote to prevent globbing and word splitting [shellcheck]`, rc 1; dasselbe mit `-e SHELLCHECK_OPTS=--severity=warning` am Container, rc 1 |
| e | Probe ohne den SC2086-Schritt | "the actionlint gate is blind: no SC2086 on .github/fixtures/workflow-lint-probe.yml, shellcheck did not run or its threshold excludes info", rc 1 |

Gegenprobe zu d (unabhängiges Muster, ohne Gate-Skript): actionlint direkt im Image über die Kopie d mit `SHELLCHECK_OPTS=--severity=warning` meldet nichts, Exit 0. Die Variable senkt die Schwelle also wirklich; erst das `unset` im Skript hält den Befund rot.

Kopien danach gelöscht.

## Task 2: workflow-lint.yml

- `name: Workflow security lint`, englischer Kopfkommentar (was geprüft wird, eigener Workflow statt security.yml wegen Pitfall 12, offline und Grenze Pitfall 13, kein SARIF nach E-05, Persona E-04, Schwelle E-03, kein schedule mit Begründung). Das Wort SHELLCHECK_OPTS steht nicht in der Datei (Zählung 0).
- Trigger: push mit `branches: ['**']`, Tag `v[0-9]+.[0-9]+.[0-9]+`, paths `.github/**` und `scripts/ci/workflow_lint_gate.sh`; pull_request mit denselben paths. `permissions: contents: read`, concurrency `workflow-lint-${{ github.event_name }}-${{ github.ref }}`.
- Zwei Jobs, ubuntu-24.04, `timeout-minutes: 10`, checkout mit dem Repo-Pin und `persist-credentials: false`, dann `docker run` mit Image per Digest im Schritt-env. Kein continue-on-error, kein security-events.
- Entscheidung gegen `container:`: actions/checkout bräuchte im Container Node und Schreibrechte als USER guest auf dem Workspace; `docker run` mit read-only Mount und ohne Netz ist robuster und identisch mit dem lokalen Rezept. Vom Plan als Alternative vorgesehen.
- test_workflow_tag_triggers.py verlangt keinen PATHS_BEFORE-Eintrag für neue Dateien (nur die fünf dort geführten), daher unverändert.
- Zählungen: `scripts/ci/workflow_lint_gate.sh` 5, Digest zizmor 1, Digest actionlint 1, `^    timeout-minutes:` 2, `continue-on-error` 0, `security-events` 0, `'.github/**'` 2, `SHELLCHECK_OPTS` 0.
- pytest test_workflow_pins, test_workflow_tag_triggers, test_workflow_size, test_workflow_contexts, test_public_artifacts: 123 passed.

## Deviations from Plan

1. [Rule 3] Jobs ohne `container:`, Werkzeuge per `docker run` (siehe Task 2), vom Plan als Ausweichform erlaubt.
2. [Rule 2] `--network none` an jedem Werkzeug-Container (CI und lokal): zizmor läuft ohnehin offline, actionlint braucht kein Netz.
3. Zeitliche Abweichung: der freie RAM lag über eine Stunde unter der Docker-Schwelle; Shell-Erkundung deshalb per `docker image inspect`/`docker history` statt `docker run`, zizmor-Rotläufe per uvx. Grünlauf und actionlint-Rotläufe nach RAM-Freigabe durch den Owner im Container.
4. Commit zuerst ohne Ausführbar-Bit (Windows, core.filemode), lokal per amend auf 100755 korrigiert wie die übrigen Gate-Skripte; nicht gepusht.

## Threat Flags

Keine neue Angriffsfläche über das Threat-Register hinaus. T-44-18 bis T-44-22 wie geplant behandelt, T-44-23 (Online-Audits) bewusst akzeptiert und im Workflow-Kopf benannt, Doku in 44-08.

## Commits

- 8e4ae166 ci(44-07): zizmor und actionlint als Gate über alle Workflows
- SUMMARY, STATE und ROADMAP im Abschluss-Commit docs(44-07)

## Self-Check: PASSED

Commit 8e4ae166 vorhanden, Modus 100755 für workflow_lint_gate.sh; alle vier Dateien vorhanden; lokales Rezept workflows Exit 0; fünf Rotläufe rot mit erwarteter Meldung.
