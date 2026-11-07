"""The document key per row and the bounded backfill behind it (plan 43-16, D-43-14).

The coverage of 1.6.3 counts documents and not reader paths: a file one user
sees under Daten/x.pdf and another under Shared/x.pdf is one document. The key
that says so is sha256 over the internal path in the file cache, computed in
PHP (43-15) and only ever carried by this container. Three sides are held here.

*The column.* doc_key arrives on the next open of an existing state.db without a
reindex and without a new schema mark, and a job writes it with its verdict. A
job without a key never erases one (R2), a rename brings the new one (W4), and a
value that is not 64 lower case hex digits is never stored (T-43-49).

*The backfill.* The rows of before 1.6.3 ask the companion band by band, at most
a few bands per round, resumable over a restart, behind a backup pause and with
a cooldown for a companion that has no such route yet (W3, W11). An answer that
leaves an asked id out is no answer (W8), an id that stays unanswered is set
aside with the sentinel '' after a bisection (W12, W15), and the cursor goes
back to the front after a full pass that left rows without a key (R2).

*The verify pass.* Once nothing is missing the stored keys are asked again,
slowly, and a stale one is replaced (G1); a pass without a correction rests for
a day. None of it ever logs a path or a key value (T-43-52).
"""

from __future__ import annotations  # noqa: I001 - the worker module arrives with the GREEN step

import hashlib
import logging
import math
import re
import sqlite3
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from findling.nc import queue as queue_module
from findling.nc.client import AsyncNextcloudApp
from findling.nc.files import DOC_KEY_BAND, DocKeyAnswer, FileList
from findling.store import repo as repo_module
from findling.store.repo import SCHEMA_VERSION, STORE_SCHEMA_MARK, FileMeta, Store, open_store
from findling.worker import doc_keys as doc_keys_module
from findling.worker import poller as poller_module
from findling.worker.doc_keys import (
    DOC_KEY_BACKFILL_BANDS_PER_ROUND,
    DOC_KEY_GENERATION,
    DOC_KEY_INCOMPLETE_RETRIES,
    DOC_KEY_MARK,
    ROUND_FILLED,
    ROUND_HELD,
    ROUND_RESTING,
    ROUND_UNAVAILABLE,
    ROUND_VERIFIED,
    ROUND_WAITING,
    DocKeyBackfill,
    note_coverage_call,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"
DOC_KEYS_PATH = "/ocs/v2.php/apps/findling/reconcile/doc-keys"
START = 1_800_000_000.0
DAY = 86_400
HEX64 = re.compile(r"[0-9a-f]{64}")


def key_of(file_id: int, *, generation: str = "") -> str:
    """The key the fake companion knows for a file id, 64 lower case hex digits."""
    return hashlib.sha256(f"files/doc{generation}{file_id}".encode()).hexdigest()


# -- fixtures ------------------------------------------------------------------


def _meta(storage_id: int = 3, path: str = "Daten/x.pdf", doc_key: str | None = None) -> FileMeta:
    return FileMeta(
        storage_id=storage_id,
        root_id=storage_id * 10,
        path=path,
        title=None,
        mime="application/pdf",
        size=10,
        mtime=1_700_000_000,
        etag="e",
        doc_key=doc_key,
    )


def _insert_rows(store: Store, file_ids: Sequence[int], *, doc_key: str | None = None, storage_id: int = 3) -> None:
    """Living indexed rows without going through record(), fast for a thousand of them."""
    store._conn.executemany(
        "INSERT INTO files (file_id, storage_id, root_id, path, mime, size, mtime, state, doc_key) "
        "VALUES (?, ?, ?, ?, 'application/pdf', 10, 1, 'indexed', ?)",
        [(file_id, storage_id, storage_id * 10, f"Daten/{file_id}.pdf", doc_key) for file_id in file_ids],
    )


def _doc_key(store: Store, file_id: int) -> str | None:
    row = store._conn.execute("SELECT doc_key FROM files WHERE file_id = ?", (file_id,)).fetchone()
    return None if row is None or row[0] is None else str(row[0])


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


class _Keys:
    """A scripted companion: knows key_of(id) for every id unless told otherwise."""

    def __init__(self) -> None:
        self.asked: list[list[int]] = []
        self.absent: set[int] = set()
        self.dropped: set[int] = set()
        self.overrides: dict[int, str] = {}
        self.unavailable = False
        self.route_missing = False
        self.on_ask: Callable[[], None] | None = None

    @property
    def calls(self) -> int:
        return len(self.asked)

    async def doc_keys(self, file_ids: Sequence[int]) -> DocKeyAnswer | None:
        ids = list(file_ids)
        self.asked.append(ids)
        if self.on_ask is not None:
            self.on_ask()
        if self.unavailable:
            return None
        if self.route_missing:
            return DocKeyAnswer(asked=tuple(ids), route_missing=True)
        keys = {
            file_id: self.overrides.get(file_id, key_of(file_id))
            for file_id in ids
            if file_id not in self.absent and file_id not in self.dropped
        }
        return DocKeyAnswer(
            asked=tuple(ids), keys=keys, absent=frozenset(file_id for file_id in ids if file_id in self.absent)
        )


def _backfill(store: Store, keys: _Keys, clock: list[float], *, bands: int = 2) -> DocKeyBackfill:
    return DocKeyBackfill(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: cast("Any", keys),
        bands_per_round=bands,
        pause_seconds=0.0,
        tick_seconds=300.0,
        clock=lambda: clock[0],
    )


def _mark(store: Store) -> str | None:
    return store.read_meta().get(DOC_KEY_MARK)


# -- the column ------------------------------------------------------------------


def _old_database(path: Path) -> None:
    """A state.db of 1.6.2: the files table without doc_key, one judged row."""
    schema = (PACKAGE_ROOT / "store" / "schema.sql").read_text(encoding="utf-8")
    schema = schema.replace("    deleted_at    INTEGER", "    deleted_at    INTEGER -- end")
    schema = re.sub(r",\s*doc_key\s+TEXT[^\n]*", "", schema)
    schema = re.sub(r"CREATE INDEX IF NOT EXISTS files_storage_doc_key[^;]*;", "", schema)
    connection = sqlite3.connect(path)
    connection.executescript(schema)
    connection.execute(
        "INSERT INTO files (file_id, storage_id, root_id, path, mime, size, mtime, state) "
        "VALUES (7, 3, 30, 'Daten/a.pdf', 'application/pdf', 10, 1, 'indexed')"
    )
    connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)", (STORE_SCHEMA_MARK, SCHEMA_VERSION))
    connection.commit()
    columns = [str(row[1]) for row in connection.execute("PRAGMA table_info(files)")]
    connection.close()
    assert "doc_key" not in columns


def _columns(store: Store) -> list[str]:
    return [str(row[1]) for row in store._conn.execute("PRAGMA table_info(files)")]


def _indexes(store: Store) -> set[str]:
    return {str(row[0]) for row in store._conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}


def test_an_old_state_db_gets_the_column_and_the_index_on_open_and_nothing_else(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    _old_database(path)

    opened = open_store(path)
    try:
        assert "doc_key" in _columns(opened)
        assert "files_storage_doc_key" in _indexes(opened)
        row = opened.file_row(7)
        assert row is not None
        assert row["path"] == "Daten/a.pdf"
        assert row["state"] == "indexed"
        assert row["doc_key"] is None
        meta = opened.read_meta()
        assert meta[STORE_SCHEMA_MARK] == SCHEMA_VERSION == "2"
        assert DOC_KEY_MARK not in meta
        assert opened.index_version == 0
    finally:
        opened.close()

    again = open_store(path)
    try:
        assert _columns(again).count("doc_key") == 1
        assert again.file_row(7) == row
    finally:
        again.close()


def test_a_fresh_state_db_has_the_column_and_the_index(store: Store) -> None:
    assert "doc_key" in _columns(store)
    assert "files_storage_doc_key" in _indexes(store)
    plan = " ".join(
        str(row[3])
        for row in store._conn.execute(
            "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM files WHERE storage_id = 3 AND doc_key IS NULL"
        )
    )
    assert "files_storage_doc_key" in plan


def test_two_writers_opening_an_old_state_db_add_the_column_once(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    _old_database(path)
    first = open_store(path)
    second = open_store(path)
    try:
        assert _columns(first).count("doc_key") == 1
        assert _columns(second).count("doc_key") == 1
    finally:
        first.close()
        second.close()


def test_the_schema_mark_does_not_move() -> None:
    source = (PACKAGE_ROOT / "store" / "repo.py").read_text(encoding="utf-8")
    assert 'SCHEMA_VERSION: Final = "2"' in source
    assert 'STORE_SCHEMA_MARK: Final = "store_schema_version"' in source


# -- the intake --------------------------------------------------------------------


def test_a_verdict_with_a_key_writes_it(store: Store) -> None:
    store.record(7, _meta(doc_key=key_of(7)), "indexed")
    assert _doc_key(store, 7) == key_of(7)


@pytest.mark.parametrize(
    "value",
    [
        "A" * 64,
        "0" * 63,
        "0" * 65,
        "g" * 64,
        "../" + "0" * 61,
        "",
        " " + "0" * 63,
        "0" * 63 + "\n",
    ],
)
def test_a_value_that_is_no_key_is_dropped(store: Store, value: str) -> None:
    store.record(7, _meta(doc_key=value), "indexed")
    assert _doc_key(store, 7) is None


def test_a_verdict_without_a_key_leaves_none(store: Store) -> None:
    store.record(7, _meta(), "indexed")
    assert _doc_key(store, 7) is None


def test_a_verdict_without_a_key_keeps_the_stored_one(store: Store) -> None:
    store.record(7, _meta(doc_key=key_of(7)), "indexed")
    store.record(7, _meta(), "skipped", "empty_text")
    assert _doc_key(store, 7) == key_of(7)


def test_a_rename_with_a_new_key_replaces_it_on_both_write_paths(store: Store) -> None:
    store.record(7, _meta(doc_key=key_of(7)), "indexed")
    renamed = key_of(7, generation="renamed")

    assert store.refresh_meta(7, _meta(path="Daten/b.pdf", doc_key=renamed)) == 1
    assert _doc_key(store, 7) == renamed

    again = key_of(7, generation="again")
    store.record(7, _meta(path="Daten/c.pdf", doc_key=again), "indexed")
    assert _doc_key(store, 7) == again

    store.refresh_meta(7, _meta(path="Daten/d.pdf"))
    assert _doc_key(store, 7) == again


def _source(**extra: object) -> dict[str, object]:
    return {
        "fileId": 4711,
        "storageId": 3,
        "rootId": 2,
        "path": "Daten/a.pdf",
        "title": "a.pdf",
        "mime": "application/pdf",
        "size": 1,
        "mtime": 1,
        "etag": "e",
        "kind": "content",
        "userIds": ["alice"],
        "fetchAs": "alice",
        "isUpdate": False,
        **extra,
    }


@pytest.mark.parametrize("kind", ["content", "ocr", "metadata", "acl", "embed"])
def test_every_job_kind_carries_the_key(kind: str) -> None:
    job = queue_module._job(91, _source(kind=kind, docKey=key_of(4711)))
    assert job is not None
    assert job.doc_key == key_of(4711)
    assert poller_module._meta_of(job).doc_key == key_of(4711)


@pytest.mark.parametrize("value", [None, 7, True, "A" * 64, "0" * 63, ["0" * 64]])
def test_a_job_without_a_usable_key_carries_none(value: object) -> None:
    source = _source() if value is None else _source(docKey=value)
    job = queue_module._job(91, source)
    assert job is not None
    assert job.doc_key is None


async def test_an_acl_job_after_a_move_writes_the_new_key(store: Store, tmp_path: Path) -> None:
    store.record(4711, _meta(doc_key=key_of(4711)), "indexed")
    moved = key_of(4711, generation="moved")
    job = queue_module._job(91, _source(kind="acl", docKey=moved))
    assert job is not None
    poller = poller_module.Poller(store=store, writer=cast("Any", None), tmp_dir=tmp_path)
    done: list[int] = []

    await poller._replace_access(job, done)

    assert done == [91]
    assert _doc_key(store, 4711) == moved

    plain = queue_module._job(92, _source(kind="acl"))
    assert plain is not None
    await poller._replace_access(plain, done)
    assert _doc_key(store, 4711) == moved


# -- the reading layer ------------------------------------------------------------------


class _Session:
    def __init__(self, answer: Callable[[list[int]], object]) -> None:
        self.calls: list[dict[str, Any]] = []
        self._answer = answer

    async def ocs(self, method: str, path: str, **kwargs: Any) -> Any:
        assert (method, path) == ("GET", DOC_KEYS_PATH)
        self.calls.append(kwargs)
        ids = [int(part) for part in str(kwargs["params"]["ids"]).split(",")]
        answer = self._answer(ids)
        if isinstance(answer, Exception):
            raise answer
        return answer


class _App:
    def __init__(self, session: _Session) -> None:
        self._session = session


def _list(session: _Session) -> FileList:
    return FileList(cast("AsyncNextcloudApp", _App(session)))


class _NotFound(Exception):
    status_code = 404


async def test_the_reading_layer_asks_in_bands_of_the_php_limit() -> None:
    session = _Session(lambda ids: {"keys": {str(i): key_of(i) for i in ids}, "absent": []})

    answer = await _list(session).doc_keys(list(range(1, 451)))

    assert DOC_KEY_BAND == 200
    assert [len(str(call["params"]["ids"]).split(",")) for call in session.calls] == [200, 200, 50]
    assert answer is not None
    assert answer.complete
    assert answer.keys == {i: key_of(i) for i in range(1, 451)}


async def test_the_reading_layer_keeps_only_hex_keys_of_asked_ids() -> None:
    def answer(ids: list[int]) -> object:
        del ids
        return {"keys": {"1": key_of(1), "2": "X" * 64, "99": key_of(99)}, "absent": [3, 98]}

    result = await _list(_Session(answer)).doc_keys([1, 2, 3])

    assert result is not None
    assert result.keys == {1: key_of(1)}
    assert result.absent == frozenset({3})
    assert not result.complete
    assert result.unanswered == frozenset({2})


async def test_an_empty_key_map_may_arrive_as_a_list() -> None:
    result = await _list(_Session(lambda ids: {"keys": [], "absent": ids})).doc_keys([4, 5])
    assert result is not None
    assert result.complete
    assert result.absent == frozenset({4, 5})


async def test_a_404_reads_as_a_missing_route_and_anything_else_as_no_answer(caplog: pytest.LogCaptureFixture) -> None:
    missing = await _list(_Session(lambda ids: _NotFound("x"))).doc_keys([1])
    assert missing is not None
    assert missing.route_missing

    with caplog.at_level(logging.WARNING):
        failed = await _list(_Session(lambda ids: OSError("/secret/path"))).doc_keys([1])
    assert failed is None
    assert "OSError" in caplog.text
    assert "/secret/path" not in caplog.text

    for broken in ([], "x", {"keys": {}}, {"absent": []}, {"keys": {}, "absent": "1"}, {"keys": 5, "absent": []}):
        assert await _list(_Session(lambda ids, value=broken: value)).doc_keys([1]) is None, broken


def test_the_doc_key_band_matches_the_php_constant() -> None:
    controller = PACKAGE_ROOT.parents[2] / "php" / "lib" / "Controller" / "ReconcileController.php"
    assert f"public const DOC_KEY_BAND = {DOC_KEY_BAND};" in controller.read_text(encoding="utf-8")


def test_the_route_stands_as_a_literal_at_the_call_site() -> None:
    assert (PACKAGE_ROOT / "nc" / "client.py").read_text(encoding="utf-8").count(f'"{DOC_KEYS_PATH}"') == 1


# -- the backfill -----------------------------------------------------------------------


async def test_the_backfill_fills_a_thousand_rows_in_bounded_resumable_rounds(store: Store) -> None:
    _insert_rows(store, range(1, 1001))
    keys = _Keys()
    clock = [START]

    first = await _backfill(store, keys, clock).run_once()

    assert first.state == ROUND_FILLED
    assert [len(band) for band in keys.asked] == [DOC_KEY_BAND, DOC_KEY_BAND]
    assert first.done == 400
    assert first.missing == 600
    assert _mark(store) == f"{DOC_KEY_GENERATION}:400:0"
    assert store.doc_keys_missing() == 600

    # A restart in the middle: a new object over the same database resumes at the cursor.
    keys.asked.clear()
    second = await _backfill(store, keys, clock).run_once()
    assert keys.asked[0][0] == 401
    assert second.missing == 200

    await _backfill(store, keys, clock).run_once()
    assert store.doc_keys_missing() == 0
    assert all(_doc_key(store, file_id) == key_of(file_id) for file_id in (1, 500, 1000))
    assert DOC_KEY_BACKFILL_BANDS_PER_ROUND == 25


async def test_a_file_without_a_file_cache_row_gets_the_sentinel_and_ends_counting(store: Store) -> None:
    _insert_rows(store, range(1, 11))
    keys = _Keys()
    keys.absent = {4}
    backfill = _backfill(store, keys, [START])

    await backfill.run_once()

    assert _doc_key(store, 4) == ""
    assert store.doc_keys_missing() == 0
    assert store.doc_keys_unresolved() == 1
    assert store.missing_doc_keys(after=0, limit=100) == []


async def test_the_backfill_asks_only_rows_without_a_key_and_only_living_ones(store: Store) -> None:
    _insert_rows(store, range(1, 6))
    _insert_rows(store, range(6, 9), doc_key=key_of(0))
    store._conn.execute("UPDATE files SET deleted_at = 1 WHERE file_id = 5")
    keys = _Keys()

    await _backfill(store, keys, [START]).run_once()

    assert keys.asked[0] == [1, 2, 3, 4]
    assert store.doc_keys_missing() == 0
    assert _doc_key(store, 5) is None


async def test_a_cursor_at_the_end_goes_back_for_a_new_row_without_a_key(store: Store) -> None:
    _insert_rows(store, range(10, 21), doc_key=key_of(0))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:5000:0")
    _insert_rows(store, [3])
    keys = _Keys()
    backfill = _backfill(store, keys, [START])

    await backfill.run_once()
    if _doc_key(store, 3) is None:
        await backfill.run_once()

    assert _doc_key(store, 3) == key_of(3)
    assert store.doc_keys_missing() == 0


async def test_a_missing_route_waits_with_a_doubling_cooldown_and_keeps_the_cursor(
    store: Store, caplog: pytest.LogCaptureFixture
) -> None:
    _insert_rows(store, range(1, 501))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:200:0")
    keys = _Keys()
    keys.route_missing = True
    clock = [START]
    backfill = _backfill(store, keys, clock)

    with caplog.at_level(logging.INFO, logger="findling.worker.doc_keys"):
        waits: list[float] = []
        for _ in range(8):
            result = await backfill.run_once()
            assert result.state == ROUND_WAITING
            calls = keys.calls
            # Inside the cooldown nothing is asked.
            clock[0] += 1
            assert (await backfill.run_once()).state == ROUND_WAITING
            assert keys.calls == calls
            waits.append(backfill.retry_at - clock[0] + 1)
            clock[0] = backfill.retry_at

    assert waits[:5] == [300, 600, 1200, 2400, 3600]
    assert waits[5:] == [3600, 3600, 3600]
    lines = [r.getMessage() for r in caplog.records if "the companion has no doc key route" in r.getMessage()]
    assert len(lines) == 5
    assert all(line.startswith("doc key backfill waits, the companion has no doc key route") for line in lines)
    assert _mark(store) == f"{DOC_KEY_GENERATION}:200:0"
    assert store.doc_keys_missing() == 500


async def test_a_coverage_call_ends_the_cooldown_at_once(store: Store) -> None:
    _insert_rows(store, range(1, 11))
    keys = _Keys()
    keys.route_missing = True
    clock = [START]
    backfill = _backfill(store, keys, clock)

    assert (await backfill.run_once()).state == ROUND_WAITING
    keys.route_missing = False
    clock[0] += 5
    assert (await backfill.run_once()).state == ROUND_WAITING
    calls = keys.calls

    note_coverage_call()
    result = await backfill.run_once()

    assert keys.calls == calls + 1
    assert result.state == ROUND_FILLED
    assert store.doc_keys_missing() == 0


async def test_a_coverage_call_before_the_404_does_not_end_the_cooldown(store: Store) -> None:
    _insert_rows(store, range(1, 11))
    keys = _Keys()
    keys.route_missing = True
    clock = [START]
    note_coverage_call()
    backfill = _backfill(store, keys, clock)

    assert (await backfill.run_once()).state == ROUND_WAITING
    calls = keys.calls
    clock[0] += 5
    assert (await backfill.run_once()).state == ROUND_WAITING
    assert keys.calls == calls


async def test_an_incomplete_answer_is_no_answer(store: Store) -> None:
    _insert_rows(store, range(1, 11))
    keys = _Keys()
    keys.dropped = {5}
    keys.absent = {6}

    result = await _backfill(store, keys, [START]).run_once()

    assert result.state == ROUND_UNAVAILABLE
    assert _doc_key(store, 6) is None
    assert _doc_key(store, 1) is None
    assert store.doc_keys_missing() == 10
    assert _mark(store) == f"{DOC_KEY_GENERATION}:0:0"


async def test_a_band_unanswered_three_times_is_bisected_and_one_id_set_aside(
    store: Store, caplog: pytest.LogCaptureFixture
) -> None:
    _insert_rows(store, range(1, 1001))
    keys = _Keys()
    keys.dropped = {137}
    clock = [START]
    backfill = _backfill(store, keys, clock, bands=25)

    with caplog.at_level(logging.INFO, logger="findling.worker.doc_keys"):
        for _ in range(DOC_KEY_INCOMPLETE_RETRIES - 1):
            assert (await backfill.run_once()).state == ROUND_UNAVAILABLE
            assert store.doc_keys_missing() == 1000
        result = await backfill.run_once()

    assert DOC_KEY_INCOMPLETE_RETRIES == 3
    assert result.state == ROUND_FILLED
    assert [137] in keys.asked
    assert _doc_key(store, 137) == ""
    assert store.doc_keys_missing() == 0
    assert store.doc_keys_unresolved() == 1
    assert result.unresolved == 1
    assert any("set aside" in record.getMessage() for record in caplog.records)

    # The next full pass asks it again: the verify pass reads '' rows as well.
    keys.dropped = set()
    keys.asked.clear()
    await backfill.run_once()
    assert any(137 in band for band in keys.asked)
    assert _doc_key(store, 137) == key_of(137)
    assert store.doc_keys_unresolved() == 0


async def test_a_set_aside_row_does_not_count_as_missing_after_a_restart(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    opened = open_store(path)
    _insert_rows(opened, range(1, 21))
    keys = _Keys()
    keys.dropped = {9}
    backfill = _backfill(opened, keys, [START])
    for _ in range(DOC_KEY_INCOMPLETE_RETRIES):
        await backfill.run_once()
    assert _doc_key(opened, 9) == ""
    opened.close()

    reopened = open_store(path)
    try:
        assert reopened.doc_keys_missing() == 0
        assert reopened.doc_keys_unresolved() == 1
        keys.dropped = set()
        result = await _backfill(reopened, keys, [START]).run_once()
        assert result.state == ROUND_VERIFIED
        assert _doc_key(reopened, 9) == key_of(9)
    finally:
        reopened.close()


async def test_an_unreachable_route_keeps_the_cursor(store: Store) -> None:
    _insert_rows(store, range(1, 501))
    keys = _Keys()
    backfill = _backfill(store, keys, [START], bands=1)
    await backfill.run_once()
    assert _mark(store) == f"{DOC_KEY_GENERATION}:200:0"

    keys.unavailable = True
    assert (await backfill.run_once()).state == ROUND_UNAVAILABLE
    assert _mark(store) == f"{DOC_KEY_GENERATION}:200:0"

    keys.unavailable = False
    keys.asked.clear()
    assert (await backfill.run_once()).state == ROUND_FILLED
    assert keys.asked[0][0] == 201


async def test_a_backup_pause_ends_the_backfill_between_two_bands(store: Store) -> None:
    _insert_rows(store, range(1, 1001))
    keys = _Keys()
    backfill = _backfill(store, keys, [START], bands=25)
    keys.on_ask = backfill.hold_for_backup

    result = await backfill.run_once()

    assert result.state == ROUND_HELD
    assert keys.calls == 1
    assert _mark(store) == f"{DOC_KEY_GENERATION}:200:0"
    assert backfill.backup_held
    assert not backfill.in_flight

    keys.on_ask = None
    assert (await backfill.run_once()).state == ROUND_HELD
    assert keys.calls == 1
    backfill.release_backup_hold()
    assert (await backfill.run_once()).state == ROUND_FILLED


async def test_the_backfill_runs_on_a_busy_queue_because_it_never_asks_the_queue(store: Store) -> None:
    source = (PACKAGE_ROOT / "worker" / "doc_keys.py").read_text(encoding="utf-8")
    assert "stats(" not in source
    assert "_quiet" not in source


# -- the generation ----------------------------------------------------------------------


@pytest.mark.parametrize("stored", [None, "500", "0:12:0", "0:12", "x:1:1", ""])
async def test_a_missing_or_older_generation_rebuilds_every_key_once(store: Store, stored: str | None) -> None:
    _insert_rows(store, range(1, 6), doc_key=key_of(0))
    if stored is not None:
        store.write_meta(DOC_KEY_MARK, stored)
    keys = _Keys()
    keys.unavailable = True

    await _backfill(store, keys, [START]).run_once()

    assert store.doc_keys_missing() == 5
    assert _mark(store) == f"{DOC_KEY_GENERATION}:0:0"


async def test_the_same_generation_rebuilds_nothing(store: Store) -> None:
    _insert_rows(store, range(1, 6), doc_key=key_of(0))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:0")
    keys = _Keys()
    keys.unavailable = True

    await _backfill(store, keys, [START]).run_once()

    assert store.doc_keys_missing() == 0
    assert _doc_key(store, 1) == key_of(0)


async def test_a_mark_of_the_two_part_form_is_read_and_completed(store: Store) -> None:
    _insert_rows(store, range(1, 401))
    _insert_rows(store, range(401, 601), doc_key=key_of(0))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:200")
    keys = _Keys()

    await _backfill(store, keys, [START], bands=1).run_once()

    assert keys.asked[0][0] == 201
    assert _mark(store) == f"{DOC_KEY_GENERATION}:400:0"
    assert store.doc_keys_missing() == 200
    assert _doc_key(store, 1) is None


def test_the_generation_is_one_and_only_for_a_format_change() -> None:
    source = (PACKAGE_ROOT / "worker" / "doc_keys.py").read_text(encoding="utf-8")
    assert "DOC_KEY_GENERATION: Final = 1" in source
    assert "doc_key_backfill_after" in source
    assert DOC_KEY_MARK == "doc_key_backfill_after"


# -- the verify pass ------------------------------------------------------------------------


async def test_the_verify_pass_replaces_a_stale_key_within_one_pass(store: Store) -> None:
    rows = 1000
    for file_id in range(1, rows + 1):
        _insert_rows(store, [file_id], doc_key=key_of(file_id))
    stale = 777
    store._conn.execute("UPDATE files SET doc_key = ? WHERE file_id = ?", (key_of(stale, generation="old"), stale))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:0")
    keys = _Keys()
    clock = [START]
    backfill = _backfill(store, keys, clock, bands=2)

    bound = math.ceil(rows / (DOC_KEY_BAND * 2))
    for _ in range(bound):
        result = await backfill.run_once()
        assert result.state == ROUND_VERIFIED
        assert store.doc_keys_missing() == 0
        assert all(len(band) <= DOC_KEY_BAND for band in keys.asked)
        clock[0] += 300

    assert _doc_key(store, stale) == key_of(stale)
    assert backfill.corrected == 1
    assert doc_keys_module.doc_keys_corrected() >= 1


async def test_a_pass_with_a_correction_starts_again_and_one_without_rests_a_day(store: Store) -> None:
    _insert_rows(store, range(1, 301), doc_key=None)
    for file_id in range(1, 301):
        store._conn.execute("UPDATE files SET doc_key = ? WHERE file_id = ?", (key_of(file_id), file_id))
    store._conn.execute("UPDATE files SET doc_key = ? WHERE file_id = 5", (key_of(5, generation="old"),))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:0")
    keys = _Keys()
    clock = [START]
    backfill = _backfill(store, keys, clock, bands=25)

    first = await backfill.run_once()
    assert first.corrected == 1
    # A pass with a correction starts again at once.
    keys.asked.clear()
    second = await backfill.run_once()
    assert second.state == ROUND_VERIFIED
    assert keys.asked
    assert second.corrected == 0

    # A pass without one rests until the next day.
    keys.asked.clear()
    clock[0] += 300
    assert (await backfill.run_once()).state == ROUND_RESTING
    assert keys.asked == []
    clock[0] = START + DAY + 1
    assert (await backfill.run_once()).state == ROUND_VERIFIED
    assert keys.asked


async def test_the_verify_pass_respects_the_backup_pause(store: Store) -> None:
    _insert_rows(store, range(1, 1001), doc_key=key_of(0))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:0")
    keys = _Keys()
    backfill = _backfill(store, keys, [START], bands=25)
    keys.on_ask = backfill.hold_for_backup

    result = await backfill.run_once()

    assert result.state == ROUND_HELD
    assert keys.calls == 1
    assert _mark(store) == f"{DOC_KEY_GENERATION}:0:200"


async def test_the_verify_pass_never_reports_missing_keys(store: Store) -> None:
    _insert_rows(store, range(1, 11), doc_key=key_of(0))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:0")
    keys = _Keys()
    keys.absent = {3}

    result = await _backfill(store, keys, [START]).run_once()

    assert result.state == ROUND_VERIFIED
    assert result.missing == 0
    assert store.doc_keys_missing() == 0
    assert _doc_key(store, 3) == ""


# -- the logs -----------------------------------------------------------------------------


async def test_the_log_lines_carry_numbers_and_never_a_path_or_a_key(
    store: Store, caplog: pytest.LogCaptureFixture
) -> None:
    _insert_rows(store, range(1, 31))
    keys = _Keys()
    keys.absent = {2}
    keys.dropped = {3}
    clock = [START]
    backfill = _backfill(store, keys, clock)

    with caplog.at_level(logging.DEBUG):
        for _ in range(DOC_KEY_INCOMPLETE_RETRIES + 2):
            await backfill.run_once()
        keys.route_missing = True
        await backfill.run_once()

    lines = [record.getMessage() for record in caplog.records if record.name.startswith("findling")]
    assert any(line.startswith("doc key backfill, done=") for line in lines)
    assert any(line.startswith("doc key verify, checked=") for line in lines)
    for line in lines:
        assert not HEX64.search(line), line
        assert "/" not in line, line
        assert "Daten" not in line, line


def test_the_worker_is_started_and_stopped_in_the_lifespan() -> None:
    source = (PACKAGE_ROOT / "main.py").read_text(encoding="utf-8")
    assert "DocKeyBackfill(" in source
    assert "attach_reconcile(_DOC_KEYS)" in source
    assert "stop_doc_keys.set()" in source
    assert "_DOC_KEYS.aclose()" in source


def test_the_store_marks_stay_documented() -> None:
    assert repo_module.valid_doc_key(key_of(1)) == key_of(1)
    assert repo_module.valid_doc_key("A" * 64) is None
