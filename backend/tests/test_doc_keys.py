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

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import math
import re
import sqlite3
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from types import SimpleNamespace
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
    schema = schema.replace("    deleted_at    INTEGER,", "    deleted_at    INTEGER ")
    schema = re.sub(r"(?m)^\s*doc_key\s+TEXT.*$", "", schema)
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
    job = queue_module._job(91, _source(kind=kind, docKey=key_of(4711), docKeyFormat=2))
    assert job is not None
    assert job.doc_key == key_of(4711)
    assert poller_module._meta_of(job).doc_key == key_of(4711)


@pytest.mark.parametrize("value", [None, 7, True, "A" * 64, "0" * 63, ["0" * 64]])
def test_a_job_without_a_usable_key_carries_none(value: object) -> None:
    source = _source(docKeyFormat=2) if value is None else _source(docKey=value, docKeyFormat=2)
    job = queue_module._job(91, source)
    assert job is not None
    assert job.doc_key is None


async def test_an_acl_job_after_a_move_writes_the_new_key(store: Store, tmp_path: Path) -> None:
    store.record(4711, _meta(doc_key=key_of(4711)), "indexed")
    moved = key_of(4711, generation="moved")
    job = queue_module._job(91, _source(kind="acl", docKey=moved, docKeyFormat=2))
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


@pytest.mark.parametrize(
    "extra",
    [
        {},
        {"docKeyFormat": "2"},
        {"docKeyFormat": True},
        {"docKeyFormat": 1},
        {"docKeyFormat": 2.0},
        {"docKeyFormat": 3},
    ],
    ids=["none", "string", "boolean", "format-1", "float", "format-3"],
)
async def test_a_job_without_format_two_writes_no_key(store: Store, tmp_path: Path, extra: dict[str, object]) -> None:
    """A key of another format, or of none, is not a key of this container (OE-5 a, A-2)."""
    stored = key_of(4711)
    store.record(4711, _meta(doc_key=stored), "indexed")
    arrived = key_of(4711, generation="another format")
    poller = poller_module.Poller(store=store, writer=cast("Any", None), tmp_dir=tmp_path)
    done: list[int] = []

    job = queue_module._job(91, _source(kind="acl", docKey=arrived, **extra))
    assert job is not None
    assert job.doc_key is None
    assert poller_module._meta_of(job).doc_key is None
    await poller._replace_access(job, done)

    # Not written, and the stored one not erased either (COALESCE, plan 43-16).
    assert done == [91]
    assert _doc_key(store, 4711) == stored

    marked = queue_module._job(92, _source(kind="acl", docKey=arrived, docKeyFormat=2))
    assert marked is not None
    assert marked.doc_key == arrived
    await poller._replace_access(marked, done)
    assert _doc_key(store, 4711) == arrived


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
    session = _Session(lambda ids: {"keys": {str(i): key_of(i) for i in ids}, "absent": [], "format": 2})

    answer = await _list(session).doc_keys(list(range(1, 451)))

    assert DOC_KEY_BAND == 200
    assert [len(str(call["params"]["ids"]).split(",")) for call in session.calls] == [200, 200, 50]
    assert answer is not None
    assert answer.complete
    assert answer.keys == {i: key_of(i) for i in range(1, 451)}


async def test_the_reading_layer_keeps_only_hex_keys_of_asked_ids() -> None:
    def answer(ids: list[int]) -> object:
        del ids
        return {"keys": {"1": key_of(1), "2": "X" * 64, "99": key_of(99)}, "absent": [3, 98], "format": 2}

    result = await _list(_Session(answer)).doc_keys([1, 2, 3])

    assert result is not None
    assert result.keys == {1: key_of(1)}
    assert result.absent == frozenset({3})
    assert not result.complete
    assert result.unanswered == frozenset({2})


async def test_an_empty_key_map_may_arrive_as_a_list() -> None:
    result = await _list(_Session(lambda ids: {"keys": [], "absent": ids, "format": 2})).doc_keys([4, 5])
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

    for broken in (
        [],
        "x",
        {"keys": {}, "format": 2},
        {"absent": [], "format": 2},
        {"keys": {}, "absent": "1", "format": 2},
        {"keys": 5, "absent": [], "format": 2},
    ):
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
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:0")
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


_NO_FORMAT = object()


def _companion_of_format(value: object) -> Callable[[list[int]], object]:
    """A companion that knows every key and names this format, or none at all."""

    def answer(ids: list[int]) -> object:
        body: dict[str, object] = {"keys": {str(i): key_of(i) for i in ids}, "absent": []}
        if value is not _NO_FORMAT:
            body["format"] = value
        return body

    return answer


@pytest.mark.parametrize(
    "value", [_NO_FORMAT, 1, 3, "2", True, 2.0, None], ids=["none", "1", "3", "string", "boolean", "float", "null"]
)
async def test_a_backfill_answer_of_another_format_waits_like_a_missing_route(
    store: Store, caplog: pytest.LogCaptureFixture, value: object
) -> None:
    """Keys of another format are no keys: nothing stored, no sentinel, the cursor stays (OE-5 a)."""
    read = await _list(_Session(_companion_of_format(value))).doc_keys([1, 2])
    assert read is not None
    assert getattr(read, "format_mismatch", None) is True
    assert not read.complete
    assert not read.route_missing
    assert read.keys == {}
    assert read.absent == frozenset()

    _insert_rows(store, range(1, 501))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:200:0")
    session = _Session(_companion_of_format(value))
    clock = [START]
    backfill = DocKeyBackfill(
        store=store,
        client_factory=lambda: cast("AsyncNextcloudApp", None),
        files_factory=lambda nc: _list(session),
        bands_per_round=2,
        pause_seconds=0.0,
        tick_seconds=300.0,
        clock=lambda: clock[0],
    )

    with caplog.at_level(logging.DEBUG):
        waits: list[float] = []
        for _ in range(8):
            result = await backfill.run_once()
            assert result.state == ROUND_WAITING
            calls = len(session.calls)
            # Inside the cooldown nothing is asked.
            clock[0] += 1
            assert (await backfill.run_once()).state == ROUND_WAITING
            assert len(session.calls) == calls
            waits.append(backfill.retry_at - clock[0] + 1)
            clock[0] = backfill.retry_at

    assert waits == [300, 600, 1200, 2400, 3600, 3600, 3600, 3600]
    lines = [record.getMessage() for record in caplog.records if record.name.startswith("findling")]
    waiting = [line for line in lines if "waits" in line]
    assert len(waiting) == 5
    assert all(
        line.startswith("doc key backfill waits, the companion has another doc key format, next try in ")
        for line in waiting
    )
    for line in lines:
        assert not HEX64.search(line), line
        assert "/" not in line, line
    assert _mark(store) == f"{DOC_KEY_GENERATION}:200:0"
    assert store.doc_keys_missing() == 500
    assert store.doc_keys_unresolved() == 0

    # The same companion after its update: format 2, and the backfill goes on.
    session._answer = _companion_of_format(2)
    result = await backfill.run_once()
    assert result.state == ROUND_FILLED
    assert backfill.retry_at == 0.0
    assert _mark(store) == f"{DOC_KEY_GENERATION}:500:0"
    assert _doc_key(store, 201) == key_of(201)
    assert store.doc_keys_missing() == 200


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


@pytest.mark.parametrize("stored", ["1:400:0", "1:400", "1:400:idle1800000000"])
async def test_a_rc1_mark_rebuilds_every_key_once(store: Store, stored: str) -> None:
    """Generation 1 is the format of 1.6.3-rc.1: every key goes once, then comes back (A-1)."""
    _insert_rows(store, range(1, 6), doc_key=key_of(0, generation="format 1"))
    store.write_meta(DOC_KEY_MARK, stored)
    keys = _Keys()
    keys.unavailable = True
    clock = [START]
    backfill = _backfill(store, keys, clock)

    await backfill.run_once()

    assert [_doc_key(store, file_id) for file_id in range(1, 6)] == [None] * 5
    assert store.doc_keys_missing() == 5
    assert _mark(store) == "2:0:0"

    keys.unavailable = False
    assert (await backfill.run_once()).state == ROUND_FILLED
    assert [_doc_key(store, file_id) for file_id in range(1, 6)] == [key_of(file_id) for file_id in range(1, 6)]
    # The pass is through: the cursor is back at the front (R2), the generation stays.
    assert _mark(store) == "2:0:0"

    # The mark of generation 2 forgets nothing, in this process and in the next.
    for later in (backfill, _backfill(store, keys, clock)):
        keys.unavailable = True
        await later.run_once()
        assert store.doc_keys_missing() == 0
        assert _doc_key(store, 1) == key_of(1)
        assert str(_mark(store)).startswith("2:")


async def test_the_keys_are_gone_before_the_mark_says_generation_two(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """First the reset, then the mark: the coverage route never sees generation 2 over old keys."""
    _insert_rows(store, range(1, 6), doc_key=key_of(0, generation="format 1"))
    store.write_meta(DOC_KEY_MARK, "1:400:0")
    written: list[tuple[str, int]] = []
    real_write = store.write_meta

    def write(key: str, value: str) -> None:
        if key == DOC_KEY_MARK:
            written.append((value, store.doc_keys_missing()))
        real_write(key, value)

    monkeypatch.setattr(store, "write_meta", write)
    keys = _Keys()
    keys.unavailable = True

    await _backfill(store, keys, [START]).run_once()

    assert written[0] == ("2:0:0", 5)


def test_the_generation_is_two_and_only_for_a_format_change() -> None:
    source = (PACKAGE_ROOT / "worker" / "doc_keys.py").read_text(encoding="utf-8")
    assert DOC_KEY_GENERATION == 2
    assert "DOC_KEY_GENERATION: Final = 2" in source
    assert source.count("DOC_KEY_GENERATION: Final") == 1
    assert "doc_key_backfill_after" in source
    assert DOC_KEY_MARK == "doc_key_backfill_after"
    # The reader of the route and the reader of the worker are one function.
    stored_generation = getattr(doc_keys_module, "stored_generation", None)
    assert stored_generation is not None
    assert [stored_generation(value) for value in (None, "", "500", "x:1:1", "1:400:0", "2:0", "2:7:idle9")] == [
        None,
        None,
        None,
        None,
        1,
        2,
        2,
    ]


# -- a state that is born after the arming ---------------------------------------------------
#
# Run 42991291089, the three head legs of the coverage proof: a fresh installation answered
# "counting" for five minutes. The enable arms the poller and this task in the same step, the
# poller is the one that creates state.db, and the first round of this task found no file yet.
# It then slept a whole tick of 300 s, the generation gate of the coverage route kept every
# figure back for that long, and the round after the tick forgot the 95 keys the jobs had
# written in between and asked the companion for them again.

RETRY = 0.02


def _stateless(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, keys: _Keys) -> tuple[DocKeyBackfill, Path, list[int]]:
    """A worker as the lifespan builds it: no store handed in, the real tick, a volume without state.db."""
    path = tmp_path / "state.db"
    monkeypatch.setattr(doc_keys_module, "settings", lambda: SimpleNamespace(state_db=path))
    monkeypatch.setattr(doc_keys_module, "DOC_KEY_NO_STATE_SECONDS", RETRY, raising=False)
    clients: list[int] = []

    def client() -> AsyncNextcloudApp:
        clients.append(1)
        return cast("AsyncNextcloudApp", None)

    backfill = DocKeyBackfill(client_factory=client, files_factory=lambda nc: cast("Any", keys), pause_seconds=0.0)
    return backfill, path, clients


def _mark_at(path: Path) -> str | None:
    if not path.exists():
        return None
    with contextlib.closing(sqlite3.connect(path)) as conn:
        try:
            row = conn.execute("SELECT value FROM meta WHERE key = ?", (DOC_KEY_MARK,)).fetchone()
        except sqlite3.OperationalError:
            return None
    return None if row is None else str(row[0])


async def _until(condition: Callable[[], bool], seconds: float = 5.0) -> bool:
    """Poll a condition; True as soon as it holds, False when the time is up."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if condition():
            return True
        await asyncio.sleep(0.01)
    return condition()


async def _end(task: asyncio.Task[None], stop: asyncio.Event, backfill: DocKeyBackfill) -> None:
    stop.set()
    await asyncio.wait_for(task, timeout=5.0)
    await backfill.aclose()


def test_the_wait_for_a_missing_state_is_seconds_and_never_a_tick() -> None:
    wait = getattr(doc_keys_module, "DOC_KEY_NO_STATE_SECONDS", None)
    assert isinstance(wait, float), "there is no wait of its own for a volume without state.db"
    assert 0 < wait <= 10
    assert wait < doc_keys_module.DOC_KEY_TICK_SECONDS / 10


async def test_a_state_born_after_the_arming_gets_its_generation_within_seconds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keys = _Keys()
    backfill, path, clients = _stateless(tmp_path, monkeypatch, keys)
    stop = asyncio.Event()
    backfill.arm()
    task = asyncio.create_task(backfill.run(stop))
    try:
        # The first round runs at once and finds no file.
        await asyncio.sleep(RETRY * 5)
        assert not path.exists(), "the worker created state.db, only the poller may"
        assert clients == []

        # The poller creates and seeds the database, a moment after the arming.
        poller_side = open_store(path)
        try:
            assert await _until(lambda: (_mark_at(path) or "").startswith(f"{DOC_KEY_GENERATION}:")), (
                f"no generation {DOC_KEY_GENERATION} in the meta value within seconds of the birth of state.db, "
                f"it reads {_mark_at(path)!r}: a fresh installation says 'counting' until the next tick"
            )
            # Nothing was there to ask the companion for.
            assert keys.calls == 0

            # The jobs of the crawl bring their keys, and no later round forgets them.
            _insert_rows(poller_side, range(1, 6), doc_key=key_of(7))
            await asyncio.sleep(RETRY * 10)
            assert [_doc_key(poller_side, file_id) for file_id in range(1, 6)] == [key_of(7)] * 5
            assert poller_side.doc_keys_missing() == 0
            assert keys.calls == 0
        finally:
            poller_side.close()
    finally:
        await _end(task, stop, backfill)


async def test_a_backup_pause_that_arrives_before_the_state_still_holds_the_first_round(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keys = _Keys()
    backfill, path, _clients = _stateless(tmp_path, monkeypatch, keys)
    stop = asyncio.Event()
    backfill.arm()
    task = asyncio.create_task(backfill.run(stop))
    try:
        await asyncio.sleep(RETRY * 5)
        # The pause lands while the worker waits for a state, then the state arrives with
        # keys of the test build (generation 1), as after an update behind a backup.
        backfill.hold_for_backup()
        poller_side = open_store(path)
        try:
            _insert_rows(poller_side, range(1, 6), doc_key=key_of(0, generation="1"))
            poller_side.write_meta(DOC_KEY_MARK, "1:400:0")
            await asyncio.sleep(RETRY * 15)
            assert _mark_at(path) == "1:400:0", "a round wrote behind the backup pause"
            assert poller_side.doc_keys_missing() == 0
            assert keys.calls == 0
            assert not backfill.in_flight

            backfill.release_backup_hold()
            assert await _until(lambda: (_mark_at(path) or "").startswith(f"{DOC_KEY_GENERATION}:")), (
                f"after the resume the meta value still reads {_mark_at(path)!r}"
            )
            assert await _until(lambda: poller_side.doc_keys_missing() == 0 and keys.calls >= 1)
            assert [_doc_key(poller_side, file_id) for file_id in range(1, 6)] == [key_of(n) for n in range(1, 6)]
        finally:
            poller_side.close()
    finally:
        await _end(task, stop, backfill)


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


async def test_after_a_restart_a_stored_rest_is_ignored_and_a_stale_key_is_corrected_in_the_first_round(
    store: Store,
) -> None:
    # The way back to 1.6.2 and up again (plan 43-07, G1): the rest of a clean
    # pass is in the meta value, 1.6.2 never touches it, and a file renamed
    # under 1.6.2 keeps the key of its old path. The rest belongs to one
    # running process; a new process verifies at once.
    _insert_rows(store, range(1, 11), doc_key=None)
    for file_id in range(1, 11):
        store._conn.execute("UPDATE files SET doc_key = ? WHERE file_id = ?", (key_of(file_id), file_id))
    store._conn.execute("UPDATE files SET doc_key = ? WHERE file_id = 4", (key_of(4, generation="old"),))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:idle{int(START + DAY)}")
    keys = _Keys()

    restarted = _backfill(store, keys, [START], bands=25)
    result = await restarted.run_once()

    assert result.state == ROUND_VERIFIED
    assert keys.asked
    assert result.corrected == 1
    assert _doc_key(store, 4) == key_of(4)


async def test_the_rest_still_holds_within_one_running_process(store: Store) -> None:
    _insert_rows(store, range(1, 11), doc_key=None)
    for file_id in range(1, 11):
        store._conn.execute("UPDATE files SET doc_key = ? WHERE file_id = ?", (key_of(file_id), file_id))
    store.write_meta(DOC_KEY_MARK, f"{DOC_KEY_GENERATION}:0:idle{int(START + DAY)}")
    keys = _Keys()
    clock = [START]
    backfill = _backfill(store, keys, clock, bands=25)

    # The first round of the process verifies, finds nothing and rests again.
    assert (await backfill.run_once()).state == ROUND_VERIFIED
    keys.asked.clear()
    clock[0] += 300
    assert (await backfill.run_once()).state == ROUND_RESTING
    assert keys.asked == []


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


# -- the reset in bands ---------------------------------------------------------------------
#
# Measured on a store of 491,000 keyed rows with the real schema and pragmas: one UPDATE over
# the whole table held the write lock for up to 9.1 s and a second writer waited 8.8 s of its
# 10 s busy timeout. In bands of 100,000 the second writer waited 2.4 s at most. The reasons
# for a band that large stand at the constant in store/repo.py.


def _statements(store: Store) -> list[str]:
    seen: list[str] = []
    store._conn.set_trace_callback(lambda statement: seen.append(" ".join(statement.split())))
    return seen


def test_the_reset_forgets_every_key_in_bands_and_never_in_one_transaction(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    band = 100
    assert getattr(repo_module, "_RESET_DOC_KEYS_BAND", None) == 100_000
    monkeypatch.setattr(repo_module, "_RESET_DOC_KEYS_BAND", band)
    # File ids with gaps, as on a real instance: a band is a count of rows, not a span of ids.
    keyed = [file_id * 37 for file_id in range(1, 2 * band + 8)]
    for file_id in keyed:
        _insert_rows(store, [file_id], doc_key=key_of(file_id))
    _insert_rows(store, [5], doc_key="")
    _insert_rows(store, [6], doc_key=None)
    seen = _statements(store)

    changed = store.reset_doc_keys()

    store._conn.set_trace_callback(None)
    assert changed == len(keyed) + 1
    assert store._conn.execute("SELECT COUNT(*) FROM files WHERE doc_key IS NOT NULL").fetchone()[0] == 0
    begins = [index for index, statement in enumerate(seen) if statement.upper().startswith("BEGIN")]
    commits = [index for index, statement in enumerate(seen) if statement.upper().startswith("COMMIT")]
    updates = [index for index, statement in enumerate(seen) if statement.upper().startswith("UPDATE FILES")]
    assert len(updates) == 3
    assert len(begins) == len(commits) == len(updates)
    # Every band is its own transaction: begin, one update, commit, and only then the next one.
    for begin, update, commit in zip(begins, updates, commits, strict=True):
        assert begin < update < commit
    assert all(commit < begin for commit, begin in zip(commits, begins[1:], strict=False))


def test_no_band_of_the_reset_touches_more_rows_than_the_band(store: Store, monkeypatch: pytest.MonkeyPatch) -> None:
    band = 50
    monkeypatch.setattr(repo_module, "_RESET_DOC_KEYS_BAND", band, raising=False)
    for file_id in range(1, 4 * band + 1):
        _insert_rows(store, [file_id], doc_key=key_of(file_id))
    left: list[int] = []
    real_execute = store._conn.execute
    count_sql = "SELECT COUNT(*) FROM files WHERE doc_key IS NOT NULL"

    def watch(statement: str) -> None:
        if statement.upper().startswith("COMMIT"):
            left.append(int(real_execute(count_sql).fetchone()[0]))

    store._conn.set_trace_callback(watch)
    store.reset_doc_keys()
    store._conn.set_trace_callback(None)

    assert left == [150, 100, 50, 0]


def test_a_second_writer_gets_in_between_two_bands_of_the_reset(
    store: Store, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    band = 50
    monkeypatch.setattr(repo_module, "_RESET_DOC_KEYS_BAND", band, raising=False)
    for file_id in range(1, 3 * band + 1):
        _insert_rows(store, [file_id], doc_key=key_of(file_id))
    # No patience at all: this writer only gets through when the lock is free.
    other = sqlite3.connect(tmp_path / "state.db", timeout=0)
    wrote: list[int] = []
    real_transaction = store._transaction
    bands = 0

    def transaction() -> Any:
        nonlocal bands
        if bands == 1:
            # The first band is committed, the second has not begun.
            other.execute("UPDATE files SET attempts = attempts + 1 WHERE file_id = 1")
            other.commit()
            wrote.append(1)
        bands += 1
        return real_transaction()

    monkeypatch.setattr(store, "_transaction", transaction)

    store.reset_doc_keys()

    other.close()
    assert bands == 3
    assert wrote == [1]
    assert store._conn.execute("SELECT attempts FROM files WHERE file_id = 1").fetchone()[0] == 1


def test_an_empty_table_and_a_table_without_keys_reset_to_nothing(store: Store) -> None:
    assert store.reset_doc_keys() == 0
    _insert_rows(store, [1, 2, 3], doc_key=None)
    assert store.reset_doc_keys() == 0
