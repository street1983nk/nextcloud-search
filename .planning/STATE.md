---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Leistungsprofile
status: ready_to_plan
stopped_at: Phase 27 complete (16/16), ready for secure-phase 27, then discuss Phase 28
last_updated: 2026-09-29T16:37:22.764Z
last_activity: 2026-09-29 -- Phase 27 complete
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 48
  completed_plans: 48
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-27 after v1.3 milestone)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 28 , Abnahme-Anfahrt

## Current Position

Phase: 28 (Abnahme-Anfahrt)
Plan: Not started
Status: Ready to plan
Last activity: 2026-09-29 - Phase 27 complete

Progress: [#######...] 67% (4 von 6 Phasen)

## Naechster Schritt

**/gsd:secure-phase 27** (T-27-01..50; AR-24-02 und AR-26-02 verfallen mit der Schreibroute),
danach **/gsd:discuss-phase 28** (abnahme-anfahrt).

Phase-27-Abschluss (2026-09-29): 16/16 Plaene in 7 Wellen; Owner-Abnahmen 27-01, 27-15
(gemeinsam per Playwright) und Phase ("ok abgenommen"); Push-Entscheid "push-now" =
106 Commits (d91305df..a8e3d7ea), HaRP-Routen-Ratsche um /probe und /probe/state
erweitert (2b9de323); Code-Review 1C/11W/7I, 12/12 gefixt (918f340d..d25c85e8);
Verifikation human_needed 4/4; zweiter Push bis c87a0239, alle sechs Workflows gruen
(PHPUnit 36596834116). Offen: fp32-Zweig nur automatisiert belegt; MT-Uebersetzungen
WR-02/WR-10 beim Release-Text lesen; WR-04-Rest (no_text_layer in "Uebersprungen")
nach Phase 29 verschoben. Quick 260929-kii (Deckungsgrad-Nenner) mitgereist.

Phase-26-Abschluss (2026-09-29): 14/14 Plaene in 6 Wellen, Verifikation passed 4/4;
Push-Entscheid Owner "Ja" = 229 Commits gepusht (cce78abd..d91305df), CI komplett gruen:
SC2-Kill-Test (Lauf 36522819711), PHPUnit 386 Tests (36522819728, erledigt auch
24-HUMAN-UAT Test 1 und die 25-03/25-04-Posten), arm64-Messleiter (36523219615,
Faktoren 2,000/1,979 gegen 1,05, Gesamt 3,958 = W4-Obergrenze, kein K1-Rueckfall).
Code-Review 1C/2W/4I: CR-01 halt-Rennfenster (91fefe8f), WR-01 unlock_held im
Catch-all (777f3a59), WR-02 Merker-Reihenfolge (15eb03d5) alle GEFIXT mit RED-Beleg;
IN-01..04 dokumentiert offen. Owner-Abnahmen: Latenzprobe D-26-12 (nice kappt
Ausreisser, p50/p95 unveraendert, Zahlbeleg-Grundlage fuer Issue #19) und Phase 26
gesamt. Entscheide D-26-01..16 in 26-CONTEXT.md. Commits nach dem Push wieder NUR LOKAL.

Phase-25-Abschluss (2026-09-28): 12/12 Plaene, Code-Review 0C/4W/4I, alle 4 Warnings
gefixt (00ecee3, 25ec895, 8ca5983, be2779c); Verifikation passed 4/4; Suite 3711 gruen.
fp32-Release model-e5-small-fp32-614241f live und immutable (Upload durch Orchestrator
im Owner-Auftrag, Gegenprobe committet). Entscheide D-25-01..15 in 25-CONTEXT.md.

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

### Quick Tasks Completed

| # | Description | Date | Commit | Status | Directory |
|---|-------------|------|--------|--------|-----------|
| 260929-kii | Deckungsgrad-Nenner waechst mit neuen Dateien (ScanRecountJob, Nachzaehlung absolut, Satz statt Prozent bei Zaehler > Nenner) | 2026-09-29 | bbb4f406 | Verified | [260929-kii-deckungsgrad-nenner-waechst-mit-neuen-da](./quick/260929-kii-deckungsgrad-nenner-waechst-mit-neuen-da/) |

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

Last session: 2026-09-29T07:37:34.360Z
Stopped at: Phase 27 UI-SPEC approved
Resume file: .planning/phases/27-vorab-pr-fung-und-settings-oberfl-che/27-UI-SPEC.md

## Operator Next Steps

- /gsd:execute-phase 25 (25-01 wartet auf den Owner-Upload)
- Push-Entscheid (alles lokal); nach dem Push php.yml pruefen (24-HUMAN-UAT Test 1)
