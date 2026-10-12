#!/usr/bin/env python3
"""The corresponding source of the GPL and LGPL libraries in the backend image.

Why this file exists. Since plan 31-01 the backend image carries pillow-heif,
and its manylinux wheels bundle three native libraries as binaries: x265
(GPL-2.0-or-later), libheif and libde265 (both LGPL-3.0). Whoever distributes
those binaries has to offer the complete corresponding source, including the
scripts that control the build. A pointer to an upstream tag does not hold that
promise for long: tags move, download pages disappear, and the offer has to
outlive both. So the exact archives the wheels were built from are named here
with their SHA-256, and every release mirrors them as assets.

The four archives:

- the pillow-heif sdist of the pinned version, because it carries
  ``libheif/build_libs.py``, the build recipe the upstream wheel workflow runs
  as ``CIBW_BEFORE_ALL_LINUX`` and which names the three archives below;
- x265, libde265 and libheif in exactly the versions that recipe downloads and
  that ``LICENSES_bundled.txt`` of the wheel names.

THIRD-PARTY.md carries the same four rows in the table "Corresponding source of
the native libraries in the image", and backend/tests/test_corresponding_source.py
holds the table and ``ARCHIVES`` to each other and the pillow-heif row to the
pin in backend/pyproject.toml.

Usage, from the root of the repository (stdlib only, any Python 3.13):

    python scripts/release/corresponding_source.py fetch dist/source
    python scripts/release/corresponding_source.py --verify-only dist/source
    python scripts/release/corresponding_source.py publish --tag source-1.5-dev.2 \\
        --source-dir dist/source [--dry-run]

``fetch`` downloads every archive that is missing or wrong, checks its SHA-256
and refuses to keep a file that does not match. ``--verify-only`` checks a
directory that already holds the archives and touches nothing; ``--expect
NAME=SHA256`` replaces the list it checks, which is how the test exercises it
without a network. ``publish`` creates a GitHub pre-release for the tag if there
is none (never marked latest), with exactly the four archives in the create
call, because this repository publishes immutable releases and a published
release takes no further asset. An existing draft or mutable release gets the
four with ``--clobber``; a published immutable one is refused. ``publish`` also
refuses a tag of the form vMAJOR.MINOR.PATCH: those are the store releases,
which release.yml creates. They are immutable too, so the four archives have to
be in the create call of release.yml itself; that change belongs to REL-05
(docs/store-listing.md, release checklist v1.5.0).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import NamedTuple

REPOSITORY = "street1983nk/nextcloud-search"
IMAGE = "ghcr.io/street1983nk/findling_backend:dev"
TITLE = "Source mirror: corresponding source for the dev image"

# The tags the store releases use, and the only tags the workflows start on.
RELEASE_TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+")
SHA256 = re.compile(r"[0-9a-f]{64}")
CHUNK = 1 << 16
TIMEOUT_SECONDS = 120


class Archive(NamedTuple):
    project: str
    name: str
    version: str
    url: str
    sha256: str
    licence: str


ARCHIVES: tuple[Archive, ...] = (
    Archive(
        project="pillow-heif",
        name="pillow_heif-1.8.0.tar.gz",
        version="1.8.0",
        url="https://files.pythonhosted.org/packages/source/p/pillow_heif/pillow_heif-1.8.0.tar.gz",
        sha256="e47c27432c6fd3d66c22f0de9f27fd379383b646c947520bc485854ce72060d0",
        licence="BSD-3-Clause",
    ),
    Archive(
        project="x265",
        name="x265_4.2.tar.gz",
        version="4.2",
        url="https://bitbucket.org/multicoreware/x265_git/downloads/x265_4.2.tar.gz",
        sha256="40b1ea0453e0309f0eba934e0ddf533f8f6295966679e8894e8f1c1c8d5e1210",
        licence="GPL-2.0-or-later",
    ),
    Archive(
        project="libde265",
        name="libde265-1.1.3.tar.gz",
        version="1.1.3",
        url="https://github.com/strukturag/libde265/releases/download/v1.1.3/libde265-1.1.3.tar.gz",
        sha256="554228bd17788c99a7e63b37ab5634722190e6e2bf60c1dcb01cef328e133905",
        licence="LGPL-3.0",
    ),
    Archive(
        project="libheif",
        name="libheif-1.23.4.tar.gz",
        version="1.23.4",
        url="https://github.com/strukturag/libheif/releases/download/v1.23.4/libheif-1.23.4.tar.gz",
        sha256="d0c02b4b0e978f34a1974b6f3eea7975a537bf7a9195ffeea38e7242ff316fdd",
        licence="LGPL-3.0",
    ),
)


class Expected(NamedTuple):
    name: str
    sha256: str


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def verify(directory: Path, expected: list[Expected]) -> list[str]:
    """Return one line per archive that is missing or does not match, and per entry nobody expects.

    The directory is the mirror, so it holds the expected archives and nothing
    else: a foreign file beside them is a problem too, even though publish would
    upload only the expected names (security audit 31-15, L-31-03).
    """
    problems: list[str] = []
    for item in expected:
        path = directory / item.name
        if not path.is_file():
            problems.append(f"missing: {item.name}")
            continue
        actual = sha256_of(path)
        if actual != item.sha256:
            problems.append(f"sha256 mismatch: {item.name} is {actual}, expected {item.sha256}")
    wanted = {item.name for item in expected}
    if directory.is_dir():
        problems += [f"unexpected: {entry.name}" for entry in sorted(directory.iterdir()) if entry.name not in wanted]
    return problems


def _download(url: str, target: Path) -> None:
    if not url.startswith("https://"):
        raise ValueError(f"refusing a download that is not https: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "findling-corresponding-source"})  # noqa: S310 - https only, checked above
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response, target.open("wb") as out:  # noqa: S310 - https only, checked above
        while chunk := response.read(CHUNK):
            out.write(chunk)


def fetch(directory: Path) -> list[str]:
    """Download every archive that is missing or wrong; return the problems left."""
    directory.mkdir(parents=True, exist_ok=True)
    for archive in ARCHIVES:
        path = directory / archive.name
        if path.is_file() and sha256_of(path) == archive.sha256:
            print(f"ok (present) {archive.name} {archive.sha256}")
            continue
        with tempfile.NamedTemporaryFile(dir=directory, prefix=".part-", delete=False) as handle:
            part = Path(handle.name)
        try:
            _download(archive.url, part)
            actual = sha256_of(part)
            if actual != archive.sha256:
                print(f"REFUSED {archive.name}: sha256 {actual}, expected {archive.sha256}", file=sys.stderr)
                continue
            part.replace(path)
            print(f"ok (fetched) {archive.name} {actual}")
        finally:
            part.unlink(missing_ok=True)
    return verify(directory, [Expected(a.name, a.sha256) for a in ARCHIVES])


def release_notes() -> str:
    """The body of the source mirror release: a short English list of facts."""
    lines = [f"Corresponding source for the GPL and LGPL binaries in {IMAGE}.", ""]
    lines += [f"- {a.project} {a.version} ({a.name}, {a.licence}): sha256 {a.sha256}" for a in ARCHIVES]
    lines += ["", "Licences and details: THIRD-PARTY.md"]
    return "\n".join(lines) + "\n"


def publish_commands(tag: str, directory: Path, *, release_exists: bool, target: str) -> list[list[str]]:
    """The gh calls that put exactly the four archives on the release of ``tag``.

    This repository publishes immutable releases: once a release is published,
    no asset can be added to it. So a new release gets the archives in its
    create call, and gh then creates a draft, uploads and publishes last. An
    existing release can only take an upload while it is a draft or mutable;
    ``main`` refuses an immutable one before it gets here.
    """
    if RELEASE_TAG.fullmatch(tag):
        raise ValueError(f"refusing {tag}: a vMAJOR.MINOR.PATCH tag is a store release, see REL-05")
    files = [str(directory / a.name) for a in ARCHIVES]
    if release_exists:
        return [["gh", "release", "upload", tag, *files, "--repo", REPOSITORY, "--clobber"]]
    return [
        [
            "gh", "release", "create", tag, *files,
            "--repo", REPOSITORY,
            "--target", target,
            "--prerelease",
            "--latest=false",
            "--title", TITLE,
            "--notes", release_notes(),
        ]
    ]  # fmt: skip


def _release_state(tag: str) -> dict[str, object] | None:
    """None when there is no release for ``tag``, its JSON view otherwise."""
    result = subprocess.run(  # noqa: S603 - fixed argument list, tag validated by the caller
        ["gh", "release", "view", tag, "--repo", REPOSITORY, "--json", "tagName,isImmutable,isDraft"],  # noqa: S607 - gh from PATH by design
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    state = json.loads(result.stdout)
    if not isinstance(state, dict):
        raise TypeError(f"gh release view returned {type(state).__name__}, not an object")
    return state


def _parse_expect(values: list[str]) -> list[Expected]:
    expected: list[Expected] = []
    for value in values:
        name, _, digest = value.partition("=")
        if not name or not SHA256.fullmatch(digest):
            raise SystemExit(f"--expect wants NAME=SHA256 with 64 lowercase hex characters, got {value!r}")
        # A plain file name inside the checked directory, never a path out of it (L-31-03).
        if name in (".", "..") or Path(name).name != name or "/" in name or "\\" in name:
            raise SystemExit(f"--expect wants a plain file name, got {name!r}")
        expected.append(Expected(name, digest))
    return expected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verify-only", metavar="DIR", type=Path, help="check the archives in DIR and touch nothing")
    parser.add_argument("--expect", action="append", default=[], metavar="NAME=SHA256", help="check these instead")
    commands = parser.add_subparsers(dest="command")
    fetch_parser = commands.add_parser("fetch", help="download and check the archives into DIR")
    fetch_parser.add_argument("directory", type=Path)
    publish_parser = commands.add_parser("publish", help="mirror the archives as assets of a pre-release")
    publish_parser.add_argument("--tag", required=True)
    publish_parser.add_argument("--source-dir", type=Path, default=Path("dist/source"))
    publish_parser.add_argument("--target", default="main", help="commit or branch a new tag points at")
    publish_parser.add_argument("--dry-run", action="store_true", help="print the gh calls as JSON and run nothing")
    args = parser.parse_args(argv)

    if args.verify_only is not None:
        expected = _parse_expect(args.expect) or [Expected(a.name, a.sha256) for a in ARCHIVES]
        problems = verify(args.verify_only, expected)
        for item in expected:
            if not any(item.name in problem for problem in problems):
                print(f"ok {item.name} {item.sha256}")
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0

    if args.command == "fetch":
        problems = fetch(args.directory)
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1 if problems else 0

    if args.command == "publish":
        if RELEASE_TAG.fullmatch(args.tag):
            print(f"refusing {args.tag}: a vMAJOR.MINOR.PATCH tag is a store release, see REL-05", file=sys.stderr)
            return 2
        if args.dry_run:
            for command in publish_commands(args.tag, args.source_dir, release_exists=False, target=args.target):
                print(json.dumps(command))
            return 0
        problems = fetch(args.source_dir)
        if problems:
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
        state = _release_state(args.tag)
        if state is not None and state.get("isImmutable") and not state.get("isDraft"):
            print(
                f"refusing {args.tag}: the release is published and immutable, no asset can be added; "
                "a mirror needs a new tag",
                file=sys.stderr,
            )
            return 1
        for command in publish_commands(
            args.tag, args.source_dir, release_exists=state is not None, target=args.target
        ):
            print("running: " + " ".join(command[:4]))
            subprocess.run(command, check=True)  # noqa: S603 - fixed gh argument list built above
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
