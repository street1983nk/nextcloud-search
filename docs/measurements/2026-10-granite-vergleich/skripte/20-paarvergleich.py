#!/usr/bin/env python3
"""Step 20 of the granite comparison: the paired comparison of e5 against granite.

A local evaluation of the raw files of step 3, no model run. For every language
it reads the ranks per case of two runs (the "per case" line written by
scripts/dev/model_quality.py --per-case) and reports what rule (a) and rule (b)
of section 1 of the README ask for:

- the cases whose rank moves between the two runs, how many moved to the front
  (better rank for the second run) and how many to the back; cases with the
  same rank do not count (rule a);
- the exact one sided sign test over the moved cases, binomial with p = 0.5,
  P(X >= improved | n = moved): the chance to see at least this many moves to
  the front if both models were equal;
- the paired t value of the reciprocal ranks over all cases (rule a, reported
  beside the sign test, not part of the decision);
- MRR of both runs and the relative MRR change of the second against the first
  (rule b, the limit is minus 5 percent).

Run from the root of the repository, one pair per language and fassung:

    python docs/measurements/2026-10-granite-vergleich/skripte/20-paarvergleich.py \\
      --pair de:int8 rohdaten/03-qualitaet-e5-int8-de.txt rohdaten/03-qualitaet-granite-int8-de.txt \\
      --out rohdaten/20-paarvergleich.txt

Paths are relative to the run directory docs/measurements/2026-10-granite-vergleich
unless they are absolute. Standard library only.
"""

from __future__ import annotations

import argparse
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path

RUN_DIR = Path(__file__).resolve().parent.parent
ALPHA = 0.05
MRR_LIMIT = -0.05


@dataclass(frozen=True)
class Pair:
    label: str
    first: Path
    second: Path


def ranks_of(path: Path) -> dict[str, int]:
    """The rank per case of one raw file of step 3."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("per case"):
            body = line.removeprefix("per case").strip()
            found: dict[str, int] = {}
            for item in body.split(","):
                match = re.fullmatch(r"\s*(\S+) (\d+)\s*", item)
                if match is None:
                    message = f"unreadable case {item!r} in {path.name}"
                    raise ValueError(message)
                found[match.group(1)] = int(match.group(2))
            return found
    message = f"no per case line in {path.name}"
    raise ValueError(message)


def sign_test_upper(improved: int, moved: int) -> float:
    """Exact one sided sign test, P(X >= improved) for X ~ Bin(moved, 0.5)."""
    if moved == 0:
        return 1.0
    tail = sum(math.comb(moved, k) for k in range(improved, moved + 1))
    return tail / 2**moved


def paired_t(first: list[float], second: list[float]) -> float:
    """Paired t value of second minus first."""
    differences = [b - a for a, b in zip(first, second, strict=True)]
    spread = statistics.stdev(differences)
    if spread == 0:
        return 0.0
    return statistics.fmean(differences) / (spread / math.sqrt(len(differences)))


def resolve(name: str) -> Path:
    path = Path(name)
    return path if path.is_absolute() else RUN_DIR / path


def evaluate(pair: Pair) -> list[str]:
    first = ranks_of(pair.first)
    second = ranks_of(pair.second)
    if first.keys() != second.keys():
        message = f"{pair.label}: the two files do not carry the same cases"
        raise ValueError(message)
    cases = sorted(first, key=lambda case: int(case.rsplit("-", 1)[1]))
    improved = [case for case in cases if second[case] < first[case]]
    worsened = [case for case in cases if second[case] > first[case]]
    moved = len(improved) + len(worsened)
    p_value = sign_test_upper(len(improved), moved)
    rr_first = [1 / first[case] for case in cases]
    rr_second = [1 / second[case] for case in cases]
    mrr_first = statistics.fmean(rr_first)
    mrr_second = statistics.fmean(rr_second)
    change = (mrr_second - mrr_first) / mrr_first
    return [
        f"== {pair.label}: {pair.first.name} gegen {pair.second.name}",
        f"faelle {len(cases)}",
        f"gleicher rang {len(cases) - moved}",
        f"bewegt {moved}",
        f"verbessert {len(improved)}",
        f"verschlechtert {len(worsened)}",
        f"vorzeichentest einseitig p = {p_value:.3g} (P(X >= {len(improved)}), X ~ Bin({moved}, 0.5))",
        f"vorzeichentest unter {ALPHA}: {'ja' if p_value < ALPHA else 'nein'}",
        f"gepaarter t-wert der reziprokraenge {paired_t(rr_first, rr_second):.3f} (df {len(cases) - 1})",
        f"mrr erste {mrr_first:.4f}",
        f"mrr zweite {mrr_second:.4f}",
        f"mrr relative aenderung {change * 100:+.2f} prozent",
        f"mrr-rueckgang ueber 5 prozent: {'ja' if change < MRR_LIMIT else 'nein'}",
        f"verbessert: {' '.join(improved)}",
        f"verschlechtert: {' '.join(worsened)}",
        "",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="paired comparison e5 against granite, sign test and MRR change")
    parser.add_argument(
        "--pair",
        nargs=3,
        action="append",
        metavar=("LABEL", "FIRST", "SECOND"),
        required=True,
        help="label, raw file of the first model, raw file of the second model",
    )
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    lines = [
        "schritt 20 paarvergleich, lokale auswertung der rohdaten aus schritt 3, kein modelllauf",
        "erste = e5, zweite = granite; verbessert heisst: granite hat den kleineren rang",
        "regel (a): vorzeichentest ueber die bewegten faelle, einseitig, niveau 0,05",
        "regel (b): relativer mrr-rueckgang hoechstens 5 prozent",
        "",
    ]
    for label, first, second in args.pair:
        lines.extend(evaluate(Pair(label, resolve(first), resolve(second))))
    lines.append("schritt 20 fertig")
    out = resolve(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
