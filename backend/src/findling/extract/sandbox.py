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
replaced on schedule instead. IDX-08 is untouched: exactly one extraction runs at
a time, it simply lives in another address space, and that address space is used
more than once.

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

import multiprocessing as mp
import os
import sys
import time
from multiprocessing.context import SpawnProcess
from typing import Any, Final

from findling import config
from findling.extract.errors import ExtractionOutcome, Reason

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
    """Drive the guard into one of its four failure situations, on request.

    This exists because the guard cannot be tested with a document. A file that
    hangs for two minutes or allocates half a gigabyte is not in the reference
    corpus, and writing one would test the file rather than the guard. The four
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
    elif kind == "die":
        # No unwinding, no answer on the pipe: the parent sees the boundary break.
        os._exit(70)
    else:
        raise ValueError(f"unknown probe kind {kind!r}")
    return ExtractionOutcome.indexed(kind)


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


def _child_main(pipe: PipeEnd, address_space_bytes: int) -> None:
    """The child: shed credentials and cap the address space first, then answer jobs.

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
    _shed_secrets()
    _limit_address_space(address_space_bytes)

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
        else:
            try:
                answer = _run_probe(job[1], job[2]) if kind == _JOB_PROBE else _extraction_of(job)
            except MemoryError:
                # Reported rather than raised: the parent has to tell an exhausted
                # address space apart from a hang, and it can only do that if the
                # child still manages to say which one it was.
                answer = ExtractionOutcome.failed(Reason.OUT_OF_MEMORY)
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
        if not isinstance(outcome, ExtractionOutcome):
            outcome = ExtractionOutcome.failed(Reason.CORRUPT)
        return self._recycle_if_needed(outcome)

    def loaded_modules(self) -> tuple[str, ...]:
        """Every module of this package the child holds, for the import hygiene test."""
        answer = self._ask((_JOB_MODULES,))
        return answer if isinstance(answer, tuple) else ()

    def stop(self) -> None:
        """End the child politely, then make sure it is gone either way."""
        if self._process is not None and self._pipe is not None and self._process.is_alive():
            try:
                self._pipe.send((_JOB_STOP,))
                self._process.join(_JOIN_GRACE_SECONDS)
            except (BrokenPipeError, OSError):
                pass
        self._recycle()

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
            self._recycle()
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
            self._recycle()
            return ExtractionOutcome.failed(Reason.CORRUPT)

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

    The facade the indexing worker calls. One worker per process, because IDX-08
    allows exactly one extraction at a time and a second worker would quietly
    double both the memory peak and the number of children to supervise. That
    stays true with the OCR track: a second facade for OCR would double the
    memory peak of the container for a branch that runs one file at a time
    anyway (T-03-904).

    ``route`` and ``timeout_seconds`` are what an OCR job brings along and a text
    job leaves alone. Both are passed through rather than resolved here, because
    which kind of job this is is known by the poller and by nobody else.
    """
    global _WORKER
    if _WORKER is None:
        _WORKER = ExtractionWorker()
    return _WORKER.run(path, mime, size, route=route, timeout_seconds=timeout_seconds)
