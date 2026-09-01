"""The three text formats: plain text, HTML and RTF.

These three share one property that the document formats do not have: there is no
container to open, so the whole risk sits in two places, the encoding and the
parser.

**Encoding.** German legacy documents are the reason charset detection is not
optional here. A file written in cp1252 or latin-1 decodes as UTF-8 into
replacement characters, and a document whose every umlaut has turned into a
question mark is worse than no document: it is silently in the index, findable by
nothing. charset-normalizer decides, UTF-8 with replacement is the fallback, and a
fallback that is itself unreadable becomes failed(encoding_unknown) rather than
noise in the index.

**Parser.** An HTML file from a user's folder is untrusted input. The XML parser
is therefore built with entity resolution off, network access off and DTD loading
off, which is the defence against XXE and SSRF (T-02-54): without those three, a
crafted document can make this container read a local file or call an address of
the attacker's choosing, and both would then travel into the search index. The
HTML parser of libxml2 expands no external entities in the first place, and it
gets the network switch anyway, because relying on a default that is not written
down is how defaults get changed.

**RTF has no error path at all.** striprtf does not raise on a broken file, it
returns nonsense. A plausibility check on the share of unprintable characters is
the only available defence, and skipped(empty_text) is the honest verdict:
nonsense in the index costs a user's trust in every future result.

None of these functions log, none of them opens a file for writing, and none of
them imports the analysis half of the package.
"""

from __future__ import annotations

from pathlib import Path

from charset_normalizer import from_bytes
from lxml import etree, html  # pyright: ignore[reportAttributeAccessIssue]
from striprtf.striprtf import rtf_to_text

from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason

# The three switches that matter, with the reason they are set. resolve_entities
# stops an external entity from being expanded at all, no_network stops the parser
# from fetching anything, and load_dtd stops it from following a doctype to
# somewhere else. Together they close XXE and parser driven SSRF (T-02-54).
_XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)

# libxml2's HTML parser does not expand external entities and does not load a DTD,
# so the two arguments it does not accept describe behaviour it already has. The
# network switch it does accept is set explicitly.
_HTML_PARSER = html.HTMLParser(no_network=True)

# Elements whose content is code, not text. Indexing them means a search for a
# variable name finds every page that uses a library, and a search for a word
# finds pages that only mention it in a stylesheet.
#
# The namespace wildcard is what makes this work in both branches below, and it
# is security audit L2 (Indexverschmutzung). An HTML document parsed by libxml2's
# HTML parser has elements without a namespace, so "script" matched; an XHTML
# document goes to the XML parser and its elements are named
# {http://www.w3.org/1999/xhtml}script, so the same pattern matched nothing at
# all and the whole stylesheet plus the whole script body went into the index.
# "{*}" matches the tag in any namespace and in none, so one tuple serves both
# parsers and the two branches cannot drift apart again.
_INVISIBLE_TAGS = ("{*}script", "{*}style")

# Above this share of replacement characters the fallback decoding is not a text
# any more, it is a guess that failed.
_REPLACEMENT_CHARACTER = "�"
_MAX_REPLACEMENT_SHARE = 0.05

# Hard ceiling on the RTF bytes handed to striprtf (security audit H1). Its
# HYPERLINK regex backtracks quadratically, and INDEX_WORKERS is 1, so a crafted
# file under a megabyte burns the full extraction deadline of the single indexer
# of the whole instance (measured: 252 KB = 10.7 s, 656 KB > 120 s). A real RTF
# whose text survives the 512k character cap is far smaller than this; anything
# larger is skipped as oversized rather than parsed.
_MAX_RTF_BYTES = 256 * 1024

# Below this share of printable characters an RTF result is nonsense rather than
# text. Measured against a deliberately broken file: 0.72 printable, while an
# intact document sits at 1.0.
_MIN_PRINTABLE_SHARE = 0.90


def _decode(raw: bytes) -> str | None:
    """Turn bytes into text, or say that it cannot be done.

    charset-normalizer first, because it is the one component that knows about
    cp1252 and latin-1, which is what German legacy files are written in. When it
    has no answer, UTF-8 with replacement characters is the fallback, and when
    that fallback is mostly replacement characters the honest answer is None.
    """
    if not raw:
        return ""
    best = from_bytes(raw).best()
    if best is not None:
        return str(best)
    text = raw.decode("utf-8", errors="replace")
    if not text or text.count(_REPLACEMENT_CHARACTER) / len(text) > _MAX_REPLACEMENT_SHARE:
        return None
    return text


def _printable_share(text: str) -> float:
    """Share of characters that a reader would see. Whitespace counts as printable."""
    if not text:
        return 0.0
    printable = sum(1 for character in text if character.isprintable() or character in "\t\r\n ")
    return printable / len(text)


def extract_plain(path: str) -> ExtractionOutcome:
    """Plain text, Markdown and CSV, which are the same problem three times.

    Markdown syntax and CSV separators are left in place on purpose. Stripping
    them would need a parser per format for a search index that tokenises the text
    anyway, and a stray pipe character has never made a document unfindable.
    """
    raw = Path(path).read_bytes()
    text = _decode(raw)
    if text is None:
        return ExtractionOutcome.failed(Reason.ENCODING_UNKNOWN)
    return cap_text(text)


def extract_html(path: str) -> ExtractionOutcome:
    """The visible text of an HTML or XHTML file, script and style removed."""
    raw = Path(path).read_bytes()
    text = _decode(raw)
    if text is None:
        return ExtractionOutcome.failed(Reason.ENCODING_UNKNOWN)

    if _looks_like_xml(text):
        # The raw bytes, not the decoded string: an XML parser reads its own
        # encoding declaration, and handing it text that no longer matches that
        # declaration is how a document becomes unparseable on the way in.
        root = etree.fromstring(raw, parser=_XML_PARSER)
    else:
        root = html.document_fromstring(text, parser=_HTML_PARSER)

    for element in list(root.iter(*_INVISIBLE_TAGS)):
        parent = element.getparent()
        if parent is not None:
            parent.remove(element)

    return cap_text(" ".join(part.strip() for part in root.itertext() if part.strip()))


def extract_rtf(path: str) -> ExtractionOutcome:
    """RTF, with the plausibility check that stands in for the missing error path."""
    raw = Path(path).read_bytes()
    # Oversized RTF is skipped before striprtf ever sees it (security audit H1):
    # its hyperlink regex backtracks quadratically and would hold the single
    # indexer for the full deadline. A genuine RTF whose text matters is small.
    if len(raw) > _MAX_RTF_BYTES:
        return ExtractionOutcome.skipped(Reason.TOO_LARGE)
    source = _decode(raw)
    if source is None:
        return ExtractionOutcome.failed(Reason.ENCODING_UNKNOWN)

    text = rtf_to_text(source, errors="ignore")
    if _printable_share(text) < _MIN_PRINTABLE_SHARE:
        return ExtractionOutcome.skipped(Reason.EMPTY_TEXT)
    return cap_text(text)


def _looks_like_xml(text: str) -> bool:
    """True for a document that starts with an XML declaration.

    XHTML is parsed as XML, with the hardened parser, and everything else goes to
    the forgiving HTML parser. The declaration is the only reliable marker: the
    mimetype comes from Nextcloud and says xhtml for files that are plain HTML
    inside, and the HTML parser would silently accept a broken XML document
    instead of reporting failed(xml_invalid).
    """
    return text.lstrip().startswith("<?xml")
