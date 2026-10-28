---
phase: 36-haertung-und-store-einreichung-1-5-0
plan: 11
subsystem: Store-Texte und Außentexte 1.5.0
tags: [rel-05, d-36-07, d-36-08, d-36-16, store-text, readme, changelog]
requires: [36-10]
provides:
  - "Sechs Beschreibungen beider info.xml zeichengleich mit 36-WORTLAUT.md B1 (per ElementTree gegen die Fence-Blöcke geprüft, alle sechs identisch)"
  - "READMEs de/en/fr mit Filter-, Ähnlich- und Ausschlusszeile und dem Profilsatz nach D-36-08 (B2)"
  - "CHANGELOG [Unreleased] zeichengleich mit B3 (ohne Markierung (neu), Kopf bleibt [Unreleased] bis 36-13)"
  - "docs/embeddings.md mit dem Halbsatz von D-36-07 (B5)"
  - "docs/store-listing.md: Abschnitt 'Entwurf v1.5.0 (Gesamttext), abgenommen am 20.10.2026' mit sechs Texten, README-Zeilen und Release-Notiz (B4)"
affects: [36-13, 36-14]
tech-stack:
  added: []
  patterns:
    - "Übernahme per Skript aus den Fence-Blöcken von 36-WORTLAUT.md, Gegenprobe unabhängig per ElementTree statt per Regex der Umsetzung"
key-files:
  created: []
  modified:
    - backend/appinfo/info.xml
    - php/appinfo/info.xml
    - README.md
    - README.en.md
    - README.fr.md
    - backend/tests/test_store_metadata.py
    - CHANGELOG.md
    - docs/embeddings.md
    - docs/store-listing.md
decisions:
  - "CHANGELOG-Kopf bleibt [Unreleased] (Plan-Vorgabe, Versionssprung erst in 36-13); B3 nennt [1.5.0] mit Tag-Datum, das setzt 36-13"
  - "README-Zeilen sind im Stil der Dateien auf etwa 80 Zeichen umbrochen; Wortlaut nach Zusammenziehen der Leerräume identisch mit B2 (Gate collapse() liest es ebenso)"
  - "Store-Gate scan_language_line erlaubt zwischen Sprachzeile und Grenz-Überschrift genau den abgenommenen Umstiegsabsatz (MIGRATION_LINE_OPENINGS), sonst nichts"
metrics:
  duration: "ca. 90 min (davon ca. 20 min lokale Suite, Rest CI)"
  completed: 2026-10-21
  tasks: 2
  files: 9
---

# Phase 36 Plan 11: Abgenommener Store-Text 1.5.0 Summary

Der vom Owner am 20.10.2026 abgenommene Gesamttext 1.5.0 steht zeichengleich in beiden info.xml, den drei READMEs, im CHANGELOG, in docs/embeddings.md und als abgenommener Gesamtentwurf in docs/store-listing.md; die Version bleibt 1.4.2.

## Ergebnis der Diff-Prüfung (T-36-39)

Skript im Scratch-Verzeichnis: Fence-Block je Überschrift aus 36-WORTLAUT.md B1 gegen den per ElementTree gelesenen Text der info.xml.

| App | Sprache | Ergebnis | Zeichen (B7) |
|---|---|---|---|
| findling | en | identisch | 2517 (2 517) |
| findling | de | identisch | 2662 (2 662) |
| findling | fr | identisch | 2884 (2 884) |
| findling_backend | en | identisch | 2284 (2 284) |
| findling_backend | de | identisch | 2403 (2 403) |
| findling_backend | fr | identisch | 2631 (2 631) |

- Vor der Übernahme meldete dieselbe Prüfung ABWEICHUNG für alle Blöcke (Positivkontrolle).
- "half of the box" und "Hälfte der Box" kommen in keiner info.xml und keinem README mehr vor; Ähnlich-Zeile in allen sechs Beschreibungen.
- CHANGELOG [Unreleased]: identisch mit B3 nach Entfernen der Markierung "(neu) ".
- Halbgeviert- und Geviertstriche: 0 in allen geänderten Dateien; Wortstamm "Archiv" im neuen store-listing-Abschnitt: 0.

## Tasks

| Task | Name | Commit |
|---|---|---|
| 1 | Store-Beschreibungen in beide info.xml, READMEs, Gates | fdccef86 |
| 2 | CHANGELOG, embeddings.md, store-listing.md | 7a4c3b2c |

## Gates

- Lokal: volle Backend-Suite 6189 passed, 264 skipped (19 min); ruff check/format und pyright auf test_store_metadata.py grün.
- `reuse lint` lokal nicht lauffähig (libmagic fehlt unter Windows); in CI grün über die Gate-Läufe.
- CI auf 7a4c3b2c: Python gates, PHP and store metadata gates, Integration, Resilience, Security scans, Multi-arch image, OpenSSF Scorecard und HaRP deploy (39563847139) grün, also alle acht Läufe.
- PHP-Baumhash-Ratsche nicht berührt: das Rezept liest nur `**/*.php`, nicht appinfo/info.xml (test_measurement_scripts grün).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Store-Gates kodierten den alten Wortlaut**
- **Found during:** Task 1
- **Issue:** `test_store_metadata.py` hielt den Profilsatz mit "half of the box" (SHARE_SENTENCES) und verlangte die Sprachzeile direkt vor der Grenz-Überschrift; der abgenommene Text setzt den Umstiegsabsatz dazwischen. 7 Tests rot.
- **Fix:** SHARE_SENTENCE_DE/EN/FR auf den abgenommenen Wortlaut von D-36-08 gezogen, mit Journalabsatz "Moved on 21.10.2026 by plan 36-11"; neue Konstante MIGRATION_LINE_OPENINGS, scan_language_line lässt genau diesen einen Absatz zwischen Sprachzeile und Überschrift zu. Mutationstests (umformulierter Satz, doppelter Satz, verschobene Sprachzeile) bleiben unverändert und grün.
- **Files modified:** backend/tests/test_store_metadata.py
- **Commit:** fdccef86

**2. Commit-Aufteilung:** Plan nennt einen Text-Commit; nach Protokoll je Task ein Commit (fdccef86, 7a4c3b2c).

Sonst nichts zusätzlich geändert (Owner-Regel, T-36-40).

## Known Stubs

Keine. Tag-Links `blob/v1.5.0` und der Compare-Link der Release-Notiz lösen erst nach dem Tag auf (Prüfung in 36-14, wie in B2/B4 vorgesehen).

## Self-Check: PASSED

- Dateien vorhanden: alle neun geänderten Dateien im Baum, Abschnitt "Entwurf v1.5.0 (Gesamttext), abgenommen am 20.10.2026" in docs/store-listing.md.
- Commits vorhanden: fdccef86, 7a4c3b2c (auf origin/main).
