---
phase: 44-php-sicherheits-gates
plan: 09
subsystem: ci
tags: [push, ci-green, positive-controls, environments, secrets, t-44-16]
requires: [44-08]
provides: [Phase-44-Kopf fd48fd0a auf main in CI grün, Log-Belege der Positivkontrollen, Namens-Lesebeleg der Environment-Secrets (Abnahme T-44-16)]
affects: [44-10]
key-files:
  created:
    - .planning/phases/44-php-sicherheits-gates/44-09-SUMMARY.md
  modified:
    - scripts/ci/psalm_taint_gate.sh
    - backend/tests/test_php_static_gates.py
    - LICENSES/MIT.txt
decisions:
  - "Workflow security lint lief auf fd48fd0a nicht (paths-Filter, keine Änderung unter .github/ und am Gate-Skript seit d2c07dad); maßgeblich ist der grüne Lauf 44889090612 auf d2c07dad mit identischem .github-Baum"
  - "Die Repo-Secrets APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY hat auf ausdrückliche Owner-Anweisung der Orchestrator gelöscht, nicht der Owner selbst (Abweichung von E-04 und Task 3)"
requirements: [PRUEF-02, PRUEF-03, PRUEF-04]
completed: 2026-11-21
---

# Phase 44 Plan 09: Push und grüner CI-Kopf Summary

Die Commits der Phase 44 liegen auf main (Kopf fd48fd0a), alle Läufe des Kopfs sind grün, jede Positivkontrolle (Psalm je OCP-Bein, php-cs, composer audit, zizmor, actionlint) ist im CI-Log belegt, und die drei umgezogenen Secrets liegen nur noch in ihren Environments (T-44-16 abgenommen).

Stand: 21.11.2026.

## Task 1: Push-Freigabe

- Erster Push d2c07dad nach Owner-Wort "Push" (21.11.2026).
- Zweiter Push fd48fd0a (Fix, siehe Abweichungen) nach Owner-Wort "go für push" (21.11.2026).

## Task 2: CI-Kopf grün, Positivkontrollen

`git rev-parse HEAD` gleich `git rev-parse origin/main` gleich `fd48fd0a723be9b0d9cdbe1bbb740175b759ecf1`.

head_green.sh auf fd48fd0a: Exit 0, alle acht Läufe success:

```
44892647684 Multi-arch image success
44892647752 Resilience success
44892647711 Integration success
44892647685 HaRP deploy success
44892647708 Security scans success
44892647717 PHP and store metadata gates success
44892647679 Python gates success
44892647726 OpenSSF Scorecard success
```

### Workflow security lint

workflow-lint.yml startet nur auf `.github/**` und `scripts/ci/workflow_lint_gate.sh`. fd48fd0a ändert nur LICENSES/MIT.txt, backend/tests/test_php_static_gates.py und scripts/ci/psalm_taint_gate.sh (`git diff --stat d2c07dad fd48fd0a`), deshalb gibt es auf fd48fd0a keinen Lauf; ein Aufruf von head_green.sh mit dem Namen "Workflow security lint" auf fd48fd0a würde mangels Lauf mit Exit 1 enden. Der geprüfte Stand ist trotzdem identisch: der .github-Baum und das Gate-Skript sind auf d2c07dad und fd48fd0a gleich. Maßgeblicher Lauf:

```
44889090612 Workflow security lint d2c07dad completed success push 2026-11-21T09:20:12Z
```

(`gh run list --workflow "Workflow security lint"` zeigt keinen anderen Lauf.)

### Log-Belege

Lauf 44892647717 (PHP and store metadata gates, fd48fd0a):

```
Psalm taint analysis against OCP v33.0.9   taint findings: 0
Psalm taint analysis against OCP v33.0.9   psalm taint gate: 0 findings, probe found 3
Psalm taint analysis against OCP v34.0.6   taint findings: 0
Psalm taint analysis against OCP v34.0.6   psalm taint gate: 0 findings, probe found 3
Psalm taint analysis against OCP v35.0.3   taint findings: 0
Psalm taint analysis against OCP v35.0.3   psalm taint gate: 0 findings, probe found 3
php-cs-fixer dry run (nextcloud/coding-standard)   php cs gate: 0 violations, probe seen
composer validate and audit   No security vulnerability advisories found.   (3 x)
```

- "probe seen" gibt scripts/ci/php_cs_gate.sh nur aus, wenn die cs-Probe mit Exit 8 endet (Zeile 95 `if [ "${probe_rc}" -ne 8 ]`), damit ist Exit 8 belegt.
- Die drei composer-audit-Zeilen kommen der Reihe nach aus den Schritten mit `working-directory: php`, `php/tools/psalm` und `php/tools/php-cs-fixer` (php.yml Zeilen 278, 290, 300).

Lauf 44889090612 (Workflow security lint, d2c07dad):

```
zizmor (persona auditor, medium and above)   No findings to report. Good job! (238 ignored)
zizmor (persona auditor, medium and above)   zizmor: probe seen (exit 14)
actionlint (shellcheck of every severity)    actionlint: no finding
actionlint (shellcheck of every severity)    actionlint: probe seen (exit 1, SC2086 reported)
```

probe-92d.yml lief auf keinem der beiden Köpfe (nicht in der Laufliste), Annahme A6 bleibt damit ohne CI-Beleg aus diesem Plan.

## Task 3: Repo-Secrets und Namens-Lesebeleg (Abnahme T-44-16)

E-11 und E-12: Umzug für APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY; NTFY_TOPIC bleibt Repo-Secret.

Vorher (Orchestrator, nur Namen): Repo APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY, NTFY_TOPIC; Environment release APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY; app-store APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY; app-store-delete APPSTORE_TOKEN; notify leer.

grep-Beleg (jede Verwendung, umschließender Job per awk über die Job-Einrückung, keine `secrets: inherit`, kein `toJSON(secrets)`, kein `secrets[`):

```
.github/workflows/issue-notify.yml:27 job=notify environment=notify          (NTFY_TOPIC)
.github/workflows/release.yml:323 job=archives environment=release          (APP_PRIVATE_KEY)
.github/workflows/release.yml:378 job=archives environment=release          (APP_PRIVATE_KEY)
.github/workflows/release.yml:444 job=archives environment=release          (BACKEND_PRIVATE_KEY)
.github/workflows/store-release-delete.yml:78 job=remove environment=app-store-delete (APPSTORE_TOKEN)
.github/workflows/store-submit.yml:90 job=submit environment=app-store      (APPSTORE_TOKEN)
.github/workflows/store-submit.yml:91 job=submit environment=app-store      (APP_PRIVATE_KEY)
.github/workflows/store-submit.yml:92 job=submit environment=app-store      (BACKEND_PRIVATE_KEY)
.github/workflows/store-submit.yml:124 job=submit environment=app-store     (APPSTORE_TOKEN)
.github/workflows/store-submit.yml:178 job=submit environment=app-store     (APPSTORE_TOKEN)
```

deploy-harp.yml:2671 nennt `secrets.APP_PRIVATE_KEY` nur in einem Kommentar (keine Verwendung).

Lesebelege nachher (21.11.2026, seriell, nur Namen):

- `gh api repos/street1983nk/nextcloud-search/actions/secrets`: `NTFY_TOPIC`
- environments/release/secrets: `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY`
- environments/app-store/secrets: `APPSTORE_TOKEN`, `APP_PRIVATE_KEY`, `BACKEND_PRIVATE_KEY`
- environments/app-store-delete/secrets: `APPSTORE_TOKEN`
- environments/notify/secrets: leer
- environments: app-store, app-store-delete, notify, release, je `{"custom_branch_policies":true,"protected_branches":false}`
- deployment-branch-policies je Environment (release, app-store, app-store-delete, notify): `main branch`, `v* tag`

Automatisierte Prüfung aus Task 3 je Environment (release: APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY; app-store: alle drei; app-store-delete: APPSTORE_TOKEN): `automated check exit 0`, kein Secret mehr auf Repo-Ebene, jedes im zugeordneten Environment.

Grenze: Der Release- und Store-Pfad mit Environment ist erst im nächsten echten Release- bzw. Store-Lauf belegt (store-release-delete wartet dort auf die Freigabe durch street1983nk), issue-notify erst beim nächsten issues-Ereignis. NTFY_TOPIC bleibt nach E-12 Repo-Secret, bis der Owner es ins Environment notify einrichtet.

## Deviations from Plan

1. [Rule 1 - Bug] Erster Push d2c07dad rot (Läufe 44889090525 und 44889090488).
   - Psalm 6.20.10 beendet sich bei Taint-Befund mit `--report` und gesetztem `GITHUB_WORKFLOW` mit 0 statt 2, die Probe im Gate wurde damit auf dem Runner nicht erkannt. Fix: `env -u GITHUB_WORKFLOW` für den Psalm-Aufruf in scripts/ci/psalm_taint_gate.sh, Strukturtest in backend/tests/test_php_static_gates.py hält das fest. Keine Gate-Schwächung: die Probe muss weiterhin gefunden werden.
   - REUSE: LICENSES/MIT.txt fehlte (MIT-Kopf des kopierten Taint-Plugins), Lizenztext ergänzt.
   - Commit fd48fd0a "fix(44): Psalm-Taint-Gate auf Runnern scharf, MIT-Lizenztext für REUSE", nach erneuter Owner-Freigabe "go für push" gepusht, danach alle Läufe grün.
2. Abweichung von E-04 und Task 3 (Repo-Secrets löscht nur der Owner): Der Owner hat am 21.11.2026 ausdrücklich gesagt "Mach du das ich bin nicht am Rechner". Daraufhin hat der Orchestrator nach Prüfung der Environment-Secrets per `gh secret delete` die Repo-Secrets APPSTORE_TOKEN, APP_PRIVATE_KEY und BACKEND_PRIVATE_KEY gelöscht. Der Executor dieses Abschlusses hat keinen `gh secret`-Schreibaufruf ausgeführt, nur Lesebelege.
3. Workflow security lint ohne Lauf auf fd48fd0a (paths-Filter), Beleg über den grünen Lauf 44889090612 auf d2c07dad mit identischem .github-Baum, siehe oben.

## Threat Flags

Keine neue Angriffsfläche. T-44-27 (Autor und Trailer vor Push vom Owner gesehen), T-44-28 (Fix ohne Gate-Schwächung, Probe weiterhin Pflicht), T-44-16 (Namens-Lesebeleg oben, automatisierte Prüfung Exit 0).

## Commits

- d2c07dad und Vorgänger aus 44-01 bis 44-08 (gepusht)
- fd48fd0a fix(44): Psalm-Taint-Gate auf Runnern scharf, MIT-Lizenztext für REUSE (gepusht)
- docs(44-09) SUMMARY (lokal, kein Push)

## Self-Check: PASSED

fd48fd0a gleich origin/main; alle Lauf-IDs oben stammen aus `gh run list` bzw. head_green.sh; drei Zeilen "taint findings: 0" und drei "probe found" im Lauf 44892647717; php-cs-, zizmor- und actionlint-Positivkontrolle belegt; Namens-Lesebeleg und automatisierte Prüfung Exit 0.
