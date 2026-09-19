"""The one embedding engine of this process, for the search side and the track.

Both halves of the container embed. The second track turns document chunks into
vectors and every semantic search turns the query into one, and until plan
06.1-02 each of them built its own :class:`~findling.embed.model.EmbeddingModel`.
That is two tokenizers and two onnxruntime sessions in one process. The load run
of 2026-09-05 measured what it costs: the first search with a semantic part
added 276 MB that stayed resident for the rest of the container's life, on a box
with 210 MB of headroom against a hard 2 GB limit, and it is the reason
``memory.events max`` stood at 2796 while every damage counter stayed at zero.

**Why the holder is here and not on either side that uses it.** Not in
``embed/model.py``, because the class comment there argues, correctly, that a
global beside the class would make the moment of the first load depend on which
import ran first; the decision belongs one layer up, where it is a decision.
Not in ``api/resources.py``, although the shape below is copied from
``query_model`` there: that module is the reading half of the container, its own
head says "Nothing here decides anything", and the worker would end up importing
from the API to get its engine. The dependency direction is the point.
``worker/poller.py`` imports from ``embed/``; nothing in ``worker/`` imports from
``findling.api``.

**Why a cache at all, and why keyed on the directory.** Both answers come from
``api/resources.py`` and both still hold. Constructing the wrapper loads
nothing, so this may be called long before it is known whether there is a model
at all, but the wrapper remembers an absent model, so a container without one
looks for it once instead of once per search. And it is keyed on the model
directory because a process has one of those while a test suite has one per
test: without the key the second test would be handed the remembered refusal of
the first. Absence itself is never cached here, only the wrapper is.

**And the question about the engine, next to the holder that answers it.**
:func:`engine_state` says which of five states this process is in, for the
admin page of plan 07-04. It lives here because the holder is what it reads,
and it is the one function in this module that must build nothing: an admin
page polls, so a question that loaded the engine on the way would be the
loading trigger of a container nobody is searching on.

**The one thing this module is told rather than reads.** The second track needs
a tokenizer and a splitter next to the weights, it builds them at the first row
that needs one, and that build can throw for the same reason a load can: 544,3
MB arriving under a hard 2 GB limit. The holder knows nothing of it, because the
build never gets as far as asking for the engine, so before this the page said
"cold" for a track that was lying dead in its cooldown (bug audit MEDIUM-2 of
plan 07-05). :func:`note_cutter_failure` is how the poller says it, and the
stamp it hands over is its own, so the two halves cannot drift into two clocks.
It is a fact about this process, like the holder itself, and it is remembered
in the same place for the same reason.

**What this does not do.** It does not make the engine thread safe. That belongs
to the object, holds for every caller including the ones that build their own,
and lives in :class:`~findling.embed.model.EmbeddingModel` with the arithmetic
that justifies the lock.
"""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Final

from findling.config import settings
from findling.embed.model import LOAD_RETRY_SECONDS, EmbeddingModel, artifacts_present, unload_count

if TYPE_CHECKING:
    from pathlib import Path

# The directory the wrapper was built for, and the wrapper. One entry, because
# one process reads one model.
_ENGINE: tuple[Path, EmbeddingModel] | None = None

# Re-entrant for the reason the read side lock is: the cost of proving that no
# path below ever takes it twice is higher than the cost of the flag inside it.
_LOCK = threading.RLock()

# When the second track last failed to build its cutter, on the monotonic clock,
# and None when it never did or not since the last success. Written by the
# poller through :func:`note_cutter_failure` and read by :func:`engine_state`
# alone. A plain module global next to the holder because it describes the same
# thing the holder does, this process, and because the poller keeps its own copy
# as the field its own gates read: this one is the diagnosis and never the gate.
_CUTTER_FAILED_AT: float | None = None

# The directory the artifact question was answered "no" for, once, in this
# process. The same remembered refusal as ``EmbeddingModel._absent`` and for the
# same reason (perf audit PERF-F2): a directory without the two files is a
# property of the installation and not of the moment, the admin page polls every
# few seconds for as long as it is open, and an empty holder is exactly the
# state in which nobody else answers that question. Only the "no" is
# remembered. A "yes" stays a question, because a model that is taken out of a
# running container has to become visible, and because the two stats it costs
# are paid on the state that resolves itself.
_ABSENT: Path | None = None

# Whether a search has been refused a load since the last warm run, and
# whether a warm run is in flight right now. Two plain module flags beside
# the holder, because both describe this process the way the holder does,
# and both are written under :data:`_LOCK`.
#
# The second one is efficiency and not correctness. _load() already returns
# at its head when the engine is bound, so ten concurrent warm runs pay for
# one load whatever this flag says; what it saves is the nine threadpool
# threads that would otherwise queue at the lock of the holder
# (14-RESEARCH.md 5.3).
_WARM_WANTED = False
_WARMING = False

# The line a warm run embeds. A fixed constant and never anything a user
# typed or anything read off the disk: it travels the path a search line
# travels, through the tokenizer and the graph, so a user line here would be
# a user line in whatever that path ever comes to log (T-14-22). Short,
# because the cost of the run is the load and not the sentence.
WARM_TEXT: Final = "aufwaermen"

# The closed set of answers :func:`engine_state` gives, as named constants in
# the shape of the notes of ``api/status.py``: every one of them names a state
# of this container and none of them names a place on disk (T-07-01). The words
# themselves travel to the other half and are the protocol, not a label. What an
# admin reads is decided over there, in the admin's own language.
ENGINE_LOADED: Final = "loaded"
ENGINE_COLD: Final = "cold"
ENGINE_DISABLED: Final = "disabled"
ENGINE_MISSING: Final = "missing"
ENGINE_RETRY_PENDING: Final = "waiting_for_retry"
ENGINE_UNLOADED: Final = "unloaded"

# The set as a whole, so that the other half can be held against it and so that
# a seventh answer cannot arrive without this line seeing it.
#
# The sixth one arrived on 2026-09-19, by the owner's decision for branch B of
# plan 14-09, and it is the one word this line was written to make expensive.
# The price was paid on purpose: the switch of MEM-01 gives the weights back in
# an idle span, and without a word of its own that saving is invisible, because
# a released container shows the same coverage figure and the same empty holder
# as one that has never read anything. Two things needed it. The A/B measurement
# of phase 15 reads the state trail cold -> loaded -> unloaded -> loaded to show
# that a warm window costs exactly one load, and the support case "the first
# search is slow" is answered by the page instead of by a log.
ENGINE_STATES: Final = frozenset(
    {ENGINE_LOADED, ENGINE_COLD, ENGINE_DISABLED, ENGINE_MISSING, ENGINE_RETRY_PENDING, ENGINE_UNLOADED}
)


def shared_model() -> EmbeddingModel:
    """Return the embedding engine of this process, building it on first use.

    Both callers go through here: ``api/resources.py::query_model`` for the
    search side and ``worker/poller.py::_wire_the_second_track`` for the second
    track. Two calls answer the same object as long as the settings name the
    same model directory, which is what makes tokenizer and weights arrive once.

    Nothing is loaded by this call. The artifacts are read on the first text
    that reaches the engine, and whether there are any is answered there with
    the ``embedding_unavailable`` verdict rather than with an exception.
    """
    global _ENGINE

    resolved = settings()
    with _LOCK:
        if _ENGINE is not None and _ENGINE[0] == resolved.embed_model_dir:
            return _ENGINE[1]
        model = EmbeddingModel(
            resolved.embed_model_dir,
            batch_size=resolved.embed_batch_size,
            sequence_len=resolved.embed_sequence_len,
        )
        _ENGINE = (resolved.embed_model_dir, model)
        return model


def note_cutter_failure(stamp: float | None) -> None:
    """The second track says when its cutter build last threw, or that it did not.

    One writer, one reader, one clock. The stamp is the poller's own
    ``_cutter_failed_at``, handed over rather than taken here, so the cooldown
    the track runs on and the state the page shows can never be two different
    moments. None is the whole of the other message: the build worked, or the
    track never got to one.

    Called from ``worker/poller.py`` and from nowhere else. The dependency
    direction of this module holds: ``worker/`` imports from ``embed/``, and
    nothing here knows that a poller exists.
    """
    global _CUTTER_FAILED_AT

    global _ABSENT

    with _LOCK:
        _CUTTER_FAILED_AT = stamp
        if stamp is None:
            # A build that worked read both artifacts, so a remembered "no"
            # about that directory is out of date by the time this arrives. The
            # two facts are kept consistent here rather than by a comment,
            # because they come from the same directory and would otherwise
            # contradict each other on the page.
            _ABSENT = None


def _cutter_cooling_down() -> bool:
    """True while the failed cutter build of the second track is inside its cooldown.

    The same comparison as
    :attr:`~findling.embed.model.EmbeddingModel.load_cooling_down`, against the
    same constant, because it is the same failure one layer up. Reading it has
    no side effect: the clock is read, nothing else.
    """
    stamp = _CUTTER_FAILED_AT
    return stamp is not None and time.monotonic() - stamp < LOAD_RETRY_SECONDS


def reset() -> None:
    """Forget the engine of this process, for a test suite and for one tool.

    Named as what it is and used by nobody in the container: the holder is a
    property of a process, and a running container has exactly one interest in
    it, which is that it stays. Two callers have the opposite interest, and both
    of them run outside a container.

    ``tools/one_load.py`` is the one that needs it (bug audit LOW-7 of plan
    07-05). Its gate asserts that one process pays for exactly one load, and it
    measures that by driving the search side and the second track for real. A
    second call of ``measure()`` in the same process used to find the engine of
    the first one in the holder, take the cache hit, count nought loads and
    report "green for nothing" about a tool that was working perfectly.

    A test suite is the other. It is one process with one model directory per
    case, so the holder is keyed away from most of the trouble, but a case that
    reuses a directory would inherit whatever the case before it loaded.

    **What it does not reset is the load counter.** Every caller of
    :func:`~findling.embed.model.load_count` reads it as a difference against a
    baseline it took itself, so nothing needs it zeroed, and a counter that can
    be zeroed is one a gate could zero itself green with. The evidence of "one
    load per process" stays monotonic for the life of the process. The unload
    counter behind :func:`released_count` is not zeroed either, for the same
    reason and by the same argument: the two are read as one difference.
    """
    global _ENGINE

    with _LOCK:
        _ENGINE = None
        # The notice of the second track goes with it, and the remembered
        # refusal about the artifacts with that: all three say something about
        # this process, and this is the call that says the process starts over.
        note_cutter_failure(None)


def _artifacts_absent(model_dir: Path) -> bool:
    """True when the two files are not in that directory, asked at most once.

    The seam of perf audit PERF-F2, in the shape ``EmbeddingModel._load`` uses
    for the same question: the "no" is remembered for the life of the process
    and the "yes" is not. What makes the asymmetry right is what each answer
    describes. A directory without the artifacts is a container built without
    the model stage, which is the ordinary case outside the shipping image and
    stays true until somebody deploys another image; asking again is a pair of
    stats per poll of an admin page, for ever, for an answer that cannot change.
    A directory with them may lose them, and that has to become visible.
    """
    global _ABSENT

    with _LOCK:
        if model_dir == _ABSENT:
            return True
        if artifacts_present(model_dir):
            return False
        _ABSENT = model_dir
        return True


def _held(model_dir: Path) -> EmbeddingModel | None:
    """The engine of this process if there is one, and never a new one.

    The holder is read under the same lock :func:`shared_model` writes it
    under, and the one difference to that function is the whole point of this
    one: an empty holder is answered with None and not filled.
    """
    with _LOCK:
        if _ENGINE is not None and _ENGINE[0] == model_dir:
            return _ENGINE[1]
        return None


def engine_state() -> str:
    """Which of six states the embedding engine of this process is in.

    For the admin page, which shows how many documents carry a vector and can
    say nothing else about the semantic half. Nought documents is the same
    figure for a model that is not in the image, for a load that threw and is
    still inside its cooldown, and for a track that has not got there yet, and
    the three ask completely different things of an admin: rebuild the image,
    wait five minutes, or do nothing at all.

    ``unloaded`` is the sixth and answers the question the switch of MEM-01
    raised: it tells "never read" from "released to save memory, and the next
    search pays the reload". The two look identical on the coverage figure and
    on the holder, and the milestone asks for the cost of warming up again to be
    shown rather than left in a log.

    **Nothing is built and nothing is loaded here.** An empty holder is
    answered with a state and not with an instance, and no path below reads an
    artifact. That is not tidiness: the page polls every few seconds while it is
    open, so a question that loaded the engine would be the loading trigger of a
    container nobody is searching on, and it would report the 118 MB it had just
    spent itself (T-07-04).

    **The order of the answers is fixed, and it is not the order of the fields
    they come from.** Switched off outranks everything, because a container
    whose semantic half is off would otherwise be reported cold and look like
    one that is about to begin. Then the missing model, the one state that does
    not resolve itself. Then the cooldown, then the loaded engine, then the
    released one, and cold last, as the state that is left when nothing else is
    true.

    ``unloaded`` sits behind ``loaded`` because a container that has warmed up
    again after a release is loaded and not released: the counter is monotonic
    and can only say that a release has happened, never that the holder is empty
    right now, and the holder is what answers that. It sits in front of ``cold``
    because cold is the state that is left when nothing else is true, and after
    a release something else is true.

    **The counter is the source, and not a field of its own.** A released engine
    leaves an empty holder behind, which is exactly the holder a container that
    has never read anything has, so the answer cannot be read off the holder.
    :func:`released_count` is monotonic, :func:`reset` does not zero it, and a
    process that has never let go of anything therefore cannot report this word
    at all (T-14-17).

    **The cooldown has two sources and one answer** (bug audit MEDIUM-2 of plan
    07-05). A load of the weights that threw is one of them and the holder knows
    it. A cutter build of the second track that threw is the other, and the
    holder cannot know it: that build fails before it ever asks for the engine,
    so the holder stays empty and the page used to say "cold", which reads as
    "the model arrives on first demand" for a track that is lying dead for five
    minutes. Both are the same sentence to an admin, wait and look again, so
    both give the same word and no sixth one is invented for it.
    """
    resolved = settings()
    if not resolved.embed_enabled:
        return ENGINE_DISABLED

    held = _held(resolved.embed_model_dir)

    # The missing model, asked of whichever source can answer it. With an
    # instance in the holder that is the refusal its load path remembered for
    # ever; without one it is the pair of stats, and it is asked here rather
    # than left at cold because since plan 07-03 neither half of this container
    # builds the engine before the first row or the first search that needs one.
    # A container without a model would otherwise report cold for its whole
    # life, and cold reads as "the model arrives on first demand", which is the
    # one sentence an admin must not be given in that situation.
    absent = held.artifacts_absent if held is not None else _artifacts_absent(resolved.embed_model_dir)
    if absent:
        return ENGINE_MISSING
    if (held is not None and held.load_cooling_down) or _cutter_cooling_down():
        return ENGINE_RETRY_PENDING
    if held is not None and held.loaded:
        return ENGINE_LOADED
    if unload_count() > 0:
        return ENGINE_UNLOADED

    # What is left when nothing else is true: the artifacts are there, nothing
    # threw, and nothing has been read yet.
    return ENGINE_COLD


def query_may_load() -> bool:
    """Whether a search is allowed to pay for the weights, asked in one place.

    False is not a refusal to answer. ``embed_query(may_load=False)`` answers
    out of the engine that is held or gives the ``embedding_unavailable``
    verdict, ``_rank_chunks`` returns an empty list, RRF becomes the identity on
    the lexical list, and the user gets full text hits. That path exists, is
    tested, and is what every container without a model has been doing all
    along (D-19).

    **The rule hangs on the switch and does not hold in general.** The incident
    of 2026-09-10 was the very first search of a container that had never
    unloaded anything: 1838.4 ms against the 1500 ms ceiling of
    ``ExAppService``, cURL error 28 in the Nextcloud log, an answer group
    without the container half, nought hits, and all of it invisible from the
    outside because the route answers HTTP 200
    (``docs/measurements/2026-09-vergleichsmessung-m7g/``, sections 9.2 and
    19.4). A seam without the switch would stop that incident in general. It
    would also be a change to shipped behaviour at the first search of every
    container, outside the switch, and the one paid trip to the box of phase 15
    would then measure two changes at once. The general case is carried as a
    backlog item and is not forgotten.

    **Why the rule is here and not at the three places that build a
    ``SemanticSide``** (``api/search.py``, ``api/snippets.py``,
    ``api/diagnose.py``): three places are the place where the fourth one is
    forgotten. Every caller asks this function instead of repeating it.

    Nothing is built and nothing is loaded here, for the reason
    :func:`engine_state` gives for itself: this question sits on the path of
    every single search. One setting is read, and that is the whole body.
    """
    # ``api/diagnose.py::ranked_sides`` is the one caller that does **not** ask
    # this question and goes on loading (14-RESEARCH.md, open question 2). A
    # measuring tool has to be able to measure, and that route carries no 1.5
    # second ceiling and no user. The other side of that decision is that a
    # diagnosis call warms the container up, so it must not be made before a
    # cold measurement. That consequence belongs in the runbook of plan 14-11
    # and is only named here.
    return settings().embed_idle_release_seconds == 0


def release_if_idle(ttl_seconds: int) -> bool:
    """Let go of the weights when nothing has used them for that long.

    True means this call really released: the engine is gone, the pages have
    been handed back and :func:`released_count` has risen by one. False is every
    other answer, and on a container that is being worked on it is almost all of
    them, because the caller of plan 14-07 runs on a tick and the idle span is
    the exception.

    **Nothing is built on the way.** The holder is read through :func:`_held`
    and never through :func:`shared_model`, which is the argument
    :func:`engine_state` makes for itself one function up: an unloader that
    filled the holder while asking would be the loading trigger of a container
    nobody is searching on, once per tick, for the life of the process
    (T-14-21).

    **The identity check is not theory** (T-14-20). The warm run of MEM-03 runs
    beside the unload task, so between reading the clock above and letting go
    below the holder can come to carry a different instance, and that one has
    just paid for 118 MB of weights. Throwing away the load pair that was bought
    a millisecond ago is exactly the cost this phase exists to avoid, so the
    holder is read a second time under :data:`_LOCK` and the release only
    happens when it is still the same object.

    **The release itself is outside the lock.**
    :meth:`~findling.embed.model.EmbeddingModel.release` takes its own lock,
    lets go under it and then runs ``gc.collect()`` and ``malloc_trim(0)``
    outside it, and both of those block. Holding :data:`_LOCK` across that would
    block every concurrent :func:`shared_model` question with them (T-14-16).
    The caller puts the whole of this function through ``asyncio.to_thread``, so
    the blocking never reaches the event loop either.

    A span of nought or less is answered False without asking the holder
    anything. Nought is the word for off in
    ``settings().embed_idle_release_seconds``, the caller should not be here at
    all with it, and a function that treated it as an unbounded release would be
    a function with two truths.
    """
    if ttl_seconds <= 0:
        return False

    model_dir = settings().embed_model_dir
    held = _held(model_dir)
    if held is None or not held.loaded:
        return False

    stamp = held.last_use()
    if stamp is None or time.monotonic() - stamp < ttl_seconds:
        # None is a holder that has loaded and never embedded anything. That is
        # not an idle span of infinite length: the clock of ``_embed`` has not
        # started, nobody has worked, and the next row or search is as likely as
        # not to be a moment away.
        return False

    with _LOCK:
        if _held(model_dir) is not held:
            return False

    return held.release()


def released_count() -> int:
    """How often this process has let go of tokenizer and weights.

    A pass through of :func:`~findling.embed.model.unload_count`, so that a
    caller can read the counter beside :func:`~findling.embed.model.load_count`
    without importing ``embed/model.py`` for one number. It is the same figure
    and never a second one kept here.

    Monotonic, and :func:`reset` does not zero it, for the reason written at the
    counter itself: every reader takes a difference against a baseline of its
    own, nothing needs it zeroed, and a counter that can be zeroed is one a gate
    could zero itself green with (T-14-17).
    """
    return unload_count()


def request_warm() -> None:
    """A search says that it answered without the weights.

    The one way in. ``api/search.py`` calls it in plan 14-08, on the path of a
    search that :func:`query_may_load` refused a load to, and nothing else in
    the container ever sets the marker. The call is cheap on purpose: it takes
    :data:`_LOCK` for one assignment and never touches the holder, because it
    runs inside a request that has already spent its budget.

    Whether the warm run then really happens is not decided here.
    :func:`warm_wanted` asks the four questions, and the caller that runs it
    asks that one.
    """
    global _WARM_WANTED

    with _LOCK:
        _WARM_WANTED = True


def warm_wanted() -> bool:
    """Whether a warm run is owed, would help, and could work.

    Four conditions and all of them have to hold. Somebody was refused a load
    (:func:`request_warm`), the release is switched on at all, there is a holder
    with a cold engine, and the artifacts are not remembered as absent. A
    container without a model would otherwise be warmed once per refused search,
    for ever, and every one of those runs would read a directory that has
    nothing in it.

    **Nothing is built and nothing is loaded here** (T-14-21). The holder is
    read through :func:`_held`, the same way :func:`release_if_idle` reads it
    and for the same reason: this question sits on a tick, and a question that
    filled the holder would be the loading trigger of a container nobody is
    searching on.
    """
    with _LOCK:
        wanted = _WARM_WANTED
    if not wanted:
        return False
    if query_may_load():
        # The switch is off, so no search was ever refused a load and there is
        # nothing to make good. Warming here would be the behaviour change
        # outside the switch that query_may_load exists to refuse.
        return False

    held = _held(settings().embed_model_dir)
    if held is None:
        return False
    return not held.loaded and not held.artifacts_absent


def warm() -> bool:
    """Fetch the weights back in the calling thread, once per warm window.

    True when this call did the run and the engine answered. False when another
    warm run was already in flight, or when there is no model to load, which is
    a verdict and never an exception: the same stance the search side takes
    towards a missing model.

    **The promise of success criterion 5, and its two levels.**
    :meth:`~findling.embed.model.EmbeddingModel._load` runs under the lock of
    the holder and returns at its head when the engine is already bound, so ten
    concurrent warm runs raise
    :func:`~findling.embed.model.load_count` **once**. That is structural and
    holds whatever this function does. The :data:`_WARMING` flag below saves the
    nine threadpool threads that would otherwise queue at that lock. It is
    efficiency and not correctness, and it is said here plainly so that nobody
    reads the flag as the promise (14-RESEARCH.md 5.3).

    **Setting the idle clock is the condition and not a side effect.** The run
    goes through :meth:`~findling.embed.model.EmbeddingModel.embed_query` and
    therefore through ``_embed``, which writes ``_last_use``. Without that the
    next tick of the unload task would find a holder whose last use is older
    than the span and would eat the load pair that had just been paid for.

    The text is :data:`WARM_TEXT`, a fixed module constant. It travels the path
    a search line travels, so it must not be a search line: no user content and
    no file name reaches a log, a vector or a report through here (T-14-22).

    Blocking, like every load. The caller runs it through ``asyncio.to_thread``.
    """
    global _WARM_WANTED, _WARMING

    with _LOCK:
        if _WARMING:
            return False
        _WARMING = True
        # Cleared here and not at the end, because the request has been taken
        # on. A marker still standing after the run would make every later tick
        # read a warm run that has already happened.
        _WARM_WANTED = False

    try:
        return shared_model().embed_query(WARM_TEXT, may_load=True).available
    finally:
        with _LOCK:
            _WARMING = False
