"""OpenDocument text, spreadsheets and presentations, from the archive directly.

An OpenDocument file is a documented ZIP with a part named content.xml inside,
and the text of the document is the content of its paragraph and heading
elements. That is the whole format for our purposes, which is why this module is
about thirty lines of zipfile and XPath instead of a dependency.

**Why odfpy is not used.** Its last release is from January 2020, it carries no
type annotations and no py.typed marker, so it falls through the pyright gate of
this project. Taking on an unmaintained dependency, and then weakening a quality
gate for it, to save thirty lines is a bad trade in both directions.

**Why the archive is never unpacked.** Only the one part that is needed is read
into memory. Unpacking would write names chosen by the document to the file
system, and a name of the shape ``../../etc/something`` is how zip slip works
(T-02-84). There is no unpacking call in this module, and a test replaces the
one in the standard library with a call that fails, so it cannot come back
unnoticed.

**Why the parser is built rather than taken as it comes.** The content part is
XML from a user's folder, which is untrusted input. The three switches below turn
off entity resolution, network access and DTD loading, and together they close
XXE and parser driven SSRF (T-02-83). A test measures this against a parser built
without them: the same document leaks a local file through that one and does not
through this one.
"""

from __future__ import annotations

from zipfile import BadZipFile, ZipFile

from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from findling.config import EXTRACT_ARCHIVE_MEMBER_MAX_BYTES
from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason

# The single part of the archive that is read. Its name is fixed by the
# OpenDocument specification, so this is a constant and not a search.
_CONTENT_PART = "content.xml"

# The text namespace of OpenDocument. Named rather than guessed: a plain search
# for the string "text:p" would match a prefix that a document is free to rename.
_TEXT_NAMESPACE = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"

# Paragraphs and headings. Everything a reader sees sits inside one of these two.
_TEXT_ELEMENTS = (f"{{{_TEXT_NAMESPACE}}}p", f"{{{_TEXT_NAMESPACE}}}h")

# The three switches, with the reasons in the module docstring above.
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)


def extract_odf(path: str) -> ExtractionOutcome:
    """The text of an ODT, ODS or ODP file.

    One function for all three, because the difference between them lives in the
    part of the format we do not read: a spreadsheet keeps its cells and a
    presentation its slides, but the words in both sit in the same elements.

    Defined at module level so it survives the process boundary of the extraction
    child.
    """
    try:
        with ZipFile(path) as archive:
            # The declared size is checked before a byte is decompressed: a
            # bomb names its real size in the archive directory, and reading
            # first would be the attack (security audit M4). zipfile enforces
            # the declared size on read, so the check cannot be lied past.
            if archive.getinfo(_CONTENT_PART).file_size > EXTRACT_ARCHIVE_MEMBER_MAX_BYTES:
                return ExtractionOutcome.skipped(Reason.TOO_LARGE)
            content = archive.read(_CONTENT_PART)
    except BadZipFile as error:
        return ExtractionOutcome.from_exception(error)
    except KeyError:
        # A ZIP without the content part is not an OpenDocument file. It stays
        # corrupt rather than becoming mime_not_allowed, because Nextcloud told us
        # what this file claims to be and the claim is what turned out to be wrong.
        return ExtractionOutcome.failed(Reason.CORRUPT)

    try:
        root = etree.fromstring(content, parser=_PARSER)
    except etree.XMLSyntaxError as error:
        # Its own reason on purpose: a package that will not open is a different
        # repair job from a package that opens and holds nonsense.
        return ExtractionOutcome.from_exception(error)

    # iter() walks in document order, so the text arrives in the order a reader
    # would meet it. The parts are joined with a space, never glued: two
    # paragraphs run together produce a word that exists in neither of them, and
    # that word is then the only thing the index knows about the boundary.
    parts = ["".join(element.itertext()).strip() for element in root.iter(*_TEXT_ELEMENTS)]
    return cap_text(" ".join(part for part in parts if part))
