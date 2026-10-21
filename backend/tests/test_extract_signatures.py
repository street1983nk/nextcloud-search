"""The attack signatures of ZIP files and Office packages (D-36-17, 36-WORTLAUT.md A3, plan 36-08).

Pure tests in this process, without the sandbox: the corpus of
test_phase36_hostile_corpus.py runs the same families through the real child.
Here every edge of every rule stands on its own:

* **zip_ratio, two steps (answer O12).** A member from ARCHIVE_RATIO_MIN_BYTES
  on with a ratio over ARCHIVE_MAX_RATIO (100) up to and including
  ARCHIVE_MALICIOUS_RATIO (1000) stays archive_limit; only above that number
  is the file blocked as malicious. The ratios are built through lying
  declarations of a stored member where an exact number is needed, and every
  test reads the ratio back from the bytes (file_size over compress_size)
  instead of believing the generator.
* **zip_overlap on every level (answer O2).** The refusal of zipfile and its
  warning about two entries at one local header, outside and inside.
* **zip_traversal on the raw name (answer O5).** Read from the name as the
  directory carries it, before any member is read, never from the cleaned
  display name.
* **What stays a limit (answer O7).** Depth, entry count and the declared sum
  keep archive_limit.
"""

from __future__ import annotations

import inspect
import io
import warnings
import zipfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling import config
from findling.config import (
    ARCHIVE_MALICIOUS_RATIO,
    ARCHIVE_MAX_RATIO,
    ARCHIVE_RATIO_MIN_BYTES,
    settings,
)
from findling.extract import archive
from findling.extract.archive import extract_zip
from findling.extract.errors import ExtractionOutcome, Reason, State
from hostile import (
    ATTACK_RATIO,
    Member,
    _same_offset_twice,
    build_zip,
    text_member,
    zip_depth_three,
    zip_entries,
    zip_moderate_ratio_member,
    zip_overlap,
    zip_ratio_member,
    zip_traversal,
)


@pytest.fixture(autouse=True)
def _fresh_settings() -> Iterator[None]:
    settings.cache_clear()
    yield
    settings.cache_clear()


def _run(tmp_path: Path, raw: bytes) -> tuple[ExtractionOutcome, list[str]]:
    """extract_zip in this process, and what stands next to the job file afterwards."""
    target = tmp_path / "job-8.part"
    target.write_bytes(raw)
    outcome = extract_zip(str(target))
    return outcome, sorted(path.name for path in tmp_path.iterdir())


def _blocked(outcome: ExtractionOutcome, detail: str) -> None:
    assert (outcome.state, outcome.reason, outcome.detail) == (State.SKIPPED, Reason.BLOCKED_MALICIOUS, detail)
    assert outcome.text == ""


def _limit(outcome: ExtractionOutcome) -> None:
    assert (outcome.state, outcome.reason, outcome.detail) == (State.SKIPPED, Reason.ARCHIVE_LIMIT, None)


def _ratio_of(raw: bytes, name: str) -> float:
    """The ratio archive.py judges, read back from the directory of the bytes."""
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        info = check.getinfo(name)
    return info.file_size / max(info.compress_size, 1)


def _declared(packed: int, declared: int) -> bytes:
    """A stored member of ``packed`` bytes that declares ``declared`` bytes, next to a plain member."""
    return build_zip([text_member("vornwort"), Member(b"dicht.bin", b"\x01" * packed, declared=declared)])


# -- the owner's number ------------------------------------------------------------


def test_the_corpus_and_the_code_carry_the_same_owner_number() -> None:
    assert ATTACK_RATIO == config.ARCHIVE_MALICIOUS_RATIO == 1000
    assert ARCHIVE_MAX_RATIO < ARCHIVE_MALICIOUS_RATIO


# -- zip_ratio, two steps (O12) ------------------------------------------------------


def test_a_member_just_over_the_first_ratio_is_an_archive_limit(tmp_path: Path) -> None:
    raw = _declared(10_383, 101 * 10_383)
    assert _ratio_of(raw, "dicht.bin") == 101
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        assert check.getinfo("dicht.bin").file_size >= ARCHIVE_RATIO_MIN_BYTES + 1

    _limit(_run(tmp_path, raw)[0])


def test_a_member_of_about_150_to_1_is_an_archive_limit(tmp_path: Path) -> None:
    raw = zip_moderate_ratio_member()
    assert ARCHIVE_MAX_RATIO < _ratio_of(raw, "dicht.bin") < 200

    _limit(_run(tmp_path, raw)[0])


def test_a_member_just_under_the_attack_ratio_of_deflate_is_an_archive_limit(tmp_path: Path) -> None:
    raw = zip_moderate_ratio_member(950)
    assert 900 < _ratio_of(raw, "dicht.bin") <= ARCHIVE_MALICIOUS_RATIO

    _limit(_run(tmp_path, raw)[0])


def test_a_member_exactly_at_the_attack_ratio_is_an_archive_limit(tmp_path: Path) -> None:
    raw = _declared(1_049, ARCHIVE_MALICIOUS_RATIO * 1_049)
    assert _ratio_of(raw, "dicht.bin") == ARCHIVE_MALICIOUS_RATIO

    _limit(_run(tmp_path, raw)[0])


def test_a_member_one_byte_over_the_attack_ratio_is_blocked(tmp_path: Path) -> None:
    raw = _declared(1_049, ARCHIVE_MALICIOUS_RATIO * 1_049 + 1)
    assert _ratio_of(raw, "dicht.bin") > ARCHIVE_MALICIOUS_RATIO

    outcome, left = _run(tmp_path, raw)

    _blocked(outcome, "zip_ratio")
    assert left == ["job-8.part"]


def test_two_mib_of_zeros_under_deflate_are_blocked(tmp_path: Path) -> None:
    raw = zip_ratio_member()
    assert _ratio_of(raw, "nullen.bin") > ARCHIVE_MALICIOUS_RATIO

    _blocked(_run(tmp_path, raw)[0], "zip_ratio")


def test_the_attack_ratio_wins_over_a_member_between_the_ratios(tmp_path: Path) -> None:
    raw = build_zip(
        [
            Member(b"dicht.bin", b"\x01" * 10_383, declared=101 * 10_383),
            Member(b"bombe.bin", b"\x01" * 1_049, declared=ARCHIVE_MALICIOUS_RATIO * 1_049 + 1),
        ]
    )

    _blocked(_run(tmp_path, raw)[0], "zip_ratio")


def test_a_small_member_is_not_judged_by_its_ratio(tmp_path: Path) -> None:
    raw = _declared(1_048, ARCHIVE_RATIO_MIN_BYTES - 1)
    assert _ratio_of(raw, "dicht.bin") > ARCHIVE_MALICIOUS_RATIO

    outcome, _ = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert "vornwort" in outcome.text


def test_a_member_exactly_at_the_first_ratio_is_not_judged(tmp_path: Path) -> None:
    raw = _declared(10_486, ARCHIVE_MAX_RATIO * 10_486)
    assert _ratio_of(raw, "dicht.bin") == ARCHIVE_MAX_RATIO
    with zipfile.ZipFile(io.BytesIO(raw)) as check:
        assert check.getinfo("dicht.bin").file_size >= ARCHIVE_RATIO_MIN_BYTES

    outcome, _ = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert "vornwort" in outcome.text


def test_the_attack_ratio_is_read_through_the_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = zip_ratio_member()
    monkeypatch.setattr(archive, "ARCHIVE_MALICIOUS_RATIO", 10**9)

    _limit(_run(tmp_path, raw)[0])


def test_the_attack_ratio_counts_inside_an_inner_zip_file(tmp_path: Path) -> None:
    inner = _declared(1_049, ARCHIVE_MALICIOUS_RATIO * 1_049 + 1)
    raw = build_zip([text_member("aussenwort"), Member(b"innen.zip", inner)])

    _blocked(_run(tmp_path, raw)[0], "zip_ratio")


# -- zip_overlap on every level (O2) --------------------------------------------------


def test_overlapping_entries_outside_are_blocked(tmp_path: Path) -> None:
    raw = zip_overlap()
    with zipfile.ZipFile(io.BytesIO(raw)) as check, pytest.raises(zipfile.BadZipFile, match="Overlapped"):
        check.read("a.txt")

    outcome, left = _run(tmp_path, raw)

    _blocked(outcome, "zip_overlap")
    assert left == ["job-8.part"]


def test_overlapping_entries_inside_are_blocked(tmp_path: Path) -> None:
    raw = build_zip([Member(b"innen.zip", zip_overlap()), text_member("aussenwort")])

    _blocked(_run(tmp_path, raw)[0], "zip_overlap")


def test_two_entries_at_one_local_header_are_blocked_outside(tmp_path: Path) -> None:
    raw = _same_offset_twice(b"o.txt", b"overlapwort")
    # zipfile warns instead of refusing, for one of the two entries.
    with zipfile.ZipFile(io.BytesIO(raw)) as check, warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for info in check.infolist():
            check.read(info)
    assert [str(warning.message).startswith("Overlapped entries") for warning in caught] == [True]

    _blocked(_run(tmp_path, raw)[0], "zip_overlap")


def test_two_entries_at_one_local_header_are_blocked_inside(tmp_path: Path) -> None:
    raw = build_zip([Member(b"innen.zip", _same_offset_twice(b"o.txt", b"overlapwort")), text_member("aussenwort")])

    _blocked(_run(tmp_path, raw)[0], "zip_overlap")


def test_duplicate_names_at_their_own_headers_are_no_overlap(tmp_path: Path) -> None:
    raw = build_zip([Member(b"gleich.txt", b"erstwort"), Member(b"gleich.txt", b"zweitwort")])

    outcome, _ = _run(tmp_path, raw)

    assert outcome.state is State.INDEXED
    assert "erstwort" in outcome.text
    assert "zweitwort" in outcome.text


# -- zip_traversal on the raw name (O5) -----------------------------------------------

_CLIMBING = (
    b"../x.txt",
    b"a/../../b",
    b"..\\x",
    b"/etc/x",
    b"\\x",
    b"C:\\x",
    b"c:x",
    b"a\x00b",
    b"a/..",
    b"..",
)
_NOT_CLIMBING = (b"..x.txt", b"a..b/c.txt", b"x/..y", b"x../y.txt", b"...txt", b"a/b:c.txt")


@pytest.mark.parametrize("name", _CLIMBING, ids=repr)
def test_a_name_that_climbs_out_is_blocked(name: bytes, tmp_path: Path) -> None:
    outcome, left = _run(tmp_path, zip_traversal(name))

    _blocked(outcome, "zip_traversal")
    assert left == ["job-8.part"]


@pytest.mark.parametrize("name", _CLIMBING, ids=repr)
def test_the_rule_flags_every_climbing_name(name: bytes) -> None:
    assert archive._is_traversal(name.decode("ascii"))


@pytest.mark.parametrize("name", _NOT_CLIMBING, ids=repr)
def test_a_name_with_dots_that_do_not_climb_stays_text(name: bytes, tmp_path: Path) -> None:
    assert not archive._is_traversal(name.decode("ascii"))

    outcome, _ = _run(tmp_path, zip_traversal(name))

    assert outcome.state is State.INDEXED
    assert "aussenwort" in outcome.text


def test_a_climbing_name_inside_an_inner_zip_file_is_blocked(tmp_path: Path) -> None:
    raw = build_zip([text_member("aussenwort"), Member(b"innen.zip", zip_traversal(b"../x.txt"))])

    _blocked(_run(tmp_path, raw)[0], "zip_traversal")


def test_a_climbing_name_is_judged_before_any_member_is_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reads: list[str] = []
    real = archive._read_member

    def counting(*args: object, **kwargs: object) -> None:
        reads.append("member")
        real(*args, **kwargs)  # pyright: ignore[reportArgumentType]

    monkeypatch.setattr(archive, "_read_member", counting)
    # The climbing name is the last member: the plain ones in front of it are not read.
    raw = build_zip([text_member("vornwort"), text_member("mittewort"), Member(b"../x.txt", b"x")])

    _blocked(_run(tmp_path, raw)[0], "zip_traversal")
    assert reads == []


def test_the_rule_reads_the_raw_name_and_never_the_display_name() -> None:
    rule = inspect.getsource(archive._is_traversal)
    caller = inspect.getsource(archive._read_zip)

    assert "clean_display_name" not in rule
    assert "_is_traversal(info.orig_filename)" in caller
    assert "clean_display_name" not in caller
    # zipfile cuts a name at NUL in ZipInfo.filename; the raw name keeps it.
    info = zipfile.ZipInfo("a\x00b")
    assert info.filename == "a"
    assert info.orig_filename == "a\x00b"


# -- what stays a limit (O7) ---------------------------------------------------------


def test_depth_three_without_zeros_is_an_archive_limit(tmp_path: Path) -> None:
    _limit(_run(tmp_path, zip_depth_three())[0])


def test_10001_entries_are_an_archive_limit(tmp_path: Path) -> None:
    _limit(_run(tmp_path, zip_entries())[0])


def test_a_lying_huge_declaration_is_an_archive_limit_before_the_ratio(tmp_path: Path) -> None:
    raw = build_zip([Member(b"a.txt", b"hallo", declared=0xFFFFFFF0)])
    assert _ratio_of(raw, "a.txt") > ARCHIVE_MALICIOUS_RATIO

    _limit(_run(tmp_path, raw)[0])


def test_an_over_limit_without_a_signature_carries_no_code() -> None:
    assert archive.OverLimit().signature is None
    assert archive.OverLimit("zip_ratio").signature == "zip_ratio"
