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
import subprocess
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

# The one mimetype that carries the trap of DI-06.1-31, because office.py is the
# module that imports openpyxl and openpyxl is what pulls numpy and OpenBLAS in.
OFFICE_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

# The two numbers of the many core trap case, derived at the bottom of its
# docstring: an address space cap that one pinned thread fits under and a thread
# stack wide enough that a single unpinned neighbour does not.
TRAP_ADDRESS_SPACE_BYTES = 192 * 1024 * 1024
TRAP_THREAD_STACK_BYTES = 64 * 1024 * 1024

# The child of the counterfactual: the three steps of _child_main that decide the
# trap, in the order it does them, with the pin as the one switched line. It
# calls the real functions of the real module, so it cannot drift away from the
# mechanism it is about, and it deliberately does not import anything else of
# _child_main: the pipe protocol has nothing to do with this question.
_BARE_CHILD = """
from findling.extract import sandbox
sandbox._limit_address_space({cap})
{pin}
try:
    from findling.extract.dispatch import extract
    print(extract({document!r}, {mime!r}, {size}, None).state)
except BaseException as error:
    print(type(error).__name__)
"""


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


def test_a_timeout_leaves_no_file_counted_against_the_next_child() -> None:
    # Recycling rule 2 kills the child and resets the count with it, and the
    # count was raised again right afterwards for a job that no child had
    # survived. The replacement then started life as if it had already worked,
    # so it was recycled one file too early and every timeout cost an extra
    # spawn. A deadline below the cost of starting a child is the cheapest way
    # into that branch.
    impatient = sandbox.ExtractionWorker(max_files=2, timeout_seconds=60)
    try:
        outcome = impatient.run(NOWHERE, UNSUPPORTED, 1024, timeout_seconds=0.01)

        assert outcome == ExtractionOutcome.failed(Reason.TIMEOUT)
        assert impatient.pid is None, "the deadline has to take the child with it"
        assert impatient.files_handled == 0, "a file nobody handled must not be counted"
    finally:
        impatient.stop()


def test_a_handled_file_is_counted_against_the_child_that_handled_it() -> None:
    # The other direction of the same rule: the count is what bounds the sum of
    # the leaks in a shared address space, so a job that really ran has to
    # arrive in it.
    worker = sandbox.ExtractionWorker(max_files=200, timeout_seconds=60)
    try:
        worker.run(NOWHERE, UNSUPPORTED, 1024)

        assert worker.files_handled == 1
    finally:
        worker.stop()


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


def test_the_native_thread_pools_are_pinned_to_one_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    # The fix of the bug the owner sight check of plan 06.1-19 found: every DOCX,
    # XLSX and PPTX came back as failed(corrupt) on a twelve core host, because
    # openpyxl imports numpy, numpy loads OpenBLAS, and OpenBLAS starts one thread
    # per CPU inside an address space that RLIMIT_AS has just capped at 512 MB.
    # All four names, because they are one class of library reading one class of
    # variable and pinning only the one that fired leaves the rest waiting.
    for name in sandbox._NATIVE_THREAD_POOL_VARIABLES:
        monkeypatch.delenv(name, raising=False)

    sandbox._pin_native_thread_pools()

    for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        assert os.environ[name] == "1"


def test_the_thread_pools_are_pinned_before_the_parsers_load() -> None:
    # Order is the property, exactly as with the shedding above: these variables
    # are read while a native library initialises, so a pin after the dispatcher
    # import would change nothing and this test would be the only thing left
    # saying it works.
    body = SANDBOX_SOURCE.read_text(encoding="utf-8").split("def _child_main", 1)[1]

    assert body.index("_pin_native_thread_pools()") < body.index("from findling.extract.dispatch import ")
    assert body.index("_limit_address_space(") < body.index("_pin_native_thread_pools()")


def _an_office_document(tmp_path: Path) -> Path:
    """One small DOCX on disk. The content is irrelevant, the route is the point."""
    import docx

    document = docx.Document()
    document.add_paragraph("Aktenvermerk der Gemeinde zur Winterdienstpauschale.")
    path = tmp_path / "vermerk.docx"
    document.save(str(path))
    return path


def _usable_cpus() -> int:
    """How many CPUs this process may use, which is the thread count OpenBLAS takes.

    The allowance and not the count of the machine, asked the way
    findling.embed.bench asks it: OpenBLAS reads the affinity mask, so a
    container pinned to two of twelve cores starts two threads and not twelve.
    """
    affinity = getattr(os, "sched_getaffinity", None)
    return len(affinity(0)) if affinity is not None else os.cpu_count() or 1


def _thread_stack_limit() -> tuple[int, int]:
    """The soft and the hard limit on the thread stack, zeroes on Windows."""
    if sys.platform == "win32":
        return (0, 0)
    import resource

    return resource.getrlimit(resource.RLIMIT_STACK)


def _set_thread_stack_limit(soft: int, hard: int) -> None:
    """Set the thread stack limit, and do nothing at all on Windows."""
    if sys.platform == "win32":
        return
    import resource

    resource.setrlimit(resource.RLIMIT_STACK, (soft, hard))


def _widen_the_thread_stack() -> None:
    """Raise the soft limit on the thread stack, keeping the hard one as it is.

    Runs between fork and exec of the bare child, which is the only window in
    which a limit can be set that the new process reads while it starts. The
    hard limit is carried over unchanged because raising it is a privilege this
    process does not have and does not need.
    """
    _set_thread_stack_limit(TRAP_THREAD_STACK_BYTES, _thread_stack_limit()[1])


def _the_thread_stack_can_be_widened() -> bool:
    """Whether this machine allows the stack the trap case needs."""
    if sys.platform == "win32":
        return False
    import resource

    _soft, hard = _thread_stack_limit()
    return hard == resource.RLIM_INFINITY or hard >= TRAP_THREAD_STACK_BYTES


def _extract_in_a_bare_child(document: Path, *, pinned: bool) -> str:
    """Extract one document in a fresh interpreter, with or without the pin.

    A plain subprocess and not a worker of this module: the question is what the
    three steps of the child do to a document, and the parent side of the pipe
    would only add a way for the answer to be a timeout instead of a verdict.
    """
    code = _BARE_CHILD.format(
        cap=TRAP_ADDRESS_SPACE_BYTES,
        pin="sandbox._pin_native_thread_pools()" if pinned else "",
        document=str(document),
        mime=OFFICE_MIME,
        size=document.stat().st_size,
    )
    environment = dict(os.environ)
    # Whatever the machine running the suite carries in its environment, this
    # child starts from the state the container starts from: nothing set, so
    # OpenBLAS asks the kernel how many CPUs it may use. Without this an
    # OPENBLAS_NUM_THREADS in the shell of a developer would silently turn the
    # unpinned run into a pinned one and the whole case green for the wrong
    # reason.
    for name in sandbox._NATIVE_THREAD_POOL_VARIABLES:
        environment.pop(name, None)

    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=environment,
        timeout=300,
        check=False,
        preexec_fn=_widen_the_thread_stack,
    )
    lines = answer.stdout.strip().splitlines()
    # The last line, because a native library may write to stdout before python
    # gets to say anything. A child that never spoke at all is reported by its
    # exit code, which is a verdict of its own and never mistaken for indexed.
    return lines[-1] if lines else f"exit {answer.returncode}"


def test_an_office_document_survives_the_guarded_path(tmp_path: Path) -> None:
    """A DOCX through the real child, which is where the corrupt verdict came from.

    The limit of this test, stated rather than left to be discovered: it is only a
    ratchet on a machine with enough cores. OpenBLAS starts one thread per CPU, so
    on the two vCPU measurement box and on a four vCPU runner the threads fit
    under the cap and this assertion holds even without the pin above. That is
    precisely why the bug survived five phases of tests and measurements, and it
    is why the two tests above assert the mechanism instead of the outcome. This
    one is here because it is the assertion the sight check actually saw fail.

    The test below it is the one that removes that limit and makes the trap
    reachable on any runner (DI-06.1-31).
    """
    document = _an_office_document(tmp_path)

    outcome = sandbox.extract_guarded(str(document), OFFICE_MIME, document.stat().st_size)

    assert outcome.state is State.INDEXED, f"reason {outcome.reason}"
    assert outcome.text_chars > 0


@ONLY_POSIX
def test_an_office_document_survives_the_many_core_trap_no_runner_could_reach(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The trap of the sight check, made reachable on a runner with two CPUs.

    **The gap this closes.** The Office bug of plan 06.1-19 fell through five
    phases because no job in this repository could reach it. It needs
    ``pthread_create`` to fail inside the capped address space of the extraction
    child, the thread count follows the CPU count, and a runner has two to four
    CPUs while the owner's machine has twelve. The test above therefore holds on
    every runner with or without the fix, which is worth exactly nothing as a
    ratchet. The reference corpus could not help either: it is mostly PDF, and
    the PDF route never imports openpyxl and therefore never loads numpy.

    **Why the thread count cannot simply be raised.** Measured before this case
    was written, in the release image on a container pinned to two CPUs:
    OpenBLAS clamps ``OPENBLAS_NUM_THREADS`` to the CPUs it may actually use, so
    asking for 12, 24 or 128 threads on a two CPU box yields two threads and a
    green run every time. The environment variable cannot manufacture the trap.
    The only lever left is the one the address space is made of, which is why
    this case lowers ``RLIMIT_AS`` and widens the thread stack instead.

    **The two numbers, and both are measurements.** With a 64 MiB thread stack a
    single extra thread already costs 64 MiB of address space, so two CPUs are
    enough to break a cap that one thread fits under, and every larger machine
    breaks it further. In the release image the pinned child was measured green
    from 160 MiB upwards and the unpinned child red from 240 MiB downwards, so
    192 MiB sits between the two with roughly 32 MiB of room below and 48 above.
    Verified at 2, 4 and 12 usable CPUs; the shape of the failure differs with
    the core count, from the OpenBLAS message and a SIGINT at two CPUs to a
    child that dies without a word at twelve, which is why the assertion below
    asks for "not indexed" and never for one particular exception.

    **The three runs, and each of them answers a different question.** The
    guarded path has to survive the trap, which is the ratchet on the production
    code: remove the pin from ``_child_main`` or make it ineffective and this
    goes red on any runner. The bare child with the pin has to survive it too,
    which proves the harness of the third run is sound rather than merely
    hostile. The bare child without the pin has to fail, and that is the state
    of this repository before commit debb395: the same three steps in the same
    order, minus the one line that fixed it. So the case carries its own
    falsification and does not need a dispatch switch to be trusted.
    """
    if _usable_cpus() < 2:
        pytest.skip("the trap needs two usable CPUs, with one OpenBLAS starts one thread and there is nothing to trap")
    if not _the_thread_stack_can_be_widened():
        pytest.skip("the hard limit on the thread stack is below the size this case needs")

    document = _an_office_document(tmp_path)

    # The cap travels through the documented setting rather than a test hook, so
    # what runs here is the ordinary worker of the container with an ordinary
    # configuration. The cache is cleared on both sides of the run for the reason
    # the volume fixture of conftest clears it: it is resolved once per process.
    monkeypatch.setenv("FINDLING_EXTRACT_ADDRESS_SPACE_BYTES", str(TRAP_ADDRESS_SPACE_BYTES))
    config.settings.cache_clear()
    soft, hard = _thread_stack_limit()
    # Before the child is started and never after: glibc reads this limit once,
    # while a process starts, and takes the default thread stack size from it.
    # Raised in the parent because that is the only place a spawned child can
    # inherit it from, and put back in the finally, because a wide stack left
    # behind would follow every later test of the session.
    _set_thread_stack_limit(TRAP_THREAD_STACK_BYTES, hard)
    worker = sandbox.ExtractionWorker(max_files=200, timeout_seconds=120)
    try:
        assert worker.address_space_bytes == TRAP_ADDRESS_SPACE_BYTES, "the lowered cap has to reach the worker"
        outcome = worker.run(str(document), OFFICE_MIME, document.stat().st_size)
    finally:
        worker.stop()
        _set_thread_stack_limit(soft, hard)
        config.settings.cache_clear()

    assert outcome.state is State.INDEXED, f"the pin has to hold under the trap, reason {outcome.reason}"
    assert outcome.text_chars > 0

    pinned = _extract_in_a_bare_child(document, pinned=True)
    unpinned = _extract_in_a_bare_child(document, pinned=False)

    assert pinned == str(State.INDEXED), f"the harness itself has to be survivable, it answered {pinned}"
    assert unpinned != str(State.INDEXED), (
        "the state before debb395 has to fail under this trap, otherwise this case proves nothing"
    )


def test_every_kill_goes_through_the_group_kill() -> None:
    # Today the child spawns nothing; phase 3 runs tesseract, and a plain
    # kill() would orphan a hung grandchild that keeps the worker slot (audit
    # L3). The single bare kill() is the fallback inside _kill_child_tree.
    code = [
        line for line in SANDBOX_SOURCE.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")
    ]

    assert sum("process.kill()" in line for line in code) == 1
    assert sum("_kill_child_tree(" in line for line in code) == 3, "the definition and both kill sites"
