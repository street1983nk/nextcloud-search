"""How well the OCR chain reads a DACH page, in numbers instead of in a claim.

The acceptance test for D-09 asks whether a scanned Swiss or Austrian document is
findable through the ordinary search route, and it answers that with three search
hits. ``docs/testing.md`` says in as many words what that proves and what it does
not: it does not prove that tesseract read the page correctly, and the refusal is
well founded, because a raw text comparison would be a test against the version
of the engine and would go red on the next Debian point release.

The owner asked the other question. Does the chain read the umlauts, the dates
and the amounts of this region. A search hit cannot answer it: a character the
engine got wrong inside a word that still stems onto the same token is invisible
to a search, and a word it missed entirely just fails without saying why. So the
gate stays what it is, and this module steps next to it and measures.

The truth is not borrowed from anywhere. ``scripts/dev/build_corpus.py`` renders
the scanned pages of the corpus out of its own prose, so the source text is the
ground truth, byte for byte, and the generator refuses to render at all if a
character would come out as a replacement box. The generator writes that prose
into ``testdata/corpus-truth.json``, page by page, and this module reads it. No
foreign scan corpus with an unclear licence has to exist for the question to have
an answer.

**The output is numbers.** Never the text that was read, never the text that was
expected, never a path. A quality tool that prints what it recognised prints user
content the moment somebody points it at a real directory (T-06.1-58), and the
log of this project carries counters and reason codes and nothing else. The one
label besides numbers is the language variant, ``de``, ``ch`` or ``at``, which
the generator puts into the truth file so that the breakdown is readable without
a file name leaving this module.

**The bar is coarse and says so.** It exists to catch a total failure, a page
that comes back empty or as noise, not to hold a decimal place steady. What it
does not catch is measured rather than assumed and written down in the comment on
``MAX_CHARACTER_ERROR_RATE``.

Run it against the corpus of this repository:

    python -m findling.extract.ocr_quality --corpus testdata/corpus \\
        --truth testdata/corpus-truth.json

Like every module of this package it never writes: the pages are rendered into
memory, the engine answers on a pipe, and nothing is put on disk.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pypdfium2

from findling import config
from findling.extract import raster
from findling.extract.ocr import read_page

# The coarse bar. Measured value, margin, and the reason for the coarseness, in
# that order, because a threshold without all three is a number somebody picked.
#
# **Measured** on 2026-09-06 with the runtime image of this repository, six
# rendered pages, 3148 characters of truth, deu+eng+fra at 300 dpi: 0.000000
# overall and on every one of the three variants. Not a single character wrong.
# The full run and its command line are in
# docs/measurements/2026-09-06-ocr-dach/README.md.
#
# **The margin** is the whole of the bar, since the measured value is zero. At
# 0.05 this corpus may lose 157 characters before the bar bites.
#
# **Why so coarse, and what that costs.** A tighter bar would be the statement
# about the version of the engine that docs/testing.md deliberately refuses to
# make: the engine is pinned to the digest of the base image and not to a
# version, a Debian point release moves single characters, and docs/ocr.md has
# one such shift written down already, a capital U that came back without its two
# dots. A build that goes red for that costs a debugging session and proves
# nothing.
#
# The cost is measured and not guessed, and it is larger than the plan for this
# module assumed. Swapping the language list for the wrong one does **not** trip
# this bar: eng alone reads the same six pages at 0.0203 and fra alone at 0.0073,
# both far under 0.05. On clean rendered Latin script the LSTM recogniser barely
# leans on its language model, so a bar that caught a wrong language would have
# to sit near 0.005, which over 3148 characters is fifteen characters of slack,
# which is the sharp bar again under another name. A wrong language is therefore
# caught where it belongs: the allowlist in findling.config refuses a language
# the image does not carry, and the image build itself fails without deu, eng and
# fra in --list-langs.
#
# What this bar does catch is the failure it is named for. A page that comes back
# empty or as noise scores at or near 1.0 and trips it by a factor of twenty, and
# that is what a dead engine, an unreadable rendering or a page of the wrong size
# produces. There is a test for exactly that case.
MAX_CHARACTER_ERROR_RATE: Final = 0.05

# The engine call, as a parameter rather than as an import at the call site. The
# default is the shipped call form of findling.extract.ocr, so the measurement
# measures what is delivered; the seam exists so the arithmetic and the breakdown
# can be tested against known answers without starting tesseract, which is the
# same split test_embed_bench.py makes for the wave 0 tools.
Engine = Callable[[bytes, str, int], str]


@dataclass(frozen=True, slots=True)
class RenderedPage:
    """One page of the corpus: the prose it was drawn from, and its pixels."""

    variant: str
    truth: str
    image: bytes


@dataclass(frozen=True, slots=True)
class PageResult:
    """What one page cost, in characters of truth and in edits to get there."""

    variant: str
    truth_characters: int
    errors: int

    @property
    def rate(self) -> float:
        """Errors over the characters of the truth, never over what was read."""
        if self.truth_characters == 0:
            return 0.0 if self.errors == 0 else 1.0
        return self.errors / self.truth_characters


def edit_distance(truth: str, recognised: str) -> int:
    """The Levenshtein distance: one insertion, one deletion, one substitution, one error.

    Written out rather than pulled in, and that is not a hand rolled algorithm in
    the sense the project rules warn about: it is thirteen lines of textbook
    dynamic programming with a test per edit kind, against a dependency that
    would have to be pinned, licence checked, wheel checked on arm64 and carried
    into an image whose size is a product property. The rule this repository
    keeps is not to reimplement a *system*, and a distance function is not one.

    The substitution is the case that decides the whole measurement. Counted as a
    deletion plus an insertion it would be two errors, every rate in every report
    would be too high, and the coarse bar would start to bite for a reason that
    has nothing to do with the engine. There is a test for exactly that.
    """
    if truth == recognised:
        return 0
    if not truth:
        return len(recognised)
    if not recognised:
        return len(truth)

    previous = list(range(len(recognised) + 1))
    for row, expected in enumerate(truth, start=1):
        current = [row]
        for column, actual in enumerate(recognised, start=1):
            substitution = previous[column - 1] + (expected != actual)
            deletion = previous[column] + 1
            insertion = current[column - 1] + 1
            current.append(min(substitution, deletion, insertion))
        previous = current
    return previous[-1]


def character_error_rate(truth: str, recognised: str) -> float:
    """Edits per character of the truth, with the two degenerate cases spelled out.

    An empty truth against an empty reading is not an error: there was nothing to
    read and nothing was read. An empty truth against a reading is a full error,
    because the alternative is a division by zero or a silent zero, and a silent
    zero would hide the case where the engine invents a page out of noise.
    """
    if not truth:
        return 0.0 if not recognised else 1.0
    return edit_distance(truth, recognised) / len(truth)


def normalise(text: str) -> str:
    """Collapse every run of whitespace into one space, and strip the ends.

    A measurement decision, so it is written down rather than hidden in a call.
    The line breaks of a rendered page and the line breaks tesseract puts between
    the lines it found are two different things, and comparing them would make
    the layout of the page the largest term in the rate. What is being measured
    here is which characters came back, not where the engine thought the line
    ended.
    """
    return " ".join(text.split())


def measure_pages(pages: Iterable[RenderedPage], *, engine: Engine, languages: str, seconds: int) -> list[PageResult]:
    """Run the engine over every page and count the edits, page by page."""
    results: list[PageResult] = []
    for page in pages:
        truth = normalise(page.truth)
        recognised = normalise(engine(page.image, languages, seconds))
        results.append(
            PageResult(
                variant=page.variant,
                truth_characters=len(truth),
                errors=edit_distance(truth, recognised),
            )
        )
    return results


def overall_rate(results: Sequence[PageResult]) -> float:
    """All errors over all characters of truth, weighted by characters and not by page.

    The mean of the page rates would be the other candidate and it would be the
    wrong one: a three line page with one error would then weigh as much as a
    full page with one error, and the number would say something about the page
    lengths of this corpus rather than about the engine.
    """
    characters = sum(result.truth_characters for result in results)
    errors = sum(result.errors for result in results)
    if characters == 0:
        return 0.0 if errors == 0 else 1.0
    return errors / characters


def _line(label: str, results: Sequence[PageResult]) -> str:
    characters = sum(result.truth_characters for result in results)
    errors = sum(result.errors for result in results)
    counted = f"pages={len(results):<3} chars={characters:<6} errors={errors:<5}"
    return f"{label:<14} {counted} cer={overall_rate(results):.6f}"


def report(results: Sequence[PageResult]) -> str:
    """The pages, the language variants, the total, and the verdict against the bar.

    Numbers and variant labels only. Pages are named by their ordinal in the run,
    which is stable because the ground truth file is sorted by document name.
    """
    lines = [
        f"page {number:<9} variant={result.variant} chars={result.truth_characters:<6}"
        f" errors={result.errors:<5} cer={result.rate:.6f}"
        for number, result in enumerate(results, start=1)
    ]
    lines.append("")
    for variant in sorted({result.variant for result in results}):
        lines.append(_line(f"variant={variant}", [result for result in results if result.variant == variant]))
    lines.append(_line("overall", results))

    rate = overall_rate(results)
    verdict = "ok" if rate <= MAX_CHARACTER_ERROR_RATE else "over"
    lines.append(f"bar={MAX_CHARACTER_ERROR_RATE:.6f} verdict={verdict}")
    return "\n".join(lines)


def rendered_pages(corpus: Path, truth: object, dpi: int) -> list[RenderedPage]:
    """Render every page the ground truth knows about, in the order it lists them.

    The renderer is the one the OCR pass uses, at the DPI the settings carry, so
    the pixels the measurement judges are the pixels the index is built from.
    """
    if not isinstance(truth, dict):
        message = "the ground truth is not an object"
        raise ValueError(message)
    documents = truth.get("documents")
    if not isinstance(documents, list):
        message = "the ground truth carries no documents"
        raise ValueError(message)

    pages: list[RenderedPage] = []
    for entry in documents:
        document = pypdfium2.PdfDocument(str(corpus / str(entry["name"])))
        try:
            for number, text in enumerate(entry["pages"]):
                pages.append(
                    RenderedPage(
                        variant=str(entry["variant"]),
                        truth=str(text),
                        image=raster.render_page_png(document, number, dpi=dpi),
                    )
                )
        finally:
            document.close()
    return pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure the character error rate of the OCR chain against rendered pages."
    )
    parser.add_argument("--corpus", type=Path, required=True, help="directory holding the rendered pages")
    parser.add_argument("--truth", type=Path, required=True, help="the ground truth file the corpus generator writes")
    arguments = parser.parse_args(argv)

    # No path in the message, deliberately, and none in a traceback either: the
    # rule of this module is that its output is numbers, and it holds on the
    # error path as well, which is where it is easiest to forget.
    if not arguments.corpus.is_dir() or not arguments.truth.is_file():
        print("input missing: point --corpus at a directory of rendered pages and --truth at the generated file")
        return 2

    resolved = config.settings()
    truth = json.loads(arguments.truth.read_text(encoding="utf-8"))
    pages = rendered_pages(arguments.corpus, truth, resolved.ocr_dpi)
    results = measure_pages(
        pages,
        engine=read_page,
        languages="+".join(resolved.ocr_languages),
        seconds=resolved.ocr_page_seconds,
    )

    print(f"ocr character error rate, dpi={resolved.ocr_dpi} languages={len(resolved.ocr_languages)}")
    print(report(results))
    return 0 if overall_rate(results) <= MAX_CHARACTER_ERROR_RATE else 1


if __name__ == "__main__":
    raise SystemExit(main())
