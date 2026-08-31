"""The process guard: one long lived child, killed on time, replaced on schedule.

Three of the tests here cannot be written with a document. A file that hangs for
two minutes or eats half a gigabyte does not exist in the reference corpus, and
building one would test the document rather than the guard. The worker therefore
answers a small set of diagnostic jobs, and these tests use them to drive the
guard into exactly the three situations it exists for: a job that never returns, a
job that exceeds the address space, and a child that dies mid sentence.

The fourth property is the one that is easiest to lose again: the child must not
import the analysis half of the package. That costs roughly 23 MB and a third of a
second per recycle, measured in plan 02-01, for an automaton the extractor never
uses. The test asks a running child what it has loaded, because the alternative is
a comment, and a comment does not notice the next convenient import.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator

import pytest

from findling import config
from findling.extract import sandbox
from findling.extract.errors import ExtractionOutcome, Reason, State

# A mimetype outside the allowlist is the cheapest complete round trip there is:
# the child judges it and answers without touching the file system at all, so the
# test measures the guard and not a disk.
UNSUPPORTED = "application/x-findling-not-a-real-type"
NOWHERE = "/nowhere/does-not-exist.bin"

ONLY_POSIX = pytest.mark.skipif(
    sys.platform == "win32",
    reason="RLIMIT_AS is a POSIX limit; the container this ships in is Linux",
)


@pytest.fixture
def worker() -> Iterator[sandbox.ExtractionWorker]:
    started = sandbox.ExtractionWorker(max_files=200, timeout_seconds=60)
    yield started
    started.stop()


def test_the_start_method_is_spawn_not_fork() -> None:
    # fork in a process that holds an event loop and open sockets is a documented
    # source of deadlocks, and the parent of this child is exactly that.
    assert sandbox.SPAWN_CONTEXT.get_start_method() == "spawn"


def test_extract_guarded_returns_the_verdict_from_the_child() -> None:
    outcome = sandbox.extract_guarded(NOWHERE, UNSUPPORTED, 1024)

    assert outcome == ExtractionOutcome.skipped(Reason.MIME_NOT_ALLOWED)


def test_two_jobs_share_one_child(worker: sandbox.ExtractionWorker) -> None:
    worker.run(NOWHERE, UNSUPPORTED, 1024)
    first = worker.pid
    worker.run(NOWHERE, UNSUPPORTED, 1024)
    second = worker.pid

    assert first is not None
    assert first == second


def test_child_is_recycled_after_max_files() -> None:
    # The count is a safety parameter, not a performance one: because the address
    # space limit now covers the sum over many files instead of one, the planned
    # replacement is what bounds a slow leak.
    short_lived = sandbox.ExtractionWorker(max_files=2, timeout_seconds=60)
    try:
        short_lived.run(NOWHERE, UNSUPPORTED, 1024)
        first = short_lived.pid
        short_lived.run(NOWHERE, UNSUPPORTED, 1024)
        short_lived.run(NOWHERE, UNSUPPORTED, 1024)
        third = short_lived.pid

        assert first is not None
        assert third is not None
        assert third != first
    finally:
        short_lived.stop()


def test_a_job_over_the_deadline_is_a_timeout_and_costs_the_child() -> None:
    # The deadline covers the start of the child as well, so it has to stay above
    # the cost of a spawn. Three seconds is far below the 120 s of production and
    # far above the roughly one second an interpreter start costs here.
    impatient = sandbox.ExtractionWorker(max_files=200, timeout_seconds=3)
    try:
        before = impatient.probe("sleep", 0.0)
        doomed_pid = impatient.pid
        outcome = impatient.probe("sleep", 30.0)

        assert before.state is State.INDEXED
        assert outcome == ExtractionOutcome.failed(Reason.TIMEOUT)
        assert impatient.pid is None, "the killed child must not be counted as usable"

        impatient.probe("sleep", 0.0)

        assert impatient.pid is not None
        assert impatient.pid != doomed_pid
    finally:
        impatient.stop()


@ONLY_POSIX
def test_a_job_over_the_address_space_cap_is_out_of_memory(worker: sandbox.ExtractionWorker) -> None:
    worker.probe("sleep", 0.0)
    doomed_pid = worker.pid
    outcome = worker.probe("allocate", 4 * 1024 * 1024 * 1024)

    assert outcome == ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)
    # The address space of that child is spent, so it is replaced rather than
    # asked to try again in the same arena.
    assert worker.pid is None

    worker.probe("sleep", 0.0)

    assert worker.pid != doomed_pid


def test_an_unexpected_child_death_is_a_verdict_and_not_a_hang(worker: sandbox.ExtractionWorker) -> None:
    worker.probe("sleep", 0.0)
    doomed_pid = worker.pid
    outcome = worker.probe("die", 0.0)

    assert outcome == ExtractionOutcome.failed(Reason.CORRUPT)

    worker.probe("sleep", 0.0)

    assert worker.pid is not None
    assert worker.pid != doomed_pid


def test_child_does_not_import_findling_index(worker: sandbox.ExtractionWorker) -> None:
    worker.run(NOWHERE, UNSUPPORTED, 1024)

    loaded = worker.loaded_modules()

    assert loaded, "the child has to report something, otherwise this test proves nothing"
    assert any(name.startswith("findling.extract") for name in loaded)
    assert [name for name in loaded if name.startswith("findling.index")] == []


def test_the_address_space_cap_is_the_configured_one(worker: sandbox.ExtractionWorker) -> None:
    assert worker.address_space_bytes == config.settings().extract_address_space_bytes
