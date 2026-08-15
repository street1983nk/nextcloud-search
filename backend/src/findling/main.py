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
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from findling.nc.client import AppAPIAuthMiddleware, AsyncNextcloudApp, run_app, set_handlers

LOGGER = logging.getLogger("findling")

KNOWN_LOG_LEVELS = frozenset({"debug", "info", "warning", "error"})


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

# The search router of task 2 is included right here, after the middleware, so
# that no route can ever be reachable without a verified AppAPI header.


if __name__ == "__main__":
    run_app("findling.main:APP", log_level=log_level())
