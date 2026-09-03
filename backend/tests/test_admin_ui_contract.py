"""Gate C: the prohibitions of the phase 4 design contract, as far as text can judge them.

The contract in ``.planning/phases/04-admin-sichtbarkeit-und-diagnose/04-UI-SPEC.md``
ends in a list of prohibitions, and most of them are decisions a reader has to
keep in mind. A few are not: they are the presence or absence of a literal
string in one of three files, and those are the ones this gate holds. No markup
built from a string in the script, no unescaped printing in the template, no
inline script, no literal colour in the stylesheet, no removed focus ring, no
dash that is not a hyphen, no emoji, and none of the five Nextcloud APIs the
contract retired.

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

REPO_ROOT = Path(__file__).resolve().parents[2]

TEMPLATE = REPO_ROOT / "php" / "templates" / "admin.php"
STYLESHEET = REPO_ROOT / "php" / "css" / "admin.css"
SCRIPT = REPO_ROOT / "php" / "js" / "admin.js"

# The two hand written translation catalogues and the two PHP files that decide
# what the error list of the page can say. They are not part of the three files
# the prohibitions above are scanned in; the tests at the bottom read them for
# the two agreements this app has no tooling to enforce (IN-02 and DI-04-03).
L10N_JSON = REPO_ROOT / "php" / "l10n" / "de.json"
L10N_JS = REPO_ROOT / "php" / "l10n" / "de.js"
ADMIN_VIEW = REPO_ROOT / "php" / "lib" / "Service" / "AdminViewService.php"
FILE_STATE = REPO_ROOT / "php" / "lib" / "Service" / "FileStateService.php"

# The separator between the coverage figure and its sign, written as an escape
# on both sides of the page so that the agreement can be read in a diff (IN-03).
NBSP = "\u00a0"

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


Scanner = Callable[[str, str], list[str]]


def _sources() -> list[tuple[str, str, Scanner]]:
    """The three files of the page, as (name, source, scanner).

    The scanner is typed as what it is rather than as an object. With ``object``
    the call in the comprehension below is not a call any type checker can
    verify, and the gate would only fail on the release that starts to care.
    """
    return [
        (TEMPLATE.name, TEMPLATE.read_text(encoding="utf-8"), scan_template),
        (STYLESHEET.name, STYLESHEET.read_text(encoding="utf-8"), scan_stylesheet),
        (SCRIPT.name, SCRIPT.read_text(encoding="utf-8"), scan_script),
    ]


# -- the real tree ---------------------------------------------------------


def test_the_three_files_of_the_page_exist() -> None:
    # The anti vacuity clause. Every scanner below returns an empty list for a
    # file that is not there, so a gate that lost its files would look perfect.
    missing = [path.name for path in (TEMPLATE, STYLESHEET, SCRIPT) if not path.is_file()]

    assert missing == []


def test_the_page_breaks_none_of_the_checkable_prohibitions() -> None:
    violations = [message for name, source, scan in _sources() for message in scan(name, source)]

    assert violations == []


def test_no_file_of_the_page_carries_a_dash_or_an_emoji() -> None:
    violations = [message for name, source, _ in _sources() for message in scan_prose(name, source)]

    assert violations == []


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
    # from questioning the instance for a week.
    source = SCRIPT.read_text(encoding="utf-8")

    assert "AbortController" in source
    assert "visibilityState" in source


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
