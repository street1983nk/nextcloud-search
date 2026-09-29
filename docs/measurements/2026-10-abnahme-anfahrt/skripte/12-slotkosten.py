#!/usr/bin/env python3
"""The cost of one OCR slot out of a proc_anon series, and the calculation per cell.

**DIESE FASSUNG IST NICHT GEFAHREN.** No raw file lies next to it; the series
it reads are written on the trip by scripts/ops/proc_anon_sampler.sh.

D-28-08: the measured slot costs replace the estimate in formula and probe
(OCR_SLOT_COST_BYTES, 235 MiB), and a cell whose anon peak lies at most 10
percent above its calculation counts as carried by the calculation. This tool
supplies both halves of that comparison.

Subcommands:

    slots SERIE (--slots N | --meta ZELLDATEI)
        (a) the highest VmHWM of a sandbox child plus the highest VmHWM of a
            tesseract: the pair of B2 (child 136.4 plus tesseract 98.8, 235
            MiB, there as RssAnon) read as VmHWM, an upper bound that also
            catches peaks between two samples; the RssAnon pair of the same
            shape stands next to it
        (b) per point in time the anon sum over the sandbox children and the
            tesseract processes, divided by slotsInForce; its maximum
        (c) the main process on its own, the long lived pid, its maximum
    fp32 SERIE_INT8 SERIE_FP32
        (d) the extra of the main process with fp32 over int8 on the same box
    rechnung [--profil P --slots N --praezision int8|fp32 [--gemessen-bytes B]]
        without a cell: the calculation of every measured cell of 00-ablauf.md;
        with one: its calculation, the limit of 1.10 and, with a measured
        value, the verdict "getragen" or "nicht getragen"

The cell metadata file carries "slotsInForce N" (and may carry profil,
praezision, embed_slots), one "key value" or "key=value" per line, as read off
the admin overview of the cell. The main process is the pid seen in the most
samples; sh, init.sh and the other helpers of the sampler itself do not count.

The calculation (Rechnung_anon of 28-RESEARCH.md, pattern 4) counts the items
of the product and not a list of its own: it imports findling.config and
findling.probe and forms the load costs with probe.pending_load_bytes. That
import works on the development machine inside the backend environment (uv
run), never on the box; slots and fp32 need the standard library only.

Clarified before writing it, from the comments of config.py (lines 880 to 945)
and probe_run._measured, so that no item counts twice:

  * MAIN_PROCESS_BASELINE_BYTES (1257.5 MiB) is the RssAnon maximum of the main
    process in B2 (docs/performance.md, v1.3): OCR under product load on
    m7g.large, unload switch 0, the text of the scans chunked and embedded
    inline. So the baseline already HOLDS the int8 weights
    (EMBED_WEIGHTS_LOAD_BYTES, 392 MiB), the built cutter (CUTTER_LOAD_BYTES,
    545 MiB), the writer heap of Sparsam (50 MB) and the activations of the one
    inline embedding (EMBED_ACTIVATION_BYTES).
  * pending_load_bytes is therefore asked with cutter_built True and
    engine_loaded True, so neither the cutter nor the weights count again.
    Its result always carries EMBED_ACTIVATION_BYTES (already in the baseline)
    and EMBED_LANE_RESERVE_BYTES (room the lane keeps free, no anon a sampler
    can see); both are taken off again. What stays is what the profile adds on
    top of B2: embed_slots x EMBED_ACTIVATION_BYTES of the parallel lanes and
    the growth of the writer heap over Sparsam.
  * The children are slots x OCR_SLOT_COST_BYTES (sandbox child plus
    tesseract, B2). With fp32, FP32_EXTRA_BYTES (367 MiB) comes on top; the
    weights are loaded while a cell indexes, so pending_load_bytes would not
    count it (fp32 only counts there while the engine is unloaded).

    Rechnung_anon = MAIN_PROCESS_BASELINE_BYTES
                  + slotsInForce x OCR_SLOT_COST_BYTES
                  + embed_slots x EMBED_ACTIVATION_BYTES
                  + writer heap of the profile minus that of Sparsam
                  + FP32_EXTRA_BYTES (fp32 only)
    getragen, when measured <= 1.10 x Rechnung_anon (whole bytes, floor)

Exit codes:

  0 done
  2 usage: unknown subcommand, a slot count that is no count above zero, an
    unknown profile or precision, or a metadata file without slotsInForce
  3 a series without a single row of a process
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

EXIT_USAGE = 2
EXIT_NO_SERIES = 3

PREFIX = "findling-anon "
TESSERACT = "tesseract"
# The processes of the container that are neither the main process nor a slot:
# the entry script and the shells the sampler starts for its own reading.
HELPERS = frozenset({"init.sh", "sh", "bash", "dash", "grep", "sleep", "cat"})

KIB = 1024
MIB = 1024 * KIB
B2_SLOT_MIB = 235.0

PROFILES = ("economy", "standard", "performance")
PRECISIONS = ("int8", "fp32")

# The measured cells of the trip in the order of 00-ablauf.md: box, cell,
# profile, precision, the slots the formula grants (findling.profile.ocr_slots
# with MemAvailable = MemTotal minus 1 GiB, 28-RESEARCH.md), the verdict the
# probe is expected to give, and the run plan value of the research.
CELLS: tuple[tuple[str, str, str, str, int, str, str], ...] = (
    ("m7g.large", "S-voll", "economy", "int8", 1, "keine", "21:15"),
    ("m7g.large", "Anker-S-T", "economy", "int8", 1, "keine", "3:50"),
    ("m7g.large", "St-T", "standard", "int8", 1, "nofit-oder-narrow", "3:20"),
    ("m7g.large", "L-T", "performance", "int8", 1, "nofit-oder-narrow", "3:20"),
    ("m7g.4xlarge", "S-T", "economy", "int8", 1, "keine", "3:50"),
    ("m7g.4xlarge", "St-T", "standard", "int8", 4, "fits", "1:00"),
    ("m7g.4xlarge", "L-T", "performance", "int8", 15, "fits", "0:45"),
    ("c7a.xlarge", "S-T", "economy", "int8", 1, "keine", "3:50"),
    ("c7a.xlarge", "St-T", "standard", "int8", 1, "fits", "3:20"),
    ("c7a.xlarge", "L-T", "performance", "int8", 3, "fits", "1:15"),
    ("c7a.xlarge", "St-fp32-T", "standard", "fp32", 1, "fits", "3:30"),
    ("c7a.2xlarge", "S-T", "economy", "int8", 1, "keine", "3:50"),
    ("c7a.2xlarge", "St-T", "standard", "int8", 3, "fits", "1:15"),
    ("c7a.2xlarge", "L-T", "performance", "int8", 7, "fits", "0:45"),
    ("c7a.4xlarge", "S-T", "economy", "int8", 1, "keine", "3:50"),
    ("c7a.4xlarge", "St-T", "standard", "int8", 4, "fits", "1:00"),
    ("c7a.4xlarge", "L-T", "performance", "int8", 15, "fits", "0:45"),
    ("c7a.4xlarge", "St-fp32-T", "standard", "fp32", 4, "fits", "1:30"),
    ("c7a.8xlarge", "S-T", "economy", "int8", 1, "keine", "3:50"),
    ("c7a.8xlarge", "St-T", "standard", "int8", 4, "fits", "1:00"),
    ("c7a.8xlarge", "L-T", "performance", "int8", 16, "fits", "0:45"),
)


@dataclass(frozen=True)
class Row:
    epoch: int
    pid: int
    name: str
    anon_kb: int
    hwm_kb: int


def read_series(path: Path) -> list[Row]:
    """The rows of a proc_anon series; header, summary and foreign lines are skipped."""
    rows: list[Row] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        rest = line.removeprefix(PREFIX)
        fields = rest.split(",")
        if len(fields) != 5:
            continue
        try:
            rows.append(Row(int(fields[0]), int(fields[1]), fields[2], int(fields[3]), int(fields[4])))
        except ValueError:
            continue
    return rows


def main_pid(rows: Iterable[Row]) -> int | None:
    """The long lived process: seen in the most samples, the lowest pid on a tie."""
    seen: dict[int, int] = {}
    for row in rows:
        if row.name in HELPERS or row.name == TESSERACT:
            continue
        seen[row.pid] = seen.get(row.pid, 0) + 1
    if not seen:
        return None
    return min(seen, key=lambda pid: (-seen[pid], pid))


@dataclass(frozen=True)
class SlotFigures:
    pair_hwm_kb: int
    pair_anon_kb: int
    per_slot_kb: int
    main_kb: int


def slot_figures(rows: list[Row], slots: int) -> SlotFigures:
    main = main_pid(rows)
    children = [row for row in rows if row.pid != main and row.name not in HELPERS and row.name != TESSERACT]
    tesseracts = [row for row in rows if row.name == TESSERACT]
    pair_hwm = max((row.hwm_kb for row in children), default=0) + max((row.hwm_kb for row in tesseracts), default=0)
    pair_anon = max((row.anon_kb for row in children), default=0) + max((row.anon_kb for row in tesseracts), default=0)
    per_moment: dict[int, int] = {}
    for row in (*children, *tesseracts):
        per_moment[row.epoch] = per_moment.get(row.epoch, 0) + row.anon_kb
    per_slot = max(per_moment.values(), default=0) // slots
    main_max = max((row.anon_kb for row in rows if row.pid == main), default=0)
    return SlotFigures(pair_hwm, pair_anon, per_slot, main_max)


def mib(kilobytes: int) -> str:
    return f"{kilobytes / KIB:.1f}"


def read_meta(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, _, value = stripped.replace("=", " ", 1).partition(" ")
        meta[key.strip()] = value.strip()
    return meta


def slot_count(text: str | None) -> int | None:
    if text is None or not text.isdigit() or int(text) < 1:
        return None
    return int(text)


def command_slots(arguments: argparse.Namespace) -> int:
    text = arguments.slots
    if arguments.meta is not None:
        text = read_meta(Path(arguments.meta)).get("slotsInForce")
    slots = slot_count(text)
    if slots is None:
        print("12-slotkosten: slotsInForce has to be a whole number above zero", file=sys.stderr)
        return EXIT_USAGE
    rows = read_series(Path(arguments.serie))
    if not rows:
        print("12-slotkosten: the series carries no row of a process", file=sys.stderr)
        return EXIT_NO_SERIES
    figures = slot_figures(rows, slots)
    print(f"slot-paar-vmhwm-kb {figures.pair_hwm_kb}")
    print(f"slot-paar-vmhwm-mib {mib(figures.pair_hwm_kb)}")
    print(f"slot-paar-rssanon-kb {figures.pair_anon_kb}")
    print(f"slot-paar-rssanon-mib {mib(figures.pair_anon_kb)}")
    print(f"slot-anon-je-slot-kb {figures.per_slot_kb} slots {slots}")
    print(f"slot-anon-je-slot-mib {mib(figures.per_slot_kb)}")
    print(f"hauptprozess-max-kb {figures.main_kb}")
    print(f"hauptprozess-max-mib {mib(figures.main_kb)}")
    print(f"vergleich-b2-mib {B2_SLOT_MIB:.1f}")
    return 0


def command_fp32(arguments: argparse.Namespace) -> int:
    from findling.config import FP32_EXTRA_BYTES  # development machine only, never on the box

    mains: list[int] = []
    for name in (arguments.serie_int8, arguments.serie_fp32):
        rows = read_series(Path(name))
        if not rows:
            print("12-slotkosten: a series carries no row of a process", file=sys.stderr)
            return EXIT_NO_SERIES
        mains.append(slot_figures(rows, 1).main_kb)
    extra = mains[1] - mains[0]
    expected = FP32_EXTRA_BYTES // KIB
    print(f"hauptprozess-int8-kb {mains[0]}")
    print(f"hauptprozess-fp32-kb {mains[1]}")
    print(f"fp32-mehrbedarf-kb {extra}")
    print(f"fp32-mehrbedarf-mib {mib(extra)}")
    print(f"fp32-rechnung-kb {expected}")
    print(f"urteil {verdict(extra, expected)}")
    return 0


def calculation(profile: str, slots: int, precision: str) -> int:
    """Rechnung_anon of one cell in bytes, with the items of the product (see the head)."""
    from findling import config, probe  # development machine only, never on the box

    heap = {
        "economy": config.WRITER_HEAP_BYTES,
        "standard": config.PROFILE_STANDARD_WRITER_HEAP_BYTES,
        "performance": config.PROFILE_PERFORMANCE_WRITER_HEAP_BYTES,
    }
    embed_slots = {
        "economy": 0,
        "standard": config.PROFILE_STANDARD_EMBED_SLOTS,
        "performance": config.PROFILE_PERFORMANCE_EMBED_SLOTS,
    }
    loads = probe.pending_load_bytes(
        cutter_built=True,
        engine_loaded=True,
        fp32=False,
        embed_slots=embed_slots[profile],
        writer_heap_delta=heap[profile] - heap["economy"],
    )
    # The activation of the inline lane is in the baseline, the lane reserve is free room.
    loads -= config.EMBED_ACTIVATION_BYTES + config.EMBED_LANE_RESERVE_BYTES
    fp32 = config.FP32_EXTRA_BYTES if precision == "fp32" else 0
    return config.MAIN_PROCESS_BASELINE_BYTES + slots * config.OCR_SLOT_COST_BYTES + loads + fp32


def limit_of(calculation_bytes: int) -> int:
    """1.10 x the calculation in whole bytes, rounded down."""
    return calculation_bytes * 11 // 10


def verdict(measured: int, calculation_bytes: int) -> str:
    """D-28-08: carried when the measurement lies at most 10 percent above the calculation."""
    return "getragen" if measured * 10 <= calculation_bytes * 11 else "nicht getragen"


def command_rechnung(arguments: argparse.Namespace) -> int:
    if arguments.profil is None and arguments.slots is None and arguments.praezision is None:
        for box, cell, profile, precision, slots, probe_expected, plan in CELLS:
            value = calculation(profile, slots, precision)
            print(
                f"zelle {box} {cell} {profile} {precision} slots {slots} "
                f"rechnung-mib {value / MIB:.1f} grenze-mib {limit_of(value) / MIB:.1f} "
                f"probe {probe_expected} plan {plan}"
            )
        return 0
    slots = slot_count(arguments.slots)
    if arguments.profil not in PROFILES or arguments.praezision not in PRECISIONS or slots is None:
        print("12-slotkosten: rechnung wants --profil, --slots and --praezision together", file=sys.stderr)
        return EXIT_USAGE
    value = calculation(arguments.profil, slots, arguments.praezision)
    print(f"rechnung-bytes {value}")
    print(f"rechnung-mib {value / MIB:.1f}")
    print(f"grenze-bytes {limit_of(value)}")
    if arguments.gemessen_bytes is not None:
        measured = slot_count(arguments.gemessen_bytes)
        if measured is None:
            print("12-slotkosten: --gemessen-bytes wants a whole number of bytes", file=sys.stderr)
            return EXIT_USAGE
        print(f"gemessen-bytes {measured}")
        print(f"urteil {verdict(measured, value)}")
    return 0


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Slot costs and calculation per cell, phase 28.")
    commands = parser.add_subparsers(dest="command", required=True)
    slots = commands.add_parser("slots")
    slots.add_argument("serie")
    source = slots.add_mutually_exclusive_group(required=True)
    source.add_argument("--slots")
    source.add_argument("--meta")
    fp32 = commands.add_parser("fp32")
    fp32.add_argument("serie_int8")
    fp32.add_argument("serie_fp32")
    rechnung = commands.add_parser("rechnung")
    rechnung.add_argument("--profil")
    rechnung.add_argument("--slots")
    rechnung.add_argument("--praezision")
    rechnung.add_argument("--gemessen-bytes", dest="gemessen_bytes")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    arguments = parse_arguments(argv)
    if arguments.command == "slots":
        return command_slots(arguments)
    if arguments.command == "fp32":
        return command_fp32(arguments)
    return command_rechnung(arguments)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
