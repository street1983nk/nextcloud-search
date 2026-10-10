---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Umsteiger-Release
status: executing
stopped_at: Completed 30-06-PLAN.md
last_updated: "2026-10-10T07:30:32.450Z"
last_activity: 2026-10-10 -- Plan 30-06 abgeschlossen
progress:
  total_phases: 7
  completed_phases: 0
  total_plans: 9
  completed_plans: 6
  percent: 67
---

# Project State

## Project Reference

Siehe .planning/PROJECT.md (Stand nach Phase 29, Milestone v1.5 gestartet) und .planning/MILESTONES.md (v1.0 bis v1.4).

**Core Value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 30, Owner-Tor, Schema und Tschechisch

## Current Position

Phase: 30 von 30-36 (Owner-Tor, Schema und Tschechisch)
Plan: 30-06 abgeschlossen, als Nächstes 30-07
Status: In Ausführung
Last activity: 2026-10-10 -- Plan 30-06 abgeschlossen

Progress: [███████░░░] 67%

## Performance Metrics

- v1.4: 6 Phasen, 78 Plaene in 10 Tagen (Referenz)
- v1.5: 30-01 in ca. 21 min (3 Tasks, 9 Dateien)
- v1.5: 30-02 in ca. 35 min (2 Tasks, 7 Dateien)
- v1.5: 30-03 in ca. 45 min (2 Tasks, 7 Dateien)
- v1.5: 30-04 in ca. 40 min (3 Tasks, 14 Dateien)
- v1.5: 30-05 in ca. 75 min (2 Tasks, 3 Dateien)
- v1.5: 30-06 in ca. 60 min (2 Tasks, 2 Dateien)

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
- 30-04: cs am Ende von SUPPORTED_LANGUAGES, ausserhalb Snowball (STEMMERLESS_LANGUAGES); body_cs als 14. Feld, neun Ketten unbedingt; SCHEMA_VERSION 3 mit GOLD_V1_5. Store upgrade 6 verlangt bereits Schema 2 vorher, 3 nachher (30-07 nur noch der cs-Teil). CZ-02 bleibt offen bis 30-05 bis 30-07.
- 30-05: Bestand (Schema 2, Schema 1) baut unter Schema-3-Code nicht um, cs an/aus per Bandlauf ohne Neu-Einbettung bewiesen; GROWTH_PER_LANGUAGE bleibt 0.40 (cs gemessen 0.358, es 0.361, 2000 Dokumente). CZ-02 offen bis 30-07, CZ-03 bis zur Doku (30-08/30-09).
- 30-06: Upgrade-Strecke startet von v1.4.2 (D-30-07); 1.4.2 urteilt die Saat richtig (Sidecar skipped/system_file, Bild indexed), recheck_1_4_0 done vor und nach dem Upgrade, Store upgrade 5 haelt alle neun Zaehler unveraendert und verlangt schemaVersion 2 und rebuildState idle per Wert; Andockblock fuer Phase 31 am Ende von Store upgrade 2b. deploy-harp-Lauf 38033629694 gruen ueber Store upgrade 0 bis 6. CZ-02 offen bis 30-07.

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

Last session: 2026-10-10T07:30:32.433Z
Stopped at: Completed 30-06-PLAN.md
Resume file: None
