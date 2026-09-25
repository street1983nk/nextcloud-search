"""The ratchet under decision D-04, so the promise outlives the phase that gave it.

D-04 of 2026-09-10 says an upgrade from 1.0.x to 1.1.0 leaves the index alone,
and since 2026-09-21 the same five values also carry the jump from 1.1.x to
1.2.0: the filter and sort work of phase 13 and the engine work of phase 14
moved none of them. The promise is therefore held over two minor jumps and no
longer over one.
Six marks decide whether that holds since 2026-09-24, they live in
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

from findling.index.open import LANGUAGES_MARK, expected_versions

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = BACKEND_ROOT / "Dockerfile"
PYPROJECT = BACKEND_ROOT / "pyproject.toml"

# The measurement script that names the engine of a run in its own output. It is
# the second place in the tree that spells the pin out, and until the audit of
# 2026-09-23 (M-17-06) it was the only one no test looked at: plan 17-08 moved
# the pin and left this line on 0.26.0, so the script kept printing the wrong
# engine as the provenance of every chain measurement.
MEASURE_CHAINS = BACKEND_ROOT.parent / "scripts" / "dev" / "measure_chains.sh"

# The index format both pinned tantivy releases report. It is the half of the
# banner that decides whether the files on disk can still be opened at all, and
# since the owner decision E-17-7 option a of 2026-09-23 it is also the half the
# store compares. Measured on 2026-09-23, four ways: 0.26.0 and 0.26.2 both
# report "index_format v7"; an index written by one opens and answers under the
# other, and the same test runs backwards, which keeps the way back out of a
# failed upgrade open; the tokenisation of seven chains over 32 words, 224 lines
# of output, is diff equal between them; and cp313 wheels exist for aarch64 and
# for x86_64.
#
# What the assurance still claims: the files on disk stay readable. What it no
# longer claims: the same release. The part given up, a changed tokenisation
# behind an unchanged format, is held by backend/tests/test_analyzer.py and
# backend/tests/test_language_analyzers.py instead.
GOLD_INDEX_FORMAT = "index_format v7"

# The four stable marks of the 1.0.x and the 1.1.x releases, which is the state
# every user of an existing installation upgrades from. The fifth mark,
# wordlist_hash, is not in here on purpose: it is a digest of the German word
# list and is held below through the pin it grows out of.
#
# The values did not move when 1.1.0 was published and they did not move for
# 1.2.0 either, and that is what makes them worth more than they were: a value
# that has stood over two minor jumps is a stronger statement than one that has
# stood over a single one. Whoever moves one now breaks the index of every
# installation of two release lines and not of one.
GOLD_V1_0_AND_V1_1 = {
    "schema_version": "1",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": GOLD_INDEX_FORMAT,
}

# The one mark whose value is a banner rather than a number. tantivy reports
# "tantivy v0.26.0, index_format v7", and open.py stores the banner deliberately,
# since tantivy makes no promise that its on disk format survives its own
# releases. The gold value above is therefore held inside the banner and not
# against it, and the format half gets an assertion of its own below.
TANTIVY_MARK = "tantivy_version"

# The factory setting, and what the sixth mark reads on an installation that
# never touched FINDLING_LANGUAGES. It is a literal and not an import of
# DEFAULT_LANGUAGES on purpose: this file holds what a release produces against a
# value written down by hand, and a gold value that follows the code it guards
# guards nothing.
GOLD_LANGUAGES = "de,en"

# The Debian package the German word list comes out of. wordlist_hash is a digest
# of that list, so the pin is the thing that has to hold; a version literal for
# the digest would be a number nobody could check against anything.
WNGERMAN_PIN = "wngerman=20161207-15"

# The Debian package the Dutch word list comes out of, held for the same reason:
# wordlist_hash_nl is a digest of that list. The epoch 1: belongs to the version.
WDUTCH_PIN = "wdutch=1:2.20.19+1-3"

# The pin the banner above grows out of. Named here because a moved pin and a
# moved mark are the same event seen from two sides. The patch number may move
# with a decision behind it; the format half above may not.
#
# It walked from 0.26.0 to 0.26.2 on 2026-09-23 in plan 17-08, under the owner
# decision E-17-7 option a of the same day, and it walked only after plan 17-07
# had loosened the comparison rule, so that the loosening stayed provable on its
# own. GOLD_V1_0_AND_V1_1["tantivy_version"] did not walk with it and must not:
# it is GOLD_INDEX_FORMAT, that is "index_format v7", and v7 is what both
# releases report. A pin that moves while the format half holds is the one shape
# of this change that costs no installation in the field a rebuild.
TANTIVY_PIN = "tantivy==0.26.2"

# The second gold table, and the reason it stands beside the first one instead of
# replacing it.
#
# On 2026-09-23 the owner answered the four decisions E-17-1, E-17-2, E-17-3 and
# E-17-4 with option a each. Option a of E-17-2 is the one that costs a mark: the
# schema carries all six body fields at all times, so body_es, body_it, body_nl
# and body_pt were added on 2026-09-24 and schema_version walked from 1 to 2.
#
# What the mark means has not changed: a value that moved makes
# Store.version_mismatch report a difference, start_rebuild_on_drift raises the
# local generation, and the index of the installation is built again. What has
# changed is that this one is a release with a decision behind it and not an
# accident. The table above stays where it is as the witness of what an
# installation of 1.0.x, 1.1.x or 1.2.x carries on disk; this one is what the
# running code produces, and the gate below holds the distance between the two
# at exactly one step.
#
# The other four marks did not move with it and must not: index_version is the
# on disk layout, analyzer_version is the tokenisation, the tantivy banner still
# reports index_format v7, and the word list is untouched. A second mark moving
# in the same release would make the reason for this one unprovable.
GOLD_V1_3 = {
    "schema_version": "2",
    "index_version": "1",
    "analyzer_version": "1",
    "tantivy_version": GOLD_INDEX_FORMAT,
    LANGUAGES_MARK: GOLD_LANGUAGES,
}

# The six marks an index carries. A mark that disappears counts as a difference
# in Store.version_mismatch, so a set that shrank would trigger a rebuild just as
# surely as a value that changed.
#
# The sixth one joined on 2026-09-24, under owner decision E-17-4 option a of
# 2026-09-23: the language set becomes a version mark, normalised into schema
# field order, so that switching a language on is a state the code can see.
#
# It is the one mark that is deliberately NOT seeded. findling.store.repo skips
# it in _seed_meta and reads its absence as legacy rather than as a difference,
# because no release up to 1.2.0 could write a body field outside ("de", "en").
# A sixth mark would otherwise be a rebuild for every installation in the field,
# which is exactly what the ratchet above exists to prevent; here it is a rebuild
# for the installations that switch a language on, and for no others.
ALL_MARKS = (
    "schema_version",
    "index_version",
    "analyzer_version",
    "wordlist_hash",
    TANTIVY_MARK,
    LANGUAGES_MARK,
)


def drift_findings(marks: Mapping[str, str], gold_marks: Mapping[str, str] = GOLD_V1_0_AND_V1_1) -> list[str]:
    """Every gold mark the given set does not carry, as one sentence each.

    Fails closed: a mark that is missing altogether reads as the empty value and
    becomes a finding, because that is exactly how the store reads it too.

    The table to read against became a parameter on 2026-09-24, with the default
    it always had, so that the same reader serves both generations. One reader
    and not two: a second copy of this loop for GOLD_V1_3 would be a second way
    of comparing, and the day somebody corrected one of them the other would
    still be green.
    """
    findings: list[str] = []
    for mark, gold in gold_marks.items():
        value = marks.get(mark, "")
        # Do not "unify" this line. The tantivy gold value is the index_format
        # half, and asking for it as a substring of the banner is exactly what
        # Store.version_mismatch does since E-17-7 option a; an equality here
        # would put the patch number back into the gate.
        held = gold in value if mark == TANTIVY_MARK else value == gold
        if not held:
            findings.append(
                f"{mark} ist {value!r} statt {gold!r}; "
                f"ein Upgrade von 1.0.x oder 1.1.x wuerde jetzt einen Reindex ausloesen (D-04)"
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


def test_a_patch_bump_with_the_same_index_format_is_no_drift() -> None:
    """The fourth staged set: another patch number, the same format half.

    This is the whole point of owner decision E-17-7 option a. A tantivy patch
    release that keeps index_format v7 must read as no drift at all, or every
    installation in the field pays a full crawl for a number nobody looked at.
    """
    holding = {
        "schema_version": "1",
        "index_version": "1",
        "analyzer_version": "1",
        "tantivy_version": "tantivy v0.26.2, index_format v7",
    }

    findings = drift_findings(holding)

    assert findings == [], findings


def test_a_changed_index_format_is_still_drift() -> None:
    """The fifth staged set: the red state the loosening keeps.

    A release that moves the format moves the files on disk, and that is the one
    tantivy change this gate must still see.
    """
    changed = {
        "schema_version": "1",
        "index_version": "1",
        "analyzer_version": "1",
        "tantivy_version": "tantivy v0.27.0, index_format v8",
    }

    findings = drift_findings(changed)

    assert len(findings) == 1, findings
    assert TANTIVY_MARK in findings[0]


def test_an_upgrade_from_1_0_x_to_1_2_x_now_moves_exactly_one_mark() -> None:
    """The ratchet turned around on 2026-09-24, and it was turned and not filed off.

    Until v1.2 this test read ``findings == []`` and carried D-04: an upgrade
    left the index of every installation alone. It cannot read that any more,
    because v1.3 adds four body fields to the schema and schema_version walked
    from 1 to 2 for it, under the owner decisions E-17-1 to E-17-4 of
    2026-09-23, all of them option a.

    So the question the file header demands was asked and answered, and the
    answer is written down instead of the test being made green: the promise is
    given up deliberately, for one release, for one mark. The test now holds the
    price of that decision rather than its absence, and it stays a gate, because
    a second moving mark would be a second reindex reason nobody decided on and
    would fail right here.

    The digest handed in is arbitrary, because the word list is held through its
    Debian pin in the test below rather than through a literal here.
    """
    findings = drift_findings(expected_versions("digest-egal", GOLD_LANGUAGES))

    assert len(findings) == 1, findings
    assert "schema_version" in findings[0], findings
    assert "'2'" in findings[0], findings
    assert "'1'" in findings[0], findings


def test_an_index_built_by_this_code_carries_the_marks_of_v1_3() -> None:
    """The new floor. What v1.2 held against GOLD_V1_0_AND_V1_1, v1.3 holds against this.

    Without it the release would have a moved mark and no table to hold the moved
    state against, which is a ratchet that was opened and never closed again.
    """
    findings = drift_findings(expected_versions("digest-egal", GOLD_LANGUAGES), GOLD_V1_3)

    assert findings == [], findings


def test_the_schema_mark_moved_by_exactly_one_step() -> None:
    """One step, and why two would be a finding rather than a bigger step.

    A skipped step is a schema nobody ever shipped: there is no installation in
    the field carrying it, so no upgrade path leads out of it and no measurement
    can be taken over it. The reindex of 1 to 2 is a route somebody can walk and
    can be walked again in a test; a jump from 1 to 3 would leave the state 2
    described in this repository and existing nowhere, and every later statement
    about "the previous schema" would be about a thing that never was.

    The other marks are held at a standstill in the same breath, because the one
    step is only cheap as long as it is the only one.
    """
    step = int(GOLD_V1_3["schema_version"]) - int(GOLD_V1_0_AND_V1_1["schema_version"])

    assert step == 1, step
    for mark in ("index_version", "analyzer_version", TANTIVY_MARK):
        assert GOLD_V1_3[mark] == GOLD_V1_0_AND_V1_1[mark], mark


def test_the_index_format_of_the_banner_holds_as_well() -> None:
    """The other half of the tantivy mark, and the half that opens the files.

    A tantivy release that kept its version string and changed the format would
    pass the comparison above and break every index in the field, so the format
    is asked for by name.
    """
    banner = expected_versions("digest-egal", GOLD_LANGUAGES)[TANTIVY_MARK]
    assert GOLD_INDEX_FORMAT in banner, banner


def test_no_mark_appeared_and_none_went_missing() -> None:
    """Six marks, the same six, and the digest travels through untouched.

    A seventh mark is a rebuild for everyone just as much as a changed value is,
    and a mark that vanished is one the store counts as a difference. The digest
    is asserted as passed through so that the fourth mark stays what it claims to
    be: a statement about the word list and about nothing else.

    The sixth arrived on 2026-09-24 and is the one exception this file records
    rather than forbids: it costs no installation in the field a rebuild, because
    its absence is read as legacy instead of as a difference. The proof of that
    lives where the reading happens, in backend/tests/test_store_metadata.py.
    """
    marks = expected_versions("ein-digest", GOLD_LANGUAGES)
    assert tuple(marks) == ALL_MARKS, marks
    assert marks["wordlist_hash"] == "ein-digest"
    assert expected_versions("ein-anderer", GOLD_LANGUAGES)["wordlist_hash"] == "ein-anderer"


def test_the_word_list_is_held_through_its_debian_pin() -> None:
    """wordlist_hash hangs on a package, so the package is what gets pinned.

    A bump of wngerman changes the compound splitting, which changes what the
    index contains, which is the same owner question as a bumped constant. The
    pin is exact in backend/Dockerfile and it stays exact.
    """
    assert WNGERMAN_PIN in DOCKERFILE.read_text(encoding="utf-8"), WNGERMAN_PIN


def test_the_dutch_word_list_is_held_through_its_debian_pin() -> None:
    """wordlist_hash_nl hangs on wdutch, so wdutch is what gets pinned.

    The Dutch mark is a digest of the list this package ships. A bump of wdutch
    changes how Dutch compounds fall apart and therefore what the index holds
    for every Dutch document. The pin is exact in backend/Dockerfile, epoch
    included, and it stays exact.
    """
    assert WDUTCH_PIN in DOCKERFILE.read_text(encoding="utf-8"), WDUTCH_PIN


def test_the_engine_is_held_through_its_exact_pin() -> None:
    """The banner is what tantivy reports, and the pin is what decides it.

    Held with two equals signs on purpose: a floor would let the resolver walk
    into a release that writes a different index format, and the first sign of
    that would be a rebuild on every installation in the field.
    """
    assert TANTIVY_PIN in PYPROJECT.read_text(encoding="utf-8"), TANTIVY_PIN


def test_the_measurement_script_names_the_pinned_engine() -> None:
    """The provenance line of a chain measurement names the engine that ran it.

    scripts/dev/measure_chains.sh prints its TANTIVY line as the provenance of
    the run, and the provenance of the measurements is what the whole chain
    argument of phase 17 rests on. A pin that moves in pyproject.toml and not
    here leaves the reports naming an engine nobody measured with.
    """
    script = MEASURE_CHAINS.read_text(encoding="utf-8")

    assert TANTIVY_PIN in script, (
        f"{MEASURE_CHAINS.name} does not name {TANTIVY_PIN}; the pin moved in pyproject.toml and the "
        "provenance line of every chain measurement stayed behind"
    )
