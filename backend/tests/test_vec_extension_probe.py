"""Wave 0 of phase 6: the two five minute probes that a schema decision hangs on.

Two questions from the assumptions log of 06-RESEARCH.md, both cheap to answer
now and expensive to answer after a vector schema exists.

**A13, and it is a gate.** Does the CPython build inside the image allow
loadable SQLite extensions? sqlite-vec is one, so a "no" here means the image
needs a Python translation of its own, and that is a decision about the image
and not a line of code. Two different findings hide behind one question and are
reported separately, because they have different answers: the ``sqlite3``
connection may not carry ``enable_load_extension`` at all (the interpreter was
built without ``--enable-loadable-sqlite-extensions``), or it may carry it and
the load may still fail (the file is missing, is not a shared object, or was
built for another architecture). This is the one gate in this file: without a
loadable extension the phase is not buildable, so the test is allowed to be red.

**A12, and it is a measurement, not a gate.** Does a vec0 KNN query run under
``PRAGMA query_only = 1``? The read side of ``store/repo.py`` sets that pragma
(``_connect``, read_only branch) and it is the structural half of the read/write
split: a bug in the search path cannot change the operating state, whatever it
tries. vec0 keeps shadow tables and may want a temporary write, so the answer is
genuinely open. The test is green **either way** and records what happened,
because the point is the fact and not a verdict:

- runs: the read side keeps its pragma and plan 06-04 changes nothing.
- refuses: plan 06-04 has to open the vector store on a connection without
  ``query_only``, and the exact error is what tells it which weaker guard is
  still available. So the message class is captured rather than swallowed.

**Nothing real is touched.** The vectors are derived from a fixed seed with
SHA-256 in counter mode, the same construction ``scripts/dev/build_corpus.py``
uses and for the same reason: an int8 vector is 384 arbitrary bytes, so no text
has to exist for this probe to run. Nothing but numbers, paths and the sqlite
error class is printed (T-02-14, T-06-05).

**Two ways to run it, on purpose.** As a test file it runs next to the other
unit tests, against the extension of the local virtual environment. As a plain
script it runs inside the built image, where ``FINDLING_VEC0_PATH`` points at
the copy the Dockerfile placed at a fixed path and where pytest is deliberately
not installed:

    cd backend && uv run python -m pytest tests/test_vec_extension_probe.py -q -s

    docker run --rm --network none \\
        -v "$PWD/backend/tests:/probe:ro" findling-sem-probe:local \\
        python /probe/test_vec_extension_probe.py
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path

# 384 is the dimension of intfloat/multilingual-e5-small and the width the
# vector table of plan 06-04 is proposed with. The count is small on purpose:
# this probe answers whether the query runs, never how fast it is.
DIMENSIONS = 384
VECTOR_COUNT = 512
NEIGHBOURS = 5
SEED = "phase6-welle0"


@dataclass(frozen=True)
class LoadResult:
    """The answer to A13, with the two failure modes kept apart."""

    path: str
    has_api: bool
    loaded: bool
    version: str | None
    error: str | None


@dataclass(frozen=True)
class QueryOnlyResult:
    """The answer to A12. ``ran`` is the fact; neither value is a verdict."""

    ran: bool
    neighbours: int
    error_class: str | None
    error: str | None


def vector(index: int) -> bytes:
    """One deterministic int8 vector of ``DIMENSIONS`` bytes.

    SHA-256 in counter mode rather than the standard library generator: the
    bytes have to be the same on every machine and in every year, and an int8
    vector is raw bytes to sqlite-vec, so no float conversion is involved.
    """
    raw = b""
    counter = 0
    while len(raw) < DIMENSIONS:
        raw += hashlib.sha256(f"{SEED}:{index}:{counter}".encode()).digest()
        counter += 1
    return raw[:DIMENSIONS]


def extension_path() -> str:
    """Where the vec0 extension is, and the reason for the order of the two answers.

    In the image the path is a constant of the image and arrives as
    ``FINDLING_VEC0_PATH``: that is the value the running application will use,
    so that is the value the probe has to judge. Outside the image there is no
    such constant, and the extension of the installed wheel is asked for
    instead, so this file is not a test that quietly does nothing on a
    developer machine.
    """
    from_env = os.environ.get("FINDLING_VEC0_PATH")
    if from_env:
        return from_env

    import sqlite_vec

    suffix = ".dll" if sys.platform == "win32" else ".so"
    return sqlite_vec.loadable_path() + suffix


def probe_loadable_extensions(path: str) -> LoadResult:
    """A13. Is the extension loadable in this interpreter, and does it load?"""
    connection = sqlite3.connect(":memory:")
    try:
        if not hasattr(connection, "enable_load_extension"):
            return LoadResult(path, has_api=False, loaded=False, version=None, error=None)
        try:
            connection.enable_load_extension(True)
            connection.load_extension(path)
            connection.enable_load_extension(False)
        except (AttributeError, sqlite3.Error) as error:
            # AttributeError covers the build where the attribute exists but the
            # call is refused, which is a different finding from a missing file.
            return LoadResult(path, has_api=True, loaded=False, version=None, error=f"{type(error).__name__}: {error}")
        row = connection.execute("SELECT vec_version()").fetchone()
        return LoadResult(path, has_api=True, loaded=True, version=str(row[0]), error=None)
    finally:
        connection.close()


def _fill(database: Path, path: str) -> None:
    """Write the vector table on a connection that is allowed to write."""
    connection = sqlite3.connect(database)
    try:
        connection.enable_load_extension(True)
        connection.load_extension(path)
        connection.enable_load_extension(False)
        connection.execute(f"CREATE VIRTUAL TABLE chunk_vectors USING vec0(embedding int8[{DIMENSIONS}])")
        with connection:
            # vec_int8() and not a plain parameter. A blob handed to an int8
            # column without it is read as float32 and rejected, which is a
            # finding worth writing down here rather than rediscovering in plan
            # 06-04: sqlite-vec does not infer the element type from the column
            # declaration, it wants the blob marked at the call site.
            connection.executemany(
                "INSERT INTO chunk_vectors(rowid, embedding) VALUES (?, vec_int8(?))",
                [(index + 1, vector(index)) for index in range(VECTOR_COUNT)],
            )
    finally:
        connection.close()


def probe_knn_under_query_only(database: Path, path: str) -> QueryOnlyResult:
    """A12. Reopen the written file the way the read side does, then ask for neighbours.

    The pragma order is the order the read side will have to use: the extension
    is loaded first, because loading is itself a write to the connection state,
    and ``query_only`` is set afterwards, exactly as ``repo.py::_connect`` sets
    it after the other pragmas.
    """
    connection = sqlite3.connect(database)
    try:
        connection.enable_load_extension(True)
        connection.load_extension(path)
        connection.enable_load_extension(False)
        connection.execute("PRAGMA query_only = 1")
        try:
            rows = connection.execute(
                "SELECT rowid, distance FROM chunk_vectors WHERE embedding MATCH vec_int8(?) AND k = ?",
                (vector(0), NEIGHBOURS),
            ).fetchall()
        except sqlite3.Error as error:
            return QueryOnlyResult(
                ran=False,
                neighbours=0,
                error_class=type(error).__name__,
                error=str(error),
            )
        return QueryOnlyResult(ran=True, neighbours=len(rows), error_class=None, error=None)
    finally:
        connection.close()


def report(load: LoadResult, query_only: QueryOnlyResult | None) -> list[str]:
    """The record both callers print. Numbers, paths and error classes only."""
    lines = [
        f"python           {sys.version.split()[0]}",
        f"platform         {sysconfig.get_platform()}",
        f"sqlite           {sqlite3.sqlite_version}",
        f"vec0 path        {load.path}",
        f"A13 has api      {load.has_api}",
        f"A13 loaded       {load.loaded}",
        f"A13 vec_version  {load.version}",
        f"A13 error        {load.error}",
    ]
    if query_only is None:
        lines.append("A12 not measured in this run")
        return lines
    lines += [
        f"A12 knn ran      {query_only.ran}",
        f"A12 neighbours   {query_only.neighbours}",
        f"A12 error class  {query_only.error_class}",
        f"A12 error        {query_only.error}",
    ]
    return lines


# -- the tests -------------------------------------------------------------


def test_the_extension_loads(tmp_path: Path) -> None:
    # The one gate of this file. Everything else in phase 6 is unbuildable if
    # this is red, so it is allowed to be red and nothing else here is.
    load = probe_loadable_extensions(extension_path())
    for line in report(load, None):
        print(line)

    assert load.has_api, f"this CPython has no enable_load_extension: {load.path}"
    assert load.loaded, f"the extension at {load.path} did not load: {load.error}"
    assert load.version is not None

    # tmp_path is asked for here as well so that a broken fixture cannot make
    # the whole file silently collect nothing.
    assert tmp_path.is_dir()


def test_a_path_that_is_not_an_extension_is_reported(tmp_path: Path) -> None:
    # The anti vacuity clause: the probe above proves something only if it can
    # tell a loadable file from an unloadable one. A file of the right name and
    # the wrong content has to come back as a finding, not as a pass.
    decoy = tmp_path / "vec0.so"
    decoy.write_bytes(b"this is not a shared object")

    load = probe_loadable_extensions(str(decoy))

    assert load.has_api
    assert not load.loaded
    assert load.error is not None


def test_knn_under_query_only_is_recorded(tmp_path: Path) -> None:
    # A12, and deliberately not a gate. Both outcomes are green; the run log is
    # where the answer lives, and docs/measurements/2026-09-05-welle0-proben/
    # is where it is written down.
    path = extension_path()
    database = tmp_path / "probe.db"
    _fill(database, path)

    result = probe_knn_under_query_only(database, path)
    for line in report(probe_loadable_extensions(path), result):
        print(line)

    if result.ran:
        assert result.neighbours == NEIGHBOURS
    else:
        # The message class is what plan 06-04 derives its connection decision
        # from, so an empty one would make a negative answer useless.
        assert result.error_class is not None
        assert result.error


def main() -> int:
    """The script form, for the image, where pytest is not installed."""
    path = extension_path()
    load = probe_loadable_extensions(path)
    query_only = None
    if load.loaded:
        database = Path(os.environ.get("TMPDIR", "/tmp")) / "vec0_probe.db"  # noqa: S108
        database.unlink(missing_ok=True)
        try:
            _fill(database, path)
            query_only = probe_knn_under_query_only(database, path)
        finally:
            database.unlink(missing_ok=True)
    for line in report(load, query_only):
        print(line)
    if not load.loaded:
        print("A13 is negative: the image cannot load sqlite-vec", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
