---
phase: 45-findling-1-7-0
plan: 06
subsystem: ci (Integrationsstrecke M-32-02/M-45-01), Release-Ablauf (Push mit Owner-Freigabe)
tags: [excl-04, integration, push, owner-approval]
requires: [45-05]
provides:
  - "Zwei Schritte M-45-01 in .github/workflows/integration.yml vor 'M-32-02: cycle 3': Ausschluss von E1 per Konfigurations-ID bei Hauptschalter an, dann Zurücknehmen und Rückkehr im nächsten regulären Abgleich"
  - "Freigabezeile 'Freigabe Push 45-06' in 45-FREIGABEN.md"
  - "origin/main = 612b7c9e mit allen Commits von 45-01 bis 45-06, alle Workflows des Kopfs grün"
affects: [45-07, 45-08, 45-09]
tech-stack:
  added: []
  patterns: ["Strecke wartet auf den regulären Abgleich statt eines Sofort-Anstoßes im Produkt (D-45-05)"]
key-files:
  created: []
  modified:
    - .github/workflows/integration.yml
    - .planning/phases/45-findling-1-7-0/45-FREIGABEN.md
decisions:
  - "Push von 17 Commits (017e6d8a bis 612b7c9e) auf main nach Owner-Antwort 'Ja' (2026-11-22 03:47 UTC, Claude-Code-Chat); kein Tag, keine Store-Aktion, kein Kommentar"
  - "Kontrollen in M-45-01: E3 (nicht ausgeschlossen, trägt aus Zyklus 2 noch eine Zeile mit Gnadenstempel) und das Heimverzeichnis von keep36 bleiben unverändert"
metrics:
  duration: "Task 1 in der Vorsitzung; Fortsetzung ab Task 2 ca. 35 min laut Systemzeit (03:47 bis ca. 04:20 UTC), davon ca. 30 min CI"
  completed: 2026-11-22
---

# Phase 45 Plan 06: Integrationsstrecke M-45-01 und Push mit Owner-Freigabe Summary

Die Integrationsstrecke belegt auf echter Nextcloud (stable34), dass ein per Konfigurations-ID ausgeschlossener Admin-Speicher bei eingeschaltetem Hauptschalter im nächsten Abgleich sofort und ohne Gnadenstempel aus dem Index fällt und nach dem Zurücknehmen im nächsten regulären Abgleich zurückkehrt; alle Commits von 45-01 bis 45-06 sind mit Owner-Freigabe gepusht, der Kopf 612b7c9e ist in allen neun Workflows grün.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Zyklen M-45-01 in der Integrationsstrecke | f95fdf86 | .github/workflows/integration.yml |
| 2 | Owner-Freigabe für den Push von 45-01 bis 45-06 | 612b7c9e | .planning/phases/45-findling-1-7-0/45-FREIGABEN.md |
| 3 | Push und grüner Kopf mit Beleg der Strecke | (kein Commit, Push edc08233..612b7c9e) | keine |

## Freigabe

`Freigabe Push 45-06: "Ja" (2026-11-22 03:47, Claude-Code-Chat) Entscheid: ja` (Zeit in UTC). Danach `git pull --rebase origin main` (schon aktuell), `git push origin main`: `edc08233..612b7c9e  main -> main`. `git log origin/main..HEAD` ist leer.

## Grüner Kopf (scripts/ci/head_green.sh, exit 0)

```
44982244151 Multi-arch image success
44982244149 Security scans success
44982244171 Python gates success
44982244168 Workflow security lint success
44982244174 HaRP deploy success
44982244156 OpenSSF Scorecard success
44982244176 Integration success
44982244213 Resilience success
44982244155 PHP and store metadata gates success
```

Kein Rerun nötig.

## Beleg der Strecke (Integration-Lauf 44982244176, Job reconcile-and-dach (stable34, 8.2))

Schritt "M-45-01: the switch is on and E1 is excluded by its mount, E1 goes at once":

```
Config value 'excluded_external_mounts' for app 'findling' is now set to '[1]', stored as array in fast cache
[1]
findling.worker.reconcile: storage sweep, absent=2 gone=0 deselected=1 stamped=1 removed=1, removed storages [5], waiting [7]
  GONE storage 8: 0 living rows, stamp ''
  KEEP storage 9: 1 living rows, stamp ''
  E1 storage 5: 0 living rows, stamp ''
  E2 storage 6: 0 living rows, stamp ''
  E3 storage 7: 1 living rows, stamp '1795319536'
E1 (storage 5): 0 living rows, expected 0
E1 (storage 5): stamp ''
E3 (storage 7): 1 living rows, expected 1
E3 (storage 7): stamp '1795319536'
keep36 (storage 9): 1 living rows, expected 1
keep36 (storage 9): stamp ''
```

Schritt "M-45-01: E1 is included again and comes back on the next regular comparison run":

```
Config value excluded_external_mounts of app findling deleted
findling.worker.reconcile: storage sweep, absent=1 gone=0 deselected=0 stamped=1 removed=0, removed storages [], waiting [7]
  E1 storage 5: 1 living rows, stamp ''
E1 (storage 5): 1 living rows, expected 1
E1 (storage 5): stamp ''
E3 (storage 7): 1 living rows, expected 1
keep36 (storage 9): 1 living rows, expected 1
one external storage left the index by its mount and came back, the controls stayed
```

Im ganzen Log steht `::error::` nur in den angezeigten Skripttexten (Zeilen mit Befehlsecho), keine ausgegebene Fehlermeldung (0 Treffer außerhalb der Befehlsechos, 0 `##[error]`).

## Deviations from Plan

None - plan executed exactly as written.

## Threat-Abgleich

- T-45-23: keine `${{ }}` mit Fremdinhalt in den neuen run:-Blöcken; zizmor/actionlint lokal (Task 1) und "Workflow security lint" im CI grün.
- T-45-24: Freigabezeile vor dem Push committet (612b7c9e), Push erst danach.
- T-45-25: `expect_unstamped` für E1 in M-45-01 grün (stamp '').

## Self-Check: PASSED

- .github/workflows/integration.yml enthält "M-45-01" (FOUND)
- Commits f95fdf86 und 612b7c9e auf origin/main (FOUND)
- Integration-Lauf 44982244176 success, Log enthält "M-45-01: E1 is included again" (FOUND)
