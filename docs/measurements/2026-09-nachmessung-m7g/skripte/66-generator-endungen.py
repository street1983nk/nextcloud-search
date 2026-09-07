#!/usr/bin/env python3
"""The extension distribution of the generator, replayed from the seed alone.

Half one of the extension comparison of assumption A10. It writes nothing and it
needs no box: the generator picks the extension of every file with
``Rng(seed, category.key, index).pick(category.extensions)``, so the same seed
produces the same distribution on any machine, and the allocation over the eight
categories is the same largest remainder arithmetic.

Why replayed and not read off the corpus. The corpus is the thing under test. If
the expectation were read from the files on the volume, the comparison would ask
the corpus whether it agrees with itself, and the one failure mode worth catching
here, a category that never reached the index, would be invisible.

Call: 66-generator-endungen.py [--seed phase5-full] [--files 50000]
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts" / "dev"))

from build_load_corpus import CATEGORIES, Rng, allocate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", default="phase5-full")
    parser.add_argument("--files", type=int, default=50_000)
    arguments = parser.parse_args(argv)

    counts = allocate(arguments.files)
    by_extension: collections.Counter[str] = collections.Counter()
    by_category_extension: dict[str, collections.Counter[str]] = {}
    index = 0
    for category in CATEGORIES:
        seen: collections.Counter[str] = collections.Counter()
        for _ in range(counts[category.key]):
            index += 1
            rng = Rng(arguments.seed, category.key, index)
            extension = rng.pick(category.extensions)
            by_extension[extension] += 1
            seen[extension] += 1
        by_category_extension[category.key] = seen

    print(
        json.dumps(
            {
                "seed": arguments.seed,
                "files": arguments.files,
                "je_kategorie": counts,
                "je_endung": dict(sorted(by_extension.items())),
                "je_kategorie_und_endung": {
                    key: dict(sorted(value.items())) for key, value in by_category_extension.items()
                },
                "summe": sum(by_extension.values()),
            },
            indent=1,
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
