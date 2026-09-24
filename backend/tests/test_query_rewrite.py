"""The query rewriting, measured against a real index rather than a Query object.

Every assertion below runs a search over three German documents. That is the
point: a test that only inspects the parsed query answers whether the code built
what it meant to build, never whether the engine finds the document a user is
looking for, and the two came apart in every interesting case while this file was
written. The written out umlaut form is the clearest one. "kuendigung" and
"Kündigung" both survive the German chain on their own, they simply do not reduce
to the same stem, so a query object test would have looked perfectly healthy
while the search stayed empty.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from tantivy import Document, Index, Query

from conftest import FIXTURE_DOCUMENTS
from findling.index.open import open_index
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_EXT,
    FIELD_FILE_ID,
    FIELD_MTIME,
    FIELD_NAME,
    FIELD_PATH,
    FIELD_STORAGE_ID,
    FIELD_TITLE,
)
from findling.query.rewrite import (
    BOOLEAN,
    EXCLUSION,
    FIELD,
    FILETYPE,
    LEGACY_PLAN,
    PHRASE,
    TYPE_GROUPS,
    RewrittenQuery,
    build_query,
    carried_operators,
    carries_one_term,
    extract_filters,
    umlaut_variants,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "constituents_de.txt"
CONSTITUENTS = FIXTURE.read_text(encoding="utf-8").split()

# Three documents, one per file type, so that the type filter has something to
# choose between and the file name differs from the content in every one of them.
CORPUS = (
    (
        1,
        "Kündigung.pdf",
        "Kündigung",
        "pdf",
        "Sehr geehrte Damen und Herren, die Kündigungsfrist für Ihren Vertrag beträgt drei Monate.",
    ),
    (
        2,
        "Vertrag.docx",
        "Vertrag",
        "docx",
        "Der Vertrag wurde gestern unterschrieben und gilt ab dem ersten Januar.",
    ),
    (
        3,
        "Antrag.txt",
        "Antrag",
        "txt",
        "Herr Müller hat die Grundstücksverkehrsgenehmigung beantragt, die Frist läuft im Mai ab.",
    ),
)


class _CountingIndex:
    """Wraps an index and counts how often the engine was asked to parse.

    The claim "an empty search term never reaches the engine" is a statement
    about a call that does not happen, and the only way to observe one of those
    is to count.
    """

    def __init__(self, index: Index) -> None:
        self._index = index
        self.parse_calls = 0

    @property
    def schema(self) -> Any:
        return self._index.schema

    def parse_query_lenient(self, *args: Any, **kwargs: Any) -> Any:
        self.parse_calls += 1
        return self._index.parse_query_lenient(*args, **kwargs)


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Index]:
    directory = tmp_path_factory.mktemp("query-index")
    built = open_index(directory, CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id, name, title, extension, body in CORPUS:
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_unsigned(FIELD_STORAGE_ID, 1)
        document.add_text(FIELD_NAME, name)
        document.add_text(FIELD_TITLE, title)
        document.add_text(FIELD_PATH, f"/Akten/{name}")
        document.add_text(FIELD_EXT, extension)
        document.add_text(FIELD_BODY_DE, body)
        document.add_integer(FIELD_MTIME, 1_700_000_000 + file_id)
        writer.add_document(document)
    writer.commit()
    built.reload()
    yield built
    writer.wait_merging_threads()


def _file_ids(index: Index, query: Query) -> list[int]:
    searcher = index.searcher()
    found: list[int] = []
    for _, address in searcher.search(query, 10).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        assert value is not None
        found.append(int(value))
    return sorted(found)


def _found(index: Index, rewritten: RewrittenQuery) -> list[int]:
    """Run the rewritten query and return the file ids it matches, sorted."""
    assert rewritten.query is not None
    return _file_ids(index, rewritten.query)


def _raw(index: Index, text: str) -> list[int]:
    """Run the text through the engine untouched, for the before and after pairs."""
    parsed, _ = index.parse_query_lenient(text, [FIELD_BODY_DE, FIELD_NAME, FIELD_TITLE])
    return _file_ids(index, parsed)


def test_a_written_umlaut_form_finds_the_umlaut_spelling(index: Index) -> None:
    # The before and after in one test, because the "after" alone would stay
    # green if the German chain started folding umlauts by itself one day.
    assert _raw(index, "kuendigung") == []

    assert _found(index, build_query(index, "kuendigung")) == [1]


def test_the_plan_a_caller_leaves_out_is_the_frozen_legacy_plan(index: Index) -> None:
    # The safe default of 19-RESEARCH pitfall 6, asked instead of assumed. Every
    # other call in this file hands no plan at all, and what keeps those two
    # dozen lines searching the four fields of today is this equality and nothing
    # else. A default read out of the settings or computed from an index would
    # pass every one of them and still change what a bare word means.
    without = _found(index, build_query(index, "kuendigung"))

    assert without == _found(index, build_query(index, "kuendigung", plan=LEGACY_PLAN))
    assert without == [1]


def test_a_term_without_a_written_umlaut_form_is_left_untouched(index: Index) -> None:
    assert umlaut_variants("frist") == ["frist"]

    rewritten = build_query(index, "frist")

    assert rewritten.text == "frist"
    assert _found(index, rewritten) == [1, 3]


def test_the_file_type_prefix_leaves_the_text_and_binds_the_extension(index: Index) -> None:
    rewritten = build_query(index, "type:pdf frist")

    assert rewritten.extensions == ("pdf",)
    assert "type:" not in rewritten.text
    assert rewritten.text == "frist"
    # Document 3 carries the word and is a txt file, so the filter is what
    # removes it rather than the ranking.
    assert _found(index, rewritten) == [1]


def test_the_file_type_prefix_is_cut_before_anything_else_sees_it() -> None:
    # extract_filters runs first and on its own, so a later step cannot put the
    # filter expression back into the full text search.
    residual, extensions = extract_filters("type:PDF drei Monate")

    assert extensions == ("pdf",)
    assert residual == "drei Monate"


def test_title_only_searches_the_file_name_and_not_the_content(index: Index) -> None:
    # "Vertrag" is the name of document 2 and stands in the body of document 1.
    assert _found(index, build_query(index, "vertrag")) == [1, 2]

    assert _found(index, build_query(index, "vertrag", title_only=True)) == [2]


def test_a_phrase_stays_a_phrase(index: Index) -> None:
    assert _found(index, build_query(index, '"drei Monate"')) == [1]

    # Nothing inside the quotation marks is turned into an alternative: a phrase
    # is a phrase, and a rewritten one would no longer be the word order the user
    # asked for.
    quoted = build_query(index, '"Kuendigung"')

    assert quoted.text == '"Kuendigung"'
    assert _found(index, quoted) == []


def test_a_required_term_narrows_and_an_excluded_term_removes(index: Index) -> None:
    assert _found(index, build_query(index, "vertrag +frist")) == [1]
    assert _found(index, build_query(index, "vertrag -frist")) == [2]


def test_an_unbalanced_quotation_mark_yields_errors_instead_of_raising(index: Index) -> None:
    rewritten = build_query(index, 'kaputt "')

    assert rewritten.errors
    assert _found(index, rewritten) == []


def test_regex_syntax_is_not_executed_as_a_regex(index: Index) -> None:
    rewritten = build_query(index, "/.*genehmigung.*/")

    assert rewritten.errors
    assert _found(index, rewritten) == []


def test_an_empty_search_term_never_reaches_the_engine(index: Index) -> None:
    counting = _CountingIndex(index)

    for text in ("", "   ", "type:pdf"):
        rewritten = build_query(cast(Index, counting), text)

        assert rewritten.query is None

    assert counting.parse_calls == 0


def test_no_module_of_the_request_path_uses_the_throwing_parser() -> None:
    # The strict parser raises on a stray quotation mark, and on the request path
    # that is an HTTP 500 for a user who typed one character too many. One module
    # is exempt and named here rather than in a document: index/bench.py is the
    # measurement tool, it is never reached by a request, and its query text is a
    # constant inside the file rather than user input.
    package = Path(__file__).resolve().parents[1] / "src" / "findling"
    users = {
        module.relative_to(package).as_posix()
        for module in package.rglob("*.py")
        if "parse_query(" in module.read_text(encoding="utf-8")
    }

    assert users == {"index/bench.py"}


def test_a_filter_alone_still_reports_the_extension_it_recognised(index: Index) -> None:
    # No term, so no engine call, but the caller still learns what was asked for
    # and does not have to parse the search line a second time.
    rewritten = build_query(index, "type:docx")

    assert rewritten.query is None
    assert rewritten.extensions == ("docx",)


def test_a_query_nested_past_the_bracket_ceiling_never_reaches_the_parser(index: Index) -> None:
    # Security audit C2: parse_query_lenient descends recursively on parentheses,
    # so a deeply nested line overflows the native stack of this process, a crash
    # no except-clause can catch. The depth guard rejects it with an empty query
    # and a message before the parser is entered, so this returns instead of
    # taking the process down.
    from findling.config import SEARCH_QUERY_MAX_DEPTH

    line = "(" * (SEARCH_QUERY_MAX_DEPTH + 5) + "haus" + ")" * (SEARCH_QUERY_MAX_DEPTH + 5)
    rewritten = build_query(index, line)

    assert rewritten.query is None
    assert rewritten.errors
    assert "brackets" in str(rewritten.errors[0])


def test_a_query_at_the_bracket_ceiling_is_still_parsed(index: Index) -> None:
    # The boundary is a legitimate, if unusual, query and must still run.
    from findling.config import SEARCH_QUERY_MAX_DEPTH

    line = "(" * SEARCH_QUERY_MAX_DEPTH + "haus" + ")" * SEARCH_QUERY_MAX_DEPTH
    rewritten = build_query(index, line)

    assert rewritten.query is not None


def test_unbalanced_closers_do_not_inflate_the_depth() -> None:
    # A run of closing brackets without openers is depth zero, not depth n: the
    # guard must not reject a line that never nests.
    from findling.query.rewrite import _max_bracket_depth

    assert _max_bracket_depth(")))))") == 0
    assert _max_bracket_depth("(a) (b) (c)") == 1
    assert _max_bracket_depth("((a))") == 2


# ---------------------------------------------------------------------------
# The operators a search line carries, read on the raw line
# ---------------------------------------------------------------------------
#
# The model sees words and no operators. Somebody who puts quotation marks
# around two words, writes a minus, names a field or asks for a file type has
# asked for precision, and a second list that does not know that request can
# only undercut it. So the request is recognised here, once, in the file where
# the grammar already lives, and the caller acts on it.


def test_quotation_marks_are_a_phrase_query() -> None:
    assert carried_operators('"drei Monate"') == frozenset({PHRASE})


def test_a_leading_minus_is_an_exclusion() -> None:
    assert carried_operators("bescheid -frist") == frozenset({EXCLUSION})


def test_a_minus_inside_a_word_is_not_an_exclusion() -> None:
    # E-Mail, Baden-Baden, Nord-Sued: a hyphen inside a word is spelling and
    # not grammar, and the parser reads it the same way.
    assert carried_operators("E-Mail Baden-Baden") == frozenset()


def test_a_field_prefix_is_a_field_query() -> None:
    assert carried_operators("name:vertrag") == frozenset({FIELD})


def test_a_file_type_prefix_is_a_file_type_filter() -> None:
    # The file type prefix is the one that is cut out of the line rather than
    # parsed, so it gets a mark of its own instead of being read as a field.
    assert carried_operators("type:pdf bescheid") == frozenset({FILETYPE})


def test_a_grammar_word_of_the_parser_is_a_boolean_query() -> None:
    for line in ("haus AND hof", "haus OR hof", "haus NOT hof"):
        assert carried_operators(line) == frozenset({BOOLEAN}), line


def test_an_ordinary_line_carries_no_operator() -> None:
    assert carried_operators("bescheid") == frozenset()
    assert carried_operators("kuendigung im mietverhaeltnis") == frozenset()


def test_the_umlaut_line_carries_no_operator_because_it_is_read_raw() -> None:
    # add_umlaut_variants turns this line into "(kuendigung OR kuendigung)" with
    # the character, so a recognition that ran after the rewriting would report
    # a boolean query for a line the user typed as one word. This case is the
    # proof that the reading happens before any of the three steps.
    assert carried_operators("kuendigung") == frozenset()
    assert BOOLEAN not in carried_operators("Mueller")


def test_the_marks_are_reported_together_when_a_line_carries_several() -> None:
    assert carried_operators('type:pdf "drei Monate" -frist') == frozenset({FILETYPE, PHRASE, EXCLUSION})


def test_the_rewritten_query_carries_the_marks_of_its_raw_line(index: Index) -> None:
    # One caller and one reading: the API layer asks the rewriting what it saw
    # rather than looking at the line a second time with a second opinion.
    assert build_query(index, "bescheid -frist").operators == frozenset({EXCLUSION})
    assert build_query(index, "bescheid").operators == frozenset()


# ---------------------------------------------------------------------------
# One term on the line, counted on the raw line as well
# ---------------------------------------------------------------------------
#
# The measurement of plan 06.1-20 turned the assumption of that plan around: a
# single word does not stand far away from an arbitrary document, it stands
# nearer to one (68 to 77 on the int8 L2 scale) than a paraphrase stands to the
# passage it paraphrases (79.5487). No pair of distances holds both ends, so a
# line that carries exactly one term is answered lexically. For one word the
# compound splitter, the stemmer and the umlaut variant already do what the
# second list was meant to add, and one word gives the model no context at all.


def test_a_line_of_one_word_carries_one_term() -> None:
    assert carries_one_term("Genehmigung") is True
    assert carries_one_term("Mueller") is True


def test_a_line_of_two_words_does_not_carry_one_term() -> None:
    # The counter case of the rule, and the reason it counts terms rather than
    # characters: two words are the shortest line a relation can be read out of,
    # and the paraphrase of the integration run is a longer one of exactly these.
    assert carries_one_term("drei Monate") is False
    assert carries_one_term("wann darf ich den vertrag beenden") is False


def test_the_whitespace_around_a_word_does_not_make_a_second_term() -> None:
    assert carries_one_term("  Genehmigung  ") is True
    assert carries_one_term("Genehmigung\tBescheid") is False


def test_the_file_type_filter_is_not_a_term_of_its_own() -> None:
    # Counted after the filter is cut out, the way the query is built as well,
    # so that a filter cannot silently turn a one word line into a two word one.
    assert carries_one_term("type:pdf Genehmigung") is True


def test_a_line_that_holds_nothing_but_a_filter_carries_no_term() -> None:
    # Nought is not one. Such a line never reaches the engine anyway, and this
    # answer says what was on the line rather than what the caller does with it.
    assert carries_one_term("type:pdf") is False
    assert carries_one_term("   ") is False


def test_the_rewritten_query_carries_whether_its_raw_line_held_one_term(index: Index) -> None:
    # One caller and one reading, exactly as with the operator marks above.
    assert build_query(index, "Genehmigung").one_term is True
    assert build_query(index, "wann darf ich den vertrag beenden").one_term is False


# ---------------------------------------------------------------------------
# The structured filter: type groups and a period
# ---------------------------------------------------------------------------
#
# The same six groups the result page shows, as a parameter rather than as text
# in the search line. Everything below is about the difference between those
# two ways of asking the same question: the text sets a mark that switches the
# vector half off, and the parameter must not.

# The three documents of the fixture carry 1_700_000_000 plus their file id.
MTIME_PDF = 1_700_000_001
MTIME_DOCX = 1_700_000_002
MTIME_TXT = 1_700_000_003


def _filtered(index: Index, rewritten: RewrittenQuery) -> list[int]:
    """Run the filter clause on its own and return the file ids it matches."""
    assert rewritten.filter_query is not None
    return _file_ids(index, rewritten.filter_query)


def test_a_type_group_binds_its_extensions_and_leaves_the_text_alone(index: Index) -> None:
    rewritten = build_query(index, "frist", groups=["pdf"])

    # The line stays what the user typed. A group that ended up in the text
    # would be searched for as a word and would find nothing at all.
    assert rewritten.text == "frist"
    assert rewritten.extensions == ("pdf",)
    # Document 3 carries the word and is a txt file, so the group is what
    # removes it rather than the ranking.
    assert _found(index, rewritten) == [1]


def test_a_group_filter_does_not_set_the_file_type_mark(index: Index) -> None:
    # The case FILT-01 is about. api/search.py reads a non empty set of marks as
    # "this line is answered lexically" and drops the vector half; if this
    # assertion fell, a chip on the result page would switch the semantic search
    # off and a paraphrase under an active filter would find nothing any more.
    rewritten = build_query(index, "frist", groups=["pdf"], since=MTIME_PDF)

    assert rewritten.operators == frozenset()
    assert FILETYPE not in rewritten.operators
    assert rewritten.one_term is True


def test_several_type_groups_are_a_union_and_not_a_narrowing(index: Index) -> None:
    # D-01: every chip switches its group on, and two chips show more rather
    # than less. Document 1 is the pdf, document 2 the docx, and both carry the
    # word.
    assert _found(index, build_query(index, "vertrag", groups=["pdf"])) == [1]

    assert _found(index, build_query(index, "vertrag", groups=["pdf", "documents"])) == [1, 2]


def test_a_group_the_table_does_not_know_is_no_filter_and_no_error(index: Index) -> None:
    # It reaches the rewriting out of an address, and an address with a word
    # nobody knows means "no filter", the way every other value of that address
    # is read.
    rewritten = build_query(index, "frist", groups=["xyz"])

    assert rewritten.extensions == ()
    assert rewritten.filter_query is None
    assert _found(index, rewritten) == _found(index, build_query(index, "frist"))


def test_a_group_written_in_capitals_still_matches(index: Index) -> None:
    # extension_of writes the extension in lower case and the raw tokeniser
    # normalises nothing, so a group name that is not folded would produce a
    # term that matches not one document.
    assert _found(index, build_query(index, "frist", groups=["PDF"])) == [1]


def test_the_text_syntax_and_the_group_parameter_are_united(index: Index) -> None:
    # "type:pdf" plus the chip for documents finds both and not neither. As an
    # intersection the answer would be guaranteed empty, and the page has no way
    # of explaining an empty list that is nobody's mistake.
    rewritten = build_query(index, "type:pdf vertrag", groups=["documents"])

    assert rewritten.extensions == ("pdf", "docx", "odt", "rtf")
    assert _found(index, rewritten) == [1, 2]


def test_a_type_group_of_the_text_syntax_means_the_same_as_the_chip(index: Index) -> None:
    # One vocabulary and not two: the word behind the prefix is resolved through
    # the same table the parameter is resolved through.
    assert build_query(index, "frist type:pdf").extensions == build_query(index, "frist", groups=["pdf"]).extensions


def test_the_lower_bound_of_the_period_is_inclusive(index: Index) -> None:
    # Both documents carry the word; the period is what removes the older one,
    # and the younger one sits exactly on the bound.
    assert _found(index, build_query(index, "frist")) == [1, 3]

    assert _found(index, build_query(index, "frist", since=MTIME_TXT)) == [3]


def test_the_upper_bound_of_the_period_is_inclusive(index: Index) -> None:
    assert _found(index, build_query(index, "frist", until=MTIME_PDF)) == [1]


def test_both_bounds_together_are_the_window_between_them(index: Index) -> None:
    rewritten = build_query(index, "vertrag", since=MTIME_DOCX, until=MTIME_DOCX)

    assert _found(index, rewritten) == [2]


def test_a_period_that_lies_in_the_future_is_empty_and_not_an_error(index: Index) -> None:
    # no_data, and at the same time the guard against the one silent failure of
    # this feature: the range runs over the fast column, and with
    # use_inverted_index set to True tantivy answers every period with an empty
    # list instead of an error. This case would then be the only green one of
    # the four above, which is the pattern to look for.
    rewritten = build_query(index, "frist", since=2_000_000_000)

    assert rewritten.query is not None
    assert rewritten.errors == []
    assert _found(index, rewritten) == []


def test_a_lower_bound_above_the_upper_bound_is_empty_and_not_an_error(index: Index) -> None:
    # A hand edited address may carry since above until: each edge passes the
    # wire bounds on its own, so the inverted window reaches the engine. The
    # range over the fast column answers it with an empty list, and the page
    # reads that as its filter empty state instead of an error block.
    rewritten = build_query(index, "frist", since=MTIME_TXT, until=MTIME_PDF)

    assert rewritten.query is not None
    assert rewritten.errors == []
    assert _found(index, rewritten) == []


def test_all_six_type_groups_together_are_no_narrowing(index: Index) -> None:
    # An address may switch every chip on at once, which is exactly
    # SEARCH_TYPE_GROUPS_MAX names. Switching everything on means nothing is
    # switched off, so the union has to answer what the unfiltered search
    # answers, and the whole vocabulary is read from the one table it lives in.
    rewritten = build_query(index, "frist", groups=list(TYPE_GROUPS))

    assert _found(index, rewritten) == _found(index, build_query(index, "frist"))


def test_without_a_group_and_without_a_bound_there_is_no_filter_clause(index: Index) -> None:
    rewritten = build_query(index, "frist", groups=[], since=None, until=None)

    assert rewritten.filter_query is None


def test_the_filter_clause_carries_the_expected_set_on_its_own(index: Index) -> None:
    # The clause is handed out separately because the semantic half knows
    # neither an extension nor a time stamp: its hits never pass through the
    # parser, and only this clause can cut them to the requested type. So it has
    # to hold without the full text part as well.
    assert _filtered(index, build_query(index, "frist", groups=["pdf"])) == [1]
    assert _filtered(index, build_query(index, "frist", since=MTIME_TXT)) == [3]
    assert _filtered(index, build_query(index, "frist", groups=["documents"], since=MTIME_DOCX)) == [2]


# -- the same holdings under both schema generations -------------------------
#
# Phase 18 raises the schema from nine fields to thirteen, and between the day
# that ships and the day a given instance has rebuilt, the query builder in this
# module runs against indexes of both generations. The failure it has to survive
# is not a wrong ranking, it is an exception: measured on tantivy 0.26.2,
# ``parse_query_lenient`` answers a field name the schema does not know with
# ``ValueError``, that exception leaves ``build_query``, and the route answers
# without a lexical half for as long as the old index is on disk.
#
# The index these two cases run against is built by ``conftest.build_schema_1``
# and not by a ``SchemaBuilder`` written out here, and the difference matters
# more than it looks. A schema assembled in this file would be a schema the test
# author believes was shipped; it would drift from the real one on any field
# whose stored or indexed flag was remembered wrong, and the proof would then be
# about an index that never existed on any installation. The fixture copies the
# nine field builder from the last commit before plan 18-01 and freezes it, which
# is the only version of it anybody can still be running.
#
# The set inclusions that say the same thing about names rather than about an
# index live in ``tests/test_schema_generations.py``, together with the syntax
# tree guard that keeps the field list inside both generations.


def _hits_of(index: Index, text: str) -> list[int]:
    """Run the whole query builder against ``index`` and return the ids it found.

    The assertions inside are the ones that would otherwise need a
    ``pytest.raises`` around the call and a second case for the degraded answer.
    An exception fails the test where it happens, an empty ``errors`` list says
    the parser did not quietly swallow the field name, and a query that is not
    None says the builder did not take the "nothing to search for" exit.
    """
    rewritten = build_query(index, text)

    assert rewritten.errors == []
    assert rewritten.query is not None

    searcher = index.searcher()
    found: list[int] = []
    for _, address in searcher.search(rewritten.query, FIXTURE_DOCUMENTS * 2).hits:
        value = searcher.doc(address).get_first(FIELD_FILE_ID)
        assert value is not None
        found.append(int(value))
    return sorted(found)


ALL_DOCUMENTS = list(range(1, FIXTURE_DOCUMENTS + 1))

# Seven search lines and the ids each of them has to find, whichever schema the
# index was built with. Written out rather than compared between the two runs
# alone: two empty lists are equal, and four of these lines find every document
# there is, so an expected list is what keeps the comparison from being true for
# a reason that has nothing to do with the schema.
#
# The lines take different routes into the engine on purpose. "vertrag" is a
# plain body word, "kuendigungsfrist" arrives as an umlaut variant and as a
# compound, "akte" stands in the file name and in the title rather than in the
# body, the phrase goes past the token rewriting untouched and needs positions
# in the posting list, "absaetze" separates the documents by their tail, the
# bare number reaches exactly one of them, and the last line adds the extension
# filter, which is a clause over a separate field rather than a term.
SEARCHES = (
    ("vertrag", ALL_DOCUMENTS),
    ("kuendigungsfrist", ALL_DOCUMENTS),
    ("akte", ALL_DOCUMENTS),
    ('"drei Monate"', ALL_DOCUMENTS),
    ("absaetze", [file_id for file_id in ALL_DOCUMENTS if file_id % 3]),
    ("7", [7]),
    ("type:pdf vertrag", [file_id for file_id in ALL_DOCUMENTS if file_id % 2]),
)


def test_the_query_builder_answers_an_index_of_the_old_schema(schema_1_index: Index) -> None:
    # The case the whole section exists for. No pytest.raises anywhere: an
    # exception out of build_query is a failure of this test, not its subject,
    # and a degraded answer is caught by the empty errors list inside _hits_of.
    for text, expected in SEARCHES:
        assert _hits_of(schema_1_index, text) == expected, text


def test_both_schema_generations_answer_the_same_search_the_same(schema_1_index: Index, schema_2_index: Index) -> None:
    # Success criterion 1 of the phase on the level of a test: the same holdings
    # answer the same under both schemas, hit for hit and not merely in number.
    for text, expected in SEARCHES:
        assert _hits_of(schema_1_index, text) == expected == _hits_of(schema_2_index, text), text
