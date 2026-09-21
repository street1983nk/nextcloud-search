# Phase 13: Filter und Sortierung auf der Ergebnisseite - Pattern Map

**Mapped:** 2026-09-16
**Files analyzed:** 27 (davon 2 neu, 25 Aenderungen)
**Analogs found:** 27 / 27 (kein "kein Analog"-Fall)

> Schreibweise: ASCII-Konvention der `.planning`-Dateien (ae/oe/ue/ss), keine
> Gedankenstriche. Die Code-Auszuege sind woertlich aus dem Baum und tragen
> deshalb echte Zeichen, so wie sie dort stehen.
>
> Alle Zeilenangaben sind der Stand vom 16.09.2026. Sie verschieben sich, sobald
> ein Plan die Datei bearbeitet; ein spaeterer Plan sucht die Stelle am Namen
> (Funktion, Konstante, Klasse) und nicht an der Zahl.

---

## File Classification

### Backend (Python), Bauordnung: diese Gruppe VOR jeder Zeile PHP

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Passung |
|---|---|---|---|---|
| `backend/src/findling/query/rewrite.py` (MOD) | utility / query-builder | transform | sich selbst: `_extension_query` + `build_query` (Z. 292-297, 317-383) | exakt |
| `backend/src/findling/index/search.py` (MOD) | service / read-side | request-response | sich selbst: Abschnitt 2 von `candidates` (Z. 444-470), `_mtimes_of` (Z. 323-346), `_ranked` (Z. 142-163) | exakt |
| `backend/src/findling/api/search.py` (MOD) | controller (Route) | request-response | sich selbst: `SearchRequest` (Z. 75-95), `one_round` (Z. 176-233) | exakt |
| `backend/src/findling/api/snippets.py` (MOD) | controller (Route) | request-response | `SearchRequest` in `api/search.py` (Z. 75-95) | exakt |
| `backend/src/findling/api/diagnose.py` (MOD) | controller (Route) | request-response | `one_round` in `api/search.py` (Z. 194) | Rollen-Treffer |
| `backend/src/findling/config.py` (MOD, optional) | config | -- | Konstantenblock `SEARCH_LIMIT_MAX` bis `SEARCH_QUERY_MAX_DEPTH` (Z. 165-194) | exakt |

### Backend-Tests und Gates

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Passung |
|---|---|---|---|---|
| `backend/tests/test_search_fields_lockstep.py` (NEU) | test / Text-Gate | transform | `backend/tests/test_search_limits_lockstep.py` (ganze Datei) | exakt |
| `backend/tests/test_query_rewrite.py` (MOD) | test | transform | sich selbst: `type:`-Faelle (Z. 157-175, 242-248) | exakt |
| `backend/tests/test_search_library.py` (MOD) | test | request-response | sich selbst (ganze Datei, Fixture-Muster Z. 56-101) | exakt |
| `backend/tests/test_semantic_search.py` (MOD) | test | request-response | `test_search_library.py` | Rollen-Treffer |
| `backend/tests/test_search_endpoint.py` (MOD) | test / HTTP | request-response | sich selbst: 422-Faelle (Z. 142-177) | exakt |
| `backend/tests/test_snippets_endpoint.py` (MOD) | test / HTTP | request-response | `test_search_endpoint.py` (Z. 142-148) | exakt |
| `backend/tests/test_admin_ui_contract.py` (MOD) | test / Katalog-Gate | transform | sich selbst: Z. 304-313 (G2-Ausnahmen), Z. 1052-1100 (Zahl 174) | exakt |

### PHP-Companion

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Passung |
|---|---|---|---|---|
| `php/lib/Service/SearchFilters.php` (NEU) | model / Wertobjekt | -- | `php/lib/Service/SearchCaps.php` (ganze Datei, 46 Zeilen) | exakt |
| `php/lib/Service/ApprovedHit.php` (MOD) | model / Wertobjekt | -- | sich selbst (ganze Datei) | exakt |
| `php/lib/Service/SearchService.php` (MOD) | service | request-response | sich selbst: `run()` (Z. 131), Knotenaufloesung (Z. 324-359) | exakt |
| `php/lib/Service/ExAppService.php` (MOD) | service / Proxy-Client | request-response | sich selbst: `searchCandidates` (Z. 402-455), `snippets` (Z. 471-504) | exakt |
| `php/lib/Search/Provider.php` (MOD) | provider | request-response | sich selbst: `getSupportedFilters` (Z. 131-134), `titleOnly` (Z. 253-257) | exakt |
| `php/lib/Controller/PageController.php` (MOD) | controller | request-response | sich selbst: `pageNumber` (Z. 247-256), `cursorPath` (Z. 274-301), `pageUrl` (Z. 455-466), `caps` (Z. 336-346) | exakt |
| `php/templates/search.php` (MOD) | view / Template | -- | sich selbst: Pager-Links (Z. 285-312), Leerzustand (Z. 246-279), Icon-Variablen (Z. 41-49) | exakt |
| `php/css/search.css` (MOD) | style | -- | `.findling-pager__step` (Z. 341-364) + `php/css/admin.css` `.findling-chip` (Z. 125-192) | exakt |
| `php/l10n/{de,de_DE}.{js,json}`, `php/l10n/fr.{js,json}` (MOD, 6 Dateien) | i18n | -- | dieselben Dateien, bestehende Eintraege | exakt |

### PHP-Tests

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Passung |
|---|---|---|---|---|
| `php/tests/Unit/PageControllerTest.php` (MOD) | test | request-response | sich selbst: `setUp` (Z. 51-74), `controller()` (Z. 83-97), `constantOf` (Z. 162-164) | exakt |
| `php/tests/Unit/ProviderTest.php` (MOD) | test | request-response | sich selbst: Filterliste (Z. 473-474) | exakt |
| `php/tests/Unit/SearchServiceTest.php` (MOD) | test | request-response | sich selbst | exakt |
| `php/tests/Unit/ExAppServiceTest.php` (MOD) | test | request-response | sich selbst: `limitThatReachedTheContainer` (Z. 303-320) | exakt |

### Dokumente und CI

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Passung |
|---|---|---|---|---|
| `THIRD-PARTY.md` (MOD) | doc | -- | Zeile 211, Spalte "Where it lands" ("`search.php` carries six") | exakt |
| `docs/l10n-french.md` (MOD) | doc | -- | Zaehltabelle Z. 24-38, Abschnitt "Die Tabelle" ab Z. 106 | exakt |
| `docs/testing.md` (MOD) | doc | -- | bestehende Registertabelle der Gates | exakt |
| `.github/workflows/integration.yml` (MOD, Job `search-parity`) | ci | batch | bestehende Szenarien mit `ask_page`, `scripts/ci/parity_diff.py::compare_page` (Z. 260) | exakt |

---

## Pattern Assignments

### `backend/src/findling/query/rewrite.py` (utility, transform)

**Analog:** sich selbst. Die Gruppentabelle und der neue Parameter setzen genau
dort an, wo `_extension_query` heute schon eine `Should`-Gruppe baut.

**Konstanten-Muster am Dateikopf** (Z. 43-57, 61, 80-84): `Final`-Annotation,
Kommentar ueber der Konstante, der das WARUM traegt, nie nur das WAS. Die neue
`TYPE_GROUPS` gehoert in dieselbe Reihe:

```python
UMLAUTS: Final = (("ue", "ü"), ("oe", "ö"), ("ae", "ä"), ("ss", "ß"))

# SRCH-03 file type. Nextcloud has no built in filter for it, so it travels
# inside the search line and is translated into a required term on the extension.
TYPE_PREFIX: Final = "type:"

# The five marks a search line can carry. Named constants rather than string
# literals at two call sites, for the reason every allowlist in this project is
# one: a literal spelled differently at the second site is a difference nobody
# sees.
PHRASE: Final = "phrase"
...
FILETYPE: Final = "filetype"
```

**Die Klausel-Fabrik, die kopiert wird** (Z. 292-297):

```python
def _extension_query(index: Index, extensions: tuple[str, ...]) -> Query:
    """One required term on the extension field, several of them as alternatives."""
    terms = [Query.term_query(index.schema, FIELD_EXT, extension) for extension in extensions]
    if len(terms) == 1:
        return terms[0]
    return Query.boolean_query([(Occur.Should, term) for term in terms])
```

Die neue `_mtime_range_query` folgt derselben Form: eine private Funktion, die
genau eine `Query` (oder `None`) liefert und nichts entscheidet.

**Die Anhaengestelle der Klausel** (Z. 374-375). Hier kommt die zweite
`Occur.Must`-Klausel fuer `since`/`until` dazu, und hier vereinigt sich die
Endungsmenge aus `type:`-Text mit der aus den Gruppen:

```python
    if extensions:
        parsed = Query.boolean_query([(Occur.Must, parsed), (Occur.Must, _extension_query(index, extensions))])
```

**Signatur-Muster** (Z. 317): neue Parameter ausschliesslich als Schluesselwort,
mit Vorgabewert, damit die drei Produktivaufrufer unveraendert weiterlaufen,
solange sie nichts uebergeben:

```python
def build_query(index: Index, text: str, *, title_only: bool = False) -> RewrittenQuery:
```

**Fruehe Rueckgabe ohne Ausnahme** (Z. 330-336, 351-361): jeder Abbruchpfad
liefert ein vollstaendiges `RewrittenQuery` und nie eine Exception. Ein neuer
Zweig (etwa "nur Gruppen, kein Term") wird genauso gebaut.

**Nicht anfassen, aber kennen** (Z. 130-166): `carried_operators` setzt die Marke
`FILETYPE` nur am Text `type:`. Der strukturierte Gruppenparameter darf sie NICHT
setzen, sonst schaltet `api/search.py:230` die Vektorhaelfte ab. Genau dafuer
verlangt 13-RESEARCH Befund 13 einen Negativtest.

---

### `backend/src/findling/index/search.py` (service, request-response)

**Analog:** sich selbst, Abschnitt 2 von `candidates`.

**Der Schleifenrumpf, den der Sortierzweig kopiert** (Z. 451-470). Portionsgroesse,
Abbruchbedingungen und der `_permit`-Aufruf sind woertlich das Muster; der
Sortierzweig ersetzt nur `offset=raw_cursor` durch
`order_by_field=FIELD_MTIME, order=..., offset=raw_cursor` und den Score durch `0.0`:

```python
    lexical_rank = len(lexical)
    raw_cursor = raw_hits
    exhausted = raw_hits < window
    while not exhausted and len(permitted) < needed and raw_cursor < scan_cap:
        chunk_limit = min(max(needed, _SCAN_CHUNK_MIN), scan_cap - raw_cursor)
        more = searcher.search(query, chunk_limit, offset=raw_cursor).hits
        if not more:
            break
        tail: list[Candidate] = []
        for file_id, _, mtime in _ranked(searcher, more):
            ...
            tail.append(Candidate(file_id=file_id, score=score, mtime=mtime))
        permitted.extend(_permit(store, uid, tail))
        raw_cursor += len(more)
        if len(more) < chunk_limit:
            break
```

**Der Seitenschnitt am Ende, unveraendert zu uebernehmen** (Z. 476-481). `offset`
zaehlt erlaubte Kandidaten, nie Engine-Treffer; das gilt im Sortierzweig genauso:

```python
    page = permitted[offset : offset + limit]
    return CandidatePage(
        candidates=page,
        has_more=len(permitted) > offset + limit,
        next_offset=offset + len(page),
    )
```

**Die Stelle fuer den Filter auf der semantischen Haelfte** (Z. 323-338). Die
Filterklausel wird als `(Occur.Must, <klausel>)` zu diesen `Should`-Klauseln
gelegt; was hier herausfaellt, fehlt in `known` und damit in `merged` (Z. 426-434):

```python
def _mtimes_of(searcher: Searcher, schema: Schema, file_ids: Sequence[int]) -> dict[int, int]:
    if not file_ids:
        return {}
    clauses = [(Occur.Should, Query.term_query(schema, FIELD_FILE_ID, file_id)) for file_id in file_ids]
    hits = searcher.search(Query.boolean_query(clauses), len(file_ids)).hits
```

**Der Score-Zweig** (Z. 142-163). `_ranked` liest das erste Tupelglied ungeprueft
als Score; unter `order_by_field` ist das der Feldwert. Empfohlener kleinster
Eingriff aus 13-RESEARCH Befund 2: ein Schluesselwortargument `scored: bool = True`:

```python
    ranked: list[tuple[int, float, int]] = []
    for (score, _), file_id, mtime in zip(hits, file_ids, mtimes, strict=True):
        if file_id is None:
            LOGGER.warning("skipping a hit without a file id")
            continue
        ranked.append((int(file_id), float(score), int(mtime) if mtime is not None else 0))
```

**Die eine Rechtestelle, die unberuehrt bleibt** (Z. 166-183). Ein Test zaehlt
`prefilter_visible` in dieser Datei und erwartet genau zwei Vorkommen
(`test_search_library.py:220-228`). Der Sortierzweig ruft `_permit`, niemals
`store.prefilter_visible` direkt:

```python
def _permit(store: Store, uid: str, ranked: Sequence[Candidate]) -> list[Candidate]:
    if not ranked:
        return []
    visible = store.prefilter_visible(uid, [candidate.file_id for candidate in ranked])
    return [candidate for candidate in ranked if candidate.file_id in visible]
```

**Decke und Log-Disziplin** (Z. 402-404, 472-474): `SEARCH_SCAN_MAX` bleibt auch
im Sortierzweig die Decke, und die Log-Zeile nennt nur die Tatsache, nie Begriff
oder Zahlen.

---

### `backend/src/findling/api/search.py` und `api/snippets.py` (controller, request-response)

**Analog:** `SearchRequest` (search.py Z. 75-95). Neue Felder kommen in genau
dieser Form dazu: `Field(...)` mit Grenzen, Kommentar ueber dem Feld, camelCase
nur dort, wo das Wire-Format es verlangt.

```python
class SearchRequest(BaseModel):
    """Request body of the candidate call.

    ``extra="forbid"`` is a security control, not tidiness: it is what keeps a
    caller from smuggling an identity past the signed header.
    """

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=SEARCH_QUERY_MAX_CHARS)
    limit: int = Field(default=20, ge=1, le=SEARCH_LIMIT_MAX)
    # le= is a denial-of-service control (security audit C1): ...
    offset: int = Field(default=0, ge=0, le=SEARCH_OFFSET_MAX)
    # camelCase because the wire format belongs to the PHP side. A rename here
    # would silently drop the field on the way in ...
    titleOnly: bool = False
```

**Das Gegenstueck** (snippets.py Z. 80-86), das die neuen Anfragefelder
(`types`, `since`, `until`) spiegeln muss, aber `sort` NICHT bekommt:

```python
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=SEARCH_QUERY_MAX_CHARS)
    fileIds: list[int] = Field(max_length=SEARCH_LIMIT_MAX)
    # camelCase because the wire format belongs to the PHP side; see the same
    # field in findling.api.search for the whole reason.
    titleOnly: bool = False
```

**Der Moduswechsel** (search.py Z. 229-233). Der Sortiermodus haengt sich an
dieselbe Zeile wie `lexical_only`, nicht an eine zweite Weiche:

```python
        semantic = None
        lexical_only = bool(rewritten.operators) or rewritten.one_term or title_only
        if not lexical_only and side.vectors is not None and settings().embed_enabled:
            semantic = SemanticSide(vectors=side.vectors, model=resources.query_model(), text=text)
        page = candidate_round(side.index, side.store, uid, rewritten.query, limit, offset, semantic=semantic)
```

**Fehlerpfad** (Z. 234-239, identisch in snippets.py Z. 158-163): jede Ausnahme
endet in einer leeren Runde mit `degraded`, und die Log-Zeile traegt nur den
Typnamen:

```python
    except Exception as error:
        LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
        return _Round([], False, offset, True)
```

**Der Aufruf, der die Signatur mittraegt** (search.py Z. 194, snippets.py Z. 135,
diagnose.py Z. 172): `build_query(side.index, text, title_only=title_only)`.

---

### `backend/src/findling/config.py` (config)

**Analog:** der Block Z. 165-182. Jede neue Grenze bekommt genau diese Form:
Konstante, darueber der Absatz mit der Begruendung inklusive Sicherheitsargument.

```python
# Upper bound of the limit a caller may request, mirrored by the API model.
SEARCH_LIMIT_MAX = 100

# Upper bound of the paging offset a caller may request (security audit C1). The
# endpoints carry access_level USER, so any signed-in account reaches them with a
# free JSON body; the offset sizes the page the candidate scan has to fill, and
# an unbounded one would turn a single request into an unbounded amount of work.
SEARCH_OFFSET_MAX = SEARCH_LIMIT_MAX * SEARCH_OVERFETCH * SEARCH_ROUNDS
```

---

### `backend/tests/test_search_fields_lockstep.py` (NEU, test / Text-Gate)

**Analog:** `backend/tests/test_search_limits_lockstep.py`, ganze Datei. Der neue
Gate liest die beiden Modelldefinitionen als Text, bildet die Feldmengen und
prueft die Differenz gegen eine benannte Ausnahmeliste, in der `sort` mit
Begruendung steht.

**Modul-Docstring mit dem Pflichtabsatz "Was dieser Gate nicht beweist"** (Z. 1-32):

```python
"""The two search ceilings of the container, held against their PHP mirrors.
...
**What this gate does not prove.** It says nothing about whether either number
is the right one. ... this gate only insists that the decision is made in
one place and arrives in both.
"""
```

**Fail-closed-Leser und Befund-Funktion** (Z. 59-103):

```python
def read(path: Path) -> str:
    """The text of one file, or an empty string when it is not there.

    The empty string produces a finding for every value that should have come
    out of it, which is the fail closed direction ...
    """
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def findings(php_limit: int | None, php_offset: int | None) -> list[str]:
    unreadable = [
        f"{side} could not be read at all"
        for side, value in ((PHP_LIMIT, php_limit), (PHP_OFFSET, php_offset))
        if value is None
    ]
    if unreadable:
        return unreadable
    ...
```

**Anti-Vakuitaets-Klausel plus Selbsttests** (Z. 117-133, 154-195). Beide Bloecke
sind Pflicht: ein Gate, dessen Rumpf geloescht wurde, muss rot werden koennen.

```python
def test_both_php_sources_are_where_this_gate_looks_for_them() -> None:
    missing = [str(path) for path in (EXAPP_SERVICE, SEARCH_SERVICE) if not path.is_file()]
    assert missing == []


def test_a_pair_that_agrees_produces_no_finding() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every tree as broken would pass all the failure tests as well.
    assert findings(SEARCH_LIMIT_MAX, SEARCH_OFFSET_MAX) == []
```

**Die Ausnahmeliste** wird nach dem Muster von
`FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` gebaut (siehe "Shared Patterns"):
Abbildung Name auf Begruendung, keine Schwelle.

---

### `backend/tests/test_search_library.py` und `test_query_rewrite.py` (test)

**Analog:** sich selbst. Das Index-Fixture, das ein Sortier- und Filtertest
braucht, steht fertig da (Z. 56-85) und traegt bereits `ext` (pdf/docx im
Wechsel) und aufsteigende `mtime`:

```python
@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    directory = tmp_path_factory.mktemp("candidate-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id in range(1, DOCUMENTS + 1):
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        ...
        document.add_text(FIELD_EXT, "pdf" if file_id % 2 else "docx")
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
```

**Assertion-Muster fuer die neuen Faelle** (Z. 196-217): erst die erwartete
Reihenfolge aus dem Index ableiten, dann gegen `candidates()` pruefen; der
Score-Test ist die Vorlage fuer "Score ist unter Sortierung 0.0":

```python
def test_every_candidate_carries_its_modification_time(index: Index, store: Store) -> None:
    page = candidates(index, store, ALICE, _query(index), limit=DOCUMENTS)

    for candidate in page.candidates:
        assert candidate.mtime == 1_700_000_000 + candidate.file_id
        assert candidate.score > 0.0
```

**Filter-Testmuster** (`test_query_rewrite.py` Z. 157-165): Behauptung ueber das
Ergebnis UND ueber den Text, damit der Filter nicht heimlich im Volltext landet:

```python
def test_the_file_type_prefix_leaves_the_text_and_binds_the_extension(index: Index) -> None:
    rewritten = build_query(index, "type:pdf frist")

    assert rewritten.extensions == ("pdf",)
    assert "type:" not in rewritten.text
    assert rewritten.text == "frist"
    # Document 3 carries the word and is a txt file, so the filter is what
    # removes it rather than the ranking.
    assert _found(index, rewritten) == [1]
```

**HTTP-Negativfaelle** (`test_search_endpoint.py` Z. 142-148, 151-156):

```python
def test_an_unknown_field_that_is_not_an_identity_stays_a_422(client: TestClient, sign: Sign) -> None:
    # A misspelled field is a typo, not an attack. ...
    response = client.post("/search", json={"query": "contract", "limitt": 5}, headers=sign("alice"))

    assert response.status_code == 422
    assert "limitt" in str(response.json()["detail"])
```

---

### `php/lib/Service/SearchFilters.php` (NEU, model / Wertobjekt)

**Analog:** `php/lib/Service/SearchCaps.php`, ganze Datei. Woertlich dieselbe
Bauform: `final class`, Konstruktor-Promotion mit `public readonly`, ein
`@param`-Block je Feld, und ein Klassen-Docstring, der begruendet, warum es ein
Objekt ist und keine vier weiteren Positionsparameter.

```php
<?php

declare(strict_types=1);

namespace OCA\Findling\Service;

/**
 * The four families of ceilings one search run is bounded by, as one named
 * value rather than as seven optional arguments.
 *
 * An object and not a parameter list because there are two callers with two
 * different sets of numbers: ... With optional arguments the dialog would call
 * run($user, $term, $titleOnly) and the page would call run($user, $term,
 * $titleOnly, 25, $cursor, 3.0, 1.5), and no reader could tell from either call
 * site which number applies where.
 */
final class SearchCaps {
	/**
	 * @param int $pageSize how many approved hits one run may return
	 * ...
	 */
	public function __construct(
		public readonly int $pageSize,
		public readonly int $maxRounds,
		...
	) {
	}
}
```

Abweichung, die der Plan entscheiden muss: `SearchCaps` hat bewusst **keine**
Fabrik ("a default is a number nobody has to think about"). `SearchFilters`
braucht laut 13-RESEARCH Befund 6 eine statische `none()` fuer den Dialogfall;
das ist eine begruendete Abweichung und gehoert in den Klassen-Docstring, sonst
liest der naechste Leser sie als Nachlaessigkeit.

Die geschlossenen Wertelisten (`types`, `sort`, `range`) gehoeren als
Klassenkonstanten hierher, nach dem Muster der `MIN_LIMIT`/`MAX_LIMIT`-Konstanten
in `ExAppService` (dort Z. 412 im Gebrauch).

---

### `php/lib/Service/ApprovedHit.php` (model)

**Analog:** sich selbst. Das fuenfte Feld `mtime` kommt in genau dieser Form
dazu, samt Satz im Klassen-Docstring, woher der Wert stammt und was der
Kanarienvogel bekommt:

```php
/**
 * One hit that has passed the permission decision, and the three fields a
 * caller may render out of it.
 *
 * Title, path and mime type come out of the confirmed node and never out of the
 * answer of the container: a confused or a compromised backend can otherwise
 * put the name of a foreign file in front of the user ...
 *
 * A fileId of 0 is the canary path of phase 1 and the one named exception ...
 */
final class ApprovedHit {
	/**
	 * @param int $fileId the confirmed file id, or 0 for the canary
	 * @param string $title the name of the confirmed node, bounded
	 * ...
	 */
	public function __construct(
		public readonly int $fileId,
		public readonly string $title,
		public readonly string $path,
		public readonly string $mimeType,
	) {
	}
}
```

---

### `php/lib/Service/SearchService.php` (service, request-response)

**Analog:** sich selbst.

**Signatur** (Z. 131), die um `SearchFilters` waechst, mit `@param`-Zeile:

```php
	/**
	 * One run: ask, decide, and only then fetch the text of the survivors.
	 *
	 * @param IUser $user whose folder answers the permission question
	 * @param string $term the search term, already trimmed by the caller
	 * @param bool $titleOnly file name instead of content
	 * @param int $startCursor the container offset this run continues from
	 * @param SearchCaps $caps every ceiling of this run, written out by the
	 *                         caller
	 */
	public function run(IUser $user, string $term, bool $titleOnly, int $startCursor, SearchCaps $caps): SearchOutcome {
```

**Die Stelle fuer `mtime`** (Z. 322-359). Der Knoten ist bereits aufgeloest und
bestaetigt; `$node->getMTime()` wird genau hier gelesen, in derselben Reihe wie
Name, Pfad und Mimetype, und niemals aus der Containerantwort:

```php
				$rechecks++;
				$consumed++;
				$node = $userFolder->getFirstNodeById($candidate['fileId']);
				if (!$node instanceof File) {
					continue;
				}

				// The stricter question, asked right after the type check
				// (security audit L5). Reaching a node is not the same as being
				// allowed to read it ...
				if (!$node->isReadable()) {
					continue;
				}

				$title = PlainText::bounded($node->getName(), self::MAX_TITLE_LENGTH);
				$path = PlainText::bounded(
					ltrim((string)$userFolder->getRelativePath($node->getPath()), '/'),
					self::MAX_PATH_LENGTH,
				);
				if ($title === null || $path === null) {
					continue;
				}

				// Title, path and type come out of the confirmed node, never
				// out of the container answer. ...
				$approved[] = new ApprovedHit(
					$candidate['fileId'],
					$title,
					$path,
					PlainText::bounded($node->getMimetype(), self::MAX_MIME_LENGTH) ?? '',
				);
```

**Kanarienvogel-Zweig** (Z. 292-307): dort bleibt `mtime` bei `0`, weil es keinen
Knoten gibt.

**Beide Containeraufrufe** (Z. 229-237 fuer `/search`, der Snippet-Aufruf weiter
unten) tragen die Filter unveraendert weiter; `sort` geht nur an `/search`.

---

### `php/lib/Service/ExAppService.php` (service / Proxy-Client)

**Analog:** sich selbst, `searchCandidates` (Z. 402-455).

**Rumpfbau und Klemm-Disziplin** (Z. 407-420). Neue Felder gehen in dasselbe
Array; unbekannte Werte werden weggelassen, Zahlen geklemmt statt abgelehnt:

```php
		$term = trim($term);
		if ($term === '') {
			return null;
		}

		$limit = max(self::MIN_LIMIT, min(self::MAX_LIMIT, $limit));
		$offset = max(0, $offset);

		$decoded = $this->call('/search', $userId, [
			'query' => $term,
			'limit' => $limit,
			'offset' => $offset,
			'titleOnly' => $titleOnly,
		], $secondsLeft, $ceilingSeconds);
		if ($decoded === null) {
			return null;
		}
```

**Der Snippet-Rumpf** (Z. 488-492), der `types`/`since`/`until` bekommt und
`sort` ausdruecklich nicht:

```php
		$decoded = $this->call('/snippets', $userId, [
			'query' => $term,
			'fileIds' => array_values($wanted),
			'titleOnly' => $titleOnly,
		], $secondsLeft, $ceilingSeconds);
```

**Die Grenze, die nicht faellt** (Z. 761-800): `filterCandidates()` laesst nur
`fileId` durch. Kein Plan dieser Phase reicht `mtime` hier hindurch; das Datum
kommt aus dem Knoten (13-RESEARCH Befund 8):

```php
	private function filterCandidates(array $candidates): array {
		$kept = [];
		$dropped = 0;

		foreach ($candidates as $candidate) {
			if (!is_array($candidate) || !isset($candidate['fileId']) || !is_int($candidate['fileId'])) {
				$dropped++;
				continue;
			}

			$fileId = $candidate['fileId'];
			if ($fileId > 0) {
				$kept[] = ['fileId' => $fileId];
				continue;
			}
			...
```

---

### `php/lib/Search/Provider.php` (provider, request-response)

**Analog:** sich selbst.

**Die Deklaration** (Z. 120-134), die um `BUILTIN_SINCE` und `BUILTIN_UNTIL`
waechst. Der Docstring erklaert bereits die Wirkung eines fehlenden Eintrags und
wird um den Datumsfall ergaenzt:

```php
	/**
	 * The filters this provider understands, and the list has to be complete
	 * rather than sparse.
	 *
	 * A provider is skipped without a word when a client sends a filter it does
	 * not declare, and a skipped provider looks exactly like a broken backend:
	 * no error, no entry, no hint. ...
	 *
	 * @return list<string>
	 */
	#[\Override]
	public function getSupportedFilters(): array {
		return [IFilter::BUILTIN_TERM, IFilter::BUILTIN_TITLE_ONLY];
	}
```

**Das defensive Lesen eines Filterwerts** (Z. 248-257). Der neue `epochOf()`
kopiert diese Form woertlich: Klasse pruefen, alles andere gilt als nicht gesetzt:

```php
	/**
	 * "File name instead of content", the built in filter of the dialog. The
	 * value of a boolean filter is a bool, so anything else is a defect over
	 * there and is read as "not set".
	 */
	private function titleOnly(ISearchQuery $query): bool {
		$filter = $query->getFilter(IFilter::BUILTIN_TITLE_ONLY);

		return $filter !== null && $filter->get() === true;
	}
```

**`getCustomFilters()` bleibt leer** (Z. 148-154), mit dem bestehenden
Docstring-Grund. Kein Typ- und kein Sortierfilter im Dialog.

**Die Adresse in die Ergebnisseite** (Z. 326-334) zeigt, wie Parameter an
`linkToRoute` angehaengt werden, wenn der Dialog spaeter Filter mitgeben soll:

```php
			resourceUrl: $this->urlGenerator->linkToRoute(
				'findling.page.index',
				['query' => $term] + ($titleOnly ? ['names' => '1'] : []),
			),
```

---

### `php/lib/Controller/PageController.php` (controller, request-response)

**Analog:** sich selbst.

**Stiller Rueckfall auf einen geschlossenen Wert** (Z. 241-256). Das ist das
Muster fuer `types`, `sort`, `range`, `since`, `until`: Typ pruefen, Form
pruefen, Bereich pruefen, sonst der Standardwert, ohne Meldung:

```php
	/**
	 * The requested page, or page one for everything that is not a page number
	 * of this address. Zero, a negative number, a number above the ceiling and
	 * a word all arrive at the same place, because all four mean the same thing
	 * here: there is no such page.
	 */
	private function pageNumber(): int {
		$raw = $this->request->getParam('page', '');
		if (!is_string($raw) || !ctype_digit($raw)) {
			return 1;
		}

		$page = (int)$raw;

		return $page >= 1 && $page <= self::MAX_PAGE ? $page : 1;
	}
```

**Der Cursorpfad und sein Rueckfall** (Z. 274-301, 181-189). Die
Fingerabdruck-Bindung setzt hier an: eine Abweichung ist Seite eins, still:

```php
		$raw = $this->request->getParam('cursors', '');
		$cursors = is_string($raw) ? $this->cursorPath($raw, $page) : [0];
		if ($cursors === [0]) {
			// A path that did not check out is page one, and the page number
			// follows it rather than the other way round ...
			$page = 1;
		}
```

**Der Adressbau** (Z. 448-466). `filterUrl()` wird als zweite, eigene Methode
daneben gestellt, die `page` und `cursors` gar nicht erst schreiben kann:

```php
	/**
	 * One address of this route with all four values in it, built by the url
	 * generator rather than glued together, so that the query string is encoded
	 * correctly and a rewritten web root is honoured.
	 *
	 * @param list<int> $cursors
	 */
	private function pageUrl(string $query, bool $titleOnly, int $page, array $cursors): string {
		$arguments = [
			'query' => $query,
			'page' => (string)$page,
			'cursors' => implode('.', $cursors),
		];
		if ($titleOnly) {
			$arguments['names'] = '1';
		}

		return $this->urlGenerator->linkToRoute('findling.page.index', $arguments);
	}
```

**Das Wertobjekt-Bauen** (Z. 325-346) ist die Vorlage fuer `filters()`: eine
private Methode, die das Objekt vollstaendig ausschreibt:

```php
	private function caps(): SearchCaps {
		return new SearchCaps(
			self::PAGE_SIZE,
			self::MAX_ROUNDS,
			self::OVERFETCH,
			...
		);
	}
```

**Die Template-Parameter** (Z. 202-219). Neue Schluessel kommen in dieselbe Liste,
fertig berechnet, damit das Template nichts fragen muss:

```php
		return new TemplateResponse(
			Application::APP_ID,
			'search',
			[
				'query' => $query,
				'titleOnly' => $titleOnly,
				'page' => $page,
				...
				'formAction' => $this->urlGenerator->linkToRoute('findling.page.index'),
			],
			TemplateResponse::RENDER_AS_USER,
		);
```

**Zwei Fallen, am Code belegt:**
1. Der Klassen-Docstring (Z. 36-43) darf weiterhin **kein** Route-Attribut beim
   Namen nennen; `test_php_trust_boundary.py` zaehlt solche Erwaehnungen.
2. Neue Konstruktorabhaengigkeiten (`IDateTimeZone`, `IDateTimeFormatter`) gehen
   in die Liste Z. 145-154 und ziehen zwei Mocks in `PageControllerTest::setUp()`
   nach.

---

### `php/templates/search.php` (view)

**Analog:** sich selbst.

**Icon-Variable am Dateikopf** (Z. 41-49). Der `close`-Pfad wird genau so einmal
zugewiesen und dann mehrfach gedruckt, wie `admin.php` es macht:

```php
// The six path data of the page, taken word for word from the pinned upstream
// commit of Material Design Icons that THIRD-PARTY.md names. Curve data and
// nothing else: no package, no runtime, no code.
$chevronLeftIcon = 'M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z';
```

Der Wert steht woertlich in `php/templates/admin.php:781`:

```php
$closeIcon = 'M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z';
```

**Defensives Lesen der Parameter** (Z. 51-65). Jeder neue Parameter kommt in
dieselbe Reihe, mit demselben Typtest:

```php
$query = is_string($_['query'] ?? null) ? $_['query'] : '';
$titleOnly = ($_['titleOnly'] ?? false) === true;
$page = is_int($_['page'] ?? null) ? $_['page'] : 1;
$hits = is_array($_['hits'] ?? null) ? $_['hits'] : [];
```

**Die Leerzustands-Entscheidung, die ein Gate liest** (Z. 105). Die neue
Filter-Variante ist ein Zweig INNERHALB von `$showEmpty`, nie ein Block daneben,
und die Zeile muss weiterhin `$hasError`, `$hasHint` und `$hasQuery` lesen
(`test_admin_ui_contract.py:506-537`, `:698`):

```php
$showEmpty = $hits === [] && (!$hasQuery || (!$hasError && !$hasHint));
```

**Der Zweig darunter** (Z. 266-273) ist die Vorlage fuer die vierte Variante; die
Rangfolge (Filter schlaegt `$allRejected`) wird hier als zusaetzliche Bedingung
eingesetzt:

```php
			<?php if ($hasQuery) { ?>
				<svg class="findling-empty__icon" viewBox="0 0 24 24" width="64" height="64" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($fileSearchIcon); ?>"/></svg>
				<h2 class="findling-empty__heading"><?php p($l->t('No file contains "%s"', [$query])); ?></h2>
				<?php if ($allRejected) { ?>
					<p class="findling-empty__text"><?php p($l->t('Other files contain this word, but none that you may open.')); ?></p>
				<?php } else { ?>
					<p class="findling-empty__text"><?php p($l->t('Try another word, a part of a compound word, or check the spelling.')); ?></p>
				<?php } ?>
```

**Link mit Inline-SVG, das Chip-Muster** (Z. 288-293). Genau diese Form bekommt
jeder Chip- und Sortierlink, plus `aria-current="true"` am aktiven:

```php
				<?php if ($previousUrl !== null) { ?>
					<a class="findling-pager__step findling-pager__step--previous" href="<?php p($previousUrl); ?>">
						<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false"><path fill="currentColor" d="<?php p($chevronLeftIcon); ?>"/></svg>
						<span><?php p($l->t('Previous page')); ?></span>
					</a>
				<?php } ?>
```

**Zugaenglicher Name mit Platzhaltern** (Z. 222-223). Vorlage fuer die datierte
Fassung (`%1$s in %2$s, modified on %3$s`) und fuer `Remove filter %s`:

```php
					<a class="findling-hit__link" href="<?php p($url); ?>" target="_self"
						aria-label="<?php p($l->t('%1$s in %2$s', [$title, $path])); ?>">
```

**Versteckte Formularfelder**: das Formular traegt heute nur `query` und `names`
(Z. 142-159) und ausdruecklich kein `page`/`cursors`. Die neuen versteckten
Felder folgen dem `names`-Muster (nur rendern, wenn gesetzt).

---

### `php/css/search.css` (style)

**Analog zwei Quellen.** Die Chip-Optik kommt aus `php/css/admin.css:125-141`,
das Link-Verhalten aus `search.css:341-364`.

**Chip-Grundform** (`admin.css` Z. 125-141):

```css
.findling-chips {
	display: flex;
	flex-wrap: wrap;
	gap: calc(var(--default-grid-baseline) * 2);
	margin-block: calc(var(--default-grid-baseline) * 4);
}

.findling-chip {
	display: inline-flex;
	align-items: center;
	gap: var(--default-grid-baseline);
	padding: var(--default-grid-baseline) calc(var(--default-grid-baseline) * 2);
	border-radius: var(--border-radius-small);
	font-size: 13px;
	background-color: var(--color-background-hover);
	color: var(--color-main-text);
}
```

**Link mit Klickflaeche und Hover/Fokus-Paar** (`search.css` Z. 335-358). Der
Kommentar ueber der Regel traegt die Begruendung der Farbwahl, und genau dieser
Kommentarstil wird fuer den aktiven Chip erwartet:

```css
/* Ordinary links with the look of a tertiary button, so that they work without
   a line of script and a middle click opens a tab. They rest on the strip
   without a surface of their own and take the page ground when they are hovered
   or focused ... */
.findling-pager__step {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	gap: var(--default-grid-baseline);
	min-height: var(--default-clickable-area);
	padding-inline: calc(var(--default-grid-baseline) * 4);
	border-radius: var(--border-radius-container);
	color: var(--color-main-text);
	font-size: var(--default-font-size);
	font-weight: 400;
	text-decoration: none;
}

.findling-pager__step:hover,
.findling-pager__step:focus {
	background-color: var(--color-main-background);
}
```

**Die beiden Umbruchstellen** (Z. 412, 461). Neue Regeln fuer Chips gehoeren in
genau diese bestehenden Bloecke, nicht in neue Media Queries:

```css
@media (max-width: 639px) {
...
/* A finger is not a mouse pointer. Thirty four pixels is enough for a cursor
   and not for a thumb, so the two things a thumb aims at grow. Forty four is a
   multiple of four and therefore still on the grid. */
@media (pointer: coarse) {
	.findling-hit__link {
		min-height: 44px;
	}
```

**Verboten und als Gate gelesen** (Kopfkommentar Z. 1-27): kein Hexwert, keine
Farbfunktion, kein `outline: none`, Abstaende als
`calc(var(--default-grid-baseline) * n)`.

---

### `php/l10n/{de,de_DE,fr}.{js,json}` (i18n)

**Analog:** die bestehenden Eintraege derselben Dateien.

`de.json` (JSON, `translations`-Objekt):

```json
{
    "translations": {
        "Findling": "Findling",
        "Search coverage": "Deckungsgrad der Suche",
        "%1$s of %2$s indexable files are searchable": "%1$s von %2$s indexierbaren Dateien sind durchsuchbar",
```

`fr.js` (Aufruf von `OC.L10N.register`, die Datei ist kein Objekt):

```javascript
OC.L10N.register(
    "findling",
    {
    "Findling": "Findling",
    "Search coverage": "Couverture de la recherche",
```

Regeln, die aus den Gates folgen: `de_DE.*` ist **textgleich** mit `de.*` (nicht
nur schluesselgleich), alle sechs Dateien tragen dieselbe Schluesselmenge, und
die Werte tragen echte Umlaute und Akzente.

---

### `backend/tests/test_admin_ui_contract.py` (test / Katalog-Gate)

**Analog:** sich selbst. Drei Stellen sind anzufassen.

**Die harte Zahl mit ihrem Begruendungsabsatz** (Z. 1066-1100). Der Absatz ist
Pflicht, er schreibt seine eigene Fortschreibung vor:

```python
    The hard number below stands at 174 and stood at 173 until 10.09.2026. It
    rose by exactly one key, and the key is the sentence the result page says
    for a run that was handed candidates and kept none of them: finding
    DI-07-03 of phase 7, decided by the owner as V-1a on 10.09.2026 in
    .planning/phases/11-haertung-und-store-einreichung-v1-1/11-VORENTSCHEIDE.md.
    Without this paragraph the next reader takes a raised number for sloppiness
    and lowers it again. ...
    """
    ...
    assert len(set(map(frozenset, keys_of.values()))) == 1, f"the four catalogues disagree: {sorted(keys_of)}"
    assert len(keys_of["de.json"]) == 174
```

**Die G2-Ausnahmeliste** (Z. 304-313). Drei neue Eintraege (`PDF`, `Documents`,
`Images`), jeder mit seiner Begruendung als Wert:

```python
# The named exceptions of gate G2, taken from the section "Ausnahmen fuer das
# Vollstaendigkeitsgate G2" of docs/l10n-french.md. A list and deliberately not
# a threshold: a number that says "this many values may equal their key" covers
# a forgotten wording exactly as well as an intended one, while a list names two
# and nothing else. The reason travels with the key, so a third entry has to be
# argued rather than counted.
FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY = {
    "Findling": "the name of the app, the same word in all three languages",
    "Page %s": "Page is the same word in French, and a difference would be a loss",
}
```

**Der Selbsttest der Ausnahmen** (Z. 1153-1159) haelt fest, dass jede Ausnahme
noch einen Schluessel im Baum hat:

```python
    french = catalogue_of(L10N_FR_JSON)
    assert [key for key in FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY if key not in french] == []
```

**Der Leerzustands-Gate** (Z. 506-537, 698) liest die `$showEmpty`-Zeile als Text
und verlangt `$hasError`, `$hasHint`, `$hasQuery` darin sowie die Form
`} elseif ($showEmpty) {`.

---

### PHP-Tests

**`php/tests/Unit/PageControllerTest.php`** (Analog: sich selbst).

Aufbau und Adress-Staging (Z. 51-97). Die zwei neuen Mocks (`IDateTimeZone`,
`IDateTimeFormatter`) kommen in `setUp()` und in den Konstruktoraufruf:

```php
	protected function setUp(): void {
		parent::setUp();

		$this->searchService = $this->createMock(SearchService::class);
		...
		// A predictable address rather than a real one: the assertions below are
		// about which values the page puts into a link, not about how Nextcloud
		// spells a web root.
		$this->urlGenerator->method('linkToRoute')->willReturnCallback(
			static fn (string $route, array $arguments = []): string => $arguments === []
				? "/{$route}"
				: "/{$route}?" . http_build_query($arguments),
		);
	}

	private function controller(array $params = []): PageController {
		$request = $this->createMock(IRequest::class);
		$request->method('getParam')->willReturnCallback(
			static fn (string $key, mixed $default = null): mixed => $params[$key] ?? $default,
		);

		return new PageController(
			$request,
			$this->searchService,
			...
		);
	}
```

Konstanten werden gelesen, nie kopiert (Z. 158-164):

```php
	/**
	 * A constant of the class under test, read rather than copied, after the
	 * pattern of ProviderTest and ExAppServiceTest.
	 */
	private function constantOf(string $name): mixed {
		return (new \ReflectionClass(PageController::class))->getConstant($name);
	}
```

Die neuen Faelle heissen wie die bestehenden, ganze Saetze in Methodennamen:
`testACursorPathThatDoesNotCheckOutIsPageOne` (Z. 243),
`testTheFilterIsSetOnlyByTheOneWordTheAddressKnows` (Z. 205).

**`php/tests/Unit/ExAppServiceTest.php`** (Analog: Z. 303-320). So wird geprueft,
welcher Wert wirklich im Rumpf ankam:

```php
	private function limitThatReachedTheContainer(int $requested): int {
		$service = $this->service();
		$seen = null;

		$service->method('proxyRequest')->willReturnCallback(
			function (string $path, string $userId, string $method, array $params, float $timeout) use (&$seen): IResponse {
				$seen = $params['limit'] ?? null;

				return $this->answer('{"candidates":[],"hasMore":false,"nextOffset":0}');
			},
		);

		$service->searchCandidates('alice', 'quarterly report', $requested, 0, false);

		self::assertIsInt($seen, 'the container was never asked, so no limit reached it');

		return $seen;
	}
```

**`php/tests/Unit/ProviderTest.php`** (Analog: Z. 473-474):

```php
			[IFilter::BUILTIN_TERM, IFilter::BUILTIN_TITLE_ONLY],
			$this->provider()->getSupportedFilters(),
```

---

### `THIRD-PARTY.md`, `docs/l10n-french.md`, `docs/testing.md` (doc)

**`THIRD-PARTY.md` Zeile 211**, die Textstelle, die auf sieben zieht (keine neue
Zeile, kein neuer Eintrag in der Pruefschleife):

> `php/templates/search.php` carries six, three of them new here: `chevron-left`
> and `chevron-right` on the two pagination buttons, `file-search-outline` in
> the empty state without a hit, and `magnify`, `alert-circle-outline` and
> `information-outline` a second time ...

**`docs/l10n-french.md` Z. 24-38**: die Zaehltabelle zieht von 174 auf 197 nach,
mit demselben Aufbau (Groesse, Wert, Recherchestand) und einem Absatz, der die
Erhoehung begruendet; die grosse Tabelle ab Z. 106 bekommt die neuen Zeilen im
Format `| \`Schluessel\` | DE | FR |`.

**`docs/testing.md`**: Hausregel, jedes Gate bekommt eine Zeile mit "was es NICHT
beweist" (siehe Docstring-Muster von `test_search_limits_lockstep.py`).

---

## Shared Patterns

### Geschlossene Werteliste mit stillem Rueckfall (PHP)
**Quelle:** `php/lib/Controller/PageController.php:247-256`
**Gilt fuer:** jeden neuen URL-Wert (`types`, `sort`, `range`, `since`, `until`, `fp`)

```php
	private function pageNumber(): int {
		$raw = $this->request->getParam('page', '');
		if (!is_string($raw) || !ctype_digit($raw)) {
			return 1;
		}

		$page = (int)$raw;

		return $page >= 1 && $page <= self::MAX_PAGE ? $page : 1;
	}
```

Keine Meldung, keine Aussage ueber die Adresszeile. Die Begruendung steht im
Docstring von `index()` (Z. 165-172) und gilt fuer die neuen Werte mit.

### Ausnahmeliste statt Schwelle (Gates)
**Quelle:** `backend/tests/test_admin_ui_contract.py:304-313`
**Gilt fuer:** `FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY` und die `sort`-Ausnahme
im neuen `test_search_fields_lockstep.py`

```python
FRENCH_VALUES_THAT_MAY_EQUAL_THEIR_KEY = {
    "Findling": "the name of the app, the same word in all three languages",
    "Page %s": "Page is the same word in French, and a difference would be a loss",
}
```

Abbildung Name auf Begruendung, nie eine Zahl: "the reason travels with the key,
so a third entry has to be argued rather than counted".

### Fail-closed lesen, Anti-Vakuitaet, Selbsttest (Text-Gates)
**Quelle:** `backend/tests/test_search_limits_lockstep.py:71-78, 117-133, 154-161`
**Gilt fuer:** jedes neue Gate dieser Phase

```python
def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def test_both_php_sources_are_where_this_gate_looks_for_them() -> None:
    missing = [str(path) for path in (EXAPP_SERVICE, SEARCH_SERVICE) if not path.is_file()]
    assert missing == []


def test_a_pair_that_agrees_produces_no_finding() -> None:
    assert findings(SEARCH_LIMIT_MAX, SEARCH_OFFSET_MAX) == []
```

### Log ohne Inhalt
**Quelle:** `backend/src/findling/api/search.py:234-239`, `index/search.py:472-474`,
`php/lib/Service/ExAppService.php:795-797`
**Gilt fuer:** jeden neuen Zweig in beiden Haelften

```python
    except Exception as error:
        # The type name and nothing else: a traceback carries whatever a library
        # put into its message, and the search text is the usual content.
        LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
```

Kein Suchbegriff, kein Pfad, keine Trefferzahl. Auch nicht im Sortier- oder
Filterzweig.

### Ausgabe nur ueber `p()` und `$l->t()`
**Quelle:** `php/templates/search.php:19-22` (Kopfkommentar), Z. 136, 223, 295
**Gilt fuer:** jede neue Zeile im Template

```php
					<span class="findling-pager__mark"><?php p($l->t('Page %s', [(string)$page])); ?></span>
```

Das `mark`-Element (Z. 229-234) bleibt die einzige Stelle, an der Markup und
Daten zusammentreffen, und dort ist das Element ein Literal des Templates.

### Kein zweites Vokabular, keine zweite Rechtestelle
**Quelle:** `backend/tests/test_search_library.py:220-228`,
`backend/src/findling/index/search.py:166-183`
**Gilt fuer:** Sortierzweig, Filterklausel, PHP-Filterleiste

```python
def test_the_permission_prefilter_is_called_at_exactly_two_places() -> None:
    source = SEARCH_SOURCE.read_text(encoding="utf-8")

    assert source.count("prefilter_visible") == 2
```

Und auf der PHP-Seite: `getFirstNodeById` plus `isReadable` bleiben die einzige
Grenze (`SearchService.php:324-339`, gezaehlt von
`backend/tests/test_php_acl_boundary.py`).

### Wertobjekt statt weiterer Positionsparameter
**Quelle:** `php/lib/Service/SearchCaps.php` (ganze Datei)
**Gilt fuer:** `SearchFilters` und jede Signaturerweiterung von `run()`,
`searchCandidates()`, `snippets()`

---

## No Analog Found

Keine. Jede neue oder geaenderte Datei dieser Phase hat ein Vorbild im eigenen
Baum. Drei Stellen haben zwar ein Vorbild, aber keinen identischen Vorfall; sie
sind unten benannt, damit der Plan sie nicht fuer Routine haelt.

| Stelle | Naechstes Vorbild | Was daran neu ist |
|---|---|---|
| Sortierzweig in `candidates()` | Fortsetzungsschleife Z. 451-470 | `order_by_field`/`order`/`offset` wurde in diesem Baum noch nie aufgerufen; die Portions-Nachsortierung nach `(-mtime, -file_id)` hat kein Vorbild und braucht den Kommentar zur Portionsgrenze |
| Fingerabdruck `fp` | `cursorPath()` Z. 274-301 | Der Baum kennt heute nur die Formpruefung, keine Bindung an den Anfragezustand. Kommentarpflicht: Verwechslungssperre, kein Sicherheitsmerkmal |
| `range_query` auf `mtime` | `_extension_query` Z. 292-297 | Erste Bereichsabfrage des Projekts; `use_inverted_index` bleibt bei `False` und braucht genau dafuer den Kommentar (13-RESEARCH Befund 3) |

---

## Metadata

**Analog search scope:** `backend/src/findling/{query,index,api}`, `backend/tests`,
`php/lib/{Controller,Service,Search}`, `php/templates`, `php/css`, `php/l10n`,
`php/tests/Unit`, `docs`, `scripts/ci`, `THIRD-PARTY.md`

**Files scanned:** 31 gelesen (davon 21 vollstaendig, 10 gezielt nach Zeilenbereich)

**Pattern extraction date:** 2026-09-16
