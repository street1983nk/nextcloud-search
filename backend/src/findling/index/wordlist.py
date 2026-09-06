"""The constituent list for the German compound splitter, and its digest.

Recipe A, measured against sixteen real administrative compounds and ten
everyday words that must not fall apart:

    all words of /usr/share/dict/ngerman, lowercased, alphabetic only,
    length 4 to 14, plus the six linking elements as entries of their own

    276496 entries, 0.44 s to build the automaton, roughly 23 MB of resident
    memory, 14 of 16 compounds findable through one of their parts, 0 mis-splits

Three recipes were measured against it and all three are worse:

    B  nouns only, linking forms appended to every word, letters folded to
       plain ASCII: 222708 entries, 7 of 16, and real mis-splits such as
       "haushaltss" plus "atzung". This is the recipe that suggests itself, and
       it is the measurably worst one. It must not come back.
    C  nouns only, same window: 86345 entries, 12 of 16. Kept as the frugal
       variant behind FINDLING_COMPOUND_DICT=nouns, roughly a third of the
       memory. Default stays full.
    D  nouns only, window 4 to 12: 65693 entries, 12 of 16, and it over-splits:
       "betrieb | kost | abrechn" instead of "betriebskost | abrechn".

Two properties of the list are load bearing and both are counter-intuitive.

*The window has an upper end.* An entry longer than MAX_LEN is itself a
compound, and a compound that stands in the list is never split, because the
splitter matches leftmost-longest. "Kuendigungsfrist" is fifteen characters,
stands in the raw Debian list, and would swallow the whole token: a search for
"Frist" would then not find the document. The honest cost of the upper end is
the other direction: "Mietvertrag" is eleven characters, stands in the list, and
is not findable through "Vertrag". A smaller window splits more and over-splits,
which is recipe D.

*The list keeps its umlauts.* It is never folded to plain letters. The splitter
compares the raw, lowercased token against these entries, so a folded list would
simply never match and the splitting would fail silently while every test that
only asserts "something came back" stays green.

The list is a build artifact, not a runtime decision. Reading and filtering the
Debian file costs about a tenth of a second, and the resulting list decides every
token in the index, so it is written once to ``$APP_PERSISTENT_STORAGE/dict/``
together with its SHA-256 and read back on every later start. That digest belongs
into the metadata table next to schema_version and analyzer_version: if the list
changes, the tokenisation changes, and the index stops agreeing with the query
parser (T-02-11). A visible reindex is the only correct answer to that, and it
can only be triggered by something that is actually compared.

Source and licence: Debian package ``wngerman`` 20161207-15, source package
``igerman98``, upstream Bjoern Jacke, file ``/usr/share/dict/ngerman``, 356010
lines. GPL-2+, which reaches AGPL-3.0 through GPLv3. The licence text and the
provenance ship in the image, see docs/german-analyzer.md.
"""

import hashlib
import logging
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from findling.config import DEFAULT_COMPOUND_DICT, settings

LOGGER = logging.getLogger("findling.index.wordlist")

# The file the Debian package wngerman installs. Present in the image, never
# downloaded at runtime, identical on amd64 and arm64 (Architecture: all).
SYSTEM_WORDLIST = Path("/usr/share/dict/ngerman")

# Lower end: shorter fragments turn every word into confetti. Upper end: an entry
# above it is a compound itself and would never be split. Measured as the best of
# four windows; see the recipe table above.
MIN_LEN = 4
MAX_LEN = 14

# The German linking elements, as entries of their own. Without them the chain of
# matches breaks between the parts and the whole compound stays unsplit. They are
# shorter than MIN_LEN, so they can only enter the list through this constant.
#
# The same constant is used twice on purpose: it goes into the splitter here and
# comes back out as a custom stopword in findling.index.analyzer. Two literals
# would drift apart at the next rewrite, and the symptom would be a bare token
# "s" sitting in the index.
FUGEN = ("s", "es", "n", "en", "er", "ns")

# Suffix of the file holding the digest of the artifact next to it.
DIGEST_SUFFIX = ".sha256"

# Encoding of both the Debian source and our artifact.
ENCODING = "utf-8"


@dataclass(frozen=True, slots=True)
class Artifact:
    """A constituent list together with the digest that identifies it.

    ``rebuilt`` says whether the recipe ran or the artifact on the volume was
    good enough. It is the number that tells a slow start apart from a start that
    merely read a file.
    """

    entries: list[str]
    digest: str
    rebuilt: bool


def load_constituents(
    source: Path = SYSTEM_WORDLIST,
    *,
    variant: str = DEFAULT_COMPOUND_DICT,
    window: tuple[int, int] = (MIN_LEN, MAX_LEN),
) -> list[str]:
    """Apply the recipe to a raw word list and return the sorted constituents.

    ``variant`` is ``full`` (recipe A, every word) or ``nouns`` (recipe C, only
    the capitalised source entries). The window applies unchanged to both, and
    the linking elements are added to both.
    """
    minimum, maximum = window
    nouns_only = variant == "nouns"
    words: set[str] = set()
    for word in source.read_text(encoding=ENCODING, errors="replace").split():
        if not word.isalpha() or not minimum <= len(word) <= maximum:
            continue
        if nouns_only and not word[0].isupper():
            continue
        words.add(word.lower())
    words.update(FUGEN)
    return sorted(words)


def wordlist_hash(entries: Sequence[str]) -> str:
    """Return the SHA-256 of the list, stable across processes and machines.

    Hashing the joined entries rather than the source file is deliberate: what
    changes the tokenisation is the filtered list, not the bytes it came from. A
    Debian point release that only reorders lines must not force a reindex, and a
    changed window must.
    """
    digest = hashlib.sha256()
    digest.update("\n".join(entries).encode(ENCODING))
    return digest.hexdigest()


def _digest_path(target: Path) -> Path:
    """Return the path of the digest file that belongs to an artifact."""
    return target.with_name(target.name + DIGEST_SUFFIX)


def _read_artifact(target: Path) -> list[str]:
    """Read an artifact back into the list it was written from."""
    return target.read_text(encoding=ENCODING).split()


# ---------------------------------------------------------------------------
# The cache in front of the artifact. Per process, at most one entry, keyed on
# the identity of the file on the volume.
#
# Why it is here: the search side calls build_artifact again on its first
# request, so the whole list travelled into the process a second time. It is
# 276496 Python strings in the container, roughly 21.9 MB by the start up
# measurement of 2026-09-05 (docs/measurements/2026-09-05-semantiklauf-m7g,
# step 08 to step 09 of 52-woher-die-grundlast.txt), and the allocator does not
# hand that back to the operating system. A dictionary in front of the read is
# the smallest change that ends it. The log line "constituent list read from
# the volume" at the first search was the evidence the report of plan 06-11
# read as a second decomposition automaton; the automaton has had its own cache
# in analyzer.py all along, and this was the real second item.
#
# The key is the identity of the artifact, not its path alone: the recorded
# digest plus the size and the modification time of the file that carries it.
# The digest catches an exchanged list, which changes the tokenisation and has
# to arrive (T-02-11, T-06.1-13). Size and modification time catch a file
# edited behind a digest file that was left alone, so the fail closed check
# below still runs on a tampered artifact instead of being answered out of
# memory. Absence is never a key, so a volume that lost the file gets the
# recipe again and never a ghost of a list that is no longer there (T-06.1-14).
_CacheKey = tuple[str, str, int, int]

_CACHED_ENTRIES: dict[_CacheKey, list[str]] = {}

# One lock around the whole read. Two threads arriving together would otherwise
# both read the file, and one of the two copies would be paid for nothing.
_CACHE_LOCK = threading.Lock()

# How often this process really put the list into memory, by reading the
# artifact or by running the recipe. Both pay for the whole list, so both count.
# The counter is what makes the cache checkable from the outside: it tells a
# cache hit from a cheap rebuild, which no resident memory measurement on a
# shared runner can do. Same purpose as analyzer.build_count() next door.
_READ_COUNT = 0


def read_count() -> int:
    """Return how often this process has read the constituent list into memory."""
    return _READ_COUNT


def _artifact_key(target: Path, digest_path: Path) -> _CacheKey | None:
    """Return the identity of the stored artifact, or None when there is none."""
    if not target.is_file() or not digest_path.is_file():
        return None
    try:
        status = target.stat()
        recorded = digest_path.read_text(encoding=ENCODING).strip()
    except OSError:
        return None
    if not recorded:
        return None
    return (str(target), recorded, status.st_size, status.st_mtime_ns)


def _remember(target: Path, digest_path: Path, entries: list[str]) -> None:
    """Put the list into the cache under the identity it now has on the volume."""
    key = _artifact_key(target, digest_path)
    if key is None:
        return
    # At most one entry. A changed list frees the old one instead of stacking a
    # second 21.9 MB next to it, which is the shape the automaton cache has.
    _CACHED_ENTRIES.clear()
    _CACHED_ENTRIES[key] = entries


def build_artifact(
    source: Path = SYSTEM_WORDLIST,
    target: Path | None = None,
    *,
    variant: str = DEFAULT_COMPOUND_DICT,
) -> Artifact:
    """Return the constituent list, reading it at most once per process.

    Fail closed on the stored artifact: it is used only when the digest file next
    to it describes exactly the file that is there. Anything else, a truncated
    write, a half finished container start, an edited file, runs the recipe again
    rather than feeding a mystery list into the index.

    A second call that finds the same file on the volume gets the same list
    object back and touches neither the artifact nor the recipe. ``rebuilt`` is
    False for such a call, because nothing was built; :func:`read_count` is the
    number that says nothing was read either.
    """
    if target is None:
        target = settings().dict_dir / "de.txt"

    digest_path = _digest_path(target)
    with _CACHE_LOCK:
        key = _artifact_key(target, digest_path)
        if key is not None:
            cached = _CACHED_ENTRIES.get(key)
            if cached is not None:
                return Artifact(entries=cached, digest=key[1], rebuilt=False)
        return _load_artifact(source, target, digest_path, variant=variant)


def _load_artifact(source: Path, target: Path, digest_path: Path, *, variant: str) -> Artifact:
    """Read the stored artifact or run the recipe, and cache whichever ran.

    Called with the cache lock held, so the counter below is raised under the
    same lock that decides whether anything is read at all.
    """
    global _READ_COUNT

    if target.is_file() and digest_path.is_file():
        entries = _read_artifact(target)
        _READ_COUNT += 1
        recorded = digest_path.read_text(encoding=ENCODING).strip()
        if recorded and recorded == wordlist_hash(entries):
            LOGGER.info(
                "constituent list read from the volume, %d entries, read %d in this process",
                len(entries),
                _READ_COUNT,
            )
            _remember(target, digest_path, entries)
            return Artifact(entries=entries, digest=recorded, rebuilt=False)
        LOGGER.warning("stored constituent list does not match its digest, rebuilding it from the source")

    started = time.perf_counter()
    entries = load_constituents(source, variant=variant)
    _READ_COUNT += 1
    digest = wordlist_hash(entries)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(entries) + "\n", encoding=ENCODING)
    digest_path.write_text(digest + "\n", encoding=ENCODING)
    LOGGER.info(
        "constituent list built, %d entries in %.3f s, read %d in this process",
        len(entries),
        time.perf_counter() - started,
        _READ_COUNT,
    )
    _remember(target, digest_path, entries)
    return Artifact(entries=entries, digest=digest, rebuilt=True)


# ---------------------------------------------------------------------------
# Measurement mode. Numbers only, never a token and never a word: the analysis
# path sees user content, and a measurement that prints what it tokenised is the
# cheapest way to leak it (T-02-14). Driven by scripts/dev/measure_wordlist.sh,
# which runs it in a throwaway Debian container because there is no
# /usr/share/dict/ngerman on a developer machine.
# ---------------------------------------------------------------------------

# /proc/self/status is read directly instead of adding psutil for one number.
STATUS_FILE = Path("/proc/self/status")
RSS_PREFIX = "VmRSS:"


def rss_bytes() -> int:
    """Return the resident set size in bytes, or 0 where /proc is not available.

    Lives here rather than in the analyser so that the measurement of the
    automaton can reuse it without the analyser importing anything extra.
    """
    if not STATUS_FILE.is_file():
        return 0
    for line in STATUS_FILE.read_text(encoding=ENCODING).splitlines():
        if line.startswith(RSS_PREFIX):
            return int(line.split()[1]) * 1024
    return 0


def _count_source_lines(source: Path) -> int:
    """Return the number of lines of the raw source list."""
    return len(source.read_text(encoding=ENCODING, errors="replace").splitlines())


def measure(source: Path = SYSTEM_WORDLIST, *, variant: str = DEFAULT_COMPOUND_DICT) -> dict[str, float | int | str]:
    """Measure the recipe and return plain numbers.

    Nothing here reaches into :mod:`findling.index.analyzer`, not even to time
    it. Anything that only needs the list, and the extraction child of plan 02-05
    is exactly that, must be able to import this module without paying the
    roughly 23 MB of the automaton. The automaton has its own measurement mode
    next to the filter chain it belongs to.
    """
    source_lines = _count_source_lines(source)

    rss_before = rss_bytes()
    filter_started = time.perf_counter()
    entries = load_constituents(source, variant=variant)
    filter_seconds = time.perf_counter() - filter_started
    rss_after = rss_bytes()

    return {
        "variant": variant,
        "source_lines": source_lines,
        "entries": len(entries),
        "sha256": wordlist_hash(entries),
        "filter_seconds": round(filter_seconds, 3),
        "list_rss_growth_bytes": rss_after - rss_before,
    }


if __name__ == "__main__":  # pragma: no cover
    for key, value in measure(variant=settings().compound_dict).items():
        print(f"{key}={value}")
