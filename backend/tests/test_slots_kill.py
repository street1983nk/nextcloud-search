"""SC2 under four slots: a SIGKILL costs no row and indexes no file twice (D-26-08).

Both cases of D-26-08, each against the real poller on four real children, the
real writer and the real state.db, driven by tests/slots_kill_harness.py in a
process of its own (the subject is a SIGKILL, which cannot be staged inside the
process that asserts on it):

1. **The main process dies** in the middle of a pass. The rows it held come back
   after the lease of the queue file, a second run on the same volume works them
   off, and every file ends in the index exactly once. On the way the pass mark
   multi_slot_pass is left behind, and the restore of the guard reads it as an
   unclean end (D-26-16).
2. **One child dies** while the three beside it keep working. Its file gets no
   verdict under four slots, runs once more alone behind the barrier, and is in
   the index exactly once; the guard counts the kill as an OOM kill (D-26-16).

**Why the slots are injected.** The 4 core runner of the CI never reaches four
slots through the profile formula (Pitfall 10), and an environment switch for
the slot count is the INDEX_WORKERS taboo; so the harness hands ocr_slots to
the constructor of the poller. The files take 1.5 s each on the sleep probe of a
real child, so no tesseract is needed and the moment of the kill is under
control.

**Where the proof lives.** Linux only: SIGKILL, process groups and /proc. On
Windows the module is skipped; the evidence is the Linux CI (python.yml,
ubuntu-24.04) after a push. Every wait has a hard deadline, so a broken build
fails instead of hanging, and every child is killed in a finally.
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from tantivy import Query

from findling import guard
from findling.index.open import open_index
from findling.index.schema import FIELD_FILE_ID
from findling.store.repo import open_store
from slots_kill_harness import (
    CONSTITUENTS,
    INDEX_DIR,
    MARK_ADDED,
    MARK_STARTED,
    MARKS_DIR,
    MODE_RESTORE,
    MODE_RUN,
    PIDS_FILE,
    QUEUE_FILE,
    SLOTS,
    STATE_FILE,
    FileQueue,
)

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="SIGKILL and process groups, Linux CI carries it")

HARNESS = Path(__file__).resolve().with_name("slots_kill_harness.py")
BACKEND = Path(__file__).resolve().parents[1]

# The corpus: twelve OCR rows, eight of them in the first pass (two per slot)
# and four behind it.
ROWS = 12
# How long one wait may take, and how long a whole harness run; both far below
# the 30 s budget of a case on a healthy runner, and both end in a failure.
WAIT_SECONDS = 20.0
RUN_SECONDS = 25.0
POLL_SECONDS = 0.02


def _start(volume: Path, mode: str) -> subprocess.Popen[str]:
    environment = dict(os.environ)
    environment["APP_PERSISTENT_STORAGE"] = str(volume)
    environment["FINDLING_EMBED_ENABLED"] = "false"
    return subprocess.Popen(  # noqa: S603 - an argument list of this interpreter, never a shell
        [sys.executable, str(HARNESS), str(volume), mode],
        cwd=BACKEND,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _answer(process: subprocess.Popen[str]) -> dict[str, Any]:
    """Wait for a harness run and read its JSON line; a failed run is red with its stderr."""
    out, err = process.communicate(timeout=RUN_SECONDS)
    assert process.returncode == 0, f"the harness ended with {process.returncode}: {err[-2000:]}"
    lines = [line for line in out.splitlines() if line.strip()]
    assert lines, f"the harness printed nothing: {err[-2000:]}"
    return json.loads(lines[-1])


def _marks(volume: Path, kind: str) -> set[int]:
    return {int(entry.name.rsplit("-", 1)[1]) for entry in (volume / MARKS_DIR).glob(f"{kind}-*")}


def _pids(volume: Path) -> list[int]:
    try:
        return [int(pid) for pid in json.loads((volume / PIDS_FILE).read_text(encoding="ascii"))]
    except (OSError, ValueError):
        return []


def _wait_for(condition: Callable[[], bool], process: subprocess.Popen[str], what: str) -> None:
    deadline = time.monotonic() + WAIT_SECONDS
    while not condition():
        if process.poll() is not None:
            _, err = process.communicate()
            pytest.fail(f"the harness ended before {what}: {err[-2000:]}")
        if time.monotonic() >= deadline:
            pytest.fail(f"no {what} within {WAIT_SECONDS:.0f} s")
        time.sleep(POLL_SECONDS)


def _kill(pid: int, *, group: bool = False) -> None:
    """SIGKILL to one process, or to the group a child leads; gone already is fine."""
    if sys.platform == "win32":
        return
    import signal

    with contextlib.suppress(ProcessLookupError, PermissionError):
        if group:
            os.killpg(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)


@contextlib.contextmanager
def _reaped(volume: Path, processes: list[subprocess.Popen[str]]) -> Iterator[None]:
    """Kill every harness and every child it left, whatever the case did (T-26-37)."""
    try:
        yield
    finally:
        for process in processes:
            if process.poll() is None:
                _kill(process.pid)
                process.communicate()
        # Each child made itself a session leader, so its group is its pid.
        for pid in _pids(volume):
            _kill(pid, group=True)


def _once_each(volume: Path, file_ids: list[int]) -> None:
    """Every file exactly once in the index, and nothing else in it."""
    index = open_index(volume / INDEX_DIR, CONSTITUENTS)
    index.reload()
    searcher = index.searcher()
    for file_id in file_ids:
        hits = searcher.search(Query.term_query(index.schema, FIELD_FILE_ID, file_id), 10).hits
        assert len(hits) == 1, f"file {file_id} is {len(hits)} times in the index"
    assert searcher.num_docs == len(file_ids)


def _pass_mark(volume: Path) -> str:
    store = open_store(volume / STATE_FILE)
    try:
        return store.read_meta().get(guard.META_MULTI_SLOT_PASS, "")
    finally:
        store.close()


def test_a_killed_main_process_mid_pass_loses_no_row_and_indexes_once(tmp_path: Path) -> None:
    volume = tmp_path / "volume"
    volume.mkdir()
    queue = FileQueue(volume / QUEUE_FILE)
    file_ids = queue.seed(ROWS)
    processes: list[subprocess.Popen[str]] = []

    with _reaped(volume, processes):
        first = _start(volume, MODE_RUN)
        processes.append(first)
        # Half a pass: the first wave is through its extraction, the second has
        # started on its children, and nothing of the pass is committed yet.
        _wait_for(
            lambda: (
                len(_marks(volume, MARK_ADDED)) >= 2
                and len(_marks(volume, MARK_STARTED)) >= len(_marks(volume, MARK_ADDED)) + 2
            ),
            first,
            "half a pass",
        )
        _kill(first.pid)
        first.communicate(timeout=RUN_SECONDS)
        # The container died with its children; a restart finds none of them.
        for pid in _pids(volume):
            _kill(pid, group=True)

        assert _pass_mark(volume) == "performance"
        restore = _start(volume, MODE_RESTORE)
        processes.append(restore)
        assert _answer(restore)["cause"] == guard.CAUSE_UNCLEAN_END

        second = _start(volume, MODE_RUN)
        processes.append(second)
        answer = _answer(second)

    assert answer["waiting"] == 0
    assert queue.waiting() == []
    assert queue.failures() == []
    _once_each(volume, file_ids)


def test_a_killed_child_mid_pass_is_retried_alone_and_indexed_once(tmp_path: Path) -> None:
    volume = tmp_path / "volume"
    volume.mkdir()
    queue = FileQueue(volume / QUEUE_FILE)
    file_ids = queue.seed(ROWS)
    processes: list[subprocess.Popen[str]] = []

    with _reaped(volume, processes):
        run = _start(volume, MODE_RUN)
        processes.append(run)
        # All four children are there and every one of them is inside a file.
        _wait_for(
            lambda: len(_pids(volume)) == SLOTS and len(_marks(volume, MARK_STARTED)) == SLOTS,
            run,
            "four children at work",
        )
        assert not _marks(volume, MARK_ADDED), "a file was through before the kill, the case lost its moment"
        _kill(_pids(volume)[0])
        answer = _answer(run)

    assert answer["kills"] == 1
    assert answer["cause"] == guard.CAUSE_OOM_KILL
    assert answer["waiting"] == 0
    assert queue.waiting() == []
    assert queue.failures() == []
    _once_each(volume, file_ids)
