"""The rebuild: the precheck of the volume, the band run and the resume after a break.

Two of the three halves are measured against a real index rather than a stand in.
A fake index would answer every question except the ones this module exists for,
because all three of them are properties of tantivy: what ``to_dict()`` hands back,
whether a range query over a fast field really walks the documents in order, and
whether a half written target directory can say on its own how far it got.

The precheck is the exception and is measured against the real volume the tests
run on, with ``FINDLING_MIN_FREE_BYTES`` raised until no machine can satisfy it.
That is the only way to get a refusal without a full disk.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from findling.config import settings
from findling.index.rebuild import NOT_ENOUGH_ROOM, ROOM_ENOUGH, may_rebuild

# More than any volume this suite ever runs on, so the refusal is about the floor
# and never about the machine.
IMPOSSIBLE_FLOOR = str(1 << 60)


@pytest.fixture(autouse=True)
def _cold_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Every test resolves the settings itself, on an environment nobody else set."""
    for name in ("APP_PERSISTENT_STORAGE", "FINDLING_MIN_FREE_BYTES", "FINDLING_LANGUAGES"):
        monkeypatch.delenv(name, raising=False)
    settings.cache_clear()


def test_a_floor_no_volume_can_satisfy_refuses_the_start(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", IMPOSSIBLE_FLOOR)
    settings.cache_clear()

    verdict = may_rebuild(tmp_path, 4)

    assert verdict.may_start is False
    assert verdict.reason == NOT_ENOUGH_ROOM


def test_the_refusal_carries_both_numbers_it_was_decided_on(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The banner names the figures, so the verdict has to carry them.

    A banner that measured the volume again would print two numbers that were
    never true at the same moment.
    """
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", IMPOSSIBLE_FLOOR)
    settings.cache_clear()

    verdict = may_rebuild(tmp_path, 4)

    assert verdict.needed_bytes >= 0
    assert verdict.free_bytes > 0


def test_the_warning_of_a_refusal_names_no_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """T-18-06-02: the lines of this module count bytes and name nothing."""
    monkeypatch.setenv("FINDLING_MIN_FREE_BYTES", IMPOSSIBLE_FLOOR)
    settings.cache_clear()

    with caplog.at_level("WARNING", logger="findling.index.rebuild"):
        may_rebuild(tmp_path, 4)

    assert caplog.records
    assert not any(tmp_path.name in record.getMessage() for record in caplog.records)


def test_an_ordinary_volume_lets_the_rebuild_start(tmp_path: Path) -> None:
    verdict = may_rebuild(tmp_path, 4)

    assert verdict.may_start is True
    assert verdict.reason == ROOM_ENOUGH


def test_an_empty_directory_needs_nothing_and_may_start(tmp_path: Path) -> None:
    """A rebuild of an index of zero byte is refused by nothing here.

    index_bytes answers 0 for a directory with no segments in it, so the need is
    0 and the floor alone decides. There is nothing to carry over, which is a
    question for the caller and not for the precheck.
    """
    verdict = may_rebuild(tmp_path, 6)

    assert verdict.needed_bytes == 0
    assert verdict.may_start is True


def test_every_new_language_raises_the_need(tmp_path: Path) -> None:
    """The factor is per chain, so four chains want more room than one.

    Measured over a directory that holds something: the file below is not an
    index, and it does not have to be, because index_bytes sums bytes and the
    factor multiplies them.
    """
    (tmp_path / "segment").write_bytes(b"x" * 1_000_000)

    one = may_rebuild(tmp_path, 1)
    four = may_rebuild(tmp_path, 4)

    assert one.needed_bytes == 1_400_000
    assert four.needed_bytes == 2_600_000
