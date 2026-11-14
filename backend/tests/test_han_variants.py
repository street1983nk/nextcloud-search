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
from findling.index.open import open_index
from findling.index.schema import FIELD_BODY_DE, FIELD_BODY_ZH, FIELD_FILE_ID, FIELD_NAME, FIELD_TITLE
from findling.query.rewrite import BODY_BOOST, FieldPlan, add_umlaut_variants, build_query, han_variants

FULL_STOP = chr(0x3002)

CORPUS: Mapping[int, str] = {
    # 臺灣 in its traditional shape.
    4: f"臺灣的天氣很好{FULL_STOP}",
    # 台北市 in its common shape.
    5: f"台北市政府公告{FULL_STOP}",
}

PLAN_DE_ZH = FieldPlan(
    fields=(FIELD_BODY_DE, FIELD_BODY_ZH, FIELD_NAME, FIELD_TITLE),
    boosts=MappingProxyType(
        {FIELD_BODY_DE: BODY_BOOST["de"], FIELD_BODY_ZH: BODY_BOOST["zh"], FIELD_NAME: 3.0, FIELD_TITLE: 2.0}
    ),
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


def _found(index: Index, text: str) -> set[int]:
    rewritten = build_query(index, text, plan=PLAN_DE_ZH)
    assert rewritten.errors == []
    if rewritten.query is None:
        return set()
    searcher = index.searcher()
    hits = searcher.search(rewritten.query, limit=10).hits
    return {int(searcher.doc(address).to_dict()[FIELD_FILE_ID][0]) for _score, address in hits}  # pyright: ignore[reportArgumentType]


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


def test_a_term_inside_parentheses_is_left_as_typed(index: Index) -> None:
    # The documented limit, shared with the umlaut variant: the rewrite looks at
    # plain tokens, and a token with a parenthesis attached is not one. So the
    # common shape inside a group does not reach the traditional one.
    assert add_umlaut_variants("(台灣)") == "(台灣)"
    assert add_umlaut_variants("(台灣 OR 日本)") == "(台灣 OR 日本)"
    assert _found(index, "(台灣)") == set()
    assert _found(index, "(臺灣)") == {4}
