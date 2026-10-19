"""The house rules of the distance measurement, as a gate instead of a review note.

``scripts/dev/vector_distances.py`` produced the two numbers the vector gate runs
on, and it lives outside ``src/`` where no ordinary test reaches it. Three of its
promises are mechanical, so they are checked here rather than remembered.

* **It agrees with the store instead of rebuilding it.** The stock ranks under
  ``vec_distance_l2`` over an ``int8[384]`` column, and the tool computes the
  same number in this process. The case below puts known vectors into a real
  :class:`~findling.store.vectors.VectorStore`, lets ``nearest`` answer and
  compares. This is the case that goes red the day somebody rebuilds the metric
  instead of using it, and a threshold measured against a different metric is a
  threshold for a search this container does not run.
* **It never prints content.** Neither the script nor its report may carry a
  query or a passage of the three language test set (T-06.1-86, pattern
  T-06-11). Checked as the absence of the two field names on the output side.
* **No em dash and no en dash**, which is a project wide typography rule, in the
  script and in the report it produced.

The measuring runs themselves are not here and cannot be: they need 118 MB of
weights that exist inside the image and nowhere on a development machine, which
is the same split ``test_ocr.py`` makes. What is testable without the artifact is
everything above, plus the arithmetic of the tool over a handful of numbers.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path
from typing import Any

import pytest

from findling.embed.model import DIMENSIONS, to_int8
from findling.store.vectors import Chunk, open_vectors

REPOSITORY = Path(__file__).resolve().parents[2]
TOOL = REPOSITORY / "scripts" / "dev" / "vector_distances.py"
REPORT = REPOSITORY / "docs" / "measurements" / "2026-09-06-vektordistanzen" / "README.md"

# Assembled from code points so that this file does not carry the characters it
# forbids and fail on itself.
DASHES = (chr(0x2014), chr(0x2013))

# The two field names of testdata/semantik. Assembled for the same reason as the
# dashes: a literal here would be found by the very check below.
QUERY_FIELD = "quer" + "y"
PASSAGE_FIELD = "passa" + "ge"


@pytest.fixture(scope="module")
def tool() -> Any:
    """The measurement script, imported by path because scripts/dev is not a package."""
    spec = importlib.util.spec_from_file_location("vector_distances", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def stock() -> dict[int, bytes]:
    """Four known vectors: identical, between two axes, orthogonal, opposite."""
    share = 1.0 / math.sqrt(2.0)
    return {
        1: to_int8(tuple(1.0 if index == 0 else 0.0 for index in range(DIMENSIONS))),
        2: to_int8(tuple(share if index in (0, 1) else 0.0 for index in range(DIMENSIONS))),
        3: to_int8(tuple(1.0 if index == 1 else 0.0 for index in range(DIMENSIONS))),
        4: to_int8(tuple(-1.0 if index == 0 else 0.0 for index in range(DIMENSIONS))),
    }


# ---------------------------------------------------------------------------
# The one case that cannot be replaced by a stand-in
# ---------------------------------------------------------------------------


def test_the_tool_computes_the_distance_the_store_ranks_on(
    tool: Any,
    stock: dict[int, bytes],
    tmp_path: Path,
) -> None:
    """The arithmetic of the tool against ``nearest`` of a real vector store.

    A stand-in would answer whatever the tool computes, and the whole point of
    the comparison is that the stock has an opinion of its own: the metric is a
    property of the vec0 column and not of the measuring process.
    """
    query = stock[1]
    vectors = open_vectors(tmp_path / "vectors.db")
    try:
        for file_id, vector in stock.items():
            vectors.replace_chunks(file_id, [Chunk(ordinal=0, char_start=0, char_end=1, embedding=vector)])
        answered = vectors.nearest(query, len(stock), k_max=len(stock))
    finally:
        vectors.close()

    assert len(answered) == len(stock)
    for neighbour in answered:
        own = tool.l2_distance(query, stock[neighbour.file_id])
        assert own == pytest.approx(neighbour.distance, abs=1e-4), neighbour.file_id


def test_the_scale_of_the_metric_is_the_scale_the_thresholds_live_on(tool: Any, stock: dict[int, bytes]) -> None:
    """0 identical, 127*sqrt(2) orthogonal, 254 opposite, because to_int8 scales by 127.

    Every threshold of ``config.py`` is a number on this scale and on no other,
    so the three anchors are asserted rather than described.
    """
    assert tool.l2_distance(stock[1], stock[1]) == pytest.approx(0.0)
    assert tool.l2_distance(stock[1], stock[3]) == pytest.approx(127.0 * math.sqrt(2.0), abs=1e-3)
    assert tool.l2_distance(stock[1], stock[4]) == pytest.approx(254.0)
    assert pytest.approx(254.0) == tool.METRIC_MAXIMUM


def test_the_selftest_of_the_tool_is_green(tool: Any) -> None:
    """The command line the report quotes, run as a test rather than trusted."""
    report = tool.selftest()

    assert "the tool and the store agree" in report
    assert "179.6051" in report


# ---------------------------------------------------------------------------
# The privacy contract of the tool and of its report
# ---------------------------------------------------------------------------


def test_the_tool_names_neither_of_the_two_content_fields_in_its_output(tool: Any) -> None:
    """Identifiers, file names and numbers leave this tool. Content does not.

    Read on the report building functions rather than on the whole file: the
    loader has to know the names of the fields it reads, and forbidding them
    there would forbid reading the data set at all. What must not happen is one
    of them reaching an output line (T-06.1-86).
    """
    import inspect

    printing = (
        tool.testset_report,
        tool.corpus_report,
        tool.derivation_report,
        tool.selftest,
        tool._gate_effect,
        tool._probe_effect,
        tool.similar_population_report,
        tool.similar_corpus_report,
        tool.similar_derivation_report,
        tool.group_report,
        tool.similar_verdict,
        tool.run_similar,
    )
    for function in printing:
        source = inspect.getsource(function)
        assert f'record["{QUERY_FIELD}"]' not in source, function.__name__
        assert f'record["{PASSAGE_FIELD}"]' not in source, function.__name__
        assert ".probe_text" not in source, function.__name__


def test_the_measurement_classes_carry_identifiers_and_numbers_and_no_text(tool: Any) -> None:
    """A dataclass that holds a passage would leak it through any repr of it."""
    import dataclasses

    for name in ("LanguageMeasurement", "CorpusChunk", "ProbeMeasurement", "SimilarPopulation", "GroupProbe"):
        fields = {field.name for field in dataclasses.fields(getattr(tool, name))}
        assert "passage" not in fields, name
        assert "text" not in fields, name


def test_the_report_carries_no_case_of_the_test_set(tool: Any) -> None:
    """The report quotes numbers, file names and identifiers, never a case.

    Checked through the identifiers rather than through the texts, because the
    texts cannot be quoted here either: a case that stood in this file would be
    the leak the case is guarding against.
    """
    text = REPORT.read_text(encoding="utf-8")
    dataset = REPOSITORY / "testdata" / "semantik" / "de.jsonl"
    import json

    for line in dataset.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        assert record[QUERY_FIELD] not in text, record["id"]
        assert record[PASSAGE_FIELD] not in text, record["id"]
    assert tool.PARAPHRASE_WANTS in text


# ---------------------------------------------------------------------------
# Typography, in the two files this plan produced
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("path", [TOOL, REPORT], ids=lambda path: Path(path).name)
def test_the_file_carries_neither_kind_of_dash(path: Path) -> None:
    text = Path(path).read_text(encoding="utf-8")
    for dash in DASHES:
        assert dash not in text, f"{dash!r} in {Path(path).name}"


def test_the_report_names_the_metric_and_the_reservation() -> None:
    """Three things the report may never lose: the metric, the OCR caveat, the finding."""
    text = REPORT.read_text(encoding="utf-8")

    assert "L2" in text
    assert "OCR" in text
    assert "VECTOR_MAX_DISTANCE" in text
    assert "VECTOR_DISTANCE_BAND" in text


# ---------------------------------------------------------------------------
# The arithmetic of the derivation, over a handful of numbers
# ---------------------------------------------------------------------------


def test_the_gate_of_the_tool_keeps_only_what_is_under_both_numbers(tool: Any) -> None:
    """The mask the derivation searched the grid with, on one readable row."""
    import numpy as np

    row = np.array([[10.0, 12.0, 30.0, 90.0]])

    kept = tool.near_enough_rows(row, ceiling=50.0, band=5.0)

    assert kept.tolist() == [[True, True, False, False]]


def test_the_band_of_the_tool_is_measured_against_the_smallest_and_not_the_first(tool: Any) -> None:
    """An unsorted row answers the same mask as the sorted one, or the grid lied."""
    import numpy as np

    ascending = np.array([[10.0, 12.0, 30.0]])
    shuffled = np.array([[30.0, 10.0, 12.0]])

    assert tool.near_enough_rows(ascending, ceiling=50.0, band=5.0).tolist() == [[True, True, False]]
    assert tool.near_enough_rows(shuffled, ceiling=50.0, band=5.0).tolist() == [[False, True, True]]


# ---------------------------------------------------------------------------
# The similar mode (Plan 35-04): document against document
# ---------------------------------------------------------------------------

SIMILAR_REPORT = REPOSITORY / "docs" / "measurements" / "2026-10-aehnlich-distanzen" / "README.md"


def axis(index: int, sign: float = 1.0) -> bytes:
    """A stored unit vector along one axis of the real width."""
    return to_int8(tuple(sign if position == index else 0.0 for position in range(DIMENSIONS)))


def between(first: int, second: int) -> bytes:
    """A stored unit vector halfway between two axes."""
    share = 1.0 / math.sqrt(2.0)
    return to_int8(tuple(share if position in (first, second) else 0.0 for position in range(DIMENSIONS)))


def test_the_similar_mode_and_the_derivation_can_be_named_together(tool: Any) -> None:
    args = tool.parse_args(["--similar", "--derive", "--groups", "gruppen.tsv"])

    assert args.similar is True
    assert args.derive is True
    assert args.groups == Path("gruppen.tsv")


def test_the_german_cases_are_the_first_42_lines_however_long_the_file_is(tool: Any) -> None:
    # 35-03 grows de.jsonl to about 120 cases and keeps the first 42 byte for
    # byte; this run measures exactly those, whatever the stand of 35-03 is.
    records = [{"id": f"de-{number:03d}", "query": "q", "passage": "p"} for number in range(120)]

    german = tool.similar_cases(records, "de")
    english = tool.similar_cases(records, "en")

    assert [record["id"] for record in german] == [f"de-{number:03d}" for number in range(42)]
    assert len(english) == 120


def test_the_related_pair_is_query_and_passage_of_one_case_and_the_unrelated_are_passage_pairs(
    tool: Any,
) -> None:
    queries = [axis(0), axis(1), axis(2)]
    passages = [axis(0), between(1, 3), axis(2, sign=-1.0)]

    population = tool.similar_pairs("en", queries, passages)

    assert population.related.tolist() == pytest.approx([0.0, tool.l2_distance(axis(1), between(1, 3)), 254.0])
    # Every unordered pair of passages of different cases, once.
    assert population.unrelated.size == 3
    assert sorted(population.unrelated.tolist()) == pytest.approx(
        sorted(
            [
                tool.l2_distance(passages[0], passages[1]),
                tool.l2_distance(passages[0], passages[2]),
                tool.l2_distance(passages[1], passages[2]),
            ]
        )
    )


def _population(tool: Any, language: str, related: list[float], unrelated: list[float]) -> Any:
    import numpy as np

    return tool.SimilarPopulation(
        language=language,
        related=np.array(related, dtype=np.float64),
        unrelated=np.array(unrelated, dtype=np.float64),
    )


def test_the_ceiling_is_the_smallest_grid_value_under_which_95_percent_of_related_pairs_lie(tool: Any) -> None:
    # Nineteen of twenty related pairs at 10.2 make 95 percent, so the grid
    # answers 10.5 and not the outlier at 80; every unrelated pair lies beyond.
    populations = [_population(tool, language, [10.2] * 19 + [80.0], [100.0] * 10) for language in ("de", "en", "fr")]

    verdict = tool.derive_similar(populations)

    assert verdict.satisfied is True
    assert verdict.ceiling == pytest.approx(10.5)
    assert verdict.cut == {"de": pytest.approx(1.0), "en": pytest.approx(1.0), "fr": pytest.approx(1.0)}


def test_the_ceiling_is_refused_when_one_language_cuts_less_than_90_percent(tool: Any) -> None:
    # French lets two of ten unrelated pairs through at the 95 percent value,
    # which is 80 percent cut: the rule is not met, and no value is chosen.
    populations = [
        _population(tool, "de", [10.2] * 20, [100.0] * 10),
        _population(tool, "en", [10.2] * 20, [100.0] * 10),
        _population(tool, "fr", [30.0] * 20, [20.0, 25.0] + [100.0] * 8),
    ]

    verdict = tool.derive_similar(populations)

    assert verdict.satisfied is False
    assert verdict.ceiling is None
    assert verdict.candidate == pytest.approx(30.0)
    assert verdict.cut["fr"] == pytest.approx(0.8)
    # The owner question carries both numbers: the largest grid value that cuts
    # 90 percent everywhere, and what it costs in related pairs.
    assert verdict.fallback == pytest.approx(24.5)
    assert verdict.fallback_lost == {"de": 0, "en": 0, "fr": 20}


def test_the_group_probe_counts_group_pairs_and_foreign_pairs_under_a_ceiling(tool: Any) -> None:
    groups = {
        "a1": "a",
        "a2": "a",
        "b1": "b",
        "b2": "b",
        "c1": "c",
        "c2": "c",
        "lose": tool.NO_GROUP,
        "ohne-text": "c",
    }
    centroids = {
        "a1": axis(0),
        "a2": axis(0),
        "b1": axis(1),
        "b2": axis(1),
        "c1": axis(2),
        "c2": axis(2),
        "lose": axis(3),
    }

    probe = tool.group_probe(groups, centroids, ceiling=50.0)

    assert probe is not None
    assert probe.group_pairs == 3
    # Seven files with a vector make 21 pairs; the three group pairs leave 18,
    # and every pair with the file without a group is one of them.
    assert probe.foreign_pairs == 18
    assert probe.group_share == pytest.approx(1.0)
    assert probe.foreign_share == pytest.approx(0.0)


def test_the_group_probe_is_not_checkable_with_fewer_than_three_groups_of_two(tool: Any) -> None:
    groups = {"a1": "a", "a2": "a", "b1": "b", "b2": "b", "c1": "c"}
    centroids = {name: axis(index) for index, name in enumerate(groups)}

    assert tool.group_probe(groups, centroids, ceiling=50.0) is None


def test_the_overlap_of_mean_and_minimum_is_a_number_between_0_and_1_per_multi_chunk_document(
    tool: Any,
) -> None:
    # The document of two chunks lies between axis 0 and axis 1. Its mean finds
    # the halfway document first, the minimum over its chunks finds the one on
    # axis 0 first: one neighbour apart, everything when ten are compared.
    documents = {
        "mehr": [axis(0), axis(1)],
        "achse": [axis(0)],
        "halb": [between(0, 1)],
        "fern": [axis(5)],
    }

    first = tool.neighbour_overlap(documents, neighbours=1)
    ten = tool.neighbour_overlap(documents, neighbours=10)

    assert set(first) == {"mehr"}
    assert first["mehr"] == pytest.approx(0.0)
    assert ten["mehr"] == pytest.approx(1.0)


def test_the_similar_mode_measures_with_the_product_centroid(tool: Any) -> None:
    from findling.index import fusion

    assert tool.centroid is fusion.centroid


def test_the_similar_report_carries_neither_kind_of_dash() -> None:
    text = SIMILAR_REPORT.read_text(encoding="utf-8")
    for dash in DASHES:
        assert dash not in text


def test_the_similar_report_carries_no_case_of_the_test_set() -> None:
    import json

    text = SIMILAR_REPORT.read_text(encoding="utf-8")
    for language in ("de", "en", "fr"):
        dataset = REPOSITORY / "testdata" / "semantik" / f"{language}.jsonl"
        for line in dataset.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            assert record[QUERY_FIELD] not in text, record["id"]
            assert record[PASSAGE_FIELD] not in text, record["id"]
