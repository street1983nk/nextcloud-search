---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Messbeleg und Ausbau
status: "Roadmap steht, naechster Schritt /gsd:plan-phase 12"
stopped_at: Phase 12 context gathered
last_updated: "2026-09-14T15:03:30.393Z"
last_activity: 2026-09-14 — Roadmap v1.2 erstellt (5 Phasen, 17 von 17 Requirements zugeordnet)
progress:
  total_phases: 5
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-11)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** v1.2 Messbeleg und Ausbau, Phasen 12 bis 16

## Current Position

Phase: 12 von 16 (Messwerkzeug, Runbook und Terminentscheid) - noch nicht geplant
Plan: —
Status: Roadmap steht, naechster Schritt /gsd:plan-phase 12
Progress: 0/5 Phasen des Milestones abgeschlossen [....................] 0%
Last activity: 2026-09-14 — Roadmap v1.2 erstellt (5 Phasen, 17 von 17 Requirements zugeordnet)

## Milestone-Reihenfolge v1.2

| Phase | Inhalt | Requirements |
|-------|--------|--------------|
| 12 | Messwerkzeug, Runbook und Terminentscheid (ohne Box) | MESS-04, MESS-06, HART-03 |
| 13 | Filter und Sortierung auf der Ergebnisseite (Backend vor PHP) | FILT-01..05 |
| 14 | Modell-Entladung im Leerlauf (Schalter ab Werk aus) | MEM-01..05 |
| 15 | Messphase, eine Box-Anfahrt | MESS-05 |
| 16 | Haertung und Store-Einreichung v1.2.0 | HART-01, HART-02, REL-02 |

Harte Abhaengigkeiten: 12 vor 15, Backend vor PHP innerhalb 13, 14 vor 15, 16 zuletzt.

## Termine und Owner-Checkpoints

- **16.09.2026**: stable35-Fenster-Entscheid (HART-03, Entscheid v2-a), verankert in Phase 12
- **Vor der Box-Anfahrt**: neu gerechneter Zeit-/Kostendeckel vom Owner freigegeben (MESS-05, Phase 15); der 26-h-Vorschlag reisst rechnerisch, Empfehlung mindestens 31 h / rund 3,59 USD oder bewusst Teilkorpus
- **Vor dem Bau des Zustandsteils**: engineState-Wortwahl `cold` vs sechstes Wort `unloaded` (MEM-05, Phase 14)
- **Vor dem Bau der Entladung**: Vorprueflauf zur tatsaechlichen RSS-Rueckgabe auf Zielhardware (MEM-04, Phase 14); negatives Ergebnis ist ein legitimer Ausgang

## Nach v1.2 (Wiedervorlage)

- Snapshot-Wiedervorlage snap-03f1d1d9ad9262704 (loeschen oder Archive-Tier, rund 2,9 USD/Monat)
- Aufraeumbefunde aus der Recherche: fastembed gepinnt aber nicht importiert, numpy als indirekte Abhaengigkeit
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht

## Offene Blocker

- Kill-Kriterium aktiv: kuendigt Nextcloud auf der Conference im September eine
  Elasticsearch-freie Volltextsuche mit OCR an, wird das Projekt neu bewertet

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-09-11:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| debug | kill-resume-di-05-36-red | investigating | 2026-09-11 |
| debug | parity-login-probe-404 | verifying | 2026-09-11 |
| debug | store-install-5-routes-probe | verifying | 2026-09-11 |

Einordnung: alle drei Debug-Sessions gehoeren zu CI-Befunden, deren Fixe laengst
gemerged und gruen sind (parity-login-probe-404: Fix d604880, Probe fragt
/index.php/apps/findling/; store-install-5-routes-probe: Step auf
oc_ex_apps_routes umgebaut; kill-resume-di-05-36-red: DI-05-36 lief in Phase 10/11
gruen durch). Nur der Session-Status wurde nie auf resolved gesetzt.

## Session Continuity

Last session: 2026-09-14T15:03:30.378Z
Stopped at: Phase 12 context gathered
Resume file: .planning/phases/12-messwerkzeug-runbook-und-terminentscheid/12-CONTEXT.md
