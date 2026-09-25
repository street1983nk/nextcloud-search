#!/usr/bin/env python3
"""Count the slow backend calls of finding M-01 in one time window of nextcloud.log.

**DIESE FASSUNG IST NICHT GEFAHREN.** No raw file lies next to it; what it counts
on the box is measured on the trip.

The line this reader looks for is written by the PHP half,
php/lib/Service/ExAppService.php, whenever one inner call to the container takes
at least SLOW_CALL_LOG_MILLISECONDS (1000 ms): the message
"Findling: slow backend call" with the context path, innerMs and ceilingMs.
Nextcloud writes its log as one JSON object per line and puts that context
under "data"; this reader also accepts it under "context" or on the top level,
because the place has moved between Nextcloud releases and a reader that knew
only one of them would count nothing on the other.

**Pitfall 5 of the research.** The line is written at level info, and the
default loglevel of a Nextcloud is 2 (warning), so on a box that was not
switched the reader counts nothing and that nothing would read like "no call
above one second". The run script therefore reads the level with
`occ config:system:get loglevel`, sets it to 1 for the block and back
afterwards, and it takes the path of the log from
`occ config:system:get logfile`, or from datadirectory plus nextcloud.log when
logfile is not set. The counter-check is a cold start search of about two
seconds outside, which has to produce one line; if it does not, the level or
this reader is wrong, not the backend.

**What is printed**, and nothing else, because the raw data of a trip go into a
public repository (T-22-09): the time stamp, the path (a route of this app,
never a file name), innerMs and ceilingMs. User, remote address, URL, request id
and user agent of the log line never leave this tool.

  stufe <name> langsame-aufrufe <anzahl>
  aufruf <time> <path> innerMs <x> ceilingMs <y>      one per hit
  maximum innerMs <x> ceilingMs <y>                   or: maximum innerMs keins
  kaputte-zeilen <n>                                  lines that were no JSON

A log that cannot be read answers "stufe <name> langsame-aufrufe unklar" and
not 0: "not known" and "none" are two different answers, and only the second
one may go into the report as a figure. The exit code is 0 in both cases,
because the run script runs under set -eu and reads the line, not the code; a
wrong argument ends with 2 through argparse.

Call: 91m-langsame-aufrufe.py --log <nextcloud.log> --von <ISO UTC> --bis <ISO UTC> --stufe <name>

Standard library only, because the host python of the box runs it.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Sequence
from datetime import UTC, datetime

MESSAGE = "Findling: slow backend call"
UNKNOWN = "unklar"
CONTEXT_KEYS = ("data", "context")


def moment(text: str) -> datetime:
    """An ISO time stamp as an aware UTC datetime; a naive one counts as UTC."""
    value = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def window_bound(text: str) -> datetime:
    """An argparse type for --von and --bis."""
    try:
        return moment(text)
    except ValueError as error:
        message = f"kein ISO-Zeitstempel: {text!r}"
        raise argparse.ArgumentTypeError(message) from error


def number(value: object) -> float | None:
    """A number of the log, or None. A bool is no number here.

    Nextcloud 34 writes every context value of a log line as a string: the PHP
    half hands over the float 1171.2, and the line carries "innerMs":"1171.2".
    Found in the dress rehearsal of 22-06 against the local test Nextcloud,
    where a reader that took only JSON numbers counted the one slow call of the
    cold start as a broken line and printed "langsame-aufrufe 0". A string is
    therefore read as a number when it is one, and only a finite one counts.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value.strip())
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def context_of(entry: dict[str, object]) -> dict[str, object]:
    """The context of the line, wherever this Nextcloud put it."""
    for key in CONTEXT_KEYS:
        candidate = entry.get(key)
        if isinstance(candidate, dict) and "innerMs" in candidate:
            return {str(name): value for name, value in candidate.items()}
    return entry


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Die M-01-Zeilen eines Zeitfensters aus nextcloud.log.")
    parser.add_argument("--log", required=True)
    parser.add_argument("--von", required=True, type=window_bound)
    parser.add_argument("--bis", required=True, type=window_bound)
    parser.add_argument("--stufe", required=True)
    arguments = parser.parse_args(argv)
    stage = arguments.stufe

    try:
        with open(arguments.log, encoding="utf-8", errors="replace") as log:
            lines = log.read().splitlines()
    except OSError:
        print(f"stufe {stage} langsame-aufrufe {UNKNOWN}")
        return 0

    broken = 0
    hits: list[tuple[str, str, float, float | None]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            broken += 1
            continue
        if not isinstance(entry, dict) or entry.get("message") != MESSAGE:
            continue
        stamp = entry.get("time")
        try:
            when = moment(stamp) if isinstance(stamp, str) else None
        except ValueError:
            when = None
        if when is None:
            broken += 1
            continue
        if not arguments.von <= when <= arguments.bis:
            continue
        context = context_of(entry)
        inner = number(context.get("innerMs"))
        if inner is None:
            broken += 1
            continue
        path = context.get("path")
        hits.append(
            (
                when.strftime("%Y-%m-%dT%H:%M:%SZ"),
                path if isinstance(path, str) and path else UNKNOWN,
                inner,
                number(context.get("ceilingMs")),
            )
        )

    print(f"stufe {stage} langsame-aufrufe {len(hits)}")
    for when, path, inner, ceiling in hits:
        shown = UNKNOWN if ceiling is None else f"{ceiling:.1f}"
        print(f"aufruf {when} {path} innerMs {inner:.1f} ceilingMs {shown}")
    if hits:
        _, _, inner, ceiling = max(hits, key=lambda hit: hit[2])
        shown = UNKNOWN if ceiling is None else f"{ceiling:.1f}"
        print(f"maximum innerMs {inner:.1f} ceilingMs {shown}")
    else:
        print("maximum innerMs keins")
    print(f"kaputte-zeilen {broken}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
