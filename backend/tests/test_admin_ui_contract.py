"""Gate C: the prohibitions of the phase 4 design contract, as far as text can judge them.

The contract in ``.planning/phases/04-admin-sichtbarkeit-und-diagnose/04-UI-SPEC.md``
ends in a list of prohibitions, and most of them are decisions a reader has to
keep in mind. A few are not: they are the presence or absence of a literal
string in one of six files, and those are the ones this gate holds. No markup
built from a string in the script, no unescaped printing in the template, no
inline script, no literal colour in the stylesheet, no removed focus ring, no
dash that is not a hyphen, no emoji, and none of the five Nextcloud APIs the
contract retired.

Six files and not three since plan 09-06. The result page of phase 9 brought a
template, a stylesheet and a script of its own, and the prohibitions marked
**[G]** in ``09-UI-SPEC.md`` are the same ones with two additions of their own,
so the three new files are judged by the same scanners rather than by a fourth
gate. What did not travel with them are the special tests of the administration
page, and the reason is written where the list of sources is.

Two agreements between the halves of the page are held here as well, and they
are not prohibitions but pairs: the second coverage figure (D-16) and the state
of the embedding engine (plan 07-04). Both are rendered once server side and
rewritten on every poll, so a half that loses one of them produces no error at
all. It produces a line that never moves, or one that changes its wording three
seconds after the page opened with nothing having happened.

**Why a Python gate over PHP, CSS and JavaScript sources.** There is no PHP and
no npm on the development machine and none in this repository; the PHP side is
checked with ``php -l`` inside a container and nothing else, and there is no
JavaScript tooling at all, because the design contract forbids a build step in
the companion app. A textual gate that runs is worth more than the perfect
check that does not exist. This is the same shape as Gate A in
``test_readonly_gate.py`` and Gate B in ``test_php_trust_boundary.py``: read the
sources, judge them, name the file and the reason on every finding.

Two self tests against text samples belong to that shape and are not
decoration. A gate whose only assertion is "the current tree is clean" stays
green on the day somebody deletes its body, so both a clean sample and a dirty
one are staged here and the gate has to tell them apart.

**One scan that is not about the six files.** Since phase 9 this file also
reads every PHP source of the companion app for a single interface name,
``IInAppSearch``. It is not a prohibition of the page contract but of the app,
it has no file of its own to live in, and it is the same kind of check: a
literal string that must not appear. It is written here rather than in a fourth
gate for that reason, with its own anti vacuity clause, because a scan over zero
files reports zero findings and looks exactly like a clean tree.

**What this gate does not claim.** It says nothing about how the page looks, how
it reads or whether the spacing follows the grid. Those are the six dimensions
the design checker signed off on, and they are judged by a human looking at the
page in light, dark and high contrast. This file only makes sure the handful of
mechanically checkable prohibitions cannot come back unnoticed.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path

from findling.embed.engine import ENGINE_STATES

REPO_ROOT = Path(__file__).resolve().parents[2]

TEMPLATE = REPO_ROOT / "php" / "templates" / "admin.php"
STYLESHEET = REPO_ROOT / "php" / "css" / "admin.css"
SCRIPT = REPO_ROOT / "php" / "js" / "admin.js"

# The same three files of the result page of phase 9. They are judged by the
# same scanners and by nothing else: the prohibitions marked [G] in the
# 09-UI-SPEC are the ones of the phase 4 contract plus two spellings of built
# markup, and everything beyond them is the human sight check over there as
# much as it is here.
PAGE_TEMPLATE = REPO_ROOT / "php" / "templates" / "search.php"
PAGE_STYLESHEET = REPO_ROOT / "php" / "css" / "search.css"
PAGE_SCRIPT = REPO_ROOT / "php" / "js" / "search.js"

# The two hand written translation catalogues and the two PHP files that decide
# what the error list of the page can say. They are not part of the three files
# the prohibitions above are scanned in; the tests at the bottom read them for
# the two agreements this app has no tooling to enforce (IN-02 and DI-04-03).
L10N_JSON = REPO_ROOT / "php" / "l10n" / "de.json"
L10N_JS = REPO_ROOT / "php" / "l10n" / "de.js"

# The second German language code, and why the app ships the same words twice.
#
# Nextcloud treats ``de`` and ``de_DE`` as two languages and offers both in the
# personal settings: ``core/l10n/`` carries a catalogue for each of them. An app
# that ships only ``de`` is therefore untranslated for everybody who picked the
# other one, and that was this app until 09.09.2026: acceptance probe 20 of
# phase 9 found the result page and the administration page in English for a
# user on ``de_DE``, which is the entry the instance had set by default.
#
# The two codes are the informal and the formal address, du and Sie. Every
# sentence of this catalogue is written in the Sie form ("Grenzen Sie die Suche
# ein", "Versuchen Sie ein anderes Wort"), so its words belong under ``de_DE``
# and are at worst a shade too polite under ``de``. Writing a second, informal
# catalogue would be a translation round nobody asked for, and half of it would
# drift within a phase; the same argument that parks the French catalogue in
# docs/l10n-french.md rather than translating 24 of 173 strings.
#
# Hence: the same words under both codes, and a gate that holds the sameness
# instead of a comment that asks for it. Whoever wants to tell du from Sie later
# changes this test on purpose, which is the right amount of friction.
L10N_DE_DE_JSON = REPO_ROOT / "php" / "l10n" / "de_DE.json"
L10N_DE_DE_JS = REPO_ROOT / "php" / "l10n" / "de_DE.js"
ADMIN_VIEW = REPO_ROOT / "php" / "lib" / "Service" / "AdminViewService.php"
FILE_STATE = REPO_ROOT / "php" / "lib" / "Service" / "FileStateService.php"

# The separator between the coverage figure and its sign, written as an escape
# on both sides of the page so that the agreement can be read in a diff (IN-03).
NBSP = "\u00a0"

# The sentence the page shows when nothing moves forward any more, and the one
# the page must never show while the container is working (DI-05-22). It is
# written out here because three files have to carry it identically, the
# template, the script and the German catalogue, and because the wording is the
# claim this whole verdict is judged against: it names both halves, so it is
# only true when both of them stood still.
STALLED_SENTENCE = (
    "Indexing has not progressed for %s. Neither a background job nor the backend finished anything in that time."
)

# What it said before plan 05-20. Asserted absent by name, so that a revert is a
# red test and not a sentence that quietly accuses the background jobs again
# during an OCR pass that is doing exactly what it should.
STALLED_SENTENCE_BEFORE = "Indexing has not progressed for %s. Background jobs may not be running."

# The five APIs the contract retired, with the reason in one word each: the
# first three are deprecated since Nextcloud 18, 30 and 30, the fourth is a
# dialog helper that is deprecated too, and the last one is a CSS class that was
# removed from the server in Nextcloud 32. The app declares max-version 35, so
# every one of them is a bet on a version window it may not survive.
DEPRECATED_APIS = (
    "OCP.InitialState.loadState",
    "OC.getCanonicalLocale",
    "OC.getLanguage",
    "OC.dialogs.confirmDestructive",
    "icon-info",
)

# An em dash and an en dash. Both are forbidden in this project, in user facing
# text as much as in a comment, and both are easy to paste in without noticing.
# Written as escapes rather than as themselves, so that this file does not carry
# the two characters it exists to keep out.
EM_DASH = "\u2014"
EN_DASH = "\u2013"

# A literal colour of any of the three CSS notations. The hexadecimal pattern
# demands at least three hexadecimal characters directly behind the hash and a
# non identifier character behind them, so an id selector like
# ``#findling-coverage`` is not mistaken for a colour: its second character is
# not hexadecimal at all.
_HEX_COLOUR = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9a-zA-Z_-])")
_FUNCTION_COLOUR = re.compile(r"\b(?:rgb|rgba|hsl|hsla)\s*\(")
_REMOVED_OUTLINE = re.compile(r"outline\s*:\s*none")

# Anything in the pictographic, emoticon, transport, dingbat or symbol blocks,
# plus the variation selector that turns a plain character into one. Icons on
# this page are inline SVG and nothing else.
_EMOJI = re.compile("[\U0001f000-\U0001faff\u2600-\u27bf\ufe0f]")


def scan_script(name: str, source: str) -> list[str]:
    """Findings of the script: built markup and the retired APIs."""
    violations: list[str] = []

    # The one property that turns a string from the container into markup. The
    # page updates text nodes, which cannot carry an element no matter what a
    # path or a reason code contains.
    if "innerHTML" in source:
        violations.append(f"{name}: assigns markup from a string instead of replacing a text node")
    if "outerHTML" in source:
        violations.append(f"{name}: assigns markup from a string instead of replacing a text node")

    # The same mistake in two more spellings. Neither is an assignment, so the
    # two tests above cannot see them, and both build markup out of a string
    # that arrived from the container: a path, a reason code, a snippet of a
    # document. document.write on a page that has finished loading also replaces
    # the whole document, which is the second reason it is never right here.
    if "insertAdjacentHTML" in source:
        violations.append(f"{name}: builds markup from a string with insertAdjacentHTML instead of a text node")
    if "document.write" in source:
        violations.append(f"{name}: builds markup from a string with document.write instead of a text node")

    return violations + _deprecated(name, source)


def scan_template(name: str, source: str) -> list[str]:
    """Findings of the template: unescaped output, an inline script, retired APIs."""
    violations: list[str] = []

    # Every value on this page can be a path, a reason code or a note the
    # container sent, so the escaping printer is the only one allowed.
    if "print_unescaped" in source:
        violations.append(f"{name}: prints a value without escaping it")

    # The Nextcloud CSP blocks an inline script, so one here does not produce a
    # security hole, it produces a page whose script silently never runs.
    if "<script" in source:
        violations.append(f"{name}: carries an inline script, which the Nextcloud CSP blocks")

    return violations + _deprecated(name, source)


def scan_stylesheet(name: str, source: str) -> list[str]:
    """Findings of the stylesheet: literal colours and a removed focus ring."""
    violations: list[str] = []

    for match in _HEX_COLOUR.findall(source):
        violations.append(
            f"{name}: carries the literal colour {match}, which ignores dark mode, high contrast and theming"
        )
    if _FUNCTION_COLOUR.search(source) is not None:
        violations.append(f"{name}: carries a literal colour function instead of a theme variable")
    if _REMOVED_OUTLINE.search(source) is not None:
        violations.append(f"{name}: removes a focus ring, which leaves keyboard users without a cursor")

    return violations + _deprecated(name, source)


def scan_prose(name: str, source: str) -> list[str]:
    """Findings that apply to all three files alike: dashes and emoji."""
    violations: list[str] = []

    if EM_DASH in source:
        violations.append(f"{name}: carries an em dash")
    if EN_DASH in source:
        violations.append(f"{name}: carries an en dash")
    if _EMOJI.search(source) is not None:
        violations.append(f"{name}: carries an emoji; every icon on this page is inline SVG")

    return violations


def _deprecated(name: str, source: str) -> list[str]:
    return [f"{name}: uses the retired {api}" for api in DEPRECATED_APIS if api in source]


# The four identifiers a script that watches something cannot do without, and
# the result page has none of them: "there is no polling on this page. The
# administration page polls because it watches a running process; a search
# result is an answer to a question, not an observation" (09-UI-SPEC,
# interaction contract). Two of the four are the very markers
# test_the_script_polls_politely demands of admin.js, which is the whole point:
# the same word is a requirement on one page and a prohibition on the other.
POLLING_MARKERS = ("AbortController", "visibilityState", "setInterval", "setTimeout")

# The call that turns a link into a handler. The return mark of the page rests
# on the click going through normally, so the script writes its note and lets
# the browser navigate; a page that intercepted the click would own the
# navigation, and with it the back button that the whole return contract is
# built on.
DEFAULT_PREVENTION = "preventDefault"


def scan_page_script_for_polling(name: str, source: str) -> list[str]:
    """Findings of the result page script: any sign that it watches something."""
    return [
        f"{name}: carries {marker}, and there is no polling on this page"
        for marker in POLLING_MARKERS
        if marker in source
    ]


def scan_page_script_for_interception(name: str, source: str) -> list[str]:
    """Findings of the result page script: a click it took away from the browser."""
    if DEFAULT_PREVENTION in source:
        return [f"{name}: calls {DEFAULT_PREVENTION}, which takes the navigation away from the browser"]
    return []


# The two names the second coverage figure travels under, and every half of the
# page has to carry both (D-16). The container reports ``embedded``,
# AdminViewService turns it into ``embeddedPercent``, and the template and the
# script render the pair. A half that loses one of them does not break: it shows
# a figure that never moves, or none at all, next to a first figure that is
# live, which is a page that lies while looking healthy.
#
# Matched with word boundaries, because ``embedded`` is a prefix of
# ``embeddedPercent`` and a plain substring test would accept a file that
# carries only the second one.
COVERAGE_KEYS = ("embedded", "embeddedPercent")


def scan_coverage_keys(name: str, source: str) -> list[str]:
    """Findings of one half of the page: a key of the second figure it lost."""
    return [
        f"{name}: does not carry {key} of the second coverage figure"
        for key in COVERAGE_KEYS
        if re.search(rf"\b{key}\b", source) is None
    ]


# The three places the state of the engine has to appear in, and what each of
# them has to carry (plan 07-04). AdminViewService judges the word, the template
# renders the sentence for it on the first paint, and the script rewrites the
# same line on every poll. The identifier is spelled once here and matched in
# all three, because the failure this catches is a half that stops naming it.
ENGINE_MARKERS = {
    ADMIN_VIEW.name: ("engineState",),
    TEMPLATE.name: ("engineState", "findling-semantic-engine"),
    SCRIPT.name: ("engineState", "findling-semantic-engine"),
}

# The sentence for the sixth situation, the one that is not a state of the
# engine at all: the container did not report one. Written out because it is the
# one of the six that no mapping below can produce, both halves reach it through
# their default, and a half that lost it would silently show one of the five.
ENGINE_UNKNOWN_SENTENCE = "This container does not report the state of the model yet."


def scan_engine_state(name: str, source: str) -> list[str]:
    """Findings of one half of the page: a marker of the engine line it lost."""
    markers = ENGINE_MARKERS.get(name)
    if markers is None:
        return [f"{name}: is not one of the three files the state of the engine lives in"]
    return [
        f"{name}: does not carry {marker} of the engine state line"
        for marker in markers
        if re.search(rf"\b{re.escape(marker)}\b", source) is None
    ]


def engine_sentences_of_the_template(source: str) -> dict[str, str]:
    """The word to sentence mapping the template renders the first paint from."""
    block = re.search(r"\$engineSentences = \[(.*?)\];", source, re.DOTALL)
    if block is None:
        return {}
    return dict(re.findall(r"'([a-z_]+)' => \$l->t\('([^']+)'\)", block.group(1)))


def engine_sentences_of_the_script(source: str) -> dict[str, str]:
    """The same mapping as the script writes it on every poll."""
    block = re.search(r"function engineSentence \(state\) \{(.*?)\n  \}", source, re.DOTALL)
    if block is None:
        return {}
    return dict(re.findall(r"case '([a-z_]+)':\s*\n\s*return t\('findling', '([^']+)'\)", block.group(1)))


# The tree of PHP sources of the companion app, and the one interface name that
# must not appear anywhere in it. SearchComposer switches a button "Search in
# Findling" into the unified search dialog for a provider that implements it,
# and that button has neither a click handler nor an href in stable33, stable34,
# stable35 or master. A dead button is worse than no button, so the entry point
# to the result page is an ordinary result entry at the end of the group and
# this interface is implemented nowhere (09-UI-SPEC, verification table).
APP_PHP_ROOT = REPO_ROOT / "php" / "lib"
IN_APP_SEARCH = "IInAppSearch"


def scan_app_php_sources(name: str, source: str) -> list[str]:
    """Findings of one PHP source of the app: the interface that draws a dead button."""
    if IN_APP_SEARCH in source:
        return [
            (
                f"{name}: names {IN_APP_SEARCH}, which switches a button without a click handler "
                "and without an href into the search dialog"
            )
        ]
    return []


def _app_php_sources() -> list[tuple[str, str]]:
    """Every PHP source of the app below ``php/lib``, as (path below php, source)."""
    return [
        (path.relative_to(REPO_ROOT / "php").as_posix(), path.read_text(encoding="utf-8"))
        for path in sorted(APP_PHP_ROOT.glob("**/*.php"))
    ]


# The empty state of the result page, and the banner it must not contradict.
#
# Block 4 of ``search.php`` used to render whenever the hit list was empty, and
# with a term it says "no file contains X". That is a statement about a search
# that happened and came back with nothing, so it is untrue in every state where
# a banner above it says that the search did not happen at all (silent backend,
# version drift, no home folder) or that it did not go all the way (the paging
# ceiling, an index still being built). Both blocks on one screen then tell the
# user two different things to do, wait and retype, and only one of them can be
# right. Reachable without any hand editing: a stopped backend, and the ceiling
# after a dozen clicks on "next page".
#
# The template therefore decides once, in ``$showEmpty``, next to the banner
# decision it depends on, and this gate holds that decision. The variant without
# a term is an invitation and never a claim, which is why the decision has to
# read ``$hasQuery`` as well: a page that a hint reached before the user typed
# anything must still say what it is for. Bug audit A of phase 9, 09.09.2026.
_EMPTY_STATE = re.compile(r'class="findling-empty"')
_EMPTY_STATE_BRANCH = re.compile(r"\}\s*elseif\s*\(\$showEmpty\)\s*\{")
_EMPTY_STATE_DECISION = re.compile(r"\$showEmpty\s*=(?P<body>[^;]*);", re.DOTALL)


def scan_page_template_for_an_unguarded_empty_state(name: str, source: str) -> list[str]:
    """Findings of the result page template: an empty state that speaks over a banner."""
    if not _EMPTY_STATE.search(source):
        return []

    findings: list[str] = []
    if not _EMPTY_STATE_BRANCH.search(source):
        findings.append(
            f"{name}: the empty state does not sit behind elseif ($showEmpty), so it renders "
            "under a banner that has already explained the emptiness"
        )

    decision = _EMPTY_STATE_DECISION.search(source)
    if decision is None:
        findings.append(
            f"{name}: no $showEmpty decision, so nothing keeps the sentence about a search "
            "that came back empty away from a page whose search never happened"
        )
    else:
        missing = [marker for marker in ("$hasError", "$hasHint", "$hasQuery") if marker not in decision.group("body")]
        if missing:
            findings.append(f"{name}: the $showEmpty decision does not read {', '.join(missing)}")

    return findings


Scanner = Callable[[str, str], list[str]]


def _sources() -> list[tuple[str, str, Scanner]]:
    """The six files of the two pages, as (name, source, scanner).

    The scanner is typed as what it is rather than as an object. With ``object``
    the call in the comprehension below is not a call any type checker can
    verify, and the gate would only fail on the release that starts to care.

    Six since plan 09-06, and the three of the result page were added the day
    they were on disk and not earlier: every scanner returns an empty list for a
    file it cannot read, so a name in this list without a file behind it is not
    a red gate, it is a green one that reads nothing.

    **What was deliberately not extended with it.** The special tests further
    down stay literally on the administration files, and the three that would be
    tempting to "make consistent" are
    ``test_the_script_reads_the_token_inside_the_call``,
    ``test_the_script_polls_politely`` and
    ``test_both_halves_of_the_page_write_the_same_percent_separator``, together
    with every pair test after them. All of them describe a page that watches a
    running process: it reads a rotating token, it holds an abort controller, it
    asks whether the tab is visible, and it renders one value twice, once server
    side and once on every poll. The result page does none of that, because a
    search result is an answer to a question and not an observation. Widening
    those tests onto ``search.js`` turns the tree red for a property the new
    file deliberately does not have (pitfall 4 of the phase 9 research). What
    the new script has to hold instead is asserted in its own two tests, and
    they assert the absence of exactly those markers.
    """
    return [
        (TEMPLATE.name, TEMPLATE.read_text(encoding="utf-8"), scan_template),
        (STYLESHEET.name, STYLESHEET.read_text(encoding="utf-8"), scan_stylesheet),
        (SCRIPT.name, SCRIPT.read_text(encoding="utf-8"), scan_script),
        (PAGE_TEMPLATE.name, PAGE_TEMPLATE.read_text(encoding="utf-8"), scan_template),
        (PAGE_STYLESHEET.name, PAGE_STYLESHEET.read_text(encoding="utf-8"), scan_stylesheet),
        (PAGE_SCRIPT.name, PAGE_SCRIPT.read_text(encoding="utf-8"), scan_script),
    ]


# -- the real tree ---------------------------------------------------------


def test_the_six_files_of_the_two_pages_exist() -> None:
    # The anti vacuity clause. Every scanner below returns an empty list for a
    # file that is not there, so a gate that lost its files would look perfect.
    # Six paths since plan 09-06, and the count is the point of the clause: a
    # gate that reads nothing reports nothing, so the cleanest possible run of
    # this file is also the one in which it has stopped judging anything at all.
    missing = [
        path.name
        for path in (TEMPLATE, STYLESHEET, SCRIPT, PAGE_TEMPLATE, PAGE_STYLESHEET, PAGE_SCRIPT)
        if not path.is_file()
    ]

    assert missing == []


def test_the_page_breaks_none_of_the_checkable_prohibitions() -> None:
    violations = [message for name, source, scan in _sources() for message in scan(name, source)]

    assert violations == []


def test_no_file_of_the_page_carries_a_dash_or_an_emoji() -> None:
    violations = [message for name, source, _ in _sources() for message in scan_prose(name, source)]

    assert violations == []


def test_no_php_source_of_the_app_names_the_in_app_search_interface() -> None:
    violations = [message for name, source in _app_php_sources() for message in scan_app_php_sources(name, source)]

    assert violations == []


def test_the_scan_over_the_php_sources_reads_files() -> None:
    # The anti vacuity clause of the scan above. A glob that stopped matching,
    # or a root that moved, would report nothing over nothing and look like the
    # cleanest tree in the world. The controllers are named as well, because an
    # empty list is not the only way to read the wrong tree.
    names = [name for name, _ in _app_php_sources()]

    assert names != []
    assert [name for name in names if name.startswith("lib/Controller/")] != []


def test_the_script_reads_the_token_inside_the_call() -> None:
    # Not a prohibition of the contract but the mechanism behind one of them:
    # the token is rotated when the session is renewed, so a copy taken at load
    # time leaves the page on old numbers without an error anywhere. Read inside
    # a function means indented, and top level means column zero.
    source = SCRIPT.read_text(encoding="utf-8")
    lines = [line for line in source.splitlines() if "dataset.requesttoken" in line]

    assert lines != []
    assert [line for line in lines if not line.startswith((" ", "\t"))] == []


def test_the_script_polls_politely() -> None:
    # The three halves of the interaction contract that keep a forgotten tab
    # from questioning the instance for a week. admin.js and no other file: the
    # result page script is asserted to carry none of these markers, two tests
    # below.
    source = SCRIPT.read_text(encoding="utf-8")

    assert "AbortController" in source
    assert "visibilityState" in source


def test_the_page_script_does_no_polling() -> None:
    """The other side of the test above, over the other script.

    There is no polling on the result page, and the four markers are the ones
    that would show it: an abort controller, the visibility of the tab and the
    two timers. The page renders once, server side, and then stands still until
    somebody asks another question.
    """
    findings = scan_page_script_for_polling(PAGE_SCRIPT.name, PAGE_SCRIPT.read_text(encoding="utf-8"))

    assert findings == []
    # And the assertion can go red. Without this line a scanner whose body was
    # deleted would report a clean page over a script that polls every second.
    dirty = "const controller = new AbortController()\nwindow.setInterval(ask, 3000)\n"
    assert len(scan_page_script_for_polling("sample.js", dirty)) == 2


def test_the_page_script_does_not_intercept_a_click() -> None:
    """The return mark is written on the way out, and the link still travels.

    The interaction contract allows the script to listen for a click and write
    the mark, and forbids it to take the click away. A prevented default would
    make the script the owner of the navigation, and everything the return
    contract promises about the back button rests on the browser owning it.
    """
    findings = scan_page_script_for_interception(PAGE_SCRIPT.name, PAGE_SCRIPT.read_text(encoding="utf-8"))

    assert findings == []
    dirty = "link.addEventListener('click', function (event) { event.preventDefault() })\n"
    assert len(scan_page_script_for_interception("sample.js", dirty)) == 1


def test_the_empty_state_of_the_page_does_not_speak_over_a_banner() -> None:
    """The page says one thing about why a list is empty, not two.

    Probed on the running instance on 09.09.2026, in all five states: hits, a
    real empty result, no term, past the paging ceiling and a version drift. The
    two that produced the finding this gate now holds were the error block and
    the ceiling, both of which carried "no file contains X" underneath them.
    """
    findings = scan_page_template_for_an_unguarded_empty_state(
        PAGE_TEMPLATE.name, PAGE_TEMPLATE.read_text(encoding="utf-8")
    )

    assert findings == []

    # And it goes red on the shape it replaced, which is what makes this a gate
    # and not a decoration: a bare else that renders the empty state whatever
    # the banner above it says, and no decision anywhere.
    dirty = '<?php } else { ?>\n\t<div class="findling-empty">\n\t</div>\n<?php } ?>\n'
    assert len(scan_page_template_for_an_unguarded_empty_state("sample.php", dirty)) == 2

    # And on the half measure: the branch is there, the decision forgets the
    # hint, so the ceiling would go on contradicting itself while the error
    # block behaved.
    half = (
        "<?php $showEmpty = $hits === [] && !$hasError; ?>\n"
        "<?php } elseif ($showEmpty) { ?>\n"
        '\t<div class="findling-empty"></div>\n'
        "<?php } ?>\n"
    )
    assert scan_page_template_for_an_unguarded_empty_state("sample.php", half) == [
        "sample.php: the $showEmpty decision does not read $hasHint, $hasQuery"
    ]


# -- self tests: the gate has to report every shape it judges --------------

_CLEAN_SCRIPT = """'use strict'

;(function () {
  async function ask (path) {
    const response = await fetch(OC.generateUrl('/apps/findling/admin/' + path), {
      headers: { requesttoken: document.head.dataset.requesttoken }
    })
    return response.json()
  }
})()
"""

_CLEAN_TEMPLATE = """<?php
\\OCP\\Util::addScript('findling', 'admin');
?>
<div id="findling-coverage" class="section"><?php p($l->t('Search coverage')); ?></div>
"""

_CLEAN_STYLESHEET = """#findling-coverage {
\tmax-width: 900px;
\tcolor: var(--color-main-text);
}
"""


def test_the_clean_samples_are_clean() -> None:
    # The counter sample of everything below. Without it a gate that reported
    # every file as broken would pass all the failure tests too. The stylesheet
    # sample also pins the id selector case: a hash followed by letters is not a
    # colour, and a gate that thinks it is would be deleted within a week.
    assert scan_script("sample.js", _CLEAN_SCRIPT) == []
    assert scan_template("sample.php", _CLEAN_TEMPLATE) == []
    assert scan_stylesheet("sample.css", _CLEAN_STYLESHEET) == []
    assert scan_prose("sample.js", _CLEAN_SCRIPT) == []


def test_markup_built_in_the_script_is_reported() -> None:
    source = _CLEAN_SCRIPT.replace("return response.json()", "document.body.innerHTML = path")

    violations = scan_script("sample.js", source)

    assert len(violations) == 1
    assert "text node" in violations[0]


def test_markup_built_with_insert_adjacent_html_is_reported() -> None:
    source = _CLEAN_SCRIPT.replace("return response.json()", "document.body.insertAdjacentHTML('beforeend', path)")

    violations = scan_script("sample.js", source)

    assert len(violations) == 1
    assert "insertAdjacentHTML" in violations[0]


def test_markup_written_with_document_write_is_reported() -> None:
    source = _CLEAN_SCRIPT.replace("return response.json()", "document.write(path)")

    violations = scan_script("sample.js", source)

    assert len(violations) == 1
    assert "document.write" in violations[0]


def test_a_php_source_naming_the_in_app_search_interface_is_reported() -> None:
    # The dirty sample of the scan over php/lib, and the shape it would really
    # arrive in: one more interface on the provider that is already there.
    dirty = "<?php\n\nfinal class Provider implements IProvider, " + IN_APP_SEARCH + " {\n}\n"

    assert scan_app_php_sources("lib/Search/Provider.php", "<?php\n\nfinal class Provider {\n}\n") == []
    violations = scan_app_php_sources("lib/Search/Provider.php", dirty)

    assert len(violations) == 1
    assert IN_APP_SEARCH in violations[0]
    assert "lib/Search/Provider.php" in violations[0]


def test_unescaped_output_in_the_template_is_reported() -> None:
    source = _CLEAN_TEMPLATE.replace("p($l->t(", "print_unescaped($l->t(")

    violations = scan_template("sample.php", source)

    assert len(violations) == 1
    assert "escaping" in violations[0]


def test_an_inline_script_in_the_template_is_reported() -> None:
    source = _CLEAN_TEMPLATE + "<script>alert(1)</script>\n"

    violations = scan_template("sample.php", source)

    assert len(violations) == 1
    assert "inline script" in violations[0]


def test_a_literal_colour_in_the_stylesheet_is_reported() -> None:
    hexadecimal = scan_stylesheet("sample.css", _CLEAN_STYLESHEET.replace("var(--color-main-text)", "#1a1a1a"))
    functional = scan_stylesheet("sample.css", _CLEAN_STYLESHEET.replace("var(--color-main-text)", "rgb(26, 26, 26)"))

    assert len(hexadecimal) == 1
    assert "literal colour" in hexadecimal[0]
    assert len(functional) == 1
    assert "colour function" in functional[0]


def test_a_removed_focus_ring_is_reported() -> None:
    violations = scan_stylesheet("sample.css", _CLEAN_STYLESHEET.replace("max-width: 900px;", "outline: none;"))

    assert len(violations) == 1
    assert "focus ring" in violations[0]


def test_a_retired_api_is_reported_in_every_file() -> None:
    assert len(scan_script("sample.js", _CLEAN_SCRIPT + "OC.getCanonicalLocale()\n")) == 1
    assert len(scan_template("sample.php", _CLEAN_TEMPLATE + '<span class="icon-info"></span>\n')) == 1
    assert len(scan_stylesheet("sample.css", _CLEAN_STYLESHEET + ".icon-info { display: none }\n")) == 1


def test_a_dash_and_an_emoji_are_reported() -> None:
    assert len(scan_prose("sample.js", _CLEAN_SCRIPT + "// a dash " + EM_DASH + "\n")) == 1
    assert len(scan_prose("sample.js", _CLEAN_SCRIPT + "// a dash " + EN_DASH + "\n")) == 1
    assert len(scan_prose("sample.js", _CLEAN_SCRIPT + "// a face \U0001f600\n")) == 1


def test_both_halves_of_the_page_write_the_same_percent_separator() -> None:
    """IN-03, turned from a review note into a gate.

    The template renders the coverage figure once, server side, and the script
    rewrites it on every poll. If the two spell the separator differently, the
    number visibly changes its shape three seconds after the page opened with
    nothing having happened, and the page promised the opposite: a value does
    not change form when the script takes over.

    Both sides write the escape rather than the character, which is the second
    half of the fix. The literal was there all along and reads as an ordinary
    space in most editors, so the phase 4 review filed a drift that did not
    exist. An invisible agreement is one nobody can review.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert '"\\u{00A0}%"' in template
    assert "'\\u00a0%'" in script
    # And neither side smuggles the character in instead of naming it.
    assert NBSP not in template
    assert NBSP not in script


def test_every_half_of_the_page_carries_the_second_coverage_figure() -> None:
    """D-16 as a gate, and the other half of it is the PHPUnit case.

    The semantic figure fills up for hours after the full text figure is
    complete, so it is the one number on this page that moves while everything
    else stands still. That is exactly why it is the one that can be lost
    without anybody noticing: a template without it renders nothing, a service
    without it sends nothing, and a script without it leaves whatever the first
    render put there, and none of the three produces an error.
    """
    findings = (
        scan_coverage_keys(ADMIN_VIEW.name, ADMIN_VIEW.read_text(encoding="utf-8"))
        + scan_coverage_keys(TEMPLATE.name, TEMPLATE.read_text(encoding="utf-8"))
        + scan_coverage_keys(SCRIPT.name, SCRIPT.read_text(encoding="utf-8"))
    )

    assert findings == []


def test_a_half_that_lost_the_second_coverage_figure_is_reported() -> None:
    # The gate has to be able to go red, and the prefix case is the one it would
    # get wrong: a file that carries only embeddedPercent has lost the counter
    # the figure is made of, and a plain substring test would call it clean.
    assert len(scan_coverage_keys("sample.php", "'percent' => $percent,")) == 2
    assert len(scan_coverage_keys("sample.php", "'embeddedPercent' => $share,")) == 1
    assert scan_coverage_keys("sample.php", "'embedded' => 3, 'embeddedPercent' => 25,") == []


def test_the_second_figure_is_a_second_call_and_not_a_second_calculation() -> None:
    """The mechanism behind the pair, held where it is decided.

    One declaration and two calls. Two calculations for one kind of number are
    the beginning of the drift phase 4 avoided by working the denominator out
    exactly once, and the failure they produce is the worst kind this page has:
    two figures that are each plausible and no longer comparable.
    """
    php = ADMIN_VIEW.read_text(encoding="utf-8")

    # The call sites and not every mention of the name: the docblock of
    # coverage() names the method as well, and a count that included prose would
    # go red on an edit that only explained something better.
    assert php.count("public static function coverageShare(") == 1
    assert php.count("self::coverageShare(") == 2
    # And the second call is the one that knows the figure may be absent. Without
    # that guard a container older than this app would be shown as nought per
    # cent semantic coverage, which is a claim about something nobody asked.
    assert "$backendReachable && $embeddedKnown" in php


def test_every_half_of_the_page_carries_the_state_of_the_engine() -> None:
    """Plan 07-04 as a gate, in the shape the second coverage figure has one.

    The same failure mode, one field further on: the state of the engine is
    rendered server side and rewritten on every poll, and a half that loses it
    breaks nothing. The service stops sending a word, or the template stops
    holding a line, or the script stops writing one, and in all three cases the
    page keeps looking healthy while it no longer says whether the semantic half
    is going to work at all.
    """
    findings = [
        message
        for path in (ADMIN_VIEW, TEMPLATE, SCRIPT)
        for message in scan_engine_state(path.name, path.read_text(encoding="utf-8"))
    ]

    assert findings == []


def test_a_half_that_lost_the_state_of_the_engine_is_reported() -> None:
    # The gate has to be able to go red, and a file that is not one of the three
    # has to be a finding rather than a clean answer: a scanner that returned an
    # empty list for an unknown name would report a renamed file as perfect.
    assert len(scan_engine_state(TEMPLATE.name, '<p id="findling-semantic"></p>')) == 2
    assert len(scan_engine_state(ADMIN_VIEW.name, "'note' => $this->text($answer, 'note'),")) == 1
    assert scan_engine_state(SCRIPT.name, "backend.engineState findling-semantic-engine") == []
    assert len(scan_engine_state("somewhere-else.php", "engineState findling-semantic-engine")) == 1


def test_the_engine_line_is_not_hidden_behind_a_denominator_that_does_not_exist_yet() -> None:
    """Bug audit MEDIUM-3 of plan 07-05, as a gate over both halves.

    The line sat inside the block of the second coverage figure, and that block
    is shown only when there is a denominator. A fresh installation has none for
    hours, which is exactly the installation the line says the most to: whether
    there is a model in this image at all decides whether waiting is worth
    anything. It was invisible in the one situation it was written for.

    Held as the rule and not as the rendering, because there is no DOM here. The
    template hides the block on two conditions and the script shows it on two,
    and the second of them is the word about the engine in both.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert "$hasEngineWord = $engineState !== '';" in template
    assert "if (!$hasDenominator && !$hasEngineWord) { ?> hidden" in template
    assert "const hasEngineWord = typeof engineState === 'string' && engineState !== ''" in script
    assert "shown('findling-semantic', hasDenominator || hasEngineWord)" in script
    # And the share line inside keeps the denominator of its own, in both
    # halves: a block that appears for the engine line alone must not claim
    # that a figure could not be worked out.
    assert 'id="findling-semantic-unknown"<?php if (!$hasDenominator || $hasEmbeddedFraction)' in template
    assert "shown('findling-semantic-unknown', hasDenominator && !hasFraction)" in script


def test_both_halves_of_the_page_map_the_same_state_to_the_same_sentence() -> None:
    """The pair itself, and not only the presence of the two names.

    The template paints the sentence once and the script rewrites the very same
    element on the first poll. Two halves that agree on the identifier and
    disagree on the wording are worse than a half that lost the line: the page
    opens with one sentence and replaces it with another three seconds later,
    with nothing having happened on the instance.
    """
    template = engine_sentences_of_the_template(TEMPLATE.read_text(encoding="utf-8"))
    script = engine_sentences_of_the_script(SCRIPT.read_text(encoding="utf-8"))

    assert template != {}, "the mapping is no longer where this gate looks for it"
    assert script != {}, "the mapping is no longer where this gate looks for it"
    assert template == script
    # And the words are the ones the container really sends. The set is imported
    # from the container half rather than spelled again here, because a second
    # spelling of a closed set is a second thing to forget (T-07-02).
    assert set(template) == set(ENGINE_STATES)


def test_the_six_sentences_of_the_engine_line_are_in_the_german_catalogue() -> None:
    """IN-02 for the new line: a sentence in one catalogue only is half German.

    The sixth is the one for a container that reports no state at all. It is
    reached through the default of both halves, so no mapping carries it and
    nothing but this line would notice its absence.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    catalogue = json.loads(L10N_JSON.read_text(encoding="utf-8"))["translations"]
    sentences = set(engine_sentences_of_the_template(template).values()) | {ENGINE_UNKNOWN_SENTENCE}

    assert len(sentences) == 6

    missing = [f"de.json: {sentence}" for sentence in sorted(sentences) if sentence not in catalogue]
    if ENGINE_UNKNOWN_SENTENCE not in template:
        missing.append(f"admin.php: {ENGINE_UNKNOWN_SENTENCE}")
    if ENGINE_UNKNOWN_SENTENCE not in script:
        missing.append(f"admin.js: {ENGINE_UNKNOWN_SENTENCE}")

    assert missing == []


def test_the_two_translation_files_carry_the_same_keys() -> None:
    """IN-02, and the reason it is a gate rather than a single deletion.

    This app has no string extractor: ``l10n/de.json`` and ``l10n/de.js`` are
    written by hand and have to stay identical, because Nextcloud reads the
    first from PHP and the second from the browser. A key removed from one of
    them alone is a sentence that is German on the server and English in the
    page, which is the shape of every half finished cleanup.
    """
    catalogue = json.loads(L10N_JSON.read_text(encoding="utf-8"))
    # de.js is a call of OC.L10N.register with the catalogue as its third
    # argument, so the object is cut out rather than parsed as a whole file.
    script = L10N_JS.read_text(encoding="utf-8")
    keys = set(json.loads(script[script.index("{") : script.rindex("}") + 1]))

    assert keys == set(catalogue["translations"])
    # The dead entry of IN-02 named a sentence the page never showed. Its
    # absence is asserted by name, so that a revert is a red test and not a
    # silent return.
    assert "Indexing, about %s left" not in keys


def test_the_german_catalogue_covers_both_german_language_codes() -> None:
    """Abweichung B of the phase 9 acceptance: de alone leaves de_DE in English.

    Four files, two languages, one set of words. The two ``de_DE`` catalogues
    carry the same text as the two ``de`` ones, and this test is what keeps them
    from drifting: a key added to one German catalogue and forgotten in the
    other is a page that is German for one half of the German speaking users and
    English for the other, and nothing in a diff would show it.

    Compared as text and not only as key sets, because that is the invariant
    that costs nothing to keep and catches a translated value as well as a
    missing key. The comparison runs over the text as Python reads it, so a
    different line ending in a working copy on Windows is not a finding.
    """
    for language, twin in ((L10N_JSON, L10N_DE_DE_JSON), (L10N_JS, L10N_DE_DE_JS)):
        assert twin.is_file(), f"{twin.name} is missing, so everybody on de_DE reads this app in English"
        assert twin.read_text(encoding="utf-8") == language.read_text(encoding="utf-8"), (
            f"{twin.name} and {language.name} have drifted apart"
        )

    # And the key set once more from the reading end, because that is the shape
    # Nextcloud actually loads: the JSON from PHP, the object out of the
    # register call from the browser.
    keys_of = {
        path.name: set(json.loads(path.read_text(encoding="utf-8"))["translations"])
        if path.suffix == ".json"
        else set(
            json.loads(
                path.read_text(encoding="utf-8")[
                    path.read_text(encoding="utf-8").index("{") : path.read_text(encoding="utf-8").rindex("}") + 1
                ]
            )
        )
        for path in (L10N_JSON, L10N_JS, L10N_DE_DE_JSON, L10N_DE_DE_JS)
    }

    assert len(set(map(frozenset, keys_of.values()))) == 1, f"the four catalogues disagree: {sorted(keys_of)}"
    assert len(keys_of["de.json"]) == 173


def test_every_reason_of_the_closed_list_has_a_label_and_a_remedy() -> None:
    """DI-04-03 from the reading end: a group without words is a blank cell.

    Four of the codes are decided by the container alone, and until plan 05-11
    they never reached this side, so their rows in the label table were never
    rendered by anything. Now they are, and a code without a row would be shown
    as "Unknown reason (code)" to an admin whose files are perfectly ordinary.
    """
    php = ADMIN_VIEW.read_text(encoding="utf-8")
    labelled = set(re.findall(r"^\t\t'([a-z_]+)' => \[$", php, re.MULTILINE))
    block = re.search(r"const REASONS = \[(.*?)\];", FILE_STATE.read_text(encoding="utf-8"), re.DOTALL)

    assert block is not None, "the closed list of reasons is no longer where this test looks for it"
    reasons = set(re.findall(r"'([a-z_]+)'", block.group(1)))
    assert reasons
    assert reasons - labelled == set()
    for decided_here in ("encrypted", "no_text_layer", "empty_text", "image_not_ocrable"):
        assert decided_here in labelled


def test_all_three_files_carry_the_same_sentence_about_a_stall() -> None:
    """DI-05-22 from the reading end: the page has to say what it measures.

    The sentence appears three times, once in the template for the first render,
    once in the script for every poll after it, and once in the German
    catalogue. Two of them agreeing and the third one left behind is a page that
    changes its accusation three seconds after it opened, or one that is German
    on the server and English in the browser.
    """
    catalogue = json.loads(L10N_JSON.read_text(encoding="utf-8"))["translations"]

    assert STALLED_SENTENCE in TEMPLATE.read_text(encoding="utf-8")
    assert STALLED_SENTENCE in SCRIPT.read_text(encoding="utf-8")
    assert STALLED_SENTENCE in catalogue
    assert STALLED_SENTENCE_BEFORE not in catalogue


def test_the_stall_verdict_asks_both_halves_and_reads_the_counter_before_it_writes_it() -> None:
    """The mechanism behind the sentence above, held where it is decided.

    Two properties, and the second one is the trap. The age the page reports has
    to be the age of the LATER of the two movements, otherwise the container
    half is measured and then ignored. And the remembered indexed count has to
    be read BEFORE rememberIndexedCount writes the new one over it: the growth
    between two polls is the whole evidence, and the write destroys it. Both are
    the kind of line a later refactoring moves without noticing, and neither
    produces an error when it goes wrong. It reports a stall for eight hours
    instead, next to a coverage figure that is climbing (plan 05-14).
    """
    php = ADMIN_VIEW.read_text(encoding="utf-8")
    overview = php[php.index("public function overview(") : php.index("public function rules(")]

    assert "backendProgressAt(" in overview
    assert re.search(r"\$movedAt = max\(\s*\$lastJobRun,", overview) is not None
    assert re.search(r"\$stalledFor = \$movedAt === 0 \? 0 : max\(0, \$now - \$movedAt\)", overview) is not None
    assert overview.index("lastIndexedCount()") < overview.index("rememberIndexedCount(")
