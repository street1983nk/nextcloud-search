"""What a process start actually costs, measured instead of assumed.

The phase research assumed that one interpreter per file is negligible next to
fetching the file over the network (assumption A11). Nobody measured it, and it
was measured on x86 laptops if at all, while this app ships onto 4 GB ARM boards.
At 100.000 files the difference between a start per file and a child that lives
on decides whether the initial index takes hours or days, which is a product
property and not a detail.

So this module times both shapes and prints the numbers: a cold cycle, meaning a
spawn plus the imports of the extraction path plus one minimal job, and a warm
job against a child that is already running. The projection at the end is the
only figure that matters for the decision, and it is deliberately printed in
hours rather than in microseconds per call.

The tool prints numbers only. It never touches user data, never reads a document
and never logs a path: the job it times is the diagnostic probe of the guard.
"""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass

from findling.extract.sandbox import ExtractionWorker

# The scale the decision is about. 100.000 files is the load target of phase 5 and
# the number the research argued with.
PROJECTED_FILES = 100_000


@dataclass(frozen=True, slots=True)
class Sample:
    """Mean and p95 of one series, in seconds."""

    label: str
    count: int
    mean: float
    p95: float

    def line(self) -> str:
        return f"{self.label:<34} n={self.count:<6} mean={self.mean * 1000:9.2f} ms   p95={self.p95 * 1000:9.2f} ms"


def _summarise(label: str, durations: list[float]) -> Sample:
    """p95 by rank, not by interpolation: with 1000 samples the 950th is the answer."""
    ordered = sorted(durations)
    rank = min(len(ordered) - 1, int(0.95 * len(ordered)))
    return Sample(
        label=label,
        count=len(ordered),
        mean=statistics.fmean(ordered),
        p95=ordered[rank],
    )


def measure_cold_starts(cycles: int) -> Sample:
    """Time a full spawn, the imports of the child, and one minimal job, per cycle."""
    durations: list[float] = []
    for _ in range(cycles):
        worker = ExtractionWorker(max_files=1, timeout_seconds=120)
        started = time.perf_counter()
        worker.probe("sleep", 0.0)
        durations.append(time.perf_counter() - started)
        worker.stop()
    return _summarise("cold cycle, spawn and imports", durations)


def measure_warm_jobs(jobs: int) -> Sample:
    """Time the same minimal job against one child that stays alive."""
    worker = ExtractionWorker(max_files=jobs + 1, timeout_seconds=120)
    durations: list[float] = []
    try:
        worker.probe("sleep", 0.0)  # not counted: this one pays for the spawn
        for _ in range(jobs):
            started = time.perf_counter()
            worker.probe("sleep", 0.0)
            durations.append(time.perf_counter() - started)
    finally:
        worker.stop()
    return _summarise("warm job, same child", durations)


def report(cold: Sample, warm: Sample) -> str:
    """The two series and the only number the decision hangs on."""
    cold_hours = cold.mean * PROJECTED_FILES / 3600
    warm_hours = warm.mean * PROJECTED_FILES / 3600
    return "\n".join(
        [
            cold.line(),
            warm.line(),
            "",
            f"projected over {PROJECTED_FILES} files:",
            f"  one child per file : {cold_hours:8.2f} h of pure process handling",
            f"  one child, recycled: {warm_hours:8.2f} h of pure process handling",
            f"  saved              : {cold_hours - warm_hours:8.2f} h",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Measure the process start cost of the extraction guard.")
    parser.add_argument(
        "--spawns",
        type=int,
        default=100,
        help="number of cold cycles, and of warm jobs, to time",
    )
    arguments = parser.parse_args(argv)
    cycles = max(1, arguments.spawns)
    print(f"extraction start cost, {cycles} spawns")
    print(report(measure_cold_starts(cycles), measure_warm_jobs(cycles)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
