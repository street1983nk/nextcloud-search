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
from findling.query.rewrite import RewrittenQuery, build_query, extract_filters, umlaut_variants

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
    assert "brackets" in rewritten.errors[0]


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
