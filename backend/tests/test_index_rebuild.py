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
import hashlib
import inspect
import logging
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tantivy import Document, Index, Query

from conftest import Corpus, write_wordlist
from findling.api import resources
from findling.config import SCHEMA_VERSION, settings
from findling.index.open import (
    LANGUAGES_MARK,
    REBUILD_MARK,
    expected_versions,
    fingerprint,
    open_index,
    open_reader,
)
from findling.index.rebuild import (
    _CARRIED_WITHOUT_A_MARK,
    _SCHEMA_MARK,
    FALLBACK_TO_FULL_REINDEX,
    HALF_FILLED_TARGET_KEPT,
    NOT_ENOUGH_ROOM,
    NOTHING_TO_PUT_IN_ORDER,
    NOTHING_TO_REBUILD,
    REBUILD_THROUGH,
    RETIRED_BROUGHT_BACK,
    RETIRED_DISCARDED,
    ROOM_ENOUGH,
    RUN_INCOMPLETE,
    RUN_INCOMPLETE_TARGET_DISCARDED,
    RUN_STOPPED_EARLY,
    TARGET_MARK_FILE,
    TARGET_RAISED_TO_THE_LIVE_NAME,
    RebuildRun,
    _document_from,
    _resume_cursor,
    counts_match,
    discard_directory,
    may_rebuild,
    rebuild_progress,
    rebuild_the_index,
    recover_the_index_directories,
    retire_directory,
    stamp_after_swap,
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
from findling.store.repo import LEGACY_LANGUAGES, Store, open_store

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


# What the rebuild may take out of the store package, and it is two names.
# index_bytes reads bytes and writes nothing; Store is the type of the handle the
# caller hands in for the stamp. Widened from one name to two by plan 18-07,
# because the stamp writes three marks and a module that could not name the type
# would have to take an untyped handle, which is the same access with the review
# removed. What stays out is the opening: a module that opened a database of its
# own could keep a progress record beside the index, and a second record is
# exactly the state that can disagree with the first one.
STORE_NAMES_THE_REBUILD_MAY_TAKE = {"index_bytes", "Store"}


def test_the_rebuild_keeps_no_progress_of_its_own_in_the_state_database() -> None:
    """Static half of the resume: the module cannot write a second progress record.

    The marks the stamp writes are not a progress record and never travel with a
    half finished pass: they are written once, after the final probe and after
    the swap, and they say what the directory on disk was built with. Progress
    would be a number that the index can contradict, which is why the opening of
    a database stays out of this module altogether.
    """
    tree = ast.parse(REBUILD_SOURCE.read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("findling.store")
        for alias in node.names
    }
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("findling.store")
    }

    assert imported <= STORE_NAMES_THE_REBUILD_MAY_TAKE
    assert modules == {"findling.store.repo"}
    assert "open_store" not in REBUILD_SOURCE.read_text(encoding="utf-8")


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


def test_a_leftover_the_volume_will_not_release_does_not_cost_the_swap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The half of C-18-01 that is about the order of the three steps, not the writer.

    The removal behind the two renames used to be outside every ``try``, so an
    ``OSError`` from it travelled out of ``swap_in`` and took ``stamp_after_swap``
    with it. The marks then stayed as they were, and the next start read a drift
    and rebuilt the whole index again, over and over, while the directory it
    would have stamped was already in place and answering.

    So the two renames still raise and the removal no longer does. What is left
    behind is exactly the state the clean up path of the next start knows by
    name, a retired directory beside a live one, and it says so in one line
    without a path.
    """
    live = tmp_path / "index"
    target = tmp_path / "index.rebuild"
    live.mkdir()
    target.mkdir()
    (target / "meta.json").write_text("{}", encoding="utf-8")

    def a_volume_that_will_not_let_go(retired: Path) -> None:
        del retired
        raise PermissionError(str(tmp_path / "index.retired"))

    monkeypatch.setattr("findling.index.rebuild.discard_directory", a_volume_that_will_not_let_go)

    with caplog.at_level("WARNING", logger="findling.index.rebuild"):
        swap_in(target, live)

    assert (live / "meta.json").is_file(), "the swap itself is through"
    assert not target.exists()
    assert any("PermissionError" in record.getMessage() for record in caplog.records)
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


# -- the stamp, which stands behind the final probe and behind the swap --------


def test_the_schema_mark_of_the_stamp_is_the_one_the_expectation_carries() -> None:
    """The two spellings of the key held together, because there is no constant.

    A stamp that wrote schemaVersion or index_schema would be green in every
    case that reads it back and would leave the mark the comparison asks for
    untouched, which is a rebuild that runs again on every start.
    """
    expected = expected_versions("a-digest", "de,en")

    assert _SCHEMA_MARK in expected
    assert expected[_SCHEMA_MARK] == str(SCHEMA_VERSION) == "2"


def test_a_finished_rebuild_stamps_the_schema_the_languages_and_clears_the_mark(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The whole order in one case: probe, swap, stamp, and nothing before its turn."""
    monkeypatch.setenv("FINDLING_LANGUAGES", "de,en,es")
    settings.cache_clear()
    live = tmp_path / "index"
    target = tmp_path / "index.rebuild"
    source = open_index(live, CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 6)])
    store = open_store(tmp_path / "state.db")
    store.write_meta(_SCHEMA_MARK, "1")
    store.write_meta(REBUILD_MARK, "3f1d1d9ad9262704")

    run = transfer_documents(live, target, CONSTITUENTS)
    assert run.complete is True
    del source
    gc.collect()
    swap_in(target, live)
    stamp_after_swap(store, ",".join(settings().languages))

    marks = store.read_meta()
    store.close()

    assert marks[_SCHEMA_MARK] == str(SCHEMA_VERSION)
    assert marks[LANGUAGES_MARK] == "de,en,es"
    assert marks[REBUILD_MARK] == ""
    assert _documents_in(live) == 5


def test_a_rebuild_does_not_move_the_generation(tmp_path: Path) -> None:
    """The crawl is what a raised generation is for, and this pass reads no file.

    A generation raised here would make every stored verdict stale and order the
    full reindex that the rebuild was built to avoid.
    """
    live = tmp_path / "index"
    target = tmp_path / "index.rebuild"
    source = open_index(live, CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 6)])
    store = open_store(tmp_path / "state.db")
    store.write_meta("index_version", "7")
    before = store.index_version

    transfer_documents(live, target, CONSTITUENTS, ("de", "en"))
    del source
    gc.collect()
    swap_in(target, live)
    stamp_after_swap(store, "de,en")

    after = store.index_version
    store.close()

    assert before == 7
    assert after == before


def test_a_run_whose_final_probe_fails_neither_swaps_nor_stamps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gate in front of both, written out the way the caller of plan 18-09 runs it.

    The break is staged in the middle of the third band, so the target really
    does hold fewer documents than the source rather than being told it does.
    """
    live = tmp_path / "index"
    target = tmp_path / "index.rebuild"
    source = open_index(live, CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 10)])
    store = open_store(tmp_path / "state.db")
    before = dict(store.read_meta())

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
        transfer_documents(live, target, CONSTITUENTS, ("de", "en"), band_documents=2)
    monkeypatch.undo()

    rebuilt = open_index(target, CONSTITUENTS)
    complete = counts_match(source, rebuilt)
    del source, rebuilt
    gc.collect()
    # The gate, and it is the only thing standing between a half carried run and
    # an index that calls itself current.
    if complete:
        swap_in(target, live)
        stamp_after_swap(store, "de,en")

    after = dict(store.read_meta())
    store.close()

    assert complete is False
    assert _documents_in(live) == 9, "nothing was swapped, so the old directory still answers"
    assert target.is_dir(), "the half written directory is still there for the next pass"
    assert after == before


def _called_names(tree: ast.AST) -> list[str]:
    """Every name that is called anywhere under a node, one entry per call."""
    return [
        node.id if isinstance(node, ast.Name) else node.attr
        for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        for node in [call.func]
        if isinstance(node, ast.Name | ast.Attribute)
    ]


def test_the_generation_is_raised_in_the_fallback_branch_and_nowhere_else() -> None:
    """Static, because the mistake would be invisible until the next full reindex.

    **Turned on 2026-09-24 by plan 18-09, and deliberately not made green.** Up
    to that plan this case said that ``start_rebuild_on_drift`` appears in no
    call of this module at all, and the reasoning behind that sentence has not
    moved by a word: the function raises the generation so that a crawl reads
    every file again, this pass reads no file at all, and a call behind the band
    run would order hours of extraction right after the pass that made them
    unnecessary.

    What changed is that the module gained a second path. With
    ``FINDLING_REBUILD_FALLBACK=fullreindex`` the box says it has no room for two
    index directories, so the band run deliberately does not start and the
    existing reindex way is taken instead, and that way IS the generation raise.
    It is one call, it stands inside :func:`rebuild_the_index` and in front of
    everything the band run does, and this case holds exactly that shape now.
    ``stamp_after_rebuild`` stays out altogether, because the stamp of this module
    is the narrow one that opens on the swap rather than on a count of stale
    verdicts (T-18-07-03).
    """
    tree = ast.parse(REBUILD_SOURCE.read_text(encoding="utf-8"))
    conductor = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "rebuild_the_index"
    )

    assert _called_names(tree).count("start_rebuild_on_drift") == 1
    assert _called_names(conductor).count("start_rebuild_on_drift") == 1
    assert "stamp_after_rebuild" not in _called_names(tree)


# -- the clean up path at the start, five states of one volume -----------------


def _volume_fingerprint(directory: Path) -> list[tuple[str, int, str]]:
    """Every file of a directory as path, mtime in nanoseconds and content digest.

    Three readings rather than one, because "unchanged" has to hold against all
    three ways a directory can move: a file that came or went shows in the list
    of paths, a file that was written shows in the digest, and a file that was
    rewritten with the same bytes shows in the mtime.
    """
    readings: list[tuple[str, int, str]] = []
    for path in sorted(directory.rglob("*"), key=lambda candidate: candidate.relative_to(directory).as_posix()):
        if not path.is_file():
            continue
        readings.append(
            (
                path.relative_to(directory).as_posix(),
                path.stat().st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    return readings


def _only_the_live_directory_is_left(root: Path) -> bool:
    """True while the volume holds index and neither of the two extra names."""
    return (root / "index").is_dir() and not (root / "index.rebuild").exists() and not (root / "index.retired").exists()


def test_the_state_of_a_live_directory_alone_is_left_untouched(volume: Path) -> None:
    """State 1, the ordinary start, and the only one whose proof is that nothing moved.

    A clean up path that reached for the live directory on an ordinary start
    would touch the one thing on this volume that takes hours to build, once per
    container start and for no reason at all.
    """
    live = volume / "index"
    index = open_index(live, CONSTITUENTS)
    _stage(index, [_document(file_id) for file_id in range(1, 6)])
    del index
    gc.collect()
    before = _volume_fingerprint(live)
    assert before, "the fixture wrote nothing, so the case would pass over an empty directory"

    answer = recover_the_index_directories()

    assert answer == NOTHING_TO_PUT_IN_ORDER
    assert _volume_fingerprint(live) == before
    assert _only_the_live_directory_is_left(volume)


def test_the_state_of_a_half_filled_target_beside_the_live_one_keeps_it(volume: Path) -> None:
    """State 2, and the branch whose correct handling is the counter intuitive one.

    Removing the half filled directory is what "clean up" sounds like, and it
    would throw away every band the broken run had already committed.
    """
    live = volume / "index"
    target = volume / "index.rebuild"
    source = open_index(live, CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 7)])
    half = open_index(target, CONSTITUENTS)
    _stage(half, [_document(file_id) for file_id in range(1, 3)])
    del source, half
    gc.collect()

    answer = recover_the_index_directories()

    assert answer == HALF_FILLED_TARGET_KEPT
    assert live.is_dir()
    assert target.is_dir()
    assert _documents_in(target) == 2


def test_the_kept_target_lets_the_band_run_resume_at_the_same_file_id(volume: Path) -> None:
    """The follow up to state 2: the directory that was kept is the progress record.

    The cursor is read before and after the clean up path, because the claim is
    not that a directory survived but that the next pass starts in the same place
    it would have started in without the restart.
    """
    live = volume / "index"
    target = volume / "index.rebuild"
    source = open_index(live, CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, 7)])
    half = open_index(target, CONSTITUENTS)
    _stage(half, [_document(file_id) for file_id in range(1, 3)])
    before = _resume_cursor(half)
    del source, half
    gc.collect()

    assert recover_the_index_directories() == HALF_FILLED_TARGET_KEPT

    resumed = open_index(target, CONSTITUENTS)
    after = _resume_cursor(resumed)
    del resumed
    gc.collect()
    run = transfer_documents(live, target, CONSTITUENTS, ("de", "en"))

    assert before == 2
    assert after == before
    assert run.documents_written == 4, "the two documents of the broken run were not carried a second time"
    assert run.complete is True


def test_the_state_of_a_rebuilt_directory_without_a_live_one_raises_it(volume: Path) -> None:
    """State 3: the swap broke off between its two renames, and the absence is the proof.

    The rebuilt directory is complete here for one reason only, that ``index`` is
    gone, and ``index`` only ever goes away inside a swap that the final probe
    already let through.
    """
    live = volume / "index"
    target = volume / "index.rebuild"
    rebuilt = open_index(target, CONSTITUENTS)
    _stage(rebuilt, [_document(file_id) for file_id in range(1, 9)])
    del rebuilt
    gc.collect()

    answer = recover_the_index_directories()

    assert answer == TARGET_RAISED_TO_THE_LIVE_NAME
    assert _only_the_live_directory_is_left(volume)
    assert _documents_in(live) == 8


def test_the_state_of_a_rebuilt_directory_beside_a_retired_one_takes_the_rebuilt_one(volume: Path) -> None:
    """State 3 with the retired directory still there, which is the exact half swap.

    Both extra directories stand and the live name is free, so the volume was
    caught between the first rename and the second. The rebuilt one wins, and the
    retired one is the removal the swap never got to.
    """
    live = volume / "index"
    target = volume / "index.rebuild"
    retired = volume / "index.retired"
    rebuilt = open_index(target, CONSTITUENTS)
    _stage(rebuilt, [_document(file_id) for file_id in range(1, 9)])
    old = open_index(retired, CONSTITUENTS)
    _stage(old, [_document(file_id) for file_id in range(1, 4)])
    del rebuilt, old
    gc.collect()

    answer = recover_the_index_directories()

    assert answer == TARGET_RAISED_TO_THE_LIVE_NAME
    assert _only_the_live_directory_is_left(volume)
    assert _documents_in(live) == 8, "the rebuilt directory took the live name and not the retired one"


def test_the_state_of_a_retired_directory_without_a_live_one_brings_it_back(volume: Path) -> None:
    """State 4: the first rename ran, the second did not, and the target is gone.

    The installation loses the rebuild and keeps its search. That is the right
    way round: a rebuild costs one pass, an index costs the hours that filled it.
    """
    live = volume / "index"
    retired = volume / "index.retired"
    old = open_index(retired, CONSTITUENTS)
    _stage(old, [_document(file_id) for file_id in range(1, 4)])
    del old
    gc.collect()

    answer = recover_the_index_directories()

    assert answer == RETIRED_BROUGHT_BACK
    assert _only_the_live_directory_is_left(volume)
    assert _documents_in(live) == 3


def test_the_state_of_a_retired_directory_beside_a_live_one_discards_it(volume: Path) -> None:
    """State 5: the swap was through and the removal behind it was not, so this one is waste.

    Waste is not harmless here. It counts against the free space the next
    precheck measures, and that precheck is what decides whether the next rebuild
    may start at all.
    """
    live = volume / "index"
    retired = volume / "index.retired"
    index = open_index(live, CONSTITUENTS)
    _stage(index, [_document(file_id) for file_id in range(1, 6)])
    waste = open_index(retired, CONSTITUENTS)
    _stage(waste, [_document(file_id) for file_id in range(1, 3)])
    del index, waste
    gc.collect()

    answer = recover_the_index_directories()

    assert answer == RETIRED_DISCARDED
    assert _only_the_live_directory_is_left(volume)
    assert _documents_in(live) == 5, "the live directory is the one that stayed"


def test_an_empty_volume_is_a_first_start_and_not_a_finding(volume: Path) -> None:
    """The sixth shape, and the reason the list of five is complete anyway.

    A volume with no index directory at all is what a container sees before it
    has ever indexed anything. It gets the same answer as state 1, and it may not
    be a warning, because a warning that appears on every first start is not a
    warning.
    """
    assert recover_the_index_directories() == NOTHING_TO_PUT_IN_ORDER
    assert not (volume / "index").exists()


def test_no_line_of_the_clean_up_path_names_a_path(
    volume: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T-18-08-04: all four speaking branches driven in one case, all four lines read.

    Driven rather than read out of the source, because a format string that
    carries no path can still be handed one as an argument.
    """
    live = volume / "index"
    target = volume / "index.rebuild"
    retired = volume / "index.retired"
    answers: list[str] = []

    with caplog.at_level("WARNING", logger="findling.index.rebuild"):
        # State 3, then state 4, then state 5, then state 2, each of them staged
        # as bare directories: this case reads log lines and never documents.
        target.mkdir()
        answers.append(recover_the_index_directories())
        live.rename(retired)
        answers.append(recover_the_index_directories())
        retired.mkdir()
        answers.append(recover_the_index_directories())
        target.mkdir()
        answers.append(recover_the_index_directories())

    assert answers == [
        TARGET_RAISED_TO_THE_LIVE_NAME,
        RETIRED_BROUGHT_BACK,
        RETIRED_DISCARDED,
        HALF_FILLED_TARGET_KEPT,
    ]
    assert len(caplog.records) == 4, "one line per speaking branch, and every one of them read below"
    for record in caplog.records:
        message = record.getMessage()
        assert volume.name not in message
        assert str(volume) not in message
        assert "/" not in message
        assert "\\" not in message


def test_the_clean_up_path_takes_no_path_and_derives_all_three_names(volume: Path) -> None:
    """T-18-08-03: the removal of this module can only reach the volume it was pointed at.

    Two halves of one statement. The signature takes nothing, so no caller hands
    a path in, and the three directories are the three siblings of
    ``settings().index_dir``, the path findling.config builds. The second half is
    asked of a volume that has a decoy one level up, because a name assembled by
    string concatenation instead of with_name is exactly how a clean up path
    walks out of the directory it belongs to.
    """
    assert inspect.signature(recover_the_index_directories).parameters == {}

    decoy = volume.parent / (volume.name + ".retired")
    decoy.mkdir()
    (decoy / "keep.txt").write_text("not this one", encoding="utf-8")
    (volume / "index.retired").mkdir()
    (volume / "index").mkdir()

    assert recover_the_index_directories() == RETIRED_DISCARDED
    assert decoy.is_dir(), "the sibling of the volume itself was never the business of this function"
    assert (decoy / "keep.txt").is_file()


# -- the one entry point, and the order it leads -------------------------------
#
# Every case below runs the real thing against a real volume: a real index, a
# real state database with a real drift in it, and the callbacks as the only
# stand ins. They are stand ins for a reason and not for convenience: what the
# order has to be proven against is the sequence of calls, and a poller built
# into these cases would answer the same question through three more objects.
# That the callbacks the container hands in are the methods of the real poller
# is asserted where that decision is taken, in backend/tests/test_main_lifespan.py.


class _Hands:
    """The three callbacks the run is led by, recording instead of doing.

    ``stand_down`` answers True by default, which is what a poller that really
    went quiet does. The case that hands in a False builds its own.
    """

    def __init__(self) -> None:
        self.journal: list[str] = []

    def stand_down(self) -> bool:
        self.journal.append("stand_down")
        return True

    def arm(self) -> None:
        self.journal.append("arm")

    def drop_read_side(self) -> None:
        self.journal.append("drop_read_side")


def _a_volume_that_asks_for_a_rebuild(volume: Path, documents: int = 5) -> Store:
    """A live index, a word list and a state database with a drift a rebuild answers.

    Two marks are written after the seed rather than into it, because the seed
    only fills what is missing: an installation that asks for a rebuild is one
    whose database already carries a value, and it is the wrong one.

    The one that makes this volume ask is the language mark, and since
    2026-09-24 it has to be, which is worth a sentence because it used to be the
    schema mark alone. A stored schema generation of 1 against the expected 2 is
    the state every installation upgrading from 1.2.0 is legitimately in, and
    :func:`findling.store.repo._schema_is_legacy` stopped calling it a drift for
    exactly that reason; a fixture that leaned on it would stage a volume no
    rebuild is owed. The stored set here names Spanish and the container runs
    the factory pair, which is case four of plan 18-05, the counter direction,
    and a real reason to carry the documents over. It also leaves the disk
    precheck where it was: no language is new, so
    :func:`_new_language_count` answers 0 here as it did before.

    The schema mark stays at 1 all the same. It is the truth about a directory
    that was built before the four body fields existed, and the cases below read
    it back to tell a stamped run from an unstamped one.
    """
    digest = write_wordlist(volume)
    source = open_index(volume / "index", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in range(1, documents + 1)])
    del source
    gc.collect()
    store = open_store(volume / "state.db", meta=expected_versions(digest, ",".join(settings().languages)))
    store.write_meta(_SCHEMA_MARK, "1")
    store.write_meta(LANGUAGES_MARK, "de,en,es")
    return store


def test_the_run_stands_down_before_the_first_document_and_arms_behind_the_stamp(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The whole order in one journal, and the two ends of it are the claim.

    The stand down has to be in front of the first written document, because a
    document the poller writes into the source below the cursor after the band
    that would have taken it is a document the swap loses, and the count would
    not say so (T-18-09-01, pitfall 4 of the phase research). Arm has to stand
    behind the stamp, because the marks are what the next start reads: a poller
    let go one line earlier would index into a directory whose marks still
    describe the one before it.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume)
    hands = _Hands()
    honest_document = _document_from
    honest_stamp = stamp_after_swap

    def note_the_first_document(stored: Mapping[str, list[object]], languages: Sequence[str]) -> Document:
        if "document" not in hands.journal:
            hands.journal.append("document")
        return honest_document(stored, languages)

    def note_the_stamp(handle: Store, languages: str) -> None:
        hands.journal.append("stamp")
        honest_stamp(handle, languages)

    monkeypatch.setattr("findling.index.rebuild._document_from", note_the_first_document)
    monkeypatch.setattr("findling.index.rebuild.stamp_after_swap", note_the_stamp)

    verdict = rebuild_the_index(store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side)
    marks = store.read_meta()
    store.close()

    assert verdict == REBUILD_THROUGH
    assert hands.journal == ["stand_down", "document", "drop_read_side", "stamp", "arm"]
    assert marks[_SCHEMA_MARK] == str(SCHEMA_VERSION)
    assert _documents_in(volume / "index") == 5
    assert not (volume / "index.rebuild").exists()
    assert not (volume / "index.retired").exists()


def test_a_volume_without_room_refuses_before_it_creates_anything_and_arms_again(
    volume: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The early exit, and the three things that make it clean.

    Nothing was created, so the next start finds the volume it would have found
    without the attempt; the refusal names the figures it was decided on; and the
    indexing task is let go again, because a container that cannot rebuild has to
    go on indexing into the directory it has.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume)
    hands = _Hands()
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", IMPOSSIBLE_FLOOR)
    settings.cache_clear()

    with caplog.at_level(logging.WARNING, logger="findling.index.rebuild"):
        verdict = rebuild_the_index(
            store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side
        )
    store.close()

    assert verdict == NOT_ENOUGH_ROOM
    assert not (volume / "index.rebuild").exists(), "a refused run leaves no third directory behind"
    assert hands.journal == ["arm"], "nothing was stood down, and the poller is let go all the same"
    message = caplog.records[0].getMessage()
    assert "byte" in message
    assert any(word.isdigit() for word in message.split())


def test_the_fallback_raises_the_generation_and_never_starts_a_band_run(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The named way out for a box with room for one directory and not for two.

    It is the existing path and not a new one: the generation goes up, every
    stored verdict goes stale, and the reindex banner that has named the restart
    command since phase 4 is what the admin follows. The proof that no band run
    starts is the absent directory, because the band run creates it in its first
    line.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume)
    before = store.index_version
    hands = _Hands()
    monkeypatch.setenv("FINDLING_REBUILD_FALLBACK", "fullreindex")
    settings.cache_clear()

    verdict = rebuild_the_index(store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side)
    after = store.index_version
    marks = store.read_meta()
    store.close()

    assert verdict == FALLBACK_TO_FULL_REINDEX
    assert after == before + 1
    assert not (volume / "index.rebuild").exists()
    assert hands.journal == ["arm"]
    # And it declares nothing current: the banner stays up until the crawl is
    # through, which is what the drifted mark is still saying here.
    assert marks[_SCHEMA_MARK] == "1"


def test_marks_that_agree_are_answered_without_touching_anything(volume: Path) -> None:
    """The ordinary start of an installation that never drifted.

    The fourth lifespan task does not even get created in that state, so this is
    the second half of the same guard: a caller that starts the run anyway has to
    find it doing nothing rather than carrying a whole index into a second
    directory for no reason at all.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume)
    store.write_meta(_SCHEMA_MARK, str(SCHEMA_VERSION))
    store.write_meta(LANGUAGES_MARK, ",".join(settings().languages))
    hands = _Hands()

    verdict = rebuild_the_index(store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side)
    store.close()

    assert verdict == NOTHING_TO_REBUILD
    assert hands.journal == []
    assert not (volume / "index.rebuild").exists()


def test_the_progress_rests_before_the_run_and_carries_two_numbers_during_it(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reading of the moment and no second record of it anywhere.

    Sampled from inside the band run, because that is the only place where a run
    is in progress at all: after it the answer is the resting one again, and a
    case that only looked before and after would be green for a function that
    never moves.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume, documents=6)
    hands = _Hands()
    at_rest = rebuild_progress()
    honest = _document_from
    samples: list[tuple[bool, int, int]] = []

    def sample(stored: Mapping[str, list[object]], languages: Sequence[str]) -> Document:
        reading = rebuild_progress()
        samples.append((reading.running, reading.documents_carried, reading.documents_total))
        return honest(stored, languages)

    monkeypatch.setattr("findling.index.rebuild._document_from", sample)
    monkeypatch.setattr("findling.index.rebuild.BAND_DOCUMENTS", 2)

    verdict = rebuild_the_index(store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side)
    store.close()

    assert verdict == REBUILD_THROUGH
    assert (at_rest.running, at_rest.documents_carried, at_rest.documents_total) == (False, 0, 0)
    # The first band has nothing behind it, the later ones have what the bands
    # before them committed, and the total never moves.
    assert samples[0] == (True, 0, 6)
    assert samples[-1] == (True, 4, 6)
    assert {total for _running, _carried, total in samples} == {6}
    assert rebuild_progress() == at_rest, "a finished run leaves no banner behind"


def test_a_stop_between_two_bands_keeps_the_half_filled_directory(
    volume: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shutdown, and why it costs nothing: the band is the crash granularity.

    What the container is spared is the wait for a run that takes hours on the
    box this project targets. What the run keeps is every band it committed, and
    the next start resumes in exactly that directory, which is the state the
    clean up path of plan 18-08 names HALF_FILLED_TARGET_KEPT and leaves alone.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume, documents=6)
    hands = _Hands()
    monkeypatch.setattr("findling.index.rebuild.BAND_DOCUMENTS", 2)
    bands = 0

    def after_the_first_band() -> bool:
        nonlocal bands
        bands += 1
        return bands > 1

    verdict = rebuild_the_index(
        store,
        stand_down=hands.stand_down,
        arm=hands.arm,
        drop_read_side=hands.drop_read_side,
        should_stop=after_the_first_band,
    )
    marks = store.read_meta()
    store.close()

    assert verdict == RUN_STOPPED_EARLY
    assert hands.journal == ["stand_down", "arm"], "nothing was swapped, so the read side was never dropped"
    assert _documents_in(volume / "index.rebuild") == 2
    assert _documents_in(volume / "index") == 6, "the live directory still answers with everything"
    assert marks[_SCHEMA_MARK] == "1", "and nothing was stamped"


def _the_fingerprint_of_this_code(volume: Path) -> str:
    """The short name of the marks a run on this volume is aimed at."""
    digest = expected_versions(write_wordlist(volume), ",".join(settings().languages))
    return fingerprint(digest)


def test_a_finished_run_leaves_no_mark_file_in_the_live_directory(volume: Path) -> None:
    """The mark says "this half filled target is mine", and nothing is half filled after a swap.

    It travels into the live directory with the second rename, so it is removed
    behind the swap rather than in front of it: a rename that fails has to leave
    a target the next start still recognises as its own.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume)
    hands = _Hands()

    verdict = rebuild_the_index(store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side)
    store.close()

    assert verdict == REBUILD_THROUGH
    assert not (volume / "index" / TARGET_MARK_FILE).exists()


def test_a_half_filled_target_of_other_marks_is_discarded_instead_of_filled_up(
    volume: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """H-18-02: a resume into a directory somebody else built is the worst outcome of all.

    ``Index.open`` reads the PERSISTED schema back, and a field that schema does
    not know is dropped by ``add_document`` without a word. So a run that
    resumed into a directory of an older build carried the whole index into an
    outdated shape, ``counts_match`` was satisfied because it counts documents,
    and the stamp behind the swap wrote the current schema and the current
    language set over it: an index that says it is current and is not, with no
    banner and no second attempt.

    The same thing happens without a code change at all when an admin moves
    ``FINDLING_LANGUAGES`` while a half filled target is lying there, which is
    what this case stages, because it is the shape an installation really meets.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume, documents=4)
    target = volume / "index.rebuild"
    stale = open_index(target, CONSTITUENTS)
    _stage(stale, [_document(file_id) for file_id in range(1, 3)])
    del stale
    gc.collect()
    (target / TARGET_MARK_FILE).write_text("a fingerprint of another language set", encoding="utf-8")
    hands = _Hands()

    with caplog.at_level(logging.WARNING, logger="findling.index.rebuild"):
        verdict = rebuild_the_index(
            store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side
        )
    marks = store.read_meta()
    store.close()

    assert verdict == REBUILD_THROUGH
    assert _documents_in(volume / "index") == 4, "every document was carried over, and none twice"
    assert marks[_SCHEMA_MARK] == str(SCHEMA_VERSION)
    assert any("other version marks" in record.getMessage() for record in caplog.records)
    assert not any(volume.name in record.getMessage() for record in caplog.records)


def test_a_half_filled_target_of_this_code_is_resumed_and_not_discarded(volume: Path) -> None:
    """The other side of the same question, and the one that must not move.

    The half filled directory IS the progress record. A fix that threw every
    target away would buy the schema check with a rebuild that starts from
    scratch after every restart, which on the box this project targets is hours.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume, documents=4)
    target = volume / "index.rebuild"
    half = open_index(target, CONSTITUENTS)
    _stage(half, [_document(file_id) for file_id in (1, 2)])
    del half
    gc.collect()
    (target / TARGET_MARK_FILE).write_text(_the_fingerprint_of_this_code(volume), encoding="utf-8")
    hands = _Hands()
    carried: list[int] = []
    honest = _document_from

    def note(stored: Mapping[str, list[object]], languages: Sequence[str]) -> Document:
        carried.append(int(stored[FIELD_FILE_ID][0]))  # pyright: ignore[reportArgumentType]
        return honest(stored, languages)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("findling.index.rebuild._document_from", note)
        verdict = rebuild_the_index(
            store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side
        )
    store.close()

    assert verdict == REBUILD_THROUGH
    assert carried == [3, 4], "the two documents already in the target were not carried a second time"
    assert _documents_in(volume / "index") == 4


def test_a_target_that_cannot_be_opened_is_discarded_instead_of_failing_every_start(
    volume: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """The third change of H-18-04: nothing in the system ever threw a broken target away.

    A hard abort between two writes of ``meta.json`` leaves a directory that
    ``Index.open`` raises on. The clean up path of the start keeps it on purpose
    because it cannot tell it from a good one, and the rebuild then failed at
    the same line at every start, for ever, with a log line that named only the
    type.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume, documents=3)
    target = volume / "index.rebuild"
    target.mkdir()
    (target / "meta.json").write_text("{ this is half of a json file", encoding="utf-8")
    (target / TARGET_MARK_FILE).write_text(_the_fingerprint_of_this_code(volume), encoding="utf-8")
    hands = _Hands()

    with caplog.at_level(logging.WARNING, logger="findling.index.rebuild"):
        verdict = rebuild_the_index(
            store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side
        )
    store.close()

    assert verdict == REBUILD_THROUGH
    assert _documents_in(volume / "index") == 3
    assert any("could not be opened" in record.getMessage() for record in caplog.records)


def test_a_pass_that_carries_nothing_and_stays_short_discards_the_target(
    volume: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """H-18-04: the dead end, and the one way out of it.

    The cursor is read out of the highest ``file_id`` the target holds and the
    band starts above it, so a target that is short of a document BELOW that
    cursor gets no hit at all on the next pass. It writes nothing, the count
    disagrees again, and the container repeated the whole thing at every start
    for ever: the new languages never worked, the extra directory stayed on the
    volume, and ``FINDLING_REBUILD_FALLBACK`` did not reach it because it is
    read in the branch above.

    Staged the way it really happens: a target that already holds the highest
    file id and is missing one below it. A pass that carries something over is
    resumable and is left alone, which the case above this one covers; this one
    is the pass that has nothing left to try.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume, documents=4)
    target = volume / "index.rebuild"
    short = open_index(target, CONSTITUENTS)
    # Three of the four, and the one that is missing is not the highest: the
    # cursor therefore stands at the top and the next band is empty.
    _stage(short, [_document(file_id) for file_id in (1, 2, 4)])
    del short
    gc.collect()
    (target / TARGET_MARK_FILE).write_text(_the_fingerprint_of_this_code(volume), encoding="utf-8")
    hands = _Hands()
    monkeypatch.setattr("findling.index.rebuild.BAND_DOCUMENTS", 2)

    with caplog.at_level(logging.WARNING, logger="findling.index.rebuild"):
        verdict = rebuild_the_index(
            store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side
        )
    marks = store.read_meta()
    store.close()

    assert verdict == RUN_INCOMPLETE_TARGET_DISCARDED
    assert not target.exists(), "the next start begins at an empty target instead of repeating this one"
    assert _documents_in(volume / "index") == 4, "and the live directory is untouched"
    assert marks[_SCHEMA_MARK] == "1", "nothing was stamped"
    assert any("carried nothing over" in record.getMessage() for record in caplog.records)


def test_a_pass_that_carried_something_over_keeps_its_target(volume: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The line between the two answers, and it is progress and not the count.

    A run that is short but wrote documents is resumable, so it keeps what it
    has. Throwing that one away would turn the fix for the dead end into a
    rebuild that starts from scratch whenever a band is interrupted.
    """
    store = _a_volume_that_asks_for_a_rebuild(volume, documents=4)
    hands = _Hands()
    honest = counts_match

    def short_of_one(source: Index, target: Index) -> bool:
        del source, target
        return False

    monkeypatch.setattr("findling.index.rebuild.counts_match", short_of_one)
    assert honest is not short_of_one

    verdict = rebuild_the_index(store, stand_down=hands.stand_down, arm=hands.arm, drop_read_side=hands.drop_read_side)
    store.close()

    assert verdict == RUN_INCOMPLETE
    assert _documents_in(volume / "index.rebuild") == 4, "the pass that wrote something keeps it"


def test_a_source_that_shrank_during_the_run_is_not_a_fault(tmp_path: Path) -> None:
    """The other direction of the equality the audit found (H-18-04).

    A delete job that reaches the container while the band run is going shrinks
    the source, so the target legitimately holds one document more than the
    directory it was copied from. The equality refused that swap and sent the
    run round again for ever; the document too many is a file that is gone in
    Nextcloud, and the poller removes it on its first pass after the swap.
    """
    source = open_index(tmp_path / "index", CONSTITUENTS)
    target = open_index(tmp_path / "index.rebuild", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in (1, 2)])
    _stage(target, [_document(file_id) for file_id in (1, 2, 3)])

    assert counts_match(source, target) is True


def test_a_target_short_of_the_source_is_still_a_refusal(tmp_path: Path) -> None:
    """The direction the final probe exists for, and it did not move."""
    source = open_index(tmp_path / "index", CONSTITUENTS)
    target = open_index(tmp_path / "index.rebuild", CONSTITUENTS)
    _stage(source, [_document(file_id) for file_id in (1, 2, 3)])
    _stage(target, [_document(file_id) for file_id in (1, 2)])

    assert counts_match(source, target) is False


def test_the_pair_this_module_assumes_for_a_missing_mark_is_the_one_the_comparison_reads() -> None:
    """Two spellings of one piece of history, held together like the schema mark.

    An index without a language mark was built by a release that could not write
    a body field outside this pair. If the two spellings drifted, the precheck
    would charge a rebuild for chains that are already in the directory and
    refuse runs that fit.
    """
    assert _CARRIED_WITHOUT_A_MARK == LEGACY_LANGUAGES
