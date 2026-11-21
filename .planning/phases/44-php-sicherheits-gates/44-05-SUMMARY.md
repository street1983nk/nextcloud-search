---
phase: 44-php-sicherheits-gates
plan: 05
status: checkpoint-task-2
---

# Phase 44 Plan 05: Workflow-Befunde Teil 1 (Zwischenstand am Checkpoint Task 2)

Stand: 21.11.2026, HEAD 7c860fbb. Task 1 erledigt, Task 2 wartet auf den Owner, Task 3 offen.

## Task 1: Ist-Lauf

### zizmor 1.32.0, `--persona auditor --min-severity medium`, Wurzel `.`

Aufruf wie in 44-05-PLAN.md (interfaces). Exit 14 (High-Befunde vorhanden). Schlusszeile: `306 findings (238 ignored, 4 safe fixes, 51 unsafe fixes): 0 informational, 0 low, 64 medium, 4 high`.

Zählung je Audit:

| Audit | Schwere | Anzahl | RESEARCH/E-04 | Klasse |
|-------|---------|--------|---------------|--------|
| artipacked | Medium | 49 | 49 | bekannt |
| secrets-outside-env | Medium | 10 | 10 | bekannt |
| dependabot-cooldown | Medium | 4 | 4 | bekannt |
| excessive-permissions | Medium | 1 | 1 | bekannt |
| cache-poisoning | High | 2 | 2 | bekannt |
| unpinned-images | High | 2 | 2 | bekannt |
| Summe | | 68 | 68 | |

artipacked je Datei (deckt sich mit der Verteilung im Plan): coverage-e2e 5, deploy-harp 2, docker 1, integration 12, measure 2, php 5, probe-92d 1, python 2, rc-version-proof 4, release 2, resilience 5, security 3, smb-acl-measure 2, store-release-delete 1, store-submit 1, setup-test-nc/action.yml 1.

Alle 68 Fundstellen (Datei:Zeile:Spalte, Ausgabe gekürzt auf die Fundzeile; die Langform mit Codeausschnitten hat 988 Zeilen und wird nicht kopiert):

```
warning[artipacked]: ./.github/actions/setup-test-nc/action.yml:196:7
warning[dependabot-cooldown]: ./.github/dependabot.yml:24:5
warning[dependabot-cooldown]: ./.github/dependabot.yml:52:5
warning[dependabot-cooldown]: ./.github/dependabot.yml:78:5
warning[dependabot-cooldown]: ./.github/dependabot.yml:133:5
warning[artipacked]: ./.github/workflows/coverage-e2e.yml:111:9
warning[artipacked]: ./.github/workflows/coverage-e2e.yml:124:9
warning[artipacked]: ./.github/workflows/coverage-e2e.yml:131:9
warning[artipacked]: ./.github/workflows/coverage-e2e.yml:137:9
warning[artipacked]: ./.github/workflows/coverage-e2e.yml:144:9
warning[artipacked]: ./.github/workflows/deploy-harp.yml:523:9
warning[artipacked]: ./.github/workflows/deploy-harp.yml:530:9
warning[artipacked]: ./.github/workflows/docker.yml:91:9
warning[artipacked]: ./.github/workflows/integration.yml:168:9
warning[artipacked]: ./.github/workflows/integration.yml:175:9
warning[artipacked]: ./.github/workflows/integration.yml:600:9
warning[artipacked]: ./.github/workflows/integration.yml:607:9
warning[artipacked]: ./.github/workflows/integration.yml:1256:9
warning[artipacked]: ./.github/workflows/integration.yml:1263:9
warning[artipacked]: ./.github/workflows/integration.yml:2414:9
warning[artipacked]: ./.github/workflows/integration.yml:2421:9
warning[artipacked]: ./.github/workflows/integration.yml:3275:9
warning[artipacked]: ./.github/workflows/integration.yml:3282:9
warning[artipacked]: ./.github/workflows/integration.yml:4721:9
warning[artipacked]: ./.github/workflows/integration.yml:4728:9
error[unpinned-images]: ./.github/workflows/integration.yml:1101:9
error[unpinned-images]: ./.github/workflows/integration.yml:1116:9
warning[secrets-outside-env]: ./.github/workflows/issue-notify.yml:22:27
warning[artipacked]: ./.github/workflows/measure.yml:116:9
warning[artipacked]: ./.github/workflows/measure.yml:439:9
warning[artipacked]: ./.github/workflows/php.yml:102:9
warning[artipacked]: ./.github/workflows/php.yml:145:9
warning[artipacked]: ./.github/workflows/php.yml:460:9
warning[artipacked]: ./.github/workflows/php.yml:467:9
warning[artipacked]: ./.github/workflows/php.yml:627:9
warning[artipacked]: ./.github/workflows/probe-92d.yml:91:9
warning[artipacked]: ./.github/workflows/python.yml:121:9
warning[artipacked]: ./.github/workflows/python.yml:243:9
error[cache-poisoning]: ./.github/workflows/python.yml:125:9
error[cache-poisoning]: ./.github/workflows/python.yml:247:9
warning[artipacked]: ./.github/workflows/rc-version-proof.yml:99:9
warning[artipacked]: ./.github/workflows/rc-version-proof.yml:106:9
warning[artipacked]: ./.github/workflows/rc-version-proof.yml:153:9
warning[artipacked]: ./.github/workflows/rc-version-proof.yml:162:9
warning[artipacked]: ./.github/workflows/release.yml:115:9
warning[artipacked]: ./.github/workflows/release.yml:118:9
warning[secrets-outside-env]: ./.github/workflows/release.yml:316:32
warning[secrets-outside-env]: ./.github/workflows/release.yml:371:32
warning[secrets-outside-env]: ./.github/workflows/release.yml:437:36
warning[artipacked]: ./.github/workflows/resilience.yml:125:9
warning[artipacked]: ./.github/workflows/resilience.yml:132:9
warning[artipacked]: ./.github/workflows/resilience.yml:738:9
warning[artipacked]: ./.github/workflows/resilience.yml:745:9
warning[artipacked]: ./.github/workflows/resilience.yml:1235:9
warning[excessive-permissions]: ./.github/workflows/scorecard.yml:18:1
warning[artipacked]: ./.github/workflows/security.yml:34:9
warning[artipacked]: ./.github/workflows/security.yml:50:9
warning[artipacked]: ./.github/workflows/security.yml:64:9
warning[artipacked]: ./.github/workflows/smb-acl-measure.yml:42:9
warning[artipacked]: ./.github/workflows/smb-acl-measure.yml:49:9
warning[artipacked]: ./.github/workflows/store-release-delete.yml:54:9
warning[secrets-outside-env]: ./.github/workflows/store-release-delete.yml:71:31
warning[artipacked]: ./.github/workflows/store-submit.yml:70:9
warning[secrets-outside-env]: ./.github/workflows/store-submit.yml:83:31
warning[secrets-outside-env]: ./.github/workflows/store-submit.yml:84:32
warning[secrets-outside-env]: ./.github/workflows/store-submit.yml:85:36
warning[secrets-outside-env]: ./.github/workflows/store-submit.yml:117:31
warning[secrets-outside-env]: ./.github/workflows/store-submit.yml:171:31
```

Die Zeilen der 13 auditor-Befunde decken sich exakt mit der Tabelle unter E-04.

### actionlint 1.7.12, ohne SHELLCHECK_OPTS

Exit 1 (Befunde), 19 Zeilen, alle shellcheck info/style, 0 eigene actionlint-Fehler. Vollständige Ausgabe:

```
.github/workflows/deploy-harp.yml:1638:9: shellcheck reported issue in this script: SC2086:info:133:17: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/deploy-harp.yml:3592:9: shellcheck reported issue in this script: SC2086:info:20:16: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/deploy-harp.yml:3925:9: shellcheck reported issue in this script: SC2129:style:867:1: Consider using { cmd1; cmd2; } >> file instead of individual redirects [shellcheck]
.github/workflows/deploy-harp.yml:5263:9: shellcheck reported issue in this script: SC2086:info:75:24: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/deploy-harp.yml:5378:9: shellcheck reported issue in this script: SC2086:info:206:30: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/deploy-harp.yml:5378:9: shellcheck reported issue in this script: SC2086:info:207:33: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/deploy-harp.yml:5378:9: shellcheck reported issue in this script: SC2086:info:207:61: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/deploy-harp.yml:5378:9: shellcheck reported issue in this script: SC2086:info:239:35: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/deploy-harp.yml:5378:9: shellcheck reported issue in this script: SC2086:info:239:87: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/integration.yml:3723:9: shellcheck reported issue in this script: SC2016:info:30:21: Expressions don't expand in single quotes, use double quotes for that [shellcheck]
.github/workflows/integration.yml:3723:9: shellcheck reported issue in this script: SC2329:info:8:1: This function is never invoked. Check usage (or ignored if invoked indirectly) [shellcheck]
.github/workflows/measure.yml:257:9: shellcheck reported issue in this script: SC2086:info:2:10: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/measure.yml:542:9: shellcheck reported issue in this script: SC2012:info:19:17: Use find instead of ls to better handle non-alphanumeric filenames [shellcheck]
.github/workflows/measure.yml:574:9: shellcheck reported issue in this script: SC2086:info:2:10: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/measure.yml:606:9: shellcheck reported issue in this script: SC2086:info:2:10: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/measure.yml:676:9: shellcheck reported issue in this script: SC2086:info:2:10: Double quote to prevent globbing and word splitting [shellcheck]
.github/workflows/php.yml:538:9: shellcheck reported issue in this script: SC2016:info:1:16: Expressions don't expand in single quotes, use double quotes for that [shellcheck]
.github/workflows/php.yml:572:9: shellcheck reported issue in this script: SC2016:info:1:8: Expressions don't expand in single quotes, use double quotes for that [shellcheck]
.github/workflows/probe-92d.yml:334:9: shellcheck reported issue in this script: SC2015:info:14:21: Note that A && B || C is not if-then-else. C may run when A is true [shellcheck]
```

Zählung je Regel: SC2086 x12 (deploy-harp 8, measure 4), SC2016 x3 (integration 1, php 2), SC2012 x1, SC2015 x1, SC2129 x1, SC2329 x1. Je Datei: deploy-harp 9, measure 5, integration 2, php 2, probe-92d 1. Deckt sich mit RESEARCH und E-03: bekannt.

### Unbekannte Befunde

| Audit/Regel | Schwere | Datei | Zeile |
|-------------|---------|-------|-------|
| (keine) | | | |

Kein unbekannter Befund. Arbeitsbaum unter .github unverändert (`git status --porcelain .github` leer).

## Task 2: Lesebeleg vor der Owner-Entscheidung (nur Namen)

- `gh api repos/street1983nk/nextcloud-search/environments`: total_count 0, es gibt noch kein Environment.
- Repo-Secrets (Namen): APPSTORE_TOKEN, APP_PRIVATE_KEY, BACKEND_PRIVATE_KEY, NTFY_TOPIC.

Die Owner-Antworten (E-11 ff., da E-09 und E-10 bereits vergeben sind) und der Lesebeleg nach dem Anlegen folgen nach dem Checkpoint.
