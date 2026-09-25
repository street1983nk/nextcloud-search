"""From a search line to a query: filters, umlaut variants, lenient parsing.

The order of the three steps is fixed and it is the reason this module exists as
one function instead of three call sites. Cutting the filter prefix has to happen
before anything reads the text as a full text expression, adding umlaut
alternatives has to happen after the prefix is gone so that "type:pdf" is never
turned into a term, and the parser runs last on the finished string.

Four parser settings are written out at the call below rather than left to their
defaults, because three of them differ from the default and the fourth is a
security control:

* ``default_field_names`` decides what "a word without a field" means. The answer
  depends on whether the caller asked for the file name filter, and since phase
  19 it depends on the index directory as well: which body fields a search may
  name is a question about the schema that lies on disk, never about the line
  that was typed.
* ``field_boosts`` puts the file name above the title and the title above the
  body. A name is a deliberate act, a body word is an accident of prose. It hangs
  on that very same directory for the very same reason, which is why both halves
  arrive as one :class:`FieldPlan` and never as two constants beside one another.
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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from tantivy import FieldType, Index, Occur, Query

from findling.config import SEARCH_QUERY_MAX_DEPTH
from findling.index.analyzer import normalize
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_EXT,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_TITLE,
)

LOGGER = logging.getLogger("findling.query")

# The written out spellings and the umlaut they stand for. German keyboards are
# not always German, and a fair share of file names and search terms carries the
# transcription rather than the character.
UMLAUTS: Final = (("ue", "ü"), ("oe", "ö"), ("ae", "ä"), ("ss", "ß"))


@dataclass(frozen=True, slots=True)
class FieldPlan:
    """Which fields one search reaches into, and what each of them weighs.

    Both halves in one value, and that is the whole statement of this class.
    Measured on tantivy 0.26.2 (19-RESEARCH measurement M-1), ``field_boosts``
    answers a field name the schema does not know with the same
    ``ValueError: Field `body_es` is not defined in the schema.`` that
    ``default_field_names`` answers it with. That exception leaves the query
    builder, the route loses its lexical half, and the search bar stays empty
    until somebody rebuilds the index. Two constants beside one another are
    therefore two ways into that failure while only one of them looks like the
    subject; held as one value they cannot drift apart.

    ``fields`` is what a bare word searches. It is not the schema and it is not
    "every field that carries text": a name the index on disk does not have is
    the failure above, and a field whose analyzer chain nobody meant to ask is a
    hit nobody can explain.

    ``boosts`` is how the hits of those fields weigh against one another. It is
    not a filter and not a ranking of its own: tantivy sums the contributions of
    every field a document matches in (measurement M-3), so a weight moves a
    document and never removes it. Its keys stay inside ``fields`` for the reason
    in the paragraph above.

    It is a ``Mapping`` in the annotation and a ``MappingProxyType`` in every
    value this module builds, which is audit finding L-19-02. ``frozen=True``
    freezes the assignment of the attribute and nothing about the object behind
    it, so a plain dict here would leave the frozen fallback plan editable from
    anywhere in the process, which is the one thing it must not be. The proxy is
    not a deep copy and does not have to be: the values are floats.

    A plan is unhashable either way, before and after that change, because
    neither a dict nor a proxy over one hashes. Nothing hashes a plan today; a
    ``functools.cache`` over a function taking one would be an unpleasant
    surprise, and this sentence is here so that it is a known one.

    ``title_only`` is what the same bare word searches once the built in
    Nextcloud filter for "file name instead of content" is set. It is not a
    second plan and not a subset by construction: it is the other answer of this
    one value, so that two answers to one question cannot be taken from two
    places.
    """

    fields: tuple[str, ...]
    boosts: Mapping[str, float]
    title_only: tuple[str, ...]


# The file name above the title and the title above the body. A name is a
# deliberate act, a body word is an accident of prose.
NAME_BOOST: Final = 3.0
TITLE_BOOST: Final = 2.0

# One weight per body language, keyed by the language code the way
# findling.index.schema.BODY_FIELD is keyed, and a closed mapping for the reason
# that one is closed: a composed key loses a whole language on a typo and nothing
# anywhere says so.
#
# The four languages of the build out stand at 0.6. That figure comes from
# .planning/research/FEATURES.md question 3, it is a recommendation and not a
# measurement, and the ranking probe of plan 19-04 is what supplies the measured
# number behind it. What is not open is the direction: 0.6 lies below body_en at
# 0.8, and that is the literal promise of success criterion 3 of the roadmap.
BODY_BOOST: Final = {"de": 1.0, "en": 0.8, "es": 0.6, "it": 0.6, "nl": 0.6, "pt": 0.6}

# What a bare word searches on an index of every release up to 1.2.0. In schema
# order, and the German body first because it is the field that carries the
# content of the file.
#
# The file name list is the answer once the built in Nextcloud filter for "file
# name instead of content" is set. The PHP side has to name that filter in
# getSupportedFilters(), and a provider that leaves it out is skipped entirely by
# the client rather than being asked without it: the search then looks like a
# broken backend while it is a missing declaration. That declaration is plan
# 02-12; this module only has to answer correctly once the flag arrives.
#
# Every weight is read out of the constants above, so that one number has exactly
# one spelling in this file.
LEGACY_PLAN: Final = FieldPlan(
    fields=(FIELD_BODY_DE, FIELD_BODY_EN, FIELD_NAME, FIELD_TITLE),
    # Behind a read only view, audit finding L-19-02. ``frozen=True`` protects
    # the assignment of the field and not the object behind it, and this one is
    # the fail closed line of the whole phase: a single
    # ``LEGACY_PLAN.boosts["body_es"] = 0.6`` anywhere in the process would turn
    # the value that exists to keep a name out of the parser into the very
    # ValueError it is held against, on every installation coming from 1.2.0 and
    # for as long as the container lives.
    boosts=MappingProxyType(
        {
            FIELD_NAME: NAME_BOOST,
            FIELD_TITLE: TITLE_BOOST,
            FIELD_BODY_DE: BODY_BOOST["de"],
            FIELD_BODY_EN: BODY_BOOST["en"],
        }
    ),
    title_only=(FIELD_NAME,),
)

# The plan of a directory that answers none of the names anybody holds for it,
# and the one value build_query turns into an empty answer instead of a query.
#
# Audit finding M-19-01. Until that finding the fallback of
# findling.api.resources.field_plan_for was the legacy plan and nothing stood
# behind it, so a directory that had lost one of the four legacy fields would
# have been answered with a plan naming it, which is the ValueError this whole
# value exists to keep out of the search path. The fallback is probed against the
# directory now like every other plan, and this is what is left when even that
# probe keeps nothing: a container that answers every search empty and says so in
# its log, rather than one that answers every search with an exception.
EMPTY_PLAN: Final = FieldPlan(fields=(), boosts=MappingProxyType({}), title_only=())

# SRCH-03 file type. Nextcloud has no built in filter for it, so it travels
# inside the search line and is translated into a required term on the extension.
TYPE_PREFIX: Final = "type:"

# The one table from a type group to its extensions in this whole project. The
# PHP side knows the six group names and not a single extension, and the text
# syntax above is resolved through this very table rather than through a second
# one: two vocabularies for the same six words drift apart without a test ever
# turning red. Both "jpg" and "jpeg" stand here, and so do "tif" and "tiff",
# because a file with the other spelling wears the same symbol in the file list
# and would otherwise fall out of a filter it visibly belongs to.
#
# The limits of the table belong to docs/search-filters.md and not into it: an
# extension that is not listed is reachable under no chip, and a file without an
# extension is reachable under none of them either, because extension_of returns
# the empty string for it and an empty raw field produces no term at all.
TYPE_GROUPS: Final[Mapping[str, tuple[str, ...]]] = {
    "pdf": ("pdf",),
    "documents": ("docx", "odt", "rtf"),
    "spreadsheets": ("xlsx", "ods", "csv"),
    "presentations": ("pptx", "odp"),
    "images": ("jpg", "jpeg", "jps", "mpo", "png", "tif", "tiff", "webp"),
    "text": (
        "txt",
        "text",
        "md",
        "markdown",
        "mdown",
        "mdwn",
        "mkd",
        "htm",
        "html",
        "json",
        "xml",
        "yaml",
        "yml",
        "conf",
        "cnf",
        "eml",
        "adoc",
        "asciidoc",
        "org",
        "fb2",
        "js",
    ),
}

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
        # The mark hangs on the text ``type:`` and on that text alone. The
        # structured group parameter of build_query never sets it, and that is
        # the whole line between the two: api/search.py reads a non empty set of
        # marks as "drop the vector half", so a chip on the result page that
        # arrived as text would switch the semantic search off, which is exactly
        # the failure FILT-01 exists against.
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

    A word behind the prefix that names a group of :data:`TYPE_GROUPS` is
    resolved through that same table, so ``type:images`` means what the chip for
    images means and there is one vocabulary rather than two. The table is the
    source and the text syntax is connected to it, not the other way round.
    Everything else stays what it has always been, a raw extension: a word the
    table does not know is not an error, it is a file type nobody put into a
    group.
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
                word = token[len(TYPE_PREFIX) :].lower().lstrip(".")
                extensions.extend(TYPE_GROUPS.get(word, (word,)))
            else:
                kept.append(token)
        segments.append((quoted, "".join(kept)))
    residual = _rejoin(segments).strip()
    return residual, tuple(dict.fromkeys(extensions))


def carries_one_term(text: str) -> bool:
    """Whether the raw search line holds exactly one term, the file type aside.

    **A single word is answered by the word index alone.** The reason is a
    measurement and not a preference. The report of plan 06.1-20
    (``docs/measurements/2026-09-06-vektordistanzen/README.md``) put both
    distributions on one scale, and they overlap: the one word probes of the
    reference corpus sit 68 to 77 away from their nearest chunk, while the
    paraphrase reaches the document it paraphrases only at 79.5487. So no
    ceiling can hold "one word brings back nothing unrelated" and "the
    paraphrase still finds its document" at the same time, and the second of the
    two is the case the vector half exists for. One word gives the model no
    context to read a meaning out of, and on the lexical side that same word
    already gets the compound splitter, the stemmer and the umlaut variant.

    Counted on the raw line, like :func:`carried_operators`, and after the file
    type prefix is cut out, because that prefix is not a term: ``type:pdf
    vertrag`` asks for one word in a narrower place and not for two words.
    Nought terms is not one: a line that holds nothing but a filter never
    reaches the engine, and this function answers what stood on the line rather
    than what its caller does with the answer.

    The structured group parameter of build_query does not touch this answer
    either, for the same reason it does not set a mark: what is counted here is
    the raw line, and a chip on the result page never stood on it.
    """
    residual, _ = extract_filters(text)
    return len(residual.split()) == 1


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
    # Whether that same raw line held exactly one term, read once by
    # carries_one_term() and carried along for the same reason. Both fields
    # answer the one question of the caller: is this a line the vector half has
    # anything to add to.
    one_term: bool = False
    # The same filter once more on its own, because the vector half knows
    # neither an extension nor a time stamp: its hits never pass through the
    # parser and can only be cut to the requested type by the index lookup in
    # index/search.py::_mtimes_of, which is where this clause is meant to go. A
    # filter that lives in ``query`` alone lets hits of a foreign type through
    # the semantic side (13-RESEARCH finding 1). None when nothing was filtered.
    filter_query: Query | None = None


def extensions_of(groups: Sequence[str]) -> tuple[str, ...]:
    """The extensions of the named type groups, free of duplicates and in order.

    Every name is lowercased before it is looked up, and the reason is not
    tidiness: extension_of writes the extension of a file in lower case, the raw
    tokeniser normalises nothing afterwards, and a group name that arrives as
    "PDF" would therefore be translated into a term that matches not one single
    document.

    A name that is not a group of the table contributes nothing, and it does not
    raise. It reaches this function out of an address, and an address that
    carries a word nobody knows is not an error worth an exception; it means
    "no filter", the way every other value of that address is read.
    """
    found: list[str] = []
    for group in groups:
        found.extend(TYPE_GROUPS.get(group.lower(), ()))
    return tuple(dict.fromkeys(found))


def _extension_query(index: Index, extensions: tuple[str, ...]) -> Query:
    """One required term on the extension field, several of them as alternatives."""
    terms = [Query.term_query(index.schema, FIELD_EXT, extension) for extension in extensions]
    if len(terms) == 1:
        return terms[0]
    return Query.boolean_query([(Occur.Should, term) for term in terms])


def _mtime_range_query(index: Index, since: int | None, until: int | None) -> Query | None:
    """One range over the modification time, or None when neither bound is set.

    ``use_inverted_index`` is left at its default of False and is deliberately
    neither written out nor passed through. FIELD_MTIME carries
    ``indexed=False`` (index/schema.py), and the reflex of reading that and
    setting the parameter to True does not produce an error: measured against
    the installed tantivy 0.26.0 on 16.09.2026, the very range that returns
    three documents over the column returns an empty hit list through the
    inverted index, without an exception and without a warning. On the result
    page that reads as "there is nothing in this period", which is the kind of
    defect that survives a release.

    Both bounds are inclusive and either one may stand alone.
    """
    if since is None and until is None:
        return None
    return Query.range_query(
        index.schema,
        FIELD_MTIME,
        FieldType.Integer,
        lower_bound=since,
        upper_bound=until,
        include_lower=True,
        include_upper=True,
    )


def _filter_clause(
    index: Index,
    extensions: tuple[str, ...],
    since: int | None,
    until: int | None,
) -> Query | None:
    """Extensions and period as exactly one clause, or None when neither is set.

    One clause and not two, because the semantic half of the search receives
    this same object in index/search.py::_mtimes_of: a filter that is assembled
    a second time somewhere else is a filter that differs in one of the two
    places on the day somebody changes it.
    """
    clauses = [
        clause
        for clause in (
            _extension_query(index, extensions) if extensions else None,
            _mtime_range_query(index, since, until),
        )
        if clause is not None
    ]
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return Query.boolean_query([(Occur.Must, clause) for clause in clauses])


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


def build_query(
    index: Index,
    text: str,
    *,
    title_only: bool = False,
    groups: Sequence[str] = (),
    since: int | None = None,
    until: int | None = None,
    plan: FieldPlan = LEGACY_PLAN,
) -> RewrittenQuery:
    """Turn a search line into a query, its filters and the parser's complaints.

    Never raises on user input. A stray quotation mark, a regular expression, a
    field that does not exist **in the typed line**: all of them come back as an
    entry in ``errors`` together with a query that finds nothing, because an
    exception here is an HTTP 500 and a search bar that stays broken until
    somebody redeploys.

    A field that does not exist in ``plan`` is the other case and it is not
    covered by that sentence, which is audit finding L-19-04. Measured on
    tantivy 0.26.2 (19-RESEARCH M-1), both ``default_field_names`` and
    ``field_boosts`` answer a name the schema does not know with a ``ValueError``
    out of the parser, and nothing here catches it. That is the whole reason
    ``plan`` is computed against the directory in
    :func:`findling.api.resources.field_plan_for` and never composed at a call
    site: the lenient parser is lenient about what a user types and about
    nothing else.

    ``groups``, ``since`` and ``until`` are the structured half of the filter,
    the one the result page sets. They are keyword arguments with a default so
    that the callers who filter nothing stay exactly as they are, and ``groups``
    is a list of group names rather than a piece of text on purpose: written
    into the search line as ``type:``, the same request would set the mark
    FILETYPE and switch the vector half off, which is the failure FILT-01 is
    about.

    ``plan`` carries a default for that same reason and for one more: here the
    default is a safety measure rather than a convenience. It is
    :data:`LEGACY_PLAN`, the frozen field plan of every release up to 1.2.0, and
    it is never anything read out of ``settings()``. A caller who forgets the
    plan therefore searches exactly the four fields of today and breaks nothing,
    which is the fail closed line that ``_schema_is_legacy`` and
    ``_languages_are_legacy`` already walk (19-RESEARCH pitfall 6).
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
    one_term = carries_one_term(text)
    # The second of the two calls of the normalisation helper, and it stands
    # after the depth guard on purpose: that guard is counted on the raw input so
    # that nothing can walk past it, and composing a string cannot open a bracket
    # anyway. Everything below this line therefore works in the one Unicode
    # spelling the write side put into the index; without it a name a Mac client
    # wrote shares no term with the same name typed into the search bar. The
    # reasoning is at findling.index.analyzer.normalize.
    residual, extensions = extract_filters(normalize(text))
    # The union of what the line asked for and what the chips ask for, the ones
    # from the line first. The union and not the intersection: "type:pdf"
    # together with the chip for images would be guaranteed empty as an
    # intersection, and the page has no way of explaining an empty list that is
    # nobody's mistake.
    extensions = tuple(dict.fromkeys(extensions + extensions_of(groups)))
    rewritten = add_umlaut_variants(residual).strip()
    if not rewritten:
        # No term, no engine. A search line that holds nothing but a filter would
        # otherwise ask for every PDF on the instance in no meaningful order.
        # ``filter_query`` stays at None for the same reason: there is no list to
        # narrow, and a clause without a query is a clause nobody can use.
        return RewrittenQuery(
            query=None,
            text="",
            extensions=extensions,
            errors=[],
            operators=operators,
            one_term=one_term,
        )

    searched = list(plan.title_only) if title_only else list(plan.fields)
    if not searched:
        # No field, no query, and the same empty answer as a line without a term
        # above. A plan reaches this state when the directory knows none of the
        # names its marks promise and none of the legacy four either, which is
        # audit finding M-19-01: the alternative is handing an empty field list
        # to the parser, and an empty list is the one input that turns the
        # lenient parser into a raising one. The reason is already in the log,
        # one warning per dropped field, written where the plan was computed.
        return RewrittenQuery(
            query=None,
            text="",
            extensions=extensions,
            errors=[],
            operators=operators,
            one_term=one_term,
        )

    # The list above and this copy are the two allocations per query that audit
    # finding L-19-03 names, and they are kept on purpose. Both are at most eight
    # entries against a parser measured at 2,26 us, so the cost is under the
    # noise of one call; both cross into a native extension, which may keep what
    # it is handed; and the alternative, two ready made forms cached on the
    # frozen value through object.__setattr__ in a __post_init__, would put a
    # second representation of the field list beside the first one for a saving
    # nothing can measure. A plan is one value, and that is worth more here than
    # two allocations of eight.
    parsed, errors = index.parse_query_lenient(
        rewritten,
        default_field_names=searched,
        field_boosts=dict(plan.boosts),
        conjunction_by_default=True,
        allow_regexes=False,
    )
    if errors:
        # Debug and nowhere else. These entries quote the input, so an info line
        # would put a search term into a log that operators read and ship.
        LOGGER.debug("the query parser reported %d issue(s)", len(errors))
    # Built once and used twice: required here, so that the lexical half is
    # narrowed before the fusion window is filled, and handed out below, so that
    # the semantic half is narrowed by the very same object.
    filter_query = _filter_clause(index, extensions, since, until)
    if filter_query is not None:
        parsed = Query.boolean_query([(Occur.Must, parsed), (Occur.Must, filter_query)])
    return RewrittenQuery(
        query=parsed,
        text=rewritten,
        extensions=extensions,
        errors=list(errors),
        operators=operators,
        one_term=one_term,
        filter_query=filter_query,
    )
