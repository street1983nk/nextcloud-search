#!/usr/bin/env python3
"""How much body_zh changes the order of English hits, and what its weight does to that.

One index over English documents, written by the real writer with de, en and zh
filled, and a second one whose body_zh chain cuts Han characters only. Twenty
English queries go through findling.query.rewrite.build_query twice, once with
a plan without body_zh and once with it, and the two top ten lists are
compared: the mean share of the first list that the second one keeps (1 when
both are empty), how often the first hit stays the same, and how often the two
lists are identical.
The comparison is made for en against en,zh and for de,en against de,en,zh, and
for the Han and Latin chain once per body_zh weight of the sweep.

What it measures is how much the order moves, not whether it gets better:
there are no relevance judgements behind these queries.

The documents are the files named in a list, one path per line; a file shorter
than 400 characters is left out and a longer one is cut at 20000 characters.

Run from backend/:

    uv run python ../docs/measurements/2026-11-zh-kette/skripte/zh_rank.py <list>
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from types import MappingProxyType

sys.path.insert(0, "tests")

from tantivy import Filter, Index, TextAnalyzerBuilder, Tokenizer

from conftest import CONSTITUENTS
from findling.index.analyzer import MAX_TOKEN_CHARS, TOKENIZER_ZH
from findling.index.open import open_index
from findling.index.schema import FIELD_BODY_DE, FIELD_BODY_EN, FIELD_BODY_ZH, FIELD_FILE_ID, FIELD_NAME, FIELD_TITLE
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.query.rewrite import BODY_BOOST, NAME_BOOST, TITLE_BOOST, FieldPlan, build_query

QUERIES = (
    "license",
    "warranty",
    "copyright notice",
    "source code",
    "patent",
    "distribution",
    "modify",
    "installation",
    "configuration file",
    "bug report",
    "documentation",
    "compile",
    "library",
    "free software",
    "trademark",
    "contributors",
    "dependencies",
    "security",
    "version",
    "terms and conditions",
)
FIELDS = {"de": FIELD_BODY_DE, "en": FIELD_BODY_EN, "zh": FIELD_BODY_ZH}
WEIGHTS = (0.6, 0.3, 0.15, 0.05)


def documents(listing: Path) -> list[str]:
    texts: list[str] = []
    for line in listing.read_text(encoding="utf-8").splitlines():
        try:
            text = Path(line).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if len(text) > 400:
            texts.append(text[:20000])
    return texts


def build(texts: list[str], *, han_only: bool) -> Index:
    directory = Path(tempfile.mkdtemp())
    index = open_index(directory, CONSTITUENTS)
    if han_only:
        chain = TextAnalyzerBuilder(Tokenizer.regex(r"\p{Han}")).filter(Filter.lowercase())
        index.register_tokenizer(TOKENIZER_ZH, chain.filter(Filter.remove_long(MAX_TOKEN_CHARS)).build())
    writer = IndexBatchWriter(index, directory=directory, min_free_bytes=0, languages=("de", "en", "zh"))
    for file_id, body in enumerate(texts, 1):
        writer.add(
            IndexRecord(
                file_id=file_id,
                storage_id=1,
                name=f"d{file_id}.txt",
                title=f"d{file_id}",
                path=f"/d{file_id}.txt",
                ext="txt",
                body=body,
                mtime=1_700_000_000 + file_id,
            )
        )
    writer.flush()
    writer.close()
    index.reload()
    return index


def plan(codes: tuple[str, ...], zh_weight: float) -> FieldPlan:
    boosts = {FIELDS[code]: zh_weight if code == "zh" else BODY_BOOST[code] for code in codes}
    boosts |= {FIELD_NAME: NAME_BOOST, FIELD_TITLE: TITLE_BOOST}
    bodies = tuple(FIELDS[code] for code in codes)
    return FieldPlan(
        fields=(*bodies, FIELD_NAME, FIELD_TITLE), boosts=MappingProxyType(boosts), title_only=(FIELD_NAME,)
    )


def top(index: Index, query: str, chosen: FieldPlan) -> list[int]:
    rewritten = build_query(index, query, plan=chosen)
    if rewritten.query is None:
        raise SystemExit(f"the query {query!r} built nothing")
    searcher = index.searcher()
    hits = searcher.search(rewritten.query, limit=10).hits
    return [int(searcher.doc(address).to_dict()[FIELD_FILE_ID][0]) for _, address in hits]


def compare(index: Index, without: tuple[str, ...], zh_weight: float, label: str) -> None:
    kept: list[float] = []
    first = 0
    identical = 0
    for query in QUERIES:
        a = top(index, query, plan(without, zh_weight))
        b = top(index, query, plan((*without, "zh"), zh_weight))
        # Two empty lists agree completely; a query that finds nothing in either
        # plan must not count as a list that lost all its hits.
        kept.append(1.0 if not a and not b else len(set(a) & set(b)) / max(1, len(a)))
        first += a[:1] == b[:1]
        identical += a == b
    print(
        f"{label:<36} overlap@10 mean {sum(kept) / len(kept):.3f}  first hit kept {first}/{len(QUERIES)}"
        f"  identical lists {identical}/{len(QUERIES)}"
    )


def main(listing: Path) -> None:
    texts = documents(listing)
    print(f"documents {len(texts)} characters {sum(map(len, texts))} queries {len(QUERIES)}")
    latin = build(texts, han_only=False)
    for weight in WEIGHTS:
        compare(latin, ("en",), weight, f"Han and Latin, weight {weight}, en")
        compare(latin, ("de", "en"), weight, f"Han and Latin, weight {weight}, de,en")
    han = build(texts, han_only=True)
    compare(han, ("en",), BODY_BOOST["zh"], f"Han only, weight {BODY_BOOST['zh']}, en")
    compare(han, ("de", "en"), BODY_BOOST["zh"], f"Han only, weight {BODY_BOOST['zh']}, de,en")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
