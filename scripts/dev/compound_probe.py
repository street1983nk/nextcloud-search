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

``--against LIST`` extends that comparison to a list the caller names, which is
how the fixture of the test suite is checked rather than believed. The fixture
is not the generated subset: it is the union of the subset with the entries the
suite already carried, and adding entries to a constituent list is not a
monotone operation. One more entry can send a split that used to succeed into a
dead end, so the union has to be measured, and the only measurement that counts
is one against the real Debian list inside the image the app ships on.

Security rule, carried unchanged from T-02-14: the probe reads the case list of
the repository, the Debian word list of the image, and with ``--against`` one
further list that the caller names. It never reads state.db, never an index and
never a user file, so nothing it prints can be user content. The words it prints
are the cases of the repository and the entries of a published spelling
dictionary.

Run it through scripts/dev/measure_compounds.sh. A developer machine has no
Debian word list, and a measurement that quietly falls back to a fixture is a
measurement of the fixture.

Usage: compound_probe.py [--against LIST] CASES OUTPUT_DIR
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

AGAINST = "--against"

USAGE = "compound_probe: usage: compound_probe.py [--against LIST] CASES OUTPUT_DIR"


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


def _differing(words: Sequence[str], left: Sequence[Sequence[str]], right: Sequence[Sequence[str]]) -> list[str]:
    """Return the cases whose two token lists are not the same list."""
    return [word for word, one, other in zip(words, left, right, strict=True) if one != other]


def _report(words: Sequence[str], headline: str) -> None:
    """Write a difference to stderr, headline first and then case by case."""
    print(f"compound_probe: {headline}", file=sys.stderr)
    for word in words:
        print(f"compound_probe: differing case: {word}", file=sys.stderr)


def _split_arguments(argv: Sequence[str]) -> tuple[Path | None, Path, Path] | None:
    """Return the optional list to check, the case list and the output directory."""
    rest = list(argv)
    against: Path | None = None
    if rest and rest[0] == AGAINST:
        if len(rest) < 2:
            return None
        against = Path(rest[1])
        rest = rest[2:]
    if len(rest) != 2:
        return None
    return against, Path(rest[0]), Path(rest[1])


def main(argv: Sequence[str]) -> int:
    """Write the three measurement files and prove the subset equals the list."""
    parsed = _split_arguments(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2

    against_path, cases_path, out_dir = parsed
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

    differing = _differing(words, full_tokens, subset_tokens)
    if differing:
        _report(differing, "the subset does not tokenise like the full list")
        return 1

    if against_path is not None:
        # The named list, held against the real one case by case. Adding entries
        # is not monotone, so a fixture that carries more than the subset has to
        # be measured rather than assumed to be at least as good.
        named = against_path.read_text(encoding=ENCODING).split()
        named_differing = _differing(words, full_tokens, _tokenise(named, words))
        if named_differing:
            _report(named_differing, f"{against_path} does not tokenise like the full list")
            return 1
        print(f"compound_probe: {against_path} tokenises like the full list, {len(named)} entries")

    print(f"compound_probe: {len(words)} cases, {len(entries)} entries, {len(subset)} in the subset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
