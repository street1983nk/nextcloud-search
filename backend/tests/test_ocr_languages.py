"""Nine OCR languages on offer, three of them the default, and one image that has to agree.

Plan 16-10 put six more language packs into ``backend/Dockerfile`` (spa, ita,
nld, por, dan, est) and six more entries into ``OCR_LANGUAGE_ALLOWLIST``. That
is two lists in two files, and the two ways they can part company are both
silent:

* a language the reader offers but the image does not carry makes tesseract
  reject every page of every scan on that instance, and the reader cannot tell,
  because the allowlist is exactly the thing it trusts (T-03-502, T-16-36),
* a language the image installs and the build does not prove is an installation
  nobody watches: apt can succeed while the traineddata is not where tesseract
  looks for it, and the failure then appears per page, on a stranger's box.

So this file reads the Dockerfile as text, exactly like ``test_ocr_french.py``
does for the French half, and asserts both halves against the list in
``findling.config``. The list is imported and never written down a second time:
a test that repeats the set it guards agrees with itself on the very day
somebody adds a tenth language, which is the only day it matters.

The third assertion is the other half of the decision and just as deliberate:
the default stays at three. Every additional language loads another
traineddata, which costs time and memory on every single OCR page (T-16-37).
Nine languages available is a feature; nine languages switched on for every
existing installation is a slowdown nobody ordered.

Not asserted here, because it is not true: index languages. The analyzer chain
of Tantivy is German and English, OCR turns pixels into words, and no text
outside this file may claim more.
"""

from __future__ import annotations

import re
from pathlib import Path

from findling.config import OCR_DEFAULT_LANGUAGES, OCR_LANGUAGE_ALLOWLIST

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"

# The one pin every language pack of this image carries. Written as a character
# class rather than an escaped dot so that this pattern stays readable: the
# subject of the assertion is the version, and an unpinned pack is a different
# traineddata after the next rebuild, which is a different text in the index.
APT_LINE = re.compile(r"tesseract-ocr-([a-z]{3})=1:4[.]1[.]0-2")

# The fail closed half of the same apt block: the build asks the installed
# engine which languages it can actually see.
PROVEN_LINE = re.compile(r"list-langs.*grep -qx ([a-z]{3})")

# The language whose two lines the mutation below removes. Any of the nine
# would do; spa is the first of the six that plan 16-10 added.
MUTATED_LANGUAGE = "spa"


def _dockerfile_lines() -> list[str]:
    """The Dockerfile as the build reads it, comments included."""
    return DOCKERFILE.read_text(encoding="utf-8").splitlines()


def _installed(lines: list[str]) -> set[str]:
    """The language codes with a pinned apt line, commented out ones ignored.

    The Fraktur pack sits in this file as a commented example, and a reader that
    counted it would claim an image that carries a pack apt never installed.
    """
    found: set[str] = set()
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        match = APT_LINE.search(line)
        if match is not None:
            found.add(match.group(1))
    return found


def _proven_at_build_time(lines: list[str]) -> set[str]:
    """The language codes the build checks with tesseract --list-langs."""
    found: set[str] = set()
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        match = PROVEN_LINE.search(line)
        if match is not None:
            found.add(match.group(1))
    return found


def _without(lines: list[str], language: str) -> list[str]:
    """The same file with both lines of one language removed, as a mutation."""
    return [line for line in lines if f"tesseract-ocr-{language}=" not in line and f"grep -qx {language}" not in line]


def test_every_offered_language_has_a_pinned_apt_line() -> None:
    lines = _dockerfile_lines()
    installed = _installed(lines)

    missing = set(OCR_LANGUAGE_ALLOWLIST) - installed
    assert not missing, f"the allowlist offers languages the image does not install: {missing}"

    # osd is the only pack the image may carry without the allowlist naming it:
    # it is an orientation and script model, not a text language.
    surplus = installed - set(OCR_LANGUAGE_ALLOWLIST) - {"osd"}
    assert not surplus, f"the image carries language packs nothing may ever use: {surplus}"

    # The mutation, staged here rather than described: with the apt line of one
    # language gone, this case has to see it go. A gate whose red state is never
    # produced is a gate nobody has tested.
    assert MUTATED_LANGUAGE in installed
    assert MUTATED_LANGUAGE not in _installed(_without(lines, MUTATED_LANGUAGE))


def test_every_offered_language_is_proven_when_the_image_is_built() -> None:
    lines = _dockerfile_lines()
    proven = _proven_at_build_time(lines)

    unchecked = set(OCR_LANGUAGE_ALLOWLIST) - proven
    assert not unchecked, f"the build does not prove these languages arrived: {unchecked}"

    # And the same mutation from the other side.
    assert MUTATED_LANGUAGE in proven
    assert MUTATED_LANGUAGE not in _proven_at_build_time(_without(lines, MUTATED_LANGUAGE))


def test_the_default_stays_at_three_and_is_a_true_subset_of_the_offer() -> None:
    # Three, and the number is the assertion. Making all nine the default would
    # load six more traineddata files on every page of every scan, on every
    # instance that upgrades, in exchange for a language most of them do not
    # have. An instance that wants Spanish says so through
    # FINDLING_OCR_LANGUAGES and pays for exactly what it uses.
    assert len(OCR_DEFAULT_LANGUAGES) == 3

    # A true subset, and true in both directions: the default may never leave
    # the allowlist, because the fallback path of _ocr_languages would then hand
    # the engine a language it just refused, and the offer has to be the larger
    # of the two, or the six packs of plan 16-10 are dead weight in the layer.
    # Which three they are is the subject of backend/tests/test_ocr_french.py,
    # and one statement belongs in one file.
    assert set(OCR_DEFAULT_LANGUAGES) < set(OCR_LANGUAGE_ALLOWLIST)
