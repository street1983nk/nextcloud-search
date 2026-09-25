"""The constituent list for the Dutch compound splitter, and its digest.

The sibling of findling.index.wordlist and deliberately a module of its own: the
German list, its recipe and its digest stay byte for byte where they are, and
dropping Dutch compounds again is deleting this file and its callers.

Recipes measured on 2026-09-25 against 28 Dutch administrative compounds and 33
guard words that must not fall apart (17 everyday words, 16 long non-compounds),
source /usr/share/dict/dutch, tantivy 0.26.2:

    | Recipe | Window | List   | Split       | Entries | Compounds | Guards |
    |--------|--------|--------|-------------|---------|-----------|--------|
    | none   | n/a    | n/a    | n/a         | n/a     |  0/28     | n/a    |
    | A      | 4-14   | raw    | before fold | 317320  | 20/28     | 32/33  |
    | A      | 4-12   | raw    | before fold | 257766  | 24/28     | 31/33  |
    | A      | 4-16   | raw    | before fold | 353318  | 15/28     | 33/33  |
    | B      | 4-14   | folded | behind fold | 316740  | 21/28     | 32/33  |
    | B      | 4-12   | folded | behind fold | 257194  | 25/28     | 31/33  |
    | B      | 4-16   | folded | behind fold | 352737  | 16/28     | 33/33  |

Recipe B 4-14 is the one encoded here, chosen by the owner on 2026-09-25
(decision D-03): all alphabetic lines of the source, window 4 to 14 on the
unfolded length, folded by tantivy's lowercase and ascii_fold, plus the three
linking elements s, e and en as entries of their own. The one guard that comes
apart at 4-14 is "belastingplichtige", and that is a real compound, not a
mis-split.

Why not 4-12, which finds four compounds more: it over-splits.
"onderhandelingen" becomes "onderhandel, ing", and a junk term "ing" in the
index is exactly the pattern that ruled out the German recipe D. Why B and not
A: recipe A keeps the list raw and splits before the fold, so the flat spelling
"coordinatiecentrum" of a user who does not type the trema stays whole, and the
fold position measured in phase 17 for the Dutch chain would move.

*The list is folded*, which is the opposite of the German list. The Dutch chain
folds in front of the splitter, so the splitter compares folded tokens and the
list has to lie in exactly that form. The fold is tantivy's own and never a
Python normalisation: the list and the token must be folded by the same code.

*The source is read line by line.* It carries 4380 lines with spaces, which a
split on whitespace would turn into single words the list never contained.

The list is a build artifact, written once to ``$APP_PERSISTENT_STORAGE/dict/``
together with its SHA-256 and trusted only while that digest describes it.
Unlike the German module, the process caches the digest and never the entries
(D-02): the search side needs only the digest to compare the mark, and the
entries are roughly 19.6 MB of Python strings the allocator never hands back.
The automaton is built from a list that is released right after the build.

Nothing here is read while nl is not a configured language: :func:`dutch_mark`
answers ``off`` and :func:`dutch_digest_for` answers None without touching the
source or the artifact.

Source and licence: Debian package ``wdutch`` 1:2.20.19+1-3, source package
``dutch``, upstream OpenTaal, file ``/usr/share/dict/dutch``, 413288 lines.
Distributed under CC-BY-3.0 (decision D-04); the copyright file ships in the
image as COPYING.wdutch.

This module never imports the analyser module next door, for the same reason the
German module does not: anything that only needs the list must be able to
import it without paying for an automaton.
"""

import logging
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from tantivy import Filter, TextAnalyzerBuilder, Tokenizer

from findling.config import settings
from findling.index.wordlist import DIGEST_SUFFIX, ENCODING, Artifact, rss_bytes, wordlist_hash

LOGGER = logging.getLogger("findling.index.wordlist_nl")

# The file the Debian package wdutch installs. Present in the image, never
# downloaded at runtime, identical on amd64 and arm64 (Architecture: all).
SYSTEM_WORDLIST_NL = Path("/usr/share/dict/dutch")

# Same window as the German recipe and measured separately for Dutch; see the
# table above. Applied to the unfolded length of a source line.
MIN_LEN = 4
MAX_LEN = 14

# The Dutch linking elements, as entries of their own. Without them the chain of
# matches breaks between the parts. Measured: 14 of 28 without them, 20 of 28
# with them (recipe A).
#
# The same constant is used twice on purpose: it goes into the splitter here and
# comes back out as a custom stopword in analyzer.dutch_analyzer. Two literals
# would drift apart at the next rewrite, and the symptom would be a bare token
# "s" sitting in the index.
TUSSENKLANKEN: Final = ("s", "e", "en")

# The value of the Dutch mark while nl is not a configured language.
DUTCH_LIST_OFF: Final = "off"

# Raise it when analyzer.dutch_analyzer changes its filters or their order. The
# mark carries the digest of the list, and a changed chain over an unchanged list
# would leave that digest where it was, so the index would silently disagree with
# the query parser. ANALYZER_VERSION is not the lever for that: raising it costs
# a full reindex on every installation, with or without nl.
DUTCH_CHAIN_VERSION: Final = 1

# One spelling of the artifact name, read by the build below and by tests.
ARTIFACT_NAME_NL = "nl-full.txt"

# The fold of the list, built from exactly the filters that stand in front of
# the splitter in the Dutch chain. Small and compiled into tantivy, it carries no
# list, so it costs nothing to hold.
_FOLD = TextAnalyzerBuilder(Tokenizer.simple()).filter(Filter.lowercase()).filter(Filter.ascii_fold()).build()


def load_constituents_nl(
    source: Path = SYSTEM_WORDLIST_NL,
    *,
    window: tuple[int, int] = (MIN_LEN, MAX_LEN),
) -> list[str]:
    """Apply recipe B to the raw Dutch word list and return the sorted constituents."""
    minimum, maximum = window
    words: set[str] = set()
    for line in source.read_text(encoding=ENCODING, errors="replace").split("\n"):
        word = line.strip()
        if not word or not word.isalpha() or not minimum <= len(word) <= maximum:
            continue
        tokens = _FOLD.analyze(word)
        # One word in, one token out. Anything else was not a word to begin with.
        if len(tokens) == 1:
            words.add(tokens[0])
    words.update(TUSSENKLANKEN)
    return sorted(words)


def artifact_path_nl() -> Path:
    """Where the Dutch artifact lives on the volume."""
    return settings().dict_dir / ARTIFACT_NAME_NL


def _digest_path(target: Path) -> Path:
    """Return the path of the digest file that belongs to an artifact."""
    return target.with_name(target.name + DIGEST_SUFFIX)


def _read_artifact(target: Path) -> list[str]:
    """Read an artifact back into the list it was written from.

    ``errors="replace"`` and never the strict read, and that is the fail closed
    contract of this module rather than a leniency (review finding CR-01). A byte
    that is not UTF-8 (bit rot, half a block, a hand edit) used to raise a
    UnicodeDecodeError before the digest could be compared, and nothing on the
    way up catches that class: report_version_drift in the lifespan let it out,
    and the container did not start, at every restart again. Replaced bytes
    change the content, so the digest comparison fails and the artifact is
    rebuilt from the source exactly like a tampered one.
    """
    return [line for line in target.read_text(encoding=ENCODING, errors="replace").split("\n") if line]


def _read_digest(digest_path: Path) -> str:
    """Read the recorded digest, with undecodable bytes as a mismatch and not a raise.

    Same reasoning as :func:`_read_artifact`: a digest file with a byte that is
    not UTF-8 is a digest that describes no list, and the answer to that is the
    rebuild path, never an exception out of the lifespan.
    """
    return digest_path.read_text(encoding=ENCODING, errors="replace").strip()


# ---------------------------------------------------------------------------
# The digest cache (D-02). Per process, at most one entry, keyed on the identity
# of the artifact on the volume: the recorded digest plus size and modification
# time, so a file edited behind an unchanged digest file still reaches the fail
# closed check. Absence is never a key. The value is the digest alone.
# ---------------------------------------------------------------------------
_CacheKey = tuple[str, str, int, int]

_CACHED_DIGESTS: dict[_CacheKey, str] = {}

_CACHE_LOCK = threading.Lock()

# How often this process really put the Dutch list into memory, by reading the
# artifact or by running the recipe.
_READ_COUNT = 0


def read_count_nl() -> int:
    """Return how often this process has read the Dutch list into memory."""
    return _READ_COUNT


def _artifact_key(target: Path, digest_path: Path) -> _CacheKey | None:
    """Return the identity of the stored artifact, or None when there is none."""
    if not target.is_file() or not digest_path.is_file():
        return None
    try:
        status = target.stat()
        recorded = _read_digest(digest_path)
    except OSError:
        return None
    if not recorded:
        return None
    return (str(target), recorded, status.st_size, status.st_mtime_ns)


def _remember(target: Path, digest_path: Path, digest: str) -> None:
    """Put the digest into the cache under the identity the artifact now has."""
    key = _artifact_key(target, digest_path)
    if key is None:
        return
    _CACHED_DIGESTS.clear()
    _CACHED_DIGESTS[key] = digest


def build_artifact_nl(source: Path = SYSTEM_WORDLIST_NL, target: Path | None = None) -> Artifact:
    """Return the Dutch list, from the artifact when it is sound, else from the recipe.

    Fail closed on the stored artifact: it is used only when the digest file next
    to it describes exactly the file that is there. Every call reads, because the
    entries are not cached; callers that only need the digest go through
    :func:`dutch_digest_for`.
    """
    if target is None:
        target = artifact_path_nl()
    digest_path = _digest_path(target)
    with _CACHE_LOCK:
        return _load_artifact(source, target, digest_path)


def _load_artifact(source: Path, target: Path, digest_path: Path) -> Artifact:
    """Read the stored artifact or run the recipe. Called with the lock held."""
    global _READ_COUNT

    if target.is_file() and digest_path.is_file():
        entries = _read_artifact(target)
        _READ_COUNT += 1
        recorded = _read_digest(digest_path)
        if recorded and recorded == wordlist_hash(entries):
            LOGGER.info(
                "dutch constituent list read from the volume, %d entries, read %d in this process",
                len(entries),
                _READ_COUNT,
            )
            _remember(target, digest_path, recorded)
            return Artifact(entries=entries, digest=recorded, rebuilt=False)
        LOGGER.warning("stored dutch constituent list does not match its digest, rebuilding it from the source")

    started = time.perf_counter()
    entries = load_constituents_nl(source)
    _READ_COUNT += 1
    digest = wordlist_hash(entries)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(entries) + "\n", encoding=ENCODING)
    digest_path.write_text(digest + "\n", encoding=ENCODING)
    LOGGER.info(
        "dutch constituent list built, %d entries in %.3f s, read %d in this process",
        len(entries),
        time.perf_counter() - started,
        _READ_COUNT,
    )
    _remember(target, digest_path, digest)
    return Artifact(entries=entries, digest=digest, rebuilt=True)


def dutch_digest_for(languages: Sequence[str]) -> str | None:
    """Return the digest of the Dutch list, or None while nl is not configured.

    Without nl nothing is touched, neither the source nor the volume. With nl the
    digest comes out of the cache as long as the artifact on the volume keeps its
    identity, and otherwise the artifact is read or built once and only its
    digest is kept.
    """
    if "nl" not in languages:
        return None
    target = artifact_path_nl()
    digest_path = _digest_path(target)
    with _CACHE_LOCK:
        key = _artifact_key(target, digest_path)
        if key is not None:
            cached = _CACHED_DIGESTS.get(key)
            if cached is not None:
                return cached
    # Read at call time rather than bound as a default, so the source can be
    # pointed elsewhere without reaching into the signature.
    return build_artifact_nl(SYSTEM_WORDLIST_NL, target).digest


def dutch_mark(languages: Sequence[str]) -> str:
    """Return the value of the Dutch mark: ``off``, or the chain version and the digest."""
    digest = dutch_digest_for(languages)
    if digest is None:
        return DUTCH_LIST_OFF
    return f"{DUTCH_CHAIN_VERSION}:{digest}"


# ---------------------------------------------------------------------------
# Measurement mode. Numbers only, never a token and never a word (T-02-14).
# ---------------------------------------------------------------------------


def measure(source: Path = SYSTEM_WORDLIST_NL) -> dict[str, float | int | str]:
    """Measure recipe B and return plain numbers."""
    source_lines = len(source.read_text(encoding=ENCODING, errors="replace").split("\n"))

    rss_before = rss_bytes()
    filter_started = time.perf_counter()
    entries = load_constituents_nl(source)
    filter_seconds = time.perf_counter() - filter_started
    rss_after = rss_bytes()

    return {
        "source_lines": source_lines,
        "entries": len(entries),
        "sha256": wordlist_hash(entries),
        "filter_seconds": round(filter_seconds, 3),
        "list_rss_growth_bytes": rss_after - rss_before,
    }


if __name__ == "__main__":  # pragma: no cover
    for key, value in measure().items():
        print(f"{key}={value}")
