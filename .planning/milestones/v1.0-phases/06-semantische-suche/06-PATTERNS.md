# Phase 6: Semantische Suche - Pattern Map

**Gemappt:** 2026-09-04
**Analysierte Dateien (neu/geändert):** 27
**Analoga gefunden:** 25 / 27

Diese Datei beantwortet genau eine Frage: **von welcher existierenden Datei soll
jede neue Datei ihr Muster abschreiben?** Sie trifft keine Entscheidungen (die
stehen in 06-CONTEXT.md D-01..D-21) und wiederholt keine Recherche (die steht in
06-RESEARCH.md). Alle Zeilennummern sind am 04.09.2026 gelesen.

---

## File Classification

### Neue Dateien

| Neue Datei | Rolle | Datenfluss | Nächstes Analog | Match |
|---|---|---|---|---|
| `backend/src/findling/embed/__init__.py` | package-init | - | `backend/src/findling/index/__init__.py` | exakt |
| `backend/src/findling/embed/model.py` | service (Engine-Wrapper) | transform (Text -> Vektor) | `backend/src/findling/extract/ocr.py` | exakt |
| `backend/src/findling/embed/chunker.py` | utility (pure) | transform (Text -> Spans) | `backend/src/findling/index/search.py::char_ranges` | rolle |
| `backend/src/findling/embed/bench.py` | tool (Messung A/B/C) | batch | `backend/src/findling/index/bench.py` | exakt |
| `backend/src/findling/store/vectors.py` | store/repository (Abstraktionsschnitt D-08) | CRUD + KNN | `backend/src/findling/store/repo.py` | exakt |
| `backend/src/findling/store/vectors.sql` | schema/config | - | `backend/src/findling/store/schema.sql` | exakt |
| `backend/src/findling/index/fusion.py` | utility (pure, RRF) | transform (2 Ranglisten -> 1) | `backend/src/findling/index/search.py::char_ranges` | rolle |
| `backend/tests/test_embed_model.py` | test | transform | `backend/tests/test_ocr.py` | exakt |
| `backend/tests/test_chunker.py` | test | transform | `backend/tests/test_snippet_offsets.py` | exakt |
| `backend/tests/test_vector_store.py` | test | CRUD | `backend/tests/test_store_repo.py` | exakt |
| `backend/tests/test_rrf_fusion.py` | test | transform | `backend/tests/test_search_library.py` | exakt |
| `backend/tests/test_semantic_search.py` | test (ACL + Degradieren) | request-response | `backend/tests/test_acl_prefilter.py` + `test_search_endpoint.py` | exakt |
| `backend/tests/test_embedding_track.py` | test (Zweitspur) | event-driven | `backend/tests/test_poller.py` (OCR-Handover-Fälle) | exakt |
| `docs/embeddings.md` | doc | - | `docs/ocr.md` | exakt |
| `docs/measurements/2026-09-XX-welle0-arm64/README.md` | doc (Messbericht) | - | `docs/measurements/2026-09-04-volllauf-cpx22/README.md` | exakt |
| `scripts/dev/quantize_model.py` (Bauschritt D-02/D-06) | tool | file-I/O | `scripts/dev/measure_wordlist.sh` + Dockerfile-Fail-Closed-Block | rolle |

### Geänderte Dateien

| Geänderte Datei | Rolle | Datenfluss | Muster kommt aus | Match |
|---|---|---|---|---|
| `backend/src/findling/index/search.py` (`candidates`, `snippets_for`) | read-side | request-response | sich selbst (Schleifenform + Vorfilter-Position) | in-place |
| `backend/src/findling/index/writer.py` (`add`, `drop_document`) | write-side | CRUD | sich selbst (Delete-vor-Insert Z. 224) | in-place |
| `backend/src/findling/store/repo.py` (`_connect`, `SCHEMA_VERSION`, `tombstone`, `reset_for_reindex`) | store | CRUD | sich selbst | in-place |
| `backend/src/findling/store/schema.sql` | schema | - | sich selbst (`acl`-Tabellenblock) | in-place |
| `backend/src/findling/config.py` | config | - | OCR-Block + `SEARCH_OFFSET_MAX` | in-place |
| `backend/src/findling/api/resources.py` (`expected_marks`) | read-side cache | - | sich selbst | in-place |
| `backend/src/findling/api/status.py` (zweiter Deckungsgrad, D-16) | controller | request-response | sich selbst (`StatusResponse`, `_of`) | in-place |
| `backend/src/findling/api/diagnose.py` (Herkunftsmarkierung, D-14) | controller | request-response | sich selbst | teilweise |
| `backend/src/findling/worker/poller.py` (Embedding-Zweitspur, D-15) | worker | event-driven | `_read_the_scan` / `_goes_to_the_ocr_track` / `_hand_over` | in-place |
| `backend/src/findling/nc/queue.py` (`KIND_EMBED`) | client/constants | event-driven | `KIND_OCR` (Z. 63-68) | in-place |
| `php/lib/Db/QueueMapper.php` (`KIND_EMBED`, LOCK_TIMEOUTS, KIND_RANK) | model/constants | event-driven | `KIND_OCR`-Zeilen | in-place |
| `php/lib/Service/QueueService.php` (`KIND_BATCH`) | service | event-driven | `KIND_OCR => 2` (Z. 108) | in-place |
| `php/lib/Service/AdminViewService.php` (zweite Deckungszahl) | service | request-response | `coverage()` Z. 1313-1350 | in-place |
| `php/templates/admin.php` | template | - | bestehender Coverage-Block | in-place |
| `backend/pyproject.toml` + `uv.lock` | config | - | `pillow`-Kommentarmuster Z. 22-28 | in-place |
| `backend/Dockerfile` | config/build | file-I/O | wngerman-/tesseract-Block (fail-closed) | in-place |
| `THIRD-PARTY.md` | doc | - | OCR-Abschnitt | in-place |

---

## Pattern Assignments

### 1. `backend/src/findling/store/vectors.py` (store, CRUD + KNN)

**Analog:** `backend/src/findling/store/repo.py`
**Warum:** Der Kopfkommentar von repo.py macht "die eine Datei mit SQL" zur
Architekturaussage. D-21 verlangt, dass aller vec0-SQL derselben Disziplin folgt.
`vectors.py` ist das Geschwistermodul unter `store/`, nicht ein SQL-Zweig im
Vektorcode.

**Modul-Kopf-Muster** (`repo.py` Z. 1-28, gekürzt):
```python
"""The one module in Findling that contains SQL.
...
This module deliberately does not import ``findling.config``. Every path arrives
as an argument, which keeps the store testable without an environment and lets
the callers decide where their database lives.
"""
```
-> `vectors.py` erbt diese zwei Eigenschaften wörtlich: kein `config`-Import, Pfad
als Argument. Das ist auch die Voraussetzung dafür, dass Claude's-Discretion-Frage
"eigene vectors.db oder state.db" später ohne Umbau kippbar bleibt.

**Schema-Artefakt statt String-Literal** (`repo.py` Z. 44 + Z. 1142):
```python
_SCHEMA_FILE: Final = Path(__file__).with_name("schema.sql")
...
connection.executescript(_SCHEMA_FILE.read_text(encoding="utf-8"))
```
-> `vectors.sql` neben `vectors.py`, jede Anweisung `IF NOT EXISTS`, auf jedem
Start anwendbar.

**Verbindungsmuster, das erweitert werden muss** (`repo.py` Z. 427-456):
```python
def _connect(path: Path, *, read_only: bool) -> sqlite3.Connection:
    connection = sqlite3.connect(path, autocommit=True, check_same_thread=False)
    connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
    connection.execute("PRAGMA foreign_keys = ON")
    if read_only:
        connection.execute("PRAGMA query_only = 1")
    else:
        connection.execute("PRAGMA synchronous = NORMAL")
    return connection
```
-> Hier fehlt `enable_load_extension` (06-RESEARCH 1.2). Die Probe A12 (vec0-KNN
unter `query_only = 1`) entscheidet, ob der Lesezweig diese Zeile behalten kann.
Der Kommentar zu `check_same_thread=False` (Z. 434-445) erklärt, warum
`asyncio.to_thread` erlaubt ist; derselbe Satz gilt für den Embedding-Schreibweg.

**Transaktionsmuster** (`repo.py` Z. 527-536):
```python
@contextmanager
def _transaction(self) -> Iterator[None]:
    """One explicit transaction. Validation belongs before it, never inside."""
    self._conn.execute("BEGIN IMMEDIATE")
    try:
        yield
    except BaseException:
        self._conn.execute("ROLLBACK")
        raise
    self._conn.execute("COMMIT")
```

**Der Löschweg-vor-Schreibweg (D-21), wörtliches Vorbild** (`repo.py` Z. 908-920):
```python
def replace_acl(self, file_id: int, uids: Iterable[str]) -> None:
    """Write the permissions of one file as a whole, never as a change.

    DELETE followed by INSERT in one transaction. ...
    """
    rows = [(uid, file_id) for uid in dict.fromkeys(uids)]
    with self._transaction():
        self._conn.execute("DELETE FROM acl WHERE file_id = ?", (file_id,))
        self._conn.executemany("INSERT INTO acl (uid, file_id) VALUES (?, ?)", rows)
```
-> `replace_chunks(file_id, chunks)` ist exakt diese Form: `DELETE FROM chunks
WHERE file_id = ?` plus Löschung der vec0-Zeilen, dann `executemany`. Damit ist
Fallstrick 5 (Chunk-Dubletten nach Wiederzustellung) strukturell erledigt.

**Bandung langer ID-Listen** (`repo.py` Z. 79 + Z. 953-963) fuer den Rueckweg
chunk_id -> file_id:
```python
_ACL_BAND: Final = 1000
...
for start in range(0, len(file_ids), _ACL_BAND):
    band = file_ids[start : start + _ACL_BAND]
    placeholders = ",".join("?" * len(band))
    rows = self._conn.execute(
        # The parameters are placeholders, all of them. Only their number
        # is interpolated, and it is a count this function computed.
        f"SELECT file_id FROM acl WHERE uid IN (?, ?) AND file_id IN ({placeholders})",  # noqa: S608
        (uid, ACL_ANY_USER, *band),
    )
```
-> Das `noqa: S608` samt Begründungskommentar ist der einzige im Projekt
akzeptierte Weg, eine Platzhalterzahl zu interpolieren. Abschreiben, nicht neu
erfinden.

**Namensverbot beachten:** `writer.py` Z. 251-253 nennt es ausdrücklich, Gate A
verbietet den Bezeichner `delete` in jedem Modul dieses Pakets. Also
`drop_vectors` / `forget_chunks`, niemals `delete_vectors`.

---

### 2. `backend/src/findling/store/vectors.sql` (schema)

**Analog:** `backend/src/findling/store/schema.sql`

**Der Tabellenblock, dessen Form zu kopieren ist** (`schema.sql` Z. 74-91):
```sql
-- The prefilter table. It carries no rowid because the composite key *is* the table:
-- an ordinary table would keep a second B-tree on an invisible rowid and pay for
-- it twice, once in space and once on every insert. Measured at 100k files and
-- 50 users: 335515 rows, 12.0 MB, 0.18 ms for a prefilter over 400 candidates.
--
-- No foreign key to files on purpose. ...
CREATE TABLE IF NOT EXISTS acl (
    uid     TEXT    NOT NULL,
    file_id INTEGER NOT NULL,
    PRIMARY KEY (uid, file_id)
) WITHOUT ROWID;

-- The delete path asks by file_id, which the composite key cannot answer: its
-- leading column is uid. Without this index, forgetting one file would scan the
-- whole table.
CREATE INDEX IF NOT EXISTS acl_file ON acl (file_id);
```
-> Muster: jede Tabelle traegt (a) den gemessenen Grössenbeleg, (b) die Begründung
für fehlende Fremdschlüssel, (c) den Index mit dem Satz, welcher Zugriffspfad ihn
braucht. Für `chunks` ist das der Löschweg `chunks_file ON chunks (file_id)`
(06-RESEARCH 1.2).

**Die meta-Marke braucht keine Migration** (`schema.sql` Z. 19-27):
```sql
-- The version marks. Every one of them can invalidate the Tantivy index on its
-- own: schema_version, index_version, analyzer_version, wordlist_hash,
-- tantivy_version, plus instance_id and created_at for provenance. Their names
-- are open on purpose, because phase 6 adds an embedding version and must not
-- need a migration to do so.
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```
-> `embedding_version` wird über `store.write_meta()` gesetzt, kein DDL.

---

### 3. `backend/src/findling/embed/model.py` (service, Engine-Wrapper)

**Analog:** `backend/src/findling/extract/ocr.py`
**Warum:** Das ist der einzige existierende Wrapper um eine schwere, externe,
gedeckelte Rechenmaschine im Schreibweg. Die Parallelen sind eins zu eins:
Modelldatei im Abbild statt Download, Caps aus `config.py`, Messprotokoll in
`docs/`, und ein Ausfall ist ein Verdikt, keine Exception.

**Modul-Kopf-Muster** (`ocr.py` Z. 1-37, gekürzt):
```python
"""Text out of a scan, with four caps deciding when a long document becomes a part.
...
**The cap cascade, and why its order is the whole statement.** Three caps end the
page loop and keep what was read, two end the job:
...
The numbers themselves are in :mod:`findling.config`, measured, with the full table
and the measurement protocol in ``docs/ocr.md``.

**What is deliberately not in here.** No decision about whether a file belongs in
the OCR track: that is made where the text layer is measured...

Like every module of this package, this one never writes: the engine answers on a
pipe, no page is ever put on disk, and the original file is not touched even on
the error path (IDX-07, T-03-805).
"""
```
-> `embed/model.py` schreibt denselben Kopf: die Caps (1.024-Token-Deckel D-01,
Chargengröße, Sequenzlänge) stehen in `config.py`, das Messprotokoll in
`docs/embeddings.md`, und was hier ausdrücklich NICHT passiert ist die
Entscheidung, ob eine Datei in die Embedding-Spur gehört (die faellt im poller,
Muster `_goes_to_the_ocr_track`).

**Binärabhängigkeit ohne harten Pfad** (`ocr.py` Z. 52-55):
```python
# The binary, by name and not by path. Which directory it lives in is a property
# of the image and of the distribution, and a hard coded path would make the
# honest ocr_unavailable verdict below depend on that path staying true.
```
-> Dasselbe Argument gilt für die gebackene ONNX-Datei und die sqlite-vec-`.so`:
ein Pfad aus `settings()`, und ein fehlendes Modell erzeugt ein ehrliches
"embedding_unavailable"-Verdikt statt einer Exception (D-19).

**Import- und Konfigurationsmuster** (`ocr.py` Z. 40-56):
```python
from __future__ import annotations

import os
import subprocess
import time
from typing import Final

import pypdfium2

from findling import config
from findling.config import Settings
from findling.extract import raster
from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason
```

**E5-Präfixe (D-05):** hierfür gibt es kein Analog im Bestand. Das Muster, dem
sie folgen sollen, ist die Allowlist-Konstante aus `config.py` Z. 213
(`OCR_LANGUAGE_ALLOWLIST = frozenset({"deu", "eng"})`) plus der Paritätstest, der
sie gegen die andere Seite prüft: zwei `Final`-Konstanten `QUERY_PREFIX = "query: "`
und `PASSAGE_PREFIX = "passage: "` im Modul, und der Rangtest in
`tests/test_embed_model.py`.

---

### 4. `backend/src/findling/embed/chunker.py` und `backend/src/findling/index/fusion.py` (pure utilities)

**Analog:** `backend/src/findling/index/search.py::char_ranges` (Z. 208-265)
**Warum:** Das ist das Projektmuster für "reine Funktion, die neben der Suche
lebt, damit sie mit ein paar Zahlen statt mit einem ganzen Index geprüft werden
kann". Beide neuen Funktionen sind genau das: Chunk-Spans aus Text, und zwei
Ranglisten in eine.

**Die Form, wörtlich** (`search.py` Z. 208-227, gekürzt):
```python
def char_ranges(fragment: str, ranges: Sequence[ByteRange]) -> list[tuple[int, int]]:
    """Convert byte ranges of a fragment into character ranges, merged and sorted.

    Two separate corrections happen here, and both are measured rather than
    assumed.
    ...
    A pure function, and it lives next to the search rather than in the endpoint
    so that it can be tested with a fragment and two numbers.
    """
```

**Das Byte-gegen-Zeichen-Argument gilt für `char_start`/`char_end` (D-13) direkt**
(`search.py` Z. 214-220):
```
The engine counts UTF-8 bytes while the wire protocol of this project
promises characters. Measured on a German sentence: the engine reports
(35, 51) where the character range is (35, 50), so a naive slice takes one
character too many and every umlaut in front of the match shifts the
highlight further. The text stays correct, only the marking moves, which is
why this bug survives review and testing so reliably.
```
-> `semantic-text-splitter` arbeitet auf Zeichen (Rust/str), der gespeicherte
`body_de` ist ein Python-`str`. `char_start`/`char_end` sind ZEICHEN, nicht Bytes.
Genau diese Verwechslung ist im Projekt schon einmal gemessen worden; der
Chunker-Test muss sie mit einem Umlaut-Satz festnageln.

**Protokoll statt Fremdtyp** (`search.py` Z. 179-191):
```python
class ByteRange(Protocol):
    """The two numbers a highlighted range consists of.

    Written as a protocol rather than as the engine's own type so that the pure
    conversion below can be exercised with a handful of numbers instead of a
    whole index.
    """
    @property
    def start(self) -> int: ...
    @property
    def end(self) -> int: ...
```
-> `fusion.py` nimmt zwei `Sequence[int]` (Ranglisten von file_ids) und gibt eine
`list[tuple[int, float]]`, ohne `tantivy`- oder `sqlite`-Typen zu kennen. Damit
ist der RRF-Test ein Test mit zwölf Zahlen und ohne Index.

**Der rank-beginnt-bei-1-Fehler (D-12)** hat kein Analog; er gehört als
Kommentarzeile über die Formel und als eigener Testfall in `test_rrf_fusion.py`,
nach dem Muster des `<` gegen `<=`-Kommentars in `search.py` Z. 255-260:
```python
for start, end in spans:
    # Strictly less, and that is the whole distinction. ...
    # The earlier form compared with <= and turned two neighbouring hits into one mark.
    if merged and start < merged[-1][1]:
```

---

### 5. `backend/src/findling/index/search.py::candidates()` (geändert, D-20)

**Analog:** die Funktion selbst, Z. 92-176. Das ist die einzige Stelle, an der
verschmolzen werden darf, und sie ruft den Vorfilter selbst.

**Die Schleifenform, die sich ändern muss** (Falle A, Z. 114-165):
```python
searcher = index.searcher()
# One permitted hit more than the page needs, and it only ever becomes a
# boolean. It replaces the engine's total: a total counts documents BEFORE
# the permission filter, so comparing against it told whoever varies offset
# and limit how many documents of other people match a term (a counting
# oracle, T-02-93).
needed = offset + limit + 1
permitted: list[Candidate] = []
raw_cursor = 0
scan_cap = SEARCH_SCAN_MAX

while len(permitted) < needed and raw_cursor < scan_cap:
    chunk_limit = min(max(needed, _SCAN_CHUNK_MIN), scan_cap - raw_cursor)
    result = searcher.search(query, chunk_limit, offset=raw_cursor)
    ...
    # From the candidates to the permissions, never the other way round.
    visible = store.prefilter_visible(uid, [file_id for file_id, _, _ in ranked])
    permitted.extend(
        Candidate(file_id=file_id, score=score, mtime=mtime)
        for file_id, score, mtime in ranked
        if file_id in visible
    )
```

**Die drei Eigenschaften, die den Umbau überleben müssen** (alle in dieser Datei
begründet, nicht in der Roadmap):

1. **Offset zählt erlaubte Kandidaten** (Kopfkommentar Z. 15-20 und Z. 100-113):
```
*Offsets count permitted candidates, not engine hits.* An offset in engine-hit
space tells whoever varies it how many documents of other people match a term:
the gap between two raw cursors minus the candidates delivered in between is a
count of foreign documents, page by page (the counting oracle of T-02-93). So the
cursor that crosses the process boundary counts only what the caller was allowed
to see, and the raw cursor stays inside this function.
```
2. **Kein Total** (Z. 78-89, `CandidatePage`): `has_more` ist alles, was den
   Prozess verlässt.
3. **Der Deckel** (Z. 167-169): ein erreichter Deckel antwortet ehrlich mit
   `has_more=False` plus einer Logzeile ohne Query und ohne Zahlen:
```python
if len(permitted) < needed and raw_cursor >= scan_cap:
    # Only the fact, never the query or the counts: both are content.
    LOGGER.info("the candidate scan hit its raw ceiling and answered a truncated page")
```
-> Die Vektorseite braucht ihren eigenen Deckel nach diesem Muster
(06-RESEARCH, Security Domain, DoS-Zeile), Konstante nach dem Vorbild von
`SEARCH_SCAN_MAX` in `config.py` Z. 160-166.

**Der eigene try/except für den Vektorzweig (D-19)** hat sein Vorbild eine Ebene
höher, aber ausdrücklich NICHT dessen Reichweite (`api/search.py` Z. 187-203):
```python
try:
    side = resources.read_side()
    ...
    page = candidate_round(side.index, side.store, uid, rewritten.query, limit, offset)
# Deliberately every exception, for the reason in the docstring above.
except Exception as error:
    # The type name and nothing else: a traceback carries whatever a library
    # put into its message, and the search text is the usual content.
    LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
    return _Round([], False, offset, True)
```
-> Der Vektor-`except` liegt INNERHALB von `candidates()`, gibt eine leere
Vektorliste zurück und loggt nach genau diesem Muster: **nur der Typname**, nie
die Meldung, nie die Anfrage. Fällt der Fehler stattdessen bis hierher durch,
ist die Antwort leer und Kriterium 3 verletzt (Fallstrick 4).

---

### 6. `backend/src/findling/index/search.py::snippets_for()` (geändert, D-13)

**Analog:** die Funktion selbst, Z. 277-321.

**Die Reihenfolge, die nicht verhandelbar ist** (Z. 284-301):
```python
    """Cut one text excerpt per confirmed file id, in the order they were asked for.

    The prefilter runs as the first action of this function, before a single byte
    of text is read. Without it this path would be a confused deputy: a snippet is
    file content, and whoever reaches the proxy could otherwise ask for the
    content of any document by its id. ...
    """
    visible = store.prefilter_visible(uid, file_ids)
    if not visible:
        return []
```
-> Der Chunk-Ausschnitt aus `char_start`/`char_end` entsteht NACH dieser Zeile,
im selben Schleifenkörper wie der bestehende Generator-Ausschnitt.

**Der Fallback-Satz, der zum Normalfall wird** (Z. 295-297 + Z. 309-321):
```python
    A document the index does not know is skipped. A document the query does not
    match inside the text field yields an empty excerpt rather than an error: a
    hit without a snippet is still a hit, and the subline falls back to the path
    on the PHP side.
    """
...
    for file_id in file_ids:
        if file_id not in visible:
            continue
        document = _document_for(index, file_id)
        if document is None:
            continue
        snippet = generator.snippet_from_doc(document)
        fragment = snippet.fragment()
        excerpts.append(
            SnippetText(file_id=file_id, text=fragment, highlights=char_ranges(fragment, snippet.highlighted()))
        )
```
-> Die Ergänzung: ist `fragment` leer und liegt ein Rang-Chunk für diese file_id
vor, wird der Ausschnitt aus dem gespeicherten `body_de` geschnitten
(`highlights=[]`, denn es gibt keine wörtliche Übereinstimmung zu markieren).
Der Zugriff auf den gespeicherten Text folgt `writer.py::stored_body` (Z. 266-299),
das den `body_de`-Wert bereits genau so ausliest.

---

### 7. `backend/src/findling/index/writer.py` (geändert, D-21)

**Analog:** `add()` Z. 210-249, `drop_document()` Z. 251-264.

**Delete-vor-Insert, das Vorbild für den Vektor-Schreibweg** (Z. 210-224):
```python
def add(self, record: IndexRecord) -> None:
    """Write one file into the pending batch, replacing an earlier version.

    The deletion before the insert is what makes a second run harmless: the
    queue redelivers a batch that was interrupted after the commit and before
    the acknowledgement, and without the deletion that redelivery would leave
    the same file in the index twice.
    """
    writer = self._require_open()
    # Through the schema, so the term carries the type of the field. ...
    writer.delete_documents_by_query(Query.term_query(self._schema, FIELD_FILE_ID, record.file_id))
```

**Der Name** (Z. 251-259):
```python
def drop_document(self, file_id: int) -> None:
    """Take one file out of the index; an unknown id is not an error.

    Named drop_document because gate A forbids the identifier ``delete`` in
    every module of this package, ...
    """
```

**Die Chargen-Grenze als Absturzgranularität** (Modulkopf Z. 17-22 + `flush`
Z. 301-330): Der Vektor-Commit gehört in dieselbe Charge wie der
Tantivy-Commit, sonst gibt es zwei Absturzgranularitäten, die nach einem
`docker kill` auseinanderliegen. `flush()` prüft zuerst den freien Plattenplatz
und gibt `FLUSH_PAUSED_LOW_DISK` zurück, bevor irgendetwas geschrieben wird; ein
Vektorschreibvorgang darf diesen Zustand nicht umgehen.

---

### 8. `backend/src/findling/worker/poller.py` (geändert, D-15: die Zweitspur)

**Analog:** die OCR-Zweitspur in derselben Datei. Drei Bausteine, alle drei zu
kopieren.

**(a) Der Verteiler** (`_goes_to_the_ocr_track`, Z. 734-771):
```python
def _goes_to_the_ocr_track(self, outcome: ExtractionOutcome) -> bool:
    """True when this verdict becomes an OCR job instead of an end state.
    ...
    **With OCR switched off nothing changes.** An instance whose admin set
    ``FINDLING_OCR_ENABLED=false`` gets the honest verdict rather than rows
    that wait forever for a track that does not exist there.
    ...
    """
    if outcome.state is not State.SKIPPED or outcome.reason is not Reason.NO_TEXT_LAYER:
        return False
    return self._ocr_enabled
```
-> `_goes_to_the_embedding_track(outcome)` prüft `outcome.state is State.INDEXED`
und den Schalter. Der Satz "mit abgeschaltetem Schalter wartet keine Zeile auf eine
Spur, die es dort nicht gibt" gilt wörtlich für die Semantik.

**(b) Der Handover, nach dem Commit und vor der Quittierung** (`run_once`,
Z. 475-488):
```python
        # 3b. The handover to the OCR track, after the commit and before the
        #     acknowledgement. An abort right here costs one repeated text layer
        #     check and nothing else: the rows were not acknowledged, so they come
        #     back after the lock timeout and are handed over again. The reverse
        #     order would delete the row in the same pass in which the requeue put
        #     work on it, and the scan would never be read.
        requeued = await self._hand_over(queue, handover)

        # 4. The acknowledgement, the last step by construction. ...
        ack = await queue.acknowledge(done, failed, _skip_verdicts(verdicts, handover))
```

**(c) Der Ausfall ist eine Zahl, nie eine Ausnahme** (`_hand_over`, Z. 773-787):
```python
async def _hand_over(self, queue: DocumentQueue, file_ids: Sequence[int]) -> int:
    """Move the rows of this pass to the OCR track, and count what moved.

    A failure is a number and never an exception: the rows stay claimed, run
    into the lock timeout and are handed over by a later pass. The pass
    itself has to finish, because index and verdicts are already durable.
    """
    if not file_ids:
        return 0
    result = await queue.requeue(file_ids, kind=KIND_OCR)
    if not result.ok:
        LOGGER.warning("could not move %d files to the OCR track, they run into the lock timeout", len(file_ids))
        return 0
    return result.count
```

**(d) Der zweite Spurzweig selbst** (`_read_the_scan`, Z. 669-732) ist das
strukturelle Vorbild für `_embed_the_body`, mit einem entscheidenden Unterschied,
der ausdrücklich zu kommentieren ist: die OCR-Spur lädt die Datei erneut
(`self._fetch_file(job)`, Z. 698), die Embedding-Spur tut das NICHT (D-15,
Backfill aus dem gespeicherten `body_de`). Der Text kommt aus
`writer.py::stored_body(file_id)` (Z. 266-299), dessen Docstring genau dieses
Argument bereits führt:
```python
    This method is the reason a rename costs no download. ``body_de`` is the
    only stored copy of the extracted text in the whole system, the same copy
    the snippet generator already cuts from, so a file that was renamed can be
    written again from what the index holds: no gateway call, no scratch file,
    no extraction, no OCR.
```
-> Das ist der Satz, den `_embed_the_body` erbt. Und der `reload()`-Kommentar
darüber (Z. 288-292) ist der Grund, warum ein Embedding-Job aus demselben
Durchgang den Text schon sieht.

**(e) Kein zweiter Umlauf** (Z. 728-732):
```python
    # No handover, whatever came back. This row was the handover, and putting
    # it on the track again is the endless loop of T-03-704 from the other
    # side.
```

---

### 9. `backend/src/findling/nc/queue.py` und die PHP-Warteschlange (KIND_EMBED)

**Analoga:** `queue.py` Z. 63-68, `QueueMapper.php` Z. 50-72 / 107-112 / 127ff,
`QueueService.php` Z. 103-108.

**Python** (`queue.py` Z. 63-68):
```python
KIND_CONTENT: Final = "content"
KIND_METADATA: Final = "metadata"
KIND_DELETE: Final = "delete"
KIND_ACL: Final = "acl"
KIND_OCR: Final = "ocr"
KINDS: Final = frozenset({KIND_CONTENT, KIND_METADATA, KIND_DELETE, KIND_ACL, KIND_OCR})
```

**PHP, vier Stellen in einer Änderung** (`QueueMapper.php`):
```php
public const KIND_OCR = 'ocr';           // Z. 54
public const KINDS = [ ... self::KIND_OCR ];              // Z. 67-72
public const LOCK_TIMEOUTS = [ ... self::KIND_OCR => 1800 ];  // Z. 107-112
private const KIND_RANK = [ ... ];       // Z. 127ff, die Aufstiegsordnung
```
**und** (`QueueService.php` Z. 103-108):
```php
private const KIND_BATCH = [
    QueueMapper::KIND_ACL => 128,
    QueueMapper::KIND_DELETE => 128,
    QueueMapper::KIND_METADATA => 64,
    QueueMapper::KIND_CONTENT => 32,
    QueueMapper::KIND_OCR => 2,
];
```
**Das Paritätsband zwischen beiden Seiten** (`config.py` Z. 246-252):
```python
# The two PHP-side numbers the job ceiling below is derived from, mirrored here
# because a PHP constant cannot be imported: QueueMapper::LOCK_TIMEOUTS[ocr] and
# QueueService::KIND_BATCH[ocr]. A parity test in tests/test_config.py reads
# both out of the PHP sources and goes red the day one of them moves, the same
# construction that holds the two mimetype allowlists together.
OCR_LOCK_TIMEOUT_SECONDS = 1800
OCR_CLAIM_BATCH = 2
```
-> Für `embed` denselben Spiegel plus Paritätstest anlegen. Ohne ihn driften die
Chargengröße der Embedding-Spur und ihr Lock-Timeout lautlos auseinander, und das
Ergebnis ist wortwörtlich der `failed(repeatedly_stuck)`-Fehler aus T-03-503.

---

### 10. `backend/src/findling/config.py` (geändert: Deckel, semantisches Gewicht, RRF)

**Analog A, der DoS-begründete Deckel** (Z. 152-158):
```python
# Upper bound of the paging offset a caller may request (security audit C1). The
# endpoints carry access_level USER, so any signed-in account reaches them with a
# free JSON body; the offset sizes the page the candidate scan has to fill, and
# an unbounded one would turn a single request into an unbounded amount of work.
SEARCH_OFFSET_MAX = SEARCH_LIMIT_MAX * SEARCH_OVERFETCH * SEARCH_ROUNDS
```

**Analog B, der Schalter mit Vorgabe an** (Z. 194-197):
```python
# OCR is on out of the box, because "the search finds the content of scanned
# documents" is the core promise of the product and a feature an admin has to
# discover is a feature that is off on most instances.
OCR_ENABLED = True
```

**Analog C, die Bereichsprüfung** (Z. 388-401):
```python
def _bounded_int_from_environment(name: str, default: int, bounds: tuple[int, int]) -> int:
    """Read a whole number that also has to fall inside a measured range.

    Same contract as the reader above, one condition more. A number that is
    positive but absurd is not obviously a typo to a parser and is very much one
    in practice: ...
    """
    value = _int_from_environment(name, default)
    low, high = bounds
    if low <= value <= high:
        return value
    LOGGER.warning("%s is outside the range this build was measured for, falling back to the default", name)
    return default
```
-> Der 1.024-Token-Deckel (D-01) und das semantische Gewicht (D-12) gehen durch
diese Funktion, mit einem `*_RANGE`-Tupel daneben. Ein Gleitkommagewicht braucht
einen `_bounded_float_from_environment` nach exakt diesem Bauplan; das
Warnverhalten (nie ein Startabbruch, immer der eingebaute Vorgabewert) ist die
Modulregel, siehe `_bool_from_environment` Z. 432-446.

**Analog D, die Settings-Struktur** (Z. 317-358):
```python
@dataclass(frozen=True, slots=True)
class Settings:
    """The resolved caps and paths of one process.

    Frozen on purpose: a cap that can be reassigned at runtime is a cap that
    differs between two call sites, and the whole point of this module is that
    it cannot.
    """
    ...
    ocr_enabled: bool
    ocr_languages: tuple[str, ...]
    ocr_max_pages: int
```
-> Ein `embed_`-Block in derselben Reihenfolge, plus die entsprechenden Zeilen in
`settings()` (Z. 531-585). `test_config.py` hat für jeden OCR-Wert genau einen
Test (Z. 208-395); dieselbe Dichte gilt für die neuen Werte.

**Die Zeile, die Phase 6 bereits erwartet** (Z. 52-57), und die dabei zu prüfen ist:
```python
# IDX-08. One indexing worker, always. OCR peaks at 300 to 600 MB for a single
# 300 dpi A4 page and the embedding model adds 250 to 400 MB; on the 4 GB box
# this project targets, those two peaks must never be allowed to meet. This is
# not a tuning knob and deliberately reads no environment variable, so that
# making it one is a code change somebody has to defend in review.
INDEX_WORKERS = 1
```
-> Die 250 bis 400 MB sind eine Schätzung vom Baubeginn. Nach Messung B/der
RSS-Neubelegung (D-17c) gehört die gemessene Zahl hierher.

---

### 11. `backend/src/findling/api/status.py` (geändert, D-16: zweite Deckungszahl)

**Analog:** dieselbe Datei, `StatusResponse` Z. 79-132 und `_of` Z. 203-239.

**Feldmuster mit Vorgabewert und Begründung** (Z. 88-101):
```python
    indexed: int = 0
    # Contained in indexed above and never added next to it: a truncated
    # document is indexed, it is just indexed at the front only. D-08 of phase 3
    # asks for the number because "indexed" would otherwise be read as a promise
    # this container never made about the end of a long document.
    truncated: int = 0
```
-> Genau diese Kommentarform für `embedded: int = 0`: enthalten in `indexed`,
niemals daneben addiert, und die Zahl existiert, weil "indexiert" sonst als ein
Versprechen über die Semantik gelesen wird, das dieser Container nicht gegeben hat.

**Kein Zeilen-Spread** (Z. 203-215):
```python
def _of(store: Store, volume: StatusResponse) -> StatusResponse:
    """Read every number out of one open state database.

    Every field is named. Nothing here spreads a row of ``files`` into the
    answer, however convenient that would be on the day somebody adds a column:
    that table carries ``path`` and ``title``, and a spread would put both on the
    wire in the same commit that meant to add a counter (T-04-06).
    """
```

**Der Fehlerpfad** (Z. 262-277): `sqlite3.Error` neben `OSError`, Antwort ist ein
Zustand mit `note`, niemals ein 500. Eine fehlende oder nicht ladbare
Vektordatenbank ist derselbe Fall.

**PHP-Gegenstück** (`AdminViewService.php` Z. 1313-1350):
```php
$percent = null;
if ($indexable > 0 && $backendReachable) {
    // Rounded down, and held below a hundred while anything is still
    // missing. A page that says a hundred per cent with files left over
    // is the failure this whole phase exists to make impossible.
    $percent = $indexable - $indexed > 0
        ? min(99, max(0, (int)floor($indexed * 100 / $indexable)))
        : 100;
}
```
-> Die zweite Zahl ist ein zweiter Aufruf derselben privaten Methode mit einem
anderen Zähler, kein zweiter Rechenweg. Der Nenner bleibt `indexable`, und der
`provisional`-Schlüssel (Z. 1342-1348) gilt für die Semantikspur genauso.
`php/tests/Unit/AdminViewServiceTest.php` und
`backend/tests/test_admin_ui_contract.py` halten die Schlüsselmenge fest; beide
gehen rot, wenn ein Schlüssel fehlt.

---

### 12. `backend/src/findling/api/diagnose.py` (geändert, D-14: Herkunftsmarkierung)

**Analog:** dieselbe Datei. **Match nur teilweise**, und das ist zu wissen: die
heutige Route beantwortet "welches Verdikt hat DIESE Datei" (Z. 128-138,
`fileId: int` als Query-Parameter), nicht "warum steht dieses Dokument in dieser
Trefferliste". Die Herkunftsmarkierung braucht entweder einen zweiten
Query-Parameter oder eine zweite Admin-Route. Was in jedem Fall zu kopieren ist:

**Der Antwortvertrag** (Z. 11-15):
```
``textChars`` is the one figure that touches the content, and it is a count and
never the text. A snippet is file content and stays bound to SRCH-02, where it is
only ever built for a hit that already survived the permission recheck. Blurring
that line here is the way an administration tool turns into a content leak, so
there is no text field on this model and there is not going to be one.
```

**Feld für Feld, nie ein Row-Spread** (Z. 112-125):
```python
    # Field by field and never a row spread into the model: the row carries path
    # and title, and a spread would put both on the wire the day somebody adds a
    # field to the table (T-04-40).
    return DiagnoseResponse(
        fileId=file_id,
        state=str(row["state"]),
        reason="" if row["reason"] is None else str(row["reason"]),
        ocrUsed=bool(row["ocr_used"]),
```
-> `embedded: bool` und `chunks: int` reihen sich hier ein. Die
Treffer-Herkunft ("lexikalisch/semantisch/beides") ist dagegen eine Aussage über
eine Suche und nicht über eine Datei; sie gehört an die Verschmelzungsstelle in
`fusion.py` und wird von dort als Zahl gereicht, nie über den Suchweg (D-14).

**Die Gegenprobe, die NICHT verletzt werden darf** (`api/search.py` Z. 96-104):
```python
class Candidate(BaseModel):
    """One hit before the permission recheck: three values, and no fourth.

    Everything that is missing is the point, and a test asserts the field names
    as a set because their absence is invisible in every functional test.
    """
    fileId: int
    score: float = 0.0
    mtime: int = 0
```
-> Der Test, der die Feldmenge als Menge prüft, liegt in
`backend/tests/test_search_endpoint.py` und geht rot, sobald jemand eine
Herkunftsmarkierung in den Suchweg legt. Das ist die strukturelle Absicherung
von D-14; sie ist bereits vorhanden und muss nur bestehen bleiben.

---

### 13. `backend/src/findling/api/resources.py` (geändert: embedding_version)

**Analog:** `expected_marks()` Z. 93-117 und `version_drift()` Z. 120-131.
```python
def expected_marks() -> dict[str, str] | None:
    """The version marks an index built by this code carries, or None.
    ...
    Cached under the directory the list was read from, for the same reason the
    handles below are: one process has one volume, but a suite has one per test,
    and a digest carried over from the previous volume would report a drift that
    does not exist.
    """
```
Plus die Store-Seite (`repo.py` Z. 486-515, `version_mismatch`), deren Docstring
die Regel setzt: "It decides nothing." Ein `embedding_version`-Drift darf keinen
Reindex des Volltextbestands auslösen (D-21: nur additive Schemaänderung); das ist
genau die Sonderbehandlung, die `index_version` heute schon hat (Z. 500-504 und
`_generation_at_least` Z. 1088-1097).

---

### 14. `backend/src/findling/embed/bench.py` (Welle-0-Messungen A/B/C, D-18)

**Analog:** `backend/src/findling/index/bench.py` (368 Zeilen).

**Der Kopf, der das Muster vollständig enthält** (Z. 1-33, gekürzt):
```python
"""What the search costs while the index is being written.
...
So this module measures instead of assuming. Two modes:

* ``idle``: N searches against a resting index.
* ``under-write``: the same N searches while documents are written in the
  background and batch commits go off, plus the number of commits that fell into
  the measurement window.

Both print the median and the p95, the document count and the size of the index
directory. ...

Numbers only, never a token and never a word from a document: this path would see
user content in a production index, and a measurement that prints what it read is
the cheapest way to leak it (T-02-14). The text below is fixed and synthetic.

Run it with::

    uv run python -m findling.index.bench --mode idle --queries 200
"""
```
-> `embed/bench.py` bekommt drei Modi (`chars-per-token`, `tokens-per-second`,
`scan-latency`), druckt p50 und p95, und der T-02-14-Satz gilt wörtlich: Messung A
läuft über echten deutschen Text aus `testdata/`, also darf sie kein Wort davon
ausgeben, nur Zahlen. Der `argparse`-Aufbau und die `statistics`-Nutzung stehen
im Analog ab Z. 36-50.

**Ausführungsort:** die arm64-Läufer aus `.github/workflows/docker.yml` Z. 74-80:
```yaml
          - platform: linux/amd64
            arch: amd64
            runner: ubuntu-24.04
          - platform: linux/arm64
            arch: arm64
            runner: ubuntu-24.04-arm
```
-> `ubuntu-24.04-arm` ist der Läufer, auf dem Messung B und C laufen, ohne die
AWS-Box anzufassen.

---

### 15. `backend/Dockerfile` (geändert: Modell, Quantisierung, .so, HF_HUB_OFFLINE)

**Analog:** der wngerman-Block Z. 73-110 und der tesseract-Block Z. 112-164.
Beide sind exakt das Muster, das D-02/D-06/D-09 verlangen: Daten ins Abbild
gebacken, Version hart gepinnt, Lizenztext mitgeliefert, und ein fail-closed Test
im selben `RUN`.

**Fail-closed Bauprüfung plus Lizenzkopie** (Z. 104-110):
```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends wngerman=20161207-15 \
    && rm -rf /var/lib/apt/lists/* \
    && test -s /usr/share/dict/ngerman \
    && test -s /usr/share/doc/wngerman/copyright \
    && install -D -m 0444 /usr/share/doc/wngerman/copyright \
        /usr/local/share/findling/COPYING.wngerman
```
-> Die Größenprüfung nach der Quantisierung (D-06, Abbruch über ~130 MB) ist
genau dieselbe Konstruktion, nur mit einem Byte-Vergleich statt `test -s`. Der
Kommentar darüber muss die Zahl begründen (81,7 Prozent der Parameter in der
Einbettungstabelle), so wie der tesseract-Block seine Pins begründet.

**Warum etwas gepinnt wird und etwas anderes nicht** (Z. 117-130):
```
# Why the engine is NOT pinned to a version while the language packs are.
...
# The three language packages are the opposite case: they are Architecture: all,
# they come from the tesseract-lang source package and they have not moved since
# bookworm. They are pinned hard, because the traineddata decides what the OCR
# reads, and a silent change of it is a silent change of the text of every
# scanned document in the index.
```
-> Wortgleiches Argument für sqlite-vec 0.1.9 (exakt, kein `>=`, D-07) und für
die Modelldatei: sie entscheidet, was jeder Vektor bedeutet.

**Digest-Pin als Projektregel** (Z. 19-22 und Z. 26-29):
```dockerfile
ARG BASE_IMAGE=python:3.13-slim-trixie@sha256:ffb752e139c0a19692a43af8d8523b274222dd68eebad5d583b45c2201c6e30a
...
COPY --from=ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a /uv /usr/local/bin/uv
```
-> Das ist das `APPSTORE_SHA`-Muster aus D-09: die `.so` kommt mit ihrer Prüfsumme
ins Abbild, nicht ungeprüft von PyPI beim Bau.

**Der Ort für HF_HUB_OFFLINE=1 und den festen cache_dir** ist der `ENV`-Block
Z. 228-230:
```dockerfile
ENV APP_HOST=0.0.0.0 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"
```

---

### 16. `backend/pyproject.toml` (geändert: fünf neue Kanten)

**Analog:** der Pillow-Block Z. 22-28:
```toml
    # Pillow was already in uv.lock, pulled in transitively by python-pptx. The
    # OCR path uses it directly (header inspection before decoding, EXIF
    # rotation, downscaling, PNG encoding), and a direct import of an indirect
    # dependency is the version that silently disappears when the package that
    # dragged it in stops needing it. So it becomes a direct edge here. Net new
    # PyPI packages of phase 3: zero.
    "pillow==12.3.0",
```
-> Jede neue Zeile (`fastembed`, `onnxruntime`, `sqlite-vec`,
`semantic-text-splitter`) traegt ihre Begründung im Kommentar darüber, exakt
gepinnt mit `==`, so wie jede bestehende Zeile. Die Sicherheitsuntergrenze-Form
für transitive Kanten steht Z. 48-52 (`constraint-dependencies`); dort gehört
`huggingface-hub`/`requests` hin, falls eine Untergrenze nötig wird.

---

### 17. `docs/embeddings.md` (neu)

**Analog:** `docs/ocr.md`. Das ist die Datei, auf die `config.py` Z. 219 und
`extract/ocr.py` Z. 26 verweisen ("The numbers themselves are in
:mod:`findling.config`, measured, with the full table and the measurement
protocol in ``docs/ocr.md``"). `docs/embeddings.md` steht in derselben Beziehung
zu den neuen Konstanten: jede Zahl mit Kommandozeile und Messdatum.

**Messbericht-Analog:** `docs/measurements/2026-09-04-volllauf-cpx22/` mit
`README.md`, `.csv` und den Rohlogs daneben. Die Welle-0-Ergebnisse (A/B/C plus
die zwei Fünf-Minuten-Proben A12/A13) gehören in ein Geschwisterverzeichnis
derselben Form, weil D-17 auf sie verlinken muss.

---

### 18. Die Testdateien

**`test_semantic_search.py`** -> **Analog `backend/tests/test_acl_prefilter.py`**
(Kopf Z. 1-21). Das ist die Datei, die die drei Eigenschaften des Vorfilters
festnagelt, inklusive eines Greps auf den Namen:
```
**The name.** ``prefilter_visible``, never ``check`` and never ``authorize``. The
last test in this file is a grep with a reason: once somebody believes the
backend already decided, the PHP recheck becomes an obvious thing to optimise
away, and that recheck is the only authority there is.
```
-> Der Grep-Test für Phase 6 lautet: in `api/` existiert keine zweite Route mit
"semantic" im Pfad, und `prefilter_visible` wird an genau zwei Stellen gerufen
(`candidates`, `snippets_for`). Das ist Fallstrick 1 als Test statt als Vorsatz.
Das Vorbild für einen quellcode-lesenden Test steht in `test_search_library.py`
Z. 35:
```python
SEARCH_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "index" / "search.py"
```

**`test_rrf_fusion.py`** -> **Analog `backend/tests/test_search_library.py`**
(Kopf Z. 1-13): "Two of the assertions below are about things that must *not* be
there". Für RRF sind das: rank beginnt bei 1, und ein Ausfall des Vektorzweigs
macht die Verschmelzung zur Identität auf der Tantivy-Liste.

**Die Fixture-Form** (`test_search_library.py` Z. 43-80): echter Index, echter
Store, drei Nutzer (alice ungerade IDs, bob alles, carol keine Zeile). Der
Vektorzweig-Test benutzt exakt dieselbe Aufteilung, damit die Aussage "ein
Vektortreffer durchläuft dieselbe Kette" an denselben Daten gemessen wird.

**`test_embedding_track.py`** -> **Analog `backend/tests/test_poller.py`**
(2.710 Zeilen, die OCR-Handover-Fälle). Dort steht bereits, wie ein Handover, ein
verlorener Requeue und eine Wiederzustellung geprüft werden.

**`test_embed_model.py`** -> **Analog `backend/tests/test_ocr.py`** (922 Zeilen):
Engine fehlt -> ehrliches Verdikt, Caps greifen, kein Inhalt im Log. Plus die
zwei phasenspezifischen Fälle: Präfixtest (D-05) und Modelldatei-umbenennen-Test
(D-19).

**Die gemeinsame Fixture-Infrastruktur** (`backend/tests/conftest.py` Z. 1-19):
```
The fixtures here build the real thing rather than a stand-in. A fake index and
a fake permission table would answer every question except the one these suites
exist for: whether the endpoints wire the analyzer chain, the query rewriting and
the ACL prefilter together correctly.
```
-> Gilt unverändert: keine Attrappe für den Vektorspeicher in den
Endpunkt-Suiten. Für `embed/model.py` ist eine Attrappe dagegen zulässig, weil
das Modell nicht im Testabbild liegt; das ist derselbe Schnitt, den `test_ocr.py`
zwischen "tesseract vorhanden" und "tesseract fehlt" zieht.

---

## Shared Patterns

Diese fünf gelten für JEDE neue Datei dieser Phase.

### A. Der Privacy-Vertrag im Log

**Quelle:** `api/search.py` Z. 199-202 und `index/search.py` Z. 168
**Gilt für:** jedes neue Modul mit einem `LOGGER`
```python
except Exception as error:
    # The type name and nothing else: a traceback carries whatever a library
    # put into its message, and the search text is the usual content.
    LOGGER.warning("the candidate search ended in an unexpected %s", type(error).__name__)
```
```python
# Only the fact, never the query or the counts: both are content.
LOGGER.info("the candidate scan hit its raw ceiling and answered a truncated page")
```
Ein Chunk-Text, ein Anfragetext oder ein Dateiname in einer Logzeile ist im
Vektorzweig genauso ein Leck wie im Volltextzweig.

### B. Der Container-zu-PHP-Vertrag bleibt unverändert

**Quelle:** `api/search.py` Z. 16-27 und `Candidate` Z. 96-109
**Gilt für:** `fusion.py`, `candidates()`, alles auf dem Suchweg
Ein Vektortreffer hat dieselbe `Candidate`-Form: `fileId`, `score`, `mtime`. Der
Feldmengen-Test in `test_search_endpoint.py` ist die strukturelle Sicherung.

### C. Der Vorfilter ist ein Beschleuniger, keine Grenze

**Quelle:** `repo.py::prefilter_visible` Z. 922-946
```python
    """Drop candidates the user almost certainly cannot see.

    This is a speed-up, never a security boundary. It over-approximates on
    team folders with advanced permissions, ... The only authority is the PHP recheck
    through getUserFolder()->getFirstNodeById(), and it runs before any
    snippet exists.

    The direction is fixed: given candidates, which of them are permitted.
    Materialising every file a user may see is the inverse, and it is the
    documented anti-pattern of the app this one replaces...
    """
```
**Gilt für:** den Vektorzweig ohne Ausnahme. Kein `vec0`-Metadaten- oder
Partitionsfilter auf `uid` (A8 ist ohnehin ungeprüft), keine dritte Stufe. Die
Richtung bleibt: Kandidaten rein, erlaubte Kandidaten raus.

### D. Konstanten mit Herkunft, Warnung statt Abbruch

**Quelle:** `config.py` Z. 266-269 und Z. 380-401
Jede neue Zahl traegt (a) woher sie kommt (gemessen/belegt/hergeleitet),
(b) was passiert, wenn ein Admin sie falsch setzt, (c) eine Bereichsprüfung, die
warnt und auf die Vorgabe zurückfällt. Ein unlesbarer Wert lässt den Container
nie scheitern.

### E. Der Ausfall ist ein Zustand, nie ein 500

**Quelle:** `api/status.py` Z. 255-272, `api/diagnose.py` Z. 87-102
```python
    # sqlite3.Error is caught next to OSError on both the open and the read,
    # because two realistic shapes of a broken state escape the open alone: a
    # file that is not a SQLite database raises DatabaseError from the first
    # PRAGMA, and a zero byte state.db, which a kill between connect and the
    # schema script leaves behind, opens cleanly and raises OperationalError on
    # the first query. Both are the same answer as an unreadable file: a state
    # of this container, never a 500 (review finding WR-01).
```
**Gilt für:** eine fehlende `vectors.db`, eine nicht ladbare Erweiterung, ein
fehlendes Modell. Alle drei sind Zustände mit einer `note`, plus `degraded=True`
auf dem Suchweg (D-19).

---

## No Analog Found

| Datei / Baustein | Rolle | Datenfluss | Grund |
|---|---|---|---|
| RRF-Verschmelzung selbst (`fusion.py`, die Formel) | utility | transform | Es gibt im Repository keine zweite Rangliste und keine Verschmelzung. Formel und `k=60`-Vorgabe kommen aus 06-RESEARCH 2.5 (Elasticsearch-Referenz), das Projektmuster liefert nur die Form (reine Funktion, Kommentar mit Messbeleg, Test mit zwölf Zahlen). |
| Ladbare SQLite-Erweiterung (`enable_load_extension`, `vec0`) | store | CRUD | `repo.py::_connect` Z. 427-456 ruft es heute nicht, und es gibt keine zweite Datenbank im Projekt. Die Proben A12 (query_only) und A13 (CPython-Build) aus D-18 sind der Ersatz für ein fehlendes Analog und gehören an den Phasenanfang. |

Beide Punkte sind der Grund, warum D-18 (Welle 0 vor der Schemafixierung) keine
Formalie ist: an genau diesen zwei Stellen kann der Planner nicht von bestehendem
Code abschreiben.

---

## Metadata

**Suchbereich:** `backend/src/findling/{api,index,store,worker,extract,nc,query,tools}`,
`backend/tests/`, `php/lib/{Search,Service,Db}/`, `php/templates/`,
`backend/Dockerfile`, `backend/pyproject.toml`, `.github/workflows/`, `docs/`,
`scripts/`
**Gescannte Dateien:** 47 gelistet, 21 gelesen (davon 6 gezielt in Teilbereichen)
**Nicht angefasst:** die AWS-Box 3.65.24.222 (dort läuft der 05-21-Volllauf),
`.planning/` ausser den beiden Eingangsdokumenten. Es wurde nichts committet und
keine Quelldatei geändert.
**Extraktionsdatum:** 2026-09-04
