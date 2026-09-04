"""The store texts of both halves, held in shape by one gate.

D-12 asks for three languages in both store entries and for a follow up rule:
every change to a text takes all three languages with it. A rule of that kind
is kept by nobody for long unless something checks it, and the store entry is
the worst possible place to rely on attention, because a missing translation
there is invisible to everyone who works on this repository and visible only to
the person who reads the app page in that language.

What can go wrong here is not a matter of taste, it is a list of hard edges of
the store schema and of one measured trap of the sister project:

* ``name`` and ``summary`` are ``l10n-string``, which is at most 128 characters,
  and German is reliably longer than English,
* ``lang`` takes ``de`` and ``fr`` and not ``de_DE``, which is the spelling every
  other part of a Nextcloud app uses,
* the same ``lang`` may appear only once per element kind,
* ``description`` is a non empty string, and an empty element does not fail the
  validation with a message: it ends the upload in a server error, which is the
  most expensive thing this project knows about the store,
* a ``screenshot`` has to be an https address of at most 256 characters, there
  has to be at least one of them per app, and an image has to be lying behind
  every one of them: an address without a file is an empty frame on the store
  page, which passes every schema check there is,
* and the whole file, like every public artefact of this project, carries no em
  dash, no en dash and no emoji.

One more thing is checked that is not a schema rule at all. The measured
sentence of plan 05-14 lives in three places: ``README.md`` and the English
description of both halves. Three places for one number drift apart, and the
store description is the one where nobody would notice; so the equality is
mechanical here rather than remembered.

**What this gate does not claim.** It says nothing about whether a translation
is good, whether it says the same thing as the other two, or whether the German
text is idiomatic. Those are a reading, and the reading happens against
``docs/store-listing.md``, which is where all three languages stand side by
side. This file only makes sure that a language cannot go missing, that a text
cannot get too long, and that the forbidden characters cannot come back
unnoticed.

The shape is the shape of the other textual gates of this repository, for the
reason written up in ``docs/testing.md``: findings as a list that names the
file, the element and the language; an anti vacuity clause in front, so that a
gate whose files moved goes red instead of quiet; and self tests against staged
samples, so that a gate whose body was deleted cannot report zero findings over
zero elements and look healthy.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import cast
from xml.etree import ElementTree

REPO_ROOT = Path(__file__).resolve().parents[2]

PHP_INFO = REPO_ROOT / "php" / "appinfo" / "info.xml"
BACKEND_INFO = REPO_ROOT / "backend" / "appinfo" / "info.xml"
README = REPO_ROOT / "README.md"

# Where the images of the store page live. The store keeps addresses and not
# files, so the images are in this repository and are linked over https; this
# directory is the other end of every one of those addresses.
MEDIA = REPO_ROOT / "store" / "media"

# An em dash and an en dash, written as escapes rather than as themselves, so
# that this file does not carry the two characters it exists to keep out. Same
# device as in test_admin_ui_contract.py, and for the same reason.
EM_DASH = "\u2014"
EN_DASH = "\u2013"

# Anything in the pictographic, emoticon, transport, dingbat or symbol blocks,
# plus the variation selector that turns a plain character into one. Copied from
# Gate C so that both gates judge an emoji by the same rule.
_EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\ufe0f]")

# The three element kinds the store keeps per language, in the order of the
# xs:sequence. The follow up rule of D-12 is a statement about these three as a
# group: whatever languages one of them carries, the other two carry as well.
L10N_ELEMENTS = ("name", "summary", "description")

# The two element kinds that are l10n-string rather than l10n-text. 128 is the
# maxLength of that type, and it is the edge a German translation walks into
# first.
LENGTH_LIMITED = ("name", "summary")
LENGTH_LIMIT = 128

# The languages this project ships. The English wording sits in an element
# without a lang attribute, because the schema defaults the attribute to "en";
# an explicit lang="en" next to it would be a duplicate. The empty string stands
# for that default everywhere below.
DEFAULT_LANGUAGE = ""
TRANSLATIONS = ("de", "fr")
ALLOWED_LANGUAGES = (DEFAULT_LANGUAGE, *TRANSLATIONS)

# secure-url in the store schema: https and at most 256 characters.
SCREENSHOT_LIMIT = 256

# The one address every screenshot of this project starts with. The branch and
# not a tag is a decision of plan 05-18 and stands with its reason in both
# info.xml: an image has to stay reachable for as long as the entry stands, and
# a broken one should be fixable with a commit instead of with a release.
RAW_MEDIA_PREFIX = "https://raw.githubusercontent.com/street1983nk/nextcloud-search/main/store/media/"

# One image per app is the floor and not a target. Plan 05-17 left this number
# out on purpose, because the images did not exist yet and a gate that demanded
# them would have been red over a tree that was correct; plan 05-18 adds the
# images and therefore the number.
SCREENSHOT_MINIMUM = 1

# The sentence of plan 05-14, quoted and not paraphrased. It is compared after
# the whitespace of every side has been collapsed, because README.md wraps its
# lines at a different width than an info.xml does and a line break is not a
# difference in what the sentence says.
MEASURED_SENTENCE = (
    "A full index and OCR run over 50,000 files and 20 GB on a 4-GB box peaked at 429 MB of resident "
    "anonymous memory, under a hard 2 GB limit enforced by the kernel, with no OOM kill."
)


def _named(language: str) -> str:
    """How a language is spelled in a finding."""
    return "the English default" if language == DEFAULT_LANGUAGE else f"lang={language}"


def collapse(text: str) -> str:
    """The text with every run of whitespace turned into one space."""
    return " ".join(text.split())


def scan_prose(name: str, source: str) -> list[str]:
    """Findings that apply to all three files alike: dashes and emoji."""
    violations: list[str] = []

    if EM_DASH in source:
        violations.append(f"{name}: carries an em dash")
    if EN_DASH in source:
        violations.append(f"{name}: carries an en dash")
    if _EMOJI.search(source) is not None:
        violations.append(f"{name}: carries an emoji, and no public text of this project does")

    return violations


def scan_info(name: str, source: str) -> list[str]:
    """Findings of one info.xml: the schema edges and the follow up rule."""
    try:
        info = ElementTree.fromstring(source)  # noqa: S314
    except ElementTree.ParseError as broken:
        return [f"{name}: is not well formed XML ({broken})"]

    violations: list[str] = []
    present: dict[str, list[str]] = {}

    for kind in L10N_ELEMENTS:
        languages: list[str] = []
        for element in info.findall(kind):
            language = element.get("lang", DEFAULT_LANGUAGE)
            text = (element.text or "").strip()

            if not text:
                violations.append(f"{name}: the {kind} for {_named(language)} is empty, which fails the store upload")
            if language not in ALLOWED_LANGUAGES:
                hint = ", and de_DE is not a language code the store knows" if language == "de_DE" else ""
                violations.append(f"{name}: the {kind} carries lang={language}, which is not one of de, fr{hint}")
            if language in languages:
                violations.append(f"{name}: the {kind} carries {_named(language)} twice")
            if kind in LENGTH_LIMITED and len(text) > LENGTH_LIMIT:
                violations.append(
                    f"{name}: the {kind} for {_named(language)} is {len(text)} characters, "
                    f"over the limit of {LENGTH_LIMIT}"
                )

            languages.append(language)

        present[kind] = languages

    return violations + _missing_translations(name, present) + _screenshots(name, info)


def _missing_translations(name: str, present: dict[str, list[str]]) -> list[str]:
    """The follow up rule of D-12, as a statement about three element kinds.

    Whatever languages the group carries as a whole, every kind carries too. A
    language nobody has is not a finding: this project ships three and may one
    day ship four, and a gate that pinned the list would have to be edited by
    the very plan that adds one.

    A code the schema does not know is deliberately left out of the expectation,
    and the first draft of this function got that wrong. With de_DE counted as a
    language the group carries, one typo produced four findings: the wrong code,
    plus a missing de_DE for each of the other two element kinds, plus the
    missing de of the kind that carries the typo. Three of those four send a
    reader looking for problems that do not exist, and the remedy for all of
    them is the one edit. The rule is the same one the lockstep gate states in
    its own words: the shape is the defect, the difference is what follows from
    it, and a finding per consequence is a finding too many.
    """
    expected = {language for languages in present.values() for language in languages if language in ALLOWED_LANGUAGES}

    return [
        f"{name}: the {kind} has no entry for {_named(language)}, although another element kind has one"
        for kind, languages in present.items()
        for language in sorted(expected - set(languages))
    ]


def _screenshots(name: str, info: ElementTree.Element) -> list[str]:
    """Every screenshot address, judged, plus the two rules of plan 05-18.

    The schema half is the shape of an address: https and at most 256
    characters, which is what secure-url means. Two rules are added here that
    the schema cannot state.

    The first is a number. At least one image per app, because a store entry
    without one is a page of text next to an empty carousel, and because the
    images now exist; plan 05-17 deliberately left this floor out while they
    did not.

    The second is the anti vacuity clause of the media themselves. An address
    that no image stands behind passes every schema check there is and shows an
    empty frame on the store page, which is worse than showing nothing: it says
    the entry was not looked at. So every address has to point into the media
    directory of this repository, and the file it names has to be there. A
    third party host would be the same hole with an extra owner.
    """
    violations: list[str] = []
    addresses = [(element.text or "").strip() for element in info.findall("screenshot")]

    if len(addresses) < SCREENSHOT_MINIMUM:
        violations.append(
            f"{name}: carries {len(addresses)} screenshot elements and the store entry needs "
            f"at least {SCREENSHOT_MINIMUM}"
        )

    for url in addresses:
        if not url.startswith("https://"):
            violations.append(f"{name}: the screenshot address {url!r} is not https, which the schema demands")
        if len(url) > SCREENSHOT_LIMIT:
            violations.append(
                f"{name}: the screenshot address is {len(url)} characters, over the limit of {SCREENSHOT_LIMIT}"
            )
        violations += _local_image(name, url)

    return violations


def _is_present_file(path: Path) -> bool:
    """Whether the path is a file, with an unstattable name counting as absent.

    The two platforms of this project disagree about a name that is longer than
    the filesystem allows. Windows swallows it and answers False, Linux raises
    OSError with ENAMETOOLONG out of the stat call inside ``is_file``. The
    length gate right above produces exactly such a name on purpose, so the
    disagreement was not hypothetical: the suite was green on the development
    machine and red in CI on the same commit.

    A name the filesystem cannot even look at is certainly not a file that lies
    there, so both platforms are made to reach that same verdict here instead of
    at every call site.
    """
    try:
        return path.is_file()
    except OSError:
        return False


def _local_image(name: str, url: str) -> list[str]:
    """Whether an address names an image that is really lying under store/media.

    Only an address into the media directory of this repository is judged for
    existence, and an address anywhere else is a finding of its own: the images
    of this entry are kept where this repository can keep them reachable, and a
    picture on somebody else's server is one outage away from an empty frame
    that nobody here can fix.
    """
    if not url.startswith(RAW_MEDIA_PREFIX):
        foreign = (
            f"{name}: the screenshot address {url!r} does not start with {RAW_MEDIA_PREFIX!r}, "
            f"so no file of this repository can be checked behind it"
        )
        return [foreign]

    relative = url[len(RAW_MEDIA_PREFIX) :]
    if not relative or "/" in relative:
        return [f"{name}: the screenshot address names {relative!r}, and store/media holds no subdirectories"]
    if not _is_present_file(MEDIA / relative):
        absent = (
            f"{name}: the screenshot address names {relative!r}, which does not exist under store/media, "
            f"so the store page would show an empty frame"
        )
        return [absent]

    return []


def scan_measured_sentence(name: str, source: str) -> list[str]:
    """The one sentence that has to read the same in three files.

    Why this is mechanical rather than remembered: the number comes out of a
    measurement that took ten hours on rented hardware, it lives in README.md
    and in the English description of both halves, and the store description is
    the place where a drift would be seen by nobody who could notice it. The
    comparison collapses whitespace first, because the three files wrap their
    lines differently and a line break says nothing.
    """
    return [] if MEASURED_SENTENCE in collapse(source) else [f"{name}: does not carry the measured sentence of 05-14"]


def _sources() -> list[tuple[str, str]]:
    """The three files this gate reads, as (name, source)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in (PHP_INFO, BACKEND_INFO, README)]


def _english_description(source: str) -> str:
    """The description without a lang attribute, which is the English one."""
    info = ElementTree.fromstring(source)  # noqa: S314

    return "".join(element.text or "" for element in info.findall("description") if element.get("lang") is None)


# -- the real tree ---------------------------------------------------------


def test_the_three_files_of_the_store_texts_exist() -> None:
    # The anti vacuity clause. Every scanner below returns an empty list for a
    # file that is not there, so a gate that lost its files would look perfect.
    missing = [path.name for path in (PHP_INFO, BACKEND_INFO, README) if not path.is_file()]

    assert missing == []


def test_the_media_directory_holds_at_least_one_image() -> None:
    # The second half of the same clause, for the images. Without it a tree in
    # which store/media had been deleted would report nothing at all: the
    # existence rule only judges the addresses it finds, and an address that
    # was deleted with the image is an address nobody judges.
    assert MEDIA.is_dir()
    assert sorted(path.name for path in MEDIA.glob("*.png")) != []


def test_no_store_text_carries_a_dash_or_an_emoji() -> None:
    violations = [message for name, source in _sources() for message in scan_prose(name, source)]

    assert violations == []


def test_both_info_files_keep_the_schema_edges_and_all_three_languages() -> None:
    violations = [
        message
        for path in (PHP_INFO, BACKEND_INFO)
        for message in scan_info(f"{path.parent.parent.name}/appinfo/info.xml", path.read_text(encoding="utf-8"))
    ]

    assert violations == []


def test_the_measured_sentence_reads_the_same_in_all_three_places() -> None:
    violations = scan_measured_sentence("README.md", README.read_text(encoding="utf-8"))
    for path in (PHP_INFO, BACKEND_INFO):
        name = f"{path.parent.parent.name}/appinfo/info.xml"
        violations += scan_measured_sentence(name, _english_description(path.read_text(encoding="utf-8")))

    assert violations == []


# -- self tests: the gate has to report every shape it judges --------------

_CLEAN_INFO = """<?xml version="1.0"?>
<info>
\t<id>findling</id>
\t<name>Findling</name>
\t<name lang="de">Findling</name>
\t<name lang="fr">Findling</name>
\t<summary>Zero-config full text search</summary>
\t<summary lang="de">Volltextsuche ohne Konfiguration</summary>
\t<summary lang="fr">Recherche plein texte sans configuration</summary>
\t<description>What it does, in English.</description>
\t<description lang="de">Was sie tut, auf Deutsch.</description>
\t<description lang="fr">Ce qu'elle fait, en francais.</description>
\t<screenshot>{prefix}header.png</screenshot>
\t<version>1.0.0</version>
</info>
""".replace("{prefix}", RAW_MEDIA_PREFIX)

# The one address in the clean sample that is not made up: it names an image
# that really is under store/media, so the sample passes the existence rule for
# the same reason the two real files do.
_CLEAN_SCREENSHOT = f"\t<screenshot>{RAW_MEDIA_PREFIX}header.png</screenshot>\n"


def test_the_clean_sample_is_clean() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every document as broken would pass all the failure tests too.
    assert scan_info("sample.xml", _CLEAN_INFO) == []
    assert scan_prose("sample.xml", _CLEAN_INFO) == []


def test_a_dash_and_an_emoji_are_reported() -> None:
    assert len(scan_prose("sample.xml", _CLEAN_INFO + EM_DASH)) == 1
    assert len(scan_prose("sample.xml", _CLEAN_INFO + EN_DASH)) == 1
    assert len(scan_prose("sample.xml", _CLEAN_INFO + "\U0001f600")) == 1


def test_a_summary_over_the_limit_is_reported_with_its_language_and_length() -> None:
    too_long = "A" * (LENGTH_LIMIT + 1)
    violations = scan_info("sample.xml", _CLEAN_INFO.replace("Volltextsuche ohne Konfiguration", too_long))

    assert len(violations) == 1
    assert "lang=de" in violations[0]
    assert str(LENGTH_LIMIT + 1) in violations[0]


def test_a_language_the_store_does_not_know_is_reported_and_de_de_by_name() -> None:
    violations = scan_info("sample.xml", _CLEAN_INFO.replace('summary lang="de"', 'summary lang="de_DE"'))

    # Two findings for one edit, and both are real: the code is wrong, and the
    # element kind has lost its German entry while the other two still have one.
    # Not four: a code the schema does not know is no language the other kinds
    # are expected to carry, which is what _missing_translations leaves out.
    assert len(violations) == 2
    assert "de_DE is not a language code the store knows" in violations[0]
    assert "the summary has no entry for lang=de" in violations[1]


def test_an_empty_element_is_reported_because_it_fails_the_upload() -> None:
    violations = scan_info("sample.xml", _CLEAN_INFO.replace("Was sie tut, auf Deutsch.", ""))

    assert len(violations) == 1
    assert "is empty" in violations[0]


def test_a_language_missing_from_one_element_kind_is_reported() -> None:
    # The follow up rule of D-12: the French summary is deleted while name and
    # description keep theirs.
    violations = scan_info(
        "sample.xml",
        _CLEAN_INFO.replace('\t<summary lang="fr">Recherche plein texte sans configuration</summary>\n', ""),
    )

    assert len(violations) == 1
    assert "the summary has no entry for lang=fr" in violations[0]


def test_a_duplicated_language_is_reported() -> None:
    violations = scan_info(
        "sample.xml",
        _CLEAN_INFO.replace(
            '\t<name lang="fr">Findling</name>\n',
            '\t<name lang="fr">Findling</name>\n\t<name lang="fr">Findling</name>\n',
        ),
    )

    assert len(violations) == 1
    assert "carries lang=fr twice" in violations[0]


def _with_screenshot(address: str) -> str:
    """The clean sample with one more screenshot element, the given address."""
    return _CLEAN_INFO.replace(_CLEAN_SCREENSHOT, f"{_CLEAN_SCREENSHOT}\t<screenshot>{address}</screenshot>\n")


def test_a_screenshot_that_is_not_https_is_reported() -> None:
    # Two findings, and both are real: the scheme is wrong, and an address that
    # is not the https address of this repository names no file that could be
    # checked. One edit fixes both.
    violations = scan_info("sample.xml", _with_screenshot(f"http{RAW_MEDIA_PREFIX[5:]}header.png"))

    assert len(violations) == 2
    assert "is not https" in violations[0]
    assert "does not start with" in violations[1]


def test_a_screenshot_over_the_length_limit_is_reported() -> None:
    violations = scan_info("sample.xml", _with_screenshot(f"{RAW_MEDIA_PREFIX}{'a' * SCREENSHOT_LIMIT}.png"))

    assert len(violations) == 2
    assert f"over the limit of {SCREENSHOT_LIMIT}" in violations[0]
    assert "does not exist under store/media" in violations[1]


def test_a_name_the_filesystem_refuses_counts_as_absent() -> None:
    """The verdict about an unstattable name must read the same on both platforms.

    Without this rule the length gate above is green on the development machine
    and red in CI on the very same commit, which is how it reached main on
    2026-09-04: Windows answers False for a name that is too long, Linux raises
    OSError out of the stat call. The stub raises what Linux raises, so the
    verdict is checked here without needing a filesystem that refuses the name.
    """

    class _Refusing:
        def is_file(self) -> bool:
            raise OSError(36, "File name too long")

    assert _is_present_file(cast(Path, _Refusing())) is False


def test_a_screenshot_whose_image_is_not_in_the_repository_is_reported() -> None:
    # The anti vacuity clause of the media: this address is well formed, it is
    # https, it is short enough, it points at the right directory, and there is
    # no image behind it. Nothing but this rule can see that.
    never = f"{RAW_MEDIA_PREFIX}screenshot-of-a-thing-that-never-was.png"
    violations = scan_info("sample.xml", _with_screenshot(never))

    assert len(violations) == 1
    assert "screenshot-of-a-thing-that-never-was.png" in violations[0]
    assert "does not exist under store/media" in violations[0]


def test_a_screenshot_on_a_foreign_host_is_reported() -> None:
    violations = scan_info("sample.xml", _with_screenshot("https://example.org/one.png"))

    assert len(violations) == 1
    assert "does not start with" in violations[0]


def test_a_screenshot_in_a_subdirectory_is_reported() -> None:
    violations = scan_info("sample.xml", _with_screenshot(f"{RAW_MEDIA_PREFIX}2026/header.png"))

    assert len(violations) == 1
    assert "no subdirectories" in violations[0]


def test_an_entry_without_a_screenshot_is_reported() -> None:
    # The rule plan 05-17 left open on purpose, and the reason it was left
    # open: over a tree without images this finding would have been noise.
    violations = scan_info("sample.xml", _CLEAN_INFO.replace(_CLEAN_SCREENSHOT, ""))

    assert len(violations) == 1
    assert f"carries 0 screenshot elements and the store entry needs at least {SCREENSHOT_MINIMUM}" in violations[0]


def test_a_document_that_is_not_well_formed_is_a_finding_and_not_an_error() -> None:
    violations = scan_info("sample.xml", _CLEAN_INFO.replace("</info>", ""))

    assert len(violations) == 1
    assert "not well formed" in violations[0]


def test_a_text_without_the_measured_sentence_is_reported() -> None:
    assert scan_measured_sentence("sample.md", f"nothing {MEASURED_SENTENCE} here".replace("50,000", "60,000")) != []
    # And a line break inside the sentence is not a difference: README.md wraps
    # at a different width than an info.xml, and that must not be a finding.
    assert scan_measured_sentence("sample.md", MEASURED_SENTENCE.replace(" ", "\n", 4)) == []
