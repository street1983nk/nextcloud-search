---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 08
subsystem: audit, embed, ci-comments
tags: [haertung, audit, security, F-23-01, D-07, D-08, owner-acceptance, HART-04, HART-05, REL-03]
requires:
  - "23-01 bis 23-07"
  - "257caac (Issue #14)"
provides:
  - "docs/audits/2026-09-phase-23/README.md: Härtungsmatrix, Gate-Protokoll, ASVS, Geheimnis-Gegenprobe, Bug/Perf-Durchgang, Befundliste, Abnahme"
  - "F-23-01 behoben: release_if_idle löscht die stehengebliebene Warmlauf-Anforderung"
  - "Owner-Abnahme der Härtung vom 27.09.2026, Plan 23-09 darf beginnen"
affects:
  - "Plan 23-09 (Tag, Release, Einreichung)"
  - "Orchestrator: Push der Fixe und CI-Auslesen aller sechs Werkbänke"
tech-stack:
  added: []
  patterns:
    - "Gegenprobe mit eigenem Skript und eigenen Musterfamilien, nur im Arbeitsbaum"
key-files:
  created:
    - docs/audits/2026-09-phase-23/README.md
  modified:
    - backend/src/findling/embed/engine.py
    - backend/tests/test_embed_engine.py
    - backend/tests/test_measurement_scripts.py
    - backend/appinfo/info.xml
    - .github/workflows/docker.yml
    - .github/workflows/release.yml
    - .planning/phases/23-haertung-und-store-einreichung-1-3-0/deferred-items.md
decisions:
  - "Härtung am 27.09.2026 vom Owner abgenommen, ohne Auflagen"
  - "F-23-04 (Admin-Pfadsuche, LIKE-Muster) bleibt v1.4-Backlog, Owner bestätigt"
  - "Admin-Oberflächentext zu cold/unloaded bleibt, docs/admin-page.md genügt (Owner: So lassen)"
  - "L-16-04 im Zuge des Audits geschlossen: Workflow-Kommentare nennen den gemessenen Tag-Fall"
metrics:
  completed: 2026-09-27
  tasks: 3
  files: 8
requirements: [HART-04, HART-05, REL-03]
---

# Phase 23 Plan 08: Launch-Härtung und Phasenaudit Summary

Das Phasenaudit vor der Abgabe 1.3.0 hat 0 CRITICAL, 0 HIGH und 1 MEDIUM ergeben. Der MEDIUM ist behoben: Bei eingeschalteter Leerlauf-Freigabe lud der Container die Gewichte 30 s nach dem Freigeben wieder, weil eine alte Warmlauf-Anforderung stehen geblieben war. Von den vier LOW sind zwei behoben, einer liegt im v1.4-Backlog und einer ist vom Owner entschieden. Der Owner hat die Härtung am 27.09.2026 abgenommen.

## Tasks

| Task | Name | Commits |
|---|---|---|
| 1 | Härtungsmatrix und Phasenaudit | ed8a57a |
| 2 | Befunde ab MEDIUM fixen, LOW adressieren | 5f9ca5f (RED), 0227289, ea293cc, 9304cfc, b544842 |
| 3 | Owner-Abnahme | 0f96ef8 |

## Was entstanden ist

- **Bericht** `docs/audits/2026-09-phase-23/README.md` in der Form von Phase 16, mit zehn Abschnitten:
  - Härtungsmatrix mit acht Zeilen, jede mit Laufnummer oder Datei als Beleg
  - Gate-Protokoll
  - ASVS V2, V4, V5, V6, V7, V12, V14; bei V4 ist der #14-Fix 257caac inhaltlich gelesen
  - Geheimnis-Gegenprobe über 95 Dateien mit sechs Musterfamilien, die das Gate nicht kennt, plus Entropie; Ausnahmeliste mit 51 Einträgen geprüft
  - Bug- und Performance-Durchgang über jeden Pfad der D-07-Liste, einschließlich der sechs Dateien aus 257caac
  - Ladefenster D-08 mit Zahl: warm-ms 669,6 in CI, auf der Zielhardware nicht gemessen
  - Stand der Altbefunde
  - die vier Erfolgskriterien mit Urteil
  - Befundliste und "Was dieser Bericht nicht sagt"
  - Abnahme
- **F-23-01 (MEDIUM):** `release_if_idle` löscht `_WARM_WANTED` unter dem Schloss der Identitätsprüfung. Der Test `test_a_release_does_not_inherit_the_warm_request_of_a_search_on_a_warm_engine` ist ohne Fix rot. Der Ledger hat einen datierten Absatz bekommen.
- **F-23-02, F-23-03 (LOW):** Der Docstring von `warm()` und der XML-Kommentar über `FINDLING_EMBED_IDLE_RELEASE_SECONDS` stimmen wieder mit dem Code überein. Store-Texte sind unverändert.
- **L-16-04:** Die Kommentare in docker.yml und release.yml behaupten nicht mehr, dass ein Tag-Push vom Pfadfilter aufgehalten wird.

## Die Abnahme (Owner, 27.09.2026, im Wortlaut der Auswahl)

- A: "Haertung abgenommen", ohne Auflagen.
- B: F-23-04 "Ja, v1.4-Backlog".
- C: Admin-Oberflächentext "So lassen".

## Verifikation

- ruff check, ruff format --check (147 Dateien), pyright latest (0 Fehler), vulture: grün. ruff über `../scripts` (14 Dateien): grün.
- Volle Suite vor den Fixen: 3347 bestanden, 15 übersprungen, 1 rot. Der rote Fall ist der Ledger, weil der Fix mitten im Lauf geschrieben wurde.
- Volle Suite nach den Fixen: **3349 bestanden, 15 übersprungen**. Die Skipzahl liegt weiter bei 15.
- `test_public_artifacts.py` über den Bericht: 55 bestanden. Keine Gedankenstriche in den geänderten Dokumenten.
- CI auf 68b679a (letzter gepushter Kopf): alle sechs Werkbänke success, PHPUnit 319 Fälle.
- Autorenprobe `6f27930..HEAD`: nur street1983nk, 0 Co-authored-Zeilen, keine Löschungen.

## Deviations from Plan

**1. [Rule 1 - Bug] F-23-01 vorbestehend, im Audit gefunden und behoben**
- Gefunden in: Task 1, beim Lesen von `embed/engine.py` gegen `main.py`
- Commits: 5f9ca5f und 0227289

**2. L-16-04 mitgenommen**
- Die Zieladresse aus Phase 16 war "der nächste Plan, der einen Workflow anfasst". Der Fix steht vor dem 1.3.0-Tag, damit der Baum unter dem Tag keine widerlegte Aussage trägt.
- Commit: ea293cc

**3. Push und CI-Auslesen (Teil von Task 2) nicht in diesem Plan**
- Ein Worktree-Executor pusht nicht. Der Orchestrator pusht nach dem Merge.
- Danach sind alle sechs Läufe des neuen Kopfes auszulesen und die Laufnummern in Abschnitt 2 des Berichts und hier nachzutragen.
- Betroffen sind alle Werkbänke, weil backend/src, backend/appinfo und zwei Workflows berührt sind.

## Deferred Issues

- F-23-04 steht im v1.4-Backlog, mit Zieladresse in `deferred-items.md`.

## Known Stubs

Keine.

## Self-Check: PASSED

- FOUND: docs/audits/2026-09-phase-23/README.md (enthält "Abgenommen: 27.09.2026")
- FOUND: Commits 5f9ca5f, 0227289, ea293cc, 9304cfc, b544842, ed8a57a, 0f96ef8
- STATE.md und ROADMAP.md sind unverändert
