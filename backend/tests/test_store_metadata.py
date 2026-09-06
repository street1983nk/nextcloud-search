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

Three more rules of the store arrived with plan 06.1-13, and until then they
lived in a documentation table where nobody could trip over them:

* no image under ``store/media`` is over the store's limit of two mebibytes,
* every ``category`` of both halves is one of the fifteen the store knows,
* the ``licence`` is one of the values the schema accepts.

They sit in this file rather than in a second gate next to it, because they
answer the same question as everything above: what the store would refuse
without a schema saying so. The address to file mapping of the images is not
among them, because it already exists: ``_local_image`` has judged every
screenshot address against the media directory since plan 05-18, and the
mapping there is mechanical rather than guessed by matching names.

**The vocabulary rule, and how far it reaches.** The owner keeps one German
word out of the texts this project puts in front of readers, the word for a
place where things are kept. Until plan 06.1-13 this repository held no gate for
it, and the finding that made the question unavoidable is DI-05-32 of phase 5:
the English technical term stands in a comment in ``backend/appinfo/info.xml``,
in the paragraph about the release package, and that comment travels inside the
package.

Decision E-H2 of 06.09.2026 answers it, and the reach is written here rather
than in a summary nobody reads twice: **the rule is about German prose in the
public facing texts.** The English technical term in a technical comment of a
delivered file is **exempt**, and the comment stays as it is. A silent exception
would be the same finding reopened in half a year, so the exception is not only
allowed here, it is exercised: one case below proves the term is still standing
in that comment and that this gate deliberately says nothing about it.

Which brings the counting hygiene with it, because two different counts are in
play and mixing them silently would make this gate unreadable:

* the prose rule counts **without** comment lines, and every case that uses it
  says so in its name or in its message,
* the exception is proven with a count **including** the comments, and that case
  says so too.

One more thing is checked that is not a schema rule at all. The measured
sentence of plan 06-11 lives in three places: ``README.md`` and the English
description of both halves. Three places for one number drift apart, and the
store description is the one where nobody would notice; so the equality is
mechanical here rather than remembered. The privacy paragraph of D-12 is checked
in the same spirit and with the same modesty: it has to stand in all three
languages of both descriptions, and whether the three say the same thing is a
reading and not a comparison this file can make.

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

# The six store texts in one German document, side by side in three languages.
# The rule of E-H2 reaches it too: it is German prose that a reader reads.
STORE_LISTING = REPO_ROOT / "docs" / "store-listing.md"

# Where the images of the store page live. The store keeps addresses and not
# files, so the images are in this repository and are linked over https; this
# directory is the other end of every one of those addresses.
MEDIA = REPO_ROOT / "store" / "media"

# The file a human reads before adding a fourth image. It is held against the
# directory it describes below, because a size written down once is a size that
# stops being true the first time an image is replaced.
MEDIA_README = MEDIA / "README.md"

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

# The blocked term of the owner's vocabulary rule, lowercase and as a stem, so
# that the German word and every compound built on it are caught by the same
# comparison. Assembled from two halves for the same reason the dashes above are
# escapes: a gate must not carry the thing it exists to keep out.
#
# The reach of the rule is decision E-H2 of 06.09.2026, stated in the module
# docstring: German prose in the public facing texts, and the English technical
# term in a technical comment of a delivered file is exempt.
BLOCKED_TERM = "arch" + "iv"

# Every XML comment of a document. Used to say out loud which of the two counts
# a case is making, rather than relying on the fact that an XML parser drops
# comments on its own.
_XML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

# How the privacy paragraph of D-12 opens in each of the three languages. The
# French one is matched without its colon because French typography puts a space
# in front of it, and that space is not what this rule is about.
PRIVACY_MARKERS = {
    DEFAULT_LANGUAGE: "Privacy:",
    "de": "Datenschutz:",
    "fr": "Confidentialité",
}

# The store's limit per image, in bytes so that the comparison below reads as a
# comparison and not as arithmetic. Two mebibytes, and it is a limit of the
# upload rather than a recommendation: an image over it ends the submission.
MEDIA_MAX_BYTES = 2 * 1024 * 1024

# How the limit is spelled where a human reads it. The media README has to name
# it, because the person who adds a fourth image reads that file and not this
# one.
MEDIA_LIMIT_PHRASE = "2 MiB"

# The fifteen categories the store knows, read on 06.09.2026 out of
# nextcloudappstore/core/fixtures/categories.json at the commit that
# .github/workflows/php.yml pins. The date is part of the constant: when the pin
# is raised, this list is what has to be read again.
#
# Deliberately a constant and not a fetch. A gate that asks the network turns the
# build red the day somebody else rebuilds a page, and green again for reasons
# that have nothing to do with this repository.
#
# info.xsd carries the same enumeration, so a wrong value does fail the store
# validation path too. This exists next to it because that path needs a network
# fetch and a runner, and because its message is about an enumeration in a
# normalised document, whereas this one names the file and the value.
STORE_CATEGORIES = frozenset(
    {
        "ai",
        "customization",
        "dashboard",
        "files",
        "games",
        "integration",
        "monitoring",
        "multimedia",
        "office",
        "organization",
        "search",
        "security",
        "social",
        "tools",
        "workflow",
    }
)

# The licence values info.xsd accepts, from the same file at the same commit and
# read on the same day. The four short ones are marked "Deprecated" in the schema
# and are still accepted; the SPDX spellings above them carry the schema comment
# "Requires Nextcloud minVersion >= 31".
#
# This entry ships "agpl", which is one of the deprecated four. That is valid and
# stays valid, and the move to AGPL-3.0-or-later is a change to both halves at
# once rather than a fix inside this gate, so it is written down as a deferred
# item instead of being done here in passing.
STORE_LICENCES = frozenset(
    {
        "0BSD",
        "AGPL-3.0-only",
        "AGPL-3.0-or-later",
        "Apache-2.0",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "BSD-3-Clause-Clear",
        "CC0-1.0",
        "EUPL-1.2",
        "FSFAP",
        "GPL-2.0-or-later",
        "GPL-3.0-only",
        "GPL-3.0-or-later",
        "LGPL-2.1-only",
        "LGPL-2.1-or-later",
        "LGPL-3.0-only",
        "LGPL-3.0-or-later",
        "MIT",
        "MPL-2.0",
        "OLDAP-2.7",
        "PDDL-1.0",
        "SAX-PD",
        "Unlicense",
        "X11",
        "agpl",
        "apache",
        "mit",
        "mpl",
    }
)

# The sentence of plan 06-11 (the semantic full run, superseding 05-14), quoted and
# not paraphrased. It is compared after
# the whitespace of every side has been collapsed, because README.md wraps its
# lines at a different width than an info.xml does and a line break is not a
# difference in what the sentence says.
MEASURED_SENTENCE = (
    "A full index, OCR and embedding run over 50,000 files and 20 GB on a 4-GB ARM64 box peaked at "
    "1,838 MB of resident anonymous memory, under a hard 2 GB limit enforced by the kernel, with no OOM "
    "kill and no restart."
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


def media_files() -> list[Path]:
    """Every image of the store entry, the README of the directory excluded."""
    return sorted(path for path in MEDIA.glob("*") if path.is_file() and path != MEDIA_README)


def judge_image_size(name: str, size: int) -> list[str]:
    """Whether one image is inside the store's limit per image.

    A pure comparison rather than a look at the disk, so that the sample which
    has to make this fire is a number and not a file of two megabytes staged in
    a repository that would then carry it forever.
    """
    if size > MEDIA_MAX_BYTES:
        return [f"store/media/{name}: is {size} bytes, over the store limit of {MEDIA_MAX_BYTES} bytes per image"]

    return []


def scan_media_sizes() -> list[str]:
    """Every image of the directory, held against the limit."""
    return [message for path in media_files() for message in judge_image_size(path.name, path.stat().st_size)]


def scan_catalogue(name: str, source: str) -> list[str]:
    """The category and licence values of one info.xml.

    Both are enumerations, both are in info.xsd, and both are therefore caught
    on the store validation path as well. The reason they are here too is what
    that path costs: a runner, a network fetch of two pinned files, and a
    message about an enumeration in a document that no longer looks like the one
    that was edited. This says the same thing in a second, and it names the file
    and the value.

    A file without a category is a finding of its own and not a silent pass.
    Without that clause a document whose category elements were all deleted
    would report nothing at all, which is how a gate over an empty list looks
    healthy.
    """
    try:
        info = ElementTree.fromstring(source)  # noqa: S314
    except ElementTree.ParseError as broken:
        return [f"{name}: is not well formed XML ({broken})"]

    violations: list[str] = []

    categories = [(element.text or "").strip() for element in info.findall("category")]
    if not categories:
        violations.append(f"{name}: carries no category, so the store has no shelf to file the entry on")
    violations += [
        f"{name}: the category {category!r} is not one of the {len(STORE_CATEGORIES)} the store knows"
        for category in categories
        if category not in STORE_CATEGORIES
    ]

    licences = [(element.text or "").strip() for element in info.findall("licence")]
    if len(licences) != 1:
        violations.append(f"{name}: carries {len(licences)} licence elements and the store expects exactly one")
    violations += [
        f"{name}: the licence {licence!r} is not one the store accepts"
        for licence in licences
        if licence not in STORE_LICENCES
    ]

    return violations


def scan_media_readme(source: str) -> list[str]:
    """Whether the media README names every image with the size it really has.

    The size of an image is written down for one reason: so that the person who
    is about to add a fourth one knows how much room is left before the store
    refuses the upload. A number that was true when it was typed is worse than
    no number, so the file is held against the directory it describes rather
    than trusted.
    """
    violations: list[str] = []

    if MEDIA_LIMIT_PHRASE not in source:
        violations.append(f"store/media/README.md: does not name the limit ({MEDIA_LIMIT_PHRASE}) at all")

    for path in media_files():
        size = str(path.stat().st_size)
        if path.name not in source:
            violations.append(f"store/media/README.md: says nothing about {path.name}, which lies in the directory")
        elif size not in source:
            violations.append(
                f"store/media/README.md: does not name the size of {path.name}, which is {size} bytes today"
            )

    return violations


def strip_xml_comments(source: str) -> str:
    """The document without any of its comments."""
    return _XML_COMMENT.sub("", source)


def count_blocked_term(text: str) -> int:
    """How often the blocked term stands in a text, upper and lower case alike."""
    return text.lower().count(BLOCKED_TERM)


def scan_german_prose_of_an_info(name: str, source: str) -> list[str]:
    """The blocked term in the German store texts of one info.xml.

    **This count leaves comment lines out.** The comments are removed from the
    document before it is parsed, which an XML parser would do anyway; it is
    done here in the open so that the claim is a line of code and not a property
    of somebody else's library. The reason is E-H2: the rule is about the prose
    a reader reads, and the English technical term in a technical comment of a
    delivered file is exempt.
    """
    try:
        info = ElementTree.fromstring(strip_xml_comments(source))  # noqa: S314
    except ElementTree.ParseError as broken:
        return [f"{name}: is not well formed XML ({broken})"]

    return [
        f"{name}: the German {kind} carries the blocked term of the owner's vocabulary rule "
        f"(comment lines are not counted here, the rule is about prose, E-H2)"
        for kind in L10N_ELEMENTS
        for element in info.findall(kind)
        if element.get("lang") == "de" and count_blocked_term(element.text or "")
    ]


def scan_german_document(name: str, source: str) -> list[str]:
    """The blocked term anywhere in a German document.

    **This count includes every line of the file.** A markdown document has no
    comment syntax to exempt, and the six store texts quoted inside it are the
    same prose the rule is about. If an English wording ever needs the term as a
    file type, that is a decision to take against E-H2 and not a line to slip in
    here.
    """
    if count_blocked_term(source):
        finding = (
            f"{name}: carries the blocked term of the owner's vocabulary rule "
            f"(every line of the file is counted here, comments included, E-H2)"
        )
        return [finding]

    return []


def scan_privacy_paragraph(name: str, source: str) -> list[str]:
    """Whether the privacy paragraph of D-12 stands in all three languages.

    It says nothing about what the three paragraphs say. Comparing translations
    is a reading, and the reading happens against ``docs/store-listing.md``. What
    this can see is the one failure nobody would notice: a description that was
    rewritten in one language and lost the paragraph on the way.
    """
    info = ElementTree.fromstring(strip_xml_comments(source))  # noqa: S314

    return [
        f"{name}: the description for {_named(language)} has lost the privacy paragraph of D-12"
        for element in info.findall("description")
        for language in [element.get("lang", DEFAULT_LANGUAGE)]
        if language in PRIVACY_MARKERS and PRIVACY_MARKERS[language] not in (element.text or "")
    ]


def scan_measured_sentence(name: str, source: str) -> list[str]:
    """The one sentence that has to read the same in three files.

    Why this is mechanical rather than remembered: the number comes out of a
    measurement that took ten hours on rented hardware, it lives in README.md
    and in the English description of both halves, and the store description is
    the place where a drift would be seen by nobody who could notice it. The
    comparison collapses whitespace first, because the three files wrap their
    lines differently and a line break says nothing.
    """
    return [] if MEASURED_SENTENCE in collapse(source) else [f"{name}: does not carry the measured sentence of 06-11"]


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


# -- the store rules that no schema of ours states: images and the two lists --


def test_no_image_of_the_store_entry_is_over_the_store_limit() -> None:
    assert scan_media_sizes() == []


def test_the_media_directory_is_not_empty_before_the_sizes_are_judged() -> None:
    # The anti vacuity clause of the size rule. scan_media_sizes returns an
    # empty list over an empty directory, which is exactly what it returns over
    # a directory of correct images, and the two have to be told apart.
    assert media_files() != []


def test_both_info_files_carry_a_known_category_and_an_accepted_licence() -> None:
    violations = [
        message
        for path in (PHP_INFO, BACKEND_INFO)
        for message in scan_catalogue(f"{path.parent.parent.name}/appinfo/info.xml", path.read_text(encoding="utf-8"))
    ]

    assert violations == []


def test_the_media_readme_names_every_image_with_its_size_and_the_limit() -> None:
    assert MEDIA_README.is_file()
    assert scan_media_readme(MEDIA_README.read_text(encoding="utf-8")) == []


# -- self tests for the three rules above ------------------------------------

_CLEAN_CATALOGUE = """<?xml version="1.0"?>
<info>
\t<id>findling</id>
\t<category>search</category>
\t<category>files</category>
\t<licence>agpl</licence>
</info>
"""


def _readme_sample() -> str:
    """A media README that says the truth about every image lying there now."""
    described = [f"`{path.name}`: {path.stat().st_size} bytes" for path in media_files()]

    return "\n".join([f"the limit is {MEDIA_LIMIT_PHRASE} per image", *described])


def test_the_clean_catalogue_sample_is_clean() -> None:
    # The counter sample, for the same reason the one above the screenshots has
    # one: a scanner that reported every document would pass every failure test.
    assert scan_catalogue("sample.xml", _CLEAN_CATALOGUE) == []


def test_an_image_over_the_limit_is_reported_and_one_exactly_on_it_is_not() -> None:
    over = judge_image_size("header.png", MEDIA_MAX_BYTES + 1)

    assert len(over) == 1
    assert "over the store limit" in over[0]
    assert str(MEDIA_MAX_BYTES + 1) in over[0]
    # The limit itself passes. "At most two mebibytes" is what the store says,
    # and a gate that refused the boundary would be a different rule.
    assert judge_image_size("header.png", MEDIA_MAX_BYTES) == []


def test_a_category_the_store_does_not_know_is_reported() -> None:
    violations = scan_catalogue(
        "sample.xml", _CLEAN_CATALOGUE.replace("<category>files</category>", "<category>fulltext</category>")
    )

    assert len(violations) == 1
    assert "'fulltext'" in violations[0]


def test_an_entry_without_a_category_is_reported() -> None:
    without = _CLEAN_CATALOGUE.replace("\t<category>search</category>\n", "").replace(
        "\t<category>files</category>\n", ""
    )
    violations = scan_catalogue("sample.xml", without)

    assert len(violations) == 1
    assert "carries no category" in violations[0]


def test_a_licence_the_store_does_not_accept_is_reported() -> None:
    violations = scan_catalogue(
        "sample.xml", _CLEAN_CATALOGUE.replace("<licence>agpl</licence>", "<licence>wtfpl</licence>")
    )

    assert len(violations) == 1
    assert "'wtfpl'" in violations[0]


def test_a_missing_licence_is_reported() -> None:
    violations = scan_catalogue("sample.xml", _CLEAN_CATALOGUE.replace("\t<licence>agpl</licence>\n", ""))

    assert len(violations) == 1
    assert "carries 0 licence elements" in violations[0]


def test_a_catalogue_document_that_is_not_well_formed_is_a_finding_and_not_an_error() -> None:
    violations = scan_catalogue("sample.xml", _CLEAN_CATALOGUE.replace("</info>", ""))

    assert len(violations) == 1
    assert "not well formed" in violations[0]


def test_the_clean_readme_sample_is_clean() -> None:
    assert scan_media_readme(_readme_sample()) == []


def test_a_readme_without_the_limit_is_reported() -> None:
    violations = scan_media_readme(_readme_sample().replace(MEDIA_LIMIT_PHRASE, "some size or other"))

    assert len(violations) == 1
    assert "does not name the limit" in violations[0]


def test_a_readme_whose_size_stopped_being_true_is_reported() -> None:
    # The failure this rule exists for: an image is replaced and the number next
    # to it stays. Nothing but a comparison against the directory can see it.
    first = media_files()[0]
    stale = _readme_sample().replace(f"{first.stat().st_size} bytes", "1 byte")
    violations = scan_media_readme(stale)

    assert len(violations) == 1
    assert first.name in violations[0]
    assert "does not name the size" in violations[0]


def test_a_readme_that_forgot_an_image_entirely_is_reported() -> None:
    first = media_files()[0]
    violations = scan_media_readme(_readme_sample().replace(f"`{first.name}`", "`something-else.png`"))

    assert len(violations) == 1
    assert "says nothing about" in violations[0]


# -- the vocabulary rule of E-H2, with its reach, and the paragraph of D-12 ---


def test_the_german_store_texts_avoid_the_blocked_term_without_counting_comments() -> None:
    violations = [
        message
        for path in (PHP_INFO, BACKEND_INFO)
        for message in scan_german_prose_of_an_info(
            f"{path.parent.parent.name}/appinfo/info.xml", path.read_text(encoding="utf-8")
        )
    ]

    assert violations == []


def test_the_store_listing_document_avoids_the_blocked_term_counting_every_line() -> None:
    assert STORE_LISTING.is_file()
    assert scan_german_document("docs/store-listing.md", STORE_LISTING.read_text(encoding="utf-8")) == []


def test_the_exception_of_e_h2_is_exercised_and_not_only_claimed() -> None:
    """The English term still stands in the comment, and this gate lets it stand.

    **This is the count that includes the comments**, and it is the whole point
    of the case. Without it the exception would be indistinguishable from an
    absence: a tree in which somebody had quietly removed the word would look
    exactly like a tree in which the exception works.

    If this case ever goes red, one of two things happened, and both want a
    decision rather than an edit. Either the comment was reworded, in which case
    the exception has lost its example and this case goes with it, or the gate
    was tightened to read the raw file, in which case E-H2 has to be re-read
    before anything else is touched.
    """
    delivered = BACKEND_INFO.read_text(encoding="utf-8")

    assert count_blocked_term(delivered) >= 1
    assert count_blocked_term(strip_xml_comments(delivered)) == 0
    assert scan_german_prose_of_an_info("backend/appinfo/info.xml", delivered) == []


def test_the_privacy_paragraph_of_d_12_stands_in_all_three_languages_of_both_halves() -> None:
    violations = [
        message
        for path in (PHP_INFO, BACKEND_INFO)
        for message in scan_privacy_paragraph(
            f"{path.parent.parent.name}/appinfo/info.xml", path.read_text(encoding="utf-8")
        )
    ]

    assert violations == []


# -- self tests for the vocabulary rule and the privacy paragraph ------------

_CLEAN_PRIVACY = (
    _CLEAN_INFO.replace("What it does, in English.", "What it does. Privacy: no file content leaves the server.")
    .replace("Was sie tut, auf Deutsch.", "Was sie tut. Datenschutz: kein Dateiinhalt geht vom Server fort.")
    .replace("Ce qu'elle fait, en francais.", "Ce qu'elle fait. Confidentialité : rien ne quitte le serveur.")
)


def test_the_blocked_term_in_a_german_store_text_is_reported() -> None:
    # The prose count, which is the one that leaves comments out.
    violations = scan_german_prose_of_an_info(
        "sample.xml", _CLEAN_INFO.replace("Was sie tut, auf Deutsch.", f"Ein {BLOCKED_TERM} voller Dateien.")
    )

    assert len(violations) == 1
    assert "comment lines are not counted" in violations[0]


def test_the_blocked_term_in_an_english_store_text_is_not_the_business_of_this_rule() -> None:
    # E-H2 draws the line at German prose. An English wording is judged by the
    # store and by a reader, not by this gate, and pretending otherwise here
    # would be a rule nobody decided.
    assert (
        scan_german_prose_of_an_info(
            "sample.xml", _CLEAN_INFO.replace("What it does, in English.", f"A release {BLOCKED_TERM}e.")
        )
        == []
    )


def test_the_blocked_term_inside_a_comment_is_not_reported_by_the_prose_count() -> None:
    # The staged twin of the delivered file: the term stands in the document,
    # inside a comment, and the prose count says nothing. This is the mechanical
    # form of the exception in E-H2.
    commented = _CLEAN_INFO.replace(
        '<?xml version="1.0"?>\n',
        f'<?xml version="1.0"?>\n<!-- the release {BLOCKED_TERM}e carries this file unchanged -->\n',
    )

    assert count_blocked_term(commented) == 1
    assert count_blocked_term(strip_xml_comments(commented)) == 0
    assert scan_german_prose_of_an_info("sample.xml", commented) == []


def test_the_blocked_term_in_a_german_document_is_reported_with_every_line_counted() -> None:
    violations = scan_german_document("sample.md", f"Ein Satz ueber ein {BLOCKED_TERM} und seine Dateien.")

    assert len(violations) == 1
    assert "every line of the file is counted" in violations[0]


def test_a_document_that_is_not_well_formed_is_a_finding_of_the_vocabulary_scan_too() -> None:
    violations = scan_german_prose_of_an_info("sample.xml", _CLEAN_INFO.replace("</info>", ""))

    assert len(violations) == 1
    assert "not well formed" in violations[0]


def test_the_clean_privacy_sample_is_clean() -> None:
    assert scan_privacy_paragraph("sample.xml", _CLEAN_PRIVACY) == []


def test_a_description_that_lost_the_privacy_paragraph_is_reported_by_language() -> None:
    violations = scan_privacy_paragraph("sample.xml", _CLEAN_PRIVACY.replace("Datenschutz: ", ""))

    assert len(violations) == 1
    assert "lang=de" in violations[0]


def test_the_privacy_scan_says_nothing_about_what_the_three_paragraphs_mean() -> None:
    # The modesty clause, as a case rather than as a sentence in a docstring: a
    # German paragraph that says something else entirely still passes, because
    # judging that is a reading and this file does not read.
    rewritten = _CLEAN_PRIVACY.replace("kein Dateiinhalt geht vom Server fort.", "etwas ganz anderes.")

    assert scan_privacy_paragraph("sample.xml", rewritten) == []
