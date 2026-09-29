#!/usr/bin/env python3
"""The cost sheet of the acceptance trip: the cap out of the items, and the running cost.

**DIESE FASSUNG IST NICHT GEFAHREN.** No raw file lies next to it; the cap it
prints is the proposal the owner releases before the first box starts (SC1).

D-28-01: the cap is the sum of the items of the sheet (runbook section 2, the
actual values of the last trips as floor per item) for exactly the scope of
D-28-06, plus 30 percent reserve. The items are the table "Summe und Deckel
(Variante A)" of 28-RESEARCH.md, as data in this file, one row per item and
box. The anchor cell of D-28-11 (Sparsam on the subset on m7g.large, 4 h 35)
stands as its own row, so that the sheet shows the research figure and the
figure with the anchor side by side.

    Deckel (USD) = sum over boxes (hours of the box x rate of the box)
                   + parked disks, all of it x 1.30
    Deckel (h)   = box hours x 1.30, display only

USD binds and hours do not, because the rates lie up to a factor of 16 apart.

The rates are those read on 29.09.2026 from the public on demand price map of
Frankfurt (box total per hour including 100 GB gp3 and the IPv4 address). They
are read a second time on the day of the trip (runbook 2.3); a changed rate is
handed in with --satz TYP=USD or as a whole rate file with --satzdatei (one
line "TYP USD" per type, every type the items need, nothing else). A rate that
is missing ends the sheet: a missing rate counted as zero would be a cap that
is too low, which is the one mistake this sheet exists to prevent (T-28-01).

Subcommands:

    deckel [--satz TYP=USD ...] [--satzdatei DATEI]
        the table per box, the sum and the cap, with and without the anchor
    stand STEMPELDATEI --deckel USD [--jetzt ISO] [--satz ...] [--satzdatei ...]
        the running cost out of cost stamps, the rest up to the cap and the
        minutes to the cap and to the cap x 1.20 at the rate in force now

A cost stamp is one line "TYP START ENDE", times in UTC as
2026-10-01T08:00:00Z, ENDE either a time or "laeuft" for the box that runs
now; the parked disks are stamped with the type "geparkt". The minutes to
the cap x 1.20 are the input of the safety timer of 28-02 (D-28-14): at that
point the timer STOPS the instance, it never terminates it.

No identifier of any AWS resource, no AWS call: the stamps are written by the
operator on the development machine and hold types and times only.

Exit codes:

  0 done, and for stand: the cap is not reached
  2 usage: unknown subcommand or option, a rate of the wrong shape or type
  3 a rate the items or the stamps need is missing
  4 a cost stamp of the wrong shape, an unknown type or an end before its start
  5 stand: the cap is reached, no new cell starts (D-28-02)
  6 stand: the cap x 1.20 is reached, the safety timer stops the box (D-28-14)
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

EXIT_USAGE = 2
EXIT_MISSING_RATE = 3
EXIT_BAD_STAMP = 4
EXIT_CAP_REACHED = 5
EXIT_SAFETY_STOP = 6

RESERVE = Decimal("1.30")
SAFETY = Decimal("1.20")
CENT = Decimal("0.01")
PARKED = "geparkt"
STILL_RUNNING = "laeuft"
STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Box total in USD per hour, read on 29.09.2026 (28-RESEARCH.md, "Gelesene
# Saetze"): instance plus 100 GB gp3 0.013041 plus IPv4 0.005. "geparkt" is a
# stopped box, the disk alone.
RATES_OF_29_09: dict[str, Decimal] = {
    "m7g.large": Decimal("0.115841"),
    "m7g.4xlarge": Decimal("0.800141"),
    "c7a.xlarge": Decimal("0.252301"),
    "c7a.2xlarge": Decimal("0.486561"),
    "c7a.4xlarge": Decimal("0.955081"),
    "c7a.8xlarge": Decimal("1.892121"),
    PARKED: Decimal("0.013041"),
}

# The items of variant A, (type, item, minutes), in the order of the trip.
ITEMS: tuple[tuple[str, str, int], ...] = (
    ("m7g.large", "Aufbau Bloecke 1 bis 13", 60),
    ("m7g.large", "Volume-Initialisierung", 45),
    ("m7g.large", "Abbildwechsel auf den Phase-27-Stand", 45),
    ("m7g.large", "Cron-Gate", 15),
    ("m7g.large", "S-voll 52k mit Zellen-Overhead", 1335),
    ("m7g.large", "Teilkorpus einrichten", 20),
    ("m7g.large", "St-T", 245),
    ("m7g.large", "L-T", 245),
    ("m7g.4xlarge", "Typwechsel", 30),
    ("m7g.4xlarge", "S-T", 275),
    ("m7g.4xlarge", "St-T", 105),
    ("m7g.4xlarge", "L-T", 90),
    ("c7a.xlarge", "x86-Aufbau mit Machbarkeitstor", 120),
    ("c7a.xlarge", "Volume-Initialisierung", 45),
    ("c7a.xlarge", "Abbildwechsel", 45),
    ("c7a.xlarge", "Teilkorpus einrichten", 20),
    ("c7a.xlarge", "Cron-Gate", 15),
    ("c7a.xlarge", "S-T", 275),
    ("c7a.xlarge", "St-T", 245),
    ("c7a.xlarge", "L-T", 120),
    ("c7a.xlarge", "St-fp32-T", 255),
    ("c7a.2xlarge", "Typwechsel", 15),
    ("c7a.2xlarge", "S-T", 275),
    ("c7a.2xlarge", "St-T", 120),
    ("c7a.2xlarge", "L-T", 90),
    ("c7a.4xlarge", "Typwechsel", 15),
    ("c7a.4xlarge", "S-T", 275),
    ("c7a.4xlarge", "St-T", 105),
    ("c7a.4xlarge", "L-T", 90),
    ("c7a.4xlarge", "St-fp32-T", 135),
    ("c7a.8xlarge", "Typwechsel", 15),
    ("c7a.8xlarge", "S-T", 275),
    ("c7a.8xlarge", "St-T", 105),
    ("c7a.8xlarge", "L-T", 90),
    # The ARM disk stays parked while the x86 half runs (45 h 45), and the take
    # down takes one hour with both disks parked. Not box hours.
    (PARKED, "ARM-Platte geparkt waehrend der x86-Haelfte", 2745),
    (PARKED, "Abbau, zwei Platten je eine Stunde", 120),
)

# D-28-11, its own row so that the research figure stays readable next to it.
ANCHOR: tuple[str, str, int] = ("m7g.large", "Anker S-T", 275)


def money(value: Decimal) -> str:
    return str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def hours(minutes: int | Decimal) -> str:
    return str((Decimal(minutes) / 60).quantize(CENT, rounding=ROUND_HALF_UP))


def cost(box: str, minutes: int, rates: dict[str, Decimal]) -> Decimal:
    return Decimal(minutes) / 60 * rates[box]


def parse_rate(text: str) -> Decimal | None:
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    return value if value.is_finite() and value > 0 else None


def read_rates(arguments: argparse.Namespace) -> tuple[dict[str, Decimal], int]:
    """The rates in force: the file replaces all of them, --satz replaces one."""
    rates = dict(RATES_OF_29_09)
    if arguments.satzdatei is not None:
        rates = {}
        for line in Path(arguments.satzdatei).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            fields = stripped.split()
            value = parse_rate(fields[1]) if len(fields) == 2 else None
            if value is None or fields[0] not in RATES_OF_29_09:
                print(f"02-rechenblatt: a rate line of the wrong shape: '{stripped}'", file=sys.stderr)
                return {}, EXIT_USAGE
            rates[fields[0]] = value
    for override in arguments.satz:
        box, separator, text = override.partition("=")
        value = parse_rate(text) if separator else None
        if value is None or box not in RATES_OF_29_09:
            print(f"02-rechenblatt: --satz wants TYP=USD with a known type, got '{override}'", file=sys.stderr)
            return {}, EXIT_USAGE
        rates[box] = value
    return rates, 0


def missing_rates(needed: set[str], rates: dict[str, Decimal]) -> int:
    missing = sorted(needed - rates.keys())
    if missing:
        print(f"02-rechenblatt: no rate for {' '.join(missing)}, nothing is counted as zero", file=sys.stderr)
        return EXIT_MISSING_RATE
    return 0


def command_deckel(arguments: argparse.Namespace) -> int:
    rates, code = read_rates(arguments)
    if code:
        return code
    code = missing_rates({box for box, _, _ in ITEMS} | {ANCHOR[0]}, rates)
    if code:
        return code

    boxes: dict[str, list[tuple[str, int]]] = {}
    for box, item, minutes in ITEMS:
        boxes.setdefault(box, []).append((item, minutes))

    total = Decimal(0)
    box_minutes = 0
    for box, items in boxes.items():
        minutes = sum(item_minutes for _, item_minutes in items)
        amount = cost(box, minutes, rates)
        total += amount
        if box != PARKED:
            box_minutes += minutes
        for item, item_minutes in items:
            print(f"posten {box} {item_minutes} min {item}")
        print(f"box {box} {hours(minutes)} h {money(amount)} USD satz {rates[box]}")

    anchor_box, _, anchor_minutes = ANCHOR
    anchor = cost(anchor_box, anchor_minutes, rates)
    print(f"anker {anchor_box} {hours(anchor_minutes)} h {money(anchor)} USD")

    print(f"summe {hours(box_minutes)} h {money(total)} USD")
    print(f"deckel {hours(box_minutes * RESERVE)} h {money(total * RESERVE)} USD")
    with_anchor = total + anchor
    anchored_minutes = box_minutes + anchor_minutes
    print(f"mit anker summe {hours(anchored_minutes)} h {money(with_anchor)} USD")
    print(f"mit anker deckel {hours(anchored_minutes * RESERVE)} h {money(with_anchor * RESERVE)} USD")
    print("bindend ist USD, die Stunden sind nur Anzeige")
    return 0


def parse_time(text: str) -> datetime | None:
    try:
        return datetime.strptime(text, STAMP_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return None


def read_stamps(path: Path) -> tuple[list[tuple[str, datetime, datetime | None]], int]:
    stamps: list[tuple[str, datetime, datetime | None]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        stamp = parse_stamp(stripped.split())
        if stamp is None:
            print(f"02-rechenblatt: a cost stamp of the wrong shape: '{stripped}'", file=sys.stderr)
            return [], EXIT_BAD_STAMP
        stamps.append(stamp)
    return stamps, 0


def parse_stamp(fields: list[str]) -> tuple[str, datetime, datetime | None] | None:
    """(type, start, end or None while it runs), or None for a stamp of the wrong shape."""
    if len(fields) != 3 or fields[0] not in RATES_OF_29_09:
        return None
    start = parse_time(fields[1])
    if start is None:
        return None
    if fields[2] == STILL_RUNNING:
        return fields[0], start, None
    end = parse_time(fields[2])
    if end is None or end < start:
        return None
    return fields[0], start, end


def minutes_left(rest: Decimal, rate: Decimal) -> str:
    if rest <= 0:
        return "0"
    if rate <= 0:
        return "unbegrenzt"
    return str(math.floor(rest / rate * 60))


def command_stand(arguments: argparse.Namespace) -> int:
    rates, code = read_rates(arguments)
    if code:
        return code
    cap = parse_rate(arguments.deckel)
    now = datetime.now(UTC) if arguments.jetzt is None else parse_time(arguments.jetzt)
    if cap is None or now is None:
        print("02-rechenblatt: --deckel wants USD above zero, --jetzt a time as 2026-10-01T08:00:00Z", file=sys.stderr)
        return EXIT_USAGE
    stamps, code = read_stamps(Path(arguments.stempeldatei))
    if code:
        return code
    code = missing_rates({box for box, _, _ in stamps}, rates)
    if code:
        return code

    spent = Decimal(0)
    rate_now = Decimal(0)
    for box, start, end in stamps:
        until = now if end is None else end
        seconds = max(0, int((until - start).total_seconds()))
        spent += Decimal(seconds) / 3600 * rates[box]
        if end is None:
            rate_now += rates[box]

    safety = cap * SAFETY
    print(f"bisher {money(spent)} USD")
    print(f"deckel {money(cap)} USD sicherheitsstopp {money(safety)} USD")
    print(f"rest {money(cap - spent)} USD")
    print(f"satz jetzt {rate_now.normalize() if rate_now else 0} USD/h")
    print(f"minuten bis deckel {minutes_left(cap - spent, rate_now)}")
    print(f"minuten bis sicherheitsstopp {minutes_left(safety - spent, rate_now)}")
    if spent >= safety:
        print("sicherheitsstopp erreicht")
        return EXIT_SAFETY_STOP
    if spent >= cap:
        print("deckel erreicht")
        return EXIT_CAP_REACHED
    return 0


def parse_arguments(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="The cost sheet of the acceptance trip of phase 28.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("deckel", "stand"):
        command = commands.add_parser(name)
        command.add_argument("--satz", action="append", default=[], metavar="TYP=USD")
        command.add_argument("--satzdatei", metavar="DATEI")
        if name == "stand":
            command.add_argument("stempeldatei")
            command.add_argument("--deckel", required=True, metavar="USD")
            command.add_argument("--jetzt", metavar="ISO")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    arguments = parse_arguments(argv)
    if arguments.command == "deckel":
        return command_deckel(arguments)
    return command_stand(arguments)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
