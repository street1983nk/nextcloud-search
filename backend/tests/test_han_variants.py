"""The two shapes of 臺 and 台, answered on the query side (issue #53).

Taiwanese text writes 臺灣 and 台灣, 臺北 and 台北 for the same names, and the
Chinese chain indexes whichever shape a document carries. The query side adds
the other one, the way it adds the umlaut to a written out umlaut: no index
space, no version mark, and a changed table needs no rebuild (E4 of the research
notes). This file holds the table, the rewrite of a search line, and the effect
on a real index of the running schema through the real query path.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

import pytest
from tantivy import Document, Index

from conftest import CONSTITUENTS
from findling.index.analyzer import MAX_NAME_CHARS, MAX_TOKEN_CHARS
from findling.index.open import open_index
from findling.index.schema import FIELD_BODY_DE, FIELD_BODY_ZH, FIELD_FILE_ID, FIELD_NAME, FIELD_TITLE
from findling.query.rewrite import (
    BODY_BOOST,
    FieldPlan,
    RewrittenQuery,
    add_umlaut_variants,
    build_query,
    han_variants,
)

FULL_STOP = chr(0x3002)

# The name of a regulation without its first character, which is 臺 or 台. With
# it the term is 25 Han characters and 75 bytes: more than the name chain keeps
# and more than every body chain but the Chinese one keeps.
LONG_NAME = "中市政府所屬各機關公務人員出國報告審核及管理要點"

CORPUS: Mapping[int, str] = {
    # 臺灣 in its traditional shape.
    4: f"臺灣的天氣很好{FULL_STOP}",
    # 台北市 in its common shape.
    5: f"台北市政府公告{FULL_STOP}",
    # A long name in its traditional shape.
    6: f"臺{LONG_NAME}{FULL_STOP}",
}

PLAN_DE_ZH = FieldPlan(
    fields=(FIELD_BODY_DE, FIELD_BODY_ZH, FIELD_NAME, FIELD_TITLE),
    boosts=MappingProxyType(
        {FIELD_BODY_DE: BODY_BOOST["de"], FIELD_BODY_ZH: BODY_BOOST["zh"], FIELD_NAME: 3.0, FIELD_TITLE: 2.0}
    ),
    title_only=(FIELD_NAME,),
)

# The plan of a directory without zh: no chain in it cuts a Han run apart.
PLAN_DE = FieldPlan(
    fields=(FIELD_BODY_DE, FIELD_NAME, FIELD_TITLE),
    boosts=MappingProxyType({FIELD_BODY_DE: BODY_BOOST["de"], FIELD_NAME: 3.0, FIELD_TITLE: 2.0}),
    title_only=(FIELD_NAME,),
)


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Index:
    built = open_index(tmp_path_factory.mktemp("zh-variants"), CONSTITUENTS)
    writer = built.writer(heap_size=15_000_000, num_threads=1)
    for file_id, body in CORPUS.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.txt")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        document.add_text(FIELD_BODY_DE, body)
        document.add_text(FIELD_BODY_ZH, body)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    built.reload()
    return built


def _hits(index: Index, rewritten: RewrittenQuery) -> set[int]:
    if rewritten.query is None:
        return set()
    searcher = index.searcher()
    hits = searcher.search(rewritten.query, limit=10).hits
    return {int(searcher.doc(address).to_dict()[FIELD_FILE_ID][0]) for _score, address in hits}  # pyright: ignore[reportArgumentType]


def _found(index: Index, text: str) -> set[int]:
    rewritten = build_query(index, text, plan=PLAN_DE_ZH)
    assert rewritten.errors == []
    return _hits(index, rewritten)


def test_the_variant_table_expands_both_directions() -> None:
    assert han_variants("台灣") == ["台灣", "臺灣"]
    assert han_variants("臺北市") == ["臺北市", "台北市"]
    assert han_variants("天氣") == ["天氣"]
    assert han_variants("kuendigung") == ["kuendigung"]


def test_a_mixed_term_gets_its_two_uniform_spellings_and_no_more() -> None:
    # The documented gap: 台灣臺北 in a document is not reached through this term.
    assert han_variants("臺灣台北") == ["臺灣台北", "台灣台北", "臺灣臺北"]


@pytest.mark.parametrize(
    ("line", "rewritten"),
    [
        ("台灣", "(台灣 OR 臺灣)"),
        ("臺北市 天氣", "(臺北市 OR 台北市) 天氣"),
        ("+台灣 -臺北", "+(台灣 OR 臺灣) -(臺北 OR 台北)"),
        ("body_zh:台灣", "body_zh:(台灣 OR 臺灣)"),
        ('"台灣" 台灣', '"台灣" (台灣 OR 臺灣)'),
        ("台灣 OR 日本", "(台灣 OR 臺灣) OR 日本"),
        ("kuendigung", "(kuendigung OR kündigung)"),
    ],
)
def test_the_rewrite_keeps_operators_fields_and_quotes(line: str, rewritten: str) -> None:
    assert add_umlaut_variants(line) == rewritten


def test_the_common_shape_finds_the_traditional_one(index: Index) -> None:
    assert _found(index, "台灣") == {4}


def test_the_traditional_shape_finds_the_common_one(index: Index) -> None:
    assert _found(index, "臺北市") == {5}


def test_a_quoted_shape_is_left_as_typed(index: Index) -> None:
    # Quoted segments are not rewritten, the same rule as for the umlaut.
    assert _found(index, '"台灣"') == set()
    assert _found(index, '"臺灣"') == {4}


def test_a_term_with_a_bracket_attached_is_left_as_typed(index: Index) -> None:
    # The documented limit, shared with the umlaut variant: the rewrite looks at
    # plain tokens, and a token with a bracket attached is not one. So the common
    # shape at the edge of a group does not reach the traditional one.
    assert add_umlaut_variants("(台灣)") == "(台灣)"
    assert add_umlaut_variants("(台灣 OR 日本)") == "(台灣 OR 日本)"
    assert add_umlaut_variants("(a 台灣)") == "(a 台灣)"
    assert _found(index, "(台灣)") == set()
    assert _found(index, "(臺灣)") == {4}
    assert _found(index, "(台灣 OR 日本)") == set()


def test_a_term_between_spaces_inside_a_group_is_rewritten(index: Index) -> None:
    # The other side of the limit: what counts is the token and not the group
    # around it, so a term with spaces on both sides is rewritten inside brackets
    # as well. The document writes 臺灣, so only the rewrite reaches it.
    assert add_umlaut_variants("(a 台灣 b)") == "(a (台灣 OR 臺灣) b)"
    assert add_umlaut_variants("(a kuendigung b)") == "(a (kuendigung OR kündigung) b)"
    assert _found(index, "(日本 OR 台灣 OR 東京)") == {4}
    assert _found(index, "(日本 OR 東京)") == set()


def test_the_long_name_is_longer_than_every_chain_but_the_chinese_one_keeps() -> None:
    assert len(f"臺{LONG_NAME}".encode()) >= MAX_NAME_CHARS > MAX_TOKEN_CHARS


@pytest.mark.parametrize("shape", ["台", "臺"])
def test_a_long_term_keeps_both_shapes_where_the_chinese_chain_is_asked(index: Index, shape: str) -> None:
    assert _found(index, shape + LONG_NAME) == {6}


@pytest.mark.parametrize("line", [f"台{LONG_NAME}", f"臺{LONG_NAME}", f"+臺{LONG_NAME}"])
def test_a_long_term_finds_nothing_where_no_chain_keeps_it(index: Index, line: str) -> None:
    # Without zh no chain keeps a term of 75 bytes, so both branches of the
    # group are empty, and the parser repairs a group of nothing into every
    # document. The line is then sent the way it was before the variants: one
    # term that finds nothing.
    rewritten = build_query(index, line, plan=PLAN_DE)

    assert rewritten.text == line
    assert rewritten.errors == []
    assert _hits(index, rewritten) == set()


@pytest.mark.parametrize("shape", ["台", "臺"])
def test_a_long_term_finds_nothing_under_the_file_name_filter(index: Index, shape: str) -> None:
    # With zh as well: the filter asks the name chain alone, which drops it.
    rewritten = build_query(index, shape + LONG_NAME, plan=PLAN_DE_ZH, title_only=True)

    assert rewritten.text == shape + LONG_NAME
    assert _hits(index, rewritten) == set()


@pytest.mark.parametrize(
    "line",
    [
        f"name:台{LONG_NAME}",
        # Sixteen Han characters are 48 bytes, which the German chain drops.
        f"body_de:台{LONG_NAME[:15]}",
        # A field the schema does not know keeps nothing of any length.
        "notiz:台灣",
    ],
)
def test_a_term_its_field_does_not_keep_finds_nothing(index: Index, line: str) -> None:
    rewritten = build_query(index, line, plan=PLAN_DE_ZH)

    assert rewritten.text == line
    assert _hits(index, rewritten) == set()


def test_an_exclusion_somebody_typed_keeps_both_shapes(index: Index) -> None:
    # The parser repairs this line as well, and here the repair is the answer
    # that was asked for: every document without the name, in either shape.
    rewritten = build_query(index, "-台灣", plan=PLAN_DE_ZH)

    assert rewritten.text == "-(台灣 OR 臺灣)"
    assert _hits(index, rewritten) == {5, 6}


def test_the_line_without_han_variants_is_the_line_of_the_umlaut_alone() -> None:
    assert add_umlaut_variants("台灣 kuendigung", han=False) == "台灣 (kuendigung OR kündigung)"
    assert add_umlaut_variants("台灣 kuendigung") == "(台灣 OR 臺灣) (kuendigung OR kündigung)"
