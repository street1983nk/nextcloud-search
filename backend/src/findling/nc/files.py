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

Both calls of this module read. Neither needs an entry in the write allowlist of
the read-only gate, because that list only judges writing HTTP methods, and
neither gets one: an entry that is not needed is a widening of a security gate
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
from findling.nc.client import mounts as read_mounts

LOGGER = logging.getLogger("findling.nc.files")


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

    Five fields and no more. There is no path, no name and no owner in this
    object, because the comparison works on file id and etag and everything
    beyond that would be content of a private instance travelling for no reason.
    """

    file_id: int
    etag: str
    size: int
    mtime: int
    mime: str


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

    return FileRow(file_id=file_id, etag=etag, size=size, mtime=mtime, mime=mime)


class FileList:
    """The two reading calls of the reconcile, bound to one client for the run."""

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
