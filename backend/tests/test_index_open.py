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
from findling.index.open import (
    TANTIVY_VERSION,
    expected_versions,
    open_index,
    open_reader,
    stamp_after_rebuild,
    start_rebuild_on_drift,
)
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
from findling.store.repo import FileMeta, Store, open_store

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
    store = open_store(tmp_path / "state.db", meta=expected_versions("older-digest"))
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
    expected = expected_versions(DIGEST)
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
    expected = expected_versions(DIGEST)
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
    expected = expected_versions(DIGEST)

    start_rebuild_on_drift(store, expected)

    assert "wordlist_hash" in store.version_mismatch(expected)
    store.close()


def test_a_rebuild_that_is_not_through_does_not_stamp(tmp_path: Path) -> None:
    # T-05-48. A mark written too early declares half an index complete, which
    # is worse than the banner it would remove: the admin stops looking for the
    # cause of the missing hits.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST)
    start_rebuild_on_drift(store, expected)

    assert stamp_after_rebuild(store, expected) is False
    assert store.version_mismatch(expected) != []
    store.close()


def test_a_finished_rebuild_stamps_and_the_banner_goes(tmp_path: Path) -> None:
    # The whole chain in one test: drift, raised generation, every file judged
    # again by the running code, marks written, no drift left.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST)
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
    expected = expected_versions(DIGEST)
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


def test_a_restart_in_the_middle_does_not_start_the_rebuild_over(tmp_path: Path) -> None:
    # A container that raised the generation on every start would never finish
    # on a box that restarts often: every pass would make the work of the pass
    # before it stale again. The mark of what is being rebuilt towards is what
    # makes the raise happen once per drift and not once per start.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST)
    first = start_rebuild_on_drift(store, expected)

    assert start_rebuild_on_drift(store, expected) is None
    assert store.index_version == first
    store.close()


def test_a_second_drift_during_a_rebuild_starts_a_new_one(tmp_path: Path) -> None:
    # Two updates in a row are the case the mark above must not swallow. The
    # rebuild that is under way was aimed at the code of yesterday, so it is not
    # the rebuild this code needs.
    store = _drifted_store(tmp_path)
    first = start_rebuild_on_drift(store, expected_versions(DIGEST))

    second = start_rebuild_on_drift(store, expected_versions("another-digest"))

    assert first is not None
    assert second == first + 1
    store.close()


def test_a_tombstoned_row_does_not_hold_the_rebuild_open(tmp_path: Path) -> None:
    # A file that was deleted while the rebuild ran will never be judged again,
    # so its old row must not be the reason the marks are never written.
    store = _drifted_store(tmp_path)
    expected = expected_versions(DIGEST)
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
    first = open_store(path, meta=expected_versions("older-digest"))
    first.close()

    second = open_store(path, meta=expected_versions(DIGEST))

    assert second.read_meta()["wordlist_hash"] == "older-digest"
    second.close()
