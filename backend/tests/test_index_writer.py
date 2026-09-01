"""The one writer: idempotent writing, batched commits and the disk guard.

Three of the tests below are static, and that is deliberate. Whether a document
is built field by field, whether the upsert uses the current deletion API and
whether a second writer is recognised are properties of the code rather than of
one run: the wrong version of the first two does not fail, it produces a panic in
a background thread of tantivy after the Python call has already returned, and a
test that waits for an exception waits forever.

Measured on tantivy 0.26.0 while writing this file:

* ``Document(file_id=42)`` and ``document.add_integer("file_id", 42)`` both put an
  I64 into the U64 column of a fast unsigned field. The indexing thread panics
  with "Input type forbidden. This column has been forced to type U64, received
  I64(42)" and the Python call returns success.
* ``Document.from_dict`` silently drops a field the schema does not know, so a
  misspelled field name loses the value without an error anywhere.
* The old deletion name still exists in 0.26.0 and emits no DeprecationWarning on
  this build, contrary to the note in the phase research. It stays out of this
  module all the same: it is the name the bindings deprecated, and the suite
  turns that warning into an error the moment it starts being raised.
"""

import ast
import shutil
import warnings
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace

import pytest
from tantivy import Document, Index, IndexWriter

from findling.config import settings
from findling.index.open import open_index
from findling.index.schema import FIELD_BODY_DE, FIELD_BODY_EN, FIELD_FILE_ID, FIELD_STORAGE_ID
from findling.index.writer import (
    FLUSH_COMMITTED,
    FLUSH_NOTHING_PENDING,
    FLUSH_PAUSED_LOW_DISK,
    IndexBatchWriter,
    IndexLockedError,
    IndexRecord,
)

WRITER_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "index" / "writer.py"

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

GERMAN_BODY = "Die Kündigungsfrist beträgt drei Monate."
ENGLISH_BODY = "The notice period is three months."


def _record(file_id: int = 1, *, body: str = GERMAN_BODY, name: str = "Kündigung.pdf") -> IndexRecord:
    return IndexRecord(
        file_id=file_id,
        storage_id=7,
        name=name,
        title="Kündigung",
        path="/Verträge/Kündigung.pdf",
        ext="pdf",
        body=body,
        mtime=1_700_000_000,
    )


def _write_raw(writer: IndexWriter, record: IndexRecord) -> None:
    """Write past IndexBatchWriter, for the tests that measure the binding itself."""
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, record.file_id)
    document.add_unsigned(FIELD_STORAGE_ID, record.storage_id)
    document.add_text(FIELD_BODY_DE, record.body)
    writer.add_document(document)


def _hits(index: Index, query: str, fields: list[str] | None = None) -> int:
    index.reload()
    searcher = index.searcher()
    parsed = index.parse_query(query, fields if fields is not None else [FIELD_BODY_DE])
    return len(searcher.search(parsed, 10).hits)


def _low_disk(_: object) -> SimpleNamespace:
    """One kilobyte free: far below every configured floor."""
    return SimpleNamespace(total=1_000_000, used=999_000, free=1_024)


@pytest.fixture
def index_dir(tmp_path: Path) -> Path:
    return tmp_path / "index"


@pytest.fixture
def index(index_dir: Path) -> Index:
    return open_index(index_dir, CONSTITUENTS)


@pytest.fixture
def batch_writer(index: Index, index_dir: Path) -> Iterator[IndexBatchWriter]:
    writer = IndexBatchWriter(index, directory=index_dir)
    yield writer
    writer.close()


def test_a_committed_document_is_findable_on_body_de(index: Index, batch_writer: IndexBatchWriter) -> None:
    batch_writer.add(_record())

    result = batch_writer.flush()

    assert result.state == FLUSH_COMMITTED
    assert result.documents == 1
    assert _hits(index, "frist") == 1


def test_the_same_file_id_written_twice_leaves_exactly_one_document(
    index: Index, batch_writer: IndexBatchWriter
) -> None:
    batch_writer.add(_record(42, body="Die alte Kündigungsfrist beträgt drei Monate."))
    batch_writer.flush()

    batch_writer.add(_record(42, body="Die neue Kündigungsfrist beträgt sechs Monate."))
    batch_writer.flush()

    index.reload()
    assert index.searcher().num_docs == 1
    assert _hits(index, "sechs") == 1
    assert _hits(index, "alte") == 0


def test_the_identifiers_come_back_as_unsigned_values(index: Index, batch_writer: IndexBatchWriter) -> None:
    # The runtime half of pitfall 8: a signed value in these columns kills the
    # indexing thread instead of raising, so the round trip is the assertion.
    batch_writer.add(_record(42))
    batch_writer.flush()
    index.reload()
    searcher = index.searcher()
    address = searcher.search(index.parse_query("frist", [FIELD_BODY_DE]), 10).hits[0][1]

    assert searcher.fast_field_values(FIELD_FILE_ID, [address]) == [42]
    assert searcher.fast_field_values(FIELD_STORAGE_ID, [address]) == [7]


def test_the_writer_never_builds_a_document_from_keyword_arguments() -> None:
    offenders = [
        f"line {node.lineno}"
        for node in ast.walk(ast.parse(WRITER_SOURCE.read_text(encoding="utf-8")))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Document"
        and node.keywords
    ]

    assert offenders == [], "documents are built field by field, never from keyword arguments: " + ", ".join(offenders)


def test_the_upsert_deletes_through_the_schema_and_not_by_a_raw_term() -> None:
    source = WRITER_SOURCE.read_text(encoding="utf-8")
    calls = {
        node.func.attr
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }

    assert "delete_documents_by_query" in calls
    # Neither the deprecated name nor the one that quietly deletes nothing on an
    # unsigned key; the test below measures why.
    assert "delete_documents" not in calls
    assert "delete_documents_by_term" not in calls


def test_deleting_by_term_does_not_reach_the_unsigned_key(index: Index, index_dir: Path) -> None:
    # A tripwire on the binding, not on our code. Deleting by term builds an I64
    # term from a Python integer, and the U64 column of file_id holds no such
    # term: nothing is raised and nothing is deleted. The day tantivy fixes that,
    # this test turns red and the upsert may take the shorter route again.
    raw_writer = index.writer(heap_size=15_000_000, num_threads=1)
    first = _record(42, body="Die alte Kündigungsfrist beträgt drei Monate.")
    second = _record(42, body="Die neue Kündigungsfrist beträgt sechs Monate.")
    _write_raw(raw_writer, first)
    raw_writer.commit()

    raw_writer.delete_documents_by_term(FIELD_FILE_ID, 42)
    _write_raw(raw_writer, second)
    raw_writer.commit()
    raw_writer.wait_merging_threads()
    index.reload()

    assert index.searcher().num_docs == 2


def test_writing_and_committing_raises_no_warning(batch_writer: IndexBatchWriter) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")

        batch_writer.add(_record())
        batch_writer.flush()


def test_flush_below_the_free_disk_floor_pauses_and_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, index: Index, batch_writer: IndexBatchWriter
) -> None:
    monkeypatch.setattr(shutil, "disk_usage", _low_disk)
    batch_writer.add(_record())

    result = batch_writer.flush()

    assert result.state == FLUSH_PAUSED_LOW_DISK
    assert result.free_bytes == 1_024
    index.reload()
    assert index.searcher().num_docs == 0


def test_a_paused_flush_leaves_the_search_answering(
    monkeypatch: pytest.MonkeyPatch, index: Index, batch_writer: IndexBatchWriter
) -> None:
    # A full volume is a state, not an outage: what is already committed stays
    # readable while the indexer waits.
    batch_writer.add(_record(1))
    batch_writer.flush()
    monkeypatch.setattr(shutil, "disk_usage", _low_disk)
    batch_writer.add(_record(2))

    assert batch_writer.flush().state == FLUSH_PAUSED_LOW_DISK
    assert _hits(index, "frist") == 1


def test_the_pending_batch_is_committed_once_the_disk_is_free_again(
    monkeypatch: pytest.MonkeyPatch, index: Index, batch_writer: IndexBatchWriter
) -> None:
    monkeypatch.setattr(shutil, "disk_usage", _low_disk)
    batch_writer.add(_record())
    batch_writer.flush()

    monkeypatch.undo()

    assert batch_writer.flush().state == FLUSH_COMMITTED
    assert _hits(index, "frist") == 1


def test_documents_survive_closing_and_reopening(index: Index, index_dir: Path) -> None:
    writer = IndexBatchWriter(index, directory=index_dir)
    writer.add(_record())
    writer.flush()
    writer.close()

    reopened = open_index(index_dir, CONSTITUENTS)

    assert _hits(reopened, "frist") == 1


def test_a_second_writer_on_the_same_directory_is_reported_as_locked(
    index: Index, index_dir: Path, batch_writer: IndexBatchWriter
) -> None:
    # Measured: the second writer answers "Failed to acquire Lockfile: LockBusy".
    # Unwrapped it reads like a corrupt index instead of like two writers. The
    # first writer is the fixture; it is still open while this one is refused.
    assert batch_writer.should_flush is False

    with pytest.raises(IndexLockedError):
        IndexBatchWriter(index, directory=index_dir)


def test_the_lock_is_released_when_the_writer_is_closed(index: Index, index_dir: Path) -> None:
    first = IndexBatchWriter(index, directory=index_dir)
    first.close()

    second = IndexBatchWriter(index, directory=index_dir)
    second.close()


def test_body_en_stays_empty_when_only_german_is_configured(
    monkeypatch: pytest.MonkeyPatch, index: Index, index_dir: Path
) -> None:
    monkeypatch.setenv("FINDLING_LANGUAGES", "de")
    settings.cache_clear()
    try:
        writer = IndexBatchWriter(index, directory=index_dir)
        writer.add(_record(body=ENGLISH_BODY))
        writer.flush()
        writer.close()

        assert _hits(index, "notice", [FIELD_BODY_EN]) == 0
        assert _hits(index, "notice", [FIELD_BODY_DE]) == 1
    finally:
        settings.cache_clear()


def test_flush_without_pending_documents_commits_nothing(batch_writer: IndexBatchWriter) -> None:
    result = batch_writer.flush()

    assert result.state == FLUSH_NOTHING_PENDING
    assert result.documents == 0


def test_collect_garbage_keeps_the_committed_documents(index: Index, batch_writer: IndexBatchWriter) -> None:
    # Cleaning up orphaned segment files is housekeeping, never recovery: after a
    # hard kill the index opens on the last commit all by itself.
    batch_writer.add(_record())
    batch_writer.flush()

    batch_writer.collect_garbage()

    assert _hits(index, "frist") == 1


def test_should_flush_follows_the_configured_batch_caps(index: Index, index_dir: Path) -> None:
    writer = IndexBatchWriter(index, directory=index_dir, batch_files=2)
    try:
        writer.add(_record(1))
        assert writer.should_flush is False

        writer.add(_record(2))

        assert writer.should_flush is True
    finally:
        writer.close()


def test_a_closed_writer_refuses_further_work(index: Index, index_dir: Path) -> None:
    writer = IndexBatchWriter(index, directory=index_dir)
    writer.close()

    with pytest.raises(RuntimeError, match="closed"):
        writer.add(_record())


def test_stored_body_returns_the_text_that_was_written(batch_writer: IndexBatchWriter) -> None:
    # body_de is the only stored copy of the text in the whole system. That it
    # can be read back is the entire reason a rename needs no download.
    batch_writer.add(_record(42, body=GERMAN_BODY))
    batch_writer.flush()

    assert batch_writer.stored_body(42) == GERMAN_BODY


def test_stored_body_returns_none_for_unknown_file(batch_writer: IndexBatchWriter) -> None:
    # Not an error. A file that was never indexed, or one that ended as skipped,
    # has no stored text, and the metadata job turns into a content job for it.
    batch_writer.add(_record(42))
    batch_writer.flush()

    assert batch_writer.stored_body(4711) is None


def test_stored_body_reads_a_document_of_an_earlier_run(index: Index, index_dir: Path) -> None:
    # The rename usually arrives days after the indexing, so the text has to
    # come out of a writer that never wrote it.
    first = IndexBatchWriter(index, directory=index_dir)
    first.add(_record(42))
    first.flush()
    first.close()

    reopened = open_index(index_dir, CONSTITUENTS)
    second = IndexBatchWriter(reopened, directory=index_dir)
    try:
        assert second.stored_body(42) == GERMAN_BODY
    finally:
        second.close()


def test_dropped_document_is_not_found_after_commit(index: Index, batch_writer: IndexBatchWriter) -> None:
    # The proof that the delete path of D-10 actually deletes. The failure it
    # guards against is silent: a deletion built from the field name instead of
    # from the schema raises nothing, deletes nothing, and leaves the document
    # findable while every counter reports success.
    batch_writer.add(_record(42))
    batch_writer.flush()
    assert _hits(index, "frist") == 1

    batch_writer.drop_document(42)
    batch_writer.flush()

    assert _hits(index, "frist") == 0
    index.reload()
    assert index.searcher().num_docs == 0


def test_a_dropped_document_makes_the_flush_commit_at_all(index: Index, batch_writer: IndexBatchWriter) -> None:
    # A batch of nothing but deletions has no added document, and a flush that
    # only counted additions would answer nothing_pending and leave the deletion
    # sitting in the writer. The file would stay findable until some unrelated
    # file happened to be indexed, which is the same bug as not deleting at all,
    # only harder to reproduce.
    batch_writer.add(_record(42))
    batch_writer.flush()

    batch_writer.drop_document(42)

    assert batch_writer.pending == 1
    assert batch_writer.flush().state == FLUSH_COMMITTED
    assert _hits(index, "frist") == 0


def test_dropping_an_unknown_file_id_is_harmless(index: Index, batch_writer: IndexBatchWriter) -> None:
    # A delete job carries no proof that the document was ever indexed, and it
    # must not need one: the file is gone, so nobody can look.
    batch_writer.add(_record(42))
    batch_writer.flush()

    batch_writer.drop_document(4711)
    batch_writer.flush()

    assert _hits(index, "frist") == 1


def test_a_closed_writer_refuses_to_drop(index: Index, index_dir: Path) -> None:
    writer = IndexBatchWriter(index, directory=index_dir)
    writer.close()

    with pytest.raises(RuntimeError, match="closed"):
        writer.drop_document(42)


def test_drop_document_builds_its_term_through_the_schema() -> None:
    # The same I64 against U64 mismatch as the upsert, with the worst possible
    # consequence: a term built from the field name matches nothing, the document
    # stays in the index, and the pass reports a successful deletion.
    tree = ast.parse(WRITER_SOURCE.read_text(encoding="utf-8"))
    method = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "drop_document"
    )
    calls = [node for node in ast.walk(method) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    by_name = {node.func.attr for node in calls if isinstance(node.func, ast.Attribute)}

    assert "delete_documents_by_query" in by_name
    terms = [node for node in calls if isinstance(node.func, ast.Attribute) and node.func.attr == "term_query"]
    assert len(terms) == 1
    first = terms[0].args[0]
    assert isinstance(first, ast.Attribute)
    assert first.attr == "_schema"


def test_stored_body_builds_its_term_through_the_schema() -> None:
    # The same I64 against U64 mismatch as the upsert, with a quieter failure:
    # a term built from the field name matches nothing, stored_body answers None
    # for every file, and every rename falls back to a download nobody asked for.
    tree = ast.parse(WRITER_SOURCE.read_text(encoding="utf-8"))
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "stored_body")
    terms = [
        node
        for node in ast.walk(method)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "term_query"
    ]

    assert len(terms) == 1
    first = terms[0].args[0]
    assert isinstance(first, ast.Attribute)
    assert first.attr == "_schema"
