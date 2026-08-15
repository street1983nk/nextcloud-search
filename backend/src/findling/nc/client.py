"""The only module in Findling that touches nc_py_api.

Every other module imports the AppAPI building blocks from here, never from
nc_py_api itself. Two reasons, both load bearing:

1. An nc_py_api update hits exactly one file. The sync API disappears in 0.31.0,
   so the async entry points re-exported below are the ones with a future.
2. The read-only invariant (IDX-07) is only statically checkable because of this
   seam. "No other module imports nc_py_api" is a property a parser can verify,
   "nobody writes anywhere" is not. Gate A enforces invariant 1 against this
   module path and invariant 2 against the identifiers inside it.

Consequently the writing entry points of ``nc_py_api.files`` and the
impersonation entry point of ``AsyncNextcloudApp`` are deliberately absent from
the re-export list: a caller cannot reach what the boundary does not hand out.
"""

from typing import IO

from nc_py_api import AsyncNextcloudApp, NextcloudException
from nc_py_api.ex_app import AppAPIAuthMiddleware, anc_app, run_app, set_handlers

__all__ = [
    "CHUNK_SIZE",
    "GATEWAY_PATH",
    "NC_PY_API_VERIFIED_VERSION",
    "AppAPIAuthMiddleware",
    "AsyncNextcloudApp",
    "NextcloudException",
    "anc_app",
    "create_app_client",
    "current_user_id",
    "fetch_file_stream",
    "run_app",
    "set_handlers",
]

# The release the private call inside fetch_file_stream was read against. It is
# named here so that an upgrade has one obvious place to be re-verified.
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


class _CountingSink:
    """Passes bytes through to the caller's file object and counts them.

    Counting here instead of asking the file object afterwards keeps the helper
    usable with sinks that cannot be seeked, and it is the reason the byte count
    in the report is the number that actually crossed the wire.
    """

    def __init__(self, target: IO[bytes]) -> None:
        self._target = target
        self.written = 0

    def write(self, data: bytes) -> int:
        self.written += len(data)
        return self._target.write(data)


async def fetch_file_stream(nc: AsyncNextcloudApp, file_id: int, user_id: str, fp: IO[bytes]) -> int | None:
    """Read one file through the content gateway, return the number of bytes.

    Returns ``None`` when the gateway refuses the file for this user. That is a
    normal outcome, not an error: a run over a whole corpus must not stop
    because one file belongs to somebody else. Every other failure is raised, so
    a broken gateway can never be mistaken for a permission verdict.

    Two implementation notes, both load bearing.

    First, this does not go through ``ocs``. ``AsyncNcSessionBasic.ocs`` parses
    every answer with ``loads(response.text)``, unconditionally and with no
    switch for raw data, so the first real PDF would end in a JSONDecodeError.
    The streaming entry point below writes the body block by block instead.

    Second, ``nc._session`` is private API of nc_py_api, read against
    :data:`NC_PY_API_VERIFIED_VERSION`. The dependency is deliberate and
    documented (assumptions log A4); keeping it inside this one function is what
    limits an nc_py_api upgrade to a single place. The fallback, should the call
    ever disappear, is an own httpx client with a self built AppAPI auth header.
    """
    sink = _CountingSink(fp)
    try:
        await nc._session.download2stream(
            GATEWAY_PATH.format(file_id=file_id),
            sink,
            dav=False,
            params={"userId": user_id},
            chunk_size=CHUNK_SIZE,
        )
    except NextcloudException as error:
        if error.status_code in _NOT_ACCESSIBLE_STATUS:
            return None
        raise
    return sink.written
