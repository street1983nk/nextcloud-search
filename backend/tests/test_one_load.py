"""The gate over the doubled load, and the proof that it can go red.

``findling.tools.one_load`` is the watchman of two savings that are invisible
from the outside: one embedding engine per process (plan 06.1-02) and one read
of the constituent list per process (plan 06.1-04). It drives both halves of the
container in one process and counts, and ``resilience.yml`` runs it on every
push, so the return of either regression colours a CI run rather than waiting
for the next hand measurement on the arm64 box.

**A watchman that cannot go red is worse than none**, which is the whole reason
this file exists. Three of the four cases below bring a regression back by hand,
each one at the seam the real defect would sit at, and every one of them has to
make the tool fail:

* the search side builds its own engine again, which is the shape the code had
  before the holder in ``embed/engine.py``,
* the cache in front of ``build_artifact`` stops keying, which is the shape
  ``wordlist.py`` had before this plan,
* the search never reaches the model at all, which is the vacuous green the
  planned RSS ceiling would have shipped: a gate that watches a load path the
  measurement does not enter.

None of the three touches shipped code. They are monkeypatches at module level,
so what is proven is that the counters really are the thing the gate stands on,
without a line of sabotage travelling into the image.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy
import pytest

from findling.api import resources
from findling.config import settings
from findling.embed import model as model_module
from findling.embed.chunker import ChunkSpan
from findling.embed.engine import shared_model
from findling.embed.model import DIMENSIONS, EmbeddingModel
from findling.index import wordlist as wordlist_module
from findling.tools import one_load
from findling.worker import poller as poller_module

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
    monkeypatch.setattr(poller_module, "open_tokenizer", lambda _directory: object())
    monkeypatch.setattr(poller_module, "make_splitter", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(poller_module, "chunk_spans", _one_span)

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
    assert report.candidates == 1, "the seeded document has to be findable, or nothing above was measured"
    assert report.passage_vectors == 1
    assert report.cold_search_ms > 0.0, "the round that loaded the engine took measurable time"


def test_the_cold_start_duration_is_a_line_of_its_own(prepared: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Weg A of the phase research: the wall clock around the one round that
    # brings the engine loads from zero to one. It travels in the report the
    # measurement step of resilience.yml already prints in full, so it needs no
    # step of its own.
    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 0
    duration = next(line for line in printed.splitlines() if line.startswith("cold-search-ms="))
    assert float(duration.removeprefix("cold-search-ms=")) > 0.0


def test_the_entry_point_prints_its_numbers_and_exits_zero(prepared: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = one_load.main(["--volume", str(prepared), "--source", str(FIXTURE_LIST)])

    printed = capsys.readouterr().out
    assert code == 0
    assert "engine-loads-after-worker=1" in printed
    assert "wordlist-reads-after-search=1" in printed
    assert "verdict=ok" in printed


# ---------------------------------------------------------------------------
# The three ways it has to go red
# ---------------------------------------------------------------------------


def test_it_goes_red_when_the_search_side_builds_its_own_engine(
    prepared: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # The state of the code before plan 06.1-02, put back at the exact seam it
    # was removed from: the read side stops asking the holder and constructs a
    # wrapper of its own, so the container carries two tokenizers and two
    # sessions again.
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
    assert "engine-loads-after-worker=2" in printed
    assert "no longer share the holder" in printed


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


# ---------------------------------------------------------------------------
# The verdict itself, without a volume
# ---------------------------------------------------------------------------


def test_every_counter_that_is_not_one_is_named() -> None:
    report = one_load.Report(
        wordlist_reads_after_index=2,
        wordlist_reads_after_search=3,
        engine_loads_after_search=0,
        engine_loads_after_worker=2,
        candidates=0,
        passage_vectors=0,
        cold_search_ms=12.5,
    )

    assert len(one_load.findings(report)) == 6


def test_a_clean_report_names_nothing() -> None:
    report = one_load.Report(
        wordlist_reads_after_index=1,
        wordlist_reads_after_search=1,
        engine_loads_after_search=1,
        engine_loads_after_worker=1,
        candidates=1,
        passage_vectors=1,
        cold_search_ms=12.5,
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
        candidates=1,
        passage_vectors=1,
        cold_search_ms=900_000.0,
    )

    assert one_load.findings(report) == []
    assert "cold-search-ms=900000.0" in report.lines()
