"""The ratchet under decision D-04, so the promise outlives the phase that gave it.

D-04 of 2026-09-10 says an upgrade from 1.0.x to 1.1.0 leaves the index alone.
Five marks decide whether that holds, they live in
:func:`findling.index.open.expected_versions`, and
:meth:`findling.store.repo.Store.version_mismatch` compares them against what an
existing index was really built with. One of them moving is enough:
``start_rebuild_on_drift`` raises the local generation, every stored verdict goes
stale at once, and the next crawl reads every document again.

**A red test here is not a repair, it is a question for the owner.** Nothing in
this file may be adjusted to make it green again. The green way out is to leave
the mark where it is; the other way out is a decision that an upgrade rebuilds
every installed index, and that decision is not a test edit.

**What it costs, in the one figure this project measured.** The full run of
phase 10 on the m7g box took 26 h 37 min for 51.961 documents
(``docs/measurements/2026-09-vergleichsmessung-m7g/README.md``). That is the
order of magnitude every user of an existing installation would pay for a moved
mark, on their own machine, without having asked for anything but an update.

The shape is the one of ``test_lockstep_versions.py``: a promise that lives as a
test, with the sides named in every finding and a self test against a staged
sample, so that a gate whose body was deleted cannot look healthy.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from findling.index.open import expected_versions

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = BACKEND_ROOT / "Dockerfile"
PYPROJECT = BACKEND_ROOT / "pyproject.toml"

# The four stable marks of the v1.0.3 release, which is the state every user of
# an existing installation upgrades from. The fifth mark, wordlist_hash, is not
# in here on purpose: it is a digest of the German word list and is held below
# through the pin it grows out of.
GOLD_V1_0_3 = {
    "schema_version": "1",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": "0.26.0",
}

# The one mark whose value is a banner rather than a number. tantivy reports
# "tantivy v0.26.0, index_format v7", and open.py stores the banner deliberately,
# since tantivy makes no promise that its on disk format survives its own
# releases. The gold value above is therefore held inside the banner and not
# against it, and the format half gets an assertion of its own below.
TANTIVY_MARK = "tantivy_version"

# The index format of tantivy 0.26.0. It is the half of the banner that decides
# whether the files on disk can still be opened at all.
GOLD_INDEX_FORMAT = "index_format v7"

# The Debian package the German word list comes out of. wordlist_hash is a digest
# of that list, so the pin is the thing that has to hold; a version literal for
# the digest would be a number nobody could check against anything.
WNGERMAN_PIN = "wngerman=20161207-15"

# The pin the banner above grows out of. Named here because a moved pin and a
# moved mark are the same event seen from two sides.
TANTIVY_PIN = "tantivy==0.26.0"

# The five marks an index carries. A mark that disappears counts as a difference
# in Store.version_mismatch, so a set that shrank would trigger a rebuild just as
# surely as a value that changed.
ALL_MARKS = ("schema_version", "index_version", "analyzer_version", "wordlist_hash", TANTIVY_MARK)


def drift_findings(marks: Mapping[str, str]) -> list[str]:
    """Every gold mark the given set does not carry, as one sentence each.

    Fails closed: a mark that is missing altogether reads as the empty value and
    becomes a finding, because that is exactly how the store reads it too.
    """
    findings: list[str] = []
    for mark, gold in GOLD_V1_0_3.items():
        value = marks.get(mark, "")
        held = gold in value if mark == TANTIVY_MARK else value == gold
        if not held:
            findings.append(
                f"{mark} ist {value!r} statt {gold!r}; "
                f"ein Upgrade von 1.0.x wuerde jetzt einen Reindex ausloesen (D-04)"
            )
    return findings


def test_the_drift_reader_fires_on_a_staged_sample() -> None:
    """The self test of the gate below, including the shape that fails closed.

    Three staged sets: one that holds, one whose schema version moved, and one
    that lost a mark on the way. All three have to be read the way the store
    reads them, or a green run here would say nothing at all.
    """
    holding = {
        "schema_version": "1",
        "index_version": "1",
        "analyzer_version": "1",
        "tantivy_version": "tantivy v0.26.0, index_format v7",
    }
    assert drift_findings(holding) == []

    moved = drift_findings({**holding, "schema_version": "2"})
    assert len(moved) == 1, moved
    assert "schema_version" in moved[0]
    assert "'2'" in moved[0]
    assert "'1'" in moved[0]
    assert "D-04" in moved[0]

    lost = drift_findings({key: value for key, value in holding.items() if key != "analyzer_version"})
    assert len(lost) == 1, lost
    assert "analyzer_version" in lost[0]


def test_an_upgrade_from_1_0_x_would_not_trigger_a_reindex() -> None:
    """D-04 of 2026-09-10: v1.1 keeps the index of 1.0.x usable.

    The digest handed in is arbitrary, because the word list is held through its
    Debian pin in the test below rather than through a literal here.
    """
    findings = drift_findings(expected_versions("digest-egal"))
    assert findings == [], findings


def test_the_index_format_of_the_banner_holds_as_well() -> None:
    """The other half of the tantivy mark, and the half that opens the files.

    A tantivy release that kept its version string and changed the format would
    pass the comparison above and break every index in the field, so the format
    is asked for by name.
    """
    banner = expected_versions("digest-egal")[TANTIVY_MARK]
    assert GOLD_INDEX_FORMAT in banner, banner


def test_no_mark_appeared_and_none_went_missing() -> None:
    """Five marks, the same five, and the digest travels through untouched.

    A sixth mark is a rebuild for everyone just as much as a changed value is,
    and a mark that vanished is one the store counts as a difference. The digest
    is asserted as passed through so that the fifth mark stays what it claims to
    be: a statement about the word list and about nothing else.
    """
    marks = expected_versions("ein-digest")
    assert tuple(marks) == ALL_MARKS, marks
    assert marks["wordlist_hash"] == "ein-digest"
    assert expected_versions("ein-anderer")["wordlist_hash"] == "ein-anderer"


def test_the_word_list_is_held_through_its_debian_pin() -> None:
    """wordlist_hash hangs on a package, so the package is what gets pinned.

    A bump of wngerman changes the compound splitting, which changes what the
    index contains, which is the same owner question as a bumped constant. The
    pin is exact in backend/Dockerfile and it stays exact.
    """
    assert WNGERMAN_PIN in DOCKERFILE.read_text(encoding="utf-8"), WNGERMAN_PIN


def test_the_engine_is_held_through_its_exact_pin() -> None:
    """The banner is what tantivy reports, and the pin is what decides it.

    Held with two equals signs on purpose: a floor would let the resolver walk
    into a release that writes a different index format, and the first sign of
    that would be a rebuild on every installation in the field.
    """
    assert TANTIVY_PIN in PYPROJECT.read_text(encoding="utf-8"), TANTIVY_PIN
