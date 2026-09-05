"""The spans are characters, the cap is applied before the split, and both are nailed down.

Two failures of this module would be invisible in production and are the reason
this file exists.

The first is the unit. ``semantic-text-splitter`` works on a Rust ``str`` and the
stored ``body_de`` is a Python ``str``; the offsets that travel to
``store/vectors.sql`` are characters. This repository has measured the byte
against character confusion once already (``index/search.py``: the engine reports
(35, 51) where the character range is (35, 50)), and an offset in the wrong unit
cuts every semantic snippet in the wrong place, silently and only in documents
that carry non ascii text, which in German is all of them. So the tests below cut
with ``text[char_start:char_end]`` and compare with the chunk itself, on a German
sentence with umlauts and on a French one with accents and a cedilla, because
D-03 makes French a requirement and the trap is the same one there.

The second is the order. The cap of D-01 is applied before the split and not
after, and a test holds it: only that way is the number of chunks per document
predictable, and the disk figure of criterion 4 (100136 chunks, 876.0 byte per
document) rests on exactly that.

The tokenizer here is a word level one built in memory, not the shipped model.
That is deliberate: one word is one token, so every number in this file can be
read off the text, and the tests run on a machine that has no model at all. What
the real tokenizer changes is the count, never the arithmetic.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tokenizers import Tokenizer, models, pre_tokenizers

from findling.embed.chunker import ChunkSpan, chunk_spans, make_splitter

# One word is one token, and every unknown word becomes a single [UNK]. The
# vocabulary is therefore allowed to be empty: what is measured here is where a
# boundary lands, not which word stands there.
UNKNOWN = "[UNK]"

GERMAN = (
    "Die Bueroraeume der Behoerde in Muenchen sind seit Jahren ueberfuellt. "
    "Groessere Aenderungen an der Gebuehrenordnung waeren dringend noetig. "
    "Der Ausschuss hat die Vorlage vertagt und um eine Stellungnahme gebeten."
).replace("ue", "ü").replace("oe", "ö").replace("ae", "ä")

FRENCH = (
    "La commune a recu la demande et l'a transmise au service competent. "
    "Les charges de fonctionnement ont ete revisees apres le controle. "
    "Le conseil municipal a decide de reporter la deliberation."
).replace("recu", "reçu").replace("competent", "compétent").replace("ete", "été")


@pytest.fixture
def tokenizer() -> Tokenizer:
    built = Tokenizer(models.WordLevel({UNKNOWN: 0}, unk_token=UNKNOWN))
    built.pre_tokenizer = pre_tokenizers.Whitespace()
    return built


def _tokens(tokenizer: Tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False).ids)


def _spans(tokenizer: Tokenizer, text: str, *, cap: int, chunk: int, overlap: int = 0) -> list[ChunkSpan]:
    splitter = make_splitter(tokenizer, chunk_tokens=chunk, overlap=overlap)
    return chunk_spans(text, tokenizer=tokenizer, splitter=splitter, token_cap=cap)


def test_the_ordinals_run_upwards_without_a_gap(tokenizer: Tokenizer) -> None:
    spans = _spans(tokenizer, GERMAN, cap=64, chunk=8)

    assert len(spans) > 1
    assert [span.ordinal for span in spans] == list(range(len(spans)))
    # The ordinal is the position in the document, which is what
    # vectors.replace_chunks writes and what the snippet of D-13 is looked up by.
    assert all(span.char_start < span.char_end for span in spans)


def test_the_spans_never_run_backwards(tokenizer: Tokenizer) -> None:
    spans = _spans(tokenizer, GERMAN, cap=64, chunk=8)

    starts = [span.char_start for span in spans]
    assert starts == sorted(starts)


def test_a_german_span_cuts_the_chunk_it_claims_to_describe(tokenizer: Tokenizer) -> None:
    splitter = make_splitter(tokenizer, chunk_tokens=8, overlap=0)
    chunks = splitter.chunk_indices(GERMAN)
    spans = chunk_spans(GERMAN, tokenizer=tokenizer, splitter=splitter, token_cap=64)

    # Four umlauts stand before the first boundary. Counted in bytes, every one
    # of them would push the cut one position further right, and the text would
    # still look almost correct, which is why this bug survives review.
    assert GERMAN.index("ü") < spans[0].char_end
    assert GERMAN[: spans[0].char_end].count("ü") + GERMAN[: spans[0].char_end].count("ö") >= 2
    for span, (_, chunk) in zip(spans, chunks, strict=True):
        assert GERMAN[span.char_start : span.char_end] == chunk


def test_a_french_span_cuts_the_chunk_it_claims_to_describe(tokenizer: Tokenizer) -> None:
    splitter = make_splitter(tokenizer, chunk_tokens=8, overlap=0)
    chunks = splitter.chunk_indices(FRENCH)
    spans = chunk_spans(FRENCH, tokenizer=tokenizer, splitter=splitter, token_cap=64)

    # D-03 makes French a requirement, and the cedilla and the accents are two
    # byte characters exactly like the umlauts above.
    assert "ç" in FRENCH[: spans[0].char_end]
    for span, (_, chunk) in zip(spans, chunks, strict=True):
        assert FRENCH[span.char_start : span.char_end] == chunk


def test_the_text_behind_the_cap_gets_no_chunk(tokenizer: Tokenizer) -> None:
    spans = _spans(tokenizer, GERMAN, cap=8, chunk=8)

    covered = GERMAN[: spans[-1].char_end]
    assert _tokens(tokenizer, covered) <= 8
    assert spans[-1].char_end < len(GERMAN)


def test_ten_times_the_cap_yields_as_many_chunks_as_exactly_the_cap(tokenizer: Tokenizer) -> None:
    at_the_cap = GERMAN
    ten_times = " ".join([GERMAN] * 10)
    cap = _tokens(tokenizer, at_the_cap)

    short = _spans(tokenizer, at_the_cap, cap=cap, chunk=8)
    long = _spans(tokenizer, ten_times, cap=cap, chunk=8)

    # This is the property the disk figure of criterion 4 rests on: the number of
    # chunks per document is a function of the cap and not of the document, and
    # it only is because the cap is applied before the split.
    assert len(long) == len(short)


def test_no_chunk_carries_more_tokens_than_the_window(tokenizer: Tokenizer) -> None:
    window = 8
    spans = _spans(tokenizer, GERMAN, cap=64, chunk=window)

    for span in spans:
        assert _tokens(tokenizer, GERMAN[span.char_start : span.char_end]) <= window


def test_a_text_shorter_than_one_chunk_is_one_chunk_over_all_of_it(tokenizer: Tokenizer) -> None:
    text = "Ein kurzer Satz."

    spans = _spans(tokenizer, text, cap=64, chunk=64)

    assert len(spans) == 1
    assert text[spans[0].char_start : spans[0].char_end] == text


def test_an_empty_text_is_an_empty_list_and_not_an_error(tokenizer: Tokenizer) -> None:
    assert _spans(tokenizer, "", cap=64, chunk=8) == []


@pytest.mark.parametrize("text", ["   ", "\n\n", "\t \r\n ", "   "])
def test_a_text_of_nothing_but_whitespace_is_an_empty_list(tokenizer: Tokenizer, text: str) -> None:
    # An empty chunk would still cost a vector and a row, and it would rank
    # against real content with a distance nobody can interpret.
    assert _spans(tokenizer, text, cap=64, chunk=8) == []


def test_the_same_text_with_the_same_settings_gives_the_same_spans(tokenizer: Tokenizer) -> None:
    first = _spans(tokenizer, GERMAN, cap=32, chunk=8)
    second = _spans(tokenizer, GERMAN, cap=32, chunk=8)

    assert first == second


def test_an_overlap_is_allowed_and_shows_up_as_one(tokenizer: Tokenizer) -> None:
    without = _spans(tokenizer, GERMAN, cap=64, chunk=8, overlap=0)
    with_overlap = _spans(tokenizer, GERMAN, cap=64, chunk=8, overlap=4)

    assert len(with_overlap) >= len(without)
    # Overlapping spans are the point: neighbouring chunks share text, so a
    # later start may sit before the previous end.
    assert any(
        later.char_start < earlier.char_end
        for earlier, later in zip(with_overlap, with_overlap[1:], strict=False)
    )


def test_the_split_opens_no_file(tokenizer: Tokenizer, monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args: object, **kwargs: object) -> None:
        raise AssertionError("the chunker opened a file")

    splitter = make_splitter(tokenizer, chunk_tokens=8, overlap=0)
    monkeypatch.setattr(Path, "open", refuse)
    monkeypatch.setattr("builtins.open", refuse)

    spans = chunk_spans(GERMAN, tokenizer=tokenizer, splitter=splitter, token_cap=64)

    # A pure utility next to the model rather than inside it (the char_ranges
    # shape of index/search.py): testable with a text and a few numbers, and it
    # reaches for nothing on disk.
    assert spans
