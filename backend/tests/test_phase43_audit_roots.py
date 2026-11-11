"""The audit probes of plan 43-27 over the roots and spellings delta (37b518d6..2261167b).

One probe per question of the audit that no test of plans 43-21 to 43-26
already drives; 43-AUDIT.md names the existing test for every other one. The
probes build their own rows and their own companion and compute every key
themselves, so none of them reuses the pattern of the code it judges (owner
rule "Gegenprobe nie mit dem Muster der Umsetzung").

Three of them hold a finding of the audit in place as it is today. Their names
start with ``test_p_f_43b_``; each says in its docstring what has to change in
it on the day the finding is fixed.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import sqlite3
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, cast

import pytest

from findling.config import settings
from findling.nc.files import DocKeyAnswer, Mount, MountResult, SliceResult
from findling.nc.queue import CallResult, QueueStats
from findling.store import repo as repo_module
from findling.store.repo import (
    CATCHUP_DONE,
    CATCHUP_MARK,
    CATCHUP_RECONCILE,
    FileMeta,
    Store,
    coverage_counts,
    open_store,
)
from findling.worker.doc_keys import (
    DOC_KEY_GENERATION,
    DOC_KEY_MARK,
    ROUND_VERIFIED,
    DocKeyBackfill,
    stored_generation,
)
from findling.worker.reconcile import Reconcile, RoundResult

pytestmark = pytest.mark.usefixtures("appapi_environment")

BAND = 50
NOW = 1_800_000_000.0


def _key_of_rc1(file_id: int) -> str:
    """A key as 1.6.3-rc.1 left it: 64 hex digits of another format."""
    return hashlib.sha256(f"rc1 path of {file_id}".encode()).hexdigest()


def _key_of_the_head(file_id: int) -> str:
    """The key a companion of the head names for a file id."""
    return hashlib.sha256(f"head share and path of {file_id}".encode()).hexdigest()


def _format_two(share: str, share_path: str) -> str:
    """The key of format 2 by its definition: sha256 over '2' NUL share NUL share path."""
    return hashlib.sha256(b"2\0" + share.encode() + b"\0" + share_path.encode()).hexdigest()


_INSERT: str = (
    "INSERT INTO files (file_id, storage_id, root_id, path, mime, size, mtime, state, doc_key) "
    "VALUES (?, 3, 30, ?, 'application/pdf', 10, 1, 'indexed', ?)"
)


def _rows(store: Store, keys: dict[int, str | None]) -> None:
    store._conn.executemany(_INSERT, [(file_id, f"Daten/{file_id}.pdf", key) for file_id, key in keys.items()])


def _keys(store: Store) -> dict[int, str | None]:
    return {int(file_id): key for file_id, key in store._conn.execute("SELECT file_id, doc_key FROM files")}


def _with_a_key_of_rc1(store: Store) -> int:
    return sum(1 for file_id, key in _keys(store).items() if key == _key_of_rc1(file_id))


class _Companion:
    """A companion of the head: names its key for every asked id, or calls the id absent."""

    def __init__(self, absent: Sequence[int] = ()) -> None:
        self.asked: list[list[int]] = []
        self.absent = frozenset(absent)

    async def doc_keys(self, file_ids: Sequence[int]) -> DocKeyAnswer:
        ids = list(file_ids)
        self.asked.append(ids)
        return DocKeyAnswer(
            asked=tuple(ids),
            keys={file_id: _key_of_the_head(file_id) for file_id in ids if file_id not in self.absent},
            absent=frozenset(file_id for file_id in ids if file_id in self.absent),
        )


def _worker(store: Store, companion: _Companion) -> DocKeyBackfill:
    return DocKeyBackfill(
        store=store,
        client_factory=lambda: cast("Any", None),
        files_factory=lambda nc: cast("Any", companion),
        bands_per_round=50,
        pause_seconds=0.0,
        clock=lambda: NOW,
    )


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


# -- the reset in bands (commits 53373888, c93a6f1e) ---------------------------


async def test_a_reset_that_breaks_off_between_two_bands_keeps_the_old_generation_until_a_round_finishes_it(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stopping in the middle of the reset: the gate holds, the next round forgets the rest first.

    Plan 43-24 promised "no key of another format once the meta value says
    generation 2" with one UPDATE in one transaction. In bands the same has to
    hold when a band fails (here the second one, the way a writer that keeps
    the lock longer than the busy timeout ends it): the meta value must still
    name the old generation, which is what the coverage route reads to answer
    counting, and nobody may have been asked for a key yet.
    """
    monkeypatch.setattr(repo_module, "_RESET_DOC_KEYS_BAND", BAND)
    ids = list(range(1, 3 * BAND + 1))
    _rows(store, {file_id: _key_of_rc1(file_id) for file_id in ids})
    store.write_meta(DOC_KEY_MARK, "1:150:0")
    companion = _Companion()
    worker = _worker(store, companion)
    real_transaction = store._transaction
    begun = 0

    def breaking() -> Any:
        nonlocal begun
        begun += 1
        if begun == 2:
            message = "database is locked"
            raise sqlite3.OperationalError(message)
        return real_transaction()

    monkeypatch.setattr(store, "_transaction", breaking)
    with pytest.raises(sqlite3.OperationalError):
        await worker.run_once()

    half_way = _keys(store)
    assert sum(1 for key in half_way.values() if key is None) == BAND
    assert _with_a_key_of_rc1(store) == 2 * BAND
    assert store.read_meta()[DOC_KEY_MARK] == "1:150:0"
    assert stored_generation(store.read_meta()[DOC_KEY_MARK]) != DOC_KEY_GENERATION
    assert companion.asked == []
    assert worker.in_flight is False

    # The next round, undisturbed. What the table holds at the moment the meta
    # value is written for the first time is the promise of plan 43-24.
    monkeypatch.setattr(store, "_transaction", real_transaction)
    left_at_the_mark: list[int] = []
    real_write_meta = store.write_meta

    def watching(key: str, value: str) -> None:
        if key == DOC_KEY_MARK:
            left_at_the_mark.append(_with_a_key_of_rc1(store))
        real_write_meta(key, value)

    monkeypatch.setattr(store, "write_meta", watching)
    await worker.run_once()

    assert left_at_the_mark[0] == 0
    assert stored_generation(store.read_meta()[DOC_KEY_MARK]) == DOC_KEY_GENERATION
    assert _keys(store) == {file_id: _key_of_the_head(file_id) for file_id in ids}


def test_writers_and_new_rows_between_two_bands_never_leave_a_key_of_the_old_format(
    store: Store, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """What other writers do during the reset, case by case, and the one invariant behind it.

    Every writer of a head container writes keys of format 2 only (a job needs
    docKeyFormat 2, an answer of the backfill route format 2). So after the
    reset a row holds no key or a key of the head, wherever the writer got in:

    - a key written onto a row of a band that is done stays (it is right),
    - a key written onto a row of a band still to come is forgotten and asked
      again by the backfill (one repetition, no wrong key),
    - a new row above every file id of the start is reached by a further band,
      because the edge of the next band is asked anew after every commit,
    - a new row in a gap of a band that is done stays.
    """
    monkeypatch.setattr(repo_module, "_RESET_DOC_KEYS_BAND", BAND)
    ids = [file_id * 10 for file_id in range(1, 3 * BAND + 1)]
    _rows(store, {file_id: _key_of_rc1(file_id) for file_id in ids})
    other = sqlite3.connect(tmp_path / "state.db", timeout=0)
    real_transaction = store._transaction
    begun = 0

    def with_a_writer_after_the_first_band() -> Any:
        nonlocal begun
        begun += 1
        if begun == 2:
            other.execute("UPDATE files SET doc_key = ? WHERE file_id = 10", (_key_of_the_head(10),))
            other.execute("UPDATE files SET doc_key = ? WHERE file_id = 1490", (_key_of_the_head(1490),))
            other.execute(_INSERT, (5000, "Daten/5000.pdf", _key_of_the_head(5000)))
            other.execute(_INSERT, (15, "Daten/15.pdf", _key_of_the_head(15)))
            other.commit()
        return real_transaction()

    monkeypatch.setattr(store, "_transaction", with_a_writer_after_the_first_band)

    store.reset_doc_keys()

    other.close()
    after = _keys(store)
    assert begun == 4, "three bands of the start and one more for the row that arrived above them"
    assert after[10] == _key_of_the_head(10)
    assert after[15] == _key_of_the_head(15)
    assert after[1490] is None
    assert after[5000] is None
    assert _with_a_key_of_rc1(store) == 0
    assert {file_id for file_id, key in after.items() if key is not None} == {10, 15}


# -- "doc key verify, checked=95 corrected=3" of run 43016026129 ---------------


@pytest.mark.parametrize(("unresolved_before", "corrected"), [((), 3), ((3,), 2)])
async def test_the_verify_pass_counts_the_rows_whose_file_cache_row_went_as_corrections(
    store: Store,
    caplog: pytest.LogCaptureFixture,
    unresolved_before: tuple[int, ...],
    corrected: int,
) -> None:
    """The three corrections after the topology change are the rows of a deleted home.

    The legs delete the user dave, whose home holds three indexed files; the
    file cache rows go with the user, the container rows live until the sweep
    has removed the storage. The container that starts for phase A verifies at
    once, the companion calls the three ids absent, and each gets the sentinel:
    corrected=3. The leg upgrade has taken the file cache row of one of the
    three away long before (its orphan case, docKeysUnresolved=1), that row
    carries the sentinel already and is no correction: corrected=2. No key of
    a living file changed, and no key of a storage that only left the mount
    list: its file cache rows and its written out id are still there.
    """
    home_of_dave = (1, 2, 3)
    ids = [*home_of_dave, 4, 5]
    _rows(store, {file_id: "" if file_id in unresolved_before else _key_of_the_head(file_id) for file_id in ids})
    store.write_meta(DOC_KEY_MARK, "2:0:0")
    companion = _Companion(absent=home_of_dave)
    caplog.set_level(logging.INFO, logger="findling.worker.doc_keys")

    done = await _worker(store, companion).run_once()

    assert (done.state, done.checked, done.corrected) == (ROUND_VERIFIED, 5, corrected)
    assert f"doc key verify, checked=5 corrected={corrected}" in [record.getMessage() for record in caplog.records]
    after = _keys(store)
    assert [after[file_id] for file_id in home_of_dave] == ["", "", ""]
    assert [after[file_id] for file_id in (4, 5)] == [_key_of_the_head(4), _key_of_the_head(5)]


# -- the denominator of phase A (35 in two legs, 64 to 66 in three) ------------


def _meta(storage_id: int, path: str, *, mime: str = "application/pdf", doc_key: str | None = None) -> FileMeta:
    return FileMeta(
        storage_id=storage_id,
        root_id=storage_id * 10,
        path=path,
        title=None,
        mime=mime,
        size=10,
        mtime=1,
        etag="e",
        doc_key=doc_key,
    )


def test_a_picture_that_waits_for_ocr_is_judged_from_its_first_pass_on_and_no_document_yet(tmp_path: Path) -> None:
    """Why the denominator of phase A moves by the backlog pictures.

    A picture uploaded behind the crawl is in no scan counter. The first pass
    that claims it writes skipped(no_text_layer) and hands it to OCR, and from
    that verdict on the row is judged: the denominator of its storage is
    max(scan counter, judged + verdicts of the PHP side), so it rises by one
    per picture the poller has taken, while the numerator waits for OCR. A leg
    that reads the page before the first pass ended shows the denominator
    without the pictures, a leg that reads it after shows it with them; both
    are the rule of D-43-11 at their moment. unreadable is the control: that
    verdict belongs to the PHP side and is judged nowhere here.
    """
    state = tmp_path / "state.db"
    vectors = tmp_path / "vectors.db"
    opened = open_store(state)
    try:
        opened.record(70, _meta(7, "files/akte.pdf"), "indexed")
        before = coverage_counts(state, vectors, [7], [])
        opened.record(71, _meta(7, "files/backlog/backlog-1.png", mime="image/png"), "skipped", "no_text_layer")
        waiting = coverage_counts(state, vectors, [7], [])
        opened.record(72, _meta(7, "files/gesperrt.txt", mime="text/plain"), "skipped", "unreadable")
        control = coverage_counts(state, vectors, [7], [])
    finally:
        opened.close()

    assert (before.documents_by_storage, before.judged_by_storage) == ({7: 1}, {7: 1})
    assert (waiting.documents_by_storage, waiting.judged_by_storage) == ({7: 1}, {7: 2})
    assert (control.documents_by_storage, control.judged_by_storage) == ({7: 1}, {7: 2})


# -- F-43B-01: keys taken while a hashed storage had no identity ---------------


def test_p_f_43b_01_keys_without_identity_of_two_members_under_two_roots_count_two_files_as_one(
    tmp_path: Path,
) -> None:
    """Finding F-43B-01 (LOW), the container half, as it is today.

    A storage whose id Nextcloud keeps as an md5 has its share identity only
    while the configuration can be read and oc_mounts shows it. A key asked
    in between (the verify pass while the storage is out of the mount list, a
    job or a backfill band while the configuration query fails) is taken
    without identity: an empty share and the path inside the storage alone
    (DocKeyService::docKeysFor, which StorageService::shareIdentities gives no
    error to fail on). Back in its group, two such members under the roots
    sicherheit and projekt name sicherheit/bericht.txt and projekt/bericht.txt
    with one key, and the group counts one document where two files are. The
    verify pass puts the keys right, a day later at most.

    One member alone with such a key counts too much and never merges, which
    is the direction the plans allow. On the day the companion stops handing
    out a key without identity for a hashed id, the first assertion below
    stays a statement about the container and the docstring loses its case.
    """
    share = "smb::fs.example//daten"
    state = tmp_path / "state.db"
    vectors = tmp_path / "vectors.db"

    def counted(key_under_sicherheit: str, key_under_projekt: str, key_at_the_top: str) -> tuple[int, ...]:
        with contextlib.suppress(FileNotFoundError):
            state.unlink()
        opened = open_store(state)
        try:
            opened.record(4001, _meta(40, "sicherheit/bericht.txt", doc_key=key_at_the_top), "indexed")
            opened.record(4101, _meta(41, "bericht.txt", doc_key=key_under_sicherheit), "indexed")
            opened.record(4201, _meta(42, "bericht.txt", doc_key=key_under_projekt), "indexed")
        finally:
            opened.close()
        both = coverage_counts(state, vectors, [41, 42], [[41, 42]]).documents_by_group
        with_the_top = coverage_counts(state, vectors, [40, 41], [[40, 41]]).documents_by_group
        return (*both, *with_the_top)

    right_sicherheit = _format_two(share, "sicherheit/bericht.txt")
    right_projekt = _format_two(share, "projekt/bericht.txt")
    without_identity = _format_two("", "bericht.txt")
    assert len({right_sicherheit, right_projekt, without_identity}) == 3

    # Keys taken with the identity: two files under two roots, one file under the top and its root.
    assert counted(right_sicherheit, right_projekt, right_sicherheit) == (2, 1)
    # One member without identity: nothing merges, the file it shares with the top counts twice.
    assert counted(without_identity, right_projekt, right_sicherheit) == (2, 2)
    # Both members without identity: two different files are one document.
    assert counted(without_identity, without_identity, right_sicherheit) == (1, 2)


# -- F-43B-02: a disable that lands while the catch-up looks at its mark -------


class _OneEmptyMount:
    """One mount with one empty final page behind a quiet queue."""

    async def mounts(self) -> MountResult:
        return MountResult(mounts=(Mount(storage_id=3, root_id=17, overridden_root=18),))

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> SliceResult:
        del storage, root, after, limit
        return SliceResult(files=(), final=True)

    async def stats(self) -> QueueStats:
        return QueueStats(scheduled=0)

    async def requeue(self, file_ids: object, *, kind: str) -> CallResult:
        del file_ids, kind
        return CallResult(ok=True)


class _OnceWithASlowLook(Reconcile):
    """The real reconcile in its one time mode; the look at the mark can be held open."""

    def __init__(self) -> None:
        fake = _OneEmptyMount()
        super().__init__(
            client_factory=lambda: cast("Any", None),
            files_factory=lambda nc: cast("Any", fake),
            queue_factory=lambda nc: cast("Any", fake),
            tick_seconds=0.001,
            pause_seconds=0.0,
            clock=lambda: time.time() + 100 * 3600,
        )
        self.rounds = 0
        self.looking = asyncio.Event()
        self.look_on = asyncio.Event()

    async def _catchup_mark(self) -> str:
        mark = await super()._catchup_mark()
        if not self.look_on.is_set():
            self.looking.set()
            await self.look_on.wait()
        return mark

    async def run_once(self) -> RoundResult:
        self.rounds += 1
        return await super().run_once()


def _catch_up_mark(value: str | None = None) -> str:
    opened = open_store(settings().state_db)
    try:
        if value is not None:
            opened.write_meta(CATCHUP_MARK, value)
        return opened.read_meta().get(CATCHUP_MARK, "")
    finally:
        opened.close()


@pytest.mark.usefixtures("volume")
async def test_p_f_43b_02_a_disable_that_lands_in_the_look_at_the_mark_still_starts_one_round() -> None:
    """Finding F-43B-02 (LOW), as it is today, and the cause of the flaky lifespan test.

    The one time cycle asks for its arming, then looks at CATCHUP_MARK off the
    loop, then runs. A backup hold that lands in that look is asked again
    behind it (F-41A-02); a disable is not, so the round starts on a container
    that was just switched off. tests/test_main_lifespan.py
    test_a_disable_while_the_cycle_waits_silences_it_again hit this window in
    7 of 300 runs: its cycle looks every millisecond, and the mark it writes
    after the disable could still reach a look that was under way.

    On the day run() asks for the arming again behind the look, rounds is 0
    here and the mark stays as it was.
    """
    _catch_up_mark(CATCHUP_RECONCILE)
    once = _OnceWithASlowLook()
    stop = asyncio.Event()
    once.arm()
    task = asyncio.create_task(once.run(stop, once=True))
    try:
        await asyncio.wait_for(once.looking.wait(), timeout=5.0)
        once.silence()
        once.look_on.set()
        await asyncio.wait_for(task, timeout=5.0)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5.0)
        await once.aclose()

    assert once.rounds == 1
    assert _catch_up_mark() == CATCHUP_DONE


@pytest.mark.usefixtures("volume")
async def test_a_disable_while_the_cycle_waits_between_two_looks_starts_no_round() -> None:
    """The control of the probe above: outside the look the disable holds.

    The same object and the same mark, only the moment differs: the cycle is
    between two looks (or its look has ended) when the mark turns. in_flight
    can only fall after the disable, because run() asks for the arming and
    raises in_flight in one step.
    """
    once = _OnceWithASlowLook()
    once.look_on.set()
    stop = asyncio.Event()
    once.arm()
    task = asyncio.create_task(once.run(stop, once=True))
    try:
        await asyncio.sleep(0.05)
        once.silence()
        for _ in range(5000):
            if not once.in_flight:
                break
            await asyncio.sleep(0.001)
        assert once.in_flight is False
        _catch_up_mark(CATCHUP_RECONCILE)
        await asyncio.sleep(0.1)
    finally:
        stop.set()
        await asyncio.wait_for(task, timeout=5.0)
        await once.aclose()

    assert once.rounds == 0
    assert _catch_up_mark() == CATCHUP_RECONCILE


# -- F-43B-03: the warning of a count without a vector stock -------------------


def test_p_f_43b_03_every_count_without_a_vector_stock_writes_a_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Finding F-43B-03 (LOW), as it is today: one warning per count, not one per process.

    The legs of run 43016026129 start the container with
    FINDLING_EMBED_ENABLED=false, so no vectors.db exists, and each of the 72
    counts in the request wrote the line (72 lines, 72 POST /coverage with a
    figure). An instance that runs without embeddings on purpose gets the same
    line for every look at the admin page. The figure itself is right: 0.

    On the day the line is written once per process, or below warning while
    embeddings are switched off, the count below is 1 or 0.
    """
    state = tmp_path / "state.db"
    opened = open_store(state)
    try:
        opened.record(70, _meta(7, "files/akte.pdf"), "indexed")
    finally:
        opened.close()
    caplog.set_level(logging.WARNING, logger="findling.store.repo")

    figures = [coverage_counts(state, tmp_path / "vectors.db", [7], []) for _ in range(3)]

    lines = [record.getMessage() for record in caplog.records if record.levelno == logging.WARNING]
    assert lines == ["coverage count without a vector stock, the vector figure is 0"] * 3
    assert [figure.embedded_documents for figure in figures] == [0, 0, 0]
    assert [figure.documents for figure in figures] == [1, 1, 1]
