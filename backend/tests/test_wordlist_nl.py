"""Recipe B 4-14 for Dutch, asserted rather than trusted.

The Dutch constituent list is the sibling of the German one and differs from it
in exactly one load bearing way: it is folded. The Dutch chain folds in front of
the splitter (the fold position measured in phase 17 stays where it is), so the
list has to lie in the folded form, or the flat spelling "coordinatiecentrum"
would stay whole while the accented one comes apart. Folding happens with
tantivy's own ascii_fold and nothing else, because the list and the token have
to be folded by the same code.

The other properties are the German ones: a window on the unfolded length,
linking elements as entries of their own, an artifact on the volume that is
trusted only when its digest describes it, and a cache that remembers the
digest and never the list (D-02). On top of that the language gate: without nl
in the configured languages nothing is read at all.

The system list lives at /usr/share/dict/dutch and exists only inside the image,
so every test here builds its own miniature source.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from findling.config import settings
from findling.index import wordlist_nl
from findling.index.wordlist import DIGEST_SUFFIX, wordlist_hash
from findling.index.wordlist_nl import (
    DUTCH_CHAIN_VERSION,
    DUTCH_LIST_OFF,
    MAX_LEN,
    MIN_LEN,
    TUSSENKLANKEN,
    artifact_path_nl,
    build_artifact_nl,
    dutch_digest_for,
    dutch_mark,
    load_constituents_nl,
    read_count_nl,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

# A miniature stand in for /usr/share/dict/dutch, one entry per class the recipe
# has to decide about.
SOURCE_LINES = (
    "Belasting",  # capitalised, inside the window, lands lowercase
    "gemeente",  # inside the window
    "overeenkomst",  # 12 characters, inside the window
    "coördinatie",  # trema, has to land folded
    "verantwoordelijk",  # 16 characters, above the window
    "aansprakelijkh",  # exactly 14 characters, the upper end is inclusive
    "aansprakelijkhe",  # 15 characters, one above the window
    "plan",  # exactly 4 characters, the lower end is inclusive
    "wet",  # 3 characters, below the window
    "B2B",  # not alphabetic
    "in het bijzonder",  # a line with spaces: no single word may come out of it
    "zorg-verzekering",  # not alphabetic
    "",  # an empty line
)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Write the miniature word list and return its path."""
    path = tmp_path / "dutch"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(SOURCE_LINES) + "\n")
    return path


@pytest.fixture
def storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A volume the settings point at, with the settings cache cleared on both sides."""
    root = tmp_path / "volume"
    root.mkdir(parents=True)
    monkeypatch.setenv("APP_PERSISTENT_STORAGE", str(root))
    settings.cache_clear()
    yield root
    settings.cache_clear()


def test_the_window_and_the_alphabetic_test_decide_what_stays(source: Path) -> None:
    entries = load_constituents_nl(source)

    assert "gemeente" in entries
    assert "overeenkomst" in entries
    assert "plan" in entries, "the lower end of the window is inclusive"
    assert "aansprakelijkh" in entries, "the upper end of the window is inclusive"
    assert "aansprakelijkhe" not in entries
    assert "verantwoordelijk" not in entries
    assert "wet" not in entries
    assert "b2b" not in entries
    assert "zorgverzekering" not in entries
    assert "" not in entries
    words = [entry for entry in entries if entry not in TUSSENKLANKEN]
    assert all(MIN_LEN <= len(word) <= MAX_LEN for word in words)


def test_the_window_applies_to_the_unfolded_length(tmp_path: Path) -> None:
    # Measured that way: the window reads the word as it stands in the source,
    # and a letter with a trema counts as one character.
    path = tmp_path / "dutch"
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("coördinatiecen\n")  # 14 characters unfolded
    assert load_constituents_nl(path) == sorted(["coordinatiecen", *TUSSENKLANKEN])


def test_the_source_is_read_line_by_line(source: Path) -> None:
    entries = load_constituents_nl(source)

    # The Debian source carries 4380 lines with spaces. Splitting on whitespace
    # would turn them into single words the list never contained.
    assert "bijzonder" not in entries
    assert "in het bijzonder" not in entries


def test_the_list_is_folded_by_the_engine(source: Path) -> None:
    entries = load_constituents_nl(source)

    assert "coordinatie" in entries
    assert "coördinatie" not in entries
    assert "belasting" in entries
    assert "Belasting" not in entries


def test_the_linking_elements_are_entries_of_their_own(source: Path) -> None:
    entries = load_constituents_nl(source)

    assert TUSSENKLANKEN == ("s", "e", "en")
    assert set(TUSSENKLANKEN) <= set(entries)
    assert entries == sorted(set(entries))


def test_the_first_build_writes_the_artifact_and_its_digest(source: Path, tmp_path: Path) -> None:
    target = tmp_path / "dict" / "nl-full.txt"

    artifact = build_artifact_nl(source, target)

    assert artifact.rebuilt is True
    assert target.is_file()
    assert artifact.digest == wordlist_hash(load_constituents_nl(source))
    assert target.with_name(target.name + DIGEST_SUFFIX).read_text(encoding="utf-8").strip() == artifact.digest


def test_a_tampered_artifact_is_rebuilt_from_the_source(source: Path, tmp_path: Path) -> None:
    target = tmp_path / "dict" / "nl-full.txt"
    first = build_artifact_nl(source, target)

    target.write_text("ietsanders\n", encoding="utf-8")
    second = build_artifact_nl(source, target)

    # Fail closed: the digest on disk no longer describes the file next to it.
    assert second.rebuilt is True
    assert second.entries == first.entries
    assert second.digest == first.digest


def test_an_artifact_that_is_not_utf8_is_rebuilt_instead_of_raising(source: Path, tmp_path: Path) -> None:
    """Review finding CR-01: undecodable bytes are one more shape of a broken artifact.

    The strict read raised a UnicodeDecodeError in front of the digest
    comparison, nothing on the way up to the lifespan caught that class, and the
    container did not start, at every restart again. Replaced bytes change the
    content, so the digest comparison fails and the rebuild path runs.
    """
    target = tmp_path / "dict" / "nl-full.txt"
    first = build_artifact_nl(source, target)

    target.write_bytes(b"\xff\xfe\x00kaputt\n")
    second = build_artifact_nl(source, target)

    assert second.rebuilt is True
    assert second.entries == first.entries
    assert second.digest == first.digest
    assert target.read_text(encoding="utf-8").split() == first.entries


def test_a_digest_file_that_is_not_utf8_is_rebuilt_instead_of_raising(source: Path, tmp_path: Path) -> None:
    """The same for the file next to it: a digest that describes no list is a mismatch."""
    target = tmp_path / "dict" / "nl-full.txt"
    first = build_artifact_nl(source, target)
    digest_path = target.with_name(target.name + DIGEST_SUFFIX)

    digest_path.write_bytes(b"\xff\xfe\x00kaputt\n")
    second = build_artifact_nl(source, target)

    assert second.rebuilt is True
    assert second.digest == first.digest
    assert digest_path.read_text(encoding="utf-8").strip() == first.digest


def test_the_mark_survives_undecodable_bytes_on_the_volume(
    source: Path, storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The path the lifespan takes: dutch_mark over the cache key, then the build.

    Both files are broken at once, so the cache key read and the fail closed
    check each meet a byte that is not UTF-8. The answer is the digest of the
    recipe, never an exception.
    """
    del storage
    monkeypatch.setattr(wordlist_nl, "SYSTEM_WORDLIST_NL", source)
    expected = dutch_digest_for(("de", "en", "nl"))
    target = artifact_path_nl()

    target.write_bytes(b"\xff\xfe\x00kaputt\n")
    target.with_name(target.name + DIGEST_SUFFIX).write_bytes(b"\xc3\x28\n")

    assert dutch_mark(("de", "en", "nl")) == f"{DUTCH_CHAIN_VERSION}:{expected}"


def test_the_cache_never_answers_for_a_missing_artifact(source: Path, tmp_path: Path) -> None:
    target = tmp_path / "dict" / "nl-full.txt"
    first = build_artifact_nl(source, target)

    target.unlink()
    target.with_name(target.name + DIGEST_SUFFIX).unlink()
    reads = read_count_nl()
    second = build_artifact_nl(source, target)

    assert read_count_nl() > reads
    assert second.rebuilt is True
    assert second.digest == first.digest
    assert target.is_file()


def test_the_artifact_lives_on_the_volume(storage: Path) -> None:
    assert artifact_path_nl() == storage / "dict" / "nl-full.txt"


def test_the_digest_is_read_once_per_process(source: Path, storage: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(wordlist_nl, "SYSTEM_WORDLIST_NL", source)
    reads = read_count_nl()

    first = dutch_digest_for(("de", "en", "nl"))
    second = dutch_digest_for(("de", "en", "nl"))

    assert read_count_nl() == reads + 1
    assert first == second == wordlist_hash(load_constituents_nl(source))
    assert artifact_path_nl().is_file()


def test_the_list_is_not_held_after_the_digest_is_known(
    source: Path, storage: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(wordlist_nl, "SYSTEM_WORDLIST_NL", source)

    digest = dutch_digest_for(("de", "en", "nl"))

    # D-02: the search side needs the digest, not the entries, and the entries
    # are roughly 19.6 MB of Python strings the allocator would never hand back.
    held_lists = [
        name for name, value in vars(wordlist_nl).items() if isinstance(value, list) and len(value) > len(TUSSENKLANKEN)
    ]
    assert held_lists == []
    cached = vars(wordlist_nl)["_CACHED_DIGESTS"]
    assert digest in cached.values()
    assert all(isinstance(value, str) for value in cached.values())


def test_without_dutch_nothing_is_read(storage: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(wordlist_nl, "SYSTEM_WORDLIST_NL", tmp_path / "gibt-es-nicht")
    reads = read_count_nl()

    assert dutch_digest_for(("de", "en")) is None
    assert dutch_mark(("de", "en")) == DUTCH_LIST_OFF == "off"
    assert read_count_nl() == reads
    assert not artifact_path_nl().exists()


def test_the_mark_carries_the_chain_version(source: Path, storage: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(wordlist_nl, "SYSTEM_WORDLIST_NL", source)

    digest = dutch_digest_for(("de", "en", "nl"))

    assert DUTCH_CHAIN_VERSION == 1
    assert dutch_mark(("de", "en", "nl")) == f"1:{digest}"
