"""The kill harness of SC2: the real poller on four real children, killed from outside.

Not a test module (no test_ prefix, pytest does not collect it). tests/test_slots_kill.py
starts it as its own process with ``sys.executable``, because the subject is a
SIGKILL, and a SIGKILL cannot be staged inside the process that asserts on it.

    python slots_kill_harness.py <volume> run       work the queue file until it is empty
    python slots_kill_harness.py <volume> restore   restore the guard like the lifespan does

**What is real.** The Poller of findling.worker.poller with its barrier, its
solo run and its pass mark; four ExtractionWorker children in a SlotPool; the
tantivy writer on an index in the volume; state.db through open_store; and the
GuardWatch of the lifespan for the restore and for the tick that turns a child
kill into a lowering.

**What is not, and why.** Nextcloud is replaced by :class:`FileQueue`, a SQLite
file in the volume with the lease rules of the PHP side, so that a queue row
survives the kill of the process that held it. The extraction is the sleep probe
of the sandbox on a real child, 1.5 s per file, and the text is built in the
parent afterwards; so the test needs no tesseract and the duration of a file is
under control (26-11-PLAN, discretion). The slot count is injected, four, through the
constructor of the poller: the 4 core runner of the CI never reaches four slots through the profile formula
(Pitfall 10), and an environment switch for the slots is the INDEX_WORKERS taboo.

**The PHP rules this queue follows**, each read out of QueueMapper.php and
QueueService.php, the same three _WorkStock in tests/test_poller.py models:

* claimBatch takes free rows and rows whose lease ran out, in queue order, with
  a ceiling per kind (KIND_BATCH, and KIND_BATCH_INDEX_LANE on the index lane),
  and counts the delivery on the row (retries + 1) when it hands it out;
* a row above MAX_DELIVERIES is written off as failed(repeatedly_stuck) and
  never delivered;
* unlock frees the row and gives the delivery back (retries - 1);
* acknowledge deletes the done rows and records the failed ones.

Every call is one transaction with its own commit, which is what makes the file
survive a SIGKILL at any moment. Nothing here names a real user, path or text.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
import sqlite3
import sys
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from typing import IO, Any, Final, cast

from findling import guard, lane
from findling.config import OCR_CLAIM_BATCH, OCR_CLAIM_BATCH_INDEX_LANE, settings
from findling.extract.errors import ExtractionOutcome, State
from findling.extract.pool import SlotPool
from findling.hardware import Hardware
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter
from findling.nc.client import AsyncNextcloudApp, GatewayClient
from findling.nc.queue import (
    KIND_OCR,
    LANE_ALL,
    LANE_INDEX,
    TOPUP_IDLE,
    CallResult,
    ClaimResult,
    CompanionChoice,
    DocumentQueue,
    QueueJob,
    QueueStats,
)
from findling.profile import note_hardware
from findling.store.repo import open_store
from findling.worker.poller import ROUND_EMPTY, Poller
from findling.worker.watch import GuardWatch

HERE: Final = Path(__file__).resolve().parent
PHP_QUEUE_SERVICE: Final = HERE.parents[1] / "php" / "lib" / "Service" / "QueueService.php"
CONSTITUENTS: Final = (HERE / "fixtures" / "constituents_de.txt").read_text(encoding="utf-8").split()

# The files of one volume, shared by the harness and the test.
QUEUE_FILE: Final = "queue.db"
STATE_FILE: Final = "state.db"
INDEX_DIR: Final = "index"
TMP_DIR: Final = "tmp"
MARKS_DIR: Final = "marks"
PIDS_FILE: Final = "pids.json"

MARK_STARTED: Final = "started"
MARK_ADDED: Final = "added"

MODE_RUN: Final = "run"
MODE_RESTORE: Final = "restore"

# The slot count the harness pins (Pitfall 10) and the duration of one file.
SLOTS: Final = 4
SLEEP_SECONDS: Final = 1.5
# The lease of the fake. Longer than one file, shorter than the patience of the
# test: a row the killed process held comes back within seconds, not minutes.
LEASE_SECONDS: Final = 4.0
# The rounds a run may take before it gives up, and how often pids.json is written.
MAX_ROUNDS: Final = 20
PIDS_TICK_SECONDS: Final = 0.05

# The profile the fake companion answers and the box the harness claims to be:
# 16 cores and 64 GiB, so that Performance is the effective level.
CHOSEN_PROFILE: Final = "performance"
CHOSEN_PRECISION: Final = "int8"
GIB: Final = 2**30
HEADROOM_BYTES: Final = 64 * GIB
HARDWARE: Final = Hardware(
    cpu_count=16,
    cpu_quota=None,
    cores=16,
    memory_limit_bytes=None,
    memory_available_bytes=HEADROOM_BYTES,
    memory_total_bytes=HEADROOM_BYTES,
    architecture="x86_64",
    cgroup="none",
)

# The kind ceilings of one claim (QueueService::KIND_BATCH and
# KIND_BATCH_INDEX_LANE for ocr). Both mirrors are parity pinned in
# tests/test_config.py, so reading them from the config is reading the PHP.
_OCR_CEILING: Final = {LANE_INDEX: OCR_CLAIM_BATCH_INDEX_LANE, LANE_ALL: OCR_CLAIM_BATCH}

_SCHEMA: Final = """
CREATE TABLE IF NOT EXISTS queue (
    queue_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL UNIQUE,
    kind TEXT NOT NULL,
    mime TEXT NOT NULL,
    size INTEGER NOT NULL,
    retries INTEGER NOT NULL DEFAULT 0,
    locked_at REAL,
    verdict TEXT
);
CREATE TABLE IF NOT EXISTS failures (file_id INTEGER NOT NULL, reason TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS handovers (file_id INTEGER NOT NULL, kind TEXT NOT NULL);
"""


def _max_deliveries() -> int:
    """QueueService::MAX_DELIVERIES, read out of the PHP source like test_poller does."""
    found = re.search(r"const MAX_DELIVERIES = (\d+);", PHP_QUEUE_SERVICE.read_text(encoding="utf-8"))
    if found is None:
        raise RuntimeError("the delivery ceiling is no longer where the harness looks for it")
    return int(found.group(1))


def scan_title(file_id: int) -> str:
    """The synthetic name of one scan."""
    return f"scan-{file_id}.pdf"


def scan_text(file_id: int) -> str:
    """The synthetic text the parent builds for one scan."""
    return f"document {file_id}"


class FileQueue:
    """A work stock in a SQLite file, with the lease semantics of the PHP side.

    The surface is the one the poller reaches through ``queue_factory``, with the
    signatures of DocumentQueue. Each call opens its own connection and commits
    before it returns, so a SIGKILL between two calls loses nothing.
    """

    def __init__(self, path: Path, *, lease_seconds: float = LEASE_SECONDS) -> None:
        self._path = path
        self._lease = lease_seconds
        self._max_deliveries = _max_deliveries()
        # executescript commits on its own, so the schema runs outside a transaction.
        connection = sqlite3.connect(self._path, timeout=10.0, isolation_level=None)
        try:
            connection.executescript(_SCHEMA)
        finally:
            connection.close()

    @contextlib.contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._path, timeout=10.0, isolation_level=None)
        try:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            connection.execute("COMMIT")
        finally:
            connection.close()

    # -- what the test uses ------------------------------------------------

    def seed(self, count: int, *, first_file_id: int = 1001) -> list[int]:
        """Put ``count`` OCR rows into the stock and return their file ids."""
        file_ids = [first_file_id + offset for offset in range(count)]
        with self._transaction() as connection:
            connection.executemany(
                "INSERT INTO queue (file_id, kind, mime, size) VALUES (?, ?, 'application/pdf', 64)",
                [(file_id, KIND_OCR) for file_id in file_ids],
            )
        return file_ids

    def waiting(self) -> list[int]:
        """The file ids still in the stock, locked or not, in queue order."""
        with self._transaction() as connection:
            return [int(row[0]) for row in connection.execute("SELECT file_id FROM queue ORDER BY queue_id")]

    def failures(self) -> list[tuple[int, str]]:
        """Every failed verdict the stock recorded, a give-up included."""
        with self._transaction() as connection:
            return [(int(row[0]), str(row[1])) for row in connection.execute("SELECT file_id, reason FROM failures")]

    def seconds_until_a_lease_ends(self) -> float | None:
        """How long until the next locked row is free again; None without one."""
        with self._transaction() as connection:
            row = connection.execute("SELECT MIN(locked_at) FROM queue WHERE locked_at IS NOT NULL").fetchone()
        if row is None or row[0] is None:
            return None
        return max(0.0, float(row[0]) + self._lease - time.time())

    # -- what the poller uses ---------------------------------------------

    async def companion_choice(self) -> CompanionChoice:
        return CompanionChoice(profile=CHOSEN_PROFILE, precision=CHOSEN_PRECISION, confirmed=None)

    async def claim(self, *, limit: int, max_bytes: int, lane: str | None = None) -> ClaimResult:
        echoed = lane or LANE_ALL
        now = time.time()
        jobs: list[QueueJob] = []
        taken: dict[str, int] = {}
        budget = max_bytes
        with self._transaction() as connection:
            rows = connection.execute(
                "SELECT queue_id, file_id, kind, mime, size, retries FROM queue "
                "WHERE locked_at IS NULL OR locked_at <= ? ORDER BY queue_id",
                (now - self._lease,),
            ).fetchall()
            for queue_id, file_id, kind, mime, size, retries in rows:
                if len(jobs) >= limit:
                    break
                ceiling = _OCR_CEILING[echoed] if kind == KIND_OCR else limit
                if taken.get(kind, 0) >= ceiling or (jobs and int(size) > budget):
                    continue
                # claimBatch counts the delivery when it hands the row out.
                delivered = int(retries) + 1
                if delivered > self._max_deliveries:
                    connection.execute("DELETE FROM queue WHERE queue_id = ?", (queue_id,))
                    connection.execute(
                        "INSERT INTO failures (file_id, reason) VALUES (?, 'repeatedly_stuck')", (file_id,)
                    )
                    continue
                connection.execute(
                    "UPDATE queue SET retries = ?, locked_at = ? WHERE queue_id = ?", (delivered, now, queue_id)
                )
                taken[kind] = taken.get(kind, 0) + 1
                budget = max(0, budget - int(size))
                jobs.append(_job_of(int(queue_id), int(file_id), str(kind), str(mime), int(size)))
        return ClaimResult(jobs=tuple(jobs), lane_honored=True)

    async def unlock(self, ids: Sequence[int]) -> CallResult:
        released = 0
        with self._transaction() as connection:
            for queue_id in ids:
                cursor = connection.execute(
                    "UPDATE queue SET locked_at = NULL, retries = MAX(0, retries - 1) "
                    "WHERE queue_id = ? AND locked_at IS NOT NULL",
                    (queue_id,),
                )
                released += cursor.rowcount
        return CallResult(ok=True, count=released)

    async def acknowledge(
        self, done: Sequence[int], failed: Mapping[int, str], skipped: Mapping[int, str] | None = None
    ) -> CallResult:
        del skipped
        count = 0
        with self._transaction() as connection:
            for queue_id in done:
                count += connection.execute("DELETE FROM queue WHERE queue_id = ?", (queue_id,)).rowcount
            for queue_id, reason in failed.items():
                row = connection.execute("SELECT file_id FROM queue WHERE queue_id = ?", (queue_id,)).fetchone()
                if row is None:
                    continue
                connection.execute("INSERT INTO failures (file_id, reason) VALUES (?, ?)", (row[0], reason))
                count += connection.execute("DELETE FROM queue WHERE queue_id = ?", (queue_id,)).rowcount
        return CallResult(ok=True, count=count)

    async def requeue(self, file_ids: Sequence[int], *, kind: str) -> CallResult:
        # A handover (to embed, with a model) is taken and kept apart: the row
        # leaves the stock of this harness, which is about the OCR rows only.
        moved = 0
        with self._transaction() as connection:
            for file_id in file_ids:
                connection.execute("INSERT INTO handovers (file_id, kind) VALUES (?, ?)", (file_id, kind))
                moved += connection.execute("DELETE FROM queue WHERE file_id = ?", (file_id,)).rowcount
        return CallResult(ok=True, count=moved)

    async def top_up(self) -> str:
        return TOPUP_IDLE

    async def stats(self) -> QueueStats:
        return QueueStats(scheduled=len(self.waiting()))


def _job_of(queue_id: int, file_id: int, kind: str, mime: str, size: int) -> QueueJob:
    title = scan_title(file_id)
    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=1,
        root_id=1,
        path=f"Scans/{title}",
        title=title,
        mime=mime,
        size=size,
        mtime=1_756_600_000,
        etag="",
        user_ids=("alice",),
        fetch_as="alice",
        is_update=False,
        kind=kind,
    )


async def _fetch(
    nc: AsyncNextcloudApp, file_id: int, user_id: str, fp: IO[bytes], *, client: object = None, expected: int = 0
) -> int | None:
    """The content gateway: the bytes of a scan are its file id, which the extractor reads back."""
    del nc, user_id, client, expected
    body = f"{file_id}".encode("ascii")
    fp.write(body)
    return len(body)


class _Gateway:
    async def aclose(self) -> None:
        return None


class _Extractor:
    """The sleep probe on a real child, then the text built in the parent."""

    def __init__(self, pool: SlotPool, marks: Path) -> None:
        self._pool = pool
        self._marks = marks

    def __call__(
        self, path: str, mime: str, size: int, *, route: object = None, timeout_seconds: float | None = None
    ) -> ExtractionOutcome:
        del mime, size, route, timeout_seconds
        file_id = int(Path(path).read_text(encoding="ascii"))
        (self._marks / f"{MARK_STARTED}-{file_id}").touch()
        # ChildKilled travels on untouched: the poller is the one that decides.
        outcome = self._pool.run_probe("sleep", SLEEP_SECONDS)
        if outcome.state is not State.INDEXED:
            return outcome
        (self._marks / f"{MARK_ADDED}-{file_id}").touch()
        return ExtractionOutcome.indexed(scan_text(file_id))


class _PidWriter(threading.Thread):
    """Writes the pids of the children into pids.json until stopped, atomically."""

    def __init__(self, pool: SlotPool, target: Path) -> None:
        super().__init__(daemon=True)
        self._pool = pool
        self._target = target
        self.halt = threading.Event()

    def run(self) -> None:
        scratch = self._target.with_suffix(".tmp")
        while not self.halt.is_set():
            scratch.write_text(json.dumps(sorted(self._pool.pids())), encoding="ascii")
            scratch.replace(self._target)
            self.halt.wait(PIDS_TICK_SECONDS)


def _guard_watch(volume: Path) -> GuardWatch:
    # No cgroup readings: the harness is about the kills it stages, not about
    # the memory of the runner.
    return GuardWatch(state_path=volume / STATE_FILE, events=lambda: None, headroom=lambda: None)


async def _run(volume: Path) -> dict[str, Any]:
    marks = volume / MARKS_DIR
    marks.mkdir(parents=True, exist_ok=True)
    note_hardware(HARDWARE)
    # The embed runner beside the loop, so the claim asks for the index lane and
    # its ocr ceiling of 32 (D-26-05); inline it would be the 2 of lane all.
    lane.note_mode(lane.MODE_PARALLEL, lane.REASON_NONE)
    queue = FileQueue(volume / QUEUE_FILE)
    store = open_store(volume / STATE_FILE)
    watch = _guard_watch(volume)
    # Before the first pass, as the lifespan orders it (D-26-01).
    await watch.restore()
    index_dir = volume / INDEX_DIR
    writer = IndexBatchWriter(open_index(index_dir, CONSTITUENTS), directory=index_dir, min_free_bytes=0)
    pool = SlotPool(SLOTS)
    pids = _PidWriter(pool, volume / PIDS_FILE)
    pids.start()
    poller = Poller(
        store=store,
        writer=writer,
        tmp_dir=volume / TMP_DIR,
        client_factory=lambda: cast("AsyncNextcloudApp", object()),
        gateway_factory=lambda: cast("GatewayClient", _Gateway()),
        queue_factory=lambda nc: cast("DocumentQueue", queue),
        fetch=_fetch,
        extract=_Extractor(pool, marks),
        pool=pool,
        ocr_slots=4,
        headroom=lambda: HEADROOM_BYTES,
    )
    try:
        for _ in range(MAX_ROUNDS):
            if not queue.waiting():
                break
            result = await poller.run_once()
            if result.state == ROUND_EMPTY:
                wait = queue.seconds_until_a_lease_ends()
                if wait is None:
                    break
                await asyncio.sleep(wait + 0.05)
        # The tick of the guard task over the kills of this run, exactly as the
        # lifespan runs it; the count is taken first so it can be reported, and
        # handed back so the tick sees what the pool saw.
        kills = guard.take_child_kills()
        for _ in range(kills):
            guard.report_child_kill()
        await watch.run_once()
        return {"cause": guard.snapshot().cause, "kills": kills, "waiting": len(queue.waiting())}
    finally:
        pids.halt.set()
        pids.join()
        await poller.aclose()
        await asyncio.to_thread(pool.close)
        writer.close()
        store.close()
        await watch.aclose()


async def _restore(volume: Path) -> dict[str, Any]:
    watch = _guard_watch(volume)
    try:
        await watch.restore()
    finally:
        await watch.aclose()
    return {"cause": guard.snapshot().cause}


def main(argv: Sequence[str]) -> int:
    """``<volume> run|restore``; prints one JSON line and answers 0."""
    if len(argv) != 2 or argv[1] not in {MODE_RUN, MODE_RESTORE}:
        sys.stderr.write("usage: slots_kill_harness.py <volume> run|restore\n")
        return 2
    volume = Path(argv[0])
    volume.mkdir(parents=True, exist_ok=True)
    # The volume is the persistent storage of this process, and no model is
    # loaded: the text of a scan is built in the parent.
    os.environ["APP_PERSISTENT_STORAGE"] = str(volume)
    os.environ["FINDLING_EMBED_ENABLED"] = "false"
    settings.cache_clear()
    runner = _run if argv[1] == MODE_RUN else _restore
    answer = asyncio.run(runner(volume))
    sys.stdout.write(json.dumps(answer) + "\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
