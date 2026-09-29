"""GET /status: what this container has done, counted, and nothing beyond that.

Phase 4 builds the admin page, and this is where one half of its numbers comes
from. The split is deliberate and written out on both sides of it, because two
docstrings that each claim the whole page is how a page ends up reporting "no
errors" while a switched off container quietly answers nothing at all.

*From the Nextcloud side*, out of ``findling_file_state``: skipped, failed, the
reason codes behind them, and the per file error list. That is the half an admin
can still read when this container is off, which is exactly the moment they go
looking for it.

*From here*: indexed, indexed(truncated), indexed(embedded), the document count
of the index, the permission rows, the version marks, the space on the volume and
the throughput. Only this process sees the volume, the tantivy index and the
vector stock, so nobody else can count them.

The third of those is the newest and the one with a track of its own behind it.
The embedding pass runs for hours after the full text half is already usable, so
a page with one coverage figure says a hundred per cent while a search by
paraphrase still finds nothing (D-16). The number is read out of the vector
stock, which is the only place that holds it, and a stock that is absent or
unreadable is a state of this container with a note, exactly like a state
database that is.

That figure has a companion since phase 7, and the two are not the same kind of
value. ``embedded`` counts documents, ``engineState`` names the state of the
engine that produces them, and the two take every combination: nought documents
with a loaded engine is a track that is starting up, nought documents without a
model in the image is a track that never starts. The page used to show one line
for both. The state is read out of the holder in ``embed/engine.py``, and
reading it builds nothing and loads nothing, which is a property this route
depends on: an admin page polls, and an answer that loaded the engine on the way
would report the memory it had just spent itself (T-07-04).

*And one value that is neither a counter nor a measurement*: ``appVersion``, the
version AppAPI registered this container under. It is here because D-11 has both
halves carry the same major and minor and the other half compare them, and this
is the only place that can say what this container really is. It is deliberately
not one of the version marks: those describe the index, this one describes the
release.

Both views stay visible next to each other, each with its source named. A
difference between them is a diagnostic signal and not a defect of the page,
while a single number called "failed" without a source would hide precisely the
case that is worth seeing.

Everything here is a number, a version mark or a flag. No file name, no location,
no search term, ever. An admin page is a place where such a value is easy to add
"just for support" and impossible to take back, and the counters this app exists
for say everything that is needed: how many documents were indexed, how many were
deliberately left out, and how many could not be read.

The numbers come out of the state database through its read-only connection.
There is no second counting logic in here and there is not going to be one: two
places that count the same rows agree on the day they are written.

A missing state database is not a server error. It is what an installation looks
like for the first few minutes, and the honest answer to it is zeros plus a line
saying so. One value is handed out even then: ``maxFileBytes`` is read from the
environment and not from the database, and the page needs it to clamp its own
setting to the cap this container really enforces. An empty container is no
reason to show a setting that does not apply.

Who may ask. The route is declared with access level ADMIN in appinfo/info.xml,
and that is what the AppAPI proxy enforces, in
``ExAppProxyController::passesExAppProxyRouteAccessLevelCheck``. The path this
app itself uses is ``PublicFunctions::exAppRequest``, which does not go through
that check, so the effective protection of the admin page is its PHP route,
declared without ``NoAdminRequired``. The access level stays correct as defence
in depth for the proxy route. Either way nothing in here reads an identity: how
far the indexing has come is an operator's business, not every user's, and the
answer is the same for all of them.
"""

import asyncio
import logging
import os
import sqlite3
from typing import Final

from fastapi import APIRouter
from pydantic import BaseModel, Field

from findling import guard, lane, precision, probe
from findling.api import resources
from findling.config import settings
from findling.embed.engine import engine_precision, engine_state
from findling.index.open import LANGUAGES_MARK
from findling.index.rebuild import rebuild_blocked_bytes, rebuild_progress
from findling.instance import volume_is_shared
from findling.profile import snapshot
from findling.store.repo import EMBEDDING_BACKLOG_MARK, Store, index_bytes, open_read_only
from findling.store.vectors import VectorStoreError, open_vectors

LOGGER = logging.getLogger("findling.api.status")

ROUTER = APIRouter()

# Every note names a state of this container and never a location on disk.
NO_STATE_YET = "no state database yet, the first indexing pass has not finished"
STATE_UNREADABLE = "the state database exists but could not be opened"
# The two of the second track. They are worth having apart from the two above,
# because the answer they belong to is otherwise complete: every full text
# counter is still true when the vector stock is gone, and exactly one figure of
# the answer is missing.
NO_VECTORS_YET = "no vector database yet, the second track has not written anything"
VECTORS_UNREADABLE = "the vector database exists but could not be read"
# The one note that outranks the four above (DI-06.1-22). It is not a state of
# one storage, it is the statement that none of the counters below describes
# work this container is allowed to do: the volume carries the marker of another
# Nextcloud instance, so the indexing is off and the numbers belong to somebody
# else's index. It names the page that explains the constellation because a
# reader of this line cannot be expected to know how AppAPI names a volume.
VOLUME_SHARED = "this volume belongs to another Nextcloud instance, indexing is off, see docs/uninstall.md"

# The wire keys of the profile values and of their sources, field name to key.
# Spelled out rather than derived by a case conversion, so that renaming a field
# of ProfileValues is a change here on purpose and not a silent change on the
# wire the admin page reads.
PROFILE_VALUE_KEYS: Final = {
    "ocr_slots": "ocrSlots",
    "text_slots": "textSlots",
    "embed_slots": "embedSlots",
    "onnx_threads": "onnxThreads",
    "writer_heap_bytes": "writerHeapBytes",
    "writer_threads": "writerThreads",
    "embed_batch_size": "embedBatchSize",
    "ocr_max_pages": "ocrMaxPages",
    "ocr_dpi": "ocrDpi",
    "memory_reserve_share": "memoryReserveShare",
}


class HardwareReport(BaseModel):
    """The one reading of this start, numbers only (HW-01).

    None means the container could not tell, which is also the answer before
    the lifespan read anything. No path is ever part of it.
    """

    cores: float | None = None
    coresWhole: int | None = None
    cpuCount: int | None = None
    cpuQuota: float | None = None
    memoryLimitBytes: int | None = None
    memoryAvailableBytes: int | None = None
    memoryTotalBytes: int | None = None
    architecture: str = ""
    cgroup: str = ""


class ProfileReport(BaseModel):
    """Chosen, suggested and effective profile, with the values and their sources.

    ``chosen`` and ``effective`` are two fields on purpose (D-24-07): a box that
    shrank keeps the chosen profile and runs a smaller one, and an admin has to
    see both to know it was the box and not the setting.
    """

    chosen: str | None = None
    effective: str = "economy"
    suggested: str = "economy"
    downgraded: bool = False
    hardware: HardwareReport = Field(default_factory=HardwareReport)
    values: dict[str, int | float | None] = Field(default_factory=dict)
    sources: dict[str, str] = Field(default_factory=dict)


class ModelReport(BaseModel):
    """The precision of the embedding model and whether the stock is written again.

    ``precisionChosen`` and ``precisionActive`` are two fields on purpose
    (D-25-03), like chosen and effective of the profile: fp32 chosen and int8
    running is a download, a refusal or a failure, and the verdict says which.
    ``precisionVerdict`` is one word out of the closed set
    ``findling.precision.VERDICTS``, the empty string when there is nothing to
    say. ``reembedRunning`` is true while the redelivery cursor of the vector
    stock is set; the progress of the sweep is ``embedded`` against ``indexed``
    and no figure of its own (D-25-08). ``chunks`` is the row count of the
    vector stock, nought without one: the page estimates how long a switch of
    the precision embeds again from it (D-27-03).
    """

    precisionChosen: str | None = None
    precisionActive: str | None = None
    precisionVerdict: str = ""
    reembedRunning: bool = False
    chunks: int = 0


class LaneReport(BaseModel):
    """Where the embedding runs, out of ``findling.lane``: inline or parallel, and why.

    ``mode`` is one word out of ``lane.MODES`` and ``reason`` one out of
    ``lane.REASONS``; the empty reason belongs to the parallel mode (PAR-01).
    """

    mode: str = "inline"
    reason: str = ""


class ProbeReport(BaseModel):
    """Whether this container can run the pre-check, and whether one runs now.

    ``supported`` is true on every container that carries this field, so the
    page knows without a click that the check can be started (Z15); an older
    container answers without the block. ``running`` says a check runs, in
    another tab as well (Z6), and ``step`` is one word out of
    ``findling.probe.STEPS``, the empty string without a running check. Read out
    of ``findling.probe.snapshot()``; the route measures nothing for this
    block (T-07-04).
    """

    supported: bool = True
    running: bool = False
    step: str = ""


class GuardReport(BaseModel):
    """The memory guard of this process: the level it lowered to, why, and the way back.

    ``chosen`` and ``effective`` are two fields on purpose, like those of the
    profile (D-24-07): the guard never rewrites the chosen profile, it caps the
    level in force, and an admin has to see both to know it was the guard and
    not the setting (D-26-01). Both are read out of the profile snapshot, so
    that there is one truth for them and not two. ``cap`` is the level the
    guard lowered to and None without a lowering. ``cause`` is one word out of
    the closed set ``findling.guard.CAUSES``, the empty string without a
    lowering; ``since`` the epoch second of the lowering. ``token`` exists for
    one purpose only: it lifts the lowering once the admin presses the button
    "Erneut prüfen" and the pre-check fits (D-26-04, D-27-12). It stays here,
    the PHP side reads it server side and no page shows it; it is the empty
    string without a lowering. The three slot fields
    say what the throttle let run against what the profile asked for (D-26-02).
    The route measures nothing for this block (T-26-27).
    """

    chosen: str | None = None
    effective: str = "economy"
    cap: str | None = None
    cause: str = ""
    since: int | None = None
    token: str = ""
    slotsTarget: int = 1
    slotsInForce: int = 1
    throttled: bool = False


class StatusResponse(BaseModel):
    """The operating state of one container.

    Every field defaults, so the answer for a container that has nothing yet is
    the same shape as the answer for one that has been running for a month. A
    status output whose fields come and go cannot be read by a page that has to
    render both.
    """

    indexed: int = 0
    # Contained in indexed above and never added next to it: a truncated
    # document is indexed, it is just indexed at the front only. D-08 of phase 3
    # asks for the number because "indexed" would otherwise be read as a promise
    # this container never made about the end of a long document.
    truncated: int = 0
    # Contained in indexed above and never added next to it: a document without
    # a vector is indexed, it is just not findable by meaning yet. D-16 asks for
    # the number because "indexed" would otherwise be read as a promise about
    # the semantic half that this container has not made: the second track fills
    # up for hours after the full text half is usable, and without a figure of
    # its own the page says a hundred per cent while a paraphrase finds nothing.
    embedded: int = 0
    skipped: int = 0
    failed: int = 0
    # State to reason code to count, and the key for "no reason at all" is the
    # empty string. None is not a JSON object key, so normalising it here is what
    # keeps a page from having to guess which of two spellings it got. Declared
    # with a factory because a mutable default on a model is one object shared by
    # every instance of it.
    reasons: dict[str, dict[str, int]] = Field(default_factory=dict)
    aclRows: int = 0
    docs: int = 0
    indexVersion: int = 0
    analyzerVersion: int = 0
    # The version this container was registered under, and the one field of this
    # answer that says nothing about the index. The two marks above are index
    # format numbers: they decide whether the documents have to be read again.
    # This one is the release both halves are supposed to share (D-11), and the
    # other half compares its major and minor against it. Confusing the two
    # would mix a reindex banner with a protocol check, which are opposite
    # answers: one says "the index is old", the other says "the two halves do
    # not agree on what they are saying to each other".
    #
    # An empty string means the container does not know, which is what a
    # container without APP_VERSION looks like. It is not a mismatch and the
    # other half must not read it as one.
    appVersion: str = ""
    wordlistHash: str = ""
    reindexRequired: bool = False
    lowDisk: bool = False
    # The three raw measurements the space estimate of the admin page is built
    # from, next to the flag above rather than instead of it: the flag carries a
    # threshold this container decided, these carry what the file system said.
    diskFreeBytes: int = 0
    diskTotalBytes: int = 0
    indexBytes: int = 0
    # The cap this container enforces a second time, after the PHP crawl already
    # enforced it. Reported so that the setting on the page can be clamped to it
    # instead of displaying a number that does not apply (pitfall 2).
    maxFileBytes: int = 0
    # Which of five states the embedding engine is in, out of embed/engine.py.
    # The other half of ``embedded`` above and never a second spelling of it:
    # that counter counts documents, this one describes the process, and no
    # combination of the two is impossible. Nought documents with a loaded
    # engine says the track is starting up, nought documents with no model says
    # nothing is coming, and one figure alone cannot tell those apart.
    #
    # Defaulted to the empty string like every other field of this answer, and
    # deliberately not to one of the five words: a default that named a state
    # would be a claim this module makes without having asked. Nothing in this
    # container produces it, because _volume() fills the field on every path.
    engineState: str = ""
    # The set of body chains the index was built under, as the stored mark
    # spells it, and expressly **not** the set this container currently wishes
    # for. The two are the same on a settled installation and they differ for
    # exactly as long as a rebuild is due or running, which is the one moment
    # this field is asked: whoever reads the wish here reads the job as done
    # while it is still being carried out. A container whose index carries no
    # mark answers with the active set, because that is what its next index will
    # be built under, and the field is a string on every path and never null:
    # the page prints it.
    languagesActive: str = ""
    # Which of those chains really carry terms, measured in the index itself.
    # The other half of the line above and never a second spelling of it: that
    # one is an intention, this one is what a search can hit. A chain that was
    # switched on yesterday and has seen no document is in the first and not in
    # the second, and so is every chain of a rebuild that is halfway through.
    languagesFilled: str = ""
    # Which of them a question really reaches, read out of the field plan of the
    # reading side (audit finding M-19-03). The third statement of the group and
    # the only one a search obeys: the two above are the marks and the term
    # dictionary, and the fallback of findling.api.resources.field_plan_for
    # happens between them, in the plan. An instance whose marks name six chains
    # and whose plan fell back answered "six switched on, six filled" while it
    # searched two, and the only trace of that was one log line per opening.
    # Empty means there is no reading side at all, exactly as it does above.
    languagesSearched: str = ""
    # The three readings of the band run of this process, out of
    # findling.index.rebuild. They describe a run and never a queue: a container
    # that is not rebuilding answers false, nought and nought, which is the
    # resting state and not a run of length nought.
    rebuildRunning: bool = False
    rebuildDone: int = 0
    rebuildTotal: int = 0
    # How many bytes the precheck of the rebuild was short of, and nought when
    # it did not refuse. Not the size of the index and not the free space, both
    # of which are already in this answer: the difference, because that is the
    # only figure an admin can act on without doing the arithmetic of this
    # container a second time.
    rebuildBlockedBytes: int = 0
    # The profile of this process (plan 24-06, HW-01, PROF-01): the hardware of
    # this start, the suggestion, the chosen and the effective level, the values
    # they stand for and per value whether the profile or an admin variable set
    # it. A process value like engineState, so the state database knows nothing
    # of it. Reported only: phase 24 switches nothing, and the page shows the
    # block from phase 27 on.
    profile: ProfileReport = Field(default_factory=ProfileReport)
    # The precision of the model and the redelivery of the stock (plan 25-12,
    # MOD-02). A process value like engineState, with one part out of the state
    # database: whether the cursor of the redelivery is set, which _of() reads
    # out of the meta table.
    model: ModelReport = Field(default_factory=ModelReport)
    # Where the embedding runs (plan 25-12, PAR-01). A process value like
    # engineState, so the state database knows nothing of it.
    lane: LaneReport = Field(default_factory=LaneReport)
    # The memory guard (plan 26-08, PAR-03). A process value like engineState,
    # so the state database knows nothing of it; the guard task keeps its own
    # copy there and restores it at start.
    guard: GuardReport = Field(default_factory=GuardReport)
    # The pre-check (plan 27-11, PRUEF-01). A process value like engineState,
    # so the state database knows nothing of it; the check keeps its own copy
    # there and restores it at start.
    probe: ProbeReport = Field(default_factory=ProbeReport)
    note: str = ""


def _profile_report() -> ProfileReport:
    """The profile state of this process as the wire spells it.

    Reads ``findling.profile.snapshot()`` and nothing else. Nothing is measured,
    loaded or written here: the hardware was read once at start, and a poll of
    the admin page must not become a second reading (T-07-04, T-24-23).
    """
    state = snapshot()
    hardware = state.hardware
    reading = (
        HardwareReport()
        if hardware is None
        else HardwareReport(
            cores=hardware.cores,
            coresWhole=hardware.cores_whole,
            cpuCount=hardware.cpu_count,
            cpuQuota=hardware.cpu_quota,
            memoryLimitBytes=hardware.memory_limit_bytes,
            memoryAvailableBytes=hardware.memory_available_bytes,
            memoryTotalBytes=hardware.memory_total_bytes,
            architecture=hardware.architecture,
            cgroup=hardware.cgroup,
        )
    )
    resolution = state.resolution
    return ProfileReport(
        chosen=None if state.chosen is None else state.chosen.value,
        effective=state.effective.value,
        suggested=state.suggested.value,
        downgraded=state.downgraded,
        hardware=reading,
        values={key: getattr(resolution.values, field) for field, key in PROFILE_VALUE_KEYS.items()},
        sources={key: resolution.sources[field] for field, key in PROFILE_VALUE_KEYS.items()},
    )


def _model_report() -> ModelReport:
    """The precision state of this process as the wire spells it.

    Reads ``findling.precision.snapshot()`` and, before the start state is
    settled, the precision of the holder. Nothing is measured, loaded or written
    here: no digest and no look at the fp32 file, because a poll of the admin
    page must not become a second reading of a file of hundreds of megabytes
    (T-07-04, T-25-53). ``reembedRunning`` stays false in this branch: the
    cursor lives in the state database and :func:`_of` reads it.
    """
    state = precision.snapshot()
    return ModelReport(
        precisionChosen=None if state.chosen is None else state.chosen.value,
        precisionActive=engine_precision() if state.active is None else state.active.value,
        precisionVerdict=state.verdict,
    )


def _lane_report() -> LaneReport:
    """The lane state of this process, out of ``findling.lane.snapshot()`` and nothing else."""
    state = lane.snapshot()
    return LaneReport(mode=state.mode, reason=state.reason)


def _probe_report() -> ProbeReport:
    """The pre-check of this process, out of ``findling.probe.snapshot()`` and nothing else."""
    state = probe.snapshot()
    running = state.state == probe.STATE_RUNNING
    return ProbeReport(running=running, step=state.step if running else "")


def _guard_report() -> GuardReport:
    """The guard state of this process as the wire spells it.

    Reads the snapshot of ``findling.guard`` and the profile snapshot, and
    nothing else: no cgroup file, no counter. The guard task reads the kernel
    on its own tick, and a poll of the admin page must not become a second
    reading (T-07-04, T-26-27).
    """
    state = guard.snapshot()
    levels = snapshot()
    return GuardReport(
        chosen=None if levels.chosen is None else levels.chosen.value,
        effective=levels.effective.value,
        cap=None if state.cap is None else state.cap.value,
        cause=state.cause,
        since=None if state.since is None else int(state.since),
        token=state.token,
        slotsTarget=state.slots_target,
        slotsInForce=state.slots_in_force,
        throttled=state.throttled,
    )


def _number(mark: str | None) -> int:
    """A version mark as a number, and 0 for the placeholder of an unnamed one.

    An index whose analyzer never identified itself carries the placeholder, and
    it shows up here as a zero next to ``reindexRequired`` being true, which
    together say exactly what happened.
    """
    if mark is None:
        return 0
    try:
        return int(mark)
    except ValueError:
        return 0


def _app_version() -> str:
    """The version AppAPI registered this container under, empty when it did not say.

    Read out of the environment on every call and not through ``settings()``.
    ``settings()`` is the configuration of this app, every name in it starts with
    ``FINDLING_`` and it is cached once per process; ``APP_VERSION`` belongs to
    the four variables AppAPI itself sets next to ``APP_ID``, ``APP_SECRET`` and
    ``NEXTCLOUD_URL``, which the client library also reads per request. Keeping
    it out of the cached settings means a container that AppAPI restarted with a
    new version reports the new one, and it keeps this value out of a structure
    whose defaults are a matter of this app.

    Whitespace is stripped and nothing else is judged. What a version has to look
    like is decided where it is compared, which is the other half.
    """
    return os.environ.get("APP_VERSION", "").strip()


def _named_reasons(breakdown: dict[str, dict[str | None, int]]) -> dict[str, dict[str, int]]:
    """The breakdown with the absent reason spelled as an empty string."""
    return {
        state: {("" if reason is None else reason): total for reason, total in per_state.items()}
        for state, per_state in breakdown.items()
    }


def _volume() -> StatusResponse:
    """Everything this container can say without opening the state database.

    Built as a whole answer rather than as four loose values, so the three
    branches of :func:`report` below add what they learned to it instead of
    repeating the volume part each time. Every one of these values comes from the
    environment or from the file system, which is why a container without a
    state database still reports them.

    ``appVersion`` belongs in exactly this branch and for exactly that reason. A
    container that was deployed a minute ago has no index and no state database,
    and it is the one whose version the other half most needs to be able to
    check: the minutes after an update are when a protocol mismatch is either
    seen or mistaken for a slow first pass.

    ``engineState`` belongs here for the same kind of reason and it is asked in
    the same minutes: a container that was deployed a minute ago is the one
    whose admin wants to know whether the semantic half is going to work at all,
    and there is no index yet to read that out of. It comes out of the process
    and not out of a file, so it is available whether or not anything has been
    counted.

    The four values of the rebuild travel the same way and for the third variant
    of the same reason: they are readings of this process, they exist before the
    first document is counted, and a container that has never rebuilt anything
    answers with the resting state rather than with nothing.

    ``languagesActive`` is set here to the **active** set, and that is the
    fallback and not the answer: :func:`_of` below overwrites it with the stored
    mark whenever there is one. A container without a state database has no mark
    to read, and the set it will build its first index under is the honest thing
    to say about it.
    """
    resolved = settings()
    free, total = resources.disk_bytes()
    progress = rebuild_progress()
    return StatusResponse(
        appVersion=_app_version(),
        engineState=engine_state(),
        languagesActive=",".join(resolved.languages),
        languagesFilled=",".join(resources.filled_languages()),
        languagesSearched=",".join(resources.searched_languages()),
        rebuildRunning=progress.running,
        rebuildDone=progress.documents_carried,
        rebuildTotal=progress.documents_total,
        rebuildBlockedBytes=rebuild_blocked_bytes(),
        profile=_profile_report(),
        model=_model_report(),
        lane=_lane_report(),
        guard=_guard_report(),
        probe=_probe_report(),
        lowDisk=resources.low_disk(),
        diskFreeBytes=free,
        diskTotalBytes=total,
        indexBytes=index_bytes(resolved.index_dir),
        maxFileBytes=resolved.max_file_bytes,
    )


def _embedded() -> tuple[int, int, str]:
    """How many documents and chunks carry a vector, and the note that belongs to them.

    Its own function because it needs its own try, and the shape of that try is
    the one :func:`report` uses one file over: ``sqlite3.Error`` next to
    ``OSError``, on the open and on the read, because the two realistic shapes of
    a broken stock escape the open alone. A file that is not a SQLite database
    raises from the first PRAGMA, and a zero byte vectors.db, which a kill
    between connect and the schema script leaves behind, opens cleanly and
    raises on the first query. Both are a state of this container and never a 500
    (review finding WR-01).

    ``VectorStoreError`` joins the two, and it is the finding this file adds to
    them: reading the stock means loading a shared object into this process, and
    a box where vec0 refuses to load is a third way to have no figure and the
    same answer for the page.

    ``read_only=True`` refuses a missing file rather than creating an empty one,
    the same discipline the read side keeps: an empty stock this route created
    would report nought embedded for ever and look exactly like a second track
    that has not started.
    """
    resolved = settings()
    if not resolved.vectors_db.is_file():
        return (0, 0, NO_VECTORS_YET)

    try:
        vectors = open_vectors(resolved.vectors_db, read_only=True)
    except (OSError, sqlite3.Error, VectorStoreError) as error:
        LOGGER.warning("the vector database could not be opened, an %s", type(error).__name__)
        return (0, 0, VECTORS_UNREADABLE)

    try:
        return (vectors.document_count(), vectors.chunk_count(), "")
    except sqlite3.Error as error:
        LOGGER.warning("the vector database could not be read, an %s", type(error).__name__)
        return (0, 0, VECTORS_UNREADABLE)
    finally:
        # Opened per call rather than kept, for the reason the state database is:
        # this route is asked rarely, by one admin page, and a connection of its
        # own is always current without a cache anybody has to invalidate. The
        # read side keeps a cached handle and this route deliberately does not
        # share it: that one is opened for searching and is absent on a container
        # that has no index yet, which is a container this route still answers
        # for.
        vectors.close()


def _of(store: Store, volume: StatusResponse) -> StatusResponse:
    """Read every number out of one open state database.

    Every field is named. Nothing here spreads a row of ``files`` into the
    answer, however convenient that would be on the day somebody adds a column:
    that table carries ``path`` and ``title``, and a spread would put both on the
    wire in the same commit that meant to add a counter (T-04-06).
    """
    counters = store.counts()
    breakdown = store.reasons_by_state()
    rows, documents = store.acl_totals()
    marks = store.read_meta()
    return StatusResponse(
        indexed=counters.get("indexed", 0),
        truncated=breakdown.get("indexed", {}).get("truncated", 0),
        skipped=counters.get("skipped", 0),
        failed=counters.get("failed", 0),
        reasons=_named_reasons(breakdown),
        aclRows=rows,
        docs=documents,
        indexVersion=_number(marks.get("index_version")),
        analyzerVersion=_number(marks.get("analyzer_version")),
        wordlistHash=marks.get("wordlist_hash", ""),
        # A drift means the index was built with a different tokenisation than
        # the one queries are parsed with, so hits vanish with nothing saying
        # why. Reported, never acted on: what follows is the poller's decision.
        reindexRequired=bool(resources.version_drift(store)),
        # Carried over from the volume answer, named like every other field of
        # it. The version says nothing about the state database, so it is not
        # read a second time here: one place asks the environment.
        appVersion=volume.appVersion,
        # The second track and its note travel the same way, and for the same
        # reason: they come out of another file, so a healthy state database
        # neither produces them nor clears them.
        embedded=volume.embedded,
        # Carried over like the version above: the state of the engine is a
        # property of this process and the state database has nothing to say
        # about it, so it is asked once, in the branch that runs either way.
        engineState=volume.engineState,
        # The set the directory was built under, and the one value of this group
        # that the state database really owns. A missing mark is an installation
        # that comes from 1.2.0 and never wrote one, and the active set of the
        # volume answer is what it falls back to: that is the set its next index
        # will carry, and it is a truer statement than an empty line.
        languagesActive=marks.get(LANGUAGES_MARK, "") or volume.languagesActive,
        # Carried over like the engine state above: the chains that carry terms
        # are a property of the index directory, and the state database has
        # nothing to say about them.
        languagesFilled=volume.languagesFilled,
        # Carried over for the same reason, and it is the value to read next to
        # the mark above: that one is what the directory was built for, this one
        # is what a question reaches. Two lines that disagree are a fallback, and
        # the degraded flag says so as well (M-19-03).
        languagesSearched=volume.languagesSearched,
        rebuildRunning=volume.rebuildRunning,
        rebuildDone=volume.rebuildDone,
        rebuildTotal=volume.rebuildTotal,
        rebuildBlockedBytes=volume.rebuildBlockedBytes,
        # Carried over like the engine state: the profile is a value of this
        # process and the state database has nothing to say about it. Left out
        # here, it would vanish on every installation that has indexed anything
        # (24-RESEARCH.md, Pitfall 2).
        profile=volume.profile,
        # Carried over like the profile, and for the same Pitfall 2: both are
        # values of this process, and left out here they would fall back to
        # their defaults on every installation that has indexed anything. The
        # one part the state database owns is set on the way: a redelivery runs
        # while its cursor is set, and the sweep clears it when it is through.
        model=volume.model.model_copy(update={"reembedRunning": bool(marks.get(EMBEDDING_BACKLOG_MARK, ""))}),
        lane=volume.lane,
        # Carried over like the lane, for the same Pitfall 2.
        guard=volume.guard,
        # Carried over like the guard, for the same Pitfall 2.
        probe=volume.probe,
        note=volume.note,
        lowDisk=volume.lowDisk,
        diskFreeBytes=volume.diskFreeBytes,
        diskTotalBytes=volume.diskTotalBytes,
        indexBytes=volume.indexBytes,
        maxFileBytes=volume.maxFileBytes,
    )


def report() -> StatusResponse:
    """The state of this container. Runs in a worker thread, never raises.

    Two steps, and the split exists for one reason: the shared volume of
    DI-06.1-22 is the only finding that outranks all four notes of the counting
    half, and a check woven into that half would have had to be repeated in each
    of its three exits. So the counters are gathered first, unchanged, and the
    note is overwritten afterwards if the volume turns out not to be this
    instance's. The counters stay in the answer on purpose: they are true, they
    are simply the numbers of another instance's index, and hiding them would
    take away the very evidence that shows the sharing.
    """
    answer = _counted()
    if volume_is_shared():
        return answer.model_copy(update={"note": VOLUME_SHARED})
    return answer


def _counted() -> StatusResponse:
    """Everything this container can count, with the note of the counting half.

    The whole function runs off the event loop, which is what lets it sum the
    size of the index directory: that walk grows with the number of segments and
    would otherwise stall every other request while an admin page polls
    (T-04-09).
    """
    resolved = settings()
    volume = _volume()
    # Asked before the state database, and its note is carried in the same
    # structure. One answer carries one note, so the two findings are ordered
    # rather than joined: the state database is the bigger one, because without
    # it there are no counters at all, while a missing vector stock costs
    # exactly one of them. Every branch below therefore overwrites this note and
    # none of them appends to it.
    embedded, chunks, vector_note = _embedded()
    volume = volume.model_copy(
        update={
            "embedded": embedded,
            "note": vector_note,
            "model": volume.model.model_copy(update={"chunks": chunks}),
        }
    )

    if not resolved.state_db.is_file():
        return volume.model_copy(update={"note": NO_STATE_YET})

    # sqlite3.Error is caught next to OSError on both the open and the read,
    # because two realistic shapes of a broken state escape the open alone: a
    # file that is not a SQLite database raises DatabaseError from the first
    # PRAGMA, and a zero byte state.db, which a kill between connect and the
    # schema script leaves behind, opens cleanly and raises OperationalError on
    # the first query. Both are the same answer as an unreadable file: a state
    # of this container, never a 500 (review finding WR-01).
    try:
        store = open_read_only(resolved.state_db)
    except (OSError, sqlite3.Error) as error:
        LOGGER.warning("the state database could not be opened, an %s", type(error).__name__)
        return volume.model_copy(update={"note": STATE_UNREADABLE})

    try:
        return _of(store, volume)
    except sqlite3.Error as error:
        LOGGER.warning("the state database could not be read, an %s", type(error).__name__)
        return volume.model_copy(update={"note": STATE_UNREADABLE})
    finally:
        # Opened per call rather than kept: this route is asked rarely, by one
        # admin page, and a connection of its own is always current without a
        # cache anybody has to invalidate.
        store.close()


@ROUTER.get("/status")
async def read_status() -> StatusResponse:
    """Answer with the counters and the version marks of this container."""
    return await asyncio.to_thread(report)
