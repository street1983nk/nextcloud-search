"""Mail files (.eml): subject, sender, recipients, the text and the names of attachments.

FMT-01. A mail is found by the words a person remembers about it: who wrote,
to whom, what the subject said, what the text said. Those four go into the
index, decoded (RFC 2047 encoded words in any charset, transfer encodings), and
an HTML only mail goes through the same hardened HTML route as an HTML file
(text.html_to_text: no entity resolution, no network, script and style
removed).

**Attachments by name only (D-31-04).** The name of an attachment is in the
text, its content is not. Reading attachments would be a second container
format inside this one, with its own limits for size, time and depth (a
forwarded mail carries a mail that carries attachments), and that is a piece of
work of its own (a v1.6 candidate). A search for "vertrag.pdf" finds the mail;
a search for a word inside that PDF does not, and the user knows where to look.

**Headers: Subject, From, To and Cc, nothing else.** Bcc is not meant to be
seen by the other recipients, and the Received chain names servers and internal
addresses that nobody searches for. A header the parser cannot read is left out
rather than failing the mail (a From with thousands of nested parentheses ends
in RecursionError inside the header parser, measured), because the other
headers and the text still find it.

**Limits, and why they sit before the parser.** The email package builds an
object for every part and recurses once per level before any loop of ours can
count anything. Measured on CPython 3.13.13: 200 000 empty parts in a 1.4 MB
mail cost the parser 10.8 s, 1 000 nested levels end in RecursionError inside
it. So count_parts runs over the raw bytes first and is an upper bound of the
parts: every part starts with a delimiter line, a delimiter line is "--" plus a
boundary that the mail declares somewhere. Over MAX_MAIL_PARTS the body is not
parsed at all; the headers alone are read, and the verdict is
indexed(truncated). The loop over the attachments counts against the same limit
as a second line, for a structure the rough count should ever miss.

**Headers are bounded in length and in total (security audit 31-15, H-31-01).**
The header parser of the email package is pure Python and grows faster than
the length it reads. Measured on CPython 3.13.13 in the extraction child: a To
of 100 000 addresses (1.2 MB) and a Content-Type of 100 000 parameters (1 MB)
each ran into the extraction deadline of 120 s, and 900 parts with a
Content-Type of 8 KiB took 97 s, because the parser reads the structural
headers of every part more than once (the feed parser, get_content_type,
get_filename). count_parts bounds the parts, not the length of a header. So
every header value the parser is handed is cut to MAX_HEADER_CHARS first, and
every value it parses counts against MAX_HEADER_BUDGET for the whole mail; past
the budget the body is given up and only the headers are read, as for a mail
with too many parts. A cut header and a spent budget both make the verdict
indexed(truncated).

**Forwarding deeper than MAIL_MAX_NESTING is an attack signature (D-36-17,
plan 36-09).** Nesting needs no boundary at all (message/rfc822 inside
message/rfc822), so no count of parts sees it coming. After a parse that
succeeded, a walk over a stack (no recursion of ours) measures the deepest
chain of message/rfc822 parts before any text is collected; deeper than 32 is
skipped(blocked_malicious) with the detail "mail_nesting" (36-WORTLAUT.md A3,
owner answer O6 (a)). Forwarded chains of real mailboxes reach a few levels,
32 leaves room for automatic forwarding, and a mail with hundreds of levels is
no mail a person wrote.

**RecursionError.** The parser itself recurses once per level, so 1000 levels
end in RecursionError inside it before the walk could run. The error is caught
around the parser and around get_body, iter_attachments and get_content, which
recurse on their own. Then a cheap count over the raw bytes decides: more than
32 header lines "Content-Type: message/rfc822" (any case) make the verdict
mail_nesting as well; otherwise it stays failed(corrupt) with the detail
"RecursionError", as before: a structure deep enough to beat the parser
without forwarding is a broken file, not a signature of A3.

clean_display_name is shared: the reader of ZIP files uses it for the names of
its members (plan 31-08), so both kinds of name are cleaned the same way.

This module does not log. Everything it reads is content of a user's file.
"""

from __future__ import annotations

import io
import re
import unicodedata
from dataclasses import dataclass
from email.message import EmailMessage, Message
from email.parser import BytesHeaderParser, BytesParser
from email.policy import EmailPolicy
from pathlib import Path
from typing import Any, Final, cast
from urllib.parse import unquote_to_bytes

from lxml import etree  # pyright: ignore[reportAttributeAccessIssue]

from findling.extract.dispatch import cap_text
from findling.extract.errors import ExtractionOutcome, Reason, State
from findling.extract.text import _decode, html_to_text

# The most parts a mail may have before only its headers are read. Far above any
# mail a person sends (a thick thread with every quoted attachment stays in the
# tens), far below the 200 000 parts that cost the parser 10.8 s. Applies to the
# rough count before parsing and to the loop over the attachments alike.
MAX_MAIL_PARTS = 1000

# The longest name of an attachment that goes into the text. A file system
# allows 255 bytes per name; a longer one is not a name but a payload.
MAX_DISPLAY_NAME_CHARS = 255

# The longest header value the parser is handed, and how many characters of
# header values it may parse for one mail (H-31-01, see the module docstring).
# 32 KiB hold a To or Cc of about 1000 addresses; parsing one such value took
# 0.25 s on the development machine. The budget is spent by every read of a
# header, structural ones included, and holds the worst case of a whole mail to
# a few seconds there (31-AUDIT.md, H-31-01), while a mail with the full 1000
# attachments of MAX_MAIL_PARTS and ordinary headers stays far below it.
MAX_HEADER_CHARS = 32 * 1024
MAX_HEADER_BUDGET = 1024 * 1024

# The deepest chain of message/rfc822 parts a mail may carry (D-36-17,
# 36-WORTLAUT.md A3, owner answer O6 (a)); one level deeper is mail_nesting.
MAIL_MAX_NESTING: Final = 32

# A header line that opens a forwarded mail, at the start of the mail or after a
# line break, in any case. Only counted when the parser ran into RecursionError.
_FORWARD_HEADER = re.compile(rb"(?:\A|(?<=[\r\n]))content-type:[ \t]*message/rfc822", re.IGNORECASE)

_HEADERS = ("subject", "from", "to", "cc")

# The body in the order a reader would choose it: the plain text when the mail
# has both, the HTML when it has nothing else.
_BODY_PREFERENCE = ("plain", "html")

# Every spelling of the boundary parameter that the parser of the standard
# library accepts (all five measured): boundary=, in any case, quoted or bare,
# and the RFC 2231 forms boundary*= (charset'language'percent-encoded),
# boundary*0= and boundary*0*= (sections, joined in order). Searched over the
# whole raw mail and not only in Content-Type headers: a stray match in a text
# only adds a boundary that no delimiter line uses, the count stays an upper
# bound.
_BOUNDARY_PARAMETER = re.compile(
    rb'boundary(?:\*(\d+))?(\*)?[ \t]*=[ \t]*(?:"((?:[^"\\\r\n]|\\.)*)"|([^\s;"]+))',
    re.IGNORECASE,
)

# A line that starts with "--", at the start of the mail or after a line break.
# A lone CR counts as a line break: the parser of the standard library splits
# there too, so a mail written with CR only must not slip past the count.
_DELIMITER_CANDIDATE = re.compile(rb"(?:\A|(?<=[\r\n]))--([^\r\n]*)")

_QUOTED_PAIR = re.compile(rb"\\(.)")

# Characters that change how a name is shown without being part of it: the bidi
# embeddings and overrides U+202A to U+202E (U+202E turns "rechnung<RLO>fdp.exe"
# into what looks like a PDF), the isolates U+2066 to U+2069 and the three
# directional marks. Control characters (category Cc) go as well.
_HIDDEN_FORMATTING = frozenset("\u200e\u200f\u061c\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


class _HeaderBudgetSpent(Exception):
    """The header values of this mail cost more parsing than MAX_HEADER_BUDGET allows."""


@dataclass(slots=True)
class _HeaderBudget:
    """What is left to parse of the header values of one mail, and whether a value was cut."""

    left: int = MAX_HEADER_BUDGET
    cut: bool = False

    def take(self, value: str) -> str:
        if len(value) > MAX_HEADER_CHARS:
            value = value[:MAX_HEADER_CHARS]
            self.cut = True
        if len(value) > self.left:
            raise _HeaderBudgetSpent
        self.left -= len(value)
        return value


class _BoundedPolicy(EmailPolicy):
    """policy.default, with every header value cut and counted before the parser reads it.

    header_fetch_parse is the one place the email package turns a stored raw
    value into a parsed header: ``message[name]``, get_content_type, get_param,
    get_filename and the feed parser all come through it. A value that is
    already a parsed header object is passed on as it is.
    """

    header_budget: _HeaderBudget | None = None

    def header_fetch_parse(self, name: str, value: Any) -> Any:
        if self.header_budget is not None and isinstance(value, str):
            value = self.header_budget.take(value)
        return super().header_fetch_parse(name, value)


# The policy every parse of this module starts from; each mail gets a clone
# with a fresh budget, because a policy object cannot be changed once built.
_BOUNDED: Final = _BoundedPolicy()


def _policy_for(budget: _HeaderBudget) -> EmailPolicy:
    """A clone of _BOUNDED that spends ``budget``.

    clone() takes every attribute the class defines; typeshed lists only the
    fields of EmailPolicy, so the call goes through Any.
    """
    return cast("EmailPolicy", cast("Any", _BOUNDED).clone(header_budget=budget))


def extract_eml(path: str) -> ExtractionOutcome:
    """The searchable text of one .eml file, with the limits described above."""
    raw = Path(path).read_bytes()
    if count_parts(raw) > MAX_MAIL_PARTS:
        return _headers_only(raw)

    budget = _HeaderBudget()
    try:
        message = cast("EmailMessage", BytesParser(policy=_policy_for(budget)).parse(io.BytesIO(raw)))
        if forwarding_depth(message) > MAIL_MAX_NESTING:
            return ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail="mail_nesting")
        lines = _header_lines(message)
        lines.append(_body_text(message))
        names, complete = _attachment_names(message)
    except _HeaderBudgetSpent:
        return _headers_only(raw)
    except RecursionError:
        if count_forward_headers(raw) > MAIL_MAX_NESTING:
            return ExtractionOutcome.skipped(Reason.BLOCKED_MALICIOUS, detail="mail_nesting")
        return ExtractionOutcome.failed(Reason.CORRUPT, detail="RecursionError")

    outcome = cap_text(_joined([*lines, *names]))
    return outcome if complete and not budget.cut else _cut(outcome)


def forwarding_depth(message: Message) -> int:
    """The deepest chain of message/rfc822 parts in a parsed mail, measured without recursion.

    The content type is read from the raw header items and never through the
    policy, so the walk spends nothing of the header budget and cannot be
    beaten by a header parser that recurses. A mail that is itself
    message/rfc822 counts as the first level, which is how a forwarded mail
    stored on its own looks.
    """
    deepest = 0
    stack: list[tuple[Message, int]] = [(message, 0)]
    while stack:
        part, depth = stack.pop()
        if _raw_content_type(part) == "message/rfc822":
            depth += 1
            deepest = max(deepest, depth)
        payload = part.get_payload()
        if isinstance(payload, list):
            stack.extend((child, depth) for child in cast("list[Message]", payload))
    return deepest


def _raw_content_type(part: Message) -> str:
    """The media type of a part from its raw Content-Type item, lower case, empty when there is none."""
    for name, value in part.raw_items():
        if name.lower() == "content-type":
            return str(value).split(";", 1)[0].strip().lower()
    return ""


def count_forward_headers(raw: bytes) -> int:
    """How many header lines of the raw mail open a forwarded mail; an upper bound of its nesting."""
    return sum(1 for _ in _FORWARD_HEADER.finditer(raw))


def _headers_only(raw: bytes) -> ExtractionOutcome:
    """Subject, From, To and Cc alone, marked truncated: the way out of every limit on the body."""
    head = BytesHeaderParser(policy=_policy_for(_HeaderBudget())).parse(io.BytesIO(raw))
    return _cut(cap_text(_joined(_header_lines(head))))


def count_parts(raw: bytes) -> int:
    """An upper bound of the MIME parts of a mail, read from its bytes without parsing.

    Counts the lines that open a part: "--" plus a declared boundary, followed
    by nothing but blanks. A closing line ("--boundary--") opens no part and is
    not counted, and a line of "--" that belongs to no declared boundary (a
    signature separator) is text. Stops one past MAX_MAIL_PARTS, which is all
    the caller needs to know.
    """
    boundaries = _declared_boundaries(raw)
    if not boundaries:
        return 0
    count = 0
    for match in _DELIMITER_CANDIDATE.finditer(raw):
        if match.group(1).rstrip(b" \t") in boundaries:
            count += 1
            if count > MAX_MAIL_PARTS:
                break
    return count


def clean_display_name(name: str) -> str:
    """A file name as it may be shown: no control or bidi characters, at most 255 characters.

    Shared by the mail reader (names of attachments) and the ZIP reader (names
    of members, plan 31-08). The name is display text only and never a path.
    """
    kept = "".join(
        character
        for character in name
        if character not in _HIDDEN_FORMATTING and unicodedata.category(character) != "Cc"
    )
    return kept.strip()[:MAX_DISPLAY_NAME_CHARS]


def _declared_boundaries(raw: bytes) -> set[bytes]:
    """Every boundary the mail declares, in every spelling the parser accepts.

    Sections of an RFC 2231 parameter (boundary*0, boundary*1, ...) are joined
    in the order they come, and every prefix of the join is kept as well: a
    prefix that no delimiter line uses costs nothing, a join that misses one
    would let a whole structure past the count. The parser strips trailing
    blanks off a boundary, so both forms go in.
    """
    found: set[bytes] = set()
    joined = b""
    for match in _BOUNDARY_PARAMETER.finditer(raw):
        section, extended, quoted, bare = match.groups()
        value = _QUOTED_PAIR.sub(rb"\1", quoted) if quoted is not None else bare
        if extended is not None:
            value = _rfc2231_value(value, first=section in (None, b"0"))
        if section is None or section == b"0":
            joined = value
        else:
            joined += value
        found.update((joined, joined.rstrip()))
    return found


def _rfc2231_value(value: bytes, *, first: bool) -> bytes:
    """The bytes of an extended parameter value: charset'language' prefix off, percent signs decoded."""
    if first and value.count(b"'") >= 2:
        value = value.split(b"'", 2)[2]
    return unquote_to_bytes(value)


def _header_lines(message: Message) -> list[str]:
    """The decoded values of Subject, From, To and Cc, each one left out when it cannot be read."""
    return [text for name in _HEADERS if (text := _header_text(message, name))]


def _header_text(message: Message, name: str) -> str | None:
    """One decoded header, or None when it is missing or beats the header parser.

    The header parser recurses on nested comments and quoted strings, and a
    header is the cheapest place for a crafted mail to put that: one header
    lost is a smaller loss than the mail. RecursionError is an Exception and
    is caught here on purpose. A spent header budget is not a broken header
    and goes on to extract_eml, which reads the headers alone then.
    """
    try:
        value = message[name]
        return None if value is None else str(value)
    except _HeaderBudgetSpent:
        raise
    except Exception:
        return None


def _body_text(message: EmailMessage) -> str:
    """The text of the body the mail prefers, plain before HTML, empty when there is none."""
    body = message.get_body(preferencelist=_BODY_PREFERENCE)
    if body is None:
        return ""
    content = _content_of(cast("EmailMessage", body))
    if not content or not content.strip():
        return ""
    if body.get_content_type() != "text/html":
        return content
    try:
        return html_to_text(content)
    except etree.LxmlError:
        # A part that the XML parser refuses costs the body and nothing else:
        # subject, sender and recipients still find the mail.
        return ""


def _content_of(part: EmailMessage) -> str | None:
    """The decoded text of a part, through charset-normalizer when its charset is unknown.

    get_content raises LookupError for a charset no codec knows (pitfall 4 of
    phase 31, measured with x-unknown-zz) and UnicodeDecodeError for bytes the
    declared one cannot decode. Both are a wrong label and not a broken mail,
    so the raw bytes go to the same detection that plain text files get.
    """
    try:
        content = part.get_content()
    except (LookupError, UnicodeDecodeError):
        payload = part.get_payload(decode=True)
        return _decode(payload) if isinstance(payload, bytes) else None
    return content if isinstance(content, str) else None


def _attachment_names(message: EmailMessage) -> tuple[list[str], bool]:
    """The cleaned names of the attachments, and whether the loop saw all of them."""
    names: list[str] = []
    for seen, part in enumerate(message.iter_attachments()):
        if seen >= MAX_MAIL_PARTS:
            return names, False
        name = _filename_of(part)
        if name:
            names.append(name)
    return names, True


def _filename_of(part: Message) -> str:
    """The display name of an attachment, empty when it has none or it cannot be read.

    The name lives in a header (Content-Disposition or Content-Type), so the
    same rule as for _header_text applies: a header that beats the parser is
    left out.
    """
    try:
        name = part.get_filename()
    except _HeaderBudgetSpent:
        raise
    except Exception:
        return ""
    return clean_display_name(name) if name else ""


def _joined(parts: list[str]) -> str:
    return "\n".join(part for part in parts if part.strip())


def _cut(outcome: ExtractionOutcome) -> ExtractionOutcome:
    """The same outcome marked truncated, when it has text to mark."""
    if outcome.state is State.INDEXED and not outcome.truncated:
        return ExtractionOutcome.indexed(outcome.text, truncated=True)
    return outcome
