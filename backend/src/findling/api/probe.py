"""POST /probe and GET /probe/state: the pre-check of a profile change (PRUEF-01).

The check itself lives in :mod:`findling.worker.probe_run`; this module is its
door. POST starts one check and answers at once, because a check runs for
minutes and no caller waits for its verdict (D-27-04): 202 with the id of the
check, 409 while another check runs (with the id of that one) or while the
index directory is rebuilt, 503 while no lifespan holds a check at all. GET
reads the probe state of this process and measures nothing: a poll of the admin
page must not become a second measurement (T-07-04).

Both answers carry codes, numbers and an id, and nothing else: no path, no URL,
no text. Every word of the state answer comes out of a closed set of
:mod:`findling.probe`, so the PHP side can say it without inventing words
(D-27-20, T-27-37).

The body of POST is two closed sets as well, profile and precision as pydantic
literals with extra fields forbidden, so a foreign value is a 422 before the
check is asked anything (T-27-35). The single flight is the check's own: its
start lock answers busy for a second start (T-27-36).

Declared with access level ADMIN in appinfo/info.xml, which guards the AppAPI
proxy path in ``ExAppProxyController::passesExAppProxyRouteAccessLevelCheck``.
The path this app actually uses is ``PublicFunctions::exAppRequest``, and that one
does not pass through the proxy's access level check: the effective guard there is
the admin-only PHP route in front of it. The access level stays declared as
defence in depth for the path this app does not walk (pitfall 10, T-27-34).
"""

import logging
from typing import Annotated, Literal, Protocol

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from findling import probe
from findling.nc.client import AsyncNextcloudApp, anc_app, current_user_id

LOGGER = logging.getLogger("findling.api.probe")

ROUTER = APIRouter()

# The answer of a start while no lifespan holds a check. A state word of this
# route and not one of findling.probe: the check never reports it, only its door.
STATE_UNAVAILABLE = "unavailable"


class ProbeStarter(Protocol):
    """What the door needs of the check: its start."""

    async def start(self, profile_name: str, precision: str) -> tuple[str, str]: ...


def probe_run() -> ProbeStarter | None:
    """The check of the running lifespan, None outside it.

    A dependency rather than a direct read, so that a test replaces it. The
    import is deferred because findling.main mounts this router.
    """
    from findling import main

    return main.active_probe_run()


class ProbeRequest(BaseModel):
    """The target of a check, two closed sets and nothing else."""

    model_config = ConfigDict(extra="forbid")

    profile: Literal["economy", "standard", "performance"]
    precision: Literal["int8", "fp32"]


class ProbeStateResponse(BaseModel):
    """The running or the last check of this process.

    Every field defaults, so the resting state has the same shape as a check
    that just ended. ``numbers`` carries only keys out of
    ``findling.probe.NUMBER_KEYS``, and only those the sentence of the cause
    needs. The two moments are epoch seconds, nought while not reached.
    """

    id: str = ""
    state: str = probe.STATE_IDLE
    step: str = ""
    bytesDone: int = 0
    bytesTotal: int = 0
    verdict: str = ""
    cause: str = ""
    numbers: dict[str, int] = Field(default_factory=dict)
    targetProfile: str = ""
    targetPrecision: str = ""
    fp32Fetched: bool = False
    fp32Deleted: bool = False
    startedAt: int = 0
    finishedAt: int = 0


def _moment(value: float | None) -> int:
    return 0 if value is None else max(0, int(value))


def state_answer(snap: probe.ProbeSnapshot) -> ProbeStateResponse:
    """The snapshot as the wire spells it, field by field and never spread."""
    return ProbeStateResponse(
        id=snap.id,
        state=snap.state,
        step=snap.step,
        bytesDone=snap.bytes_done,
        bytesTotal=snap.bytes_total,
        verdict=snap.verdict,
        cause=snap.cause,
        numbers={key: value for key, value in snap.numbers.items() if key in probe.NUMBER_KEYS},
        targetProfile=snap.target_profile,
        targetPrecision=snap.target_precision,
        fp32Fetched=snap.fp32_fetched,
        fp32Deleted=snap.fp32_deleted,
        startedAt=_moment(snap.started_at),
        finishedAt=_moment(snap.finished_at),
    )


@ROUTER.post("/probe")
async def start_probe(
    body: ProbeRequest,
    nc: Annotated[AsyncNextcloudApp, Depends(anc_app)],
    run: Annotated[ProbeStarter | None, Depends(probe_run)],
) -> JSONResponse:
    """Start one check and answer at once; the verdict comes through GET /probe/state."""
    user_id = await current_user_id(nc)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="no user in the AppAPI header")
    if run is None:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"state": STATE_UNAVAILABLE})
    try:
        outcome, probe_id = await run.start(body.profile, body.precision)
    # Deliberately every exception, the type name only: a start that broke is
    # a container that cannot check right now, never a 500 with a message.
    except Exception as error:
        LOGGER.error("a pre-check could not be started, an %s", type(error).__name__)
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"state": STATE_UNAVAILABLE})
    if outcome == probe.START_BUSY:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"state": probe.START_BUSY, "id": probe_id})
    if outcome == probe.START_REBUILDING:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"state": probe.START_REBUILDING})
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"id": probe_id})


@ROUTER.get("/probe/state")
async def read_probe_state() -> ProbeStateResponse:
    """The probe state of this process; always 200, reading changes nothing."""
    return state_answer(probe.snapshot())


__all__ = ["ROUTER", "STATE_UNAVAILABLE", "ProbeRequest", "ProbeStateResponse", "probe_run", "state_answer"]
