"""Findling ExApp entry point.

Skeleton for the RED step of plan 01-04 task 1: the module exists so the test
suite can import it, but neither the AppAPI handshake nor the middleware are
wired up yet. The GREEN step replaces this placeholder.
"""

from fastapi import FastAPI

APP = FastAPI()


async def enabled_handler(enabled: bool, nc: object) -> str:
    """Placeholder handler. The GREEN step reports success and logs the event."""
    del enabled, nc
    return "not implemented"
