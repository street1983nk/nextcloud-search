#!/usr/bin/env python3
"""How much a filled body_zh adds to the index directory, through the real writer.

Three directories over the same documents, written by IndexBatchWriter exactly
as the running container writes them: languages de,en, then de,en,zh, then
de,en,cs as the yardstick the rebuild reserve GROWTH_PER_LANGUAGE was measured
with. The growth is printed as a share of the de,en directory, which is the
share findling.index.rebuild.may_rebuild charges, and as a share of the text.

Two corpora:

    statutes <articles> <chars>   the article files of zh_corpus.py, joined in
                                  file order into documents of at least <chars>
                                  characters
    wordlist <file> <seed>        2000 documents of 450 words each, drawn from a
                                  word list with Zipf weights and a fixed seed

Run from backend/, because the script imports the package and the test fixture
word list:

    uv run python ../docs/measurements/2026-11-zh-kette/skripte/zh_growth.py statutes <articles> 3000
    uv run python ../docs/measurements/2026-11-zh-kette/skripte/zh_growth.py wordlist <file> 53
"""

from __future__ import annotations

import gc
import random
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "tests")

from conftest import CONSTITUENTS
from findling.index.open import open_index
from findling.index.writer import IndexBatchWriter, IndexRecord
from findling.store.repo import index_bytes


def statutes(directory: Path, chars: int) -> list[str]:
    documents: list[str] = []
    pending: list[str] = []
    for path in sorted(directory.glob("*.txt")):
        pending.append(path.read_text(encoding="utf-8"))
        if sum(map(len, pending)) >= chars:
            documents.append("\n".join(pending))
            pending = []
    if pending:
        documents.append("\n".join(pending))
    return documents


def wordlist(source: Path, seed: str) -> list[str]:
    words = [word for word in source.read_text(encoding="utf-8").split() if word.isalpha()]
    # A measurement corpus, where the fixed seed is the point and nothing is hidden.
    rng = random.Random(seed)  # noqa: S311
    rng.shuffle(words)
    weights = [1 / (rank + 1) for rank in range(len(words))]
    return [" ".join(rng.choices(words, weights, k=450)) for _ in range(2000)]


def directory_bytes(documents: list[str], languages: tuple[str, ...]) -> int:
    directory = Path(tempfile.mkdtemp())
    index = open_index(directory, CONSTITUENTS)
    writer = IndexBatchWriter(index, directory=directory, min_free_bytes=0, languages=languages)
    for file_id, body in enumerate(documents, 1):
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
    del index
    gc.collect()
    size = index_bytes(directory)
    shutil.rmtree(directory)
    return size


def main(kind: str, source: Path, parameter: str) -> None:
    documents = statutes(source, int(parameter)) if kind == "statutes" else wordlist(source, parameter)
    text = sum(len(document.encode("utf-8")) for document in documents)
    print(f"corpus {kind} documents {len(documents)} characters {sum(map(len, documents))} text_bytes {text}")
    base = directory_bytes(documents, ("de", "en"))
    print(f"de,en     {base:>10} byte  {base / text:.3f} of the text")
    for code in ("zh", "cs"):
        size = directory_bytes(documents, ("de", "en", code))
        growth = size - base
        shares = f"growth {growth / base:.3f} of the directory, {growth / text:.3f} of the text"
        print(f"de,en,{code}  {size:>10} byte  {shares}")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]), sys.argv[3])
