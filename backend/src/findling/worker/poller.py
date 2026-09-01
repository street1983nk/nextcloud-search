"""The one indexing task: take work, read it, extract it, write it, report it.

The whole file exists for the sake of one ordering, so it is stated before any
code. One pass over a batch does, in this order:

1. take the batch and, per file, judge it, read the bytes, extract the text and
   hand the document to the writer;
2. **commit** the writer, which is the moment the index becomes durable;
3. write the verdicts and the permissions into the state database;
4. acknowledge the batch to the queue.

What an abort costs at each point, and why the order is not negotiable:

* Before 2 nothing has happened. The rows stay locked in Nextcloud and run in
  again after the lock timeout.
* Between 2 and 3 the documents are in the index while the state database still
  counts them as unjudged. The redelivery repeats the work, and the upsert of the
  writer replaces the document instead of duplicating it. One document, not two,
  and a test stages exactly this abort.
* Between 3 and 4 the rows come back once more, the fast path sees the same
  content hash next to state ``indexed`` and acknowledges without doing anything.

The reverse order loses documents silently: acknowledged rows are gone from the
queue, and an abort before the commit means nobody ever writes them. Nothing
raises, no counter moves, and the missing documents are only noticed by the user
who cannot find a file. That is the failure this project was started over.

**Crash safety is not built here, it follows from the architecture.** The backlog
lives in Nextcloud as queue rows, and tantivy opens on the last commit after a
``kill -9`` (measured in plan 02-06). What has to be built here is idempotence,
discipline and thrift on the hot path.

**Thrift means one client per run.** A hundred thousand files are a hundred
thousand byte fetches, and a client of its own would be a connection setup each
plus, on the PHP side, a Nextcloud bootstrap including the AppAPI signature
check. ``tools/read_corpus.py`` already carries a single client through a whole
loop and this is the same shape, in the place where it decides the runtime of the
initial index.

**Discipline means the event loop stays free.** tantivy releases the GIL in
``add_document``, ``commit`` and ``search``, but the calls still belong in
``asyncio.to_thread``, and so does the SQLite transaction: a long commit on the
event loop is a ``/heartbeat`` that hangs while ``/enabled`` still answers, which
is the warning sign from the phase research. The ruff group ASYNC is armed here
for the first time and catches most of the rest.

**And the log carries counters and reason codes, nothing else.** No path, no file
name, no excerpt, no search term (T-02-107). A test greps for it, because this is
a rule that is broken while adding a helpful detail rather than on purpose.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, Final, cast

from tantivy import Index

from findling.config import settings
from findling.extract.dispatch import Route, extension_of, judge
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.sandbox import extract_guarded
from findling.index.open import expected_versions, open_index
from findling.index.wordlist import build_artifact
from findling.index.writer import FLUSH_PAUSED_LOW_DISK, IndexBatchWriter, IndexRecord
from findling.nc import client as nc_client
from findling.nc.client import (
    AsyncNextcloudApp,
    FileTooLargeError,
    GatewayClient,
    fetch_file_stream,
    new_gateway_client,
)
from findling.nc.queue import KIND_ACL, KIND_DELETE, KIND_METADATA, KIND_OCR, DocumentQueue, QueueJob
from findling.store.repo import ACL_ANY_USER, FileMeta, Store, open_store

LOGGER = logging.getLogger("findling.worker.poller")

# What one pass came to. Strings rather than an enum because they travel to the
# status page, where a closed list of readable names is worth more than a type.
ROUND_WORKED: Final = "worked"
ROUND_EMPTY: Final = "empty"
ROUND_QUEUE_UNAVAILABLE: Final = "queue_unavailable"
ROUND_GATEWAY_UNAVAILABLE: Final = "gateway_unavailable"
ROUND_PAUSED_LOW_DISK: Final = "paused_low_disk"

# Suffix of the scratch files under tmp_dir. Named so that the cleanup on start
# can recognise its own leftovers and touches nothing else in the volume.
SCRATCH_SUFFIX: Final = ".part"

# How long the shutdown waits for a pass to end before it stops waiting.
POLLER_STOP_SECONDS: Final = 30.0

# Everything the poller talks to, as a type. The defaults are the production
# wiring and a test replaces them one by one.
FetchFile = Callable[..., Awaitable[int | None]]
# Open in its arguments since plan 03-09, because an OCR job passes two more of
# them: the route it forces and the deadline it is allowed to take. Writing the
# three positional ones out and leaving the keywords implicit would look precise
# and be wrong, since the keyword names are the part a replacement has to match.
ExtractFile = Callable[..., ExtractionOutcome]
GatewayFactory = Callable[[], GatewayClient]
QueueFactory = Callable[[AsyncNextcloudApp], DocumentQueue]

# The factory behind this alias is reached through the module (nc_client.…)
# instead of being imported by name, so that the name of the factory occurs
# exactly once in this file. That is not tidiness: one client for a whole run is
# the difference between an initial index and a weekend, and a grep over this
# file is what makes a second creation visible in review rather than in a support
# case.
ClientFactory = Callable[[], AsyncNextcloudApp]


class _GatewayDown(RuntimeError):
    """The content gateway did not answer, so the batch cannot be finished.

    Its own type because the answer differs from every other failure: a file that
    could not be read says nothing about the file, so no verdict may be written
    for it. The rows go back unacknowledged and the pass ends.
    """


@dataclass(frozen=True, slots=True)
class RoundResult:
    """What one pass did, in a form the status page can render."""

    state: str
    claimed: int = 0
    indexed: int = 0
    skipped: int = 0
    failed: int = 0
    unchanged: int = 0
    acknowledged: int = 0
    # Rows this pass moved to the OCR track instead of finishing them. Counted
    # separately from skipped because they are the opposite of an end state: the
    # text track is done with them and the second track has not started.
    requeued: int = 0


@dataclass(frozen=True, slots=True)
class _Read:
    """One file on the local volume, with the hash taken on the way in."""

    path: Path
    size: int
    content_hash: str


@dataclass(frozen=True, slots=True)
class _Verdict:
    """A finished judgement, waiting for the commit to make it writable."""

    job: QueueJob
    outcome: ExtractionOutcome
    content_hash: str | None = None
    # Whether an OCR run stands behind this verdict. Carried per verdict rather
    # than derived from the job kind, because the rename path re-records a
    # verdict it did not produce and would otherwise drop the flag of the run
    # that did.
    ocr_used: bool = False


class _HashingSink:
    """A sink that hashes the bytes it passes on.

    The content hash decides whether a redelivered file has to be read again, so
    it has to exist for every file. Taking it in a second pass over the scratch
    file would double the disk reads of the whole initial index for a number that
    is free while the bytes are already going by.
    """

    def __init__(self, target: IO[bytes]) -> None:
        self._target = target
        self._digest = hashlib.sha256()
        self.written = 0

    def write(self, data: bytes) -> int:
        self._digest.update(data)
        self.written += len(data)
        return self._target.write(data)

    @property
    def content_hash(self) -> str:
        return self._digest.hexdigest()


def _open_state() -> Store:
    """The state database of the running container, seeded with version marks.

    The seed only fills keys that are missing, so an existing database keeps the
    marks its index was actually built with. Without the seed a state database
    created by this process carries unknown/0 marks forever: every answer says
    degraded, /status reports reindexRequired, and the drift alarm this
    mechanism exists for becomes permanent noise nobody reads (bug audit H1).
    """
    return open_store(settings().state_db, meta=expected_versions(build_artifact().digest))


def _open_writer(store: Store) -> IndexBatchWriter:
    """The single index writer of the running container."""
    resolved = settings()
    artifact = build_artifact()
    index = open_index(resolved.index_dir, artifact.entries)
    _raise_generation_for_lost_index(index, store)
    return IndexBatchWriter(index, directory=resolved.index_dir)


def _raise_generation_for_lost_index(index: Index, store: Store) -> None:
    """Force a reindex when the index is gone but the state database is not.

    An empty index directory next to a state database full of ``indexed``
    verdicts means the tantivy directory was lost, restored from an older
    backup, or wiped by hand. Without this check the state stays authoritative:
    a crawl requeues every file, ``is_unchanged`` skips every one of them, and
    the search is empty for good with every counter claiming success (bug audit
    H5). Raising the generation makes every stored verdict stale at once, so
    the next crawl actually rebuilds the index.

    The container cannot start that crawl itself; the queue lives in Nextcloud
    and is filled by ``occ findling:index --restart``. What this check
    guarantees is that the restart rebuilds instead of skipping.
    """
    if index.searcher().num_docs > 0:
        return
    if store.counts()["indexed"] == 0:
        return
    generation = store.index_version + 1
    store.write_meta("index_version", str(generation))
    LOGGER.warning(
        "the index is empty while the state database holds indexed verdicts; "
        "raised the generation to %d so the next crawl reindexes everything",
        generation,
    )


class Poller:
    """The single asyncio task that keeps the index in step with the queue.

    ``run_once`` and ``run`` are separate on purpose. One pass is testable
    without time, without a task and without a queue that keeps answering, and the
    acceptance criterion of this phase hangs off exactly that sequence.

    Everything the poller talks to arrives through the constructor, which is what
    makes the pass testable against a real index and a real state database while
    Nextcloud is a fake. The defaults are the production wiring.
    """

    def __init__(
        self,
        *,
        store: Store | None = None,
        writer: IndexBatchWriter | None = None,
        tmp_dir: Path | None = None,
        client_factory: ClientFactory = nc_client.create_app_client,
        gateway_factory: GatewayFactory = new_gateway_client,
        queue_factory: QueueFactory = DocumentQueue,
        fetch: FetchFile = fetch_file_stream,
        extract: ExtractFile = extract_guarded,
        batch_files: int | None = None,
        batch_max_bytes: int | None = None,
        cooldown_start: float | None = None,
        cooldown_max: float | None = None,
    ) -> None:
        resolved = settings()
        self._store = store
        self._writer = writer
        self._owns_resources = store is None and writer is None
        self._tmp_dir = resolved.tmp_dir if tmp_dir is None else tmp_dir
        self._client_factory = client_factory
        self._gateway_factory = gateway_factory
        self._queue_factory = queue_factory
        self._fetch = fetch
        self._extract = extract
        self._ocr_enabled = resolved.ocr_enabled
        # The hard deadline of an OCR job, derived in the configuration so that it
        # is always above the soft one the child checks in its page loop. See the
        # cap cascade in docs/ocr.md.
        self._ocr_hard_deadline = float(resolved.ocr_hard_deadline_seconds)
        self._batch_files = resolved.batch_files if batch_files is None else batch_files
        self._batch_max_bytes = resolved.batch_max_bytes if batch_max_bytes is None else batch_max_bytes
        self._cooldown_start = float(resolved.poll_cooldown_start_seconds if cooldown_start is None else cooldown_start)
        self._cooldown_max = float(resolved.poll_cooldown_max_seconds if cooldown_max is None else cooldown_max)

        self._client: AsyncNextcloudApp | None = None
        self._gateway: GatewayClient | None = None
        self._queue: DocumentQueue | None = None
        self._held: set[int] = set()
        self._cooldown = 0.0
        self._armed = asyncio.Event()

    # -- lifecycle -------------------------------------------------------

    @property
    def armed(self) -> bool:
        """True while the backend is enabled and the task may collect work."""
        return self._armed.is_set()

    @property
    def cooldown(self) -> float:
        """Seconds the loop waits before the next pass."""
        return self._cooldown

    def arm(self) -> None:
        """Let the task collect work again."""
        self._armed.set()

    def silence(self) -> None:
        """Stop collecting work without ending the task.

        A disabled backend that keeps polling is the classic of the integration
        list, and it is invisible from the outside: the container looks healthy
        while it drains the queue of an app the admin switched off.
        """
        self._armed.clear()

    async def unlock_held(self) -> int:
        """Hand back the rows this pass is holding, so a restart is productive.

        Only a hard kill pays the lock timeout, which is the price of losing
        nothing after one.
        """
        queue, held = self._queue, sorted(self._held)
        if queue is None or not held:
            return 0
        result = await queue.unlock(held)
        self._held.clear()
        return result.count

    async def aclose(self) -> None:
        """Give back the connection pool and, if it opened them, its resources."""
        gateway, self._gateway = self._gateway, None
        if gateway is not None:
            await gateway.aclose()
        if not self._owns_resources:
            return
        writer, self._writer = self._writer, None
        if writer is not None:
            writer.close()
        store, self._store = self._store, None
        if store is not None:
            store.close()

    # -- the loop --------------------------------------------------------

    async def run(self, stop_event: asyncio.Event) -> None:
        """Pass after pass until the stop event, silent while not armed.

        An exception inside a pass is logged and does not end the task. The search
        is the part a user sees, and a broken indexer must not take it along.
        """
        while not stop_event.is_set():
            if not self._armed.is_set():
                await _first_of(self._armed.wait(), stop_event.wait())
                continue
            try:
                await self.run_once()
            # Deliberately every exception. The search is the part a user sees,
            # and a broken indexer must not take it along.
            except Exception as error:
                # The type name and nothing else. A traceback here would carry
                # whatever a library put into its message, and the extraction
                # path is full of libraries that put a file name there.
                LOGGER.error("indexing pass ended in an unexpected %s", type(error).__name__)
                self._back_off()
            await _pause(self._cooldown, stop_event)

    async def run_once(self) -> RoundResult:
        """One pass over one batch, in the order the module docstring states."""
        queue = self._open()

        claim = await queue.claim(limit=self._batch_files, max_bytes=self._batch_max_bytes)
        if claim.unavailable:
            self._back_off()
            return RoundResult(ROUND_QUEUE_UNAVAILABLE)
        if not claim.jobs:
            self._back_off()
            return RoundResult(ROUND_EMPTY)

        self._held = {job.queue_id for job in claim.jobs}
        done: list[int] = []
        failed: dict[int, str] = {}
        verdicts: list[_Verdict] = []
        # File ids, not queue ids: the requeue is about the file, and the row it
        # belongs to may not even exist for the caller that comes in plan 03-12.
        handover: list[int] = []
        unchanged = 0

        # 1. Per file: judge, read the bytes into scratch, extract, hand over to
        #    the writer. An abort anywhere in here costs nothing: the rows are
        #    still locked in Nextcloud and run in again after the lock timeout.
        for job in claim.jobs:
            try:
                counted = await self._handle(job, done, failed, verdicts, handover)
            except _GatewayDown:
                # The gateway says nothing about the file, so no verdict may be
                # written for any of them. Give the whole batch back and wait.
                return await self._abort(queue, len(claim.jobs))
            unchanged += counted

        # 2. The commit. From here the index is durable, and this is the earliest
        #    moment at which a verdict may be written down.
        flush = await asyncio.to_thread(self._writer_or_die().flush)
        if flush.state == FLUSH_PAUSED_LOW_DISK:
            # A worker that keeps going on a full volume turns a space problem
            # into a data loss.
            LOGGER.warning("index paused, free space below the floor, %d rows handed back", len(claim.jobs))
            return await self._abort(queue, len(claim.jobs), state=ROUND_PAUSED_LOW_DISK)

        # 3. The verdicts and the permissions, per file replace_acl then record().
        #    An abort in between leaves the file unjudged, so the redelivery
        #    repeats the work instead of acknowledging a half written state.
        await asyncio.to_thread(self._record_verdicts, verdicts)

        # 3b. The handover to the OCR track, after the commit and before the
        #     acknowledgement. An abort right here costs one repeated text layer
        #     check and nothing else: the rows were not acknowledged, so they come
        #     back after the lock timeout and are handed over again. The reverse
        #     order would delete the row in the same pass in which the requeue put
        #     work on it, and the scan would never be read.
        requeued = await self._hand_over(queue, handover)

        # 4. The acknowledgement, the last step by construction. Everything it
        #    reports is already durable, so losing it costs one repetition and
        #    never a document.
        ack = await queue.acknowledge(done, failed)
        self._held.clear()
        self._reset_cooldown()

        indexed = sum(1 for verdict in verdicts if verdict.outcome.state is State.INDEXED)
        skipped = sum(1 for verdict in verdicts if verdict.outcome.state is State.SKIPPED)
        LOGGER.info(
            "pass finished, claimed=%d indexed=%d skipped=%d failed=%d unchanged=%d requeued=%d committed=%d",
            len(claim.jobs),
            indexed,
            skipped,
            len(failed),
            unchanged,
            requeued,
            flush.documents,
        )
        return RoundResult(
            ROUND_WORKED,
            claimed=len(claim.jobs),
            indexed=indexed,
            skipped=skipped,
            failed=len(failed),
            unchanged=unchanged,
            acknowledged=ack.count,
            requeued=requeued,
        )

    # -- one file --------------------------------------------------------

    async def _handle(
        self,
        job: QueueJob,
        done: list[int],
        failed: dict[int, str],
        verdicts: list[_Verdict],
        handover: list[int],
    ) -> int:
        """Take one job as far as the writer. Returns 1 when it needed no work."""
        # The kind=delete branch, and it stands before everything because a
        # deletion is the one job that must not touch the file. Every line below
        # would either ask the gateway for bytes that are gone or read the empty
        # mimetype of a delete row as skipped(mime_not_allowed), which is a
        # verdict about a file that is simply no longer there.
        if job.kind == KIND_DELETE:
            await self._forget(job, done)
            return 0

        # The kind=acl branch, and it stands here for the same reason: a
        # permission change touches the file as little as a deletion does. It
        # costs one write and no download, and that is exactly why the claim
        # hands it out before any content job (D-04): its effect has to be
        # visible while an OCR backlog is still being worked off.
        if job.kind == KIND_ACL:
            await self._replace_access(job, done)
            return 0

        # A rename or a move, and the cheapest job the system has: the text is
        # already in the index, so nothing is fetched, nothing is extracted and
        # no sandbox child is started.
        #
        # It needs a branch of its own because the ordinary content route would
        # do nothing at all. The bytes of a renamed file are the bytes of the
        # same file, so is_unchanged below acknowledges the row without a single
        # write, and neither the name in the index nor the path in the state
        # database would ever be corrected (phase research, pitfall 2).
        #
        # A False answer means the index holds no text for this file, because it
        # was never indexed or ended as skipped. That is not an error and not a
        # reason to requeue either, since the row is already here: it falls
        # through to the content route below, which is exactly what a first
        # indexing of this file would have done.
        if job.kind == KIND_METADATA and await self._rewrite_metadata(job, done, failed, verdicts):
            return 0

        # The second track, and it stands before the judgement below because the
        # route of such a job is not a property of its mimetype. The row got here
        # through the requeue of step 3b, which only ever puts a file on it that
        # the text pass judged as skipped(no_text_layer); nothing else can reach
        # this branch, which is what keeps D-06 intact (T-03-906).
        if job.kind == KIND_OCR:
            await self._read_the_scan(job, done, failed, verdicts)
            return 0

        route = judge(job.mime, job.size)
        if isinstance(route, ExtractionOutcome):
            # Decided before the first byte. Reading fifty megabytes to learn what
            # the mimetype already said is the most expensive possible way of
            # finding out that a film has no text in it.
            self._collect(job, route, done, failed, verdicts)
            return 0

        try:
            read = await self._fetch_file(job)
        except FileTooLargeError:
            # The size the crawl checked was the file of that moment; whoever
            # replaced it under the same id afterwards does not get to fill the
            # scratch volume (security audit M5). A verdict, not an error: the
            # row leaves the queue with a reason a status page can show.
            self._collect(job, ExtractionOutcome.skipped(Reason.TOO_LARGE), done, failed, verdicts)
            return 0
        if read is None:
            # 404 is what the gateway answers for "does not exist" and for "not
            # yours" alike, deliberately indistinguishable. Either way the row has
            # to leave the queue rather than circle until the give-up rule ends it.
            self._collect(job, ExtractionOutcome.skipped(Reason.GONE), done, failed, verdicts)
            return 0

        try:
            if await asyncio.to_thread(self._store_or_die().is_unchanged, job.file_id, read.content_hash):
                # The permissions are written even here, and that is bug audit
                # M1. The fast path acknowledges a file whose bytes did not
                # change without a single write, while the user list of the job
                # is the current one: a permission change that arrives as a
                # content job, which is what every crawl and every write of a
                # shared file produces, would otherwise never reach the
                # prefilter. It is one declarative write against a file the pass
                # has read anyway, so the exit stays cheap.
                await asyncio.to_thread(self._store_or_die().replace_acl, job.file_id, _acl_users(job))
                done.append(job.queue_id)
                return 1
            outcome = await asyncio.to_thread(self._extract, str(read.path), job.mime, read.size)
        finally:
            # The scratch file holds user content. Leaving one behind is a
            # disclosure, and leaving one behind per job fills the volume.
            _discard(read.path)

        if outcome.state is State.INDEXED:
            await asyncio.to_thread(self._writer_or_die().add, _record_of(job, outcome))
        hand_over = await self._goes_to_the_ocr_track(job, outcome, read.content_hash)
        if hand_over:
            handover.append(job.file_id)
        self._collect(job, outcome, done, failed, verdicts, read.content_hash, hand_over=hand_over)
        return 0

    async def _read_the_scan(
        self,
        job: QueueJob,
        done: list[int],
        failed: dict[int, str],
        verdicts: list[_Verdict],
    ) -> None:
        """The same file once more, this time as pixels rather than as text.

        It runs like the content branch above, and the three places where it does
        not are the reason it is a branch at all. Each of them carries its own
        comment below: the route is forced instead of derived, the deadline is
        the long one, and the fast path is skipped.

        **The fast path is skipped, and that is not an oversight.** A file that
        was just recognised as a scan has exactly the content hash it had during
        the text attempt, and its stored verdict is skipped(no_text_layer). Ask
        ``is_unchanged`` and the answer is False today, because that verdict is
        not ``indexed``, but the question is the wrong one either way, and the
        day an OCR run is repeated after a successful one the fast path would
        acknowledge the row without ever starting the engine. The bytes did not
        change; what changed is what is to be done with them.
        """
        try:
            read = await self._fetch_file(job)
        except FileTooLargeError:
            self._collect(job, ExtractionOutcome.skipped(Reason.TOO_LARGE), done, failed, verdicts)
            return
        if read is None:
            self._collect(job, ExtractionOutcome.skipped(Reason.GONE), done, failed, verdicts)
            return

        try:
            outcome = await asyncio.to_thread(
                self._extract,
                str(read.path),
                job.mime,
                read.size,
                # The route comes from the kind of the job, so that the second
                # track is not disguised as a mimetype the crawl could send.
                route=Route.OCR,
                # And the long deadline, not the 120 s of a text job. It sits
                # above the soft one of the page loop, and that distance is the
                # window in which the child hands over the pages it already read
                # (D-08, T-03-902).
                timeout_seconds=self._ocr_hard_deadline,
            )
        finally:
            # Same rule as on the content path: the scratch file holds user
            # content, and the error path is where a cleanup is forgotten.
            _discard(read.path)

        if outcome.state is State.INDEXED:
            await asyncio.to_thread(self._writer_or_die().add, _record_of(job, outcome))
        # No handover, whatever came back. This row was the handover, and putting
        # it on the track again is the endless loop of T-03-704 from the other
        # side. ocr_used travels with the verdict even when the engine found
        # nothing, because the time was spent either way.
        self._collect(job, outcome, done, failed, verdicts, read.content_hash, ocr_used=True)

    async def _goes_to_the_ocr_track(self, job: QueueJob, outcome: ExtractionOutcome, content_hash: str) -> bool:
        """True when this verdict becomes an OCR job instead of an end state.

        ``skipped(no_text_layer)`` is the handover point phase 2 prepared: the
        page carries pixels and no text, so the text track is done and the second
        track has to read it (D-07). Without this the scanned half of a typical
        administration is skipped for good, which is exactly what this phase was
        started over.

        **With OCR switched off nothing changes.** An instance whose admin set
        ``FINDLING_OCR_ENABLED=false`` gets the honest verdict rather than rows
        that wait forever for a track that does not exist there.

        **The same bytes are handed over once.** The requeued row comes back as
        an ocr job, and until the OCR route is wired it runs the content route
        again and produces the same verdict again. Handing it over once more
        every pass, with the attempt counter reset every time, is an endless loop
        (T-03-704), and the stored verdict of the earlier pass is what ends it.
        The content hash is part of the question, so a file that was replaced in
        the meantime is a different file and is handed over again.
        """
        if outcome.state is not State.SKIPPED or outcome.reason is not Reason.NO_TEXT_LAYER:
            return False
        if not self._ocr_enabled:
            return False

        row = await asyncio.to_thread(self._store_or_die().file_row, job.file_id)
        if row is None or row["content_hash"] != content_hash:
            return True
        return not (row["state"] == str(State.SKIPPED) and row["reason"] == str(Reason.NO_TEXT_LAYER))

    async def _hand_over(self, queue: DocumentQueue, file_ids: Sequence[int]) -> int:
        """Move the rows of this pass to the OCR track, and count what moved.

        A failure is a number and never an exception: the rows stay claimed, run
        into the lock timeout and are handed over by a later pass. The pass
        itself has to finish, because index and verdicts are already durable.
        """
        if not file_ids:
            return 0

        result = await queue.requeue(file_ids, kind=KIND_OCR)
        if not result.ok:
            LOGGER.warning("could not move %d files to the OCR track, they run into the lock timeout", len(file_ids))
            return 0
        return result.count

    async def _forget(self, job: QueueJob, done: list[int]) -> None:
        """Take one file out of the index, out of the prefilter and mark it gone.

        Three writes and no reading of the file. A delete job carries a file id
        and a storage id and nothing else, because the node it used to describe
        does not exist any more, and needing one of the missing fields is exactly
        how a deletion never reached this container before (pitfall 3).

        It deliberately does not go through :meth:`Store.record`. That call counts
        ``attempts`` up and overwrites the verdict, so three deletions of the same
        file would walk into the give-up rule, and the row would end as
        failed(repeatedly_stuck) for having been deleted successfully. The
        tombstone is the state here, and it leaves the old verdict readable so
        that phase 4 can still say what the file was before it went.

        The permissions are cleared inside step 1 of the pass rather than in step
        3, which is what makes the file stop being a candidate at once (D-10).
        Nothing is lost by that: the acknowledgement stays the last thing that
        happens, so an abort before the commit hands the row back and the whole
        deletion runs a second time, and all three writes are idempotent. The
        commit itself happens in the shared step 2, so the rule of this module
        holds for deletions as well: durable first, acknowledged second.
        """
        store = self._store_or_die()
        await asyncio.to_thread(self._writer_or_die().drop_document, job.file_id)
        await asyncio.to_thread(store.forget_acl, job.file_id)
        await asyncio.to_thread(store.tombstone, job.file_id)
        done.append(job.queue_id)

    async def _replace_access(self, job: QueueJob, done: list[int]) -> None:
        """Write the permissions of one file again, and touch nothing else.

        One call, no bytes over the network, no extraction and no index write.
        The job carries the target state, so this is ``replace_acl`` and never an
        addition or a removal: a delivery that gets lost costs one round of
        staleness and repairs itself with the next one, while an incremental
        variant would be wrong forever after the first lost message.

        **An empty user list is the payload, not an error.** After an unshare
        nobody may see the file any more, and ``replace_acl(file_id, [])`` is what
        removes the last rows. Treating the emptiness as a broken job is how the
        old permissions used to survive an unshare for good (pitfall 4).

        **How much this is worth, and how much it is not.** Nothing leaks while
        this job waits. A hit only becomes a snippet after the recheck in PHP, and
        that recheck resolves the file through ``getUserFolder()->
        getFirstNodeById()``, so a user who lost access sees nothing either way. A
        stale prefilter costs result quality and compute time, not
        confidentiality. It is written down here because the alternative readings
        are both bad: panic, which turns this into a security control it is not,
        and negligence, which lets the delay grow because nothing breaks.

        Like the deletion this deliberately does not go through
        :meth:`Store.record`. That call counts ``attempts`` up and overwrites the
        verdict, and a permission change judges nothing: three unshares of the
        same file would walk into the give-up rule and end as
        failed(repeatedly_stuck) although every one of them worked.
        """
        await asyncio.to_thread(self._store_or_die().replace_acl, job.file_id, _acl_users(job))
        done.append(job.queue_id)

    async def _rewrite_metadata(
        self,
        job: QueueJob,
        done: list[int],
        failed: dict[int, str],
        verdicts: list[_Verdict],
    ) -> bool:
        """Write the file again with new metadata and the text the index holds.

        False means the index has no text for this file, and it is the caller's
        signal to run the content route instead.

        Both reads block: the searcher opens a snapshot of the segments and the
        state row is a SQLite query, so both go through a worker thread like
        every other blocking call on this path.
        """
        body = await asyncio.to_thread(self._writer_or_die().stored_body, job.file_id)
        if body is None:
            return False

        # The verdict does not change, and neither does the content hash. The same
        # text is indexed, only under a different name, so carrying the hash over
        # is what keeps the fast path intact: writing None into it would send the
        # next content job into a full download and extraction of a file nobody
        # touched, and is_unchanged would answer False until the next reindex.
        row = await asyncio.to_thread(self._store_or_die().file_row, job.file_id)
        content_hash = str(row["content_hash"]) if row and row["content_hash"] else None
        truncated = bool(row and row["reason"] == str(Reason.TRUNCATED))
        # Carried over for the same reason as the content hash above: this path
        # writes a verdict it did not produce. The text in the index may well be
        # the text an OCR run read, and letting the rename reset the flag would
        # make the engine time disappear from the state on the day somebody moves
        # the file into another folder.
        ocr_used = bool(row and row["ocr_used"])

        outcome = ExtractionOutcome.indexed(body, truncated=truncated)
        # writer.add replaces through the term deletion, so this is an upsert on
        # the file id and not a second document under a second name.
        await asyncio.to_thread(self._writer_or_die().add, _record_of(job, outcome))
        self._collect(job, outcome, done, failed, verdicts, content_hash, ocr_used=ocr_used)
        return True

    async def _fetch_file(self, job: QueueJob) -> _Read | None:
        """Stream one file into scratch, hashing it on the way.

        Returns None when the gateway refuses the file, and raises
        :class:`_GatewayDown` for everything else: a permission verdict and an
        unreachable server must never be mistaken for one another.
        """
        scratch = self._tmp_dir / f"job-{job.queue_id}{SCRATCH_SUFFIX}"
        try:
            written, sink = await self._stream_into(scratch, job)
        except FileTooLargeError:
            # A verdict about this one file, never a gateway problem: the
            # caller records it as skipped(too_large) and the pass goes on.
            _discard(scratch)
            raise
        except Exception as error:
            _discard(scratch)
            LOGGER.warning("content gateway did not deliver, %s", type(error).__name__)
            raise _GatewayDown from error

        if written is None:
            _discard(scratch)
            return None
        return _Read(path=scratch, size=sink.written, content_hash=sink.content_hash)

    async def _stream_into(self, scratch: Path, job: QueueJob) -> tuple[int | None, _HashingSink]:
        """Open the scratch file off the loop, stream into it, close it again.

        Opening and closing go through a worker thread as well. On the target
        hardware the volume may be a slow SD card, and a blocking open in the
        event loop is the same stall as a blocking write, only harder to spot.
        """
        handle = await asyncio.to_thread(scratch.open, "wb")
        sink = _HashingSink(handle)
        try:
            written = await self._fetch(
                self._client,
                job.file_id,
                job.fetch_as,
                cast("IO[bytes]", sink),
                client=self._gateway,
            )
        finally:
            await asyncio.to_thread(handle.close)
        return written, sink

    @staticmethod
    def _collect(
        job: QueueJob,
        outcome: ExtractionOutcome,
        done: list[int],
        failed: dict[int, str],
        verdicts: list[_Verdict],
        content_hash: str | None = None,
        *,
        hand_over: bool = False,
        ocr_used: bool = False,
    ) -> None:
        """Sort one verdict into the two lists the acknowledgement carries.

        ``failed`` travels with its reason code, because the give-up rule and the
        error list of the status page live on the Nextcloud side, where an admin
        can still read them while the container is down. ``skipped`` is a decision
        this container made and needs no second home.

        ``hand_over`` is the one verdict that ends in neither list. Acknowledging
        is deleting, so a row that travels in ``done`` and in the requeue at once
        would be gone from the queue in the same pass in which it was put on the
        OCR track. The verdict is still recorded, because it is the truth about
        the text track and because the next pass reads it to see that this file
        has been handed over already.
        """
        verdicts.append(_Verdict(job=job, outcome=outcome, content_hash=content_hash, ocr_used=ocr_used))
        if outcome.state is State.FAILED and outcome.reason is not None:
            failed[job.queue_id] = str(outcome.reason)
            return
        if hand_over:
            return
        done.append(job.queue_id)

    def _record_verdicts(self, verdicts: Sequence[_Verdict]) -> None:
        """Write permissions and verdicts, permissions first.

        The store opens one transaction per call, so the two writes of a file are
        not atomic together. The order is what makes that harmless: while the
        verdict is missing the file counts as unjudged, the queue hands it back
        and the next pass writes both again. The reverse order would leave a file
        marked ``indexed`` whose permissions were never written, and the fast path
        would acknowledge it forever without ever repairing them.
        """
        store = self._store_or_die()
        for verdict in verdicts:
            job = verdict.job
            if verdict.outcome.state is State.INDEXED:
                # Declarative, never incremental: the queue entry carries the
                # target state, so a lost delivery costs one round of staleness
                # and repairs itself with the next one.
                store.replace_acl(job.file_id, _acl_users(job))
            store.record(
                job.file_id,
                _meta_of(job),
                str(verdict.outcome.state),
                str(verdict.outcome.reason) if verdict.outcome.reason is not None else None,
                content_hash=verdict.content_hash,
                text_chars=verdict.outcome.text_chars,
                ocr_used=verdict.ocr_used,
            )

    # -- plumbing --------------------------------------------------------

    def _open(self) -> DocumentQueue:
        """Build the client, the connection pool and the resources exactly once.

        One client for the whole run. A client per file would pay a connection
        setup per file and, on the PHP side, a Nextcloud bootstrap including the
        signature check; ``tools/read_corpus.py`` carries a single client through
        its whole loop for the same reason.
        """
        if self._queue is not None:
            return self._queue
        if self._store is None:
            self._store = _open_state()
        if self._writer is None:
            self._writer = _open_writer(self._store)
        self._tmp_dir.mkdir(parents=True, exist_ok=True)
        _clear_scratch(self._tmp_dir)
        self._client = self._client_factory()
        self._gateway = self._gateway_factory()
        self._queue = self._queue_factory(self._client)
        return self._queue

    async def _abort(
        self,
        queue: DocumentQueue,
        claimed: int,
        *,
        state: str = ROUND_GATEWAY_UNAVAILABLE,
    ) -> RoundResult:
        """End the pass without a commit, a verdict or an acknowledgement.

        Whatever the writer already holds stays pending and is written again by
        the redelivery; the upsert makes that harmless. Handing the rows back is
        the only thing worth doing here, because it turns the lock timeout into an
        immediate retry.
        """
        await queue.unlock(sorted(self._held))
        self._held.clear()
        self._back_off()
        return RoundResult(state, claimed=claimed)

    def _store_or_die(self) -> Store:
        if self._store is None:  # pragma: no cover - _open sets it
            raise RuntimeError("the poller has no state database")
        return self._store

    def _writer_or_die(self) -> IndexBatchWriter:
        if self._writer is None:  # pragma: no cover - _open sets it
            raise RuntimeError("the poller has no index writer")
        return self._writer

    def _back_off(self) -> None:
        """Grow the pause: from the configured start, doubling up to the cap."""
        self._cooldown = min(self._cooldown * 2, self._cooldown_max) if self._cooldown else self._cooldown_start

    def _reset_cooldown(self) -> None:
        """A batch that worked means there is probably another one waiting."""
        self._cooldown = 0.0


def default_poller() -> Poller:
    """The poller of the running container; its resources open on the first pass.

    Nothing is opened here. The lifespan builds this object while the backend may
    still be disabled, and a container that opened the index writer at that point
    would hold the tantivy lock without ever indexing anything.
    """
    return Poller()


def _acl_users(job: QueueJob) -> tuple[str, ...]:
    """The rows the prefilter gets for this job, capped list or real list.

    One function for all three write sites, and that is the whole point of it.
    Nextcloud caps a user list that would otherwise be the complete user list of
    the instance (perf audit M5) and marks the job when it did; writing the
    remaining names as if they were the truth would make the file disappear from
    the prefilter for everybody behind the cap. The collective row of
    :data:`findling.store.repo.ACL_ANY_USER` says "no usable list" instead, and
    the prefilter reads it as "candidate for anybody".

    A generosity, never a right: the only authority is the PHP recheck, and a
    candidate that the recheck rejects costs one resolution and shows nobody
    anything. The three call sites all go through here so that a fourth one
    cannot forget the mark and quietly write the short list.
    """
    if job.users_truncated:
        return (ACL_ANY_USER,)
    return job.user_ids


def _meta_of(job: QueueJob) -> FileMeta:
    """What the crawl knew about the file, as the state database takes it."""
    return FileMeta(
        storage_id=job.storage_id,
        root_id=job.root_id,
        path=job.path,
        title=job.title,
        mime=job.mime,
        size=job.size,
        mtime=job.mtime,
        # Nextcloud's own version mark, written down for the first time here. The
        # reconcile of plan 03-12 compares it against the current one, and without
        # a stored value it would have to fetch every file to find out that none
        # of them changed.
        etag=job.etag,
    )


def _record_of(job: QueueJob, outcome: ExtractionOutcome) -> IndexRecord:
    """The document as the index takes it."""
    return IndexRecord(
        file_id=job.file_id,
        storage_id=job.storage_id,
        name=job.title,
        title=job.title,
        path=job.path,
        ext=extension_of(job.title),
        body=outcome.text,
        mtime=job.mtime,
    )


def _discard(scratch: Path) -> None:
    """Remove one scratch file, whatever state it is in."""
    with contextlib.suppress(OSError):
        scratch.unlink(missing_ok=True)


def _clear_scratch(directory: Path) -> None:
    """Remove the scratch files an earlier crash left behind.

    Only the files this module names. A cleanup that swept the directory would
    one day sweep something else that lives in the volume.
    """
    removed = 0
    for entry in directory.glob(f"*{SCRATCH_SUFFIX}"):
        _discard(entry)
        removed += 1
    if removed:
        LOGGER.info("removed %d scratch files from an earlier run", removed)


async def _first_of(*waits: Awaitable[Any]) -> None:
    """Wait until the first of these finishes, then let the others go."""
    tasks = [asyncio.ensure_future(wait) for wait in waits]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


async def _pause(seconds: float, stop_event: asyncio.Event) -> None:
    """Wait out the cooldown, or return at once when the stop event arrives."""
    if seconds <= 0:
        # Still a suspension point: a pass that never yields would starve the
        # request handlers of the same loop.
        await asyncio.sleep(0)
        return
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)


__all__ = [
    "POLLER_STOP_SECONDS",
    "ROUND_EMPTY",
    "ROUND_GATEWAY_UNAVAILABLE",
    "ROUND_PAUSED_LOW_DISK",
    "ROUND_QUEUE_UNAVAILABLE",
    "ROUND_WORKED",
    "Poller",
    "RoundResult",
    "default_poller",
]
