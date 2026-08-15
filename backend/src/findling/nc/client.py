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

from nc_py_api import AsyncNextcloudApp
from nc_py_api.ex_app import AppAPIAuthMiddleware, anc_app, run_app, set_handlers

__all__ = [
    "AppAPIAuthMiddleware",
    "AsyncNextcloudApp",
    "anc_app",
    "current_user_id",
    "run_app",
    "set_handlers",
]


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
