"""The closed taxonomy and the allowlist that judges a file before its first byte.

Two properties carry this file. The first is that a verdict is a pair, and that a
reason which does not belong to its state cannot be built at all: a wrong pair
does not fail loudly at the database, it quietly makes the status page lie.

The second is that the allowlist decides before an extractor exists. In this plan
every format route still raises NotImplementedError, which turns that claim into
something a test can observe: a mimetype outside the allowlist has to come back
as a verdict, and a call that reached a library would raise instead.
"""

from __future__ import annotations

import zipfile

import pytest
from docx.opc.exceptions import PackageNotFoundError

# lxml ships no type information for its C extension, so pyright cannot see the
# submodule. Importing the real class is the point of this test file: the mapping
# in errors.py matches class names as strings, and only the genuine exception
# object proves that those strings still describe reality.
from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from findling import config
from findling.extract.dispatch import (
    ALLOWED_MIMETYPES,
    Route,
    cap_text,
    extension_of,
    extract,
    judge,
)
from findling.extract.errors import STATE_REASONS, ExtractionOutcome, Reason, State
from findling.store import repo

PLAIN = "text/plain"


def test_indexed_carries_no_reason_by_default() -> None:
    outcome = ExtractionOutcome.indexed("Aktenvermerk")

    assert outcome.state is State.INDEXED
    assert outcome.reason is None
    assert outcome.text_chars == len("Aktenvermerk")
    assert outcome.truncated is False


def test_truncated_is_the_one_reason_an_indexed_file_may_carry() -> None:
    outcome = ExtractionOutcome.indexed("Aktenvermerk", truncated=True)

    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert outcome.truncated is True


def test_a_reason_outside_its_state_is_refused() -> None:
    # skipped(timeout) reads plausibly and is wrong: timeout is a failure, and a
    # file in the wrong bucket makes both counters on the status page lie.
    with pytest.raises(ValueError, match="does not belong to state"):
        ExtractionOutcome.skipped(Reason.TIMEOUT)

    with pytest.raises(ValueError, match="does not belong to state"):
        ExtractionOutcome.failed(Reason.NO_TEXT_LAYER)


def test_a_verdict_other_than_indexed_carries_no_text() -> None:
    outcome = ExtractionOutcome.skipped(Reason.NO_TEXT_LAYER)

    assert outcome.text == ""
    assert outcome.text_chars == 0


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (zipfile.BadZipFile("File is not a zip file"), Reason.CORRUPT),
        (PackageNotFoundError("Package not found"), Reason.CORRUPT),
        (etree.XMLSyntaxError("mismatched tag", None, 1, 1), Reason.XML_INVALID),
        (MemoryError(), Reason.OUT_OF_MEMORY),
    ],
)
def test_from_exception_translates_the_measured_library_errors(error: Exception, expected: Reason) -> None:
    outcome = ExtractionOutcome.from_exception(error)

    assert outcome.state is State.FAILED
    assert outcome.reason is expected


def test_an_unknown_exception_becomes_failed_corrupt_instead_of_travelling_on() -> None:
    # Anything that escapes an extractor is a broken document until proven
    # otherwise. Re-raising here would take the container with it.
    outcome = ExtractionOutcome.from_exception(RuntimeError("something nobody predicted"))

    assert outcome.state is State.FAILED
    assert outcome.reason is Reason.CORRUPT


def test_a_subclass_of_a_known_error_translates_like_its_base() -> None:
    class OwnZipTrouble(zipfile.BadZipFile):
        pass

    assert ExtractionOutcome.from_exception(OwnZipTrouble()).reason is Reason.CORRUPT


def test_the_taxonomy_is_identical_to_the_one_the_state_store_enforces() -> None:
    # Two lists that drift apart break the return channel to Nextcloud silently:
    # the extractor produces a pair the store refuses to write, and the file ends
    # up with no verdict at all.
    ours = {
        state.value: {reason.value if reason is not None else None for reason in reasons}
        for state, reasons in STATE_REASONS.items()
    }
    theirs = {state: set(reasons) for state, reasons in repo.STATE_REASONS.items()}

    assert ours == theirs


def test_a_mimetype_outside_the_allowlist_is_judged_without_reaching_an_extractor() -> None:
    verdict = judge("application/x-shockwave-flash", 1024)

    assert isinstance(verdict, ExtractionOutcome)
    assert verdict.state is State.SKIPPED
    assert verdict.reason is Reason.MIME_NOT_ALLOWED

    # The proof that no library was involved: every route still raises
    # NotImplementedError in this plan, so a call that got that far would blow up.
    assert extract("/nowhere/clip.swf", "application/x-shockwave-flash", 1024).reason is Reason.MIME_NOT_ALLOWED


@pytest.mark.parametrize(
    "mime",
    [
        "video/mp4",
        "video/quicktime",
        "audio/mpeg",
        "application/zip",
        "application/x-tar",
        "application/msword",
        "application/vnd.ms-excel",
        "application/vnd.ms-powerpoint",
        "image/jpeg",
        "image/png",
    ],
)
def test_video_archive_image_and_legacy_office_are_deliberately_not_supported(mime: str) -> None:
    assert mime not in ALLOWED_MIMETYPES
    assert judge(mime, 1024) == ExtractionOutcome.skipped(Reason.MIME_NOT_ALLOWED)


@pytest.mark.parametrize(
    ("mime", "expected"),
    [
        ("application/pdf", Route.PDF),
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", Route.DOCX),
        ("application/vnd.openxmlformats-officedocument.presentationml.presentation", Route.PPTX),
        ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", Route.XLSX),
        ("application/vnd.oasis.opendocument.text", Route.ODF),
        ("text/html", Route.HTML),
        ("application/rtf", Route.RTF),
        (PLAIN, Route.PLAIN),
        ("text/markdown", Route.PLAIN),
    ],
)
def test_an_allowed_mimetype_yields_its_route(mime: str, expected: Route) -> None:
    assert judge(mime, 1024) is expected


def test_a_zero_byte_file_is_failed_not_skipped() -> None:
    # Nobody decided against this file, the file simply has nothing in it.
    assert judge(PLAIN, 0) == ExtractionOutcome.failed(Reason.EMPTY_FILE)


def test_a_file_over_the_size_cap_is_skipped_a_second_time() -> None:
    # The PHP crawl already refuses it when queueing. This is the second line, for
    # the day somebody raises the cap on one side only.
    oversized = config.settings().max_file_bytes + 1

    assert judge(PLAIN, oversized) == ExtractionOutcome.skipped(Reason.TOO_LARGE)


def test_text_over_the_character_cap_is_cut_and_says_so() -> None:
    cap = config.settings().max_text_chars
    outcome = cap_text("a" * (cap + 500))

    assert outcome.state is State.INDEXED
    assert outcome.reason is Reason.TRUNCATED
    assert outcome.text_chars == cap
    assert len(outcome.text) == cap


def test_text_below_the_cap_arrives_whole() -> None:
    outcome = cap_text("Grundstuecksverkehrsgenehmigung")

    assert outcome.text == "Grundstuecksverkehrsgenehmigung"
    assert outcome.truncated is False


@pytest.mark.parametrize("nothing", ["", "   ", "\n\t \r\n"])
def test_an_extraction_that_yields_nothing_is_skipped(nothing: str) -> None:
    assert cap_text(nothing) == ExtractionOutcome.skipped(Reason.EMPTY_TEXT)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Vertrag.PDF", "pdf"),
        ("notes.tar.gz", "gz"),
        ("Ordner/Akte 2026.docx", "docx"),
        ("README", ""),
        (".gitignore", ""),
    ],
)
def test_extension_of_reports_the_lowercase_suffix(name: str, expected: str) -> None:
    assert extension_of(name) == expected
