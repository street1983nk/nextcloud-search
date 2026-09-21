---
phase: 13-filter-und-sortierung-auf-der-ergebnisseite
plan: 03
subsystem: backend-api
tags: [wire, pydantic, extra-forbid, lockstep-gate, literal, filt-01, filt-02, filt-03]

requires:
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 01
    provides: "build_query(groups=, since=, until=) und RewrittenQuery.filter_query"
  - phase: 13-filter-und-sortierung-auf-der-ergebnisseite
    plan: 02
    provides: "SORT_MODES und candidates(filter_query=, sort=)"
provides:
  - "SearchRequest.types, .sort, .since, .until als geschlossene, begrenzte Wire-Felder"
  - "SnippetsRequest.types, .since, .until, ausdrücklich ohne sort"
  - "SEARCH_TYPE_GROUPS_MAX und SEARCH_MTIME_MAX als benannte Grenzen mit Sicherheitsbegründung"
  - "one_round(groups=, since=, until=, sort=): der Moduswechsel an derselben lexical_only-Zeile"
  - "excerpts(groups=, since=, until=) und read_diagnosis(types=, since=, until=)"
  - "tests/test_search_fields_lockstep.py: das Gleichstands-Gate der beiden Modelle plus der Sortiernamen"
affects: [13-04, 13-05, 13-07, 13-08, 13-09, 13-12]

tech-stack:
  added: []
  patterns:
    - "Geschlossene Wertemengen als Literal statt Freitext, weil die Route access_level USER trägt"
    - "Ein Feld, das den Abfragebau berührt, steht in beiden Request-Modellen; die Ausnahme ist benannt, nicht gezählt"
    - "functools.partial vor asyncio.to_thread, weil to_thread keine Schlüsselwortargumente durchreicht, die es selbst deuten könnte"

key-files:
  created:
    - backend/tests/test_search_fields_lockstep.py
  modified:
    - backend/src/findling/config.py
    - backend/src/findling/api/search.py
    - backend/src/findling/api/snippets.py
    - backend/src/findling/api/diagnose.py
    - backend/tests/test_search_endpoint.py
    - backend/tests/test_snippets_endpoint.py
    - backend/tests/test_measurement_scripts.py

key-decisions:
  - "FIELDS_THAT_MAY_DIFFER trägt vier Einträge statt des einen aus dem Plantext, weil limit, offset und fileIds schon vor dieser Phase einseitig waren; jeder Eintrag trägt seine Begründung"
  - "Der Ausschnittsaufruf schneidet nicht: die drei Felder reisen mit, damit ein Rumpf beide Modelle passiert, und sie nehmen einem bestätigten Treffer seinen Ausschnitt nicht weg"
  - "Die Diagnoseroute bekommt die drei Filter als Query-Parameter, aber keine Trefferzahl und keinen Gesamtwert"
  - "types ist an der Diagnoseroute ein tuple, damit der Vorgabewert unveränderlich ist"
  - "Der Sortierterm hängt an derselben lexical_only-Zeile wie lexical_only selbst, nicht an einer zweiten Weiche"

patterns-established:
  - "Ein Gate, das zwei Wire-Modelle vergleicht, nennt seine einseitigen Felder mit Begründung statt mit einer Zahl"

requirements-completed: []  # FILT-01, FILT-02 und FILT-03 tragen noch die PHP-Pläne 13-04 bis 13-09

duration: 41min
completed: 2026-09-16
---

# Phase 13 Plan 03: Wire-Felder, Grenzen, Moduswechsel und Gleichstands-Gate Summary

**Die vier neuen Werte bekommen ihren Weg über den Draht: drei geschlossene Felder an `SearchRequest`, zwei davon plus `since`/`until` an `SnippetsRequest`, zwei benannte Grenzen in `config.py`, der Sortierterm an derselben `lexical_only`-Zeile, und ein fail-closed lesendes Text-Gate, das ein einseitiges Feld künftig rot statt stumm macht.**

## Performance

- **Duration:** 41 min
- **Started:** 2026-09-16T19:02:00Z
- **Completed:** 2026-09-16T19:43:00Z
- **Tasks:** 3
- **Files modified:** 8 (1 neu, 7 geändert)

## Accomplishments

- `SEARCH_TYPE_GROUPS_MAX = 6` und `SEARCH_MTIME_MAX = 4_102_444_800` stehen im Grenzenblock von `config.py`, je mit dem Begründungsabsatz nach dem Muster von `SEARCH_OFFSET_MAX`. Die Sechs ist nicht eine Politik, sondern die ganze Liste; die Obergrenze der Zeit ist der 01.01.2100, und die untere ist die Epoche selbst.
- `SearchRequest` trägt `types` (als `list[Literal[...]]` mit `max_length`), `sort` (als `Literal` über die drei Namen), `since` und `until` (beide `int | None` mit `ge=0` und `le=SEARCH_MTIME_MAX`). Kein Feld ist Freitext: die Route trägt `access_level USER`, und ein freier String wäre ein zweiter Weg in den Abfragebau neben der Suchzeile.
- `SnippetsRequest` trägt dieselben drei Abfragefelder und ausdrücklich kein `sort`. Über der Stelle der Abwesenheit steht die Begründung, und ein HTTP-Fall belegt sie: ein `sort` im Ausschnitts-Rumpf ist ein 422.
- `one_round` hängt den Sortierterm an dieselbe Zeile: `lexical_only = ... or sort != "relevance"`. Der Kommentar nennt den Grund, den 13-02 vorbereitet hat: unter Sortierung gibt es keine Fusion, in die eine Vektorliste eingehen könnte, und ein Zeitstempel als Relevanz entstünde genau dort. `candidates` bekommt jetzt `filter_query=rewritten.filter_query` und `sort=sort`.
- `api/snippets.py` und `api/diagnose.py` reichen `groups`, `since` und `until` an `build_query` durch. Die Diagnoseroute nimmt sie als Query-Parameter mit denselben Grenzen; ihre Antwort bleibt eine Marke für eine benannte Datei, ohne Trefferzahl je Typ und ohne Gesamtwert (T-13-14).
- `tests/test_search_fields_lockstep.py` (373 Zeilen) liest beide Modelldefinitionen als Text statt sie zu importieren, kappt den Klassen-Docstring vor dem Feldlesen, fällt bei einer nicht lesbaren Datei auf einen Befund zurück, und hält zusätzlich die `Literal`-Werte von `SearchRequest.sort` gegen die Schlüssel von `SORT_MODES`. Anti-Vakuitäts-Klausel plus neun Selbsttests.
- Achtzehn neue HTTP-Fälle über beide Endpunktdateien, davon zehn Negativ- oder Randpfade.

## Task Commits

Jeder Task wurde einzeln committet:

1. **Task 1: Grenzen in config.py, die Wire-Felder und der Moduswechsel** - `66a6b3d` (feat)
2. **Task 2: Das Gleichstands-Gate der beiden Modelle** - `d7eaf3e` (test)
3. **Abweichung: Baumhash des Pakets nachziehen** - `a2d3522` (test)
4. **Task 3: HTTP-Fälle für die neuen Felder, positiv wie negativ** - `89b26f7` (test)

## Files Created/Modified

- `backend/tests/test_search_fields_lockstep.py` (neu, 373 Zeilen) - das Gleichstands-Gate mit `FIELDS_THAT_MAY_DIFFER`, `findings`, `order_findings` und den Selbsttests
- `backend/src/findling/config.py` - zwei neue Grenzen mit Begründungsabsatz
- `backend/src/findling/api/search.py` - vier Wire-Felder, die erweiterte `one_round`-Signatur, der Sortierterm, `filter_query` und `sort` an `candidates`
- `backend/src/findling/api/snippets.py` - drei Wire-Felder ohne `sort`, die erweiterte `excerpts`-Signatur, der geschärfte Docstring
- `backend/src/findling/api/diagnose.py` - die drei Filter als Query-Parameter, durchgereicht bis `build_query`
- `backend/tests/test_search_endpoint.py` - elf neue Fälle in einem eigenen Abschnitt
- `backend/tests/test_snippets_endpoint.py` - fünf neue Fälle in einem eigenen Abschnitt
- `backend/tests/test_measurement_scripts.py` - `PACKAGE_TREE_HASH_TODAY` nachgezogen, mit Begründungsabsatz

## Decisions Made

- **`FIELDS_THAT_MAY_DIFFER` trägt vier Einträge und nicht einen.** Der Plan schreibt genau einen vor (`sort`), aber drei Felder waren schon vor dieser Phase einseitig: `limit` und `offset` stehen nur in `SearchRequest`, `fileIds` nur in `SnippetsRequest`. Eine Liste mit nur `sort` hätte ein Gate ergeben, das ab dem ersten Lauf drei Befunde meldet, und ein dauerhaft rotes Gate ist ein Gate, das jemand innerhalb einer Woche abschaltet. Jeder der vier Einträge trägt seine eigene Begründung, die Abbildung bleibt eine Liste und niemals eine Zahl, und ein eigener Testfall hält fest, dass `sort` darin steht und dass der Ausschnittsaufruf es wirklich nicht führt.
- **Der Ausschnittsaufruf schneidet nicht, und das steht jetzt ausdrücklich da.** `snippets_for` wählt keine Dokumente aus: es läuft über die bestätigten Kennungen und holt für jede das Dokument aus dem Index; die Abfrage dient dem Hervorheben. Die Filterklausel nennt das Endungs- und das Zeitfeld und markiert deshalb nichts im Text. Die drei Felder reisen trotzdem mit, und zwar aus dem einen Grund, für den das Gate gebaut ist: der Rumpf der Seite muss beide Modelle passieren. Zwei Testfälle halten das als Zusage fest, statt es einem späteren Leser zu überlassen.
- **Die Diagnoseroute bekommt die Filter, aber kein Zählwerk.** Sie ist die einzige Stelle, an der "ist die semantische Hälfte unter Filter noch da" überhaupt beobachtbar ist, weil ein Kandidat drei Werte und keine Marke trägt. Der Docstring benennt zugleich die Grenze dieser Beobachtung: `ranked_sides` geht nicht durch `_mtimes_of`, also sieht die Route den Schnitt der semantischen Hälfte nicht (13-02).
- **`types` ist an der Diagnoseroute ein `tuple` und keine `list`.** Ein veränderlicher Vorgabewert wäre an einer Funktionssignatur ein Befund des Linters und an dieser Stelle auch sachlich falsch; FastAPI nimmt ein Tupel als Mehrfach-Query-Parameter genauso an.
- **`functools.partial` statt Positionsargumenten an `asyncio.to_thread`.** `to_thread` reicht Schlüsselwortargumente durch, aber ein Name wie `sort` oder `until` kollidiert sichtbar mit dem, was ein Leser für einen Parameter von `to_thread` halten könnte. `partial` bindet sie an die gerufene Funktion und macht die Zuordnung an der Aufrufstelle eindeutig.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Fehler im Plantext] `FIELDS_THAT_MAY_DIFFER` kann nicht genau einen Eintrag haben**

- **Found during:** Task 2
- **Issue:** Der Plan verlangt die Ausnahmeliste "mit genau einem Eintrag: `sort`". Das ist mit dem tatsächlichen Baum unvereinbar: `SearchRequest` führt `limit` und `offset`, `SnippetsRequest` führt `fileIds`, und alle drei sind seit v1.0 legitim einseitig. Ein Gate mit nur `sort` in der Liste hätte beim ersten Lauf drei Befunde gemeldet.
- **Fix:** Die Abbildung trägt vier Einträge, jeder mit seiner Begründung. Drei davon sind "diese Frage stellt der andere Aufruf gar nicht" (Seitengröße, Seitenanfang, Gegenstand des Ausschnitts), der vierte ist der dieser Phase (`sort` verändert die Reihenfolge, nicht die Frage). Ein eigener Testfall prüft, dass `sort` in der Liste steht und dass jede Begründung nicht leer ist, damit ein Schlüssel ohne Argument nicht durchrutscht.
- **Files modified:** backend/tests/test_search_fields_lockstep.py
- **Verification:** `uv run python -m pytest tests/test_search_fields_lockstep.py -q` = 15 passed
- **Committed in:** `d7eaf3e`

**2. [Rule 1 - Falsche Annahme über den Ausschnittspfad] Zwei geplante Testfälle waren nicht erfüllbar**

- **Found during:** Task 3
- **Issue:** Der Plan lässt erwarten, dass die Filterklausel im Ausschnittsaufruf denselben Schnitt bewirkt wie im Kandidatenlauf ("damit derselbe Schnitt gilt"). Am Code gelesen tut sie das nicht und kann es nicht: `snippets_for` läuft über die bestätigten Kennungen und zieht für jede das Dokument über `_document_for`; die Abfrage geht nur in den `SnippetGenerator`, und die Klausel nennt `ext` und `mtime`, also Felder, die im Textfeld nichts markieren. Zwei Testfälle, die einen leeren Ausschnitt unter einem fremden Typ erwarteten, waren entsprechend rot.
- **Fix:** Die beiden Fälle behaupten jetzt die Wahrheit und begründen sie: ein Filter, zu dem das Dokument nicht gehört, lässt dem bestätigten Treffer seinen Ausschnitt. Das ist auch die richtige Zusage, denn ein zweiter Schnitt hier nähme einem bereits angezeigten Treffer die Unterzeile weg und gäbe nichts dafür zurück. Der Docstring von `excerpts` sagt jetzt beides ausdrücklich: was die drei Felder nicht tun, und warum sie trotzdem am Modell stehen müssen (`extra="forbid"`, 422, `null` auf der PHP-Seite).
- **Files modified:** backend/tests/test_snippets_endpoint.py, backend/src/findling/api/snippets.py
- **Verification:** `uv run python -m pytest tests/test_snippets_endpoint.py -q` = 25 passed
- **Committed in:** `89b26f7`

**3. [Rule 3 - Blockierend] Der Baumhash des Python-Pakets war nach Task 1 rot**

- **Found during:** Gesamtlauf der Backend-Tests nach Task 3
- **Issue:** `test_measurement_scripts.py::test_the_recipe_reproduces_the_tree_hash_of_the_python_package` hält einen sha256 über alle 54 Dateien unter `backend/src/findling`. Das war in 13-01 und 13-02 schon so und stand in den Eisernen Regeln dieses Auftrags als erwartete Abweichung.
- **Fix:** `PACKAGE_TREE_HASH_TODAY` auf `ae8f1684...` nachgezogen. `PACKAGE_FILES` bleibt bei 54: vier Dateien haben ihre Bytes geändert, keine kam hinzu und keine ging. Über der Konstante steht der vorgeschriebene Begründungsabsatz mit Datum, Plan und den vier Dateien.
- **Files modified:** backend/tests/test_measurement_scripts.py
- **Verification:** `uv run python -m pytest tests/test_measurement_scripts.py -q` = 228 passed
- **Committed in:** `a2d3522`

---

**Total deviations:** 3 auto-fixed (2 Fehler in Annahmen des Plans, 1 blockierendes Gate)
**Impact on plan:** Kein Scope Creep. Die Zusagen des Plans sind unverändert belegt; zwei davon sind jetzt präziser formuliert als der Plantext sie hatte.

## Issues Encountered

Keine offenen. Ein Punkt wurde ausdrücklich gegengeprüft statt angenommen: die Frage, ob die Filterklausel im Ausschnittspfad wirkt. Sie wirkt nicht, und das ist in Abweichung 2 mit dem Weg durch `snippets_for` belegt, nicht behauptet.

## Known Stubs

Keine. Die vier Wire-Felder haben ab jetzt einen Produktivweg bis in die Suchmaschine; was fehlt, ist die Seite, die sie schickt, und die trägt Plan 13-04 und die Wellen darüber. Alle neuen Parameter der Backend-Funktionen sind Schlüsselwortparameter mit Vorgabewert, also bleiben die bestehenden Aufrufer unverändert lauffähig (belegt: die vier Direktaufrufe von `one_round` in `test_semantic_search.py` und der in `probe_image_search.py` sind ungeändert grün).

## Threat Flags

Keine neue Oberfläche außerhalb des `<threat_model>` des Plans. Die Diagnoseroute erhält Parameter, aber keine neue Route, keine Zahl und keine Rechteentscheidung; `T-13-14` ist damit adressiert und nicht erweitert.

## Gates

| Gate | Ergebnis |
|---|---|
| `uv run ruff check .` (ganzes Backend) | All checks passed |
| `uv run ruff format --check .` (122 Dateien) | already formatted |
| `uv run pyright` | 0 errors, 0 warnings |
| `uv run vulture src tests --min-confidence 80` | keine Meldung |
| `uv run python -m pytest -q` (ganze Suite) | 2120 passed, 15 skipped |
| `uv run ruff check --config pyproject.toml ../scripts` | All checks passed |
| `uv run ruff format --config pyproject.toml --check ../scripts` | 10 Dateien formatiert |
| Verifikationsskript aus Task 1 (Feldmengen und beide Grenzen) | GRUEN |
| Vokabular-Gate (gesperrtes Wort in den neuen Zeichenketten) | 0 Treffer |

Kein PHP angefasst, also kein `php -l` nötig. Kein Paket installiert.

## User Setup Required

Keine. Kein Paket, kein Schema, kein Reindex.

## Next Phase Readiness

- Plan 13-04 kann die zwei Rümpfe bauen: `SearchRequest` nimmt `types`, `sort`, `since`, `until`, `SnippetsRequest` nimmt `types`, `since`, `until` und weist `sort` mit einem 422 ab. Die Gruppennamen der Adresse stehen fest: `pdf`, `documents`, `spreadsheets`, `presentations`, `images`, `text`.
- Die PHP-Seite muss den stillen Rückfall selbst tragen. Der Container lehnt einen unbekannten Gruppen- oder Sortiernamen mit 422 ab, weil ihn nur die eigene Oberfläche ruft; eine von Hand editierte Adresse darf deshalb dort drüben nicht ungeprüft weitergereicht werden, sonst zeigt die Seite den Fehlerblock statt eines entfernten Chips.
- Ein neues Feld, das die Seite schickt, gehört ab jetzt in beide Modelle oder namentlich in `FIELDS_THAT_MAY_DIFFER`. Das Gate ist die Stelle, an der ein Vergessen rot wird, und es liegt in `backend/tests/test_search_fields_lockstep.py`.
- Der Ausschnittsaufruf filtert nicht und soll es nicht: wer dort einen leeren Ausschnitt unter einem engen Filter erwartet, sucht einen Defekt, den es nicht gibt.
- FILT-01, FILT-02 und FILT-03 sind ausdrücklich NICHT erfüllt: alle drei tragen noch die PHP-Pläne 13-04 bis 13-09.

## Self-Check: PASSED

- `backend/tests/test_search_fields_lockstep.py` FOUND (373 Zeilen, `min_lines: 100` erfüllt, enthält `FIELDS_THAT_MAY_DIFFER` und `SORT_MODES`)
- `backend/src/findling/api/search.py` FOUND (enthält `Literal`, `groups=`, `filter_query=`)
- `backend/src/findling/api/snippets.py` FOUND (enthält `types`, kein `sort` am Modell)
- `backend/src/findling/config.py` FOUND (enthält `SEARCH_MTIME_MAX`)
- `backend/src/findling/api/diagnose.py` FOUND
- Commit `66a6b3d` FOUND
- Commit `d7eaf3e` FOUND
- Commit `a2d3522` FOUND
- Commit `89b26f7` FOUND
- Automatisierte Verifikation aus Task 1, 2 und 3: alle GRUEN

---
*Phase: 13-filter-und-sortierung-auf-der-ergebnisseite*
*Completed: 2026-09-16*
