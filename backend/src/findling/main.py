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

import logging
import os
from collections.abc import AsyncIterator, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from findling.api.search import ROUTER
from findling.nc.client import AppAPIAuthMiddleware, AsyncNextcloudApp, run_app, set_handlers

LOGGER = logging.getLogger("findling")

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


def binding_mode() -> str:
    """Describe where the server will listen, without secrets."""
    if os.environ.get("HP_SHARED_KEY"):
        return f"unix socket {os.environ.get('HP_EXAPP_SOCK', '/tmp/exapp.sock')} (HaRP)"  # noqa: S108
    return f"tcp {os.environ.get('APP_HOST', '127.0.0.1')}:{os.environ.get('APP_PORT', 'unset')}"


async def enabled_handler(enabled: bool, nc: AsyncNextcloudApp) -> str:
    """Report the result of enabling or disabling the app; empty means success.

    Must be a coroutine. The registration helper checks that, and the synchronous
    path is scheduled for removal upstream.
    """
    del nc
    LOGGER.info("findling backend %s", "enabled" if enabled else "disabled")
    return ""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Register the AppAPI routes and announce the binding mode."""
    logging.basicConfig(level=log_level().upper())
    # The upstream parameter type still admits the synchronous client class,
    # which disappears in the next minor release. Narrowing our handler to the
    # async one is deliberate, and the resulting contravariance complaint is the
    # price for not carrying the deprecated type into our own signatures.
    set_handlers(app, enabled_handler)  # pyright: ignore[reportArgumentType]
    LOGGER.info("findling backend starting, binding mode: %s", binding_mode())
    yield


APP = FastAPI(lifespan=lifespan)
# /heartbeat is always exempt from this middleware, which is what lets AppAPI
# probe the container before any request is signed.
APP.add_middleware(AppAPIAuthMiddleware)
# The router is mounted behind the middleware, so no search route can ever be
# reached without a verified AppAPI header.
APP.include_router(ROUTER)


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
    run_app("findling.main:APP", log_level=log_level())
