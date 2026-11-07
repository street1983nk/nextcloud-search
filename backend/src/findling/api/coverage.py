"""POST /coverage: the per document coverage of the admin page (plan 43-04, issue #25).

The companion sends the mount list and the share groups that build its
denominator, the same two lists and nothing else, and this route answers with
the figures of :func:`findling.store.repo.coverage_counts`: how many documents
of those storages the search finds, how many carry a vector, how many have a
verdict that belongs to the denominator, each per group and per single storage.
A POST and not a parameter of /status, because the mount list of an instance
with a home storage per user does not fit the 8000 characters of leaveOut.
GET /status?leaveOut= stays as it was, for a companion 1.6.2 (mixed versions).

The body is input, even though only the companion builds it (T-43-11): at most
COVERAGE_MAX_MOUNTED storages and COVERAGE_MAX_MEMBERS group members, every id
a whole number from 1 to 10**18 - 1, groups disjoint and every member mounted.
Anything else is a 422 before a database is opened. A group with fewer than two
members is no group: it is dropped and its member counts as a single storage,
and the answer keeps the order of the remaining groups of the request.

Up to COVERAGE_SYNC_CEILING living rows in the listed storages the count runs
in the request (1.1 s for 188 600 rows, 43-03-SUMMARY.md). Above it the pattern
of the left out count of /status: a background thread with a single flight, a
small cache keyed by the canonical request and by the identity of both stocks,
the age taken from the end of the count. Until a figure exists the answer says
counting with null figures, never an old number.

While a living row of a group member still waits for its document key (the
backfill of plan 43-16), the answer says counting as well: a figure without the
key would rest on reader paths (D-43-14). Every call ends the 404 cooldown of
that backfill, because a companion that asks this route knows the route the
backfill asks.

The answer carries numbers, storage ids, one boolean and null, never a path
(T-43-13). Declared ADMIN in appinfo/info.xml next to /status.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import sqlite3
import threading
import time
from collections import OrderedDict
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Annotated, Final, Self

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from findling.config import settings
from findling.store.repo import CoverageCounts, coverage_counts, open_read_only
from findling.worker.doc_keys import doc_keys_corrected, note_coverage_call

LOGGER = logging.getLogger("findling.api.coverage")

ROUTER = APIRouter()

# The bounds of the body (T-43-11). Fifty thousand storages cover an instance
# with a home storage for every user of a large organisation; a thousand group
# members are the ceiling of leaveOut on /status (LEAVE_OUT_MAX_IDS), which the
# groups replace. Mirrored in php/lib/Service/AdminViewService.php.
COVERAGE_MAX_MOUNTED: Final = 50_000
COVERAGE_MAX_MEMBERS: Final = 1000
# Eighteen digits, the bound of LEAVE_OUT_PATTERN on /status.
COVERAGE_MAX_ID: Final = 10**18 - 1
# Up to this many living rows in the listed storages the count runs in the
# request; above it in the background (the ceiling of the left out count).
COVERAGE_SYNC_CEILING: Final = 100_000
# How long a background figure is answered without a new count, from the end
# of the count that made it, and how many requests the cache keeps.
COVERAGE_CACHE_SECONDS: Final = 300
COVERAGE_CACHE_KEYS: Final = 4

type _FileId = tuple[str, int, int]
type _StockId = tuple[_FileId, _FileId | None]

# The single flight and the cache, all under _COVERAGE_LOCK. An entry is the
# counts in the canonical group order, the monotonic moment the count ended,
# and the stocks it was counted on.
_COVERAGE_LOCK = threading.Lock()
_COVERAGE_REFRESH: threading.Thread | None = None
_COVERAGE_CACHE: OrderedDict[str, tuple[CoverageCounts, float, _StockId]] = OrderedDict()

StorageId = Annotated[int, Field(ge=1, le=COVERAGE_MAX_ID)]


class CoverageRequest(BaseModel):
    """The mount list and the share groups of the companion, numbers only."""

    model_config = ConfigDict(extra="forbid", strict=True)

    mounted: list[StorageId] = Field(max_length=COVERAGE_MAX_MOUNTED)
    groups: list[list[StorageId]] = Field(max_length=COVERAGE_MAX_MEMBERS)

    @model_validator(mode="after")
    def _groups_fit_the_mount_list(self) -> Self:
        """At most COVERAGE_MAX_MEMBERS members, disjoint groups, every member mounted."""
        if sum(len(group) for group in self.groups) > COVERAGE_MAX_MEMBERS:
            message = f"groups name more than {COVERAGE_MAX_MEMBERS} members"
            raise ValueError(message)
        mounted = set(self.mounted)
        seen: set[int] = set()
        for group in self.groups:
            members = set(group)
            if members & seen:
                message = "a storage stands in two groups"
                raise ValueError(message)
            if not members <= mounted:
                message = "a group member is not in the mount list"
                raise ValueError(message)
            seen |= members
        return self


class CoverageResponse(BaseModel):
    """The per document coverage, or null figures while it is counted.

    ``documentsByGroup`` and ``judgedByGroup`` follow the groups of the request
    after the groups of fewer than two members were dropped; the two
    ``ByStorage`` lists are [storage id, figure] pairs of the listed storages
    outside every group, ascending, only figures above zero. ``docKeysMissing``
    is the number of living rows of the whole state without a document key,
    ``docKeysUnresolved`` those with the sentinel, ``docKeysCorrected`` the
    keys the verify pass replaced since this process started.
    """

    documents: int | None
    embeddedDocuments: int | None
    judgedDocuments: int | None
    documentsByGroup: list[int] | None
    judgedByGroup: list[int] | None
    documentsByStorage: list[tuple[int, int]] | None
    judgedByStorage: list[tuple[int, int]] | None
    counting: bool
    docKeysMissing: int
    docKeysUnresolved: int
    docKeysCorrected: int


def answer_of(counts: CoverageCounts | None, *, missing: int, unresolved: int, corrected: int) -> CoverageResponse:
    """The answer, field by field and never spread; counting while there is no figure.

    No figure exists before the first count ended and while a group member
    still waits for its key (D-43-14).
    """
    if counts is None or counts.doc_keys_missing > 0:
        return CoverageResponse(
            documents=None,
            embeddedDocuments=None,
            judgedDocuments=None,
            documentsByGroup=None,
            judgedByGroup=None,
            documentsByStorage=None,
            judgedByStorage=None,
            counting=True,
            docKeysMissing=missing,
            docKeysUnresolved=unresolved,
            docKeysCorrected=corrected,
        )
    return CoverageResponse(
        documents=counts.documents,
        embeddedDocuments=counts.embedded_documents,
        judgedDocuments=counts.judged_documents,
        documentsByGroup=list(counts.documents_by_group),
        judgedByGroup=list(counts.judged_by_group),
        documentsByStorage=sorted(counts.documents_by_storage.items()),
        judgedByStorage=sorted(counts.judged_by_storage.items()),
        counting=False,
        docKeysMissing=missing,
        docKeysUnresolved=unresolved,
        docKeysCorrected=corrected,
    )


def _kept_groups(groups: Sequence[Sequence[int]]) -> list[list[int]]:
    """The groups of the request with two members or more, sorted inside, in request order."""
    kept: list[list[int]] = []
    for group in groups:
        members = sorted(set(group))
        if len(members) >= 2:
            kept.append(members)
    return kept


def canonical_key(mounted: Sequence[int], groups: Sequence[Sequence[int]]) -> str:
    """The cache key of a request: sha256 over its canonical form.

    The order of the ids and of the groups does not change the question, so it
    does not change the key either (T-43-12).
    """
    form = {"mounted": sorted(set(mounted)), "groups": sorted(_kept_groups(groups))}
    return hashlib.sha256(json.dumps(form, separators=(",", ":")).encode()).hexdigest()


def _in_request_order(counts: CoverageCounts, canonical: list[list[int]], kept: list[list[int]]) -> CoverageCounts:
    """Counts of the canonical group order, put back into the order of the request."""
    position = {tuple(group): index for index, group in enumerate(canonical)}
    order = [position[tuple(group)] for group in kept]
    return replace(
        counts,
        documents_by_group=tuple(counts.documents_by_group[index] for index in order),
        judged_by_group=tuple(counts.judged_by_group[index] for index in order),
    )


def _monotonic() -> float:
    return time.monotonic()


def _file_id(path: Path) -> _FileId | None:
    """The identity of the file at this path, None when it cannot be read."""
    try:
        found = path.stat()
    except OSError:
        return None
    return (str(path), found.st_dev, found.st_ino)


def _stock_id(state_db: Path, vectors_db: Path) -> _StockId | None:
    """Both stocks a figure was counted on; None without a state database.

    A missing vector stock is a stock of its own (the vector figure is 0 on
    it), so it is part of the identity rather than a reason for no figure.
    """
    state = _file_id(state_db)
    if state is None:
        return None
    return (state, _file_id(vectors_db))


def _cached(key: str, mounted: list[int], canonical: list[list[int]]) -> CoverageCounts | None:
    """The background figure of this request, None while there is none.

    Answers at once. A figure of other stocks is no figure; a stale one is
    answered and starts the next count; a missing one starts one. Single
    flight: while a count runs, for this request or another, nothing starts.
    """
    resolved = settings()
    stock = _stock_id(resolved.state_db, resolved.vectors_db)
    now = _monotonic()
    with _COVERAGE_LOCK:
        cached = _COVERAGE_CACHE.get(key)
        if cached is not None and stock is not None and cached[2] == stock:
            _COVERAGE_CACHE.move_to_end(key)
            if now - cached[1] >= COVERAGE_CACHE_SECONDS:
                _start_refresh(key, mounted, canonical)
            return cached[0]
        _start_refresh(key, mounted, canonical)
        return None


def _start_refresh(key: str, mounted: list[int], canonical: list[list[int]]) -> None:
    """Start the background count of one request unless a count runs. Under _COVERAGE_LOCK."""
    global _COVERAGE_REFRESH
    if _COVERAGE_REFRESH is not None:
        return
    thread = threading.Thread(
        target=_refresh,
        args=(key, mounted, canonical),
        name="findling-coverage-refresh",
        daemon=True,
    )
    _COVERAGE_REFRESH = thread
    try:
        thread.start()
    except RuntimeError as error:
        _COVERAGE_REFRESH = None
        LOGGER.warning("the coverage count could not start, %s", type(error).__name__)


def _refresh(key: str, mounted: list[int], canonical: list[list[int]]) -> None:
    """Count outside the lock, write inside it, only onto the stocks it counted.

    The thread is handed storage ids and nothing that names a file; both
    paths come from the settings. Never raises: a failure costs this figure,
    leaves no entry, and the next request starts a new count.
    """
    global _COVERAGE_REFRESH
    try:
        resolved = settings()
        stock = _stock_id(resolved.state_db, resolved.vectors_db)
        if stock is None:
            return
        counted = coverage_counts(resolved.state_db, resolved.vectors_db, mounted, canonical)
        ended = _monotonic()
        with _COVERAGE_LOCK:
            current = settings()
            if (current.state_db, current.vectors_db) == (resolved.state_db, resolved.vectors_db) and _stock_id(
                current.state_db, current.vectors_db
            ) == stock:
                _COVERAGE_CACHE[key] = (counted, ended, stock)
                _COVERAGE_CACHE.move_to_end(key)
                while len(_COVERAGE_CACHE) > COVERAGE_CACHE_KEYS:
                    _COVERAGE_CACHE.popitem(last=False)
    except (OSError, sqlite3.Error) as error:
        LOGGER.warning("the coverage count could not be read, an %s", type(error).__name__)
    finally:
        with _COVERAGE_LOCK:
            if _COVERAGE_REFRESH is threading.current_thread():
                _COVERAGE_REFRESH = None


def join_coverage_refresh(timeout: float | None = 10.0) -> None:
    """Wait for a running background count to end. For tests and nothing else."""
    with _COVERAGE_LOCK:
        thread = _COVERAGE_REFRESH
    if thread is not None:
        thread.join(timeout)


def cached_keys() -> int:
    """How many requests the cache holds. For tests and nothing else."""
    with _COVERAGE_LOCK:
        return len(_COVERAGE_CACHE)


def _reset_coverage_cache_for_tests() -> None:
    """Empty the cache. For tests and nothing else."""
    with _COVERAGE_LOCK:
        _COVERAGE_CACHE.clear()


def _unavailable(error: Exception) -> HTTPException:
    LOGGER.warning("the coverage could not be counted, an %s", type(error).__name__)
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="unavailable")


def _answer(request: CoverageRequest) -> CoverageResponse:
    """Everything of one request, off the event loop."""
    mounted = sorted(set(request.mounted))
    kept = _kept_groups(request.groups)
    canonical = sorted(kept)
    corrected = doc_keys_corrected()
    resolved = settings()
    if not resolved.state_db.is_file():
        # A fresh volume: nothing is indexed yet, which is a figure.
        empty = CoverageCounts(0, 0, 0, (0,) * len(kept), (0,) * len(kept), {}, {}, 0)
        return answer_of(empty, missing=0, unresolved=0, corrected=corrected)
    try:
        store = open_read_only(resolved.state_db)
        try:
            rows = store.living_rows_in_storages(mounted)
            missing = store.doc_keys_missing()
            unresolved = store.doc_keys_unresolved()
        finally:
            store.close()
        if rows <= COVERAGE_SYNC_CEILING:
            counts: CoverageCounts | None = coverage_counts(resolved.state_db, resolved.vectors_db, mounted, canonical)
        else:
            counts = _cached(canonical_key(mounted, canonical), mounted, canonical)
    except (OSError, sqlite3.Error) as error:
        raise _unavailable(error) from None
    if counts is not None:
        counts = _in_request_order(counts, canonical, kept)
    return answer_of(counts, missing=missing, unresolved=unresolved, corrected=corrected)


@ROUTER.post("/coverage")
async def read_coverage(body: CoverageRequest) -> CoverageResponse:
    """Count the coverage per document for the mount list and the groups of the body."""
    note_coverage_call()
    return await asyncio.to_thread(_answer, body)


__all__ = [
    "COVERAGE_CACHE_KEYS",
    "COVERAGE_CACHE_SECONDS",
    "COVERAGE_MAX_ID",
    "COVERAGE_MAX_MEMBERS",
    "COVERAGE_MAX_MOUNTED",
    "COVERAGE_SYNC_CEILING",
    "ROUTER",
    "CoverageRequest",
    "CoverageResponse",
    "answer_of",
    "cached_keys",
    "canonical_key",
    "join_coverage_refresh",
]
