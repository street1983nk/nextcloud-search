"""Chinese words found through body_zh, on a real index and through the real query path.

The chain cuts one token per Han character (``tests/test_chinese_analyzer.py``),
and what turns that into a word search is the query parser: a search term that
analyses into several tokens becomes a phrase query with slop 0. This file holds
that on a real directory of the running schema, through
:func:`findling.query.rewrite.build_query`, so that the parser, the field plan
and the variant expansion are the ones the search path uses.

Four parts: the phrase behaviour of issue #53 (E2 of the research notes), the
field plan that names body_zh only where the marks allow it, the snippet a
Chinese only hit gets today, held so that the measurement report starts from a
known state, and the documented limits of the chain.

Full width punctuation is built from code points, for the reason given in
``tests/test_chinese_analyzer.py``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from types import MappingProxyType

import pytest
from tantivy import DocAddress, Document, Index

from conftest import CONSTITUENTS, open_schema_3_index
from findling.api.resources import field_plan_for
from findling.index.open import LANGUAGES_MARK, SCHEMA_MARK, open_index
from findling.index.schema import (
    FIELD_BODY_DE,
    FIELD_BODY_EN,
    FIELD_BODY_ZH,
    FIELD_FILE_ID,
    FIELD_NAME,
    FIELD_TITLE,
)
from findling.index.search import SnippetText, snippets_for
from findling.query.rewrite import BODY_BOOST, FieldPlan, build_query
from findling.store.repo import Store, open_store

COMMA = chr(0xFF0C)
COLON = chr(0xFF1A)
FULL_STOP = chr(0x3002)

OWNER = "owner"

# The fixture of E2 and E4 of the research notes, one document per line of
# argument. The comments say which case each one exists for.
CORPUS: Mapping[int, str] = {
    # 天氣 as a word, inside a longer run between two punctuation marks.
    1: f"今天台北的天氣很好{COMMA}我們去開會{FULL_STOP}",
    # 天 and 氣 both present, never side by side.
    2: f"氣象報告{COLON}台中天晴{FULL_STOP}",
    # 會議 as a word.
    3: f"會議記錄{COLON}下週一上午十點{FULL_STOP}",
    # 臺灣 in its traditional shape.
    4: f"臺灣的天氣很好{FULL_STOP}",
    # 台北市 in its common shape.
    5: f"台北市政府公告{FULL_STOP}",
    # A year against a Han character, and the same character without the year.
    6: f"2026年度預算{FULL_STOP}",
    7: f"年度報告{FULL_STOP}",
    # English inside Chinese.
    8: f"Nextcloud 的全文檢索{FULL_STOP}",
}

PLAN_DE_ZH = FieldPlan(
    fields=(FIELD_BODY_DE, FIELD_BODY_ZH, FIELD_NAME, FIELD_TITLE),
    boosts=MappingProxyType(
        {FIELD_BODY_DE: BODY_BOOST["de"], FIELD_BODY_ZH: BODY_BOOST["zh"], FIELD_NAME: 3.0, FIELD_TITLE: 2.0}
    ),
    title_only=(FIELD_NAME,),
)


def _write(index: Index, bodies: Mapping[int, str], fields: tuple[str, ...]) -> None:
    writer = index.writer(heap_size=15_000_000, num_threads=1)
    for file_id, body in bodies.items():
        document = Document()
        document.add_unsigned(FIELD_FILE_ID, file_id)
        document.add_text(FIELD_NAME, f"Akte-{file_id}.txt")
        document.add_text(FIELD_TITLE, f"Akte {file_id}")
        for field in fields:
            document.add_text(field, body)
        writer.add_document(document)
    writer.commit()
    writer.wait_merging_threads()
    index.reload()


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> Index:
    built = open_index(tmp_path_factory.mktemp("zh-index"), CONSTITUENTS)
    # body_de stored, as the writer does it whatever the language set says, and
    # body_zh beside it, as the writer does it once zh is switched on.
    _write(built, CORPUS, (FIELD_BODY_DE, FIELD_BODY_ZH))
    return built


def _ids(index: Index, hits: Sequence[tuple[float, DocAddress]]) -> list[int]:
    searcher = index.searcher()
    return [int(searcher.doc(address).to_dict()[FIELD_FILE_ID][0]) for _score, address in hits]  # pyright: ignore[reportArgumentType]


def _found(index: Index, text: str, plan: FieldPlan = PLAN_DE_ZH) -> set[int]:
    rewritten = build_query(index, text, plan=plan)
    assert rewritten.errors == []
    if rewritten.query is None:
        return set()
    return set(_ids(index, index.searcher().search(rewritten.query, limit=20).hits))


def _found_in_body_zh(index: Index, text: str) -> set[int]:
    return set(_ids(index, index.searcher().search(index.parse_query(text, [FIELD_BODY_ZH]), limit=20).hits))


# -- 1. the phrase behaviour ---------------------------------------------------


def test_a_two_character_word_is_found_as_a_phrase_and_not_as_two_characters(index: Index) -> None:
    assert _found_in_body_zh(index, "天氣") == {1, 4}
    assert 2 not in _found(index, "天氣")


def test_a_word_is_not_found_inside_another_order_of_its_characters(index: Index) -> None:
    # 會議 in 會議記錄, not the 會 of 開會 in document 1.
    assert _found(index, "會議") == {3}


def test_the_german_chain_alone_does_not_find_the_word(index: Index) -> None:
    # The counter probe: body_de keeps the whole run as one token, so the word
    # inside it is reachable only through body_zh.
    body_de_only = FieldPlan(
        fields=(FIELD_BODY_DE,), boosts=MappingProxyType({FIELD_BODY_DE: 1.0}), title_only=(FIELD_NAME,)
    )
    assert _found(index, "天氣", body_de_only) == set()


def test_two_words_with_a_space_require_both_under_conjunction(index: Index) -> None:
    assert _found(index, "台北 天氣") == {1}
    assert _found(index, "天氣 很好") == {1, 4}


def test_a_quoted_phrase_is_found_as_written(index: Index) -> None:
    assert _found(index, '"台北的天氣"') == {1}
    assert _found(index, '"台北天氣"') == set()


def test_a_year_against_a_han_character_keeps_its_number(index: Index) -> None:
    # 2026年 is the phrase 2026 followed by 年, so the document that carries 年
    # without the year is not a hit. With a Han only pattern it would be.
    assert _found(index, "2026年") == {6}


def test_a_latin_word_inside_chinese_text_is_found_through_body_zh(index: Index) -> None:
    assert _found_in_body_zh(index, "nextcloud") == {8}
    assert _found_in_body_zh(index, "全文檢索") == {8}


# -- 2. the field plan ---------------------------------------------------------


def test_the_plan_names_body_zh_with_its_boost_when_zh_is_switched_on(index: Index) -> None:
    plan = field_plan_for({SCHEMA_MARK: "4", LANGUAGES_MARK: "de,en,zh"}, index)

    assert plan.fields[:3] == (FIELD_BODY_DE, FIELD_BODY_EN, FIELD_BODY_ZH)
    assert plan.boosts[FIELD_BODY_ZH] == 0.6


def test_the_plan_leaves_body_zh_out_while_zh_is_off(index: Index) -> None:
    plan = field_plan_for({SCHEMA_MARK: "4", LANGUAGES_MARK: "de,en"}, index)

    assert FIELD_BODY_ZH not in plan.fields
    assert FIELD_BODY_ZH not in plan.boosts


def test_a_schema_3_directory_drops_body_zh_from_a_plan_that_names_it(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # A state the marks cannot reach in practice, because switching zh on is a
    # rebuild; the probe is what holds the search path if they ever do.
    stock = open_schema_3_index(tmp_path / "index")

    with caplog.at_level(logging.WARNING, logger="findling"):
        plan = field_plan_for({SCHEMA_MARK: "3", LANGUAGES_MARK: "de,zh"}, stock)

    assert FIELD_BODY_ZH not in plan.fields
    assert FIELD_BODY_ZH not in plan.boosts
    assert FIELD_BODY_DE in plan.fields
    assert any(FIELD_BODY_ZH in record.getMessage() for record in caplog.records)


# -- 3. the snippet of a Chinese only hit, as it is today ------------------------


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    for file_id in CORPUS:
        opened.replace_acl(file_id, [OWNER])
    yield opened
    opened.close()


def test_a_chinese_only_hit_gets_the_empty_excerpt_today(index: Index, store: Store) -> None:
    """The starting point of the snippet decision of issue #53, measured.

    The generator reads body_de with the German chain, which knows 天氣 only as
    part of the run 今天台北的天氣很好, so it finds no match in the document and
    the excerpt is empty: no text, no highlight, and above all no text of
    another document. The hit itself stays a hit, and the PHP side shows the
    path instead. Which of the three snippet options replaces this is decided
    by the measurement report.
    """
    rewritten = build_query(index, "開會", plan=PLAN_DE_ZH)
    assert rewritten.query is not None

    assert snippets_for(index, store, OWNER, rewritten.query, [1]) == [SnippetText(file_id=1, text="", highlights=[])]


def test_a_whole_run_equal_to_the_term_is_highlighted_through_body_de(tmp_path: Path, store: Store) -> None:
    # The one case the German chain reaches: a run that is the search term and
    # nothing else, between two punctuation marks.
    single = open_index(tmp_path / "single", CONSTITUENTS)
    _write(single, {1: f"今天{COMMA}天氣{COMMA}很好"}, (FIELD_BODY_DE, FIELD_BODY_ZH))
    rewritten = build_query(single, "天氣", plan=PLAN_DE_ZH)
    assert rewritten.query is not None

    excerpt = snippets_for(single, store, OWNER, rewritten.query, [1])[0]

    assert excerpt.text[excerpt.highlights[0][0] : excerpt.highlights[0][1]] == "天氣"


# -- 4. the documented limits, held so that docs/language-analyzers.md stays true --

LIMITS: Mapping[int, str] = {
    1: "今天天气很好",
    2: "今日本店公休",
    3: "台北天氣預報",
    4: "台北的天氣預報",
}


@pytest.fixture(scope="module")
def limits_index(tmp_path_factory: pytest.TempPathFactory) -> Index:
    built = open_index(tmp_path_factory.mktemp("zh-limits"), CONSTITUENTS)
    _write(built, LIMITS, (FIELD_BODY_DE, FIELD_BODY_ZH))
    return built


def test_traditional_and_simplified_are_not_converted(limits_index: Index) -> None:
    # 氣 against 气: the Simplified document is found by its own spelling only.
    assert _found(limits_index, "天氣") == {3, 4}
    assert _found(limits_index, "天气") == {1}


def test_a_two_character_search_can_match_across_a_word_boundary(limits_index: Index) -> None:
    # 今日 and 本店 are the words; 日本 stands across them all the same.
    assert _found(limits_index, "日本") == {2}


def test_an_unspaced_term_is_one_exact_phrase(limits_index: Index) -> None:
    assert _found(limits_index, "台北天氣") == {3}
    assert _found(limits_index, "台北 天氣") == {3, 4}
