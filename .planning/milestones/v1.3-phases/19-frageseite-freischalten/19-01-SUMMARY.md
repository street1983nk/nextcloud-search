---
phase: 19-frageseite-freischalten
plan: 01
subsystem: api
tags: [tantivy, query-parser, field-boosts, dataclass, pytest]

# Dependency graph
requires:
  - phase: 18-schema-und-umbau
    provides: "Dreizehn-Felder-Schema, schema_1_index/schema_2_index-Fixturen, AST-Waechter als Phasengrenze"
provides:
  - "FieldPlan: frozen dataclass mit fields, boosts und title_only als EIN Wert"
  - "LEGACY_PLAN: der eingefrorene Bestandsplan jeder Auslieferung bis 1.2.0"
  - "NAME_BOOST, TITLE_BOOST, BODY_BOOST: jede Gewichtszahl hat genau eine Schreibweise"
  - "build_query(..., plan=LEGACY_PLAN) als keyword-only-Parameter mit sicherem Vorgabewert"
  - "backend/tests/test_query_fields_plan.py: der Plan gegen echte Indexe beider Generationen"
affects: [19-03 Feldplan aus den zwei Marken, 19-04 Rangprobe, 19-06 Sprachfaelle auf dem Suchweg]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Zwei Haelften einer Parserfrage sind ein Wert, nicht zwei Konstanten"
    - "Neue Parameter keyword-only mit dem fail-closed-Vorgabewert"
    - "Ein Waechter ueber Namen wird durch eine Probe an der Maschine ersetzt"

key-files:
  created:
    - backend/tests/test_query_fields_plan.py
  modified:
    - backend/src/findling/query/rewrite.py
    - backend/tests/test_schema_generations.py
    - backend/tests/test_query_rewrite.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Feldliste und Boost-Abbildung sind ein Wert, weil parse_query_lenient gemessen auch fuer field_boosts wirft (19-RESEARCH M-1)"
  - "Der Vorgabewert von plan ist LEGACY_PLAN und niemals etwas aus settings(): wer den Plan vergisst, sucht die vier Felder von heute"
  - "BODY_BOOST ist nach Sprachcode geschluesselt wie schema.BODY_FIELD, 0.6 fuer es/it/nl/pt ist eine Empfehlung und wird von 19-04 nachgemessen"
  - "Der ganze Plan ist EIN Commit: Ratschenregel und die Uebergabebedingung aus 18-03 lassen keinen gruenen Zwischenstand zu"

patterns-established:
  - "FieldPlan: eine Parserfrage, ein Wert. Getrennte Haelften sind getrennte Wege in denselben Totalausfall"
  - "Ersatz einer Phasengrenze: der geleerte Modulkopf nennt seinen Nachfolger namentlich"

requirements-completed: []

# Metrics
duration: 42min
completed: 2026-09-24
---

# Phase 19 Plan 01: FieldPlan als Wert Summary

**Die drei Modulkonstanten der Frageseite sind ein frozen FieldPlan mit sicherem Vorgabewert, und der AST-Waechter der Phasengrenze ist durch eine Probe an zwei echten Indexen ersetzt**

## Performance

- **Duration:** rund 42 min
- **Started:** 2026-09-24T21:00:00Z
- **Completed:** 2026-09-24T21:42:00Z
- **Tasks:** 3
- **Files modified:** 5 (4 geaendert, 1 neu)

## Accomplishments

- `DEFAULT_FIELDS`, `TITLE_ONLY_FIELDS` und `FIELD_BOOSTS` existieren als Modulnamen nicht mehr. Ihre Werte und ihre erklaerenden Kommentare stehen unveraendert in `LEGACY_PLAN`, einer Instanz der neuen frozen dataclass `FieldPlan` mit `fields`, `boosts` und `title_only`.
- Die Gewichtszahlen haben je genau eine Schreibweise: `NAME_BOOST = 3.0`, `TITLE_BOOST = 2.0` und `BODY_BOOST` als geschlossene Abbildung nach Sprachcode (de 1.0, en 0.8, es/it/nl/pt 0.6), gebaut wie `schema.BODY_FIELD`.
- `build_query` nimmt `plan: FieldPlan = LEGACY_PLAN` als letzten keyword-only-Parameter. Keine der rund zwei Dutzend vorhandenen Aufrufzeilen wurde angefasst, und ein neuer Fall in `test_query_rewrite.py` belegt, dass der Vorgabewert wirklich der Bestandsplan ist.
- Der AST-Waechter aus `test_schema_generations.py` ist weg (alles ab dem Abschnittstrenner, 196 Zeilen), sein Modulkopf sagt jetzt, was er war, warum er faellt und wer an seine Stelle getreten ist.
- `backend/tests/test_query_fields_plan.py` ist der Ersatz und die staerkere Aussage: fuenf Faelle, die Feldliste und Boosts GEMEINSAM in echte `parse_query_lenient`-Aufrufe gegen `schema_1_index` und `schema_2_index` schicken, mit der Gegenprobe, dass ein zusaetzlicher Boost auf `body_es` denselben Pfad aufreisst.
- `PACKAGE_TREE_HASH_TODAY` ist im selben Commit nachgezogen (`9e76762c...`), `PACKAGE_FILES_TODAY` steht weiter auf 56, `PHP_TREE_HASH_TODAY` ist unberuehrt.

## Task Commits

Die drei Tasks stehen in einem gemeinsamen Commit, siehe Deviation 1:

1. **Task 1: FieldPlan, LEGACY_PLAN und der plan-Parameter** - `82bf2b1` (refactor)
2. **Task 2: Die Phasengrenze aufloesen und den Ersatz danebenstellen** - `82bf2b1` (refactor)
3. **Task 3: Ratsche nachziehen und die Gates gruen fahren** - `82bf2b1` (refactor)

**Plan metadata:** siehe docs-Commit unten

## Files Created/Modified

- `backend/src/findling/query/rewrite.py` - `FieldPlan`, `NAME_BOOST`/`TITLE_BOOST`/`BODY_BOOST`, `LEGACY_PLAN`, `plan`-Parameter an `build_query`, `parse_query_lenient` liest beide Haelften aus dem Plan; Modulkopf sagt, dass die Antwort ab hier auch am Verzeichnis haengt
- `backend/tests/test_query_fields_plan.py` - NEU, fuenf Faelle: Bestandsplan gegen Schema-1-Index (Felder und Boosts gemeinsam), die Dateinamenhaelfte, die Gegenprobe mit `body_es`, die Mengenaussage `set(boosts) <= set(fields)`, derselbe Plan gegen den Schema-2-Index
- `backend/tests/test_schema_generations.py` - AST-Waechter entfernt, Modulkopf von drei auf zwei Teile umgeschrieben und nennt `backend/tests/test_query_fields_plan.py` namentlich; die Mengeninklusionen lesen `LEGACY_PLAN.fields`, `.title_only` und `.boosts`, Testnamen unveraendert
- `backend/tests/test_query_rewrite.py` - ein neuer Fall `test_the_plan_a_caller_leaves_out_is_the_frozen_legacy_plan`, sonst unveraendert
- `backend/tests/test_measurement_scripts.py` - sechsunddreissigster Absatz der Ratschenkette plus neuer Baumhash

## Decisions Made

- **Beide Haelften in einem Wert.** 19-RESEARCH Messung M-1 ist der Grund und steht im Klassendocstring: `parse_query_lenient` wirft fuer einen unbekannten Feldnamen unter `field_boosts` dieselbe `ValueError` wie unter `default_field_names`. Zwei Konstanten waeren zwei Wege in denselben Totalausfall, von denen nur einer wie der Gegenstand aussieht.
- **`BODY_BOOST` nach Sprachcode, nicht nach Feldnamen.** So ist sie gebaut wie `schema.BODY_FIELD` und die kommenden Plaene koennen aus Sprachmenge plus Abbildung einen Plan bauen, ohne eine zweite Lesart einzufuehren. `LEGACY_PLAN` liest seine beiden Koerpergewichte da heraus.
- **`RewrittenQuery` bleibt bei sechs Feldern.** Der Plan ist Eingabe und nicht Ergebnis.
- **Die 0.6 ist als Empfehlung markiert.** Der Kommentar sagt ausdruecklich, dass die Zahl aus `.planning/research/FEATURES.md` Frage 3 stammt, keine Messung ist und von der Rangprobe in 19-04 nachgeliefert wird; nicht offen ist die Richtung (unterhalb `body_en` bei 0.8, die woertliche Zusage von Erfolgskriterium 3).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Alle drei Tasks in einem Commit statt in dreien**
- **Found during:** Task 1 (vor dem ersten Commit)
- **Issue:** Drei getrennte Commits sind in diesem Plan nicht erreichbar, ohne mindestens eine der bindenden Projektregeln zu verletzen. (a) Die Arbeitsregel "jede Aenderung unter `backend/src/findling` zieht `PACKAGE_TREE_HASH_TODAY` im SELBEN Commit nach" zwingt Task 3 in denselben Commit wie Task 1; die Akzeptanzbedingung von Task 3 sagt dasselbe ("`git diff --name-only` zeigt `test_measurement_scripts.py` und `query/rewrite.py` im selben Commit"). (b) Die Plan-Objective und die Uebergabebedingung aus `18-03-SUMMARY.md` verlangen, dass der AST-Waechter und die Nennung seines Ersatzes im selben Commit stehen wie die Aufloesung der drei Konstanten; nach Task 1 allein importiert `test_schema_generations.py` drei Namen, die es nicht mehr gibt, die Suite ist rot und die Regel "Qualitaetsgates lokal gruen VOR jedem Commit" waere verletzt.
- **Fix:** Tasks 1 bis 3 in der Planreihenfolge ausgefuehrt und verifiziert (je eigene Akzeptanzpruefung, siehe unten), danach ein gemeinsamer atomarer Commit `82bf2b1` ueber alle fuenf Dateien.
- **Files modified:** keine zusaetzlichen
- **Verification:** Die Akzeptanzkriterien aller drei Tasks einzeln geprueft, bevor committet wurde; volle Suite danach gruen.
- **Committed in:** `82bf2b1`

**2. [Rule 3 - Blocking] `ruff format` hat zwei Dateien nachformatiert**
- **Found during:** Task 3 (Gate-Lauf)
- **Issue:** `ruff format --check` meldete `rewrite.py` und `test_schema_generations.py` als unformatiert (Leerzeilenabstand vor der neuen Klasse, Dateiende nach der Kuerzung).
- **Fix:** `uv run ruff format .` ausgefuehrt, danach der Baumhash neu gemessen, damit die Ratsche den formatierten Stand traegt und nicht den davor.
- **Files modified:** `backend/src/findling/query/rewrite.py`, `backend/tests/test_schema_generations.py`
- **Verification:** `ruff format --check` meldet "134 files already formatted".
- **Committed in:** `82bf2b1`

---

**Total deviations:** 2 auto-fixed (beide Rule 3, blockierend)
**Impact on plan:** Kein Scope-Zuwachs. Deviation 1 aendert nur die Commit-Granularitaet, nicht den Inhalt; Deviation 2 ist Routine des Qualitaetsgates.

## TDD Gate Compliance

Task 1 traegt `tdd="true"`, und der RED-Schritt war hier nicht herstellbar: die Akzeptanzkriterien desselben Tasks verbieten ausdruecklich, `test_query_rewrite.py` in diesem Task anzufassen, und die neue Testdatei gehoert laut Plan zu Task 2. Ein `test(...)`-Commit vor dem `refactor(...)` haette also entweder den Fussabdruck des Tasks gesprengt oder einen Test enthalten, der gegen die noch unveraenderte Maschine gruen ist, was der Fail-Fast-Regel widerspricht.

Was an die Stelle des RED-Gates getreten ist, und es ist fuer einen Umbau ohne Verhaltensaenderung die passendere Zusicherung: die 90 vorhandenen Faelle aus `test_query_rewrite.py` und `test_index_open.py` liefen unveraendert vor und nach dem Umbau, plus die neue Gegenprobe in `test_query_fields_plan.py`, die den Fehlerpfad provoziert, den der Plan verhindert. Der Plan selbst traegt `type: execute`, nicht `type: tdd`; die Gate-Sequenz eines TDD-Plans ist hier nicht einschlaegig.

## Threat Flags

Keine. Der Plan legt keine Route an, oeffnet keinen neuen Netzpfad und aendert weder `pyproject.toml` noch `uv.lock`. Die Mitigationen T-19-01-01 (sicherer Vorgabewert) und T-19-01-02 (`set(boosts) <= set(fields)` plus Gegenprobe) sind umgesetzt und jeweils von einem Testfall belegt; T-19-01-04 haelt: die Logzeile bei den Parserfehlern steht unveraendert auf `debug` und zaehlt nur.

## Known Stubs

Keine.

## Issues Encountered

- Drei Prosastellen ausserhalb des Fussabdrucks nennen weiter den gefallenen Namen `DEFAULT_FIELDS`: `backend/src/findling/store/repo.py` Zeilen 128 und 1448 sowie `backend/tests/test_language_cases_field_level.py` Zeilen 7 und 221. Der Plan nennt in `files_modified` genau fuenf Dateien und die Verifikation verlangt, dass keine sechste im Diff steht, also wurden sie NICHT angefasst. Als mitzunehmende Kleinigkeit in STATE.md eingetragen; 19-02 fasst `test_language_cases_field_level.py` ohnehin an.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `LEGACY_PLAN` ist der eingefrorene Ausgangspunkt, gegen den 19-03 den berechneten Feldplan haelt, und `BODY_BOOST` ist die Abbildung, aus der 19-03 die Gewichte der aktiven Sprachen zieht.
- `build_query` nimmt einen Plan entgegen, ohne dass eine Aufrufstelle ihn schon liefert: die drei Aufrufstellen (`api/search.py`, `api/snippets.py`, `api/diagnose.py`) sind unberuehrt und bleiben es bis 19-03.
- `test_query_fields_plan.py` ist bewusst nur zur Haelfte gefuellt. Die zweite Haelfte (jede erzeugbare Sprachmenge gegen ihre Schemageneration) gehoert zu dem Plan, der Plaene berechnet.

## Verification

- `uv run pytest -q` aus `backend/`: 2749 bestanden, 15 uebersprungen, 0 Fehlschlaege.
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 134 files already formatted.
- `PYRIGHT_PYTHON_FORCE_VERSION=latest uv run pyright`: 0 errors, 0 warnings, 0 informations.
- `uv run vulture src tests --min-confidence 80`: keine Befunde.
- `git diff --stat` nennt genau die fuenf Dateien aus `files_modified`, `pyproject.toml` und `uv.lock` stehen nicht im Diff.
- Kein Em-Dash und keine neuen echten Umlaute in Code oder Kommentaren; die vorhandenen Umlaute stehen ausschliesslich in den deutschen Testdaten und in `UMLAUTS`, wo sie hingehoeren.

---
*Phase: 19-frageseite-freischalten*
*Completed: 2026-09-24*

## Self-Check: PASSED

Alle fuenf Code-Dateien und die SUMMARY liegen auf der Platte, beide Commits (`82bf2b1`, `6a7ae9f`)
stehen in der Historie, das Arbeitsverzeichnis ist sauber.
