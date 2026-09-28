"""One long lived extraction child, bounded by the kernel and by a deadline.

**What was measured and taken over.** A hanging call inside a C extension such as
pypdfium2 or lxml cannot be interrupted from Python: the interpreter never gets
the chance to look at a flag. The alarm of the signal module only fires on the
main thread of the main process, so it is useless for a worker. A pool executor
of the futures module cannot cancel a running task either, because waiting on a
future with a deadline gives up on behalf of the waiter and leaves the work
running. Neither name appears in this file, and a grep gate keeps it that way.
What does work, measured, is a process of its own: ``RLIMIT_AS`` produces a clean
``MemoryError`` inside the child, and ``kill()`` on a hung process produces exit
code -9. The start method is spawn rather than the Linux default fork, because
the parent holds an event loop and open sockets, and forking such a process is a
documented way to deadlock.

**Where this deviates from the phase research, and why.** The research sketch
starts one interpreter per file. That was an assumption, never measured on the
target hardware (assumption A11), and it is the expensive half of the design: an
interpreter start plus imports on a Raspberry class ARM board is realistically
half a second to two seconds. At 100.000 files that is 14 to 55 hours of pure
process start time, which is the difference between an initial index that takes
hours and one that takes days. So the child stays alive across jobs and is
replaced on schedule instead. Each worker runs exactly one extraction at a time,
in another address space that is used more than once. Since phase 26 that is a
statement about one worker and no longer about the container: Economy and the
tools keep the single worker of :func:`extract_guarded`, while the slot pool of
plan 26-04 holds N of them, each with its own child.

**A child killed from outside is not a verdict.** Under N slots the OOM killer
takes whichever child is largest, and that child is rarely the one with the
troublesome file. Every child therefore volunteers as the victim
(``oom_score_adj`` 1000) and runs below the main process (nice 10), and a death
by SIGKILL that this module did not send itself reaches the caller as
:class:`~findling.extract.errors.ChildKilled` instead of failed(corrupt). The
deadline kill and :meth:`ExtractionWorker.halt` are this module's own and keep
their verdicts.

**The four recycling rules** appear as comments at the code that implements them.
The one that is easy to overlook is the count: with a shared address space,
``RLIMIT_AS`` now bounds the sum of the leaks over many files instead of the peak
of a single one, which makes ``extract_worker_max_files`` a safety parameter and
not a performance knob.

**Import hygiene.** The child imports the dispatcher inside the child function and
nothing from the analysis half of the package, whose automaton costs roughly
23 MB and a third of a second to build (plan 02-01). Paying that on every recycle
would turn a start cost optimisation into a start cost doubling. A test asks a
running child which modules it holds, because that invariant is one convenient
import away from being false.
"""

from __future__ import annotations

import contextlib
import multiprocessing as mp
import os
import sys
import time
from multiprocessing.context import SpawnProcess
from pathlib import Path
from typing import Any, Final

from findling import config
from findling.extract.errors import KILLED_EXIT_CODE, ChildKilled, EngineKilled, ExtractionOutcome, Reason

if sys.platform == "win32":  # the two platforms name the same thing differently
    from multiprocessing.connection import PipeConnection as PipeEnd
else:
    from multiprocessing.connection import Connection as PipeEnd

# Not fork: the parent runs an event loop and open sockets.
SPAWN_CONTEXT: Final = mp.get_context("spawn")

# The job protocol on the pipe. Small on purpose: everything that crosses the
# boundary has to be picklable, and a rich object graph between two address
# spaces is a source of surprises nobody needs at this depth of the stack.
_JOB_EXTRACT: Final = "extract"
_JOB_MODULES: Final = "modules"
_JOB_PROBE: Final = "probe"
_JOB_STOP: Final = "stop"
_JOB_PRIORITY: Final = "priority"

# The answer of a child whose engine was killed from outside. A tuple and not an
# ExtractionOutcome, because it is no verdict: the parent turns it into
# ChildKilled(engine=True) and the file is run again (D-26-16).
_ANSWER_KILLED: Final = "engine_killed"

# The nice level every extraction child runs at, in every profile (D-26-11).
#
# Only the children and never the main process: the main process answers the
# Unified Search and the status page, and those have to stay quick while N
# children read scans next to them. Economy with its single slot is no
# exception, because a lone OCR child on a small box is exactly the load that
# makes the search wait (issue #19). tesseract is started by the child and
# inherits the level, so the engine is covered without a word in ocr.py.
SANDBOX_NICE: Final = 10

# How long a kill is given to take effect before the parent stops waiting. The
# kernel does not negotiate, so this is a formality; it exists so that a wedged
# join can never become the hang that the whole module is here to prevent.
_JOIN_GRACE_SECONDS: Final = 5.0


def _limit_address_space(cap: int) -> None:
    """Hand the address space cap to the kernel, which is the only enforcer that counts.

    An application level check would have to run inside the allocation it is
    trying to prevent. RLIMIT_AS is POSIX, and the container this ships in is
    Linux; on Windows, where the tests also run, there is no equivalent that could
    be set from here, so the limit is absent and the deadline plus the process
    boundary carry the guard alone.
    """
    if sys.platform == "win32":
        return
    import resource

    resource.setrlimit(resource.RLIMIT_AS, (cap, cap))


def _kill_child_tree(process: SpawnProcess) -> None:
    """Kill the child together with everything it may have spawned.

    The child made itself a session leader, so its process group id is its own
    pid and the group kill reaches a hung grandchild too. Before the child got
    that far, or on Windows where neither sessions nor group kills exist, the
    plain kill of the single process is the whole answer.
    """
    if sys.platform != "win32" and process.pid is not None:
        import signal

        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except (ProcessLookupError, PermissionError, OSError):
            pass
    process.kill()


def _run_probe(kind: str, amount: float) -> ExtractionOutcome:
    """Drive the guard into one of its failure situations, on request.

    This exists because the guard cannot be tested with a document. A file that
    hangs for two minutes or allocates half a gigabyte is not in the reference
    corpus, and writing one would test the file rather than the guard. The
    kinds are reached only through an explicit probe job, never from the
    extraction path, and they never touch user data.
    """
    if kind == "sleep":
        time.sleep(amount)
    elif kind == "grandchild":
        # The shape the OCR branch has since phase 3: this child starts a process
        # of its own and answers while it is still running. Its pid travels back
        # so that a test can watch the group kill reach it (security audit L3).
        # A python that sleeps rather than tesseract, because the guard is the
        # subject here and an engine would only make the test need one.
        import subprocess

        started = subprocess.Popen(  # noqa: S603 - an argument list, never a shell
            [sys.executable, "-c", f"import time; time.sleep({float(amount)})"],
        )
        return ExtractionOutcome.indexed(str(started.pid))
    elif kind == "allocate":
        # Freed immediately on success. Under RLIMIT_AS this raises MemoryError,
        # which the loop below turns into failed(out_of_memory).
        blob = bytearray(int(amount))
        del blob
    elif kind == "interrupt":
        # The shape OpenBLAS gives an exhausted address space: pthread_create
        # fails, the library raises SIGINT, Python turns it into
        # KeyboardInterrupt (DI-06.1-37). Raised directly rather than through a
        # real thread storm, because the storm needs a machine shape most
        # runners do not have; the many core trap in test_sandbox.py builds the
        # real one where the machine allows it.
        raise KeyboardInterrupt
    elif kind == "die":
        # No unwinding, no answer on the pipe: the parent sees the boundary break.
        os._exit(70)
    elif kind == "engine_killed":
        # What read_page raises when the OOM killer took tesseract. Raised
        # directly, because a real engine killed on cue would test the kernel.
        raise EngineKilled
    else:
        raise ValueError(f"unknown probe kind {kind!r}")
    return ExtractionOutcome.indexed(kind)


def _lower_own_standing(
    oom_score_adj_path: Path = Path("/proc/self/oom_score_adj"),
    autogroup_path: Path = Path("/proc/self/autogroup"),
) -> None:
    """Make this child the first thing the OOM killer takes, and the last thing the scheduler serves.

    The kernel picks its OOM victim by badness, and badness follows resident
    memory. The main process holds the model, the tokenizer and the index
    readers and is roughly five times the size of a child, so without this line
    a tight container loses the process that owns every slot rather than one
    child that can simply be started again (D-26-16). Raising the own score
    needs no privilege; only lowering it does.

    The autogroup is the second half of the nice level. After ``setsid`` the
    child forms an autogroup of its own, and where no CPU cgroup controller
    sorts the tasks, nice only ranks threads inside that group; the group
    itself gets the same nice here. Inside a container with a CPU controller
    the kernel ignores the value, which costs nothing.

    Both writes are best effort, each on its own: a read only /proc or a rate
    limited autogroup changes nothing about how the child extracts, it only
    means the kernel keeps its default opinion.
    """
    with contextlib.suppress(OSError):
        oom_score_adj_path.write_text("1000", encoding="ascii")
    with contextlib.suppress(OSError):
        autogroup_path.write_text(str(SANDBOX_NICE), encoding="ascii")


def _own_standing() -> tuple[int, int]:
    """The nice level and the OOM score adjustment of this process, as the child sees them.

    ``os.nice(0)`` reads the level without changing it. An unreadable score
    comes back as -1, which no child of this module ever sets, so a test cannot
    mistake a missing file for a hardened child. Windows has neither, and says
    so with the same two neutral values.
    """
    if sys.platform == "win32":
        return (0, -1)
    try:
        score = int(Path("/proc/self/oom_score_adj").read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        score = -1
    return (os.nice(0), score)


def _is_engine_killed(answer: object) -> bool:
    """Whether the child answered with the sentinel for a killed engine rather than a verdict."""
    return isinstance(answer, tuple) and answer == (_ANSWER_KILLED,)


def _shed_secrets() -> None:
    """Drop everything from the environment a compromised child could spend.

    This child is the one place of the container where attacker controlled
    bytes meet C libraries, and it never talks to Nextcloud, so it has no
    business holding the AppAPI credentials the spawn inherited (security audit
    M6). With APP_SECRET in hand, code running in here could sign content
    gateway requests for any user id and read every file of the instance; with
    the variables gone, an RCE in a parser is confined to what the child can
    already see.
    """
    for name in ("APP_SECRET", "HP_SHARED_KEY", "NEXTCLOUD_URL", "AA_VERSION"):
        os.environ.pop(name, None)


# The native thread pools of the numeric libraries, pinned to one thread each.
#
# This is not a performance setting, it is the fix for a bug that made every
# DOCX, XLSX and PPTX on a twelve core host report "File damaged" (plan 06.1-19,
# found by the owner sight check). The chain, measured rather than reasoned:
# findling/extract/office.py imports openpyxl at module level,
# openpyxl.compat.numbers imports numpy unconditionally, numpy loads OpenBLAS,
# and OpenBLAS starts one worker thread per CPU. Every one of those threads wants
# a stack inside the address space that _limit_address_space just capped at
# 512 MB, so on a machine with enough cores pthread_create fails, the numpy
# import dies half way, and dispatch maps the unknown exception to
# failed(corrupt). The container said
# "OpenBLAS blas_thread_init: pthread_create failed for thread 10 of 12" and
# "ensure that your address space and process count limits are big enough",
# which is OpenBLAS naming its own remedy.
#
# Why it stayed hidden for five phases: the thread count follows the CPU count.
# On the two vCPU measurement box and on a four vCPU runner the threads fit under
# the cap, so every test and every measurement passed while the same code failed
# on an ordinary developer machine and would fail on any self hosted server with
# enough cores. The first thing a fresh Nextcloud showed was its own
# "Welcome to Nextcloud Hub.docx" marked as damaged.
#
# One thread and not two: this child extracts one document at a time, in a
# container that runs a single index worker on purpose, and there is no matrix
# multiplication in reading a spreadsheet. numpy is in this process because
# openpyxl imports it, not because anything on this path computes with it.
#
# All four names rather than only the one that fired. They are the same class of
# library reading the same class of variable, and pinning only OpenBLAS would
# leave the identical failure waiting behind whichever backend a future wheel
# ships with.
_NATIVE_THREAD_POOL_VARIABLES = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def _pin_native_thread_pools() -> None:
    """Pin every native thread pool to one thread, before any of them is loaded.

    Order is the whole point: these variables are read while the library
    initialises, so setting them after the import would change nothing at all.
    """
    for name in _NATIVE_THREAD_POOL_VARIABLES:
        os.environ[name] = "1"


def _child_main(pipe: PipeEnd, address_space_bytes: int) -> None:
    """The child: shed credentials, cap the address space, pin the pools, then answer jobs.

    The dispatcher is imported here rather than at module level so that the cap is
    already in place while the extraction libraries are being loaded, and so that
    the parent, which imports this module too, never pays for them.
    """
    if sys.platform != "win32":
        # Its own session, so a kill can take the whole process group with it.
        # Today the child spawns nothing; phase 3 runs tesseract, and a hung
        # grandchild that survives the kill would hold the worker slot forever
        # (security audit L3).
        os.setsid()
        # Straight after the new session and before anything else is loaded:
        # the level is inherited by every process this child starts, tesseract
        # included, and the OOM score has to be in place before the parsers
        # below can allocate the memory that would make the kernel look for a
        # victim (D-26-11, D-26-16). The main process never lowers itself.
        os.nice(SANDBOX_NICE)
        _lower_own_standing()
    _shed_secrets()
    _limit_address_space(address_space_bytes)
    # Before the import below and not after it: the cap is in place now, and the
    # numeric libraries the dispatcher pulls in read these variables while they
    # initialise. The paragraph above the function says what happens without it.
    _pin_native_thread_pools()

    from findling.extract.dispatch import Route, extract

    def _extraction_of(job: tuple[Any, ...]) -> ExtractionOutcome:
        """Run one extraction job, forced route included.

        The route crosses the pipe as a plain string and becomes a ``Route``
        here, which is the whole reason this function sits inside the child: the
        parent must not import the dispatcher, and a ``Route`` in the job tuple
        would make it do exactly that while unpickling.
        """
        wanted = job[4]
        return extract(job[1], job[2], job[3], Route(wanted) if wanted is not None else None)

    while True:
        try:
            job = pipe.recv()
        except EOFError:
            return
        kind = job[0]
        if kind == _JOB_STOP:
            return
        if kind == _JOB_MODULES:
            answer: object = tuple(sorted(name for name in sys.modules if name.startswith("findling")))
        elif kind == _JOB_PRIORITY:
            answer = _own_standing()
        else:
            try:
                answer = _run_probe(job[1], job[2]) if kind == _JOB_PROBE else _extraction_of(job)
            except MemoryError:
                # Reported rather than raised: the parent has to tell an exhausted
                # address space apart from a hang, and it can only do that if the
                # child still manages to say which one it was.
                answer = ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)
            except KeyboardInterrupt:
                # DI-06.1-37: in this non interactive child a SIGINT has one
                # known source, native code failing pthread_create inside the
                # capped address space (OpenBLAS raises it and names its own
                # remedy in the message). The honest verdict is the spent
                # address space, not a corrupt file. An operator's Ctrl+C in a
                # dev terminal reaches the parent too, which ends the worker
                # anyway, so nothing is swallowed that mattered.
                answer = ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)
            except EngineKilled:
                # Before the blanket handler below, which would read it as a
                # corrupt file. The child itself is fine; only its engine was
                # killed, and that is no verdict on the file (D-26-16).
                answer = (_ANSWER_KILLED,)
            except Exception as error:
                answer = ExtractionOutcome.from_exception(error)
        try:
            pipe.send(answer)
        except (BrokenPipeError, OSError):
            return


class ExtractionWorker:
    """Holds exactly one extraction child and the rules for replacing it."""

    def __init__(self, *, max_files: int | None = None, timeout_seconds: float | None = None) -> None:
        resolved = config.settings()
        self._max_files = resolved.extract_worker_max_files if max_files is None else max_files
        self._timeout_seconds = (
            float(resolved.extract_timeout_seconds) if timeout_seconds is None else float(timeout_seconds)
        )
        self.address_space_bytes = resolved.extract_address_space_bytes
        self._process: SpawnProcess | None = None
        self._pipe: PipeEnd | None = None
        self._files_handled = 0
        # Set by halt() before its kill, so that the death it causes is read as
        # this module's own and not as the OOM killer's (D-26-16).
        self._halted = False

    @property
    def pid(self) -> int | None:
        """The process id of the current child, or None while there is none."""
        return None if self._process is None else self._process.pid

    @property
    def files_handled(self) -> int:
        """How many files the CURRENT child has served.

        Per child, never per worker: the count is what bounds the sum of the
        leaks inside one shared address space, so it has to start at zero every
        time a child is replaced.
        """
        return self._files_handled

    def run(
        self,
        path: str,
        mime: str,
        size: int,
        *,
        route: str | None = None,
        timeout_seconds: float | None = None,
    ) -> ExtractionOutcome:
        """Extract one file behind the boundary and return its verdict.

        ``route`` is a plain string and not a ``Route``, so that this side of the
        boundary keeps its promise never to import the dispatcher. It is the one
        thing an OCR order brings along that a text job does not: the second
        track belongs to the kind of the job, not to the mimetype of the file.
        """
        outcome = self._ask((_JOB_EXTRACT, path, mime, size, route), timeout_seconds)
        if _is_engine_killed(outcome):
            # The child answered, so it handled the file and stays; only its
            # engine is gone. Counted like any handled file, because the count
            # bounds the leaks of this address space whatever the verdict was.
            self._files_handled += 1
            if self._files_handled >= self._max_files:
                self._recycle()
            raise ChildKilled(engine=True)
        if not isinstance(outcome, ExtractionOutcome):
            outcome = ExtractionOutcome.failed(Reason.CORRUPT)
        if self._process is not None:
            # Only a child that is still there can have handled a file. _ask
            # replaces the child on a deadline and on an unexpected death, and
            # that replacement sets the count back to zero; raising the count
            # afterwards wrote a used file onto a process that had not seen one.
            # The consequence was paid on every timeout: the next child counted
            # as already used and was recycled one file early, so a hung
            # document cost an extra spawn on top of the deadline.
            self._files_handled += 1
        return self._recycle_if_needed(outcome)

    def probe(self, kind: str, amount: float, *, timeout_seconds: float | None = None) -> ExtractionOutcome:
        """Run a diagnostic job. See :func:`_run_probe` for why this is here."""
        outcome = self._ask((_JOB_PROBE, kind, amount), timeout_seconds)
        if _is_engine_killed(outcome):
            raise ChildKilled(engine=True)
        if not isinstance(outcome, ExtractionOutcome):
            outcome = ExtractionOutcome.failed(Reason.CORRUPT)
        return self._recycle_if_needed(outcome)

    def loaded_modules(self) -> tuple[str, ...]:
        """Every module of this package the child holds, for the import hygiene test."""
        answer = self._ask((_JOB_MODULES,))
        return answer if isinstance(answer, tuple) else ()

    def priority(self) -> tuple[int, int]:
        """The nice level and the OOM score adjustment the child runs with, for the hardening test.

        Asked of the running child rather than read from the parent, because
        the child lowers itself and the parent is exactly the process that must
        not. Anything that is not a pair of integers is the neutral (0, -1).
        """
        answer = self._ask((_JOB_PRIORITY,))
        if isinstance(answer, tuple) and len(answer) == 2:
            nice, score = answer
            if isinstance(nice, int) and isinstance(score, int):
                return (nice, score)
        return (0, -1)

    def stop(self) -> None:
        """End the child politely, then make sure it is gone either way."""
        if self._process is not None and self._pipe is not None and self._process.is_alive():
            try:
                self._pipe.send((_JOB_STOP,))
                self._process.join(_JOIN_GRACE_SECONDS)
            except (BrokenPipeError, OSError):
                pass
        self._recycle()

    def halt(self) -> None:
        """Kill the running child from another thread, as this module's own kill.

        For the one caller that has to end a slot while a job is still in it:
        the pool when the container shuts down, and the pool's barrier when a
        sibling was killed. The waiting :meth:`_ask` sees the pipe break and
        answers failed(corrupt) as it always did for a death it caused itself,
        never ChildKilled, because the flag is set before the kill is sent.
        The next job starts a fresh child and clears the flag again.

        The child is read once into a local. The waiting thread may recycle and
        close it in the same moment, and a closed process object answers every
        question with ValueError, which here only means there is nothing left
        to kill.
        """
        self._halted = True
        process = self._process
        if process is None:
            return
        try:
            if process.is_alive():
                _kill_child_tree(process)
        except ValueError:
            pass

    def _ask(self, job: tuple[object, ...], timeout_seconds: float | None = None) -> object:
        """Send one job, wait for the answer with a deadline, judge what comes back.

        The deadline is an argument of the job and not a property of the worker,
        because there are two of them. A text job gets EXTRACT_TIMEOUT_SECONDS,
        an OCR job the far longer budget of docs/ocr.md, and the caller that
        knows which kind of job this is is the only one that can tell them apart.
        Anything that passes nothing keeps the configured default.
        """
        deadline = self._timeout_seconds if timeout_seconds is None else float(timeout_seconds)
        self._start_child()
        process, pipe = self._process, self._pipe
        if process is None or pipe is None:  # pragma: no cover - _start_child sets both
            return ExtractionOutcome.failed(Reason.CORRUPT)

        try:
            pipe.send(job)
        except (BrokenPipeError, OSError):
            # Recycling rule 4: an unexpected child death leaves an unknown state.
            self._bury(process)
            return ExtractionOutcome.failed(Reason.CORRUPT)

        if not pipe.poll(deadline):
            # Recycling rule 2: over the deadline. Only a kill ends a hung C
            # extension, and after it the process is gone by definition.
            #
            # Which deadline this is matters. An OCR job carries the hard one of
            # docs/ocr.md, and it has to sit strictly above the soft deadline the
            # child checks in its page loop: without that distance the parent
            # kills the child in the very moment it wants to hand over the pages
            # it already read, and indexed(truncated) from D-08 would never occur
            # in practice (T-03-902). The margin is derived in the configuration,
            # so raising the soft budget moves the hard one along with it.
            _kill_child_tree(process)
            process.join(_JOIN_GRACE_SECONDS)
            self._recycle()
            return ExtractionOutcome.failed(Reason.TIMEOUT)

        try:
            return pipe.recv()
        except (EOFError, OSError):
            # Recycling rule 4 again, from the other side: the child died between
            # accepting the job and answering it.
            self._bury(process)
            return ExtractionOutcome.failed(Reason.CORRUPT)

    def _bury(self, process: SpawnProcess) -> None:
        """Replace a child that died on its own, and raise ChildKilled if something else killed it.

        The exit code is read after a join and before the recycle, because the
        recycle closes the process object and takes the code with it. SIGKILL is
        the one death this module can tell apart from a file that beat the
        parser: nothing in the child sends it to itself, the deadline path has
        returned before this point, and a halt sets its flag first. What is
        left is the kernel, and the kernel picks by size, not by guilt
        (D-26-16). Every other end, the exit code 70 of the die probe or a
        segfault, stays failed(corrupt) as before.
        """
        process.join(_JOIN_GRACE_SECONDS)
        killed = process.exitcode == KILLED_EXIT_CODE and not self._halted
        self._recycle()
        if killed:
            raise ChildKilled(engine=False)

    def _recycle_if_needed(self, outcome: ExtractionOutcome) -> ExtractionOutcome:
        if outcome.reason is Reason.OUT_OF_MEMORY:
            # Recycling rule 3: the address space of that child is spent, and the
            # next file would inherit whatever is left of it.
            self._recycle()
        elif self._files_handled >= self._max_files:
            # Recycling rule 1: leak prevention. Because one address space now
            # serves many files, RLIMIT_AS bounds the sum of the leaks rather than
            # a single outlier, which makes this count part of the guard.
            self._recycle()
        return outcome

    def _start_child(self) -> None:
        if self._process is not None and self._process.is_alive():
            return
        self._recycle()
        parent_end, child_end = SPAWN_CONTEXT.Pipe(duplex=True)
        process = SPAWN_CONTEXT.Process(
            target=_child_main,
            args=(child_end, self.address_space_bytes),
            daemon=True,
        )
        process.start()
        # The parent keeps no handle on the child's end. Left open here, the pipe
        # would never report an end of file, and a dead child would look like a
        # slow one until the deadline expired.
        child_end.close()
        self._process = process
        self._pipe = parent_end
        self._files_handled = 0
        self._halted = False

    def _recycle(self) -> None:
        """Leave no child and no pipe behind, whatever state either of them is in."""
        if self._process is not None:
            if self._process.is_alive():
                _kill_child_tree(self._process)
            self._process.join(_JOIN_GRACE_SECONDS)
            self._process.close()
            self._process = None
        if self._pipe is not None:
            self._pipe.close()
            self._pipe = None
        self._files_handled = 0


_WORKER: ExtractionWorker | None = None


def extract_guarded(
    path: str,
    mime: str,
    size: int,
    *,
    route: str | None = None,
    timeout_seconds: float | None = None,
) -> ExtractionOutcome:
    """Extract one file without ever letting it take the container with it.

    The facade for Economy and for the tools: one worker, one extraction at a
    time, as IDX-08 had it for the whole container before phase 26. The OCR
    slots of the other profiles are the pool of plan 26-04, which holds N
    workers and talks to them directly, because it has to see ChildKilled.

    This facade does not. It keeps its promise to answer with a verdict only,
    so a :class:`~findling.extract.errors.ChildKilled` becomes the verdict the
    same death produced before phase 26: failed(ocr_failed) when only the
    engine was killed, failed(corrupt) when the child went. With a single child
    there is no neighbour a solo run could leave out, so nothing is lost by it.

    ``route`` and ``timeout_seconds`` are what an OCR job brings along and a text
    job leaves alone. Both are passed through rather than resolved here, because
    which kind of job this is is known by the poller and by nobody else.
    """
    global _WORKER
    if _WORKER is None:
        _WORKER = ExtractionWorker()
    try:
        return _WORKER.run(path, mime, size, route=route, timeout_seconds=timeout_seconds)
    except ChildKilled as killed:
        return ExtractionOutcome.failed(Reason.OCR_FAILED if killed.engine else Reason.CORRUPT)
