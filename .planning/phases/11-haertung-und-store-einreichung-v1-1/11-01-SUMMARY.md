---
phase: 11-haertung-und-store-einreichung-v1-1
plan: 01
subsystem: planning
tags: [owner-entscheid, di-07-03, versionsfenster, l10n, deploy-harp]

# Dependency graph
requires:
  - phase: 07-gemeinsame-embedding-engine
    provides: DI-07-03 mit Messteil geschlossen und der offenen Frage an den Rechteabgleich
  - phase: 10-vergleichsmessung-auf-der-aws-box
    provides: die Zahlen zur Kandidatenschleife und die Rohdatei 98b-sprachfaelle-diagnose.txt
provides:
  - "Vorentscheid V-1 = v1-a: DI-07-03 wird in v1.1.0 gefixt, Plan 11-13 ist scharf"
  - "Wortlaut des 174. Katalogschluessels, englisch und deutsch, als geltender Text"
  - "Vorentscheid V-2 = v2-a: Versionsfenster bleibt min-version 33 bis max-version 35"
  - "Belegdossier, das D-11 und den Codebestand nebeneinander stellt"
affects: [11-04, 11-05, 11-08, 11-10, 11-11, 11-13]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Vorentscheide stehen vor der Phase und nicht in ihrer Mitte: eine eigene Datei mit Beleglage, Optionen, Kosten und wartenden Plaenen"
    - "Folgeplaene zitieren die Optionskennung (v1-a bis v2-b) woertlich statt einer Zusammenfassung"

key-files:
  created:
    - .planning/phases/11-haertung-und-store-einreichung-v1-1/11-VORENTSCHEIDE.md
  modified: []

key-decisions:
  - "V-1 = v1-a: DI-07-03 wird in v1.1.0 gefixt, als MEDIUM mit einer von der Berechtigungskette getrennten Abhilfe; Plan 11-13 faehrt in Welle 2, der Katalog steigt von 173 auf 174 Schluessel"
  - "Der Wortlaut des 174. Schluessels gilt wie im Dossier vorgeschlagen, weil der Owner keinen eigenen genannt hat: en 'Other files contain this word, but none that you may open.', de 'Andere Dateien enthalten dieses Wort, aber keine, die Sie oeffnen duerfen.' (im Repo mit echten Umlauten)"
  - "V-2 = v2-a: Das Versionsfenster bleibt bei min-version 33 und max-version 35; beide info.xml, der stable35-Matrixeintrag und test_lockstep_versions.py bleiben unveraendert, der RE-CHECK am 16.09.2026 bleibt eigener Merkposten und die Einreichung wartet nicht darauf"
  - "D-11 ist damit in der Lesart bestaetigt, die den Codebestand beschreibt, und senkt das ausgelieferte Fenster nicht"

patterns-established:
  - "Vorentscheid-Datei je Phase, wenn zwei oder mehr Owner-Fragen den Umfang spaeterer Plaene bewegen"
  - "Eine Entscheidzeile beginnt mit **Entscheid, traegt das Datum und die Optionskennung; Paraphrasen sind ausgeschlossen"

requirements-completed: []

# Metrics
duration: 30min
completed: 2026-09-10
---

# Phase 11 Plan 01: Vorentscheide V-1 und V-2 Summary

**Beide Umfangsfragen der Phase 11 sind vor der Uebersetzungs- und Workflowarbeit entschieden: DI-07-03 wird gefixt (v1-a, Katalog 173 auf 174, Plan 11-13 scharf) und das Versionsfenster bleibt bei max-version 35 (v2-a, keine Aenderung an ausgelieferten Metadaten).**

## Performance

- **Duration:** rund 30 min inklusive Owner-Checkpoint
- **Started:** 2026-09-10T18:33:00Z
- **Completed:** 2026-09-10T19:05:00Z
- **Tasks:** 2 von 2
- **Files modified:** 1 neu

## Accomplishments

- Belegdossier `11-VORENTSCHEIDE.md` (223 Zeilen) mit beiden Fragen in der geforderten Form: Feststellung mit Belegstelle, was unklar ist, Optionen, Kosten, wartende Plaene.
- V-1 stellt die Zahlen aus Phase 7 und 10 nebeneinander (1,0 Runde bei 1,9 Containeraufrufen je Suche; drei von vier Begriffen ohne die eigene Datei unter den ersten 2.000 Kandidaten eines 52.111er Fremdbestands, `rohdaten/98b-sprachfaelle-diagnose.txt`) und haelt fest, dass beide Optionen die ROADMAP-Konvention gegen eine zweite Berechtigungsgrenze einhalten.
- V-2 stellt den Wortlaut von D-11 und den Codebestand gegenueber (beide `info.xml` mit `max-version="35"`, drei Matrixaeste, `tolerate-failure` mit RE-CHECK 2026-09-16, Lockstep-Test in beide Richtungen, gruener Lauf 34114937751).
- Owner hat beide Fragen in einer Runde entschieden, die Entscheide stehen datiert und mit Optionskennung in der Datei.

## Task Commits

1. **Task 1: Belegdossier zu beiden Fragen** , `b577d0f` (docs)
2. **Task 2: Owner entscheidet V-1 und V-2** , `82c8fa3` (docs)

Beide gepusht: `721bde6..82c8fa3` auf `origin/main`.

## Files Created/Modified

- `.planning/phases/11-haertung-und-store-einreichung-v1-1/11-VORENTSCHEIDE.md` , Beleglage zu V-1 und V-2, beide Optionspaare mit Kosten, die zwei datierten Entscheide, der Wortlaut des 174. Katalogschluessels.

## Decisions Made

- **v1-a**, DI-07-03 wird gefixt. Der Dienst unterscheidet kuenftig "keine Kandidaten" von "Kandidaten, alle vom Recheck verworfen"; ein Zustand mehr im Ergebnisobjekt und ein Katalogschluessel, kein Eingriff in `MAX_ROUNDS` und keine zweite Grenze. Plan 11-13 in Welle 2 ist damit scharf und braucht keine Nachplanung.
- **Wortlaut** des neuen Schluessels wie vorgeschlagen, ohne Prozent-Direktive, damit das Platzhalter-Gate von 11-08 nichts Neues zu pruefen bekommt.
- **v2-a**, Versionsfenster unveraendert. Kein Eingriff in ausgelieferte Metadaten kurz vor der Abgabe; der gruene 35er-Lauf bleibt in der Beleglage, die Wiedervorlage am 16.09.2026 bleibt bestehen.

## Deviations from Plan

Keine Abweichung an der Sache. Eine bewusste Auslassung im Nachlauf:

**1. REL-01 wurde NICHT als erfuellt markiert**
- **Gefunden bei:** Statusnachlauf nach Task 2
- **Sachverhalt:** Die Plan-Frontmatter traegt `requirements: [REL-01]`, aber REL-01 ist "v1.1 ist im Nextcloud App Store eingereicht" und wird von 15 Plaenen dieser Phase getragen. Ein Abhaken nach Plan 1 von 13 waere eine falsche Zusage in `REQUIREMENTS.md`.
- **Vorgehen:** `requirements.mark-complete` bewusst nicht gefahren. REL-01 bleibt `Pending` bis zur tatsaechlichen Einreichung (Plan 11-12 beziehungsweise der Abgabeplan der Phase).

**2. [Rule 2 - fehlende kritische Angabe] ROADMAP-Zeile zu 11-13 praezisiert**
- **Gefunden bei:** Statusnachlauf nach Task 2
- **Sachverhalt:** Die Zeile las "bedingt bei Entscheid v1-a" und liess offen, ob die Bedingung eingetreten ist. Ein Leser der Welle 2 haette den Plan fuer optional halten koennen.
- **Fix:** Zeile auf "SCHARF seit Entscheid v1-a vom 10.09.2026 (11-VORENTSCHEIDE.md)" geaendert.
- **Datei:** `.planning/ROADMAP.md`

## Issues Encountered

Keine.

## User Setup Required

Keine externe Konfiguration.

## Next Phase Readiness

- **Plan 11-13 ist scharf** und faehrt in Welle 2. Er baut den Zustand, den Satz auf der Ergebnisseite, die Unterscheidung in der Ablaufspur des Suchdialogs und den 174. Katalogschluessel in Template und den vier deutschen Katalogen.
- **Plan 11-05** uebersetzt 174 statt 173 Schluessel ins Franzoesische, **Plan 11-08** prueft den Katalog gegen 174.
- **Plan 11-04** laesst die Matrix von `deploy-harp.yml` unveraendert und haelt nur die Wiedervorlage vom 16.09.2026 fest; **Plan 11-11** setzt den Versionsbump ohne Aenderung am Fenster.
- **Plan 11-10** traegt DI-07-03 als MEDIUM-gefixt ins Phase-11-Audit.
- Reihenfolge beachten: 11-13 muss vor der Abnahme der Uebersetzungstabelle liegen, sonst laeuft die Owner-Abnahme ein zweites Mal.

## Self-Check: PASSED

- `11-VORENTSCHEIDE.md` vorhanden, 223 Zeilen, zwei `## V-`-Ueberschriften, zwei `**Entscheid`-Zeilen mit Datum und Optionskennung.
- Commits `b577d0f` und `82c8fa3` im Log, beide auf `origin/main` gepusht.
- `git diff --stat 721bde6..HEAD` nennt genau eine Datei unter `.planning/`, keine unter `php/`, `backend/src/`, `scripts/` oder `.github/`.
- Keine Gedankenstriche, kein verbotenes Vokabular, echte Umlaute nur im Produktstring.

---
*Phase: 11-haertung-und-store-einreichung-v1-1*
*Completed: 2026-09-10*
