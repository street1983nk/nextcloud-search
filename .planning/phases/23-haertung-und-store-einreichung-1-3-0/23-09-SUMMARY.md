---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 09
subsystem: release
tags: [rel-03, hart-04, hart-05, abgabe, store, tag, signatur, belegkette, issue-14]
requires:
  - "23-08: Owner-Abnahme der Härtung vom 27.09.2026 und sechs grüne Werkbänke auf 87e41cd"
  - "23-03/23-07: abgenommene Store-Texte, Changelog-Zeile und Issue-Antwort"
provides:
  - "v1.3.0 im Nextcloud App Store, beide Hälften, je mit HTTP 201 belegt"
  - "GitHub-Release v1.3.0 mit genau vier signierten Anhängen und der Changelog-Zeile als erster Zeile"
  - "ghcr.io/street1983nk/findling_backend:1.3.0 als Manifestindex mit linux/amd64 und linux/arm64"
  - "Belegkette der Abgabe als Abschnitt 11 des Phasenaudits, acht Zeilen je mit Zahl"
  - "Antwort in Issue #14 auf die letzte Frage von budachst, Issue offen"
affects: [phase-23-abschluss, milestone-abschluss-v1.3]
tech-stack:
  added: []
  patterns:
    - "Dispatch unmittelbar nach dem Owner-Wort, Dokumentation der Freigabe erst danach, damit zwischen Freigabe und Dispatch keine Handlung am Repositorium liegt"
key-files:
  created:
    - .planning/phases/23-haertung-und-store-einreichung-1-3-0/23-09-SUMMARY.md
  modified:
    - docs/audits/2026-09-phase-23/README.md
    - .planning/REQUIREMENTS.md
key-decisions:
  - "Der Tag sitzt auf 744d7e4 (Spitze von main): Code identisch mit 87e41cd, dem Kopf mit allen Befund-Fixen aus 23-08 und sechs grünen Werkbänken; die zwei Commits danach tragen nur Doku"
  - "Store-Token unverändert (Owner: \"Unveraendert\"), deshalb keine 400/401-Probe"
  - "Issue-Antwort mit Zitatzeile der Frage von budachst (Owner: \"Mit Zitatzeile\"), Issue bleibt offen (Owner: \"Offen lassen\")"
requirements-completed: [HART-04, HART-05, REL-03]
metrics:
  duration: "ca. 4 h Wandzeit, davon rund 3,5 h Warten auf das Owner-Wort"
  completed: 2026-09-27
  tasks: 3
  files: 2
---

# Phase 23 Plan 09: Die Abgabe 1.3.0 Summary

Findling 1.3.0 steht als signiertes App-Paar im Nextcloud App Store. Der Submission-Lauf 36304007154 antwortete zweimal mit HTTP 201, beide App-Seiten nennen 1.3.0, und Issue #14 hat seine Antwort.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Tag, Release-Lauf, Belegkette Zeilen 1 bis 5 | 8c589a5 |
| 2 | Owner-Freigabe (Checkpoint) | kein eigener Commit, Wortlaut in d4aec47 und hier |
| 3 | Einreichung, Gegenprobe, Issue-Antwort, Zustandspflege | d4aec47 |

## Das Owner-Wort, im Wortlaut der Auswahl (27.09.2026)

1. Einreichung: **"Einreichen"**
2. Token: **"Unveraendert"**, also keine Probe
3. Issue-Text: **"Mit Zitatzeile"**
4. Issue-Status: **"Offen lassen"**

Zwischen Freigabe und Dispatch lag keine Handlung am Repositorium. Der Dispatch lief um 07:43:58Z, die Freigabe ist danach in den Bericht geschrieben worden.

## Die Belegkette, acht Zeilen

| Nr. | Was | Beleg |
|---|---|---|
| 1 | Tag | `v1.3.0`, annotiert, auf `744d7e4662af67c728aa9482197990c414c92bd3`, gepusht 03:55:13Z |
| 2 | Release | Lauf 36292802211, vier Anhänge, zweimal `Verified OK`, zweimal `684 base64 characters` |
| 3 | Anhänge | findling.tar.gz 367.593 B, .sig 684 B, findling_backend.tar.gz 31.713 B, .sig 684 B (Grenze 20.971.520 B) |
| 4 | Abbild | OCI-Index 1.3.0 mit linux/amd64 und linux/arm64, anonym vor der Einreichung abgefragt |
| 5 | Release-Notiz | erste Zeile ist die abgenommene Changelog-Zeile mit budachst und #14 |
| 6 | Submission | Lauf 36304007154, success, einziger Dispatch |
| 7 | HTTP-Codes | `release findling v1.3.0: HTTP 201`, `release findling_backend v1.3.0: HTTP 201` |
| 8 | Gegenprobe | apps/findling und apps/findling_backend einzeln, je 1.3.0 für NC 34 und 35 |

**Die sieben Tag-Läufe, alle success:**
- Release 36292802211
- PHP 36292802225
- Multi-arch 36292802188
- HaRP deploy 36292802231
- Python 36292802242
- Integration 36292802244
- Resilience 36292802273

Kein Lauf wurde wiederholt. Der Tag ist nicht gewandert.

## Issue #14

Der freigegebene Text mit Zitatzeile ("I can always throw the index away and start over, can't I?") ist um 07:44:41Z gepostet worden, nach den zwei 201:
https://github.com/street1983nk/nextcloud-search/issues/14#issuecomment-5853918446

Das Issue steht auf OPEN.

## Zustandspflege

- REQUIREMENTS.md: HART-04, HART-05 und REL-03 sind abgehakt, jeweils mit Beleg und Vorbehalt in der Traceability. Vorbehalte:
  - Das Ladefenster D-08 ist nur in CI gemessen.
  - Wie der Store die Texte rendert, ist nicht nachgesehen.
- Auditbericht: Erfolgskriterium 4 steht auf erfüllt, Abschnitt 11 enthält die Belegkette, die Freigabe und den Issue-Link.
- STATE.md und ROADMAP.md sind **nicht** angefasst; diese Schreibzugriffe gehören laut Auftrag dem Orchestrator.
- UPGRADE_FROM_TAG in deploy-harp.yml ist nicht bewegt.

## Verifikation

- `git rev-list -n 1 v1.3.0` ergibt 744d7e4…, `gh release view v1.3.0 --json assets` ergibt 4.
- Volle Suite: **3349 bestanden, 15 übersprungen**, wie die Referenz aus 23-08.
- `test_public_artifacts.py` ist grün, keine Gedankenstriche in den geänderten Dateien.
- Autorenprobe seit v1.2.0: nur street1983nk plus ein dependabot-Merge, 0 Co-authored-Zeilen.

## Deviations from Plan

1. **STATE.md und ROADMAP.md sind nicht nachgezogen.** Der Plan nennt sie, der Auftrag des Orchestrators schließt sie aus. Der Orchestrator übernimmt sie.
2. **Die Belegkette steht als neuer Abschnitt 11.** Abschnitt 9 ist in diesem Bericht bereits "Was dieser Bericht nicht sagt", deshalb kommt die Kette an das Ende.
3. **Der Issue-Kommentar hat eine Zitatzeile vor dem abgenommenen Wortlaut.** GitHub kennt keine verschachtelten Antworten. Die Zitatzeile ist vom Owner freigegeben.

## Known Stubs

Keine.

## Threat Flags

Keine neue Angriffsfläche.
- T-23-32: Kein Tokenwert steht irgendwo.
- T-23-33: Zweimal `Verified OK`.
- T-23-34: Der Manifestindex ist vor der Einreichung geprüft.
- T-23-35: Die Belegkette hat acht Zeilen.
- T-23-36: Die sieben Tag-Läufe waren grün.
- T-23-37: Der Issue-Text ist freigegeben, das Issue ist nicht geschlossen.

## Self-Check: PASSED

- FOUND: docs/audits/2026-09-phase-23/README.md (Abschnitt 11, zwei "HTTP 201")
- FOUND: .planning/REQUIREMENTS.md (`[x] **REL-03`)
- FOUND: Commits 8c589a5, d4aec47; Tag v1.3.0 auf 744d7e4
