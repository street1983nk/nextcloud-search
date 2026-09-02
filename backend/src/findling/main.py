"""Findling ExApp entry point: FastAPI application, AppAPI lifecycle, logging.

The lifespan registers the three routes AppAPI expects (``PUT /enabled``,
``GET /heartbeat``, ``POST /init``) through a single call into the boundary
module. ``enabled_handler`` is a coroutine on purpose: the handler registration
inspects it with ``asyncio.iscoroutinefunction``, and a synchronous handler only
warns today while it stops working in the next minor release of the client
library.

The startup log names the chosen binding mode. That single line is worth its
space: under HaRP the server binds a unix socket instead of a TCP port, and a
container that binds the wrong one looks perfectly healthy in its own log while
being unreachable from Nextcloud.
"""

import asyncio
import contextlib
import logging
import os
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from findling.api import resources
from findling.api.diagnose import ROUTER as DIAGNOSE_ROUTER
from findling.api.rates import ROUTER as RATES_ROUTER
from findling.api.search import ROUTER as SEARCH_ROUTER
from findling.api.snippets import ROUTER as SNIPPETS_ROUTER
from findling.api.status import ROUTER as STATUS_ROUTER
from findling.config import settings
from findling.nc.client import AppAPIAuthMiddleware, AsyncNextcloudApp, run_app, set_handlers
from findling.worker.poller import POLLER_STOP_SECONDS, Poller, default_poller
from findling.worker.reconcile import RECONCILE_STOP_SECONDS, Reconcile, default_reconcile

LOGGER = logging.getLogger("findling")

# The one indexing task of the process, held at module level because the AppAPI
# handler that arms and silences it takes no application object. It exists while
# the lifespan is up and is None outside it, which is also what keeps a test
# suite that enters the lifespan repeatedly from accumulating pollers.
_POLLER: Poller | None = None

# The second task, and the same reasoning: the AppAPI handler has to reach it to
# arm and silence it. It is None while the comparison is switched off, which is
# the difference between a task that does nothing and no task at all.
_RECONCILE: Reconcile | None = None

KNOWN_LOG_LEVELS = frozenset({"debug", "info", "warning", "error"})

# The AppAPI header is the only trusted source of identity, so a body that names
# a user is refused rather than ignored. Dropping the field silently would leave
# the caller believing the request ran as somebody else.
BODY_IDENTITY_REJECTED = "user identity is taken from the AppAPI header only"

# Field names that would name a user. Only these turn a rejected extra field into
# the security answer below; a body with a misspelled ``limitt`` is a typo and has
# to read like one.
IDENTITY_FIELDS = frozenset({"user", "userId", "user_id", "userid", "uid"})


def log_level() -> str:
    """Return the configured log level, falling back to info on anything unknown."""
    level = os.environ.get("FINDLING_LOG_LEVEL", "info").strip().lower()
    return level if level in KNOWN_LOG_LEVELS else "info"


def unusable_startup_variables() -> list[str]:
    """Return the environment variables that keep this process from starting.

    Only APP_PORT can be checked here, and only when there is no HaRP: the client
    library reads it while the server is still binding, with ``int(environ[...])``
    and no default, so a missing or non numeric value ends as a bare KeyError or
    ValueError several frames inside the library without naming the variable.
    Under HaRP the server binds HP_EXAPP_SOCK and never looks at the port at all.

    APP_ID, APP_SECRET, APP_VERSION and NEXTCLOUD_URL are deliberately not in
    here. They are read per request, so a missing one of those is a failing
    request with a clear message rather than a container that will not start.
    """
    if os.environ.get("HP_SHARED_KEY"):
        return []
    return [] if os.environ.get("APP_PORT", "").isdigit() else ["APP_PORT"]


def binding_mode() -> str:
    """Describe where the server will listen, without secrets."""
    if os.environ.get("HP_SHARED_KEY"):
        return f"unix socket {os.environ.get('HP_EXAPP_SOCK', '/tmp/exapp.sock')} (HaRP)"  # noqa: S108
    return f"tcp {os.environ.get('APP_HOST', '127.0.0.1')}:{os.environ.get('APP_PORT', 'unset')}"


def active_poller() -> Poller | None:
    """The poller of this process, None while the lifespan is not running."""
    return _POLLER


def active_reconcile() -> Reconcile | None:
    """The reconcile of this process, None while it is off or not running."""
    return _RECONCILE


async def enabled_handler(enabled: bool, nc: AsyncNextcloudApp) -> str:
    """Report the result of enabling or disabling the app; empty means success.

    Must be a coroutine. The registration helper checks that, and the synchronous
    path is scheduled for removal upstream.

    This is also where the two background tasks are armed and silenced. A disabled
    backend that keeps collecting work is the classic of the integration list: the
    container looks healthy in its own log while it drains the queue of an app the
    admin switched off. The reconcile is armed with the same call and for the same
    reason: a backend that is off but keeps reading the file list of the instance
    is the same mistake with a different verb.
    """
    del nc
    for task in (active_poller(), active_reconcile()):
        if task is None:
            continue
        if enabled:
            task.arm()
        else:
            task.silence()
    LOGGER.info("findling backend %s", "enabled" if enabled else "disabled")
    return ""


async def _guarded_reconcile(reconcile: Reconcile, stop_event: asyncio.Event) -> None:
    """Run the repair task and let nothing out of it but a log line.

    ``Reconcile.run`` already survives an exception inside a round. This is the
    layer above it, for the failure that ends the loop itself. The reason it
    exists at all is a ranking: the search is the part a user sees, the indexing
    is what keeps it worth using, and the comparison is repair work that both of
    them are fine without for a while. So a broken repair must never end the
    process and never end the poller, and only the type name is logged, because a
    traceback here would carry whatever a library put into its message.
    """
    try:
        await reconcile.run(stop_event)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        kind_of_failure = type(error).__name__
        LOGGER.error("the reconcile task ended in an unexpected %s; search and indexing continue", kind_of_failure)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Register the AppAPI routes once, start the one poller, stop it in order."""
    # One task per process, and the AppAPI handler that arms it is given no
    # application object, so the task has to be reachable from module level.
    global _POLLER
    logging.basicConfig(level=log_level().upper())
    # set_handlers adds routes to the application object, and the application
    # object outlives the lifespan: one process can start it once, a test suite
    # enters and leaves it many times on the same global APP. Without this guard
    # every entry adds a second /enabled, /heartbeat and /init, which is a
    # growing router that resolves by whichever copy happens to be first.
    if not getattr(app.state, "findling_handlers_registered", False):
        # The upstream parameter type still admits the synchronous client class,
        # which disappears in the next minor release. Narrowing our handler to
        # the async one is deliberate, and the resulting contravariance complaint
        # is the price for not carrying the deprecated type into our own
        # signatures.
        set_handlers(app, enabled_handler)  # pyright: ignore[reportArgumentType]
        app.state.findling_handlers_registered = True
    LOGGER.info("findling backend starting, binding mode: %s", binding_mode())

    # Stated once at startup, and decided nowhere. An existing index whose
    # version marks differ from the ones this build produces answers queries with
    # a different tokenisation than it was written with, so hits disappear
    # without anything saying why. What follows from that, resetting one storage
    # or rebuilding everything, is the poller's decision; the only unacceptable
    # outcome is nobody hearing about it. In a worker thread because it opens a
    # database and may read the constituent list, neither of which belongs on the
    # event loop while the server is still coming up.
    await asyncio.to_thread(resources.report_version_drift)

    # Exactly one indexing task, started silenced. It opens neither the index nor
    # the state database before it is armed, so a container that is deployed but
    # not yet enabled holds no tantivy lock and touches no volume.
    stop_indexing = asyncio.Event()
    _POLLER = default_poller()
    indexing = asyncio.create_task(_POLLER.run(stop_indexing))

    # The second task, and only when the comparison is switched on. Not starting
    # it is different from starting one that returns at once: a task that exists
    # holds a state connection sooner or later, and an admin who switched the
    # comparison off gets to see one line saying so rather than nothing.
    global _RECONCILE
    stop_reconcile = asyncio.Event()
    repairing: asyncio.Task[None] | None = None
    if settings().reconcile_enabled:
        _RECONCILE = default_reconcile()
        repairing = asyncio.create_task(_guarded_reconcile(_RECONCILE, stop_reconcile))
    else:
        LOGGER.info("findling reconcile is switched off, the index follows events only")

    try:
        yield
    finally:
        stop_indexing.set()
        stop_reconcile.set()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(asyncio.shield(indexing), timeout=POLLER_STOP_SECONDS)
        if not indexing.done():
            # Over the budget. The pass is somewhere inside a worker thread and
            # will not come back in time; the rows it holds fall back to the lock
            # timeout, which is exactly what that timeout is for.
            indexing.cancel()
            await asyncio.gather(indexing, return_exceptions=True)
        # Hand back what the container is holding, so a restart is productive at
        # once instead of waiting the rows out.
        with contextlib.suppress(Exception):
            await _POLLER.unlock_held()
        await _POLLER.aclose()
        _POLLER = None

        if repairing is not None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(asyncio.shield(repairing), timeout=RECONCILE_STOP_SECONDS)
            if not repairing.done():
                # A slice is bounded work, so the budget is generous. Over it the
                # round is inside a worker thread and the only thing it could
                # still have written is its own bookmark, which may be lost.
                repairing.cancel()
                await asyncio.gather(repairing, return_exceptions=True)
        if _RECONCILE is not None:
            await _RECONCILE.aclose()
            _RECONCILE = None


APP = FastAPI(lifespan=lifespan)
# /heartbeat is always exempt from this middleware, which is what lets AppAPI
# probe the container before any request is signed.
APP.add_middleware(AppAPIAuthMiddleware)
# The routers are mounted behind the middleware, so no route of this app can
# ever be reached without a verified AppAPI header.
APP.include_router(SEARCH_ROUTER)
APP.include_router(SNIPPETS_ROUTER)
APP.include_router(STATUS_ROUTER)
APP.include_router(RATES_ROUTER)
APP.include_router(DIAGNOSE_ROUTER)


def smuggles_identity(errors: Sequence[Mapping[str, Any]]) -> bool:
    """True when a rejected extra field tried to name the user of the request.

    Only the field name decides. Any other rejected extra field is an ordinary
    validation error, and calling it an identity smuggling attempt would send
    whoever misspelled ``limit`` looking for a security problem.
    """
    for error in errors:
        if error.get("type") != "extra_forbidden":
            continue
        location = error.get("loc") or ()
        if location and str(location[-1]) in IDENTITY_FIELDS:
            return True
    return False


@APP.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Turn a body that names a user into 400 and keep 422 for everything else.

    ``SearchRequest`` forbids extra fields, so a body carrying ``userId`` fails
    validation instead of reaching the handler. The default answer would be 422,
    which reads like a typo. 400 with an explicit message states what actually
    happened: the request tried to choose its own identity.

    Every other rejected field keeps the 422 including the field name, so a
    misspelled field is diagnosable instead of being accused of an attack.
    """
    del request
    errors = exc.errors()
    if smuggles_identity(errors):
        return JSONResponse(status_code=400, content={"detail": BODY_IDENTITY_REJECTED})
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(errors)})


if __name__ == "__main__":
    _unusable = unusable_startup_variables()
    if _unusable:
        raise SystemExit(
            "findling: cannot start, missing or not a number in the environment: "
            + ", ".join(_unusable)
            + ". AppAPI sets these when it deploys the container; a manual run has to set them by hand."
        )
    run_app("findling.main:APP", log_level=log_level())
