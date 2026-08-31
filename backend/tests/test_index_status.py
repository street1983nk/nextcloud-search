"""What the status tool has to answer, and why its numbers come from two sources.

The kill-resume job of plan 02-13 waits on these numbers and then asserts against
them. That makes two properties of this module load bearing, and both are checked
below rather than assumed.

*It must not fail on an empty volume.* The waiting loop calls the tool before the
first document exists, and a tool that exits non zero on a missing database would
turn the very first round of that loop into a red job.

*``docs`` must come from the index and the state counters from the database.*
The doubled document check of the job compares the two, and a comparison of two
numbers that share a source proves nothing at all.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.store.repo import FileMeta, open_store
from findling.tools import index_status

# Enough entries for a real automaton without reading the Debian list, which does
# not exist on a developer machine. Which words they are does not matter here: no
# test below searches, they only count.
_CONSTITUENTS = ("frist", "kosten", "vertrag", "verwaltung", "s", "es", "n", "en")

_META = FileMeta(
    storage_id=1,
    root_id=1,
    path="/dokument.txt",
    title="Dokument",
    mime="text/plain",
    size=10,
    mtime=1_700_000_000,
)


def _state_database(db: Path, *, meta: dict[str, str] | None = None) -> None:
    """Write two verdicts and two permission rows into a fresh state database."""
    store = open_store(db, meta=meta)
    try:
        store.record(1, _META, "indexed")
        store.record(2, _META, "skipped", "too_large")
        store.replace_acl(1, ["alice", "bob"])
    finally:
        store.close()


def _record(file_id: int) -> IndexRecord:
    return IndexRecord(
        file_id=file_id,
        storage_id=1,
        name=f"dokument-{file_id}.txt",
        title="Dokument",
        path=f"/dokument-{file_id}.txt",
        ext="txt",
        body="Der Vertrag regelt die Betriebskosten.",
        mtime=1_700_000_000,
    )


def _index_with(directory: Path, file_ids: tuple[int, ...]) -> None:
    """Commit one document per file id into a fresh index directory."""
    index = open_index(directory, _CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=directory)
    try:
        for file_id in file_ids:
            writer.add(_record(file_id))
        writer.flush()
    finally:
        writer.close()


def test_the_report_is_valid_json_and_the_run_succeeds(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = tmp_path / "state.db"
    _state_database(db)

    exit_code = index_status.main(["--db", str(db)])

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert report["indexed"] == 1


def test_the_report_carries_every_counter_and_every_version(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _state_database(db, meta={"index_version": "1", "analyzer_version": "1", "wordlist_hash": "abc123"})
    _index_with(tmp_path / "index", (1, 2))

    report = index_status.collect(db, tmp_path / "index")

    assert report["indexed"] == 1
    assert report["skipped"] == 1
    assert report["failed"] == 0
    assert report["aclRows"] == 2
    assert report["docs"] == 2
    assert report["indexVersion"] == "1"
    assert report["analyzerVersion"] == "1"
    assert report["wordlistHash"] == "abc123"


def test_a_state_without_rows_is_a_zero_and_not_a_missing_key(tmp_path: Path) -> None:
    # The whole promise of the status output: "no failures" and "the counter is
    # broken" have to look different from each other.
    db = tmp_path / "state.db"
    open_store(db).close()

    report = index_status.collect(db, tmp_path / "index")

    for state in ("indexed", "skipped", "failed"):
        assert report[state] == 0


def test_a_missing_database_is_zeroes_and_not_an_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # A freshly installed container has no state database yet, and the waiting
    # loop of the workflow asks before the first document exists.
    exit_code = index_status.main(["--db", str(tmp_path / "state.db")])

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert report["databaseFound"] is False
    assert report["indexed"] == 0
    assert report["aclRows"] == 0
    assert report["docs"] == 0


def test_the_state_database_is_only_read(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _state_database(db)
    before = hashlib.sha256(db.read_bytes()).hexdigest()

    index_status.collect(db, tmp_path / "index")

    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    # The structural half. open_read_only sets PRAGMA query_only, so a write over
    # this connection fails whatever code issues it; naming open_store here would
    # take that away without any test noticing.
    source = Path(index_status.__file__).read_text(encoding="utf-8")
    assert "open_read_only" in source
    assert "open_store" not in source


def test_documents_come_from_the_index_and_not_from_the_database(tmp_path: Path) -> None:
    # The doubled document check of the kill-resume job is exactly this
    # comparison, and it only means something because the two numbers are read
    # from two different places.
    db = tmp_path / "state.db"
    _state_database(db)
    _index_with(tmp_path / "index", (1, 2, 3))

    report = index_status.collect(db, tmp_path / "index")

    assert report["indexed"] == 1
    assert report["docs"] == 3


def test_a_missing_index_reports_no_documents_and_says_so(tmp_path: Path) -> None:
    db = tmp_path / "state.db"
    _state_database(db)

    report = index_status.collect(db, tmp_path / "index")

    assert report["indexFound"] is False
    assert report["docs"] == 0


def test_the_reasons_are_broken_down_per_state(tmp_path: Path) -> None:
    # Phase 4 builds its error list from this breakdown, and the job prints it
    # when an assertion fails: "eleven files failed" without the reason is a
    # number nobody can act on.
    db = tmp_path / "state.db"
    _state_database(db)

    report = index_status.collect(db, tmp_path / "index")

    # The report is a mapping of plain values, so the nested breakdown is narrowed
    # here rather than typed away at the source: the values really are of mixed
    # type, and a signature that claimed otherwise would be the lie.
    reasons = report["reasons"]
    assert isinstance(reasons, dict)
    assert reasons["skipped"]["too_large"] == 1
    assert reasons["indexed"][index_status.NO_REASON] == 1


def test_the_index_sits_next_to_the_database_unless_it_is_named(tmp_path: Path) -> None:
    # The layout of the persistent volume, so the workflow passes one path and
    # not two. Overriding it stays possible for a run against a copied volume.
    db = tmp_path / "state.db"
    _state_database(db)
    _index_with(tmp_path / "index", (1,))

    assert index_status.index_directory(db, None) == tmp_path / "index"
    assert index_status.index_directory(db, tmp_path / "elsewhere") == tmp_path / "elsewhere"
    assert index_status.main(["--db", str(db)]) == 0
