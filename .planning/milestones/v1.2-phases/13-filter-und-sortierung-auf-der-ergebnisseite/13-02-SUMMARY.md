---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 02
subsystem: backend-index
tags: [tantivy, sortierung, order-by-field, fast-field, filter, semantik, filt-01, filt-02]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 01
    provides: "RewrittenQuery.filter_query als einzeln herausgereichte Klausel"
  - phase: 06-semantische-suche
    provides: "_mtimes_of als der eine Indexabgleich der Vektortreffer, _permit als die eine Rechtestelle"
provides:
  - "SORT_MODES: die eine Tabelle der drei Wire-Namen relevance, newest, oldest"
  - "_ranked(scored=False): 0.0 statt des Feldwerts, den order_by_field im ersten Tupelglied liefert"
  - "_mtimes_of(filter_query=): dieselbe Filterklausel als Occur.Must ueber den file_id-Should-Klauseln"
  - "_sorted_round: ein rein lexikalischer Zweig ohne RRF, mit Zweitschluessel file_id von Hand"
  - "candidates(..., filter_query=None, sort='relevance')"
affects: [13-03, 13-04, 13-08, 13-09]

tech-stack:
  added: []
  patterns:
    - "Sortierung als eigener Modus nach dem Vorbild von lexical_only, nicht als Argument an der Fusion"
    - "Eine Filterklausel, zwei Haelften: die lexikalische ueber build_query, die semantische ueber _mtimes_of"
    - "Gemessene Bibliothekseigenschaft als Kommentar mit Datum, damit sie niemand korrigiert"

key-files:
  created: []
  modified:
    - backend/src/findling/index/search.py
    - backend/tests/test_search_library.py
    - backend/tests/test_semantic_search.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "Der Sortierzweig ist eine eigene private Funktion mit eigener Schleife und eigenem Seitenschnitt; der Relevanzpfad bleibt Byte fuer Byte, wie er war"
  - "Ein unbekannter Sortiername faellt still auf relevance zurueck, weil die Route schon prueft und eine zweite Ausnahme aus einem Tippfehler einen HTTP 500 machen wuerde"
  - "Der Zweitschluessel file_id wird portionsweise von Hand hergestellt; die Grenze an der Portionsgrenze steht im Kommentar statt in einem unbegrenzten Nachschlag"
  - "semantic ist im Sortierzweig wirkungslos statt verboten: die zweite, defensive Haelfte der Zusage, die der Aufrufer in 13-03 gibt"
  - "VECTOR_SCAN_MAX wird nicht angehoben; die Verkleinerung der semantischen Haelfte unter engem Filter steht als Preis im Docstring"

patterns-established:
  - "Ein Testfall, der ohne die zu belegende Zeile nicht gruen werden kann, wird vor dem Commit einmal gegen die entfernte Zeile gefahren"

requirements-completed: []  # FILT-01 und FILT-02 tragen noch 13-03, 13-04, 13-08 und 13-09

duration: 34min
completed: 2026-09-16
---

# Phase 13 Plan 02: Sortierzweig und Filter auf der semantischen Hälfte Summary

**Die Datumsordnung entsteht in der Engine als eigener, rein lexikalischer Modus mit Score 0.0 und handgemachtem Zweitschlüssel, und dieselbe Filterklausel aus 13-01 schneidet über `_mtimes_of` jetzt auch die semantische Hälfte.**

## Performance

- **Duration:** 34 min
- **Started:** 2026-09-16T18:05:00Z
- **Completed:** 2026-09-16T18:39:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments

- `SORT_MODES` steht im Kopf-Konstantenblock von `index/search.py` und bildet `relevance` auf `None`, `newest` auf `Order.Desc` und `oldest` auf `Order.Asc` ab. Der Kommentar sagt beides: `None` heißt nicht "keine Sortierung", sondern "die Relevanzordnung der Fusion", und die Tabelle ist die eine Stelle, gegen die 13-03 seine `Literal`-Werte hält.
- `_ranked` hat das Schlüsselwortargument `scored: bool = True`. Mit `False` steht `0.0` an der Stelle des Scores. Der Grund steht ohne Umschweife darüber: unter `order_by_field` liefert tantivy im ersten Tupelglied den Feldwert (gemessen 500, 400, 300 statt 0.087), und ein ungeprüft übernommener Feldwert wäre ein Zeitstempel in der Größenordnung 1.7e9 als Relevanz auf der Seite.
- `_mtimes_of` nimmt `filter_query` und legt es als `Occur.Must` über die bestehende `Should`-Gruppe der `file_id`-Terme. Der Docstring benennt die Wirkung (was hier herausfällt, fehlt in `known` und verschwindet aus `merged`) und den Preis (`VECTOR_SCAN_MAX` zieht seine Chunks VOR dem Schnitt, die semantische Hälfte schrumpft unter engem Filter sichtbar, und der Wert wird in dieser Phase nicht angehoben).
- `_sorted_round` ist der Sortierzweig: eine Schleife nach dem Vorbild der Fortsetzungsschleife, ein einziger `searcher.search(..., order_by_field=FIELD_MTIME, order=order, offset=raw_cursor)`, `_ranked(..., scored=False)`, Stabilisierung nach `(mtime, file_id)` vor `_permit`, `SEARCH_SCAN_MAX` als Decke, Abbruch bei unvollständiger Portion.
- `candidates` schaltet vor Abschnitt 1 um. Ein unbekannter Wert in `sort` läuft über `SORT_MODES.get(sort)` still in den Relevanzzweig. Der Seitenschnitt und die Deckenzeile des Sortierzweigs sind dieselben wie im Relevanzzweig; `offset` zählt auch hier erlaubte Kandidaten und nie Engine-Treffer.
- Der Docstring von `candidates` trägt jetzt Pitfall G: auf einer Instanz mit großem Fremdbestand liefert die Datumssortierung für einen Nutzer mit wenigen eigenen Dateien systematisch leere Seiten. Das ist der Normalfall dieses Modus, und die Antwort darauf bleibt die begrenzte Wiederholung auf der PHP-Seite.
- Fünfzehn neue Testfälle über beide Dateien, darunter der Gleichstandsfall, die Seitenstabilität, die drei Randpfade und die Gegenprobe des typfremden Vektortreffers.

## Task Commits

Jeder Task wurde einzeln committet:

1. **Task 1: SORT_MODES, _ranked(scored=) und die Filterklausel in _mtimes_of** - `4a91263` (feat)
2. **Task 2: Der Sortierzweig als eigener Modus in candidates** - `9e7cde9` (feat)
3. **Abweichung: Baumhash des Pakets nachziehen** - `57f0783` (test)
4. **Task 3: Testfälle für Sortierung, Filter und die Paraphrase unter Filter** - `5e66188` (test)

## Files Created/Modified

- `backend/src/findling/index/search.py` (863 Zeilen) - `SORT_MODES`, `_ranked(scored=)`, `_mtimes_of(filter_query=)`, `_sorted_round`, die Weiche und die zwei neuen Parameter an `candidates`
- `backend/tests/test_search_library.py` - Fixture `tied_index` plus zwölf Fälle in zwei neuen Abschnitten
- `backend/tests/test_semantic_search.py` - drei Fälle im neuen Abschnitt "Criterion 1 under a filter"
- `backend/tests/test_measurement_scripts.py` - `PACKAGE_TREE_HASH_TODAY` nachgezogen, mit Begründungsabsatz

## Decisions Made

- **Der Sortierzweig bekommt seinen eigenen Seitenschnitt statt eines gemeinsamen Helfers.** Der Plan schreibt die wörtliche Übernahme vor, und sie hat einen Vorteil, der den doppelten Vierzeiler aufwiegt: der Relevanzpfad bleibt unverändert, also kann kein Testfall dieser Datei aus einem Umbau heraus rot werden, den niemand angefordert hat.
- **Ein unbekannter Sortiername wirft nicht.** `SORT_MODES.get(sort)` liefert `None`, und `None` ist der Relevanzzweig. Die Route hält ihre drei Werte bereits am Wire-Modell; eine zweite Ausnahme hier würde aus einem Tippfehler in einer Adresse einen HTTP 500 machen, und die Hausregel von `PageController` ist der stille Rückfall.
- **Der Zweitschlüssel wird portionsweise hergestellt.** Gemessen am 16.09.2026 und in diesem Plan noch einmal nachgestellt: bei Einfügereihenfolge 7, 3, 9, 1 und gleichem Zeitstempel antwortet tantivy genau 7, 3, 9, 1. Die Alternative (Überholen bis zur Gleichstandsgrenze) kostet einen unbegrenzten Nachschlag und kauft nur die Reihenfolge innerhalb einer Sekunde an genau einer Seitengrenze.
- **`semantic` ist im Sortierzweig wirkungslos und nicht verboten.** Ein Fehler wäre eine zweite Stelle, die dieselbe Zusage gibt; die Wirkungslosigkeit ist die defensive Hälfte der Zusage, die der Aufrufer in 13-03 gibt. Ein eigener Testfall hält fest, dass derselbe Aufruf mit und ohne Bündel unter `sort='newest'` dieselbe Folge liefert.
- **`VECTOR_SCAN_MAX` bleibt, wo es ist.** Es ist ein Sicherheits- und Laufzeitdeckel mit eigener Begründung; die Verkleinerung der semantischen Hälfte unter einem engen Filter ist eine Eigenschaft und kein Defekt und steht als solche im Docstring.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blockierend] Der Baumhash des Python-Pakets war nach Task 2 rot**

- **Found during:** Gesamtlauf der Backend-Tests nach Task 2
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` hält einen sha256 über alle 54 Dateien unter `backend/src/findling`. Jede Änderung am Paket macht ihn rot; das war in 13-01 schon so und war dort angekündigt.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf `a67a22b8...` nachgezogen. `PACKAGE_FILES` bleibt bei 54, weil genau eine Datei ihre Bytes geändert hat und keine hinzukam. Über der Konstante steht der vorgeschriebene Begründungsabsatz mit Datum, Plan und geänderter Datei.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` = 228 passed
- **Committed in:** `57f0783`

---

**Total deviations:** 1 auto-fixed (ein blockierendes Gate, in den Eisernen Regeln des Auftrags ausdrücklich erwartet)
**Impact on plan:** Kein Scope Creep. Die Abweichung betrifft eine Testdatei; die Zusagen des Plans sind unverändert belegt.

## Issues Encountered

Keine. Zwei Punkte wurden vor dem Commit ausdrücklich gegengeprüft statt angenommen:

- Die Gleichstands-Reihenfolge der Bibliothek wurde mit einer eigenen Probe gegen die installierte tantivy 0.26.0 nachgestellt: Einfügereihenfolge 7, 3, 9, 1 kommt als 7, 3, 9, 1 zurück. Der Testfall, der `[9, 7, 3, 1]` erwartet, ist damit ohne die Handarbeit wirklich rot.
- Die Gegenprobe des typfremden Vektortreffers wurde einmal mit `filter_query=None` gefahren und war rot. Ohne die Klausel in `_mtimes_of` kann dieser Fall also nicht grün werden, was der Plan ausdrücklich verlangt.

## Known Stubs

Keine. `SORT_MODES`, `filter_query` und `sort` haben in diesem Plan noch keinen Produktivaufrufer: `api/search.py` reicht sie erst in 13-03 durch. Das ist kein Stub, sondern die Bauordnung Backend vor Wire vor PHP; alle drei sind Schlüsselwortparameter mit Vorgabewert, also bleiben die drei bestehenden Aufrufer von `candidates` unverändert lauffähig.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` (ganzes Backend) | All checks passed |
| `uv run ruff format --check .` (121 Dateien) | already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | keine Meldung |
| `uv run python -m pytest -q` (ganze Suite) | 2089 passed, 15 skipped |
| `uv run ruff check --config pyproject.toml ../scripts` | All checks passed |
| `uv run ruff format --config pyproject.toml --check ../scripts` | 10 Dateien formatiert |
| Rechtestelle: `prefilter_visible` außerhalb von Kommentaren | genau zweimal |
| `order_by_field=FIELD_MTIME` in der Datei | genau einmal |

Kein PHP angefasst, also kein `php -l` nötig. Kein Paket installiert.

## User Setup Required

Keine. Kein Paket, kein Schema, kein Reindex.

## Next Phase Readiness

- Plan 13-03 kann `SORT_MODES` als Quelle für die `Literal`-Werte von `SearchRequest.sort` nehmen und das angekündigte Gate dagegen bauen. `sort` gehört ausdrücklich NICHT in `SnippetsRequest`.
- `one_round` in `api/search.py` muss beim Durchreichen zwei Dinge zugleich tun: `filter_query` aus `RewrittenQuery` an `candidates` legen UND die Vektorhälfte unter einer Sortierung abschalten. Die Wirkungslosigkeit von `semantic` im Sortierzweig ist die zweite Hälfte dieser Zusage, nicht ihr Ersatz.
- Die semantische Hälfte ist ab jetzt typ- und zeitgeschnitten. Die Diagnoseroute (`ranked_sides`) sieht diesen Schnitt NICHT, weil sie `_mtimes_of` nicht anfasst; wer dort unter Filter misst, misst die ungeschnittene Seite.
- FILT-01 und FILT-02 sind ausdrücklich NICHT erfüllt: beide tragen noch die Pläne 13-03, 13-04, 13-08 und 13-09.

## Self-Check: PASSED

- `backend/src/findling/index/search.py` FOUND (863 Zeilen, `min_lines: 700` erfüllt, enthält `SORT_MODES`, `_sorted_round`, `order_by_field=FIELD_MTIME` genau einmal)
- `backend/tests/test_search_library.py` FOUND (enthält `sort="newest"` und `sort="oldest"`)
- `backend/tests/test_semantic_search.py` FOUND (enthält `groups`)
- Commit `4a91263` FOUND
- Commit `9e7cde9` FOUND
- Commit `57f0783` FOUND
- Commit `5e66188` FOUND
- Automatisierte Verifikation aus Task 1, 2 und 3: alle GRUEN

---
*Phase: 13-filter-und-sortierung-auf-der-ergebnisseite*
*Completed: 2026-09-16*
