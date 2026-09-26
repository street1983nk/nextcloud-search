---
phase: 22-messanfahrt-bl-f03
plan: 11
subsystem: messung, doku
tags: [performance, v13, MESS-07, MESS-08, BL-F04, pruefsumme, runbook]
requires:
  - "22-08/22-09: Rohdaten der Anfahrt vom 26.09.2026, Kosten, Abbau"
  - "22-10: MESS-09 entschieden (Summe), Kaltstart-Ursache README 6.11"
provides:
  - "docs/performance.md: Abschnitt 'Die v1.3-Anfahrt vom 26.09.2026' mit allen Zahlen oder benannten Lücken"
  - "README 6.12 Urteile E1 bis E14, 6.13 Auswertung, 6.14 gefahrene Fassungen"
  - "Runbook-Nachträge (92d statt 13b, 00-lauf.sh, Vorprüfung, Bewaffnung, B4-Typwechsel, Fallen)"
  - "Prüfsummen-Wächter: DRIVEN_V13_FASSUNGEN (elf Werkzeuge), DRIVEN_SUCCESSOR_FASSUNGEN (92c, 99d)"
affects:
  - "22-12 (Audit, Owner-Abnahme): MESS-07 bleibt offen wegen der Kaltstart-Lücke"
tech-stack:
  added: []
  patterns:
    - "Prüfsumme je gefahrener Fassung plus Rohdatenzeile, die die Fassung selbst geschrieben hat"
    - "Kopfsatz NOT_DRIVEN bleibt byteweise, das Fahrdatum steht im Bericht"
key-files:
  created:
    - backend/tests/test_v13_gefahren.py
  modified:
    - docs/performance.md
    - docs/measurements/2026-09-v13-messung/README.md
    - docs/runbook-messbox.md
    - .planning/BACKLOG.md
    - backend/tests/test_measurement_scripts.py
decisions:
  - "Urteile: elf gehalten, drei verfehlt (E4 M-01 Stufe 1 kalt, E5 Kaltstart 0 Treffer, E8 Indexfaktor 1,82 unter 2,0)"
  - "tesseract-Satz performance.md:2887 per Nachtrag berichtigt: im Produkt OMP_THREAD_LIMIT=1, ein Kern je Seite; ungesetzt auf der Box 1,70-mal langsamer; zwei Slots Faktor 1,97"
  - "MESS-08 abgehakt (Indexgröße und Umbau-Wandzeit gemessen); MESS-07 bleibt offen (Kaltstartlatenz mit Trefferpflicht fehlt, Nachfreigabe braucht Owner-Wahl des Weges)"
  - "Prüfsummen-Dicts nach DRIVEN_V12-Muster mit Bytezahl statt Zeilenzahl"
metrics:
  duration: "ca. 75 min"
  completed: 2026-09-26
  tasks: 2
  files: 6
---

# Phase 22 Plan 11: Auswertung nach performance.md, Urteile, Runbook, Prüfsummen Summary

Die Zahlen der v1.3-Anfahrt stehen mit Wert, Datum und Rohdatei in docs/performance.md, drei als benannte Lücke. E1 bis E14 haben ihr Urteil (11 gehalten, 3 verfehlt), das Runbook hat sechs datierte Nachträge, und alle 13 gefahrenen Fassungen sind prüfsummengeschützt, jede mit Mutationsprobe.

## Aufgaben

| Task | Name | Commit | Ergebnis |
|---|---|---|---|
| 1 | Auswertung, Bericht, Runbook, Backlog | 44bba82 | performance.md +342 Zeilen, README 6.12 bis 6.14, Runbook +148 Zeilen, BL-F03 Stand und Vermerk |
| 2 | Prüfsummen-Wächter | b497cc0 | test_v13_gefahren.py (46 Fälle), DRIVEN_SUCCESSOR_FASSUNGEN mit drei Tests |

## Die Zahlen (docs/performance.md, Abschnitt "Die v1.3-Anfahrt vom 26.09.2026")

- **M-01:** warm (Stufen 4 bis 16) höchstens 1.080,6 ms gegen 1.500. Stufe 1 lief 5 s nach einem Containerstart und lud das Modell (anon 116,9 auf 552,7 MB), 9 von 10 Zeilen über 1.500, Maximum 1.512,5. Deshalb E4 verfehlt.
- **92c/99d:** 36 mit `registrierung-gelungen nein`, regulär 0; 99d ohne `FINDLING_LOAD_PASSWORD` 0.
- **Bodensatz:** A 107,9, C1 730,2, C2 760,8; Zyklus 2 minus C1 30,5 MB (Schwelle 50).
- **Einzelliste:** alle 50 (44 / 6) einzeln mit Kennung, Endung, Größe, Grund, ohne Pfade.
- **Kaltstart:** Lücke (6 kalte Suchen, 0 Treffer, innerer Aufruf 1.505 bis 1.596 ms am Deckel).
- **MESS-08:** 786.508.818 auf 1.431.953.684 Byte (Faktor 1,82), Platz während des Umbaus bis 2,22 GB, Wandzeit 581 s, rund 120-mal kürzer als 19 h 20 min. Die Obergrenze von 3 h hält, die Schätzung 1 bis 3 h war zu vorsichtig.
- **BL-F04:** B1 Umbau 1,03 Kerne, OCR 0,90, r = 0,25; B2 4,09 s je Seite; B3 Faktor 1,97; B4 fast linear bis N 16 (15,86), Einbettung T 8 6,01; B5 Thread 2 Faktor 1,87, Batch 8 ohne Gewinn; B6 einkernig ja, Hebel klein bei 9 min 41 s; B7 22,99 MB.
- **Kosten:** 2,32 h / 0,4716 USD laufend, Deckel 24 h / 3,76 USD gehalten.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] tesseract-Satz widerlegt statt bestätigt**
- **Found during:** Task 1
- **Issue:** Der W4-Abschnitt im README hielt den Satz "tesseract nutzt beide Kerne" für bestätigt (CI, 4 Kerne, ungesetzt). Auf der Box ist ungesetzt 1,70-mal langsamer, und das Produkt setzt `OMP_THREAD_LIMIT=1` immer.
- **Fix:** Datierter Nachtrag in performance.md nach dem Abschnitt (Originalsatz Zeile 2887 unverändert), Nachtrag zu Abschnitt 2 in README 6.12.
- **Commit:** 44bba82

**2. [Rule 1 - Bug] Einheit des Bodensatzes**
- **Found during:** Task 1
- **Issue:** 94c und 94b schreiben "MB" für 2^20 Byte.
- **Fix:** In README und performance.md ausdrücklich vermerkt, Werte wie vom Werkzeug geschrieben, damit sie mit v1.2 vergleichbar bleiben.

**3. [Plan-Abweichung] Weg a benennt 50 statt 37**
- Der Plan schrieb für Weg a "37 Übersprungene einzeln, 44 / 6 nicht reproduzierbar". Die Anfahrt hat gezeigt, dass der Snapshot 52.137 / 44 / 6 trägt (Owner-Entscheid 22-08). Dokumentiert ist, was gilt: alle 50 einzeln, und ob es dieselben Dateien wie auf der v1.2-Box sind, sagt keine Rohdatei. Der BACKLOG-Vermerk zu Punkt 4 sagt entsprechend, dass die Annahme "Volume mounten" falsch war und der Punkt trotzdem ohne Reindex erfüllt ist.

**4. [Plan-Abweichung] Bytezahl statt Zeilenzahl**
- Der Plan nennt für die Dicts "(sha256, Zeilenzahl)", verlangt aber zugleich das DRIVEN_V12_FASSUNGEN-Muster, das die Bytezahl führt. Genommen ist die Bytezahl (Muster, und strenger).

**5. [CLAUDE.md] Kein roter Commit**
- Task 2 ist `tdd="true"`. Die RED-Phase ist gelaufen (NameError auf DRIVEN_SUCCESSOR_FASSUNGEN, Sammlung bricht ab), aber nicht committet, weil die Projektregel "Gates grün vor jedem Commit" gilt. Ein Commit für RED und GREEN zusammen.

**6. [Rule 2] Rohdatenbeleg je Fassung**
- Zusätzlich zu Prüfsumme und Mutationsprobe prüft `test_the_driven_v13_fassung_left_its_line_in_the_raw_data`, dass jede gepinnte Fassung eine eigene Endzeile in den Rohdaten hat. Eine Prüfsumme ohne Fahrbeleg hätte eine Fassung einfrieren können, die nie lief.

## Nicht angefasst, mit Grund

- **41,9 gegen 42,1 MB (Messbericht 21-04, Abschnitt 4.3):** weder Plan noch deferred-items verlangen den Fix; performance.md zitiert korrekt 42,1. Offen wie in STATE.md.
- **Docstrings in test_v13_wechsel.py und test_v13_zyklen.py** sagen noch "says that it never ran"; die Asserts dort prüfen nur den Kopfsatz und bleiben richtig. Außerhalb der Dateiliste des Plans.
- **v1.2-Rohdatei 94b** mit geklebtem Wert 11142026092103: bleibt, performance.md nennt die Lesart 1.114 MB.

## Deferred Issues

- **MESS-07 bleibt offen.** Die Kaltstartlatenz mit Trefferpflicht fehlt. Eine Nachmessung (rund 0,24 USD, alle drei Lücken zusammen 0,34 USD) braucht zuerst die Wahl des Weges durch den Owner: (a) Entladeschalter an, (b) einwortiger Begriff, (c) erst Produktfix. Danach eine neue Freigabe (D-02). Das gehört in den Checkpoint von 22-12.
- Nebenlücken: 94c-Spitze (Befund 32), B5-RAM (Befund 50).

## Known Stubs

Keine.

## Threat Flags

Keine. Die Einzelliste nennt nur Kennung, Endung, Größe, Grund (T-22-43); test_public_artifacts.py grün.

## Verification

- `grep -c "## Die v1.3-Anfahrt vom" docs/performance.md` = 1, vor `## Reproduzieren` (Zeile 4506 gegen 4798)
- `19 h 20 min` in performance.md: 2 auf 3 Zeilen
- README-Tabelle 14 Zeilen E1 bis E14, je ein Urteilswort; Erwartungen in 00-ablauf.md unverändert
- Keine Gedankenstriche in den geänderten Dokumenten
- `git diff 44bba82 -- docs/measurements` leer
- ruff check, ruff format --check, pyright latest (0 errors), vulture: grün
- Volle Suite: 3322 passed, 15 skipped

## Self-Check: PASSED

- FOUND: backend/tests/test_v13_gefahren.py (DRIVEN_V13_FASSUNGEN)
- FOUND: DRIVEN_SUCCESSOR_FASSUNGEN in backend/tests/test_measurement_scripts.py
- FOUND: docs/performance.md "## Die v1.3-Anfahrt vom 26.09.2026", "### Nachtrag vom 26.09.2026: tesseract und die Kerne"
- FOUND: README 6.12, 6.13, 6.14; Runbook-Nachträge mit 92d und 00-lauf.sh
- FOUND: Commits 44bba82, b497cc0
