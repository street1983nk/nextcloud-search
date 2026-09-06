"""From a search line to a query: filters, umlaut variants, lenient parsing.

The order of the three steps is fixed and it is the reason this module exists as
one function instead of three call sites. Cutting the filter prefix has to happen
before anything reads the text as a full text expression, adding umlaut
alternatives has to happen after the prefix is gone so that "type:pdf" is never
turned into a term, and the parser runs last on the finished string.

Four parser settings are written out at the call below rather than left to their
defaults, because three of them differ from the default and the fourth is a
security control:

* ``default_field_names`` decides what "a word without a field" means, and the
  answer depends on whether the caller asked for the file name filter.
* ``field_boosts`` puts the file name above the title and the title above the
  body. A name is a deliberate act, a body word is an accident of prose.
* conjunction by default, because a split compound otherwise turns into an OR
  over three everyday parts and buries the document that carries all three.
* regular expressions stay off. A regex from a public search bar is a denial of
  service against the instance that hosts it.

The error list of the parser never leaves this module towards a user and never
reaches an info log. It quotes the input it choked on, which makes it exactly as
sensitive as a search term.
"""

import logging
import re
from dataclasses import dataclass
from typing import Final

from tantivy import Index, Occur, Query

from findling.config import SEARCH_QUERY_MAX_DEPTH
from findling.index.analyzer import normalize
from findling.index.schema import FIELD_BODY_DE, FIELD_BODY_EN, FIELD_EXT, FIELD_NAME, FIELD_TITLE

LOGGER = logging.getLogger("findling.query")

# The written out spellings and the umlaut they stand for. German keyboards are
# not always German, and a fair share of file names and search terms carries the
# transcription rather than the character.
UMLAUTS: Final = (("ue", "ü"), ("oe", "ö"), ("ae", "ä"), ("ss", "ß"))

# What a bare word searches. In schema order, and the German body first because
# it is the field that carries the content of the file.
DEFAULT_FIELDS: Final = [FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE]

# What a bare word searches once the built in Nextcloud filter for "file name
# instead of content" is set. The PHP side has to name that filter in
# getSupportedFilters(), and a provider that leaves it out is skipped entirely by
# the client rather than being asked without it: the search then looks like a
# broken backend while it is a missing declaration. That declaration is plan
# 02-12; this module only has to answer correctly once the flag arrives.
TITLE_ONLY_FIELDS: Final = [FIELD_NAME]

FIELD_BOOSTS: Final = {FIELD_NAME: 3.0, FIELD_TITLE: 2.0, FIELD_BODY_DE: 1.0, FIELD_BODY_EN: 0.8}

# SRCH-03 file type. Nextcloud has no built in filter for it, so it travels
# inside the search line and is translated into a required term on the extension.
TYPE_PREFIX: Final = "type:"

# A token this module is willing to rewrite: optional leading + - or !, an
# optional field prefix, and a plain word. Everything else, phrases, wildcards,
# ranges, parentheses, is handed to the parser untouched, because a rewriting
# step that half understands a grammar is worse than one that does not touch it.
_PLAIN_TOKEN: Final = re.compile(r"^(?P<lead>[+\-!]*)(?:(?P<field>[a-z_]+):)?(?P<term>\w+)$")

# Grammar words of the parser. They look like plain tokens and must survive as
# they are.
_OPERATORS: Final = frozenset({"AND", "OR", "NOT", "IN", "TO"})

_QUOTE: Final = '"'

# The five marks a search line can carry. Named constants rather than string
# literals at two call sites, for the reason every allowlist in this project is
# one: a literal spelled differently at the second site is a difference nobody
# sees. They are marks and not a grammar; what they mean to the caller is
# "this person asked for precision", and nothing more.
PHRASE: Final = "phrase"
EXCLUSION: Final = "exclusion"
FIELD: Final = "field"
FILETYPE: Final = "filetype"
BOOLEAN: Final = "boolean"

# A token that begins a negation: a minus or an exclamation mark in front of a
# word. Both are negation in the parser's grammar, and both are somebody asking
# for a document without a word in it. The word character behind the sign is
# what keeps a hyphen inside a word out: "E-Mail" and "Baden-Baden" are spelling
# and not grammar, and the parser reads them the same way.
_NEGATED_TOKEN: Final = re.compile(r"(?:^|\s)[-!]+\w")

# A token that names a field. The same shape the rewriting below recognises, so
# the two cannot drift apart, minus the type prefix, which gets a mark of its
# own because it is cut out of the line instead of parsed.
_FIELD_TOKEN: Final = re.compile(r"(?:^|\s)[+\-!]*([a-z_]+):\w")

# Splits a run into words and the whitespace between them, keeping both. Joining
# on single spaces instead would look identical in every ordinary case and would
# still be wrong: measured, `kaputt "` loses its space, the parser then reads
# `kaputt"` as a well formed term and reports no missing delimiter at all. A
# rewriting step must change what it came for and nothing else.
_WHITESPACE: Final = re.compile(r"(\s+)")


def umlaut_variants(term: str) -> list[str]:
    """Return the term, plus its umlaut spelling when the two differ.

    The German stemmer folds an umlaut inside a word, so "Müller" and "muller"
    both reduce well on their own, but they do not reduce to the *same* stem: one
    character against two. This is the query side answer to that gap. It costs no
    index space, it only ever adds a branch, and it is deliberately dumb.

    Deliberately dumb means it produces nonsense on ordinary words: "neue" comes
    back as "neü". That branch matches nothing and costs one term lookup, which
    is the whole reason the table is allowed to be this simple (assumption A10 of
    the phase research). Do not "fix" the table by adding exceptions; a list of
    exceptions is a dictionary, and a dictionary here would drift away from the
    one the analyser splits compounds with.

    The replacement ignores case because a user types "Mueller" as often as
    "mueller", and the analyser lowercases only after the parser has run.
    """
    variant = term
    for written, umlaut in UMLAUTS:
        variant = re.sub(written, umlaut, variant, flags=re.IGNORECASE)
    return [term] if variant == term else [term, variant]


def carried_operators(text: str) -> frozenset[str]:
    """Which marks of precision the raw search line carries, if any.

    **The model sees words and it does not see operators.** Somebody who puts
    quotation marks around two words, writes a minus in front of one, names a
    field or asks for a file type has asked for exactness, and a second list
    that does not know about that request can only undercut it: it answers the
    documents that feel close to the words, which is the opposite of what was
    asked. So the caller drops the vector half for such a line, and this
    function is where that decision gets its facts.

    **It reads the raw line, before every one of the three steps below.**
    Afterwards the question cannot be answered any more: ``extract_filters`` has
    cut the type prefix out, and ``add_umlaut_variants`` has inserted an ``OR``
    of its own, so a line somebody typed as one word would come back as a
    boolean query. That is the case ``kuendigung`` covers in the tests, and it
    is the only reason this function is not simply called on the finished
    string.

    Recognition and nothing else. What a mark costs is decided by the caller
    (``api/search.py::one_round``), which is also where ``titleOnly`` belongs,
    because that one is not a property of the line at all.
    """
    marks: set[str] = set()
    if _QUOTE in text:
        marks.add(PHRASE)
    if _NEGATED_TOKEN.search(text):
        marks.add(EXCLUSION)
    for token in _WHITESPACE.split(text):
        if token in _OPERATORS:
            marks.add(BOOLEAN)
        if token.lower().startswith(TYPE_PREFIX) and len(token) > len(TYPE_PREFIX):
            marks.add(FILETYPE)
    for match in _FIELD_TOKEN.finditer(text):
        if match.group(1) != TYPE_PREFIX.removesuffix(":"):
            marks.add(FIELD)
    return frozenset(marks)


def _segments(text: str) -> list[tuple[bool, str]]:
    """Split into (is quoted, part) runs along the quotation marks.

    An odd number of quotation marks leaves the last run unterminated. It is
    reported as quoted, which means untouched, and the parser is left to complain
    about the missing delimiter: repairing the quote here would answer a
    different question than the user asked.
    """
    parts = text.split(_QUOTE)
    return [(position % 2 == 1, part) for position, part in enumerate(parts)]


def _rejoin(segments: list[tuple[bool, str]]) -> str:
    return _QUOTE.join(part for _, part in segments)


def extract_filters(text: str) -> tuple[str, tuple[str, ...]]:
    """Cut every ``type:`` prefix out of the text and return it separately.

    Runs before every other step. If it ran later, the prefix would already have
    been read as a word and the file type would end up as a full text term, which
    is the failure that makes a filter look like it silently does nothing.

    Quoted parts are left alone: inside quotation marks ``type:pdf`` is what the
    user is looking for, not how they are looking for it.
    """
    extensions: list[str] = []
    segments: list[tuple[bool, str]] = []
    for quoted, part in _segments(text):
        if quoted:
            segments.append((quoted, part))
            continue
        kept: list[str] = []
        for token in _WHITESPACE.split(part):
            if token.lower().startswith(TYPE_PREFIX) and len(token) > len(TYPE_PREFIX):
                extensions.append(token[len(TYPE_PREFIX) :].lower().lstrip("."))
            else:
                kept.append(token)
        segments.append((quoted, "".join(kept)))
    residual = _rejoin(segments).strip()
    return residual, tuple(dict.fromkeys(extensions))


def add_umlaut_variants(text: str) -> str:
    """Turn every plain token with a written out umlaut form into an alternative.

    ``kuendigung`` becomes ``(kuendigung OR kündigung)``, and a leading plus,
    minus or field prefix is kept in front of the group so that the operator
    still applies to both spellings.
    """
    segments: list[tuple[bool, str]] = []
    for quoted, part in _segments(text):
        if quoted:
            segments.append((quoted, part))
            continue
        segments.append((quoted, "".join(_rewrite_token(token) for token in _WHITESPACE.split(part))))
    return _rejoin(segments)


def _rewrite_token(token: str) -> str:
    if token in _OPERATORS:
        return token
    match = _PLAIN_TOKEN.match(token)
    if match is None:
        return token
    variants = umlaut_variants(match["term"])
    if len(variants) == 1:
        return token
    field = f"{match['field']}:" if match["field"] else ""
    return f"{match['lead']}{field}({' OR '.join(variants)})"


@dataclass(frozen=True, slots=True)
class RewrittenQuery:
    """What one search line turned into.

    ``query`` is ``None`` when there was nothing left to search for. That is a
    normal answer, not a failure: the caller returns an empty result and the
    engine was never asked.
    """

    query: Query | None
    text: str
    extensions: tuple[str, ...]
    errors: list[object]
    # What the raw line asked for, read once by carried_operators() before any
    # of the three steps ran. It rides along here so that the one caller does
    # not ask a second time with a second opinion: two readings of what an
    # operator is drift apart, and the drift would be invisible.
    operators: frozenset[str] = frozenset()


def _extension_query(index: Index, extensions: tuple[str, ...]) -> Query:
    """One required term on the extension field, several of them as alternatives."""
    terms = [Query.term_query(index.schema, FIELD_EXT, extension) for extension in extensions]
    if len(terms) == 1:
        return terms[0]
    return Query.boolean_query([(Occur.Should, term) for term in terms])


def _max_bracket_depth(text: str) -> int:
    """Deepest run of unclosed round brackets, ignoring closers without an opener.

    A pure counter, so the depth guard is testable without an index and cannot
    itself recurse. Only ``(`` and ``)`` matter to the query parser's grammar.
    """
    depth = 0
    deepest = 0
    for char in text:
        if char == "(":
            depth += 1
            deepest = max(deepest, depth)
        elif char == ")" and depth > 0:
            depth -= 1
    return deepest


def build_query(index: Index, text: str, *, title_only: bool = False) -> RewrittenQuery:
    """Turn a search line into a query, its filters and the parser's complaints.

    Never raises on user input. A stray quotation mark, a regular expression, a
    field that does not exist: all of them come back as an entry in ``errors``
    together with a query that finds nothing, because an exception here is an
    HTTP 500 and a search bar that stays broken until somebody redeploys.
    """
    # Bracket depth is checked before the parser is ever entered (security audit
    # C2): parse_query_lenient descends recursively on parentheses, so a deeply
    # nested line overflows the native stack of this very process, which is a
    # crash no except-clause can catch, not an error the parser reports. Counted
    # on the raw input so the guard cannot be walked past by a filter or a variant.
    if _max_bracket_depth(text) > SEARCH_QUERY_MAX_DEPTH:
        return RewrittenQuery(
            query=None,
            text="",
            extensions=(),
            errors=[f"the query nests brackets deeper than {SEARCH_QUERY_MAX_DEPTH} levels"],
        )
    # On the raw line, and therefore above every step below: the type prefix is
    # about to be cut out and the umlaut variants are about to insert an OR, and
    # after either of those the question is not answerable any more.
    operators = carried_operators(text)
    # The second of the two calls of the normalisation helper, and it stands
    # after the depth guard on purpose: that guard is counted on the raw input so
    # that nothing can walk past it, and composing a string cannot open a bracket
    # anyway. Everything below this line therefore works in the one Unicode
    # spelling the write side put into the index; without it a name a Mac client
    # wrote shares no term with the same name typed into the search bar. The
    # reasoning is at findling.index.analyzer.normalize.
    residual, extensions = extract_filters(normalize(text))
    rewritten = add_umlaut_variants(residual).strip()
    if not rewritten:
        # No term, no engine. A search line that holds nothing but a filter would
        # otherwise ask for every PDF on the instance in no meaningful order.
        return RewrittenQuery(query=None, text="", extensions=extensions, errors=[], operators=operators)

    parsed, errors = index.parse_query_lenient(
        rewritten,
        default_field_names=TITLE_ONLY_FIELDS if title_only else DEFAULT_FIELDS,
        field_boosts=FIELD_BOOSTS,
        conjunction_by_default=True,
        allow_regexes=False,
    )
    if errors:
        # Debug and nowhere else. These entries quote the input, so an info line
        # would put a search term into a log that operators read and ship.
        LOGGER.debug("the query parser reported %d issue(s)", len(errors))
    if extensions:
        parsed = Query.boolean_query([(Occur.Must, parsed), (Occur.Must, _extension_query(index, extensions))])
    return RewrittenQuery(
        query=parsed,
        text=rewritten,
        extensions=extensions,
        errors=list(errors),
        operators=operators,
    )
