---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 04
subsystem: semantic-search
status: blockiert, Owner-Frage
tags: [STR-01, similar-documents, vector-distance, int8, measurement]
requires:
  - 35-03 (Reihenfolgekante, RAM)
provides:
  - findling.index.fusion.centroid(vectors) -> bytes | None
  - scripts/dev/vector_distances.py --similar [--derive] [--groups]
  - docs/measurements/2026-10-aehnlich-distanzen/ (Regel, gruppen.tsv, Befund)
affects:
  - 35-05 (startet nicht ohne Owner-Wort: kein SIMILAR_CEILING)
tech-stack:
  added: []
  patterns: [Regel vor der Messung, mechanische Ableitung auf dem 0,5-Raster]
key-files:
  created:
    - docs/measurements/2026-10-aehnlich-distanzen/README.md
    - docs/measurements/2026-10-aehnlich-distanzen/gruppen.tsv
    - docs/measurements/2026-10-aehnlich-distanzen/rohdaten/00-selftest.txt
    - docs/measurements/2026-10-aehnlich-distanzen/rohdaten/00-umgebung.txt
    - docs/measurements/2026-10-aehnlich-distanzen/rohdaten/01-similar.txt
  modified:
    - backend/src/findling/index/fusion.py
    - backend/tests/test_rrf_fusion.py
    - backend/tests/test_measurement_scripts.py
    - scripts/dev/vector_distances.py
    - backend/tests/test_vector_distances.py
decisions:
  - "SIMILAR_CEILING bekommt keinen Wert: Regel (2) und Gruppenprobe (4) unerfüllbar, Owner-Frage in Abschnitt 7 des Berichts"
  - "A1 auf dem e2e-Korpus nicht prüfbar (26 Chunks über 26 Dateien), nicht ersatzweise geprüft"
metrics:
  duration: ~75 min
  completed: 2026-10-19
  tasks: 3
  files: 10
---

# Phase 35 Plan 04: centroid und Ähnlich-Distanzlauf Summary

Reine Funktion `centroid` (int8-Mittelwert, renormiert über `to_int8`) steht getestet in `index/fusion.py`; der Distanzlauf Dokument gegen Dokument mit vorab festgelegter Regel ergibt "Regel nicht erfüllbar", `SIMILAR_CEILING` bleibt ohne Wert.

## Status: blockiert, Owner-Frage

- 35-05 startet nicht ohne Owner-Wort.
- Owner-Frage: `docs/measurements/2026-10-aehnlich-distanzen/README.md`, Abschnitt 7.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | centroid in index/fusion.py | 8f9a9cae | fusion.py, test_rrf_fusion.py, test_measurement_scripts.py |
| 2a | Regel vor der Messung + gruppen.tsv | 7068abe7 | README.md, gruppen.tsv |
| 2b | Messmodus --similar / --groups | 74d9d08d | vector_distances.py, test_vector_distances.py |
| 3 | Distanzlauf und Befund | 839a5fdf | README.md, rohdaten/00-selftest.txt, 00-umgebung.txt, 01-similar.txt |

Reihenfolge belegt: Regel-Commit 7068abe7 vor Werkzeug 74d9d08d vor Rohdaten 839a5fdf.

## TDD-Belege

- Task 1 rot: `ImportError: cannot import name 'centroid' from 'findling.index.fusion'` (Sammelfehler, 1 error). Grün: 6 neue Fälle, `test_rrf_fusion.py`, `test_search_library.py`, `test_semantic_boundary.py` 76 passed.
- Task 2 rot: 9 failed, 13 passed (`AttributeError: module 'vector_distances' has no attribute 'centroid'` u. a.). Grün: 22 passed.
- Baumhash: `030cb71fe8a7b82eee9b575720cb9ae5da8d76f13c0d74d410c292d8b7967b28` aus dem roten Lauf, unabhängig mit find/sort/tr/sha256sum über den CRLF-normierten Baum nachgerechnet, identisch. `PACKAGE_FILES_TODAY` bleibt 79.
- Volle Gates nach Task 1 und Task 2: ruff (backend + scripts), ruff format, pyright 0 Fehler, vulture sauber, pytest 5767 bzw. 5778 passed, 264 skipped.

## Messergebnis (Task 3)

- Speicher vorab: 3046 MB frei von 16071 MB; Modell aus `findling_backend:1.4.3`, sha256 = `MODEL_SHA256`.
- Selbsttest: 0 / 97,3088 / 179,6051 / 254 gegen `nearest()`.
- Regel (1): 84,0. Regel (2) bei 84,0: abgeschnitten de 0,58 %, en 14,40 %, fr 0,08 % (gefordert 90 %).
- Gegenwert: 61,5 schnitte überall 90 %, verlöre 42/42, 42/42, 119/120 verwandte Paare.
- Gruppenprobe: 38 Gruppen-, 287 Fremdpaare; 80 % Gruppenpaare erst ab 71,0, höchstens 10 % Fremdpaare nur bis 65,0; bei 84,0 Fremdpaare 95,47 % darunter.
- A1: nicht prüfbar, kein mehrchunkiges Dokument im Korpus.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Vokabular-Gate in gruppen.tsv**
- Found during: Task 2 (Regel-Commit)
- Issue: `test_public_artifacts` (Familie vokabular) schlug auf das gesperrte deutsche Wort in der Begründung von 34-zip-bombe.docx an.
- Fix: Begründung auf "ZIP-Bombe" umformuliert, vor dem Commit.
- Commit: 7068abe7

### Abweichungen im Ablauf

- **Kein Push, kein CI-Block:** Ausführung im Worktree, der Orchestrator merged; Pushes und CI-Blöcke der drei Commits entfallen hier.
- **Zusatz-Rohdatei `rohdaten/00-umgebung.txt`:** freier Speicher, Modell-Hash, Laufzeiten, wie der Plan "Wert in die Rohdaten" verlangt.
- **Gruppentabelle mit Textlosen:** alle 39 Korpusdateien stehen in `gruppen.tsv`; 13 ohne Text als "ohne Gruppe", sie tragen keinen Vektor und fallen aus beiden Zählungen (so in Regel (4) festgehalten).

## Known Stubs

Keine.

## Threat Flags

Keine neuen Oberflächen. `fusion.py` enthält weder den Vorfilter-Namen noch "uid" (Gates grün).

## Self-Check: PASSED

- Dateien vorhanden: fusion.py (def centroid), README.md, gruppen.tsv, rohdaten/00-selftest.txt, 00-umgebung.txt, 01-similar.txt.
- Commits vorhanden: 8f9a9cae, 7068abe7, 74d9d08d, 839a5fdf.
