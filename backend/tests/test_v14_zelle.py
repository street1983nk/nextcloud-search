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
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

import pytest

from test_measurement_scripts import MEASUREMENTS_DIR, a_boxless_run

# Built here from MEASUREMENTS_DIR rather than imported, so this module does not
# lean on a name another plan introduced.
RUN_DIR = MEASUREMENTS_DIR / "2026-10-abnahme-anfahrt" / "skripte"
PROBE_ROUTE = RUN_DIR / "11-probe-route.py"
CELL = RUN_DIR / "10-zelle.sh"
CHAIN = RUN_DIR / "00-kette.sh"
NOUGHT = RUN_DIR / "93b-nullstand.sh"
A_DIGEST = "sha256:" + "0" * 64
NO_SHELL = shutil.which("sh") is None

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
                    "backendReachable": True,
                    "scheduled": 0,
                    "running": 0,
                    # The shape of AdminViewService::backend: the guard fields
                    # live in the backend block, not on the top level.
                    "backend": {
                        "indexed": 5000,
                        "embedded": 5000,
                        "guardEffective": "standard",
                        "guardCause": None,
                        "slotsInForce": 2,
                        "slotsThrottled": False,
                    },
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


# ---------------------------------------------------------------------------
# 10-zelle.sh and 00-kette.sh against stand ins on the PATH.
#
# sudo runs its command, setsid and nohup pass it on, sync does nothing, docker
# logs every call and answers the handful of questions a cell asks, the occ
# calls inside docker exec are logged on a line of their own, python3 answers
# for 11-probe-route.py and 96d-statusbeobachter.py and runs the real
# interpreter for everything else (01-teilkorpus.py zaehltor, the reading of a
# state.db), and shutdown logs and plans. None of them reaches a network.

STUB_SUDO = '#!/bin/sh\n[ "${1:-}" = -E ] && shift\nexec "$@"\n'
STUB_HANDOVER = '#!/bin/sh\nexec "$@"\n'
STUB_NOTHING = "#!/bin/sh\nexit 0\n"
STUB_DOCKER = r"""#!/bin/sh
printf 'docker %s\n' "$*" >>"$STUB_LOG"
case "$1" in
ps)
    i=0
    while [ "$i" -lt "${STUB_NEXTCLOUDS:-1}" ]; do
        echo "ghcr.io/nextcloud-releases/aio-nextcloud:latest"
        i=$((i + 1))
    done
    echo "ghcr.io/street1983nk/findling_backend:dev"
    ;;
inspect)
    case "$*" in
    *OOMKilled*) echo "${STUB_OOM:-false 0 2026-10-01T00:00:00Z}" ;;
    *) echo "stubkennung" ;;
    esac
    ;;
image) echo "ghcr.io/street1983nk/findling_backend@$ABBILD_DIGEST" ;;
exec)
    case "$*" in
    *nextcloud-aio-database*)
        # The database side of the count gate: the mark before the trigger,
        # and the fresh skipped/failed rows of the running cell. A state
        # whose variable is unset or 0 prints no row, like group by.
        case "$*" in
        *"max(updated_at)"*) printf '%s\n' "${STUB_ZAEHLMARKE:-2026-10-01 00:00:00}" ;;
        *"findling_queue"*)
            # The work stock of the partial corpus, path sharp (28-07 run 7).
            # STUB_VORRAT_TEIL=fehler is a failed psql (db_lesen: unlesbar);
            # without the variable the stock of the current occ reading, so
            # the older count gate tests keep their numbers: the first reading
            # after the trigger is the count gate reading.
            case "${STUB_VORRAT_TEIL:-}" in
            fehler) exit 1 ;;
            '')
                lesungen=$(cat "$STUB_STATE/lesungen" 2>/dev/null || echo 0)
                if [ "$lesungen" -le 1 ]; then
                    echo $((${STUB_SCHEDULED:-0} + ${STUB_HANDED:-0}))
                else
                    echo 0
                fi
                ;;
            *) printf '%s\n' "$STUB_VORRAT_TEIL" ;;
            esac
            ;;
        *"group by s.state"*)
            [ "${STUB_FRISCH_SKIPPED:-0}" = 0 ] || printf 'skipped|%s\n' "$STUB_FRISCH_SKIPPED"
            [ "${STUB_FRISCH_FAILED:-0}" = 0 ] || printf 'failed|%s\n' "$STUB_FRISCH_FAILED"
            ;;
        esac
        ;;
    *" php occ "*)
        alles="$*"
        occ=${alles#* php occ }
        printf 'occ %s\n' "$occ" >>"$STUB_LOG"
        case "$occ" in
        "findling:index --restart -n")
            : >"$STUB_STATE/getriggert"
            echo "Queued a full rebuild."
            ;;
        "findling:index --restart"*) echo "Nothing was changed." ;;
        findling:index)
            s=0
            h=0
            if [ -e "$STUB_STATE/getriggert" ]; then
                lesungen=$(cat "$STUB_STATE/lesungen" 2>/dev/null || echo 0)
                lesungen=$((lesungen + 1))
                printf '%s' "$lesungen" >"$STUB_STATE/lesungen"
                if [ "$lesungen" -le 1 ]; then
                    s=${STUB_SCHEDULED:-0}
                    h=${STUB_HANDED:-0}
                fi
            elif [ -n "${STUB_NACHSCHUB:-}" ] && [ -e "$STUB_STATE/bewaffnet" ]; then
                # Fresh top-up of the armed container itself, before the
                # trigger: the 6-16 s self-crawl of run 4 over the top-up
                # route. Harmless since 93i (the trigger clears it), so the
                # cell must run through.
                s=$STUB_NACHSCHUB
            elif [ -n "${STUB_ALTVORRAT:-}" ]; then
                # Old stock of an earlier run lies BEFORE the arming, fresh
                # top-up only after it: the early gate ends the cell before
                # any enable, so the two switches cannot collide. After the
                # trigger the reading counter above owns the counters (the
                # count gate tests lean on STUB_SCHEDULED/STUB_HANDED).
                s=$STUB_ALTVORRAT
            fi
            printf 'Work stock\n  scheduled            %s\n  handed to the worker %s\n\n' "$s" "$h"
            printf 'End states as Nextcloud recorded them\n  indexed              0\n'
            printf '  skipped              %s\n  failed               %s\n' "${STUB_SKIPPED:-0}" "${STUB_FAILED:-0}"
            ;;
        "config:app:set findling profile --value="*) printf '%s' "${occ#*--value=}" >"$STUB_STATE/profil" ;;
        app_api:app:register*) [ "${STUB_REGISTER:-0}" = 0 ] || exit 1 ;;
        app_api:app:enable*)
            # The arming mark: STUB_NACHSCHUB answers only after the first
            # enable contact (disable stays in the default branch).
            : >"$STUB_STATE/bewaffnet"
            echo "ok"
            ;;
        *) echo "ok" ;;
        esac
        ;;
    *40b-baumhash.py*) echo "baumhash: ${STUB_HASH:-abc}" ;;
    esac
    ;;
esac
exit 0
"""
STUB_PYTHON = r"""#!/bin/sh
case "$(basename "${1:-}")" in
11-probe-route.py)
    printf 'probe-route %s\n' "$2 ${3:-} ${4:-}" >>"$STUB_LOG"
    case "$2" in
    abwaerts)
        printf economy >"$STUB_STATE/profil"
        echo "abwaerts code=saved saved=true HTTP200"
        ;;
    pruefen)
        echo "t=2s state=done step=cleanup bytes=0/0 verdict=${STUB_VERDIKT:-fits}"
        case "${STUB_VERDIKT:-fits}" in
        fits)
            printf '%s' "$3" >"$STUB_STATE/profil"
            echo "verdikt fits erzwungen nein"
            exit 0
            ;;
        narrow)
            echo "verdikt narrow ursache ${STUB_URSACHE:-memory} numbers {}"
            exit 30
            ;;
        nofit)
            echo "verdikt nofit ursache ${STUB_URSACHE:-reserve} numbers {}"
            exit 31
            ;;
        *) exit 33 ;;
        esac
        ;;
    uebersicht)
        p=$(cat "$STUB_STATE/profil" 2>/dev/null || echo economy)
        [ "${STUB_WIRKT:-ja}" = ja ] || p=economy
        e=${STUB_EMBEDDED:-10}
        if [ "${STUB_EMBEDDED_WACKELN:-nein}" = ja ]; then
            w=$(cat "$STUB_STATE/wackeln" 2>/dev/null || echo 0)
            w=$((w + 1))
            printf '%s' "$w" >"$STUB_STATE/wackeln"
            e=$((e + w % 2))
        elif [ "$(cat "$STUB_STATE/lesungen" 2>/dev/null || echo 0)" -gt 1 ]; then
            e=${STUB_INDEXED:-10}
        fi
        printf 'uebersicht HTTP200 effective=%s guardEffective=%s' "$p" "${STUB_GUARD:-$p}"
        printf ' guardCause=keine slotsInForce=2'
        printf ' throttled=false backendReachable=%s scheduled=0 running=0' "${STUB_REACHABLE:-true}"
        printf ' indexed=%s embedded=%s storedPrecision=int8 profileSaved=%s\n' \
            "${STUB_INDEXED:-10}" "$e" "$p"
        ;;
    esac
    exit 0
    ;;
96d-statusbeobachter.py)
    printf 'statusbeobachter\n' >>"$STUB_LOG"
    exit 0
    ;;
esac
exec "$REAL_PYTHON" "$@"
"""
STUB_SHUTDOWN = r"""#!/bin/sh
printf 'shutdown %s\n' "$*" >>"$STUB_LOG"
case "${2:-}" in
+*)
    minuten=${2#+}
    printf 'USEC=%s\nMODE=poweroff\n' "$((($(date +%s) + minuten * 60) * 1000000))" >"$GEPLANT_DATEI"
    ;;
esac
exit 0
"""
STUB_SAMPLER = r"""#!/bin/sh
printf 'sampler %s\n' "$(basename "$0")" >>"$STUB_LOG"
exit 0
"""
STUB_TREE_HASH = r"""#!/bin/sh
{
    echo "baumhash: ${STUB_HASH:-abc}"
    echo "baumhash: ${STUB_HASH:-abc}"
    echo "baumhash: php"
    echo "abbild-baumhash: ${STUB_HASH:-abc}"
    echo "baumhash-gleich ja"
} >"$OUT/40b-baumhash.txt"
printf 'baumhash-werkzeug\n' >>"$STUB_LOG"
"""
STUB_CELL = r"""#!/bin/sh
printf 'zelle %s korpus %s\n' "$*" "${ZELLE_KORPUS:-}" >>"$STUB_LOG"
exit "${STUB_ZELLE_RC:-0}"
"""


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path


@dataclass
class Bench:
    out: Path
    log: Path
    environment: dict[str, str | None]

    def calls(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.is_file() else []


def a_bench(tmp_path: Path, values: dict[str, str]) -> Bench:
    """Stand ins, a value file and an environment for one boxless run."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, text in (
        ("sudo", STUB_SUDO),
        ("setsid", STUB_HANDOVER),
        ("nohup", STUB_HANDOVER),
        ("sync", STUB_NOTHING),
        ("docker", STUB_DOCKER),
        ("python3", STUB_PYTHON),
        ("shutdown", STUB_SHUTDOWN),
    ):
        _write(bin_dir / name, text)
    tools = tmp_path / "werkzeuge"
    tools.mkdir()
    _write(tools / "40b-baumhash.sh", STUB_TREE_HASH)
    _write(tools / "40b-baumhash.py", "#!/usr/bin/env python3\n")
    samplers = tmp_path / "sampler"
    samplers.mkdir()
    for name in ("rss_sampler.sh", "proc_anon_sampler.sh", "cpu_sampler.sh"):
        _write(samplers / name, STUB_SAMPLER)
    state = tmp_path / "zustand"
    state.mkdir()
    (tmp_path / "volumen").mkdir()
    secret = tmp_path / "pw"
    secret.write_text("geheim\n", encoding="utf-8")
    file = tmp_path / "werte.env"
    lines = {"ABBILD_DIGEST": A_DIGEST, "GRENZE_2G": "nein", "PWFILE": secret.as_posix(), **values}
    file.write_text("".join(f"{key}={value}\n" for key, value in lines.items() if value), encoding="utf-8")
    log = tmp_path / "aufrufe.txt"
    environment: dict[str, str | None] = {
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "LAUFWERTE": file.as_posix(),
        "STUB_LOG": log.as_posix(),
        "STUB_STATE": state.as_posix(),
        "REAL_PYTHON": Path(sys.executable).as_posix(),
        "WERKZEUGE": tools.as_posix(),
        "RSS_SAMPLER": (samplers / "rss_sampler.sh").as_posix(),
        "ANON_SAMPLER": (samplers / "proc_anon_sampler.sh").as_posix(),
        "CPU_SAMPLER": (samplers / "cpu_sampler.sh").as_posix(),
        "VOLUME": (tmp_path / "volumen").as_posix(),
        "DROP_CACHES": (tmp_path / "drop_caches").as_posix(),
        "CGROUP_ROOT": (tmp_path / "cgroup").as_posix(),
        "GEPLANT_DATEI": (tmp_path / "scheduled").as_posix(),
        "BEWAFFNUNG_TAKT": "0",
        "WIRK_TAKT": "0",
        "ENDE_TAKT": "0",
        "KORPUS_FRIST": "0",
        "RUHE": "0",
        "HERZ_TAKT": "1",
        "ZELLE_SKRIPT": _write(tmp_path / "zelle-stub.sh", STUB_CELL).as_posix(),
        "PYTHONUTF8": "1",
    }
    return Bench(out=tmp_path / "rohdaten", log=log, environment=environment)


def run_cell(
    bench: Bench, arguments: list[str], extra: dict[str, str | None] | None = None
) -> subprocess.CompletedProcess[str]:
    return a_boxless_run(CELL, bench.out, arguments, umgebung={**bench.environment, **(extra or {})})


def cell_lines(bench: Bench, box: str = "m7g.large", cell: str = "St-T") -> list[str]:
    raw = bench.out / box / cell / "10-zelle.txt"
    return raw.read_text(encoding="utf-8").splitlines() if raw.is_file() else []


def steps_of(lines: list[str]) -> list[str]:
    return [line.split()[1] for line in lines if line.startswith("schritt ")]


def code_of(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))


def first_index(calls: list[str], pattern: str) -> int:
    return next(index for index, call in enumerate(calls) if pattern in call)


ORDER = [
    "abwaerts",
    "zaehlung-eine-nextcloud",
    "nullstand",
    "registrierung",
    "vorrat-tor",
    "bewaffnung",
    "grenze",
    "baumhash",
    "93b-nullstand",
    "drop-caches",
    "probe",
    "wirksamkeit",
    "sampler",
    "trigger",
    "ende",
    "nachlauf",
    "abholen",
]
CALL_ORDER = (
    "probe-route abwaerts",
    "docker ps",
    "--rm-data",
    "occ app_api:app:register",
    "occ app_api:app:disable",
    "baumhash-werkzeug",
    "probe-route pruefen standard int8",
    "occ findling:index --restart -n",
)
CELL_ARGUMENTS = ["m7g.large", "St-T", "standard", "int8"]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_order_runs_every_step_in_the_order_of_pattern_1(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS)
    assert answer.returncode == 0, answer
    lines = cell_lines(bench)
    assert steps_of(lines) == ORDER, lines
    assert lines[-1] == "10-ZELLE-FERTIG St-T"
    calls = bench.calls()
    positions = [first_index(calls, pattern) for pattern in CALL_ORDER]
    assert positions == sorted(positions), list(zip(CALL_ORDER, positions, strict=True))
    assert "erzwungen nein" in lines
    assert "caches-geleert ja" in lines
    assert (tmp_path / "drop_caches").read_text(encoding="utf-8").strip() == "3"
    assert "waechter-absenkung nein" in lines
    assert any(line.startswith("guard effective=standard ") for line in lines), lines
    assert not [call for call in calls if call.startswith("occ config:app:set")]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_refuse_two_nextclouds_before_any_rm_data(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_NEXTCLOUDS": "2"})
    assert answer.returncode == 61, answer
    assert not [call for call in bench.calls() if "--rm-data" in call]
    assert "nextcloud-instanzen 2" in cell_lines(bench)


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
@pytest.mark.parametrize("digest", ["", "latest", "sha256:" + "0" * 63, "sha256:" + "g" * 64])
def test_cell_refuse_a_digest_without_its_shape_before_the_nought_state(tmp_path: Path, digest: str) -> None:
    bench = a_bench(tmp_path, {"ABBILD_DIGEST": digest})
    answer = run_cell(bench, CELL_ARGUMENTS)
    assert answer.returncode == 2, answer
    assert "ABBILD_DIGEST" in answer.stderr
    assert bench.calls() == []


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["m7g.large"],
        ["m7g.large", "St-T", "turbo", "int8"],
        ["m7g.large", "St-T", "economy", "fp32"],
        ["m7g.large", "St/T", "standard", "int8"],
        ["m7g.large", "St-T", "standard", "fp16"],
    ],
)
def test_cell_refuse_an_unknown_call(tmp_path: Path, arguments: list[str]) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, arguments)
    assert answer.returncode == 2, answer
    assert "Benutzung:" in answer.stderr
    assert bench.calls() == []


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_refuse_the_trigger_while_the_old_profile_is_in_force(tmp_path: Path) -> None:
    """No trigger after the frist, with one arming more in between (pitfall 1)."""
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_WIRKT": "nein", "WIRK_FRIST": "2", "WIRK_TAKT": "0.2"})
    assert answer.returncode == 69, answer
    calls = bench.calls()
    assert not [call for call in calls if "--restart" in call]
    assert not [call for call in calls if call.startswith("sampler ")]
    assert len([call for call in calls if call.startswith("occ app_api:app:disable")]) == 2
    assert any(line.startswith("wirksamkeit neu-bewaffnet ") for line in cell_lines(bench))


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_refuse_a_container_that_is_not_armed(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_REACHABLE": "false", "BEWAFFNUNG_FRIST": "1"})
    assert answer.returncode == 65, answer
    assert not [call for call in bench.calls() if "probe-route pruefen" in call]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_sparsam_runs_no_probe(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, ["m7g.large", "S-T", "economy", "int8"])
    assert answer.returncode == 0, answer
    assert "probe keine abwaertsweg" in cell_lines(bench, cell="S-T")
    assert not [call for call in bench.calls() if "probe-route pruefen" in call]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    ("verdict", "precision", "reason"),
    [("narrow", "int8", "narrow/memory"), ("nofit", "fp32", "nofit/reserve")],
)
def test_cell_forced_over_occ_after_narrow_or_nofit(tmp_path: Path, verdict: str, precision: str, reason: str) -> None:
    """D-28-05: occ skips the probe, and the cell carries the mark."""
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, ["m7g.large", "L-T", "performance", precision], {"STUB_VERDIKT": verdict})
    assert answer.returncode == 0, answer
    assert f"erzwungen ja grund {reason}" in cell_lines(bench, cell="L-T")
    calls = bench.calls()
    assert "occ config:app:set findling profile --value=performance" in calls
    fp32 = "occ config:app:set findling model_precision --value=fp32"
    assert (fp32 in calls) == (precision == "fp32")


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_aborts_74_without_forcing_when_the_probe_says_hardware_short(tmp_path: Path) -> None:
    """D-24-07: below the suggestion thresholds effective never reaches the target.

    Forcing over occ would only hang at the gate of abort 69, so the cell ends
    with its own code and nothing is forced (owner decision 03.10.2026).
    """
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_VERDIKT": "nofit", "STUB_URSACHE": "hardware_short"})
    assert answer.returncode == 74, answer
    lines = cell_lines(bench)
    assert [line for line in lines if line.startswith("zelle-abbruch rueckgabe 74 ")], lines
    assert not [line for line in lines if line.startswith("erzwungen ja")]
    calls = bench.calls()
    assert not [call for call in calls if "config:app:set findling profile" in call]
    assert not [call for call in calls if "--restart" in call]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_ends_with_its_own_code_when_the_probe_fails_otherwise(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_VERDIKT": "besetzt"})
    assert answer.returncode == 68, answer
    assert not [call for call in bench.calls() if "--restart" in call]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_trigger_carries_the_n(tmp_path: Path) -> None:
    """Without -n the command asks back, gets no answer and changes nothing."""
    code = code_of(CELL.read_text(encoding="utf-8"))
    assert code.count("findling:index --restart -n") >= 1
    assert re.findall(r"findling:index --restart(?! -n)", code) == []
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS)
    assert answer.returncode == 0, answer
    calls = bench.calls()
    assert "occ findling:index --restart -n" in calls
    # A full corpus cell (ZELLE_KORPUS=voll, the default) never touches the
    # database: no psql call, neither for the mark nor for the fresh count.
    assert not [call for call in calls if "psql" in call], calls


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_demands_the_count_gate(tmp_path: Path) -> None:
    """Fresh end states of the cell count; the global occ counters are noise."""
    bench = a_bench(tmp_path, {})
    good: dict[str, str | None] = {
        "ZELLE_KORPUS": "teil",
        "STUB_INDEXED": "4990",
        "STUB_EMBEDDED": "4990",
        "STUB_FRISCH_SKIPPED": "6",
        "STUB_FRISCH_FAILED": "4",
        # The global occ end states stay set as a disturbance: they must not
        # flow into the sum, or the gate would see 5041 again.
        "STUB_SKIPPED": "35",
        "STUB_FAILED": "6",
    }
    answer = run_cell(bench, CELL_ARGUMENTS, good)
    assert answer.returncode == 0, answer
    assert "zaehltor bestanden 5000" in cell_lines(bench)


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_passes_with_the_counters_of_run_5(tmp_path: Path) -> None:
    """The proof of run 5 (04-teilkorpus-arm.txt): 5041 becomes 5000.

    Run 5 held the stock at 3535 (scheduled 3525, handed 10) and embedded
    1465: exactly the 5000 files of the partial corpus. The 41 foreign old
    end states in oc_findling_file_state (skipped 35, failed 6, written
    before the mark and outside files/teilkorpus) made the old global sum
    5041 and aborted the cell with 71. The fresh count must drop them.
    """
    bench = a_bench(tmp_path, {})
    counters: dict[str, str | None] = {
        "ZELLE_KORPUS": "teil",
        "STUB_SCHEDULED": "3525",
        "STUB_HANDED": "10",
        "STUB_EMBEDDED": "1465",
        "STUB_INDEXED": "1465",
        "STUB_SKIPPED": "35",
        "STUB_FAILED": "6",
    }
    answer = run_cell(bench, CELL_ARGUMENTS, counters)
    assert answer.returncode == 0, answer
    lines = cell_lines(bench)
    assert "zaehltor bestanden 5000" in lines, lines
    counting = next(line for line in lines if line.startswith("zaehlung "))
    assert "summe 5000" in counting, counting
    assert "summe 5041" not in counting, counting
    assert any(line.startswith("zaehlmarke ") for line in lines), lines


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_old_states_mask_no_real_shortfall(tmp_path: Path) -> None:
    """The calibration trap of run 2: a real shortfall of 41 stays abort 71.

    With embedded only 1424 the sum is 4959; the 41 global old end states
    (skipped 35, failed 6) would fill the gap exactly, as they did when the
    gate was calibrated on run 2. They must not.
    """
    bench = a_bench(tmp_path, {})
    counters: dict[str, str | None] = {
        "ZELLE_KORPUS": "teil",
        "STUB_SCHEDULED": "3525",
        "STUB_HANDED": "10",
        "STUB_EMBEDDED": "1424",
        "STUB_INDEXED": "1424",
        "STUB_SKIPPED": "35",
        "STUB_FAILED": "6",
    }
    answer = run_cell(bench, CELL_ARGUMENTS, counters)
    assert answer.returncode == 71, answer
    lines = cell_lines(bench)
    assert "zaehltor verfehlt 4959 statt 5000" in lines, lines
    assert "ende" not in steps_of(lines)


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_ends_the_cell_on_a_missed_count(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"ZELLE_KORPUS": "teil"})
    assert answer.returncode == 71, answer
    lines = cell_lines(bench)
    assert "zaehltor verfehlt 10 statt 5000" in lines
    assert "ende" not in steps_of(lines)


# The counters of the real abort 71 on m7g.large: the stock still held 3528
# files (scheduled 3518, handed 10), 41 were terminal (skipped 35, failed 6),
# 3368 were indexed but only 1431 embedded. The stock drains in step with
# embedded, so indexed double counts what is still in the stock: the first
# broken formula summed 6937 instead of 5000. The calibration on run 2 then
# summed the GLOBAL occ end states, which run 5 proved to be old states of
# files outside the partial corpus (point 4 of the follow-up): here the 41
# are fresh states of the running cell, read time and path sharp from
# oc_findling_file_state, so they count.
ABORT_71_COUNTERS: dict[str, str | None] = {
    "ZELLE_KORPUS": "teil",
    "STUB_SCHEDULED": "3518",
    "STUB_HANDED": "10",
    "STUB_FRISCH_SKIPPED": "35",
    "STUB_FRISCH_FAILED": "6",
    "STUB_INDEXED": "3368",
    "STUB_EMBEDDED": "1431",
}


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_counts_embedded_not_indexed(tmp_path: Path) -> None:
    """The gate must pass the real abort 71 counters: 3528 + 41 + 1431 = 5000."""
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, dict(ABORT_71_COUNTERS))
    assert answer.returncode == 0, answer
    lines = cell_lines(bench)
    assert "zaehltor bestanden 5000" in lines, lines
    counting = next(line for line in lines if line.startswith("zaehlung "))
    assert "eingebettet 1431" in counting, counting


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_still_fails_on_a_real_shortfall(tmp_path: Path) -> None:
    """A real shortfall (31 files short of 5000) still ends the cell with 71."""
    bench = a_bench(tmp_path, {})
    counters = dict(ABORT_71_COUNTERS)
    counters["STUB_EMBEDDED"] = "1400"
    answer = run_cell(bench, CELL_ARGUMENTS, counters)
    assert answer.returncode == 71, answer
    lines = cell_lines(bench)
    assert "zaehltor verfehlt 4969 statt 5000" in lines, lines
    assert "ende" not in steps_of(lines)


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_aborts_on_an_unstable_embedded_reading(tmp_path: Path) -> None:
    """When embedded wobbles between readings, the gate never passes a guess."""
    bench = a_bench(tmp_path, {})
    counters = dict(ABORT_71_COUNTERS)
    counters["STUB_EMBEDDED_WACKELN"] = "ja"
    answer = run_cell(bench, CELL_ARGUMENTS, counters)
    assert answer.returncode == 71, answer
    lines = cell_lines(bench)
    assert any(line.startswith("zaehlung-instabil") for line in lines), lines


# The counters of run 7 L-T on m7g.4xlarge (rohdaten/05-typwechsel-arm.txt):
# the partial corpus was fully embedded, 5000 of 5000, and nothing of it was
# left in the stock. The global stock still held 549 files, all of them under
# folders an exclusion rule keeps out (loadtest 500, Templates/Photos/samples
# 49, none under files/teilkorpus), requeued by the reconcile tick that landed
# ~17 s before the gate read. The old gate summed 549 + 5000 = 5549 and aborted
# the cell with 71 twice. The stock is now read path sharp from
# oc_findling_queue, the same line as the fresh end states (quick 261002-cvf).
RUN_7_COUNTERS: dict[str, str | None] = {
    "ZELLE_KORPUS": "teil",
    "STUB_SCHEDULED": "549",
    "STUB_VORRAT_TEIL": "0",
    "STUB_EMBEDDED": "5000",
    "STUB_INDEXED": "5000",
}


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_passes_with_the_counters_of_run_7(tmp_path: Path) -> None:
    """The proof of run 7 L-T (05-typwechsel-arm.txt): 5549 becomes 5000."""
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, dict(RUN_7_COUNTERS))
    assert answer.returncode == 0, answer
    lines = cell_lines(bench)
    assert "zaehltor bestanden 5000" in lines, lines
    counting = next(line for line in lines if line.startswith("zaehlung "))
    assert "summe 5000" in counting, counting
    assert "summe 5549" not in counting, counting
    assert "vorrat-teilkorpus 0" in counting, counting
    assert "vorrat-global 549" in counting, counting


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_global_stock_fills_no_real_shortfall(tmp_path: Path) -> None:
    """The positive control: 549 foreign files must not fill a gap of 49."""
    bench = a_bench(tmp_path, {})
    counters = dict(RUN_7_COUNTERS)
    counters["STUB_EMBEDDED"] = "4951"
    counters["STUB_INDEXED"] = "4951"
    answer = run_cell(bench, CELL_ARGUMENTS, counters)
    assert answer.returncode == 71, answer
    lines = cell_lines(bench)
    assert "zaehltor verfehlt 4951 statt 5000" in lines, lines
    assert "ende" not in steps_of(lines)


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_teilkorpus_aborts_on_an_unreadable_partial_stock(tmp_path: Path) -> None:
    """A stock the database does not answer is no zero: abort 71."""
    bench = a_bench(tmp_path, {})
    counters: dict[str, str | None] = {
        "ZELLE_KORPUS": "teil",
        "STUB_VORRAT_TEIL": "fehler",
        "STUB_EMBEDDED": "5000",
        "STUB_INDEXED": "5000",
    }
    answer = run_cell(bench, CELL_ARGUMENTS, counters)
    assert answer.returncode == 71, answer
    lines = cell_lines(bench)
    counting = next(line for line in lines if line.startswith("zaehlung "))
    assert "summe unlesbar" in counting, counting
    assert "ende" not in steps_of(lines)


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_marks_a_guard_that_lowered_during_the_cell(tmp_path: Path) -> None:
    """Pitfall 8: marked, not thrown away."""
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_GUARD": "economy"})
    assert answer.returncode == 0, answer
    assert "waechter-absenkung ja" in cell_lines(bench)


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_sets_the_2g_limit_only_on_request_and_reads_it_back(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {"GRENZE_2G": "ja"})
    scope = tmp_path / "cgroup" / "system.slice" / "docker-stubkennung.scope"
    scope.mkdir(parents=True)
    (scope / "memory.max").write_text("2147483648\n", encoding="utf-8")
    (scope / "memory.swap.max").write_text("0\n", encoding="utf-8")
    answer = run_cell(bench, ["m7g.large", "S-voll", "economy", "int8"])
    assert answer.returncode == 0, answer
    assert "grenze-gesetzt ja" in cell_lines(bench, cell="S-voll")
    assert "docker update --memory=2g --memory-swap=2g nc_app_findling_backend" in bench.calls()
    (scope / "memory.max").write_text("max\n", encoding="utf-8")
    again = run_cell(bench, ["m7g.large", "S-voll-2", "economy", "int8"])
    assert again.returncode == 64, again


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_without_limit_sets_none(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, ["c7a.xlarge", "St-T", "standard", "int8"])
    assert answer.returncode == 0, answer
    assert "grenze keine" in cell_lines(bench, box="c7a.xlarge")
    assert not [call for call in bench.calls() if "docker update" in call]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_refuses_a_raw_directory_that_is_not_empty(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    (bench.out / "m7g.large" / "St-T").mkdir(parents=True)
    (bench.out / "m7g.large" / "St-T" / "alt.txt").write_text("x", encoding="utf-8")
    answer = run_cell(bench, CELL_ARGUMENTS)
    assert answer.returncode == 59, answer
    assert bench.calls() == []


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_nought_reading_refuses_a_volume_with_indexed_files(tmp_path: Path) -> None:
    """93b reads the four sources without queueing anything, and a filled store ends the cell."""
    bench = a_bench(tmp_path, {})
    connection = sqlite3.connect(tmp_path / "volumen" / "state.db")
    connection.execute("create table files (id integer, state text, deleted_at integer)")
    connection.execute("create table meta (key text, value text)")
    connection.execute("insert into files values (1, 'indexed', null)")
    connection.commit()
    connection.close()
    answer = run_cell(bench, CELL_ARGUMENTS)
    assert answer.returncode == 67, answer
    assert not [call for call in bench.calls() if "--restart" in call]
    raw = (bench.out / "m7g.large" / "St-T" / "93b-nullstand.txt").read_text(encoding="utf-8")
    assert "volumen-leer nein" in raw


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_nought_reading_refuses_a_filled_work_stock(tmp_path: Path) -> None:
    """The stock gate (BLOCKER-28-07): --rm-data does not clear the NC queue.

    The gate sits BEFORE the arming, because only there the position carries:
    run 4 showed the freshly armed container pulls the crawl itself within
    6-16 s over the top-up route (POST /queues/documents/topup ->
    CrawlAdvanceService, first_index_scheduled=1 survives --rm-data), so a
    gate at the 93b step sees fresh, harmless stock (549 and 581 in run 4)
    and is impassable. Before the arming no container can push anything in,
    so a stock there is old orders of an earlier run (run 3: 3420) and ends
    the cell with 73, before anything expensive: no arming, no tree hash, no
    93b reading, no samplers, no trigger.
    """
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_ALTVORRAT": "3420"})
    assert answer.returncode == 73, answer
    lines = cell_lines(bench)
    steps = steps_of(lines)
    assert steps[-1] == "vorrat-tor", steps
    assert "bewaffnung" not in steps
    assert "vorrat-tor altvorrat 3420" in lines
    assert not (bench.out / "m7g.large" / "St-T" / "93b-nullstand.txt").exists()
    calls = bench.calls()
    assert not [call for call in calls if "app_api:app:disable" in call]
    assert not [call for call in calls if "app_api:app:enable" in call]
    assert "baumhash-werkzeug" not in calls
    assert not [call for call in calls if "--restart" in call]
    assert not [call for call in calls if call.startswith("sampler ")]


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_tolerates_fresh_topup_after_the_arming(tmp_path: Path) -> None:
    """Fresh stock AFTER the arming is the container's own top-up, no defect.

    Since 93i the trigger (findling:index --restart) clears fresh stock
    itself, so the gate must not punish it: the 93b reading only records
    source 4 as one line "arbeitsvorrat N", and the cell runs through to the
    end with 0.
    """
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS, {"STUB_NACHSCHUB": "581"})
    assert answer.returncode == 0, answer
    raw = (bench.out / "m7g.large" / "St-T" / "93b-nullstand.txt").read_text(encoding="utf-8")
    assert "arbeitsvorrat 581" in raw
    lines = cell_lines(bench)
    assert "ende" in steps_of(lines)
    assert not [line for line in lines if line.startswith("zelle-abbruch")]


def test_cell_nought_reading_queues_nothing() -> None:
    text = NOUGHT.read_text(encoding="utf-8")
    assert "--restart" not in code_of(text)
    assert "93-nullstand.sh" in text


def test_cell_calls_the_tools_instead_of_rebuilding_them() -> None:
    text = CELL.read_text(encoding="utf-8")
    for tool in (
        "40b-baumhash.sh",
        "96d-statusbeobachter.py",
        "rss_sampler.sh",
        "proc_anon_sampler.sh",
        "cpu_sampler.sh",
        "11-probe-route.py",
        "93b-nullstand.sh",
        "93-nullstand.sh",
        "01-teilkorpus.py",
    ):
        assert tool in text, tool
    code = code_of(text)
    assert '"$RSS_SAMPLER" "$CONTAINER" 2 ' in code
    assert '"$ANON_SAMPLER" "$CONTAINER" 1 ' in code
    assert "shutdown" not in code


# ---------------------------------------------------------------------------
# 00-kette.sh


def run_chain(bench: Bench, extra: dict[str, str | None] | None = None) -> subprocess.CompletedProcess[str]:
    return a_boxless_run(CHAIN, bench.out, ["m7g.large"], umgebung={**bench.environment, **(extra or {})})


def chain_values(**overrides: str) -> dict[str, str]:
    values = {
        "DECKEL_USD": "58.74",
        "BISHER_USD": "0",
        "SATZ_USD_H": "0.0978",
        "BOX_START_EPOCH": str(int(time.time())),
        "ZELLEN": "S-T:economy:int8:teil St-T:standard:int8:teil",
        "VORPRUEFUNG": "stop-ja",
    }
    values.update(overrides)
    return values


def shutdowns(bench: Bench) -> list[str]:
    return [call for call in bench.calls() if call.startswith("shutdown ")]


def cells_run(bench: Bench) -> list[str]:
    return [call for call in bench.calls() if call.startswith("zelle ")]


def chain_lines(bench: Bench) -> list[str]:
    raw = bench.out / "m7g.large" / "00-kette.txt"
    return raw.read_text(encoding="utf-8").splitlines() if raw.is_file() else []


def minutes_of(call: str) -> int:
    found = re.fullmatch(r"shutdown -h \+(\d+)", call)
    assert found is not None, call
    return int(found.group(1))


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_kette_timer_is_set_at_cap_times_1_20_and_the_end_stops_the_box(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, chain_values())
    answer = run_chain(bench)
    assert answer.returncode == 0, answer
    calls = shutdowns(bench)
    assert len(calls) == 2, calls
    # (1.20 x 58.74 - 0) / 0.0978 x 60 = 43243.4 minutes, give or take the seconds of the run.
    assert 43240 <= minutes_of(calls[0]) <= 43244, calls
    assert calls[-1] == "shutdown -h +2"
    assert cells_run(bench) == [
        "zelle m7g.large S-T economy int8 korpus teil",
        "zelle m7g.large St-T standard int8 korpus teil",
    ]
    assert any(line.startswith("kette-ende ") for line in chain_lines(bench)), chain_lines(bench)
    assert (bench.out / "m7g.large" / "00-herzschlag.txt").is_file()


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_kette_deckel_starts_no_cell_and_does_not_stop_the_box(tmp_path: Path) -> None:
    """D-28-02: a mark, no new cell, and no shutdown beyond the safety timer of the start."""
    bench = a_bench(tmp_path, chain_values(BISHER_USD="58.80"))
    answer = run_chain(bench)
    assert answer.returncode == 83, answer
    assert cells_run(bench) == []
    calls = shutdowns(bench)
    assert len(calls) == 1, calls
    # (70.488 - 58.80) / 0.0978 x 60 = 7170.5 minutes
    assert 7168 <= minutes_of(calls[0]) <= 7171, calls
    lines = chain_lines(bench)
    mark = [line for line in lines if line.startswith("deckel-erreicht ")]
    assert mark, lines
    assert re.fullmatch(r"deckel-erreicht \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ bisher 58\.80\d*", mark[0]), mark
    assert (bench.out / "m7g.large" / "00-DECKEL-ERREICHT").is_file()


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_kette_deckel_counts_the_running_hours_of_the_box(tmp_path: Path) -> None:
    """57.50 USD before plus one hour at 1.5 USD/h is over 58.74; the same without the hour is not."""
    started = str(int(time.time()) - 3600)
    over = a_bench(tmp_path / "a", chain_values(BISHER_USD="57.50", SATZ_USD_H="1.5", BOX_START_EPOCH=started))
    assert run_chain(over).returncode == 83
    assert cells_run(over) == []
    under = a_bench(tmp_path / "b", chain_values(BISHER_USD="57.50", SATZ_USD_H="1.5"))
    assert run_chain(under).returncode == 0
    assert len(cells_run(under)) == 2


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_kette_without_the_vorpruefung_mark_does_not_start(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, chain_values(VORPRUEFUNG=""))
    answer = run_chain(bench)
    assert answer.returncode == 80, answer
    assert shutdowns(bench) == []
    assert cells_run(bench) == []


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_kette_without_a_readable_timer_does_not_start(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, chain_values())
    answer = run_chain(bench, {"GEPLANT_DATEI": (tmp_path / "nirgends" / "scheduled").as_posix()})
    assert answer.returncode == 81, answer
    assert cells_run(bench) == []


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_kette_at_the_safety_stop_stops_the_box_at_once(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, chain_values(BISHER_USD="71"))
    answer = run_chain(bench)
    assert answer.returncode == 82, answer
    assert shutdowns(bench) == ["shutdown -h now"]
    assert cells_run(bench) == []


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_kette_a_failed_cell_ends_the_chain_and_pulls_the_timer_forward(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, chain_values())
    answer = run_chain(bench, {"STUB_ZELLE_RC": "69"})
    assert answer.returncode == 84, answer
    assert len(cells_run(bench)) == 1
    calls = shutdowns(bench)
    assert calls[-1] == "shutdown -h +60", calls
    assert "shutdown -h +2" not in calls
    assert any(line.startswith("kette-abbruch zelle S-T rueckgabe 69") for line in chain_lines(bench))


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
@pytest.mark.parametrize(
    "broken",
    [
        {"DECKEL_USD": ""},
        {"DECKEL_USD": "viel"},
        {"SATZ_USD_H": "0"},
        {"BISHER_USD": "-1"},
        {"BOX_START_EPOCH": str(int(time.time()) + 3600)},
        {"ZELLEN": ""},
        {"ZELLEN": "St-T:standard:int8"},
        {"ZELLEN": "St-T:turbo:int8:teil"},
        {"ZELLEN": "St-T:standard:int8:halb"},
        {"ABBILD_DIGEST": "latest"},
    ],
)
def test_kette_refuses_incomplete_values(tmp_path: Path, broken: dict[str, str]) -> None:
    bench = a_bench(tmp_path, chain_values(**broken))
    answer = run_chain(bench)
    assert answer.returncode == 2, answer
    assert bench.calls() == []


def test_kette_shuts_down_only_in_the_timer_the_safety_stop_the_abort_and_the_end() -> None:
    code = code_of(CHAIN.read_text(encoding="utf-8"))
    shutdown_lines = sorted(line.strip() for line in code.splitlines() if "shutdown -h" in line)
    assert shutdown_lines == sorted(
        [
            'sudo shutdown -h +"$minuten" >/dev/null 2>&1 || true',
            "sudo shutdown -h now >/dev/null 2>&1 || true",
            'sudo shutdown -h +"$ABBRUCH_FRIST" >/dev/null 2>&1 || true',
            "sudo shutdown -h +2 >/dev/null 2>&1 || true",
        ]
    ), shutdown_lines
    start = code.index("deckel_erreicht() {")
    assert "shutdown" not in code[start : code.index("\n}\n", start)]


# The OOM closing line (since 01.10.2026): the gap of S-voll had no line that
# said whether the container fell. Positive control: a staged OOM kill with one
# restart and two kills in memory.events has to show up word for word.
@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_writes_the_oom_closing_line_from_inspect_and_memory_events(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    scope = tmp_path / "cgroup" / "system.slice" / "docker-stubkennung.scope"
    scope.mkdir(parents=True)
    events = ("low 0", "high 0", "max 7", "oom 3", "oom_kill 2")
    (scope / "memory.events").write_text("".join(f"{line}\n" for line in events), encoding="utf-8")
    bench.environment["STUB_OOM"] = "true 1 2026-10-01T06:07:48Z"
    answer = run_cell(bench, CELL_ARGUMENTS)
    assert answer.returncode == 0, answer
    lines = cell_lines(bench)
    expected = "oom oomkilled true restartcount 1 containerstart 2026-10-01T06:07:48Z memory-events oom 3 oom_kill 2"
    assert expected in lines, lines
    assert lines.index(expected) < lines.index("10-ZELLE-FERTIG St-T")


@pytest.mark.skipif(NO_SHELL, reason="no POSIX shell on this machine")
def test_cell_oom_closing_line_says_unlesbar_without_a_cgroup(tmp_path: Path) -> None:
    bench = a_bench(tmp_path, {})
    answer = run_cell(bench, CELL_ARGUMENTS)
    assert answer.returncode == 0, answer
    lines = cell_lines(bench)
    expected = (
        "oom oomkilled false restartcount 0 containerstart 2026-10-01T00:00:00Z "
        "memory-events oom unlesbar oom_kill unlesbar"
    )
    assert expected in lines, lines
