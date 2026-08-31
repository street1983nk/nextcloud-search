"""The only module in Findling that touches nc_py_api.

Every other module imports the AppAPI building blocks from here, never from
nc_py_api itself. Two reasons, both load bearing:

1. An nc_py_api update hits exactly one file. The sync API disappears in 0.31.0,
   so the async entry points re-exported below are the ones with a future.
2. The read-only invariant (IDX-07) is only statically checkable because of this
   seam. "No other module imports nc_py_api" is a property a parser can verify,
   "nobody writes anywhere" is not. Gate A enforces invariant 1 against this
   module path and invariant 2 against the identifiers inside it.

The same seam holds for ``httpx``, which this module uses for the content gateway
and which no other module may import. A module with its own HTTP client could
write to Nextcloud without naming the client library once, so the gate treats both
imports the same way.

Consequently the writing entry points of ``nc_py_api.files`` and the
impersonation entry point of ``AsyncNextcloudApp`` are deliberately absent from
the re-export list: a caller cannot reach what the boundary does not hand out.

Since plan 02-10 this module holds the one writing channel the container has: two
of the four queue calls at the bottom of the file acknowledge and release rows of
the work stock. They reach the two database tables the companion app owns and
nothing else, and the gate carries them as a named, tested exception rather than
as a general permission to write.
"""

import asyncio
import os
from base64 import b64encode
from collections.abc import Mapping, Sequence
from typing import IO

import httpx
from nc_py_api import AsyncNextcloudApp, NextcloudException
from nc_py_api.ex_app import AppAPIAuthMiddleware, anc_app, run_app, set_handlers

__all__ = [
    "CHUNK_SIZE",
    "GATEWAY_PATH",
    "NC_PY_API_VERIFIED_VERSION",
    "AppAPIAuthMiddleware",
    "AsyncNextcloudApp",
    "GatewayClient",
    "NextcloudException",
    "ack_documents",
    "anc_app",
    "app_api_headers",
    "claim_documents",
    "create_app_client",
    "current_user_id",
    "fetch_file_stream",
    "gateway_url",
    "new_gateway_client",
    "queue_stats",
    "run_app",
    "set_handlers",
    "unlock_documents",
]

# The transport type of the content gateway. Exported so that a caller can
# annotate a pooled client without importing httpx: the read-only gate allows that
# import in this module only, and this alias is how the restriction stays cheap to
# obey rather than something to work around.
GatewayClient = httpx.AsyncClient

# The release the header layout below was read against. It is named here so that
# an upgrade has one obvious place to be re-verified.
NC_PY_API_VERIFIED_VERSION = "0.30.3"

# The content gateway of the PHP companion. The file id is the only variable
# part; there is no path string anywhere, so traversal is impossible by shape
# rather than by filtering.
GATEWAY_PATH = "/ocs/v2.php/apps/findling/files/{file_id}"

# Bytes per block on the way from the gateway into the caller's file object. The
# target hardware is a 4 GB box, so a file is never held in memory as a whole.
CHUNK_SIZE = 65536

# Answers that mean "this user does not get this file". 404 is what the gateway
# returns for both "does not exist" and "not yours", deliberately indistinguishable.
# 998 is the OCS specific variant of the same verdict.
_NOT_ACCESSIBLE_STATUS = frozenset({404, 998})

_FIRST_ERROR_STATUS = 400

# Fallbacks for the two environment variables the client library uses to
# configure transport. Mirrored rather than invented, so an admin who sets
# NPA_NC_CERT for a private CA or NPA_TIMEOUT_DAV for a slow disk keeps both
# working on this path as well.
_DEFAULT_TIMEOUT_SECONDS = 90.0
_DEFAULT_AA_VERSION = "2.2.0"


async def current_user_id(nc: AsyncNextcloudApp) -> str | None:
    """Return the user id AppAPI signed for this request, None when there is none.

    ``AsyncNextcloudApp.user`` is an async property, hence the await. For an ExApp
    session it resolves to the name that ``AppAPIAuthMiddleware`` already verified
    against the ``AUTHORIZATION-APP-API`` header, so this never reaches the
    network. An empty string means "no identity" and becomes None, because an
    empty user id must never look like a valid one to a caller.
    """
    user_id = await nc.user
    return user_id or None


def create_app_client() -> AsyncNextcloudApp:
    """Build an ExApp client from the AppAPI environment.

    Reads ``APP_ID``, ``APP_SECRET``, ``APP_VERSION`` and ``NEXTCLOUD_URL`` from
    the process environment, exactly like the running backend does. Only command
    line tools need this; inside a request the client arrives through
    ``Depends(anc_app)`` and must never be built by hand.
    """
    return AsyncNextcloudApp()


def gateway_url(file_id: int) -> str:
    """Absolute URL of the content gateway for one file id."""
    # The same normalisation the client library applies to NEXTCLOUD_URL, so a
    # value with a trailing slash or an index.php in it behaves identically here.
    base = os.environ.get("NEXTCLOUD_URL", "").removesuffix("/").removesuffix("/index.php").removesuffix("/")
    return base + GATEWAY_PATH.format(file_id=file_id)


def app_api_headers(header_user: str) -> dict[str, str]:
    """The headers AppAPI authenticates a call from an ExApp with.

    Deliberately the same set the client library puts on its own adapter: app id
    and version identify the caller, the base64 of ``user:secret`` is the
    credential, and ``OCS-APIRequest`` is what makes Nextcloud accept a call on
    an ``/ocs/`` route at all. ``AA-VERSION`` is informational and carries the
    library's own default when the environment does not name one.

    Built from the process environment, not read off the session object. The
    environment is the documented interface AppAPI hands the container, while the
    attribute that used to carry these headers is private API.
    """
    secret = os.environ.get("APP_SECRET", "")
    return {
        "AA-VERSION": os.environ.get("AA_VERSION", _DEFAULT_AA_VERSION),
        "EX-APP-ID": os.environ.get("APP_ID", ""),
        "EX-APP-VERSION": os.environ.get("APP_VERSION", ""),
        "AUTHORIZATION-APP-API": b64encode(f"{header_user}:{secret}".encode()).decode(),
        "OCS-APIRequest": "true",
    }


def _certificate_setting() -> bool | str:
    """Mirror NPA_NC_CERT: True, False, or a path to a CA bundle."""
    value = os.environ.get("NPA_NC_CERT", "True")
    if value.lower() in {"false", "0"}:
        return False
    if value.lower() in {"true", "1"}:
        return True
    return value


def _timeout() -> httpx.Timeout:
    """Mirror NPA_TIMEOUT_DAV, the file transfer timeout of the client library."""
    try:
        return httpx.Timeout(float(os.environ.get("NPA_TIMEOUT_DAV", _DEFAULT_TIMEOUT_SECONDS)))
    except ValueError:
        # An unparsable value disables timeouts in the client library too. Keeping
        # the same meaning is better than a surprise here.
        return httpx.Timeout(None)


def new_gateway_client() -> httpx.AsyncClient:
    """A client for the content gateway, transport configured like the library's.

    Redirects are not followed on purpose. A redirect that leaves the instance
    would carry the AppAPI credential to wherever it points.
    """
    return httpx.AsyncClient(verify=_certificate_setting(), timeout=_timeout(), follow_redirects=False)


async def _stream_file(
    client: httpx.AsyncClient,
    header_user: str,
    file_id: int,
    user_id: str,
    fp: IO[bytes],
) -> int | None:
    """Stream one gateway answer into the sink, return the byte count."""
    written = 0
    async with client.stream(
        "GET",
        gateway_url(file_id),
        params={"userId": user_id},
        headers=app_api_headers(header_user),
    ) as response:
        if response.status_code in _NOT_ACCESSIBLE_STATUS:
            return None
        if response.status_code >= _FIRST_ERROR_STATUS:
            # The body is deliberately not read. It may be an OCS error document,
            # it may be a page of HTML from a reverse proxy, and the status code
            # is the entire verdict either way.
            raise NextcloudException(response.status_code, reason=f"content gateway refused file id {file_id}")

        async for chunk in response.aiter_bytes(CHUNK_SIZE):
            written += len(chunk)
            # The sink is an ordinary file object, so this is blocking disk IO in
            # the middle of an async request. On a 4 GB box one large PDF would
            # otherwise stall every other request in the process, indexing and
            # search alike.
            await asyncio.to_thread(fp.write, chunk)
    return written


async def fetch_file_stream(
    nc: AsyncNextcloudApp,
    file_id: int,
    user_id: str,
    fp: IO[bytes],
    *,
    client: httpx.AsyncClient | None = None,
) -> int | None:
    """Read one file through the content gateway, return the number of bytes.

    Returns ``None`` when the gateway refuses the file for this user. That is a
    normal outcome, not an error: a run over a whole corpus must not stop because
    one file belongs to somebody else. Every other failure is raised, so a broken
    gateway can never be mistaken for a permission verdict.

    Three implementation notes, all load bearing.

    First, this does not go through the ``ocs`` entry point of the client library.
    That one parses every answer as JSON, unconditionally and with no switch for
    raw data, so the first real PDF would end in a decode error.

    Second, the request is an own streamed httpx call inside ``async with``, and
    not the library's ``download2stream``. Two reasons. The library holds the
    response open without a context manager, so an exception in the middle of a
    file, a cancelled request or a shutdown leaves the connection dangling in the
    pool. And it writes every block to the sink from the event loop, which turns
    a large file into a stall for everything else in the process; the write goes
    to a worker thread here. As a side effect this module no longer touches any
    private attribute of the library, only its documented environment.

    Third, ``client`` exists so that a caller with many files can hand in one
    pooled client instead of paying for a connection per file. Phase 2 does that
    from the indexing loop; a single call may leave it out and gets its own.
    """
    header_user = await nc.user
    if client is not None:
        return await _stream_file(client, header_user, file_id, user_id, fp)

    async with new_gateway_client() as owned_client:
        return await _stream_file(owned_client, header_user, file_id, user_id, fp)


# ---------------------------------------------------------------------------
# The work queue: take work, acknowledge it, hand it back, count it.
# ---------------------------------------------------------------------------
#
# Two properties of the four functions below are load bearing and neither of them
# is obvious from the code, so both are stated here once instead of four times.
#
# **The client is an argument and is never built here.** ``AsyncNextcloudApp``
# owns a connection pool, and the pool is the point: an initial index walks a
# hundred thousand files, and a client per file would pay a TCP and TLS setup per
# file plus, on the PHP side, a Nextcloud bootstrap including the AppAPI signature
# check. The shape is already in the repository: ``tools/read_corpus.py`` calls
# ``create_app_client`` exactly once and carries the client through the whole loop
# over all file ids. The poller of plan 02-10 does the same.
#
# **The path is a string literal inside the call, and it has to stay one.** The
# read-only gate (``tests/test_readonly_gate.py``) reads the path as an
# ``ast.Constant`` at the call site and compares it against its allowlist. Lifting
# these four paths into module constants would look tidier and would leave the
# gate with "an unknown path": a violation for the two writing calls, and a blind
# spot for all four. The duplication is deliberate and a test pins it.
#
# The two writing calls are the only writes this container performs against
# Nextcloud. They reach the two database tables the companion app owns and have no
# code path into the file system; the reasoning and the threat ids sit at
# OCS_WRITE_ALLOWLIST in the gate.


async def claim_documents(nc: AsyncNextcloudApp, *, limit: int, max_bytes: int) -> object:
    """Take a batch of queued files, at most ``limit`` of them and ``max_bytes`` big.

    Answers with a map of queue row id to source object. The row id is what has to
    come back on acknowledgement, and the source carries metadata only: the bytes
    of a file are a separate request through the content gateway, so this answer
    stays small even for a batch of large scans.

    Returned untyped on purpose. Turning the answer into work is the job of
    :mod:`findling.nc.queue`, which validates every field; a convenient type
    annotation here would claim a guarantee this boundary cannot give.
    """
    return await nc._session.ocs(
        "GET",
        "/ocs/v2.php/apps/findling/queues/documents",
        params={"n": limit, "max_bytes": max_bytes},
    )


async def ack_documents(
    nc: AsyncNextcloudApp,
    *,
    files: Sequence[int],
    failed: Sequence[Mapping[str, object]],
) -> object:
    """Acknowledge a batch: what is done, and what could not be processed and why.

    The second list is the return channel. Without it the status page would have
    to ask the container which files it could not process, which would be a second
    place holding the truth about the same fact, and the copy on the Nextcloud side
    is the one an admin can still read while the container is down.

    Nextcloud binds OCS parameters from the query string and from the request body
    alike, so this goes out as a DELETE with a JSON body and needs no POST
    override.
    """
    return await nc._session.ocs(
        "DELETE",
        "/ocs/v2.php/apps/findling/queues/documents",
        json={"files": list(files), "failed": [dict(entry) for entry in failed]},
    )


async def unlock_documents(nc: AsyncNextcloudApp, *, ids: Sequence[int]) -> object:
    """Hand rows back unprocessed, the graceful half of a shutdown.

    A container that is asked to stop returns what it holds, so a restart is
    productive at once instead of waiting out the lock timeout. Only a hard kill
    pays that timeout, which is the price of not losing anything after one.
    """
    return await nc._session.ocs(
        "POST",
        "/ocs/v2.php/apps/findling/queues/documents/unlock",
        json={"ids": list(ids)},
    )


async def queue_stats(nc: AsyncNextcloudApp) -> object:
    """Waiting, held right now, and how many files ended as failed."""
    return await nc._session.ocs(
        "GET",
        "/ocs/v2.php/apps/findling/queues/documents/stats",
    )
