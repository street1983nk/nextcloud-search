---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Sprachausbau
status: executing
stopped_at: Phase 19, Plan 19-01 fertig (FieldPlan), naechster Plan 19-02
last_updated: "2026-09-24T21:40:00.000Z"
last_activity: 2026-09-24 -- 19-01 ausgefuehrt (FieldPlan, AST-Waechter ersetzt)
progress:
  total_phases: 7
  completed_phases: 2
  total_plans: 38
  completed_plans: 21
  percent: 30
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-23, Start Milestone v1.3)

**Core value:** Nach der Installation findet die Nextcloud-Suche den Inhalt von Dokumenten (inklusive gescannter PDFs), ohne dass der Admin irgendetwas konfigurieren muss.
**Current focus:** Phase 19 (frageseite-freischalten), Ausfuehrung laeuft; Phase 20 geplant

## Current Position

Phase: 19 (frageseite-freischalten), EXECUTING, Plan 1 of 9; Phase 20 (ui-kataloge) geplant, 0 of 9
Status: Ausfuehrung Phase 19 laeuft (9 Plaene in 6 Wellen). 19-01 fertig (82bf2b1): die drei
Modulkonstanten DEFAULT_FIELDS/TITLE_ONLY_FIELDS/FIELD_BOOSTS sind ein Wert (FieldPlan,
LEGACY_PLAN), build_query nimmt plan keyword-only mit dem Bestandsplan als Vorgabewert, der
AST-Waechter aus test_schema_generations.py ist weg und test_query_fields_plan.py steht an
seiner Stelle. Volle Suite 2749 bestanden / 15 uebersprungen. Planung 24.09.: Research b2ef69f,
Pattern-Karte, Plaene 51525d5, Checker PASS, Warnungen behoben 3c35186. Phase 20 geplant
(a8d40fd, Checker PASS, f32bdec). Phase 18 davor KOMPLETT (12/12, CI-Beweis 36026836087).
Last activity: 2026-09-24 -- 19-01 ausgefuehrt (FieldPlan, AST-Waechter ersetzt)

Progress: [███.......] 30% (2 von 7 Phasen)

## Naechster Schritt

Weiter in Phase 19 mit 19-02 (it-Fixture waechst, Messung neu gefahren, Zaehlgate und
Klassifizierung nachgezogen). Danach oder parallel:
`/gsd:execute-phase 20` (UI-Kataloge; Wellen 1 und 9 sind Checkpoints, 20-01 Pluralfix
der sechs Bestandskataloge braucht die Owner-Sichtprobe). Phase-20-Planung 24.09.:
9 Plaene in 9 Wellen (a8d40fd), Checker PASS, Fussabdruck strikt getrennt von Phase 19
(php/l10n/**, test_admin_ui_contract.py, docs/l10n-*.md, python.yml + integration.yml).
Groesster Research-Fund: Pluralschluessel aller sechs Bestandskataloge im falschen Format
(de/fr antworten bei n=2 mit "2 days"), Fix ist Welle 1.
Entscheide der Planung, die die Ausfuehrung tragen: it-Beweis ueber neue Flexionsfamilie
(19-02), "befuellt" = languages-Marke (19-03), EIN ungegateter CI-Schritt mit vier
Ergebnisseiten-Abrufen (19-07), AST-Waechter-Ersatz im selben Commit (19-01).

## Performance Metrics

**Velocity:** v1.2 lieferte 63 Plaene in 5 Phasen (8 Tage). Fuer v1.3 noch keine Messwerte.

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

## Accumulated Context

### Entscheidungen, die v1.3 tragen

- Feldliste und Boost-Abbildung einer Anfrage sind EIN Wert (`FieldPlan`), nie zwei
  Konstanten: `parse_query_lenient` wirft die ValueError gemessen auch fuer `field_boosts`
  (19-RESEARCH M-1). Der Vorgabewert von `build_query(plan=...)` ist der eingefrorene
  Bestandsplan und niemals etwas aus `settings()`.

- 19-01 wurde als EIN Commit gefahren statt als drei: die Ratschenregel (Aenderung unter
  backend/src/findling zieht PACKAGE_TREE_HASH_TODAY im selben Commit nach) und die
  Uebergabebedingung aus 18-03 (Waechter faellt und sein Ersatz wird im selben Commit
  genannt) lassen keinen gruenen Zwischenstand zu.

- D-04-Linie (v1.1): index-kompatibel ueber Minor-Spruenge. v1.3 verletzt sie bewusst und
  nur fuer Instanzen, die eine neue Sprache einschalten; der Bruch braucht den Owner-Entscheid
  in Phase 17.

- Riskantester Pfad des Milestones: Schema erreicht den Bestandsindex nie, Suche antwortet
  danach dauerhaft leer (`parse_query_lenient`-ValueError zu leerer degraded-Antwort).
  Gegenmassnahme ist die Phasentrennung 18 (Schema und Umbau) gegen 19 (Frageseite).

- Re-Analyse-Umbau statt Vollreindex: geschaetzt 1 bis 3 h gegen gemessene 19 h 20 min.
- Keine Spracherkennung, weder dokument- noch anfrageseitig (Anti-Feature, einstimmig).
- Katalogzahl beim Planstart aus `php/l10n/de.json` ZAEHLEN (Stand Research 199, nicht 174).

### Termine und Owner-Checkpoints

- **Beim Owner offen:** Store-Token-Rotation (apps.nextcloud.com/account/token);
  Outlook-Entwurf an Denny senden; InfraNode ntfy-401-Entscheid.

- **Forum-Post** haengt in der Discourse-Moderation (Konto street1983nk);
  Plan B bei Ablehnung: Antwort im Bestandsthread t/249031.

- **ISV-Nachfass Fabrice Mous:** Wiedervorlage 25.09.2026, dann Nachfass-Entwurf anbieten.
- **Findling-Pro-Entscheid:** vertagt auf 03.11.2026 (Go-Kriterium >=10 Grenzen-Anfragen
  oder 1 Pilotkunde >250 Nutzer; Stand 21.09.: null Signale).

- **Connector Issue #8** (piAreSquare): Community-Beitrag zur geparkten Connector-Spur,
  zeitnah sichten.

- **Korpus-Snapshot** snap-03f1d1d9ad9262704 bleibt im Standard-Tier (~2,85 USD/Monat) und
  wird fuer die Messphase 22 gebraucht; Wiedervorlage beim v1.3-Close.

### Offene Blocker

- Kill-Kriterium: kuendigt Nextcloud eine Elasticsearch-freie Volltextsuche mit OCR an,
  wird das Projekt neu bewertet. Geprueft 21.09.2026: NICHT ausgeloest. Ende September
  einmalig die Conference-Nachberichte ansehen, danach quartalsweise.

### Mitzunehmende Kleinigkeiten

- L-16-04-Kommentarfix beim naechsten Workflow-Plan (paths-Filter gilt nicht fuer
  Tag-Pushes, zwei Workflow-Kommentare berichtigen).

- Systemplatten-Skripte Phasen 5-6.1: Repo-Aufnahme erst nach Geheimnis-Durchsicht.
- Estnischer Stemmer nicht verfuegbar: aktiv an die Buerokratt/OS2ai-Spur kommunizieren.

- Drei Prosastellen nennen noch den gefallenen Namen `DEFAULT_FIELDS`:
  `store/repo.py:128` und `:1448` sowie `tests/test_language_cases_field_level.py:7` und `:221`.
  Keine davon steht im Fussabdruck von 19-01; beim naechsten Plan, der diese Dateien ohnehin
  anfasst (19-02 fasst test_language_cases_field_level.py an), mitnehmen.

## Deferred Items

Keine offenen Deferred Items (die drei Debug-Sessions aus v1.1 sind am 21.09.2026 formal
auf resolved gesetzt).

## Session Continuity

Last session: 2026-09-24
Stopped at: 19-01 abgeschlossen und committet (82bf2b1), SUMMARY geschrieben
Resume file: .planning/phases/19-frageseite-freischalten/19-02-PLAN.md
