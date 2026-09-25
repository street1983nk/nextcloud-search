#!/usr/bin/env python3
"""How many OCR pages per second N parallel extraction slots produce.

W3 of phase 22. The question behind it is decision D-03: does a second, third
or fourth OCR slot buy throughput on the target hardware, or does it only buy
memory? The product runs exactly one extraction at a time (IDX-08), so the
answer cannot be read off a running instance. This probe builds the answer out
of the product's own parts instead: N threads, and every thread holds its own
ExtractionWorker, the long lived child of findling.extract.sandbox, and hands it
the same synthetic scan over the OCR route with route="ocr". That is the path a
scanned document takes in production, child process, page rendering and
tesseract grandchild included, with nothing mocked.

What is measured per round, and where it comes from:

* wall time around the N parallel runs, and from it pages per second, which is
  N times the page count of the scan divided by the wall time;
* anon out of memory.stat and usage_usec out of cpu.stat of the cgroup of this
  container, read before and after the round. The cgroup and not a resource
  counter of this process, because the children of the workers live across the
  whole run and their tesseract grandchildren are waited for by the child and
  not by this process; only the cgroup sees all of them.

Every worker handles the scan once before the first timed round, so that the
start of the child and its imports are not billed to round 1. The median over
the rounds is the figure F4 of measure.yml is built from.

The second mode, --mode single, checks one sentence of docs/performance.md: that
tesseract uses both cores. The product sets OMP_THREAD_LIMIT=1 for every call
(findling.extract.ocr), so this mode renders one page of the scan the way the
product does and runs tesseract on it with the product's arguments, once with
that variable and once without it, and prints wall time and cgroup CPU time of
both.

What it prints: arch, the CPUs this process may run on (sched_getaffinity, not
the CPUs of the host), the slot count, one line per round and the median. Never
a line of the extracted text and never a path: the scan is named by its base
name only, and it is a synthetic file out of scripts/dev/build_load_corpus.py,
never a user file.

Run inside the product image, with this directory mounted read only, for
example:

    docker run --rm --network none --cpuset-cpus 0-3 \\
      -v "$PWD/scripts/ops:/ops:ro" -v "$SCAN_DIR:/scan:ro" \\
      --entrypoint /app/.venv/bin/python <image> \\
      /ops/ocr_slot_probe.py --slots 4 --rounds 3 --scan /scan/scan-8.pdf

The findling package is imported inside the functions that need it and not at
the top, so the argument check and the report can be loaded and tested on a
machine without the product installed.
"""

from __future__ import annotations

import argparse
import os
import platform
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

# The cgroup of this container as the container sees it: with cgroup v2 and a
# private cgroup namespace, which is the docker default on Ubuntu 24.04, the
# root of /sys/fs/cgroup is the container's own cgroup.
CGROUP = Path("/sys/fs/cgroup")

PDF_MIME = "application/pdf"

DEFAULT_ROUNDS = 3
DEFAULT_PAGES = 8
# The parent deadline of one run. The product's soft deadline of an OCR job is
# lower than this, so a run that hits it is a truncated result and not a hang.
DEFAULT_TIMEOUT_SECONDS = 900.0

THREAD_LIMIT_VARIABLE = "OMP_THREAD_LIMIT"


@dataclass(frozen=True)
class Round:
    """One timed round. Numbers only: there is no field a text could live in."""

    number: int
    wall_seconds: float
    pages: int
    failed_slots: int
    anon_bytes_delta: int | None
    cpu_usec: int | None

    @property
    def pages_per_second(self) -> float:
        return self.pages / self.wall_seconds if self.wall_seconds > 0 else 0.0


def visible_cpus() -> int:
    """The CPUs this process may run on, which is what a cpu set changes."""
    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        return len(affinity(0))
    return os.cpu_count() or 1


def cgroup_value(file_name: str, key: str, root: Path = CGROUP) -> int | None:
    """One counter out of a flat keyed cgroup file, or None when it cannot be read."""
    try:
        text = (root / file_name).read_text(encoding="ascii")
    except OSError:
        return None
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == key and parts[1].isdigit():
            return int(parts[1])
    return None


def delta(before: int | None, after: int | None) -> int | None:
    return None if before is None or after is None else after - before


def number_or_na(value: float | None, digits: int = 0) -> str:
    if value is None:
        return "na"
    return f"{value:.{digits}f}"


def succeeded(outcome: object) -> bool:
    """A slot counts when it indexed the whole scan: no failure, no cut."""
    # State is a StrEnum, so its str() is the plain value; a failed or skipped
    # verdict and a truncated one (reason TRUNCATED) all count as a lost slot.
    return str(getattr(outcome, "state", "")) == "indexed" and getattr(outcome, "reason", None) is None


def round_from_outcomes(
    number: int,
    wall_seconds: float,
    pages_per_scan: int,
    outcomes: Sequence[object],
    anon_bytes_delta: int | None,
    cpu_usec: int | None,
) -> Round:
    """Reduce the outcomes of one round to numbers. The text is not looked at."""
    failed = sum(1 for outcome in outcomes if not succeeded(outcome))
    return Round(
        number=number,
        wall_seconds=wall_seconds,
        pages=pages_per_scan * (len(outcomes) - failed),
        failed_slots=failed,
        anon_bytes_delta=anon_bytes_delta,
        cpu_usec=cpu_usec,
    )


def report_lines(arch: str, cpus: int, slots: int, rounds: Sequence[Round]) -> list[str]:
    """Everything the slot mode prints, as a list so a test can read it."""
    lines = [f"arch {arch}", f"cpus_visible {cpus}", f"slots {slots}"]
    lines.extend(
        f"round {item.number} wall_seconds {item.wall_seconds:.3f} "
        f"pages_per_second {item.pages_per_second:.3f} "
        f"anon_bytes_delta {number_or_na(item.anon_bytes_delta)} "
        f"cpu_usec {number_or_na(item.cpu_usec)} "
        f"failed_slots {item.failed_slots}"
        for item in rounds
    )
    median = statistics.median(item.pages_per_second for item in rounds) if rounds else None
    lines.append(f"pages_per_second_median {number_or_na(median, 3)}")
    return lines


def _parallel(jobs: Iterable[Callable[[], object]]) -> list[object]:
    """Run every job on its own thread at once and return their results in order."""
    callables = list(jobs)
    results: list[object] = [None] * len(callables)

    def run(index: int, job: Callable[[], object]) -> None:
        results[index] = job()

    threads = [threading.Thread(target=run, args=(index, job)) for index, job in enumerate(callables)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def measure_slots(scan: Path, slots: int, rounds: int, pages: int, timeout_seconds: float) -> list[Round]:
    """The slot mode: N workers, one untimed warm up, then the timed rounds."""
    from findling.extract.sandbox import ExtractionWorker

    size = scan.stat().st_size
    workers = [ExtractionWorker(timeout_seconds=timeout_seconds) for _ in range(slots)]

    def job(worker: ExtractionWorker) -> Callable[[], object]:
        return lambda: worker.run(str(scan), PDF_MIME, size, route="ocr", timeout_seconds=timeout_seconds)

    measured: list[Round] = []
    try:
        _parallel(job(worker) for worker in workers)
        for number in range(1, rounds + 1):
            anon_before = cgroup_value("memory.stat", "anon")
            cpu_before = cgroup_value("cpu.stat", "usage_usec")
            started = time.perf_counter()
            outcomes = _parallel(job(worker) for worker in workers)
            wall = time.perf_counter() - started
            anon_after = cgroup_value("memory.stat", "anon")
            cpu_after = cgroup_value("cpu.stat", "usage_usec")
            measured.append(
                round_from_outcomes(
                    number,
                    wall,
                    pages,
                    outcomes,
                    delta(anon_before, anon_after),
                    delta(cpu_before, cpu_after),
                )
            )
    finally:
        for worker in workers:
            worker.stop()
    return measured


def measure_single(scan: Path, rounds: int) -> list[str]:
    """The single mode: one rendered page, tesseract with and without the limit."""
    import pypdfium2

    from findling import config
    from findling.extract import ocr, raster

    resolved = config.settings()
    document = pypdfium2.PdfDocument(str(scan))
    try:
        png = raster.render_page_png(document, 0, dpi=resolved.ocr_dpi)
    finally:
        document.close()
    command = [ocr._ENGINE, "-", "-", "-l", "+".join(resolved.ocr_languages), *ocr._ENGINE_OPTIONS]
    inherited = {key: value for key, value in os.environ.items() if key != THREAD_LIMIT_VARIABLE}
    variants = (("omp_limit_1", {**inherited, THREAD_LIMIT_VARIABLE: "1"}), ("omp_unset", inherited))

    walls: dict[str, list[float]] = {name: [] for name, _ in variants}
    cpus: dict[str, list[int]] = {name: [] for name, _ in variants}
    failed: dict[str, int] = dict.fromkeys(walls, 0)
    # Alternating inside every round, so a drift of the machine over the run
    # lands on both variants and not on the second one alone.
    for _ in range(rounds):
        for name, environment in variants:
            cpu_before = cgroup_value("cpu.stat", "usage_usec")
            started = time.perf_counter()
            finished = subprocess.run(  # noqa: S603 - an argument list, never a shell
                command,
                input=png,
                capture_output=True,
                env=environment,
                check=False,
            )
            walls[name].append(time.perf_counter() - started)
            used = delta(cpu_before, cgroup_value("cpu.stat", "usage_usec"))
            if used is not None:
                cpus[name].append(used)
            if finished.returncode != 0:
                failed[name] += 1

    lines = [
        f"arch {platform.machine()}",
        f"cpus_visible {visible_cpus()}",
        f"omp_env_preset {'yes' if THREAD_LIMIT_VARIABLE in os.environ else 'no'}",
        f"rounds {rounds}",
    ]
    for name, _ in variants:
        cpu = statistics.median(cpus[name]) if cpus[name] else None
        lines.append(
            f"{name} wall_seconds {statistics.median(walls[name]):.3f} "
            f"cpu_usec {number_or_na(cpu)} failed {failed[name]}"
        )
    return lines


def _at_least_one(text: str) -> int:
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("has to be a whole number") from error
    if value < 1:
        raise argparse.ArgumentTypeError("has to be at least one")
    return value


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ocr_slot_probe.py",
        description="OCR pages per second over N parallel extraction slots (W3 of phase 22).",
    )
    parser.add_argument("--slots", type=_at_least_one, default=1, help="parallel extraction workers, at least 1")
    parser.add_argument("--rounds", type=_at_least_one, default=DEFAULT_ROUNDS, help="timed rounds, default 3")
    parser.add_argument(
        "--scan", type=Path, required=True, help="the synthetic scan PDF out of build_load_corpus.py, never a user file"
    )
    parser.add_argument("--pages", type=_at_least_one, default=DEFAULT_PAGES, help="pages of the scan, default 8")
    parser.add_argument("--mode", choices=("slots", "single"), default="slots")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="deadline of one run")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = _parse(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else 2
    scan: Path = arguments.scan
    if not scan.is_file():
        print(f"ocr_slot_probe: no scan file called {scan.name}", file=sys.stderr)
        return 2
    print(f"scan {scan.name}", file=sys.stderr)
    if arguments.mode == "single":
        for line in measure_single(scan, arguments.rounds):
            print(line, flush=True)
        return 0
    rounds = measure_slots(scan, arguments.slots, arguments.rounds, arguments.pages, arguments.timeout)
    for line in report_lines(platform.machine(), visible_cpus(), arguments.slots, rounds):
        print(line, flush=True)
    return 1 if any(item.failed_slots for item in rounds) else 0


if __name__ == "__main__":
    sys.exit(main())
