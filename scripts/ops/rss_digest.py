#!/usr/bin/env python3
"""Turn a directory of sampler series into the few numbers the report states.

Every figure in docs/performance.md that is a sum over containers comes out of
here, and it lives in the repository for one reason: a number whose derivation
is a shell history on a machine that has been deleted is not reproducible, no
matter how carefully the raw data was kept.

The one decision in this file is how the sum is formed. It is built per point in
time, and only then is its maximum taken. What the box has to carry is the
simultaneous total, not the sum of six maxima that occurred in different minutes.
The other reading, the sum of the per container maxima, is printed next to it as
an upper bound, because a reader will ask, and because the distance between the
two says how much the choice mattered.

Usage: rss_digest.py <directory> [phase-boundary-iso ...]

The directory holds one csv per container, as written by rss_sampler.sh. The
optional boundaries split the series into phases, which is how the base load run
separates idle from load.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path

PREFIX = "findling-rss "
MB = 1024 * 1024


def series(path: Path) -> dict[int, int]:
    """Timestamp to anon, in bytes.

    The header line and the closing summary line are skipped rather than parsed:
    the summary is the sampler's own verdict and belongs in the report as text,
    not in a series of measurements.
    """
    values: dict[int, int] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith(PREFIX):
            continue
        rest = line[len(PREFIX) :]
        if rest.startswith(("timestamp", "summary")):
            continue
        fields = rest.split(",")
        if len(fields) < 2:
            continue
        try:
            values[int(fields[0])] = int(fields[1])
        except ValueError:
            continue
    return values


def iso(stamp: int) -> str:
    return datetime.fromtimestamp(stamp, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_boundary(value: str) -> int:
    moment = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
    return int(moment.timestamp())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    directory = Path(argv[1])
    boundaries = [parse_boundary(value) for value in argv[2:]]

    found = {path.stem: series(path) for path in sorted(directory.glob("*.csv"))}
    found = {name: values for name, values in found.items() if values}
    if not found:
        print(f"rss_digest: no series with a {PREFIX.strip()} prefix under {directory}", file=sys.stderr)
        return 1

    print("| container | samples | mean anon | highest |")
    print("|---|---|---|---|")
    bound = 0
    for name, values in sorted(found.items(), key=lambda pair: -max(pair[1].values())):
        highest = max(values.values())
        bound += highest
        mean = sum(values.values()) / len(values)
        print(f"| {name} | {len(values)} | {mean / MB:.0f} MB | {highest / MB:.0f} MB |")

    # Only the points every series has, so that a sum is never formed from a
    # moment where one sampler had not written yet.
    shared = sorted(set.intersection(*(set(values) for values in found.values())))
    if not shared:
        print("rss_digest: the series share no single point in time", file=sys.stderr)
        return 1
    totals = {stamp: sum(values[stamp] for values in found.values()) for stamp in shared}
    peak_at = max(totals, key=lambda stamp: totals[stamp])
    print()
    print(f"shared samples:   {len(shared)}")
    print(f"window:           {iso(shared[0])} to {iso(shared[-1])}")
    print(f"duration:         {(shared[-1] - shared[0]) / 60:.1f} min")
    print(f"total, mean:      {sum(totals.values()) / len(totals) / MB:.0f} MB")
    print(f"total, peak:      {totals[peak_at] / MB:.0f} MB, at {iso(peak_at)}")
    print(f"upper bound:      {bound / MB:.0f} MB (sum of the maxima, for orientation only)")

    if boundaries:
        print()
        print("| phase | samples | mean | highest |")
        print("|---|---|---|---|")
        edges = [shared[0], *boundaries, shared[-1] + 1]
        for left, right in pairwise(edges):
            part = [totals[stamp] for stamp in shared if left <= stamp < right]
            if not part:
                continue
            print(
                f"| {iso(left)} to {iso(right - 1)} | {len(part)} | "
                f"{sum(part) / len(part) / MB:.0f} MB | {max(part) / MB:.0f} MB |"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
