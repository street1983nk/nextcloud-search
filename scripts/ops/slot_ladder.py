#!/usr/bin/env python3
"""How many OCR pages per second the product itself gets out of 1, 2 and 4 slots.

The ladder of SC3 in phase 26 (D-26-09). The W4 curve of phase 22 answered
the raw question with ocr_slot_probe.py: N extraction children side by side,
nothing else. That curve (factor 3.955 at N = 4) is the ceiling. This tool
measures the product under it: the real Poller.run_once with a pinned slot
count, the real SlotPool with its children, the real index writer and a real
state database, and a fake queue that hands out a fixed synthetic corpus as
OCR rows. Everything a pass does in series, the claim, the trim of the rows
to two per slot, the barrier, the commit and the verdicts, is paid inside the
timed window, which is why the product curve lies below the raw one.

What one round is: a fresh state.db and a fresh index in a directory of their
own, a fresh Poller over the shared pool, and run_once until the queue holds
no row any more. Measured are the wall time of those passes and the pages of
the scans that ended indexed without a reason; a scan that did not counts in
the failed column, and a round with a failed scan makes the median
"unbestimmt". The children of the pool are started and warmed by one untimed
extraction each before the first round, so their start is not billed to it.

The throttle of D-26-02 is neutral in this setup: the headroom the poller
reads is a fixed 64 GiB from two slots on, so the pinned count is the count
that runs. The claim honours the limit and the byte budget of the poller the
way the companion does; a claim the byte budget cut is counted in
byte_capped_claims (Pitfall 11 of the phase research), because it can leave a
pass with fewer rows than two per slot.

The second mode, --mode embed, is the side figure of pattern 9 (A5, no
acceptance criterion): the int8 engine of the image embeds 64 fixed synthetic
passages as eight rows of eight, once one row at a time and once with two
threads at once, the question behind embed_slots 2 in Performance.

What it prints: arch, the CPUs this process may run on, the slot count, one
line per round and the median. Numbers and counters only: never a file name,
never a path and never a line of extracted text. The corpus is synthetic,
built by scripts/dev/build_load_corpus.py with a fixed seed, never a user
file.

Run inside the product image, with this directory mounted read only, e.g.:

    docker run --rm --network none --cpuset-cpus 0-3 \\
      -v "$PWD/scripts/ops:/ops:ro" -v "$LADDER_DIR:/scan/ladder:ro" \\
      --entrypoint /app/.venv/bin/python <image> \\
      /ops/slot_ladder.py --slots 4 --rounds 3 --scan-dir /scan/ladder

The findling package and pypdfium2 are imported inside the functions that
need them and not at the top, so the argument check and the report can be
loaded and tested on a machine without the product installed.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import platform
import statistics
import sys
import tempfile
import threading
import time
from collections import deque
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, cast

PDF_MIME = "application/pdf"

DEFAULT_ROUNDS = 3
MAX_SLOTS = 16

# The headroom the throttle reads from two slots on. Far above what any count
# of this ladder needs, so the throttle never cuts the pinned count.
LADDER_HEADROOM_BYTES = 64 * 2**30

# Where a queue id and a file id of the corpus start. Arbitrary, only apart.
QUEUE_ID_BASE = 1000
FILE_ID_BASE = 5000
LADDER_USER = "ladder"

# The side figure: 64 passages as eight rows of eight, the shape of eight
# documents of eight chunks each.
EMBED_PASSAGES = 64
EMBED_ROW = 8
EMBED_WORDS = (
    "Antrag",
    "Beschluss",
    "Gemeinderat",
    "Haushalt",
    "Satzung",
    "Vorlage",
    "Verwaltung",
    "Sitzung",
    "Frist",
    "Vertrag",
    "Rechnung",
    "Bauamt",
    "Schule",
    "Strasse",
    "Planung",
    "Kosten",
    "Ausschuss",
    "Bericht",
    "Anlage",
    "Mittel",
    "wird",
    "die",
    "der",
    "das",
    "und",
    "mit",
    "fuer",
    "nach",
    "zum",
    "beraten",
    "genehmigt",
    "vorgelegt",
)
EMBED_PASSAGE_WORDS = 60


@dataclass(frozen=True)
class Round:
    """One timed round of the ladder. Numbers only, no field a text could live in."""

    number: int
    slots: int
    pages: int
    seconds: float
    failed: int

    @property
    def pages_per_second(self) -> float:
        return self.pages / self.seconds if self.seconds > 0 else 0.0


@dataclass(frozen=True)
class LadderRow:
    """One scan of the corpus as the fake queue holds it."""

    queue_id: int
    file_id: int
    size: int
    path: Path


def visible_cpus() -> int:
    """The CPUs this process may run on, which is what a cpu set changes."""
    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        return len(affinity(0))
    return os.cpu_count() or 1


def format_round(item: Round) -> str:
    """The line of one round, without a path and without a text."""
    return (
        f"round {item.number} slots {item.slots} pages {item.pages} seconds {item.seconds:.3f} "
        f"pages_per_second {item.pages_per_second:.3f} failed {item.failed}"
    )


def summarize(rounds: Sequence[Round]) -> str:
    """The median line; "unbestimmt" when there is no round or a round lost a scan."""
    if not rounds or any(item.failed for item in rounds):
        return "pages_per_second_median unbestimmt"
    median = statistics.median(item.pages_per_second for item in rounds)
    return f"pages_per_second_median {median:.3f}"


def report_lines(arch: str, cpus: int, slots: int, scans: int, byte_capped: int, rounds: Sequence[Round]) -> list[str]:
    """Everything the poller mode prints, as a list so a test can read it."""
    lines = [f"arch {arch}", f"cpus_visible {cpus}", f"slots {slots}", f"scans {scans}"]
    lines.extend(format_round(item) for item in rounds)
    lines.append(f"byte_capped_claims {byte_capped}")
    lines.append(summarize(rounds))
    return lines


def embed_lines(arch: str, cpus: int, passages: int, timings: dict[int, list[float]]) -> list[str]:
    """Everything the embed mode prints: one line per slot count, median of the rounds."""
    lines = [f"arch {arch}", f"cpus_visible {cpus}", f"passages {passages}"]
    for slots in sorted(timings):
        walls = [wall for wall in timings[slots] if wall > 0]
        if not walls or len(walls) != len(timings[slots]):
            lines.append(f"embed_slots {slots} passages_per_second unbestimmt")
            continue
        lines.append(f"embed_slots {slots} passages_per_second {passages / statistics.median(walls):.3f}")
    return lines


def synthetic_passages(count: int = EMBED_PASSAGES, words: int = EMBED_PASSAGE_WORDS) -> list[str]:
    """Fixed passages out of a small word list and a linear congruential sequence."""
    state = 26_09
    passages: list[str] = []
    for _ in range(count):
        chosen: list[str] = []
        for _ in range(words):
            state = (state * 1_103_515_245 + 12_345) % 2**31
            chosen.append(EMBED_WORDS[state % len(EMBED_WORDS)])
        passages.append(" ".join(chosen) + ".")
    return passages


def corpus_of(scan_dir: Path) -> list[LadderRow]:
    """The PDFs of the corpus directory in name order, as rows of the fake queue."""
    paths = sorted(path for path in scan_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")
    return [
        LadderRow(queue_id=QUEUE_ID_BASE + index, file_id=FILE_ID_BASE + index, size=path.stat().st_size, path=path)
        for index, path in enumerate(paths)
    ]


class LadderQueue:
    """The fake work stock: every scan an OCR row, claimed, trimmed, handed back.

    It answers the calls of DocumentQueue that a pass makes. A claim hands out
    rows from the front up to the limit and the byte budget, at least one; an
    unlock puts rows back at the front in their order, which is what the trim
    of D-26-13 relies on; an acknowledgement and a requeue take rows out.
    """

    def __init__(self, rows: Sequence[LadderRow]) -> None:
        self._stock: deque[LadderRow] = deque(rows)
        self._held: dict[int, LadderRow] = {}
        self.claims = 0
        self.byte_capped = 0
        self.failed: dict[int, str] = {}

    @property
    def pending(self) -> bool:
        """True while a row waits or is held by a pass."""
        return bool(self._stock) or bool(self._held)

    async def companion_choice(self) -> Any:
        from findling.nc.queue import CompanionChoice

        return CompanionChoice(profile=None, precision=None)

    async def claim(self, *, limit: int, max_bytes: int, lane: str | None = None) -> Any:
        from findling.nc.queue import ClaimResult

        self.claims += 1
        rows: list[LadderRow] = []
        total = 0
        while self._stock and len(rows) < limit:
            row = self._stock[0]
            if rows and total + row.size > max_bytes:
                self.byte_capped += 1
                break
            self._stock.popleft()
            total += row.size
            self._held[row.queue_id] = row
            rows.append(row)
        return ClaimResult(jobs=tuple(_job_of(row) for row in rows), lane_honored=lane is not None)

    async def unlock(self, ids: Sequence[int]) -> Any:
        from findling.nc.queue import CallResult

        back = [self._held.pop(queue_id) for queue_id in ids if queue_id in self._held]
        for row in reversed(back):
            self._stock.appendleft(row)
        return CallResult(ok=True, count=len(back))

    async def acknowledge(self, done: Sequence[int], failed: dict[int, str], skipped: Any = None) -> Any:
        from findling.nc.queue import CallResult

        del skipped
        count = 0
        for queue_id in [*done, *failed]:
            if self._held.pop(queue_id, None) is not None:
                count += 1
        self.failed.update(failed)
        return CallResult(ok=True, count=count)

    async def requeue(self, file_ids: Sequence[int], *, kind: str) -> Any:
        from findling.nc.queue import CallResult

        del kind
        moved = [queue_id for queue_id, row in self._held.items() if row.file_id in set(file_ids)]
        for queue_id in moved:
            del self._held[queue_id]
        return CallResult(ok=True, count=len(moved))

    async def top_up(self) -> str:
        from findling.nc.queue import TOPUP_IDLE

        return TOPUP_IDLE

    async def stats(self) -> Any:
        from findling.nc.queue import QueueStats

        return QueueStats()


def _job_of(row: LadderRow) -> Any:
    from findling.nc.queue import KIND_OCR, QueueJob

    name = f"ladder-{row.file_id}.pdf"
    return QueueJob(
        queue_id=row.queue_id,
        file_id=row.file_id,
        storage_id=1,
        root_id=1,
        path=name,
        title=name,
        mime=PDF_MIME,
        size=row.size,
        mtime=0,
        etag=f"ladder{row.file_id}",
        user_ids=(LADDER_USER,),
        fetch_as=LADDER_USER,
        is_update=False,
        kind=KIND_OCR,
    )


def local_fetch(rows: Sequence[LadderRow]) -> Callable[..., Any]:
    """A fetch_file_stream stand in that reads the scan from the corpus directory."""
    by_id = {row.file_id: row.path for row in rows}

    async def fetch(nc: object, file_id: int, user_id: str, fp: IO[bytes], *, client: object = None) -> int | None:
        del nc, user_id, client
        path = by_id.get(file_id)
        if path is None:
            return None
        data = await asyncio.to_thread(path.read_bytes)
        fp.write(data)
        return len(data)

    return fetch


class _Gateway:
    """The pooled HTTP client of the poller; this setup never opens one."""

    async def aclose(self) -> None:
        return None


def page_counts(rows: Sequence[LadderRow]) -> dict[int, int]:
    """Pages per scan, read once with the library the product renders with."""
    import pypdfium2

    counts: dict[int, int] = {}
    for row in rows:
        document = pypdfium2.PdfDocument(str(row.path))
        try:
            counts[row.file_id] = len(document)
        finally:
            document.close()
    return counts


async def _warm(pool: Any, rows: Sequence[LadderRow], slots: int, deadline: float) -> None:
    """Start every child of the pool and let it read the smallest scan once, untimed."""
    from findling.extract.dispatch import Route

    smallest = min(rows, key=lambda row: row.size)
    await asyncio.gather(
        *(
            pool.call(pool.run, str(smallest.path), PDF_MIME, smallest.size, route=Route.OCR, timeout_seconds=deadline)
            for _ in range(slots)
        )
    )


async def _one_round(
    number: int, slots: int, rows: Sequence[LadderRow], pages: dict[int, int], pool: Any, root: Path
) -> tuple[Round, int]:
    """One timed round over a fresh state.db and a fresh index. Returns the round and the capped claims."""
    from findling.config import settings
    from findling.index.open import open_index
    from findling.index.wordlist import build_artifact
    from findling.index.wordlist_nl import dutch_digest_for
    from findling.index.writer import IndexBatchWriter
    from findling.store.repo import open_store
    from findling.worker.poller import ROUND_WORKED, Poller

    directory = root / f"round-{slots}-{number}"
    directory.mkdir(parents=True)
    store = open_store(directory / "state.db")
    index_dir = directory / "index"
    index = open_index(index_dir, build_artifact().entries, dutch=dutch_digest_for(settings().languages))
    writer = IndexBatchWriter(index, directory=index_dir)
    queue = LadderQueue(rows)
    poller = Poller(
        store=store,
        writer=writer,
        tmp_dir=directory / "tmp",
        client_factory=lambda: cast("Any", object()),
        gateway_factory=lambda: cast("Any", _Gateway()),
        queue_factory=lambda nc: cast("Any", queue),
        fetch=local_fetch(rows),
        pool=pool,
        ocr_slots=slots,
        headroom=lambda: None if slots == 1 else LADDER_HEADROOM_BYTES,
    )
    try:
        passes = 0
        started = time.perf_counter()
        while queue.pending and passes <= len(rows):
            result = await poller.run_once()
            passes += 1
            if result.state != ROUND_WORKED:
                break
        wall = time.perf_counter() - started
        verdicts = {row.file_id: store.file_row(row.file_id) for row in rows}
    finally:
        await poller.aclose()
        writer.close()
        store.close()
    good = [
        file_id
        for file_id, verdict in verdicts.items()
        if verdict is not None and verdict.get("state") == "indexed" and verdict.get("reason") is None
    ]
    measured = Round(
        number=number,
        slots=slots,
        pages=sum(pages[file_id] for file_id in good),
        seconds=wall,
        failed=len(rows) - len(good),
    )
    return measured, queue.byte_capped


async def _ladder(rows: Sequence[LadderRow], slots: int, rounds: int, root: Path) -> tuple[list[Round], int]:
    from findling.config import settings
    from findling.extract.pool import SlotPool

    pages = page_counts(rows)
    pool = SlotPool(slots)
    measured: list[Round] = []
    capped = 0
    try:
        await _warm(pool, rows, slots, float(settings().ocr_hard_deadline_seconds))
        for number in range(1, rounds + 1):
            item, byte_capped = await _one_round(number, slots, rows, pages, pool, root)
            measured.append(item)
            capped += byte_capped
    finally:
        await asyncio.to_thread(pool.close)
    return measured, capped


def measure_ladder(rows: Sequence[LadderRow], slots: int, rounds: int) -> tuple[list[Round], int]:
    """The poller mode: the real Poller over the fake queue, round after round."""
    with tempfile.TemporaryDirectory(prefix="slot-ladder-") as scratch:
        root = Path(scratch)
        # The volume of this run, in scratch: the word list artifact and the
        # settings land here and nowhere near a real instance.
        os.environ.setdefault("APP_PERSISTENT_STORAGE", str(root / "volume"))
        (root / "volume").mkdir(exist_ok=True)
        return asyncio.run(_ladder(rows, slots, rounds, root / "rounds"))


def _embed_once(model: Any, rows: Sequence[Sequence[str]], threads: int) -> float:
    """Wall time of all rows through ``threads`` threads; 0.0 when a row got no vectors."""
    pending = deque(rows)
    lock = threading.Lock()
    broken: list[bool] = []

    def work() -> None:
        while True:
            with lock:
                if not pending:
                    return
                row = pending.popleft()
            if not model.embed_passages(list(row)).available:
                broken.append(True)

    started = time.perf_counter()
    workers = [threading.Thread(target=work) for _ in range(threads)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
    wall = time.perf_counter() - started
    return 0.0 if broken else wall


def measure_embed(variants: Sequence[int], rounds: int) -> dict[int, list[float]]:
    """The embed mode: the int8 engine of the image, one row at a time against n at once."""
    from findling.embed.engine import shared_model

    passages = synthetic_passages()
    rows = [passages[start : start + EMBED_ROW] for start in range(0, len(passages), EMBED_ROW)]
    model = shared_model()
    # The load, untimed; a missing model leaves every figure undetermined.
    if not model.embed_passages(rows[0]).available:
        return {variant: [0.0] for variant in variants}
    timings: dict[int, list[float]] = {variant: [] for variant in variants}
    # Alternating inside every round, so a drift of the machine lands on both.
    for _ in range(rounds):
        for variant in variants:
            timings[variant].append(_embed_once(model, rows, variant))
    return timings


def _slot_count(text: str) -> int:
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("has to be a whole number") from error
    if not 1 <= value <= MAX_SLOTS:
        raise argparse.ArgumentTypeError(f"has to lie between 1 and {MAX_SLOTS}")
    return value


def _at_least_one(text: str) -> int:
    try:
        value = int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("has to be a whole number") from error
    if value < 1:
        raise argparse.ArgumentTypeError("has to be at least one")
    return value


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="slot_ladder.py",
        description="OCR pages per second of the real poller over 1, 2 or 4 slots (D-26-09).",
    )
    parser.add_argument("--slots", type=_slot_count, required=True, help=f"OCR slots, 1 to {MAX_SLOTS}")
    parser.add_argument("--rounds", type=_at_least_one, default=DEFAULT_ROUNDS, help="timed rounds, default 3")
    parser.add_argument(
        "--scan-dir",
        type=Path,
        required=True,
        help="the synthetic corpus out of build_load_corpus.py, never user files; the embed mode reads nothing from it",
    )
    parser.add_argument("--mode", choices=("poller", "embed"), default="poller")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = parse_args(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else 2
    if arguments.mode == "embed":
        variants = sorted({1, max(2, arguments.slots)})
        timings = measure_embed(variants, arguments.rounds)
        for line in embed_lines(platform.machine(), visible_cpus(), EMBED_PASSAGES, timings):
            print(line, flush=True)
        return 0 if all(wall > 0 for walls in timings.values() for wall in walls) else 1
    scan_dir: Path = arguments.scan_dir
    if not scan_dir.is_dir():
        print("slot_ladder: the corpus directory does not exist", file=sys.stderr)
        return 2
    rows = corpus_of(scan_dir)
    if not rows:
        print("slot_ladder: the corpus directory holds no PDF", file=sys.stderr)
        return 2
    rounds, capped = measure_ladder(rows, arguments.slots, arguments.rounds)
    for line in report_lines(platform.machine(), visible_cpus(), arguments.slots, len(rows), capped, rounds):
        print(line, flush=True)
    return 1 if not rounds or any(item.failed for item in rounds) else 0


if __name__ == "__main__":
    sys.exit(main())
