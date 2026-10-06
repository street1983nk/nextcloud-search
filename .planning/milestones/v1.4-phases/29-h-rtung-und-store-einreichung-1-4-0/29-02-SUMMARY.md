---
phase: 29-h-rtung-und-store-einreichung-1-4-0
plan: 02
subsystem: docs/store-texts
tags: [REL-04, D-24-04, store, release-note, issues, pillow, owner-acceptance]
requires: [29-01, 29-03, 29-05, 29-06, 29-07, 29-08, 29-09, 29-10]
provides:
  - "docs/store-listing.md: Abschnitt 'Entwurf 1.4.0 (Phase 29)' Teil 1 bis 9 und 'Die Abnahme 1.4.0'"
  - "Abgenommene EN- und FR-Fassung des D-24-04-Satzes"
affects: [29-12, 29-15, 29-16]
tech-stack:
  added: []
  patterns: ["Alle Außentexte einer Phase in einem Entwurf, eine Owner-Lektüre"]
key-files:
  created: []
  modified:
    - docs/store-listing.md
decisions:
  - "D-24-04 EN: 'Without any change on your side, Findling keeps running as economically as before. Anyone with more hardware can use a profile to free at most half of the box (Standard profile) or everything but one core (Performance profile).' (Owner 06.10.2026)"
  - "D-24-04 FR: 'Sans aucune intervention, Findling continue de fonctionner aussi sobrement qu'avant. Avec plus de matériel, un profil libère au plus la moitié de la machine (profil Standard) ou tout sauf un cœur (profil Performance).' (Owner 06.10.2026)"
  - "Ratifiziert: skipped für system_file/legacy_format/unsupported_variant (29-01), filterwarnings statt httpx2 (29-03), ocr_failed außerhalb der Nachprüfung (29-09), Grenze D-29-06(b) SF0 komprimiert bis 32 MiB (29-07)"
  - "Store-Texte: zwei neue Stichpunkte (Profile, Suchmodell), D-24-04-Satz als Absatz nach Requirements, einzige Messzahl bleibt 730.2"
metrics:
  duration: "ca. 60 min plus Owner-Lektüre"
  completed: 2026-10-06
  tasks: 2
  files: 1
---

# Phase 29 Plan 02: Textentwurf 1.4.0 und Owner-Abnahme Summary

Alle Außentexte von 1.4.0 liegen in einer Datei vor und sind vom Owner abgenommen: die sechs Store-Beschreibungen mit dem D-24-04-Satz (deutsch wörtlich, EN/FR jetzt festgelegt), die README-Zeilen, die Labels der neuen Urteile, zwei Variablentexte, die englische Release-Notiz, fünf Issue-Antworten und das Pillow-Upstream-Issue.

## Die Abnahme (wörtlich)

**2026-10-06, Owner: "ok abgenommen"**, über den Orchestrator am Checkpoint von 29-02 angekommen.

- (a) EN- und FR-Fassung des D-24-04-Satzes wie vorgeschlagen abgenommen.
- (b) bis (e) ratifiziert, also kein Fix-Plan vor 29-12.
- Die drei offenen Punkte zum Lesen bleiben wie im Entwurf: der Abhilfe-Satz zu `out_of_memory`, die 40-MP-Schwelle nur für PNG und TIFF und der Linux-Satz im Pillow-Issue.
- Änderungen des Owners: keine. Kein Diff zwischen vorgelegtem und abgenommenem Entwurf.

**Plan 29-12 übernimmt die Texte wörtlich** in beide `info.xml`, die drei READMEs, Labels und Kataloge und die zwei Variablentexte. Die Release-Notiz geht in 29-15 hinaus. Antworten und Pillow-Issue postet 29-16 erst nach dem Release und nach erneuter Freigabe.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Entwurf 1.4.0, Teil 1 bis 9 | a15d5ef4 |
| 2 | Owner-Abnahme eingetragen | f664565c |

## Selbstprüfung (Task 1)

- `scan_one_measured_figure` und `scan_resident_figure_of_an_info` auf einer `info.xml`-Hülle je App: kein Befund. Jede der sechs Beschreibungen trägt genau eine Messzahl: `['730.2 MB']`, `['730,2 MB']`, `['730,2 Mo']`.
- Der D-24-04-Satz steht in beiden deutschen Texten zeichengleich mit 24-CONTEXT.md.
- Länge gegenüber 1.3.2: findling EN 1509 auf 1949, DE 1645 auf 2040, FR 1780 auf 2225; backend EN 1398 auf 1715, DE 1499 auf 1781, FR 1628 auf 1971.
- Im Abschnitt kein U+2013, kein U+2014, kein Emoji. Teil 8 ohne budachst, ohne Golfpreis/Sixt und ohne Container-ID. "SampleFormat" steht in Teil 7 und Teil 9.
- Das Repro-Skript des Pillow-Issues lief lokal gegen Pillow 12.3.0: ExtraSamples 0 und 1 ergeben `UnidentifiedImageError` (raw und LZW), ExtraSamples 2 ergibt `LA`.
- `tests/test_store_metadata.py`: 76 passed. Das gilt auch nach dem Eintrag der Abnahme.

## Deviations from Plan

**1. [Rule 1 - Bug] Gesperrtes Wort der Vokabelregel in der #18-Antwort**
- Der Store-Gate (`test_the_store_listing_document_avoids_the_blocked_term_counting_every_line`) hat es beim ersten Lauf gefunden. "print archive" ist jetzt "large print images", vor dem Commit a15d5ef4.

**2. Korrekturen an früheren eigenen Issue-Kommentaren in die Antworten aufgenommen.** Der gebaute Stand weicht ab bei: "profiles size the ceiling" (#18), "real error stored" für Float-TIFFs (#18) und "excluded by a rule" (#22). Der Owner hat das mit abgenommen.

## Known Stubs

Keine.

## Threat Flags

Keine. T-29-05: Teil 8 ist ohne Kundendaten, per Selbstprüfung belegt. T-29-06: die Abnahme steht wörtlich in Datei und SUMMARY. T-29-07: keine Feldbelege versprochen, die #18-Antwort sagt ausdrücklich, dass 1.4.0 nicht gegen einen solchen Bestand gefahren wurde.

## Self-Check: PASSED

- FOUND: docs/store-listing.md ("## Entwurf 1.4.0", "## Die Abnahme 1.4.0", "ok abgenommen")
- FOUND: a15d5ef4, f664565c
