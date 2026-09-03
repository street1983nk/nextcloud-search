"""The three version numbers of a release, held together by one comparison.

D-11 says both halves of this app carry the same version and are released as a
pair, so that nobody can end up with a companion and a container that disagree
about the protocol between them. Three places state that version, and they are
three files apart:

* ``<version>`` in ``php/appinfo/info.xml``, the version of the companion app,
* ``<version>`` in ``backend/appinfo/info.xml``, the version of the container,
* ``<image-tag>`` in ``backend/appinfo/info.xml``, which is the tag the deploy
  daemon pulls at installation time.

What happens when they drift apart is not a wrong number on a page. A companion
that is a minor ahead of its container answers every search with nothing at all
since plan 05-07, because that is the honest answer to a protocol break; and an
``<image-tag>`` that names a tag nobody pushed is an app that cannot be
installed, with the failure landing on the user rather than on us.

``.github/workflows/docker.yml`` already compares all three against the git tag,
and it does so ``if: startsWith(github.ref, 'refs/tags/v')``, which is the one
moment where being wrong is most expensive: the tag exists, the release is under
way, and the fix is another tag. This gate asks the smaller question every day
instead. It never asks for a particular number, and the comment on that is the
whole point of it: the bump to the first store release belongs to plan 05-17, and
a gate that wrote a number down would be the first file somebody edits at that
moment, without the equality ever being checked.

The shape is the shape of the other textual gates of this repository, for the
reason written up in ``docs/testing.md``: there is no PHP on the development
machine and none in this repository, so a gate that reads the sources as text is
worth more than the perfect check that does not exist. Like
``test_allowlist_parity.py`` it names the side and the value on every finding,
it fails closed when a value cannot be read at all, and it carries self tests
against staged samples so that a gate whose body was deleted cannot report zero
findings over zero files and look healthy.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PHP_INFO = REPO_ROOT / "php" / "appinfo" / "info.xml"
BACKEND_INFO = REPO_ROOT / "backend" / "appinfo" / "info.xml"

# How the three values are named in a finding. A side without a file name sends
# the reader looking through two documents that are spelled almost the same.
PHP_VERSION = "the version in php/appinfo/info.xml"
BACKEND_VERSION = "the version in backend/appinfo/info.xml"
IMAGE_TAG = "the image-tag in backend/appinfo/info.xml"

# Read as text and with the same expressions the release step uses, which are
# the sed lines of .github/workflows/docker.yml:88-108. A gate that parsed the
# document differently from the step it is meant to protect could be green while
# that step is red, which is the one outcome that would make it worthless.
_VERSION = re.compile(r"<version>([^<]*)</version>")
_IMAGE_TAG = re.compile(r"<image-tag>([^<]*)</image-tag>")

# The semver type of the store schema, copied from
# https://raw.githubusercontent.com/nextcloud/appstore/<APPSTORE_SHA>/nextcloudappstore/api/v1/release/info.xsd
# at the commit pinned as APPSTORE_SHA in .github/workflows/php.yml, where
# <version> is declared as type "semver". Three number groups without leading
# zeros, an optional prerelease tail, and no build metadata. An XSD pattern is
# anchored on both ends by definition, which is why this one is used with
# fullmatch below and carries no anchors of its own.
#
# The image tag is a plain xs:string for the store, so holding it to the same
# shape is a rule of this project and not of the schema: it is compared against
# a git tag at release time, and a tag that is not a version is a tag nobody can
# derive from the release.
_SEMVER = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-([0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*))?")


def _first(pattern: re.Pattern[str], source: str) -> str | None:
    """The first value of an element, or None when the file does not carry one.

    None and an empty string are kept apart on purpose. An empty element is a
    document that says the version is nothing, a missing one is a document this
    gate could not read, and both are findings while only one of them is a typo.
    """
    found = pattern.search(source)

    return None if found is None else found.group(1).strip()


def _read(path: Path) -> str:
    """The source of one file, or an empty string when it is not there.

    The empty string produces a finding for every value that should have come
    out of it, which is the fail closed direction: a gate whose files moved has
    to go red rather than quiet.
    """
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _findings(php: str | None, backend: str | None, image: str | None) -> list[str]:
    """Every disagreement between the three values, one line each.

    The order of the two rounds is the order of cause and consequence. A value
    that is not a version at all is reported as that and is NOT reported a
    second time as a difference: the shape is the defect and the difference is
    what follows from it, and two lines for one cause send the reader looking
    for a second problem that does not exist.
    """
    values = {PHP_VERSION: php, BACKEND_VERSION: backend, IMAGE_TAG: image}

    unreadable = [f"{side} could not be read at all" for side, value in values.items() if value is None]
    misshapen = [
        f"{side} is {value!r}, which is not a version of the shape the store accepts"
        for side, value in values.items()
        if value is not None and _SEMVER.fullmatch(value) is None
    ]
    if unreadable or misshapen:
        return unreadable + misshapen

    return [
        f"{side} is {value!r} and {BACKEND_VERSION} is {backend!r}"
        for side, value in ((PHP_VERSION, php), (IMAGE_TAG, image))
        if value != backend
    ]


def _of_the_tree() -> tuple[str | None, str | None, str | None]:
    """The three values as they stand in this checkout."""
    php_source = _read(PHP_INFO)
    backend_source = _read(BACKEND_INFO)

    return (
        _first(_VERSION, php_source),
        _first(_VERSION, backend_source),
        _first(_IMAGE_TAG, backend_source),
    )


# -- the real tree ---------------------------------------------------------


def test_both_info_files_are_where_this_gate_looks_for_them() -> None:
    # The anti vacuity clause. Without it a gate whose files were renamed would
    # read two empty strings and could only be made to pass by deleting it.
    missing = [str(path) for path in (PHP_INFO, BACKEND_INFO) if not path.is_file()]

    assert missing == []


def test_all_three_values_can_be_read() -> None:
    # The second half of the same clause: the files exist and the expressions
    # still find something in them. A pattern that stopped matching would leave
    # the comparison below comparing None with None, which agrees perfectly.
    php, backend, image = _of_the_tree()

    assert php not in (None, "")
    assert backend not in (None, "")
    assert image not in (None, "")


def test_the_two_halves_and_the_image_tag_carry_the_same_version() -> None:
    # No number is demanded anywhere in this file, and that is deliberate: the
    # bump to the first store release is the business of plan 05-17, and a gate
    # that pinned a value would be edited at exactly that moment by somebody who
    # then never finds out whether the three still agree.
    php, backend, image = _of_the_tree()

    assert _findings(php, backend, image) == []


# -- self tests: the gate has to report every shape it judges --------------


def test_a_clean_sample_produces_no_finding() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every tree as broken would pass all the failure tests as well.
    assert _findings("1.2.3", "1.2.3", "1.2.3") == []
    assert _findings("1.2.3-rc.1", "1.2.3-rc.1", "1.2.3-rc.1") == []


def test_two_different_versions_are_reported_with_both_sides_named() -> None:
    findings = _findings("1.2.3", "1.3.0", "1.3.0")

    assert len(findings) == 1
    assert "php/appinfo/info.xml" in findings[0]
    assert "'1.2.3'" in findings[0]
    assert "'1.3.0'" in findings[0]


def test_an_image_tag_of_its_own_is_reported_as_the_image_tag() -> None:
    # The one of the three that costs a user rather than a developer: the deploy
    # daemon pulls this tag at installation time, so a tag nobody pushed is an
    # app that cannot be installed.
    findings = _findings("1.2.3", "1.2.3", "1.2.4")

    assert len(findings) == 1
    assert findings[0].startswith(IMAGE_TAG)
    assert "'1.2.4'" in findings[0]


def test_a_value_that_is_not_a_version_is_reported_as_that_and_only_that() -> None:
    # Two number groups are the realistic typo, and it is the case in which the
    # difference is only the consequence: reporting both would name two defects
    # where there is one.
    findings = _findings("1.2", "1.2.3", "1.2.3")

    assert len(findings) == 1
    assert findings[0].startswith(PHP_VERSION)
    assert "not a version" in findings[0]


def test_a_leading_zero_is_not_a_version_either() -> None:
    # The store pattern refuses it, so an app carrying it is rejected at the
    # submission and not here, which is the more expensive of the two places.
    findings = _findings("01.2.3", "01.2.3", "01.2.3")

    assert len(findings) == 3
    assert all("not a version" in finding for finding in findings)


def test_a_value_that_could_not_be_read_is_a_finding_and_never_a_match() -> None:
    findings = _findings(None, "1.2.3", "1.2.3")

    assert len(findings) == 1
    assert findings[0] == f"{PHP_VERSION} could not be read at all"
