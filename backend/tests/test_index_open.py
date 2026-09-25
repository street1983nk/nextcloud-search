"""Opening an index, asserted against a real directory on disk.

The load bearing test in this file is the reopen. The schema persists the *name*
of a tokenizer and never the tokenizer itself, so an index that is opened without
registering answers the very first parse_query with
``The tokenizer '"de"' for the field '"body_de"' is unknown``. That reads like a
broken index and is a missing line of setup, which is why one test closes the
index, opens it through open_index again and only then searches. Without the
registration inside the opening function, exactly that test falls over, and that
is its whole purpose.

Everything else here is measured behaviour rather than a description of the
schema: tantivy's Python bindings expose no field introspection, so a table
asserted against a second table would only prove that the two tables agree. The
tests below write a document and ask the index what it can answer.

Umlauts appear inside string literals only. They are data, the words the product
has to handle; identifiers stay ASCII as the project rules require.
"""

import ast
import logging
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from textwrap import dedent

import pytest
from tantivy import Document, Filter, Index, TextAnalyzer, TextAnalyzerBuilder, Tokenizer

from conftest import open_schema_1_index, write_wordlist_nl
from findling.config import INDEX_VERSION, SCHEMA_VERSION, SNOWBALL_NAME, settings
from findling.index import analyzer
from findling.index.analyzer import (
    ANALYZER_VERSION,
    MAX_TOKEN_CHARS,
    TOKENIZER_DE,
    build_count,
    cached_german_analyzer,
    dutch_build_count,
)
from findling.index.open import (
    DUTCH_MARK,
    LANGUAGES_MARK,
    SCHEMA_MARK,
    TANTIVY_VERSION,
    expected_versions,
    open_index,
    open_reader,
    stamp_a_new_directory,
    stamp_after_rebuild,
    start_rebuild_on_drift,
)
from findling.index.schema import (
    BODY_FIELD,
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ES,
    FIELD_BODY_IT,
    FIELD_BODY_NL,
    FIELD_BODY_PT,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
    FIELDS,
    build_schema,
)
from findling.index.wordlist import FUGEN, wordlist_hash
from findling.index.wordlist_nl import dutch_digest_for, read_count_nl
from findling.store.repo import FileMeta, Store, open_store

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# The single module that may open an index. Everything else has to go through it,
# because opening is registering.
OPENING_MODULE = "index/open.py"

# The single module that may open an index with an empty constituent list. It
# reads a document count and nothing else, so the automaton nobody needs is not
# built; the guard below holds that it stays a counter.
COUNTING_MODULE = "tools/index_status.py"

# What a module that only counts must never call. parse_query and its lenient
# sibling are the tantivy side, build_query is ours, and search is where an
# answer would leave the process.
QUESTION_CALLS = frozenset({"parse_query", "parse_query_lenient", "build_query", "search"})

# The same fixture the analyzer table runs on: the subset of the real Debian list
# that occurs inside the test inputs, proven token identical to the full list.
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

# One digest for the version marks. The value is never interpreted here, it only
# has to travel from the caller into the expectation unchanged.
DIGEST = "0" * 64

# The language set of the factory setting, handed to expected_versions the way
# every production call site hands it: as one normalised string.
LANGUAGES = "de,en"


def _write(
    index: Index,
    *,
    file_id: int = 1,
    storage_id: int = 7,
    name: str = "Kündigung.pdf",
    title: str = "Kündigung",
    path: str = "/Verträge/Kündigung.pdf",
    ext: str = "pdf",
    body: str = "Die Kündigungsfrist beträgt drei Monate.",
    body_en: str | None = None,
    mtime: int = 1_700_000_000,
) -> None:
    """Write one document field by field and commit it.

    Field by field on purpose, and never through keyword arguments: measured, a
    keyword built document puts an I64 into the U64 column of file_id and the
    indexing thread of tantivy panics, after the Python call has already returned
    successfully.
    """
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, file_id)
    document.add_unsigned(FIELD_STORAGE_ID, storage_id)
    document.add_text(FIELD_NAME, name)
    document.add_text(FIELD_TITLE, title)
    document.add_text(FIELD_PATH, path)
    document.add_text(FIELD_EXT, ext)
    document.add_text(FIELD_BODY_DE, body)
    document.add_text(FIELD_BODY_EN, body if body_en is None else body_en)
    document.add_integer(FIELD_MTIME, mtime)
    writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()


def _hits(index: Index, query: str, fields: list[str] | None = None) -> int:
    searcher = index.searcher()
    parsed = index.parse_query(query, fields if fields is not None else [FIELD_BODY_DE])
    return len(searcher.search(parsed, 10).hits)


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    """A path that does not exist yet, so creation is part of every test."""
    return tmp_path / "index"


def test_open_index_creates_the_index_in_an_empty_directory(index_dir: Path) -> None:
    open_index(index_dir, CONSTITUENTS)

    assert Index.exists(str(index_dir))


def test_open_index_opens_the_existing_index_instead_of_starting_a_new_one(index_dir: Path) -> None:
    _write(open_index(index_dir, CONSTITUENTS), file_id=42)

    reopened = open_index(index_dir, CONSTITUENTS)

    assert reopened.searcher().num_docs == 1


def test_a_query_against_body_de_parses_after_opening(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)

    # Without the registration this raises before it ever reaches the index.
    assert index.parse_query("frist", [FIELD_BODY_DE]) is not None


def test_reopen_answers_the_same_query(index_dir: Path) -> None:
    # The test this file exists for. The index is written, dropped and opened
    # again; a missing register_tokenizer in open_index fails right here.
    _write(open_index(index_dir, CONSTITUENTS))

    reopened = open_index(index_dir, CONSTITUENTS)

    assert _hits(reopened, "frist") == 1


def test_the_schema_carries_exactly_the_thirteen_documented_fields() -> None:
    # Nine until 2026-09-24, thirteen since: the four body fields of the v1.3
    # languages sit between body_en and mtime, which is schema field order and
    # therefore the order of this tuple as well.
    assert FIELDS == (
        FIELD_FILE_ID,
        FIELD_STORAGE_ID,
        FIELD_NAME,
        FIELD_TITLE,
        FIELD_PATH,
        FIELD_EXT,
        FIELD_BODY_DE,
        FIELD_BODY_EN,
        FIELD_BODY_ES,
        FIELD_BODY_IT,
        FIELD_BODY_NL,
        FIELD_BODY_PT,
        FIELD_MTIME,
    )
    assert len(FIELDS) == 13
    assert len(set(FIELDS)) == 13


def test_the_body_field_map_and_the_language_names_carry_the_same_codes() -> None:
    # Two mappings with one job each: BODY_FIELD turns a code into a schema
    # field, SNOWBALL_NAME turns the same code into a tantivy language. Held
    # against each other by key and by order, because the order is schema field
    # order in one and has to be the same in the other: a loop over one of them
    # that fills or registers through the other must not be able to pair es with
    # the Italian chain, and a code that exists in one alone is either a field
    # nobody can fill or a chain for a field that does not exist.
    assert tuple(BODY_FIELD) == ("de", "en", "es", "it", "nl", "pt")
    assert tuple(BODY_FIELD) == tuple(SNOWBALL_NAME)
    assert tuple(BODY_FIELD.values()) == FIELDS[FIELDS.index(FIELD_BODY_DE) : FIELDS.index(FIELD_MTIME)]


def test_a_document_that_leaves_the_four_new_bodies_empty_is_accepted(index_dir: Path) -> None:
    # The everyday case of every installation that did not switch a language on:
    # nine of the thirteen fields carry a value and four do not. The write has to
    # go through all the same, and the chains of the empty fields have to be
    # registered for it, which is what the guards further down hold.
    index = open_index(index_dir, CONSTITUENTS)

    _write(index)

    assert index.searcher().num_docs == 1


def test_a_document_that_fills_all_six_bodies_is_accepted(index_dir: Path) -> None:
    # The other end: a document written into every body field there is. It says
    # that the four new fields are real fields and not decoration, and that each
    # of them answers on its own chain.
    index = open_index(index_dir, CONSTITUENTS)
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, 1)
    document.add_text(FIELD_BODY_DE, "Die Kündigungsfrist beträgt drei Monate.")
    document.add_text(FIELD_BODY_EN, "The notice period is three months.")
    document.add_text(FIELD_BODY_ES, "El plazo de preaviso es de tres meses.")
    document.add_text(FIELD_BODY_IT, "Il preavviso è di tre mesi.")
    document.add_text(FIELD_BODY_NL, "De opzegtermijn bedraagt drie maanden.")
    document.add_text(FIELD_BODY_PT, "O prazo de aviso prévio é de três meses.")
    writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()

    assert _hits(index, "preaviso", [FIELD_BODY_ES]) == 1
    assert _hits(index, "preavviso", [FIELD_BODY_IT]) == 1
    assert _hits(index, "opzegtermijn", [FIELD_BODY_NL]) == 1
    assert _hits(index, "previo", [FIELD_BODY_PT]) == 1


def test_the_two_identifiers_and_mtime_are_fast_fields(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, file_id=42, storage_id=7, mtime=1_700_000_000)
    searcher = index.searcher()
    address = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits[0][1]

    assert searcher.fast_field_values(FIELD_FILE_ID, [address]) == [42]
    assert searcher.fast_field_values(FIELD_STORAGE_ID, [address]) == [7]
    assert searcher.fast_field_values(FIELD_MTIME, [address]) == [1_700_000_000]


def test_the_text_fields_are_not_fast_fields(index_dir: Path) -> None:
    # A fast field is a column on disk. body_de is read from the document store
    # for snippets, and paying for a column as well would be paying twice.
    index = open_index(index_dir, CONSTITUENTS)
    _write(index)
    searcher = index.searcher()
    address = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits[0][1]

    with pytest.raises(ValueError, match="not a fast field"):
        searcher.fast_field_values(FIELD_BODY_DE, [address])


def test_path_is_stored_and_not_searchable(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, path="/Verträge/Kündigung.pdf")
    searcher = index.searcher()
    address = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits[0][1]

    assert searcher.doc(address).get_first(FIELD_PATH) == "/Verträge/Kündigung.pdf"
    assert _hits(index, f'{FIELD_PATH}:"/Verträge/Kündigung.pdf"') == 0
    assert _hits(index, f"{FIELD_PATH}:Kündigung") == 0


def test_body_de_is_stored_and_body_en_is_only_indexed(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, body="Die Kündigungsfrist beträgt drei Monate.", body_en="The notice period is three months.")
    searcher = index.searcher()
    address = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits[0][1]
    document = searcher.doc(address)

    assert document.get_first(FIELD_BODY_DE) == "Die Kündigungsfrist beträgt drei Monate."
    assert document.get_first(FIELD_BODY_EN) is None
    assert _hits(index, "notice", [FIELD_BODY_EN]) == 1


def test_the_registered_german_chain_splits_compounds(index_dir: Path) -> None:
    # Proves which analyzer answers for body_de: tantivy's default would index
    # "kündigungsfrist" as one term and "frist" would find nothing.
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, body="Die Kündigungsfrist beträgt drei Monate.")

    assert _hits(index, "frist") == 1
    assert _hits(index, "kündigung") == 1


# -- the way and not the result (QUAL-02) ------------------------------------
#
# The test above counts a hit, and a hit counter alone proves nothing about the
# way it came: a prefix, wildcard or fuzzy rewrite in query/rewrite.py would
# answer "frist" with the very same 1 and leave that test green while the
# splitter is gone. The three tests below make the statements that only the
# decomposition can satisfy: without the splitter the constituent finds nothing,
# a mere prefix of the compound finds nothing, and both sides of the search
# produce exactly the same terms and no others.

# The sentence every test in this section writes. Named once, because a test
# that asserts about tokens has to be asking about the text it wrote.
COMPOUND_SENTENCE = "Die Kündigungsfrist beträgt drei Monate."

# A real prefix of "Kündigungsfrist" that is no constituent of it. Measured
# against the full Debian list: it stays the single token "kundigungsf", so the
# shipped way cannot answer it, while any prefix query would.
MERE_PREFIX = "kündigungsf"

# The measured tokens of the shipped chain, both sides of the search.
COMPOUND_TERMS = ["kundig", "frist"]
CONSTITUENT_TERMS = ["frist"]


def _splitterless_german() -> TextAnalyzer:
    """The shipped German chain minus Filter.split_compound, filter for filter.

    Everything else stays: lowercase, the linking elements as custom stopwords,
    the built in German stopwords, the length limit and the Snowball stemmer, in
    the shipped order. That is what makes it a control and not a second recipe.
    MAX_TOKEN_CHARS and FUGEN are imported rather than copied, so the control
    cannot drift away from the chain it is a control for.
    """
    return (
        TextAnalyzerBuilder(Tokenizer.simple())
        .filter(Filter.lowercase())
        .filter(Filter.custom_stopword(list(FUGEN)))
        .filter(Filter.stopword("german"))
        .filter(Filter.remove_long(MAX_TOKEN_CHARS))
        .filter(Filter.stemmer("german"))
        .build()
    )


def test_without_the_splitter_the_constituent_finds_nothing(index_dir: Path) -> None:
    # The negative control, both halves in one test so that neither can be read
    # on its own. The chain is overwritten under the name the schema persists
    # BEFORE anything is written, so the write side and the question side both
    # run on the splitterless chain; overwriting afterwards would only ask a
    # differently tokenised question of a correctly written index.
    without = open_index(index_dir, CONSTITUENTS)
    without.register_tokenizer(TOKENIZER_DE, _splitterless_german())
    _write(without, body=COMPOUND_SENTENCE)

    assert _hits(without, "frist") == 0

    # The same text, the same question, the shipped chain. The difference
    # between the two numbers is the work Filter.split_compound does, and
    # nothing else differs between them.
    shipped = open_index(index_dir.parent / "shipped", CONSTITUENTS)
    _write(shipped, body=COMPOUND_SENTENCE)

    assert _hits(shipped, "frist") == 1


def test_a_mere_prefix_of_the_compound_does_not_hit(index_dir: Path) -> None:
    # The guard against a prefix crutch. This test goes red the day somebody
    # rewrites a question into a prefix, wildcard or fuzzy query in
    # query/rewrite.py: such a query answers "kündigungsf" with a hit, while the
    # decomposition answers it with nothing, because the fragment is a prefix of
    # the compound and no constituent of it. The other half of the same promise
    # is allow_regexes=False in query/rewrite.py::build_query, which keeps a
    # regular expression from reaching the parser in the first place.
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, body=COMPOUND_SENTENCE)

    assert _hits(index, MERE_PREFIX) == 0
    assert _hits(index, "frist") == 1


def test_the_question_side_produces_the_same_terms_as_the_index_side(index_dir: Path) -> None:
    # A hit says the two sides met somewhere; this says they meet on exactly the
    # same terms and on no others. Both sides go through open_index, which
    # registers the analyser cached_german_analyzer hands out for this digest, so
    # asking the cache for it again returns the very object the index answers
    # with. The build counter proves that: an object built a second time here
    # would raise it, and the assertion below would be about a different chain.
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, body=COMPOUND_SENTENCE)
    before = build_count()

    analyzer = cached_german_analyzer(wordlist_hash(CONSTITUENTS), CONSTITUENTS)

    assert build_count() == before
    assert analyzer.analyze("Kündigungsfrist") == COMPOUND_TERMS
    assert analyzer.analyze("Frist") == CONSTITUENT_TERMS
    assert _hits(index, "frist") == 1


def test_the_registered_name_chain_folds_umlauts_and_does_not_stem(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, name="Kündigung.pdf")

    assert _hits(index, f"{FIELD_NAME}:kuendigung", [FIELD_NAME]) == 0
    assert _hits(index, f"{FIELD_NAME}:kundigung", [FIELD_NAME]) == 1
    assert _hits(index, f"{FIELD_NAME}:kundigungen", [FIELD_NAME]) == 0


def test_ext_is_an_exact_term(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)
    _write(index, ext="pdf")

    assert _hits(index, f"{FIELD_EXT}:pdf", [FIELD_EXT]) == 1
    assert _hits(index, f"{FIELD_EXT}:pd", [FIELD_EXT]) == 0


def test_the_schema_does_not_change_with_the_language_setting(monkeypatch: pytest.MonkeyPatch, index_dir: Path) -> None:
    # FINDLING_LANGUAGES decides what the writer fills in, never what the schema
    # holds. A language switch that reshaped the schema would silently turn every
    # existing index into a different one.
    monkeypatch.setenv("FINDLING_LANGUAGES", "de")
    settings.cache_clear()
    try:
        assert settings().languages == ("de",)
        index = open_index(index_dir, CONSTITUENTS)
        _write(index, body_en="The notice period is three months.")

        assert len(FIELDS) == 13
        assert _hits(index, "notice", [FIELD_BODY_EN]) == 1
    finally:
        settings.cache_clear()


def test_build_schema_returns_a_usable_schema() -> None:
    document = Document.from_dict({FIELD_FILE_ID: 1, FIELD_BODY_DE: "Kündigungsfrist"}, build_schema())

    assert document.get_first(FIELD_BODY_DE) == "Kündigungsfrist"


def test_a_second_open_does_not_build_the_automaton_again(tmp_path: Path) -> None:
    open_index(tmp_path / "first", CONSTITUENTS)
    before = build_count()

    open_index(tmp_path / "second", CONSTITUENTS)

    assert build_count() == before


def test_open_reader_sees_a_commit_that_happened_after_it(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)
    searcher = open_reader(index)
    assert searcher.num_docs == 0

    _write(index)

    # The reader is configured on "commit" and therefore sees new segments with a
    # delay; a deterministic test reloads and asks for a fresh searcher.
    assert index.searcher().num_docs == 1


def test_expected_versions_names_every_mark_the_store_compares() -> None:
    expected = expected_versions(DIGEST, LANGUAGES)

    assert expected == {
        "schema_version": str(SCHEMA_VERSION),
        "index_version": str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": DIGEST,
        "tantivy_version": TANTIVY_VERSION,
        "languages": LANGUAGES,
        "wordlist_hash_nl": "off",
    }
    assert all(isinstance(value, str) for value in expected.values())


def test_the_tantivy_mark_carries_the_on_disk_format() -> None:
    # tantivy makes no promise that its index format survives its own releases,
    # so the mark has to name the format and not only the release.
    assert TANTIVY_VERSION.startswith("tantivy v")
    assert "index_format" in TANTIVY_VERSION


def test_only_the_opening_module_opens_an_index() -> None:
    # The static half of pitfall 4. A second opener is not wrong on the day it is
    # written, it is wrong on the day somebody forgets the registration in it.
    offenders: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        if relative == OPENING_MODULE:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=relative)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            names = {func.attr} if isinstance(func, ast.Attribute) else set()
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                names.add(f"{func.value.id}.{func.attr}")
            if isinstance(func, ast.Name):
                names.add(func.id)
            if names & {"Index", "Index.open", "tantivy.Index"}:
                offenders.append(f"{relative}:{node.lineno}")

    assert offenders == [], "only " + OPENING_MODULE + " may open an index:\n" + "\n".join(offenders)


def _opens_without_a_word_list(node: ast.Call) -> bool:
    """True for an open_index call whose second argument is an empty collection.

    An empty literal and an empty ``tuple()`` or ``list()`` are the same thing to
    the reader and to the analyser, so both count; a name that happens to hold an
    empty sequence is out of reach of a syntax tree and stays out of reach here.
    """
    if len(node.args) < 2:
        return False
    second = node.args[1]
    if isinstance(second, ast.Tuple | ast.List):
        return not second.elts
    return isinstance(second, ast.Call) and isinstance(second.func, ast.Name) and second.func.id in {"tuple", "list"}


def test_the_only_index_opened_without_a_word_list_is_never_asked_a_question() -> None:
    # tools/index_status.py opens the index with an empty constituent list on
    # purpose: it reads num_docs and building the real automaton would cost
    # 0.44 s and 23 MB on every round of a waiting loop. That is only safe as
    # long as nothing there asks, because a question against that index runs
    # through a chain the documents were never written with and comes back empty
    # with no reason in it. So the exemption is held from two sides: this file
    # asks no question, and no second file takes the same shortcut.
    questions: list[str] = []
    openers: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=relative)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                name = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            else:
                continue
            if relative == COUNTING_MODULE and name in QUESTION_CALLS:
                questions.append(f"{relative}:{node.lineno}")
            if name == "open_index" and _opens_without_a_word_list(node):
                openers.append(f"{relative}:{node.lineno}")

    assert questions == [], COUNTING_MODULE + " counts and must never ask:\n" + "\n".join(questions)
    assert [entry.rsplit(":", 1)[0] for entry in openers] == [COUNTING_MODULE], (
        "only " + COUNTING_MODULE + " may open an index without a constituent list:\n" + "\n".join(openers)
    )


# -- the eight chains, and that none of them hangs on a condition ------------
#
# Measured on 2026-09-24 with tantivy 0.26.2: a schema that carries a text field
# whose chain is not registered answers every writer.add_document with
# "Schema error: 'Error getting tokenizer for field: body_es'", and it does so
# even for a document that does not carry the field. So a registration behind
# "if language in settings().languages" would stop the indexer of every
# installation that does not run all six languages, and it would do it at the
# first write rather than at start up, where somebody would see it.

# The file the guard reads. Read as text and parsed, never imported: a module
# that stopped importing has to be a red gate and not an error in collection.
OPENING_SOURCE = PACKAGE_ROOT / OPENING_MODULE

# Six body chains, the file name chain, the chain that indexes nothing. Not a
# tautology, a ratchet: seven means a body field whose chain nobody registered
# and therefore a writer that raises on every document, nine means a name the
# schema does not persist and that nothing can ever ask for.
EXPECTED_REGISTRATIONS = 8


def registrations_of_open_index(source: str, filename: str = OPENING_MODULE) -> tuple[list[int], list[int]]:
    """The register_tokenizer calls inside open_index, split by what stands over them.

    Returns the line numbers of the free calls first and of the conditional ones
    second. A call counts as conditional when any ``if`` stands anywhere above it
    inside the function, in its test, its body or its else branch, because all
    three make the call depend on something that is not the schema.

    Read off the syntax tree and not out of the text: a comment that spells
    register_tokenizer out is not part of the tree, so it cannot raise the count,
    and a call that was reformatted over three lines cannot lower it.
    """
    free: list[int] = []
    conditional: list[int] = []
    for function in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(function, ast.FunctionDef) or function.name != "open_index":
            continue
        for node, guarded in _walk_with_conditions(function):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr == "register_tokenizer":
                (conditional if guarded else free).append(node.lineno)
    return sorted(free), sorted(conditional)


def _walk_with_conditions(node: ast.AST, guarded: bool = False) -> list[tuple[ast.AST, bool]]:
    """Every node below ``node``, each with the answer whether an if stands over it."""
    found: list[tuple[ast.AST, bool]] = []
    for child in ast.iter_child_nodes(node):
        below = guarded or isinstance(node, ast.If)
        found.append((child, below))
        found.extend(_walk_with_conditions(child, below))
    return found


def test_the_registration_reader_fires_on_a_staged_sample() -> None:
    # The self test of the gate below. Without it a reader whose body was
    # deleted would report zero findings over zero lines and look healthy, and
    # the gate would be green on the day the registrations disappear.
    staged = dedent(
        """
        def open_index(path, constituents):
            index = Index(build_schema(), path=str(path))
            index.register_tokenizer(TOKENIZER_DE, cached_german_analyzer(digest, constituents))
            if "es" in settings().languages:
                index.register_tokenizer(TOKENIZER_ES, snowball_analyzer("spanish"))
            # index.register_tokenizer(TOKENIZER_IT, snowball_analyzer("italian"))
            return index
        """
    )
    free, conditional = registrations_of_open_index(staged, "staged.py")

    # One free call, one behind the condition, and the one that only stands in a
    # comment is in neither list, which is what reading the tree buys.
    assert len(free) == 1, free
    assert len(conditional) == 1, conditional

    empty = registrations_of_open_index(
        dedent(
            """
            def open_index(path, constituents):
                return None
            """
        ),
        "staged.py",
    )
    assert empty == ([], []), empty

    elsewhere = registrations_of_open_index(
        dedent(
            """
            def open_reader(index):
                index.register_tokenizer("de", chain())
                return index
            """
        ),
        "staged.py",
    )
    assert elsewhere == ([], []), elsewhere


def test_open_index_registers_eight_chains_and_hangs_none_of_them_on_a_condition() -> None:
    free, conditional = registrations_of_open_index(OPENING_SOURCE.read_text(encoding="utf-8"))

    assert conditional == [], (
        "a chain that is registered behind a condition makes writer.add_document raise on every "
        "installation the condition is false on: " + ", ".join(f"{OPENING_MODULE}:{line}" for line in conditional)
    )
    assert len(free) == EXPECTED_REGISTRATIONS, free
    # And the six of them that belong to a body field are exactly the six codes
    # the schema carries, so the count above cannot be met by registering one
    # chain twice and leaving a field without one.
    assert len(BODY_FIELD) + 2 == EXPECTED_REGISTRATIONS


def callers_without_the_dutch_mark(source: str, filename: str) -> list[int]:
    """Line numbers of every call of expected_versions that does not name dutch_mark.

    Read off the syntax tree, like the registration reader above: a call spread
    over three lines is one Call node, and a comment or a docstring that spells
    the name out is not a call at all. Both a bare name and an attribute count,
    so ``open.expected_versions(...)`` cannot slip past.
    """
    missing: list[int] = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name != "expected_versions":
            continue
        if not any(keyword.arg == "dutch_mark" for keyword in node.keywords):
            missing.append(node.lineno)
    return missing


def test_the_dutch_mark_gate_sees_a_caller_without_it() -> None:
    # The self test of the gate below: a reader that found nothing would be
    # green on the day a caller forgot the Dutch mark.
    staged = dedent(
        """
        def _open_state():
            expected = expected_versions(build_artifact().digest, ",".join(settings().languages))
            named = expected_versions(
                digest,
                languages,
                dutch_mark=dutch_mark(settings().languages),
            )
            other = open.expected_versions(digest, languages)
            # expected_versions(digest, languages) in a comment is not a call
            return expected, named, other
        """
    )
    assert callers_without_the_dutch_mark(staged, "staged.py") == [3, 9]


def test_every_caller_in_src_names_the_dutch_mark() -> None:
    """D-06: every caller in src builds the Dutch value itself, none falls back on off.

    The default of ``dutch_mark`` is there for the tests and for a store that
    never saw nl. A src caller that leaned on it would expect off on an
    installation that runs nl with a list, report a drift nothing answers and,
    in the poller, compare the stamp against the wrong value (T-21-06-03).
    """
    files = sorted(PACKAGE_ROOT.rglob("*.py"))
    assert files, "the package root moved and the gate would look at nothing"
    found: dict[str, list[int]] = {}
    calls = 0
    for path in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        calls += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "expected_versions")
                or (isinstance(node.func, ast.Attribute) and node.func.attr == "expected_versions")
            )
        )
        missing = callers_without_the_dutch_mark(source, str(path))
        if missing:
            found[str(path.relative_to(PACKAGE_ROOT))] = missing

    assert found == {}, f"callers of expected_versions without dutch_mark: {found}"
    # Six callers today: three in the poller, one each in resources, one_load
    # and rebuild. Fewer means the walk lost files, which would be a green gate
    # over nothing.
    assert calls >= 6, calls


# -- the Dutch chain behind the language set (plan 21-07) --------------------
#
# The registration of the nl chain stays free, as the gate above demands; what
# follows the language set is which variant stands behind the name. Without nl
# the plain Snowball chain answers for body_nl and no Dutch list is read. With
# nl the splitting chain answers, and a Dutch compound is found through its
# constituent. The behaviour is held here, the choice at every caller below.

# The sentence of success criterion 2, and the question that must reach it.
DUTCH_COMPOUND_SENTENCE = "De gemeentebelastingen voor dit jaar zijn verhoogd."
DUTCH_CONSTITUENT = "belasting"

# The language set of a Dutch container, as settings() hands it out.
DUTCH_LANGUAGES = ("de", "en", "nl")


def _write_dutch(index: Index, body: str = DUTCH_COMPOUND_SENTENCE) -> None:
    """Write one document with the text in body_de and body_nl, field by field."""
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, 1)
    document.add_unsigned(FIELD_STORAGE_ID, 7)
    document.add_text(FIELD_BODY_DE, body)
    document.add_text(FIELD_BODY_NL, body)
    writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()


def _switch_dutch_on(volume: Path, monkeypatch: pytest.MonkeyPatch) -> str | None:
    """Put the Dutch list on the volume, switch nl on and return the digest the callers hand in."""
    write_wordlist_nl(volume)
    monkeypatch.setenv("FINDLING_LANGUAGES", ",".join(DUTCH_LANGUAGES))
    settings.cache_clear()
    return dutch_digest_for(settings().languages)


def test_with_dutch_the_constituent_finds_the_compound(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dutch = _switch_dutch_on(volume, monkeypatch)
    assert dutch is not None

    index = open_index(volume / "index", CONSTITUENTS, dutch=dutch)
    _write_dutch(index)

    assert _hits(index, DUTCH_CONSTITUENT, [FIELD_BODY_NL]) == 1


def test_without_the_dutch_splitter_the_constituent_finds_nothing(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The negative control of the test above, both halves in one test like its
    # German model: the same volume, the same text, the same question, and the
    # only difference is the variant behind the nl name.
    dutch = _switch_dutch_on(volume, monkeypatch)

    without = open_index(volume / "without", CONSTITUENTS, dutch=None)
    _write_dutch(without)

    assert _hits(without, DUTCH_CONSTITUENT, [FIELD_BODY_NL]) == 0

    shipped = open_index(volume / "shipped", CONSTITUENTS, dutch=dutch)
    _write_dutch(shipped)

    assert _hits(shipped, DUTCH_CONSTITUENT, [FIELD_BODY_NL]) == 1


def test_without_dutch_no_dutch_automaton_is_built(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The list lies on the volume on purpose: a reader that reached for it would
    # find it, so an unchanged read counter says that nothing reached for it.
    write_wordlist_nl(volume)
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en")
    settings.cache_clear()
    builds, reads = dutch_build_count(), read_count_nl()

    dutch = dutch_digest_for(settings().languages)
    index = open_index(volume / "index", CONSTITUENTS, dutch=dutch)
    _write_dutch(index)

    assert dutch is None
    assert dutch_build_count() == builds
    assert read_count_nl() == reads


def test_two_openings_with_dutch_build_one_automaton(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dutch = _switch_dutch_on(volume, monkeypatch)
    before = dutch_build_count()

    open_index(volume / "first", CONSTITUENTS, dutch=dutch)
    open_index(volume / "second", CONSTITUENTS, dutch=dutch)

    assert dutch_build_count() - before <= 1


def _at_once(work: Callable[[], object], count: int = 4) -> list[object]:
    """Run one callable in ``count`` threads released by one barrier, return every answer.

    The barrier is the whole point: started one after the other the threads would
    mostly serialise on their own, the first would fill the cache and no other
    would ever reach the miss the lock is about.
    """
    barrier = threading.Barrier(count)
    answers: list[object] = [None] * count
    failures: list[BaseException] = []

    def gated(slot: int) -> None:
        barrier.wait(30)
        try:
            answers[slot] = work()
        # Handed back to the test thread, where the assertion below reads it.
        except BaseException as error:
            failures.append(error)

    workers = [threading.Thread(target=gated, args=(slot,)) for slot in range(count)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join(60)
    assert not failures, failures
    return answers


def _slow_down(monkeypatch: pytest.MonkeyPatch, name: str) -> None:
    """Stretch a build to the width the box measures, so the race window is real."""
    real = getattr(analyzer, name)

    def slow(constituents: Sequence[str]) -> TextAnalyzer:
        time.sleep(0.2)
        return real(constituents)

    monkeypatch.setattr(analyzer, name, slow)


def test_four_threads_opening_with_dutch_at_once_build_one_automaton(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Review finding WR-01: the single threaded case above cannot see the race.

    The poller, the band run and the reading side open in threads of their own,
    and a lookup outside a lock let every one of them miss the cache inside the
    build window and build an automaton of its own.
    """
    dutch = _switch_dutch_on(volume, monkeypatch)
    assert dutch is not None
    monkeypatch.setattr(analyzer, "_CACHED_DUTCH", {})
    _slow_down(monkeypatch, "dutch_analyzer")
    before = dutch_build_count()

    answers = _at_once(lambda: analyzer.dutch_chain_for(dutch))

    assert dutch_build_count() - before == 1
    assert all(answer is answers[0] for answer in answers)


def test_four_threads_asking_for_the_german_automaton_at_once_build_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The pre-existing twin of the same class, closed with the same lock pattern."""
    monkeypatch.setattr(analyzer, "_CACHED_GERMAN", {})
    _slow_down(monkeypatch, "german_analyzer")
    before = build_count()

    answers = _at_once(lambda: cached_german_analyzer("race", CONSTITUENTS))

    assert build_count() - before == 1
    assert all(answer is answers[0] for answer in answers)


def callers_without_the_dutch_choice(source: str, filename: str) -> list[int]:
    """Line numbers of every call of open_index that does not name ``dutch``.

    The same reading as the Dutch mark gate above: syntax tree, bare name and
    attribute alike, and a comment or a docstring is no call.
    """
    missing: list[int] = []
    for node in ast.walk(ast.parse(source, filename=filename)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name != "open_index":
            continue
        if not any(keyword.arg == "dutch" for keyword in node.keywords):
            missing.append(node.lineno)
    return missing


def test_the_dutch_choice_gate_sees_a_caller_without_it() -> None:
    # The self test of the gate below: a reader that found nothing would be
    # green on the day a caller forgot the Dutch choice.
    staged = dedent(
        """
        def _open_writer():
            index = open_index(resolved.index_dir, artifact.entries)
            named = open_index(
                directory,
                constituents,
                dutch=dutch_digest_for(languages),
            )
            other = open.open_index(directory, constituents)
            # open_index(directory, constituents) in a comment is not a call
            return index, named, other
        """
    )
    assert callers_without_the_dutch_choice(staged, "staged.py") == [3, 9]


def test_every_caller_in_src_names_the_dutch_choice() -> None:
    """No caller in src decides the Dutch chain by leaning on the default.

    The default of ``dutch`` is None for the tests. A src caller that leaned on
    it would open a Dutch installation with the Snowball chain, and the index
    would quietly stop splitting the compounds its mark says it splits.
    """
    files = sorted(PACKAGE_ROOT.rglob("*.py"))
    assert files, "the package root moved and the gate would look at nothing"
    found: dict[str, list[int]] = {}
    calls = 0
    for path in files:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        calls += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Name) and node.func.id == "open_index")
                or (isinstance(node.func, ast.Attribute) and node.func.attr == "open_index")
            )
        )
        missing = callers_without_the_dutch_choice(source, str(path))
        if missing:
            found[str(path.relative_to(PACKAGE_ROOT))] = missing

    assert found == {}, f"callers of open_index without dutch: {found}"
    # Nine callers today: poller, resources, one_load, bench, index_status and
    # four in rebuild. Fewer means the walk lost files.
    assert calls >= 9, calls


def test_a_write_goes_through_when_only_german_is_switched_on(monkeypatch: pytest.MonkeyPatch, index_dir: Path) -> None:
    # The measured failure of pitfall 2, held as a statement about behaviour and
    # not about source text: FINDLING_LANGUAGES=de is the narrowest set an
    # installation can run, the schema still carries all six body fields, and a
    # document has to go in and come back out all the same.
    monkeypatch.setenv("FINDLING_LANGUAGES", "de")
    settings.cache_clear()
    try:
        assert settings().languages == ("de",)
        index = open_index(index_dir, CONSTITUENTS)

        _write(index)

        searcher = index.searcher()
        assert searcher.num_docs == 1
        address = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits[0][1]
        assert searcher.doc(address).get_first(FIELD_BODY_DE) == "Die Kündigungsfrist beträgt drei Monate."
    finally:
        settings.cache_clear()


def test_the_chain_of_a_language_nobody_switched_on_still_answers(
    monkeypatch: pytest.MonkeyPatch, index_dir: Path
) -> None:
    # The other half of the same promise. Registration does not follow the
    # language set, so a Spanish document written under FINDLING_LANGUAGES=de
    # is tokenised by the Spanish chain and not by a default the schema never
    # named. Whether anything writes that field is the filling question, and the
    # filling question belongs to the writer and not to this module.
    monkeypatch.setenv("FINDLING_LANGUAGES", "de")
    settings.cache_clear()
    try:
        index = open_index(index_dir, CONSTITUENTS)
        writer = index.writer(heap_size=15_000_000, num_threads=1)
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, 1)
        document.add_text(FIELD_BODY_ES, "El plazo de preaviso es de tres meses.")
        writer.add_document(document)
        writer.commit()
        writer.wait_merging_threads()
        index.reload()

        # "de" is a Spanish stop word and is dropped, the rest is stemmed.
        assert _hits(index, "preaviso", [FIELD_BODY_ES]) == 1
        assert _hits(index, "de", [FIELD_BODY_ES]) == 0
    finally:
        settings.cache_clear()


# -- the marks after a rebuild (DI-04-04) ------------------------------------
#
# The reindex banner names one remedy, `occ findling:index --restart`, and until
# this plan that command could never make it disappear: nothing wrote the marks
# again once a rebuild was through, and nothing made the rebuild rebuild in the
# first place, because a stored verdict of the old analysis still counted as
# unchanged. An advice a program gives is a promise the program has to keep, so
# both halves are held here: the rebuild becomes real, and its end is what
# stamps.


def _drifted_store(tmp_path: Path) -> Store:
    """A state database whose index was built by an older analysis.

    Built the way the container builds it, then aged: one indexed verdict and
    marks that do not match the running code any more, which is what a container
    update leaves behind.
    """
    store = open_store(tmp_path / "state.db", meta=expected_versions("older-digest", LANGUAGES))
    store.record(
        4711,
        FileMeta(storage_id=3, root_id=2, path="a/b.txt", title="b.txt", mime="text/plain", size=7, mtime=1, etag="e"),
        "indexed",
        None,
        content_hash="hash-of-b",
    )
    return store


def test_a_fresh_database_has_nothing_to_rebuild(tmp_path: Path) -> None:
    # The seed wrote the marks of the running code, so there is no drift, no
    # generation is raised and the first index is an ordinary first index.
    expected = expected_versions(DIGEST, LANGUAGES)
    store = open_store(tmp_path / "state.db", meta=expected)

    assert start_rebuild_on_drift(store, expected) is None
    assert store.index_version == INDEX_VERSION
    assert store.version_mismatch(expected) == []
    store.close()


def test_a_drift_raises_the_generation_so_the_restart_really_rebuilds(tmp_path: Path) -> None:
    # Without this the remedy is a no-op: the crawl requeues every file, the
    # fast path reads state indexed at the same generation and acknowledges each
    # of them without reading a byte, and the index keeps the tokenisation
    # nobody can query it with any more.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES)
    before = store.index_version

    generation = start_rebuild_on_drift(store, expected)

    assert generation == before + 1
    assert store.index_version == generation
    assert store.is_unchanged(4711, "hash-of-b") is False
    store.close()


def test_the_marks_stay_old_until_the_rebuild_is_through(tmp_path: Path) -> None:
    # Raising the generation is not the same as declaring the index current. The
    # banner has to stay up while the work is being done, because it is the only
    # thing telling the admin that hits are still missing.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES)

    start_rebuild_on_drift(store, expected)

    assert "wordlist_hash" in store.version_mismatch(expected)
    store.close()


def test_a_rebuild_that_is_not_through_does_not_stamp(tmp_path: Path) -> None:
    # T-05-48. A mark written too early declares half an index complete, which
    # is worse than the banner it would remove: the admin stops looking for the
    # cause of the missing hits.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES)
    start_rebuild_on_drift(store, expected)

    assert stamp_after_rebuild(store, expected) is False
    assert store.version_mismatch(expected) != []
    store.close()


def test_a_finished_rebuild_stamps_and_the_banner_goes(tmp_path: Path) -> None:
    # The whole chain in one test: drift, raised generation, every file judged
    # again by the running code, marks written, no drift left.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES)
    generation = start_rebuild_on_drift(store, expected)
    assert generation is not None

    store.record(
        4711,
        FileMeta(storage_id=3, root_id=2, path="a/b.txt", title="b.txt", mime="text/plain", size=7, mtime=1, etag="e"),
        "indexed",
        None,
        content_hash="hash-of-b",
    )

    assert stamp_after_rebuild(store, expected) is True
    assert store.version_mismatch(expected) == []
    store.close()


def test_the_stamp_leaves_the_local_generation_alone(tmp_path: Path) -> None:
    # The one mark that must not be written back: index_version is a floor and
    # not an equality, and the local generation stands above the baseline of the
    # code precisely because a rebuild happened. Writing the baseline back would
    # make every row of the finished rebuild look stale and start it over.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES)
    generation = start_rebuild_on_drift(store, expected)
    store.record(
        4711,
        FileMeta(storage_id=3, root_id=2, path="a/b.txt", title="b.txt", mime="text/plain", size=7, mtime=1, etag="e"),
        "indexed",
        None,
        content_hash="hash-of-b",
    )

    stamp_after_rebuild(store, expected)

    assert store.index_version == generation
    assert store.is_unchanged(4711, "hash-of-b") is True
    store.close()


def test_the_stamp_leaves_the_two_marks_of_a_directory_alone(tmp_path: Path) -> None:
    """Audit finding M-19-05, and the state it is about is an ordinary one.

    This stamp stands behind a pass over the holdings in the directory that is
    already there. The schema mark and the language mark describe a directory
    and not a pass, and the one place where what they claim is true is behind
    the directory swap, which is why
    :func:`findling.index.rebuild.stamp_after_swap` is a second stamper with a
    gate of its own (T-18-07-03).

    The volume below is the one every installation upgrading from 1.2.0 stands
    on: a directory of the old layout and the old pair of chains, a container
    that wants six, and a word list that has moved as well. The drift the crawl
    can answer is the word list, and that is the one this stamp may write. If it
    wrote the other two, the marks would promise thirteen fields on a directory
    that carries nine, and since phase 19 that promise is not merely wrong: it
    is what a search computes its field list from.
    """
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, "de,en,es")
    store.write_meta(SCHEMA_MARK, "1")
    store.write_meta(LANGUAGES_MARK, "de,en")
    start_rebuild_on_drift(store, expected)
    store.record(
        4711,
        FileMeta(storage_id=3, root_id=2, path="a/b.txt", title="b.txt", mime="text/plain", size=7, mtime=1, etag="e"),
        "indexed",
        None,
        content_hash="hash-of-b",
    )

    assert stamp_after_rebuild(store, expected) is True

    marks = store.read_meta()
    store.close()

    assert marks[SCHEMA_MARK] == "1"
    assert marks[LANGUAGES_MARK] == "de,en"
    # And the mark of the pass that really happened is written, because a stamp
    # that wrote nothing at all would leave the banner up for ever.
    assert marks["wordlist_hash"] == DIGEST


def test_the_stamp_after_rebuild_leaves_the_dutch_mark_alone(tmp_path: Path) -> None:
    """The seventh mark describes a directory as well, so this stamp skips it.

    Same volume shape as the case above, with Dutch switched on: a pass over the
    holdings in the directory that is already there does not split body_nl with
    a new list, so the mark must stay absent and keep speaking (T-21-05-02).
    """
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES, dutch_mark="1:d")
    start_rebuild_on_drift(store, expected)
    store.record(
        4711,
        FileMeta(storage_id=3, root_id=2, path="a/b.txt", title="b.txt", mime="text/plain", size=7, mtime=1, etag="e"),
        "indexed",
        None,
        content_hash="hash-of-b",
    )

    assert stamp_after_rebuild(store, expected) is True

    marks = store.read_meta()
    diverging = store.version_mismatch(expected)
    store.close()

    assert DUTCH_MARK not in marks
    assert diverging == [DUTCH_MARK]
    assert marks["wordlist_hash"] == DIGEST


def test_a_new_directory_is_stamped_with_the_dutch_mark(tmp_path: Path) -> None:
    """The row "fresh installation with Dutch" of the state table.

    There is no directory yet, so the one about to be built is split with the
    list of this code, and the mark may say so in front of the creation. Nothing
    sets the mark by hand here: the stamp is the only writer.
    """
    expected = expected_versions(DIGEST, LANGUAGES, dutch_mark="1:d")
    store = open_store(tmp_path / "state.db", meta=expected)
    try:
        assert DUTCH_MARK not in store.read_meta()

        assert stamp_a_new_directory(store, tmp_path / "index", expected) is True

        assert store.read_meta()[DUTCH_MARK] == "1:d"
        assert store.version_mismatch(expected) == []
    finally:
        store.close()


def test_a_restart_in_the_middle_does_not_start_the_rebuild_over(tmp_path: Path) -> None:
    # A container that raised the generation on every start would never finish
    # on a box that restarts often: every pass would make the work of the pass
    # before it stale again. The mark of what is being rebuilt towards is what
    # makes the raise happen once per drift and not once per start.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES)
    first = start_rebuild_on_drift(store, expected)

    assert start_rebuild_on_drift(store, expected) is None
    assert store.index_version == first
    store.close()


def test_a_second_drift_during_a_rebuild_starts_a_new_one(tmp_path: Path) -> None:
    # Two updates in a row are the case the mark above must not swallow. The
    # rebuild that is under way was aimed at the code of yesterday, so it is not
    # the rebuild this code needs.
    store = _drifted_store(tmp_path)
    first = start_rebuild_on_drift(store, expected_versions(DIGEST, LANGUAGES))

    second = start_rebuild_on_drift(store, expected_versions("another-digest", LANGUAGES))

    assert first is not None
    assert second == first + 1
    store.close()


def test_a_tombstoned_row_does_not_hold_the_rebuild_open(tmp_path: Path) -> None:
    # A file that was deleted while the rebuild ran will never be judged again,
    # so its old row must not be the reason the marks are never written.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST, LANGUAGES)
    start_rebuild_on_drift(store, expected)
    store.tombstone(4711)

    assert stamp_after_rebuild(store, expected) is True
    store.close()


def test_seeding_still_never_overwrites_a_mark_that_is_there(tmp_path: Path) -> None:
    # The separation this plan rests on. Seeding is a first operation: it fills
    # in what is missing and touches nothing else, so an existing database keeps
    # the marks its index was really built with. Stamping is the opposite and
    # belongs at the end of a rebuild, which is why it is a function of its own
    # and not a flag on the seed.
    path = tmp_path / "state.db"
    first = open_store(path, meta=expected_versions("older-digest", LANGUAGES))
    first.close()

    second = open_store(path, meta=expected_versions(DIGEST, LANGUAGES))

    assert second.read_meta()["wordlist_hash"] == "older-digest"
    second.close()


# -- the whole arrival of a stock installation of 1.2.0 -----------------------
#
# The four cases of plan 18-05 ask Store.version_mismatch about one mark at a
# time. That is the right question for the rule and the wrong one for the
# upgrade: an installation does not arrive carrying one mark, it arrives
# carrying a directory of nine fields, a meta table of five marks and no sixth
# one, and what decides whether the field gets a reindex is what
# start_rebuild_on_drift makes of all of that at once.
#
# The CI leg "Store upgrade 5" asks exactly that of a real volume, and on
# 2026-09-24 it answered with a raised generation, a reindex banner and the
# drift line in the container log, while every unit case in this tree stayed
# green (deploy-harp run 35989391950, leg stable34 on ubuntu-24.04). A promise
# that only holds in a workflow nobody runs between releases is not held. This
# block is that leg, small enough to run in the suite.

# The engine banner of 1.2.0: one patch number behind what this build reports
# and the same index format half, which owner decision E-17-7 option a calls no
# drift. It stands here rather than the current banner because a stock volume
# really carries the old one and this case is about the whole arrival, not about
# one loosened comparison.
BANNER_1_2_0 = "tantivy v0.26.0, index_format v7"

# The tantivy schema mark that every release up to and including 1.2.0 wrote.
SCHEMA_MARK_1_2_0 = "1"


def _stock_volume_of_1_2_0(tmp_path: Path) -> tuple[Path, Store]:
    """The volume of an installation that upgraded from 1.2.0 and changed nothing.

    Three facts, each of them read off the CI probe of the failing run rather
    than invented. The index directory carries the nine field schema, because
    ``Index.open`` reads the persisted schema back and ``build_schema()`` is
    never called on a volume that already has one. The meta table carries the
    five marks of 1.2.0. And the sixth mark is not in it at all, because no
    release ever wrote it and the seed is forbidden to.

    Only two of the five marks are written out here, and that is deliberate:
    those are the two the CI probe measured as really different across the
    upgrade. The analyzer version and the word list digest were measured
    unchanged, so they arrive through ``expected_versions`` instead of as
    literals. A literal would make this case red on the day one of them moves,
    which is a day the upgrade really does drift and a different test's business.
    """
    directory = tmp_path / "index"
    open_schema_1_index(directory)

    store = open_store(tmp_path / "state.db", meta=expected_versions(DIGEST, LANGUAGES))
    store.write_meta("schema_version", SCHEMA_MARK_1_2_0)
    store.write_meta("tantivy_version", BANNER_1_2_0)
    return directory, store


def test_a_stock_volume_of_1_2_0_arrives_without_a_rebuild(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Success criterion 1 of phase 18, asserted the way the CI leg asserts it.

    An installation on the factory setting upgrades and nothing happens to it:
    no mark diverges, no generation is raised, no line goes into the log. The
    stored schema mark stays at 1 and that is not a defect but the truth about
    the directory on disk; it becomes a 2 when the rebuild that makes it true
    has run, and never before (findling.index.rebuild.stamp_after_swap).
    """
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en")
    settings.cache_clear()
    try:
        assert settings().languages == ("de", "en")
        directory, store = _stock_volume_of_1_2_0(tmp_path)
        expected = expected_versions(DIGEST, ",".join(settings().languages))
        before = store.index_version

        with caplog.at_level(logging.WARNING, logger="findling.index.open"):
            index = open_index(directory, CONSTITUENTS)
            _write(index)
            raised = start_rebuild_on_drift(store, expected)

        # The nine field directory takes a write under the eight chains this
        # code registers and answers a query on it, so the volume this case
        # talks about is a working one and not a broken one that drifts for a
        # reason nobody named.
        assert _hits(index, "frist") == 1
        assert store.version_mismatch(expected) == []
        assert raised is None
        assert store.index_version == before
        assert "built by different code" not in caplog.text
        store.close()
    finally:
        settings.cache_clear()


def test_the_same_volume_still_rebuilds_when_a_language_is_switched_on(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The counter case, on the very volume the case above says is quiet.

    Case three of plan 18-05 through the whole path rather than through one
    comparison: the same stock volume, the same schema mark of 1, and Spanish
    switched on. The quiet of the case above is only worth having if this one
    still speaks, so the two stand next to each other.
    """
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en,es")
    settings.cache_clear()
    try:
        assert settings().languages == ("de", "en", "es")
        _, store = _stock_volume_of_1_2_0(tmp_path)
        expected = expected_versions(DIGEST, ",".join(settings().languages))
        before = store.index_version

        raised = start_rebuild_on_drift(store, expected)

        assert store.version_mismatch(expected) == ["languages"]
        assert raised == before + 1
        store.close()
    finally:
        settings.cache_clear()
