# Phase 19: Frageseite freischalten - Pattern Map

**Kartiert:** 2026-09-24
**Dateien betrachtet:** 19 (3 neu, 15 geaendert, 1 nur bestaetigt)
**Analoga gefunden:** 17 / 19

Quelle der Dateiliste: `19-RESEARCH.md`, Abschnitt "Recommended Project Structure" (Zeilen 232-251),
dazu Pattern 3 (Rangprobe als eigenes Testmodul), Pitfall 5 (Fixture-Zaehlgates) und Open Question 1
(it-Fixture). Ein `19-CONTEXT.md` gibt es nicht; die bindenden Vorentscheide stehen in RESEARCH.md
Abschnitt "Bindende Vorentscheide".

Alle Zeilenangaben sind am Baum vom 2026-09-24 gelesen. Jede Codestelle unten ist vorhandener Code
dieses Repos, kein Entwurf. Entwuerfe stehen ausschliesslich in RESEARCH.md und sind hier nie als
Analog ausgegeben.

**Eine offene Annahme der Recherche ist beim Kartieren geklaert worden.** A4 ("die Ergebnisseite
braucht keine PHP-Aenderung") ist bestaetigt: `php/lib/Service/SearchService.php` kennt kein einziges
Feld. Die Datei nennt `body_de` und `body_en` nirgends, sie reicht `term`, `titleOnly` und das
`SearchFilters`-Objekt unveraendert an `ExAppService::searchCandidates` weiter (Zeilen 144 und
242-257) und kommentiert das dort ausdruecklich als "handed on unchanged and undecided about". Die
PHP-Haelfte bleibt in dieser Phase unberuehrt, und damit auch `PHP_TREE_HASH_TODAY`.

---

## File Classification

| Neue/geaenderte Datei | Rolle | Datenfluss | Naechstes Analog | Guete |
|---|---|---|---|---|
| `backend/src/findling/api/resources.py` | provider / Prozesscache | cache-on-open | sich selbst, `ReadSide` 100-133 und `read_side` 335-428 | exakt |
| `backend/src/findling/query/rewrite.py` | service / Uebersetzer | request-response | sich selbst, `build_query` 470-565 | exakt |
| `backend/src/findling/api/search.py` | controller | request-response | sich selbst, 242-248 | exakt |
| `backend/src/findling/api/snippets.py` | controller | request-response | `api/search.py:242-248` | exakt |
| `backend/src/findling/api/diagnose.py` | controller | request-response | `api/search.py:242-248` | exakt |
| `backend/src/findling/index/schema.py` | model / Definitionstabelle | - | sich selbst, `BODY_FIELD` 94-107 | exakt (keine Aenderung erwartet) |
| `backend/tests/test_query_fields_plan.py` (NEU) | test / Einheit plus Gate | - | `test_schema_generations.py:150-180` plus `conftest.schema_1_index` | Rollentreffer |
| `backend/tests/test_field_plan_ranking.py` (NEU, Name offen) | test / Messprobe | - | `test_rrf_fusion.py:203-221` plus `test_search_library.py:175-182` | Teilstueck |
| `backend/tests/test_no_language_detection.py` (NEU) | test / Anti-Feature-Gate | - | `test_semantic_boundary.py` komplett | exakt |
| `backend/tests/test_language_cases_query_path.py` (NEU) | test / Sprachfaelle | - | `test_language_cases_field_level.py` komplett | exakt, Kopiervorlage |
| `backend/tests/test_schema_generations.py` | test / Phasengrenze | - | sich selbst, 188-381 (der Teil, der faellt) | exakt |
| `backend/tests/test_query_rewrite.py` | test (Aufrufstellen) | - | sich selbst, 98-113 und 147-211 | exakt |
| `backend/tests/test_language_cases_field_level.py` | test / Klassifizierung | - | sich selbst, 75-76 und 307-330 | exakt |
| `backend/tests/test_language_analyzers.py` | test / Zaehlgate | - | sich selbst, `EXPECTED_FAMILY_SCORES` 436 | exakt |
| `backend/tests/fixtures/chain_cases_it.txt` | test-fixture / Messeingabe | - | sich selbst und die drei Geschwister | exakt |
| `backend/tests/test_measurement_scripts.py` | test / Ratsche | - | sich selbst, 915-916 | exakt |
| `.github/workflows/deploy-harp.yml` | CI-config | Beweisstrecke | "Store install 7" ab 2129 (ungegatet) und "Store upgrade 6" ab 3736 (gegatet) | exakt |
| `docs/language-analyzers.md` | doc | - | sich selbst, "Known limits" ab 271 | exakt |
| `docs/measurements/2026-09-analyseketten/` | doc / Messbericht | - | sich selbst | exakt (nur falls die it-Fixture waechst) |

Nicht in der Tabelle und bewusst nicht angefasst: `php/lib/Service/SearchService.php`,
`php/lib/Search/Provider.php`, `php/lib/Controller/PageController.php`. Siehe Vorbemerkung zu A4.

---

## Pattern Assignments

### `backend/src/findling/api/resources.py` (provider, der Feldplan entsteht beim Oeffnen)

**Analog:** sich selbst, drei Stellen.

**Die Form des eingefrorenen Werts** (Zeilen 100-133). `ReadSide` ist selbst die Vorlage fuer
`FieldPlan`: frozen, slots, jedes Feld mit einem Absatz, der sagt, was es nicht ist.

```python
@dataclass(frozen=True, slots=True)
class ReadSide:
    """The handles a search needs, plus the path they were opened from."""

    index: Index
    store: Store
    index_dir: Path
    ...
    vectors: VectorStore | None = None
    # Which generation of the reading side these handles belong to, and the
    # whole reason the field exists is audit finding M-18-02.
    generation: int = 0
```

Ein neues Feld `field_plan: FieldPlan = LEGACY_PLAN` folgt dieser Bauart: Vorgabewert vorhanden,
Vorgabewert **sicher** (der Bestandsplan, nie ein berechneter), und ein Absatz darueber, warum der
Plan hier haengt und nicht in einem eigenen Cache.

**Die Stelle, an der er berechnet wird** (Zeilen 396-415, im `try` von `read_side()`):

```python
        try:
            index = open_index(resolved.index_dir, build_artifact().entries)
            # Once per index, not once per query: configuring the reader costs
            # 0.10 ms while a whole search costs 0.005 ms. ...
            open_reader(index)
            store = open_read_only(resolved.state_db)
            # After the two that matter, and outside their fate. Whatever this
            # answers, the read side is opened.
            vectors = _read_only_vectors(resolved.vectors_db)
            _OPEN = ReadSide(
                index=index,
                store=store,
                index_dir=resolved.index_dir,
                vectors=vectors,
                generation=_GENERATION,
            )
```

Die Zeile `vectors = _read_only_vectors(...)` mit ihrem Kommentar ist die exakte Praezedenz fuer die
Berechnung des Feldplans: eine Ermittlung, die **nach** den beiden Handles laeuft, deren Scheitern
den Lesepfad nicht kippt, und die in dasselbe `ReadSide(...)` wandert. Der Plan wird an genau dieser
Stelle gerechnet, aus `store.read_meta()` und einer `doc_freq`-Sonde auf `index.searcher()`.

**Das Lesemuster der Marken** (`api/status.py:372` und `index/rebuild.py:1009`), zwei Aufrufstellen,
die zeigen, wie eine Marke in diesem Baum gelesen wird:

```python
    marks = store.read_meta()
    ...
        languagesActive=marks.get(LANGUAGES_MARK, "") or volume.languagesActive,
```

```python
    stored = store.read_meta().get(LANGUAGES_MARK, "")
    carried = {code for code in stored.split(",") if code} or set(_CARRIED_WITHOUT_A_MARK)
```

Die zweite ist die Vorlage, auf die es ankommt: `_new_language_count` in `index/rebuild.py:1001-1011`
liest die Sprachmarke bereits heute mit der Legacy-Regel, und sein Docstring begruendet sie in drei
Saetzen ("A missing mark is answered with the legacy pair rather than with nothing at all"). Der
Feldplan schreibt keine dritte Lesart, er uebernimmt diese. Die Konstante dazu steht zweimal im Baum
und ist in `index/rebuild.py:229-236` mit der Begruendung versehen, warum sie zweimal dasteht:

```python
# What an index without a language mark was built with. Not a guess and not a
# default: no release up to 1.2.0 could write a body field outside this pair, so
# the absence of the mark is evidence rather than a gap. The same tuple stands in
# findling.store.repo as LEGACY_LANGUAGES, which is where the comparison reads it,
# and a case in the suite holds the two spellings together.
_CARRIED_WITHOUT_A_MARK: Final = ("de", "en")
```

`resources.py` importiert bereits aus `store.repo` und darf `LEGACY_LANGUAGES` (`store/repo.py:100`)
direkt nehmen; eine dritte Schreibweise ist in keinem Fall zulaessig.

**Das Tor am Schemamerker, Vorlage fuer die Form** (`store/repo.py:136` und 1431-1462):

```python
LEGACY_SCHEMA_STEPS: Final = frozenset({("1", "2")})
```

```python
def _schema_is_legacy(stored: str | None, expected: str) -> bool:
    ...
    if stored is None:
        return False
    return (stored, expected) in LEGACY_SCHEMA_STEPS
```

Daraus folgt fuer den Feldplan: `stored: str | None` als Eingabe, `bool` als Antwort, geschlossene
Tabelle statt Zahlenvergleich, und ein Docstring mit dem Satz, warum ein unlesbarer Zustand kein
Freifahrtschein ist. Die Gegenwartsmarke ist `str(SCHEMA_VERSION)` aus `findling.config:49`
(**heute 2**); ein Literal `"2"` in der Planfunktion waere die vierte Schreibweise desselben Werts
und faellt unter dieselbe Regel wie eine zweite Lesart der Sprachmarke.

**Die Sonde und ihre Fehlerbehandlung** (Zeilen 645-653, aus `filled_languages`):

```python
        for code in _chains_worth_probing():
            try:
                if searcher.terms_with_prefix(BODY_FIELD[code], "", limit=1):
                    filled.append(code)
            # One chain, one answer. A directory of the old generation has no
            # field beyond the first two, and asking it for one is the realistic
            # shape of this failure rather than a fault worth a warning.
            except Exception as error:
                LOGGER.debug("the chain %s could not be probed, an %s", code, type(error).__name__)
```

Die Gegenprobe des Feldplans (`searcher.doc_freq(field, "")` je Koerperfeld) kopiert genau diese
Form: ein `try` je Feld, Ausgabe nur der Feldname und `type(error).__name__`, nie ein Pfad. Ein
Unterschied ist zu begruenden: hier faellt der **ganze** Plan auf den Bestandsplan zurueck, nicht nur
das eine Feld, und das ist eine Warnzeile und keine Debugzeile, weil es der Fall "state.db aus einer
Sicherung neben einem aelteren Indexverzeichnis" ist.

**Was `filled_languages` bleibt und was es nicht wird** (Zeilen 571-624). Der Docstring nennt die
Kosten der Sonde als Grund fuer ihre Sparsamkeit (Audit M-18-08) und die eigene TTL als Grund fuer
den Cache. Diese Funktion wird vom Feldplan **nicht** gerufen; RESEARCH Open Question 2 empfiehlt die
Marke, und die Begruendung steht wortwoertlich in diesem Docstring.

---

### `backend/src/findling/query/rewrite.py` (service, die eine Zeile und ihr Modulkopf)

**Analog:** sich selbst.

**Die drei Konstanten, die verschwinden** (Zeilen 53-65) mit den Kommentaren, die mitwandern
muessen, weil sie die fachliche Aussage tragen:

```python
# What a bare word searches. In schema order, and the German body first because
# it is the field that carries the content of the file.
DEFAULT_FIELDS: Final = [FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE]

# What a bare word searches once the built in Nextcloud filter for "file name
# instead of content" is set. ...
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]

FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_TITLE: 2.0, FIELD_BODY_DE: 1.0, FIELD_BODY_EN: 0.8}
```

Diese drei Werte sind zugleich der Inhalt von `LEGACY_PLAN` (RESEARCH, Skizze am Ende der Code
Examples). Sie werden nicht umformuliert, sie werden verschoben.

**Die eine Zeile, um die es geht** (Zeilen 540-546):

```python
    parsed, errors = index.parse_query_lenient(
        rewritten,
        default_field_names=TITLE_ONLY_FIELDS if title_only else DEFAULT_FIELDS,
        field_boosts=FIELD_BOOSTS,
        conjunction_by_default=True,
        allow_regexes=False,
    )
```

`conjunction_by_default=True` und `allow_regexes=False` bleiben unangetastet; letzteres wird von
`test_index_open.py:377` bewacht.

**Die Signaturvorlage fuer den neuen Parameter** (Zeilen 470-493):

```python
def build_query(
    index: Index,
    text: str,
    *,
    title_only: bool = False,
    groups: Sequence[str] = (),
    since: int | None = None,
    until: int | None = None,
) -> RewrittenQuery:
    """Turn a search line into a query, its filters and the parser's complaints.
    ...
    ``groups``, ``since`` and ``until`` are the structured half of the filter,
    the one the result page sets. They are keyword arguments with a default so
    that the callers who filter nothing stay exactly as they are, ...
    """
```

Der Satz "keyword arguments with a default so that the callers who filter nothing stay exactly as
they are" ist die Praezedenz fuer RESEARCH Pitfall 6: `plan` ist keyword-only mit Vorgabewert, und
der Vorgabewert ist `LEGACY_PLAN` und niemals etwas aus `settings()`.

**Der Modulkopf, der die Aenderung mittragen muss** (Zeilen 1-25). Er erklaert heute vier
Parsereinstellungen einzeln, zwei davon sind genau die, die beweglich werden:

```
* ``default_field_names`` decides what "a word without a field" means, and the
  answer depends on whether the caller asked for the file name filter.
* ``field_boosts`` puts the file name above the title and the title above the
  body. A name is a deliberate act, a body word is an accident of prose.
```

Nach Phase 19 haengt die Antwort nicht mehr nur am Dateinamenfilter, sondern am Verzeichnis. Ein
Diff, der diese zwei Absaetze stehen laesst, widerlegt sich selbst; dieselbe Regel hat Phase 18 am
Kopf von `index/schema.py` angewandt.

**Die Dataclass, die den Plan nicht bekommt** (Zeilen 337-366). `RewrittenQuery` traegt heute sechs
Felder und jedes mit einem Absatz. Der Feldplan gehoert **nicht** hinein: er ist Eingabe und nicht
Ergebnis, und ein siebtes Feld waere die zweite Lesart, gegen die Pattern 5 Aussage 2 gerichtet ist.

---

### `backend/src/findling/api/search.py`, `api/snippets.py`, `api/diagnose.py` (Aufrufstellen)

**Analog:** `api/search.py:242-248`, und die drei Stellen sind bis auf ein Wort identisch:

```python
    try:
        side = resources.read_side()
        if side is None:
            return _Round([], False, offset, True)
        is_degraded = resources.degraded(side)
        rewritten = build_query(side.index, text, title_only=title_only, groups=groups, since=since, until=until)
```

| Datei:Zeile | Aufruf heute |
|---|---|
| `backend/src/findling/api/search.py:248` | `build_query(side.index, text, title_only=title_only, groups=groups, since=since, until=until)` |
| `backend/src/findling/api/snippets.py:187` | dieselbe Zeile, identisch |
| `backend/src/findling/api/diagnose.py:198` | dieselbe Zeile mit `title_only=False` |

An allen drei Stellen liegt `side` bereits in der Hand, also ist die Aenderung je Datei ein
`plan=side.field_plan` und nichts sonst. Keine der drei Dateien darf den Plan selbst rechnen; das
waere die zweite Lesart. Die Importzeilen stehen in `search.py:60`, `snippets.py:58`,
`diagnose.py:62` und aendern sich nicht.

---

### `backend/src/findling/index/schema.py` (nur bestaetigen)

**Analog:** sich selbst (Zeilen 94-107):

```python
# The one place where a language code turns into a schema field name, built the
# way findling.config.SNOWBALL_NAME is built and held against it by a test: a
# closed mapping, never a composed string. Measured, and that is why it is a
# mapping: writer.add_document accepts a field name the schema does not know
# without a word of complaint and drops the value, so "body_" + code would lose
# a whole language on a typo and nothing anywhere would say so.
BODY_FIELD: Final = {
    "de": FIELD_BODY_DE,
    "en": FIELD_BODY_EN,
    ...
}
```

`BODY_FIELD` ist geordnet und ist die Schemafeldreihenfolge. Der Feldplan iteriert ueber diese
Abbildung und filtert gegen die Sprachmenge, genau wie `_chains_worth_probing`
(`api/resources.py:665-676`) es vormacht:

```python
    active = set(settings().languages) | {"de"}
    return tuple(code for code in BODY_FIELD if code in active)
```

**Achtung, der Unterschied ist die ganze Phase:** diese Funktion liest `settings()`, weil sie eine
Diagnose der Adminseite ist. Der Feldplan liest die Marke. Die Schleifenform wird kopiert, die
Quelle nicht. Und `| {"de"}` faellt weg: RESEARCH Pitfall 7 sagt, dass `body_de` keinen Sonderfall
in der Frage bekommt.

---

### `backend/tests/test_query_fields_plan.py` (NEU, der Feldplan als Einheit)

**Analoga, nach Aufgaben zerlegt:**

| Aufgabe im neuen Modul | Von wo kopieren |
|---|---|
| Der Plan gegen einen echten Bestandsindex | `conftest.py:395-406` (`schema_1_index`) plus `test_schema_generations.py:150-180` |
| Der Plan gegen einen Index der neuen Generation | `conftest.py:408-416` (`schema_2_index`) |
| Die Maschine statt der Namen pruefen | `test_schema_generations.py:170-180` |
| Mengenaussage `set(plan.boosts) <= set(plan.fields)` | `test_schema_generations.py:112-134` (Form der Inklusionstests) |
| Gestellte Muster und Selbsttest | `test_schema_generations.py:295-381` |

**Die Fixture, die den Bestandsbeweis moeglich macht** (`conftest.py:395-406`):

```python
@pytest.fixture
def schema_1_index(tmp_path: Path) -> Index:
    """A real index of the schema that shipped up to 1.2.0, filled and committed.

    No volume and no settings: this fixture hands out an index and nothing else,
    because the question it answers is asked of the query builder and never of an
    endpoint. ...
    """
    return write_schema_1_index(tmp_path, FIXTURE_DOCUMENTS)
```

**Die Bauart des Falls, der an die Stelle des AST-Waechters tritt** (`test_schema_generations.py:
153-180`), und die beiden Haelften zusammen sind der Ersatz, den Pattern 6 verlangt:

```python
def test_the_old_index_rejects_a_body_field_it_does_not_have(schema_1_index: Index) -> None:
    # The failure this whole file is about, provoked once so that the inclusions
    # above are known to be guarding something real rather than nothing at all.
    # Lenient parsing is lenient about the query text; a field name is not text.
    for field in (FIELD_BODY_ES, FIELD_BODY_IT, FIELD_BODY_NL, FIELD_BODY_PT):
        with pytest.raises(ValueError, match=field):
            schema_1_index.parse_query_lenient("vertrag", default_field_names=[field])


def test_the_old_index_accepts_every_field_of_the_query(schema_1_index: Index) -> None:
    # The inclusion above, asked of the engine instead of of a set. ...
    for field in sorted(set(DEFAULT_FIELDS) | set(TITLE_ONLY_FIELDS) | set(FIELD_BOOSTS)):
        parsed, errors = schema_1_index.parse_query_lenient("vertrag", default_field_names=[field])

        assert errors == []
        assert parsed is not None
```

`pytest.raises(ValueError, match=field)` matcht auf den Feldnamen und nicht auf die Klammerung; das
ist die Stelle, die RESEARCH unter "Deprecated" ausdruecklich als bereits richtig ausweist.

**Die Form der Gate-Dateien insgesamt** (`test_search_fields_lockstep.py:19-25`), gueltig fuer jedes
neue Gate dieser Phase:

```
The shape is the shape of ``test_search_limits_lockstep.py`` ...: it reads the
sources as text rather than importing them, so that a model which does not even
import any more is a red gate and not an error in collection; it fails closed,
so a file that moved produces a finding for every field that should have come
out of it; and it carries self tests against staged samples, so that a gate
whose body was deleted cannot report zero findings over zero fields and look
healthy.
```

---

### `backend/tests/test_field_plan_ranking.py` (NEU, die Rangprobe)

**Analoga:**

| Aufgabe | Von wo kopieren |
|---|---|
| Aussage plus Gegenprobe als Paar | `test_rrf_fusion.py:203-221` |
| Die Reihenfolge einer echten Suche ablesen | `test_search_library.py:175-182` |
| Einen Index mit genau drei Dokumenten bauen | `test_language_cases_field_level.py:186-211` |
| Modulkopf, der sagt, was die Probe nicht beweist | `test_rrf_fusion.py:1-25` |

**Das Paarmuster, das Zusicherung 4 traegt** (`test_rrf_fusion.py:203-213`):

```python
def test_a_semantic_weight_of_zero_removes_the_semantic_list() -> None:
    # Damping down to nothing has to produce exactly the lexical result set,
    # otherwise a document that is only in the vector list would ride along
    # with a score of zero and the setting would not be a setting but a
    # reordering.
    lexical = [10, 20]

    fused = fuse(lexical, [30, 10], semantic_weight=0.0)

    assert ids(fused) == lexical
```

Uebertragen: die Zusicherung "A steht vor B" braucht daneben den Lauf mit allen vier Boosts auf 1,0,
der den Rang kippt. Ohne ihn waere die Zusicherung auch fuer einen Index gruen, in dem B die Frage
gar nicht trifft.

**Das Ablesen der Reihenfolge** (`test_search_library.py:175-182`):

```python
def _unfiltered_order(index: Index, text: str = "Kündigungsfrist") -> list[int]:
    searcher = index.searcher()
    found: list[int] = []
    for _, address in searcher.search(_query(index, text), DOCUMENTS).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        assert value is not None
        found.append(int(value))
    return found
```

**Der Modulkopf, der die Grenze der Probe benennt** (`test_rrf_fusion.py:1-25`). Er sagt zuerst, was
schiefgeht, dann was die Datei beweist, und er endet mit dem Satz, was sie nicht beweist. Genau
dieser Aufbau wird hier gebraucht, weil Erfolgskriterium 3 der Roadmap eine Begruendung traegt, die
die Behauptung nicht deckt (RESEARCH Pattern 3). Die Messreihe M-3 gehoert als Zahlentabelle in
diesen Kopf, so wie `index/writer.py:1-49` es fuer seine vier Messreihen vormacht.

---

### `backend/tests/test_no_language_detection.py` (NEU, der Anti-Feature-Waechter)

**Analog:** `backend/tests/test_semantic_boundary.py`, vollstaendige Kopiervorlage, Helfer fuer
Helfer.

**Die Hygiene, ohne die der Waechter sich selbst ausloest** (Zeilen 79-102):

```python
def _significant_tokens(source: str) -> list[tokenize.TokenInfo]:
    """The names and operators of a source, comments and string literals gone.

    This is the whole of the grep hygiene, and it is done with the tokenizer
    rather than with a line filter on purpose. A line filter drops ``#`` lines
    and leaves docstrings standing, and docstrings are exactly where this phase
    spells out the forbidden words ...
    """
    return [
        token
        for token in tokenize.generate_tokens(io.StringIO(source).readline)
        if token.type in {tokenize.NAME, tokenize.OP}
    ]


def code_mentions(source: str, name: str) -> int:
    """How often an identifier stands in the *code* of a source. ..."""
    return sum(1 for token in _significant_tokens(source) if token.type == tokenize.NAME and token.string == name)
```

`code_mentions` ist der Zaehler fuer Aussage 2 (`build_query` liest den Plan nur aus seinem
Parameter und nie aus `settings()`), `call_sites` (Zeilen 105-122) fuer die Aufrufzaehlung, und
`functions_calling` (Zeilen 134-149) fuer die Frage, **welche** Funktion es tut.

**Die Begruendung, warum das Modul ueberhaupt ein Quelltextleser ist** (Zeilen 12-18):

```
**Why this file is a grep and not a functional test.** A functional test cannot
prove the absence of a route. It exercises what exists; a second route would sit
next to everything it touches and every single assertion would stay green.
```

Dieser Absatz ist wortgleich auf die Spracherkennung uebertragbar und gehoert in den Kopf des neuen
Moduls.

**Die zwei gestellten Muster, die der Waechter braucht** (Zeilen 265-283 und 360-396):

```python
_THIRD_CALL_SITE = '''


def a_second_gate(store: object, uid: str, file_ids: list[int]) -> object:
    """Another place that decides what a user may see."""
    return store.prefilter_visible(uid, file_ids)
'''


def test_a_third_call_site_makes_the_count_red() -> None:
    # The red proof of the count, against the real source plus one function.
    grown = SEARCH_SOURCE.read_text(encoding="utf-8") + _THIRD_CALL_SITE

    assert call_sites(grown, PREFILTER) == 3, (
        "a third call site has to move the number, otherwise the assertion above is decoration"
    )
```

```python
def test_a_comment_line_full_of_the_forbidden_words_moves_no_count() -> None:
    naive = _HYGIENE_SAMPLE.count(PREFILTER)

    assert naive >= 6, "the sample has to be far off under a naive count, otherwise it proves nothing"
```

Fuer Phase 19 heisst das konkret: ein gestelltes Muster mit einem Textparameter in der Signatur der
Planfunktion muss rot werden (Aussage 1), und ein Muster, das `settings` in einem Kommentar und in
einem Docstring nennt, darf keinen Zaehler bewegen. Die Signaturpruefung selbst laeuft ueber `ast`
und nicht ueber `tokenize`; die Vorlage dafuer ist `functions_calling` (Zeilen 134-149), die bereits
`ast.FunctionDef | ast.AsyncFunctionDef` besucht.

**Aussage 3 am Abhaengigkeitsbaum** hat keine direkte Vorlage im Paketpruefer, wohl aber im
Dateilesemuster von `test_measurement_scripts.py`: Datei als Text lesen, gegen eine benannte
Konstantenmenge halten, Befund je Treffer. Die Namen stehen in RESEARCH Pattern 5 Aussage 3.

**Aussage 4 wird nicht wiederholt.** `test_search_fields_lockstep.py` haelt `extra="forbid"` und die
Feldliste von `SearchRequest` bereits; der neue Waechter nennt die Datei und dupliziert sie nicht.

---

### `backend/tests/test_language_cases_query_path.py` (NEU, die Faelle auf dem Suchweg)

**Analog:** `backend/tests/test_language_cases_field_level.py`, vollstaendige Kopiervorlage. Der
Modulkopf dort sieht diese Hebung ausdruecklich vor (Zeilen 1-10).

**Die Auswahllogik, die uebernommen und um eine Kette erweitert wird** (Zeilen 120-132):

```python
def _separated_pairs(chain: TextAnalyzer, english: TextAnalyzer, families: Sequence[Sequence[str]]) -> list[Pair]:
    """The pairs the target chain merges AND the English chain keeps on two terms.

    This is the strong criterion, the one the failed probe of 2026-09-24 did not
    apply. A pair out of this list can only be brought together by the chain of
    its own language.
    """
    return [
        pair
        for forms in families
        for pair in _pairs(forms)
        if _share_a_term(chain, pair) and not _share_a_term(english, pair)
    ]
```

Auf dem normalen Suchweg sind alle aktiven Felder in der Liste, also kommt die **deutsche** Kette als
dritter Ausschluss dazu (RESEARCH Pattern 4 und Pitfall 2). Die deutsche Kette ist teuer zu bauen;
`test_language_cases_field_level.py:83-86` zeigt, wie das Modul die Konstituentenliste einmal je
Session laedt:

```python
CONSTITUENTS: Final = (
    (Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()
)
```

**Die Wahl des Paares als Zusicherung und nicht als Kommentar** (Zeilen 153-168):

```python
def _case_pair(code: str, chain: TextAnalyzer, english: TextAnalyzer, families: Sequence[Sequence[str]]) -> Pair:
    """The pair one case runs on: the first one of the fixture that qualifies.

    First and not "the nicest one", because the choice has to come out of the
    fixture and not out of the taste of whoever wrote the file. ...
    """
    separated = _separated_pairs(chain, english, families)
    if separated:
        return separated[0]
```

**Die Gegenprobe, die den Fall erst zu einem Fall macht** (Zeilen 393-406):

```python
@pytest.mark.parametrize("code", CODES)
def test_the_same_question_against_the_english_field_finds_nothing(
    code: str, indexes: dict[str, Index], searchers: dict[str, Searcher], pairs: dict[str, Pair]
) -> None:
    # The counter proof. body_en of this index was never written, so an answer
    # here would mean the hit above came from somewhere other than the field the
    # case is about.
```

Auf dem Suchweg wird daraus die Gegenprobe, die RESEARCH Pitfall 2 unter "Warnzeichen" nennt: **der
Fall muss rot werden, wenn man `body_<code>` aus dem Plan nimmt.** Das ist mit einem Plan, der als
Parameter reist, ein Einzeiler und gehoert in genau dieses Modul.

**Die Regel, die weiter gilt** (Zeilen 447-458):

```python
def test_no_form_of_the_case_stands_in_this_file(
    code: str, pairs: dict[str, Pair], distractors: dict[str, str]
) -> None:
    # T-18-04-02. A form copied in here would survive a rebuild of the chains
    # that moves the fixture, and the case would then measure a word the
    # measurement has dropped.
```

`SOURCE_WORDS` (Zeile 81) liest die eigene Datei; die Zeile wird mitkopiert, sonst haelt die Regel
im neuen Modul nicht.

**Der Index eines Falls** (Zeilen 186-211): `open_index` und nie der tantivy-Konstruktor, Feld fuer
Feld und nie ueber Schluesselwoerter, `commit()` plus `wait_merging_threads()` plus `reload()`. Fuer
den Suchweg braucht der Fall zusaetzlich einen Store oder zumindest die Marken, aus denen der Plan
faellt; die billigste Form ist, den Plan im Test direkt zu bauen und zusaetzlich einen Fall zu
haben, der ihn aus einer echten `state.db` rechnet (dafuer ist
`conftest.write_state:267-273` die Vorlage, sie ruft `expected_versions(corpus.digest, ",".join(...))`).

---

### `backend/tests/test_schema_generations.py` (die Phasengrenze aufloesen)

**Analog:** sich selbst. Was faellt und was bleibt, ist in der Datei bereits auseinandersortiert.

**Was faellt:** alles ab Zeile 186 ("-- the syntax tree guard over the three field lists --"), also
`FIELD_LISTS` (195), `_field_constants` (198), `_entries` (221), `_field_name` (236),
`body_fields_outside_the_old_schema` (243), der Gate-Test (292) und die sechs gestellten Muster
(295-381). Die Datei selbst sagt in Zeilen 34-43, dass das so vorgesehen ist:

```
**Why the guard is written to be thrown away.** Phase 19 turns ``DEFAULT_FIELDS``
and ``FIELD_BOOSTS`` into functions of the stored ``schema_version`` mark, and
from that moment a check over constants has nothing left to check ...
whoever deletes it in phase 19 will have to say in the same commit what took its
place.
```

**Was bleibt:** `FIELDS_SCHEMA_1` (78-88) mit seinem Kommentarblock (66-77), die Mengeninklusionen
(96-146) und die drei Faelle gegen den echten Schema-1-Index (153-180). Die Inklusionen lesen heute
`DEFAULT_FIELDS`, `TITLE_ONLY_FIELDS` und `FIELD_BOOSTS`; sie lesen nach dem Umbau die Felder und
Boosts des Bestandsplans, was dieselbe Aussage ist und derselbe Einzeiler bleibt:

```python
def test_the_default_field_list_exists_in_the_old_schema() -> None:
    missing = sorted(set(DEFAULT_FIELDS) - set(FIELDS_SCHEMA_1))
    assert not missing, f"DEFAULT_FIELDS names {missing}, which an index of the old schema does not have"
```

**Der Fall, der den Uebergang schon festhaelt** (Zeilen 371-381): `test_the_gate_fails_closed_when_
a_field_list_stops_being_a_list` mit dem Muster `_SAMPLE_WITH_A_COMPUTED_LIST` (Zeilen 330-334) ist
die Stelle, an der die Datei ihren eigenen Tod voraussagt. Er faellt mit dem Rest, und der Commit
sagt, was an seine Stelle trat (`test_query_fields_plan.py`).

---

### `backend/tests/test_query_rewrite.py` (Aufrufstellen nachziehen)

**Analog:** sich selbst.

**Die Fixture, gegen die alles laeuft** (Zeilen 98-113): drei deutsche Dokumente, ein Index ueber
`open_index`, `FIELD_BODY_DE` befuellt. Sie bleibt, wie sie ist.

**Die Aufrufform, die sich nicht aendern darf** (Zeilen 147-211), rund zwei Dutzend Stellen der Form
`build_query(index, "kuendigung")`:

```python
    assert _found(index, build_query(index, "kuendigung")) == [1]
    ...
    assert _found(index, build_query(index, "vertrag", title_only=True)) == [2]
```

Genau darum ist der Parameter keyword-only mit sicherem Vorgabewert (RESEARCH Pitfall 6): keine
dieser Zeilen wird angefasst, und ein neuer Fall belegt, dass der Vorgabewert der Bestandsplan ist.

---

### `backend/tests/test_language_cases_field_level.py` und `test_language_analyzers.py` (nur falls die it-Fixture waechst)

**Analog:** sich selbst, zwei zusammengehoerige Stellen.

**Die Klassifizierung, die sich dann umdreht** (`test_language_cases_field_level.py:75-76`):

```python
SEPARATED: Final = ("es", "nl", "pt")
FOLDED: Final = ("it",)
```

Der Test darueber (Zeilen 317-330) ist so geschrieben, dass er bei einer neuen it-Flexionsfamilie
rot wird, und der Kommentar sagt, dass das gute Nachricht ist:

```python
    assert separated == [], (
        f"{CASE_FIXTURES[code].name} now holds {len(separated)} pair(s) the English chain keeps apart, the first "
        f"of them {separated[0] if separated else ()}: move {code} from FOLDED to SEPARATED and let the case run "
        "on the strong criterion"
    )
```

Die Fehlermeldung ist zugleich die Handlungsanweisung des Plans: `it` wandert von `FOLDED` nach
`SEPARATED`.

**Das Zaehlgate, das im selben Commit wandert** (`test_language_analyzers.py:425-436`):

```python
# Hits and possible ordered pairs per language, read out of
# docs/measurements/2026-09-analyseketten/rohdaten/kennzahlen.txt, run of
# 2026-09-23 against tantivy tag 0.26.2: es_Aplus_hits 174 of es_pairs 208,
# it 56 of 56, nl 57 of 81, pt 180 of 228, together 467 of 573.
#
# Equality and not "at least". ... When one of these numbers falls, run
# scripts/dev/measure_chains.sh first, write the finding into the measurement
# report, and only then pull the constant here after it. Never the other way
# round: a number corrected in this file first is a gate agreeing with the
# change it was built to catch.
EXPECTED_FAMILY_SCORES = {"es": (174, 208), "it": (56, 56), "nl": (57, 81), "pt": (180, 228)}
```

Die Reihenfolge ist damit vorgeschrieben und gehoert als Schrittfolge in den Plan: Fixture
erweitern, `scripts/dev/measure_chains.sh` laufen lassen, Befund in
`docs/measurements/2026-09-analyseketten/` schreiben (README.md, `rohdaten/kennzahlen.txt`,
`familien.tsv`, `verluste.tsv`), erst danach die Konstante nachziehen. Nie umgekehrt.

---

### `backend/tests/test_measurement_scripts.py` (die Ratsche)

**Analog:** sich selbst, Zeilen 915-916 mit dem Kommentarblock darueber:

```python
PACKAGE_FILES_TODAY = 56
PACKAGE_TREE_HASH_TODAY = "193449595cfb677a64bb82fa250a89c53fe90f5ee3053832950ca3d5275f94b2"
```

Der Kommentar darueber ist eine datierte Kette von Absaetzen, einer je Bewegung, und jeder sagt,
**welche** der 56 Dateien ihre Bytes geaendert haben und ob die Zahl mitgeht. Phase 19 aendert fuenf
Module unter `backend/src/findling` und fuegt keines hinzu, also bleibt `PACKAGE_FILES_TODAY = 56`
und nur der Hash bewegt sich, mit einem Absatz in genau dieser Form.

`PHP_FILES_TODAY` (564) und `PHP_TREE_HASH_TODAY` (565) werden **nicht** angefasst: die PHP-Haelfte
aendert sich in dieser Phase nicht (siehe A4 oben).

---

### `.github/workflows/deploy-harp.yml` (zwei Fragen, zwei Orte)

**(a) Der spanische Vorher-Nachher-Beweis, gegatet.**

**Analog:** "Store upgrade 6, the rebuild a changed language set orders" (ab 3736) und die
Vorbedingungsblöcke ab 3777.

Die Schrittbedingung, die diesen Ast auf amd64 festnagelt (Zeile 3737, wortgleich auf 3528):

```yaml
        if: matrix.server-version == 'stable34' && matrix.runner == 'ubuntu-24.04' && env.RELEASE_TAG == ''
```

Die Vorbedingung, die der neue Term **nicht** verletzen darf (Zeilen 3790-3795, gleichlautend auf
3133):

```bash
          if ! jq -e '[.terms[]] | all(. == 1)' "${before}" > /dev/null; then
            echo "::error::not every one of the three terms brings back exactly one file before the rebuild"
            echo "An unchanged count after the rebuild would then be the unchanged absence of a hit."
            jq '.terms' "${before}"
            exit 1
          fi
```

Deshalb bekommt der spanische Term einen **eigenen Schluessel** neben `.terms`, nicht einen vierten
Eintrag darin. Die Stelle dafuer ist `snapshot()` (Zeilen 3011-3100), und ihre Bauart ist
vorgeschrieben: jeder Wert erst in eine Shellvariable, jeder Leerwert ein Abbruch mit Rohtext auf
dem Protokoll, und erst danach baut genau ein `jq -n` das Objekt. Der Kommentar bei Zeile 3038 sagt
das fuer den achten Wert aus:

```bash
            # The eighth value of a snapshot, since 2026-09-24. Its own line and
            # its own emptiness check, in the shape the four occ numbers above
            # are checked in: a value goes into a shell variable first, an empty
            # one ends the snapshot with the raw answer on record, and only then
            # does one jq -n build the object (T-18-12-03).
            rebuild=$(rebuild_state) || return 1
```

Der Zaehler selbst existiert schon und wird gerufen, nicht nachgebaut (`term_hits`, Zeilen
2841-2862): eine OCS-Suche, Statuscode geprueft, `entries | length` als Zahl, unlesbare Antwort ist
ein Abbruch.

Die spanische Datei wandert in "Store upgrade 2" (ab 2608), wo heute der Referenzkorpus und der
Fuellkorpus ins Nutzerverzeichnis gelegt werden. Der Kommentarblock dort (Zeilen 2646-2652) nennt
die Regel, die fuer die neue Datei genauso gilt:

```
          # The words are deliberately botanical. None of them carries Belehrung,
          # Auszug, Erinnerung, florpel or findling-canary, and none of them
          # splits into a constituent that does: the three term assertions of
          # this proof have to keep answering with exactly one file each, and
          # the check right after the drain below says so rather than assumes it.
```

Die Sprachumgebung des Umbaus steht in Zeilen 362-363 und wird nicht bewegt:
`REBUILD_LANGUAGES: 'es,de,en'`, `REBUILD_LANGUAGES_NORMALISED: 'de,en,es'`.

**(b) Der ungegatete Sprachbeweis, der auch auf arm64 laeuft.**

**Analog:** "Store install 7, a search finds content without anybody configuring anything" (ab 2129).
Der Schritt traegt **kein** `if`, laedt eine Datei ueber WebDAV hoch und pollt die OCS-Suchroute bis
zum Treffer:

```bash
          code=$(curl -s -o /dev/null -w '%{http_code}' \
            -T "${RUNNER_TEMP}/zero-config.txt" \
            -u "testuser:${TESTUSER_PASS}" \
            'http://localhost:8080/remote.php/dav/files/testuser/findling-zero-config.txt')
          ...
          deadline=$(( $(date +%s) + ZERO_CONFIG_BUDGET_SECONDS ))
          while [ "$(date +%s)" -lt "${deadline}" ]; do
            rounds=$(( rounds + 1 ))
            timeout 300 php -f cron.php > "${RUNNER_TEMP}/cron-${rounds}.log" 2>&1 || true
            code=$(curl -s -o zero-config.json -w '%{http_code}' \
              -u "testuser:${TESTUSER_PASS}" \
              -H 'OCS-APIRequest: true' \
              -H 'Accept: application/json' \
              'http://localhost:8080/ocs/v2.php/search/providers/findling/search?term=florpel')
            if [ "${code}" = "200" ] && jq -e '.ocs.data.entries | length >= 1' zero-config.json > /dev/null 2>&1; then
              found="yes"
              break
            fi
            echo "round ${rounds}: HTTP ${code}, no hit yet, $(( deadline - $(date +%s) ))s of the budget left"
            sleep 10
          done
```

Drei Merkmale sind zu uebernehmen und stehen dort auch begruendet: die Schleife verlaesst sich beim
Treffer und schlaeft nie eine feste Zeit (die 52-Sekunden-Lehre aus Plan 06-11, Kommentar Zeilen
2154-2158), ein Reissen des Budgets ist ein Befund und kein Grund, das Budget zu heben
(`T-06.1-52`, Zeile 2181), und die Behauptung wird gegen das Protokoll geprueft und nicht
behauptet (Zeilen 2190-2201). Die Zusicherung selbst prueft `entries | length` und nie
`entries[0].subline`, was hier zufaellig genau die Form ist, die RESEARCH Pitfall 4 verlangt.

**(c) Die Ergebnisseite.** `PageController::index` traegt `NoAdminRequired`, `NoCSRFRequired` und
`FrontpageRoute` (Zeilen 215-218), ist also mit einem einzigen `curl -u testuser:pass` erreichbar:

```php
	#[\OCP\AppFramework\Http\Attribute\NoAdminRequired]
	#[\OCP\AppFramework\Http\Attribute\NoCSRFRequired]
	#[\OCP\AppFramework\Http\Attribute\FrontpageRoute(verb: 'GET', url: '/')]
	public function index(): TemplateResponse {
```

Heute beruehrt kein CI-Schritt diese Route. Der neue Aufruf gehoert in den Schritt aus (b) und
prueft den Dateinamen im HTML, nicht den Textauszug.

---

### `docs/language-analyzers.md` (zwei Abschnitte)

**Analog:** sich selbst.

**Vorlage fuer den neuen Abschnitt "Was die Frageseite durchsucht"**: der Abschnitt "Switching a
language on, and when it takes effect" (ab Zeile 14). Er beginnt mit der Mechanik in zwei Saetzen,
dann "Two things are worth knowing before the variable is touched", dann je ein fett eingeleiteter
Absatz. Der zweite davon (Zeilen 35-43) ist inhaltlich der direkte Vorlauf des Feldplans: er
erklaert die fehlende Sprachmarke als Beleg und nicht als Luecke.

**Vorlage fuer die Grenze des Textauszugs**: der Abschnitt "Known limits" (ab Zeile 271). Jeder
Eintrag hat dieselbe Form:

```
**The number class with an accented suffix, Spanish.** `información` and
`informacion` share the term `informacion`, and `informaciones` produces
`inform`, so the plural does not meet its own singular. ... The alternative is
the late fold, which buys 4 of 208 pairs and pays with the OCR direction ...
```

Also: fette Einleitung mit Sprache und Klasse, gemessenes Beispiel mit den echten Termen, dann die
Alternative und ihr Preis. Fuer Pitfall 4 heisst das: `SnippetGenerator.create(..., FIELD_BODY_DE)`
(`index/search.py:875`), das gemessene Ergebnis (`fragment() == ''` bei `alemanes` gegen `alemana`,
volles Fragment bei der Kontrollfrage), und die Alternative (ein Auszugspfad je Koerperfeld, also
sechs gespeicherte Textkopien statt einer). Der Satz aus dem Docstring der Funktion
(`index/search.py:855`) gehoert zitiert: "a hit without a snippet is still a hit, and the subline
falls back to the path on the PHP side".

Die Zahl aus der Rangprobe (ab welchem Boost der Rang kippt) gehoert nach RESEARCH Open Question 4
ebenfalls auf diese Seite, in den Abschnitt "Measured numbers" (ab Zeile 152), der bereits die Form
hat: Zahl, Messlauf, Datum.

---

## Shared Patterns

### Logzeilen

**Quelle:** `backend/src/findling/api/resources.py:415-421`
**Gilt fuer:** jede neue Warnung des Feldplans

```python
        except Exception as error:
            # The type name and nothing else. A traceback here would carry
            # whatever a library put into its message, and a path is the usual
            # content.
            LOGGER.warning("the read side could not be opened, an unexpected %s", type(error).__name__)
```

Fuer diese Phase kommt eine zweite Regel dazu, die in RESEARCH unter "Security Domain" steht und im
Baum bereits gelebt wird (`query/rewrite.py:546-549`): der Anfragetext und die Fehlerliste des
Parsers bleiben auf `debug`, eine Zeile zum Feldplan nennt nur Feldnamen und Marken.

```python
    if errors:
        # Debug and nowhere else. These entries quote the input, so an info line
        # would put a search term into a log that operators read and ship.
        LOGGER.debug("the query parser reported %d issue(s)", len(errors))
```

### Der Generationsschutz der Prozesscaches

**Quelle:** `backend/src/findling/api/resources.py:117-133` und 656-665
**Gilt fuer:** jeden Wert, der an `ReadSide` haengt

```python
        if side.generation == _GENERATION:
            # The same guard degraded() carries, and for the same race
            # (M-18-02). This is the reading a rebuild exists to move, so a
            # cache entry filled from the retired directory would have the admin
            # page report the old chains for the whole window right after the
            # run that filled the new ones.
            _FILLED = (side.index_dir, now, answer)
```

Der Feldplan braucht diesen Schutz **nicht** als eigenen Zweig, weil er innerhalb des Locks
zusammen mit den Handles entsteht und nicht ausserhalb gemessen und drinnen geschrieben wird. Genau
das ist der Grund, ihn an `ReadSide` zu haengen statt neben sie, und der Plan sollte es so
begruenden.

### Eine Marke hat genau eine Lesart

**Quelle:** `backend/src/findling/store/repo.py:752-771` (die Vergleichsschleife),
`store/repo.py:1465-1489` (`_languages_are_legacy`), `index/rebuild.py:229-236`
**Gilt fuer:** den Feldplan, ausnahmslos

```python
        stored = self.read_meta()
        diverging = []
        for key, value in expected.items():
            current = stored.get(key)
            if current == value:
                continue
            if key == "index_version" and _generation_at_least(current, value):
                continue
            if key == "tantivy_version" and _index_format_matches(current, value):
                continue
            if key == _SCHEMA_MARK and _schema_is_legacy(current, value):
                continue
            if key == _LANGUAGES_MARK and _languages_are_legacy(current, value):
                continue
            diverging.append(key)
```

Vier benannte Ausnahmen, jede mit einer eigenen Funktion und einem Docstring, der sagt, warum sie
beweisbar und nicht bequem ist. Der Feldplan fuegt hier nichts hinzu, er liest dieselben zwei
Marken mit denselben Regeln.

### Kein zweiter Cache und keine zweite Suchroute

**Quelle:** `backend/src/findling/api/resources.py:135-179` (vier Caches, ein `_LOCK`, jede
Ausnahme kommentiert), `backend/tests/test_semantic_boundary.py:241-266`
**Gilt fuer:** alles in dieser Phase

Der Rechte-Vorfilter wird an genau zwei Stellen gerufen, und das ist eine gezaehlte Zusicherung. Ein
Feldplan, der irgendwo selbst sucht, waere der dritte Aufruf oder, schlimmer, keiner.

### Blockierendes gehoert in einen Worker-Thread

**Quelle:** `backend/src/findling/api/status.py:428`, `backend/src/findling/main.py:365`
**Gilt fuer:** nichts Neues in dieser Phase, aber die Plaene muessen es wissen: der Feldplan wird in
`read_side()` gerechnet, und `read_side()` laeuft bereits in `asyncio.to_thread`.

### Sprache und Zeichensatz

**Quelle:** `CLAUDE.md`, durchgaengig im Baum bestaetigt
**Gilt fuer:** alles

Code, Bezeichner, Kommentare, Docstrings und Logtexte englisch und ASCII. Echte Umlaute nur in
deutscher Prosa (dieses Dokument, Planungsdateien) und in den Fixture-Dateien, wo sie der Gegenstand
sind. Keine Em-Dashes, auch nicht in Kommentaren. Python-Schreibvorgaenge in `.planning`- und
Testdateien mit `newline="\n"`.

### Qualitaetsgates je Plan

**Quelle:** `./CLAUDE.md`, globale Python-Regel
**Gilt fuer:** jeden Plan dieser Phase

ruff-Vollregelsatz, pyright basic mit `PYRIGHT_PYTHON_FORCE_VERSION=latest`, vulture, alles ueber
`uv run` aus `backend/`, lokal gruen vor dem Commit.

---

## No Analog Found

| Datei / Mechanik | Rolle | Datenfluss | Grund |
|---|---|---|---|
| Die Rangprobe ueber mehrere Koerperfelder (`test_field_plan_ranking.py`) | test / Messprobe | - | Im Baum prueft kein Test eine BM25-Reihenfolge, die aus der Summierung ueber Felder entsteht. `test_search_library.py:276-282` haelt eine Reihenfolge fest, aber gegen sich selbst (`_unfiltered_order`), nicht gegen eine erwartete. Die Form der Probe kommt aus RESEARCH Pattern 3 und die Zahlen aus Messung M-3; die **Bauart** (Aussage plus Gegenprobe, Modulkopf mit Messtabelle) kommt aus `test_rrf_fusion.py` und `index/writer.py:1-49`. |
| Das Wachsen einer eingefrorenen Messfixture (`chain_cases_it.txt`) samt Nachziehen von Zaehlgate und Bericht | test-fixture / Messeingabe | - | Die vier Fixtures sind am 2026-09-23 einmal geschrieben und seither nicht bewegt worden. Es gibt kein Vorbild fuer den Vorgang, nur die Reihenfolgeregel im Kommentar von `test_language_analyzers.py:425-435`. Der Plan nimmt diese Regel als Schrittfolge und erfindet keine zweite. |

Fuer beide gilt: der Planer nimmt das Muster aus RESEARCH.md und nicht aus dem Baum, aber die
**Form** (Modulkopf mit Messabsaetzen, Gegenprobe zu jeder Aussage, Logregel, Gate-Bauart) kommt
weiterhin aus den oben benannten Analoga.

---

## Metadata

**Suchraum:** `backend/src/findling/**`, `backend/tests/**`, `php/lib/**`,
`.github/workflows/deploy-harp.yml`, `docs/**`
**Dateien gescannt:** 12 Python-Module des Pakets (gezielt gelesen), 9 Testmodule, 1 Workflow
(4369 Zeilen, vier Abschnitte gelesen), 2 PHP-Dateien, 2 Dokumentationsseiten
**Nicht gelesen und bewusst nicht als Analog gefuehrt:** `embed/*`, `extract/*`, `nc/*`,
`worker/reconcile.py`, `index/fusion.py`, weil keine Datei dieser Phase in ihre Rolle faellt
**Beim Kartieren geklaert:** RESEARCH-Annahme A4 (PHP-Seite unveraendert), siehe Vorbemerkung
**Extraktionsdatum:** 2026-09-24
**Gueltigkeit:** solange keine der zitierten Dateien bewegt wird. Alle Zeilennummern sind erneut zu
pruefen, sobald ein Plan dieser Phase eine der Dateien geaendert hat; `query/rewrite.py`,
`api/resources.py` und `test_schema_generations.py` bewegen sich in dieser Phase garantiert.
