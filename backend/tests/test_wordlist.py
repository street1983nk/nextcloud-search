"""Recipe A, asserted rather than trusted.

The constituent list is not a spell checker dictionary and the difference is the
whole point. Four recipes were measured against sixteen real compounds; the
obvious one, nouns only with linking forms appended and the letters folded,
scored seven of sixteen and produced real mis-splits. The recipe that scored
fourteen is the one encoded here, and these tests are what keeps a later
simplification from quietly swapping it back.

Three properties carry the rest of the phase:

* the length window, because an entry longer than the window is itself a
  compound and a compound in the list is never split,
* the umlauts, because the splitter compares the raw token against the list and
  a folded list would silently never match,
* the digest, because a changed list changes the tokenisation, and a changed
  tokenisation without a visible reindex means silently different result lists
  (T-02-11).

The system list lives at /usr/share/dict/ngerman and exists only inside the
Debian based image, so every test here builds its own miniature source. That is
deliberate: these tests assert the recipe, not the Debian package. The package is
measured by scripts/dev/measure_wordlist.sh in a throwaway container.
"""

from pathlib import Path

import pytest

from findling.index.wordlist import (
    FUGEN,
    MAX_LEN,
    MIN_LEN,
    build_artifact,
    load_constituents,
    wordlist_hash,
)

# A miniature stand in for /usr/share/dict/ngerman. Mixed case like the original,
# with one entry per class the filter has to decide about.
SOURCE_WORDS = (
    "Abschluss",  # noun inside the window
    "Frist",  # noun inside the window
    "Kündigung",  # umlaut, must survive unfolded
    "Kündigungsfrist",  # 15 characters, above the window: itself a compound
    "Vertrag",
    "Genehmigung",
    "Grundstück",
    "Verkehr",
    "Rindfleisch",
    "Etikettierung",
    "Straße",  # sharp s is a letter, the entry stays
    "straße",  # same word lowercase: has to collapse into one entry
    "und",  # 3 characters, below the window
    "ab",  # below the window
    "suchen",  # verb: recipe A keeps all words, not only nouns
    "abrechnen",  # verb
    "B2B",  # not alphabetic
    "e-Mail",  # not alphabetic
)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Write the miniature word list and return its path."""
    path = tmp_path / "ngerman"
    path.write_text("\n".join(SOURCE_WORDS) + "\n", encoding="utf-8")
    return path


def test_the_window_and_the_alphabetic_test_decide_what_stays(source: Path) -> None:
    entries = load_constituents(source)

    assert "abschluss" in entries
    assert "genehmigung" in entries
    # Above the window. Keeping it would make the splitter swallow the whole
    # token, and "Frist" would not find the document.
    assert "kündigungsfrist" not in entries
    assert "und" not in entries
    assert "ab" not in entries
    assert "b2b" not in entries
    assert "e-mail" not in entries


def test_every_kept_word_lies_inside_the_window(source: Path) -> None:
    entries = load_constituents(source)

    words = [entry for entry in entries if entry not in FUGEN]
    assert words
    assert all(MIN_LEN <= len(word) <= MAX_LEN for word in words)


def test_recipe_a_keeps_all_words_not_only_nouns(source: Path) -> None:
    entries = load_constituents(source)

    # This is the measured difference between fourteen of sixteen and twelve.
    assert "suchen" in entries
    assert "abrechnen" in entries


def test_the_linking_elements_are_entries_of_their_own(source: Path) -> None:
    entries = load_constituents(source)

    # Without them the chain of matches breaks between the parts and the whole
    # compound stays unsplit. They are shorter than MIN_LEN, so they can only get
    # in as an explicit addition.
    assert set(FUGEN) <= set(entries)
    assert FUGEN == ("s", "es", "n", "en", "er", "ns")


def test_umlauts_survive_because_the_splitter_compares_raw_tokens(source: Path) -> None:
    entries = load_constituents(source)

    assert "kündigung" in entries
    assert "grundstück" in entries
    assert "straße" in entries
    assert "kundigung" not in entries
    assert "grundstueck" not in entries


def test_case_collapses_into_a_single_entry(source: Path) -> None:
    entries = load_constituents(source)

    assert entries.count("straße") == 1


def test_the_output_is_sorted_and_free_of_duplicates(source: Path) -> None:
    entries = load_constituents(source)

    assert entries == sorted(entries)
    assert len(entries) == len(set(entries))


def test_the_digest_is_stable_for_the_same_input(source: Path) -> None:
    first = wordlist_hash(load_constituents(source))
    second = wordlist_hash(load_constituents(source))

    assert first == second
    assert len(first) == 64


def test_the_digest_changes_when_the_list_changes(source: Path) -> None:
    before = wordlist_hash(load_constituents(source))

    source.write_text("\n".join([*SOURCE_WORDS, "Sitzung"]) + "\n", encoding="utf-8")
    after = wordlist_hash(load_constituents(source))

    # T-02-11: a changed list has to be visible, because it changes every token
    # the index and the query parser produce.
    assert before != after


def test_the_nouns_variant_keeps_only_capitalised_source_entries(source: Path) -> None:
    entries = load_constituents(source, variant="nouns")

    assert "abschluss" in entries
    assert "genehmigung" in entries
    assert "suchen" not in entries
    assert "abrechnen" not in entries


def test_the_window_is_unchanged_in_the_nouns_variant(source: Path) -> None:
    entries = load_constituents(source, variant="nouns")

    assert "kündigungsfrist" not in entries
    assert set(FUGEN) <= set(entries)


def test_the_first_build_writes_the_artifact_and_its_digest(source: Path, tmp_path: Path) -> None:
    target = tmp_path / "volume" / "dict" / "de.txt"

    artifact = build_artifact(source, target)

    assert artifact.rebuilt is True
    assert target.is_file()
    assert artifact.digest == wordlist_hash(load_constituents(source))
    assert target.read_text(encoding="utf-8").split("\n")[0] == artifact.entries[0]


def test_a_second_call_reads_the_artifact_instead_of_the_source(source: Path, tmp_path: Path) -> None:
    target = tmp_path / "dict" / "de.txt"
    first = build_artifact(source, target)

    # Removing the source proves the second call never touched it. In the
    # container the source is present but reading and filtering it costs a tenth
    # of a second on every start for no gain.
    source.write_text("Unsinn\n", encoding="utf-8")
    second = build_artifact(source, target)

    assert second.rebuilt is False
    assert second.digest == first.digest
    assert second.entries == first.entries


def test_a_tampered_artifact_is_rebuilt_from_the_source(source: Path, tmp_path: Path) -> None:
    target = tmp_path / "dict" / "de.txt"
    first = build_artifact(source, target)

    target.write_text("etwasanderes\n", encoding="utf-8")
    second = build_artifact(source, target)

    # Fail closed: the digest on disk no longer describes the file next to it, so
    # the file is not trusted and the recipe runs again.
    assert second.rebuilt is True
    assert second.entries == first.entries
    assert second.digest == first.digest


def test_the_artifact_round_trips_umlauts(source: Path, tmp_path: Path) -> None:
    target = tmp_path / "dict" / "de.txt"
    build_artifact(source, target)

    reloaded = build_artifact(source, target)

    assert "kündigung" in reloaded.entries
    assert "straße" in reloaded.entries


def test_the_two_variants_produce_different_digests(source: Path, tmp_path: Path) -> None:
    full = build_artifact(source, tmp_path / "full" / "de.txt", variant="full")
    nouns = build_artifact(source, tmp_path / "nouns" / "de.txt", variant="nouns")

    # The variant is part of the tokenisation, so it has to be part of what the
    # metadata table compares against.
    assert full.digest != nouns.digest
