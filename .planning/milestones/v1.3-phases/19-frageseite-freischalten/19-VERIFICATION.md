---
phase: 19-frageseite-freischalten
verified: 2026-09-25T00:32:37Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 19: Frageseite freischalten Verification Report

**Phase Goal:** Nutzer findet Dokumente in den aktiven neuen Sprachen ueber die ganz normale Suche, und zwar erst, nachdem der Umbauweg bewiesen ist.
**Verifiziert:** 2026-09-25T00:32:37Z
**Status:** passed
**Re-Verifikation:** Nein, erste Verifikation

## Zielabgleich

### Beobachtbare Wahrheiten

| # | Wahrheit | Status | Beleg |
|---|---|---|---|
| 1 | Fund je Sprache (es/it/nl/pt) ueber Stammform, Unified Search + Ergebnisseite, gruener arm64-CI-Ast, Sprachbeweis-Schritt ungegatet | VERIFIED | `gh run view 36074155306` und `gh run view 36076006854`: beide `conclusion: success`, je 4 Jobs (`stable33/amd64`, `stable34/amd64`, `stable34/arm64`, `stable35/amd64`), alle `success`. Der Schritt "Language proof, the four new chains answer on the ordinary search route" in `.github/workflows/deploy-harp.yml:821` traegt bewusst kein `if:` (Kommentarblock Zeilen 789-800 nennt das ausdruecklich als Statement, nicht als Vorliebe) und `continue-on-error: ${{ matrix.tolerate-failure }}` ist seit Plan 12-02 fuer alle vier Matrixeintraege `false`. Der Schritt laedt vier Dokumente per WebDAV hoch, pollt die OCS-Unified-Search-Route je Sprache und ruft danach `apps/findling/?query=<begriff>` fuer alle vier Sprachen ab (Zeilen 1026-1052), prueft `grep -qF "language-proof-<lang>.txt"` im HTML. `backend/tests/test_language_proof_steps.py` (757 Zeilen, mehrere Testfunktionen) bewacht die YAML-Struktur selbst: `test_the_language_proof_step_carries_no_condition`, `test_the_two_gated_steps_still_carry_theirs`, `test_the_matrix_still_runs_a_leg_on_arm64`, `test_the_real_workflow_produces_no_finding_at_all`. Stichprobenlauf lokal: alle fuenf angeforderten Testdateien 110/110 bestanden. |
| 2 | Instanz mit de,en: Trefferliste/Reihenfolge unveraendert, Feldliste haengt an schema_version-/languages-Marke statt an Konstante | VERIFIED | `backend/src/findling/api/resources.py:338-430` (`field_plan_for(marks, index)`): liest ausschliesslich `SCHEMA_MARK` und `LANGUAGES_MARK` aus den gespeicherten Marken, faellt bei jeder Abweichung (fehlende Marke, "1", unbekannte Generation) geschlossen auf `LEGACY_PLAN` zurueck (`backend/src/findling/query/rewrite.py:113-129`), niemals auf `settings()`. `ReadSide.field_plan` (Zeile 154) wird einmal je Oeffnung berechnet und mit den Handles verworfen. Alle drei Aufrufstellen (`api/search.py:255`, `api/snippets.py:194`, `api/diagnose.py:205`) reichen `plan=side.field_plan` durch. `backend/tests/test_query_fields_plan.py` (29+ parametrisierte Faelle) haelt Bestandsverhalten gegen `schema_1_index` UND `schema_2_index` fest, inklusive der Torgegenprobe `test_the_mark_and_not_the_directory_decides_which_fields_are_searched`. Lokaler Lauf gruen. |
| 3 | Boosts der vier neuen Felder unterhalb body_en, belegt an einer Rangprobe | VERIFIED | `backend/src/findling/query/rewrite.py:100-108`: `BODY_BOOST = {"de": 1.0, "en": 0.8, "es": 0.6, "it": 0.6, "nl": 0.6, "pt": 0.6}`. `backend/tests/test_field_plan_ranking.py` (acht Testfunktionen) baut einen echten Drei-Dokumente-Index mit sechs befuellten Koerperfeldern, belegt die Kettenuneinigkeit (`test_the_two_hits_answer_the_question_through_chains_that_disagree`), zeigt den besseren englischen Treffer vorn (`test_the_better_english_hit_stands_before_the_three_chain_hit`, Reihenfolge `[1, 2]`), die Gegenprobe bei Boost 1.0 kippt den Rang (`test_the_same_ranking_turns_over_once_the_four_weights_reach_one`, Reihenfolge `[2, 1]`), und der Sweep misst `TIPPING_BOOST = 0.81` (`test_the_boost_at_which_the_ranking_turns_over_is_this_one`), der ausgelieferte Wert 0.6 liegt 0.21 unterhalb der Kippgrenze. Lokaler Lauf: 8/8 gruen in 4.9s. `docs/language-analyzers.md:252` traegt dieselbe Zahl mit Messdatum. |
| 4 | Kein Spracherkennungspfad, Test haelt das Anti-Feature fest | VERIFIED | `backend/tests/test_no_language_detection.py` (rund 17 Testfunktionen): liest den Syntaxbaum von `field_plan_for` und belegt strukturell, dass die Funktion keinen Parameter nimmt, dessen Name oder Typ eine Suchzeile tragen koennte (`test_the_function_that_builds_the_field_plan_takes_no_search_text`, mit rotem Gegenbeispiel `test_a_plan_function_with_a_text_parameter_makes_that_check_red`); dass `build_query` seinen Plan nur aus dem Parameter liest und nicht aus `settings()` oder den gefallenen Konstanten `DEFAULT_FIELDS`/`TITLE_ONLY_FIELDS`/`FIELD_BOOSTS`; dass weder `pyproject.toml` noch `uv.lock` ein Erkennungspaket (`langdetect`, `lingua`, `langid` etc.) fuehren; und dass die Drahtformat-Sperre in `test_search_fields_lockstep.py` weiterhin steht. Selbstpruefung gegen einen geleerten Baum (`test_an_emptied_guard_reports_one_finding_per_statement_and_not_zero`) und gegen die eigene Prosa (`test_this_guard_does_not_trip_over_its_own_prose`) vorhanden. Lokaler Lauf gruen. |

**Score:** 4/4 Wahrheiten verifiziert

### Erforderliche Artefakte

| Artefakt | Erwartung | Status | Details |
|---|---|---|---|
| `backend/src/findling/query/rewrite.py` | `FieldPlan`, `LEGACY_PLAN`, `NAME_BOOST`/`TITLE_BOOST`/`BODY_BOOST`, `build_query(plan=...)` | VERIFIED | Existiert, inhaltlich vollstaendig, in drei Aufrufstellen verdrahtet (siehe Wahrheit 2) |
| `backend/src/findling/api/resources.py` | `field_plan_for(marks, index)`, `ReadSide.field_plan`, `SCHEMA_MARK`-Import | VERIFIED | Existiert, Torreihenfolge aus RESEARCH Pattern 1 umgesetzt, `doc_freq`-Gegenprobe vorhanden |
| `backend/tests/test_query_fields_plan.py` | Feldplan gegen echte Indexe beider Generationen | VERIFIED | Zahlreiche Testfunktionen, lokal gruen |
| `backend/tests/test_field_plan_ranking.py` | Rangprobe, TIPPING_BOOST | VERIFIED | 8 Testfunktionen, `TIPPING_BOOST = 0.81`, lokal gruen |
| `backend/tests/test_no_language_detection.py` | Anti-Feature-Waechter | VERIFIED | Rund 17 Testfunktionen, lokal gruen |
| `backend/tests/test_language_cases_query_path.py` | Vier Sprachfaelle auf dem normalen Suchweg | VERIFIED | 549 Zeilen, dritter Ketten-Ausschluss (nur eigene Kette merged), lokal gruen |
| `backend/tests/test_language_proof_steps.py` | Bewachung des ungegateten CI-Schritts | VERIFIED | 757 Zeilen, lokal gruen |
| `.github/workflows/deploy-harp.yml` | Sprachbeweis-Schritt ohne `if:`, Ergebnisseiten-Abrufe, Store upgrade 6 mit es | VERIFIED | Schritt "Language proof..." Zeile 821, kein `if:`, vier Ergebnisseiten-Abrufe Zeilen 1026-1037, `REBUILD_LANGUAGES: 'es,de,en'` Zeile 393 |
| `docs/language-analyzers.md` | Abschnitt "What a question searches", TIPPING_BOOST dokumentiert | VERIFIED | Abschnitt vorhanden mit vier Absaetzen, Zeile 252 traegt 0.81 mit Messdatum |

### Key-Link-Verifikation

| Von | Nach | Ueber | Status | Details |
|---|---|---|---|---|
| `api/search.py` | `field_plan_for` | `side.field_plan` aus `ReadSide` | WIRED | Zeile 255, `build_query(..., plan=side.field_plan)` |
| `api/snippets.py` | `field_plan_for` | `side.field_plan` | WIRED | Zeile 194 |
| `api/diagnose.py` | `field_plan_for` | `side.field_plan` | WIRED | Zeile 205 |
| `field_plan_for` | Verzeichnis (tantivy Index) | `doc_freq(field, "")`-Gegenprobe | WIRED | Faellt bei Ausnahme geschlossen auf `LEGACY_PLAN`, Warnzeile ohne Pfad/Suchbegriff |
| CI-Sprachbeweis | Unified Search + Ergebnisseite | curl gegen OCS-Route und `apps/findling/?query=` | WIRED | Beide CI-Laeufe gruen, 4/4 Matrixaeste je Lauf |

### Verhaltens-Stichproben

| Verhalten | Kommando | Ergebnis | Status |
|---|---|---|---|
| Fuenf angeforderte Testdateien laufen isoliert | `uv run pytest -q tests/test_query_fields_plan.py tests/test_field_plan_ranking.py tests/test_no_language_detection.py tests/test_language_cases_query_path.py tests/test_language_proof_steps.py --no-header` | 110 passed, 1 warning (StarletteDeprecationWarning, unrelated) | PASS |
| Volle Backend-Suite | `uv run pytest -q` aus `backend/` | 2857 passed, 15 skipped, 0 failures, 247.59s | PASS |
| CI-Lauf 1 (Sprachbeweis, ungegated) | `gh run view 36074155306 --json conclusion,jobs` | conclusion success, 4/4 Jobs success inkl. `ubuntu-24.04-arm` | PASS |
| CI-Lauf 2 (Laufzeit eingetragen) | `gh run view 36076006854 --json conclusion,jobs` | conclusion success, 4/4 Jobs success inkl. `ubuntu-24.04-arm` | PASS |
| Debt-Marker-Scan | `grep -n "TBD\|FIXME\|XXX"` auf allen relevanten Quell-/Testdateien | keine Treffer | PASS |

### Requirements-Abdeckung

| Requirement | Quelle | Beschreibung | Status | Beleg |
|---|---|---|---|---|
| LEX-05 | Phase 19 (alle 9 Plaene) | Die Anfrage durchsucht genau die aktiven Sprachfelder mit Feld-Boosts unterhalb `body_en`; keine Spracherkennung | SATISFIED (inhaltlich; Haken in REQUIREMENTS.md noch nicht gesetzt) | Wahrheiten 1-4 oben, CI-Laeufe 36074155306/36076006854 |

**Anstehende Aktion (nicht von diesem Verifikationslauf ausgefuehrt):** Der Haken fuer LEX-05 in `.planning/REQUIREMENTS.md` (aktuell `[ ]`, Zeile 15) und in der Traceability-Tabelle (Zeile 69, aktuell "Pending") ist gemaess Auftrag NICHT von der Verifikation selbst zu setzen. Nach dem Muster von LEX-02 bis LEX-08 gehoert er mit Laufnummer eingetragen, zum Beispiel "Complete (25.09.2026, Verifikation 4/4, CI 36074155306/36076006854)".

### Anti-Patterns

Keine gefunden. Kein `TBD`/`FIXME`/`XXX` in den phasenrelevanten Quell- und Testdateien, keine leeren Ruecksprungwerte, keine hartkodierten leeren Ergebnislisten. Die einzigen "verbotene Worte"-Stellen sind Prosaerklaerungen in `test_no_language_detection.py`, die absichtlich die verbotenen Woerter benennen (dokumentiert und durch eigene Tests gegen falsch-positive Zaehlung abgesichert).

Zwei kleine, dokumentierte Prosa-Altlasten (nicht sicherheits- oder funktionsrelevant): `backend/src/findling/store/repo.py` Zeilen 128 und 1448 nennen weiterhin den in Plan 19-01 gefallenen Namen `DEFAULT_FIELDS`. Laut 19-01/19-03/19-04-SUMMARY.md bewusst nicht mitgenommen, weil der Fussabdruck der jeweiligen Plaene diese Datei nicht enthaelt; in STATE.md als mitzunehmende Kleinigkeit fuer den naechsten Plan gefuehrt, der `store/repo.py` ohnehin anfasst. Kein Blocker fuer das Phasenziel.

### Menschliche Verifikation erforderlich

Keine. Keine `<human-check>`-Bloecke in den neun Plaenen gefunden, alle Erfolgskriterien sind durch Code, automatisierte Tests und tatsaechlich ausgefuehrte, live gepruefte CI-Laeufe belegt.

### Luecken-Zusammenfassung

Keine inhaltlichen Luecken gefunden. Alle vier Erfolgskriterien der ROADMAP sind durch Code, Tests (lokal nachgefahren, 110/110 sowie 2857/2857 gruen) und zwei live gegengeprobte CI-Laeufe (36074155306, 36076006854, je 4/4 gruen inklusive nativem arm64-Ast) belegt. Der einzige offene Punkt ist rein verwaltungstechnisch: das Setzen des LEX-05-Hakens in REQUIREMENTS.md, das laut Auftrag der Verifikation vorbehalten bleibt und hier als anstehende Aktion vermerkt ist statt selbst ausgefuehrt zu werden.

---
*Verifiziert: 2026-09-25T00:32:37Z*
*Verifier: Claude (gsd-verifier)*
