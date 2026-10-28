---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 01
subsystem: Wortlaut / Härtung / Store-Text
tags: [wortlaut, l10n, hart-06, rel-05, owner-abnahme, store-text]
requires: []
provides:
  - "Abgenommener Wortlaut de/en/fr der Sammelklasse blocked_malicious (Label, Abhilfe, Detail-Label)"
  - "Zuordnungstabelle mit exakten Schwellen für acht Detailcodes und sechs Bleibt-Zeilen"
  - "Abgenommener Store-Text-Gesamtentwurf 1.5.0 (sechs Beschreibungen), README-Zeilen, CHANGELOG [1.5.0], Release-Notiz, Satz embeddings.md"
  - "Owner-Antworten O1 bis O13 mit Folgen für 36-06 bis 36-11"
affects: [36-06, 36-07, 36-08, 36-09, 36-11, 36-15]
tech-stack:
  added: []
  patterns: ["Wortlaut-Plan vor Code und Katalogen (Muster 34-01/35-01)"]
key-files:
  created:
    - .planning/phases/36-haertung-und-store-einreichung-1-5-0/36-WORTLAUT.md
  modified: []
decisions:
  - "Sammelklasse blocked_malicious im Zustand skipped, Generation 3, Fallback too_large/corrupt für 1.4.x-Companions (O1 a)"
  - "ARCHIVE_MALICIOUS_RATIO = 1000: über 100 bis 1000:1 bleibt archive_limit, erst über 1000:1 blocked_malicious/zip_ratio (O12 a)"
  - "seed-bomb.zip wird auf reine Tiefe 3 ohne Nullen-Mitglied umgebaut, deploy-harp.yml-Erwartung archive_limit bleibt (O4 a)"
  - "zip_overlap sperrt auf jeder Ebene, name-nul-and-both-separators wird zip_traversal (O2 a, O5 a)"
  - "Detail-Label 'Detail: %s' nur für skipped-Zeilen; archive_limit-Abhilfe bleibt; Katalog-Schlüsselzahl 348 auf 351 (O3 a, O13 a)"
  - "Store-Text 1.5.0 ohne Zeile zur Sammelklasse, Grenzliste bleibt bei fünf Einträgen (O8 a, O10 a)"
metrics:
  duration: "ca. 15 min Arbeitszeit, ohne Wartezeit am Checkpoint"
  completed: 2026-10-20
  tasks: 3
  files: 1
requirements: [HART-06, REL-05]
---

# Phase 36 Plan 01: Wortlaut-Vorabplan Härtung und Store-Text 1.5.0 Summary

Wortlaut de/en/fr der Sammelklasse `blocked_malicious` (Zustand `skipped`, acht Detailcodes mit exakten Schwellen, Verhältnis-Sperre erst über 1000:1) und der vollständige Store-Text 1.5.0 beider Apps samt CHANGELOG, Release-Notiz und embeddings-Satz, vom Owner am 20.10.2026 mit allen Empfehlungen (a) abgenommen.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Teil A: Sammelklasse, Schwellen, Korpus- und Saat-Entscheide | 4be94d73 |
| 2 | Teil B: Store-Text 1.5.0, CHANGELOG, Release-Notiz, D-36-07/08/16 | ec12cbe0 |
| 3 | Owner-Entscheid eingetragen | bb4eee4c |

## Ergebnis

- A2: drei neue Schlüssel (Label "File blocked as malicious", Abhilfe, "Detail: %s"); Katalog-Schlüsselzahl 348 auf 351.
- A3: Detailcodes `zip_ratio`, `zip_overlap`, `zip_traversal`, `package_entries`, `xml_entities`, `image_pixels`, `mail_nesting`, `cfb_cycle`; Bleibt-Zeilen für dicht gepackte ZIP-Dateien (100 bis 1000:1), ehrlich große ZIP-Dateien, große Bilder, sonstige CFB-Fehler, Einzeleinträge, Polyglotte.
- Messung Deflate-Obergrenze am 20.10.2026: 2 MiB Nullen 1023,5:1; seed-bomb.zip-Mitglied 158,7:1.
- Teil B: sechs Beschreibungen mit D-36-08 ("Maschine, auf der das Backend läuft") und Ähnlich-Zeile (D-36-16), Dateitypen-Liste zeichengleich zu Teil Phase 31.
- Vorab-Prüfungen A5 und B7 mit Positivkontrollen: kein gesperrter Wortstamm, keine Gedankenstriche, höchstens eine Messzahl je Beschreibung.
- Owner-Abnahme: `Owner-Abnahme: 20.10.2026, "Abgenommen" (Option A) ...`, Folgen je Frage O1 bis O13 in Abschnitt E.

## Deviations from Plan

- Zusatzfrage O13 (Abhilfe von `archive_limit`) im Entwurf ergänzt, weil die im Plan vorgesehene Streichung von "too densely packed" nach O12 (a) den Satz unwahr gemacht hätte; Owner hat (a) gewählt, der Bestandssatz bleibt.
- Abnahmezeile mit Datum im Format TT.MM.JJJJ (20.10.2026) statt ISO, weil die Plan-Prüfung von Task 3 dieses Format verlangt; das ISO-Datum 2026-10-20 steht direkt darunter.
- Kein Push: der Doku-Commit reist laut Plan mit dem ersten Push von 36-02.

## Known Stubs

Keine.

## Self-Check: PASSED

- 36-WORTLAUT.md vorhanden, Commits 4be94d73, ec12cbe0, bb4eee4c im Log.
