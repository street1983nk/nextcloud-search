"""The two mimetype allowlists, held together by a comparison in both directions.

The list of document types this project touches is kept twice on purpose:
``StorageService::ALLOWED_MIMETYPES`` decides what the PHP crawl ever queues, and
``dispatch.ALLOWED_MIMETYPES`` decides what the container ever opens. The
duplication is the point, and ``dispatch`` says so itself: it is the line that
still holds on the day somebody raises the cap on one side only. What was missing
until plan 03-10 is the thing that keeps a deliberate duplication from becoming an
accidental divergence.

Both directions cost something different, and both are asserted below.

A type only Python knows is a file that never arrives. The extractor is there,
the route is there, and the crawl hands the container nothing, so gate B of the
integration run turns green without having touched the new files at all
(pitfall 13). That is the worst kind of green: a proof about an empty set.

A type only PHP knows is worse in the other direction. The crawl queues the file,
the container answers skipped(mime_not_allowed), and the nightly reconcile finds a
file in the mount that carries no usable verdict, queues it again, and does the
same thing tomorrow.

The gate is built in the shape of ``test_extract_errors.test_php_reason_list_matches_python``,
which compares the third list of the taxonomy the same way and for the same
reason, so both can be maintained together. The PHP constant is read as text
because a PHP constant cannot be imported, and writing the values into this file
a second time would be the very duplication the gate exists to catch.
"""

from __future__ import annotations

import re
from pathlib import Path

from findling.extract.dispatch import ALLOWED_MIMETYPES, IMAGE_MIMETYPES, Route

PHP_STORAGE_SERVICE = Path(__file__).resolve().parents[2] / "php" / "lib" / "Service" / "StorageService.php"
PYTHON_DISPATCH = Path(__file__).resolve().parents[1] / "src" / "findling" / "extract" / "dispatch.py"

# The two picture formats that are deliberately absent from both lists. Every
# further decoder is attack surface inside the sandbox child, and these two buy
# nothing a scan of a document needs: BMP and GIF carry documents essentially
# never. HEIC and HEIF left this set with plan 31-10 (FMT-05), by decision and
# not by drift: pillow-heif decodes them in the sandbox child since plan 31-07.
REFUSED_MIMETYPES = frozenset({"image/bmp", "image/gif"})

# What 1.5 leaves out on purpose beyond the pictures, named in the shared
# paragraph: the PowerPoint format before 2007, the archive formats other than
# ZIP, and Outlook .msg files.
LEFT_OUT_IN_1_5 = frozenset(
    {
        "application/vnd.ms-powerpoint",
        "application/x-7z-compressed",
        "application/x-rar-compressed",
        "application/x-tar",
        "application/gzip",
        "application/vnd.ms-outlook",
    }
)

# The five kinds of file of 1.5 (FMT-01 to FMT-05) and the route each one takes.
FORMATS_OF_1_5 = {
    "message/rfc822": Route.MAIL,
    "application/zip": Route.ZIP,
    "application/msword": Route.DOC,
    "application/vnd.ms-excel": Route.XLS,
    "image/heic": Route.OCR,
    "image/heif": Route.OCR,
}

# The first words of the paragraph that stands identically next to both lists.
SHARED_PARAGRAPH_START = "Since 1.5 (plan 31-10) the allowlist reads"


def _php_mimetypes() -> set[str]:
    """The ALLOWED_MIMETYPES constant of the PHP companion, read out of its source."""
    source = PHP_STORAGE_SERVICE.read_text(encoding="utf-8")
    block = re.search(r"const ALLOWED_MIMETYPES = \[(.*?)\];", source, re.DOTALL)
    assert block is not None, "the ALLOWED_MIMETYPES constant is no longer where this gate looks for it"
    return set(re.findall(r"'([a-z0-9.+/-]+)'", block.group(1)))


def _drift(python_types: set[str], php_types: set[str]) -> list[str]:
    """What is missing where, one line per type, empty when the two lists agree.

    A bare set comparison would say "these differ" and leave the reader with two
    lists of a dozen long OOXML names to diff by eye. The failure of this gate
    happens on the day somebody added one type to one file, so the message names
    that type and the side it is missing from.
    """
    return [f"{name} is missing from the PHP crawl" for name in sorted(python_types - php_types)] + [
        f"{name} is missing from the Python extractor" for name in sorted(php_types - python_types)
    ]


def test_every_type_the_extractor_knows_is_delivered_by_the_crawl() -> None:
    ours = set(ALLOWED_MIMETYPES)

    missing = sorted(ours - _php_mimetypes())

    assert missing == [], f"the container would extract these and never receive one: {missing}"


def test_every_type_the_crawl_delivers_is_known_to_the_extractor() -> None:
    theirs = _php_mimetypes()

    surplus = sorted(theirs - set(ALLOWED_MIMETYPES))

    assert surplus == [], f"the crawl queues these and the container refuses them: {surplus}"


def test_the_message_names_the_type_and_the_side_it_is_missing_from() -> None:
    # The self test of the gate, and the answer to "would this actually go red".
    # A drift in either direction produces a line, and the line carries the type
    # and the side, because that is the whole difference between a gate somebody
    # can fix in a minute and one that sends them diffing two files by hand.
    assert _drift({"image/webp"}, set()) == ["image/webp is missing from the PHP crawl"]
    assert _drift(set(), {"image/webp"}) == ["image/webp is missing from the Python extractor"]
    assert _drift({"text/plain"}, {"text/plain"}) == []


def test_the_six_picture_formats_stand_in_both_lists() -> None:
    # D-05 spelled out, and FMT-05 since plan 31-10: a scanned or photographed
    # document in any of the six formats reaches the container, and it reaches
    # it on the OCR route. Without the first half no picture is ever queued;
    # without the second half a picture is queued and then refused by the
    # dispatcher.
    assert (
        frozenset({"image/jpeg", "image/png", "image/tiff", "image/webp", "image/heic", "image/heif"})
        == IMAGE_MIMETYPES
    )

    for mime in IMAGE_MIMETYPES:
        assert ALLOWED_MIMETYPES[mime] is Route.OCR
        assert mime in _php_mimetypes()


def test_the_refused_picture_formats_stand_in_neither_list() -> None:
    # Written as a gate rather than as a comment, because the parity gate above
    # cannot see this one: adding HEIC to both lists at once would keep the two
    # sides in agreement and would still open a decoder nobody decided to open
    # (T-03-1003).
    php_types = _php_mimetypes()

    for mime in REFUSED_MIMETYPES:
        assert mime not in ALLOWED_MIMETYPES
        assert mime not in php_types


def test_the_formats_of_1_5_stand_in_both_lists_on_their_routes() -> None:
    # Plan 31-10 opens both sides in one commit (pitfall 3 of 31-RESEARCH): a
    # type the crawl queues before the container takes it would be stored as
    # mime_not_allowed against its ETag.
    php_types = _php_mimetypes()

    for mime, route in FORMATS_OF_1_5.items():
        assert ALLOWED_MIMETYPES[mime] is route
        assert mime in php_types


def test_what_1_5_leaves_out_stands_in_neither_list() -> None:
    php_types = _php_mimetypes()

    for mime in LEFT_OUT_IN_1_5:
        assert mime not in ALLOWED_MIMETYPES
        assert mime not in php_types


def _shared_paragraph(source: str, comment: str) -> str:
    """The shared paragraph of one file, comment markers removed, whitespace folded.

    It runs from SHARED_PARAGRAPH_START to the first line that is no comment or
    a comment without words.
    """
    lines = source.splitlines()
    starts = [number for number, line in enumerate(lines) if SHARED_PARAGRAPH_START in line]
    assert len(starts) == 1, f"the shared paragraph starts {len(starts)} times instead of once"
    words: list[str] = []
    for line in lines[starts[0] :]:
        stripped = line.strip()
        text = stripped.removeprefix(comment).strip()
        if not stripped.startswith(comment) or not text:
            break
        words.append(text)
    return " ".join(" ".join(words).split())


def test_the_paragraph_next_to_both_lists_is_the_same() -> None:
    # A decision readable in one place only is a decision the other place will
    # undo; this is what keeps the two paragraphs from drifting like the lists.
    python = _shared_paragraph(PYTHON_DISPATCH.read_text(encoding="utf-8"), "#")
    php = _shared_paragraph(PHP_STORAGE_SERVICE.read_text(encoding="utf-8"), "*")

    assert python == php
    for mime in FORMATS_OF_1_5:
        assert mime in python


def test_the_old_reason_for_keeping_heic_out_is_gone_from_both_files() -> None:
    for path in (PYTHON_DISPATCH, PHP_STORAGE_SERVICE):
        source = " ".join(path.read_text(encoding="utf-8").split())
        assert "HEIC, BMP and GIF stay out" not in source
        assert "Out, and why: HEIC" not in source
