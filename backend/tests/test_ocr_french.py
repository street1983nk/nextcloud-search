"""French as the third OCR language, and the four places that have to agree on it.

The owner decided on 2026-09-06 that a scanned French page has to be readable in
v1. That decision is cheap in code and expensive in drift: the language list
lives in the image (an apt line in ``backend/Dockerfile``), in the reader
(``OCR_DEFAULT_LANGUAGES`` and ``OCR_LANGUAGE_ALLOWLIST``), in the admin form
(``backend/appinfo/info.xml``) and in three README files. Four of those five can
be changed without the fifth going red, and every combination of the two halves
that is not the same set produces a failure nobody sees at build time:

* a language in the allowlist that the image does not carry makes tesseract
  reject every page of every scan, and the reader cannot tell, because the
  allowlist is exactly the thing it trusts (T-03-502),
* a language in the image that the allowlist refuses is dead weight in the
  layer, roughly a megabyte of training data that can never reach an argument
  list.

So this file asserts the set from both sides: what the reader offers is what the
apt block installs, and what the apt block installs is what the reader offers.
The Dockerfile is read as text on purpose, exactly like ``test_workflow_pins``
reads the workflow files: the pinned version is the subject of the assertion,
and a parser that resolves the file would throw it away.

What is deliberately **not** asserted here, because it is deliberately not true:
French search. Stemming, stopwords and compound splitting stay German and
English (the grilling decision of 2026-08-15). OCR turns pixels into words, the
analyzer chain turns words into an index, and only the first half learned a
third language today.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from findling.config import (
    DEFAULT_LANGUAGES,
    OCR_DEFAULT_LANGUAGES,
    OCR_LANGUAGE_ALLOWLIST,
    settings,
)

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"

# The pin the apt block carries, from the same source package tesseract-lang
# 1:4.1.0-2 that already delivers deu, eng and osd. Verified on 2026-09-06:
# the binary package is tesseract-ocr-fra_4.1.0-2_all.deb, Architecture all, so
# the amd64 and the arm64 build get the identical fra.traineddata.
FRENCH_PACKAGE = "tesseract-ocr-fra=1:4.1.0-2"

# osd is in the image but not in the allowlist: it is an orientation and script
# model, not a text language, and asking tesseract to recognise text with it
# produces nothing a search could use.
NOT_A_TEXT_LANGUAGE = frozenset({"osd"})


def _installed_languages() -> set[str]:
    """The tesseract language packs the apt block of the image installs."""
    source = DOCKERFILE.read_text(encoding="utf-8")
    lines = [line for line in source.splitlines() if not line.lstrip().startswith("#")]
    return set(re.findall(r"tesseract-ocr-([a-z]{3})=", "\n".join(lines)))


def test_french_is_the_third_default_and_the_order_is_the_argument_order() -> None:
    # Not a set: the first language weighs most in the engine, and German is the
    # language of the target audience, so it stays in front. French is appended
    # rather than inserted, which is why this asserts the whole tuple.
    assert OCR_DEFAULT_LANGUAGES == ("deu", "eng", "fra")
    assert OCR_DEFAULT_LANGUAGES[2] == "fra"


def test_french_is_allowed_to_reach_the_command_line() -> None:
    assert "fra" in OCR_LANGUAGE_ALLOWLIST
    assert set(OCR_LANGUAGE_ALLOWLIST) == {"deu", "eng", "fra"}

    # The default has to be a subset of the allowlist, or the fallback path of
    # _ocr_languages would hand the engine a language it just refused.
    assert set(OCR_DEFAULT_LANGUAGES) <= OCR_LANGUAGE_ALLOWLIST


def test_an_unset_environment_reads_a_scan_in_all_three_languages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FINDLING_OCR_LANGUAGES", raising=False)
    settings.cache_clear()

    # The zero config promise for this plan: nobody has to open a form for a
    # French scan to be read.
    assert settings().ocr_languages == ("deu", "eng", "fra")


def test_french_survives_the_allowlist_while_an_uninstalled_language_is_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # spa is a real tesseract code whose package is not in this image, so it may
    # not reach the argument list, and it may not take fra down with it either.
    monkeypatch.setenv("FINDLING_OCR_LANGUAGES", "fra+spa")
    settings.cache_clear()

    assert settings().ocr_languages == ("fra",)


def test_french_first_is_taken_in_the_order_it_was_asked_for(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FINDLING_OCR_LANGUAGES", "fra+deu")
    settings.cache_clear()

    # An instance whose scans are mostly French may say so, and the engine has
    # to weigh French most on that box.
    assert settings().ocr_languages == ("fra", "deu")


def test_the_image_installs_the_french_pack_at_the_pinned_version() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")

    # Pinned like its two siblings: an unpinned language pack is a different
    # traineddata file on a rebuild, and the OCR numbers of docs/ocr.md were
    # measured against one specific one.
    assert FRENCH_PACKAGE in source


def test_the_french_language_data_and_its_licence_are_proven_at_build_time() -> None:
    source = DOCKERFILE.read_text(encoding="utf-8")

    # The fail closed half, the same shape the German pack already has: an image
    # whose fra.traineddata did not arrive must not be built at all, because the
    # failure would otherwise appear per page, per document, on a stranger's box.
    assert "grep -qx fra" in source

    # Apache-2.0 travels with the image. The three language packs share one
    # copyright file (tessdata_fast), so the existing COPYING.tesseract-langdata
    # covers fra too, and the test proves the file is there.
    assert "test -s /usr/share/doc/tesseract-ocr-deu/copyright" in source


def test_the_allowlist_and_the_apt_block_name_the_same_languages() -> None:
    installed = _installed_languages() - NOT_A_TEXT_LANGUAGE

    # Both directions, because the two failures are different and both are silent.
    missing_from_image = set(OCR_LANGUAGE_ALLOWLIST) - installed
    missing_from_allowlist = installed - set(OCR_LANGUAGE_ALLOWLIST)

    assert not missing_from_image, f"the allowlist offers languages the image does not carry: {missing_from_image}"
    assert not missing_from_allowlist, f"the image carries languages nothing may ever use: {missing_from_allowlist}"


def test_the_index_languages_did_not_learn_french() -> None:
    # The line this plan is not allowed to cross. Tantivy gets a German and an
    # English analyzer chain and nothing else, so a French document is found by
    # its words rather than by its stems, and no outside text may claim more.
    assert DEFAULT_LANGUAGES == ("de", "en")
    assert "fr" not in DEFAULT_LANGUAGES
