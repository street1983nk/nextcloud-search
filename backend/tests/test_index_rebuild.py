"""The rebuild: the precheck of the volume, the band run and the resume after a break.

Two of the three halves are measured against a real index rather than a stand in.
A fake index would answer every question except the ones this module exists for,
because all three of them are properties of tantivy: what ``to_dict()`` hands back,
whether a range query over a fast field really walks the documents in order, and
whether a half written target directory can say on its own how far it got.

The precheck is the exception and is measured against the real volume the tests
run on, with ``FINDLING_MIN_FREE_BYTES`` raised until no machine can satisfy it.
That is the only way to get a refusal without a full disk.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tantivy import Document, Index, Query

from findling.config import settings
from findling.index.open import open_index, open_reader
from findling.index.rebuild import (
    NOT_ENOUGH_ROOM,
    ROOM_ENOUGH,
    RebuildRun,
    _document_from,
    _resume_cursor,
    counts_match,
    may_rebuild,
    transfer_documents,
)
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.store.repo import open_store

REBUILD_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "index" / "rebuild.py"

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

# The eight fields to_dict() hands back, measured on 2026-09-24 against the real
# build_schema(). body_en is not among them because it was never stored, which is
# the whole reason the rebuild reconstructs it out of body_de.
STORED_FIELDS = (
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)

# More than any volume this suite ever runs on, so the refusal is about the floor
# and never about the machine.
IMPOSSIBLE_FLOOR = str(1 << 60)


def _stage(index: Index, documents: Sequence[Mapping[str, object]]) -> None:
    """Write documents into an index the way the writer of the app writes them."""
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for values in documents:
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, int(values[FIELD_FILE_ID]))  # pyright: ignore[reportArgumentType]
        document.add_unsigned(FIELD_STORAGE_ID, int(values[FIELD_STORAGE_ID]))  # pyright: ignore[reportArgumentType]
        document.add_text(FIELD_NAME, str(values[FIELD_NAME]))
        document.add_text(FIELD_TITLE, str(values[FIELD_TITLE]))
        document.add_text(FIELD_PATH, str(values[FIELD_PATH]))
        document.add_text(FIELD_EXT, str(values[FIELD_EXT]))
        document.add_text(FIELD_BODY_DE, str(values[FIELD_BODY_DE]))
        document.add_integer(FIELD_MTIME, int(values[FIELD_MTIME]))  # pyright: ignore[reportArgumentType]
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()


def _document(file_id: int, **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        FIELD_FILE_ID: file_id,
        FIELD_STORAGE_ID: 7,
        FIELD_NAME: f"Kuendigung-{file_id}.pdf",
        FIELD_TITLE: f"Kuendigung {file_id}",
        FIELD_PATH: f"/Vertraege/{file_id}.pdf",
        FIELD_EXT: "pdf",
        FIELD_BODY_DE: f"Die Kuendigungsfrist betraegt {file_id} Monate.",
        FIELD_MTIME: 1_700_000_000 + file_id,
    }
    values.update(overrides)
    return values


def _stored(index: Index) -> dict[int, dict[str, list[object]]]:
    """Every document of an index, keyed by file_id, as to_dict() hands it back."""
    index.reload()
    searcher = index.searcher()
    everything: dict[int, dict[str, list[object]]] = {}
    for _score, address in searcher.search(Query.all_query(), limit=searcher.num_docs or 1).hits:
        values = searcher.doc(address).to_dict()
        everything[int(values[FIELD_FILE_ID][0])] = values
    return everything


@pytest.fixture(autouse=True)
def _cold_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test resolves the settings itself, on an environment nobody else set."""
    for name in ("APP_PERSISTENT_STORAGE", "FINDLING_MIN_FREE_BYTES", "FINDLING_LANGUAGES"):
        monkeypatch.delenv(name, raising=False)
    settings.cache_clear()


def test_a_floor_no_volume_can_satisfy_refuses_the_start(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", IMPOSSIBLE_FLOOR)
    settings.cache_clear()

    verdict = may_rebuild(tmp_path, 4)

    assert verdict.may_start is False
    assert verdict.reason == NOT_ENOUGH_ROOM


def test_the_refusal_carries_both_numbers_it_was_decided_on(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The banner names the figures, so the verdict has to carry them.

    A banner that measured the volume again would print two numbers that were
    never true at the same moment.
    """
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", IMPOSSIBLE_FLOOR)
    settings.cache_clear()

    verdict = may_rebuild(tmp_path, 4)

    assert verdict.needed_bytes >= 0
    assert verdict.free_bytes > 0


def test_the_warning_of_a_refusal_names_no_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T-18-06-02: the lines of this module count bytes and name nothing."""
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", IMPOSSIBLE_FLOOR)
    settings.cache_clear()

    with caplog.at_level("WARNING", logger="findling.index.rebuild"):
        may_rebuild(tmp_path, 4)

    assert caplog.records
    assert not any(tmp_path.name in record.getMessage() for record in caplog.records)


def test_an_ordinary_volume_lets_the_rebuild_start(tmp_path: Path) -> None:
    verdict = may_rebuild(tmp_path, 4)

    assert verdict.may_start is True
    assert verdict.reason == ROOM_ENOUGH


def test_an_empty_directory_needs_nothing_and_may_start(tmp_path: Path) -> None:
    """A rebuild of an index of zero byte is refused by nothing here.

    index_bytes answers 0 for a directory with no segments in it, so the need is
    0 and the floor alone decides. There is nothing to carry over, which is a
    question for the caller and not for the precheck.
    """
    verdict = may_rebuild(tmp_path, 6)

    assert verdict.needed_bytes == 0
    assert verdict.may_start is True


def test_every_new_language_raises_the_need(tmp_path: Path) -> None:
    """The factor is per chain, so four chains want more room than one.

    Measured over a directory that holds something: the file below is not an
    index, and it does not have to be, because index_bytes sums bytes and the
    factor multiplies them.
    """
    (tmp_path / "segment").write_bytes(b"x" * 1_000_000)

    one = may_rebuild(tmp_path, 1)
    four = may_rebuild(tmp_path, 4)

    assert one.needed_bytes == 1_400_000
    assert four.needed_bytes == 2_600_000


def test_every_document_arrives_with_every_stored_field_unchanged(tmp_path: Path) -> None:
    """The proof of the run, field by field and not by a hit count.

    A hit count would be green for an index that carried the text and lost the
    title, and the title is the field the search weighs highest.
    """
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 31)])
    before = _stored(source)

    run = transfer_documents(tmp_path / "index", tmp_path / "index.rebuild", CONSTITUENTS, ("de", "en"))

    after = _stored(open_index(tmp_path / "index.rebuild", CONSTITUENTS))
    assert run.documents_written == 30
    assert sorted(after) == sorted(before)
    for file_id, values in before.items():
        for field in STORED_FIELDS:
            assert after[file_id][field] == values[field], f"{field} of document {file_id} did not survive the run"


def test_the_run_ends_with_the_same_number_of_documents(tmp_path: Path) -> None:
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 13)])

    run = transfer_documents(tmp_path / "index", tmp_path / "index.rebuild", CONSTITUENTS, ("de", "en"))

    assert run.source_documents == run.target_documents == 12
    assert run.complete is True


def test_the_three_measured_edge_values_survive_the_run(tmp_path: Path) -> None:
    """Empty string, negative mtime and a storage_id of 2 to the 40th.

    All three were measured on 2026-09-24, and all three are the kind of value a
    rebuild written against the happy path quietly replaces with a default.
    """
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(
        source,
        [
            _document(1, **{FIELD_EXT: "", FIELD_BODY_DE: ""}),
            _document(2, **{FIELD_MTIME: -5}),
            _document(3, **{FIELD_STORAGE_ID: 2**40}),
        ],
    )

    transfer_documents(tmp_path / "index", tmp_path / "index.rebuild", CONSTITUENTS, ("de", "en"))

    after = _stored(open_index(tmp_path / "index.rebuild", CONSTITUENTS))
    assert after[1][FIELD_EXT] == [""]
    assert after[1][FIELD_BODY_DE] == [""]
    assert after[2][FIELD_MTIME] == [-5]
    assert after[3][FIELD_STORAGE_ID] == [2**40]


def test_the_text_reaches_the_chain_of_every_active_language(tmp_path: Path) -> None:
    """body_en was never stored, so it has to be rebuilt out of body_de.

    Asked as a question and not as a field comparison, because body_en does not
    come back out of the document store at all: if the reconstruction were left
    out, this query would answer nothing and no stored value would be missing.
    """
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(source, [_document(1, **{FIELD_BODY_DE: "the notice period is three months"})])

    transfer_documents(tmp_path / "index", tmp_path / "index.rebuild", CONSTITUENTS, ("de", "en"))

    target = open_index(tmp_path / "index.rebuild", CONSTITUENTS)
    target.reload()
    searcher = open_reader(target)
    hits = searcher.search(target.parse_query("notice", ["body_en"]), limit=5).hits

    assert len(hits) == 1


def test_an_empty_target_resumes_at_zero(tmp_path: Path) -> None:
    target = open_index(tmp_path / "index.rebuild", CONSTITUENTS)

    assert _resume_cursor(target) == 0


def test_a_half_written_target_names_its_highest_file_id(tmp_path: Path) -> None:
    target = open_index(tmp_path / "index.rebuild", CONSTITUENTS)
    _stage(target, [_document(file_id) for file_id in (3, 17, 9)])

    assert _resume_cursor(target) == 17


def test_a_run_that_broke_off_carries_on_where_it_stopped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The half written target directory is the whole progress record.

    The break is staged where a crash would hit, in the middle of the third
    band, so that two bands are committed and the third is not. The second run
    gets no hint at all beyond the directory it finds.
    """
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 10)])
    store = open_store(tmp_path / "state.db")
    before = store.read_meta()
    store.close()

    honest = _document_from
    seen = 0

    def breaks_in_the_third_band(stored: Mapping[str, list[object]], languages: Sequence[str]) -> Document:
        nonlocal seen
        seen += 1
        if seen > 4:
            message = "staged break in the middle of the third band"
            raise RuntimeError(message)
        return honest(stored, languages)

    monkeypatch.setattr("findling.index.rebuild._document_from", breaks_in_the_third_band)
    with pytest.raises(RuntimeError):
        transfer_documents(
            tmp_path / "index",
            tmp_path / "index.rebuild",
            CONSTITUENTS,
            ("de", "en"),
            band_documents=2,
        )
    monkeypatch.undo()

    assert _resume_cursor(open_index(tmp_path / "index.rebuild", CONSTITUENTS)) == 4

    run = transfer_documents(
        tmp_path / "index",
        tmp_path / "index.rebuild",
        CONSTITUENTS,
        ("de", "en"),
        band_documents=2,
    )

    assert run.documents_written == 5
    assert run.target_documents == 9
    assert run.complete is True

    store = open_store(tmp_path / "state.db")
    after = store.read_meta()
    store.close()

    assert sorted(after) == sorted(before)


def test_a_finished_run_that_is_started_again_writes_nothing(tmp_path: Path) -> None:
    """The resume is also the answer to a run that had nothing left to do."""
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 6)])
    transfer_documents(tmp_path / "index", tmp_path / "index.rebuild", CONSTITUENTS, ("de", "en"))

    again = transfer_documents(tmp_path / "index", tmp_path / "index.rebuild", CONSTITUENTS, ("de", "en"))

    assert again.documents_written == 0
    assert again.target_documents == 5


def test_the_final_probe_says_no_while_a_document_is_missing(tmp_path: Path) -> None:
    """The gate in front of the swap of plan 18-07, as a function of its own."""
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 6)])
    target = open_index(tmp_path / "index.rebuild", CONSTITUENTS)
    _stage(target, [_document(file_id) for file_id in range(1, 5)])

    assert counts_match(source, target) is False

    _stage(target, [_document(5)])

    assert counts_match(source, target) is True


def test_the_run_reports_every_number_the_caller_decides_on(tmp_path: Path) -> None:
    source = open_index(tmp_path / "index", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 4)])

    run = transfer_documents(tmp_path / "index", tmp_path / "index.rebuild", CONSTITUENTS, ("de", "en"))

    assert isinstance(run, RebuildRun)
    assert (run.documents_written, run.source_documents, run.target_documents) == (3, 3, 3)


def test_the_band_walks_the_documents_and_never_pages_with_an_offset() -> None:
    """Static, because a deep offset is not wrong on the day it is written.

    Measured on 2026-09-24: search(all_query, limit=1000, offset=51000) makes
    tantivy collect 52000 hits to hand out 1000, which is quadratic over a whole
    run. The band over the fast field is linear, and nothing in this module may
    quietly go back to paging.
    """
    source = REBUILD_SOURCE.read_text(encoding="utf-8")
    offenders = [
        node.lineno for node in ast.walk(ast.parse(source)) if isinstance(node, ast.keyword) and node.arg == "offset"
    ]

    assert offenders == []
    assert "range_query" in source


def test_the_rebuild_keeps_no_progress_of_its_own_in_the_state_database() -> None:
    """Static half of the resume: the module cannot write a second progress record.

    The one thing it may take out of the store module is the size sum, which
    reads bytes and writes nothing. A second progress record beside the index is
    exactly the state that can disagree with the index; the index cannot
    disagree with itself.
    """
    tree = ast.parse(REBUILD_SOURCE.read_text(encoding="utf-8"))
    imported = [
        (node.module, alias.name)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("findling.store")
        for alias in node.names
    ]

    assert imported == [("findling.store.repo", "index_bytes")]
