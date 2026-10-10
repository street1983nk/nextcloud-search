---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Umsteiger-Release
status: executing
stopped_at: Completed 30-01-PLAN.md
last_updated: "2026-10-10T05:03:55.160Z"
last_activity: 2026-10-10 -- Plan 30-01 abgeschlossen (Kette cs, Lucene-Stoppliste)
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 9
  completed_plans: 1
  percent: 11
---

# Project State

## Project Reference

Siehe .planning/PROJECT.md (Stand nach Phase 29, Milestone v1.5 gestartet) und .planning/MILESTONES.md (v1.0 bis v1.4).

**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 30, Owner-Tor, Schema und Tschechisch

## Current Position

Phase: 30 von 30-36 (Owner-Tor, Schema und Tschechisch)
Plan: 30-01 abgeschlossen, als Nächstes 30-02
Status: In Ausführung
Last activity: 2026-10-10 -- Plan 30-01 abgeschlossen

Progress: [█░░░░░░░░░] 11%

## Performance Metrics

- v1.4: 6 Phasen, 78 Plaene in 10 Tagen (Referenz)
- v1.5: 30-01 in ca. 21 min (3 Tasks, 9 Dateien)

## Accumulated Context

### Decisions (Roadmap v1.5)

- Alle Schema-/Markenaenderungen des Milestones in Phase 30 in einem Schritt (cs-Koerperfeld, ggf. Archiv-Mitgliedsfeld), damit ein Re-Analyse-Umbau hoechstens einmal faellt; spaetere v1.5-Phasen aendern weder Schema noch Marken.
- Owner-Tor in Phase 30: Ausschlussmuster-Syntax, tschechische Stoppwortquelle/Lizenz, Trefferdarstellung Archiv + innere Datei, Umfang des Nachholwegs FMT-06.
- F-29-03 (POL-02) reist mit den Formaten in Phase 31 (gleicher Indexierpfad).
- Umstiegs-Doku (Phase 34) erst nach den Funktionsphasen, damit der Funktionsvergleich nur Geliefertes nennt.
- Stretch-Phase 35 kann ohne Release-Risiko entfallen; kein Modellwechsel in v1.5.

- 30-01: Tschechische Stoppliste = Lucene 10.5.2 gefaltet (167), Ausnahmen byt (Wohnung) und jez (Wehr), kein achtes Merkmal, ANALYZER_VERSION bleibt 1.

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

Last session: 2026-10-10T05:03:50.566Z
Stopped at: Completed 30-01-PLAN.md
Resume file: None
