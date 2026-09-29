#!/usr/bin/env python3
"""The fixed subset of the snapshot corpus every cell of phase 28 measures.

**DIESE FASSUNG IST NICHT GEFAHREN.** No raw file lies next to it; what it reads
on the box is read on the trip.

The rule is D-28-09 (variant A of 28-RESEARCH.md, pattern 3): the first N files
of each category of the load corpus, in the order build_load_corpus.py writes
them. The snapshot corpus is numbered by category, "{index:05d}-<slug>.<ext>",
seed phase5-full, and the index ranges are those of allocate(50000) walked over
CATEGORIES in their fixed order. "The first N" is a rule and not a draw: every
file has its own seed stream, so the first N of a category are an unbiased
sample of it (assumption A11), and nobody has to keep a seed for the subset.

    scan_single   1800 of 00001-09916, i.e. 00001-01800
    scan_multi     100 of 09917-10016, all (791 pages, 2 to 30 per file)
    text_pdf      1500 of 10017-32552, i.e. 10017-11516
    ooxml          900 of 32553-42568, i.e. 32553-33452
    opendocument   400 of 42569-47576, i.e. 42569-42968
    plain_text     200 of 47577-49880, i.e. 47577-47776
    image          100 of 49881-49980, all
    oversize         0 of 49981-50000, left out (too_large measures nothing)

Sum 5000 files, 2000 of them through tesseract, 2691 OCR pages.

The ranges and the page draw of the multi page scans are copied here and not
imported: build_load_corpus.py imports Pillow at module level, and the host
python of the box has no third party package. test_v14_teilkorpus.py holds the
copies against allocate(50000), SCAN_PAGE_BANDS and _scan_page_count of the
generator, file by file, so the two cannot drift apart unnoticed.

Subcommands:

    auswahl                     the 5000 prefixes and the page sum, offline
    liste <wurzel>              name,bytes,sha256 of the rule's files, sorted,
                                and as last line the sha256 over that list
    hardlinks [--trocken] <quelle> <ziel>
                                hard links of the rule's files into <ziel>
    zaehltor <zahl>             exactly 5000, or the cell ends

liste reads the files of the rule on the box by their five digit prefix, from
the flat corpus directory lasttest/files/loadtest of the snapshot, and writes
what build_load_corpus writes for the whole corpus: one row per file and the
checksum over the sorted rows. Only file names leave the tool, never a path
of the machine (T-28-02).

hardlinks fills the folder teilkorpus/ in the home of the account lasttest
(cp -al: same bytes, no disk space, same owner www-data), so that nothing is
left to be done by hand on the box. Run it as www-data, so the new folder
belongs to the web server like the files in it. --trocken prints the cp -al
commands and touches nothing. Every file of the rule is checked BEFORE the
first link, so a missing file leaves no half filled folder behind.

zaehltor compares the count the crawl reached with 5000 (T-28-03).

Exit codes:

  0 done
  2 usage: unknown subcommand, missing argument, or a count that is no count
  3 a file of the rule is missing under the root
  4 a prefix of the rule matches more than one file
  5 the target of hardlinks exists and is not empty
  6 zaehltor: the count is not exactly 5000

Standard library only, because the host python of the box runs it.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import sys
from collections.abc import Sequence
from pathlib import Path

EXIT_USAGE = 2
EXIT_MISSING = 3
EXIT_AMBIGUOUS = 4
EXIT_TARGET_NOT_EMPTY = 5
EXIT_COUNT_GATE = 6

SEED = "phase5-full"

# allocate(50000) of scripts/dev/build_load_corpus.py walked over CATEGORIES,
# first and last index of each category. Held against the generator by a test.
SNAPSHOT_RANGES: tuple[tuple[str, tuple[int, int]], ...] = (
    ("scan_single", (1, 9916)),
    ("scan_multi", (9917, 10016)),
    ("text_pdf", (10017, 32552)),
    ("ooxml", (32553, 42568)),
    ("opendocument", (42569, 47576)),
    ("plain_text", (47577, 49880)),
    ("image", (49881, 49980)),
    ("oversize", (49981, 50000)),
)

# D-28-09, variant A.
RULE: dict[str, int] = {
    "scan_single": 1800,
    "scan_multi": 100,
    "text_pdf": 1500,
    "ooxml": 900,
    "opendocument": 400,
    "plain_text": 200,
    "image": 100,
    "oversize": 0,
}

SUBSET_FILES = 5000

# The categories whose files go through tesseract, and how many pages each has:
# a single scan and an image are one page, a multi page scan draws its count.
ONE_PAGE_OCR = frozenset({"scan_single", "image"})
MULTI_PAGE_OCR = "scan_multi"

# Copied from build_load_corpus.py, (share, low, high) of the page draw.
SCAN_PAGE_BANDS: tuple[tuple[int, int, int], ...] = (
    (60, 2, 6),
    (30, 7, 14),
    (10, 15, 30),
)


class Rng:
    """The SHA-256 counter mode generator of build_load_corpus.py, the part this tool needs."""

    __slots__ = ("_buffer", "_counter", "_root", "_used")

    def __init__(self, *parts: object) -> None:
        material = "|".join(str(part) for part in parts).encode("utf-8")
        self._root = hashlib.sha256(material).digest()
        self._counter = 0
        self._buffer = b""
        self._used = 0

    def raw(self, count: int) -> bytes:
        while len(self._buffer) - self._used < count:
            self._buffer = (
                self._buffer[self._used :] + hashlib.sha256(self._root + self._counter.to_bytes(8, "big")).digest()
            )
            self._counter += 1
            self._used = 0
        chunk = self._buffer[self._used : self._used + count]
        self._used += count
        return chunk

    def below(self, bound: int) -> int:
        return int.from_bytes(self.raw(4), "big") % bound

    def between(self, low: int, high: int) -> int:
        return low + self.below(high - low + 1)


def multi_page_count(index: int) -> int:
    """The page count of the multi page scan with this index, as the generator drew it.

    generate() draws the extension and the slug first, one four byte draw each,
    and only then does build_scan_multi draw the page count.
    """
    rng = Rng(SEED, MULTI_PAGE_OCR, index)
    rng.raw(4)
    rng.raw(4)
    draw = rng.below(sum(share for share, _, _ in SCAN_PAGE_BANDS))
    seen = 0
    for share, low, high in SCAN_PAGE_BANDS:
        seen += share
        if draw < seen:
            return rng.between(low, high)
    return SCAN_PAGE_BANDS[-1][2]


def selection() -> dict[str, list[int]]:
    """The indices of the rule, per category, in snapshot order."""
    chosen: dict[str, list[int]] = {}
    for key, (first, last) in SNAPSHOT_RANGES:
        wanted = RULE[key]
        if wanted > last - first + 1:
            message = f"01-teilkorpus: the rule wants {wanted} {key} files, the snapshot has {last - first + 1}"
            raise SystemExit(message)
        chosen[key] = list(range(first, first + wanted))
    return chosen


def prefixes() -> list[str]:
    """The five digit prefixes of the rule's files, ascending."""
    return [f"{index:05d}" for indices in selection().values() for index in indices]


def ocr_pages() -> int:
    """The OCR pages of the subset: one per single scan and image, the drawn count per multi page scan."""
    chosen = selection()
    pages = sum(len(chosen[key]) for key in ONE_PAGE_OCR)
    return pages + sum(multi_page_count(index) for index in chosen[MULTI_PAGE_OCR])


def resolve(root: Path) -> tuple[dict[str, str], int]:
    """File name per prefix of the rule under ``root``, or the exit code that forbids going on."""
    wanted = set(prefixes())
    found: dict[str, list[str]] = {}
    for entry in os.scandir(root):
        if not entry.is_file(follow_symlinks=False):
            continue
        prefix = entry.name[:5]
        if prefix in wanted and entry.name[5:6] == "-":
            found.setdefault(prefix, []).append(entry.name)
    missing = sorted(wanted - found.keys())
    if missing:
        shown = " ".join(missing[:10])
        more = f" and {len(missing) - 10} more" if len(missing) > 10 else ""
        print(f"01-teilkorpus: {len(missing)} files of the rule are missing: {shown}{more}", file=sys.stderr)
        return {}, EXIT_MISSING
    doubled = sorted(prefix for prefix, names in found.items() if len(names) > 1)
    if doubled:
        print(f"01-teilkorpus: these prefixes match more than one file: {' '.join(doubled[:10])}", file=sys.stderr)
        return {}, EXIT_AMBIGUOUS
    return {prefix: names[0] for prefix, names in found.items()}, 0


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def command_auswahl() -> int:
    chosen = selection()
    for prefix in prefixes():
        print(prefix)
    for key, indices in chosen.items():
        span = f"{indices[0]:05d}-{indices[-1]:05d}" if indices else "-"
        print(f"kategorie {key} {len(indices)} {span}")
    print(f"teilkorpus dateien {sum(len(indices) for indices in chosen.values())} ocr-seiten {ocr_pages()}")
    return 0


def command_liste(root: Path) -> int:
    names, code = resolve(root)
    if code:
        return code
    rows = []
    for name in names.values():
        path = root / name
        rows.append(f"{name},{path.stat().st_size},{sha256_of(path)}")
    rows.sort()
    print("name,bytes,sha256")
    for row in rows:
        print(row)
    # The checksum over the sorted rows, the same recipe build_load_corpus uses
    # for the whole corpus; it is the one line the report quotes.
    print(f"listen-pruefsumme {hashlib.sha256(chr(10).join(rows).encode('ascii')).hexdigest()}")
    return 0


def command_hardlinks(source: Path, target: Path, *, dry: bool) -> int:
    names, code = resolve(source)
    if code:
        return code
    if target.exists() and any(target.iterdir()):
        print("01-teilkorpus: the target exists and is not empty, nothing was linked", file=sys.stderr)
        return EXIT_TARGET_NOT_EMPTY
    ordered = [names[prefix] for prefix in sorted(names)]
    if dry:
        print(f"mkdir -p {shlex.quote(str(target))}")
        for name in ordered:
            print(f"cp -al {shlex.quote(str(source / name))} {shlex.quote(str(target / name))}")
        print(f"hardlinks trocken {len(ordered)}")
        return 0
    target.mkdir(parents=True, exist_ok=True)
    for name in ordered:
        os.link(source / name, target / name)
    print(f"hardlinks angelegt {len(ordered)}")
    return 0


def command_zaehltor(value: str) -> int:
    if not value.isdigit():
        print(f"01-teilkorpus: zaehltor wants a whole number, got '{value}'", file=sys.stderr)
        return EXIT_USAGE
    count = int(value)
    if count != SUBSET_FILES:
        print(f"zaehltor verfehlt {count} statt {SUBSET_FILES}")
        return EXIT_COUNT_GATE
    print(f"zaehltor bestanden {SUBSET_FILES}")
    return 0


def usage() -> int:
    print(
        "usage: 01-teilkorpus.py auswahl | liste <wurzel> | hardlinks [--trocken] <quelle> <ziel> | zaehltor <zahl>",
        file=sys.stderr,
    )
    return EXIT_USAGE


def main(argv: Sequence[str]) -> int:
    if not argv:
        return usage()
    command, rest = argv[0], list(argv[1:])
    if command == "auswahl" and not rest:
        return command_auswahl()
    if command == "liste" and len(rest) == 1:
        return command_liste(Path(rest[0]))
    if command == "hardlinks":
        dry = "--trocken" in rest
        paths = [item for item in rest if item != "--trocken"]
        if len(paths) == 2:
            return command_hardlinks(Path(paths[0]), Path(paths[1]), dry=dry)
    if command == "zaehltor" and len(rest) == 1:
        return command_zaehltor(rest[0])
    return usage()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
