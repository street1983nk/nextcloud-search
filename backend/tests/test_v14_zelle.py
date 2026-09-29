"""The run tools of the acceptance trip without a box, plan 28-02.

11-probe-route.py drives the probe of the product over its own admin route,
10-zelle.sh runs one cell from the nought state to the raw data, and
00-kette.sh runs every cell of one box with the cap check before each cell and
the safety timer (D-28-02, D-28-05, D-28-14). None of them has run on a box
yet, so what can be held without one is held here: the probe against a local
http.server stub, the cell and the chain against stand-in docker, occ, python3
and shutdown commands on the PATH (pattern of test_v13_wegwerf.py).

The house rules of the directory (shebang, no carriage return, no dash, no
machine path, no password on a command line) come from test_measurement_scripts
through NARROW_SCOPE_DIRS; this file holds what is particular to each tool.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import pytest

from test_measurement_scripts import MEASUREMENTS_DIR

# Built here from MEASUREMENTS_DIR rather than imported, so this module does not
# lean on a name another plan introduced.
RUN_DIR = MEASUREMENTS_DIR / "2026-10-abnahme-anfahrt" / "skripte"
PROBE_ROUTE = RUN_DIR / "11-probe-route.py"

PASSWORD = "richtig-und-geheim"  # noqa: S105 - the password of the stub, nothing real
LOGIN_TOKEN = "zeichen-der-anmeldeseite"  # noqa: S105 - a token of the stub
SESSION_TOKEN = "zeichen-der-sitzung"  # noqa: S105 - a token of the stub


# ---------------------------------------------------------------------------
# The stub of the Nextcloud routes the probe tool talks to.


@dataclass
class Scenario:
    """What the stub answers, and what it saw."""

    verdict: str = "fits"
    cause: str = ""
    running_readings: int = 2
    never_done: bool = False
    numbers: dict[str, int] = field(default_factory=lambda: {"slots": 1, "need": 1609969536, "available": 4995248128})
    posted: list[dict[str, str]] = field(default_factory=list)
    saved: list[dict[str, str]] = field(default_factory=list)
    readings: int = 0
    tokens_seen: list[str] = field(default_factory=list)
    origins_seen: list[str] = field(default_factory=list)
    target: tuple[str, str] = ("", "")


def _handler_for(scenario: Scenario) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - the name of the base class
            del format, args

        def _send(self, status: int, body: str, content_type: str = "application/json", **headers: str) -> None:
            raw = body.encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            for name, value in headers.items():
                self.send_header(name.replace("_", "-"), value)
            self.end_headers()
            self.wfile.write(raw)

        def _logged_in(self) -> bool:
            return "sitzung=angemeldet" in (self.headers.get("Cookie") or "")

        def _body(self) -> bytes:
            return self.rfile.read(int(self.headers.get("Content-Length") or 0))

        def _token_ok(self) -> bool:
            token = self.headers.get("requesttoken") or ""
            scenario.tokens_seen.append(token)
            return self._logged_in() and token == SESSION_TOKEN

        def do_GET(self) -> None:
            path = self.path.split("?")[0]
            if path == "/login":
                page = f'<html><head data-requesttoken="{LOGIN_TOKEN}"></head></html>'
                self._send(200, page, "text/html", Set_Cookie="vorab=1; Path=/")
            elif path == "/settings/admin/findling":
                if not self._logged_in():
                    self._send(303, "", "text/html", Location="/login?redirect_url=/settings/admin/findling")
                    return
                self._send(200, f'<html><head data-requesttoken="{SESSION_TOKEN}"></head></html>', "text/html")
            elif path == "/apps/dashboard/":
                self._send(200, "<html></html>", "text/html")
            elif path == "/apps/findling/admin/profile/check":
                if not self._token_ok():
                    self._send(412, json.dumps({"message": "CSRF check failed"}))
                    return
                scenario.readings += 1
                done = not scenario.never_done and scenario.readings > scenario.running_readings
                result = None
                if done:
                    result = {
                        "verdict": scenario.verdict,
                        "cause": scenario.cause,
                        "numbers": scenario.numbers,
                        "profile": scenario.target[0],
                        "precision": scenario.target[1],
                    }
                answer = {
                    "code": "ok",
                    "state": "done" if done else "running",
                    "step": "cleanup" if done else "ocr_one",
                    "bytesDone": 0,
                    "bytesTotal": 0,
                    "result": result,
                }
                self._send(200, json.dumps(answer))
            elif path == "/apps/findling/admin/overview":
                if not self._token_ok():
                    self._send(412, json.dumps({"message": "CSRF check failed"}))
                    return
                answer = {
                    "profileEffective": "standard",
                    "guardEffective": "standard",
                    "guardCause": None,
                    "slotsInForce": 2,
                    "slotsThrottled": False,
                    "backendReachable": True,
                    "scheduled": 0,
                    "running": 0,
                    "backend": {"indexed": 5000, "embedded": 5000},
                    "storedPrecision": "int8",
                    "profileSaved": "standard",
                    "examplePath": "/lasttest/files/geheim.pdf",
                }
                self._send(200, json.dumps(answer))
            else:
                self._send(404, "{}")

        def do_POST(self) -> None:
            path = self.path.split("?")[0]
            raw = self._body()
            if path == "/login":
                form = {key: value[0] for key, value in parse_qs(raw.decode()).items()}
                scenario.origins_seen.append(self.headers.get("Origin") or "")
                good = (
                    form.get("password") == PASSWORD
                    and form.get("requesttoken") == LOGIN_TOKEN
                    and bool(self.headers.get("Origin"))
                )
                if good:
                    self._send(
                        303, "", "text/html", Location="/apps/dashboard/", Set_Cookie="sitzung=angemeldet; Path=/"
                    )
                else:
                    self._send(303, "", "text/html", Location="/login?direct=1")
            elif path == "/apps/findling/admin/profile/check":
                if not self._token_ok():
                    self._send(412, json.dumps({"message": "CSRF check failed"}))
                    return
                body = json.loads(raw or b"{}")
                scenario.posted.append(body)
                scenario.target = (body.get("profile", ""), body.get("precision", ""))
                scenario.readings = 0
                self._send(200, json.dumps({"started": True, "code": "started"}))
            elif path == "/apps/findling/admin/profile":
                if not self._token_ok():
                    self._send(412, json.dumps({"message": "CSRF check failed"}))
                    return
                body = json.loads(raw or b"{}")
                scenario.saved.append(body)
                if body == {"profile": "economy", "precision": "int8"}:
                    self._send(200, json.dumps({"saved": True, "code": "saved"}))
                else:
                    self._send(400, json.dumps({"saved": False, "code": "probe_required"}))
            else:
                self._send(404, "{}")

    return Handler


@dataclass
class Stub:
    base: str
    scenario: Scenario


@pytest.fixture
def stub() -> Iterator[Stub]:
    scenario = Scenario()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(scenario))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield Stub(base=f"http://127.0.0.1:{server.server_address[1]}", scenario=scenario)
    finally:
        server.shutdown()
        server.server_close()


def run_probe(
    stub: Stub,
    tmp_path: Path,
    arguments: list[str],
    *,
    login_via: str = "file",
    extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """11-probe-route.py as a program, against the stub, with its own temp root."""
    temp_root = tmp_path / "temp"
    temp_root.mkdir(exist_ok=True)
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("FINDLING_") and key not in {"TMPDIR", "TEMP", "TMP"}
    }
    environment.update(
        {
            "FINDLING_BASE_URL": stub.base,
            "FINDLING_ADMIN_USER": "admin",
            "PROBE_TAKT": "0.05",
            "TMPDIR": str(temp_root),
            "TEMP": str(temp_root),
            "TMP": str(temp_root),
            "PYTHONUTF8": "1",
        }
    )
    if login_via == "file":
        secret = tmp_path / "pw"
        secret.write_text(PASSWORD + "\n", encoding="utf-8")
        environment["FINDLING_ADMIN_PWFILE"] = str(secret)
    elif login_via == "env":
        environment["FINDLING_ADMIN_PASSWORD"] = PASSWORD
    environment.update(extra or {})
    return subprocess.run(  # noqa: S603 - an argument list, never a shell
        [sys.executable, str(PROBE_ROUTE), *arguments],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env=environment,
    )


def test_probe_route_fits_writes_one_line_per_reading_and_ends_with_the_verdict(stub: Stub, tmp_path: Path) -> None:
    """Login with Origin, the session token as header, running twice, then fits."""
    answer = run_probe(stub, tmp_path, ["pruefen", "standard", "int8"])
    assert answer.returncode == 0, answer
    assert stub.scenario.posted == [{"profile": "standard", "precision": "int8"}]
    assert stub.scenario.origins_seen == [stub.base]
    assert set(stub.scenario.tokens_seen) == {SESSION_TOKEN}
    readings = [line for line in answer.stdout.splitlines() if line.startswith("t=")]
    assert len(readings) == 3, answer.stdout
    assert "state=running step=ocr_one" in readings[0]
    assert "state=done step=cleanup" in readings[-1]
    assert "verdict=fits" in readings[-1]
    assert '"need": 1609969536' in readings[-1]
    assert answer.stdout.splitlines()[-1] == "verdikt fits erzwungen nein"
    # No address, no password, no path in the raw output.
    assert stub.base not in answer.stdout
    assert PASSWORD not in answer.stdout + answer.stderr


@pytest.mark.parametrize(("verdict", "code"), [("narrow", 30), ("nofit", 31)])
def test_probe_route_narrow_and_nofit_end_with_their_own_code_and_the_cause(
    stub: Stub, tmp_path: Path, verdict: str, code: int
) -> None:
    """The forcing is the job of 10-zelle.sh; this tool only reports."""
    stub.scenario.verdict = verdict
    stub.scenario.cause = "memory"
    stub.scenario.numbers = {"slots": 1, "reserve": 100, "required": 246415360}
    answer = run_probe(stub, tmp_path, ["pruefen", "performance", "fp32"], login_via="env")
    assert answer.returncode == code, answer
    last = answer.stdout.splitlines()[-1]
    assert last.startswith(f"verdikt {verdict} ursache memory numbers ")
    assert '"required": 246415360' in last
    assert stub.scenario.saved == []


def test_probe_route_ends_with_its_own_code_when_the_frist_runs_out(stub: Stub, tmp_path: Path) -> None:
    """A probe that never reaches done is not a verdict."""
    stub.scenario.never_done = True
    answer = run_probe(stub, tmp_path, ["pruefen", "standard", "int8"], extra={"PROBE_FRIST": "0.5"})
    assert answer.returncode == 32, answer
    assert answer.stdout.splitlines()[-1].startswith("probe-frist-ueberschritten")


def test_probe_route_defaults_the_frist_to_900_and_adds_the_download_for_fp32() -> None:
    """900 s for int8, 900 plus the 600 s download cap of the product for fp32."""
    text = PROBE_ROUTE.read_text(encoding="utf-8")
    assert "DEFAULT_FRIST_SECONDS = 900" in text
    assert "FP32_DOWNLOAD_SECONDS = 600" in text


def test_probe_route_abwaerts_saves_economy_int8_over_the_save_route(stub: Stub, tmp_path: Path) -> None:
    answer = run_probe(stub, tmp_path, ["abwaerts"])
    assert answer.returncode == 0, answer
    assert stub.scenario.saved == [{"profile": "economy", "precision": "int8"}]
    assert stub.scenario.posted == []
    assert "abwaerts code=saved saved=true HTTP200" in answer.stdout


def test_probe_route_overview_reads_a_closed_set_of_fields(stub: Stub, tmp_path: Path) -> None:
    """One line for the shell, and no name carrier of the page leaks through."""
    answer = run_probe(stub, tmp_path, ["uebersicht"])
    assert answer.returncode == 0, answer
    line = answer.stdout.strip()
    assert line.startswith("uebersicht HTTP200 ")
    for part in (
        "effective=standard",
        "guardEffective=standard",
        "guardCause=keine",
        "slotsInForce=2",
        "throttled=false",
        "backendReachable=true",
        "indexed=5000",
        "embedded=5000",
    ):
        assert part in line.split(), line
    assert "geheim" not in line


def test_probe_route_refuses_a_password_as_an_argument(stub: Stub, tmp_path: Path) -> None:
    """An argument stands in the process list of the box (T-28-05)."""
    for shape in (["pruefen", "standard", "int8", "--pass" + "word=x"], ["--passwort", "x", "abwaerts"]):
        answer = run_probe(stub, tmp_path, shape)
        assert answer.returncode == 2, answer
        assert "Datei oder Umgebung" in answer.stderr
    assert stub.scenario.posted == []
    assert stub.scenario.saved == []


def test_probe_route_without_a_password_does_not_log_in(stub: Stub, tmp_path: Path) -> None:
    answer = run_probe(stub, tmp_path, ["abwaerts"], login_via="none")
    assert answer.returncode == 2, answer
    assert stub.scenario.origins_seen == []


def test_probe_route_with_a_wrong_password_ends_with_the_login_code(stub: Stub, tmp_path: Path) -> None:
    answer = run_probe(stub, tmp_path, ["abwaerts"], login_via="none", extra={"FINDLING_ADMIN_PASSWORD": "falsch"})
    assert answer.returncode == 34, answer
    assert stub.scenario.saved == []


def test_probe_route_removes_its_cookie_jar(stub: Stub, tmp_path: Path) -> None:
    """The jar lives in a directory of its own under the temp root and is gone afterwards (T-28-06)."""
    answer = run_probe(stub, tmp_path, ["pruefen", "standard", "int8"])
    assert answer.returncode == 0, answer
    assert list((tmp_path / "temp").iterdir()) == []
    text = PROBE_ROUTE.read_text(encoding="utf-8")
    assert "tempfile.mkdtemp(" in text
    assert "shutil.rmtree(" in text


def test_probe_route_refuses_an_unknown_target_before_any_request(stub: Stub, tmp_path: Path) -> None:
    for shape in (["pruefen", "economy", "int8"], ["pruefen", "standard", "fp16"], ["pruefen"], ["weiter"], []):
        answer = run_probe(stub, tmp_path, shape)
        assert answer.returncode == 2, (shape, answer)
    assert stub.scenario.origins_seen == []


def test_probe_route_is_standard_library_only() -> None:
    """The box has python3 and no requests."""
    text = PROBE_ROUTE.read_text(encoding="utf-8")
    assert "import requests" not in text
    assert "admin/profile/check" in text
