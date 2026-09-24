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

The lifespan also decides whether this start indexes at all. AppAPI sends
``PUT /enabled?enabled=1`` once, when it enables the ExApp, and never again, so
the arming cannot come from that call alone: a restart of the machine or a
restart by the docker policy after an out of memory kill would leave a container
that answers searches and never indexes another file (DI-05-36). The enable is
therefore remembered on the persistent volume, and the read of that mark sits in
the lifespan with the whole reasoning beside it.

One thing outranks that mark: whose volume this is (DI-06.1-22). AppAPI names
the data volume after the app alone, so two Nextcloud instances on one docker
service mount the same one. A start that finds the marker of another instance
keeps the indexing off and says so, and the server stays up so that the status
page can carry the reason, which is the shape every degraded verdict of this
app has.
"""

import asyncio
import contextlib
import logging
import os
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from typing import Any, Final

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
from findling.embed.engine import release_if_idle, warm, warm_wanted
from findling.index.rebuild import MARKS_A_REBUILD_ANSWERS, rebuild_the_index, recover_the_index_directories
from findling.instance import claim_the_volume, volume_is_shared
from findling.nc.client import AppAPIAuthMiddleware, AsyncNextcloudApp, run_app, set_handlers
from findling.store.repo import open_read_only, open_store
from findling.worker.poller import POLLER_STOP_SECONDS, Poller, _pause, default_poller
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

# How finely the container notices that the idle span has run out. It is the
# resolution of the idle clock and not the span itself: the smallest span an
# admin may configure is 60 s, so an unload lands within less than half of the
# shortest permitted span of the moment it falls due, and a tick with nothing to
# do costs one reading of a clock.
RELEASE_TICK_SECONDS: Final = 30.0

# How long the shutdown waits for the release task before it stops waiting. A
# tick holds one to_thread call at most, and the longest of those is a warm run.
RELEASE_STOP_SECONDS: Final = 5.0

# How long the shutdown waits for the rebuild task, and the figure is a band and
# not a run. A whole rebuild is hours on the box this project targets, and a
# container that made its orchestrator wait for one is a container the
# orchestrator kills, which costs the ordered shutdown of the three other tasks
# as well (T-18-09-03). A band is 500 documents, it ends in a commit, and what is
# committed is what the next start resumes in, so the budget only has to cover
# the band that is running plus a reserve for a slow volume. 30 s is the figure
# the indexing pass gets for one claim, measured against the 683 documents per
# second of 2026-09-24, and the band run is asked to stop between two bands
# anyway: this timeout is the answer to a band that hangs and not the ordinary
# way out of a run.
REBUILD_STOP_SECONDS: Final = 30.0

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


def _remember_the_enable() -> None:
    """Leave the mark that lets the next start of this container arm itself.

    A failure here is a warning and never an error to AppAPI. The enable itself
    has succeeded at this point, and refusing it because a file could not be
    written would trade a container that forgets its state across a restart for
    one that cannot be switched on at all. Only the class name of the failure is
    logged, by the rule of this module: the message of an OSError carries the
    path it was raised on, and the path of the volume is not ours to print.

    The root is not created here, and that is a decision rather than an
    oversight. This module is the one that holds an AsyncNextcloudApp, so Gate A
    judges a directory creating call in it by the same rule as a write into a
    Nextcloud node, and the exemption the four local modules have does not carry
    over to this one. AppAPI creates the volume before it starts the container,
    so the directory is there in every deployment; where it is not, the touch
    fails, the warning says so, and the next start comes up silenced, which is
    the state this container was in before the mark existed.
    """
    try:
        settings().armed_marker.touch()
    except OSError as error:
        LOGGER.warning("the enable could not be written to the volume, an %s", type(error).__name__)


def _forget_the_enable() -> None:
    """Remove the mark, so a container that was switched off comes up switched off."""
    try:
        settings().armed_marker.unlink(missing_ok=True)
    except OSError as error:
        LOGGER.warning("the disable could not be written to the volume, an %s", type(error).__name__)


def _was_enabled_before_this_start() -> bool:
    """True when this container was already enabled when it last stopped.

    ``is_file`` answers False for everything it cannot stat, a volume that is not
    there yet and one that cannot be read alike, and that is exactly the answer
    that belongs here: a container that cannot read its own mark starts silenced,
    the way every container started before this mark existed.
    """
    return settings().armed_marker.is_file()


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

    The mark on the volume is written before the arming and removed after the
    silencing, and the order is the whole safety of it. A crash between the two
    steps then leaves a mark and no running task, which the next start repairs by
    arming; the other order would leave a running task and no mark, which no
    start repairs at all.
    """
    del nc
    if enabled:
        _remember_the_enable()
    # The second half of the shared volume guard (DI-06.1-22), and without it
    # the first half would be decoration. AppAPI deploys the container, the
    # lifespan finds the foreign marker, and then this call arrives and arms the
    # poller anyway: that is the exact order of a fresh registration on a docker
    # service that already carries another instance's volume, which is the
    # constellation the guard exists for.
    #
    # The enable itself is not refused. Its return value is an error text to
    # AppAPI, and a failing enable would leave an admin with an app that cannot
    # be switched on and one line to explain it. The mark is written, so the
    # start after the volume has been sorted out arms by itself.
    #
    # Read here rather than carried over from the lifespan, because a volume can
    # be shared after the start as well: the other instance registers second.
    shared_volume = enabled and volume_is_shared()
    if shared_volume:
        LOGGER.warning(
            "the enable is remembered but nothing is armed: this volume belongs to another Nextcloud instance, "
            "see docs/uninstall.md"
        )
    for task in (active_poller(), active_reconcile()):
        if task is None:
            continue
        if not enabled:
            task.silence()
        elif not shared_volume:
            task.arm()
    if not enabled:
        _forget_the_enable()
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


async def _release_when_idle(stop_event: asyncio.Event) -> None:
    """Let go of both memory holders once nothing has embedded for the span.

    The third long lived task of the lifespan, built like the two beside it and
    created only where ``embed_idle_release_seconds`` is switched on.

    **Not in the idle branch of the poller.** A silenced poller waits in
    ``run()`` on its armed event and never enters ``run_once`` again
    (``poller.py:543-545``), and the container that does not index and is
    searched now and then is exactly the one the unload is built for.

    **Every blocking call goes through** ``asyncio.to_thread``. ``gc.collect()``
    and ``malloc_trim(0)`` block, a load blocks, and a blocked loop is a
    container that stops answering ``/heartbeat`` while its own log looks
    perfectly healthy. That is the house rule written out at the head of
    ``worker/poller.py`` and in ``run_once`` (T-14-23).

    **Warming and unloading never share a tick.** The ``continue`` behind the
    warm run is the whole guard: without it the tick that has just paid for the
    load pair would throw it away two lines later.

    **The cutter is let go only behind a release that really happened.** Both
    holders fall together (MEM-02) and the order of the two is not free:
    :func:`~findling.embed.engine.release_if_idle` carries the clock and the
    identity check, :meth:`~findling.worker.poller.Poller.release_cutter`
    carries no span of its own. A ``release_cutter`` without a release in front
    of it would throw the cutter away after every quiet stretch, including the
    ones in which the search side embedded a moment ago.

    ``_pause`` is imported out of ``worker/poller.py`` although it is private,
    and that is the smaller of the two prices. A second copy of those three
    lines would be a second truth about the stop behaviour of this container,
    and the alternative of making it public is a change to a module this plan
    does not otherwise touch.
    """
    while not stop_event.is_set():
        await _pause(RELEASE_TICK_SECONDS, stop_event)
        if stop_event.is_set():
            # The pause returns at once when the stop arrives, and nothing below
            # is worth doing during a shutdown. A warm run started here would be
            # a load nobody gets to use, and the worker thread carrying it would
            # hold the exit of the process for seconds (T-14-26).
            break
        try:
            ttl_seconds = settings().embed_idle_release_seconds
            if warm_wanted():
                await asyncio.to_thread(warm)
                continue
            poller = active_poller()
            if poller is not None and poller.busy:
                # Pitfall 3. Letting go between two batches means paying for the
                # weights again seconds later, the unload turns from a saving
                # into a cost over a full pass, and nothing anywhere turns red.
                continue
            # No poller at all means no pass can be running, so the absence
            # answers the same question the property does.
            if await asyncio.to_thread(release_if_idle, ttl_seconds) and poller is not None:
                await asyncio.to_thread(poller.release_cutter)
        except asyncio.CancelledError:
            # Ahead of the general branch, exactly like _guarded_reconcile: a
            # task that was cancelled must not read as an unexpected failure.
            raise
        except Exception as error:
            # The tick failed, the task did not. Only the type name, by the rule
            # of this module, and the wording says which of the two ended so
            # that nobody goes looking for a task that is still running.
            kind_of_failure = type(error).__name__
            LOGGER.error(
                "a tick of the release task ended in an unexpected %s; the next tick runs, "
                "search and indexing continue",
                kind_of_failure,
            )


def _silence_the_poller() -> None:
    """Stop the indexing task from writing into the index the rebuild reads.

    Handed to :func:`findling.index.rebuild.rebuild_the_index` as a callback, so
    that the index package never has to import the worker package: the poller is
    already the caller of everything ``findling.index`` hands out, and an import
    in the other direction would close that circle.

    A container without a poller is not a fault here. The task only exists inside
    the lifespan, and a rebuild that outlived it has nothing left to silence.
    """
    poller = active_poller()
    if poller is not None:
        poller.silence()


def _arm_the_poller() -> None:
    """Let the indexing task collect work again, unless the app was switched off.

    The condition is the whole reason this is not simply ``poller.arm`` handed
    over as it stands. A rebuild runs for hours, an admin can disable the app
    while it does, and the disable removes the mark on the volume. Arming
    afterwards would leave an installation with a backend that is off in
    Nextcloud and indexing in the container, which is the failure the mark exists
    against with the two sides swapped.
    """
    poller = active_poller()
    if poller is not None and _was_enabled_before_this_start():
        poller.arm()


def _rebuild_is_due() -> bool:
    """True when the marks of the existing index ask for a directory rebuild.

    Only the two marks a rebuild can do anything about count
    (:data:`findling.index.rebuild.MARKS_A_REBUILD_ANSWERS`). A moved word list
    or a moved tantivy banner is a real drift with a different remedy, the crawl
    that reads the files again, and a band run started for one of those would
    carry the old text over and leave the drift exactly where it was.

    Everything here is a read, and a missing database is a container that has
    never indexed: there is nothing to carry over, and the first pass writes the
    current schema anyway.
    """
    resolved = settings()
    if not resolved.state_db.is_file():
        return False
    try:
        store = open_read_only(resolved.state_db)
    except OSError as error:
        LOGGER.warning("the state database could not be read for the rebuild question, an %s", type(error).__name__)
        return False
    try:
        return bool(MARKS_A_REBUILD_ANSWERS.intersection(resources.version_drift(store)))
    finally:
        store.close()


def _run_the_rebuild(should_stop: Callable[[], bool]) -> str:
    """Open the one writing handle the rebuild needs, run it, hand the handle back.

    The store is opened here and not inside the rebuild, because a module that
    opened a database of its own could keep a progress record beside the index,
    and a second record is the one that can disagree with the first. The file is
    never created by this call: :func:`_rebuild_is_due` has already answered
    False for a volume without one, so the poller stays the only seeder of the
    version marks.

    Blocking from the first line to the last, which is why nothing calls it
    outside :func:`asyncio.to_thread`.
    """
    store = open_store(settings().state_db)
    try:
        return rebuild_the_index(
            store,
            silence=_silence_the_poller,
            arm=_arm_the_poller,
            drop_read_side=resources.reset_read_side,
            should_stop=should_stop,
        )
    finally:
        store.close()


async def _rebuild_the_index_directory(stop_event: asyncio.Event) -> None:
    """The fourth long lived task: one rebuild, led from here and run in a thread.

    Built like the three beside it, down to the error handling, and created only
    where the marks ask for it.

    **Not a loop.** The other three tick; this one runs once and ends, because a
    rebuild is a one off answer to a drift and the marks it writes are what keeps
    the next start from doing it again. A task that ended is a task whose
    ``done()`` is True, which is exactly what the shutdown waits for.

    **Every blocking call goes through** ``asyncio.to_thread``. The run opens two
    index directories, writes the whole index a second time and renames
    directories, for minutes to hours. On the event loop that is a container that
    stops answering ``/heartbeat`` while its own log looks perfectly healthy, and
    AppAPI takes it for dead long before the pass is through (T-14-23).

    **The stop event travels in as a predicate** rather than as something to
    await. The worker thread cannot await, and the band run is only ever
    interrupted between two bands, so the one question it has to be able to ask
    is whether the container is going down.

    ``except asyncio.CancelledError: raise`` stands ahead of the general branch,
    exactly as in the two tasks above, and the general branch logs the type name
    only: a rebuild that failed must not take the process with it, because the
    old directory is still in place and search and indexing both go on working
    out of it (T-18-09-02).
    """
    try:
        verdict = await asyncio.to_thread(_run_the_rebuild, stop_event.is_set)
        LOGGER.info("the index rebuild ended: %s", verdict)
    except asyncio.CancelledError:
        raise
    except Exception as error:
        kind_of_failure = type(error).__name__
        LOGGER.error(
            "the index rebuild ended in an unexpected %s; the old index directory is still in place, "
            "search and indexing continue",
            kind_of_failure,
        )


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

    # Whose volume this is (DI-06.1-22). Asked before anything is read out of
    # it, because everything below this line assumes the volume belongs to this
    # instance: AppAPI names it after the app alone, so two Nextclouds on one
    # docker service share it, and the ordinary consequence is that the
    # unregister of one deletes the index of the other.
    #
    # In a worker thread for the reason the drift report is: it reads and may
    # write a file, and neither belongs on the event loop while the server is
    # still coming up.
    #
    # A shared volume is degraded and not fatal, exactly like the absent model
    # of plan 06.1-17: the server stays up so that the status page can show the
    # reason, and only the indexing is kept off. Anything stronger would be a
    # container that cannot report the one thing it found out.
    shared_volume = await asyncio.to_thread(claim_the_volume)
    if shared_volume.other:
        LOGGER.warning(
            "this volume already carries the marker of another Nextcloud instance (%s, this container is %s); "
            "two instances on one docker service share it, indexing stays off, see docs/uninstall.md",
            shared_volume.other,
            shared_volume.own,
        )
    else:
        # What a hard abort left behind, read and put in order before anything
        # opens it (T-18-08-01). Between the two renames of the directory swap
        # the volume holds no directory called ``index`` at all, and a container
        # that started into that state would open an empty one, answer every
        # search with nothing and report success while doing it.
        #
        # Before the tasks are created, and that order is the point. A poller
        # armed onto half a volume does not find the fault, it adds to it: it
        # opens whatever directory is there, writes into it and commits, and the
        # clean up path would afterwards be deciding about a state that two
        # writers had already touched.
        #
        # In a worker thread because it stats directories and may rename or
        # remove one, and skipped on a shared volume for the reason the drift
        # report is skipped: those directories belong to another instance.
        await asyncio.to_thread(recover_the_index_directories)

        # Stated once at startup, and decided nowhere. An existing index whose
        # version marks differ from the ones this build produces answers queries
        # with a different tokenisation than it was written with, so hits
        # disappear without anything saying why. What follows from that,
        # resetting one storage or rebuilding everything, is the poller's
        # decision; the only unacceptable outcome is nobody hearing about it. In
        # a worker thread because it opens a database and may read the
        # constituent list, neither of which belongs on the event loop while the
        # server is still coming up.
        #
        # Skipped on a shared volume, and that is the same decision as the one
        # about the indexing: the marks in that state describe the index of
        # another instance, and a reindex banner about somebody else's index is
        # noise pointing the wrong way.
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

    # The third task, and only where the unload is switched on. There is no else
    # branch with a log line here, and that is a decision rather than an
    # oversight: the factory setting of the span is off, and a line at every
    # start about a feature nobody switched on is noise. Nobody should add one
    # later for symmetry with the reconcile block above. The reconcile is on by
    # default, which is what makes its switched off line worth its space.
    stop_release = asyncio.Event()
    releasing: asyncio.Task[None] | None = None
    if settings().embed_idle_release_seconds > 0:
        releasing = asyncio.create_task(_release_when_idle(stop_release))
        LOGGER.info("findling releases the embedding engine after an idle span")

    # The mark from the last enable, read after both tasks exist so that one
    # decision arms both of them, exactly like the AppAPI handler does.
    #
    # This reverses a decision that was taken on purpose, so the whole reasoning
    # belongs here. The container used to start silenced under every
    # circumstance, because a container that is deployed but not yet enabled must
    # hold no tantivy lock and must touch no volume. That property is untouched:
    # without a mark nothing is armed, and a container that was never enabled has
    # no mark. The mark only changes the case of a container that WAS enabled,
    # and holding the lock is right in exactly that case.
    #
    # What it buys is DI-05-36. The arming used to come from PUT /enabled and
    # from nothing else, and AppAPI sends that call once, when it enables the
    # ExApp; none of its three background jobs ever sends it again. So every
    # start that AppAPI did not order, a restart of the machine after an update
    # and a restart by the docker policy after an out of memory kill, left a
    # container that answers searches, reports its version, looks reachable on
    # the status page and never indexes another file. Measured on the box: ten
    # minutes and forty seconds, zero passes of the poller, 130 rows waiting.
    #
    # The objection to a mark is the stale state: the app was disabled while this
    # container was not running, so the mark is still there and this start arms a
    # backend that Nextcloud considers off. It does not carry. A disabled
    # companion app has no routes, the queue does not answer, and the poller goes
    # into the retreat it already has ("the queue did not answer, next attempt in
    # 15 s", up to five minutes), which is the measured and documented behaviour
    # since plan 05-08. The cost of the stale case is one unanswered request per
    # five minutes; the cost of the case without the mark is an index that
    # silently stops growing.
    #
    # The shared volume of DI-06.1-22 overrides the mark, and it is the only
    # thing that does. The mark says this container was enabled, which is true
    # and beside the point: the rows it would claim and the index it would write
    # belong to another instance, so an armed poller here would add its own
    # damage to the one the sharing already causes.
    was_enabled = _was_enabled_before_this_start()
    if shared_volume.other and was_enabled:
        LOGGER.warning(
            "this container was enabled before this start and stays silenced anyway, because the volume it would "
            "index into belongs to another instance"
        )
    elif was_enabled:
        for task in (active_poller(), active_reconcile()):
            if task is not None:
                task.arm()
        LOGGER.info("findling backend was enabled before this start, indexing continues without a switch")

    # The fourth task, and the three conditions in front of it are the whole
    # decision about when a container rebuilds its index directory.
    #
    # The marks have to ask for it. A rebuild costs the size of the index a
    # second time and a pass over every document in it, so it runs on evidence
    # and never on a suspicion; the question is asked in a worker thread because
    # it opens the state database.
    #
    # Nothing is rebuilt on a shared volume, and that is the same decision as the
    # one about the indexing two blocks up: the marks in that state describe the
    # index of another instance, so a rebuild here would carry another
    # installation's documents into a directory of its own making.
    #
    # And nothing is rebuilt while nothing is armed. A container that was
    # deployed and never enabled holds no tantivy lock and touches no volume, and
    # a rebuild would be the largest possible way of breaking that promise.
    stop_rebuild = asyncio.Event()
    rebuilding: asyncio.Task[None] | None = None
    if was_enabled and not shared_volume.other and await asyncio.to_thread(_rebuild_is_due):
        rebuilding = asyncio.create_task(_rebuild_the_index_directory(stop_rebuild))
        LOGGER.info("findling rebuilds the index directory the changed version marks ask for")

    try:
        yield
    finally:
        stop_indexing.set()
        stop_reconcile.set()
        stop_release.set()
        stop_rebuild.set()

        # The rebuild goes first, and it is the only one of the four whose place
        # in this order matters. It is the task that renames the directories the
        # other three read and write, and it is the one holding the poller
        # silenced; waiting for it here means the shutdown below finds a
        # container in one of the states the clean up path knows rather than in
        # the middle of a rename. Over the budget the band that is running is
        # inside a worker thread, and what it loses is that band and never more
        # than that band, because the commit behind every band is what the next
        # start resumes in.
        if rebuilding is not None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(asyncio.shield(rebuilding), timeout=REBUILD_STOP_SECONDS)
            if not rebuilding.done():
                rebuilding.cancel()
                await asyncio.gather(rebuilding, return_exceptions=True)

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

        if releasing is not None:
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(asyncio.shield(releasing), timeout=RELEASE_STOP_SECONDS)
            if not releasing.done():
                # Over the budget. What is still running is a collect, a trim or
                # a load inside a worker thread, and none of the three is worth
                # holding the shutdown for.
                releasing.cancel()
                await asyncio.gather(releasing, return_exceptions=True)


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
