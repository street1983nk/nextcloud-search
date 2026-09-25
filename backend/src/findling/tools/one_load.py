"""One process, one engine, one constituent list: the gate over the doubled load.

Plans 06.1-02 and 06.1-04 each removed one half of a doubled load. The engine
holder in :mod:`findling.embed.engine` made the search side and the second track
share one tokenizer and one onnxruntime session, and the cache in
:func:`findling.index.wordlist.build_artifact` made the constituent list travel
into the process once instead of twice. Both savings are invisible from the
outside a week later, and the return of either one would be a silent 276 MB and
21.9 MB on a box with 210 MB of headroom.

**The promise this gate stands on, in the words it has since phase 14.** Not
"exactly one load per process" any more. The switch of MEM-01 hands the weights
back in an idle span, so a container that has been up for a day may have read
them four times and be working exactly as designed; a gate that still asserted
one load per process would go red for the feature it was asked to watch. The
promise is **never two engines at once, exactly one load per warm window**, and
it is written in the two counters of ``embed/model.py`` and in no byte:

* Never two engines: ``loads - unloads`` is never above one and never below
  nought, at any moment of the run.
* One load per warm window: ``loads - unloads`` stands at one after a warm run
  and still at one after the next one.
* No greening by zeroing: both counters are monotonic, nothing sets either of
  them back, and ``engine.reset()`` deliberately does not either, because a
  counter that can be zeroed is a counter a gate could zero itself green with
  (T-14-17).

**Why this exists instead of a memory ceiling in CI.** The measurement step of
``resilience.yml`` starts the container on an empty ``APP_PERSISTENT_STORAGE``,
so ``read_side()`` answers None, the search turns back before it reaches the
word list, the automaton or the model, and the difference between the resident
figures before and after the first search was measured at 241 KB and 503 KB on
2026-09-06: runner noise around a load path that never ran. A ceiling over that
number would be a gate that cannot go red for the thing it names, and this
repository refuses that shape everywhere else. So the gate is a counter and not
a byte, which is the pattern that carried plan 06.1-02: ``load_count()`` next to
``read_count()``, and both of them tell a cache hit from a cheap second load,
which no resident memory reading on a shared runner can do.

**The order of the four phases is the anti-vacuity clause.** A gate that
asserts "one load" is green for nothing when the load path is never entered. So
the search side runs BEFORE the second track, and its own number is asserted:

1. the indexing side seeds a volume and reads the constituent list once,
2. the search side runs one real round, which has to bring the engine loads to
   exactly one, so a measurement that never reached the model reports a zero and
   fails instead of passing,
3. the second track wires itself the way a pass does and embeds one document,
   and the engine loads have to still be one, which is the sharing itself,
4. the weights are released and one more real round fetches them back, which is
   the warm window itself: the unloads have to come to exactly one, and the
   loads of the window with them.

**The fourth phase carries its own anti-vacuity condition, and it is the
sharper of the two.** A release that freed nothing leaves the engine exactly
where it was, so the round behind it takes a cache hit, reports a window that
cost no load at all, and every number after it says nothing. ``unloads == 0`` is
therefore a finding here and never a quiet green. It is the trap the memory
ceiling would have shipped, one phase further on: a gate that watches a release
path the measurement never enters.

Every number is measured through the real call: ``api/search.py::one_round`` for
the search side and for the warm window, and ``Poller._wire_the_second_track``
for the track, so a caller that stops going through the holder is caught rather
than a caller this tool wrote itself.

**It builds its own volume.** A fresh directory per run, seeded with one
document, one permission row and an empty vector stock. That is exactly what the
measurement container lacks, and it costs one tantivy commit and one query.

**The ninth number is a duration, and it is reported and never judged.** The
one search round this tool drives is the round that brings the engine loads from
zero to one, so the wall clock around it is a cold start duration and it costs
one line. A millisecond ceiling over that line would be the mirror image of the
memory ceiling this repository already turned down: on a shared runner it goes
red for runner load and not for the thing it names, and the argument is written
out in ``resilience.yml`` in the comment before the ratchet step. So the number
travels in the report, the runs collect the series, and ``findings()`` does not
look at it.

**Why that series is worth having next to the integration run.** This tool runs
on every push and its number is a load inside one process, without Apache, the
AppAPI and the PHP half. The figure that carries the report comes from the cold
semantic search of the ``index-search-e2e`` job in ``integration.yml``, which
goes the whole way a user goes. Two numbers over two ways, and neither of them
pretends to be the other.

Run it with::

    uv run python -m findling.tools.one_load

The exit code is the gate: 0 when every number is what the promise above says
it has to be, 1 with a named finding for every number that is not.
"""

from __future__ import annotations

import argparse
import logging
import os
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from tantivy import Document

from findling.api.search import one_round
from findling.config import settings
from findling.embed.engine import reset as forget_the_engine
from findling.embed.engine import shared_model
from findling.embed.model import load_count, unload_count
from findling.index.open import expected_versions, open_index
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.index.wordlist import SYSTEM_WORDLIST, build_artifact, read_count
from findling.index.wordlist_nl import dutch_digest_for, dutch_mark
from findling.store.repo import FileMeta, open_store
from findling.store.vectors import open_vectors
from findling.worker import poller as poller_module

LOGGER = logging.getLogger("findling.tools.one_load")

# The user of the measurement. It reaches the prefilter as a plain string, so any
# value works as long as the permission row below carries the same one.
MEASURE_USER: Final = "measurement"

# The one document, and the line that has to find it. The body keeps its umlauts
# because the analyzer chain is what the search side opens, and a folded body
# would exercise a tokenisation this app never performs.
DOCUMENT_TITLE: Final = "Akte 1"
DOCUMENT_NAME: Final = "Akte-1.pdf"
DOCUMENT_PATH: Final = "/Akten/Akte-1.pdf"
DOCUMENT_BODY: Final = "Für alle Beschäftigten gilt: die Kündigungsfrist im Vertrag beträgt drei Monate."
# Two words on purpose: since the 06.1-20 addendum a single-word line stays
# lexical and would never reach the engine, so a one-word probe here would
# measure the rule instead of the load. Both words stand in DOCUMENT_BODY.
QUERY: Final = "Vertrag Monate"

FILE_ID: Final = 1
STORAGE_ID: Final = 1
MTIME: Final = 1_700_000_000

# Enough for one hit, and far below the cap the request model enforces.
SEARCH_LIMIT: Final = 10

# The heap one commit of one document gets. The figure the endpoint suites hand
# their writer, because it is a floor of tantivy and not a tuning decision.
WRITER_HEAP_BYTES: Final = 15_000_000

# What every counter of this measurement has to come to. One process reads the
# artifacts once, whichever half of the container asks first.
EXPECTED: Final = 1


@dataclass(frozen=True, slots=True)
class Report:
    """The eight counters one run of the measurement comes to, and one duration.

    Two counters per side rather than one at the end, because the difference
    between them is the statement: the constituent list may only be read by the
    side that seeded the volume, and the engine has to be loaded by the search
    side and then not again by the track.

    The last two are the warm window of phase four, and they are a pair for the
    same reason: neither of them says anything alone. A release without a load
    behind it is a container that gave its semantics away, a load without a
    release in front of it is a second engine, and it is the difference between
    them that carries the promise.

    The ninth field is the odd one out: it is an observation and not a gate.
    ``findings()`` reads the eight counters and never the duration, because a
    millisecond ceiling on a shared runner would go red for runner load instead
    of for the load path it names, which is the same argument the comment before
    the ratchet step of ``resilience.yml`` makes for the resident memory series.
    """

    wordlist_reads_after_index: int
    wordlist_reads_after_search: int
    engine_loads_after_search: int
    engine_loads_after_worker: int
    engine_unloads_after_release: int
    engine_loads_after_rewarm: int
    candidates: int
    passage_vectors: int
    cold_search_ms: float

    def lines(self) -> list[str]:
        """The report as plain key=value lines, for a log a shell can read."""
        return [
            f"wordlist-reads-after-index={self.wordlist_reads_after_index}",
            f"wordlist-reads-after-search={self.wordlist_reads_after_search}",
            f"engine-loads-after-search={self.engine_loads_after_search}",
            f"engine-loads-after-worker={self.engine_loads_after_worker}",
            f"engine-unloads-after-release={self.engine_unloads_after_release}",
            f"engine-loads-after-rewarm={self.engine_loads_after_rewarm}",
            f"candidates={self.candidates}",
            f"passage-vectors={self.passage_vectors}",
            f"cold-search-ms={round(self.cold_search_ms, 1)}",
        ]


def _meta() -> FileMeta:
    """The metadata row of the one document, as the crawl would have written it."""
    return FileMeta(
        storage_id=STORAGE_ID,
        root_id=1,
        path=DOCUMENT_PATH,
        title=DOCUMENT_NAME,
        mime="application/pdf",
        size=len(DOCUMENT_BODY.encode("utf-8")),
        mtime=MTIME,
    )


def _write_index(directory: Path, constituents: Sequence[str], *, dutch: str | None) -> None:
    """Write and commit the one document the search below has to find.

    Field by field and never through keyword arguments: a keyword built document
    puts an I64 into the U64 column of the file id, and the indexing thread
    panics after the Python call has already returned.
    """
    index = open_index(directory, constituents, dutch=dutch)
    writer = index.writer(heap_size=WRITER_HEAP_BYTES, num_threads=1)
    document = Document()
    document.add_unsigned(FIELD_FILE_ID, FILE_ID)
    document.add_unsigned(FIELD_STORAGE_ID, STORAGE_ID)
    document.add_text(FIELD_NAME, DOCUMENT_NAME)
    document.add_text(FIELD_TITLE, DOCUMENT_TITLE)
    document.add_text(FIELD_PATH, DOCUMENT_PATH)
    document.add_text(FIELD_EXT, "pdf")
    document.add_text(FIELD_BODY_DE, DOCUMENT_BODY)
    document.add_integer(FIELD_MTIME, MTIME)
    writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()


def seed_volume(source: Path = SYSTEM_WORDLIST) -> None:
    """Put a volume in place that has indexed exactly one document.

    The indexing half of the container, in the order it works in: the constituent
    list first, because the analyzer chain of the index is built out of it, then
    the index, then the verdict and the permission row, then the vector stock.

    The empty vector stock is not decoration. ``read_side()`` opens it read only
    and refuses a missing file, and without it the search below would leave the
    semantic branch out, the engine would never be asked for anything, and the
    counter of the third phase would be green for nothing.
    """
    artifact = build_artifact(source=source)
    resolved = settings()
    _write_index(resolved.index_dir, artifact.entries, dutch=dutch_digest_for(resolved.languages))

    languages = resolved.languages
    marks = expected_versions(artifact.digest, ",".join(languages), dutch_mark=dutch_mark(languages))
    store = open_store(resolved.state_db, meta=marks)
    try:
        store.replace_acl(FILE_ID, [MEASURE_USER])
        store.record(FILE_ID, _meta(), "indexed")
    finally:
        store.close()

    open_vectors(resolved.vectors_db).close()


def drive_the_search_side() -> int:
    """Run one real search round and return how many candidates it came to.

    ``one_round`` and not a hand written path: it is the function the endpoint
    calls, it opens the read side, and it builds the semantic bundle out of
    ``resources.query_model()``. Every one of those steps is a place where a
    second engine or a second read of the word list would come back.
    """
    page = one_round(MEASURE_USER, QUERY, SEARCH_LIMIT, 0, False)
    return len(page.candidates)


def drive_the_second_track() -> int:
    """Wire the embedding track like a pass does, embed one document, count vectors.

    The three attributes are read rather than rebuilt, because the wiring is the
    thing under measurement: ``_embed_document`` reads exactly these three on
    every row, and a copy of the wiring here would measure the copy.

    Both halves of the wiring are driven, in the order a pass drives them. Since
    plan 07-03 the first one opens the vector stock and promises the rest, and
    the second one builds the tokenizer, the splitter and the engine at the
    first row that needs them; a tool that called only the first would read
    ``_chunker`` as None and report a track that stayed off, which is a
    measurement of this function and not of the container.
    """
    worker = poller_module.Poller()
    worker._wire_the_second_track()
    worker._build_the_cutter()
    model = worker._model
    chunker = worker._chunker
    stock = worker._vectors
    try:
        if model is None or chunker is None:
            LOGGER.warning("the second track stayed off, so the shared engine was never asked for a passage")
            return 0
        spans = chunker(DOCUMENT_BODY)
        outcome = model.embed_passages([DOCUMENT_BODY[span.char_start : span.char_end] for span in spans])
    finally:
        if stock is not None:
            stock.close()
    if not outcome.available:
        LOGGER.warning("the engine answered no vectors for the passages of the second track")
        return 0
    return len(outcome.vectors)


def measure(root: Path, *, source: Path = SYSTEM_WORDLIST) -> Report:
    """Drive both halves of the container in this process and count what they read.

    The volume is pointed at through the environment and the settings cache is
    cleared afterwards, which is the handle the test suite uses as well: the
    settings are resolved once per process by design, and this tool is the
    process they are resolved for.

    Every number is a difference against a baseline taken here rather than the
    raw counter. In the container the two are the same, because nothing has run
    before this function; inside a test suite they are not, and a tool whose
    gate only holds in a virgin process cannot be proven able to go red.

    **The engine holder is emptied for the same reason, and a difference cannot
    do it** (bug audit LOW-7 of plan 07-05). The second phase below has to bring
    the loads from nought to one, and that is a statement about a load and not
    about a counter: a second run in the same process used to find the engine of
    the first one in the holder, take the cache hit and report "green for
    nothing" about a tool that was working perfectly. Emptying it is the only
    way to ask the question again, and it is why ``engine.reset()`` exists.
    """
    os.environ["APP_PERSISTENT_STORAGE"] = str(root)
    settings.cache_clear()
    forget_the_engine()

    reads_at_start = read_count()
    loads_at_start = load_count()
    unloads_at_start = unload_count()

    seed_volume(source)
    reads_after_index = read_count() - reads_at_start

    # The clock sits in the caller and not in the driver, because the driver is
    # the thing under measurement: a stopwatch inside it would time its own
    # unpacking as well. This round is the one that brings the engine loads from
    # zero to one, so what it times is a cold start.
    started = time.perf_counter()
    candidates = drive_the_search_side()
    cold_search_ms = (time.perf_counter() - started) * 1000.0
    reads_after_search = read_count() - reads_at_start
    loads_after_search = load_count() - loads_at_start

    passages = drive_the_second_track()
    loads_after_worker = load_count() - loads_at_start

    # Phase four, the warm window. The three phases above are all green on a
    # container that is physically unable to let go of anything, which is the
    # container this product was until phase 14, so none of them can see the
    # promise this gate has carried since.
    #
    # **The release is taken here rather than through ``release_if_idle``, and
    # that is this tool reaching under the policy on purpose.** That function
    # carries the clock, and the span it reads comes out of
    # ``settings().embed_idle_release_seconds``, where nought is the word for
    # off: with the switch in its factory position it answers False at once and
    # would measure nothing, and with the switch on the tool would sit out an
    # admin setting. What this gate is about is the mechanics of the promise
    # and never the deadline, and a deadline has no business inside a
    # measurement run. So the holder is asked to let go, and then the counter
    # is read.
    shared_model().release()
    unloads_after_release = unload_count() - unloads_at_start

    # And back again through the real call path, the same one phase two used,
    # and not through ``engine.warm()``. This tool has measured through the way
    # a caller really goes since it was written, for the reason
    # ``drive_the_search_side`` gives: a caller that stops going through the
    # holder has to be caught here and not measured around.
    drive_the_search_side()
    loads_after_rewarm = load_count() - loads_at_start

    return Report(
        wordlist_reads_after_index=reads_after_index,
        wordlist_reads_after_search=reads_after_search,
        engine_loads_after_search=loads_after_search,
        engine_loads_after_worker=loads_after_worker,
        engine_unloads_after_release=unloads_after_release,
        engine_loads_after_rewarm=loads_after_rewarm,
        candidates=candidates,
        passage_vectors=passages,
        cold_search_ms=cold_search_ms,
    )


def findings(report: Report) -> list[str]:
    """Name every number that is not what one process is supposed to pay.

    A list and not a boolean, because the two regressions this gate watches for
    are different findings with different remedies, and a run that hit both has
    to say both.

    ``cold_search_ms`` is deliberately absent from every branch below. It is
    reported and not judged, for the reason the module docstring gives.

    The last two branches are the warm window, and the first of the two is the
    anti-vacuity clause of phase four: a release that freed nothing makes the
    load count behind it a cache hit, so it is named before the window itself
    is judged rather than left to show up as a nought somebody has to
    interpret.
    """
    found: list[str] = []
    if report.wordlist_reads_after_index != EXPECTED:
        found.append(
            f"the indexing side read the constituent list {report.wordlist_reads_after_index} times, "
            f"expected {EXPECTED}: the cache in build_artifact does not even hold within one side"
        )
    if report.wordlist_reads_after_search != EXPECTED:
        found.append(
            f"the constituent list stands at {report.wordlist_reads_after_search} reads after the first search, "
            f"expected {EXPECTED}: the search side reads it a second time again, which is the 21.9 MB of plan "
            "06.1-04 coming back"
        )
    if report.engine_loads_after_search != EXPECTED:
        found.append(
            f"the search side brought the engine to {report.engine_loads_after_search} loads, expected {EXPECTED}: "
            "a zero means this measurement never reached the model, so every number after it would be green for "
            "nothing, and the causes are the embedding switched off, missing artifacts, or a search that turned "
            "back before the semantic branch"
        )
    if report.engine_loads_after_worker != EXPECTED:
        found.append(
            f"the engine stands at {report.engine_loads_after_worker} loads after the second track wired itself, "
            f"expected {EXPECTED}: the two halves no longer share the holder in embed/engine.py, which is the "
            "276 MB of plan 06.1-02 coming back. This is the window BEFORE the release; the one behind it is the "
            "two numbers below"
        )
    if report.engine_unloads_after_release != EXPECTED:
        found.append(
            f"the release freed {report.engine_unloads_after_release} engines, expected {EXPECTED}: the fourth "
            "phase released nothing, so it measured nothing, and the load count behind it is a cache hit and not "
            "a warm window; either the holder was already empty or release() found a batch in flight"
        )
    window = report.engine_loads_after_rewarm - report.engine_unloads_after_release
    if window != EXPECTED:
        found.append(
            f"the warm window after the release came to {window} loads, expected {EXPECTED}: a nought means the "
            "weights were never fetched back and the release let go of a counter instead of an engine, and "
            "anything above one means two sessions were built for one window, which is the 276 MB of plan "
            "06.1-02 coming back inside the unload cycle"
        )
    if report.candidates < 1:
        found.append(
            "the search found nothing, so it did not run the path this gate measures, and the counters above say "
            "nothing about a search that never happened"
        )
    if report.passage_vectors < 1:
        found.append("the second track embedded nothing, so the load it is supposed to share was never asked for")
    return found


def main(argv: Sequence[str] | None = None) -> int:
    """Measure, print, and return the exit code the gate stands on."""
    parser = argparse.ArgumentParser(description="Prove that one process pays for one engine and one word list.")
    parser.add_argument("--volume", type=Path, default=None, help="volume to build in, by default a fresh directory")
    parser.add_argument("--source", type=Path, default=SYSTEM_WORDLIST, help="raw word list the recipe reads")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

    root = Path(tempfile.mkdtemp(prefix="findling-one-load-")) if args.volume is None else args.volume
    report = measure(root, source=args.source)
    for line in report.lines():
        print(line)

    trouble = findings(report)
    for line in trouble:
        print(f"finding {line}")
    print("verdict=" + ("ok" if not trouble else "failed"))
    return 1 if trouble else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
