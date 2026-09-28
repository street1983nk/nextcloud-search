"""The embedding track: the second trailing track, as an owner of its own.

Everything that turns the stored text of an indexed document into vectors lives
here, and so does everything that keeps the vector stock and its mark in step:
the cutter (tokenizer, splitter and engine), the embedding of one row, the
embedding mark, the drift chain and the bands of a redelivery. Until plan 25-07
all of it sat inside :class:`findling.worker.poller.Poller`; it moved out
without a change of behaviour, so that a second driver can run this track
beside the indexing track later on (PAR-01).

**Why the track has connections of its own.** A SQLite connection carries one
transaction at a time, and ``BEGIN IMMEDIATE`` is taken per connection: two
tracks that shared the connection of the poller would step into each other's
transaction rather than wait for it (the warning in the docstring of
:func:`findling.store.repo.open_store`). So the track writes permissions and
marks through a state database connection of its own, and vectors through a
vector database connection of its own; the busy timeout of both makes a second
writer wait instead of fail. The connections of the poller stay with the
indexing track and the delete path.

**Why it never touches the tantivy writer.** tantivy grants one writer lock per
index directory, and that lock belongs to the indexing track. The text an
embedding is computed from is the copy the index stores, and reading it needs a
searcher and nothing else: :func:`findling.index.writer.stored_body` over an
index handle this track opened itself, which never asked for a writer.

**One lock, one row at a time.** :attr:`EmbeddingTrack.lock` is held while a
row is embedded and while the mark step runs. Since plan 25-09 there are two
drivers: the indexing loop, which embeds inline in Economy, and
:class:`EmbedRunner`, which claims the embed lane on its own in Standard and
Performance. The lock is what keeps them from using the track at the same time
(cutter, engine, mark step); the parking of the runner is what keeps OCR and
embedding apart in Economy (IDX-08).

Like the rest of ``worker/``, this module imports nothing from ``api/``, and
its log lines carry counters and type names, never a path, a title or a text.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import sqlite3
import time
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any, Final, Protocol

from tantivy import Index

from findling import lane, memory_guard, profile
from findling.config import (
    CUTTER_LOAD_BYTES,
    EMBED_ACTIVATION_BYTES,
    EMBED_CLAIM_BATCH,
    EMBED_LANE_RESERVE_BYTES,
    EMBED_WEIGHTS_LOAD_BYTES,
    FP32_EXTRA_BYTES,
    settings,
)
from findling.embed.chunker import ChunkSpan, chunk_spans, make_splitter
from findling.embed.engine import (
    ENGINE_LOADED,
    engine_precision,
    engine_state,
    note_cutter_failure,
    shared_model,
    swap_engine,
)
from findling.embed.model import (
    EMBEDDING_UNAVAILABLE,
    LOAD_RETRY_SECONDS,
    EmbeddingModel,
    EmbedOutcome,
    artifacts_present,
    open_tokenizer,
    to_int8,
)
from findling.embed.weights import (
    PROCURED,
    UNAVAILABLE,
    clear_leftovers,
    fp32_verified,
    fp32_weights_path,
    procure_fp32,
)
from findling.index.open import open_index
from findling.index.wordlist import build_artifact
from findling.index.wordlist_nl import dutch_digest_for
from findling.index.writer import disk_is_tight, stored_body
from findling.nc import client as nc_client
from findling.nc.client import AsyncNextcloudApp, fetch_release_asset
from findling.nc.queue import KIND_EMBED, LANE_EMBED, CallResult, DocumentQueue, QueueJob
from findling.precision import Precision, begin_procurement, decide, end_procurement, settle
from findling.precision import snapshot as precision_snapshot
from findling.profile import Profile
from findling.store.repo import (
    ACL_ANY_USER,
    EMBEDDING_BACKLOG_MARK,
    EMBEDDING_MARK,
    UNKNOWN_VERSION,
    Store,
    open_store,
)
from findling.store.vectors import (
    EMBEDDING_MODEL,
    WEIGHTS_FP32,
    Chunk,
    VectorStore,
    embedding_mark,
    open_vectors,
)

LOGGER = logging.getLogger("findling.worker.embedding")

# How one job of the second track ended. Four names, and none of them is a state
# of the file: a document whose vectors could not be written is still indexed,
# has been since the text pass hours earlier, and stays searchable by every word
# it contains (D-15). So none of these is ever handed to Store.record, which is
# also why they are not members of extract.errors.Reason, whose list is the
# closed vocabulary of a judged file and stands in lockstep with the PHP side.
#
# EMBEDDING_UNAVAILABLE is the fourth of them and comes from embed/model.py,
# where the wrapper already answers with it. Naming it a second time here would
# be two spellings of one state.
EMBED_WRITTEN: Final = "embedded"
EMBED_NO_STORED_TEXT: Final = "no_stored_text"
EMBED_INCOMPLETE: Final = "embedding_incomplete"

# How many documents one idle pass hands back to the embedding track while the
# vector stock is being written again after a model change.
#
# Five hundred, and the number is a trade between two request sizes. The
# redelivery is one POST carrying file ids, so the whole instance in one call
# would mean fifty thousand ids in one body on the box this app targets, and the
# companion half writes them in bands of a thousand anyway. Below about a
# hundred the sweep would need an idle pass per band and a model change would
# take a day of cooldowns rather than an hour of work.
#
# It costs nothing on an instance that never drifted: the sweep only runs while
# the cursor beside the mark says a redelivery is unfinished.
VECTOR_BACKLOG_BAND: Final = 500

# Where a redelivery starts, as the cursor spells it. A named value because it
# is written in one place and read in another, and because "0" and "" are two
# different states of the same meta row: "0" is a sweep that has not handed
# anything back yet, "" is no sweep at all.
BACKLOG_START: Final = "0"

# What one round of the embed runner came to. Strings for the reason the poller
# gives: they travel to the status page, where readable names beat a type.
LANE_PARKED: Final = "parked"
ROUND_EMPTY: Final = "empty"
ROUND_WORKED: Final = "worked"
ROUND_PAUSED: Final = "paused"
ROUND_GATEWAY_UNAVAILABLE: Final = "gateway_unavailable"

# How long the runner waits between two rounds that found nothing to do, and
# after a round it parked in. The same fifteen seconds an idle pass of the
# indexing loop is spaced at, and after a memory refusal it is also the least
# time until the headroom is read again, so that a box at the edge does not
# flap between the two modes on every round.
EMBED_RUNNER_TICK_SECONDS: Final = 15.0

# The cap of the runner's backoff after a queue that did not answer or a round
# that had to hand its rows back. The retreat cap of the indexing loop, for the
# same reason: an unanswered queue is a question about the installation.
EMBED_RUNNER_BACKOFF_MAX_SECONDS: Final = 300.0

# How long the indexing loop waits, in front of its claim, for the runner to
# park after the effective level became Economy. One runner round is roughly
# 18 s at EMBED_CLAIM_BATCH rows on the target box (the derivation beside the
# constant in findling/config.py, held by tests/test_config.py), and the runner
# stops after the row in work anyway; sixty seconds cover that three times over.
RUNNER_PARK_WAIT_SECONDS: Final = 60

# How the old engine is let go of after a swap of the weights (D-25-07). A
# search that embedded its line on the old engine a moment before the swap
# still holds it, and the release refuses while that batch is in flight
# (``EmbeddingModel.release``). One query batch is tens of milliseconds, so a
# hundred tries fifty milliseconds apart are five seconds, which covers any
# search the 1.5 s ceiling of the companion lets through several times over.
# After the budget the old engine is dropped anyway: it is out of the holder,
# and the reference of the search is the last one, so its pages go when that
# search returns.
ENGINE_RELEASE_ATTEMPTS: Final = 100
ENGINE_RELEASE_PAUSE_SECONDS: Final = 0.05

# The two halves of the second track, as types. Both are replaceable for the
# same reason: the real ones need a 17 MB tokenizer and 118 MB of weights on the
# machine, and what this module decides has nothing to do with either of them.
Chunker = Callable[[str], "list[ChunkSpan]"]


class PassageEmbedder(Protocol):
    """Whatever can turn the passages of one document into vectors.

    A protocol rather than :class:`findling.embed.model.EmbeddingModel` itself,
    the shape :class:`findling.index.search.QueryEmbedder` established on the
    read side of the same model.
    """

    def embed_passages(self, texts: Sequence[str]) -> EmbedOutcome: ...


class _DiskTight(RuntimeError):
    """The volume fell below the free space floor while a job was running.

    Raised by the embedding branch and by nothing else. The index writer answers
    the same condition at its own flush, but the vector stock is written inside
    the per file loop and long before that flush, so it needs a way of saying
    "not this pass" from in there. What the caller does with it is exactly what
    the flush already does: hand the whole batch back and pause, rather than
    leave half a document in the stock.
    """


def acl_users(job: QueueJob) -> tuple[str, ...]:
    """The rows the prefilter gets for this job, capped list or real list.

    One function for all the write sites, and that is the whole point of it.
    Nextcloud caps a user list that would otherwise be the complete user list of
    the instance (perf audit M5) and marks the job when it did; writing the
    remaining names as if they were the truth would make the file disappear from
    the prefilter for everybody behind the cap. The collective row of
    :data:`findling.store.repo.ACL_ANY_USER` says "no usable list" instead, and
    the prefilter reads it as "candidate for anybody".

    A generosity, never a right: the only authority is the PHP recheck, and a
    candidate that the recheck rejects costs one resolution and shows nobody
    anything. The call sites in the poller and in this track all go through here
    so that another one cannot forget the mark and quietly write the short list.
    """
    if job.users_truncated:
        return (ACL_ANY_USER,)
    return job.user_ids


async def hand_over(queue: DocumentQueue, file_ids: Sequence[int], *, kind: str) -> CallResult:
    """Move rows to a trailing track, and say what happened.

    A failure is an answer and never an exception: the rows stay claimed, run
    into the lock timeout and are handed over by a later pass. The pass itself
    has to finish, because index and verdicts are already durable.

    The whole answer and not only the number, since bug audit M1 of plan
    06.1-17. A caller that has to know whether the hand back happened cannot
    read that off the count: zero is what a failure returns and zero is also
    what a band that found nothing to move returns, and the redelivery of the
    vector stock has to tell those two apart before it moves its cursor.

    The kind is an argument since plan 06-07, because there are two tracks and
    the call is otherwise the same one. It comes from the closed list in
    :mod:`findling.nc.queue` and never from a row, so it may appear in the line
    below without carrying anything of a user with it. A module function since
    plan 25-07, because the poller and this track both hand rows over.
    """
    if not file_ids:
        return CallResult(ok=True)

    result = await queue.requeue(file_ids, kind=kind)
    if not result.ok:
        LOGGER.warning("could not move %d files to the %s track, they run into the lock timeout", len(file_ids), kind)
    return result


def _open_existing_state() -> Store | None:
    """A connection of its own to the state database, or None while there is none.

    The pattern of :func:`findling.worker.reconcile._open_state`, and for the
    same reason: creating the database and seeding its version marks belong to
    the poller, which opens it first. A database created here would carry
    unknown analyzer marks forever (bug audit H1), so this only ever opens a
    file that exists.
    """
    path = settings().state_db
    if not path.exists():
        return None
    return open_store(path)


def _open_read_handle(directory: Path) -> Index | None:
    """An index handle of this track's own, or None while there is no index.

    Opened with the same analyzers and the same Dutch choice the writer and the
    read side use, and never asked for a writer: reading a stored document needs
    a searcher and nothing else. The directory is asked about first, because
    :func:`findling.index.open.open_index` creates a missing one and creating
    the index directory is the poller's business, in front of its first stamp.
    """
    if not directory.is_dir() or not Index.exists(str(directory)):
        return None
    return open_index(directory, build_artifact().entries, dutch=dutch_digest_for(settings().languages))


class EmbeddingTrack:
    """The owner of the second trailing track: cutter, rows, mark, drift and bands.

    The constructor does no I/O, the rule :class:`findling.worker.reconcile.Reconcile`
    follows as well: the lifespan builds the poller, and with it this track,
    while the backend may still be disabled. :meth:`open` connects, in a worker
    thread, once the poller has created the state database and the index
    directory.

    Everything is injectable for the tests. An object that was handed in
    belongs to whoever handed it in and is never closed here.
    """

    def __init__(
        self,
        *,
        vectors: VectorStore | None = None,
        chunker: Chunker | None = None,
        model: PassageEmbedder | None = None,
        store: Store | None = None,
        index: Index | None = None,
        index_dir: Path | None = None,
    ) -> None:
        resolved = settings()
        # The three parts of the second track. They travel together: a container
        # that has one of them and not the others cannot embed anything, so the
        # track is either wired whole or switched off, and _embed_ready is the
        # one place that says which of the two it is.
        self._vectors = vectors
        self._chunker = chunker
        self._model = model
        self._store = store
        self._index = index
        # The directory the text is read from and the free space floor is asked
        # against. One directory for both, the index directory, so that the
        # floor of the stock and the floor of the index are one answer about
        # one volume (T-06-36).
        self._index_dir = resolved.index_dir if index_dir is None else index_dir
        self._min_free_bytes = resolved.min_free_bytes
        self._owns_vectors = vectors is None
        self._owns_store = store is None
        # Three answers about the cutter and never two, in the shape
        # ``EmbeddingModel._load`` already uses for the weights (bug audit
        # HIGH-1 of plan 07-05). The permanent one: the directory has no
        # artifacts, which is a property of the installation and does not change
        # while the process runs. It starts true, because nothing has looked
        # yet, and the eager wiring lowers it once it has seen the two files.
        self._cutter_absent = True
        # The temporary one: when a build last threw, on the monotonic clock.
        # None means never, or not since the last success. A build that threw is
        # a state of the moment on the target box, a MemoryError while 544,3 MB
        # of tokenizer and splitter arrive under a hard 2 GB limit, and a
        # permanent no to that costs the container its semantic half until
        # somebody restarts it.
        self._cutter_failed_at: float | None = None
        self._embed_enabled = resolved.embed_enabled
        # Rows this track is working on right now, whichever driver handed
        # them in. A count and not a flag, so that a second driver later on
        # cannot lower it under the first one.
        self._rows_in_work = 0
        # Held around the embedding of a row and around the mark step. With one
        # driver it orders nothing that was not already in order.
        self.lock = asyncio.Lock()
        # The precision of the weights (MOD-02, plan 25-11). The fetch of the
        # fp32 file runs as a task of its own beside the rounds and outside
        # the lock, one at a time. The start state is settled once per track,
        # and leftovers of a killed download are cleared once per open.
        self._procurement: asyncio.Task[None] | None = None
        self._start_settled = False
        self._fresh_open = True

    # -- lifecycle -------------------------------------------------------

    def open(self, *, wire: bool) -> None:
        """Connect whatever is missing: state database, vector stock, index handle.

        Synchronous, and the poller calls it inside its own ``_open``, which
        already runs in a worker thread. ``wire`` says whether this track may
        open a vector stock of its own; the poller answers it with whether it
        owns its resources, which is the condition the wiring always had.

        Idempotent. Whatever is already there, injected or opened earlier, stays.
        """
        if self._store is None and self._owns_store:
            self._store = _open_existing_state()
        if wire and self._embed_enabled and self._vectors is None:
            self._wire_the_second_track()
        if self._index is None:
            self._index = _open_read_handle(self._index_dir)
        self._fresh_open = True

    async def aclose(self) -> None:
        """Cancel a running fetch of the fp32 weights and wait for it, then close.

        The shutdown half of :meth:`close`. A directory swap of the index goes
        through :meth:`close` alone, in a worker thread, and leaves the fetch
        running: it writes into the models directory, which the swap does not
        touch. A cancelled fetch removes its ``.part`` on the way out.
        """
        task, self._procurement = self._procurement, None
        if task is not None and not task.done():
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self.close()

    def close(self) -> None:
        """Give back the connections this track opened, and the index handle.

        Injected objects are not closed, they belong to whoever handed them in.
        The index handle is dropped either way: tantivy has no close for a
        reader, and the stand down in front of a directory swap is exactly the
        moment a handle on the old directory has to go. The cutter stays; it
        points at no file, and :meth:`release_cutter` is its own door.
        """
        self._index = None
        store, vectors = self._store, self._vectors
        if store is not None and self._owns_store:
            self._store = None
            store.close()
        if vectors is not None and self._owns_vectors:
            self._vectors = None
            vectors.close()

    @property
    def busy(self) -> bool:
        """True while this track is working on a row, whichever driver handed it in.

        Reading has no side effect and takes no lock.
        """
        return self._rows_in_work > 0

    @property
    def ready(self) -> bool:
        """True when rows may be handed to this track: switched on and runnable."""
        return self._embed_enabled and self._embed_ready

    @property
    def cutter_built(self) -> bool:
        """True when tokenizer, splitter and engine wrapper are in memory already.

        Asked by the embed runner before it admits a round: a cutter still to be
        built costs CUTTER_LOAD_BYTES on top of the round itself. Reading has no
        side effect.
        """
        return self._chunker is not None and self._model is not None

    # -- one row ---------------------------------------------------------

    def needs_vectors(self, file_id: int) -> bool:
        """True when this document has no vectors although its text is current.

        The question the two cheap exits ask, and they have to ask it because
        their verdict is ``indexed``: a redelivered content job whose bytes did
        not change is acknowledged by the fast path without a single write, and
        a rename is answered out of the stored text. Neither of them produces a
        fresh verdict, so neither reaches the ordinary handover of the poller,
        and without this question a handover that was lost between the commit
        and the acknowledgement would never be made again. That is the defect
        CR-02 named for the OCR track, one track further along: a transient
        failure turned permanent, with no counter moving anywhere.

        It is asked of the stock rather than of the state database, because the
        stock is the only place that knows. The stored verdict says the document
        is indexed and says nothing about its vectors, and adding a column for
        it would be a second truth about the same thing.

        The other direction is why the ordinary handover does NOT ask it: when
        the text is fresh, the vectors of the old text are wrong and have to be
        replaced whether or not they exist.

        A useful side effect, and it is deliberate: on an instance that was
        indexed before the embedding existed, the first crawl afterwards hands
        every file over and the stock fills up without anybody rebuilding
        anything.
        """
        vectors = self._vectors
        if vectors is None or not self.ready:
            return False
        return not vectors.chunks_of([file_id])

    async def embed_row(self, job: QueueJob, done: list[int]) -> str:
        """Write the vectors of one document, out of the text the index holds.

        **The one line this method does not have is the point of it.** The OCR
        track of the poller fetches the file a second time, because pixels are
        the only thing a scan has. This track does not, and the reason stands
        in full at :func:`findling.index.writer.stored_body`: body_de is the
        only stored copy of the extracted text in the whole system, the same
        copy the snippet generator cuts from, so there is "no gateway call, no
        scratch file, no extraction, no OCR". Downloading the bytes again would
        mean reading a file that did not change in order to produce a text that
        did not change either, once for every document on the instance.

        **No second handover, whatever comes back.** This row was the handover,
        and putting it on the track again is the endless loop of T-03-704 seen
        from the second track. Nothing in here appends to a requeue list, and an
        embed job never reaches the branches that do.

        **Every ending acknowledges the row.** The four of them are named at the
        top of this module and none is a state of the file: the document is
        indexed and stays indexed even when its vectors could not be written
        (D-15). A row that was kept back instead would come round again, collect
        a delivery each time and end as failed(repeatedly_stuck) for a document
        that is perfectly fine.
        """
        self._rows_in_work += 1
        try:
            return await self._embed(job, done)
        finally:
            self._rows_in_work -= 1

    async def _embed(self, job: QueueJob, done: list[int]) -> str:
        """The body of :meth:`embed_row`, inside the count of rows in work."""
        # Before anything is read and long before anything is written. The floor
        # is the one the index writer respects at its flush, asked against the
        # index directory so there is one directory and one number rather than
        # two of each (T-06-36). Checking here rather than just before the write
        # also saves the engine time of a document that could not be stored.
        if disk_is_tight(self._index_dir, self._min_free_bytes):
            raise _DiskTight

        # The start state of the precision before the first vector of this
        # process is written, and not only at the first mark step: a row
        # embedded with the int8 of the image under an fp32 mark would be a
        # mixed stock nothing can tell apart afterwards (T-24-02). Two attribute
        # reads per row once it is settled.
        await self._prepare_the_precision()

        # The first row of the process pays for the tokenizer and the splitter
        # here, in a thread, because the read of the 17 MB artifact and the
        # 544,3 MB behind it must not sit on the event loop that answers
        # searches.
        #
        # **Every row after it pays two attribute reads and nothing else** (perf
        # audit PERF-F1). The question "is it built" is answered on the loop,
        # where it costs nothing, and the thread is entered only when there is
        # really something to build. Before this the hop itself was per row:
        # tens of thousands of trips into the pool over an instance, each one to
        # be told at the top of the method that the cutter was already there.
        #
        # The cooldown of a build that threw is asked here as well, and for the
        # same reason: inside it the build would return false at its own second
        # gate, so hopping into a thread to hear that would be the same cost for
        # the same nothing, once per row for five minutes.
        if (self._chunker is None or self._model is None) and not self._cutter_cooling_down:
            await asyncio.to_thread(self._build_the_cutter)

        vectors, chunker, model = self._vectors, self._chunker, self._model
        if vectors is None or chunker is None or model is None:
            # A row left over from before the admin switched the embedding off,
            # or from before the model was removed. It leaves the queue.
            done.append(job.queue_id)
            return EMBEDDING_UNAVAILABLE

        # The permissions of this row, written for the reason the unchanged-file
        # exit writes them (bug audit M1). An embedding row is not displaced by
        # an acl change on the Nextcloud side (KIND_RANK), so a share that
        # arrives while the row waits travels on the row it upgraded, and this
        # is the pass that has to put it into the prefilter. One declarative
        # write against a file this pass is handling anyway, through the state
        # database connection of this track.
        await asyncio.to_thread(self._store_or_die().replace_acl, job.file_id, acl_users(job))

        index = self._index_or_die()
        body = await asyncio.to_thread(stored_body, index, index.schema, job.file_id)
        if not body:
            # An answer and not a failure: the document was never indexed, or it
            # ended as skipped, and either way there is nothing here to embed.
            done.append(job.queue_id)
            return EMBED_NO_STORED_TEXT

        spans = await asyncio.to_thread(chunker, body)
        if not spans:
            done.append(job.queue_id)
            return EMBED_NO_STORED_TEXT

        outcome = await asyncio.to_thread(
            model.embed_passages, [body[span.char_start : span.char_end] for span in spans]
        )
        if not outcome.available:
            # The container has no weights. Once per process the wrapper says so
            # and remembers it, so this costs one verdict per row and not one
            # search of the file system per document.
            done.append(job.queue_id)
            return EMBEDDING_UNAVAILABLE
        if len(outcome.vectors) != len(spans):
            # The one wrong answer that looks right. Writing what came back would
            # store passages under the offsets of other passages, and nothing in
            # the system would ever notice; half a document is worse than none.
            LOGGER.warning("the model answered %d vectors for %d passages", len(outcome.vectors), len(spans))
            done.append(job.queue_id)
            return EMBED_INCOMPLETE

        await asyncio.to_thread(
            vectors.replace_chunks,
            job.file_id,
            [
                Chunk(
                    ordinal=span.ordinal,
                    char_start=span.char_start,
                    char_end=span.char_end,
                    embedding=to_int8(vector),
                )
                for span, vector in zip(spans, outcome.vectors, strict=True)
            ],
        )
        done.append(job.queue_id)
        return EMBED_WRITTEN

    # -- the cutter ------------------------------------------------------

    def _wire_the_second_track(self) -> None:
        """Open the vector stock, and promise the cutter without building it.

        The eager half. It opens the stock and answers one cheap question about
        the model directory, and it does not read a single artifact. Two things
        can go wrong here and neither is a defect: the sqlite-vec extension is
        not loadable on this build or the volume has no vector database and
        cannot get one, and separately from both, the model directory is empty,
        which is the ordinary case outside the shipping image.

        **The two failures are not the same failure, and since bug audit
        MEDIUM-5 of plan 07-05 they do not share an answer either.** A stock
        that cannot be opened switches the whole track off; there is nothing to
        write vectors into and nothing to take them out of. A missing model
        locks the cutter and nothing else: the stock is opened and it stays
        open.

        **This stock is the track's own since plan 25-07.** The delete path of
        the state database keeps a vector connection of the poller's, attached
        in ``Poller._open``: a tombstone has to take the vectors of its file
        with it (D-21), and it does so whether or not this track ever runs. The
        same sentence is why a missing model locks the cutter and does not
        switch the delete path off: an instance that carried vectors from an
        image with a model, and then ran an image without one, would otherwise
        keep answering semantic queries for files that are gone.

        **The tokenizer and the splitter do not stay here, and that is plan
        07-03.** They cost 265,8 MB and 273,5 MB of resident memory on amd64,
        544,3 MB together with the two chunker runs, measured in
        ``docs/measurements/2026-09-grundlast-fein/rohdaten/01-grundlast-fein-amd64.txt``.
        They belong to this track alone, the read side never touches either of
        them, and a container whose second track has caught up and which only
        searches from then on used to carry them for nothing. So they are built
        at the first row that needs them, in :meth:`_build_the_cutter`, which is
        the third application in this container of the rule
        ``EmbeddingModel._load`` already follows for the weights.

        It runs on the first pass, off the event loop with the rest of
        ``Poller._open``.
        """
        resolved = settings()
        try:
            stock = open_vectors(resolved.vectors_db)
        except Exception as error:
            # The type name and nothing else, the rule of every log line in this
            # module. Once per process, because this runs once per process.
            LOGGER.warning(
                "the embedding track stays off in this container, %s; the search answers lexically",
                type(error).__name__,
            )
            return

        self._vectors = stock

        # Two stats, outside the try because they are not a failure of anything.
        # They keep the promise of _embed_ready honest now that having built the
        # cutter is no longer the thing that proves it can be built, and the
        # answer they give locks the cutter alone.
        if not artifacts_present(resolved.embed_model_dir):
            LOGGER.warning(
                "no embedding model in this container, the second track stays off and the search answers "
                "lexically; the vector stock stays open so a deletion still takes its vectors with it"
            )
            return

        self._cutter_absent = False

    def _build_the_cutter(self) -> bool:
        """Build the tokenizer, the splitter and the engine, at the first row that needs them.

        The lazy half, and it runs once per process: the second call finds the
        two attributes set and returns at the top. Sequential by construction
        rather than by a lock of its own, because the rows are worked one after
        the other under :attr:`lock`; :func:`findling.embed.engine.shared_model`
        carries its own lock for the case that the read side asks at the same
        moment.

        Nothing about the weights is loaded here. Asking ``shared_model`` for
        the engine reads no artifact, which is why it may be asked before it is
        known whether there are any; the tokenizer, on the other hand, is read
        here on purpose, because handing 17 MB of it across the language
        boundary once per document is the cost ``make_splitter`` exists to
        avoid. Both together are the 544,3 MB the eager half no longer pays.

        **The two tokenizer instances of this container are NOT merged, whatever
        the second one costs.** The measurement of plan 07-03 put 216,6 MB on a
        second instance out of the same file, and that number is a finding and
        not an invitation: ``Tokenizer.enable_truncation`` is a property of the
        object, so one shared instance would carry the 512 token window of the
        inference session into ``chunker._first_tokens`` and would silently
        halve the 1024 token cap of D-01. The second half of every document
        would stop existing with nothing failing anywhere.

        **A build that fails answers false and never raises**, so the row that
        asked for it leaves the queue with a name of its own: a row kept back
        for a spur that cannot run is the failed(repeatedly_stuck) loop this
        track exists to avoid.

        **How long that no lasts is the second question, and there are two
        answers to it** (bug audit HIGH-1 of plan 07-05). A directory without
        the artifacts is a property of the installation, is seen by the eager
        half and is answered for ever. A build that threw is a property of the
        moment: the failure that really happens on the target box is a
        MemoryError while 544,3 MB arrive under a hard 2 GB limit, and it is
        remembered with a timestamp and tried again after
        :data:`~findling.embed.model.LOAD_RETRY_SECONDS`. The same constant and
        the same three way split as ``EmbeddingModel._load``, because it is the
        same failure one layer up: before this, one bad moment cost the second
        track of this container everything until somebody restarted it.
        """
        if self._chunker is not None and self._model is not None:
            return True
        if self._cutter_absent:
            return False
        if self._cutter_cooling_down:
            return False

        resolved = settings()
        try:
            tokenizer = open_tokenizer(resolved.embed_model_dir)
            splitter = make_splitter(
                tokenizer,
                chunk_tokens=resolved.embed_chunk_tokens,
                overlap=resolved.embed_chunk_overlap,
            )
            # Inside the try and not below it (bug audit LOW-6). Asking the
            # holder for the engine builds a wrapper and reads no artifact, but
            # a wrapper is still an object and its constructor is still code: a
            # throw there left the splitter assigned and the engine at None,
            # which is the one shape the three parts of this track are never
            # allowed to have. The three travel together or none of them does.
            model = shared_model()
        except Exception as error:
            # The moment, not the property: the stamp is what the cooldown is
            # measured against, and the next row after it runs the build again.
            self._cutter_failed_at = time.monotonic()
            # And the same moment travels to the diagnosis, because the holder
            # of the engine cannot see this failure: the build throws before it
            # ever asks for one, so the admin page would report a cold container
            # for a track that is lying dead (bug audit MEDIUM-2 of plan 07-05).
            note_cutter_failure(self._cutter_failed_at)
            LOGGER.warning(
                "the second track could not build its cutter, %s; it is tried again in %d s "
                "and the search answers lexically until then",
                type(error).__name__,
                int(LOAD_RETRY_SECONDS),
            )
            return False

        def cut(text: str) -> list[ChunkSpan]:
            return chunk_spans(
                text,
                tokenizer=tokenizer,
                splitter=splitter,
                token_cap=resolved.embed_token_cap,
            )

        # Both attributes after the last thing that can throw, and never one of
        # them before it. _embed_ready and the top of this method read the pair,
        # and a half built cutter would answer "built" to both.
        self._chunker = cut
        self._model = model
        self._cutter_failed_at = None
        note_cutter_failure(None)
        return True

    # What this method deliberately does NOT touch: ``_cutter_absent``, which is
    # a property of the installation, and ``_cutter_failed_at``, the running
    # cooldown. Resetting either would be anti pattern 7 of ARCHITECTURE.md
    # (pitfall 8 of the phase research): a container without a model would start
    # stating every row again, twelve times an hour instead of once per process,
    # and a waiting time after a build that threw would end silently.
    def release_cutter(self) -> bool:
        """Let go of the tokenizer and the splitter, both halves or neither.

        The counterpart of :meth:`_build_the_cutter` and the larger of the two
        memory holders of MEM-02: 542,8 MB on the target box, against which the
        engine of the read side is the smaller post. A container that has
        indexed once and only searches from then on carries them for nothing,
        which is the whole reason this door exists.

        Three answers, in this order. A track that is working on a row keeps its
        pair, because releasing in the middle of an indexing run means loading
        the weights again seconds later (pitfall 3); the poller asks the same of
        its held rows before it delegates here. A container that never built the
        pair has nothing to let go of. Everything else drops both fields and says
        so, and the caller in plan 14-07 counts that ``True``.

        The rebuild needs no new code: the head of :meth:`_build_the_cutter`
        returns when both fields are set and builds otherwise, and the row path
        already calls it conditionally.

        **No collection round and no allocator trim here.** Handing the pages
        back to the system happens exactly once per tick, after both holders
        have let go, and it lives in ``embed/model.py`` (plan 14-05). A second
        place would be two trims per tick and a second truth about when memory
        was released.

        Synchronous, and the caller runs it through ``asyncio.to_thread``: the
        house rule of this package is that nothing blocking sits on the event
        loop that answers searches.
        """
        if self.busy:
            # Pitfall 3 of the phase research. The weights fall and the next row
            # loads them again seconds later; over a full run the release turns
            # into a cost instead of a saving, and the run time grows without
            # anything going red.
            return False
        if self._chunker is None and self._model is None:
            return False
        # Both together and never one of them. The closure ``cut`` falls and
        # with it the tokenizer and the splitter it holds; :attr:`_embed_ready`
        # and the head of :meth:`_build_the_cutter` read the pair, so a half
        # released cutter would answer "built" to both of them.
        self._chunker = None
        self._model = None
        return True

    @property
    def _cutter_cooling_down(self) -> bool:
        """True while a build that threw is still inside its cooldown.

        A property and not a field for the reason
        :attr:`~findling.embed.model.EmbeddingModel.load_cooling_down` is one:
        the state is not the timestamp, it is the timestamp measured against
        :data:`~findling.embed.model.LOAD_RETRY_SECONDS`, and that comparison
        has one home. :meth:`_build_the_cutter` and :attr:`_embed_ready` ask the
        same question through here, so the gate that stops the handover and the
        gate that stops the build can never drift into two spellings of one
        rule.

        Reading it has no side effect. The clock is read, nothing else.
        """
        stamp = self._cutter_failed_at
        return stamp is not None and time.monotonic() - stamp < LOAD_RETRY_SECONDS

    @property
    def _embed_ready(self) -> bool:
        """True when the track can run, which since plan 07-03 is not the same as built.

        Asked before a row is handed over, never after. A container whose stock
        could not be opened must not put rows on a track it cannot run: they
        would be claimed, answered with a verdict, claimed again by the next
        pass and eventually written off as failed(repeatedly_stuck) for a track
        that does not exist on this instance.

        What changed with the lazy build is the second half of the sentence, not
        the promise. The stock is still open or the answer is false. The cutter
        may be built or merely buildable, and the two fields of the build say
        which: no artifacts is a no for the life of the process, and a build
        that threw is a no until its cooldown runs out. The window in which a
        row can be handed over to a spur that cannot run is therefore one row
        wide, and that row is acknowledged rather than kept.

        **It asks the same property the build asks** (bug audit HIGH-1 of plan
        07-05). Before that the failed build lowered a flag for good, so one
        MemoryError in one thread stopped the handover of this container for
        ever, and the page said the second track was merely filling up.
        """
        if self._vectors is None:
            return False
        if self._chunker is not None and self._model is not None:
            return True
        return not self._cutter_absent and not self._cutter_cooling_down

    # -- the mark --------------------------------------------------------

    async def keep_the_vector_stock_in_step(self, queue: DocumentQueue) -> None:
        """Hold the embedding mark and the vector stock to the same statement.

        The write half of DI-06-02 and DI-06-03, and the decision behind it is
        E-H4 of 06.09.2026: the mark gets stamped rather than a sentence in the
        documentation asking an admin to do it by hand.

        **Why it is here and not in a status route.** Both halves are writes on
        the index path, and a route that stamped something while answering a
        read would be exactly the side effect this project rules out in three
        places (``open_read_only``, ``PRAGMA query_only``, and the case "asking
        for the status changes nothing"). The precedent is the poller: the marks
        of the full text index are written on an idle pass by the container
        that owns the index, by nobody else and never on a read.

        **What it costs on an ordinary instance.** One read of the meta table,
        which holds under a dozen rows, on an idle pass at most every fifteen
        seconds. The two counts behind it are only asked while the mark is still
        unwritten, and the band behind that only while a redelivery is running.

        Nothing happens on a container without the second track. An instance
        whose admin switched the embedding off, and the ordinary instance
        without the model files, has a stock nothing reads semantically, so a
        mark about it would be a statement about something nobody can reach.
        """
        if not self.ready:
            return
        await self._prepare_the_precision()
        await self._decide_the_precision()
        band = await asyncio.to_thread(self._vector_mark_step)
        if not band:
            return
        # The third step of the drift chain, and the last by construction: the
        # stock was emptied and the mark was written before this list existed.
        # A failure here is a number and not an exception, the rule of every
        # handover in this package.
        #
        # **The cursor moves here and not one step earlier, and that is the whole
        # of bug audit M1 of plan 06.1-17.** It used to be written while the band
        # was being read, so a hand back that did not reach Nextcloud left the
        # cursor past a band nobody had taken: up to VECTOR_BACKLOG_BAND
        # documents kept no vectors after a model change while the mark said the
        # stock was current. Judged on ``ok`` and never on ``count``, because a
        # hand back that found nothing to move still happened, and judging it by
        # the number would turn such a band into an endless one.
        if (await hand_over(queue, band, kind=KIND_EMBED)).ok:
            await asyncio.to_thread(self._store_or_die().write_meta, EMBEDDING_BACKLOG_MARK, str(band[-1]))

    def _vector_mark_step(self) -> list[int]:
        """One step of the mark, returning the documents to hand back, if any.

        A failure is swallowed for the reason ``Poller._stamp_if_rebuilt``
        swallows one: this is bookkeeping about the stock and not the stock, and
        a locked database must not end a pass whose documents are durable.
        """
        try:
            return self._step_of_the_vector_mark()
        except Exception as error:
            LOGGER.warning("could not keep the embedding mark in step, %s", type(error).__name__)
            return []

    def _step_of_the_vector_mark(self) -> list[int]:
        """The three cases of the mark, in the order they exclude each other.

        *Never written.* The mark is ``unknown``, which says nobody named the
        model of this stock rather than that another model wrote it. The stock
        is therefore not thrown away; it is claimed once it is provably whole,
        and "whole" is a number and not a guess: ``embedded == indexed`` at
        ``indexed > 0``, counted over documents (decision of plan 06-09).

        *Drift.* The mark carries a real value and it is not the one this build
        computes. Then the stored vectors were produced by another model,
        another quantisation or another token cap, and they are not vectors any
        more but numbers of the right width. The chain is emptying, marking,
        redelivery, and its order is the whole point: a mark written before the
        emptying would stand over a stock that nothing recognises as stale
        afterwards.

        *Current.* Nothing to decide, except carrying on a redelivery that an
        earlier pass or an earlier process started.

        **The mark deliberately does not go into expected_versions().** That set
        is the mark of the full text index, and a difference in it raises the
        index generation, which forces a rebuild of the tantivy index that costs
        hours on the box this app targets and that D-21 rules out for a vector
        problem. ``VECTOR_ONLY_MARKS`` keeps the two apart, the read side keeps
        the embedding mark out of ``reindexRequired``, and this method writes the
        mark without ever touching that set.
        """
        store = self._store_or_die()
        vectors = self._vectors
        if vectors is None:  # pragma: no cover - _embed_ready answered otherwise
            return []

        # The precision of the model this process actually holds, never a
        # default (T-24-02); plan 25-11 derives the track side from the
        # precision decision once a swap can happen.
        wanted = embedding_mark(EMBEDDING_MODEL, tokens=settings().embed_token_cap, weights=engine_precision())
        meta = store.read_meta()
        stored = meta.get(EMBEDDING_MARK, UNKNOWN_VERSION)

        if stored == UNKNOWN_VERSION:
            self._claim_a_whole_stock(store, vectors, wanted)
            return []
        if stored != wanted:
            return self._answer_the_vector_drift(store, vectors, wanted)
        return self._next_backlog_band(store, meta.get(EMBEDDING_BACKLOG_MARK, ""))

    def _claim_a_whole_stock(self, store: Store, vectors: VectorStore, wanted: str) -> None:
        """Write the mark once every indexed document carries a vector.

        **An empty container claims nothing.** At ``indexed == 0`` there is
        nothing for the stock to be complete about, and ``0 == 0`` would let a
        container that has never seen a document declare its stock whole. The
        mark would then survive the first crawl and say that vectors written
        later belong to a model that was never asked (T-06.1-41).

        The comparison is "at least" and not "equal", although the condition is
        written as an equality everywhere it is stated. The two differ in one
        direction only, a stock holding a document the state database has
        forgotten, and in that direction "equal" would leave the mark unwritten
        for ever while "at least" answers the question that was asked.
        """
        indexed = store.indexed_alive()
        if indexed <= 0 or vectors.document_count() < indexed:
            return
        store.write_meta(EMBEDDING_MARK, wanted)
        LOGGER.info("every indexed document carries a vector, the embedding mark is current")

    def _answer_the_vector_drift(self, store: Store, vectors: VectorStore, wanted: str) -> list[int]:
        """Empty the stock, then mark it, then ask for the documents back.

        The order is the mitigation of T-06.1-39 and it is not interchangeable.
        Marking first would leave a stock of the old model under the mark of the
        new one, and from that moment nothing in this container has any way of
        telling that the answers it gives semantically are computed against
        vectors that mean nothing.

        **An abort anywhere in here is repeatable and costs no double counting.**
        Between the emptying and the mark the next pass finds the same drift,
        empties an empty stock and writes the mark; between the mark and the
        redelivery the cursor beside the mark says where the sweep stands, and
        it survives a restart because it lives in the meta table rather than in
        this process. The redelivery itself is idempotent on the other side: a
        file that already carries an embedding row gets its kind and its attempt
        counter set again rather than a second row.
        """
        vectors.forget_all()
        # The cursor before the mark, and in that order for the reason the
        # emptying comes before both: an abort between them has to leave a state
        # the next pass can read. Cursor first means the next pass finds the
        # drift again, empties an empty stock and writes both; mark first would
        # mean a current mark over a stock with no sweep pointing at it, and the
        # rest of the instance would stay unwritten with nothing saying so.
        store.write_meta(EMBEDDING_BACKLOG_MARK, BACKLOG_START)
        store.write_meta(EMBEDDING_MARK, wanted)
        LOGGER.warning(
            "the vector stock was written by another build, it was emptied and is being written again",
        )
        return self._next_backlog_band(store, BACKLOG_START)

    def _next_backlog_band(self, store: Store, cursor: str) -> list[int]:
        """One band of the redelivery, read and not yet acknowledged.

        An empty cursor means no redelivery is running, which is the state of
        every instance that never changed its model. An empty band ends the
        sweep and clears the cursor here, because there is nothing left to hand
        back and therefore nobody who could confirm it; a band that carries
        documents leaves the cursor alone until they have really been handed
        back (bug audit M1 of plan 06.1-17, and the caller does it).

        The sweep terminates because the ids ascend and the primary key is the
        cursor, so every band lies above the one before it.

        A value that is not a number restarts the sweep rather than raising.
        Nothing writes one, and the answer to a meta row somebody edited by hand
        is one repeated sweep and not a container that stops handing work out.
        """
        if not cursor:
            return []
        after = int(cursor) if cursor.isdigit() else 0
        band = store.indexed_file_ids(after=after, limit=VECTOR_BACKLOG_BAND)
        if not band:
            store.write_meta(EMBEDDING_BACKLOG_MARK, "")
        return band

    # -- the precision ---------------------------------------------------

    async def _prepare_the_precision(self) -> None:
        """Clear a killed download once per open, and settle the start state once.

        **The start state comes from local facts only** (D-25-14, Pitfall 6):
        the stored mark and a verified file. A mark on fp32 with the file whose
        digest matches starts this process on fp32, without a request and
        without emptying anything, also when the profile route has not answered
        yet. Everything else starts on int8. A failed read of the companion is
        never one of the facts, so a hiccup at start cannot discard a stock
        that was built with fp32.

        **No digest without a reason.** The file is only looked at when the
        mark names fp32, so a container that never chose fp32 pays one read of
        the meta table here and nothing else (MOD-02).

        The leftover of a killed download is cleared on the first step after
        an open, and never while a fetch of this track is running: its
        ``.part`` is the file being written.
        """
        if self._fresh_open:
            self._fresh_open = False
            if self._procurement is None or self._procurement.done():
                await asyncio.to_thread(clear_leftovers, settings().models_dir)
        if self._start_settled:
            return
        try:
            start = await asyncio.to_thread(self._start_state)
        except Exception as error:
            # Bookkeeping, like the mark step: the next step asks again, and
            # nothing is settled from a read that did not happen.
            LOGGER.warning("could not read the start state of the precision, %s", type(error).__name__)
            return
        self._start_settled = True
        settle(start)

    def _start_state(self) -> Precision:
        """fp32 when the stored mark names it and the file is verified, else int8."""
        stored = self._store_or_die().read_meta().get(EMBEDDING_MARK, UNKNOWN_VERSION)
        models_dir = settings().models_dir
        if not stored.endswith(f"/{WEIGHTS_FP32}") or not fp32_verified(models_dir):
            return Precision.INT8
        self._swap_the_engine(Precision.FP32, models_dir)
        return Precision.FP32

    async def _decide_the_precision(self) -> Precision | None:
        """Ask the state machine which weights to run, and start a fetch it asks for.

        The file is only looked at while fp32 is chosen or running, so without
        a wish nothing is stated, hashed or fetched here (MOD-02). The fetch is
        started by :func:`~findling.precision.decide` alone, and that answers
        yes only for a change from int8 to fp32 observed in this process: never
        at start, never on a profile switch, never again after a failure until
        the key goes to int8 and back (D-25-04, D-25-05, D-25-10).
        """
        state = precision_snapshot()
        models_dir = settings().models_dir
        fp32_ready = False
        if Precision.FP32 in (state.chosen, state.active):
            fp32_ready = await asyncio.to_thread(fp32_verified, models_dir)
        decision = decide(fp32_ready=fp32_ready)
        if decision.procure:
            self._start_the_procurement(models_dir)
        return decision.target

    def _start_the_procurement(self, models_dir: Path) -> None:
        """One fetch of the fp32 weights as a task of its own, never a second one.

        Outside the track lock by construction: the task is only created here,
        and it runs on the loop while the rounds go on. The round that started
        it does not wait for it, so a download of 470 MB never holds up the
        indexing or the embedding of int8 vectors in the meantime.
        """
        if self._procurement is not None and not self._procurement.done():
            return
        begin_procurement()
        self._procurement = asyncio.create_task(self._procure(models_dir))

    async def _procure(self, models_dir: Path) -> None:
        """Fetch the weights and tell the state machine how it ended.

        Every ending reports, a cancellation included, so the state never
        stays on "downloading" for a fetch that is gone. The log line carries
        the name of the outcome and nothing else: no path, no URL, no digest.
        """
        outcome = UNAVAILABLE
        try:
            outcome = await procure_fp32(models_dir, fetch_release_asset, min_free_bytes=self._min_free_bytes)
        # Deliberately every exception: procure_fp32 answers with a value, and
        # anything else must not end as an unretrieved task exception.
        except Exception as error:
            LOGGER.warning("the fetch of the fp32 weights ended in an unexpected %s", type(error).__name__)
        finally:
            end_procurement(succeeded=outcome == PROCURED)
            LOGGER.info("the fetch of the fp32 weights ended: %s", outcome)

    def _swap_the_engine(self, target: Precision, models_dir: Path) -> None:
        """Point the holder at the weights of ``target`` and let go of the old engine.

        Synchronous, in a worker thread, under the track lock. The holder is
        replaced first, so every search after this line embeds with the new
        weights, and nothing is loaded by it (D-25-07: never two models). The
        old engine is released next, again and again while a search still
        runs a batch on it, within :data:`ENGINE_RELEASE_ATTEMPTS`. The passage
        engine of this track follows the holder, so the next row embeds with
        the new weights and not with the object that was just let go of.
        """
        weights_path = fp32_weights_path(models_dir) if target is Precision.FP32 else None
        old = swap_engine(weights_path, target.value)
        if old is None:
            return
        if self._model is old:
            self._model = shared_model()
        _let_go_of(old)

    # -- plumbing --------------------------------------------------------

    def _store_or_die(self) -> Store:
        if self._store is None:  # pragma: no cover - open() sets it
            raise RuntimeError("the embedding track has no state database")
        return self._store

    def _index_or_die(self) -> Index:
        if self._index is None:  # pragma: no cover - open() sets it
            raise RuntimeError("the embedding track has no index handle")
        return self._index


# Everything the runner talks to, as a type; the defaults are the production
# wiring and a test replaces them one by one.
ClientFactory = Callable[[], AsyncNextcloudApp]
QueueFactory = Callable[[AsyncNextcloudApp], DocumentQueue]
Headroom = Callable[[], "int | None"]
EngineState = Callable[[], str]
Clock = Callable[[], float]

# The levels a runner round may run under. Economy is today's container and
# embeds inside the indexing loop, never beside it (IDX-08, PROF-02).
_PARALLEL_LEVELS: Final = frozenset({Profile.STANDARD, Profile.PERFORMANCE})

# How finely stand_down notices that the round in flight is over. A resolution,
# not a budget, the same figure the poller uses.
_STAND_DOWN_TICK_SECONDS: Final = 0.05

# How long stand_down waits for the round in flight. A round is bounded by
# EMBED_CLAIM_BATCH rows, roughly 18 s on the target box; the answer to an
# overrun is False and nothing released, the rule of Poller.stand_down.
RUNNER_STAND_DOWN_SECONDS: Final = 120.0


class EmbedRunner:
    """The embed lane beside the indexing loop, in Standard and Performance (PAR-01).

    Built after :class:`findling.worker.reconcile.Reconcile`: nothing is opened
    in the constructor, a client and a queue of its own are built in the first
    round whose gate is open, and ``arm``/``silence``/``run`` are the lifecycle
    the lifespan drives (plan 25-10 wires it).

    **The gate, per round and in this order.** The effective level is Standard
    or Performance; the companion of this process has echoed a lane; the
    memory condition of PAR-04 holds, statically out of the profile snapshot
    and live out of the cgroup (anon against the limit, D-25-11), with the load
    costs of a cutter or weights that are not in memory yet. A closed gate
    parks the runner with a reason, and the indexing loop embeds the embed rows
    inline as it always has. After a memory refusal the headroom is read again
    only after a full tick, so a box at the edge does not flap.

    **One runner, one row at a time** (D-25-12). The rows of a claim are
    embedded one after the other under the track lock; Performance gets no
    second embedding beside the first.

    **Every way out without an acknowledgement unlocks.** A SQLite error or the
    disk floor hands every held row back and pauses; an exception the round did
    not expect is caught by :meth:`run`, which unlocks first. Nothing here ever
    writes a failure verdict, so no healthy file can end as
    failed(repeatedly_stuck) through this runner (SC3, DI-05-23).

    **Economy in the middle of a round.** The level is asked again before every
    row; when it turned Economy the round ends after the row in work, the rows
    not reached go back per unlock, and :attr:`parked` is set, which is what the
    indexing loop waits for in front of its claim.

    It never touches the tantivy writer: the track reads the text through a
    handle of its own.
    """

    def __init__(
        self,
        *,
        track: EmbeddingTrack,
        client_factory: ClientFactory = nc_client.create_app_client,
        queue_factory: QueueFactory = DocumentQueue,
        tick: float = EMBED_RUNNER_TICK_SECONDS,
        headroom: Headroom = memory_guard.headroom_bytes,
        engine: EngineState = engine_state,
        clock: Clock = time.monotonic,
    ) -> None:
        self._track = track
        self._client_factory = client_factory
        self._queue_factory = queue_factory
        self._tick = tick
        self._headroom = headroom
        self._engine = engine
        self._clock = clock
        # The byte cap of the claim, the one the indexing loop sends. An embed
        # row downloads nothing, so it is a formality on this lane, and the same
        # number keeps the two claims one agreement with the companion.
        self._max_bytes = settings().batch_max_bytes

        self._client: AsyncNextcloudApp | None = None
        self._queue: DocumentQueue | None = None
        self._held: set[int] = set()
        self._cooldown = 0.0
        self._memory_refused_at: float | None = None
        self._in_flight = False
        self._armed = asyncio.Event()
        # Set whenever no round is running. The indexing loop waits on it after
        # the level turned Economy, before it claims without a lane.
        self.parked = asyncio.Event()
        self.parked.set()

    # -- lifecycle -------------------------------------------------------

    @property
    def busy(self) -> bool:
        """True while this runner holds rows of the work stock. No side effect."""
        return bool(self._held)

    @property
    def cooldown(self) -> float:
        """The extra pause of the backoff, on top of the tick."""
        return self._cooldown

    def arm(self) -> None:
        """Let the runner run rounds again."""
        self._armed.set()

    def silence(self) -> None:
        """Stop running rounds without ending the task."""
        self._armed.clear()

    async def stand_down(self, *, budget: float = RUNNER_STAND_DOWN_SECONDS) -> bool:
        """Silence, wait for the round in flight, and hand the held rows back.

        The pattern of :meth:`findling.worker.poller.Poller.stand_down`: False
        means the round outlasted ``budget`` and nothing was released.
        """
        self._armed.clear()
        deadline = time.monotonic() + budget
        while self._in_flight:
            if time.monotonic() >= deadline:
                LOGGER.warning("the embed round in flight did not end within %.0f s", budget)
                return False
            await asyncio.sleep(_STAND_DOWN_TICK_SECONDS)
        await self.unlock_held()
        return True

    async def unlock_held(self) -> int:
        """Hand back the rows this runner holds and has not acknowledged."""
        queue, held = self._queue, sorted(self._held)
        if queue is None or not held:
            return 0
        result = await queue.unlock(held)
        self._held.clear()
        return result.count

    async def aclose(self) -> None:
        """Let go of the client and the queue. The track belongs to the poller."""
        self._queue = None
        self._client = None

    # -- the loop --------------------------------------------------------

    async def run(self, stop_event: asyncio.Event) -> None:
        """Round after round until the stop event, silent while not armed.

        Every exception of a round is caught here and ends neither this task
        nor the indexing loop. The held rows go back first, and the line
        carries the type name and nothing else (T-25-41).
        """
        while not stop_event.is_set():
            if not self._armed.is_set():
                await _first_of(self._armed.wait(), stop_event.wait())
                continue
            state = ROUND_PAUSED
            try:
                self._in_flight = True
                try:
                    state = await self.run_once()
                finally:
                    self._in_flight = False
            # Deliberately every exception, the rule of the poller and the
            # reconcile: a broken round must not take the search along.
            except Exception as error:
                await self.unlock_held()
                LOGGER.error("embed round ended in an unexpected %s", type(error).__name__)
                self._back_off()
            wait = 0.0 if state == ROUND_WORKED else self._tick
            await _pause(wait + self._cooldown, stop_event)

    async def run_once(self) -> str:
        """One round: the gate, then one claim of the embed lane under the track lock."""
        self.parked.clear()
        try:
            return await self._round()
        finally:
            self.parked.set()

    async def _round(self) -> str:
        reason = await self._gate()
        if reason:
            return self._park(reason)
        lane.note_mode(lane.MODE_PARALLEL, lane.REASON_NONE)
        queue = self._open()

        async with self._track.lock:
            # Asked again behind the lock: the indexing loop may have held it
            # for an inline row while the level changed.
            if not _level_allows_parallel():
                return self._park(lane.REASON_ECONOMY)
            claim = await queue.claim(limit=EMBED_CLAIM_BATCH, max_bytes=self._max_bytes, lane=LANE_EMBED)
            if claim.unavailable:
                self._back_off()
                return ROUND_GATEWAY_UNAVAILABLE
            self._held = {job.queue_id for job in claim.jobs}
            if not claim.lane_honored:
                # A companion from before the filter answered this request, so
                # its rows may be of any kind. All of them go back unjudged, and
                # the runner stays parked for the life of the process (Pitfall 1).
                await self.unlock_held()
                lane.note_refused()
                LOGGER.warning("the companion ignored the embed lane, the embedding stays in the indexing loop")
                return self._park(lane.REASON_OLD_COMPANION)
            if not claim.jobs:
                # The idle moment of this lane, and the mark step belongs to it
                # for the reason it belongs to the idle pass of the poller.
                await self._track.keep_the_vector_stock_in_step(queue)
                self._reset_cooldown()
                return ROUND_EMPTY
            return await self._work(queue, claim.jobs)

    async def _work(self, queue: DocumentQueue, jobs: Sequence[QueueJob]) -> str:
        """Embed the rows of one claim one after the other, and account for each."""
        done: list[int] = []
        stopped = False
        try:
            for job in jobs:
                if not _level_allows_parallel():
                    # Economy arrived in the middle of the claim: the row in work
                    # is finished, the rest goes back below (IDX-08, T-25-37).
                    stopped = True
                    break
                if job.kind != KIND_EMBED:
                    # A row of another lane in an echoed answer is not this
                    # runner's to judge; it goes back with the rest.
                    continue
                await self._track.embed_row(job, done)
        except (sqlite3.Error, _DiskTight) as error:
            # The _abort semantics of the poller: every held row back, a pause,
            # and no verdict at all (Pitfall 3).
            LOGGER.warning(
                "the embed round handed %d rows back after %s and pauses", len(self._held), type(error).__name__
            )
            await self.unlock_held()
            self._back_off()
            return ROUND_PAUSED

        rest = sorted(self._held.difference(done))
        if done:
            await queue.acknowledge(done, {})
        if rest:
            await queue.unlock(rest)
        self._held.clear()
        self._reset_cooldown()
        if stopped:
            return self._park(lane.REASON_ECONOMY)
        return ROUND_WORKED

    # -- the gate --------------------------------------------------------

    async def _gate(self) -> str:
        """The empty reason when a round may claim, otherwise why the runner parks."""
        snapshot = profile.snapshot()
        if snapshot.effective not in _PARALLEL_LEVELS:
            return lane.REASON_ECONOMY
        if not lane.snapshot().supported:
            return lane.REASON_OLD_COMPANION
        if not snapshot.embed_lane_fits:
            return lane.REASON_MEMORY
        refused = self._memory_refused_at
        if refused is not None and self._clock() - refused < self._tick:
            return lane.REASON_MEMORY
        if not await asyncio.to_thread(self._admits, snapshot.weights):
            self._memory_refused_at = self._clock()
            return lane.REASON_MEMORY
        self._memory_refused_at = None
        return lane.REASON_NONE

    def _admits(self, weights: str) -> bool:
        """The live half of the memory condition, in a worker thread (D-25-11)."""
        return memory_guard.admits(self._headroom(), need=self._need(weights))

    def _need(self, weights: str) -> int:
        """What one round may take: activations, one OCR page of reserve, load costs."""
        need = EMBED_ACTIVATION_BYTES + EMBED_LANE_RESERVE_BYTES
        if not self._track.cutter_built:
            need += CUTTER_LOAD_BYTES
        if self._engine() != ENGINE_LOADED:
            need += EMBED_WEIGHTS_LOAD_BYTES
            if weights == WEIGHTS_FP32:
                need += FP32_EXTRA_BYTES
        return need

    # -- plumbing --------------------------------------------------------

    def _park(self, reason: str) -> str:
        lane.note_mode(lane.MODE_INLINE, reason)
        return LANE_PARKED

    def _open(self) -> DocumentQueue:
        """The client and the queue of this runner, built once, in the first open round."""
        if self._queue is None:
            self._client = self._client_factory()
            self._queue = self._queue_factory(self._client)
        return self._queue

    def _back_off(self) -> None:
        """Grow the extra pause: one tick, doubling up to the cap."""
        self._cooldown = min(self._cooldown * 2, EMBED_RUNNER_BACKOFF_MAX_SECONDS) if self._cooldown else self._tick

    def _reset_cooldown(self) -> None:
        self._cooldown = 0.0


def _let_go_of(old: EmbeddingModel) -> bool:
    """Release an engine that left the holder, retrying while a search still runs on it.

    True once it holds no weights any more, released here or never loaded.
    False when the budget ran out; the engine is out of the holder then, and
    its weights go when the search that holds the last reference returns.
    Blocking, and only ever called in a worker thread.
    """
    for attempt in range(ENGINE_RELEASE_ATTEMPTS):
        if not old.loaded or old.release():
            return True
        if attempt + 1 < ENGINE_RELEASE_ATTEMPTS:
            time.sleep(ENGINE_RELEASE_PAUSE_SECONDS)
    LOGGER.warning("the old embedding engine was still in use after the swap, it goes with its last search")
    return False


def _level_allows_parallel() -> bool:
    """True while the effective level lets the embed lane run beside the indexing loop."""
    return profile.snapshot().effective in _PARALLEL_LEVELS


# The two helpers below are copies of the ones in worker/poller.py and
# worker/reconcile.py, for the reason reconcile.py gives: they are private
# there, and poller.py imports this module, so an import back would be a cycle.


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
    """Wait out the pause, or return at once when the stop event arrives."""
    if seconds <= 0:
        await asyncio.sleep(0)
        return
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(stop_event.wait(), timeout=seconds)


__all__ = [
    "BACKLOG_START",
    "EMBED_INCOMPLETE",
    "EMBED_NO_STORED_TEXT",
    "EMBED_RUNNER_BACKOFF_MAX_SECONDS",
    "EMBED_RUNNER_TICK_SECONDS",
    "EMBED_WRITTEN",
    "LANE_PARKED",
    "ROUND_EMPTY",
    "ROUND_GATEWAY_UNAVAILABLE",
    "ROUND_PAUSED",
    "ROUND_WORKED",
    "RUNNER_PARK_WAIT_SECONDS",
    "RUNNER_STAND_DOWN_SECONDS",
    "VECTOR_BACKLOG_BAND",
    "Chunker",
    "EmbedRunner",
    "EmbeddingTrack",
    "PassageEmbedder",
    "acl_users",
    "hand_over",
]
