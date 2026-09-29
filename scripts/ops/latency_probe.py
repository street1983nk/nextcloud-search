#!/usr/bin/env python3
"""Latency of the Findling search and of status.php, as two separate series.

D-26-12, part 2. Phase 26 starts every extraction child with nice 10 (D-26-11,
field report issue #19: the web interface timed out while the index was busy).
This probe answers what that buys, under full OCR load, for the two things a
user of the instance waits on:

* ``--target search``: the unified search route of the Findling provider,
  /ocs/v2.php/search/providers/findling/search. The Nextcloud side forwards it
  to the container, and the container answers from its main process, which
  shares the cgroup of the container with the niced children.
* ``--target status``: /status.php, answered by the Nextcloud container alone.

Why two series and never one mixed figure: nice only orders processes against
each other inside the same cgroup (research pitfall 8). The CPU scheduler first
shares time between the cgroups of the containers and only then, inside one of
them, by nice value. The niced children compete with the search in the Findling
container, so the search can profit; status.php runs in another container and
is expected not to. A single averaged figure would hide exactly that line.

The comparison "with nice" against "without nice" is made from two images (the
last state before phase 26 against HEAD), never from a switch in the product.

What it prints, one line per run:

    target <search|status> requests <n> p50_ms <x> p95_ms <y> max_ms <z> errors <e>

Never a URL with its query, never the account, never the search term and never
a byte of an answer. A timeout counts as an error and contributes the timeout as
its latency, so a series that stalls shows it in p95 and max rather than
dropping out of them.

Credentials come from FINDLING_PROBE_USER and the password variable below only;
they are never arguments. status.php needs none.

Usage:

    export FINDLING_PROBE_USER=probe FINDLING_PROBE_PASSWORD='...'
    ./latency_probe.py --base-url http://localhost:8080 --target search --term Rechnung
    ./latency_probe.py --base-url http://localhost:8080 --target status
"""

from __future__ import annotations

import argparse
import base64
import os
import statistics
import sys
import time
import urllib.parse
import urllib.request
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

SEARCH_ROUTE: Final = "/ocs/v2.php/search/providers/findling/search"
STATUS_ROUTE: Final = "/status.php"

USER_ENV: Final = "FINDLING_PROBE_USER"
PASSWORD_ENV: Final = "FINDLING_PROBE_PASSWORD"  # noqa: S105 - a variable name, not a value

DEFAULT_REQUESTS: Final = 200
DEFAULT_INTERVAL_SECONDS: Final = 0.5
# Above the 2 s budget of the unified search, so an answer that overruns it is
# measured rather than cut off at the budget.
DEFAULT_TIMEOUT_SECONDS: Final = 5.0
DEFAULT_TERM: Final = "Rechnung"


@dataclass(frozen=True, slots=True)
class Sample:
    """One request: its wall time and whether it failed. No field for text."""

    ms: float
    error: bool


@dataclass(frozen=True, slots=True)
class Percentiles:
    p50: float
    p95: float
    max: float


def percentiles(values: Sequence[float]) -> Percentiles:
    """Median, nearest-rank p95 and maximum, the reading search_load.py uses."""
    if not values:
        return Percentiles(0.0, 0.0, 0.0)
    ordered = sorted(values)
    index = min(len(ordered) - 1, round(0.95 * (len(ordered) - 1)))
    return Percentiles(statistics.median(ordered), ordered[index], ordered[-1])


def report_line(target: str, samples: Sequence[Sample]) -> str:
    """The one output line of a series, figures only."""
    result = percentiles([sample.ms for sample in samples])
    errors = sum(1 for sample in samples if sample.error)
    return (
        f"target {target} requests {len(samples)} p50_ms {result.p50:.1f} "
        f"p95_ms {result.p95:.1f} max_ms {result.max:.1f} errors {errors}"
    )


def _authorization() -> str:
    """Basic auth from the environment, in the one place the secret exists."""
    user = os.environ.get(USER_ENV, "")
    secret = os.environ.get(PASSWORD_ENV, "")
    if not user or not secret:
        raise SystemExit(f"latency_probe: {USER_ENV} and {PASSWORD_ENV} have to be set for --target search")
    return "Basic " + base64.b64encode(f"{user}:{secret}".encode()).decode("ascii")


def _url(base_url: str, target: str, term: str) -> str:
    base = base_url.rstrip("/")
    if target == "status":
        return base + STATUS_ROUTE
    query = urllib.parse.urlencode({"term": term, "limit": "5"})
    return f"{base}{SEARCH_ROUTE}?{query}"


def _timed_request(url: str, headers: dict[str, str], timeout: float) -> float:
    """Seconds for one full answer; raises on transport errors and HTTP errors."""
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 - scheme checked in _checked_base_url
    started = time.perf_counter()
    with urllib.request.urlopen(request, timeout=timeout) as answer:  # noqa: S310
        answer.read()
    return time.perf_counter() - started


def _one(url: str, headers: dict[str, str], timeout: float) -> Sample:
    started = time.perf_counter()
    try:
        seconds = _timed_request(url, headers, timeout)
    except TimeoutError:
        return Sample(ms=timeout * 1000, error=True)
    except (OSError, ValueError):
        # The type of the failure is not reported at all: a message could carry
        # the address with its query. The time until the failure is kept.
        elapsed = time.perf_counter() - started
        return Sample(ms=min(elapsed, timeout) * 1000, error=True)
    return Sample(ms=seconds * 1000, error=False)


def _checked_base_url(raw: str) -> str:
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("the base url has to be an http or https address")
    return raw


def _positive_int(raw: str) -> int:
    number = int(raw)
    if number < 1:
        raise argparse.ArgumentTypeError("has to be at least one")
    return number


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="latency_probe.py",
        description="Latency of the Findling search or of status.php, one series per run (D-26-12).",
    )
    parser.add_argument("--base-url", required=True, type=_checked_base_url)
    parser.add_argument("--target", required=True, choices=("search", "status"))
    parser.add_argument("--requests", type=_positive_int, default=DEFAULT_REQUESTS)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_SECONDS)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--term", default=DEFAULT_TERM, help="Search term out of the synthetic corpus")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse(argv)
    headers = {"Accept": "application/json"}
    if arguments.target == "search":
        headers["Authorization"] = _authorization()
        headers["OCS-APIRequest"] = "true"
    url = _url(arguments.base_url, arguments.target, arguments.term)

    samples: list[Sample] = []
    for number in range(arguments.requests):
        if number:
            time.sleep(arguments.interval)
        samples.append(_one(url, headers, arguments.timeout))

    print(report_line(arguments.target, samples))
    if all(sample.error for sample in samples):
        print("latency_probe: not one request was answered", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
