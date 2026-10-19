"""The probes of the phase 33 audit (33-AUDIT.md): exclusion patterns and limits.

Phase 33 put a new comparison into the write path of every file of an instance
(the event listener asks ExclusionService::isExcluded), a mass removal path
(ExclusionSweepJob, way C of the reconcile, the clearing of verdict rows) and a
new admin input (the pattern list of the rules form). This module holds the
audit probes as regression tests, in three groups.

**The oracle, run through the driver of plan 33-02.** A reference matcher
written for this audit from the prose of ``docs/admin-page.md`` (section
"Ausschlussmuster"), not from the PHP code: a recursive definition over lists
of characters with a memo, no ``fnmatch``, no regular expression and nothing of
the bit masks of the service. A generated corpus (fixed seed) plus fixed edge
groups is answered by the real ``php/lib/Service/ExclusionService.php`` through
``backend/tests/drivers/exclusion_driver.php`` (unchanged) on ``php:8.3-cli``,
and every answer has to agree with the oracle. Without Docker these are
skipped with that reason.

**Source probes.** ``token_get_all`` of PHP itself (a one-off script run by the
same image) instead of the regular expressions of gate D: which functions the
matcher and the normaliser call, how many ``preg_*`` calls the service holds,
and which variables reach a logger call of the classes of the phase.

**Instance probes, skipped without an instance.** The refusal corpus against
the rules routes, a second writer over ``occ config:app:set`` with garbage,
the rights of a non admin and the request token, and the log of instance and
backend with a positive control. They need these variables:

    FINDLING_AUDIT33_URL          http://localhost:8090
    FINDLING_AUDIT33_ADMIN_PASS   password of admin
    FINDLING_AUDIT33_USER         a non admin account (testuser)
    FINDLING_AUDIT33_USER_PASS    its password
    FINDLING_AUDIT33_CONTAINER    name of the Nextcloud container (occ, log)
    FINDLING_AUDIT33_BACKEND_LOG  path of the backend log (log probe)
    FINDLING_AUDIT33_BACKEND_URL  http://127.0.0.1:10035 (log probe control)

Every value of the instance corpus carries the marker ``q33`` and nothing else
in the instance does, so the log probe searches one word. The instance is left
as it was found: the pattern key is deleted again, files the probes wrote are
deleted over WebDAV, cron.php runs and the trash bin of the user is emptied.

Only ASCII in this file: every other character is written as an escape.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import shutil
import sqlite3
import subprocess
import threading
import time
import unicodedata
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import pytest

REPO = Path(__file__).resolve().parents[2]
DRIVER = "backend/tests/drivers/exclusion_driver.php"
SOURCE = "php/lib/Service/ExclusionService.php"
IMAGE = os.environ.get("FINDLING_AUDIT33_PHP_IMAGE", "php:8.3-cli")
# php:8.3-cli carries neither intl nor the polyfill of Nextcloud, so the service
# falls back to the raw value where it composes a pattern to NFC
# (ExclusionService::composed()). Finding L-33-01, accepted: the runtime of
# Nextcloud always has the class (intl or the polyfill of the server), and the
# image of the instance (nextcloud:34.0.3-apache, PHP 8.5 with intl) answers the
# same corpus with the composition. The oracle_run fixture asks the image
# whether the class exists, and on an image without it the oracle reads a
# pattern without composing it, which is the documented fallback; every other
# rule is judged the same way on both images. The composition itself is then
# proven on the real runtime by
# test_a_pattern_stored_in_nfd_by_occ_hits_the_nfc_name_on_the_instance.
OUT_DIR = os.environ.get("FINDLING_AUDIT33_OUT", "")

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------


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


def run_driver(payload: dict[str, Any]) -> dict[str, Any]:
    """One run of the unchanged driver of 33-02 over the service of today."""
    docker = _docker()
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [
            docker,
            "run",
            "--rm",
            "-i",
            "--entrypoint",
            "php",
            "-v",
            f"{REPO}:/app:ro",
            "-w",
            "/app",
            IMAGE,
            DRIVER,
            SOURCE,
            "answers",
        ],
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


def _write_out(name: str, data: object) -> None:
    """Large outputs go to a file of the audit run, never into the test output."""
    if not OUT_DIR:
        return
    target = Path(OUT_DIR)
    target.mkdir(parents=True, exist_ok=True)
    (target / name).write_text(json.dumps(data, ensure_ascii=True, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# The oracle, from docs/admin-page.md section "Ausschlussmuster"
# ---------------------------------------------------------------------------
#
# What the documentation says, and nothing else:
#
# - two wildcards: "*" any number of characters, none included, across folders;
#   "?" exactly one character inside a name, never "/";
# - a pattern hits when it fits the whole path or an ancestor at a "/" border;
# - it is compared against the path and against the path with a "/" in front;
# - case counts; the pattern is composed to NFC on save, "?" is one character,
#   not one byte;
# - on save a pattern is trimmed like a prefix: outer white space away, double
#   "/" folded, "/" at the start and the end away, a leading "files/" away;
# - refusals: empty, too_long (over 60 characters after NFC), traversal ("." or
#   ".." as a folder name), double_star, unsupported_character ([ ] { } and
#   backslash), negation (a leading "!"), control_character, no_literal (only
#   "*", "?" and "/"), no_wildcard (neither "*" nor "?"); duplicates after the
#   normalisation count once; more than 32 are not applied;
# - prefixes: a path is under a prefix when it is the prefix or starts with the
#   prefix and "/".
#
# Assumption A1 (the documentation names the path space, not the shape of a
# path handed in): a path is folded like a prefix, double "/" into one and "/"
# at both ends away. White space of a path is kept as it is, names may begin or
# end with a blank.

STAR = "*"
ANY = "?"
SLASH = "/"
MAX_PATTERNS = 32
MAX_PATTERN_LENGTH = 60
REFUSED = frozenset("[]{}\\")


def _fold_slashes(value: str) -> str:
    while "//" in value:
        value = value.replace("//", "/")
    return value.strip(SLASH)


def doc_problems(raw: object, *, compose: bool = True) -> tuple[set[str], str | None]:
    """Every refusal code the documentation gives for one entry, and its stored form.

    compose=False is the fallback of a PHP runtime without the Normalizer class
    (L-33-01): the entry keeps its code points as they came.
    """
    if not isinstance(raw, str):
        return {"not_a_string"}, None
    text = raw.strip(" \t")
    if compose:
        text = unicodedata.normalize("NFC", text)
    text = _fold_slashes(text)
    if text.startswith("files/"):
        text = text[len("files/") :]
    problems: set[str] = set()
    if text == "":
        problems.add("empty")
    if len(text) > MAX_PATTERN_LENGTH:
        problems.add("too_long")
    if any(segment in {".", ".."} for segment in text.split(SLASH)):
        problems.add("traversal")
    if STAR + STAR in text:
        problems.add("double_star")
    if any(c in REFUSED for c in text):
        problems.add("unsupported_character")
    if text.startswith("!"):
        problems.add("negation")
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in text):
        problems.add("control_character")
    if text != "" and all(c in "*?/" for c in text):
        problems.add("no_literal")
    if text != "" and STAR not in text and ANY not in text:
        problems.add("no_wildcard")
    return problems, (text if not problems else None)


def doc_patterns_in_force(stored: list[Any], *, compose: bool = True) -> list[str]:
    """What a stored list means: usable entries, once each, at most 32."""
    kept: list[str] = []
    for raw in stored:
        _problems, text = doc_problems(raw, compose=compose)
        if text is None or text in kept:
            continue
        kept.append(text)
        if len(kept) >= MAX_PATTERNS:
            break
    return kept


def doc_fits(pattern: str, path: str) -> bool:
    """Does the pattern fit the whole path or an ancestor of it at a "/" border."""
    # fits(i, j): the rest of the pattern from i fits the path from j up to its
    # end or up to a "/". The recursive definition, filled as a memo table from
    # the back, because a path of 4000 characters is deeper than the stack.
    p = list(pattern)
    s = list(path)
    width = len(s) + 1
    memo = [False] * ((len(p) + 1) * width)
    for j in range(len(s) + 1):
        memo[len(p) * width + j] = j == len(s) or s[j] == SLASH
    for i in range(len(p) - 1, -1, -1):
        row = i * width
        below = (i + 1) * width
        for j in range(len(s), -1, -1):
            if p[i] == STAR:
                result = memo[below + j] or (j < len(s) and memo[row + j + 1])
            elif p[i] == ANY:
                result = j < len(s) and s[j] != SLASH and memo[below + j + 1]
            else:
                result = j < len(s) and s[j] == p[i] and memo[below + j + 1]
            memo[row + j] = result
    return memo[0]


def doc_path(path: str) -> str:
    """Assumption A1: a path folded like a prefix."""
    return _fold_slashes(path)


def doc_excluded(prefixes: list[str], patterns: list[str], path: str) -> bool:
    folded = doc_path(path)
    if folded == "":
        return False
    for prefix in prefixes:
        if folded == prefix or folded.startswith(prefix + SLASH):
            return True
    return any(doc_fits(pattern, folded) or doc_fits(pattern, SLASH + folded) for pattern in patterns)


# ---------------------------------------------------------------------------
# The corpus
# ---------------------------------------------------------------------------

SEED = 3311
RANDOM_RUNS = 60

E_ACUTE = "\u00e9"
U_UMLAUT = "\u00dc"
CJK = "\u4e2d"
EMOJI = "\U0001f600"
COMBINING_ACUTE = "\u0301"
LITERALS = ["a", "b", "c", "A", ".", "-", "_", " ", "x", E_ACUTE, U_UMLAUT, CJK, EMOJI, "(", ")", "+", "$", "^"]

# Raw entries the read path has to drop, mixed into some random runs.
UNUSABLE = ["**/x", "[a]*", "!*.x", "*", "a/../*.b", "nowild", "", "*\nx", "x" * 61 + "*", 7, None, ["*.x"]]


@dataclass
class Run:
    group: str
    stored: list[Any]
    paths: list[str]
    prefixes: list[str] = field(default_factory=list)


def _literal(rng: random.Random) -> str:
    return rng.choice(LITERALS)


def _segment(rng: random.Random, low: int = 1, high: int = 8) -> str:
    name = "".join(_literal(rng) for _ in range(rng.randint(low, high))).strip(" ")
    if name in {"", ".", ".."}:
        name = "d"
    return name


def _gen_pattern(rng: random.Random) -> str:
    while True:
        pieces = []
        for _ in range(rng.randint(2, 12)):
            roll = rng.random()
            if roll < 0.25:
                pieces.append(STAR)
            elif roll < 0.4:
                pieces.append(ANY)
            elif roll < 0.5:
                pieces.append(SLASH)
            else:
                pieces.append(_literal(rng))
        text = "".join(pieces)
        if doc_problems(text)[1] is not None:
            return text


def _decorate(rng: random.Random, pattern: str) -> str:
    """A raw spelling of the same pattern the save has to normalise."""
    roll = rng.random()
    if roll < 0.06:
        return SLASH + pattern + SLASH
    if roll < 0.1:
        return "files/" + pattern
    if roll < 0.14:
        return " " + pattern + "\t"
    if roll < 0.18:
        return pattern.replace(SLASH, "//")
    return pattern


def _instantiate(rng: random.Random, pattern: str) -> str:
    out = []
    for c in pattern:
        if c == STAR:
            out.append("".join(rng.choice([*LITERALS, SLASH]) for _ in range(rng.randint(0, 5))))
        elif c == ANY:
            out.append(_literal(rng))
        else:
            out.append(c)
    return "".join(out)


def _canonical(path: str) -> str:
    path = _fold_slashes(path).strip(" ")
    segments = ["d" if s in {".", ".."} else s for s in path.split(SLASH)]
    path = SLASH.join(segments).strip(" ")
    return path or "x"


def _mutate(rng: random.Random, path: str) -> str:
    if not path:
        return path
    at = rng.randrange(len(path))
    roll = rng.random()
    if roll < 0.34:
        return path[:at] + _literal(rng) + path[at + 1 :]
    if roll < 0.67:
        return path[:at] + rng.choice([*LITERALS, SLASH]) + path[at:]
    return path[:at] + path[at + 1 :]


def _related_path(rng: random.Random, pattern: str) -> str:
    path = _instantiate(rng, doc_problems(pattern)[1] or pattern)
    if rng.random() < 0.4:
        path = SLASH.join(_segment(rng) for _ in range(rng.randint(1, 2))) + SLASH + path
    if rng.random() < 0.5:
        path = path + SLASH + SLASH.join(_segment(rng) for _ in range(rng.randint(1, 2)))
    if rng.random() < 0.35:
        path = _mutate(rng, path)
    return _canonical(path)


def _random_path(rng: random.Random) -> str:
    return _canonical(SLASH.join(_segment(rng) for _ in range(rng.randint(1, 4))))


def random_runs() -> list[Run]:
    rng = random.Random(SEED)  # noqa: S311 - a corpus with a fixed seed, no secret
    runs = []
    for _ in range(RANDOM_RUNS):
        patterns = [_gen_pattern(rng) for _ in range(rng.randint(1, 3))]
        stored: list[object] = [_decorate(rng, p) for p in patterns]
        if rng.random() < 0.3:
            stored.insert(rng.randrange(len(stored) + 1), rng.choice(UNUSABLE))
        paths = []
        for pattern in patterns:
            paths.extend(_related_path(rng, pattern) for _ in range(16))
        paths.extend(_random_path(rng) for _ in range(8))
        runs.append(Run("random", stored, paths))
    return runs


def _sixty(rng: random.Random) -> str:
    while True:
        text = "".join(rng.choice([STAR, ANY, ANY, "a", "b", "/", E_ACUTE]) for _ in range(MAX_PATTERN_LENGTH))
        text = text.replace(STAR + STAR, STAR + "a")
        text = ("a" + text)[:MAX_PATTERN_LENGTH] if text[0] == SLASH else text
        text = text[:-1] + "b" if text[-1] == SLASH else text
        if len(text) == MAX_PATTERN_LENGTH and doc_problems(text)[1] == text:
            return text


def edge_runs() -> list[Run]:
    rng = random.Random(SEED + 1)  # noqa: S311 - a corpus with a fixed seed, no secret
    nfd_cafe = "Cafe" + COMBINING_ACUTE
    nfc_cafe = "Caf" + E_ACUTE
    long_deep = "d/" * 1997 + "x.key"
    long_name = "a" * 3996 + ".key"
    long_mixed = "/".join("seg" + str(i) for i in range(700))[:3990] + "/n.key"
    long_random = _canonical("".join(rng.choice([*LITERALS, SLASH]) for _ in range(4000)))
    nm_long = "node_modules/" + "x" * 3980 + "/y.js"
    sixties = [_sixty(rng) for _ in range(12)]
    runs = [
        Run(
            "doc_examples",
            ["*.photoslibrary", "*/node_modules/*", "Scan_??.pdf", "Backups/*", "*.key"],
            [
                "Fotos/Mediathek.photoslibrary/database/Photos.sqlite",
                "Notiz.photoslibrary.txt",
                "node_modules/react/index.js",
                "Projekte/web/node_modules/x/y.js",
                "Projekte/node_modules_alt/x.js",
                "Scan_01.pdf",
                "Scan_1.pdf",
                "Scan_0/.pdf",
                "Backups/2024/x.pdf",
                "Alt/Backups/x.pdf",
                "Vortrag.key",
                "Vortrag.KEY",
                "Mediathek.photoslibrary",
            ],
        ),
        Run(
            "empty_segments",
            ["a//*.q", "//*.k//", "x/ /*y", "/files//m/*", "files/files/*.f"],
            [
                "a/1.q",
                "a//1.q",
                "/a/1.q/",
                "b/a/1.q",
                "z.k",
                "z/w.k/v",
                "x/ /1y",
                "x/1y",
                "m/1",
                "files/m/1",
                "files/1.f",
                "1.f",
                "files//files/1.f",
            ],
        ),
        Run(
            "star_edges",
            ["*q", "q*", "*a*b*", "*/node_modules/*", "Backups/*"],
            [
                "q",
                "xq",
                "qx",
                "x/q",
                "q/x",
                "xq/y",
                "aXb",
                "ab",
                "ba",
                "a/b",
                "node_modules",
                "node_modules/x",
                "a/node_modules",
                "Backups",
                "Backups/x",
                "x/Backups/y",
            ],
        ),
        Run(
            "question_before_slash",
            ["a?/*.t", "?/x*", "*/?", "Scan_??.pdf"],
            [
                "ab/1.t",
                "a/b/1.t",
                "a/1.t",
                "abc/1.t",
                "a/x1",
                "ab/x1",
                "q/r",
                "q/rs",
                "q/r/s",
                "Scan_0/.pdf",
                "Scan_ab.pdf",
                "Scan_a.pdf/x",
            ],
        ),
        Run(
            "multibyte",
            ["Caf?", "?" + CJK + "*", "*" + EMOJI, U_UMLAUT + "?er*"],
            [
                nfc_cafe,
                nfc_cafe + "/x",
                "Cafe",
                "Caf" + EMOJI,
                "Caf" + E_ACUTE + E_ACUTE,
                "a" + CJK,
                EMOJI + CJK + "/z",
                CJK + CJK,
                "x" + EMOJI,
                EMOJI,
                U_UMLAUT + "ber",
                U_UMLAUT + EMOJI + "er/x",
                "U\u0308ber",
            ],
        ),
        Run(
            "nfd_against_nfc",
            [nfd_cafe + "*", "Caf" + E_ACUTE + "?", "*e" + COMBINING_ACUTE],
            [
                nfc_cafe,
                nfd_cafe,
                nfc_cafe + "x",
                nfd_cafe + "x",
                "Caf" + E_ACUTE + "x",
                "Cafex",
                "xe" + COMBINING_ACUTE,
                "x" + E_ACUTE,
            ],
        ),
        Run(
            "long_paths",
            ["*.key", "*/node_modules/*", "a*b*c*d*e*f*g*h*i*j*k*l*m*n*o*p*q*r*s*t*u*v*w*x*y*z*", "d/?/*.zz"],
            [long_deep, long_name, long_mixed, long_random, nm_long, "d/" * 1998 + "zz", "d/x/" + "y" * 3990 + ".zz"],
        ),
        Run(
            "sixty_character_patterns",
            sixties[:4],
            [_related_path(rng, p) for p in sixties[:4] for _ in range(8)] + [long_random, long_deep],
        ),
        Run(
            "sixty_character_patterns",
            sixties[4:8],
            [_related_path(rng, p) for p in sixties[4:8] for _ in range(8)] + [long_random, long_name],
        ),
        Run(
            "sixty_character_patterns",
            sixties[8:],
            [_related_path(rng, p) for p in sixties[8:] for _ in range(8)] + [long_mixed],
        ),
        Run(
            "prefix_and_pattern",
            ["*.key", "Archiv/*", "Backups/*/alt*"],
            [
                "Archiv/x.pdf",
                "Archiv/v.key",
                "Archivar.pdf",
                "Archivar/v.key",
                "Backups/2024/x",
                "Backups/2024/alt.txt",
                "Backups/2024/neu/alt",
                "Backup/2024/alt",
                "a/b.key/c",
            ],
            prefixes=["Archiv", "Backups/2024"],
        ),
        Run(
            "white_space_edges",
            ["?x*", "* ", " *.k "],
            [" x", "x ", " x/y", "ax", "x", "a /b", "a/ b", "a.k", " a.k"],
        ),
    ]
    over = [f"*.k{i:03d}" for i in range(40)]
    runs.append(
        Run("ceiling_and_duplicates", [*over[:3], "/" + over[0] + "/", *over], [f"x.k{i:03d}" for i in range(40)])
    )
    return runs


@dataclass
class Deviation:
    group: str
    stored: list[Any]
    path: str
    oracle: bool
    php: bool


@dataclass
class OracleRun:
    composed: bool = True
    pairs: dict[str, int] = field(default_factory=dict)
    deviations: list[Deviation] = field(default_factory=list)
    kept_mismatch: list[tuple[str, list[str], list[str]]] = field(default_factory=list)
    log_entries: list[dict[str, Any]] = field(default_factory=list)


def image_has_normalizer() -> bool:
    """Asked of the image itself, never guessed from its name (L-33-01)."""
    docker = _docker()
    probe = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "run", "--rm", "--entrypoint", "php", IMAGE, "-r", 'echo class_exists("Normalizer") ? "yes" : "no";'],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=600,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    assert probe.returncode == 0, probe.stderr
    assert probe.stdout.strip() in {"yes", "no"}, probe.stdout
    return probe.stdout.strip() == "yes"


@pytest.fixture(scope="module")
def oracle_run() -> OracleRun:
    _docker()
    result = OracleRun(composed=image_has_normalizer())
    report: list[dict[str, Any]] = []
    for run in random_runs() + edge_runs():
        answer = run_driver(
            {"config": {"exclusions": run.prefixes, "exclusion_patterns": run.stored}, "paths": run.paths}
        )
        kept = doc_patterns_in_force(run.stored, compose=result.composed)
        if answer["patterns"] != kept:
            result.kept_mismatch.append((run.group, kept, answer["patterns"]))
        php_answers = answer["isExcluded"]
        assert len(php_answers) == len(run.paths)
        result.pairs[run.group] = result.pairs.get(run.group, 0) + len(run.paths)
        result.log_entries.extend(answer["log"])
        for path, php in zip(run.paths, php_answers, strict=True):
            mine = doc_excluded(run.prefixes, kept, path)
            if mine != php:
                result.deviations.append(Deviation(run.group, run.stored, path, mine, php))
        report.append(
            {
                "group": run.group,
                "stored": run.stored,
                "kept": kept,
                "php_kept": answer["patterns"],
                "paths": len(run.paths),
            }
        )
    _write_out(
        "oracle.json",
        {
            "image": IMAGE,
            "composed": result.composed,
            "pairs": result.pairs,
            "total": sum(result.pairs.values()),
            "deviations": [d.__dict__ for d in result.deviations],
            "kept_mismatch": result.kept_mismatch,
            "runs": report,
        },
    )
    return result


GROUPS = [
    "random",
    "doc_examples",
    "empty_segments",
    "star_edges",
    "question_before_slash",
    "multibyte",
    "nfd_against_nfc",
    "long_paths",
    "sixty_character_patterns",
    "prefix_and_pattern",
    "white_space_edges",
    "ceiling_and_duplicates",
]


def test_the_oracle_reads_the_examples_of_the_documentation_as_written() -> None:
    """Positive control of the oracle itself, without Docker: the table rows of the doc."""
    assert doc_excluded([], ["*.photoslibrary"], "Fotos/Mediathek.photoslibrary/database/Photos.sqlite")
    assert not doc_excluded([], ["*.photoslibrary"], "Notiz.photoslibrary.txt")
    assert doc_excluded([], ["*/node_modules/*"], "node_modules/react/index.js")
    assert doc_excluded([], ["*/node_modules/*"], "Projekte/web/node_modules/x/y.js")
    assert not doc_excluded([], ["*/node_modules/*"], "Projekte/node_modules_alt/x.js")
    assert doc_excluded([], ["Scan_??.pdf"], "Scan_01.pdf")
    assert not doc_excluded([], ["Scan_??.pdf"], "Scan_1.pdf")
    assert not doc_excluded([], ["Scan_??.pdf"], "Scan_0/.pdf")
    assert doc_excluded([], ["Backups/*"], "Backups/2024/x.pdf")
    assert not doc_excluded([], ["Backups/*"], "Alt/Backups/x.pdf")
    assert doc_excluded([], ["*.key"], "Vortrag.key")
    assert not doc_excluded([], ["*.key"], "Vortrag.KEY")
    assert doc_excluded([], [doc_problems("Caf?")[1] or ""], "Caf" + E_ACUTE)
    assert doc_problems("/Fotos/*.jpg/")[1] == doc_problems("Fotos/*.jpg")[1] == "Fotos/*.jpg"
    assert doc_problems("*")[0] == {"no_literal"}
    assert doc_problems("node_modules")[0] == {"no_wildcard"}


def test_the_corpus_has_at_least_2000_pairs(oracle_run: OracleRun) -> None:
    total = sum(oracle_run.pairs.values())
    assert total >= 2000, oracle_run.pairs
    assert oracle_run.pairs["random"] >= 2000, oracle_run.pairs
    assert set(oracle_run.pairs) == set(GROUPS)


@pytest.mark.parametrize("group", GROUPS)
def test_the_matcher_agrees_with_the_oracle_of_the_documentation(oracle_run: OracleRun, group: str) -> None:
    found = [d for d in oracle_run.deviations if d.group == group]
    assert found == [], [(d.stored, ascii(d.path)[:120], d.oracle, d.php) for d in found[:5]]


def test_the_list_in_force_is_the_list_of_the_documentation(oracle_run: OracleRun) -> None:
    assert oracle_run.kept_mismatch == []


def test_the_fallback_of_the_oracle_is_not_a_blind_spot() -> None:
    """Positive control of compose=False: the two readings of an NFD pattern differ.

    Without it, the oracle could agree with an image without the Normalizer class
    on the nfd_against_nfc group for a reason that has nothing to do with the
    composition, and L-33-01 would have hidden a real deviation.
    """
    nfd = "Cafe" + COMBINING_ACUTE + "*"
    nfc_name = "Caf" + E_ACUTE + ".txt"
    composed = doc_patterns_in_force([nfd])
    raw = doc_patterns_in_force([nfd], compose=False)
    assert composed != raw
    assert doc_excluded([], composed, nfc_name)
    assert not doc_excluded([], raw, nfc_name)


def test_the_driver_log_of_the_corpus_carries_counters_only(oracle_run: OracleRun) -> None:
    for entry in oracle_run.log_entries:
        context = entry.get("context", {})
        assert all(isinstance(v, int) for v in context.values()), entry


def test_the_comparison_sees_a_difference_when_there_is_one() -> None:
    """Positive control of the comparison: the oracle with another pattern than PHP."""
    paths = ["a/b.key", "a/b.pages", "x/y.key/z"]
    answer = run_driver({"config": {"exclusions": [], "exclusion_patterns": ["*.key"]}, "paths": paths})
    mine = [doc_excluded([], ["*.pages"], p) for p in paths]
    assert mine != answer["isExcluded"]
    assert [doc_excluded([], ["*.key"], p) for p in paths] == answer["isExcluded"]


# ---------------------------------------------------------------------------
# Source probes over token_get_all
# ---------------------------------------------------------------------------

PROBE_PHP = r"""<?php
declare(strict_types=1);
$skip = [T_WHITESPACE, T_COMMENT, T_DOC_COMMENT, T_OPEN_TAG, T_CLOSE_TAG, T_INLINE_HTML];
$all = [];
foreach (array_slice($argv, 1) as $file) {
    $t = [];
    $line = 1;
    foreach (token_get_all(file_get_contents($file)) as $tok) {
        if (is_array($tok)) {
            $line = $tok[2];
            if (in_array($tok[0], $skip, true)) {
                continue;
            }
            $t[] = [token_name($tok[0]), $tok[1], $line];
        } else {
            $t[] = ['CHAR', $tok, $line];
        }
    }
    $n = count($t);
    $functions = [];
    for ($i = 0; $i < $n - 1; $i++) {
        if ($t[$i][0] !== 'T_FUNCTION' || $t[$i + 1][0] !== 'T_STRING') {
            continue;
        }
        $j = $i + 2;
        while ($j < $n && !($t[$j][0] === 'CHAR' && ($t[$j][1] === '{' || $t[$j][1] === ';'))) {
            $j++;
        }
        if ($j >= $n || $t[$j][1] === ';') {
            continue;
        }
        $depth = 0;
        for ($k = $j; $k < $n; $k++) {
            $v = $t[$k];
            $opens = ['T_CURLY_OPEN', 'T_DOLLAR_OPEN_CURLY_BRACES'];
            if (($v[0] === 'CHAR' && $v[1] === '{') || in_array($v[0], $opens, true)) {
                $depth++;
            } elseif ($v[0] === 'CHAR' && $v[1] === '}') {
                $depth--;
                if ($depth === 0) {
                    break;
                }
            }
        }
        $functions[$t[$i + 1][1]] = [$j, $k];
    }
    $owner = function (int $at) use ($functions): string {
        foreach ($functions as $name => [$a, $b]) {
            if ($at > $a && $at < $b) {
                return $name;
            }
        }
        return '';
    };
    $calls = [];
    $evals = [];
    $logs = [];
    $names = ['T_STRING', 'T_NAME_FULLY_QUALIFIED', 'T_NAME_QUALIFIED', 'T_EXIT'];
    for ($i = 1; $i < $n - 1; $i++) {
        if ($t[$i][0] === 'T_EVAL') {
            $evals[] = [$owner($i), $t[$i][2]];
        }
        if (!in_array($t[$i][0], $names, true) || $t[$i + 1][1] !== '(') {
            continue;
        }
        $prev = $t[$i - 1][0];
        $kind = 'function';
        if ($prev === 'T_OBJECT_OPERATOR' || $prev === 'T_NULLSAFE_OBJECT_OPERATOR') {
            $kind = 'method';
        } elseif ($prev === 'T_DOUBLE_COLON') {
            $kind = 'static';
        } elseif ($prev === 'T_NEW') {
            $kind = 'new';
        } elseif ($prev === 'T_FUNCTION') {
            $kind = 'declaration';
        }
        $receiver = $kind === 'method' || $kind === 'static' ? $t[$i - 2][1] : '';
        $first = $t[$i + 2][0] === 'T_CONSTANT_ENCAPSED_STRING' ? $t[$i + 2][1] : null;
        $calls[] = [$owner($i), ltrim($t[$i][1], '\\'), $kind, $receiver, $t[$i][2], $first];
        $isLogger = $kind === 'method' && (
            ($t[$i - 2][1] === 'logger' && $t[$i - 3][0] === 'T_OBJECT_OPERATOR' && $t[$i - 4][1] === '$this')
            || $t[$i - 2][1] === '$logger'
        );
        if (!$isLogger) {
            continue;
        }
        $stack = [];
        $vars = [];
        $props = [];
        for ($k = $i + 1; $k < $n; $k++) {
            $v = $t[$k];
            if ($v[1] === '(' && $v[0] === 'CHAR') {
                $stack[] = in_array($t[$k - 1][0], $names, true) ? ltrim($t[$k - 1][1], '\\') : '';
            } elseif ($v[1] === ')' && $v[0] === 'CHAR') {
                array_pop($stack);
                if ($stack === []) {
                    break;
                }
            } elseif ($v[0] === 'T_VARIABLE') {
                // Reduced to a number or a truth value: inside count(), or one
                // side of a comparison.
                $compare = [
                    'T_IS_IDENTICAL', 'T_IS_NOT_IDENTICAL', 'T_IS_EQUAL', 'T_IS_NOT_EQUAL',
                    'T_IS_SMALLER_OR_EQUAL', 'T_IS_GREATER_OR_EQUAL',
                ];
                $counted = in_array('count', array_slice($stack, 1), true)
                    || in_array($t[$k + 1][0], $compare, true) || in_array($t[$k - 1][0], $compare, true);
                if ($v[1] === '$this' && $t[$k + 1][0] === 'T_OBJECT_OPERATOR' && $t[$k + 3][1] !== '(') {
                    $props[] = [$t[$k + 2][1], $counted];
                } elseif ($v[1] !== '$this') {
                    $vars[] = [$v[1], $counted];
                }
            }
        }
        $message = $t[$i + 2][0] === 'T_CONSTANT_ENCAPSED_STRING' || $t[$i + 2][0] === 'T_STRING' ? $t[$i + 2][1] : '';
        $logs[] = [$owner($i), $t[$i][1], $t[$i][2], $message, $vars, $props];
    }
    $lines = array_map(fn ($r) => [$t[$r[0]][2], $t[$r[1]][2]], $functions);
    $all[$file] = ['functions' => $lines, 'calls' => $calls, 'evals' => $evals, 'logs' => $logs];
}
echo json_encode($all, JSON_THROW_ON_ERROR);
"""

PHASE_CLASSES = [
    "php/lib/Service/ExclusionService.php",
    "php/lib/BackgroundJobs/ExclusionSweepJob.php",
    "php/lib/BackgroundJobs/SubtreeExpandJob.php",
    "php/lib/BackgroundJobs/StorageCrawlJob.php",
    "php/lib/Service/FileStateService.php",
    "php/lib/Controller/SettingsController.php",
    "php/lib/Service/AdminViewService.php",
    "php/lib/Listener/FileEventListener.php",
    "php/lib/Service/QueueService.php",
    "php/lib/Controller/ReconcileController.php",
    "php/lib/Service/PurgeService.php",
    "php/lib/Service/SettingsService.php",
]

# Names of variables that carry a path, a pattern, a prefix or the fingerprint.
FORBIDDEN_LOG_VARIABLES = frozenset(
    {
        "$path",
        "$paths",
        "$pattern",
        "$patterns",
        "$prefix",
        "$prefixes",
        "$fingerprint",
        "$raw",
        "$entry",
        "$list",
        "$mountRelativePath",
        "$internalPath",
        "$relative",
        "$normalised",
        "$stored",
        "$exclusions",
        "$exclusionPatterns",
        "$name",
        "$argument",
    }
)
FORBIDDEN_LOG_PROPERTIES = frozenset({"cachedPatterns", "cachedPrefixes", "fingerprint"})


def run_probe(tmp: Path, files: list[str], extra: dict[str, str] | None = None) -> dict[str, Any]:
    docker = _docker()
    (tmp / "probe.php").write_text(PROBE_PHP, encoding="utf-8")
    for name, text in (extra or {}).items():
        (tmp / name).write_text(text, encoding="utf-8")
    answer = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [
            docker,
            "run",
            "--rm",
            "--entrypoint",
            "php",
            "-v",
            f"{REPO}:/app:ro",
            "-v",
            f"{tmp}:/probe:ro",
            "-w",
            "/app",
            IMAGE,
            "/probe/probe.php",
            *files,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=300,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    assert answer.returncode == 0, answer.stderr
    result = json.loads(answer.stdout)
    assert isinstance(result, dict)
    return result


SYNTHETIC = """<?php
class X {
    // preg_match($a) fnmatch('x') eval('1;')
    public function matchesAPattern(string $path): bool {
        $s = 'preg_match(';
        if (fnmatch('*', $path)) { return true; }
        eval('$a = 1;');
        $this->logger->warning('m', [
            'p' => $path, 'n' => count($patterns), 'b' => $list === [] ? 0 : 1, 'q' => $this->fingerprint,
        ]);
        return preg_match('#a#', $path) === 1 || $this->matchesAPattern($path);
    }
}
"""


def _callees(calls: list[list[Any]], function: str) -> list[list[Any]]:
    return [c for c in calls if c[0] == function]


def _reaches_itself(calls: list[list[Any]], functions: set[str], start: str) -> bool:
    edges: dict[str, set[str]] = {}
    for owner, name, kind, receiver, _line, _first in calls:
        if kind in {"method", "static"} and receiver in {"$this", "self", "static"} and name in functions:
            edges.setdefault(owner, set()).add(name)
    seen: set[str] = set()
    todo = list(edges.get(start, set()))
    while todo:
        current = todo.pop()
        if current == start:
            return True
        if current in seen:
            continue
        seen.add(current)
        todo.extend(edges.get(current, set()))
    return False


def test_the_token_probe_finds_real_calls_and_nothing_in_comments_or_strings(tmp_path: Path) -> None:
    """Positive control of the source probe."""
    data = run_probe(tmp_path, ["/probe/x.php"], {"x.php": SYNTHETIC})["/probe/x.php"]
    calls = data["calls"]
    names = [c[1] for c in _callees(calls, "matchesAPattern") if c[2] == "function"]
    assert names.count("preg_match") == 1
    assert names.count("fnmatch") == 1
    assert len(data["evals"]) == 1
    assert _reaches_itself(calls, set(data["functions"]), "matchesAPattern")
    (log,) = data["logs"]
    assert log[4] == [["$path", False], ["$patterns", True], ["$list", True]]
    assert log[5] == [["fingerprint", False]]


def test_the_matcher_and_the_normaliser_use_no_glob_no_regex_no_eval_and_no_recursion(tmp_path: Path) -> None:
    data = run_probe(tmp_path, [SOURCE])[SOURCE]
    functions = set(data["functions"])
    assert {"matchesAPattern", "normalisePattern", "trimmed"} <= functions
    for name in ("matchesAPattern", "normalisePattern"):
        called = [c[1].lower() for c in _callees(data["calls"], name) if c[2] == "function"]
        assert not [c for c in called if c == "fnmatch" or c.startswith("preg_")], (name, called)
        assert not [e for e in data["evals"] if e[0] == name]
        assert not _reaches_itself(data["calls"], functions, name), name
    _write_out("source_probe_service.json", data)


def test_the_service_holds_exactly_one_preg_call_the_allowed_one_in_trimmed(tmp_path: Path) -> None:
    data = run_probe(tmp_path, [SOURCE])[SOURCE]
    pregs = [c for c in data["calls"] if c[2] == "function" and c[1].lower().startswith("preg_")]
    assert len(pregs) == 1, pregs
    owner, name, _kind, _receiver, _line, first = pregs[0]
    assert (owner, name, first) == ("trimmed", "preg_replace", "'#/+#'")
    assert data["evals"] == []


def test_no_log_call_of_the_phase_classes_carries_a_path_a_pattern_or_the_fingerprint(tmp_path: Path) -> None:
    data = run_probe(tmp_path, PHASE_CLASSES)
    seen = 0
    offending = []
    for file, info in data.items():
        for owner, method, line, message, variables, props in info["logs"]:
            seen += 1
            for name, counted in variables:
                if name in FORBIDDEN_LOG_VARIABLES and not counted:
                    offending.append((file, line, owner, method, name))
            for name, counted in props:
                if name in FORBIDDEN_LOG_PROPERTIES and not counted:
                    offending.append((file, line, owner, method, "->" + name))
            _ = message
    _write_out("source_probe_logs.json", data)
    assert seen > 20
    assert offending == []


# ---------------------------------------------------------------------------
# Instance probes
# ---------------------------------------------------------------------------

URL = os.environ.get("FINDLING_AUDIT33_URL", "")
ADMIN_PASS = os.environ.get("FINDLING_AUDIT33_ADMIN_PASS", "")
USER = os.environ.get("FINDLING_AUDIT33_USER", "")
USER_PASS = os.environ.get("FINDLING_AUDIT33_USER_PASS", "")
CONTAINER = os.environ.get("FINDLING_AUDIT33_CONTAINER", "")
BACKEND_LOG = os.environ.get("FINDLING_AUDIT33_BACKEND_LOG", "")
BACKEND_URL = os.environ.get("FINDLING_AUDIT33_BACKEND_URL", "")

instance = pytest.mark.skipif(
    not (URL and ADMIN_PASS and USER and USER_PASS and CONTAINER),
    reason="no audit instance (FINDLING_AUDIT33_URL and friends)",
)

MARK = "q33"
PREVIEW = "/index.php/apps/findling/admin/rules/preview"
SAVE = "/index.php/apps/findling/admin/rules"
OVERVIEW = "/index.php/apps/findling/admin/overview"
PAGE = "/index.php/settings/admin/findling"


def occ(*args: str) -> subprocess.CompletedProcess[str]:
    docker = _docker()
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "exec", "-u", "www-data", CONTAINER, "php", "occ", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=600,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )


def container_php(code: str) -> str:
    docker = _docker()
    out = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "exec", "-u", "www-data", CONTAINER, "php", "-r", code],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=600,
        env={**os.environ, "MSYS_NO_PATHCONV": "1"},
    )
    return out.stdout


def sql(query: str) -> list[list[Any]]:
    code = (
        '$db = new PDO("sqlite:/var/www/html/data/nextcloud.db");'
        "echo json_encode($db->query(base64_decode('"
        + base64.b64encode(query.encode()).decode()
        + "'))->fetchAll(PDO::FETCH_NUM));"
    )
    rows = json.loads(container_php(code))
    assert isinstance(rows, list)
    return rows


def cron() -> None:
    docker = _docker()
    subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "exec", "-u", "www-data", CONTAINER, "php", "cron.php"],
        capture_output=True,
        check=True,
        timeout=600,
    )


def nextcloud_log() -> list[str]:
    return container_php('readfile("/var/www/html/data/nextcloud.log");').splitlines()


def access_log_since(since: str) -> list[str]:
    docker = _docker()
    out = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [docker, "logs", "--since", since, CONTAINER],
        capture_output=True,
        check=False,
        timeout=120,
    )
    return (out.stdout + out.stderr).decode("utf-8", "replace").splitlines()


def backend_log() -> list[str]:
    if not BACKEND_LOG:
        return []
    return Path(BACKEND_LOG).read_text(encoding="utf-8", errors="replace").splitlines()


def client(user: str, password: str) -> tuple[httpx.Client, str]:
    session = httpx.Client(base_url=URL, auth=(user, password), timeout=300)
    token = session.get("/index.php/csrftoken").json()["token"]
    return session, token


def rules_snapshot() -> tuple[str, str, int]:
    exclusions = occ("config:app:get", "findling", "exclusions")
    patterns = occ("config:app:get", "findling", "exclusion_patterns")
    jobs = sum(
        1
        for line in occ("background-job:list").stdout.splitlines()
        if "ExclusionSweepJob" in line or "SubtreeExpandJob" in line
    )
    return exclusions.stdout.strip(), f"{patterns.returncode}:{patterns.stdout.strip()}", jobs


@dataclass(frozen=True, slots=True)
class Refusal:
    label: str
    body: dict[str, Any] | None
    expected: frozenset[str]
    form: str | None = None
    field: str = "exclusionPatterns"


OK = frozenset({"ok"})
ANY_CODE = frozenset({"any"})


def _p(*values: object) -> dict[str, Any]:
    return {"exclusions": ["Archiv"], "exclusionPatterns": list(values)}


def refusal_cases() -> list[Refusal]:
    def code(*names: str) -> frozenset[str]:
        return frozenset(names)

    return [
        Refusal("empty: empty string", _p(""), code("empty")),
        Refusal("empty: blanks", _p("   "), code("empty")),
        Refusal("empty: slashes", _p("///"), code("empty")),
        Refusal("empty: one slash", _p("/"), code("empty")),
        Refusal("too_long: 66 ascii", _p("*q33ab" + "a" * 60), code("too_long")),
        Refusal("too_long: 61 after NFC from NFD", _p("*q33ac" + ("e" + COMBINING_ACUTE) * 55), code("too_long")),
        Refusal("ok: 60 after NFC from NFD", _p("*q33ad" + ("e" + COMBINING_ACUTE) * 54), OK),
        Refusal("too_long: 4 MB", _p("q33ae*" + "x" * (4 * 1024 * 1024)), code("too_long")),
        Refusal("too_many: 33", _p(*[f"*.q33af{i:02d}" for i in range(33)]), code("too_many")),
        Refusal("too_many: 1000", _p(*[f"*.q33ag{i:04d}" for i in range(1000)]), code("too_many")),
        Refusal("too_many: 40000", _p(*[f"*.q33ah{i:05d}" for i in range(40000)]), code("too_many")),
        Refusal("duplicate: same", _p("*.q33ba", "*.q33ba"), code("duplicate")),
        Refusal("duplicate: slashes", _p("*.q33bb", "/*.q33bb/"), code("duplicate")),
        Refusal("duplicate: files vanguard", _p("*.q33bc", "files/*.q33bc"), code("duplicate")),
        Refusal(
            "duplicate: NFD and NFC",
            _p("Caf" + E_ACUTE + "*q33bd", "Cafe" + COMBINING_ACUTE + "*q33bd"),
            code("duplicate"),
        ),
        Refusal("traversal: leading dotdot", _p("../*.q33ca"), code("traversal")),
        Refusal("traversal: inner dot", _p("a/./*q33cb"), code("traversal")),
        Refusal("traversal: inner dotdot", _p("*/../q33cc"), code("traversal")),
        Refusal("traversal: trailing dotdot", _p("q33cd*/.."), code("traversal")),
        Refusal("double_star: front", _p("**/q33da"), code("double_star")),
        Refusal("double_star: back", _p("q33db/**"), code("double_star")),
        Refusal("double_star: triple", _p("*q33dc***"), code("double_star")),
        Refusal("double_star: inner", _p("q33dd/**/x"), code("double_star")),
        Refusal("unsupported: brackets", _p("[q33ea]*"), code("unsupported_character")),
        Refusal("unsupported: braces", _p("q33eb{a,b}*"), code("unsupported_character")),
        Refusal("unsupported: backslash", _p("*q33ec\\x"), code("unsupported_character")),
        Refusal("unsupported: closing bracket", _p("]q33ed*"), code("unsupported_character")),
        Refusal(
            "unsupported: invalid UTF-8 (form body)",
            None,
            code("unsupported_character"),
            form="exclusions%5B%5D=Archiv&exclusionPatterns%5B%5D=%FFq33ee%2A",
        ),
        Refusal("negation: plain", _p("!*.q33fa"), code("negation")),
        Refusal("negation: no star first", _p("!q33fb*"), code("negation")),
        Refusal("negation: after blanks", _p("  !*q33fc"), code("negation")),
        Refusal("negation: after a slash", _p("/!*q33fd"), frozenset({"negation", "ok"})),
        Refusal("control: line feed", _p("*q33ga\n.x"), code("control_character")),
        Refusal("control: NUL", _p("*q33gb\u0000x"), code("control_character")),
        Refusal("control: bell", _p("*q33gc\u0007x"), code("control_character")),
        Refusal("control: delete", _p("*q33gd\u007fx"), code("control_character")),
        Refusal("control: tab inside", _p("*q33ge\tx"), code("control_character")),
        Refusal("control: C1 next line", _p("*q33gf\u0085x"), frozenset({"control_character", "ok"})),
        Refusal("no_literal: star", _p("*"), code("no_literal")),
        Refusal("no_literal: star slash star", _p("*/*"), code("no_literal")),
        Refusal("no_literal: question star", _p("?*"), code("no_literal")),
        Refusal("no_literal: mixed", _p("*?/?*"), code("no_literal")),
        Refusal("no_wildcard: plain", _p("q33ha"), code("no_wildcard")),
        Refusal("no_wildcard: dotted", _p("q33hb.key"), code("no_wildcard")),
        Refusal("no_wildcard: fullwidth asterisk", _p("\uff0aq33hc"), code("no_wildcard")),
        Refusal("no_wildcard: asterisk operator", _p("\u2217q33hd"), code("no_wildcard")),
        Refusal("no_wildcard: low asterisk", _p("\u204eq33he"), code("no_wildcard")),
        Refusal("no_wildcard: small asterisk", _p("\ufe61q33hf"), code("no_wildcard")),
        Refusal("no_wildcard: fullwidth question mark", _p("\uff1fq33hh"), code("no_wildcard")),
        Refusal("ok: fullwidth asterisk as literal next to a star", _p("*\uff0aq33hg"), OK),
        Refusal("bidi: override inside", _p("*q33ia\u202e.key"), frozenset({"control_character", "ok"})),
        Refusal("bidi: override in front", _p("\u202e*q33ib"), frozenset({"control_character", "ok"})),
        Refusal("bidi: isolate", _p("*q33ic\u2066x"), frozenset({"control_character", "ok"})),
        Refusal("shape: array in the list", _p(["*.q33ja"]), ANY_CODE),
        Refusal("shape: nested arrays", _p([["*.q33jb"]]), ANY_CODE),
        Refusal("shape: object in the list", _p({"a": "*.q33jc"}), ANY_CODE),
        Refusal("shape: number", _p(5), ANY_CODE),
        Refusal("shape: null", _p(None), ANY_CODE),
        Refusal("shape: boolean", _p(True), ANY_CODE),
        # H-33-01, fixed in Task 4 of 33-11: a value that is not a list earns the
        # code of a value that is not text, in both lists and both routes.
        Refusal(
            "shape: string instead of a list",
            {"exclusions": ["Archiv"], "exclusionPatterns": "*.q33jd"},
            code("empty"),
        ),
        Refusal(
            "shape: object instead of a list", {"exclusions": ["Archiv"], "exclusionPatterns": {"x": "*.q33je"}}, OK
        ),
        Refusal(
            "shape: number instead of a list",
            {"exclusions": ["Archiv"], "exclusionPatterns": 7},
            code("empty"),
        ),
        Refusal(
            "shape: empty string instead of a list", {"exclusions": ["Archiv"], "exclusionPatterns": ""}, code("empty")
        ),
        Refusal(
            "prefix list: string instead of a list",
            {"exclusions": "q33xb", "exclusionPatterns": []},
            code("empty"),
            field="exclusions",
        ),
        Refusal(
            "prefix list: number instead of a list",
            {"exclusions": 7, "exclusionPatterns": []},
            code("empty"),
            field="exclusions",
        ),
        Refusal(
            "prefix list: traversal",
            {"exclusions": ["../q33ka"], "exclusionPatterns": []},
            code("traversal"),
            field="exclusions",
        ),
        Refusal(
            "prefix list: duplicate",
            {"exclusions": ["q33kb", "/q33kb/"], "exclusionPatterns": []},
            code("duplicate"),
            field="exclusions",
        ),
        Refusal(
            "prefix list: too long",
            {"exclusions": ["q33kc" + "x" * 300], "exclusionPatterns": []},
            code("too_long"),
            field="exclusions",
        ),
    ]


@dataclass
class RefusalAnswer:
    status: int
    codes: list[str]
    echoed: bool
    text: str


def ask_rules(
    session: httpx.Client, token: str, route: str, case: Refusal, extra: dict[str, Any] | None = None
) -> RefusalAnswer:
    headers = {"requesttoken": token}
    if case.form is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        form = case.form
        if extra:
            form += "&" + "&".join(f"{k}={v}" for k, v in extra.items())
        response = session.post(route, content=form.encode(), headers=headers)
    else:
        body = dict(case.body or {})
        body.update(extra or {})
        response = session.post(route, json=body, headers=headers)
    codes: list[str] = []
    try:
        data = response.json()
        value = data.get(case.field) if isinstance(data, dict) else None
        if isinstance(value, list):
            codes = [str(v) for v in value]
    except ValueError:
        pass
    text = response.text
    # Valid previews name the new patterns by design; the probe is about refusals.
    echoed = MARK in text and response.status_code != 200
    return RefusalAnswer(response.status_code, codes, echoed, text[:300])


def _judge(case: Refusal, answer: RefusalAnswer) -> str | None:
    if answer.status >= 500:
        return f"HTTP {answer.status}"
    if answer.echoed:
        return "value in the answer"
    if case.expected == OK:
        return None if answer.status == 200 else f"expected 200, got {answer.status} {answer.codes}"
    if answer.status == 200:
        return None if "ok" in case.expected else f"expected a refusal {sorted(case.expected)}, got 200"
    if answer.status != 400:
        return f"expected 400, got {answer.status}"
    if "any" in case.expected:
        return None if answer.codes else "400 without a code"
    return None if set(answer.codes) & case.expected else f"codes {answer.codes} not in {sorted(case.expected)}"


@dataclass
class InstanceRun:
    started: str = ""
    log_start: int = 0
    backend_start: int = 0
    preview: dict[str, RefusalAnswer] = field(default_factory=dict)
    save: dict[str, RefusalAnswer] = field(default_factory=dict)
    before: tuple[str, str, int] = ("", "", 0)
    after: tuple[str, str, int] = ("", "", 0)


@pytest.fixture(scope="module")
def instance_run() -> InstanceRun:
    run = InstanceRun()
    run.started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    run.log_start = len(nextcloud_log())
    run.backend_start = len(backend_log())
    run.before = rules_snapshot()
    session, token = client("admin", ADMIN_PASS)
    with closing(session):
        for case in refusal_cases():
            run.preview[case.label] = ask_rules(session, token, PREVIEW, case)
        # The other three fields as they stand, so a refusal of the save comes
        # from the list under test alone.
        rules = session.get(OVERVIEW, headers={"requesttoken": token}).json()["rules"]
        save_extra = {
            "maxFileBytes": rules["maxFileBytes"],
            "indexTeamFolders": rules["indexTeamFolders"],
            "indexExternalStorage": rules["indexExternalStorage"],
        }
        form_extra = {
            "maxFileBytes": str(rules["maxFileBytes"]),
            "indexTeamFolders": "1" if rules["indexTeamFolders"] else "0",
            "indexExternalStorage": "1" if rules["indexExternalStorage"] else "0",
        }
        for case in refusal_cases():
            if "ok" in case.expected:
                continue  # a valid list would be written; the save probe is about refusals
            extra: dict[str, Any] = form_extra if case.form is not None else save_extra
            run.save[case.label] = ask_rules(session, token, SAVE, case, extra)
    run.after = rules_snapshot()
    _write_out(
        "refusals.json",
        {
            "preview": {k: v.__dict__ for k, v in run.preview.items()},
            "save": {k: v.__dict__ for k, v in run.save.items()},
            "before": run.before,
            "after": run.after,
        },
    )
    return run


# H-33-01 (fixed in Task 4 of 33-11): a list sent as a string or a number ended
# saveRules in a TypeError, HTTP 500, with the arguments in the log.


@instance
@pytest.mark.parametrize(
    "case",
    [pytest.param(c, id=c.label) for c in refusal_cases()],
)
def test_a_refused_entry_names_its_code_never_fails_and_never_echoes(instance_run: InstanceRun, case: Refusal) -> None:
    answer = instance_run.preview[case.label]
    assert _judge(case, answer) is None, (_judge(case, answer), answer.status, answer.codes)
    if case.label in instance_run.save:
        saved = instance_run.save[case.label]
        assert saved.status < 500, saved.status
        assert not saved.echoed
        assert _judge(case, saved) is None, (_judge(case, saved), saved.status, saved.codes)


@instance
def test_a_refused_save_writes_nothing(instance_run: InstanceRun) -> None:
    assert instance_run.before == instance_run.after


@instance
def test_the_rules_routes_refuse_a_non_admin_and_a_request_without_token() -> None:
    before = rules_snapshot()
    body = {"exclusions": ["q33ra"], "exclusionPatterns": ["*.q33rb"], "maxFileBytes": 0}
    session, token = client(USER, USER_PASS)
    with closing(session):
        user_preview = session.post(PREVIEW, json=body, headers={"requesttoken": token})
        user_save = session.post(SAVE, json=body, headers={"requesttoken": token})
        user_overview = session.get(OVERVIEW, headers={"requesttoken": token})
    anonymous = httpx.post(URL + SAVE, json=body, timeout=60)
    session, _token = client("admin", ADMIN_PASS)
    with closing(session):
        no_token = session.post(SAVE, json=body)
        no_token_preview = session.post(PREVIEW, json=body)
        get_save = session.get(SAVE)
    after = rules_snapshot()
    outcome = {
        "user_preview": user_preview.status_code,
        "user_save": user_save.status_code,
        "user_overview": user_overview.status_code,
        "anonymous_save": anonymous.status_code,
        "admin_save_without_token": no_token.status_code,
        "admin_preview_without_token": no_token_preview.status_code,
        "admin_get_save": get_save.status_code,
    }
    _write_out("rights.json", outcome)
    assert user_preview.status_code == 403
    assert user_save.status_code == 403
    assert user_overview.status_code == 403
    assert anonymous.status_code in {401, 412}
    assert no_token.status_code == 412
    assert no_token_preview.status_code == 412
    assert get_save.status_code == 405
    for response in (user_preview, user_save, anonymous, no_token, no_token_preview):
        assert MARK not in response.text
    assert before == after


# Each value with the list the documentation says is in force afterwards.
GARBAGE = [
    ("plain string", ["q33ma not json"], []),
    ("object", ['{"a":"*.q33mb"}', "--type=array"], ["*.q33mb"]),
    ("mixed list", ['[1,2.5,{"x":"*.q33mc"},null,true,["*.q33md"],"*.q33me"]', "--type=array"], ["*.q33me"]),
    (
        "1000 entries",
        [json.dumps([f"*.q33mf{i:04d}" for i in range(1000)]), "--type=array"],
        [f"*.q33mf{i:04d}" for i in range(32)],
    ),
    ("integer", ["42", "--type=integer"], []),
]
CANARY = ["*.q33my"]


def _webdav(session: httpx.Client, method: str, path: str, content: bytes | None = None) -> httpx.Response:
    return session.request(method, f"/remote.php/dav/files/{USER}{path}", content=content)


def _jobs(name: str) -> list[str]:
    ids = []
    for line in occ("background-job:list", "--limit=500").stdout.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 2 and cells[2].endswith("\\" + name):
            ids.append(cells[1])
    return ids


def _patterns_seen_by_the_web(admin: httpx.Client, token: str, expected: list[str], seconds: float = 30) -> list[str]:
    """The web process reads appconfig through a local cache of the core; wait for it."""
    deadline = time.monotonic() + seconds
    shown: list[str] = []
    while time.monotonic() < deadline:
        shown = admin.get(OVERVIEW, headers={"requesttoken": token}).json()["rules"]["exclusionPatterns"]
        if shown == expected:
            break
        time.sleep(1)
    return shown


def _cron_until_gone(name: str, runs: int = 10) -> int:
    done = 0
    while _jobs(name) and done < runs:
        cron()
        done += 1
    return done


# H-33-02 (fixed in Task 4 of 33-11): a pattern key of another type than array
# (occ --type=integer) stopped the listener, the page and the overview.


@instance
@pytest.mark.parametrize(
    ("label", "value", "in_force"),
    [pytest.param(*g, id=g[0]) for g in GARBAGE],
)
def test_a_second_writer_with_garbage_breaks_neither_page_nor_crawl_nor_listener(
    label: str, value: list[str], in_force: list[str]
) -> None:
    log_start = len(nextcloud_log())
    admin, admin_token = client("admin", ADMIN_PASS)
    user = httpx.Client(base_url=URL, auth=(USER, USER_PASS), timeout=120)
    folder = "/Audit3311occ"
    findings: dict[str, Any] = {"label": label}
    cleanup_start = log_start
    try:
        # The canary proves the web process switched to the garbage below.
        occ("config:app:set", "findling", "exclusion_patterns", "--value=" + json.dumps(CANARY), "--type=array")
        findings["canary"] = _patterns_seen_by_the_web(admin, admin_token, CANARY)
        # occ refuses to change the type of a key, so the key goes first; both
        # commands run back to back before the web view is asked again.
        occ("config:app:delete", "findling", "exclusion_patterns")
        findings["set"] = occ(
            "config:app:set", "findling", "exclusion_patterns", "--value=" + value[0], *value[1:]
        ).returncode
        findings["stored"] = occ("config:app:get", "findling", "exclusion_patterns", "--details").stdout[-400:]
        findings["shown"] = _patterns_seen_by_the_web(admin, admin_token, in_force)
        time.sleep(5)
        findings["shown_again"] = _patterns_seen_by_the_web(admin, admin_token, in_force, seconds=1)
        findings["page"] = admin.get(PAGE).status_code
        findings["overview"] = admin.get(OVERVIEW, headers={"requesttoken": admin_token}).status_code
        _webdav(user, "MKCOL", folder)
        put = _webdav(user, "PUT", folder + "/l.txt", b"listener probe")
        findings["put"] = put.status_code
        file_id = int(put.headers.get("OC-FileId", "0" * 8)[:8])
        query = f"select count(*) from oc_findling_queue where file_id = {file_id}"  # noqa: S608 - an int
        findings["queued"] = sql(query)[0][0]
        diagnose = occ("findling:diagnose", str(file_id))
        findings["diagnose"] = [diagnose.returncode, diagnose.stdout.splitlines()[1:2]]
        # The crawl: a recount crawl (StorageCrawlJob) asks isExcluded for every
        # file of every mount. The MKCOL above marked the scan stale (listener),
        # and ScanRecountJob plans the crawl; forced here so the crawl runs on the
        # garbage and not up to 15 minutes later.
        findings["crawl_jobs_before"] = len(_jobs("StorageCrawlJob"))
        for job in _jobs("ScanRecountJob"):
            occ("background-job:execute", "--force-execute", job)
        findings["crawl_jobs_planned"] = len(_jobs("StorageCrawlJob"))
        findings["crawl_cron_runs"] = _cron_until_gone("StorageCrawlJob")
        findings["crawl_jobs_after"] = len(_jobs("StorageCrawlJob"))
    finally:
        cleanup_start = len(nextcloud_log())
        _webdav(user, "DELETE", folder)
        occ("config:app:delete", "findling", "exclusion_patterns")
        findings["cleanup_cron_runs"] = _cron_until_gone("SubtreeExpandJob")
        occ("trashbin:cleanup", USER)
        user.close()
        admin.close()
    lines = nextcloud_log()[log_start:]
    probe_lines = lines[: cleanup_start - log_start]
    errors = [line for line in probe_lines if '"level":3' in line or '"level":4' in line]
    findling_lines = [json.loads(line) for line in lines if '"app":"findling"' in line]
    findings["errors"] = [e[:600] for e in errors]
    findings["findling"] = [{"message": f.get("message"), "data": f.get("data")} for f in findling_lines]
    findings["cleanup_errors"] = [
        e[:600] for e in lines[cleanup_start - log_start :] if '"level":3' in e or '"level":4' in e
    ]
    _write_out(f"garbage_{label.replace(' ', '_')}.json", findings)
    assert findings["canary"] == CANARY, findings
    assert findings["set"] == 0, findings
    assert findings["shown"] == in_force, findings
    assert findings["shown_again"] == in_force, findings
    assert findings["page"] == 200, findings
    assert findings["overview"] == 200, findings
    assert findings["put"] in {201, 204}, findings
    assert findings["queued"] >= 1, findings
    assert findings["diagnose"][0] == 0, findings
    assert findings["crawl_jobs_planned"] >= 1, findings
    assert findings["crawl_jobs_after"] == 0, findings
    assert errors == [], errors[:2]
    for entry in findling_lines:
        assert MARK not in json.dumps(entry.get("data", {})), entry
        assert MARK not in str(entry.get("message", "")), entry


def _cron_with_pause_until_gone(name: str, runs: int = 40) -> int:
    """Jobs that plan their successor a few seconds ahead need the pause between runs."""
    done = 0
    while _jobs(name) and done < runs:
        time.sleep(6)
        cron()
        done += 1
    return done


@instance
def test_a_prefix_key_of_another_type_breaks_neither_page_nor_listener() -> None:
    """The twin of H-33-02 on the prefix key, which 1.4.2 already read the same way."""
    log_start = len(nextcloud_log())
    admin, admin_token = client("admin", ADMIN_PASS)
    user = httpx.Client(base_url=URL, auth=(USER, USER_PASS), timeout=120)
    folder = "/Audit3311pfx"
    findings: dict[str, Any] = {}
    stored_before = occ("config:app:get", "findling", "exclusions").stdout.strip()
    cleanup_start = log_start
    try:
        occ("config:app:delete", "findling", "exclusions")
        findings["set"] = occ("config:app:set", "findling", "exclusions", "--value=42", "--type=integer").returncode
        findings["stored"] = occ("config:app:get", "findling", "exclusions", "--details").stdout[-200:]
        # The web process sees the change through the local cache of the core;
        # wait for the overview to answer for the integer, whatever it answers.
        deadline = time.monotonic() + 30
        status = 0
        while time.monotonic() < deadline:
            answer = admin.get(OVERVIEW, headers={"requesttoken": admin_token})
            status = answer.status_code
            if status != 200 or answer.json()["rules"]["exclusions"] == []:
                break
            time.sleep(1)
        time.sleep(5)
        overview = admin.get(OVERVIEW, headers={"requesttoken": admin_token})
        findings["overview"] = overview.status_code
        findings["shown"] = overview.json()["rules"]["exclusions"] if overview.status_code == 200 else None
        findings["page"] = admin.get(PAGE).status_code
        _webdav(user, "MKCOL", folder)
        put = _webdav(user, "PUT", folder + "/p.txt", b"listener probe")
        findings["put"] = put.status_code
        file_id = int(put.headers.get("OC-FileId", "0" * 8)[:8])
        query = f"select count(*) from oc_findling_queue where file_id = {file_id}"  # noqa: S608 - an int
        findings["queued"] = sql(query)[0][0]
        diagnose = occ("findling:diagnose", str(file_id))
        findings["diagnose"] = diagnose.returncode
    finally:
        cleanup_start = len(nextcloud_log())
        occ("config:app:delete", "findling", "exclusions")
        occ("config:app:set", "findling", "exclusions", "--value=" + stored_before, "--type=array")
        findings["restored"] = _patterns_seen_by_the_web_key(
            admin, admin_token, "exclusions", json.loads(stored_before)
        )
        _webdav(user, "DELETE", folder)
        findings["cleanup_cron_runs"] = _cron_with_pause_until_gone("SubtreeExpandJob")
        occ("trashbin:cleanup", USER)
        user.close()
        admin.close()
    lines = nextcloud_log()[log_start:cleanup_start]
    errors = [line for line in lines if '"level":3' in line or '"level":4' in line]
    findling_lines = [json.loads(line) for line in lines if '"app":"findling"' in line]
    _write_out("garbage_prefix_integer.json", {**findings, "errors": [e[:600] for e in errors]})
    assert findings["set"] == 0, findings
    assert findings["overview"] == 200, findings
    assert findings["shown"] == [], findings
    assert findings["page"] == 200, findings
    assert findings["put"] in {201, 204}, findings
    assert findings["queued"] >= 1, findings
    assert findings["diagnose"] == 0, findings
    assert findings["restored"] == json.loads(stored_before), findings
    assert errors == [], errors[:2]
    warnings = [f for f in findling_lines if "not usable folder paths" in str(f.get("message", ""))]
    assert warnings, "the unusable key is named"
    for entry in warnings:
        # The core adds the app and writes the numbers as strings.
        data = {k: v for k, v in (entry.get("data") or {}).items() if k != "app"}
        assert data == {"unusable": "1", "inForce": "0"}, entry


def _patterns_seen_by_the_web_key(admin: httpx.Client, token: str, key: str, expected: list[str]) -> list[str]:
    deadline = time.monotonic() + 30
    shown: list[str] = []
    while time.monotonic() < deadline:
        answer = admin.get(OVERVIEW, headers={"requesttoken": token})
        if answer.status_code == 200:
            shown = answer.json()["rules"][key]
            if shown == expected:
                break
        time.sleep(1)
    return shown


@instance
def test_no_log_line_carries_a_corpus_value(instance_run: InstanceRun) -> None:
    """Runs after the corpus; the positive control proves both logs are read."""
    marker = "zz3311ctl" + str(int(time.time()))
    httpx.request("PROPFIND", URL + "/remote.php/dav/files/" + marker, auth=(marker, "wrong"), timeout=60)
    if BACKEND_URL:
        httpx.get(BACKEND_URL + "/" + marker, timeout=60)
    time.sleep(1)
    lines = nextcloud_log()[instance_run.log_start :]
    backend = backend_log()[instance_run.backend_start :]
    access = access_log_since(instance_run.started)
    assert any(marker in line for line in lines), "positive control missing in nextcloud.log"
    if BACKEND_URL and BACKEND_LOG:
        assert any(marker in line for line in backend), "positive control missing in the backend log"
    assert any(marker in line for line in access), "positive control missing in the access log"
    # The TypeError lines of H-33-01 are judged by their own test below.
    type_errors = [line for line in lines if TYPE_ERROR in line]
    hits = {
        "nextcloud.log": [line[:300] for line in lines if MARK in line and TYPE_ERROR not in line],
        "backend": [line[:300] for line in backend if MARK in line],
        "access": [line[:300] for line in access if MARK in line],
    }
    _write_out(
        "log_probe.json",
        {
            "lines": len(lines),
            "backend": len(backend),
            "access": len(access),
            "hits": hits,
            "type_errors": len(type_errors),
            "type_errors_with_value": sum(1 for line in type_errors if MARK in line),
        },
    )
    assert hits == {"nextcloud.log": [], "backend": [], "access": []}


TYPE_ERROR = "saveRules(): Argument #"


@instance
@pytest.mark.parametrize(
    ("field_name", "value"),
    [("exclusionPatterns", "*.q33xa"), ("exclusionPatterns", 33), ("exclusions", "q33xb"), ("exclusions", 33)],
)
def test_a_wrong_list_shape_leaves_neither_a_500_nor_a_value_in_the_log(field_name: str, value: object) -> None:
    """H-33-01 and its twin on the prefix list of 1.4.2, after the fix of 33-11 Task 4."""
    log_start = len(nextcloud_log())
    before = rules_snapshot()
    session, token = client("admin", ADMIN_PASS)
    with closing(session):
        rules = session.get(OVERVIEW, headers={"requesttoken": token}).json()["rules"]
        body = {
            "exclusions": rules["exclusions"],
            "exclusionPatterns": rules["exclusionPatterns"],
            "maxFileBytes": rules["maxFileBytes"],
            "indexTeamFolders": rules["indexTeamFolders"],
            "indexExternalStorage": rules["indexExternalStorage"],
        }
        body[field_name] = value
        response = session.post(SAVE, json=body, headers={"requesttoken": token})
        preview = session.post(
            PREVIEW,
            json={k: body[k] for k in ("exclusions", "exclusionPatterns")},
            headers={"requesttoken": token},
        )
    lines = nextcloud_log()[log_start:]
    assert response.status_code == 400, response.status_code
    assert response.json()[field_name] == ["empty"], response.text[:300]
    assert preview.status_code == 400, preview.status_code
    assert preview.json()[field_name] == ["empty"], preview.text[:300]
    assert MARK not in response.text
    assert MARK not in preview.text
    assert not [line for line in lines if MARK in line]
    assert not [line for line in lines if TYPE_ERROR in line]
    assert rules_snapshot() == before


@instance
def test_a_pattern_stored_in_nfd_by_occ_hits_the_nfc_name_on_the_instance() -> None:
    """The NFC half the driver of php:8.3-cli cannot show (L-33-01), on the real runtime."""
    user = httpx.Client(base_url=URL, auth=(USER, USER_PASS), timeout=120)
    folder = "/Audit3311nfc"
    nfc_name = "Caf" + E_ACUTE + ".txt"
    session, token = client("admin", ADMIN_PASS)
    try:
        _webdav(user, "MKCOL", folder)
        put = _webdav(user, "PUT", folder + "/" + nfc_name, b"nfc probe")
        assert put.status_code in {201, 204}
        before = occ("findling:diagnose", f"{USER}:Audit3311nfc/{nfc_name}").stdout
        stored = json.dumps(["Audit3311nfc/Cafe" + COMBINING_ACUTE + "*"])
        assert (
            occ("config:app:set", "findling", "exclusion_patterns", "--value=" + stored, "--type=array").returncode == 0
        )
        after = occ("findling:diagnose", f"{USER}:Audit3311nfc/{nfc_name}").stdout
        shown = _patterns_seen_by_the_web(session, token, ["Audit3311nfc/Caf" + E_ACUTE + "*"])
    finally:
        occ("config:app:delete", "findling", "exclusion_patterns")
        _webdav(user, "DELETE", folder)
        _cron_until_gone("SubtreeExpandJob")
        occ("trashbin:cleanup", USER)
        user.close()
        session.close()
    _write_out("nfc_instance.json", {"before": before, "after": after, "shown": shown})
    assert "xcluded" not in before
    assert "xcluded" in after
    assert shown == ["Audit3311nfc/Caf" + E_ACUTE + "*"]


# ---------------------------------------------------------------------------
# Task 2: edge cases of the clearing ways and of the page
# ---------------------------------------------------------------------------
#
# One scenario on the instance, in the order of 33-AUDIT.md "## Bugs", written
# to bugs.json; the tests below judge its parts. It needs, besides the
# variables above, the state database of the backend for the reconcile stamp:
#
#     FINDLING_AUDIT33_STATE_DB     path of state.db of the backend
#
# The seed words carry no German word parts, so the compound splitting of the
# index finds nothing else. Every file lives under /Audit3311bug of the user,
# and one under /Archiv (the prefix the instance holds).

STATE_DB = os.environ.get("FINDLING_AUDIT33_STATE_DB", "")
SWEEP = "ExclusionSweepJob"
BUG_ROOT = "/Audit3311bug"
BUG_SEED = {
    "R": ("/Audit3311bug/Ordner/r1.txt", "zyrnoka"),
    "K": ("/Audit3311bug/Keep/k1.txt", "zyrkelo"),
    "S1": ("/Audit3311bug/Sweep/a.pat1/s1.txt", "zyrpaxa"),
    "S2": ("/Audit3311bug/Sweep/b.pat2/s2.txt", "zyrpbeo"),
    "S3": ("/Audit3311bug/Sweep/c.pat6/s3.txt", "zyrpcia"),
    "D": ("/Audit3311bug/Both/x.pat3/d1.txt", "zyrdumo"),
}
VERDICT_FILE = ("/Archiv/v3311.txt", "zyrvoxa")

bug_instance = pytest.mark.skipif(
    not (URL and ADMIN_PASS and USER and USER_PASS and CONTAINER and STATE_DB and BACKEND_LOG),
    reason="no audit instance with state database (FINDLING_AUDIT33_STATE_DB)",
)


def fingerprint(patterns: list[str]) -> str:
    """The fingerprint the sweep carries (docblock of fingerprintOf), for a crafted job."""
    return hashlib.sha256("\n".join(sorted(patterns)).encode()).hexdigest()


def hits(user: httpx.Client, word: str) -> int:
    response = user.get(
        "/ocs/v2.php/search/providers/findling/search",
        params={"term": word, "format": "json", "limit": 20},
        headers={"OCS-APIRequest": "true"},
    )
    entries = response.json()["ocs"]["data"]["entries"]
    return sum(1 for e in entries if isinstance(e.get("attributes"), dict) and e["attributes"].get("fileId"))


def wait_hits(user: httpx.Client, words: dict[str, int], seconds: float) -> dict[str, int]:
    deadline = time.monotonic() + seconds
    seen: dict[str, int] = {}
    while True:
        seen = {w: hits(user, w) for w in words}
        if seen == words or time.monotonic() > deadline:
            return seen
        time.sleep(5)


def sweep_jobs() -> list[dict[str, Any]]:
    rows = sql("select id, argument from oc_jobs where class = 'OCA\\Findling\\BackgroundJobs\\ExclusionSweepJob'")
    return [{"id": r[0], **json.loads(r[1])} for r in rows]


def add_sweep_job(argument: dict[str, Any]) -> None:
    """A job added through the IJobList of the core, as a running band would add its successor."""
    code = (
        "require '/var/www/html/lib/base.php';"
        "\\OCP\\Server::get(\\OCP\\BackgroundJob\\IJobList::class)->add("
        "'OCA\\Findling\\BackgroundJobs\\ExclusionSweepJob', json_decode(base64_decode('"
        + base64.b64encode(json.dumps(argument).encode()).decode()
        + "'), true));"
    )
    container_php(code)


def queue_rows(file_id: int) -> list[list[Any]]:
    return sql(f"select kind, claim_token from oc_findling_queue where file_id = {int(file_id)}")  # noqa: S608 - an int


def verdicts(file_id: int) -> list[list[Any]]:
    return sql(f"select state, reason from oc_findling_file_state where file_id = {int(file_id)}")  # noqa: S608 - an int


def plant_verdict(file_id: int) -> None:
    """A stored verdict skipped(no_text_layer), as the container reports it with OCR off."""
    sql(
        "insert or replace into oc_findling_file_state (file_id, state, reason, updated_at) "  # noqa: S608 - an int
        f"values ({int(file_id)}, 'skipped', 'no_text_layer', datetime('now'))"
    )


def save_rules(admin: httpx.Client, token: str, exclusions: list[str], patterns: list[str]) -> int:
    rules = admin.get(OVERVIEW, headers={"requesttoken": token}).json()["rules"]
    body = {
        "exclusions": exclusions,
        "exclusionPatterns": patterns,
        "maxFileBytes": rules["maxFileBytes"],
        "indexTeamFolders": rules["indexTeamFolders"],
        "indexExternalStorage": rules["indexExternalStorage"],
    }
    return admin.post(SAVE, json=body, headers={"requesttoken": token}).status_code


def _put(user: httpx.Client, path: str, text: str) -> int:
    parts = path.strip("/").split("/")
    for depth in range(1, len(parts)):
        _webdav(user, "MKCOL", "/" + "/".join(parts[:depth]))
    response = _webdav(user, "PUT", path, text.encode())
    assert response.status_code in {201, 204}, (path, response.status_code)
    return int(response.headers["OC-FileId"][:8])


def roll_back_the_reconcile_stamp(hours: int = 49) -> int:
    """The escape of _is_due: twice the pause runs whatever the hour, like 32-AUDIT."""
    with sqlite3.connect(STATE_DB, timeout=30) as db:
        cursor = db.execute(
            "update reconcile set finished_at = finished_at - ?, started_at = started_at - ? "
            "where finished_at is not null",
            (hours * 3600, hours * 3600),
        )
        return cursor.rowcount


def wait_for_a_reconcile_round(start: int, seconds: float = 420) -> str:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for line in backend_log()[start:]:
            if "reconcile round" in line:
                return line
        time.sleep(5)
    return ""


@pytest.fixture(scope="module")
def bug_run() -> dict[str, Any]:
    out: dict[str, Any] = {"steps": []}
    admin, token = client("admin", ADMIN_PASS)
    user = httpx.Client(base_url=URL, auth=(USER, USER_PASS), timeout=120)
    ids: dict[str, int] = {}
    log_start = len(nextcloud_log())

    def step(name: str, **data: Any) -> None:
        out["steps"].append({"step": name, "at": time.strftime("%H:%M:%S"), **data})
        _write_out("bugs.json", out)

    try:
        # Seed and wait for the index.
        for key, (path, word) in BUG_SEED.items():
            ids[key] = _put(user, path, word)
        out["ids"] = ids
        seeded = wait_hits(user, {w: 1 for _p, w in BUG_SEED.values()}, 300)
        step("seed", hits=seeded)

        # B2: patterns taken back while a sweep runs.
        home = sql(f"select storage, parent from oc_filecache where fileid = {ids['K']}")[0][0]  # noqa: S608 - an int
        files_root = sql(f"select fileid from oc_filecache where storage = {int(home)} and path = 'files'")[0][0]  # noqa: S608
        out["save_p12"] = save_rules(admin, token, ["Archiv"], ["*.pat1", "*.pat2"])
        out["jobs_after_p12"] = sweep_jobs()
        out["save_p1"] = save_rules(admin, token, ["Archiv"], ["*.pat1"])
        out["jobs_after_p1"] = sweep_jobs()
        stale: dict[str, Any] = {"storage": int(home), "root": int(files_root), "cursor": min(ids.values()) - 1}
        stale["fingerprint"] = fingerprint(["*.pat1", "*.pat2"])
        add_sweep_job(stale)
        out["jobs_with_the_band_in_flight"] = sweep_jobs()
        out["fingerprint_p1"] = fingerprint(["*.pat1"])
        out["fingerprint_p12"] = stale["fingerprint"]
        runs = []
        for _ in range(6):
            if not sweep_jobs():
                break
            cron()
            runs.append(sweep_jobs())
        out["jobs_per_cron_run_b2"] = runs
        out["queue_after_b2"] = {k: queue_rows(ids[k]) for k in ("S1", "S2", "S3", "K")}
        step("b2 sweeps", runs=len(runs))
        out["hits_after_b2"] = wait_hits(user, {"zyrpaxa": 0, "zyrpbeo": 1, "zyrpcia": 1, "zyrkelo": 1}, 200)
        out["save_empty"] = save_rules(admin, token, ["Archiv"], [])
        out["jobs_after_empty"] = sweep_jobs()
        step("b2 done", hits=out["hits_after_b2"])

        # B3: two quick saves back to back (the race of two at the same moment
        # is test_b3_two_saves_at_the_same_moment_...).
        out["save_a"] = save_rules(admin, token, ["Archiv"], ["*.pat2"])
        out["save_b"] = save_rules(admin, token, ["Archiv"], ["*.pat6"])
        out["jobs_after_two_saves"] = sweep_jobs()
        out["fingerprint_p6"] = fingerprint(["*.pat6"])
        out["fingerprint_p2"] = fingerprint(["*.pat2"])
        out["stored_after_race"] = _patterns_seen_by_the_web(admin, token, ["*.pat6"], seconds=3)
        out["jobs_after_race"] = sweep_jobs()
        runs = []
        for _ in range(6):
            if not sweep_jobs():
                break
            cron()
            runs.append(sweep_jobs())
        out["jobs_per_cron_run_b3"] = runs
        stored = out["stored_after_race"]
        expect_b3 = {"zyrpbeo": 0 if "*.pat2" in stored else 1, "zyrpcia": 0 if "*.pat6" in stored else 1}
        out["hits_after_b3"] = wait_hits(user, expect_b3, 200)
        out["expect_b3"] = expect_b3
        step("b3 done", hits=out["hits_after_b3"])

        # B4: a prefix and a pattern over the same file, with a verdict row.
        plant_verdict(ids["D"])
        out["verdict_d_before"] = verdicts(ids["D"])
        out["save_both"] = save_rules(admin, token, ["Archiv", "Audit3311bug/Both"], [*stored, "*.pat3"])
        out["jobs_after_both"] = {
            "sweep": sweep_jobs(),
            "subtree": len(_jobs("SubtreeExpandJob")),
        }
        b4_log = len(nextcloud_log())
        cron()
        out["queue_d_after_one_cron"] = queue_rows(ids["D"])
        out["verdict_d_after_one_cron"] = verdicts(ids["D"])
        out["cron_runs_b4"] = 1 + _cron_until_gone("SubtreeExpandJob") + _cron_until_gone(SWEEP)
        out["queue_d_after"] = queue_rows(ids["D"])
        out["verdict_d_after"] = verdicts(ids["D"])
        out["errors_b4"] = [line[:400] for line in nextcloud_log()[b4_log:] if '"level":3' in line]
        out["hits_after_b4"] = wait_hits(user, {"zyrdumo": 0, "zyrkelo": 1}, 200)
        step("b4 done", hits=out["hits_after_b4"])

        # B5: a verdict row of a file under a rule that the container never knew.
        ids["V"] = _put(user, *VERDICT_FILE)
        out["queue_v"] = queue_rows(ids["V"])
        plant_verdict(ids["V"])
        out["verdict_v_before"] = verdicts(ids["V"])

        # B1: a folder renamed under a pattern inside the mount.
        out["save_bndl"] = save_rules(admin, token, ["Archiv", "Audit3311bug/Both"], [*stored, "*.pat3", "*.bndl"])
        out["cron_runs_bndl"] = _cron_until_gone(SWEEP)
        out["hits_r_before_rename"] = hits(user, "zyrnoka")
        move = user.request(
            "MOVE",
            f"/remote.php/dav/files/{USER}/Audit3311bug/Ordner",
            headers={"Destination": f"{URL}/remote.php/dav/files/{USER}/Audit3311bug/Ordner.bndl"},
        )
        out["move"] = move.status_code
        out["queue_r_after_move"] = queue_rows(ids["R"])
        out["jobs_after_move"] = {
            "sweep": len(sweep_jobs()),
            "subtree": len(_jobs("SubtreeExpandJob")),
            "crawl": len(_jobs("StorageCrawlJob")),
        }
        out["cron_runs_after_move"] = _cron_until_gone("SubtreeExpandJob")
        out["queue_r_after_cron"] = queue_rows(ids["R"])
        # One poll of the backend (up to 120 s) before the reconcile.
        time.sleep(150)
        out["hits_r_before_reconcile"] = hits(user, "zyrnoka")
        out["hits_s1_before_reconcile"] = hits(user, "zyrpaxa")
        step("b1 before reconcile", r=out["hits_r_before_reconcile"])

        backend_start = len(backend_log())
        out["stamps_rolled_back"] = roll_back_the_reconcile_stamp()
        out["reconcile_line"] = wait_for_a_reconcile_round(backend_start)
        out["hits_after_reconcile"] = wait_hits(
            user, {"zyrnoka": 0, "zyrkelo": 1, "zyrpaxa": 1, "zyrdumo": 0, "zyrvoxa": 0}, 300
        )
        out["verdict_v_after"] = verdicts(ids["V"])
        out["queue_v_after"] = queue_rows(ids["V"])
        step("b1 and b5 after reconcile", hits=out["hits_after_reconcile"])
    finally:
        out["restore_save"] = save_rules(admin, token, ["Archiv"], [])
        occ("config:app:delete", "findling", "exclusion_patterns")
        _webdav(user, "DELETE", BUG_ROOT)
        _webdav(user, "DELETE", VERDICT_FILE[0])
        _cron_until_gone("SubtreeExpandJob")
        _cron_until_gone(SWEEP)
        occ("trashbin:cleanup", USER)
        for file_id in ids.values():
            sql(f"delete from oc_findling_file_state where file_id = {int(file_id)}")  # noqa: S608 - an int
        out["end"] = {
            "exclusions": occ("config:app:get", "findling", "exclusions").stdout.strip(),
            "patterns_exit": occ("config:app:get", "findling", "exclusion_patterns").returncode,
            "jobs": [
                line[:90]
                for line in occ("background-job:list", "--limit=500").stdout.splitlines()
                if "Findling" in line
            ],
        }
        out["errors"] = [
            line[:500] for line in nextcloud_log()[log_start:] if '"level":3' in line or '"level":4' in line
        ]
        _write_out("bugs.json", out)
        user.close()
        admin.close()
    return out


@bug_instance
def test_b2_taking_a_pattern_back_replaces_the_planned_sweep_by_one_from_the_start(bug_run: dict[str, Any]) -> None:
    after_p12 = bug_run["jobs_after_p12"]
    after_p1 = bug_run["jobs_after_p1"]
    assert [j["fingerprint"] for j in after_p12] == [bug_run["fingerprint_p12"]]
    assert [(j["fingerprint"], j["storage"], j["cursor"]) for j in after_p1] == [(bug_run["fingerprint_p1"], 0, 0)]


@bug_instance
def test_b2_a_band_of_the_old_set_ends_without_successor_and_clears_nothing(bug_run: dict[str, Any]) -> None:
    planted = [
        j["id"] for j in bug_run["jobs_with_the_band_in_flight"] if j["fingerprint"] == bug_run["fingerprint_p12"]
    ]
    assert len(planted) == 1
    # cron.php may reach the planted band only in a later run; what must never
    # appear is a successor, a job of the old set with another id.
    for run in bug_run["jobs_per_cron_run_b2"]:
        assert all(j["id"] in planted for j in run if j["fingerprint"] == bug_run["fingerprint_p12"]), run
    assert bug_run["jobs_per_cron_run_b2"][-1] == []
    assert bug_run["queue_after_b2"]["S2"] == []
    assert bug_run["hits_after_b2"] == {"zyrpaxa": 0, "zyrpbeo": 1, "zyrpcia": 1, "zyrkelo": 1}


@bug_instance
def test_b2_an_empty_set_plans_no_sweep(bug_run: dict[str, Any]) -> None:
    assert bug_run["save_empty"] == 200
    assert bug_run["jobs_after_empty"] == []


@bug_instance
def test_b3_two_quick_saves_leave_one_sweep_for_the_stored_set(bug_run: dict[str, Any]) -> None:
    assert [j["fingerprint"] for j in bug_run["jobs_after_two_saves"]] == [bug_run["fingerprint_p6"]]
    assert bug_run["stored_after_race"] == ["*.pat6"]
    assert bug_run["hits_after_b3"] == {"zyrpbeo": 1, "zyrpcia": 0}


RACE_ROUNDS = 30


@instance
def test_b3_two_saves_at_the_same_moment_leave_one_sweep_for_the_stored_set() -> None:
    """Two admins press save at once: one sweep, the one of the set that was stored."""
    base_session, base_token = client("admin", ADMIN_PASS)
    with closing(base_session):
        rules = base_session.get(OVERVIEW, headers={"requesttoken": base_token}).json()["rules"]
    fields = {k: rules[k] for k in ("maxFileBytes", "indexTeamFolders", "indexExternalStorage")}
    sessions = [client("admin", ADMIN_PASS) for _ in range(2)]
    rounds = []
    try:
        for number in range(RACE_ROUNDS):
            sets = [["*.race2", f"*.round{number}"], ["*.race6", f"*.round{number}"]]
            gate = threading.Barrier(2)
            status: dict[int, int] = {}

            def racer(index: int, patterns: list[str], gate: threading.Barrier, status: dict[int, int]) -> None:
                session, token = sessions[index]
                body = {"exclusions": ["Archiv"], "exclusionPatterns": patterns, **fields}
                gate.wait()
                status[index] = session.post(SAVE, json=body, headers={"requesttoken": token}).status_code

            threads = [threading.Thread(target=racer, args=(i, sets[i], gate, status)) for i in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            stored = json.loads(occ("config:app:get", "findling", "exclusion_patterns").stdout or "[]")
            jobs = sweep_jobs()
            rounds.append({"status": status, "stored": stored, "jobs": [j["fingerprint"] for j in jobs]})
            _cron_until_gone(SWEEP)
    finally:
        session, token = sessions[0]
        session.post(
            SAVE, json={"exclusions": ["Archiv"], "exclusionPatterns": [], **fields}, headers={"requesttoken": token}
        )
        for session, _token in sessions:
            session.close()
        occ("config:app:delete", "findling", "exclusion_patterns")
        _cron_until_gone(SWEEP)
    _write_out("b3_race.json", rounds)
    # The sweep of the stored set is planned. A second job of the losing set may
    # stand next to it (two of six rounds in the first run): it carries another
    # fingerprint and ends at its first check without clearing (PE-10, shown on
    # the instance by B2), so one run works to the end.
    for entry in rounds:
        assert all(code == 200 for code in entry["status"].values()), entry
        assert entry["jobs"].count(fingerprint(entry["stored"])) == 1, entry
        assert len(entry["jobs"]) <= 2, entry


@bug_instance
def test_b4_a_prefix_and_a_pattern_over_one_file_give_one_delete_and_no_error(bug_run: dict[str, Any]) -> None:
    assert bug_run["verdict_d_before"] == [["skipped", "no_text_layer"]]
    assert len(bug_run["queue_d_after_one_cron"]) <= 1
    assert all(row[0] == "delete" for row in bug_run["queue_d_after_one_cron"])
    assert bug_run["verdict_d_after"] == []
    assert bug_run["errors_b4"] == []
    assert bug_run["hits_after_b4"] == {"zyrdumo": 0, "zyrkelo": 1}


@bug_instance
def test_b5_a_verdict_of_a_file_the_container_never_knew_goes_with_the_reconcile(bug_run: dict[str, Any]) -> None:
    assert bug_run["queue_v"] == []
    assert bug_run["verdict_v_before"] == [["skipped", "no_text_layer"]]
    assert bug_run["reconcile_line"]
    assert bug_run["verdict_v_after"] == []


@bug_instance
def test_b1_a_folder_renamed_under_a_pattern_leaves_the_index_with_the_reconcile(bug_run: dict[str, Any]) -> None:
    assert bug_run["move"] == 201
    assert bug_run["hits_r_before_rename"] == 1
    assert bug_run["reconcile_line"]
    assert bug_run["hits_after_reconcile"]["zyrnoka"] == 0
    assert bug_run["hits_after_reconcile"]["zyrkelo"] == 1


@bug_instance
def test_b1_a_pattern_taken_back_brings_its_files_back_with_the_reconcile(bug_run: dict[str, Any]) -> None:
    assert bug_run["hits_after_reconcile"]["zyrpaxa"] == 1


@bug_instance
def test_the_scenario_left_the_instance_as_it_found_it(bug_run: dict[str, Any]) -> None:
    assert bug_run["end"]["exclusions"] == '["Archiv"]'
    assert bug_run["end"]["patterns_exit"] == 1
    assert all("ExclusionSweepJob" not in j and "SubtreeExpandJob" not in j for j in bug_run["end"]["jobs"])


# B8: the link of the limit block (PE-8). The tag answers 404 until v1.5.0 is
# tagged, so only the shape of the URL is checked, and the anchor is checked in
# the documentation of the repository and, with network, on blob/main.

LIMITS_URL = "https://github.com/street1983nk/nextcloud-search/blob/v1.5.0/docs/admin-page.md#limits-per-file"
LIMITS_ANCHOR = '<a id="limits-per-file"></a>'


def test_b8_the_limit_block_links_exactly_the_tag_url_of_pe8_and_the_anchor_exists() -> None:
    template = (REPO / "php" / "templates" / "admin.php").read_text(encoding="utf-8")
    docs = (REPO / "docs" / "admin-page.md").read_text(encoding="utf-8")
    links = [part.split("'")[0] for part in template.split("'https://github.com/")[1:]]
    assert ["https://github.com/" + link for link in links].count(LIMITS_URL) == 1
    assert template.count("limits-per-file") == 1
    assert docs.count(LIMITS_ANCHOR) == 1
    heading = docs.split(LIMITS_ANCHOR, 1)[1].lstrip().splitlines()[0]
    assert heading.startswith("## ")
    assert LIMITS_URL.isascii()


@pytest.mark.skipif(
    not os.environ.get("FINDLING_AUDIT33_NETWORK"), reason="no network probe (FINDLING_AUDIT33_NETWORK)"
)
def test_b8_the_anchor_answers_on_blob_main() -> None:
    page = httpx.get(
        "https://github.com/street1983nk/nextcloud-search/blob/main/docs/admin-page.md",
        timeout=60,
        follow_redirects=True,
    )
    _write_out("b8_link.json", {"status": page.status_code, "anchor": page.text.count("limits-per-file")})
    assert page.status_code == 200
    assert "limits-per-file" in page.text
