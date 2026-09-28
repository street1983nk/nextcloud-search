---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Leistungsprofile
status: executing
stopped_at: Phase 25 context gathered
last_updated: "2026-09-28T11:04:56.984Z"
last_activity: 2026-09-28 -- Phase 25 execution started
progress:
  total_phases: 6
  completed_phases: 1
  total_plans: 18
  completed_plans: 6
  percent: 17
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-27 after v1.3 milestone)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 25 — einbettungsspur-und-modellwahl

## Current Position

Phase: 25 (einbettungsspur-und-modellwahl) — EXECUTING
Plan: 1 of 12
Status: Executing Phase 25
Last activity: 2026-09-28 -- Phase 25 execution started

Progress: [##........] 17% (1 von 6 Phasen)

## Naechster Schritt

**/gsd:execute-phase 25**: 12 Plaene in 6 Wellen (Checker PASSED, 0 Blocker, 4 Warnungen,
davon 2 behoben, 2 nur Dateizahl-Hinweise zu 25-02/25-04). Owner-Checkpoint in 25-01 Task 3:
fp32-Asset per gh release create hochladen (Tag model-e5-small-fp32-614241f, vorher Release
immutability einschalten). Pin-Regel: je Welle aendert genau ein Plan test_measurement_scripts.py.
PHPUnit (25-03/25-04) und Ueberlappungstest T3 laufen erst in CI nach einem Push (Owner).
Entscheide D-25-01..15 in 25-CONTEXT.md, Research 25-RESEARCH.md, Muster 25-PATTERNS.md.

Phase 24 secure (2026-09-28): SECURED 24/24 (22 mitigate, 2 accept AR-24-01/02), 29a6cd6.
AR-24-02 (Schreibweg nur occ) verliert mit der Schreibroute in Phase 27 seine Begruendung.

Phase-24-Abschluss (2026-09-28): Code-Review 0C/2W/6I, WR-01 (637c02b) und WR-02 (d0705e4)
gefixt; Verifikation 5/5 Kriterien (human_needed); Live-UAT bestanden mit einem Befund
(memory.max ueber MemTotal hob die Profilschwelle an), gefixt in b345fa3. Offen in
24-HUMAN-UAT.md nur Test 1: PHPUnit (php.yml) nach dem naechsten Push, Push-Entscheid beim Owner.

## Accumulated Context

### Entscheidungen

Volle Liste in PROJECT.md (Key Decisions) und .planning/milestones/v1.3-ROADMAP.md.
Fuer v1.4 unmittelbar tragend:

- Kein Vorwaermen beim Start, Ladefenster-Restrisiko akzeptiert (D-03/D-08, AR-23-01);
  ein Schnellpfad in model.py ist bewusst NICHT gebaut.

- dismax ist auf Messbasis verworfen (MESS-09); die Rangprobe-Grenze 0,81 steht in
  docs/language-analyzers.md.

- Sprachmenge ist sechster Versionsmerker, wird nie gesaet; Schema-1-Bestand ist designierter
  Zwischenzustand, keine Drift (Debug upgrade5, vierte Ausnahme in version_mismatch).

- Store-Regeln: eine Messzahl (730,2 MB), Gate test_store_metadata.py (RESIDENT_FIGURE),
  Tag im Store nie verschieben (v1.3.0 liegt auf 744d7e4).

- Roadmap v1.4 (27.09.): Reihenfolge 24 -> 29 streng seriell als Sicherheitsbedingung
  (MOD-01 vor jedem Modellschalter, H1 vor H2, N-Slot-Probe nach H2, Abnahme-Anfahrt vor
  Release). Rueckfall bei K1: Phase 26 schrumpft auf Befund, Entscheid datiert vor H2-Bau.

### Termine und Owner-Checkpoints

- **Issue #14 (budachst):** Antwort mit Zitat gepostet (issuecomment-5853918446), Issue bleibt
  OFFEN, bis budachst nach dem Upgrade bestaetigt. Nicht selbst schliessen (Owner-Regel).

- **Kill-Kriterium:** Ende September einmalig die Nextcloud-Conference-Nachberichte ansehen,
  danach quartalsweise. Zuletzt geprueft 21.09.2026: NICHT ausgeloest.

- **Findling-Pro-Entscheid:** vertagt auf 03.11.2026 (Go-Kriterium >=10 Grenzen-Anfragen oder
  1 Pilotkunde >250 Nutzer; Stand 21.09.: null Signale).

- **Korpus-Snapshot snap-03f1d1d9ad9262704:** bleibt im Standard-Tier (~2,85 USD/Monat,
  dritter Behalten-Entscheid); naechste Wiedervorlage beim v1.4-Close.

### Offene Blocker

- Keine harten Blocker. Kill-Kriterium siehe oben.

### Pending Todos

- 1 pending: Issue #18 Fix-Kandidaten einplanen (JPG-Verdikt, HEIF, Download-Groessenpruefung)
  -- wartet auf budachst-Antwort (issuecomment-5865917799), Slot-Entscheid beim Owner
  (.planning/todos/pending/2026-09-28-issue-18-jpg-verdikt-heif-download-fixes.md)

## Deferred Items

Aus Phase 23 (Details in phases-Archiv v1.3-phases/23-*/deferred-items.md):

- F-23-04 -> v1.4-Backlog.
- idle-Guard fuer EmbeddingModel.release() -> v1.4 (Mitnahme-Kandidat Phase 25, Plan-Schnitt prueft).
- IN-01..03 dokumentiert offen (23-REVIEW.md).
- Aufraeumen: Worktree nextcloud-search-worktrees/issue-14 plus Branch
  fix/issue-14-teamfolder-acl loeschen (Dateisperre pruefen).

Aeltere Merker:

- Zwei Prosastellen nennen noch `DEFAULT_FIELDS`: `store/repo.py:128` und `:1448`
  (naechster Plan, der repo.py ohnehin oeffnet, nimmt sie mit).

- Leerer Textauszug bei reinem Sprachfeld-Treffer (SnippetGenerator haengt an FIELD_BODY_DE,
  Annahme A5): seit v1.3 in der veroeffentlichten Grenzenliste; Behebung waere eigener Plan
  mit Owner-Entscheid.

- run-Block "Store upgrade 3" in deploy-harp.yml bei ~20,7k Zeichen: vor einem
  ${{ }}-Ausdruck dort erst kuerzen oder Werte per env:-Block hereinreichen.

- L-16-04-Kommentarfix beim naechsten Workflow-Plan (paths-Filter gilt nicht fuer Tag-Pushes).
- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht.
- Estnischer Stemmer nicht verfuegbar: aktiv an die Buerokratt/OS2ai-Spur kommunizieren.
- Auditor-Hinweise aus 23-SECURITY.md (beide advisory): uv lock --check laeuft in keinem
  CI-Schritt; arm64-Manifestcheck war Einmal-Nachweis, store-submit.yml prueft ihn nicht selbst.

## Session Continuity

Last session: 2026-09-28T09:34:00.080Z
Stopped at: Phase 25 context gathered
Resume file: .planning/phases/25-einbettungsspur-und-modellwahl/25-CONTEXT.md

## Operator Next Steps

- /gsd:execute-phase 25 (25-01 wartet auf den Owner-Upload)
- Push-Entscheid (alles lokal); nach dem Push php.yml pruefen (24-HUMAN-UAT Test 1)
