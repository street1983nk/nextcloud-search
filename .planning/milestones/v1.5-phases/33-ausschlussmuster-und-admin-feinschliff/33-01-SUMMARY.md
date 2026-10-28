---
phase: 33-ausschlussmuster-und-admin-feinschliff
plan: 01
subsystem: admin-ui-wording
tags: [wording, l10n, exclusions, owner-gate]
requires: []
provides:
  - "33-WORTLAUT.md: abgenommener Wortlaut en/de/fr aller sichtbaren Texte der Phase 33"
  - "Owner-Antworten G1 bis G5 (D-33-03, PE-1, PE-2, PE-4 bestätigt; PE-6 überstimmt)"
affects: [33-02, 33-03, 33-04, 33-05, 33-06, 33-07, 33-08, 33-10]
tech-stack:
  added: []
  patterns: ["Code-Marker statt Variablenname, Befehl oder Beispiel im übersetzten Satz"]
key-files:
  created:
    - .planning/phases/33-ausschlussmuster-und-admin-feinschliff/33-WORTLAUT.md
  modified:
    - .planning/phases/33-ausschlussmuster-und-admin-feinschliff/33-07-PLAN.md
decisions:
  - "33-01: Wortlaut der Phase 33 vom Owner am 13.10.2026 unverändert abgenommen (en/de/fr); 28 neue Schlüssel, Schlüsselzahl 306 auf 334"
  - "33-01: G1 bis G4 (a): 32 Muster zu je 60 Zeichen, ? nie über /, Groß/Klein zählt, no_wildcard abgelehnt, Urteilszeilen in beiden Räumwegen gelöscht"
  - "33-01: G5 (c), Abweichung von PE-6: 33-07 ersetzt hardware_short und alle sechs weiteren box-Sätze (Vermerk in 33-07-PLAN.md)"
metrics:
  duration: "ca. 20 min inkl. Checkpoint und 2 CI-Runden"
  completed: 2026-10-13
  tasks: 2
  files: 2
---

# Phase 33 Plan 01: Wortlaut-Entwurf und Owner-Abnahme Summary

Wortlaut en/de/fr für Musterliste, 13 Fehlermeldungen über 11 Codes, zahlenlose Musterbestätigung, Diagnose-Abhilfe, Grenzblock "Limits per file" samt Änderungsweg über `occ app_api:app:unregister` und neuen Hardware-Satz; vom Owner am 13.10.2026 unverändert abgenommen, G5 erweitert den Hardware-Satz auf alle sieben "box"-Sätze.

## Tasks

| Task | Name | Commit | Dateien |
|---|---|---|---|
| 1 | Wortlaut-Entwurf en/de/fr mit Code-Tabelle und offenen Fragen | 33bf0e5d | 33-WORTLAUT.md |
| 2 | Owner-Entscheid (checkpoint:decision) | 45c00a2f | 33-WORTLAUT.md, 33-07-PLAN.md |

## Owner-Entscheid (13.10.2026)

- G1 (a), G2 (a), G3 (a), G4 (a): D-33-03, PE-1, PE-2, PE-4 unverändert.
- G5 (c): Abweichung von PE-6. 33-07 ersetzt sieben Sätze (`hardware_short` plus sechs weitere "box"-Sätze aus Abschnitt F), Schlüsselzahl gleich. Vermerk in 33-07-PLAN.md unter `<context>` mit Prüfung "kein Schlüssel mit box in de.json".
- Wortlaut "abgenommen", unverändert in de, en und fr. Die Antwort kam über den Orchestrator und steht wörtlich in 33-WORTLAUT.md, Abschnitt "Owner-Abnahme".

## CI

- 33bf0e5d: Security scans 38444616386, OpenSSF Scorecard 38444616488, beide grün (`gh run watch --exit-status`).
- 45c00a2f: Security scans 38445248876, OpenSSF Scorecard 38445248457, beide grün.
- Nur Planungsdateien geändert, deshalb keine Python-, PHP- oder HaRP-Läufe (Pfadfilter). PHPL-Block leer, kein Baumhash bewegt.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Anzahl der "box"-Sätze im Plan zu klein**
- **Gefunden in:** Task 1
- **Problem:** Plan und Research nennen drei weitere "box"-Sätze, im Katalog stehen sechs (`admin.php:984`, `1021`, `1141`, `1146`, `1148`, `1224`).
- **Fix:** Alle sechs mit Entwurf in Abschnitt F, G5 um die Option (c) erweitert. Der Owner hat (c) gewählt.

**2. Französisch "service" statt "backend" im Hardware-Satz**
- Abweichung vom Research-Vorschlag, weil der französische Katalog "backend" durchgehend mit "service" übersetzt. In 33-WORTLAUT.md vermerkt und mit abgenommen.

**3. Commit-Schnitt**
- Der Plan sieht einen Commit nach der Owner-Antwort vor. Laut Auftrag gab es zusätzlich einen Task-1-Commit des Entwurfs (33bf0e5d) vor dem Checkpoint.

## Notes for Following Plans

- Bestandssätze "Enter a folder path." und "This path is already excluded." werden für `empty` und `duplicate` der Ordnerliste wiederverwendet, ohne neuen Schlüssel.
- Kommen in einem Speichern neue Ordner und neue Muster zusammen, zeigt 33-05 beide Bestätigungssätze untereinander.
- Der Backslash steht im Satz zu `unsupported_character` als Wort, nicht als Zeichen. So gibt es keinen Escape-Fallstrick in JSON, JS und den Sprachtabellen.

## Self-Check: PASSED

- FOUND: .planning/phases/33-ausschlussmuster-und-admin-feinschliff/33-WORTLAUT.md
- FOUND: 33bf0e5d, 45c00a2f
