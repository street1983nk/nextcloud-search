---
phase: 12-messwerkzeug-runbook-und-terminentscheid
plan: 02
subsystem: infra
tags: [ci, github-actions, deploy-harp, nextcloud-35, versionsfenster, vollzug]

requires:
  - phase: 12-messwerkzeug-runbook-und-terminentscheid
    provides: "Entscheidungsnotiz 12-STABLE35-ENTSCHEID.md aus 12-01 mit beiden Zweigen, Ersatztexten und Vollzugs-Checkliste"
provides:
  - "Vollzogener stable35-Fenster-Entscheid, Zweig a: NC 35 ist final (v35.0.0 vom 15.09.2026)"
  - "deploy-harp stable35-Ast ist muss-gruen (tolerate-failure: false), belegt durch Beweislauf 35095805558"
  - "Gefuellter Vollzugs-Abschnitt in 12-STABLE35-ENTSCHEID.md (alle sechs Felder)"
  - "HART-03 abgehakt; Phase 12 vollstaendig"
affects: [16-haertung-und-store-einreichung-v1-2]

tech-stack:
  added: []
  patterns:
    - "Beweislauf VOR dem Flag-Flip (Variante 1): der muss-gruen-Anspruch ruht auf einem Lauf gegen den finalen Zweigstand, nicht auf dem Release-Status allein (D-02)"

key-files:
  created: []
  modified:
    - .planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-STABLE35-ENTSCHEID.md
    - .github/workflows/deploy-harp.yml
    - .planning/REQUIREMENTS.md
    - .planning/STATE.md

key-decisions:
  - "Zweig a greift: v35.0.0 (2026-09-15T21:40:41Z) ist die erste 35er-Marke ohne Prerelease-Kennzeichen, auf der Einzelmarke gegengeprueft (prerelease=false UND draft=false)"
  - "Owner-Freigabe am Checkpoint mit Variante 1: erst Beweislauf per workflow_dispatch auf dem Ist-Stand, dann Flip; so bleibt der Kommentartext aus 12-01 woertlich wahr (before the flag came out)"
  - "Beide info.xml unberuehrt gelassen: Fenster steht bereits auf 33 bis 35, D-01 laesst dort nichts zu tun (Feststellung aus 12-01 bestaetigt)"

patterns-established:
  - "Fristgebundener Vollzug als reines Lesen-und-Einsetzen: am Stichtag wurde nur die API gelesen, der vorformulierte Ersatztext mit den Tatsachen gefuellt und eingesetzt"

requirements-completed: [HART-03]

duration: ~45min (davon ~17min Wartezeit auf den Beweislauf)
completed: 2026-09-16
---

# Phase 12 Plan 02: stable35-Vollzug Summary

**Der fristgebundene stable35-Entscheid ist am Stichtag vollzogen: NC 35 ist final (v35.0.0 vom 15.09.), der Beweislauf 35095805558 lief mit allen vier Matrixaesten gruen, danach fiel das tolerate-failure-Flag, und der stable35-Ast von deploy-harp ist ab jetzt muss-gruen.**

## Performance

- **Duration:** ~45 min (inklusive ~17 min Wartezeit auf den Beweislauf)
- **Completed:** 2026-09-16
- **Tasks:** 3 (Releasestand lesen und Zweig bestimmen; Vollzug nach Owner-Freigabe; Checkpoint)
- **Files modified:** 4

## Accomplishments

- Releasestand am 16.09.2026 live gelesen und in der Entscheidungsnotiz als
  Tabelle belegt: v35.0.0 ohne Prerelease-Kennzeichen (15.09., 21:40 UTC),
  davor v35.0.0rc4 als letzte Vorabversion. Gegengeprueft auf der Einzelmarke
  (`prerelease=false` UND `draft=false`) und beide `stable35`-Zweige (server,
  app_api) nachgelesen, damit der CI-Ast nicht auf master zurueckfaellt.
- Zweig a nach der Regel aus D-01 eingetragen: die erste 35er-Marke ohne
  Prerelease-Kennzeichen ist da, der Zweig fuer den nicht finalen Fall
  entfaellt. Der Zeitplan (16.09., "date not final") war nicht die Grundlage,
  die API-Antwort war es.
- Checkpoint vor dem Vollzug gehalten: exakter Diff, Beleglage und eine
  offene Reihenfolge-Frage (Beweislauf vor oder nach dem Flip) strukturiert
  vorgelegt. Owner gab Variante 1 frei (Lauf zuerst).
- Beweislauf 35095805558 per `gh workflow run deploy-harp.yml --ref main` auf
  dem Baum des Stichtags (ae59435) gestartet und abgewartet: alle vier
  Matrixaeste gruen, der Ast `deploy-harp (stable35, 8.3, true, ubuntu-24.04)`
  einzeln nachgelesen (success).
- Ersatztext Option a aus 12-01 woertlich eingesetzt (Zeilen 211 bis 273 von
  `.github/workflows/deploy-harp.yml`, 60 Zeilen raus, 17 rein), Platzhalter
  gefuellt: FINAL-TAG=v35.0.0, FINAL-DATUM=2026-09-15, RUN-ID=35095805558.
  `tolerate-failure` steht auf `false`, der RE-CHECK-Absatz ist raus.
- Notiz-Restfelder gefuellt (Laufnummer, vollzogen am/durch), HART-03 in
  REQUIREMENTS.md abgehakt (kein anderer Plan traegt die ID), STATE.md auf
  Phase-12-komplett gezogen.

## Verifikation

- Vollzugs-Abschnitt der Notiz: Zweig a mit Beleg eingetragen, alle sechs
  Felder gefuellt, keine Anmeldedaten, keine Gedankenstriche.
- `uv run pytest tests/test_lockstep_versions.py`: 23 passed, vor UND nach dem
  Flip (der Matrixeintrag blieb stehen, das Fenster 33 bis 35 ist abgedeckt).
- YAML-Syntax von deploy-harp.yml nach dem Einsetzen geprueft (safe_load ok);
  kein `tolerate-failure: true` mehr in der Datei.
- Der Push des Flip-Commits triggert deploy-harp erneut; dieser Lauf ist der
  erste unter muss-gruen-Bedingungen und bestaetigt den Zustand fortlaufend.

## Entscheidungen waehrend der Ausfuehrung

- Reihenfolge Beweislauf/Flip als Owner-Frage an den Checkpoint gehoben statt
  selbst entschieden, weil Iron Rule und der vorformulierte Kommentartext
  unterschiedliche Reihenfolgen nahelegten. Owner entschied Variante 1.
- Task 1 wurde vor dem Checkpoint committet (reine Dokumentation der
  Beleglage, kein Vollzug); der Vollzug selbst wartete auf die Freigabe.

## Commits

| Commit | Inhalt |
|---|---|
| ae59435 | Releasestand gelesen, Zweig a in der Notiz belegt (Task 1) |
| 795744f | deploy-harp: stable35-Ast muss-gruen, Ersatztext eingesetzt |
| (dieser) | Notiz-Restfelder, HART-03 abgehakt, STATE.md, Summary |

## Fuer Folgephasen

- Phase 16 (v1.2.0): der stable35-Ast ist muss-gruen; ein roter Lauf dort ist
  ein Befund und kein Grund, das Flag zurueckzudrehen. Die Anhebung des
  deklarierten Fensters war nie offen (steht seit v1.1.0 auf 33 bis 35).
- HART-03 zaehlt in Phase 16 nicht erneut; das Ergebnis fliesst dort nur in
  die Release-Entscheidung ein (Zuordnungs-Anmerkung in REQUIREMENTS.md).
