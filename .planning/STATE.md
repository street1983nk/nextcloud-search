---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Umsteiger-Release
status: executing
stopped_at: Completed 30-03-PLAN.md
last_updated: "2026-10-10T05:47:27.598Z"
last_activity: 2026-10-10 -- Plan 30-03 abgeschlossen (Ratsche 2->3, Lesetor-Fix)
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 9
  completed_plans: 3
  percent: 33
---

# Project State

## Project Reference

Siehe .planning/PROJECT.md (Stand nach Phase 29, Milestone v1.5 gestartet) und .planning/MILESTONES.md (v1.0 bis v1.4).

**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 30, Owner-Tor, Schema und Tschechisch

## Current Position

Phase: 30 von 30-36 (Owner-Tor, Schema und Tschechisch)
Plan: 30-03 abgeschlossen, als Nächstes 30-04
Status: In Ausführung
Last activity: 2026-10-10 -- Plan 30-03 abgeschlossen

Progress: [███░░░░░░░] 33%

## Performance Metrics

- v1.4: 6 Phasen, 78 Plaene in 10 Tagen (Referenz)
- v1.5: 30-01 in ca. 21 min (3 Tasks, 9 Dateien)
- v1.5: 30-02 in ca. 35 min (2 Tasks, 7 Dateien)
- v1.5: 30-03 in ca. 45 min (2 Tasks, 7 Dateien)

## Accumulated Context

### Decisions (Roadmap v1.5)

- Alle Schema-/Markenaenderungen des Milestones in Phase 30 in einem Schritt (cs-Koerperfeld, ggf. Archiv-Mitgliedsfeld), damit ein Re-Analyse-Umbau hoechstens einmal faellt; spaetere v1.5-Phasen aendern weder Schema noch Marken.
- Owner-Tor in Phase 30: Ausschlussmuster-Syntax, tschechische Stoppwortquelle/Lizenz, Trefferdarstellung Archiv + innere Datei, Umfang des Nachholwegs FMT-06.
- F-29-03 (POL-02) reist mit den Formaten in Phase 31 (gleicher Indexierpfad).
- Umstiegs-Doku (Phase 34) erst nach den Funktionsphasen, damit der Funktionsvergleich nur Geliefertes nennt.
- Stretch-Phase 35 kann ohne Release-Risiko entfallen; kein Modellwechsel in v1.5.

- 30-01: Tschechische Stoppliste = Lucene 10.5.2 gefaltet (167), Ausnahmen byt (Wohnung) und jez (Wehr), kein achtes Merkmal, ANALYZER_VERSION bleibt 1.
- 30-02: ces nur angeboten, OCR-Standard bleibt deu+eng+fra; Image-Probe CZ-01 auf amd64 und arm64 gruen (Lauf 38027012519).
- 30-03: LEGACY_SCHEMA_STEPS {(1,2),(2,3),(1,3)}; QUERYABLE_SCHEMA_GENERATIONS {2,3} ausgeschrieben, _of_the_marks fragt die Menge statt SCHEMA_VERSION; A5 bestaetigt (Ordnerfilter ueber files.path, kein zweiter Schemaschritt).

### Offene Faeden (kein aktiver Auftrag)

- Vier box-gebundene Feldbelege warten auf die naechste Anfahrt (D-29-11).
- Issues #15/#18/#19/#21/#22 bleiben offen, bis der Melder bestaetigt; Schliessen nur mit
  Owner-Wort je Issue.

- Reddit-Post-Entwurf liegt verifiziert in Outlook ("Reddit-Entwurf: Findling 1.4.0 + MCP
  Connector"); Konto-Appeal pruefen, Owner postet selbst.

- Dev-Instanz (Port 8090) lief am 06.10. mit Abnahme-Testdateien und Backend-Hostprozess;
  bei Gelegenheit aufraeumen.

### Blockers/Concerns

- Kill-Kriterium Nextcloud (ES-freie Volltextsuche mit OCR angekuendigt -> Neubewertung) weiter beobachten.

## Session Continuity

Last session: 2026-10-10T05:47:27.578Z
Stopped at: Completed 30-03-PLAN.md
Resume file: None
