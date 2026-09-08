"""The gate over the OCR quality measurement of the launch hardening.

It checks the ruler, not what was measured with it. Every number this file
asserts on comes out of strings written three lines above the assertion, and not
one test in here starts tesseract. That is deliberate and it is the same split
``test_embed_bench.py`` makes: what a measuring tool has to get right is the
arithmetic, the breakdown and the discipline of its output, and all three can be
proved against known answers. What the engine reads off a page cannot be proved
here at all, it can only be measured, and the measurement lands in
``docs/measurements/2026-09-06-ocr-dach/README.md``.

The one test that touches the corpus generator is the determinism of the ground
truth file. It has to live here rather than in a script test, because the file is
this tool's input and a tool whose input drifts measures a different thing every
run without saying so.
"""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType

import pytest

from findling.extract import ocr_quality

# The corpus generator arrives through the session fixture ``corpus_generator``
# of conftest.py. It used to be loaded by a private helper in this module and in
# test_corpus_terms.py, once per test that asked for it; loading it builds all
# thirty nine corpus files and cost about 5.9 s each time.


# --------------------------------------------------------------------------
# Behaviour 1 to 3: the arithmetic of the character error rate.
# --------------------------------------------------------------------------


def test_two_identical_strings_have_no_error() -> None:
    assert ocr_quality.character_error_rate("Baubewilligung", "Baubewilligung") == 0.0


def test_a_string_against_the_empty_one_is_a_full_error() -> None:
    # Nothing was read at all, so every character of the truth is a deletion.
    assert ocr_quality.character_error_rate("Baubewilligung", "") == 1.0


def test_two_empty_strings_are_not_an_error_and_do_not_divide_by_zero() -> None:
    assert ocr_quality.character_error_rate("", "") == 0.0


def test_the_empty_truth_against_a_read_string_is_a_full_error() -> None:
    # The other direction of the same degenerate case: there was nothing to read
    # and the engine produced something. Counting that as zero would hide it.
    assert ocr_quality.character_error_rate("", "Baubewilligung") == 1.0


@pytest.mark.parametrize(
    ("truth", "recognised", "expected_errors"),
    [
        ("Jaenner", "Jaenneer", 1),  # one insertion
        ("Jaenner", "Jaener", 1),  # one deletion
        ("Jaenner", "Jaenne1", 1),  # one substitution
        ("Jaenner", "Jaenne", 1),  # one deletion at the end
        ("Jaenner", "1aenner", 1),  # one substitution at the front
    ],
)
def test_one_edit_of_any_kind_counts_as_exactly_one_error(truth: str, recognised: str, expected_errors: int) -> None:
    # The load bearing assertion of the whole file. A substitution counted as a
    # deletion plus an insertion would make this two, every rate in every report
    # would be too high, and the coarse bar of the tool would start to bite for
    # a reason that has nothing to do with the engine.
    assert ocr_quality.edit_distance(truth, recognised) == expected_errors


def test_the_rate_is_errors_divided_by_the_characters_of_the_truth() -> None:
    # Seven characters of truth, one substitution, so one seventh and not one
    # eighth: the denominator is the truth and never what was read.
    assert ocr_quality.character_error_rate("Jaenner", "Jaenne1") == pytest.approx(1 / 7)


def test_the_denominator_stays_the_truth_when_the_engine_invents_characters() -> None:
    assert ocr_quality.character_error_rate("Jaenner", "Jaennerrrr") == pytest.approx(3 / 7)


# --------------------------------------------------------------------------
# Behaviour 4: the rate per page, the rate over all pages, and the character
# counts the rates were computed against.
# --------------------------------------------------------------------------


def _pages() -> list[ocr_quality.RenderedPage]:
    """Three pages with known truths, and no PDF and no engine anywhere near them."""
    return [
        ocr_quality.RenderedPage(variant="ch", truth="Strasse", image=b""),
        ocr_quality.RenderedPage(variant="at", truth="Jaenner", image=b""),
        ocr_quality.RenderedPage(variant="de", truth="Bescheid", image=b""),
    ]


def _engine_that_makes(mistakes: dict[str, str]) -> ocr_quality.Engine:
    """Stand in for the shipped engine call: it answers from a table, page by page."""
    answers = iter(mistakes.values())

    def engine(image: bytes, languages: str, seconds: int) -> str:
        assert image == b""
        assert languages
        assert seconds > 0
        return next(answers)

    return engine


def test_the_report_carries_a_rate_and_a_character_count_for_every_page() -> None:
    results = ocr_quality.measure_pages(
        _pages(),
        engine=_engine_that_makes({"ch": "Strasse", "at": "Jaenne1", "de": "Bescheid"}),
        languages="deu",
        seconds=30,
    )

    assert [page.truth_characters for page in results] == [7, 7, 8]
    assert [page.errors for page in results] == [0, 1, 0]
    assert results[1].rate == pytest.approx(1 / 7)


def test_the_overall_rate_is_the_errors_of_all_pages_over_their_characters() -> None:
    # Not the mean of the page rates. A short page with one error would otherwise
    # weigh as much as a full page with one error, and the number would say
    # something about the page lengths of this corpus rather than about the
    # engine.
    results = ocr_quality.measure_pages(
        _pages(),
        engine=_engine_that_makes({"ch": "Strass", "at": "Jaenne1", "de": "Bescheid"}),
        languages="deu",
        seconds=30,
    )

    assert ocr_quality.overall_rate(results) == pytest.approx(2 / 22)


def test_the_report_breaks_the_rate_down_by_language_variant_and_over_everything() -> None:
    results = ocr_quality.measure_pages(
        _pages(),
        engine=_engine_that_makes({"ch": "Strasse", "at": "Jaenne1", "de": "Bescheid"}),
        languages="deu",
        seconds=30,
    )

    printed = ocr_quality.report(results)

    assert "variant=at" in printed
    assert "variant=ch" in printed
    assert "variant=de" in printed
    assert "overall" in printed
    assert "chars=22" in printed
    assert "pages=3" in printed


# --------------------------------------------------------------------------
# Behaviour 5: numbers only. Never the text that was read, never the text that
# was expected, and never the directory the pages came out of.
# --------------------------------------------------------------------------


def test_the_tool_prints_neither_the_recognised_nor_the_expected_text() -> None:
    # T-06.1-58. A quality tool that prints what it read prints user content the
    # moment somebody points it at a real directory, and the report of this
    # project is counters and reason codes, nothing else.
    results = ocr_quality.measure_pages(
        _pages(),
        engine=_engine_that_makes({"ch": "Strasse", "at": "Jaenne1", "de": "Bescheid"}),
        languages="deu",
        seconds=30,
    )

    printed = ocr_quality.report(results)

    for secret in ("Strasse", "Jaenner", "Jaenne1", "Bescheid"):
        assert secret not in printed


def test_a_missing_input_is_refused_without_printing_a_path(tmp_path: Path) -> None:
    absent = tmp_path / "there-is-no-such-directory"

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = ocr_quality.main(["--corpus", str(absent), "--truth", str(absent / "truth.json")])

    assert code == 2
    assert str(absent) not in buffer.getvalue()
    assert "there-is-no-such-directory" not in buffer.getvalue()


# --------------------------------------------------------------------------
# Behaviour 6: the generator writes the truth, and it writes the same bytes twice.
# --------------------------------------------------------------------------


def test_the_generator_writes_the_same_ground_truth_twice(corpus_generator: ModuleType) -> None:
    first = corpus_generator.build_ground_truth()
    second = corpus_generator.build_ground_truth()

    assert first == second
    assert first.endswith(b"\n")
    assert b"\r\n" not in first


def test_the_committed_ground_truth_is_the_one_the_generator_builds(corpus_generator: ModuleType) -> None:
    assert corpus_generator.GROUND_TRUTH_PATH.read_bytes() == corpus_generator.build_ground_truth()


def test_the_ground_truth_names_a_variant_and_pages_for_every_document(corpus_generator: ModuleType) -> None:
    payload = json.loads(corpus_generator.build_ground_truth().decode("utf-8"))

    assert payload["documents"]
    for document in payload["documents"]:
        assert document["variant"] in {"de", "ch", "at"}
        assert document["pages"]
        assert all(page.strip() for page in document["pages"])
    names = [document["name"] for document in payload["documents"]]
    assert names == sorted(names)


# --------------------------------------------------------------------------
# The coarse bar, and the reason it is coarse.
# --------------------------------------------------------------------------


def test_the_bar_is_coarse_enough_to_survive_a_point_release() -> None:
    # Not a taste test. A bar tight enough to catch a single shifted character
    # would be the statement about the engine version that docs/testing.md
    # deliberately refuses to make, and it would go red on the next Debian point
    # release with nothing in any diff. The floor keeps it from being decorative.
    assert 0.01 <= ocr_quality.MAX_CHARACTER_ERROR_RATE <= 0.2


def test_a_total_failure_of_the_engine_trips_the_bar() -> None:
    # The one thing the bar has to catch: a wrong language, a missing language
    # file, a page that came back empty. Every character of the truth is then an
    # error and the rate is one.
    results = ocr_quality.measure_pages(
        _pages(),
        engine=_engine_that_makes({"ch": "", "at": "", "de": ""}),
        languages="deu",
        seconds=30,
    )

    assert ocr_quality.overall_rate(results) == pytest.approx(1.0)
    assert ocr_quality.overall_rate(results) > ocr_quality.MAX_CHARACTER_ERROR_RATE
