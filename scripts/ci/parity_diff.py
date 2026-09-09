#!/usr/bin/env python3
"""Compare two search answers as sets of fileids, in both directions (SRCH-04).

The parity job asks the native provider ``files`` and the provider ``findling``
the same question as the same user, and this tool decides whether the two
answers describe the same set of files. D-21 calls that visibility parity: per
scenario and marker findling produces a hit exactly when the native search shows
the file to the same user.

Both directions are reported, and they are reported separately, because they are
not the same finding:

* ``missing`` is a fileid the native search shows and findling does not. The user
  does not find a document he is allowed to see. That is a functional defect.
* ``extra`` is a fileid findling shows and the native search does not show the
  same user. That is the case that touches the permission boundary, and it is the
  reason this comparison exists at all.

A tool that printed "parity failed" for both would throw away exactly the part of
the answer somebody has to act on, so the two are never merged into one message.

Since phase 9 there is a third answer to the same question, and a third input
mode for it. The result page of findling is a second way into the same search,
and success criterion 4 of that phase asks the existing parity job to cover it:
same user, same question, same set of files over the dialog and over the page.
The page answers HTML rather than JSON, so its fileids are read out of the row
id ``findling-hit-<n>`` that ``php/templates/search.php`` writes on every hit.
That id is not a test artefact, it is the anchor of the return marker and
therefore already a contract of the page.

The HTML reader fails as hard as the JSON reader, and the two sentences that
draw the line are these. An empty hit list next to the empty state of the page is
a valid empty set, because the page answered and its answer is "nothing". An
answer without either of them is unreadable, because a page that shows neither a
list nor an empty state is not the result page at all, and so is an answer that
carries the error block: "the user sees nothing" and "the page could not ask" are
different statements, and a silent backend that passed as an empty set would make
a parity job green over two empty sets.

Two ways of being green without having proven anything are refused as well, and
both were real risks rather than hypotheticals:

* Two empty sets agree. A backend that answers nothing at all would make every
  scenario of the job agree with every other one. ``--expect-min`` is therefore
  mandatory and names how many fileids the scenario was built to compare; falling
  below it is a failure of its own kind, and the message says the comparison was
  inconclusive rather than parity broken. It holds for all three sets.
* An unreadable answer would collapse into an empty set. An OCS error body, a 502
  page from a proxy, a truncated file: each of them is valid input to a naive
  reader and each of them would silently turn into "no hits". They end as their
  own exit code, and the message names the side the bad answer came from.

The output carries fileids, counts and the scenario name, and never a path or a
title. The answers do carry both, and a workflow log of a public repository is
the cheapest place to leak the file names of a private instance.

Standard library only, and no third party import. It runs with the system python
of the runner, next to curl and occ, and never inside the locked environment of
the backend package. That is also why the HTML is read with a pattern over one
contract string and not with a parser.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

# Zero is parity. The three failure codes are kept apart on purpose: the job
# stops at the first one either way, but a red run should say whether the app
# broke a promise or the test setup fell apart before it could ask.
EXIT_OK = 0
EXIT_PARITY = 1
EXIT_VACUOUS = 2
EXIT_MALFORMED = 3

# The row id of the result page, and the whole of what the HTML reader is made
# of. php/templates/search.php writes it once per hit, as the anchor the return
# marker of php/js/search.js scrolls to.
HIT_ROW_ID = re.compile(r'id="findling-hit-(\d+)"')

# The three class names of php/templates/search.php the reader needs to tell an
# answer from a non answer. They are read out of that file and not invented: the
# hit list and the empty state are the two halves of block 3 and 4, exactly one
# of which is always rendered, and the error banner is block 2 in its error kind.
HIT_LIST_MARKER = "findling-hits"
EMPTY_STATE_MARKER = "findling-empty"
ERROR_BLOCK_MARKER = "findling-banner--error"

# The app path of the result page. The last entry of the findling group in the
# search dialog is a door into that page and not a hit, so it carries no fileId
# attribute, and it is recognised here by this address. Never by the missing
# attribute: "no attribute means skip" would switch off the very guard the
# reader below exists for, and Provider::entryPoint() carries the same sentence
# at the other end.
PAGE_APP_PATH = "/apps/findling"


class MalformedAnswer(Exception):
    """An answer that cannot be read as a search result, with the reason why.

    Its own type, so that the caller can give it its own exit code. The one
    thing this must never become is an empty set: see the module docstring.
    """


def _is_entry_point(entry: dict[str, object]) -> bool:
    """Whether this entry is the door into the result page rather than a hit.

    Decided on the address alone. Everything else about the entry, and in
    particular the attribute it does not carry, is deliberately not consulted.
    The rule is written over the address and not over the side it came from,
    because the native provider never produces this address anyway, so a rule
    that also looked at the side would say the same thing twice.
    """
    url = entry.get("resourceUrl")
    if not isinstance(url, str):
        return False

    return urlsplit(url).path.rstrip("/").endswith(PAGE_APP_PATH)


def _file_ids(path: Path, side: str) -> set[str]:
    """The fileid attribute of every entry of one OCS search answer.

    ``ocs.data.entries[].attributes.fileId`` is the one field the comparison is
    made of. Every hit of the native provider carries it (FilesSearchProvider
    adds it for every result), and so does every hit of findling, which is why
    neither titles nor paths are read here.

    Every deviation from that shape raises instead of shrinking the set. An entry
    without the attribute would otherwise remove one element from one side and be
    read as a parity violation of the other side, which is a wrong answer to a
    question about permissions. The one entry that is skipped is the door into
    the result page, and it is skipped by its address.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise MalformedAnswer(f"the {side} answer could not be read ({type(error).__name__})") from error

    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        # Deliberately without the offending text: a 502 page is harmless, but an
        # OCS body that failed halfway through carries file names.
        raise MalformedAnswer(f"the {side} answer is not valid JSON (line {error.lineno})") from error

    if not isinstance(document, dict):
        raise MalformedAnswer(f"the {side} answer is not a JSON object")

    node = document.get("ocs")
    if not isinstance(node, dict):
        raise MalformedAnswer(f"the {side} answer has no ocs object")

    data = node.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise MalformedAnswer(f"the {side} answer has no ocs.data.entries list")

    entries: list[object] = data["entries"]
    file_ids: set[str] = set()
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise MalformedAnswer(f"entry {position} of the {side} answer is not an object")
        if _is_entry_point(entry):
            continue
        attributes = entry.get("attributes")
        if not isinstance(attributes, dict) or "fileId" not in attributes:
            raise MalformedAnswer(f"entry {position} of the {side} answer has no attributes.fileId")
        file_ids.add(str(attributes["fileId"]))

    return file_ids


def _page_file_ids(path: Path) -> set[str]:
    """The fileids of the result page, read out of its hit row ids.

    Three answers are not a set of fileids and end as an unreadable answer rather
    than as an empty one, for the reason the module docstring gives: a file that
    cannot be read, an answer that carries neither the hit list nor the empty
    state, and an answer that carries the error block of the page.

    An empty hit list beside the empty state is the fourth case and is a legal
    empty set: the page was asked, it answered, and its answer is nothing.
    """
    try:
        markup = path.read_text(encoding="utf-8")
    except OSError as error:
        raise MalformedAnswer(f"the page answer could not be read ({type(error).__name__})") from error

    if ERROR_BLOCK_MARKER in markup:
        raise MalformedAnswer(
            "the page answer carries the error block, so it is a page that could not ask and not an empty result"
        )

    if HIT_LIST_MARKER not in markup and EMPTY_STATE_MARKER not in markup:
        raise MalformedAnswer(
            "the page answer carries neither the hit list nor the empty state, so it is not the result page"
        )

    return set(HIT_ROW_ID.findall(markup))


def _ordered(file_ids: set[str]) -> list[str]:
    """The ids in a readable order, numeric where they are numbers.

    A plain sort would put 100 before 99 and make two lists of ids in a log
    harder to compare by eye than they have to be. Anything that is not a plain
    number sorts after the numbers and among itself as text, because a fileid
    arrives here as whatever the answer carried and not as whatever it should
    have carried.
    """
    numeric = sorted(int(value) for value in file_ids if value.isdigit())
    other = sorted(value for value in file_ids if not value.isdigit())
    return [str(value) for value in numeric] + other


def compare(scenario: str, native: set[str], findling: set[str], expect_min: int) -> int:
    """The whole decision, as an exit code, with every finding on its own line."""
    missing = native - findling
    extra = findling - native

    if missing:
        print(
            f"parity failed: scenario={scenario} missing={_ordered(missing)} "
            "(the native search shows these fileids to this user and findling does not, "
            "which is a functional defect: the search does not find a document the user may see)",
            file=sys.stderr,
        )
    if extra:
        print(
            f"parity failed: scenario={scenario} extra={_ordered(extra)} "
            "(findling shows these fileids and the native search does not show them to the same user, "
            "which is a security defect at the permission boundary)",
            file=sys.stderr,
        )
    if missing or extra:
        return EXIT_PARITY

    compared = len(native)
    if compared < expect_min:
        # The anti vacuity clause. Nought expected is legitimate and is the right
        # expectation for a scenario whose answer is "this user finds nothing",
        # so the comparison is only inconclusive below what was asked for.
        print(
            f"parity inconclusive: scenario={scenario} compared {compared} fileids "
            f"and the scenario expects at least {expect_min}, so it did not compare "
            "the set it was built to compare",
            file=sys.stderr,
        )
        return EXIT_VACUOUS

    print(f"parity ok: scenario={scenario} compared {compared} fileids, identical on both sides")
    return EXIT_OK


def compare_page(scenario: str, findling: set[str], page: set[str], expect_min: int) -> int:
    """The same decision between the search dialog and the result page.

    Symmetric like the comparison above and with the same exit codes, and both
    directions keep their meaning: a fileid only the dialog shows is a functional
    defect of the page, a fileid only the page shows is a defect at the
    permission boundary. The messages name the page as its own side, so that a
    red run says which of the two ways into the same search is the one that
    disagrees.
    """
    missing = findling - page
    extra = page - findling

    if missing:
        print(
            f"parity failed: scenario={scenario} page-missing={_ordered(missing)} "
            "(the search dialog shows these fileids to this user and the result page does not, "
            "which is a functional defect of the page: the same search answers two different sets)",
            file=sys.stderr,
        )
    if extra:
        print(
            f"parity failed: scenario={scenario} page-extra={_ordered(extra)} "
            "(the result page shows these fileids and the search dialog does not show them to the same user, "
            "which is a security defect at the permission boundary of the page)",
            file=sys.stderr,
        )
    if missing or extra:
        return EXIT_PARITY

    compared = len(page)
    if compared < expect_min:
        print(
            f"parity inconclusive: scenario={scenario} the result page compared {compared} fileids "
            f"and the scenario expects at least {expect_min}, so it did not compare "
            "the set it was built to compare",
            file=sys.stderr,
        )
        return EXIT_VACUOUS

    print(f"parity ok: scenario={scenario} the result page compared {compared} fileids, identical to the search dialog")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare the fileids of two OCS search answers symmetrically.",
        # The epilog rather than the description carries the sentence a reader
        # needs at three in the morning: which direction means what.
        epilog=(
            "missing is a functional defect (the user does not find what he may see), "
            "extra is a security defect (the user is shown what the native search does not show him)."
        ),
    )
    parser.add_argument("--scenario", required=True, help="name of the permission scenario, for the message")
    parser.add_argument("--native", required=True, type=Path, help="OCS answer of the provider files")
    parser.add_argument("--findling", required=True, type=Path, help="OCS answer of the provider findling")
    parser.add_argument(
        "--findling-html",
        type=Path,
        help="HTML answer of the result page, optional; adds the comparison of the page against the search dialog",
    )
    parser.add_argument(
        "--expect-min",
        required=True,
        type=int,
        help="how many fileids this scenario expects at least, nought only where finding nothing is the answer",
    )
    arguments = parser.parse_args(argv)

    if arguments.expect_min < 0:
        print(f"parity unusable: scenario={arguments.scenario} was given a negative expectation", file=sys.stderr)
        return EXIT_MALFORMED

    try:
        native = _file_ids(arguments.native, "native")
        findling = _file_ids(arguments.findling, "findling")
        page = None if arguments.findling_html is None else _page_file_ids(arguments.findling_html)
    except MalformedAnswer as error:
        print(f"parity unreadable: scenario={arguments.scenario}, {error}", file=sys.stderr)
        return EXIT_MALFORMED

    verdict = compare(arguments.scenario, native, findling, arguments.expect_min)
    if page is None:
        return verdict

    # Both comparisons are always run and both print, because a run that showed
    # only the first finding would send somebody back for a second run to learn
    # whether the page agrees. The first verdict wins the exit code: it is the
    # statement about the permission chain, the second one about the page.
    page_verdict = compare_page(arguments.scenario, findling, page, arguments.expect_min)
    return verdict if verdict != EXIT_OK else page_verdict


if __name__ == "__main__":
    raise SystemExit(main())
