"""Measure recipe B case by case against the real Dutch Debian word list.

The Dutch sibling of ``compound_probe.py``. It answers four questions for every
word of ``backend/tests/fixtures/compound_cases_nl.txt`` and it answers them
with the shipped code, never with a rebuilt chain: which tokens the Dutch
splitter chain produces, which tokens the Dutch chain without a splitter
produces, whether the word itself stands in ``/usr/share/dict/dutch``, and
whether its folded form is an entry of the constituent list. The last of the
four is the trap that makes a plausible case unbuildable: an entry is never
split, so a compound that stands in the list itself can only ever come back as
one token.

A line of the case list with two words is a compound and the constituent a user
would search it by. It counts as found when the one token of the constituent
stands among the tokens of the compound. A line with one word is a guard that
must stay whole, which means exactly one token.

It also builds the test fixture instead of leaving it to a hand written subset.
The entries of the full list that occur inside one of the folded words of the
case list or of ``chain_cases_nl.txt`` are written out as
``fixture-subset.txt``, a second chain is built over exactly that subset, and
the tokens of both chains are compared for every word of both files. One
difference and the probe fails, so a fixture that is not the list can no longer
pass unnoticed. ``--against LIST`` extends that comparison to a list the caller
names, which is how the fixture of the test suite is checked rather than
believed.

``--ram`` measures the resident memory the second automaton costs, in the order
of the running container: the German list held and the German automaton built
first, then the Dutch list read, the Dutch automaton built and the list
released. It prints numbers only.

Security rule, carried unchanged from T-02-14: the probe reads the two case
lists of the repository, the Debian word lists of the image, and with
``--against`` one further list that the caller names. It never reads state.db,
never an index and never a user file, so nothing it prints can be user content.
The words it prints are the cases of the repository and the entries of a
published spelling dictionary.

Run it through scripts/dev/measure_compounds_nl.sh. A developer machine has no
Debian word list, and a measurement that quietly falls back to a fixture is a
measurement of the fixture.

Usage: compound_probe_nl.py [--against LIST] CASES CHAIN_CASES OUTPUT_DIR
       compound_probe_nl.py --ram
"""

import gc
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from findling.index.analyzer import (
    cached_dutch_analyzer,
    cached_german_analyzer,
    dutch_analyzer,
    name_analyzer,
    snowball_analyzer,
)
from findling.index.wordlist import ENCODING, load_constituents, rss_bytes, wordlist_hash
from findling.index.wordlist_nl import SYSTEM_WORDLIST_NL, TUSSENKLANKEN, load_constituents_nl

TOKENS_FILE = "tokens-rezept-b.tsv"
SUBSET_FILE = "fixture-subset.txt"
NUMBERS_FILE = "kennzahlen.txt"

HEADER = ("word", "chars", "in_dutch", "entry_in_list", "tokens_without_splitter", "tokens")

AGAINST = "--against"
RAM = "--ram"

# The Snowball name of the Dutch chain without a splitter, the chain every
# installation has had since phase 17.
SNOWBALL_DUTCH = "dutch"

# Resident memory is reported in decimal megabytes, the unit of the research.
MEGABYTE = 1_000_000

USAGE = (
    "compound_probe_nl: usage: compound_probe_nl.py [--against LIST] CASES CHAIN_CASES OUTPUT_DIR\n"
    "                          compound_probe_nl.py --ram"
)

Case = tuple[str, str | None]


def _data_lines(path: Path) -> list[str]:
    """Return the lines of a case file that are neither comments nor empty."""
    lines = [line.strip() for line in path.read_text(encoding=ENCODING).split("\n")]
    return [line for line in lines if line and not line.startswith("#")]


def _cases(path: Path) -> list[Case]:
    """Return the cases: a compound with its constituent, or a guard with None."""
    cases: list[Case] = []
    for line in _data_lines(path):
        words = line.split()
        if len(words) == 1:
            cases.append((words[0], None))
        elif len(words) == 2:
            cases.append((words[0], words[1]))
        else:
            message = f"compound_probe_nl: a case line has one or two words, not {len(words)}: {line}"
            raise SystemExit(message)
    return cases


def _unique(words: Sequence[str]) -> list[str]:
    """Return the words once each, in the order of their first appearance."""
    return list(dict.fromkeys(words))


def _fold(words: Sequence[str]) -> list[str]:
    """Return every word folded the way the Dutch chain folds in front of the splitter.

    The file name chain of the product is exactly lowercase and ascii_fold behind
    the simple tokenizer, which is the part of the Dutch chain in front of the
    splitter, so it is borrowed here instead of folding a second time in Python.
    """
    fold = name_analyzer()
    return ["".join(fold.analyze(word)) for word in words]


def _subset(entries: Sequence[str], words: Sequence[str]) -> list[str]:
    """Return the entries that can possibly match one of the words, plus the linking elements.

    An entry that is no substring of any folded input can never be matched by the
    splitter, so dropping it cannot change a single token. That is why the subset
    is allowed to stand in for the full list at all, and the comparison in
    :func:`_measure` is what proves it for these two case lists.
    """
    folded = _fold(words)
    kept = {entry for entry in entries if any(entry in word for word in folded)}
    kept.update(TUSSENKLANKEN)
    return sorted(kept)


def _tokenise(constituents: Sequence[str], words: Sequence[str]) -> list[list[str]]:
    """Return the tokens the shipped Dutch splitter chain produces for every word."""
    analyzer = dutch_analyzer(constituents)
    return [analyzer.analyze(word) for word in words]


def _found(tokens: dict[str, list[str]], compound: str, constituent: str) -> bool:
    """Return whether the one token of the constituent stands among the tokens of the compound."""
    wanted = tokens[constituent]
    return len(wanted) == 1 and wanted[0] in tokens[compound]


def _tsv(
    words: Sequence[str],
    full: dict[str, list[str]],
    plain: dict[str, list[str]],
    in_source: set[str],
    entries: set[str],
) -> str:
    """Return the case table: one line per word, tokens separated by commas."""
    folded = dict(zip(words, _fold(words), strict=True))
    rows = ["\t".join(HEADER)]
    for word in words:
        rows.append(
            "\t".join(
                (
                    word,
                    str(len(word)),
                    "1" if word.lower() in in_source else "0",
                    "1" if folded[word] in entries else "0",
                    ",".join(plain[word]),
                    ",".join(full[word]),
                )
            )
        )
    return "\n".join(rows) + "\n"


def _differing(words: Sequence[str], left: Sequence[Sequence[str]], right: Sequence[Sequence[str]]) -> list[str]:
    """Return the words whose two token lists are not the same list."""
    return [word for word, one, other in zip(words, left, right, strict=True) if one != other]


def _report(words: Sequence[str], headline: str) -> None:
    """Write a difference to stderr, headline first and then word by word."""
    print(f"compound_probe_nl: {headline}", file=sys.stderr)
    for word in words:
        print(f"compound_probe_nl: differing case: {word}", file=sys.stderr)


def _split_arguments(argv: Sequence[str]) -> tuple[Path | None, Path, Path, Path] | None:
    """Return the optional list to check, the two case lists and the output directory."""
    rest = list(argv)
    against: Path | None = None
    if rest and rest[0] == AGAINST:
        if len(rest) < 2:
            return None
        against = Path(rest[1])
        rest = rest[2:]
    if len(rest) != 3:
        return None
    return against, Path(rest[0]), Path(rest[1]), Path(rest[2])


def _measure(against_path: Path | None, cases_path: Path, chain_path: Path, out_dir: Path) -> int:
    """Write the three measurement files and prove the subset equals the list."""
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = _cases(cases_path)
    case_words = _unique([word for case in cases for word in case if word is not None])
    chain_words = _unique([word for line in _data_lines(chain_path) for word in line.split()])
    words = _unique([*case_words, *chain_words])

    raw_lines = SYSTEM_WORDLIST_NL.read_text(encoding=ENCODING, errors="replace").splitlines()
    in_source = {line.strip().lower() for line in raw_lines}

    entries = load_constituents_nl()
    subset = _subset(entries, words)

    full_tokens = _tokenise(entries, words)
    subset_tokens = _tokenise(subset, words)
    plain = snowball_analyzer(SNOWBALL_DUTCH)
    plain_tokens = [plain.analyze(word) for word in words]

    full = dict(zip(words, full_tokens, strict=True))
    without = dict(zip(words, plain_tokens, strict=True))

    compounds = [(word, constituent) for word, constituent in cases if constituent is not None]
    sentinels = [word for word, constituent in cases if constituent is None]
    chain_differs = [word for word in chain_words if full[word] != without[word]]

    figures: dict[str, int | str] = {
        "source_lines": len(raw_lines),
        "entries": len(entries),
        "digest": wordlist_hash(entries),
        "subset_entries": len(subset),
        "compounds_total": len(compounds),
        "compounds_found_via_constituent": sum(1 for word, part in compounds if _found(full, word, part)),
        "compounds_found_without_splitter": sum(1 for word, part in compounds if _found(without, word, part)),
        "sentinels_whole": sum(1 for word in sentinels if len(full[word]) == 1),
        "sentinels_total": len(sentinels),
        "chain_cases_differing": len(chain_differs),
    }
    numbers = [f"{name}={value}" for name, value in figures.items()]
    numbers.extend(f"chain_case_differs={word}" for word in chain_differs)

    (out_dir / TOKENS_FILE).write_text(_tsv(case_words, full, without, in_source, set(entries)), encoding=ENCODING)
    (out_dir / SUBSET_FILE).write_text("\n".join(subset) + "\n", encoding=ENCODING)
    (out_dir / NUMBERS_FILE).write_text("\n".join(numbers) + "\n", encoding=ENCODING)

    differing = _differing(words, full_tokens, subset_tokens)
    if differing:
        _report(differing, "the subset does not tokenise like the full list")
        return 1

    if against_path is not None:
        # The named list, held against the real one word by word. Adding entries
        # is not monotone, so a fixture has to be measured, not assumed.
        named = [line for line in against_path.read_text(encoding=ENCODING).split("\n") if line]
        named_differing = _differing(words, full_tokens, _tokenise(named, words))
        if named_differing:
            _report(named_differing, f"{against_path} does not tokenise like the full list")
            return 1
        print(f"compound_probe_nl: {against_path} tokenises like the full list, {len(named)} entries")

    print(f"compound_probe_nl: {len(words)} words, {len(entries)} entries, {len(subset)} in the subset")
    return 0


def _ram() -> int:
    """Measure what the Dutch automaton costs on top of the German one. Numbers only."""
    german = load_constituents()
    cached_german_analyzer(wordlist_hash(german), german)
    gc.collect()
    rss_base = rss_bytes()

    started = time.perf_counter()
    dutch = load_constituents_nl()
    cached_dutch_analyzer(wordlist_hash(dutch), dutch)
    seconds = time.perf_counter() - started
    del dutch
    gc.collect()
    rss_released = rss_bytes()

    print(f"ram_base_mb={rss_base / MEGABYTE:.2f}")
    print(f"ram_nl_released_mb={(rss_released - rss_base) / MEGABYTE:.2f}")
    print(f"nl_build_seconds={seconds:.3f}")
    return 0


def main(argv: Sequence[str]) -> int:
    """Dispatch to the measurement or to the memory mode."""
    if list(argv) == [RAM]:
        return _ram()
    parsed = _split_arguments(argv)
    if parsed is None:
        print(USAGE, file=sys.stderr)
        return 2
    return _measure(*parsed)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
