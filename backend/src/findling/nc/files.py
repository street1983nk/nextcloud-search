"""The file list of Nextcloud, page by page, as the reconcile has to read it.

A thin layer on top of :mod:`findling.nc.client` with the same three jobs as
:mod:`findling.nc.queue` and no fourth.

**It builds objects out of answers and refuses what it cannot use.** The rows
come out of the file cache of a live instance, and a row without a usable file
id, without an etag or without a mimetype is not a rare event on a mount that a
storage backend answered badly. Passing such a row on would not end as an error,
it would end as a wrong verdict: an etag that cannot be compared reads as
"unchanged" for a file that may well have changed.

**It turns transport failures into results.** The reconcile is repair work that
runs beside the indexing task. An exception escaping a call here would end the
task that carries it while everything else keeps answering, which is the failure
class nobody notices for days. Every call below answers with a value that says
"this did not work", and the caller decides what that means for the round.

**It creates no client, ever.** :class:`FileList` takes one and holds it. The
client owns a connection pool, and a walk over a large instance is many pages: a
client per page would pay a connection setup per page and, on the PHP side, a
Nextcloud bootstrap including the AppAPI signature check for every single one of
them.

All three calls of this module read. None needs an entry in the write allowlist of
the read-only gate, because that list only judges writing HTTP methods, and
none gets one: an entry that is not needed is a widening of a security gate
for nothing.

This module imports neither the Nextcloud client library nor an HTTP client, and
it never will: invariant 1 of the read-only gate allows both in ``nc/client.py``
alone, and the whole reason this file is separate is that the boundary stays one
file wide. A test scans the package for the two library names, so they
deliberately do not appear anywhere in this file, not even in a comment.

One property of the deletion rule runs through everything below and is the reason
this layer is careful rather than convenient. The reconcile calls a file deleted
when it knows the file locally, the file id lies in the range the page covers,
and the page does not carry it. A row this layer refuses is a row that is not in
the page. Therefore a page with a discard must never be used for a deletion
verdict, and :attr:`SliceResult.complete` is how a page says so.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

# The mount call is renamed on the way in. The method below carries the name the
# caller uses, and a call to the plain name inside a method of the same name
# reads like recursion to everybody who has ever debugged one.
from findling.nc.client import AsyncNextcloudApp, files_slice
from findling.nc.client import gone_storages as ask_gone_storages
from findling.nc.client import mounts as read_mounts

LOGGER = logging.getLogger("findling.nc.files")

# How many storage ids one storage question may carry. Equal to
# ReconcileController::MAX_STORAGE_IDS on the PHP side, which refuses a longer
# list with HTTP 400; a test in tests/test_files_client.py reads the PHP constant
# and holds the two numbers together.
GONE_LOOKUP_BAND = 256


@dataclass(frozen=True, slots=True)
class Mount:
    """One mount of the instance, as the crawl and the reconcile both see it.

    ``root_id`` and ``overridden_root`` are two different nodes and both are
    needed. Storage id and root id together identify the mount, while the
    overridden root is the node the file query walks: for a home mount it is the
    files folder, which is what keeps the trash bin and the version folder out of
    the comparison in the first place.
    """

    storage_id: int
    root_id: int
    overridden_root: int


@dataclass(frozen=True, slots=True)
class FileRow:
    """One file of a page, reduced to what the comparison needs.

    Seven fields and no more. There is no path, no name and no owner in this
    object, because the comparison works on file id and etag and everything
    beyond that would be content of a private instance travelling for no reason.

    ``state`` and ``reason`` are the end state the Nextcloud side holds for this
    file, as two codes out of the closed list both sides share. They are the
    verdict handover of review finding IN-03: the give-up rule runs over there,
    the comparison runs in here, and without the two codes the comparison keeps
    requeueing a file that was written off months ago. Codes and numbers cross
    the boundary, names and paths do not, so this stays inside the privacy
    contract of the whole route.

    Both default to the empty string, which reads as "no verdict". A companion
    app that is one release behind sends neither field, and the round then
    behaves exactly as it did before them rather than treating every file as
    unjudged work.
    """

    file_id: int
    etag: str
    size: int
    mtime: int
    mime: str
    state: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class MountResult:
    """The mount list of one round.

    ``unavailable`` is not the same as an empty ``mounts``: an instance without a
    single mount is a fresh installation and a legitimate answer, while an
    unreachable Nextcloud means the round knows nothing and must not conclude
    anything at all.
    """

    mounts: tuple[Mount, ...] = ()
    discarded: int = 0
    unavailable: bool = False


@dataclass(frozen=True, slots=True)
class GoneResult:
    """The answer of the storage question (plan 36-04, D-36-14).

    ``gone`` are storages Nextcloud no longer has at all, ``deselected`` are
    storages only a provider the admin switched off in Findling still carries.
    Both lose their documents at once; every other absent storage waits out the
    grace. Only ids that were asked for ever appear here.
    """

    gone: frozenset[int] = frozenset()
    deselected: frozenset[int] = frozenset()


@dataclass(frozen=True, slots=True)
class SliceResult:
    """One page of the file list of one mount.

    ``final`` says that there is nothing behind this page, which is the only
    thing that allows the deletion rule to drop its upper bound.

    ``complete`` says that the page carries everything the instance had in its
    range. A page that had to refuse a row is not complete, and the difference
    matters more than it looks: a refused row is missing from the page, and
    "missing from the page" is exactly the shape of a deletion.
    """

    files: tuple[FileRow, ...] = ()
    final: bool = False
    discarded: int = 0
    unavailable: bool = False

    @property
    def complete(self) -> bool:
        """True when every row of the range arrived and was usable."""
        return not self.discarded and not self.unavailable


# The three checkers below mirror the ones in nc/queue.py line for line, and the
# copy is deliberate. They are private there, this module may not reach into the
# internals of a sibling, and moving them into a shared place would be an edit to
# a module this plan does not own. Two copies of six lines each are cheaper than
# either, and a test in each suite pins the behaviour.


def _mapping(value: object) -> Mapping[str, Any] | None:
    """The value as a string keyed mapping, or None when it is not one."""
    return value if isinstance(value, dict) else None


def _sequence(value: object) -> Sequence[object]:
    """The value as a list, empty for everything that is not one.

    PHP renders an empty associative array as a JSON list and a filled one as an
    object, so a page that arrives as ``{}`` has to read as "no rows" rather than
    as a broken answer. Everything that is neither is refused as a whole, which
    is the safe direction: a broken shape read as an empty page would look like a
    mount whose files all went away at once.
    """
    return value if isinstance(value, list) else ()


def _positive_int(value: object) -> int | None:
    """A positive whole number, or None. Accepts the string form OCS may deliver.

    ``bool`` is rejected explicitly: it is a subclass of ``int`` in Python, and
    ``True`` would otherwise pass as the storage id 1.
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


def _mount(entry: object) -> Mount | None:
    """Build one mount, or None when a field makes the entry unusable."""
    fields = _mapping(entry)
    if fields is None:
        return None

    storage_id = _positive_int(fields.get("storageId"))
    root_id = _positive_int(fields.get("rootId"))
    overridden_root = _positive_int(fields.get("overriddenRoot"))
    if storage_id is None or root_id is None or overridden_root is None:
        return None

    return Mount(storage_id=storage_id, root_id=root_id, overridden_root=overridden_root)


def _row(entry: object) -> FileRow | None:
    """Build one file row, or None when a field makes the entry unusable.

    The etag is required, and that is the field worth naming. It is the whole
    comparison: without it the reconcile could only ever answer "I know this file
    id", which would let a changed file stay stale for good.
    """
    fields = _mapping(entry)
    if fields is None:
        return None

    file_id = _positive_int(fields.get("fileId"))
    etag = _text(fields.get("etag"))
    size = _whole_number(fields.get("size"))
    mtime = _whole_number(fields.get("mtime"))
    mime = _text(fields.get("mime"))
    if file_id is None or not etag or size is None or mtime is None or not mime:
        return None

    # The two verdict codes are read but never required. A missing one is the
    # honest answer of a companion app that does not send them yet, and _text
    # turns anything that is not a string into the same empty value, so a broken
    # field can only ever mean "no verdict" and never a verdict nobody wrote.
    return FileRow(
        file_id=file_id,
        etag=etag,
        size=size,
        mtime=mtime,
        mime=mime,
        state=_text(fields.get("state")),
        reason=_text(fields.get("reason")),
    )


def _id_set(value: object) -> frozenset[int] | None:
    """A list of positive whole numbers as a set, or None when any entry is not one.

    One bad entry refuses the whole list, because this answer decides on delete
    orders: a list that is read in part is a list that may be missing the entry
    that would have said "keep".
    """
    if not isinstance(value, list):
        return None
    found: set[int] = set()
    for entry in value:
        number = _positive_int(entry)
        if number is None:
            return None
        found.add(number)
    return frozenset(found)


class FileList:
    """The three reading calls of the reconcile, bound to one client for the run."""

    def __init__(self, nc: AsyncNextcloudApp) -> None:
        self._nc = nc

    async def mounts(self) -> MountResult:
        """Every mount the reconcile may walk, in the order Nextcloud lists them."""
        try:
            answer = await read_mounts(self._nc)
        except Exception:
            # Deliberately every exception, for the same reason as in the queue
            # layer: the client library raises its own type for an OCS verdict,
            # the HTTP client underneath raises several more for a connection
            # that never happened, and this module may import neither of them to
            # name their classes.
            LOGGER.warning("could not read the mount list, skipping this round")
            return MountResult(unavailable=True)

        payload = _mapping(answer) or {}
        found: list[Mount] = []
        discarded = 0
        for entry in _sequence(payload.get("mounts")):
            mount = _mount(entry)
            if mount is None:
                discarded += 1
                continue
            found.append(mount)

        if discarded:
            # A count and nothing else, exactly as in the queue layer: the entry
            # that was refused is the kind of value a file name arrives in.
            LOGGER.warning("discarded %d unusable mount entries", discarded)
        return MountResult(mounts=tuple(found), discarded=discarded)

    async def page(self, *, storage: int, root: int, after: int, limit: int) -> SliceResult:
        """One page of one mount, ordered by file id and starting behind the cursor.

        ``root`` is the overridden root of the mount, because that is the node the
        file query walks.
        """
        try:
            answer = await files_slice(self._nc, storage=storage, root=root, after=after, limit=limit)
        except Exception:
            LOGGER.warning("could not read a page of the file list, ending this walk")
            return SliceResult(unavailable=True)

        payload = _mapping(answer) or {}
        rows: list[FileRow] = []
        discarded = 0
        for entry in _sequence(payload.get("files")):
            row = _row(entry)
            if row is None:
                discarded += 1
                continue
            rows.append(row)

        if discarded:
            LOGGER.warning("discarded %d unusable file rows", discarded)

        # The mark is taken from the answer and never guessed from the number of
        # rows, and anything that is not the boolean true counts as not final. A
        # page wrongly held open costs one more round; a page wrongly declared
        # final drops the upper bound of the deletion rule and costs documents.
        final = payload.get("final") is True

        return SliceResult(files=tuple(rows), final=final, discarded=discarded)

    async def gone_storages(self, ids: Sequence[int]) -> GoneResult | None:
        """Ask which of these absent storages are deleted or switched off.

        None means "no answer" and is the safe reading: a failed call, a 404 of
        a 1.4.x companion that has no such route, a broken shape or a band that
        failed. The reconcile then treats every absent storage as merely
        vanished: nothing is deleted at once, and only a storage whose stamp has
        already outlived the grace is swept (D-36-05, WR-36-02). Ids in the
        answer that were not asked for are dropped (T-36-14).
        """
        asked = list(dict.fromkeys(ids))
        gone: set[int] = set()
        deselected: set[int] = set()
        for start in range(0, len(asked), GONE_LOOKUP_BAND):
            band = asked[start : start + GONE_LOOKUP_BAND]
            try:
                answer = await ask_gone_storages(self._nc, band)
            except Exception:
                # Every exception, for the reason given in mounts(). The message
                # is not logged: it is the kind of value a path arrives in.
                LOGGER.warning("could not ask which storages are gone, treating all of them as vanished")
                return None

            payload = _mapping(answer)
            band_gone = None if payload is None else _id_set(payload.get("gone"))
            band_deselected = None if payload is None else _id_set(payload.get("deselected"))
            if band_gone is None or band_deselected is None:
                LOGGER.warning("the answer about gone storages was unusable, treating all of them as vanished")
                return None

            wanted = frozenset(band)
            gone |= band_gone & wanted
            deselected |= band_deselected & wanted

        return GoneResult(gone=frozenset(gone), deselected=frozenset(deselected))
