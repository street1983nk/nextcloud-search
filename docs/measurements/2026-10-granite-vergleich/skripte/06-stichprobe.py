#!/usr/bin/env python3
"""Step 6 of the granite comparison: the fixed sample of 500 load corpus files.

README section 2 fixes the sample before the first throughput run: the load
corpus of ``scripts/dev/build_load_corpus.py --seed phase5``, the bytewise sorted
list of its relative paths, and ``random.Random("granite-35").sample(paths, 500)``.

The corpus is 50.000 files and about 20 GB, and only 500 of them are needed. The
generator derives every file from ``Rng(seed, category, index)`` alone, so this
script walks the same loop as ``generate`` but only draws the two name picks for
each file, and writes the bytes only for the 500 drawn names. A file written
here is byte for byte the file the full run writes; the sha256 per file in the
raw data is what makes that checkable against any later full build.

The generator is loaded from the path given on the command line rather than put
on the import path, so this file names no directory of any machine.

    cd backend && uv run python ../docs/measurements/2026-10-granite-vergleich/skripte/06-stichprobe.py \\
        --generator ../scripts/dev/build_load_corpus.py --out <WORK>/stichprobe --report <rohdaten>/06-stichprobe.txt
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import random
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType

SEED = "phase5"
SAMPLE_SEED = "granite-35"
SAMPLE_SIZE = 500
CORPUS_FILES = 50_000


def load_generator(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("build_load_corpus", path)
    if spec is None or spec.loader is None:
        message = f"cannot load the generator from {path.name}"
        raise SystemExit(message)
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolve their module through sys.modules while the class body runs.
    sys.modules["build_load_corpus"] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--generator", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    corpus = load_generator(args.generator)
    corpus.assert_ready_to_write()
    counts = corpus.allocate(CORPUS_FILES)

    # The same walk as generate(): category order, running index, two picks.
    names: dict[str, tuple[str, int]] = {}
    index = 0
    for category in corpus.CATEGORIES:
        for _ in range(counts[category.key]):
            index += 1
            rng = corpus.Rng(SEED, category.key, index)
            extension = rng.pick(category.extensions)
            name = f"{index:05d}-{rng.pick(corpus.SLUGS)}.{extension}"
            names[name] = (category.key, index)

    ordered = sorted(names, key=lambda entry: entry.encode("utf-8"))
    # The README fixes exactly this generator and seed; a reproducible draw, no secret.
    sample = random.Random(SAMPLE_SEED).sample(ordered, SAMPLE_SIZE)  # noqa: S311

    args.out.mkdir(parents=True, exist_ok=True)
    by_key = {category.key: category for category in corpus.CATEGORIES}
    rows: list[str] = []
    per_category: Counter[str] = Counter()
    total = 0
    for name in sorted(sample, key=lambda entry: entry.encode("utf-8")):
        key, number = names[name]
        category = by_key[key]
        rng = corpus.Rng(SEED, key, number)
        extension = rng.pick(category.extensions)
        rng.pick(corpus.SLUGS)
        size, digest = corpus.write_file(args.out / name, category.build(rng, extension, category.target_bytes))
        rows.append(f"{name},{key},{size},{digest}")
        per_category[key] += 1
        total += size

    listing_digest = hashlib.sha256("\n".join(ordered).encode("utf-8")).hexdigest()
    sample_digest = hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()
    header = [
        "schritt 6 stichprobe, README abschnitt 2",
        f"korpus build_load_corpus.py --seed {SEED}, {len(ordered)} dateien",
        f"namensliste bytewise sortiert, sha256 {listing_digest}",
        f'ziehung random.Random("{SAMPLE_SEED}").sample(namen, {SAMPLE_SIZE})',
        f"gezogen {len(rows)} dateien, {total} byte",
        *(f"kategorie {key} {per_category[key]}" for key in sorted(per_category)),
        f"sha256 dieser liste (zeilen unten, ohne kopf) {sample_digest}",
        "name,kategorie,bytes,sha256",
    ]
    args.report.write_text("\n".join([*header, *rows]) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(header))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
