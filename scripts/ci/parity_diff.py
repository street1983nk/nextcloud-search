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

Two ways of being green without having proven anything are refused as well, and
both were real risks rather than hypotheticals:

* Two empty sets agree. A backend that answers nothing at all would make every
  scenario of the job agree with every other one. ``--expect-min`` is therefore
  mandatory and names how many fileids the scenario was built to compare; falling
  below it is a failure of its own kind, and the message says the comparison was
  inconclusive rather than parity broken.
* An unreadable answer would collapse into an empty set. An OCS error body, a 502
  page from a proxy, a truncated file: each of them is valid input to a naive
  reader and each of them would silently turn into "no hits". They end as their
  own exit code, and the message names the side the bad answer came from.

The output carries fileids, counts and the scenario name, and never a path or a
title. The answers do carry both, and a workflow log of a public repository is
the cheapest place to leak the file names of a private instance.

Standard library only, and no third party import. It runs with the system python
of the runner, next to curl and occ, and never inside the locked environment of
the backend package.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Zero is parity. The three failure codes are kept apart on purpose: the job
# stops at the first one either way, but a red run should say whether the app
# broke a promise or the test setup fell apart before it could ask.
EXIT_OK = 0
EXIT_PARITY = 1
EXIT_VACUOUS = 2
EXIT_MALFORMED = 3


class MalformedAnswer(Exception):
    """An answer that cannot be read as a search result, with the reason why.

    Its own type, so that the caller can give it its own exit code. The one
    thing this must never become is an empty set: see the module docstring.
    """


def _file_ids(path: Path, side: str) -> set[str]:
    """The fileid attribute of every entry of one OCS search answer.

    ``ocs.data.entries[].attributes.fileId`` is the one field the comparison is
    made of. Every hit of the native provider carries it (FilesSearchProvider
    adds it for every result), and so does every hit of findling, which is why
    neither titles nor paths are read here.

    Every deviation from that shape raises instead of shrinking the set. An entry
    without the attribute would otherwise remove one element from one side and be
    read as a parity violation of the other side, which is a wrong answer to a
    question about permissions.
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
        attributes = entry.get("attributes")
        if not isinstance(attributes, dict) or "fileId" not in attributes:
            raise MalformedAnswer(f"entry {position} of the {side} answer has no attributes.fileId")
        file_ids.add(str(attributes["fileId"]))

    return file_ids


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
    except MalformedAnswer as error:
        print(f"parity unreadable: scenario={arguments.scenario}, {error}", file=sys.stderr)
        return EXIT_MALFORMED

    return compare(arguments.scenario, native, findling, arguments.expect_min)


if __name__ == "__main__":
    raise SystemExit(main())
