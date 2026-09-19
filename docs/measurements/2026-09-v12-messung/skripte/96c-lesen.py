#!/usr/bin/env python3
"""Read one recording of the admin page and print three numbers for the watchman.

Three and not one: the watchman decides on the work stock, drives the search load
sample the moment the second track starts, and waits for the end of both. A shell
that has to parse the same JSON three times parses it wrong once. The output is
"vorrat indexed embedded", whitespace separated, and every figure the recording
does not carry is the word "unklar", because "not known" and "zero" are two
different answers and the watchman acts on both.

Pitfall 8 of the research, in two sentences, because it is the whole reason this
file exists a second time. 42c-lesen.py of the semantic run looked for indexed
and embedded on the TOP LEVEL of the recording, where the indexed of the PHP half
stands and stays 0 by design and where embedded does not stand at all, so the
watchman logged indexed=0 embedded=0 for a whole night while the container held
47.000 vectors. The two consequences: the search load sample of the trailing run
never ran, because its condition is embedded > 200, and the end of both tracks
would have been noticed at the round cap, some nine hours after it happened.

Both counters therefore live under "backend" and are read there and nowhere else.
A recording without that key answers "unklar" for both of them and never the
number of the top level: a wrong number is worse than an admitted gap, because
only the wrong number gets acted on. The work stock is the sum of scheduled and
running, and those two really do live on the top level.

Standard library only, and no argument: the recording arrives on standard input,
which is what a `tail -1 | python3 96c-lesen.py` in the watchman hands it. A
closed standard input is an empty recording and answers at once, because a reader
that waits for a line it will never get hangs the whole watchman.
"""

from __future__ import annotations

import json
import sys

# The word for every figure that is not in the recording. It is a word and not an
# empty string, so the shell of the watchman can compare against it.
UNKNOWN = "unklar"


def _counter(value: object) -> str:
    """One counter as a decimal string, or the unknown word.

    A bool is not a counter even though python counts it as an int, and a string
    that happens to hold digits is not one either: the admin page answers with
    numbers, and anything else in one of these fields is a shape this reader does
    not recognise.
    """
    if isinstance(value, bool) or not isinstance(value, int | float):
        return UNKNOWN
    return str(int(value))


def _work_stock(recording: dict[str, object]) -> str:
    """scheduled plus running, or the unknown word if either one is missing.

    Not a zero for a missing key, and this is the one place where that choice has
    teeth: the end condition of the watchman reads a stock of zero, so an assumed
    zero here would let it declare the end of a run whose stock it never saw.
    """
    scheduled = _counter(recording.get("scheduled"))
    running = _counter(recording.get("running"))
    if UNKNOWN in (scheduled, running):
        return UNKNOWN
    return str(int(scheduled) + int(running))


def main() -> int:
    """The one line of output, always three words, always exit code 0.

    The exit code is 0 for every shape of recording on purpose. The watchman runs
    under `set -eu`, so a reader that ended with an error over a half written line
    would end the watchman with it, and a missing recording is a normal state of
    the first minutes of a run.
    """
    line = sys.stdin.read().strip()
    if not line:
        print(UNKNOWN, UNKNOWN, UNKNOWN)
        return 0
    try:
        recording = json.loads(line)
    except ValueError:
        print(UNKNOWN, UNKNOWN, UNKNOWN)
        return 0
    # The error key is the shape the observer writes for a request that failed. It
    # is a recording and not a gap, and it must never be read as a measurement.
    if not isinstance(recording, dict) or "fehler" in recording:
        print(UNKNOWN, UNKNOWN, UNKNOWN)
        return 0

    backend = recording.get("backend")
    if not isinstance(backend, dict):
        backend = {}
    print(
        _work_stock(recording),
        _counter(backend.get("indexed")),
        _counter(backend.get("embedded")),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
