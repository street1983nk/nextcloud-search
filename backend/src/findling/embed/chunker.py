"""Text into spans: where a document is cut, counted in characters, capped at one page.

A pure utility that lives beside the model rather than inside it, in the shape
``index/search.py::char_ranges`` established for this project: it takes a text
and a few numbers and gives back a few numbers, so it can be checked without an
index, without a model and without a database.

**Characters, not bytes.** The two offsets this module produces are the
``char_start`` and ``char_end`` of the ``chunks`` table, and that table says
CHARACTERS in capitals for a reason. ``semantic-text-splitter`` is a Rust
library working on a ``str``, the stored ``body_de`` is a Python ``str``, and a
byte offset that travels into either would still look almost right. This
repository has measured the confusion once already: ``index/search.py`` reports
(35, 51) for a German sentence where the character range is (35, 50), and the
comment there explains why that class of bug survives review so reliably. The
offsets of ``chunk_indices`` are documented as character offsets and a test in
``tests/test_chunker.py`` cuts with them and compares with the chunk itself, on
a German sentence and on a French one, rather than trusting the documentation.

**The split runs against the real tokenizer, never against a character count.**
A character count does not hit the 512 token window of the model: a chunk that
comes out too long is silently truncated at the inference session, loses its
tail and nothing fails (06-RESEARCH.md, "Don't Hand-Roll"). The splitter counts
with the same tokenizer the model is fed with, which is the only counter whose
answer means anything here.

**The cap of D-01 is applied BEFORE the split, not after.** The text is cut to
its first ``token_cap`` tokens and only then divided. The order is the whole
statement: only this way is the number of chunks per document a function of the
cap instead of a function of the document, and the disk figure of criterion 4
(100136 chunks, 876.0 byte per document, measured in plan 06-04) rests on
exactly that. Splitting first and dropping the surplus afterwards would produce
the same two chunks for an average document and quietly more for a long one.

What is deliberately not decided here: whether a file belongs in the embedding
track at all. That falls in the poller of plan 06-07. And no text of any
document is ever logged, returned or raised by this module; it answers in
integers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from semantic_text_splitter import TextSplitter

if TYPE_CHECKING:
    from tokenizers import Tokenizer


@dataclass(frozen=True, slots=True)
class ChunkSpan:
    """One chunk of a document as three numbers, and nothing else.

    Frozen and free of text on purpose. The caller already holds the document, so
    carrying the excerpt along would only mean a second copy of user content
    travelling through the embedding path (T-06-20).
    """

    ordinal: int
    char_start: int
    char_end: int


def make_splitter(tokenizer: Tokenizer, *, chunk_tokens: int, overlap: int) -> TextSplitter:
    """Build the splitter once and hand it to every document afterwards.

    A function of its own rather than a step inside :func:`chunk_spans`, because
    building it hands the whole tokenizer across the language boundary. The
    shipped ``tokenizer.json`` weighs 17 MB, and paying that per document would
    turn a one time cost into a per file one on a box with two shared cores.

    ``chunk_tokens`` and ``overlap`` come from :mod:`findling.config`, where the
    range check keeps the first inside the model window and the second below the
    first: an overlap that is not smaller than the chunk never advances.
    """
    return TextSplitter.from_huggingface_tokenizer(tokenizer, chunk_tokens, overlap=overlap)


def chunk_spans(text: str, *, tokenizer: Tokenizer, splitter: TextSplitter, token_cap: int) -> list[ChunkSpan]:
    """Cut a document into the spans of its first ``token_cap`` tokens.

    Both the tokenizer and the splitter are arguments and neither is built here.
    The splitter counts tokens but cannot say where the cap falls, and the
    tokenizer says where it falls but does not split; the caller owns both and
    keeps them for the whole run.

    A text that is empty or nothing but whitespace gives an empty list. An empty
    chunk would still cost a vector, a row and a rank, with a distance nobody can
    interpret.
    """
    if not text.strip():
        return []

    capped = _first_tokens(text, tokenizer, token_cap)
    return [
        ChunkSpan(ordinal=ordinal, char_start=offset, char_end=offset + len(chunk))
        for ordinal, (offset, chunk) in enumerate(splitter.chunk_indices(capped))
    ]


def _first_tokens(text: str, tokenizer: Tokenizer, token_cap: int) -> str:
    """Return the prefix of ``text`` that carries at most ``token_cap`` tokens.

    The cut is taken from the offset table of the encoding rather than from an
    estimated character count. 06-02 measured 3.2947 characters per token for
    German prose and 4.0452 for a bare word list, so an estimate would be off by
    a fifth between two documents of the same holding, and the number of chunks
    would stop being predictable in exactly the way this module promises it is.

    Special tokens are switched off, for the same reason as in
    ``embed/bench.py``: the encoder would add its own two per call, and the cap
    is a statement about the document.
    """
    encoding = tokenizer.encode(text, add_special_tokens=False)
    if len(encoding.ids) <= token_cap:
        return text
    # The offsets are character positions into the original text, and the second
    # entry of the last token that still fits is where the prefix ends.
    return text[: encoding.offsets[token_cap - 1][1]]
