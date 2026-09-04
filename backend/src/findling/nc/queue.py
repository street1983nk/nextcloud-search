"""The work stock, translated from an OCS answer into something the poller can run.

A thin layer on top of :mod:`findling.nc.client` with three jobs and no fourth.

**It builds jobs out of source objects and refuses the ones it cannot use.** The
source objects come out of Nextcloud, but Nextcloud builds them from file cache
rows, and a row without a mimetype, without a size, or without a single user who
can still see the file is an everyday event on an instance with a broken or
removed mount. Passing such an entry on would end as a confusing failure deep
inside the extraction path, on a file nobody can name because no log here is
allowed to name one. Discarded entries are counted instead, and the counter is
what an admin gets to see.

**It turns transport failures into results.** The poller is the single indexing
task of the process. An exception escaping a queue call would end that task while
the search kept answering, which is the failure class nobody notices for days.
Every call below therefore answers with a value that says "this did not work",
and the poller decides what that means for the batch.

**It creates no client, ever.** :class:`DocumentQueue` takes one and holds it.
``AsyncNextcloudApp`` owns a connection pool, and an initial index walks a hundred
thousand files: a client per file would pay a connection setup per file and, on
the PHP side, a Nextcloud bootstrap including the AppAPI signature check for every
single one of them. ``tools/read_corpus.py`` already carries one client through a
whole loop, and this is the same shape.

This module imports neither the Nextcloud client library nor an HTTP client, and
it never will: invariant 1 of the read-only gate allows both in ``nc/client.py``
alone, and the whole reason this file is separate is that the boundary stays one
file wide. Two tests check that by name, so the two library names deliberately do
not appear anywhere in this file, not even in a comment.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from findling.nc.client import (
    AsyncNextcloudApp,
    ack_documents,
    claim_documents,
    queue_stats,
    requeue_documents,
    unlock_documents,
)

LOGGER = logging.getLogger("findling.nc.queue")

# What the container can do with a row, spelled as the PHP side spells it.
#
# A closed list, because this string picks the branch in the poller and it
# arrives from outside this process (T-03-201). The queue itself is only
# reachable across the ExApp boundary, which rejectForeignCaller guards, but a
# route chosen by a value from a database row deserves a list it has to be in.
#
# The PHP side knows five kinds, and since plan 03-09 all five have a branch in
# the container: content, metadata, delete, acl and ocr. A kind outside this
# list still degrades to content in _kind below, which is the honest thing to
# do with a job whose handler does not exist.
KIND_CONTENT: Final = "content"
KIND_METADATA: Final = "metadata"
KIND_DELETE: Final = "delete"
KIND_ACL: Final = "acl"
KIND_OCR: Final = "ocr"
KINDS: Final = frozenset({KIND_CONTENT, KIND_METADATA, KIND_DELETE, KIND_ACL, KIND_OCR})

# The kinds that describe no node on the PHP side, and therefore arrive without
# the fields a node would have supplied.
#
# A list of the exceptions rather than a loosened check for everybody: an ocr or
# content job without a mimetype, without a size or without a user who can read
# it is still an unusable row, and it has to stay one. Written as the exceptions
# so that a kind added later is treated as needing a node until somebody decides
# otherwise, which is the safe direction of that mistake.
_KINDS_WITHOUT_A_NODE: Final = frozenset({KIND_DELETE, KIND_ACL})

# How many entries one list of an acknowledgement may carry.
#
# The number is not ours. It is QueueController::MAX_LIST_LENGTH on the other
# side, and a list longer than that turns the whole acknowledgement into a bad
# request, which would cost the batch its acknowledgement and leave every row of
# it circling until the lock expires. A test reads the constant out of the PHP
# source and compares it with this one, because the two are one agreement and
# there is no import that could carry it across.
#
# An ordinary pass cannot reach it: a claim is capped at 256 rows on the
# Nextcloud side as well. This is the guard against the day one of those two
# numbers moves without the other.
MAX_ACK_LIST: Final = 256


@dataclass(frozen=True, slots=True)
class QueueJob:
    """One file to look at, as the queue describes it.

    Frozen, because a job that can be edited after the fact is a job two stages of
    the pipeline disagree about.

    ``user_ids`` and ``fetch_as`` stay separate fields even though ``fetch_as`` is
    the first entry of ``user_ids`` today. They answer two different questions:
    who may read this file so that it can be indexed, and who may find it
    afterwards. Phase 3 answers them differently, and merging them now is exactly
    how a prefilter turns into a permission model without anybody deciding that it
    should. On a delete job both are empty, and so are ``mime`` and ``size``: the
    file is gone, nobody can read it, and the deletion needs none of them. On an
    acl job ``fetch_as`` is empty as well, because nothing is read, while
    ``user_ids`` carries the whole payload: everyone who may see the file now,
    which after an unshare can legitimately be nobody at all.

    ``etag`` has no function in phase 2. It is part of the protocol anyway, so the
    reconcile of phase 3 does not have to change the shape of this object to get
    it.

    ``kind`` says what is to be done with the file and therefore which branch of
    the poller runs. It defaults to ``content`` so that a row written before the
    kind column existed is still an ordinary job rather than an unusable entry.

    ``users_truncated`` says that ``user_ids`` is a prefix of the truth and not
    the truth. Nextcloud caps the list at QueueService::MAX_USERS, because an
    instance wide team folder otherwise puts the complete user list of the
    instance on every file (perf audit M5). What the container does with the mark
    is written down at :data:`findling.store.repo.ACL_ANY_USER`; what matters
    here is that the short list must never be written as if it were complete,
    which is why the mark travels with the job rather than being reconstructed
    from a length somewhere later.
    """

    queue_id: int
    file_id: int
    storage_id: int
    root_id: int
    path: str
    title: str
    mime: str
    size: int
    mtime: int
    etag: str
    user_ids: tuple[str, ...]
    fetch_as: str
    is_update: bool
    # Last and with a default, so that the three fields above keep having none:
    # a job without a fetch user is a job nobody can read, and that must stay
    # impossible to build by forgetting an argument.
    kind: str = KIND_CONTENT
    # False by default, and that direction is the safe one: an unmarked job is
    # the ordinary case, and reading a missing mark as "capped" would make every
    # file a candidate for every user on every search.
    users_truncated: bool = False


@dataclass(frozen=True, slots=True)
class ClaimResult:
    """What one pull from the queue produced.

    ``unavailable`` is not the same as an empty ``jobs``: an empty queue means
    there is nothing to do and the poller may sleep longer, while an unreachable
    Nextcloud means the poller knows nothing and must not touch the index.
    """

    jobs: tuple[QueueJob, ...] = ()
    discarded: int = 0
    unavailable: bool = False


@dataclass(frozen=True, slots=True)
class CallResult:
    """The answer of a call that only reports how many rows it moved."""

    ok: bool
    count: int = 0


@dataclass(frozen=True, slots=True)
class QueueStats:
    """Waiting, held right now, and how many files ended as failed."""

    scheduled: int = 0
    running: int = 0
    failed: int = 0
    ok: bool = True


def _mapping(value: object) -> Mapping[str, Any] | None:
    """The value as a string keyed mapping, or None when it is not one.

    PHP renders an empty associative array as a JSON list, so the answer of an
    empty queue arrives as ``[]`` rather than ``{}``. That is not a broken answer
    and must not read like one.
    """
    return value if isinstance(value, dict) else None


def _positive_int(value: object) -> int | None:
    """A positive whole number, or None. Accepts the string form OCS may deliver.

    ``bool`` is rejected explicitly: it is a subclass of ``int`` in Python, and
    ``True`` would otherwise pass as the queue row id 1.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, str) and value.isdigit():
        number = int(value)
        return number if number > 0 else None
    return None


def _whole_number(value: object) -> int | None:
    """A whole number of zero or more, or None. Same bool rule as above."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def _text(value: object) -> str:
    """The value as a string, empty for everything that is not one."""
    return value if isinstance(value, str) else ""


def _kind(value: object) -> str:
    """The job kind, or ``content`` for anything this container cannot run.

    Two cases fall back, and both on purpose. A row written by a PHP side from
    before the kind column carries no kind at all, and it is an ordinary content
    job: discarding it would stop the queue of an instance in the middle of an
    upgrade. And a kind this container has no branch for must not be able to
    pick a branch by being spelled a certain way (T-03-201); it runs the content
    route, which is the safe handler for the unknown.
    """
    return value if isinstance(value, str) and value in KINDS else KIND_CONTENT


def _user_ids(value: object) -> tuple[str, ...]:
    """The users who can see this file, deduplicated and in order.

    Order matters because the first entry is the one the crawl chose to read the
    bytes as, and the answer already arrives in that order.
    """
    if not isinstance(value, list):
        return ()
    return tuple(dict.fromkeys(entry for entry in value if isinstance(entry, str) and entry))


def _capped_skips(skips: Mapping[int, str]) -> list[dict[str, object]]:
    """The skip verdicts as the acknowledgement carries them, never too many.

    Cut rather than refused, and the cut is said out loud (T-05-46). The other
    side answers a list over its ceiling with a bad request for the WHOLE
    acknowledgement, so refusing here would trade a few lost verdicts for a
    whole batch that stays locked until the claim expires. Losing the verdicts
    beyond the ceiling costs two numbers on a page; losing the acknowledgement
    costs the batch.

    Nothing but the file id and the code goes into an entry. No path, no title,
    no excerpt: the reason code is the whole message (T-05-45).
    """
    entries = [{"fileId": file_id, "reason": reason} for file_id, reason in skips.items()]
    if len(entries) <= MAX_ACK_LIST:
        return entries
    LOGGER.warning("dropped %d skip verdicts over the list ceiling of the acknowledgement", len(entries) - MAX_ACK_LIST)
    return entries[:MAX_ACK_LIST]


def _job(queue_id_raw: object, source: object) -> QueueJob | None:
    """Build one job, or None when a field makes the entry unusable.

    Every rejection below has been the shape of a real row: a queue key that is
    not a row id acknowledges nothing and leaves the row circling until the
    give-up rule catches it; a file id of zero is answered with 404 by the content
    gateway and would read as "the user may not see this"; an empty mimetype has
    no route in the extraction allowlist; and a file nobody can see has no user to
    read it as.

    All of that holds for the kinds that go and read the file. A deletion and a
    permission change read nothing, so the last three rejections do not apply to
    them; see the comment at the check itself.
    """
    queue_id = _positive_int(queue_id_raw)
    fields = _mapping(source)
    if queue_id is None or fields is None:
        return None

    kind = _kind(fields.get("kind"))
    file_id = _positive_int(fields.get("fileId"))
    size = _whole_number(fields.get("size"))
    mime = _text(fields.get("mime"))
    user_ids = _user_ids(fields.get("userIds"))
    fetch_as = _text(fields.get("fetchAs"))
    # The one line that used to swallow every deletion. A deleted file has no
    # node left, so the delete branch of QueueService::describe can offer no
    # mimetype, no size and no user who still sees it, and refusing the entry
    # here left the document in the index and the rows in the prefilter forever
    # (pitfall 3). The same emptiness is the legitimate payload of an unshare:
    # after it nobody may see the file, the user list is empty, and that empty
    # list is precisely what has to reach replace_acl (pitfall 4). Hence a check
    # split by kind rather than one loosened for everybody.
    #
    # A usable file id stays required for every kind: it is the whole payload of
    # a deletion and it names the document an acl job rewrites the rows of, and a
    # zero would name no document at all.
    if file_id is None:
        return None
    if kind not in _KINDS_WITHOUT_A_NODE and (size is None or not mime or not user_ids or not fetch_as):
        return None

    return QueueJob(
        queue_id=queue_id,
        file_id=file_id,
        storage_id=_whole_number(fields.get("storageId")) or 0,
        root_id=_whole_number(fields.get("rootId")) or 0,
        path=_text(fields.get("path")),
        title=_text(fields.get("title")),
        mime=mime,
        size=0 if size is None else size,
        mtime=_whole_number(fields.get("mtime")) or 0,
        etag=_text(fields.get("etag")),
        user_ids=user_ids,
        fetch_as=fetch_as,
        is_update=bool(fields.get("isUpdate")),
        kind=kind,
        # Only the literal boolean true counts. bool() of an arbitrary value
        # would read a stray non-empty string as "capped" and widen the
        # prefilter through a typo on the PHP side; anything this container
        # cannot read as the explicit truth falls to the strict side.
        users_truncated=fields.get("userIdsTruncated") is True,
    )


class DocumentQueue:
    """The five queue calls, bound to one client for the whole run."""

    def __init__(self, nc: AsyncNextcloudApp) -> None:
        self._nc = nc

    async def claim(self, *, limit: int, max_bytes: int) -> ClaimResult:
        """Take a batch, translate it, and count what could not be translated."""
        try:
            answer = await claim_documents(self._nc, limit=limit, max_bytes=max_bytes)
        except Exception:
            # Deliberately every exception. The Nextcloud library raises its own
            # type for an OCS verdict, the HTTP client underneath raises several
            # more for a connection that never happened, and this module may
            # import neither of them to name their classes. A narrower catch would
            # be the one that lets the unnamed case end the poller, which is the
            # outcome this whole layer exists to prevent.
            # Debug and not a warning, and that is the one line of this method
            # that needs a reason. One call says nothing about the situation:
            # the caller counts the passes in a row that came back like this and
            # owns the log policy for all of them (Poller._retreat, D-17). While
            # the Nextcloud half is removed a warning here would be one line per
            # attempt forever, which is the disk filling log the retreat exists
            # to prevent (T-05-30). The unavailable flag below carries the whole
            # information, and it is not a log line.
            LOGGER.debug("could not take a batch from the queue")
            return ClaimResult(unavailable=True)

        payload = _mapping(answer)
        entries = _mapping(payload.get("files")) if payload is not None else None
        if not entries:
            return ClaimResult()

        jobs: list[QueueJob] = []
        discarded = 0
        for queue_id_raw, source in entries.items():
            job = _job(queue_id_raw, source)
            if job is None:
                discarded += 1
                continue
            jobs.append(job)

        if discarded:
            # A count and nothing else. The entry that was refused is exactly the
            # kind of value a file name arrives in (T-02-107).
            LOGGER.warning("discarded %d unusable queue entries", discarded)
        return ClaimResult(jobs=tuple(jobs), discarded=discarded)

    async def acknowledge(
        self,
        done: Sequence[int],
        failed: Mapping[int, str],
        skipped: Mapping[int, str] | None = None,
    ) -> CallResult:
        """Report the batch: what is finished, what failed, and what was skipped.

        Three lists and two ways of naming a row. ``failed`` is keyed by queue
        row id, ``skipped`` by file id, and the difference is the receiving side:
        a failure has to be translated into a file id before its row is deleted,
        while a skipped file is acknowledged in the same request anyway. The
        verdict table over there is keyed by file id in both cases.

        ``skipped`` is the crossing of DI-04-03. Four of the reasons in it are
        decided by this container alone, and until they travelled the error list
        of the status page could group only what Nextcloud had decided itself.

        Three empty lists never leave the process. That request can only answer
        zero, and on an idle instance the poller would otherwise pay a round trip
        for every single empty poll.
        """
        skips = dict(skipped or {})
        if not done and not failed and not skips:
            return CallResult(ok=True)

        failures = [{"queueId": queue_id, "reason": reason} for queue_id, reason in failed.items()]
        decisions = _capped_skips(skips)
        try:
            answer = await ack_documents(self._nc, files=list(done), failed=failures, skipped=decisions)
        except Exception:
            # Not acknowledging is survivable by construction: the rows come back
            # after the lock timeout, the state store already knows the verdicts,
            # and the second pass finds the files unchanged and acknowledges them
            # without doing the work again.
            LOGGER.warning("could not acknowledge a batch of %d rows", len(done) + len(failures))
            return CallResult(ok=False)

        payload = _mapping(answer) or {}
        return CallResult(ok=True, count=_whole_number(payload.get("acknowledged")) or 0)

    async def unlock(self, ids: Sequence[int]) -> CallResult:
        """Hand rows back unprocessed, so a restart is productive at once.

        **What the other side does with it, because this container depends on
        it.** Handing a row back is the one way this container can say "I did
        not judge this file", and since plan 05-20 the other side reads it that
        way: the delivery the claim counted is given back with the row
        (QueueMapper::unlock). Without that, a pause below the free space floor
        spent the give-up budget of exactly the rows it was protecting, and a
        disk that was tight for half a minute cost the whole load that happened
        to be with the worker (DI-05-23, measured twice in plan 05-14).

        So the three callers of this method, the disk pause, the content gateway
        that did not answer and the shutdown, all cost time and never work. A
        call that fails costs the lock timeout instead, which is time as well.
        """
        if not ids:
            return CallResult(ok=True)

        try:
            answer = await unlock_documents(self._nc, ids=list(ids))
        except Exception:
            # The lock timeout is the fallback, so this costs time and never work.
            LOGGER.warning("could not release %d held rows, they run into the lock timeout", len(ids))
            return CallResult(ok=False)

        payload = _mapping(answer) or {}
        return CallResult(ok=True, count=_whole_number(payload.get("released")) or 0)

    async def requeue(self, file_ids: Sequence[int], *, kind: str) -> CallResult:
        """Put files on another kind of job, the handover to the second track.

        File ids, not queue row ids: the caller knows the file it just looked
        into, and the reconcile of a later plan knows nothing else at all.

        An empty list never leaves the process, for the same reason as in
        :meth:`acknowledge`: a pass that found no scanned PDF would otherwise pay
        a round trip for an answer that can only be zero.
        """
        if not file_ids:
            return CallResult(ok=True)

        try:
            answer = await requeue_documents(self._nc, file_ids=list(file_ids), kind=kind)
        except Exception:
            # Survivable by construction as well: the rows were not acknowledged,
            # so they come back after the lock timeout, and the second pass finds
            # the same missing text layer and hands them over again. It costs one
            # repeated text layer check and never a document.
            LOGGER.warning("could not hand %d files to another track", len(file_ids))
            return CallResult(ok=False)

        payload = _mapping(answer) or {}
        return CallResult(ok=True, count=_whole_number(payload.get("requeued")) or 0)

    async def stats(self) -> QueueStats:
        """The three counters of the work stock, for the status display."""
        try:
            answer = await queue_stats(self._nc)
        except Exception:
            LOGGER.warning("could not count the queue")
            return QueueStats(ok=False)

        payload = _mapping(answer) or {}
        return QueueStats(
            scheduled=_whole_number(payload.get("scheduled")) or 0,
            running=_whole_number(payload.get("running")) or 0,
            failed=_whole_number(payload.get("failed")) or 0,
        )
