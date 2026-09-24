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
import gc
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tantivy import Document, Index, Query

from conftest import Corpus
from findling.api import resources
from findling.config import settings
from findling.index.open import open_index, open_reader
from findling.index.rebuild import (
    NOT_ENOUGH_ROOM,
    ROOM_ENOUGH,
    RebuildRun,
    _document_from,
    _resume_cursor,
    counts_match,
    discard_directory,
    may_rebuild,
    retire_directory,
    swap_in,
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


# -- the swap, and the reason its order is its whole content -------------------
#
# None of the cases below is skipped on a platform, and that is deliberate. The
# mistake they are about, a rename with a handle still open, is loud on Windows
# (PermissionError, WinError 5, measured on 2026-09-24) and silent on Linux,
# where POSIX renames over inodes and the reading side goes on answering out of
# a directory that has no name any more. A case that is skipped on the
# development machine throws away the only system that makes the mistake fail.


def _documents_in(path: Path) -> int:
    """How many documents the directory at ``path`` answers with, right now."""
    index = open_index(path, CONSTITUENTS)
    index.reload()
    return index.searcher().num_docs


def _documents_the_search_sees() -> int:
    """The same question, asked through the cached read side of the container.

    The handle stays in the module cache of :mod:`findling.api.resources` and
    deliberately not in a local of the caller: what the swap has to survive is
    the process cache, and a local reference in a test would be a handle the
    running container never has.
    """
    side = resources.read_side()
    assert side is not None
    side.index.reload()
    return side.index.searcher().num_docs


def test_the_swap_puts_the_rebuilt_directory_where_the_live_one_stood(tmp_path: Path) -> None:
    live = tmp_path / "index"
    target = tmp_path / "index.rebuild"
    source = open_index(live, CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 4)])
    rebuilt = open_index(target, CONSTITUENTS)
    _stage(rebuilt, [_document(file_id) for file_id in range(1, 9)])
    # Every handle on both directories goes first, which is step 1 and step 2 of
    # the order in the module header.
    del source, rebuilt
    gc.collect()

    swap_in(target, live)

    assert live.is_dir()
    assert not target.exists()
    assert not (tmp_path / "index.retired").exists()
    assert _documents_in(live) == 8


def test_after_the_swap_the_container_answers_out_of_the_new_directory(indexed_volume: Corpus) -> None:
    """The truth of this plan, asked of the read side rather than of the disk.

    On Linux the rename alone would leave this assertion at the old figure and
    nothing would say so; that is what the reset in front of it is for.
    """
    live = indexed_volume.root / "index"
    target = indexed_volume.root / "index.rebuild"
    before = _documents_the_search_sees()
    assert before == indexed_volume.documents

    rebuilt = open_index(target, CONSTITUENTS)
    _stage(rebuilt, [_document(file_id) for file_id in range(1, before + 4)])
    del rebuilt
    gc.collect()

    resources.reset_read_side()
    gc.collect()
    swap_in(target, live)

    assert _documents_the_search_sees() == before + 3


def test_a_searcher_that_was_not_let_go_is_the_mistake_this_order_prevents(tmp_path: Path) -> None:
    """Defined on both systems, skipped on neither, and different on each.

    Windows refuses and the mistake is a stack trace. Linux accepts and the
    mistake is a container that answers out of a directory without a name, so
    there the case asserts the silence itself. Those are the two halves of one
    statement, and a mark that skipped the case would keep whichever half the
    machine of the day happens to be worse at proving.
    """
    live = tmp_path / "index"
    target = tmp_path / "index.rebuild"
    source = open_index(live, CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 4)])
    source.reload()
    held = source.searcher()
    assert held.num_docs == 3
    rebuilt = open_index(target, CONSTITUENTS)
    _stage(rebuilt, [_document(file_id) for file_id in range(1, 9)])
    del rebuilt
    gc.collect()

    if sys.platform == "win32":
        with pytest.raises(PermissionError):
            swap_in(target, live)
        assert live.is_dir(), "nothing moved, so the container still answers out of the directory it knows"
        assert target.is_dir()
    else:
        swap_in(target, live)
        assert held.num_docs == 3, "the retired directory answers on, and no line anywhere says so"
        assert _documents_in(live) == 8


def test_the_retired_name_is_derived_from_the_live_one_and_stays_beside_it(tmp_path: Path) -> None:
    """T-18-07-04: the path that gets removed is never handed in from outside."""
    live = tmp_path / "index"
    live.mkdir()
    (live / "meta.json").write_text("{}", encoding="utf-8")

    retired = retire_directory(live)

    assert retired.parent == live.parent
    assert retired.name == "index.retired"
    assert not live.exists()
    assert (retired / "meta.json").is_file()


def test_a_retired_directory_that_will_not_go_is_a_finding(tmp_path: Path) -> None:
    """ignore_errors is False: a leftover keeps the clean up path of the next start busy."""
    with pytest.raises(FileNotFoundError):
        discard_directory(tmp_path / "index.retired")


def test_a_swap_that_fails_names_the_type_and_never_a_path(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T-18-07-05: the error branch counts as a line of this module like any other."""
    live = tmp_path / "index"
    target = tmp_path / "index.rebuild"
    target.mkdir()

    with caplog.at_level("WARNING", logger="findling.index.rebuild"), pytest.raises(FileNotFoundError):
        swap_in(target, live)

    assert caplog.records
    assert any("FileNotFoundError" in record.getMessage() for record in caplog.records)
    assert not any(tmp_path.name in record.getMessage() for record in caplog.records)


# The three marks that would take a case out of the run on the machine it is
# supposed to fail on. Assembled from halves so that this file does not carry the
# names it forbids and report itself, the same construction test_ops_scripts.py
# and test_measurement_scripts.py use for the dashes they ban.
PLATFORM_MARKS = frozenset({"skip" + "if", "skip", "x" + "fail"})


def test_no_case_in_this_file_is_taken_out_of_the_run_by_a_mark() -> None:
    """Static, because the swap case is worth exactly as much as the machines it runs on.

    Windows is the only system on which a rename with a handle still open fails
    at all, so a mark that took the case out of the run here would leave the
    mistake to be found on a box in the field, where it is silent. A grep would
    read the prose of this file as well; the syntax tree reads only the marks.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    marked = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        for decorator in node.decorator_list
        for attribute in ast.walk(decorator)
        if isinstance(attribute, ast.Attribute) and attribute.attr in PLATFORM_MARKS
    ]

    assert marked == []
