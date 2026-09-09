"""The two search ceilings of the container, held against their PHP mirrors.

The container refuses a request whose limit is above ``SEARCH_LIMIT_MAX`` and
one whose offset is above ``SEARCH_OFFSET_MAX``, both with a 422. The PHP half
never sends either: ``ExAppService::MAX_LIMIT`` clamps the limit before the
call, and ``SearchService::MAX_CONTAINER_OFFSET`` ends a run before a cursor
past the paging ceiling can be asked about. Both numbers are copies, and a copy
that drifts is a copy that lies.

What the drift costs is not a wrong number in a log. A limit mirror that grew
past the container turns a full page of hits into an empty result group, and an
offset mirror that grew past it turns deep paging into "the search does not
answer" while the backend answers perfectly well: the 422 arrives in PHP as
nothing at all and is indistinguishable from a container that is down. That is
pitfall 1 of the phase research, and the reason the ceiling is checked in PHP
before the call rather than repaired after the refusal.

The shape is the shape of the other textual gates of this repository, for the
reason ``docs/testing.md`` states at length: there is no PHP on the development
machine and none in this repository, so a gate that reads the sources as text is
worth more than the perfect check that does not exist. Like
``test_lockstep_versions.py`` it names both sides on every finding, it fails
closed when a value cannot be read at all, and it carries self tests against
staged samples so that a gate whose body was deleted cannot report zero findings
over zero files and look healthy.

**What this gate does not prove.** It says nothing about whether either number
is the right one. The argument for 100 and for 1200 stands at the constants in
``backend/src/findling/config.py``, and raising one of them is a decision with
its own security reasoning; this gate only insists that the decision is made in
one place and arrives in both.
"""

from __future__ import annotations

import re
from pathlib import Path

from findling.config import SEARCH_LIMIT_MAX, SEARCH_OFFSET_MAX, SEARCH_OVERFETCH, SEARCH_ROUNDS

REPO_ROOT = Path(__file__).resolve().parents[2]

EXAPP_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "ExAppService.php"
SEARCH_SERVICE = REPO_ROOT / "php" / "lib" / "Service" / "SearchService.php"

# How the four values are named in a finding. A side without a file name sends
# the reader through two languages looking for the second half of the pair.
PYTHON_LIMIT = "SEARCH_LIMIT_MAX in backend/src/findling/config.py"
PHP_LIMIT = "MAX_LIMIT in php/lib/Service/ExAppService.php"
PYTHON_OFFSET = "SEARCH_OFFSET_MAX in backend/src/findling/config.py"
PHP_OFFSET = "MAX_CONTAINER_OFFSET in php/lib/Service/SearchService.php"

# A constant declaration of the PHP half, whatever its visibility. MAX_LIMIT is
# private and MAX_CONTAINER_OFFSET is public, and neither visibility is part of
# the statement this gate makes, so neither belongs in the expression.
_CONSTANT = r"const\s+{name}\s*=\s*(\d+)\s*;"


def php_constant(source: str, name: str) -> int | None:
    """The value of a PHP class constant, or None when the source has none.

    None rather than a zero: a document this gate could not read and a document
    that declares nothing are both findings, and a zero would compare equal to
    nothing at all while looking like a number.
    """
    found = re.search(_CONSTANT.format(name=name), source)

    return None if found is None else int(found.group(1))


def read(path: Path) -> str:
    """The text of one file, or an empty string when it is not there.

    The empty string produces a finding for every value that should have come
    out of it, which is the fail closed direction: a gate whose files moved has
    to go red rather than quiet.
    """
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def findings(php_limit: int | None, php_offset: int | None) -> list[str]:
    """Every disagreement between the two pairs, one line each.

    A value that could not be read is reported as that and is never reported a
    second time as a difference: the missing declaration is the defect, and the
    difference is what follows from it.
    """
    unreadable = [
        f"{side} could not be read at all"
        for side, value in ((PHP_LIMIT, php_limit), (PHP_OFFSET, php_offset))
        if value is None
    ]
    if unreadable:
        return unreadable

    return [
        f"{php_side} is {php_value} and {python_side} is {python_value}"
        for php_side, php_value, python_side, python_value in (
            (PHP_LIMIT, php_limit, PYTHON_LIMIT, SEARCH_LIMIT_MAX),
            (PHP_OFFSET, php_offset, PYTHON_OFFSET, SEARCH_OFFSET_MAX),
        )
        if php_value != python_value
    ]


def of_the_tree() -> tuple[int | None, int | None]:
    """The two PHP values as they stand in this checkout."""
    return (
        php_constant(read(EXAPP_SERVICE), "MAX_LIMIT"),
        php_constant(read(SEARCH_SERVICE), "MAX_CONTAINER_OFFSET"),
    )


# -- the real tree ---------------------------------------------------------


def test_both_php_sources_are_where_this_gate_looks_for_them() -> None:
    # The anti vacuity clause. Without it a gate whose files were renamed would
    # read two empty strings, and two missing numbers must be a finding rather
    # than a quiet pass.
    missing = [str(path) for path in (EXAPP_SERVICE, SEARCH_SERVICE) if not path.is_file()]

    assert missing == []


def test_both_php_ceilings_can_be_read_as_numbers() -> None:
    # The second half of the same clause: the files exist and the expression
    # still finds a number in them. A pattern that stopped matching would leave
    # the comparison below comparing None with None.
    php_limit, php_offset = of_the_tree()

    assert php_limit is not None
    assert php_offset is not None


def test_the_two_ceilings_stand_in_both_halves_with_the_same_number() -> None:
    # No number is demanded anywhere in this file, and that is deliberate: both
    # are security ceilings with an argument of their own, and a gate that
    # pinned a value would be the first file edited by whoever moves one,
    # without the equality ever being checked.
    php_limit, php_offset = of_the_tree()

    assert findings(php_limit, php_offset) == []


def test_the_offset_ceiling_is_still_the_product_the_container_computes_it_from() -> None:
    # The one arithmetic statement this gate does make, and it is about the
    # Python side alone: the offset ceiling is a full result set of overfetched,
    # multi round candidates. If that ever stops being true, the comment at the
    # PHP mirror stops being true with it.
    assert SEARCH_OFFSET_MAX == SEARCH_LIMIT_MAX * SEARCH_OVERFETCH * SEARCH_ROUNDS


# -- self tests: the gate has to report every shape it judges --------------


def test_a_pair_that_agrees_produces_no_finding() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every tree as broken would pass all the failure tests as well.
    assert findings(SEARCH_LIMIT_MAX, SEARCH_OFFSET_MAX) == []


def test_an_offset_mirror_that_drifted_is_reported_with_both_sides_named() -> None:
    # The realistic accident: somebody raises the PHP mirror to buy deeper
    # paging and the container keeps refusing every cursor above its own number.
    found = findings(SEARCH_LIMIT_MAX, SEARCH_OFFSET_MAX + 100)

    assert len(found) == 1
    assert found[0].startswith(PHP_OFFSET)
    assert str(SEARCH_OFFSET_MAX + 100) in found[0]
    assert str(SEARCH_OFFSET_MAX) in found[0]


def test_a_limit_mirror_that_drifted_is_reported_as_the_limit() -> None:
    found = findings(SEARCH_LIMIT_MAX + 1, SEARCH_OFFSET_MAX)

    assert len(found) == 1
    assert found[0].startswith(PHP_LIMIT)


def test_a_value_that_could_not_be_read_is_a_finding_and_never_a_match() -> None:
    found = findings(None, SEARCH_OFFSET_MAX)

    assert found == [f"{PHP_LIMIT} could not be read at all"]


def test_the_expression_reads_a_constant_of_either_visibility() -> None:
    # Against the real shapes of the two files: one private, one public, both
    # with a docblock above them that names the constant in prose.
    private = "\t/**\n\t * MAX_LIMIT is the range the backend accepts.\n\t */\n\tprivate const MAX_LIMIT = 100;\n"
    public = "\tpublic const MAX_CONTAINER_OFFSET = 1200;\n"

    assert php_constant(private, "MAX_LIMIT") == 100
    assert php_constant(public, "MAX_CONTAINER_OFFSET") == 1200
    assert php_constant("class X {}", "MAX_LIMIT") is None
