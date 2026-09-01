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

The fifth, added with the OCR track of plan 03-09, is that there are now two
deadlines rather than one. A text job may take 120 seconds and an OCR job up to
660, and the group of tests below asserts both directions: a long budget is not
cut short by the built in default, and a short one still ends a hanging job. The
grandchild test is the one that could not be written before phase 3, because
before it the child spawned nothing at all.
"""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling import config
from findling.extract import sandbox
from findling.extract.errors import ExtractionOutcome, Reason, State

SANDBOX_SOURCE = Path(__file__).resolve().parents[1] / "src" / "findling" / "extract" / "sandbox.py"

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


def test_a_job_may_carry_a_deadline_of_its_own_above_the_default() -> None:
    # The whole point of plan 03-09: an OCR job runs up to 660 s where a text job
    # runs 120. Bound to the worker, the long value would apply to every text
    # file as well, and the short one would kill the OCR child before it could
    # hand over its partial text.
    impatient = sandbox.ExtractionWorker(max_files=200, timeout_seconds=1)
    try:
        outcome = impatient.probe("sleep", 3.0, timeout_seconds=60)

        assert outcome.state is State.INDEXED, "the deadline of the job has to win over the default"
        assert impatient.pid is not None, "nothing was killed, so the child stays"
    finally:
        impatient.stop()


def test_a_short_deadline_on_the_job_still_ends_a_hanging_call() -> None:
    # The other direction, and the one that keeps the guard a guard: a per job
    # value is not an escape hatch, it is the value that is enforced.
    patient = sandbox.ExtractionWorker(max_files=200, timeout_seconds=600)
    try:
        patient.probe("sleep", 0.0)
        doomed_pid = patient.pid
        outcome = patient.probe("sleep", 30.0, timeout_seconds=3)

        assert outcome == ExtractionOutcome.failed(Reason.TIMEOUT)
        # Recycling rule 2 is untouched by the new argument: over the deadline
        # means the child is gone, whichever deadline it was.
        assert patient.pid is None

        patient.probe("sleep", 0.0)

        assert patient.pid is not None
        assert patient.pid != doomed_pid
    finally:
        patient.stop()


def test_a_job_without_a_deadline_uses_the_configured_default() -> None:
    # Every caller that existed before plan 03-09 passes nothing, and nothing has
    # to keep meaning EXTRACT_TIMEOUT_SECONDS.
    impatient = sandbox.ExtractionWorker(max_files=200, timeout_seconds=3)
    try:
        outcome = impatient.probe("sleep", 30.0)

        assert outcome == ExtractionOutcome.failed(Reason.TIMEOUT)
    finally:
        impatient.stop()


def test_the_recycling_count_still_holds_after_a_job_with_its_own_deadline() -> None:
    # Recycling rule 1 counts files, not deadlines. A job that brought its own
    # budget must not fall out of that count, because the count is what bounds
    # the sum of the leaks in a shared address space.
    short_lived = sandbox.ExtractionWorker(max_files=2, timeout_seconds=60)
    try:
        short_lived.run(NOWHERE, UNSUPPORTED, 1024, timeout_seconds=30)
        first = short_lived.pid
        short_lived.run(NOWHERE, UNSUPPORTED, 1024, timeout_seconds=30)
        short_lived.run(NOWHERE, UNSUPPORTED, 1024, timeout_seconds=30)
        third = short_lived.pid

        assert first is not None
        assert third is not None
        assert third != first
    finally:
        short_lived.stop()


def _process_state(pid: int) -> str:
    """The letter the kernel gives one process, or the empty string when it is gone.

    Read from /proc rather than probed with signal 0, and that is the whole
    reliability of the test below. An orphaned grandchild is reparented to
    whatever runs as pid 1 in the container, and a pid 1 that does not reap
    leaves a zombie behind; ``os.kill(pid, 0)`` calls a zombie alive, which is
    exactly the answer this test must not accept.
    """
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError:
        return ""
    return stat.rpartition(")")[2].split()[0]


@ONLY_POSIX
def test_group_kill_reaches_a_grandchild() -> None:
    # The reason setsid and killpg were built in phase 2 (security audit L3),
    # asserted for the first time with a real grandchild. tesseract runs exactly
    # here, and a hung grandchild that survives the kill of its parent would hold
    # the single worker slot of the container forever (T-03-901).
    impatient = sandbox.ExtractionWorker(max_files=200, timeout_seconds=3)
    try:
        answer = impatient.probe("grandchild", 300.0)
        grandchild = int(answer.text)
        assert _process_state(grandchild) not in {"", "Z"}, "the grandchild has to be running first"

        outcome = impatient.probe("sleep", 300.0)

        assert outcome == ExtractionOutcome.failed(Reason.TIMEOUT)
        # The kill is asynchronous, so this waits rather than asserts at once.
        # It waits for a state, not for a duration: a sleep long enough to be
        # safe would be long enough to make the suite unpleasant.
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and _process_state(grandchild) not in {"", "Z"}:
            time.sleep(0.05)

        assert _process_state(grandchild) in {"", "Z"}, "the group kill has to take the grandchild with it"
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


def test_a_forced_route_survives_the_boundary(worker: sandbox.ExtractionWorker, tmp_path: Path) -> None:
    # The OCR track of plan 03-09 is the only caller that forces a route, and it
    # forces it across two address spaces. The route is written as a plain string
    # here for the same reason the parent sends one: this side of the boundary
    # must not import the dispatcher.
    #
    # A text file announced as a PDF is the cheapest way to see which route
    # actually ran, and it needs no engine: the PDF route cannot parse it, the
    # forced text route reads it without trouble. A run that lost the route on
    # the way would answer with the first verdict twice.
    page = tmp_path / "announced-as-a-pdf.txt"
    page.write_text("Bebauungsplan der Gemeinde", encoding="utf-8")
    size = page.stat().st_size

    derived = worker.run(str(page), "application/pdf", size)
    forced = worker.run(str(page), "application/pdf", size, route="plain")

    assert derived.state is State.FAILED, "a text file read as a PDF cannot end well"
    assert forced.state is State.INDEXED, "the forced route did not reach the child"
    assert "Bebauungsplan" in (forced.text or "")


def test_child_does_not_import_findling_index(worker: sandbox.ExtractionWorker) -> None:
    worker.run(NOWHERE, UNSUPPORTED, 1024)

    loaded = worker.loaded_modules()

    assert loaded, "the child has to report something, otherwise this test proves nothing"
    assert any(name.startswith("findling.extract") for name in loaded)
    assert [name for name in loaded if name.startswith("findling.index")] == []


def test_the_address_space_cap_is_the_configured_one(worker: sandbox.ExtractionWorker) -> None:
    assert worker.address_space_bytes == config.settings().extract_address_space_bytes


def test_shedding_removes_every_appapi_credential(monkeypatch: pytest.MonkeyPatch) -> None:
    # The child is the one place where attacker controlled bytes meet C
    # libraries, and it never talks to Nextcloud; with APP_SECRET in hand an
    # RCE in a parser could sign gateway requests for any user (audit M6).
    for name in ("APP_SECRET", "HP_SHARED_KEY", "NEXTCLOUD_URL", "AA_VERSION"):
        monkeypatch.setenv(name, "held-by-the-parent")

    sandbox._shed_secrets()

    for name in ("APP_SECRET", "HP_SHARED_KEY", "NEXTCLOUD_URL", "AA_VERSION"):
        assert name not in os.environ


def test_the_child_hardens_itself_before_the_parsers_load() -> None:
    # Order is the property: shedding after the dispatcher import would hand
    # the credentials to every module the import pulls in first.
    body = SANDBOX_SOURCE.read_text(encoding="utf-8").split("def _child_main", 1)[1]

    assert body.index("_shed_secrets()") < body.index("from findling.extract.dispatch import ")
    assert body.index("os.setsid()") < body.index("_shed_secrets()")


def test_every_kill_goes_through_the_group_kill() -> None:
    # Today the child spawns nothing; phase 3 runs tesseract, and a plain
    # kill() would orphan a hung grandchild that keeps the worker slot (audit
    # L3). The single bare kill() is the fallback inside _kill_child_tree.
    code = [
        line for line in SANDBOX_SOURCE.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")
    ]

    assert sum("process.kill()" in line for line in code) == 1
    assert sum("_kill_child_tree(" in line for line in code) == 3, "the definition and both kill sites"
