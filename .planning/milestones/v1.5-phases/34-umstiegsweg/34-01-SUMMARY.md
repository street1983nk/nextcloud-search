---
phase: 34-umstiegsweg
plan: 01
subsystem: migration-wording
tags: [wording, migration, fulltextsearch, owner-gate]
requires: []
provides:
  - "34-WORTLAUT.md: abgenommener Wortlaut de/en/fr der Umstiegs-Seite, des Admin-Hinweises, der README- und der Store-Zeile"
  - "Owner-Antworten O2 bis O7, O9, O10 (alle Empfehlungen, PE-34-1 bis PE-34-7 unverändert)"
affects: [34-02, 34-03, 34-04, 34-05]
tech-stack:
  added: []
  patterns: ["Pflegestand einer Fremd-App nur mit Abfragedatum, Version und Link", "Satz ohne URL, Link als eigenes Element mit vorhandenem Linkschlüssel"]
key-files:
  created:
    - .planning/phases/34-umstiegsweg/34-WORTLAUT.md
  modified:
    - .planning/phases/34-umstiegsweg/34-RESEARCH.md
decisions:
  - "34-01: Wortlaut der Phase 34 (34-WORTLAUT.md) vom Owner am 19.10.2026 abgenommen, alle Empfehlungen: O2 Formeln en 'OCR without changing files and without Elasticsearch' / fr 'OCR sans modifier les fichiers et sans Elasticsearch'; O3 Verbot in de/en/fr mit Lookahead; O4 zwei Faktenlisten; O5 Drittanbieter-Plattformen einmal neutral; O6 sprachabhängige Tag-URLs, documentation-Element erst Phase 36; O7 Hinweissatz 'Mindestens eine App ...'; O9 README-Variante 2 (eigener Abschnitt vor Installation); O10 keine UI-SPEC"
  - "34-01: Store-Zeile als Wortlaut abgenommen, förmliche Release-Abnahme bleibt offen (REL-05)"
metrics:
  duration: "ca. 45 min inkl. Checkpoint und einer CI-Runde"
  completed: 2026-10-19
  tasks: 2
  files: 2
---

# Phase 34 Plan 01: Wortlaut-Entwurf und Owner-Abnahme Summary

Seitengerüst de/en/fr für `docs/migrate-from-fulltextsearch{,.en,.fr}.md` mit Pflichtformel, zwei Faktenlisten, Pflegestand von fulltextsearch (abgefragt 19.10.2026) und sieben Abschalt-Schritten; Hinweissatz der Admin-Seite, README-Abschnitt und Store-Zeile mit Längenmaßstab; vom Owner am 19.10.2026 mit allen Empfehlungen abgenommen.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Wortlaut-Entwurf de/en/fr für Seite, Hinweis, README- und Store-Zeile | d017dd60 | 34-WORTLAUT.md |
| 2 | Owner-Entscheid (checkpoint:decision) | 267aacdc | 34-WORTLAUT.md, 34-RESEARCH.md |

## Owner-Entscheid (19.10.2026)

- Wortlaut "abgenommen"; alle Empfehlungen zu O2 bis O7, O9, O10 gelten. O1 und O8 waren schon durch D-34-01 und D-34-02 beantwortet.
- Keine Abweichung von PE-34-1 bis PE-34-7.
- Store-Zeile als Wortlaut abgenommen, förmliche Release-Abnahme offen (REL-05).
- 34-RESEARCH.md: Open Questions als "(RESOLVED in 34-01, 19.10.2026)" markiert, je Frage ein Verweis.

## Pflegestand (Abfrage 19.10.2026, 06:09 UTC)

- fulltextsearch v35.0.0 (20.09.2026), Store 33.0.3 für NC 33 bis 35; fulltextsearch_elasticsearch v35.0.1 und v34.0.3 (07.10.2026); files_fulltextsearch_tesseract nur 32.0.0 für NC 32.
- Abweichung vom Research: für NC 35 führt der Store bei fulltextsearch und files_fulltextsearch die Endfassung 35.0.0 (18.09.2026), nicht nur 35.0.0-beta.1. Im Entwurf vermerkt.

## CI

- d017dd60: nicht einzeln gepusht (lokaler Task-1-Commit, mit 267aacdc zusammen gepusht).
- 267aacdc: OpenSSF Scorecard 39209163014, Security scans 39209163022, beide grün (`gh run watch --exit-status`).
- Nur Planungsdateien, deshalb keine Python-, PHP- oder HaRP-Läufe. PHPL-Block leer, kein Baumhash bewegt.

## Deviations from Plan

**1. Hinweissatz weicht vom Research-Vorschlag ab (O7)**
- Der Research-Satz "Full text search (fulltextsearch) is switched on ..." wäre falsch, wenn nur files_fulltextsearch aktiv ist (PE-34-1 zeigt den Hinweis auch dann). Entwurf: "At least one app of the full text search framework (fulltextsearch, files_fulltextsearch) is enabled ...". Vom Owner abgenommen.

**2. Commit-Schnitt**
- Der Plan sieht einen Commit nach der Owner-Antwort vor. Laut Auftrag gab es zusätzlich einen Task-1-Commit des Entwurfs (d017dd60) vor dem Checkpoint.

## Notes for Following Plans

- 34-02: Zeilen `[Beleg 34-02]` (A1 Tabellenreste, A2 reset ohne Plattform) durch den Befund auf 8090 ersetzen, Markierung `[O5]` entfernen, Pflegestand vor dem Schreiben erneut abfragen; Gate prüft die drei Formeln zeichengleich und das Verbot in drei Sprachen.
- 34-03: Hinweissatz aus Abschnitt B zeichengleich, Linktext "Steps in the documentation" wiederverwendet, Schlüsselzahl 340 auf 341.
- 34-04: README nach Variante 2, Store-Zeile aus Abschnitt D; der Entwurfsabschnitt nennt "Wortlaut abgenommen 19.10.2026, REL-05 offen".
- Der Name "Full Text Search" der fulltextsearch-Gruppe steht auf allen drei Seiten englisch, weil seine Übersetzung nicht geprüft ist.

## Self-Check: PASSED

- FOUND: .planning/phases/34-umstiegsweg/34-WORTLAUT.md
- FOUND: d017dd60, 267aacdc
