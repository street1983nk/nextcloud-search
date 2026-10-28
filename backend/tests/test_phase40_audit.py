"""Probes of the launch audit 1.6.0 (plan 40-01) over the changes v1.5.1..HEAD.

The report with the commands, the results and the decision on every finding is
``.planning/phases/40-haertung-und-store-einreichung-1-6-0/40-AUDIT.md``. This
module keeps the probes that a checkout can run on its own, one block per
section of that report, and a probe that showed a finding names it by its id.

The probes deliberately take another road than the tests of the building plans
(test_status_leave_out.py, test_harp_connect_supervisor.py): the statements are
read off a trace callback instead of the source, the read only promise is
tested by handing the function a write instead of reading its pragmas, the
watcher is fed hostile lines through a stub of its own, and the idle loop is
counted through a sha256sum that stands first on PATH.

The watcher probes need bash, a FIFO and POSIX signals, so they run on Linux
only, in the gates job of python.yml; on Windows they are skipped.

Only ASCII in this file, like the other audit modules.
"""

from __future__ import annotations

import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from findling.api import status
from findling.extract import archive as archive_module
from findling.store import repo
from findling.store.repo import FileMeta, embedded_in_storages, open_read_only, open_store
from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

REPO = Path(__file__).resolve().parents[2]
BACKEND = REPO / "backend"
WATCHER = BACKEND / "docker" / "harp_connect.sh"
BACKEND_INFO = BACKEND / "appinfo" / "info.xml"
ADMIN_JS = REPO / "php" / "js" / "admin.js"
ADMIN_TEMPLATE = REPO / "php" / "templates" / "admin.php"
PHP_LIB = REPO / "php" / "lib"
ADMIN_VIEW = PHP_LIB / "Service" / "AdminViewService.php"
WORKFLOWS = REPO / ".github" / "workflows"
UV_LOCK = BACKEND / "uv.lock"

Sign = Callable[[str], dict[str, str]]

_ON_LINUX_WITH_BASH = pytest.mark.skipif(
    sys.platform == "win32" or any(shutil.which(tool) is None for tool in ("bash", "mkfifo", "sha256sum")),
    reason="the watcher needs bash, a FIFO and POSIX signals; it runs in the gates job of python.yml",
)


# -- fixtures of the counting probes -------------------------------------------------


def _meta(storage_id: int, file_id: int) -> FileMeta:
    return FileMeta(
        storage_id=storage_id,
        root_id=storage_id,
        path=f"/Probe/probe-{file_id}.pdf",
        title=f"probe-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000 + file_id,
    )


def _state(root: Path) -> None:
    """Storages 1, 2 and 3; storage 2 holds two living indexed documents.

    Storage 2 also holds a skipped file (23) and a tombstoned indexed one (24),
    and storages 1 and 3 hold one indexed document each: none of them may count
    for leaveOut=2.
    """
    store = open_store(root / "state.db")
    try:
        for storage_id, file_id in ((1, 11), (2, 21), (2, 22), (2, 24), (3, 31)):
            store.record(file_id, _meta(storage_id, file_id), "indexed")
        store.record(23, _meta(2, 23), "skipped", "too_large")
        store.tombstone(24)
    finally:
        store.close()


def _vectors(root: Path, file_ids: list[int]) -> None:
    stock = open_vectors(root / "vectors.db")
    try:
        for file_id in file_ids:
            stock.replace_chunks(
                file_id,
                [Chunk(ordinal=0, char_start=0, char_end=10, embedding=bytes(EMBEDDING_DIMENSIONS))],
            )
    finally:
        stock.close()


@pytest.fixture
def no_report(monkeypatch: pytest.MonkeyPatch) -> list[object]:
    """Replace report() by a recorder: a refused parameter must reach no statement."""
    calls: list[object] = []

    def recorder(*args: object) -> status.StatusResponse:
        calls.append(args)
        raise AssertionError("report() ran for a parameter that should have been refused")

    monkeypatch.setattr(status, "report", recorder)
    return calls


# == S1 the parameter leaveOut =======================================================

_REFUSED = {
    "the empty string": "",
    "a trailing comma": "1,",
    "a leading comma": ",1",
    "an empty item": "1,,2",
    "a leading blank": " 1",
    "a trailing blank": "1 ",
    "a minus sign": "-1",
    "a plus sign": "+1",
    "a hex literal": "0x1",
    "a full width digit": chr(0xFF11),
    "an arabic indic digit": chr(0x0663),
    "a trailing newline": "1\n",
    "nineteen digits": "9" * 19,
    "1001 ids": ",".join(str(storage_id) for storage_id in range(1, 1002)),
    "8001 characters": "1" * 8001,
}


@pytest.mark.usefixtures("appapi_environment")
@pytest.mark.parametrize("value", list(_REFUSED.values()), ids=list(_REFUSED))
def test_s1_every_malformed_leave_out_is_a_422_before_any_statement(
    client: TestClient,
    sign: Sign,
    volume: Path,
    no_report: list[object],
    value: str,
) -> None:
    _state(volume)

    response = client.get("/status", params={"leaveOut": value}, headers=sign("admin"))

    assert response.status_code == 422, response.text
    assert no_report == []


def test_s1_the_probe_list_holds_the_fifteen_values_of_the_plan() -> None:
    assert len(_REFUSED) == 15


@pytest.mark.usefixtures("appapi_environment")
def test_s1_without_the_parameter_neither_counter_is_on_the_wire(client: TestClient, sign: Sign, volume: Path) -> None:
    _state(volume)
    _vectors(volume, [21])

    answer = client.get("/status", headers=sign("admin")).json()

    assert "indexedLeftOut" not in answer
    assert "embeddedLeftOut" not in answer


@pytest.mark.usefixtures("appapi_environment")
def test_s1_a_repeated_id_counts_once(client: TestClient, sign: Sign, volume: Path) -> None:
    _state(volume)
    _vectors(volume, [21, 22])

    once = client.get("/status", params={"leaveOut": "2"}, headers=sign("admin")).json()
    thrice = client.get("/status", params={"leaveOut": "2,2,2"}, headers=sign("admin")).json()

    assert (once["indexedLeftOut"], once["embeddedLeftOut"]) == (2, 2)
    assert (thrice["indexedLeftOut"], thrice["embeddedLeftOut"]) == (2, 2)


@pytest.mark.usefixtures("appapi_environment")
@pytest.mark.parametrize("value", ["01", "1,02", "00", "0" + "9" * 17])
def test_s1_f_40_01_only_canonical_numbers_are_taken(client: TestClient, sign: Sign, volume: Path, value: str) -> None:
    """F-40-01, fixed: a leading zero is a 422 (strict xfail before the fix).

    Lesson L-36-02: a route at a trust boundary answers the question that was
    asked and no other. "01" is not the storage id 1 as PHP writes it.
    """
    _state(volume)

    response = client.get("/status", params={"leaveOut": value}, headers=sign("admin"))

    assert response.status_code == 422, response.text


@pytest.mark.usefixtures("appapi_environment")
@pytest.mark.parametrize("value", ["0", "1", "10", "1,20,300", "9" * 18, "100000000000000000"])
def test_s1_f_40_01_canonical_numbers_are_still_taken(client: TestClient, sign: Sign, volume: Path, value: str) -> None:
    # The positive control of the fix: every form the page writes still passes.
    _state(volume)

    response = client.get("/status", params={"leaveOut": value}, headers=sign("admin"))

    assert response.status_code == 200, response.text
    assert "indexedLeftOut" in response.json()


@pytest.mark.usefixtures("appapi_environment")
def test_s1_a_thousand_ids_of_eight_digits_are_past_the_length_ceiling(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # The page caps the count at 1000 ids (AdminViewService::LEAVE_OUT_MAX_IDS);
    # the container caps the length at 8000 characters as well. 1000 ids of
    # eight digits are within the first and beyond the second, and the 422 that
    # follows is what the page reads as "backend not reachable".
    _state(volume)
    value = ",".join(str(10_000_000 + offset) for offset in range(1000))
    assert len(value) > status.LEAVE_OUT_MAX_LENGTH

    response = client.get("/status", params={"leaveOut": value}, headers=sign("admin"))

    assert response.status_code == 422


def _php_function(source: str, name: str) -> str:
    start = source.index(f"function {name}(")
    following = source.find("\n\tpublic ", start + 1)
    following_private = source.find("\n\tprivate ", start + 1)
    ends = [end for end in (following, following_private) if end != -1]
    return source[start : min(ends)] if ends else source[start:]


@pytest.mark.xfail(strict=True, reason="F-40-04: the page names up to 1000 ids without the ceiling of 8000 characters")
def test_s1_f_40_04_the_page_holds_the_length_ceiling_of_the_route_too() -> None:
    source = ADMIN_VIEW.read_text(encoding="utf-8")

    assert f"public const LEAVE_OUT_MAX_LENGTH = {status.LEAVE_OUT_MAX_LENGTH};" in source
    body = _php_function(source, "leaveOutParameters")
    assert "strlen(" in body
    assert "self::LEAVE_OUT_MAX_LENGTH" in body


def test_s1_the_status_route_is_admin_and_the_only_route_that_reaches_it() -> None:
    routes = ET.parse(BACKEND_INFO).getroot().findall("./external-app/routes/route")  # noqa: S314 - our own file
    reaching = [
        (route.findtext("url") or "", route.findtext("access_level") or "")
        for route in routes
        if re.search(route.findtext("url") or "$^", "/status")
    ]

    assert reaching == [("^/status$", "ADMIN")]


def test_s1_the_statements_carry_placeholders_and_never_an_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Read off the statements the real connections are handed, not off the
    # source. The trace callback of sqlite3 shows the SQL with the bound values
    # expanded, so the text is caught at execute() of a recording connection.
    _state(tmp_path)
    _vectors(tmp_path, [21, 22, 31])
    statements: list[str] = []
    original = sqlite3.connect

    class Recording(sqlite3.Connection):
        def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor:
            statements.append(sql)
            return super().execute(sql, parameters)

    def recording(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        return original(*args, **kwargs, factory=Recording)

    monkeypatch.setattr(sqlite3, "connect", recording)
    store = open_read_only(tmp_path / "state.db")
    try:
        assert store.indexed_in_storages([2, 987654321]) == 2
    finally:
        store.close()
    assert embedded_in_storages(tmp_path / "state.db", tmp_path / "vectors.db", [2, 987654321]) == 2

    counting = [statement for statement in statements if "COUNT(*)" in statement and "storage_id IN" in statement]
    assert len(counting) == 2
    for statement in counting:
        assert "987654321" not in statement
        assert "IN (?,?)" in statement


# == S1b both info.xml, the discussion link ==========================================


def test_s1b_no_code_path_fetches_the_discussion_url() -> None:
    roots = [BACKEND / "src", PHP_LIB, REPO / "php" / "js", REPO / "php" / "templates"]
    hits = [
        str(path.relative_to(REPO))
        for root in roots
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix in {".py", ".php", ".js"}
        and re.search(r"249775|help\.nextcloud\.com", path.read_text(encoding="utf-8", errors="replace"))
    ]

    assert hits == []


# == S2 the second read connection, ATTACH of vectors.db ============================


def test_s2_a_missing_vector_database_stays_missing(tmp_path: Path) -> None:
    _state(tmp_path)

    with pytest.raises(sqlite3.OperationalError):
        embedded_in_storages(tmp_path / "state.db", tmp_path / "vectors.db", [2])

    assert not (tmp_path / "vectors.db").exists()
    assert sorted(path.name for path in tmp_path.iterdir() if path.name.startswith("vectors")) == []


def test_s2_a_path_with_blank_hash_percent_and_question_mark_is_counted_right(tmp_path: Path) -> None:
    # A question mark cannot stand in a Windows file name; on Linux it is part
    # of the probe, and it is the character that would end the path of a URI.
    name = "probe dir #1 %20 100%" + ("" if sys.platform == "win32" else " what?mode=rw")
    root = tmp_path / name
    root.mkdir()
    _state(root)
    _vectors(root, [21, 31])

    assert embedded_in_storages(root / "state.db", root / "vectors.db", [2]) == 1
    assert embedded_in_storages(root / "state.db", root / "vectors.db", [2, 3]) == 2
    # Nothing was created next to the two files, under the cut name or elsewhere.
    assert sorted(path.name for path in tmp_path.iterdir()) == [name]


@pytest.mark.parametrize(
    "statement",
    [
        "DELETE FROM files WHERE storage_id IN ({placeholders})",
        "DELETE FROM vec.chunks WHERE file_id IN ({placeholders})",
        "UPDATE files SET state = 'failed' WHERE storage_id IN ({placeholders})",
    ],
    ids=["a delete on state.db", "a delete on vectors.db", "an update on state.db"],
)
def test_s2_a_write_over_the_connection_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    statement: str,
) -> None:
    _state(tmp_path)
    _vectors(tmp_path, [21, 22])
    before = embedded_in_storages(tmp_path / "state.db", tmp_path / "vectors.db", [2])
    monkeypatch.setattr(repo, "_EMBEDDED_IN_STORAGES_SQL", statement)

    with pytest.raises(sqlite3.OperationalError, match=r"readonly|read-only|query_only|attempt to write"):
        embedded_in_storages(tmp_path / "state.db", tmp_path / "vectors.db", [2])

    monkeypatch.undo()
    assert embedded_in_storages(tmp_path / "state.db", tmp_path / "vectors.db", [2]) == before == 2


@pytest.mark.parametrize("held", ["state.db", "vectors.db"])
def test_s2_a_parallel_writer_in_wal_neither_blocks_nor_leaks(tmp_path: Path, held: str) -> None:
    _state(tmp_path)
    _vectors(tmp_path, [21, 22])
    writer = sqlite3.connect(tmp_path / held, autocommit=True)
    try:
        assert str(writer.execute("PRAGMA journal_mode").fetchone()[0]).lower() == "wal"
        writer.execute("BEGIN IMMEDIATE")
        if held == "state.db":
            writer.execute("UPDATE files SET deleted_at = 1 WHERE storage_id = 2")
        else:
            writer.execute("DELETE FROM chunks")

        started = time.perf_counter()
        counted = embedded_in_storages(tmp_path / "state.db", tmp_path / "vectors.db", [2])
        elapsed = time.perf_counter() - started

        # The snapshot before the open write, and far inside the busy timeout.
        assert counted == 2
        assert elapsed < repo._BUSY_TIMEOUT_MS / 1000 / 2
        writer.execute("ROLLBACK")
    finally:
        writer.close()


def test_s2_the_route_takes_both_paths_from_the_settings_only() -> None:
    source = Path(status.__file__).read_text(encoding="utf-8")
    calls = re.findall(r"embedded_in_storages\(([^)]*)\)", source)

    assert calls == ["resolved.state_db, resolved.vectors_db, leave_out"]


# == S3 the tunnel watcher (Linux only) ===============================================

_X509 = (
    b"[W] [client/service.go:298] [5f1c2a9b] connect to server error: tls: failed to verify certificate: "
    b'x509: certificate signed by unknown authority (possibly because of "crypto/rsa: verification error")'
)
_PREFIX = b"[W] [client/service.go:298] [5f1c2a9b] connect to server error: "
_HOSTILE = [
    _PREFIX + b"$(touch pwned) x509: one",
    _PREFIX + b"`touch pwned_backtick` x509: two",
    _PREFIX + b"${IFS}$((1/0))${HP_SHARED_KEY} x509: three",
    _PREFIX + b"%s%n%x%d%%%c x509: four",
    b"\x1b[31m" + _PREFIX + b"\x1b]0;title\x07\x1b[2J x509: five\x1b[0m",
    _PREFIX + b"A" * 65_536 + b" x509: six",
    _PREFIX + bytes(value for value in range(1, 256) if value != 0x0A) + b" x509: seven",
]
_FLOOD = 10_000
_STUB = """#!/bin/bash
printf 'start\\n' >>"${STUB_LOG}"
cat "${STUB_LINES}"
exit 0
"""
_REMEDY = b"harp_connect: the tunnel certificate is possibly no longer accepted by HaRP"
_SHARED_KEY = "findling-40-secret-key"


def _watcher_environment(tmp_path: Path, stub_source: str = _STUB, **extra: str) -> dict[str, str]:
    stub = tmp_path / "frpc-stub"
    stub.write_text(stub_source, encoding="utf-8", newline="\n")
    stub.chmod(0o755)
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HP_SHARED_KEY": _SHARED_KEY,
        "HP_FRP_ADDRESS": "127.0.0.1",
        "HP_FRP_PORT": "8782",
        "APP_PORT": "23000",
        "APP_ID": "findling_backend",
        "HP_FRP_CERT_DIR": str(tmp_path / "certs"),
        "FINDLING_RUN_DIR": str(tmp_path / "run"),
        "FINDLING_FRPC_BIN": str(stub),
        "FINDLING_HARP_CERT_POLL_SECONDS": "1",
        "FINDLING_HARP_RESTART_MIN_GAP_SECONDS": "0",
        "STUB_LOG": str(tmp_path / "stub.log"),
        "STUB_LINES": str(tmp_path / "lines.bin"),
        **extra,
    }


@_ON_LINUX_WITH_BASH
def test_s3_hostile_frpc_lines_are_passed_through_and_never_run(tmp_path: Path) -> None:
    lines = [*_HOSTILE, *([_X509] * _FLOOD)]
    (tmp_path / "lines.bin").write_bytes(b"\n".join(lines) + b"\n")
    work = tmp_path / "work"
    work.mkdir()

    started = time.monotonic()
    finished = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [shutil.which("bash") or "bash", str(WATCHER)],
        env=_watcher_environment(tmp_path),
        cwd=work,
        capture_output=True,
        timeout=120,
        check=False,
    )
    elapsed = time.monotonic() - started
    output = finished.stdout + finished.stderr

    # Nothing of a line was executed: no file, no division by nought, no key.
    assert sorted(path.name for path in tmp_path.rglob("pwned*")) == []
    assert _SHARED_KEY.encode() not in output
    # Every line passed through byte for byte, the long one and the binary one too.
    for line in _HOSTILE:
        assert line in output, line[:80]
    assert output.count(_X509) == _FLOOD
    # The remedy follows its schedule (0, 300, 900, 3600 s): once in a run this short.
    assert output.count(_REMEDY) == 1
    # Unchanged files, so no restart: frpc started once.
    assert (tmp_path / "stub.log").read_text(encoding="utf-8").splitlines() == ["start"]
    # frpc ended with 0 and the watcher never passes that on.
    assert finished.returncode == 1
    assert elapsed < 60, f"{_FLOOD} x509 lines took {elapsed:.1f} s"


# A line that arrives in two writes with a pause longer than the poll interval
# in between. `read -t` gives up on the unfinished line and keeps what it has
# read in the variable; the watcher has to carry that over to the next read.
_SLOW_LINE_STUB = """#!/bin/bash
printf 'start\\n' >>"${STUB_LOG}"
printf '%s' '[W] [client/service.go:298] [5f1c2a9b] connect to server error: tls: failed to verify certificate: '
sleep 2.5
printf '%s\\n' 'x509: certificate signed by unknown authority'
exit 0
"""


@_ON_LINUX_WITH_BASH
def test_s3_f_40_02_a_line_slower_than_the_poll_interval_stays_whole(tmp_path: Path) -> None:
    """F-40-02, fixed: the carry of an unfinished line (strict xfail before the fix).

    Before the fix the first part was dropped and the rest, without the
    "connect to server error:" in front, raised no remedy.
    """
    finished = subprocess.run(  # noqa: S603 - an argument list, never a shell
        [shutil.which("bash") or "bash", str(WATCHER)],
        env=_watcher_environment(tmp_path, _SLOW_LINE_STUB),
        capture_output=True,
        timeout=60,
        check=False,
    )
    output = finished.stdout + finished.stderr

    whole = (
        b"[W] [client/service.go:298] [5f1c2a9b] connect to server error: tls: failed to verify certificate: "
        b"x509: certificate signed by unknown authority\n"
    )
    assert whole in output
    assert output.count(_REMEDY) == 1
    assert finished.returncode == 1


@_ON_LINUX_WITH_BASH
def test_s3_symlinked_files_in_a_directory_with_blanks_switch_to_mutual_tls_once(tmp_path: Path) -> None:
    # Reuses the harness of the building plan; only the directory differs.
    from test_harp_connect_supervisor import _until, _watch

    cert_dir = tmp_path / "certs with blanks"
    outside = tmp_path / "outside"
    outside.mkdir()
    with _watch(tmp_path, "auto", HP_FRP_CERT_DIR=str(cert_dir)) as watcher:
        assert _until(lambda: watcher.starts() >= 1, 10), watcher.output()
        cert_dir.mkdir()
        for name in ("ca.crt", "client.crt", "client.key"):
            (outside / name).write_text(f"GOOD {name}\n", encoding="utf-8")
            (cert_dir / name).symlink_to(outside / name)

        assert _until(lambda: watcher.count("harp_connect: the tunnel is connected again") >= 1, 20), watcher.output()
        time.sleep(3)
        assert watcher.starts() == 2
        assert f'transport.tls.certFile = "{cert_dir}/client.crt"' in watcher.config()


# -- the copy command of docs/harp-tunnel.md, the half that runs in the backend --------

HARP_DOC = REPO / "docs" / "harp-tunnel.md"


def _backend_half_of_the_copy_command(target: Path) -> str:
    """The script the admin hands to `sh -c` in the backend, aimed at a tmp directory."""
    text = HARP_DOC.read_text(encoding="utf-8")
    found = re.search(r"docker exec -i nc_app_findling_backend sh -c '([^']+)' sh \"\$f\"", text)
    assert found is not None, "the copy command of the doc has changed its shape"
    return found.group(1).replace("/certs/frp", str(target))


def _copy_in(target: Path, name: str, payload: bytes) -> None:
    subprocess.run(  # noqa: S603 - an argument list, never a shell
        [shutil.which("sh") or "sh", "-c", _backend_half_of_the_copy_command(target), "sh", name],
        input=payload,
        capture_output=True,
        timeout=30,
        check=False,
    )


@_ON_LINUX_WITH_BASH
def test_s3_the_copy_command_replaces_a_file_with_what_it_reads(tmp_path: Path) -> None:
    (tmp_path / "client.key").write_bytes(b"OLD\n")

    _copy_in(tmp_path, "client.key", b"NEW\n")

    assert (tmp_path / "client.key").read_bytes() == b"NEW\n"
    assert _mode(tmp_path / "client.key") == 0o600


@pytest.mark.xfail(strict=True, reason="F-40-03: an empty read (wrong HaRP name) empties the file in the backend")
@_ON_LINUX_WITH_BASH
def test_s3_f_40_03_an_empty_read_leaves_the_file_as_it_was(tmp_path: Path) -> None:
    # What the backend half gets when the first `docker exec "$HARP" cat` fails,
    # for a mistyped HARP name for example: nothing at all on stdin.
    (tmp_path / "client.key").write_bytes(b"OLD\n")

    _copy_in(tmp_path, "client.key", b"")

    assert (tmp_path / "client.key").read_bytes() == b"OLD\n"


def _mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


# == S4 output of the new sentences ====================================================

_RULES_PENDING = (
    "The exclusion rules were changed. The search applies them at once, the counters on this page follow "
    "once they have been worked out again."
)
_NOTHING_LEFT_OUT = (
    "Nothing is left out on purpose right now. Files that are too large, of a type Findling does not read, "
    "or excluded by a rule would be counted here, and they are not in the denominator above."
)
_DUPLICATES = (
    "External storages mounted once per user are counted once per mount here, so the same file can stand "
    "in this figure several times."
)


def test_s4_admin_js_writes_no_markup_at_all() -> None:
    source = ADMIN_JS.read_text(encoding="utf-8")

    assert re.findall(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|\$\(|\.html\(", source) == []


def test_s4_the_new_flags_only_toggle_static_elements() -> None:
    source = ADMIN_JS.read_text(encoding="utf-8")

    for flag in ("rulesPending", "deliberatelyLeftOut"):
        for line in (line for line in source.splitlines() if f"coverage.{flag}" in line):
            assert "textContent" not in line
            assert "innerText" not in line
    assert "coverage.deduplicated" not in source
    for element in (
        "findling-coverage-leftout-explain",
        "findling-coverage-leftout-none",
        "findling-coverage-rules-pending",
    ):
        uses = [line.strip() for line in source.splitlines() if element in line]
        assert uses, element
        assert all(use.startswith(f"shown('{element}'") for use in uses), uses


def test_s4_the_three_sentences_are_rendered_escaped_by_the_template() -> None:
    template = ADMIN_TEMPLATE.read_text(encoding="utf-8")

    for sentence in (_RULES_PENDING, _NOTHING_LEFT_OUT, _DUPLICATES):
        assert f"<?php p($l->t('{sentence}')); ?>" in template, sentence[:40]
        assert template.count(sentence) == 1


# == S5 the write in a GET, Weg C stays a counting matter =============================


def test_s5_the_counting_key_lives_in_the_counting_paths_only() -> None:
    users = sorted(
        str(path.relative_to(PHP_LIB)).replace("\\", "/")
        for path in PHP_LIB.rglob("*.php")
        if re.search(r"countingKey(Groups)?\(", path.read_text(encoding="utf-8"))
    )

    assert users == ["Service/AdminViewService.php", "Service/StorageService.php"]


def test_s5_the_stamp_is_cleared_by_the_admin_page_only() -> None:
    users = sorted(
        str(path.relative_to(PHP_LIB)).replace("\\", "/")
        for path in PHP_LIB.rglob("*.php")
        if "forgetRulesChange(" in path.read_text(encoding="utf-8")
    )

    assert users == ["Service/AdminViewService.php", "Service/SettingsService.php"]
    assert ADMIN_VIEW.read_text(encoding="utf-8").count("forgetRulesChange(") == 1


# == S6 workflows ======================================================================


def test_s6_the_smb_measurement_is_dispatch_only_read_only_and_pinned() -> None:
    source = (WORKFLOWS / "smb-acl-measure.yml").read_text(encoding="utf-8")

    on_block = source.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert on_block.strip() == "workflow_dispatch:"
    assert "\npermissions:\n  contents: read\n" in source
    assert "secrets." not in source
    uses = re.findall(r"^\s*(?:-\s+)?uses:\s*(\S+)", source, re.MULTILINE)
    assert uses
    assert all(use.startswith("./") or re.search(r"@[0-9a-f]{40}$", use) for use in uses), uses


def test_s6_every_action_of_every_workflow_is_pinned_to_a_full_sha() -> None:
    # Only a uses: key counts, not the word in a comment.
    unpinned = [
        f"{path.name}: {use}"
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for use in re.findall(r"^\s*(?:-\s+)?uses:\s*(\S+)", path.read_text(encoding="utf-8"), re.MULTILINE)
        if not use.startswith("./") and re.search(r"@[0-9a-f]{40}$", use) is None
    ]

    assert unpinned == []


# == S7 dependencies =====================================================================


def _locked(package: str) -> tuple[int, ...]:
    text = UV_LOCK.read_text(encoding="utf-8")
    found = re.search(rf'\[\[package\]\]\nname = "{re.escape(package)}"\nversion = "([0-9.]+)"', text)
    assert found is not None, package
    return tuple(int(part) for part in found.group(1).split("."))


def test_s7_the_lock_keeps_starlette_above_the_badhost_floor() -> None:
    assert _locked("starlette") >= (1, 0, 1)
    assert 'constraints = [{ name = "starlette", specifier = ">=1.0.1" }]' in UV_LOCK.read_text(encoding="utf-8")
    assert _locked("fastapi") == (0, 161, 1)


# == B2 and B6 the counters next to the figures they are subtracted from ==============


@pytest.mark.usefixtures("appapi_environment")
def test_b2_the_left_out_counter_never_exceeds_the_figure_it_is_subtracted_from(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # Every storage of the probe left out at once, tombstones included: the
    # page subtracts indexedLeftOut from indexed, and that difference must not
    # need the clamp at nought of figures() on the container side already.
    _state(volume)
    _vectors(volume, [11, 21, 22, 31])

    answer = client.get("/status", params={"leaveOut": "1,2,3"}, headers=sign("admin")).json()

    assert answer["indexedLeftOut"] <= answer["indexed"]
    assert answer["embeddedLeftOut"] <= answer["embedded"]


@pytest.mark.usefixtures("appapi_environment")
def test_b6_f_40_06_a_tombstone_stays_in_indexed_and_out_of_indexed_left_out(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    """F-40-06, accepted: the asymmetry of 39-01, held as it is.

    ``indexed`` counts every row in the state indexed, tombstones included
    (Store.counts, the figure of 1.5), ``indexedLeftOut`` only the living ones.
    A tombstone of a left out storage therefore stays in the numerator of the
    deduplicated figure. Storage 2 of the probe has two living documents and
    one tombstone: the numerator keeps exactly that one row.
    """
    _state(volume)

    answer = client.get("/status", params={"leaveOut": "2"}, headers=sign("admin")).json()

    assert answer["indexed"] == 5
    assert answer["indexedLeftOut"] == 2
    assert answer["indexed"] - answer["indexedLeftOut"] == 3


# == B3 the IN fixes of 39-03 =============================================================


def _package(path: Path, entries: int) -> Path:
    with zipfile.ZipFile(path, "w") as archive:
        for number in range(entries):
            archive.writestr(f"part-{number}.xml", "<a/>")
    return path


@pytest.mark.parametrize(("entries", "refused"), [(19, False), (20, False), (21, True)])
def test_b3_too_many_entries_judges_the_limit_like_1_5(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    entries: int,
    refused: bool,
) -> None:
    monkeypatch.setattr(archive_module, "ARCHIVE_MAX_ENTRIES", 20)

    assert archive_module.too_many_entries(str(_package(tmp_path / "probe.docx", entries))) is refused


def test_b3_a_file_that_is_no_package_is_left_to_its_reader(tmp_path: Path) -> None:
    broken = tmp_path / "broken.docx"
    broken.write_bytes(b"PK\x03\x04 not a directory")

    assert archive_module.too_many_entries(str(broken)) is False
    assert archive_module.too_many_entries(str(tmp_path / "missing.docx")) is False


def test_b3_a_stamp_of_a_storage_with_a_living_row_and_a_bookmark_stays(tmp_path: Path) -> None:
    store = open_store(tmp_path / "state.db")
    try:
        store.record(71, _meta(7, 71), "indexed")
        store.set_reconcile_cursor(7, 500, at=1_800_000_000)
        store.mark_vanished(7, 1_800_000_000)
        store.mark_vanished(8, 1_800_000_000)

        # Neither 7 nor 8 is listed; 7 still has a living row, 8 has nothing.
        store.drop_orphan_bookmarks(frozenset())

        stamps = [int(row[0]) for row in store._conn.execute("SELECT storage_id FROM vanished_storages")]
        bookmarks = [int(row[0]) for row in store._conn.execute("SELECT storage_id FROM reconcile")]
        assert stamps == [7]
        assert bookmarks == [7]
        assert store.mark_vanished(7, 1_900_000_000) == 1_800_000_000
    finally:
        store.close()


# == P1 the cost of the status call with leaveOut ======================================


def _bulk(root: Path, per_storage: dict[int, int], *, vectors: bool) -> None:
    """A synthetic stock: living indexed documents per storage, one chunk each."""
    open_store(root / "state.db").close()
    open_vectors(root / "vectors.db").close()
    rows: list[tuple[int, int]] = []
    file_id = 1
    for storage_id, count in per_storage.items():
        for _ in range(count):
            rows.append((file_id, storage_id))
            file_id += 1
    with sqlite3.connect(root / "state.db") as state:
        state.executemany(
            "INSERT INTO files (file_id, storage_id, root_id, path, mime, size, mtime, state) "
            "VALUES (?, ?, 1, 'p', 'application/pdf', 1, 1, 'indexed')",
            rows,
        )
    if vectors:
        with sqlite3.connect(root / "vectors.db") as stock:
            stock.executemany(
                "INSERT INTO chunks (file_id, ordinal, char_start, char_end) VALUES (?, 0, 0, 1)",
                [(row[0],) for row in rows],
            )


@pytest.mark.usefixtures("appapi_environment")
@pytest.mark.parametrize(("left_out", "answered"), [(100_000, True), (100_001, False)])
def test_p1_the_vector_figure_stops_above_a_hundred_thousand_documents(
    client: TestClient,
    sign: Sign,
    volume: Path,
    left_out: int,
    answered: bool,
) -> None:
    # The real ceiling, not a lowered one: storage 2 holds exactly it or one more.
    _bulk(volume, {1: 10, 2: left_out}, vectors=True)

    answer = client.get("/status", params={"leaveOut": "2"}, headers=sign("admin")).json()

    assert status.LEFT_OUT_EMBEDDED_CEILING == 100_000
    assert answer["indexedLeftOut"] == left_out
    assert ("embeddedLeftOut" in answer) is answered
    if answered:
        assert answer["embeddedLeftOut"] == left_out


@pytest.mark.timing
@pytest.mark.skipif(os.environ.get("FINDLING_TIMING") != "1", reason="timing series runs only with FINDLING_TIMING=1")
@pytest.mark.usefixtures("appapi_environment")
def test_p1_the_status_call_with_leave_out_over_a_hundred_thousand_documents(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # 100 000 documents in three storages, every one with a vector; the page
    # leaves two of the three out, 60 000 documents, under the ceiling.
    _bulk(volume, {1: 40_000, 2: 30_000, 3: 30_000}, vectors=True)
    headers = sign("admin")

    def timed(params: dict[str, str]) -> float:
        started = time.perf_counter()
        response = client.get("/status", params=params, headers=headers)
        elapsed = time.perf_counter() - started
        assert response.status_code == 200
        return elapsed

    timed({})
    without = sorted(timed({}) for _ in range(5))
    with_leave_out = sorted(timed({"leaveOut": "2,3"}) for _ in range(5))
    answer = client.get("/status", params={"leaveOut": "2,3"}, headers=headers).json()

    print(
        f"P1 median of 5: without leaveOut {without[2] * 1000:.1f} ms, "
        f"with leaveOut=2,3 {with_leave_out[2] * 1000:.1f} ms over 100000 documents"
    )
    assert (answer["indexedLeftOut"], answer["embeddedLeftOut"]) == (60_000, 60_000)
    assert with_leave_out[2] < 5.0


# == P3 the idle loop of the watcher (Linux only) ======================================

_COUNTING_SHA = """#!/bin/bash
printf 'x\\n' >>"${SHA_LOG}"
exec "${REAL_SHA}" "$@"
"""


def _cpu_seconds(pid: int) -> float:
    """User and system time of a process and its waited for children, from /proc."""
    if sys.platform == "win32":
        pytest.skip("no /proc on Windows")
    fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").rsplit(")", 1)[1].split()
    # utime, stime, cutime and cstime are the fields 14 to 17 of proc(5).
    return sum(int(value) for value in fields[11:15]) / os.sysconf("SC_CLK_TCK")


@_ON_LINUX_WITH_BASH
def test_p3_ten_idle_seconds_are_about_ten_looks_at_the_files_and_no_busy_wait(tmp_path: Path) -> None:
    from test_harp_connect_supervisor import _until, _watch, _write_certs

    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "sha256sum").write_text(_COUNTING_SHA, encoding="utf-8", newline="\n")
    (shim / "sha256sum").chmod(0o755)
    sha_log = tmp_path / "sha.log"
    _write_certs(tmp_path / "certs", "GOOD")
    poll = 1
    with _watch(
        tmp_path,
        "quiet",
        PATH=f"{shim}:{os.environ.get('PATH', '/usr/bin:/bin')}",
        SHA_LOG=str(sha_log),
        REAL_SHA=shutil.which("sha256sum") or "/usr/bin/sha256sum",
        FINDLING_HARP_CERT_POLL_SECONDS=str(poll),
    ) as watcher:
        assert _until(lambda: watcher.starts() >= 1, 10), watcher.output()
        started = time.monotonic()
        before = len(sha_log.read_text(encoding="utf-8").splitlines()) if sha_log.exists() else 0
        time.sleep(10)
        idle = time.monotonic() - started
        after = len(sha_log.read_text(encoding="utf-8").splitlines())
        cpu_seconds = _cpu_seconds(watcher.process.pid)

    # One fingerprint is two sha256sum calls (the files, then the digest).
    looks = (after - before) / 2
    print(f"P3 {looks:.0f} looks at the files in {idle:.1f} idle s, watcher CPU {cpu_seconds:.2f} s")
    assert 5 <= looks <= math.ceil(idle / poll) + 1
    assert cpu_seconds < 1.0
