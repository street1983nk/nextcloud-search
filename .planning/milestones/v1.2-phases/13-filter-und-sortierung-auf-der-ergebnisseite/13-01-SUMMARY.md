---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 01
subsystem: backend-query
tags: [tantivy, filter, typgruppen, zeitraum, range-query, fast-field, filt-01, filt-03]

requires:
  - phase: 02-suche-und-ranking
    provides: "build_query, extract_filters, carried_operators, _extension_query, FIELD_EXT als Rohterm"
  - phase: 01-index-und-schema
    provides: "FIELD_MTIME als Fast-Spalte (indexed=False, fast=True), seit v1.0 ohne Reindex nutzbar"
provides:
  - "TYPE_GROUPS: die einzige Abbildung von Gruppe auf Endung im Projekt, sechs Gruppen in fester Reihenfolge"
  - "extensions_of(groups): Gruppennamen zu Endungen, kleingeschrieben, doppelfrei, still bei unbekannten Namen"
  - "_mtime_range_query(index, since, until): Bereichsabfrage über die Fast-Spalte, beide Grenzen inklusiv"
  - "_filter_clause(index, extensions, since, until): Endungen und Zeitraum als genau eine Klausel"
  - "build_query(index, text, *, title_only=False, groups=(), since=None, until=None)"
  - "RewrittenQuery.filter_query: dieselbe Klausel einzeln, für die semantische Hälfte in 13-02"
  - "docs/search-filters.md: die sechs Gruppen und die zwei Grenzen, die nicht in den Code gehören"
affects: [13-02, 13-03, 13-04, 13-07, 13-09]

tech-stack:
  added: []
  patterns:
    - "Strukturierter Filterparameter statt type:-Text, damit carried_operators die Vektorhälfte nicht abschaltet"
    - "Erste Bereichsabfrage des Projekts: Query.range_query auf einer nicht indizierten Fast-Spalte, use_inverted_index bleibt False"
    - "Eine Klausel, zwei Verwendungen: an die geparste Abfrage gehängt und zusätzlich einzeln herausgereicht"

key-files:
  created:
    - docs/search-filters.md
  modified:
    - backend/src/findling/query/rewrite.py
    - backend/tests/test_query_rewrite.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Die Textsyntax wird an TYPE_GROUPS angeschlossen, nicht umgekehrt: type:images ist gleichbedeutend mit dem Chip, ein unbekanntes Wort bleibt eine rohe Endung"
  - "Vereinigung statt Schnittmenge von Textendungen und Gruppenendungen, Textendungen zuerst"
  - "csv steht bei den Tabellen und nicht beim Text, weil es für jeden, der es öffnet, eine Tabelle ist"
  - "filter_query bleibt bei den frühen Rückgaben (Tiefenwächter, leere Zeile) auf None: ohne Abfrage gibt es nichts einzugrenzen"
  - "Die Testbeispiele des Plans wurden vom Suchwort frist auf vertrag umgestellt, weil nur vertrag im Fixture zwei Dokumente verschiedener Gruppen trifft"

patterns-established:
  - "Grenzen einer Allowlist gehören in docs/ und nicht in den Code (nicht gelistete Endung, Datei ohne Endung)"
  - "Der Grund für einen nicht gesetzten Parameter steht als Messdatum im Docstring, damit ihn niemand korrigiert"

requirements-completed: []  # FILT-01 und FILT-03 tragen noch 13-03, 13-04, 13-07 und 13-09

duration: 16min
completed: 2026-09-16
---

# Phase 13 Plan 01: Ein Filtervokabular und zwei Abfrageklauseln Summary

**Die sechs Typgruppen und der Zeitraum entstehen als strukturierte Parameter von `build_query`, hängen sich als genau eine `Occur.Must`-Klausel an die geparste Abfrage und liegen zusätzlich einzeln am Ergebnis, ohne die Operator-Marke `FILETYPE` zu berühren.**

## Performance

- **Duration:** 16 min
- **Started:** 2026-09-16T17:36:00Z
- **Completed:** 2026-09-16T17:52:00Z
- **Tasks:** 3
- **Files modified:** 4 (1 neu, 3 geändert)

## Accomplishments

- `TYPE_GROUPS` steht mit genau sechs Gruppen in der Reihenfolge pdf, documents, spreadsheets, presentations, images, text. `jpg` und `jpeg` stehen beide darin, ebenso `tif` und `tiff`, weil eine Datei mit der anderen Schreibweise dasselbe Symbol in der Dateiliste trägt und sonst aus einem Filter fiele, zu dem sie sichtbar gehört.
- `extensions_of` schreibt jeden Gruppennamen klein (der Rohtokenizer normalisiert nichts, "PDF" träfe sonst keinen einzigen Term), liefert für unbekannte Namen nichts und ist doppelfrei in stabiler Reihenfolge.
- `_mtime_range_query` ist die erste Bereichsabfrage des Projekts. `use_inverted_index` wird nicht gesetzt und nicht durchgereicht; der Docstring nennt `indexed=False` und die am 16.09.2026 gemessene leere Trefferliste bei `True` als Grund, damit die Zeile beim nächsten Umbau nicht "korrigiert" wird.
- `_filter_clause` verbindet Endungsklausel und Bereichsklausel zu genau einer Klausel. Sie wird einmal gebaut, an die geparste Abfrage gehängt und als `RewrittenQuery.filter_query` herausgereicht, damit 13-02 dieselbe Klausel auf die semantische Hälfte legen kann.
- `extract_filters` löst ein `type:`-Wort über dieselbe Tabelle auf: `type:images` bindet ab jetzt alle acht Bildendungen, `type:pdf` bleibt `('pdf',)`, `type:xyz` bleibt die rohe Endung `xyz`. Es gibt damit wirklich nur ein Vokabular.
- `carried_operators` blieb unverändert und trägt jetzt über dem `FILETYPE`-Zweig den Satz, der die Trennlinie benennt: die Marke hängt am Text und ausschließlich an ihm.
- `docs/search-filters.md` nennt die sechs Gruppen mit ihren Endungen und die zwei Grenzen, die ausdrücklich nicht in den Code gehören: eine nicht gelistete Endung ist unter keinem Chip erreichbar, und eine Datei ohne Endung ist es auch nicht, weil `extension_of` dafür den leeren String liefert.
- Dreizehn neue Testfälle, darunter der Negativfall von FILT-01 und der Zukunftsfall als Wächter gegen die stille Falle.

## Task Commits

Jeder Task wurde einzeln committet:

1. **Task 1: TYPE_GROUPS, die zwei Klausel-Fabriken und die erweiterte build_query-Signatur** - `3c64b8f` (feat)
2. **Task 2: Ein Vokabular auch für die Textsyntax, und die Marke FILETYPE bleibt am Text** - `336afaa` (feat)
3. **Abweichung: Baumhash des Pakets nachziehen** - `1f06327` (test)
4. **Task 3: Testfälle für Gruppen, Vereinigung, Zeitraum und den Negativfall** - `a6216e7` (test)

## Files Created/Modified

- `docs/search-filters.md` (neu, 57 Zeilen) - die sechs Gruppen als Tabelle, die Vereinigungsregel, die zwei Grenzen, die Semantik von since/until
- `backend/src/findling/query/rewrite.py` (565 Zeilen) - `TYPE_GROUPS`, `extensions_of`, `_mtime_range_query`, `_filter_clause`, `filter_query` an `RewrittenQuery`, neue `build_query`-Signatur, Gruppenauflösung in `extract_filters`
- `backend/tests/test_query_rewrite.py` (534 Zeilen) - dreizehn neue Fälle in einem eigenen Abschnitt
- `backend/tests/test_measurement_scripts.py` - `PACKAGE_TREE_HASH_TODAY` nachgezogen, mit Begründungsabsatz

## Decisions Made

- **Die Textsyntax wird an die Tabelle angeschlossen, nicht umgekehrt.** 13-RESEARCH Befund 4 stellt fest, dass heute überhaupt kein Vokabular existiert: `extract_filters` nahm das Wort hinter `type:` wörtlich. Die neue Tabelle ist damit die Quelle, und `type:images` bedeutet dasselbe wie der Chip. Ein Wort, das die Tabelle nicht kennt, bleibt eine rohe Endung, damit `type:epub` weiterhin funktioniert.
- **Vereinigung statt Schnittmenge.** `type:pdf` plus Chip "Bilder" wäre als Schnittmenge garantiert leer, und die Seite hätte keine Möglichkeit, eine leere Liste zu erklären, die niemandes Fehler ist. Die Textendungen stehen zuerst in der Reihenfolge.
- **`csv` steht bei den Tabellen.** Die Mimetype-Zuordnung führt es unter `text/csv`, aber die Gruppe, in der ein Nutzer nachsieht, ist die, zu der es gehört. Der Grund steht in `docs/search-filters.md`.
- **`filter_query` bleibt bei den frühen Rückgaben `None`.** Eine Zeile, die nur aus einem Filter besteht, erreicht die Suchmaschine nicht; eine Klausel ohne Abfrage wäre eine Klausel, die niemand benutzen kann.
- **Die Grenzen der Tabelle stehen in `docs/` und nicht im Code.** Beide sind Eigenschaften des Index und keine Entscheidung, die ein Leser anders treffen könnte; im Code steht nur der Verweis.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Der Baumhash des Python-Pakets war nach Task 1 rot**

- **Found during:** Gesamtlauf der Backend-Tests nach Task 2
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` hält einen sha256 über alle 54 Dateien unter `backend/src/findling`. Jede Änderung am Paket macht ihn rot; der Kommentar über der Konstante sagt ausdrücklich, dass "this one is what the next change to the package has to move".
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf `eb641c83...` nachgezogen. `PACKAGE_FILES` bleibt bei 54, weil genau eine Datei ihre Bytes geändert hat und keine hinzukam. Über der Konstante steht der vorgeschriebene Begründungsabsatz mit Datum, Plan und geänderter Datei.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` = 228 passed
- **Committed in:** `1f06327`

**2. [Rule 1 - Bug im Plantext] Zwei Testbeispiele des Plans wären im Fixture nicht erfüllbar gewesen**

- **Found during:** Task 3
- **Issue:** Der Plan schreibt "`groups=['pdf','documents']` findet beide Dokumente" und "`build_query(index, 'type:pdf frist', groups=['documents'])` findet BEIDE Dokumente". Im Fixture von `test_query_rewrite.py` trägt das docx-Dokument (`Vertrag.docx`) das Wort "frist" nicht; mit diesem Suchwort ist die Behauptung auch bei völlig korrektem Code nicht erfüllbar, und der Fall hätte die Vereinigung gar nicht geprüft.
- **Fix:** Beide Fälle laufen mit dem Suchwort `vertrag`, das die Dokumente 1 (pdf) und 2 (docx) trifft. Damit ist der Unterschied zwischen Vereinigung ([1, 2]) und Schnittmenge ([]) im Ergebnis sichtbar, was die eigentliche Zusage ist. Die Zeitraumfälle laufen weiter mit `frist`, weil dort die Dokumente 1 und 3 gebraucht werden.
- **Files modified:** backend/tests/test_query_rewrite.py
- **Verification:** `uv run python -m pytest tests/test_query_rewrite.py -q` = 44 passed
- **Committed in:** `a6216e7`

---

**Total deviations:** 2 auto-fixed (1 blockierendes Gate, 1 Fehler in einem Plan-Beispiel)
**Impact on plan:** Kein Scope Creep. Beide Abweichungen betreffen Testdateien; die Zusagen des Plans sind unverändert belegt.

## Issues Encountered

Keine. Die Typisierung von `Query.range_query` (der `_RangeType`-TypeVar gegen zwei `int | None`-Argumente) war der einzige Punkt, an dem pyright hätte stolpern können; er ist ohne Umweg grün.

## Known Stubs

Keine. `RewrittenQuery.filter_query` wird in diesem Plan bewusst nur bereitgestellt und noch von niemandem gelesen; das ist kein Stub, sondern die Nahtstelle, die Plan 13-02 in `index/search.py::_mtimes_of` anschließt. Die drei Produktivaufrufer von `build_query` (`api/search.py`, `api/snippets.py`, `api/diagnose.py`) bleiben unverändert lauffähig, weil alle neuen Parameter Schlüsselwortparameter mit Vorgabewert sind; Plan 13-03 zieht sie nach.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` (ganzes Backend) | All checks passed |
| `uv run ruff format --check .` (121 Dateien) | already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | keine Meldung |
| `uv run python -m pytest -q` (ganze Suite) | 2074 passed, 15 skipped |
| `uv run ruff check --config pyproject.toml ../scripts` | All checks passed |
| `uv run ruff format --config pyproject.toml --check ../scripts` | 10 Dateien formatiert |
| Vokabular-Gate (gesperrtes Wort in `docs/search-filters.md`) | 0 Treffer |

Kein PHP angefasst, also kein `php -l` nötig.

## User Setup Required

Keine. Kein Paket installiert, kein Schema geändert, kein Reindex nötig.

## Next Phase Readiness

- Plan 13-02 kann `RewrittenQuery.filter_query` unverändert übernehmen und als `(Occur.Must, klausel)` an die `Should`-Klauseln in `index/search.py::_mtimes_of` legen. Das ist die zweite der beiden Stellen aus 13-RESEARCH Befund 1; ohne sie lässt der Filter typfremde Vektortreffer durch.
- Plan 13-03 reicht `groups`, `since` und `until` aus `SearchRequest` und `SnippetsRequest` an `build_query` durch; die Signatur steht, `sort` gehört ausdrücklich nicht in den Schnitt-Rumpf.
- Die Gruppennamen der URL sind damit festgelegt: `pdf`, `documents`, `spreadsheets`, `presentations`, `images`, `text`. Die PHP-Seite führt keine eigene Endungstabelle.
- FILT-01 und FILT-03 sind ausdrücklich NICHT erfüllt: beide tragen noch die Pläne 13-03, 13-04, 13-07 und 13-09.

## Self-Check: PASSED

- `docs/search-filters.md` FOUND (enthält `spreadsheets`)
- `backend/src/findling/query/rewrite.py` FOUND (565 Zeilen, `min_lines: 400` erfüllt, enthält `TYPE_GROUPS`, `Query.range_query` genau einmal, `filter_query`, kein `use_inverted_index=True`)
- `backend/tests/test_query_rewrite.py` FOUND (enthält `FILETYPE`)
- Commit `3c64b8f` FOUND
- Commit `336afaa` FOUND
- Commit `1f06327` FOUND
- Commit `a6216e7` FOUND
- Automatisierte Verifikation aus Task 1, 2 und 3: alle GRUEN

---
*Phase: 13-filter-und-sortierung-auf-der-ergebnisseite*
*Completed: 2026-09-16*
