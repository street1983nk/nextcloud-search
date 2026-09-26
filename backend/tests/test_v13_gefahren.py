"""The driven fassungen of the v1.3 trip, held to their bytes.

The trip of phase 22 ran on 26.09.2026 (docs/measurements/2026-09-v13-messung,
report section 6.14). Every tool of its run directory ran on the box or on the
development machine against the box, and each of them wrote a raw file that the
report and docs/performance.md read their figures out of. The box was taken
down the same day, so a figure that turns out to be a claim about a changed
script cannot be measured again. From here on a change inside one of these
files is a red test and not a matter of good intentions; a fix is a successor
with a new number in a new run directory, the rule of section 5 of 00-ablauf.md
and of DRIVEN_V12_FASSUNGEN before it.

The digest belongs to the fassung that ran last. Several tools were fixed
between the drives of that day (00-lauf.sh last in 65f8399, 92e-umgebung.sh in
be35cfe, 95c-kaltstart.sh in aecca7d, 92d-wechsel.sh and 90e-einzelliste.py in
26e5e8f); the third re-entry and B4 ran with exactly the bytes pinned here.

The head sentence "DIESE FASSUNG IST NICHT GEFAHREN" stays in every file byte
for byte, after the precedent of 92c: it describes the state at the time of
writing, and removing it would itself be a change of a driven fassung. The
driving date lives in the report and in this module, not in the scripts.

Both figures are written down rather than recomputed from the file under test:
a gate that asks the file for its own expectation agrees with it no matter what
it comes to say. .gitattributes checks every .sh and every measurement .py out
with LF endings, so the bytes are the same on Windows and on a runner.
"""

from __future__ import annotations

import hashlib
import shutil
from typing import TYPE_CHECKING

import pytest

from test_measurement_scripts import DRIVEN_FASSUNG_RULE, NOT_DRIVEN, V13_RUN_DIR

if TYPE_CHECKING:
    from pathlib import Path

RAW_DIR = V13_RUN_DIR.parent / "rohdaten"
REPORT = V13_RUN_DIR.parent / "README.md"

# Driven on 26.09.2026, docs/measurements/2026-09-v13-messung. Name -> (sha256
# over the bytes of the file, byte count). The order is alphabetical, which for
# this directory is the order of the numbers.
DRIVEN_V13_FASSUNGEN: dict[str, tuple[str, int]] = {
    "00-abholen.sh": ("ac8b9f28497a31a1044c25654958985429bb524ca652545bbcd36f885008b57d", 6639),
    "00-lauf.sh": ("c3e99667c7407bb67c5bb1d705f427f33ede798002b6df582550bfd0305ddca1", 62543),
    "00-typwechsel.sh": ("bb5b4a4b2194e191f274f33f37f59e220acc4a8894a184359808eb82e1494d8c", 12284),
    "00-wegwerf.sh": ("38793345c8d2635aeceb56c21c419f133cc23f43601db85bc1f93319206549fd", 21427),
    "90e-einzelliste.py": ("46c5d0d61f48700613c7879eb2640862444894af613dc41cc2ef827d6ca82058", 10965),
    "91m-langsame-aufrufe.py": ("4e196f7e6b40bad4191bb3f51ba4a4cbdf96a5ba14e0a0fa6a08e662f1098615", 7045),
    "92d-wechsel.sh": ("a3a247e3a372cd67d8f7a618b33a41bdec895e692191170cd25648659c60f41a", 44582),
    "92e-umgebung.sh": ("7fd03930b3d025a9c066e058135ef9330b479dd8959cfe7b9e9253d4df98b71c", 18726),
    "94c-bodensatz-zyklen.sh": ("de79c6ecdee9137567f433b64dd014907426c1d3332c0ddeb3dd1c7c673d9ca0", 23167),
    "95c-kaltstart.sh": ("08f86c80222a51efb7f54a80250a55a088cc29b79f5ea04135522a1823413d05", 13247),
    "98d-dismax-probe.py": ("61c0f63b5cbcffc720eeb497ba17bf98121d2b29cf475da1db41b9b5a8d18aec", 16988),
}

# The tools of the run directory whose block was struck (00-gestrichen.txt) and
# which therefore never ran. Empty for this trip: no block was struck, and
# 00-gestrichen.txt does not exist (report section 6.6). A struck tool would
# stand here, keep its head sentence, and stay outside DRIVEN_V13_FASSUNGEN.
NOT_DRIVEN_V13: frozenset[str] = frozenset()

# Where each driven fassung left its trace: a raw file (relative to the run
# directory's parent) and a line the fassung itself wrote when it reached its
# end. A digest without such a line would pin a file nobody can show ran.
DRIVEN_EVIDENCE: dict[str, tuple[str, str]] = {
    "00-abholen.sh": ("rohdaten/00-lauf-protokoll.txt", "abholung-bestaetigt 2026-09-26T13:12:56Z"),
    "00-lauf.sh": ("rohdaten/00-lauf.txt", "b4-ende 2026-09-26T13:34:39Z"),
    "00-typwechsel.sh": ("rohdaten/00-typwechsel.txt", "typwechsel-zurueck-gestoppt"),
    "00-wegwerf.sh": ("rohdaten/00-wegwerf-b4.txt", "wegwerf-b4-ende 2026-09-26T13:34:39Z"),
    "90e-einzelliste.py": ("rohdaten/00-lauf.txt", "90e-liste-rueckgabewert 0 datei 90e-einzelliste.json"),
    "91m-langsame-aufrufe.py": ("rohdaten/m01-langsame-aufrufe-kaltstart-lasttest.txt", "kaputte-zeilen 0"),
    "92d-wechsel.sh": ("rohdaten/00-lauf.txt", "92d-rueckgabewert 0"),
    "92e-umgebung.sh": ("rohdaten/00-lauf.txt", "92e FINDLING_LANGUAGES=de,en,es,it,nl,pt rueckgabewert 0"),
    "94c-bodensatz-zyklen.sh": ("rohdaten/94c-bodensatz-zyklen.txt", "bodensatz-zyklen-ende 2026-09-26T05:50:24Z"),
    "95c-kaltstart.sh": ("rohdaten/95c-kaltstart-lasttest.txt", "kaltstart-fenster 2026-09-26T12:41:58Z"),
    "98d-dismax-probe.py": ("rohdaten/00-lauf.txt", "98d-rueckgabewert 0 fehlerzeilen 0"),
}

DRIVING_DATE = "26.09.2026"


def fassung_matches(raw: bytes, digest: str, size: int) -> bool:
    """The one comparison every watchman of this module makes."""
    return len(raw) == size and hashlib.sha256(raw).hexdigest() == digest


def tools_of_the_run_directory() -> set[str]:
    """Every executable tool of the run directory; 00-ablauf.md is the plan, not a tool."""
    return {path.name for path in V13_RUN_DIR.iterdir() if path.is_file() and path.suffix in {".sh", ".py"}}


@pytest.mark.parametrize("name", sorted(DRIVEN_V13_FASSUNGEN), ids=sorted(DRIVEN_V13_FASSUNGEN))
def test_the_driven_v13_fassung_stays_byte_identical(name: str) -> None:
    """A fassung that ran on the paid box is evidence, and evidence does not get edited."""
    digest, size = DRIVEN_V13_FASSUNGEN[name]
    path = V13_RUN_DIR / name
    assert path.is_file(), path
    # DRIVEN_FASSUNG_RULE is the diagnosis: a fix belongs in a successor with a
    # new number in a new run directory.
    assert fassung_matches(path.read_bytes(), digest, size), DRIVEN_FASSUNG_RULE


@pytest.mark.parametrize("name", sorted(DRIVEN_V13_FASSUNGEN), ids=sorted(DRIVEN_V13_FASSUNGEN))
def test_the_driven_v13_fassung_left_its_line_in_the_raw_data(name: str) -> None:
    """Only a fassung whose own end line stands in the raw data counts as driven."""
    relative, needle = DRIVEN_EVIDENCE[name]
    raw_file = V13_RUN_DIR.parent / relative
    assert raw_file.is_file(), raw_file
    assert needle in raw_file.read_text(encoding="utf-8"), (name, relative)


@pytest.mark.parametrize("name", sorted(DRIVEN_V13_FASSUNGEN), ids=sorted(DRIVEN_V13_FASSUNGEN))
def test_the_driven_v13_fassung_keeps_its_head_sentence(name: str) -> None:
    """The head sentence stays byte for byte, and the report names the driving date."""
    assert NOT_DRIVEN in (V13_RUN_DIR / name).read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    section = report[report.index("### 6.14 Gefahrene Fassungen") :]
    assert DRIVING_DATE in section
    assert f"`{name}`" in section


def test_every_tool_of_the_run_directory_is_either_driven_or_struck() -> None:
    """No tool falls between the two sets, and none is judged twice."""
    tools = tools_of_the_run_directory()
    assert set(DRIVEN_V13_FASSUNGEN) | NOT_DRIVEN_V13 == tools
    assert set(DRIVEN_V13_FASSUNGEN).isdisjoint(NOT_DRIVEN_V13)
    assert set(DRIVEN_EVIDENCE) == set(DRIVEN_V13_FASSUNGEN)


def test_a_struck_v13_fassung_stays_outside_the_pins_and_keeps_saying_so() -> None:
    """The set of struck tools matches the struck-list of the run, and each keeps its head.

    For this trip the set is empty because no block was struck, and the raw data
    say the same: there is no 00-gestrichen.txt. Should a later reading of the
    raw data find one, this test turns red until the struck tool is moved out of
    DRIVEN_V13_FASSUNGEN.
    """
    struck_list = RAW_DIR / "00-gestrichen.txt"
    assert struck_list.exists() == bool(NOT_DRIVEN_V13)
    for name in NOT_DRIVEN_V13:
        assert name not in DRIVEN_V13_FASSUNGEN
        assert NOT_DRIVEN in (V13_RUN_DIR / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", sorted(DRIVEN_V13_FASSUNGEN), ids=sorted(DRIVEN_V13_FASSUNGEN))
def test_the_watchman_fires_on_a_single_changed_byte_in_a_copy(name: str, tmp_path: Path) -> None:
    """A watchman whose only assertion is that today is fine stays green when it dies.

    Staged against a copy of the real file in tmp_path, never against the file
    itself: one byte in the middle flipped, one byte appended, one removed.
    """
    digest, size = DRIVEN_V13_FASSUNGEN[name]
    copy = tmp_path / name
    shutil.copyfile(V13_RUN_DIR / name, copy)
    raw = copy.read_bytes()
    assert fassung_matches(raw, digest, size)

    middle = len(raw) // 2
    flipped = raw[:middle] + bytes([raw[middle] ^ 0x01]) + raw[middle + 1 :]
    with copy.open("wb") as handle:
        handle.write(flipped)
    assert not fassung_matches(copy.read_bytes(), digest, size)
    assert not fassung_matches(raw + b"\n", digest, size)
    assert not fassung_matches(raw[:-1], digest, size)
