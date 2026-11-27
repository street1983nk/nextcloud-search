"""The Chinese chain on token level (issue #53).

What the chain does to text, held as tokens and nothing else: one token per Han
character, a run of other letters and digits as one word, lowercase, the fold
of full width forms, and the byte limit that never reaches a Han character.
How those tokens become a word search is the subject of
``tests/test_chinese_search.py``.

Full width characters are built from their code points and never written as
characters: the ruff rules of this project (RUF001) read a full width letter,
digit or comma in a string as a look alike of its ASCII twin, and a code point
is what a reader can tell apart from that twin.
"""

from __future__ import annotations

import pytest

from findling.index.analyzer import MAX_TOKEN_CHARS, ZH_PATTERN, chinese_analyzer

# Full width ABC123 and the full width comma, ideographic space and full stop.
FULL_WIDTH_ABC123 = "".join(map(chr, (0xFF21, 0xFF22, 0xFF23, 0xFF11, 0xFF12, 0xFF13)))
FULL_WIDTH_COMMA = chr(0xFF0C)
IDEOGRAPHIC_SPACE = chr(0x3000)
IDEOGRAPHIC_FULL_STOP = chr(0x3002)


def _tokens(text: str) -> list[str]:
    return chinese_analyzer().analyze(text)


def test_one_token_per_han_character() -> None:
    assert _tokens("今天台北的天氣很好") == ["今", "天", "台", "北", "的", "天", "氣", "很", "好"]


def test_punctuation_and_spaces_produce_no_token() -> None:
    text = f"天氣{FULL_WIDTH_COMMA}很好{IDEOGRAPHIC_FULL_STOP} 會議{IDEOGRAPHIC_SPACE}記錄"

    assert _tokens(text) == ["天", "氣", "很", "好", "會", "議", "記", "錄"]


def test_latin_words_and_digits_stay_words_between_han_characters() -> None:
    # The Han and Latin variant of ZH_PATTERN: Nextcloud and 33 are one term
    # each, the Han characters around them one term per character.
    assert _tokens("今天 Nextcloud 33 會議記錄") == ["今", "天", "nextcloud", "33", "會", "議", "記", "錄"]


def test_a_number_written_against_a_han_character_is_its_own_token() -> None:
    # The case that decides between Han and Latin and Han only: 2026年 has to
    # keep its number, or the search term would analyse to 年 alone.
    assert _tokens("2026年3月") == ["2026", "年", "3", "月"]
    assert _tokens("Q3財報") == ["q3", "財", "報"]


def test_latin_is_lowercased() -> None:
    assert _tokens("NEXTCLOUD Findling") == ["nextcloud", "findling"]


def test_full_width_letters_and_digits_are_folded_to_ascii() -> None:
    # Measured on 2026-11-15: without ascii_fold the six characters stay one
    # full width token that no half width search term can reach.
    assert _tokens(FULL_WIDTH_ABC123) == ["abc123"]
    assert _tokens(f"{FULL_WIDTH_ABC123}全形") == ["abc123", "全", "形"]


def test_accented_latin_is_folded_like_in_the_other_folding_chains() -> None:
    assert _tokens("Café Müller 臺灣") == ["cafe", "muller", "臺", "灣"]


def test_a_run_of_thirty_han_characters_stays_thirty_tokens() -> None:
    """The run the German chain drops, kept here character for character.

    Thirty Han characters are 90 bytes in UTF-8. Through Tokenizer.simple they
    are one token, and remove_long(48) drops it, so the whole sentence is gone.
    Here every character is three bytes on its own and far below the limit.
    """
    run = "全文檢索功能在中文文件上表現如何呢我很好奇想知道答案是什麼呀"
    assert len(run) == 30
    assert len(run.encode("utf-8")) > MAX_TOKEN_CHARS

    assert _tokens(run) == list(run)


def test_a_han_character_outside_the_basic_plane_is_one_token() -> None:
    # U+20000 and U+2A6A5, extension B: four bytes each, one token each.
    assert _tokens("\U00020000\U0002a6a5") == ["\U00020000", "\U0002a6a5"]


def test_a_latin_run_above_the_byte_limit_is_dropped_as_in_every_chain() -> None:
    long_word = "a" * (MAX_TOKEN_CHARS + 1)

    assert _tokens(f"天 {long_word} 氣") == ["天", "氣"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Kana is not Han, so a Kana run stays one word: Japanese is not served.
        ("日本語のテキスト", ["日", "本", "語", "のテキスト"]),
        # Hangul is not Han either: Korean stays whole words, as with spaces.
        ("한국어 텍스트", ["한국어", "텍스트"]),
    ],
)
def test_japanese_and_korean_are_documented_limits(text: str, expected: list[str]) -> None:
    assert _tokens(text) == expected


def test_the_pattern_is_the_han_and_latin_variant() -> None:
    # The one line the decision between the two variants turns on. A change of
    # it is a change of the tokenisation of body_zh and has to be measured.
    assert ZH_PATTERN == r"\p{Han}|[\p{L}\p{N}&&[^\p{Han}]]+"
