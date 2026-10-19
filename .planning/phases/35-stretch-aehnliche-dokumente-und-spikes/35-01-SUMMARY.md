---
phase: 35-stretch-aehnliche-dokumente-und-spikes
plan: 01
subsystem: l10n / Ergebnisseite (Wortlaut)
tags: [wortlaut, l10n, str-01, owner-abnahme]
requires: []
provides:
  - "Abgenommener Wortlaut de/en/fr der Ähnlich-Ansicht (7 neue Schlüssel)"
  - "Owner-Antworten O1 bis O6 und Folgen für 35-06/35-07"
affects: [35-06, 35-07, 35-13]
tech-stack:
  added: []
  patterns: ["Wortlaut-Plan vor Code und Katalogen (Muster 34-01)"]
key-files:
  created:
    - .planning/phases/35-stretch-aehnliche-dokumente-und-spikes/35-WORTLAUT.md
  modified: []
decisions:
  - "Sieben neue Schlüssel abgenommen: Similar documents, Similar documents to %s, Similar to: %s, Back to the results, No similar documents found, Erklärsatz, This file is not available (Schlüsselzahl 341 auf 348)"
  - "O1-O6 je Option a: Link an jedem Treffer, keine Filter/Sortierung/Pager/zweite Ebene, Kopien bleiben, zwei Leerzustände, aria-Label nur mit Titel, Rückweg als Satz"
  - "Im Zustand 'Datei nicht verfügbar' ist das h1 'Similar documents' (kein Dateititel)"
metrics:
  duration: "ca. 20 min"
  completed: 2026-10-19
  tasks: 2
  files: 1
requirements: [STR-01]
---

# Phase 35 Plan 01: Wortlaut der Ähnlich-Ansicht Summary

Wortlaut de/en/fr für sieben neue Sätze der Ähnlich-Ansicht (Textlink, aria-Label mit Titel, h1 "Ähnlich zu: %s", Rückweg, zwei zahlfreie Leerzustände ohne Rechte-Wort), vom Owner am 19.10.2026 mit allen Empfehlungen abgenommen.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Wortlaut-Entwurf de/en/fr | 1d02bf51 |
| 2 | Owner-Entscheid eingetragen | 3dc7cb48 |

## Ergebnis

- Tabelle A: sieben neue Schlüssel, Bestandsschlüssel zur Wiederverwendung (Banner, `%1$s in %2$s`, `last opened`), Tab-Titel entfällt (kein Titel je Zustand in `php/`).
- Vorab-Prüfung mit Positivkontrollen: kein gesperrter Wortstamm, keine Ziffern oder Zahlwörter, keine Rechte-Wörter, keine Halbgeviert-/Geviertstriche.
- Owner-Abnahme: "Abgenommen", O1 bis O6 je (a); Folgen für 35-06 und 35-07 als Stichpunkte in Abschnitt E.

## Deviations from Plan

- Der vom Orchestrator vorgegebene Text der Abnahmezeile enthielt einen Geviertstrich (U+2014). Eingetragen mit Komma statt Strich (Projektregel "keine Em-Dashes", Plan-Prüfung von Task 1 verlangt eine strichfreie Datei); im Dokument vermerkt.

## Threat Flags

Keine. T-35-01 (keine Zahl, ein Zustand "nicht verfügbar") und T-35-02 (Owner-Abnahme wörtlich mit Datum) sind umgesetzt.

## Self-Check: PASSED

- 35-WORTLAUT.md vorhanden; Commits 1d02bf51 und 3dc7cb48 im Log; Verify von Task 1 und Task 2 grün.
