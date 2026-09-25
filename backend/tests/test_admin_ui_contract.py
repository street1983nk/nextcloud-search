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
from collections.abc import Callable, Mapping
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
# docs/l10n-french.md rather than translating 24 of 174 strings.
#
# Hence: the same words under both codes, and a gate that holds the sameness
# instead of a comment that asks for it. Whoever wants to tell du from Sie later
# changes this test on purpose, which is the right amount of friction.
L10N_DE_DE_JSON = REPO_ROOT / "php" / "l10n" / "de_DE.json"
L10N_DE_DE_JS = REPO_ROOT / "php" / "l10n" / "de_DE.js"

# The third language, since plan 11-08. It is one language and not two codes, so
# it brings two files and not four: French knows no split between du and Sie,
# and ``fr_CA`` is not shipped. Both files are cast mechanically from the table
# in ``docs/l10n-french.md``, which the owner read and accepted on 11.09.2026.
L10N_FR_JSON = REPO_ROOT / "php" / "l10n" / "fr.json"
L10N_FR_JS = REPO_ROOT / "php" / "l10n" / "fr.js"

# The fourth language, since plan 20-04, and the first of the four that
# milestone v1.3 adds. Two files and not four, for the same reason as French:
# one language, one code. The code is ``es`` and not ``es_ES`` because that is
# the code the core carries for plain Spanish, and a catalogue under a code the
# core does not know is a file Nextcloud never opens.
#
# The core ships ``es_EC`` and ``es_MX`` next to ``es``; Findling deliberately
# ships neither, by the same decision that parks ``fr_CA``. A user on Spanish
# (Mexico) therefore sees Findling in English, and the three reasons for that
# are written out in section 2 of docs/l10n-catalogues.md, where the next reader
# finds an argument to refute rather than a forgotten file to suspect.
#
# The wordings are cast from the table in docs/l10n-spanish.md. That document
# carries a dated reservation and says in so many words that no native speaker
# has read them: machine translation plus the open community review of the app
# store, which is the accepted process E-17-5 and not an oversight. Both l10n
# files of this language are cast from the same table in one pass.
L10N_ES_JSON = REPO_ROOT / "php" / "l10n" / "es.json"
L10N_ES_JS = REPO_ROOT / "php" / "l10n" / "es.js"

# The fifth language, since plan 20-05, and the second of the four of milestone
# v1.3. Two files and not four, for the reason French and Spanish give: one
# language, one code.
#
# ``it`` carries no regional variant, and that is a finding and not an omission.
# The core of Nextcloud 34 and 35 ships ``es``, ``es_EC`` and ``es_MX`` next to
# each other and ``pt_PT`` next to ``pt_BR``, but for Italian it ships ``it.json``
# and ``it.js`` and nothing else; the directory listing is section 1 of
# docs/l10n-catalogues.md. So there is no variant to decide against here, while
# Spanish needed the decision written out in section 2 of that document and
# Portuguese needs two codes in plan 20-07. A catalogue under a code the core
# does not know is a file Nextcloud never opens.
#
# The wordings are cast from the table in docs/l10n-italian.md. That document
# carries a dated reservation and says in so many words that no native speaker
# has read them: machine translation plus the open community review of the app
# store, which is the accepted process E-17-5 and not an oversight. Both l10n
# files of this language are cast from the same table in one pass, which is why
# the gate below can compare them as two halves of one object.
L10N_IT_JSON = REPO_ROOT / "php" / "l10n" / "it.json"
L10N_IT_JS = REPO_ROOT / "php" / "l10n" / "it.js"

# The sixth language, since plan 20-05, and the third of the four of milestone
# v1.3. Two files and not four, for the reason French, Spanish and Italian give:
# one language, one code. The core of Nextcloud 34 and 35 ships ``nl.json`` and
# ``nl.js`` and no regional variant next to them, so ``nl_BE`` is not a decision
# this file had to take; the directory listing is section 1 of
# docs/l10n-catalogues.md.
#
# Dutch is the one language of this tree where two things are true at once that
# look like a contradiction, and both of them are written out here rather than
# discovered later:
#
#   * **Dutch carries two plural forms and not three.** ``FORM_COUNT_OF["nl"]``
#     is 2, next to the 3 of Spanish, Italian and both Portuguese codes. The five
#     plural values of nl.json therefore carry two forms each, cast from fr.json
#     and deliberately not from es.json. A third form would be an entry the rule
#     ``nplurals=2`` never addresses, so the browser would ask for an index the
#     rule cannot produce.
#   * **The Dutch rule is character for character the German one.**
#     ``nplurals=2; plural=(n != 1);`` stands in core/l10n/de.json and in
#     core/l10n/nl.json alike, measured on both instances of the version window
#     and written down in section 3 of docs/l10n-catalogues.md. It is taken from
#     the Dutch core file and not copied out of our German catalogue; that the
#     two results are equal is a property of the two languages.
#
# The second point is the reason ``scan_plural_rule`` judges per language code
# since plan 20-02 and no longer says "this file carries the German rule" without
# asking which language the file belongs to. It reports nothing for ``nl`` with
# this string and two findings for ``es`` with the same string, and that is the
# intended behaviour and not a hole in the scanner. Whoever reads this paragraph
# later should not start repairing it.
#
# The wordings are cast from the table in docs/l10n-dutch.md. That document
# carries a dated reservation and says in so many words that no native speaker
# has read them: machine translation plus the open community review of the app
# store, which is the accepted process E-17-5 and not an oversight. Both l10n
# files of this language are cast from the same table in one pass.
L10N_NL_JSON = REPO_ROOT / "php" / "l10n" / "nl.json"
L10N_NL_JS = REPO_ROOT / "php" / "l10n" / "nl.js"

# The seventh language, since plan 20-07, and the fourth of the four of
# milestone v1.3. It is the one language of this tree that brings two codes
# without being one language written twice, so three things are written out
# here rather than guessed later.
#
# **Why the code is ``pt_PT`` and not ``pt``.** Nextcloud builds the catalogue
# file name from the language code without any shortening:
# ``getL10nFilesForApp`` appends ``.json`` to the code, and ``validateLanguage``
# checks every step again with ``languageExists``. Nowhere is ``pt_PT`` cut back
# to ``pt``. That is not read out of the source but asked of a running instance,
# and the answer of 25.09.2026 stands in section 1 of docs/l10n-catalogues.md:
# with a real ``php/l10n/pt.json`` lying next to it, a user on ``pt_PT`` still
# resolved to ``en``. And nobody can stand on ``pt`` either, because
# ``core/l10n/`` of Nextcloud 34 and 35 ships ``pt_PT`` and ``pt_BR`` and no
# ``pt`` at all. A ``pt.json`` would therefore be a file that passes every gate
# in here and that no user ever opens, which is why this plan is forbidden from
# writing one.
#
# **Why ``pt_BR`` will not be a copy of this file.** Plan 20-08 adds the second
# Portuguese code, and it adds its own wordings. This is the explicit opposite
# of the ``de``/``de_DE`` pair one paragraph further up, whose text equality is
# argued there and held by a gate: German has two codes for one set of words,
# Portuguese has two codes for two sets of words. ``ficheiro`` against
# ``arquivo``, ``utilizador`` against ``usuário``, ``ecrã`` against ``tela``,
# ``a transferir`` against ``baixando``. So there is deliberately **no** text
# equality gate for ``pt_PT`` against ``pt_BR`` in this file, and building one
# later would freeze one of the two varieties in the wrong words. The positive
# counterpart, a gate over the named differences, belongs to plan 20-08, when
# the second file exists to compare against.
#
# The wordings are cast from the table in docs/l10n-portuguese.md. That document
# carries a dated reservation and says in so many words that no native speaker
# has read them: machine translation plus the open community review of the app
# store, which is the accepted process E-17-5 and not an oversight. Both l10n
# files of this language are cast from the same table in one pass. Its table
# carries three columns today and four after plan 20-08; the missing column is
# announced above it rather than left empty, because an empty cell looks like a
# forgotten translation.
L10N_PT_PT_JSON = REPO_ROOT / "php" / "l10n" / "pt_PT.json"
L10N_PT_PT_JS = REPO_ROOT / "php" / "l10n" / "pt_PT.js"

# All catalogues in the order the gates below name them. Held as one tuple so
# that the next file is added in one place and every gate sees it.
L10N_CATALOGUES = (
    L10N_JSON,
    L10N_JS,
    L10N_DE_DE_JSON,
    L10N_DE_DE_JS,
    L10N_FR_JSON,
    L10N_FR_JS,
    L10N_ES_JSON,
    L10N_ES_JS,
    L10N_IT_JSON,
    L10N_IT_JS,
    L10N_NL_JSON,
    L10N_NL_JS,
    L10N_PT_PT_JSON,
    L10N_PT_PT_JS,
)

# The common proof of every catalogue of milestone v1.3, written by plan 20-02:
# where Nextcloud looks for a catalogue, which plural rule each language declares
# and which form PHP and the browser pick. It is read here for one paragraph of
# it, the block of shipped rules, because a document and a constant that say the
# same thing have to be able to call each other wrong.
L10N_DOCUMENTATION = REPO_ROOT / "docs" / "l10n-catalogues.md"

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

# A style attribute on an element, in either spelling of the quotes. The look
# ahead behind excludes a name that merely ends in the word, so neither
# ``data-style="x"`` nor an attribute called ``font-style`` is mistaken for one.
_STYLE_ATTRIBUTE = re.compile(r"""(?<![0-9a-zA-Z_-])style\s*=\s*["']""")

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

    # The same decision one attribute further on, added in plan 13-10. A style
    # attribute is the CSS counterpart of an inline script: a declaration that
    # no stylesheet of this app can be read out of, that no theme variable
    # reaches and that the next dark mode forgets. Both pages carry their look
    # in a stylesheet, so the attribute is never the answer here. Held by this
    # scanner rather than by a second gate for the result page alone, because
    # the rule is the same one for both templates.
    if _STYLE_ATTRIBUTE.search(source) is not None:
        violations.append(f"{name}: carries a style attribute, which no stylesheet and no theme variable can reach")

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


# -- the four gates over the six catalogues (plan 11-08) -------------------
#
# The French catalogue arrives with plan 11-08 and brings a question the two
# German codes never asked: how do you hold two catalogues together that must
# not say the same thing? For German the answer is text equality, and it is
# asserted below. For French it would be nonsense. What takes its place is the
# placeholder parity of G3, the one invariant a translation can keep word for
# word, and the reason it is worth a gate is that breaking it produces no error
# message at all. It produces a sentence that no longer names the file it is
# about.

# The plural rule of the third language, and the one it must not be. The two
# differ at n = 0: French puts the singular there ("0 jour"), German the plural.
# A fr.json copied from de.js is wrong on exactly that one value and on nothing
# else, which is why it survives every diff and every glance at the page.
FRENCH_PLURAL_FORM = "nplurals=2; plural=(n > 1);"
GERMAN_PLURAL_FORM = "nplurals=2; plural=(n != 1);"

# The rule every language code of this tree declares, mapped to the string its
# catalogues have to carry. Read verbatim on 25.09.2026 out of
# ``core/l10n/<code>.json`` of both Nextclouds of the version window, 34.0.3 and
# 35.0.0, which carry the same string character for character; the reading and
# the command that repeats it stand in docs/l10n-catalogues.md, section 3.
#
# Five of the eight codes have no catalogue file yet and stand here all the same,
# because the rule comes out of the core file and not out of our catalogue.
# Keeping the read ones apart from the unread ones would mean maintaining one
# table twice and deciding, on the day a file arrives, which of the two halves
# was right.
#
# ``fr`` is the single entry that is not the core rule. Nextcloud 34 and 35 run
# French with ``nplurals=3``; Findling ships two forms since plan 11-08, and that
# variant is correct in both of its halves. Changing it would reword sentences
# the owner accepted on three dates, for nothing. It is also why this is a
# mapping and no longer two constants: ``fr`` stays at two forms while ``es``
# goes to three, and a gate with two constants cannot hold both at once.
PLURAL_FORM_OF = {
    "de": GERMAN_PLURAL_FORM,
    "de_DE": GERMAN_PLURAL_FORM,
    "fr": FRENCH_PLURAL_FORM,
    "es": "nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;",
    "it": "nplurals=3; plural=n == 1 ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;",
    "nl": GERMAN_PLURAL_FORM,
    "pt_PT": "nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;",
    "pt_BR": "nplurals=3; plural=(n == 0 || n == 1) ? 0 : n != 0 && n % 1000000 == 0 ? 1 : 2;",
}

# How many forms a plural value of each catalogue has to carry. Written down and
# deliberately not parsed out of the ``nplurals=`` of the rule above: a parsed
# number would hang on the very string this gate judges, so a catalogue that
# declared a wrong rule would build itself a matching expectation and both halves
# of the gate would agree on the same mistake. Two numbers from two sources
# disagree loudly; one number from one source cannot disagree at all.
FORM_COUNT_OF = {
    "de": 2,
    "de_DE": 2,
    "fr": 2,
    "es": 3,
    "it": 3,
    "nl": 2,
    "pt_PT": 3,
    "pt_BR": 3,
}

# The plural rule of a ``.js`` catalogue is the fourth argument of
# ``OC.L10N.register`` and therefore the last quoted string of the file. It is
# cut out here instead of being looked for with ``in``, so that both halves of a
# language go through the same scanner: a ``.js`` that merely contains the right
# rule somewhere would pass a containment test while declaring another one.
JS_PLURAL_FORM = re.compile(r'\n"([^"]*)"\);\s*\Z')

# The named exceptions of gate G2, taken from the section "Ausnahmen fuer das
# Vollstaendigkeitsgate G2" of docs/l10n-french.md. A list and deliberately not
# a threshold: a number that says "this many values may equal their key" covers
# a forgotten wording exactly as well as an intended one, while a list names each
# of them and nothing else. The reason travels with the key, so a third entry has
# to be argued rather than counted.
#
# With phase 13 the list grows from two entries to five, and the three that join
# it are file type chips of the filter row: an abbreviation that is the proper
# name of a format, and two words French writes exactly as English does. Each of
# them is argued here rather than counted, which is what the shape of this list
# is for. The alternative not taken is a threshold of five, and it would have
# covered a fourth chip nobody translated exactly as quietly as it covers these
# three.
#
# Since plan 20-03 the list is one entry of a table per language code, and the
# paragraph above is the reason for every one of them and not only for the
# French one. A language whose code is missing from this table is a failure that
# names it rather than an empty mapping: a language without a list of exceptions
# is a language whose exceptions nobody argued, and that is exactly the state in
# which a forgotten wording travels as an intended one.
#
# German is not the empty entry it looks like it should be. The German values
# are the reference the others are compared against, so the expectation was that
# no German value equals its English key; the tree says otherwise and was read on
# 25.09.2026 rather than assumed. Four keys do, and each of them is a proper name
# or a word German writes the way English does.
VALUES_THAT_MAY_EQUAL_THEIR_KEY = {
    "de": {
        "Findling": "the name of the app, the same word in every language of this tree",
        "%1$s in %2$s": "two placeholders and the preposition between them, which German spells the same way",
        "PDF": "the proper name of a file format, the same abbreviation in every language of this tree",
        "Text": "the same word in German, and an invented difference would be a mistranslation",
    },
    # Spanish, read off the file on 25.09.2026 rather than guessed: the gate was
    # run once with an empty list and reported four findings, two keys over two
    # files. Both are proper names, and both would be a mistranslation if a
    # difference were invented for them. Every other value of es.json carries a
    # Spanish wording, which is why this list is shorter than the French one.
    "es": {
        "Findling": "the name of the app, the same word in every language of this tree",
        "PDF": "the proper name of a file format, the same abbreviation in every language of this tree",
    },
    # Italian, read off the file on 25.09.2026 rather than guessed: the gate was
    # run once with an empty list and reported six findings, three keys over two
    # files. Two of them are proper names, and the third is the preposition
    # between two placeholders, which Italian writes exactly as English and
    # German do. It is the same key the German entry above carries, and for the
    # same reason; that two languages arrive at it independently is what makes it
    # an exception rather than a forgotten line. Every other value of it.json
    # carries an Italian wording, so this list is three long and not five like
    # the French one: Page %s, Documents and Images are Pagina %s, Documenti and
    # Immagini.
    "it": {
        "Findling": "the name of the app, the same word in every language of this tree",
        "%1$s in %2$s": "two placeholders and the preposition between them, which Italian spells the same way",
        "PDF": "the proper name of a file format, the same abbreviation in every language of this tree",
    },
    # Dutch, read off the file on 25.09.2026 rather than guessed: the gate was
    # run once with an empty list and reported eight findings, four keys over
    # two files. That is one more key than Italian and two more than Spanish,
    # and the reason is a property of the language rather than a forgotten line:
    # Dutch has taken more English technical words into its own vocabulary than
    # the Romance languages have. Each of the four is argued here, because a
    # language that writes a word the English way needs the argument exactly as
    # much as one that forgot to translate it.
    "nl": {
        "Findling": "the name of the app, the same word in every language of this tree",
        "%1$s in %2$s": "two placeholders and the preposition between them, which Dutch spells the same way",
        "PDF": "the proper name of a file format, the same abbreviation in every language of this tree",
        "Spreadsheets": "the word the Dutch Nextcloud interface itself uses for this file type chip",
    },
    # European Portuguese, read off the file on 25.09.2026 rather than guessed:
    # the gate was run once with an empty list and reported four findings, two
    # keys over two files. That is the shortest list of this tree, as short as
    # the Spanish one, and the reason is a property of the language rather than
    # a thorough translation round: Portuguese writes the preposition between
    # the two placeholders as ``em`` and not as ``in``, so the key the German,
    # Italian and Dutch lists all carry is not an exception here. Both entries
    # are proper names, and both would be a mistranslation if a difference were
    # invented for them.
    "pt_PT": {
        "Findling": "the name of the app, the same word in every language of this tree",
        "PDF": "the proper name of a file format, the same abbreviation in every language of this tree",
    },
    "fr": {
        "Findling": "the name of the app, the same word in all three languages",
        "Page %s": "Page is the same word in French, and a difference would be a loss",
        "PDF": "the proper name of a file format, the same abbreviation in all three languages",
        "Documents": "the same word in French, and an invented difference would be a mistranslation",
        "Images": "the same word in French, and an invented difference would be a mistranslation",
    },
}

# ``de_DE`` carries the same words as ``de`` by the decision written above
# ``L10N_DE_DE_JSON``, so it carries the same exceptions. It is bound to the
# German entry instead of being spelled out a second time, because two copies of
# one list are two things that have to stay equal and
# ``test_the_german_catalogue_covers_both_german_language_codes`` already holds
# the sameness of the words themselves.
VALUES_THAT_MAY_EQUAL_THEIR_KEY["de_DE"] = VALUES_THAT_MAY_EQUAL_THEIR_KEY["de"]

# The printf directives a value has to carry in the same number as its key: the
# numbered form with the dollar sign, the plain one, the %n of the plural forms
# and the doubled percent sign. Nextcloud fills them with vsprintf, so a lost
# %2$s is not a typo but a call whose argument goes nowhere.
PRINTF_DIRECTIVE = re.compile(r"%%|%\d+\$[sd]|%[sdn]")


def forms_of(value: str | list[str]) -> list[str]:
    """Every form of a catalogue value: one for a sentence, two for a plural."""
    return value if isinstance(value, list) else [value]


def catalogue_of(path: Path) -> dict[str, str | list[str]]:
    """The mapping of one catalogue, read the way Nextcloud reads it.

    The JSON straight from PHP, and out of the ``.js`` the object between the
    first brace and the last, because the file is a call of ``OC.L10N.register``
    and not an object. That cut is the one
    ``test_the_two_translation_files_carry_the_same_keys`` already makes; a
    second way of finding the same object would be a second thing to keep right.
    """
    source = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(source)["translations"]
    return json.loads(source[source.index("{") : source.rindex("}") + 1])


# A line of the rule block of the documentation: a language code, at least two
# spaces, and the rule that language ships, to the end of the line. The two
# spaces are what tells this block from the table above it, where the code is
# followed by the number of forms and by a column saying whether both Nextclouds
# of the version window agree; there the word ``nplurals`` stands in the fourth
# column and not in the second.
DECLARED_RULE = re.compile(r"^(\w+) {2,}(nplurals=.+;)$", re.MULTILINE)


def rules_declared_in(text: str) -> dict[str, str]:
    """The plural rule per language code as the documentation writes it down."""
    return dict(DECLARED_RULE.findall(text))


def language_code_of(path: Path) -> str:
    """The language code a catalogue file belongs to, read off its name.

    ``fr.json`` is ``fr`` and ``pt_BR.js`` is ``pt_BR``: the code is everything
    before the suffix, and the underscore of a regional code is part of it. This
    is one line and stands here all the same, because the alternative is a second
    table from file to code next to ``L10N_CATALOGUES``, and a second table is a
    second place where a new language is forgotten.
    """
    return path.stem


def scan_key_sets(keys_of: Mapping[str, frozenset[str]]) -> list[str]:
    """Findings over the catalogues: a file whose key set differs from the first."""
    reference_name = next(iter(keys_of))
    reference = keys_of[reference_name]
    return [
        f"{name}: differs from {reference_name} in {sorted(keys ^ reference)}"
        for name, keys in keys_of.items()
        if keys != reference
    ]


def scan_completeness(
    name: str,
    catalogue: Mapping[str, str | list[str]],
    exceptions: Mapping[str, str],
) -> list[str]:
    """Findings of one catalogue: a value empty or still in English.

    The emptiness runs over every form, because an empty second plural form is
    a blank line on the page for every number above one. The identity with the
    source string is judged on the value and not on the single form, and that is
    a decision rather than an oversight: the singular of ``%n minute`` is ``%n
    minute`` in French, correctly so, and a per form comparison would demand a
    further exception for a value that is translated. It is the same reading the
    machine checks of docs/l10n-french.md take, where the count of values equal
    to their source string is five, every one of them named.

    The exceptions arrive as a parameter since plan 20-03, and that is the whole
    difference to the French scanner this one used to be. A module constant made
    this function one that happened to run over French; a parameter makes it the
    same function for every language, and the caller is the one place that
    decides which language it is judging.
    """
    violations: list[str] = []
    for key, value in catalogue.items():
        violations.extend(f"{name}: {key!r} has an empty value" for form in forms_of(value) if form.strip() == "")
        if value == key and key not in exceptions:
            violations.append(f"{name}: {key!r} is still the English source string")
    return violations


def expected_directives_per_form(key: str) -> tuple[list[str], list[str]]:
    """The directives a key demands of its first form and of every further one.

    Nextcloud keeps a plural under ``_<singular>_::_<plural>_``, so such a key is
    the concatenation of two source strings and not one. It therefore carries
    every directive twice while each form carries it once, and a comparison
    against the whole key would hold every translated plural for incomplete. Cut
    at the mark, drop the leading underscore of the left half and the trailing
    one of the right, and each form is judged against the source string it really
    translates: the singular half against form 0, the plural half against the
    rest.

    A key without the mark keeps the reading of before: one expectation for all
    forms. The cut lives here and only here, so that the scanner below reads as
    one comparison and a second shape of the same split cannot drift in.
    """
    if "_::_" not in key:
        expected = sorted(PRINTF_DIRECTIVE.findall(key))
        return expected, expected

    singular, plural = key.split("_::_", 1)
    return (
        sorted(PRINTF_DIRECTIVE.findall(singular.removeprefix("_"))),
        sorted(PRINTF_DIRECTIVE.findall(plural.removesuffix("_"))),
    )


def scan_placeholder_parity(name: str, catalogue: Mapping[str, str | list[str]]) -> list[str]:
    """Findings of a catalogue: a value whose directives are not those of its key.

    The expectation comes from ``expected_directives_per_form`` and is two
    expectations rather than one, because a plural key is two source strings
    glued together; the reason stands in that docstring. The finding names the
    form it was made in, so that a loss in the second form does not read like a
    loss in the first.
    """
    violations: list[str] = []
    for key, value in catalogue.items():
        first_form, further_forms = expected_directives_per_form(key)
        for index, form in enumerate(forms_of(value)):
            expected = first_form if index == 0 else further_forms
            found = sorted(PRINTF_DIRECTIVE.findall(form))
            if found != expected:
                violations.append(f"{name}: {key!r} form {index} carries {found} where its key carries {expected}")
    return violations


# The hint every finding of the percent scanner ends with. It stands here once
# because both shapes of the finding, the one about a key and the one about a
# form, have to say the same thing: the fix is not to remove the percent sign
# but to double it.
PERCENT_HINT = "a literal percent sign is written %%"

# The same for the pipe scanner, and it names the cause rather than the fix,
# because there is no spelling that works: the character is the separator
# Nextcloud joins the plural forms with, and a wording that needs one has to say
# it with another word.
PIPE_HINT = "a pipe character, which Nextcloud reserves as the plural separator"


def _carries_a_bare_percent(text: str) -> bool:
    """Whether a text carries a percent sign outside a recognised directive.

    A counting comparison and deliberately no second regular expression: the
    number of ``%`` characters of the text has to equal the number of ``%``
    characters the directives of ``PRINTF_DIRECTIVE`` consume in it. ``%%`` is
    two and is consumed as two, ``%1$s`` and ``%s`` are one each, and anything
    left over is a percent sign that stands on its own.

    A second regular expression for "a percent sign that is not a directive"
    would be a second definition of a directive, and the two would drift on the
    day somebody adds ``%1$d`` to the first one.
    """
    return text.count("%") != sum(match.count("%") for match in PRINTF_DIRECTIVE.findall(text))


def scan_percent_discipline(name: str, catalogue: Mapping[str, str | list[str]]) -> list[str]:
    """Findings of a catalogue: a percent sign that is not part of a directive.

    The measured reason, and it is not a matter of taste.
    ``OC\\L10N\\L10NString::__toString`` ends in ``vsprintf($text, $parameters)``,
    and ``vsprintf("50 % de los archivos", [])`` throws
    ``ValueError: The arguments array must contain 1 items, 0 given`` under PHP
    8.5.9 (20-RESEARCH.md, pitfall 3, measured 24.09.2026). That is not a wrong
    sentence on the page, it is no page at all, and the four languages this phase
    is written for write percent exactly that way: Spanish and Portuguese put a
    space between the number and the sign.

    ``scan_placeholder_parity`` cannot see this. It counts the directives it
    recognises on both sides and finds none on either, so a value with a bare
    percent sign is parity perfect and lethal at the same time.

    The scan runs over the **key** as well as over every form of the value. An
    English source string with a bare percent sign is the same broken page one
    level earlier, and it would reach the page through ``de.json`` before any
    translation of it exists.
    """
    violations: list[str] = []
    for key, value in catalogue.items():
        if _carries_a_bare_percent(key):
            violations.append(f"{name}: the key {key!r} carries a bare percent sign; {PERCENT_HINT}")
        violations.extend(
            f"{name}: {key!r} form {index} carries a bare percent sign; {PERCENT_HINT}"
            for index, form in enumerate(forms_of(value))
            if _carries_a_bare_percent(form)
        )
    return violations


def scan_pipe_character(name: str, catalogue: Mapping[str, str | list[str]]) -> list[str]:
    """Findings of a catalogue: a value or a key carrying a pipe character.

    ``L10NString::__toString`` joins the plural forms with ``|`` and gives up
    before it starts if the text already carries one:
    ``if (str_contains($pipeCheck, '|')) return 'Can not use pipe character in
    translations';``. The user then reads that English sentence instead of the
    translation, on a page that is otherwise entirely in their language
    (20-RESEARCH.md, pitfall 4).

    The tree carries zero pipes today, so this gate is green from its first day,
    and that is exactly why the staged lines of its gate matter more here than
    anywhere else: a scan over a clean tree and a scan whose body was deleted
    report the same empty list.
    """
    violations: list[str] = []
    for key, value in catalogue.items():
        if "|" in key:
            violations.append(f"{name}: the key {key!r} carries {PIPE_HINT}")
        violations.extend(
            f"{name}: {key!r} form {index} carries {PIPE_HINT}"
            for index, form in enumerate(forms_of(value))
            if "|" in form
        )
    return violations


def scan_plural_rule(name: str, code: str, plural_form: str) -> list[str]:
    """Findings of one catalogue: the plural rule it declares for its language.

    Two findings and not one, because a wrong rule and a rule copied out of the
    German catalogue are two different mistakes and the second one names its
    cause: German answers n = 0 with the plural, and a file that took its rule
    from de.js is wrong at exactly that one number and right everywhere else,
    which is how it survives every diff.

    The German check is language aware, and Dutch is the case that forced it to
    be. ``nl`` declares ``nplurals=2; plural=(n != 1);``, the same string as
    German, character for character, because that is the rule of both languages.
    A scan that reported "carries the German plural rule" on sight would be red
    forever on a Dutch catalogue in which nothing whatsoever is wrong, and a red
    gate that is right to be ignored is worse than no gate. The German rule is
    therefore only a finding when it is the German one *and* not the one this
    code is supposed to carry.
    """
    expected = PLURAL_FORM_OF[code]
    violations: list[str] = []
    if GERMAN_PLURAL_FORM in plural_form and expected != GERMAN_PLURAL_FORM:
        violations.append(f"{name}: carries the German plural rule, which is not the rule of {code}")
    if plural_form != expected:
        violations.append(f"{name}: carries {plural_form!r} and not the {expected!r} of {code}")
    return violations


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


# -- the prohibitions of phase 13 that text can judge ----------------------
#
# 13-UI-SPEC marks six points of its prohibition list with [G], which means
# "this one can be read off a file". A prohibition without a gate is an
# intention: it holds until the next rebuild, and nothing says a word on the day
# it stops holding. The ones below are the ones the contract itself declared
# checkable, and they are held in the shape the rest of this file has: a scanner
# that reads a source and names every finding, an anti vacuity clause that
# proves the scanner read something, and a self test that proves the scanner can
# still go red. Two of the six are not here: the literal colour and the removed
# focus ring are already ``scan_stylesheet``, the inline script and the style
# attribute are already ``scan_template``, and the dash and the emoji in the new
# catalogue values are ``scan_prose`` and arrive with plan 13-11.

# The class names of the filter row, all of them. The script of the result page
# must not know a single one: every one of the fourteen controls is a link that
# carries a finished address out of the controller, so the row works with script
# switched off, a middle click opens any of them in a tab, and the back button
# means what it always meant (13-CONTEXT D-02, D-03 and D-05). ``aria-current``
# travels with them because it is the attribute a script would reach for if it
# ever started to move the state around in the browser instead of asking the
# server for the next page.
FILTER_ROW_MARKERS = (
    "findling-filters",
    "findling-chip-link",
    "findling-sort",
    "aria-current",
)


def scan_page_script_for_the_filter_row(name: str, source: str) -> list[str]:
    """Findings of the result page script: any sign that it knows the filter row."""
    return [
        f"{name}: names {marker}, and the filter row is served by the server and not by a script"
        for marker in FILTER_ROW_MARKERS
        if marker in source
    ]


# The two elements that would turn the type choice into a form, and the count of
# the one form this page has. A select is the obvious way to offer ten choices
# and the wrong one here: it needs a submit or a listener, it hides the whole
# set of choices behind a closed control, and it cannot show which of them are
# in force, which is the one thing FILT-04 asks of this row (D-02).
_SELECT_ELEMENT = re.compile(r"<\s*(select|option)\b", re.IGNORECASE)
_FORM_ELEMENT = re.compile(r"<\s*form\b", re.IGNORECASE)


def scan_page_template_for_a_second_control_channel(name: str, source: str) -> list[str]:
    """Findings of the result page template: a select, an option, or a second form."""
    findings = [
        f"{name}: carries a <{element}> element, and the choices of this page are links"
        for element in sorted({found.lower() for found in _SELECT_ELEMENT.findall(source)})
    ]

    forms = len(_FORM_ELEMENT.findall(source))
    if forms != 1:
        findings.append(f"{name}: carries {forms} form elements, and this page has exactly one, the search field")

    return findings


# The state marker of a button, on a page whose every control is a link.
# ``aria-pressed`` belongs to ``role="button"``; an ``a`` element with an href
# is a link, and a pressed link is nothing. What the chips and the sort links
# announce instead is ``aria-current="true"``, the marker for "this one of the
# group is the one in force" (13-RESEARCH finding 11).
PRESSED_STATE = "aria-pressed"

APP_TEMPLATE_ROOT = REPO_ROOT / "php" / "templates"


def scan_template_for_a_pressed_link(name: str, source: str) -> list[str]:
    """Findings of one template of the app: the pressed marker of a button."""
    if PRESSED_STATE in source:
        return [f"{name}: carries {PRESSED_STATE}, which belongs to a button role, and a pressed link is nothing"]
    return []


def _app_templates() -> list[tuple[str, str]]:
    """Every template of the companion app, as (name, source)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in sorted(APP_TEMPLATE_ROOT.glob("*.php"))]


# The two markers that cut the filter row out of the template, and both of them
# are the comment opener of a block rather than a class name. Cutting on the
# opener is what lets the comments inside the region be stripped: the region
# then begins with a ``/*`` of its own, and the expression below closes it on
# the first ``*/``.
FILTER_ROW_START = "<?php /* Block 2b:"
FILTER_ROW_END = "<?php /* Block 3:"

_PHP_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)

# Every shape a count beside a chip could take, and the reason they are one
# prohibition and not four: a number, a dot, a greyed out chip and a plural
# sentence are the same piece of information, namely how many files of that kind
# this user would see. It would be worked out in front of the permission
# recheck, which is the one place that knows what the user may open, so it would
# be an answer about other people's files (T-02-93, T-13-47). The plural call is
# in the list because a counted sentence cannot be built without it, and
# ``disabled`` because greying a chip out says "nothing behind this one" as
# loudly as a nought would.
COUNT_ORACLE_MARKERS = ("count", "total", "badge", "disabled", "$l->n(")


def filter_row_of(source: str) -> str:
    """The region of the template between the two block markers, or the empty string."""
    start = source.find(FILTER_ROW_START)
    end = source.find(FILTER_ROW_END)
    if start == -1 or end == -1 or end <= start:
        return ""
    return source[start:end]


def scan_filter_row_for_a_counting_oracle(name: str, source: str) -> list[str]:
    """Findings of the filter row: any shape of an answer about what is behind a chip."""
    region = filter_row_of(source)
    if region == "":
        return [f"{name}: the filter row is no longer between {FILTER_ROW_START!r} and {FILTER_ROW_END!r}"]

    # The comments of the region are stripped first, and that is the whole
    # reason the region is cut on a comment opener. The block comment of the row
    # explains why there is no count, no dot and no greyed out chip, so a scan
    # over the raw text would go red on the very sentence that promises what
    # this gate holds.
    code = _PHP_BLOCK_COMMENT.sub("", region).lower()

    return [
        f"{name}: the filter row carries {marker!r}, which answers what is behind a chip before it is clicked"
        for marker in COUNT_ORACLE_MARKERS
        if marker in code
    ]


# The three controls of the row that a thumb aims at, and the three containers
# that wrap instead of scrolling sideways. Two halves of one promise: every
# control of the row is reachable, with a mouse, with a thumb and with a
# keyboard. A row out of which part of the choice has been pushed hides controls
# behind a gesture, and on a keyboard it cannot be found at all (T-13-51).
TOUCH_CONTROLS = (".findling-chip-link", ".findling-sort__link", ".findling-filters__reset")
WRAPPING_ROWS = (".findling-filters__row", ".findling-filters__group", ".findling-sort")

COARSE_QUERY = "@media (pointer: coarse)"


def block_body_of(source: str, opener: str) -> str:
    """The body of the rule or the query that begins at column zero with ``opener``."""
    match = re.search(rf"(?m)^{re.escape(opener)} \{{\n(?P<body>.*?)^\}}", source, re.DOTALL)
    return "" if match is None else match.group("body")


def scan_page_stylesheet_for_a_reachable_row(name: str, source: str) -> list[str]:
    """Findings of the result page stylesheet: a control too small or a row that scrolls."""
    findings: list[str] = []

    for selector in TOUCH_CONTROLS:
        body = block_body_of(source, selector)
        if body == "":
            findings.append(f"{name}: has no rule for {selector}")
        elif "min-height: var(--default-clickable-area)" not in body:
            findings.append(f"{name}: {selector} is not as tall as a clickable area of the theme")

    coarse = block_body_of(source, COARSE_QUERY)
    if coarse == "":
        findings.append(f"{name}: has no {COARSE_QUERY} query, so nothing on this page grows for a thumb")
    else:
        findings.extend(
            f"{name}: {selector} does not grow to 44px under a coarse pointer"
            for selector in TOUCH_CONTROLS
            if re.search(rf"{re.escape(selector)}[,\s][^}}]*min-height: 44px", coarse, re.DOTALL) is None
        )

    findings.extend(
        f"{name}: {selector} does not wrap, so the row would have to be scrolled sideways"
        for selector in WRAPPING_ROWS
        if "flex-wrap: wrap" not in block_body_of(source, selector)
    )

    if "overflow-x" in source:
        findings.append(f"{name}: carries overflow-x, and ten short words wrap rather than scroll out of sight")

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


def test_every_file_of_the_two_pages_exists() -> None:
    # The anti vacuity clause. Every scanner below returns an empty list for a
    # file that is not there, so a gate that lost its files would look perfect.
    # Six paths since plan 09-06, and the count is the point of the clause: a
    # gate that reads nothing reports nothing, so the cleanest possible run of
    # this file is also the one in which it has stopped judging anything at all.
    #
    # The number left the name with plan 20-03. It was the last one in this file
    # that would have to be dragged along at a change nobody makes for its sake:
    # a third page brings eight paths, and a name that still said six would be
    # the note the next reader trusts instead of the tuple. The count itself
    # stays where it belongs, in the list below, which is the only place it can
    # be wrong and be seen.
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
    """The prohibition of the contract, over the six files of the pages and the six catalogues.

    The catalogues joined this scan with plan 11-08, and French is the reason.
    French typography brings guillemets and apostrophes with it and both are
    harmless here, but the em dash is common in French typesetting and would
    come in with the next wording, in a file that no gate of this repository had
    ever read. The German catalogues are read along with them: a rule that holds
    for one language and not for the others is the kind of asymmetry nobody
    remembers a year later.
    """
    violations = [message for name, source, _ in _sources() for message in scan_prose(name, source)]
    violations += [
        message for path in L10N_CATALOGUES for message in scan_prose(path.name, path.read_text(encoding="utf-8"))
    ]

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


def test_the_page_script_knows_nothing_about_the_filter_row() -> None:
    """The first [G] prohibition of phase 13: no script for filter or sort.

    The promise of D-02, D-03 and D-05 in one sentence: the filter row is served
    by the server. Every chip, every sort link and the reset link is an ordinary
    link on a finished address, so the whole row works with script switched off,
    a middle click opens any of them in a tab, and the back button means what it
    always meant. The one purpose of this file stays the return mark.

    **What this gate does not prove.** It reads names and not behaviour. A
    listener bound to a bare ``a`` element would carry none of these strings and
    would still take the row away from the browser; what keeps that out is
    ``test_the_page_script_does_not_intercept_a_click`` above, which forbids the
    one call that would be needed to make such a listener matter.
    """
    findings = scan_page_script_for_the_filter_row(PAGE_SCRIPT.name, PAGE_SCRIPT.read_text(encoding="utf-8"))

    assert findings == []
    # The anti vacuity clause: the file was read and it is not empty, so a clean
    # answer is an answer about a script and not about nothing.
    assert PAGE_SCRIPT.read_text(encoding="utf-8").strip() != ""
    # And it can go red, in the shape it would really arrive in: somebody wires
    # the chips up client side to save a page load.
    dirty = "document.querySelectorAll('.findling-chip-link').forEach(function (chip) {})\n"
    assert len(scan_page_script_for_the_filter_row("sample.js", dirty)) == 1


def test_the_filter_row_is_not_a_form_and_carries_no_select() -> None:
    """The second [G] prohibition: no select, no option and no second form.

    A select is the obvious way to offer ten choices and the wrong one on this
    page. It needs a submit button or a listener, it hides the whole set of
    choices behind a closed control, and it cannot show which of them are in
    force. The page answers with links instead, and it keeps exactly one form:
    the search field, which carries the active filters as hidden fields so that
    a sharpened term does not lose the narrowing.

    **What this gate does not prove.** It counts elements and does not read what
    the one form sends. Which fields travel with it is decided in
    ``PageController::formFilters()`` and asserted on the PHP side.
    """
    findings = scan_page_template_for_a_second_control_channel(
        PAGE_TEMPLATE.name, PAGE_TEMPLATE.read_text(encoding="utf-8")
    )

    assert findings == []
    # The anti vacuity clause, and it is the count itself: a template that lost
    # its form is reported, so a clean answer means one form was found.
    assert "<form" in PAGE_TEMPLATE.read_text(encoding="utf-8")
    # And it can go red on both halves, the element and the count.
    dirty = '<form action="/"><select name="types"><option value="pdf">PDF</option></select></form>\n<form></form>\n'
    assert len(scan_page_template_for_a_second_control_channel("sample.php", dirty)) == 3


def test_no_template_of_the_app_presses_a_link() -> None:
    """The third [G] prohibition: no aria-pressed on an a element.

    ``aria-pressed`` belongs to ``role="button"``. An ``a`` element with an href
    is a link, and a pressed link is nothing: a screen reader either says
    something meaningless or says nothing at all, and the state of the chip is
    then carried by its colour alone. The row uses ``aria-current="true"``,
    which is announced as "current".

    **What this gate does not prove.** It forbids the string in every template
    and does not ask which element carried it. That is deliberate: neither page
    has a control that would legitimately be pressed, so there is no case to
    make an exception for, and a scan that paired the attribute with its element
    would be a small HTML parser nobody wants to maintain here.
    """
    findings = [
        message for name, source in _app_templates() for message in scan_template_for_a_pressed_link(name, source)
    ]

    assert findings == []
    # The anti vacuity clause of the scan: a glob that stopped matching, or a
    # directory that moved, would report nothing over nothing.
    assert sorted(name for name, _ in _app_templates()) == ["admin.php", "search.php"]
    # And it can go red.
    dirty = '<a class="findling-chip-link" aria-pressed="true" href="/">PDF</a>\n'
    assert len(scan_template_for_a_pressed_link("sample.php", dirty)) == 1


def test_no_chip_of_the_filter_row_says_what_is_behind_it() -> None:
    """The prohibition of the counting oracle, over the region of the row itself.

    A number beside a chip, a dot, a greyed out chip and a plural sentence are
    the same piece of information: how many files of that kind this user would
    see. It would be worked out before the permission recheck, which is the one
    place that knows what the user may open, so it would be an answer about
    other people's files (T-02-93, and T-13-47 of this phase). All ten chips
    therefore look alike, including the ones behind which there is nothing, and
    a chip over an empty group leads to the empty state.

    The comments of the region are stripped before the scan, and that is why the
    region is cut on a comment opener rather than on a class name: the block
    comment of the row explains why there is no count and no greyed out chip, so
    a scan over the raw text would go red on the sentence that promises exactly
    what this gate holds.

    **What this gate does not prove.** It reads the template and not the
    controller. A count worked out in PHP and handed over under a harmless name
    would pass here and would have to be caught where the chips are built, in
    ``PageControllerTest``. What this gate holds is the rendering: no word of
    counting reaches the row.
    """
    findings = scan_filter_row_for_a_counting_oracle(PAGE_TEMPLATE.name, PAGE_TEMPLATE.read_text(encoding="utf-8"))

    assert findings == []
    # The anti vacuity clause: the region was found and it really is the row.
    region = filter_row_of(PAGE_TEMPLATE.read_text(encoding="utf-8"))
    assert region.count("findling-chip-link") >= 4
    # And it can go red, in three of the shapes the contract names at once, and
    # on the fourth failure this scan has: a region it can no longer find.
    dirty = (
        f"{FILTER_ROW_START} the filter row */ ?>\n"
        '<a class="findling-chip-link findling-chip-link--disabled">PDF'
        '<span class="findling-chip__count">$l->n(</span><span>$totalHits</span></a>\n'
        f"{FILTER_ROW_END}"
    )
    assert len(scan_filter_row_for_a_counting_oracle("sample.php", dirty)) == 4
    assert len(scan_filter_row_for_a_counting_oracle("sample.php", "<?php // no row here")) == 1


def test_every_control_of_the_filter_row_can_be_reached() -> None:
    """The last [G] prohibition, and the responsive promise behind it.

    Two halves of one sentence. Every chip, every sort link and the reset link
    is at least as tall as a clickable area of the theme and grows to 44px under
    a coarse pointer, because thirty four pixels is enough for a cursor and not
    for a thumb. And the three containers of the row wrap rather than scroll: a
    row out of which part of the choice has been pushed hides controls behind a
    gesture, and on a keyboard it cannot be found at all, so ten short words
    wrap instead (13-UI-SPEC, Responsive).

    **What this gate does not prove.** It reads declarations and cannot lay a
    page out. A rule that is present and overridden further down, or a container
    that wraps while its parent clips it, would pass here; the sight check on a
    narrow screen is acceptance probe 16 and stays a human one.
    """
    findings = scan_page_stylesheet_for_a_reachable_row(
        PAGE_STYLESHEET.name, PAGE_STYLESHEET.read_text(encoding="utf-8")
    )

    assert findings == []
    # The anti vacuity clause: the reader really found the blocks it judges, so
    # a clean answer is not an answer about two empty strings.
    stylesheet = PAGE_STYLESHEET.read_text(encoding="utf-8")
    assert block_body_of(stylesheet, ".findling-chip-link") != ""
    assert block_body_of(stylesheet, COARSE_QUERY) != ""
    # And it can go red on every half: a chip at the height of a label, a coarse
    # query that forgot it, and a row that scrolls instead of wrapping.
    dirty = (
        ".findling-chip-link {\n\tfont-size: 13px;\n}\n"
        ".findling-sort__link {\n\tmin-height: var(--default-clickable-area);\n}\n"
        ".findling-filters__reset {\n\tmin-height: var(--default-clickable-area);\n}\n"
        ".findling-filters__row {\n\toverflow-x: auto;\n}\n"
        ".findling-filters__group {\n\tflex-wrap: wrap;\n}\n"
        ".findling-sort {\n\tflex-wrap: wrap;\n}\n"
        "@media (pointer: coarse) {\n\t.findling-sort__link,\n\t.findling-filters__reset {\n"
        "\t\tmin-height: 44px;\n\t}\n}\n"
    )
    assert len(scan_page_stylesheet_for_a_reachable_row("sample.css", dirty)) == 4


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


def test_a_style_attribute_in_the_template_is_reported() -> None:
    """The fourth [G] prohibition, held by the scanner the inline script already uses.

    A style attribute is the CSS counterpart of an inline script: a declaration
    no stylesheet of this app can be read out of, that no theme variable reaches
    and that the next dark mode forgets. It was added to ``scan_template`` in
    plan 13-10 rather than written as a gate of its own for the result page,
    because the rule is the same one for both templates and a second gate would
    be a second place to keep right.

    **What this gate does not prove.** It reads the attribute and nothing about
    a stylesheet. The literal colours and the removed focus ring are the
    business of ``scan_stylesheet``, which runs over both stylesheets.
    """
    styled = scan_template("sample.php", _CLEAN_TEMPLATE + '<span style="color: #1a1a1a"></span>\n')

    assert len(styled) == 1
    assert "style attribute" in styled[0]
    # And the near miss stays clean: an attribute whose name merely ends in the
    # word is not a style attribute.
    assert scan_template("sample.php", _CLEAN_TEMPLATE + '<span data-style="x"></span>\n') == []


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


def test_the_seven_sentences_of_the_engine_line_are_in_the_german_catalogue() -> None:
    """IN-02 for the new line: a sentence in one catalogue only is half German.

    The seventh is the one for a container that reports no state at all. It is
    reached through the default of both halves, so no mapping carries it and
    nothing but this line would notice its absence.

    Seven since 19.09.2026, and the one that came is the sentence for
    ``unloaded``: the container gave the weights back in an idle span, the next
    search answers with full text hits and pays the load again in the
    background. The number word is in the name of this test on purpose, so that
    a raised figure and a name still saying six cannot stand side by side.

    The self check of plan 20-03 read this name and left it standing, with the
    reason here rather than in a commit message. Neither the seven nor the word
    German counts catalogues: the seven counts the states of the engine, and the
    German catalogue is the reference every other one is held against by
    ``test_every_catalogue_carries_the_same_keys``. A sentence that reached
    ``de.json`` reaches every other catalogue through that gate, and a tenth
    language changes nothing in this name.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    catalogue = json.loads(L10N_JSON.read_text(encoding="utf-8"))["translations"]
    sentences = set(engine_sentences_of_the_template(template).values()) | {ENGINE_UNKNOWN_SENTENCE}

    assert len(sentences) == 7

    missing = [f"de.json: {sentence}" for sentence in sorted(sentences) if sentence not in catalogue]
    if ENGINE_UNKNOWN_SENTENCE not in template:
        missing.append(f"admin.php: {ENGINE_UNKNOWN_SENTENCE}")
    if ENGINE_UNKNOWN_SENTENCE not in script:
        missing.append(f"admin.js: {ENGINE_UNKNOWN_SENTENCE}")

    assert missing == []


# The two banners of plan 18-10 and the one line of the language diagnosis, by
# the ids the template gives them and the script flips. Held as a table so that
# a third element of this kind is added in one place and every gate below sees
# it.
REBUILD_BANNERS = ("findling-banner-rebuild", "findling-banner-rebuild-space")

# The advice that must not travel into the new banner, spelled once. It is the
# right advice under the banner it already stands in and the wrong one under a
# rebuild: that run carries the text the index already holds from one directory
# into another, and a reader who follows this command instead pays nineteen
# hours on the hardware this app is built for, for nothing.
RESTART_ADVICE = "occ findling:index --restart"


def scan_rebuild_banners(template: str, script: str) -> list[str]:
    """Findings of the two rebuild banners: an id one half knows and the other does not.

    The same failure mode the two gates above are written for, one element
    further on. A banner the template renders and the script never flips stands
    still for the whole life of the page; a banner the script flips and the
    template never rendered is a write into nothing. Neither produces an error
    anywhere.
    """
    findings: list[str] = []
    for banner in REBUILD_BANNERS:
        if f"'id' => '{banner}'" not in template:
            findings.append(f"admin.php does not render the banner {banner}")
        if f"shown('{banner}'" not in script:
            findings.append(f"admin.js never flips the banner {banner}")
    # The progress banner carries a figure in its sentence, so it needs the
    # second half of the pattern as well: the text is written into the span of
    # the banner and never into the paragraph, which holds the icon.
    if "text('findling-banner-rebuild-text'," not in script:
        findings.append("admin.js does not write the sentence of findling-banner-rebuild")
    return findings


def test_both_halves_of_the_page_carry_the_two_rebuild_banners() -> None:
    """Criterion 2 of phase 18 as a gate over the template and the script."""
    findings = scan_rebuild_banners(
        TEMPLATE.read_text(encoding="utf-8"),
        SCRIPT.read_text(encoding="utf-8"),
    )

    assert findings == []


def test_a_rebuild_banner_only_one_half_knows_about_is_reported() -> None:
    # The gate has to be able to go red, in both of its directions.
    assert len(scan_rebuild_banners("", "")) == 5
    assert len(scan_rebuild_banners("'id' => 'findling-banner-rebuild',", "")) == 4


def test_the_new_banner_does_not_advise_the_full_reindex() -> None:
    """The one sentence of this plan that is about what is NOT written.

    The rebuild banner and the reindex banner look alike from a distance and
    they are opposite advice. The count is asserted rather than the absence of
    the string, because the reindex banner is supposed to keep naming the
    command: a gate that forbade it outright would delete the one place where it
    is right.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    assert template.count(RESTART_ADVICE) == 1
    assert "older text analysis" in template
    # And the sentence that does carry it is the reindex one and not a new one.
    line = next(line for line in template.splitlines() if RESTART_ADVICE in line)
    assert "older text analysis" in line
    assert "rebuilding its index" not in line
    # The script writes the sentence of the new banner and never this command.
    assert RESTART_ADVICE not in script


def test_both_halves_of_the_page_carry_the_language_diagnosis() -> None:
    """Criterion 4 of phase 18: active against filled, and both names visible.

    The names and not the counts, and that is the difference to the startup
    warning of plan 18-09, which deliberately reports a number: a log line names
    the variable and never the value, while a page whose reader has to decide
    whether a search can work at all needs to see which chain is empty.
    """
    template = TEMPLATE.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")
    view = ADMIN_VIEW.read_text(encoding="utf-8")

    assert 'id="findling-languages"' in template
    assert "text('findling-languages'," in script
    for key in ("languagesActive", "languagesFilled"):
        assert f"'{key}' => $this->text($answer, '{key}')," in view, key
        assert f"${key}" in template, key
        assert f"backend.{key}" in script, key


def test_every_new_status_key_has_exactly_one_line_in_the_service() -> None:
    """One key, one line, and the line is the whole translation of that key.

    backend() is the only place where a name from the container becomes a name
    of this page. A key read in two places would be judged twice and the two
    judgements would part company on the day one of them is corrected.
    """
    view = ADMIN_VIEW.read_text(encoding="utf-8")

    for key in (
        "languagesActive",
        "languagesFilled",
        "rebuildRunning",
        "rebuildDone",
        "rebuildTotal",
        "rebuildBlockedBytes",
    ):
        assert view.count(f"'{key}' => ") == 1, key
    assert "'rebuildRunning' => ($answer['rebuildRunning'] ?? false) === true," in view
    for key in ("rebuildDone", "rebuildTotal", "rebuildBlockedBytes"):
        assert f"'{key}' => $this->counter($answer, '{key}')," in view, key


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

    The hard number below stood at 173 until 10.09.2026 and then at 174. It
    rose by exactly one key, and the key is the sentence the result page says
    for a run that was handed candidates and kept none of them: finding
    DI-07-03 of phase 7, decided by the owner as V-1a on 10.09.2026 in
    .planning/phases/11-haertung-und-store-einreichung-v1-1/11-VORENTSCHEIDE.md.
    Without this paragraph the next reader takes a raised number for sloppiness
    and lowers it again. It is raised here rather than in plan 11-08 because
    the tree between the two plans would otherwise be red; 11-08 only reads it
    afterwards, and so does the French table of docs/l10n-french.md, which
    counts its coverage against exactly this key set.

    It stands at 197 since 17.09.2026, and the rise of 23 is the copywriting
    contract of phase 13, section "Copywriting Contract" of
    .planning/phases/13-filter-und-sortierung-auf-der-ergebnisseite/13-UI-SPEC.md.
    The 23 break down as ten chips (six file types and four time ranges), three
    row labels (File type, Time range, Sort by), three sort links, two ways of
    undoing a filter (the accessible name of one active chip and the link that
    drops all of them), two shapes of a date (the line in a hit and the dated
    accessible name of the same hit), and three sentences of the empty state
    under an active filter. That is the visible surface of FILT-01 to FILT-04,
    and every one of the 23 runs through the translation call of
    php/templates/search.php.

    This paragraph carries the same duty as the one above it: without it the
    next reader takes the raised number for sloppiness and lowers it again.
    Whoever raises it next writes the next paragraph.

    It stands at 198 since 19.09.2026, and the rise of one is "File contents",
    the group name Findling reports to the Unified Search
    (php/lib/Search/Provider.php, getName). The key predates phase 13 and was
    the single t() call of the PHP side without a catalogue entry, found by
    sight check 17 of the phase 13 acceptance (13-13-SUMMARY.md): every
    non-English user read that one group name in English. The French wording
    falls under the acceptance point that no French wording of this app has
    been checked by a native speaker yet.

    It stands at 199 since 19.09.2026 as well, later the same day, and the rise
    of one is the sentence of the sixth engine state: the model was released to
    save memory, and the next search answers with full text hits while it is
    read again in the background. The word ``unloaded`` is the owner decision of
    19.09.2026 for branch B of plan 14-09
    (.planning/phases/14-modell-entladung-im-leerlauf/14-CONTEXT.md), taken with
    this very cost written out: two spellings of the closed set, two sentence
    tables, six catalogue files and this figure. The French wording of that
    sentence was read and accepted unchanged by the owner at the phase
    checkpoint on 19.09.2026, and docs/l10n-french.md carries the dated note
    that says so.

    It stands at 202 since 24.09.2026, and the rise of three is plan 18-10 of
    phase 18: the two sentences of the rebuild banners and the one line of the
    language diagnosis. The first names the progress of a run that carries the
    documents of the index from one directory into another and deliberately
    names no command, because the command of the reindex banner next to it
    would cost the reader nineteen hours for nothing; the second names the
    bytes that were missing when that run refused itself, together with
    FINDLING_REBUILD_FALLBACK as the way out that needs no space; the third puts
    the switched on languages next to the ones whose chain really carries text,
    which is criterion 4 of the phase. The French wording of all three is cast
    from the table in docs/l10n-french.md and carries the dated reservation of
    24.09.2026 there: it is machine checked and the owner has not read it yet.

    It still stands at 202 on 25.09.2026, and what moved that day was not the
    figure but five of the names it counts: plan 20-01 of phase 20 put the five
    plural keys into the shape Nextcloud looks them up under,
    ``_<singular>_::_<plural>_``. Findling had carried them as the bare singular
    since the first catalogue, and the price of that was measured against the
    running instance rather than reasoned about: ``de`` and ``fr`` answered
    ``n('%n day', '%n days', 2)`` with ``2 days``, and so did every number above
    one. ``L10N::n`` builds the composite identifier, looks it up, and falls back
    to the English plural when it is not there; the bundled ``@nextcloud/l10n``
    does the same in the browser. Over every app that instance ships, 120 of 120
    plural entries carry the composite form and none carries the bare one. The
    figure is untouched by all of it: five keys renamed in place, in all six
    catalogues in one commit, because half a rename is a red G1.

    This paragraph carries the same duty as the four above it, and it carries it
    for a renamed key as much as for a raised figure. Whoever moves the number,
    or one of the names it counts, writes the next paragraph.
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
    assert len(keys_of["de.json"]) == 202


def test_every_catalogue_carries_the_same_keys() -> None:
    """G1 of plan 11-08: which sentences does every language of this app answer?

    Six files since the French catalogue arrived, three language codes, one key
    set. A key written into one language and forgotten in the others is half a
    surface: the page speaks French in one line and English in the next, and a
    user cannot tell which of the two is the complete one.

    The name carried the number six until plan 20-03, and the number was right
    for as long as it was right. A test name that has to be dragged along at
    every new catalogue is a name that will one day not be dragged along, and
    then it says six over sixteen files. ``L10N_CATALOGUES`` stays the one place
    that grows; the name no longer counts along with it.

    This gate stands next to
    ``test_the_german_catalogue_covers_both_german_language_codes`` and does not
    replace it. The text equality asserted there holds for the two German twins
    and expressly not for French: ``fr`` against ``de`` would be a sameness
    nobody wants, and docs/l10n-french.md says so in point 3 of "Bedingung,
    unter der der franzoesische Katalog kommt". What takes its place for French
    is the placeholder parity of G3.

    It will expressly not hold for the two Portuguese files either, and that is
    worth writing down before they arrive. ``pt_PT`` and ``pt_BR`` are two
    varieties with different everyday words, not one language under two codes the
    way ``de`` and ``de_DE`` are; a text equality check over them would look like
    the German one and would in fact nail one of the two to wordings that are
    wrong on its side of the Atlantic.

    A missing file is a failure that names it. Without that line the gate would
    compare five files, or one, and report a clean tree over a catalogue that is
    not shipped at all.
    """
    missing = [path.name for path in L10N_CATALOGUES if not path.is_file()]
    assert missing == [], f"catalogues are missing: {missing}"

    findings = scan_key_sets({path.name: frozenset(catalogue_of(path)) for path in L10N_CATALOGUES})

    assert findings == []
    # And the comparison can go red. A gate whose body was deleted would report
    # six agreeing catalogues over a tree in which one of them lost a sentence.
    drifted = {"a.json": frozenset({"one", "two"}), "b.js": frozenset({"one"})}
    assert len(scan_key_sets(drifted)) == 1


def test_every_catalogue_value_carries_a_wording_of_its_language() -> None:
    """G2 of plan 11-08, over every catalogue since plan 20-03.

    Empty or identical to the English source string are the two shapes an
    untranslated entry takes, and both of them ship a catalogue that claims a
    completeness it does not have. That is the outcome docs/l10n-french.md was
    written to prevent: 24 of 174 strings produce a half French surface.

    The exceptions are named in ``VALUES_THAT_MAY_EQUAL_THEIR_KEY`` per language
    code, with their reason, and they are a list rather than a count on purpose:
    two since plan 11-08, three more with the file type chips of phase 13, and
    four of their own for German since this plan read the tree instead of
    assuming it.

    A language code without an entry in that table is a failure that names the
    code. It would be cheaper to hand an empty mapping to an unknown language and
    let the scan run, and it would be wrong: an empty mapping is a claim that
    this language has no intended sameness with English, and nobody made that
    claim. The gate asks for the claim before it judges the catalogue.
    """
    missing = [path.name for path in L10N_CATALOGUES if not path.is_file()]
    assert missing == [], f"catalogues are missing: {missing}"

    unargued = sorted(
        {language_code_of(path) for path in L10N_CATALOGUES} - set(VALUES_THAT_MAY_EQUAL_THEIR_KEY),
    )
    assert unargued == [], f"languages without a list of exceptions: {unargued}"

    findings = [
        message
        for path in L10N_CATALOGUES
        for message in scan_completeness(
            path.name,
            catalogue_of(path),
            VALUES_THAT_MAY_EQUAL_THEIR_KEY[language_code_of(path)],
        )
    ]

    assert findings == []
    # The exceptions are exceptions of this tree and not of a former one: every
    # key of every list still exists, so no line of any list covers nothing.
    stale = sorted(
        f"{code}: {key}"
        for code, exceptions in VALUES_THAT_MAY_EQUAL_THEIR_KEY.items()
        for key in exceptions
        if key not in catalogue_of(REPO_ROOT / "php" / "l10n" / f"{code}.json")
    )
    assert stale == [], f"exceptions for keys that no longer exist: {stale}"
    # And the scan can go red, in both of its shapes.
    dirty: dict[str, str | list[str]] = {
        "Reason": "Reason",
        "Files": "",
        "_and %n more_::_and %n more_": ["et %n autre", ""],
    }
    assert len(scan_completeness("sample.json", dirty, {})) == 3
    # And the exceptions are read rather than carried along: the same catalogue
    # with "Reason" argued is one finding fewer. Without this line a scanner that
    # ignored its third argument would look exactly as green as this one.
    assert len(scan_completeness("sample.json", dirty, {"Reason": "argued for this sample"})) == 2


def test_no_catalogue_value_loses_or_invents_a_placeholder() -> None:
    """G3 of plan 11-08, over every catalogue since plan 20-03.

    The replacement for the text equality of the German twins, and the one
    invariant a translation can keep word for word. Nextcloud fills these values
    with ``vsprintf``: a value that lost its ``%2$s`` renders a sentence with the
    file name missing, and a value that invented one renders an argument that
    does not exist. Neither produces an error anybody sees.

    The walk over every catalogue is not extra work this gate does on the side,
    it is what the gate is for. A lost ``%2$s`` takes from the sentence the file
    it is talking about, and that is the same damage in every language; running
    the check over French alone was the shape of the plan that introduced it and
    never a statement that the other catalogues cannot lose a placeholder. The
    scanner itself is unchanged since plan 20-01, where it learnt to split a
    composite plural key at its mark, and it was language blind before that.

    Multisets and not sets, so two identical directives are two and not one, and
    over every form of a plural value, because the second form is where a
    dropped ``%n`` hides.
    """
    missing = [path.name for path in L10N_CATALOGUES if not path.is_file()]
    assert missing == [], f"catalogues are missing: {missing}"

    findings = [
        message for path in L10N_CATALOGUES for message in scan_placeholder_parity(path.name, catalogue_of(path))
    ]

    assert findings == []
    # The anti vacuity clause: a catalogue without directives would be judged
    # perfect by a scan that has nothing to compare, and it is asked of every
    # file now that every file is scanned.
    without = [
        path.name for path in L10N_CATALOGUES if not any(PRINTF_DIRECTIVE.search(key) for key in catalogue_of(path))
    ]
    assert without == [], f"catalogues without a single directive to compare: {without}"
    # The split of plan 20-01 reads both ways, and these two lines are what say
    # so. A composite key whose two forms are both right is silent; without the
    # split it would report both of them, because the key carries two %n and
    # each form carries one.
    composite: dict[str, str | list[str]] = {"_%n day_::_%n days_": ["%n jour", "%n jours"]}
    assert scan_placeholder_parity("sample.json", composite) == []
    # And the split swallows nothing: the plural half still demands its %n, so a
    # second form without one is exactly one finding.
    lost: dict[str, str | list[str]] = {"_%n day_::_%n days_": ["%n jour", "jours"]}
    assert len(scan_placeholder_parity("sample.json", lost)) == 1
    # And it can go red in the other half too: a lost numbered placeholder, and a
    # plural whose first form dropped its %n while the second one kept it.
    dirty: dict[str, str | list[str]] = {"%1$s in %2$s": "%1$s dans", "_%n day_::_%n days_": ["jour", "%n jours"]}
    assert len(scan_placeholder_parity("sample.json", dirty)) == 2


def test_no_catalogue_value_can_break_the_page() -> None:
    """The two wordings that take the page down rather than get it wrong.

    Every gate above this one judges whether a sentence says the right thing.
    These two judge whether the page survives it at all, and both findings come
    out of the same PHP method: ``L10NString::__toString`` fills a sentence with
    ``vsprintf`` and joins plural forms with ``|``. A bare percent sign makes the
    first throw a ``ValueError`` and leaves a white page, a pipe character makes
    the second give up and replaces the sentence with an English error message.
    The reasons in full stand in the two scanner docstrings.

    One gate for two scanners because they answer one question, "can a wording
    break this page", and because both run over ``L10N_CATALOGUES`` and take
    every later language along by themselves.

    Four staged lines and not one. The tree is clean for both scanners today, and
    a scan that reports nothing over a clean tree looks exactly like a scan whose
    body was deleted; the percent scanner therefore has to report the Spanish
    wording, stay silent on its doubled form, and name the form number when the
    finding is in a plural form, and the pipe scanner has to report a pipe.
    """
    missing = [path.name for path in L10N_CATALOGUES if not path.is_file()]
    assert missing == [], f"catalogues are missing: {missing}"

    findings = [
        message
        for path in L10N_CATALOGUES
        for scan in (scan_percent_discipline, scan_pipe_character)
        for message in scan(path.name, catalogue_of(path))
    ]

    assert findings == []
    # The wording of pitfall 3, word for word: Spanish and Portuguese put a space
    # between the number and the percent sign, and this is the value that would
    # throw in vsprintf.
    bare: dict[str, str | list[str]] = {"Half of the files": "50 % de los archivos"}
    assert len(scan_percent_discipline("sample.json", bare)) == 1
    # And the doubled form is the fix and not a second finding. Without this line
    # a scanner that simply forbade the percent sign would pass, and it would
    # forbid the one spelling that works.
    doubled: dict[str, str | list[str]] = {"Half of the files": "50 %% de los archivos"}
    assert scan_percent_discipline("sample.json", doubled) == []
    # A pipe in a value, reported once.
    piped: dict[str, str | list[str]] = {"Two things": "a | b"}
    assert len(scan_pipe_character("sample.json", piped)) == 1
    # And a plural whose second form carries the bare percent sign: one finding,
    # and it names the form, because "somewhere in this value" is not something
    # anybody can fix without reading the whole catalogue.
    plural: dict[str, str | list[str]] = {"_%n percent_::_%n percent_": ["%n %%", "%n %"]}
    assert scan_percent_discipline("sample.json", plural) == [
        f"sample.json: '_%n percent_::_%n percent_' form 1 carries a bare percent sign; {PERCENT_HINT}"
    ]


def test_every_catalogue_carries_the_plural_rule_of_its_language() -> None:
    """G4 of plan 11-08, judged per language code since plan 20-02.

    The rule stands twice per language, as ``pluralForm`` in the ``.json`` and as
    the fourth argument of ``OC.L10N.register`` in the ``.js``, and the two have
    to be the same string. Until this plan the gate asked one question for
    French and one for German, with the number of forms nailed into the body as
    a literal 2. Spanish, Italian and both Portuguese carry three forms, so the
    literal had to go, and the two constants had to become a table.

    The loop walks the codes of ``PLURAL_FORM_OF`` that have a file today and
    takes the rest along by itself on the day their files arrive. A code of
    ``PLURAL_FORM_OF`` without a file is deliberately not a finding here: a
    missing catalogue is the business of the key set gate over
    ``L10N_CATALOGUES``, and two gates for one question are one question too
    many.
    """
    german = catalogue_of(L10N_JSON)
    german_plural_keys = sorted(key for key, value in german.items() if isinstance(value, list))
    assert len(german_plural_keys) == 5

    present = [code for code in PLURAL_FORM_OF if (REPO_ROOT / "php" / "l10n" / f"{code}.json").is_file()]
    # The anti vacuity clause of the loop: a rename that took the files away
    # would leave the walk with nothing to do and the gate green over a tree
    # without a single catalogue.
    assert {"de", "de_DE", "fr"} <= set(present), f"a shipped catalogue lost its file: {sorted(present)}"

    findings: list[str] = []
    for code in present:
        path_json = REPO_ROOT / "php" / "l10n" / f"{code}.json"
        path_js = REPO_ROOT / "php" / "l10n" / f"{code}.js"
        script = path_js.read_text(encoding="utf-8")
        declared = JS_PLURAL_FORM.search(script)

        findings.extend(
            scan_plural_rule(path_json.name, code, json.loads(path_json.read_text(encoding="utf-8"))["pluralForm"])
        )
        if declared is None:
            findings.append(f"{path_js.name}: declares no rule as the fourth argument of OC.L10N.register")
        else:
            findings.extend(scan_plural_rule(path_js.name, code, declared.group(1)))

        catalogue = catalogue_of(path_json)
        plural_keys = sorted(key for key, value in catalogue.items() if isinstance(value, list))
        if plural_keys != german_plural_keys:
            drift = sorted(set(plural_keys) ^ set(german_plural_keys))
            findings.append(f"{path_json.name}: its plural keys differ from the German ones in {drift}")
        findings.extend(
            f"{path_json.name}: {key!r} carries {len(catalogue[key])} forms where {code} wants {FORM_COUNT_OF[code]}"
            for key in plural_keys
            if len(catalogue[key]) != FORM_COUNT_OF[code]
        )

    assert findings == []
    # And the scan can go red, in both of its shapes. Spanish handed the German
    # rule is reported twice, once as the copied German rule and once as the rule
    # that is not the Spanish one.
    assert len(scan_plural_rule("sample.json", "es", GERMAN_PLURAL_FORM)) == 2
    # Dutch handed the same string is reported not at all, because for Dutch it
    # is the right rule. This line is the one that keeps the gate usable once
    # nl.json exists; without it the language aware check reads like an oversight
    # and the next reader takes it back out.
    assert scan_plural_rule("sample.json", "nl", GERMAN_PLURAL_FORM) == []


def test_the_rule_table_of_the_documentation_and_the_constant_are_one_string() -> None:
    """The proof and the gate it is checked against have to say the same thing.

    ``docs/l10n-catalogues.md`` carries the rules Findling ships, read out of
    ``core/l10n/`` of both Nextclouds of the version window on 25.09.2026, and
    ``PLURAL_FORM_OF`` carries the same eight strings. Plan 20-02 compared them
    once by hand, eight out of eight, and left the comparison as a number in a
    summary; this gate is what keeps it true.

    The drift this prevents is not cosmetic. Plans 20-04 to 20-08 cast ten
    catalogue files from the table in that document, and the gate above judges
    those files against the constant. A document that drifted from the constant
    would put a wrong ``pluralForm`` into ten files and the gate would report it
    as ten broken catalogues, in a phase in which the document is the thing
    everybody trusts. One of the two has to be able to call the other wrong.
    """
    parsed = rules_declared_in(L10N_DOCUMENTATION.read_text(encoding="utf-8"))

    differing = sorted(parsed.items() ^ PLURAL_FORM_OF.items())
    assert differing == [], f"the document and the constant differ: {differing}"
    # The anti vacuity clause: a document whose block was reformatted would parse
    # to nothing, and nothing equals nothing only if the constant is empty too.
    assert len(parsed) == len(PLURAL_FORM_OF)
    # And the reading can go red: the same block with one character changed in
    # the French line is a different mapping.
    assert rules_declared_in("fr     nplurals=2; plural=(n >= 1);\n") == {"fr": "nplurals=2; plural=(n >= 1);"}


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

    The three in the name counts those three places and not the catalogues of
    this app, which is why the self check of plan 20-03 left it standing: a new
    language adds a file to ``L10N_CATALOGUES`` and nothing here, because the
    key set gate over that tuple is what carries the sentence into it.
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
