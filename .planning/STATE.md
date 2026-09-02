---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: "**Goal**: Die Betriebsversprechen sind auf echter Zielhardware belegt statt behauptet, und v1.0"
status: executing
stopped_at: Completed 04-02-PLAN.md
last_updated: "2026-09-02T16:36:23.208Z"
last_activity: 2026-09-02
progress:
  total_phases: 6
  completed_phases: 0
  total_plans: 8
  completed_plans: 36
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-15)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 04 — admin-sichtbarkeit-und-diagnose

## Current Position

Phase: 04 (admin-sichtbarkeit-und-diagnose) — EXECUTING
Plan: 3 of 10
Status: Ready to execute
Last activity: 2026-09-02

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 36
- Average duration: -
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 8 | - | - |
| 02 | 14 | - | - |
| 03 | 14 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 04 P01 | 12 min | 2 tasks | 3 files |
| Phase 04 P02 | 10 min | 2 tasks | 7 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Roadmap: Alles in v1, gestaffelt released. Phasen 1 bis 5 = v1.0 (Volltext + OCR, Store vor Jahresende 2026), Phase 6 = v1.1 (Semantik, 4 bis 6 Wochen später)
- Roadmap: ACL-Tabelle liegt im ersten Storage-Schema (Phase 2), nicht nachgerüstet
- Roadmap: Integrationsbeweis (IProvider + exAppRequest) steht vor jedem Feature, App-IDs und beide CSRs in Phase 1
- Engine: Tantivy 0.26 plus SQLite-ACL-Vorfilter, finaler PHP-Recheck ist die Sicherheitsgrenze
- OCR strikt index-only, Nutzerdateien werden nie verändert (CI-Prüfsummen-Gate ab Phase 1)
- [Phase 04]: Gate B kennt zwei Routenklassen: ApiRoute (ExApp, ExAppRequired plus rejectForeignCaller) und FrontpageRoute (Admin, kein Zugriffsattribut). Begruendung: Phase 4 legt den ersten PHP-Controller ohne ExAppRequired an; die Klassentrennung musste vor dem Controller stehen, sonst steht der Baum zwischendurch rot
- [Phase 04]: Eine Route mit beiden Attributnamen gilt als Admin-Route. Begruendung: die Admin-Klasse ist die strengere, also wird Vermischung gemeldet statt durchgelassen
- [Phase 04]: php/templates wird per .gitkeep offengehalten, statt den find-Pfad des php -l-Jobs tolerant zu machen. Begruendung: jede tolerante Schreibweise laesst das Gate stumm weniger pruefen als es behauptet
- [Phase 04]: Der Container meldet maxFileBytes aus settings() auch ohne Zustandsdatenbank, damit die PHP-Einstellung an den wirklich durchgesetzten Deckel geklemmt wird
- [Phase 04]: Die Aufteilung der Wahrheit steht woertlich in beiden Docblocks: skipped, failed und die Fehlerliste aus findling_file_state, indexed, truncated, Platz und Versionsmarken aus dem Container
- [Phase 04]: access_level ADMIN deckt nur den AppAPI-Proxy-Weg; der wirksame Schutz der Admin-Seite ist die PHP-Route ohne NoAdminRequired

### Pending Todos

[From .planning/todos/pending/ , ideas captured during sessions]

None yet.

### Blockers/Concerns

- Baustart erst nach der Store-Einreichung des Schwesterprojekts nextcloud-mcp-connector (September 2026), Solo-Kapazität
- Kill-Kriterium aktiv: Nextcloud GmbH hat fulltextsearch am 12.08.2026 reaktiviert. Kündigt sie eine Elasticsearch-freie Suche mit OCR an, wird das Projekt neu bewertet (Nextcloud Conference September beobachten)
- CSR-Vorlaufzeit für zwei getrennte App-Store-Einträge ist ein bekanntes Terminrisiko aus dem Schwesterprojekt
- RAM-Spitzen auf ARM sind bisher nur geschätzt, Messlauf steht in Phase 5 aus

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-09-02T16:36:10.897Z
Stopped at: Completed 04-02-PLAN.md
Resume file: None
