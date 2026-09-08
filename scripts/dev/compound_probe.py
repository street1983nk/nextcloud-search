"""Measure recipe A case by case against the real Debian word list.

The probe answers three questions for every word of
``backend/tests/fixtures/compound_cases_de.txt`` and it answers them with the
shipped code, never with a rebuilt chain: which tokens the German analysis
chain produces, whether the word itself stands in ``/usr/share/dict/ngerman``,
and whether its lowercase form is an entry of the filtered constituent list. The
last of the three is the machine readable form of the trap that makes a
plausible test case unbuildable: an entry is never split, so a short everyday
compound that stands in the list itself can only ever come back as one token.

It also builds the test fixture instead of leaving it to a hand written subset.
The entries of the full list that occur inside one of the cases are written out
as ``fixture-subset.txt``, a second chain is built over exactly that subset, and
the tokens of both chains are compared for every case. One difference and the
probe fails, so a fixture that is not the list can no longer pass unnoticed.

Security rule, carried unchanged from T-02-14: the probe reads exactly two
files, the case list from the repository and the Debian word list of the image.
It never reads state.db, never an index and never a user file, so nothing it
prints can be user content. The words it prints are the cases of the repository
and the entries of a published spelling dictionary.

Run it through scripts/dev/measure_compounds.sh. A developer machine has no
Debian word list, and a measurement that quietly falls back to a fixture is a
measurement of the fixture.

Usage: compound_probe.py CASES OUTPUT_DIR
"""

import sys
from collections.abc import Sequence
from pathlib import Path

from findling.index.analyzer import german_analyzer
from findling.index.wordlist import (
    ENCODING,
    SYSTEM_WORDLIST,
    load_constituents,
    wordlist_hash,
)

TOKENS_FILE = "tokens-rezept-a.tsv"
SUBSET_FILE = "fixture-subset.txt"
NUMBERS_FILE = "kennzahlen.txt"

HEADER = ("word", "chars", "in_ngerman", "entry_in_list", "tokens")


def _tokenise(constituents: Sequence[str], words: Sequence[str]) -> list[list[str]]:
    """Return the tokens the shipped German chain produces for every word.

    One factory call for both runs of this probe. The chain is the one the
    product ships, taken from findling.index.analyzer, because a chain rebuilt
    here would measure this file instead of the product.
    """
    analyzer = german_analyzer(constituents)
    return [analyzer.analyze(word) for word in words]


def _subset(entries: Sequence[str], words: Sequence[str]) -> list[str]:
    """Return the entries that can possibly match one of the cases.

    An entry that is no substring of any input can never be matched by the
    splitter, so dropping it cannot change a single token. That is why the
    subset is allowed to stand in for the full list at all, and the comparison
    in :func:`main` is what proves it for this particular case list.
    """
    lowered = [word.lower() for word in words]
    return [entry for entry in entries if any(entry in word for word in lowered)]


def _tsv(words: Sequence[str], tokens: Sequence[Sequence[str]], in_source: set[str], entries: set[str]) -> str:
    """Return the case table: one line per case, tokens separated by commas."""
    rows = ["\t".join(HEADER)]
    for word, produced in zip(words, tokens, strict=True):
        lowered = word.lower()
        rows.append(
            "\t".join(
                (
                    word,
                    str(len(word)),
                    "1" if lowered in in_source else "0",
                    "1" if lowered in entries else "0",
                    ",".join(produced),
                )
            )
        )
    return "\n".join(rows) + "\n"


def _numbers(
    source_lines: int,
    entries: Sequence[str],
    subset: Sequence[str],
    tokens: Sequence[Sequence[str]],
) -> str:
    """Return the key figures of the run. Numbers and digests, nothing else."""
    figures = {
        "source_lines": source_lines,
        "entries": len(entries),
        "wordlist_hash": wordlist_hash(entries),
        "subset_entries": len(subset),
        "cases": len(tokens),
        "cases_more_than_one_token": sum(1 for produced in tokens if len(produced) > 1),
        "cases_exactly_one_token": sum(1 for produced in tokens if len(produced) == 1),
        "cases_without_token": sum(1 for produced in tokens if not produced),
    }
    return "\n".join(f"{name}={value}" for name, value in figures.items()) + "\n"


def main(argv: Sequence[str]) -> int:
    """Write the three measurement files and prove the subset equals the list."""
    if len(argv) != 2:
        print("compound_probe: usage: compound_probe.py CASES OUTPUT_DIR", file=sys.stderr)
        return 2

    cases_path = Path(argv[0])
    out_dir = Path(argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)

    words = cases_path.read_text(encoding=ENCODING).split()
    raw_lines = SYSTEM_WORDLIST.read_text(encoding=ENCODING, errors="replace").splitlines()
    in_source = {line.strip().lower() for line in raw_lines}

    entries = load_constituents()
    subset = _subset(entries, words)

    full_tokens = _tokenise(entries, words)
    subset_tokens = _tokenise(subset, words)

    (out_dir / TOKENS_FILE).write_text(_tsv(words, full_tokens, in_source, set(entries)), encoding=ENCODING)
    (out_dir / SUBSET_FILE).write_text("\n".join(subset) + "\n", encoding=ENCODING)
    (out_dir / NUMBERS_FILE).write_text(_numbers(len(raw_lines), entries, subset, full_tokens), encoding=ENCODING)

    differing = [
        word
        for word, produced, from_subset in zip(words, full_tokens, subset_tokens, strict=True)
        if produced != from_subset
    ]
    if differing:
        print("compound_probe: the subset does not tokenise like the full list", file=sys.stderr)
        for word in differing:
            print(f"compound_probe: differing case: {word}", file=sys.stderr)
        return 1

    print(f"compound_probe: {len(words)} cases, {len(entries)} entries, {len(subset)} in the subset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
