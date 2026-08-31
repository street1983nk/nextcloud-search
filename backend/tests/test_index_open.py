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
from pathlib import Path

import pytest
from tantivy import Document, Index

from findling.config import INDEX_VERSION, SCHEMA_VERSION, settings
from findling.index.analyzer import ANALYZER_VERSION, build_count
from findling.index.open import TANTIVY_VERSION, expected_versions, open_index, open_reader
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_BODY_EN,
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

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# The single module that may open an index. Everything else has to go through it,
# because opening is registering.
OPENING_MODULE = "index/open.py"

# The same fixture the analyzer table runs on: the subset of the real Debian list
# that occurs inside the test inputs, proven token identical to the full list.
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

# One digest for the version marks. The value is never interpreted here, it only
# has to travel from the caller into the expectation unchanged.
DIGEST = "0" * 64


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


def test_the_schema_carries_exactly_the_nine_documented_fields() -> None:
    assert FIELDS == (
        FIELD_FILE_ID,
        FIELD_STORAGE_ID,
        FIELD_NAME,
        FIELD_TITLE,
        FIELD_PATH,
        FIELD_EXT,
        FIELD_BODY_DE,
        FIELD_BODY_EN,
        FIELD_MTIME,
    )
    assert len(FIELDS) == 9
    assert len(set(FIELDS)) == 9


def test_a_document_carrying_all_nine_fields_is_accepted(index_dir: Path) -> None:
    index = open_index(index_dir, CONSTITUENTS)

    _write(index)

    assert index.searcher().num_docs == 1


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

        assert len(FIELDS) == 9
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
    expected = expected_versions(DIGEST)

    assert expected == {
        "schema_version": str(SCHEMA_VERSION),
        "index_version": str(INDEX_VERSION),
        "analyzer_version": str(ANALYZER_VERSION),
        "wordlist_hash": DIGEST,
        "tantivy_version": TANTIVY_VERSION,
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
