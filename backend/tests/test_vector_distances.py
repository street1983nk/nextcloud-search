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
    )
    for function in printing:
        source = inspect.getsource(function)
        assert f'record["{QUERY_FIELD}"]' not in source, function.__name__
        assert f'record["{PASSAGE_FIELD}"]' not in source, function.__name__
        assert ".probe_text" not in source, function.__name__


def test_the_measurement_classes_carry_identifiers_and_numbers_and_no_text(tool: Any) -> None:
    """A dataclass that holds a passage would leak it through any repr of it."""
    import dataclasses

    for name in ("LanguageMeasurement", "CorpusChunk", "ProbeMeasurement"):
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
