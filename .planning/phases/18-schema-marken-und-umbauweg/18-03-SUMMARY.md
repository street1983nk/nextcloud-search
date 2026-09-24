---
phase: 18-schema-marken-und-umbauweg
plan: 03
subsystem: testing
tags: [tantivy, pytest, ast, schema-migration, query-parser]

# Dependency graph
requires:
  - phase: 18-schema-marken-und-umbauweg
    provides: "Plan 18-01: SCHEMA_VERSION 2, dreizehn Felder, acht bedingungslos registrierte Ketten"
provides:
  - "backend/tests/test_schema_generations.py: Mengeninklusion beider Schemastaende plus AST-Waechter ueber DEFAULT_FIELDS, TITLE_ONLY_FIELDS und FIELD_BOOSTS"
  - "conftest-Fixtures schema_1_index und schema_2_index: ein echter Neun-Felder-Altindex und sein Gegenstueck, mit identischen Dokumenten"
  - "Beweis, dass build_query gegen einen Bestandsindex weder wirft noch degradiert antwortet"
affects: [19-feldlisten-nach-schema-version, 18-04-umbauweg, upgrade-pfad]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Gate-Datei nach Bauart test_analyzer.py:440-470: Quelle als Text lesen und mit ast.parse pruefen, nie importieren"
    - "Fail closed plus gestellte Selbstproben, damit null Befunde nicht mit null Pruefung verwechselt werden"
    - "Eingefrorene Alt-Schemata als Testfixture statt als Nachbau im Testkoerper"

key-files:
  created:
    - backend/tests/test_schema_generations.py
  modified:
    - backend/tests/conftest.py
    - backend/tests/test_query_rewrite.py

key-decisions:
  - "FIELDS_SCHEMA_1 ist ein Literal in der Gate-Datei und wird nicht aus findling.index.schema abgeleitet, sonst waere die Inklusion eine Tautologie"
  - "build_schema_1() in conftest.py ist eine Wort-fuer-Wort-Kopie des Builders aus ca739b1~1, inklusive stored/indexed/fast-Flags, damit der Beweis gegen ein wirklich ausgeliefertes Schema laeuft"
  - "Der Altindex wird zweistufig gebaut: Index(build_schema_1(), path=...) legt das Verzeichnis an, open_index() oeffnet es und haengt alle acht Ketten daran; nur so entsteht der Zustand einer Bestandsinstallation nach dem Upgrade"
  - "write_index gibt jetzt den Index zurueck und teilt seine Schreibschleife als fill_index mit der Schema-1-Fixture, damit zwischen den beiden Generationen nichts ausser dem Schema verschieden ist"
  - "Die Gleichstandspruefung nennt erwartete Trefferlisten statt nur die beiden Laeufe zu vergleichen: vier der sieben Suchzeilen finden alle zwoelf Dokumente, ein blosser Vergleich waere dort aus dem falschen Grund gruen"

patterns-established:
  - "Phasengrenze als Codegrenze: der AST-Waechter faellt geschlossen, wenn eine Feldliste aufhoert eine Konstante zu sein, und benennt damit den Umbau, den Phase 19 vornehmen muss"
  - "Gestellte Quelltextproben (sechs Stueck) neben dem Lauf gegen die echte Quelle, darunter das leere Modul und die berechnete Liste"

requirements-completed: [LEX-04]

# Metrics
duration: 27min
completed: 2026-09-24
---

# Phase 18 Plan 03: Der Zwischenzustand als beweisbar ungefaehrlich Summary

**Die Feldliste der Anfrage bleibt in Phase 18 in der Schnittmenge beider Schemastaende, bewiesen durch vier Mengeninklusionen, einen AST-Waechter mit sechs Selbstproben und sieben Suchzeilen gegen einen echten Neun-Felder-Altindex, ohne eine einzige Produktivzeile zu bewegen.**

## Performance

- **Duration:** 27 min
- **Started:** 2026-09-24T05:18:00Z
- **Completed:** 2026-09-24T05:45:05Z
- **Tasks:** 3
- **Files modified:** 3 (1 neu, 2 geaendert)

## Accomplishments

- `FIELDS_SCHEMA_1`, die neun Feldnamen jeder Fassung bis 1.2.0, als eingefrorenes Literal, und vier Inklusionen darueber: `DEFAULT_FIELDS` gegen beide Schemastaende, `TITLE_ONLY_FIELDS` und die Schluessel von `FIELD_BOOSTS` gegen den alten. Damit ist der `ValueError`-Pfad von `parse_query_lenient` in dieser Phase nicht erreichbar, und das ist ein Satz ueber Mengen, kein Integrationstest.
- Ein echter Altindex als Fixture. `build_schema_1()` ist der Builder aus dem letzten Commit vor 18-01, `open_schema_1_index()` legt das Verzeichnis damit an und oeffnet es dann ueber `open_index`, sodass acht Ketten ueber einem Neun-Felder-Schema haengen: genau der Zustand einer Bestandsinstallation nach dem Upgrade.
- Ein AST-Waechter, der `query/rewrite.py` liest statt importiert, `ast.Name` gegen die `FIELD_*`-Konstanten von `index/schema` aufloest (also `FIELD_BODY_ES` und `"body_es"` als denselben Befund liest) und in drei Lagen geschlossen faellt: fehlende Liste, Liste die keine ist, Eintrag den er nicht lesen kann.
- Sieben Suchzeilen mit ihren erwarteten Trefferlisten, gegen beide Generationen gefuehrt, davon drei mit echter Teilmenge (8, 1 und 6 von 12 Dokumenten), sodass der Gleichstand nicht aus Gleichfoermigkeit entsteht.

## Task Commits

1. **Task 1: Schema-1-Fixture und Mengeninklusion** , `0e74f68` (test)
2. **Task 2: AST-Waechter ueber die Feldlisten der Anfrage** , `90c95de` (test)
3. **Task 3: build_query gegen einen echten Altindex** , `f9b61e4` (test)

## Files Created/Modified

- `backend/tests/test_schema_generations.py` (neu, 17 Faelle) , das eingefrorene Neun-Namen-Literal, sieben Mengenfaelle, drei Faelle gegen den gestellten Altindex, der Waechter `body_fields_outside_the_old_schema` und sechs Selbstproben.
- `backend/tests/conftest.py` , `FIXTURE_DOCUMENTS`, `fill_index` (aus `write_index` herausgeloest), `build_schema_1`, `open_schema_1_index`, `write_schema_1_index` und die Fixtures `schema_1_index` und `schema_2_index`. `write_index` gibt jetzt den Index zurueck.
- `backend/tests/test_query_rewrite.py` , neuer Abschnitt mit `_hits_of`, der Tabelle `SEARCHES` und den beiden Faellen gegen den Altindex und den Gleichstand beider Generationen.

## Decisions Made

- **Das eingefrorene Literal gehoert in die Gate-Datei, der Builder in conftest.** Die Feldnamen stehen zweimal im Baum: als `FIELDS_SCHEMA_1` im Gate und als Argumente in `build_schema_1()`. Das ist bewusst keine geteilte Konstante. Wuerde der Builder aus dem Literal lesen, waere er eine Schleife ueber Namen ohne die stored/indexed/fast-Flags, die den Index erst zu dem machen, was ausgeliefert wurde. Zusammengehalten werden die beiden von `test_the_old_index_accepts_every_field_of_the_query`, das jedes Feld der Anfrage gegen den gebauten Index parst: eine Abweichung in der Schreibweise kaeme genau dort heraus.
- **Der Waechter loest ueber `vars(index_schema)` auf, und das ist keine Tautologie.** Die Aufloesung beantwortet "wofuer steht dieser Bezeichner", nie "welche Felder gibt es". Die Frage nach den Feldern beantwortet allein das Literal.
- **Erwartete Trefferlisten statt eines blossen Vergleichs der beiden Laeufe.** Gemessen: `vertrag`, `kuendigungsfrist`, `akte` und `"drei Monate"` finden alle zwoelf Dokumente, `absaetze` acht, `7` eines, `type:pdf vertrag` sechs. Ohne die erwarteten Listen waeren vier der sieben Zeilen aus dem falschen Grund gruen, und zwei leere Listen waeren auch gleich.

## Deviations from Plan

Keine Abweichung im Sinne der Regeln 1 bis 4. Zwei Praezisierungen gegenueber dem Planwortlaut, beide innerhalb der Abnahmekriterien:

**1. Die Abwesenheit von `body_es` wird ueber `parse_query_lenient` gezeigt, nicht ueber eine Schema-Introspektion.**
Das Abnahmekriterium nennt eine "`searcher().schema`-Suche nach `body_es`". Die Python-Bindings von tantivy 0.26.2 geben dafuer nichts her: `class Schema: pass` im mitgelieferten Stub, kein Feldverzeichnis, keine Iteration. Gezeigt wird dieselbe Tatsache dort, wo sie zaehlt: `parse_query_lenient("vertrag", default_field_names=["body_es"])` gegen den Altindex wirft `ValueError: Field \`body_es\` is not defined in the schema.`, waehrend dieselbe Abfrage auf `body_de` zwoelf Dokumente liefert. Das ist zugleich die Ausnahme, gegen die der ganze Plan argumentiert, einmal wirklich provoziert.

**2. `write_index` in conftest.py wurde aufgeteilt und gibt jetzt den Index zurueck.**
Nicht im Plan genannt, aber notwendig fuer sein Ziel: die Aussage "derselbe Bestand antwortet unter beiden Schemastaenden gleich" ist nur belastbar, wenn zwischen den Indizes nichts ausser dem Schema verschieden ist. Eine zweite Schreibschleife waere genau der Weg, auf dem das aufhoert zu stimmen. Die Schleife heisst jetzt `fill_index` und wird von beiden Seiten gerufen; `write_index` behaelt Name, Signatur und Verhalten und gibt zusaetzlich den Index zurueck. Alle zehn Testmodule, die aus conftest importieren, laufen unveraendert.

---

**Total deviations:** 0 auto-fixed, 2 Praezisierungen
**Impact on plan:** Keine Ausweitung. Beide Punkte dienen den Abnahmekriterien des Plans.

## Issues Encountered

- **Der Worktree hatte keine venv.** `uv sync --frozen` im `backend/`-Verzeichnis, danach liefen alle Gates.
- **`ruff format` hat zweimal zugeschlagen**, einmal an einer 126 Zeichen langen Dict-Comprehension und einmal an einer umgebrochenen Testsignatur. Beides vor dem jeweiligen Commit geradegezogen.

## Verification

Alle vier Gates gruen, volle Suite gruen:

| Gate | Ergebnis |
|---|---|
| `uv run python -m pytest -q` | 2575 passed, 15 skipped, 285 s |
| `uv run ruff check` | All checks passed |
| `uv run ruff format --check` | 130 files already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture` | keine Befunde |

**Rot-Beweis des Waechters gegen die echte Quelle**, im Speicher gefuehrt, ohne `backend/src` anzufassen:

| Eingespielter Defekt | Befund |
|---|---|
| unveraendert | `[]` |
| `FIELD_BODY_ES` in `DEFAULT_FIELDS` | `DEFAULT_FIELDS in backend/src/findling/query/rewrite.py names body_es, which an index of the old schema lacks` |
| `"body_nl"` als Schluessel in `FIELD_BOOSTS` | `FIELD_BOOSTS in ... names body_nl, which an index of the old schema lacks` |

**`backend/src` unberuehrt:** `git diff --name-only d8f628aa..HEAD` nennt genau `backend/tests/conftest.py`, `backend/tests/test_query_rewrite.py`, `backend/tests/test_schema_generations.py`. `git diff --name-only backend/src` ist leer, die Ratsche `PACKAGE_TREE_HASH_TODAY` hat sich nicht bewegt, der Plan konnte neben 18-02 in derselben Welle laufen.

**Abnahmekriterium Task 2, dritter Punkt:** `grep -c "^from findling.query.rewrite import" backend/tests/test_schema_generations.py` meldet `1`, und der Waechter benutzt diese Konstanten nicht; er liest die Datei ueber `Path.read_text` und `ast.parse`.

## User Setup Required

Keine. Der Plan aendert ausschliesslich Testdateien, kein Paket, keine Konfiguration.

## Next Phase Readiness

- Erfolgskriterium 1 der Phase (in keinem Zwischenzustand laeuft eine Suche leer) ist auf Testebene abgesichert, solange die Feldliste eine Konstante bleibt.
- **Uebergabe an Phase 19, ausdruecklich:** Sobald `DEFAULT_FIELDS` und `FIELD_BOOSTS` Funktionen des gespeicherten `schema_version`-Merkers werden, wird `body_fields_outside_the_old_schema` genau einen Befund pro umgebauter Liste melden. Das ist gewollt und im Modul-Docstring so festgehalten: der Commit, der den Umbau vornimmt, ist der Commit, der diesen Waechter ersetzen muss, und er muss in derselben Aenderung sagen, was an seine Stelle tritt. `test_the_gate_fails_closed_when_a_field_list_stops_being_a_list` haelt diesen Uebergang bereits als gestellte Probe fest.
- Die Fixtures `schema_1_index` und `schema_2_index` stehen in conftest und sind fuer den Umbauweg (18-04) und fuer jeden weiteren Beweis gegen einen Bestandsindex sofort nutzbar.

## Self-Check: PASSED

- `backend/tests/test_schema_generations.py` vorhanden
- `backend/tests/conftest.py` vorhanden
- `backend/tests/test_query_rewrite.py` vorhanden
- `.planning/phases/18-schema-marken-und-umbauweg/18-03-SUMMARY.md` vorhanden
- Commits `0e74f68`, `90c95de`, `f9b61e4` alle drei in `git log` gefunden

---
*Phase: 18-schema-marken-und-umbauweg*
*Completed: 2026-09-24*
