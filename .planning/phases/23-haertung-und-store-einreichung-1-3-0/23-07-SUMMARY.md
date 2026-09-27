---
phase: 23-haertung-und-store-einreichung-1-3-0
plan: 07
subsystem: store-text
tags: [store-listing, known-limitations, hart-05, rel-03, gates]
requires:
  - "23-03 (abgenommener Store-Textentwurf 1.3.0)"
  - "23-06 (Versionsstellen 1.3.0)"
provides:
  - "Store-Texte 1.3.0 wörtlich in beiden info.xml (sechs Beschreibungen)"
  - "Neuer Text von FINDLING_EMBED_IDLE_RELEASE_SECONDS"
  - "Messzahl 730,2 MB an allen neun Fundstellen, Gate RESIDENT_FIGURE = 730.2"
  - "Gates für Grenzliste (vier Punkte je Text), Doku-Vergleich und Sprachzeile"
affects:
  - "Plan 23-08/23-09 (Release und Einreichung lesen diese info.xml)"
tech-stack:
  added: []
  patterns: ["Befundliste statt Ausnahme, Mutationsfälle an gestagten echten Dateien"]
key-files:
  created: []
  modified:
    - php/appinfo/info.xml
    - backend/appinfo/info.xml
    - README.md
    - README.en.md
    - README.fr.md
    - docs/store-listing.md
    - .planning/PROJECT.md
    - backend/tests/test_store_metadata.py
decisions:
  - "Die sechs Texte wurden per Skript aus Teil 4 des Entwurfs gezogen und eingesetzt, nicht abgetippt; Zeichengleichheit Vorlage gegen CDATA per Extrakt geprüft"
  - "Push und CI-Auslesen liegen beim Orchestrator (Merge nach main), nicht beim Worktree-Executor"
metrics:
  completed: 2026-09-27
  tasks: 2
  files: 8
requirements: [HART-05, REL-03]
---

# Phase 23 Plan 07: Übernahme der Store-Texte 1.3.0 Summary

Die abgenommenen Store-Texte 1.3.0 stehen jetzt zeichengleich in beiden info.xml. Sie enthalten die Sprachzeile, die vier Known limitations und 730,2 MB. Die drei READMEs tragen die neue Messzeile. Neue Gates halten die Messzahl, die Grenzliste, die Sprachzeile und den Vergleich mit `docs/language-analyzers.md` fest.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Übernahme wörtlich in beide Hälften, drei READMEs, Vorlage, PROJECT.md | 4daf712 |
| 2 | RESIDENT_FIGURE 730.2 und Grenzlisten-Gates mit Mutationsfällen | 388896a |

## Was geändert ist

- **Beide info.xml:** Die sechs `<description>`-CDATA-Inhalte sind durch Teil 4 des Entwurfs ersetzt. Das Skript hat sie aus `docs/store-listing.md` gezogen und nichts abgetippt.
- **backend/appinfo/info.xml:** Die Beschreibung von `FINDLING_EMBED_IDLE_RELEASE_SECONDS` steht im Wortlaut von Teil 5. `display-name` und `default` sind unverändert, ebenso der XML-Kommentar darüber. Der Kommentar gehört laut 23-03 zum Plan des Kaltstart-Fixes.
- **READMEs:** Die Zeile nach dem Messsatz lautet jetzt wie die "Neu"-Fassung aus Teil 3. Sie nennt 730,2 / 730.2 / 730,2 Mo, das Messdatum 26.09.2026 und das v1.3-Abbild. Das Wort "ausgelieferte"/"shipped"/"livrée" ist entfallen. Eine Grenzliste bekommen die READMEs nicht, der Owner hat keine verlangt.
- **docs/store-listing.md:**
  - Die sechs Texte in App 1 und App 2 sind ersetzt.
  - Der veraltete Kopfabsatz "Stand dieser Datei" ist nachgezogen.
  - Im Entwurf v1.3.0 steht der Absatz "Übernommen in Plan 23-07 am 27.09.2026".
- **.planning/PROJECT.md:** Die Store-Regel lautet jetzt "eine Messzahl (730,2 MB); alle Fundstellen hält das Gate test_store_metadata.py (RESIDENT_FIGURE)". Die Angabe "an drei Stellen" ist raus.
- **Versionsstellen:** nicht angefasst, sie stehen seit 23-06 auf 1.3.0.

## Neue Gates in backend/tests/test_store_metadata.py

- **Konstanten:**
  - `RESIDENT_FIGURE = "730.2"`, mit Kommentar zu D-09, Marke C1, Rohdatei und `docs/performance.md`
  - `LIMITATION_HEADINGS` (EN "Known limitations:", de "Bekannte Grenzen:", fr "Limites connues :") und `LIMITATION_COUNT = 4`
  - `LANGUAGE_ANALYZERS_DOC` und `LANGUAGE_ANALYZERS_HEADING`
  - `LANGUAGE_LINE_OPENINGS`
- **Scanner:** `scan_limitations`, `scan_language_line`, `scan_limitations_against_doc`, dazu die Hilfsfunktionen `list_under` und `documented_limitations`.
- **Gate-Tests am echten Baum (4):**
  - die Doku-Kurzliste existiert und hat 4 Punkte (Anti-Vakuität)
  - jede der sechs Beschreibungen hat 4 Grenzpunkte
  - die EN-Liste beider Hälften ist zeichengleich zur Doku
  - die Sprachzeile steht direkt vor der Grenzüberschrift
- **Mutationsfälle (5):**
  - ein fehlender Grenzpunkt (Backend, de): der Befund nennt Hälfte und Sprache
  - ein fehlender Block (PHP, fr)
  - die Doku-Liste weicht um ein Zeichen ab: beide Hälften rot
  - der Doku-Abschnitt fehlt
  - die Sprachzeile ist verschoben (PHP, EN)
- **Kaputtes XML:** Auch die zwei neuen Scanner liefern dafür einen Befund statt einer Ausnahme.
- **Literale nachgezogen:** Die Fälle, die 731.9 wörtlich erwarteten, prüfen jetzt 730.2. Die Mutationsvorlage `_with_another_figure` (741.9) bleibt eine abweichende Zahl.

## Verifikation

- RED vor dem Umstellen der Konstante: 5 Fälle rot (Messzahl in README und beiden Hälften, zwei Mutationsfälle am echten Text). Die neuen Gates können nachweislich rot werden, das belegen die Mutationsfälle.
- `grep -rn "731[.,]9" php/appinfo backend/appinfo README.md README.en.md README.fr.md`: kein Treffer.
- `Known limitations:`, `Bekannte Grenzen:` und `Limites connues :` stehen je einmal in beiden info.xml.
- Diff-Beleg per Extrakt: Die sechs Texte in App 1 und App 2 von `docs/store-listing.md` sind zeichengleich zu den CDATA-Inhalten, `IDENTICAL clean` für alle 6. "clean" heißt: keine U+2013, keine U+2014, keine Backticks.
- `ruff check`, `ruff format --check`, `pyright` (latest, 0 Fehler) und `vulture` sind grün.
- `pytest tests/test_store_metadata.py tests/test_public_artifacts.py`: 131 passed.
- Volle Suite: 3348 passed, 15 skipped.

## Deviations from Plan

- **Push und CI-Lauf nicht in diesem Plan:** Der Plan verlangt Push und das Auslesen des Python- und HaRP-deploy-Laufs. Als Worktree-Executor pushe ich weder main noch einen Wegwerf-Zweig ins öffentliche Repository. Der Orchestrator merged und pusht. Die Workflows `python.yml` und `deploy-harp.yml` starten bei Pushes auf `backend/**`, und dieser Plan ändert `backend/appinfo/info.xml` und `backend/tests/`. Beide Läufe starten also mit dem Push von main. Laufnummern und Ergebnis trägt der Orchestrator nach.
- **Zwei Commits statt einem:** Das Commit-Protokoll verlangt einen Commit je Task. Der Plan hatte einen gemeinsamen Commit genannt, dessen Nachricht jetzt Task 2 trägt.

## Self-Check: PASSED

- php/appinfo/info.xml, backend/appinfo/info.xml, README.md, README.en.md, README.fr.md, docs/store-listing.md, .planning/PROJECT.md und backend/tests/test_store_metadata.py: vorhanden und geändert
- Commits 4daf712 und 388896a: vorhanden
