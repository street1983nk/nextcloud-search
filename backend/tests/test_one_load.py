"""The gate over the doubled load, and the proof that it can go red.

``findling.tools.one_load`` is the watchman of two savings that are invisible
from the outside: one embedding engine per process (plan 06.1-02) and one read
of the constituent list per process (plan 06.1-04). Since phase 14 it watches
the promise those savings became: **never two engines at once, exactly one load
per warm window**. It drives both halves of the container in one process and
counts, and ``resilience.yml`` runs it on every push, so the return of either
regression colours a CI run rather than waiting for the next hand measurement
on the arm64 box.

**A watchman that cannot go red is worse than none**, which is the whole reason
this file exists. Six cases below bring a regression back by hand, each one at
the seam the real defect would sit at, and every one of them has to make the
tool fail:

* the search side builds its own engine again, which is the shape the code had
  before the holder in ``embed/engine.py``,
* the cache in front of ``build_artifact`` stops keying, which is the shape
  ``wordlist.py`` had before plan 06.1-04,
* the search never reaches the model at all, which is the vacuous green the
  planned RSS ceiling would have shipped: a gate that watches a load path the
  measurement does not enter,
* the search stops asking for the warm run (plan 23-04): since the cold start
  fix of plan 23-01 a round never loads by itself, the handler path
  ``if warm_wanted(): warm()`` does, and a search that forgets
  ``request_warm()`` would leave the container without semantics for good,
* a release gives up the counter and not the pages, so the container reports a
  warm window that cost nothing while the weights lie in the heap the whole
  time,
* the warm window loads twice, which is success criterion 5 of this phase read
  backwards: two sessions for one window is 276 MB twice.

The last two arrived with plan 14-10, with the fourth phase of the tool they
test. Each of them is held against the green run in
``test_the_fourth_phase_releases_the_weights_and_fetches_them_back``, so neither
of them can be passing against a tree that was red to begin with.

None of the six touches shipped code. They are monkeypatches at module and
class level, so what is proven is that the counters really are the thing the
gate stands on, without a line of sabotage travelling into the image.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy
import pytest

from findling.api import resources
from findling.api import search as search_module
from findling.config import settings
from findling.embed import engine as engine_module
from findling.embed import model as model_module
from findling.embed.chunker import ChunkSpan
from findling.embed.engine import shared_model
from findling.embed.model import DIMENSIONS, EmbeddingModel
from findling.index import wordlist as wordlist_module
from findling.tools import one_load
from findling.worker import embedding as embedding_module

if TYPE_CHECKING:
    from collections.abc import Iterator

# The recipe of the tool reads a raw word list, and there is no
# /usr/share/dict/ngerman on a developer machine. The fixture subset the endpoint
# suites use is a raw list as far as the recipe is concerned.
FIXTURE_LIST = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"


# ---------------------------------------------------------------------------
# The stand in for the artifacts, in the shape test_embed_model established:
# only the two functions that touch the files are replaced, so everything above
# them is the real code path, including the counter this gate reads.
# ---------------------------------------------------------------------------


@dataclass
class _FakeEncoding:
    ids: list[int]
    attention_mask: list[int]


class _FakeEncoder:
    """One token per text, which is everything the pooling needs."""

    def encode_batch(self, texts: list[str]) -> list[_FakeEncoding]:
        return [_FakeEncoding(ids=[1], attention_mask=[1]) for _ in texts]


@dataclass
class _FakeInput:
    name: str


class _FakeSession:
    """A graph that answers a constant hidden state of the declared width."""

    def get_inputs(self) -> list[_FakeInput]:
        return [_FakeInput("input_ids"), _FakeInput("attention_mask")]

    def get_outputs(self) -> list[_FakeInput]:
        return [_FakeInput("last_hidden_state")]

    def run(self, _outputs: list[str], feed: dict[str, Any]) -> list[Any]:
        ids = feed["input_ids"]
        return [numpy.ones((ids.shape[0], ids.shape[1], DIMENSIONS), dtype=numpy.float32)]


def _one_span(text: str, *, tokenizer: object, splitter: object, token_cap: int) -> list[ChunkSpan]:
    """Cut nothing and answer one span, so the track has a passage to embed.

    The real cut needs the 17 MB tokenizer of the image. What this suite is about
    sits behind it: which engine the track embeds through, not where a document
    is divided.
    """
    assert tokenizer is not None
    assert splitter is not None
    assert token_cap > 0
    return [ChunkSpan(ordinal=0, char_start=0, char_end=len(text))]


@pytest.fixture
def prepared(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A volume path, a pretended model, and the wiring the track needs.

    ``APP_PERSISTENT_STORAGE`` is set through monkeypatch although the tool sets
    it itself: what the fixture buys is the restore afterwards, because a case
    that left the variable behind would hand its volume to the next one.
    """
    home = tmp_path / "model"
    home.mkdir(parents=True)
    (home / "model.onnx").write_bytes(b"not a real graph")
    (home / "tokenizer.json").write_text("{}", encoding="utf-8")

    volume = tmp_path / "volume"
    monkeypatch.setenv("FINDLING_EMBED_MODEL_DIR", str(home))
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(volume))
    settings.cache_clear()

    monkeypatch.setattr(model_module, "_open_encoder", lambda _directory, *, sequence_len: _FakeEncoder())
    monkeypatch.setattr(model_module, "_open_session", lambda _path, *, threads: _FakeSession())
    # The track opens the real tokenizer and builds the real splitter, and both
    # of them read the artifact this suite does not have.
    monkeypatch.setattr(embedding_module, "open_tokenizer", lambda _directory: object())
    monkeypatch.setattr(embedding_module, "make_splitter", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(embedding_module, "chunk_spans", _one_span)
    # The warm request is a module global of the holder and outlives a case. A
    # marker left standing by the case before would warm the engine here even
    # when the search under test never asked, and the case that proves the
    # tool goes red for exactly that would be green for the wrong reason.
    monkeypatch.setattr(engine_module, "_WARM_WANTED", False)

    yield volume
    settings.cache_clear()


def _measure(volume: Path) -> one_load.Report:
    return one_load.measure(volume, source=FIXTURE_LIST)


# ---------------------------------------------------------------------------
# The green case
# ---------------------------------------------------------------------------


def test_one_process_pays_for_one_engine_and_one_word_list(prepared: Path) -> None:
    report = _measure(prepared)

    assert one_load.findings(report) == []
    assert report.wordlist_reads_after_index == 1, "the indexing side reads the list once"
    assert report.wordlist_reads_after_search == 1, "the search side takes the cache hit"
    assert report.engine_loads_after_search == 1, "the search side really reached the model"
    assert report.engine_loads_after_worker == 1, "the track shares what the search side loaded"
    assert report.engine_unloads_after_release == 1, "the fourth phase really let go of something"
    assert report.engine_loads_after_rewarm - report.engine_unloads_after_release == 1, (
        "one warm window, exactly one load"
    )
    assert report.candidates == 1, "the seeded document has to be findable, or nothing above was measured"
    assert report.passage_vectors == 1
    assert report.search_ms > 0.0, "the round itself took measurable time"
    assert report.warm_ms > 0.0, "the handler path behind it really ran the warm run"


def test_a_search_alone_never_loads_the_engine(prepared: Path) -> None:
    # Plan 23-01, D-01: ``one_round`` answers out of the lexical list while the
    # engine is cold and only asks for the warm run. This is the half of the
    # driver that must not move the counter, so the other half can be proven
    # to be the one that does.
    one_load.seed_volume(FIXTURE_LIST)
    engine_module.reset()
    loads_before = model_module.load_count()

    candidates = one_load.run_the_search()

    assert candidates == 1, "the seeded document is found lexically"
    assert model_module.load_count() == loads_before, "a search on its own never loads the weights"
    assert engine_module.warm_wanted(), "but it has asked for the warm run"


def test_the_driver_goes_the_handler_path_and_loads_exactly_once(prepared: Path) -> None:
    # What a real caller sets off: the search, and behind it the handler, which
    # runs ``warm`` once the answer is out. The driver goes both halves, so a
    # cold holder comes to exactly one load and not to nought.
    one_load.seed_volume(FIXTURE_LIST)
    engine_module.reset()
    loads_before = model_module.load_count()

    candidates = one_load.drive_the_search_side()

    assert candidates == 1
    assert model_module.load_count() - loads_before == 1, "search plus handler path, one load"
    assert not engine_module.warm_wanted(), "the request has been taken on"


def test_the_fourth_phase_releases_the_weights_and_fetches_them_back(
    prepared: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Success criterion 5, driven through the real call path and printed.

    The three phases before this one are all green in a container that can
    never let go of anything, which is the container this product was until
    this phase. So the fourth one releases the weights and drives one more real
    search round, and both of its numbers travel in the report: the release has
    to have freed exactly one engine, and the round after it has to have
    fetched back exactly one.
    """
    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 0
    assert "engine-unloads-after-release=1" in printed
    assert "engine-loads-after-rewarm=2" in printed
    assert "verdict=ok" in printed


def test_the_two_durations_are_lines_of_their_own(prepared: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Weg A of the phase research, split in two by plan 23-04: the wall clock
    # around the round itself, and the one around the warm run the handler path
    # starts behind it. They travel in the report the measurement step of
    # resilience.yml already prints in full, so neither needs a step of its own.
    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 0
    lines = printed.splitlines()
    search = next(line for line in lines if line.startswith("search-ms="))
    warm = next(line for line in lines if line.startswith("warm-ms="))
    assert float(search.removeprefix("search-ms=")) > 0.0
    assert float(warm.removeprefix("warm-ms=")) > 0.0


def test_the_entry_point_prints_its_numbers_and_exits_zero(prepared: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 0
    assert "engine-loads-after-worker=1" in printed
    assert "wordlist-reads-after-search=1" in printed
    assert "verdict=ok" in printed


# ---------------------------------------------------------------------------
# The ways it has to go red
# ---------------------------------------------------------------------------


def test_it_goes_red_when_the_search_side_builds_its_own_engine(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # The state of the code before plan 06.1-02, put back at the exact seam it
    # was removed from: the read side stops asking the holder and constructs a
    # wrapper of its own, so the container carries two tokenizers and two
    # sessions again. Since the cold start fix (plan 23-01) the search never
    # loads that wrapper itself, and the handler path can only warm the holder,
    # which this search never filled. So the search side comes to nought loads
    # while the track alone comes to one, and the tool names the zero.
    def own_engine() -> EmbeddingModel:
        resolved = settings()
        return EmbeddingModel(
            resolved.embed_model_dir,
            batch_size=resolved.embed_batch_size,
            sequence_len=resolved.embed_sequence_len,
        )

    monkeypatch.setattr(resources, "shared_model", own_engine)

    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 1
    assert "engine-loads-after-search=0" in printed
    assert "green for nothing" in printed


def test_a_second_run_in_the_same_process_measures_a_load_and_not_a_cache_hit(prepared: Path) -> None:
    # Bug audit LOW-7 of plan 07-05. The holder of the engine is a module
    # global, so it outlives a call of measure() and the second call used to
    # find the engine of the first one in it: the search side took the cache
    # hit, the load counter did not move and the tool reported "green for
    # nothing" about a run in which nothing was wrong. In the container that
    # never happens, because the container runs this tool once; the CI step and
    # this suite are the two places where it does.
    #
    # A loaded engine in the holder is the whole of the precondition, and it is
    # built here through the same call the search side uses rather than by
    # reaching into the module.
    shared_model().embed_query("bauantrag")

    report = _measure(prepared)

    assert report.engine_loads_after_search == 1, "the run has to bring the loads from nought to one again"
    assert report.engine_loads_after_worker == 1, "and the track still shares what the search side loaded"
    assert one_load.findings(report) == []


def test_it_goes_red_when_the_word_list_is_read_a_second_time(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The state of the code before this plan: without a key there is nothing to
    # remember the artifact under, so every caller reads the file again. The
    # first read still belongs to the indexing side, and the search side is the
    # one that has to show up as the second.
    monkeypatch.setattr(wordlist_module, "_artifact_key", lambda _target, _digest: None)

    report = _measure(prepared)

    assert report.wordlist_reads_after_index == 1
    assert report.wordlist_reads_after_search > 1
    assert any("coming back" in finding for finding in one_load.findings(report))


def test_it_goes_red_when_the_search_never_reaches_the_model(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # The vacuous green the planned memory ceiling would have shipped. With the
    # embedding switched off the search turns back before the semantic branch,
    # the engine is never asked, and a gate that only compared the number after
    # the track would still read one and pass.
    monkeypatch.setenv("FINDLING_EMBED_ENABLED", "0")

    report = _measure(prepared)

    assert report.engine_loads_after_search == 0
    assert report.engine_loads_after_worker == 1, "the track alone still loads once, which is the trap"
    assert any("green for nothing" in finding for finding in one_load.findings(report))


def test_it_goes_red_when_the_search_stops_asking_for_the_warm_run(
    prepared: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Plan 23-04. Since the cold start fix the round never loads by itself, and
    # ``request_warm()`` in ``one_round`` is the one way the weights are ever
    # fetched for the search side. Silence it at that seam and the handler path
    # finds nothing owed, the engine stays cold, and the tool has to say so
    # rather than time a warm run that never happened.
    with monkeypatch.context() as mutation:
        mutation.setattr(search_module, "request_warm", lambda: None)
        report = _measure(prepared / "mutated")

    assert report.engine_loads_after_search == 0
    assert report.warm_ms == 0.0, "no warm run, no duration"
    assert any("green for nothing" in finding for finding in one_load.findings(report))

    # The same tree with the mutation taken back, so the red above belongs to
    # the mutation and not to a tree that was red to begin with.
    assert one_load.findings(_measure(prepared / "clean")) == []


def test_it_goes_red_when_a_release_leaves_two_engines_behind(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A release that gives up the counter and not the pages.

    What this would be in the world is the 276 MB of plan 06.1-02, now inside
    the unload cycle: the admin page says ``unloaded``, the A/B measurement of
    phase 15 counts a warm window that cost nothing, and the weights are lying
    in the heap the whole time. The next real load would then put a second
    session beside them, which is exactly the state the holder of
    ``embed/engine.py`` exists to make impossible.

    Mutated at the seam the defect would sit at:
    :meth:`~findling.embed.model.EmbeddingModel.release` is the one function
    that raises the unload counter, and the one that has to let go of the
    engine in the same breath. Here it does the first and not the second, and
    the tool has to see it in the difference and not in a byte.
    """

    def a_release_that_only_counts(self: EmbeddingModel) -> bool:
        assert self is not None
        model_module._UNLOAD_COUNT += 1
        return True

    monkeypatch.setattr(EmbeddingModel, "release", a_release_that_only_counts)

    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 1
    assert "engine-unloads-after-release=1" in printed
    assert "engine-loads-after-rewarm=1" in printed, "the round behind the release took a cache hit"
    assert "the warm window after the release came to 0 loads" in printed
    assert "let go of a counter instead of an engine" in printed


def test_it_goes_red_when_the_warm_up_loads_twice(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Success criterion 5 in its own words: exactly one load per warm window.

    ``EmbeddingModel._load`` returns at its head when the engine is already
    bound, and that early return is the whole of the promise: ten concurrent
    warm runs raise the load counter once whatever the ``_WARMING`` flag of
    ``embed/engine.py`` does, which is why that flag is written down as
    efficiency and never as the promise (14-RESEARCH.md 5.3). Take the early
    return away inside the warm window and two sessions arrive for one window,
    which is 276 MB twice on a box with 210 MB of headroom.

    The mutation is keyed on the unload counter so that it bites in the fourth
    phase alone. A single flight broken from the first phase on would make the
    second track load a second time too, the tool would go red at the old
    counter, and this case would be proving the wrong finding.
    """
    original_load = EmbeddingModel._load
    unloads_at_start = model_module.unload_count()

    def load_without_the_single_flight(self: EmbeddingModel) -> Any:
        engine = original_load(self)
        if engine is not None and model_module.unload_count() > unloads_at_start:
            self._engine = None
            engine = original_load(self)
        return engine

    monkeypatch.setattr(EmbeddingModel, "_load", load_without_the_single_flight)

    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 1
    assert "engine-loads-after-worker=1" in printed, "the three phases in front of the window stay untouched"
    assert "engine-unloads-after-release=1" in printed
    assert "engine-loads-after-rewarm=3" in printed
    assert "the warm window after the release came to 2 loads" in printed
    assert "two sessions were built for one window" in printed


# ---------------------------------------------------------------------------
# The verdict itself, without a volume
# ---------------------------------------------------------------------------


def test_every_counter_that_is_not_one_is_named() -> None:
    report = one_load.Report(
        wordlist_reads_after_index=2,
        wordlist_reads_after_search=3,
        engine_loads_after_search=0,
        engine_loads_after_worker=2,
        engine_unloads_after_release=0,
        engine_loads_after_rewarm=0,
        candidates=0,
        passage_vectors=0,
        search_ms=12.5,
        warm_ms=40.0,
    )

    assert len(one_load.findings(report)) == 8


def test_a_release_that_freed_nothing_is_a_finding() -> None:
    """The anti-vacuity clause of the fourth phase, in the shape of the other three.

    A release that let go of nothing makes every number behind it meaningless:
    the engine never left, so the round that follows takes a cache hit and
    reports a warm window that cost no load at all. Both halves of that have to
    be named, because an admin who reads one of them without the other would
    raise the wrong number.
    """
    report = one_load.Report(
        wordlist_reads_after_index=1,
        wordlist_reads_after_search=1,
        engine_loads_after_search=1,
        engine_loads_after_worker=1,
        engine_unloads_after_release=0,
        engine_loads_after_rewarm=1,
        candidates=1,
        passage_vectors=1,
        search_ms=12.5,
        warm_ms=40.0,
    )

    trouble = one_load.findings(report)

    assert any("released nothing" in finding for finding in trouble)
    assert any("warm window" in finding for finding in trouble)


def test_a_clean_report_names_nothing() -> None:
    report = one_load.Report(
        wordlist_reads_after_index=1,
        wordlist_reads_after_search=1,
        engine_loads_after_search=1,
        engine_loads_after_worker=1,
        engine_unloads_after_release=1,
        engine_loads_after_rewarm=2,
        candidates=1,
        passage_vectors=1,
        search_ms=12.5,
        warm_ms=40.0,
    )

    assert one_load.findings(report) == []
    assert "candidates=1" in report.lines()


def test_the_duration_is_reported_and_never_judged() -> None:
    # The mirror image of the memory ceiling resilience.yml turned down: a
    # millisecond ceiling on a shared runner goes red for runner load and not
    # for the thing it names. So a report whose counters are all one has no
    # finding, however long the round took.
    report = one_load.Report(
        wordlist_reads_after_index=1,
        wordlist_reads_after_search=1,
        engine_loads_after_search=1,
        engine_loads_after_worker=1,
        engine_unloads_after_release=1,
        engine_loads_after_rewarm=2,
        candidates=1,
        passage_vectors=1,
        search_ms=900_000.0,
        warm_ms=900_000.0,
    )

    assert one_load.findings(report) == []
    assert "search-ms=900000.0" in report.lines()
    assert "warm-ms=900000.0" in report.lines()
