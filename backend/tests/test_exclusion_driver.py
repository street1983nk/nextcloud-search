"""The prefixes of 1.4.2 against the service of today, and the matcher on a stopwatch.

Plan 33-02 put a second list next to the prefixes of 1.4.2 and promised that the
first one does not move: every stored prefix is read, normalised and compared
exactly as before (success criterion 1 of phase 33, T-33-07). A promise like
that is cheap to write and expensive to get wrong, because a prefix that moves
its meaning in an upgrade fails quietly on an instance nobody looks at. So it is
compared rather than asserted: the ExclusionService of v1.4.2, checked in byte
for byte under ``fixtures/exclusion_v1_4_2/``, and the service of today run side
by side by one driver on ``php:8.3-cli`` over a corpus of awkward prefixes and
paths, and every answer has to agree.

The fixture lives outside ``php/`` on purpose: the tree hash of the PHP half
reads ``php/**/*.php`` and nothing else, and the CI checkout carries no tags
(python.yml does not fetch them), so a comparison that asked ``git show`` at run
time would be skipped exactly where it matters. The provenance test holds the
fixture against the tag wherever the tag exists, and against the blob id
everywhere.

A comparison that never sees a difference proves nothing about its own eyes,
so a positive control sets one pattern in the new service and has to find the
one answer it changes.

The timing series is the measured half of T-33-03: the matcher is linear in
the path length whatever the patterns look like. It runs only with
``FINDLING_TIMING=1``, because a shared CI runner is not a stopwatch.

Without Docker every case here is skipped with that reason; the provenance
test needs none.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Paths as the container sees them, relative to the mounted repository root.
DRIVER = "backend/tests/drivers/exclusion_driver.php"
OLD_SOURCE = "backend/tests/fixtures/exclusion_v1_4_2/ExclusionService.php"
NEW_SOURCE = "php/lib/Service/ExclusionService.php"

FIXTURE = REPO_ROOT / OLD_SOURCE
PROVENANCE = FIXTURE.parent / "PROVENANCE.md"

# Where the fixture comes from, the same three values PROVENANCE.md names.
TAG = "v1.4.2"
TAG_COMMIT = "17363bb23bdb1d5d4391a85acf37469c9f832793"
FIXTURE_BLOB = "805c63392a4337a1845794106d5e831a92868f12"
TAG_PATH = "php/lib/Service/ExclusionService.php"

IMAGE = "php:8.3-cli"

# The bounds of the timing series: the quotient of the median at 4000 and at
# 1000 characters has to read as linear (4) with room for noise and caches, and
# the hostile median at 4000 stays under the 8.4 ms of the research plus half.
LENGTHS = (250, 500, 1000, 2000, 4000)
RATIO_LOW = 2.5
RATIO_HIGH = 6.0
HOSTILE_CEILING_MS = 12.6
REPEAT = 50


def _docker() -> str:
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("docker is not available")
    probe = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "version", "--format", "{{.Server.Version}}"],
        capture_output=True,
        check=False,
        timeout=60,
    )
    if probe.returncode != 0:
        pytest.skip("docker is installed but its daemon does not answer")
    return docker


def run_driver(source: str, mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    """One run of the driver over one source file, the JSON answer as a dict."""
    docker = _docker()
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "run", "--rm", "-i", "-v", f"{REPO_ROOT}:/app", "-w", "/app", IMAGE, "php", DRIVER, source, mode],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=600,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    assert answer.returncode == 0, answer.stderr
    result = json.loads(answer.stdout)
    assert isinstance(result, dict)
    return result


# -- the corpus ------------------------------------------------------------

NFD_CAFE = "Cafe\u0301"
NFC_CAFE = unicodedata.normalize("NFC", NFD_CAFE)

# The prefixes an instance of 1.4.2 may hold, the awkward ones first, so the
# ceiling of 64 cuts the filler behind them and not them.
INTERESTING_PREFIXES: list[Any] = [
    "Archiv",
    "a*b",
    "x?y",
    "Foto (2024)",
    "files/Backups",
    "//Doppelt//Pfad/",
    "Gro\u00df",
    "gro\u00df",
    "GROSS",
    NFD_CAFE,
    "Steuer\u0001zeichen",
    ".",
    "..",
    "./Archiv",
    "Archiv/../x",
    "files",
    "L" * 257,
    7,
    None,
]


def prefix_corpus() -> list[Any]:
    """The interesting prefixes plus filler, more than the ceiling of 64 in all."""
    filler = [f"Fill/{index:02d}" for index in range(70)]
    entries = INTERESTING_PREFIXES + filler
    assert len(entries) > 64
    return entries


def path_corpus() -> list[str]:
    """Per prefix the hit, the neighbour, case, NFC and NFD, with and without files/."""
    stems = [
        "Archiv",
        "a*b",
        "x?y",
        "Foto (2024)",
        "Backups",
        "Doppelt/Pfad",
        "Gro\u00df",
        "gro\u00df",
        "GROSS",
        NFC_CAFE,
        NFD_CAFE,
        "Steuer\u0001zeichen",
        "Fill/03",
        "Fill/63",
        "Fill/69",
        "L" * 257,
    ]
    paths: list[str] = []
    for stem in stems:
        paths.extend(
            [
                stem,
                stem + "/x.pdf",
                stem + "x.pdf",
                stem.upper() + "/x.pdf",
                stem.lower() + "/x.pdf",
                "files/" + stem + "/x.pdf",
                "Sub/" + stem + "/x.pdf",
                unicodedata.normalize("NFC", stem) + "/x",
                unicodedata.normalize("NFD", stem) + "/x",
            ]
        )
    paths.extend(
        [
            "",
            "/",
            "axxb/x.pdf",
            "xzy/x.pdf",
            "Archivar.pdf",
            "/Archiv/x.pdf",
            "Archiv//x.pdf",
            "Doppelt//Pfad/x.pdf",
            "Fotos (2024)/x.pdf",
            "Vortrag.key/Data/x.jpg",
            "Archiv/Vortrag.key/Data/x.jpg",
        ]
    )
    return paths


def answers(source: str, patterns: list[str] | None = None) -> dict[str, Any]:
    config: dict[str, Any] = {"exclusions": prefix_corpus()}
    if patterns is not None:
        config["exclusion_patterns"] = patterns
    return run_driver(source, "answers", {"config": config, "paths": path_corpus()})


# -- provenance --------------------------------------------------------------


def git_blob_id(data: bytes) -> str:
    """The id git gives these bytes as a blob, computed without git and without filters."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data, usedforsecurity=False).hexdigest()


def test_the_fixture_is_the_blob_the_provenance_names() -> None:
    data = FIXTURE.read_bytes()

    assert b"\r" not in data
    assert git_blob_id(data) == FIXTURE_BLOB
    provenance = PROVENANCE.read_text(encoding="utf-8")
    for value in (TAG, TAG_COMMIT, FIXTURE_BLOB, TAG_PATH):
        assert value in provenance


def test_the_fixture_is_byte_for_byte_the_file_of_the_tag() -> None:
    git = shutil.which("git")
    if git is None:
        pytest.skip("git is not available")
    tag = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [git, "rev-parse", "--verify", "--quiet", f"{TAG}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if tag.returncode != 0:
        pytest.skip(f"tag {TAG} not fetched")

    shown = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [git, "show", f"{TAG}:{TAG_PATH}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    )

    assert tag.stdout.strip() == TAG_COMMIT
    assert shown.stdout == FIXTURE.read_bytes()


# -- the difference test -------------------------------------------------------


def test_the_prefixes_of_1_4_2_answer_exactly_as_before() -> None:
    old = answers(OLD_SOURCE)
    new = answers(NEW_SOURCE)

    # Not vacuous: the corpus hits and misses, and the ceiling cut the filler.
    assert old["patterns"] is None
    assert True in old["isExcluded"]
    assert False in old["isExcluded"]
    assert len(old["prefixes"]) == 64
    assert "Archiv" in old["prefixes"]
    assert "a*b" in old["prefixes"]

    assert new["prefixes"] == old["prefixes"]
    assert new["isExcluded"] == old["isExcluded"]
    assert new["log"] == old["log"]
    assert new["patterns"] == []
    assert new["jobs"] == old["jobs"] == 0


def test_the_comparison_sees_a_difference_when_there_is_one() -> None:
    # The positive control. One pattern in the new service, and exactly the
    # answers it should change differ: the bundle path that no prefix covers.
    # The same bundle below Archiv was excluded by the prefix already.
    paths = path_corpus()
    old = answers(OLD_SOURCE)
    new = answers(NEW_SOURCE, ["*.key"])

    pairs = zip(old["isExcluded"], new["isExcluded"], strict=True)
    differing = [paths[index] for index, (before, after) in enumerate(pairs) if before != after]

    assert new["patterns"] == ["*.key"]
    assert new["prefixes"] == old["prefixes"]
    assert differing == ["Vortrag.key/Data/x.jpg"]


# -- the timing series -------------------------------------------------------------

BENIGN_PATTERNS = [
    "*.photoslibrary",
    "*/node_modules/*",
    "*.key",
    "*.pages",
    "*.numbers",
    "*.app",
    "*.bundle",
    "*.fcpbundle",
    "*/build/*",
    "*/.git/*",
    "*/__pycache__/*",
    "*.tmp",
    "*~",
    "*.bak",
    "Backups/*",
    "*/.cache/*",
    "*/vendor/*",
    "*/dist/*",
    "*/target/*",
    "*.lrdata",
    "*.lrcat-data",
    "*.imovielibrary",
    "*.tvlibrary",
    "*.musiclibrary",
    "*/Thumbs.db",
    "*/.DS_Store",
    "*.part",
    "*.crdownload",
    "*/.venv/*",
    "*/.idea/*",
    "Archiv/*/Alt/*",
    "*.sparsebundle",
]


def hostile_patterns() -> list[str]:
    """Thirty two patterns of sixty characters, stars and question marks mixed.

    Every one begins with a star, so no pass ends early, and ends in a letter
    the hostile paths never carry, so no pass is accepted early either.
    """
    patterns = []
    for unit in ("a?a*", "?aa*", "aa?*", "a??*"):
        for tail in "zyxwvuts":
            patterns.append(("*" + unit * 15)[:59] + tail)
    assert len(set(patterns)) == 32
    assert all(len(pattern) == 60 and "**" not in pattern for pattern in patterns)
    return patterns


def benign_path(length: int, variant: int) -> str:
    """A realistic deep path of exactly this length that no benign pattern covers."""
    unit = f"Projekte/Kunde{variant}/2024/Unterlagen/Entwurf-{variant}/"
    path = (unit * (length // len(unit) + 1))[: length - 4] + ".pdf"
    assert len(path) == length
    return path


def hostile_path(length: int, variant: int) -> str:
    """Repeated near hits: runs of the letter every hostile pattern consumes."""
    unit = "a" * (40 + variant) + "/"
    path = (unit * (length // len(unit) + 1))[: length - 1] + "a"
    assert len(path) == length
    return path


def series(patterns: list[str], path_of: Any) -> dict[int, float]:
    groups = {str(length): [path_of(length, variant) for variant in range(3)] for length in LENGTHS}
    result = run_driver(
        NEW_SOURCE,
        "timing",
        {"config": {"exclusion_patterns": patterns}, "groups": groups, "repeat": REPEAT},
    )
    return {int(name): float(entry["median_ms"]) for name, entry in result["groups"].items()}


@pytest.mark.timing
@pytest.mark.skipif(os.environ.get("FINDLING_TIMING") != "1", reason="timing series runs only with FINDLING_TIMING=1")
def test_the_matcher_is_linear_in_the_path_length() -> None:
    hostile = hostile_patterns()
    # Every hostile pattern is in force, or the series would time fewer.
    probe = run_driver(NEW_SOURCE, "answers", {"config": {"exclusion_patterns": hostile}, "paths": []})
    assert len(probe["patterns"]) == 32
    probe = run_driver(NEW_SOURCE, "answers", {"config": {"exclusion_patterns": BENIGN_PATTERNS}, "paths": []})
    assert len(probe["patterns"]) == 32

    benign_medians = series(BENIGN_PATTERNS, benign_path)
    hostile_medians = series(hostile, hostile_path)

    report = "\n".join(
        f"{length:>5}  benign {benign_medians[length]:.4f} ms  hostile {hostile_medians[length]:.4f} ms"
        for length in LENGTHS
    )
    # The series is the evidence of the summary, and -s shows it.
    print("\n" + report)

    for name, medians in (("benign", benign_medians), ("hostile", hostile_medians)):
        ratio = medians[4000] / medians[1000]
        assert RATIO_LOW <= ratio <= RATIO_HIGH, f"{name}: t(4000)/t(1000) = {ratio:.2f}\n{report}"
    assert hostile_medians[4000] < HOSTILE_CEILING_MS, report
