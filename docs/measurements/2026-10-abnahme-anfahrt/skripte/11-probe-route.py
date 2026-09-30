#!/usr/bin/env python3
"""The probe of the product, driven headless over its own admin route.

**DIESE FASSUNG IST NICHT GEFAHREN.** No raw file lies next to it; what it
reads on the box is read on the trip.

Why over the route and not over a shortcut. D-28-05 wants every cell of
standard, performance or fp32 to start with the probe the admin page starts,
so the verdict of the trip is the verdict an admin would have seen. The route
is php/lib/Controller/ProfileSettingsController.php: POST
/apps/findling/admin/profile/check with profile and precision starts the
probe, GET on the same route returns its state and runs the takeOver of
ProbeService idempotently, so a "fits" stores the profile by itself. POST
/apps/findling/admin/profile takes the downward ways only, and that is the way
back to economy/int8 before each nought state (pitfall 2 of the research).

The session is the one of scripts/dev/probe_page_login.sh: the login form for
the data-requesttoken, the login with an Origin header (Nextcloud refuses a
login without a trusted origin with the same redirect a wrong password gets),
then a page of the session for a fresh token, sent as the requesttoken header
on every call, GET included (SecurityMiddleware).

The password comes from a file named in FINDLING_ADMIN_PWFILE or from
FINDLING_ADMIN_PASSWORD, never from an argument: an argument stands in the
process list of the box and in every log that records the command (T-28-05).
Any argument that looks like a password option is refused. The cookie jar is a
file in a directory of its own made by tempfile.mkdtemp, and that directory is
removed in a finally block, so no session outlives the call (T-28-06). Neither
the address nor the password is ever printed.

Standard library only, because it is copied onto the box and started there.

Environment:
    FINDLING_BASE_URL       http or https address of the instance (required)
    FINDLING_ADMIN_USER     the administrator account, default admin
    FINDLING_ADMIN_PWFILE   file with the password (first choice)
    FINDLING_ADMIN_PASSWORD the password (second choice)
    PROBE_FRIST             seconds until done, default 900, for fp32 900 plus
                            the 600 s download cap of the product
    PROBE_TAKT              seconds between two readings, default 2
    PROBE_SEITE             the page the session token is read from

Subcommands:
    pruefen <profil> <praezision>   standard|performance and int8|fp32; one
                                    line per reading, then the verdict line
    abwaerts                        economy/int8 over the save route
    uebersicht                      one line out of the admin overview, a
                                    closed set of fields and nothing else

Exit codes:
    0   fits (pruefen), saved (abwaerts), read (uebersicht)
    2   usage: unknown subcommand or target, a password as an argument, or no
        password in file or environment
    30  the probe said narrow; 10-zelle.sh forces the profile over occ
    31  the probe said nofit; 10-zelle.sh forces the profile over occ
    32  the frist ran out before the probe reached done
    33  the probe did not start (busy, unreachable, rebuilding, invalid)
    34  the login did not take
    35  a route answered with an error or with no JSON
    36  done with a verdict outside fits, narrow and nofit
    37  abwaerts: the save route did not save
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import re
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

EXIT_USAGE = 2
EXIT_NARROW = 30
EXIT_NOFIT = 31
EXIT_FRIST = 32
EXIT_NOT_STARTED = 33
EXIT_LOGIN = 34
EXIT_ROUTE = 35
EXIT_UNKNOWN_VERDICT = 36
EXIT_NOT_SAVED = 37

DEFAULT_FRIST_SECONDS = 900
# PROBE_DOWNLOAD_SECONDS of the product, the cap on fetching the fp32 weights.
FP32_DOWNLOAD_SECONDS = 600
DEFAULT_TAKT_SECONDS = 2.0
DEFAULT_USER = "admin"
DEFAULT_PAGE = "/settings/admin/findling"

CHECK_ROUTE = "/apps/findling/admin/profile/check"
SAVE_ROUTE = "/apps/findling/admin/profile"
OVERVIEW_ROUTE = "/apps/findling/admin/overview"

PROBE_PROFILES = ("standard", "performance")
PRECISIONS = ("int8", "fp32")
VERDICT_CODES = {"fits": 0, "narrow": EXIT_NARROW, "nofit": EXIT_NOFIT}

TOKEN_IN_PAGE = re.compile(r'data-requesttoken="([^"]+)"')

# The overview fields that go into the line, under the name the line gives
# them. A projection onto a closed set, so an example path of the page cannot
# leak into a raw file (T-10-21 pattern of 96d-statusbeobachter.py).
OVERVIEW_FIELDS = (
    ("effective", "profileEffective"),
    ("guardEffective", "guardEffective"),
    ("guardCause", "guardCause"),
    ("slotsInForce", "slotsInForce"),
    ("throttled", "slotsThrottled"),
    ("backendReachable", "backendReachable"),
    ("scheduled", "scheduled"),
    ("running", "running"),
    ("indexed", "indexed"),
    ("embedded", "embedded"),
    ("storedPrecision", "storedPrecision"),
    ("profileSaved", "profileSaved"),
)
# indexed and embedded are counted by the backend container, and the guard
# fields come out of its status answer (AdminViewService::backend); the overview
# carries all six in its backend block, and the top level only as a fallback.
# On 30.09.2026 the box showed slotsInForce=1 in the backend block while this
# tool read the top level and printed keine, so the gate of 10-zelle.sh waited.
BACKEND_FIELDS = frozenset({"indexed", "embedded", "guardEffective", "guardCause", "slotsInForce", "slotsThrottled"})
WORD = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")


class Refused(Exception):
    """A call that ends the tool with one exit code of the catalogue."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code


def utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def say(line: str) -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def complain(line: str) -> None:
    sys.stderr.write(f"11-probe-route: {line}\n")


def refuse_password_arguments(argv: Sequence[str]) -> None:
    for argument in argv:
        lowered = argument.lower()
        if lowered.startswith("-") and ("pass" in lowered or "pw" in lowered):
            raise Refused(EXIT_USAGE, "das Passwort kommt nur aus Datei oder Umgebung, nie als Argument")


def password() -> str:
    path = os.environ.get("FINDLING_ADMIN_PWFILE", "")
    if path:
        try:
            value = Path(path).read_text(encoding="utf-8").strip("\r\n")
        except OSError as error:
            raise Refused(EXIT_USAGE, "die Passwortdatei ist nicht lesbar (Datei oder Umgebung)") from error
        if value:
            return value
    value = os.environ.get("FINDLING_ADMIN_PASSWORD", "")
    if value:
        return value
    raise Refused(EXIT_USAGE, "kein Passwort in Datei oder Umgebung (FINDLING_ADMIN_PWFILE, FINDLING_ADMIN_PASSWORD)")


def base_url() -> str:
    base = os.environ.get("FINDLING_BASE_URL", "").rstrip("/")
    if urllib.parse.urlsplit(base).scheme not in {"http", "https"}:
        raise Refused(EXIT_USAGE, "FINDLING_BASE_URL muss eine http- oder https-Adresse sein")
    return base


def seconds_from(name: str, default: float) -> float:
    raw = os.environ.get(name, "")
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as error:
        raise Refused(EXIT_USAGE, f"{name} ist keine Zahl") from error
    if value < 0:
        raise Refused(EXIT_USAGE, f"{name} ist negativ")
    return value


class Session:
    """A cookie session of the admin, its jar in a directory of its own."""

    def __init__(self, base: str, jar_path: Path) -> None:
        self.base = base
        self.jar = http.cookiejar.MozillaCookieJar(str(jar_path))
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.request_token = ""

    def _open(
        self,
        path: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        method: str = "GET",
    ) -> tuple[int, str, str]:
        # The one place a request is built. The scheme of the base is checked in
        # base_url to be http or https, and every path is a constant of this file
        # or PROBE_SEITE, so no file: or custom scheme can reach the opener.
        request = urllib.request.Request(  # noqa: S310 - scheme checked in base_url
            self.base + path, data=data, headers=headers or {}, method=method
        )
        try:
            with self.opener.open(request, timeout=60) as response:
                return response.status, response.geturl(), response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", "replace")
            return error.code, error.geturl(), body
        except (urllib.error.URLError, OSError) as error:
            raise Refused(EXIT_ROUTE, f"die Instanz antwortet nicht ({type(error).__name__})") from error

    def login(self, user: str, phrase: str) -> None:
        _, _, form = self._open("/login")
        found = TOKEN_IN_PAGE.search(form)
        if found is None:
            raise Refused(EXIT_LOGIN, "die Anmeldeseite traegt kein data-requesttoken")
        body = urllib.parse.urlencode({"user": user, "password": phrase, "requesttoken": found.group(1)}).encode()
        self._open("/login", data=body, headers={"Origin": self.base}, method="POST")
        page = os.environ.get("PROBE_SEITE", DEFAULT_PAGE)
        if not page.startswith("/"):
            raise Refused(EXIT_USAGE, "PROBE_SEITE muss ein Pfad sein, der mit / beginnt")
        _, final, text = self._open(page)
        found = TOKEN_IN_PAGE.search(text)
        if urllib.parse.urlsplit(final).path.startswith("/login") or found is None:
            raise Refused(EXIT_LOGIN, "die Anmeldung hat nicht gegriffen")
        self.request_token = found.group(1)
        self.jar.save(ignore_discard=True)

    def call(self, method: str, route: str, payload: dict[str, str] | None = None) -> tuple[int, dict[str, Any]]:
        headers = {"requesttoken": self.request_token, "Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        status, _, text = self._open(route, data=data, headers=headers, method=method)
        try:
            answer = json.loads(text)
        except ValueError as error:
            raise Refused(EXIT_ROUTE, f"{method} {route} antwortet ohne JSON, HTTP{status}") from error
        if not isinstance(answer, dict):
            raise Refused(EXIT_ROUTE, f"{method} {route} antwortet ohne Objekt, HTTP{status}")
        return status, answer


def word(value: object) -> str:
    """A value as one word of the line: numbers, flags and closed words only."""
    if value is None:
        return "keine"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    text = str(value)
    return text if WORD.match(text) else "unlesbar"


def reading_line(elapsed: float, answer: dict[str, Any]) -> str:
    found = answer.get("result")
    result: dict[str, Any] = found if isinstance(found, dict) else {}
    numbers = result.get("numbers") if result else None
    return (
        f"t={round(elapsed)}s state={word(answer.get('state'))} step={word(answer.get('step'))} "
        f"bytes={word(answer.get('bytesDone'))}/{word(answer.get('bytesTotal'))} "
        f"verdict={word(result.get('verdict') if result else None)} "
        f"cause={word(result.get('cause') if result else None)} "
        f"numbers={json.dumps(numbers, sort_keys=True) if isinstance(numbers, dict) else 'null'}"
    )


def command_pruefen(session: Session, profile: str, precision: str) -> int:
    default = DEFAULT_FRIST_SECONDS + (FP32_DOWNLOAD_SECONDS if precision == "fp32" else 0)
    frist = seconds_from("PROBE_FRIST", default)
    takt = seconds_from("PROBE_TAKT", DEFAULT_TAKT_SECONDS)
    say(f"probe-start {utc()} ziel {profile}/{precision} frist-s {round(frist)}")
    status, started = session.call("POST", CHECK_ROUTE, {"profile": profile, "precision": precision})
    say(f"POST check: code={word(started.get('code'))} started={word(started.get('started'))} HTTP{status}")
    if started.get("started") is not True:
        say(f"probe-nicht-gestartet code {word(started.get('code'))}")
        return EXIT_NOT_STARTED
    begin = time.monotonic()
    while True:
        time.sleep(takt)
        elapsed = time.monotonic() - begin
        status, answer = session.call("GET", CHECK_ROUTE)
        say(reading_line(elapsed, answer))
        result = answer.get("result")
        # A result of an earlier probe for another target is not this verdict.
        if answer.get("state") == "done" and isinstance(result, dict):
            target = (result.get("profile"), result.get("precision"))
            if target == (profile, precision):
                return verdict_of(result)
        if elapsed >= frist:
            say(f"probe-frist-ueberschritten {utc()} nach-s {round(elapsed)}")
            return EXIT_FRIST


def verdict_of(result: dict[str, Any]) -> int:
    verdict = result.get("verdict")
    numbers = result.get("numbers")
    shown = json.dumps(numbers, sort_keys=True) if isinstance(numbers, dict) else "null"
    if verdict == "fits":
        say("verdikt fits erzwungen nein")
        return 0
    if verdict in VERDICT_CODES:
        say(f"verdikt {verdict} ursache {word(result.get('cause'))} numbers {shown}")
        return VERDICT_CODES[str(verdict)]
    say(f"verdikt unbekannt {word(verdict)}")
    return EXIT_UNKNOWN_VERDICT


def command_abwaerts(session: Session) -> int:
    status, answer = session.call("POST", SAVE_ROUTE, {"profile": "economy", "precision": "int8"})
    say(f"abwaerts code={word(answer.get('code'))} saved={word(answer.get('saved'))} HTTP{status}")
    return 0 if answer.get("saved") is True else EXIT_NOT_SAVED


def command_uebersicht(session: Session) -> int:
    status, answer = session.call("GET", OVERVIEW_ROUTE)
    found = answer.get("backend")
    backend: dict[str, Any] = found if isinstance(found, dict) else {}
    parts = [f"uebersicht HTTP{status}"]
    for name, key in OVERVIEW_FIELDS:
        value = backend.get(key) if key in BACKEND_FIELDS and key in backend else answer.get(key)
        parts.append(f"{name}={word(value)}")
    say(" ".join(parts))
    return 0 if status == 200 else EXIT_ROUTE


def usage() -> int:
    complain("Benutzung: 11-probe-route.py pruefen <standard|performance> <int8|fp32> | abwaerts | uebersicht")
    return EXIT_USAGE


def parse(argv: Sequence[str]) -> tuple[str, str, str] | None:
    if not argv:
        return None
    command, rest = argv[0], list(argv[1:])
    if command == "pruefen" and len(rest) == 2 and rest[0] in PROBE_PROFILES and rest[1] in PRECISIONS:
        return command, rest[0], rest[1]
    if command in {"abwaerts", "uebersicht"} and not rest:
        return command, "", ""
    return None


def main(argv: Sequence[str]) -> int:
    try:
        refuse_password_arguments(argv)
        parsed = parse(argv)
        if parsed is None:
            return usage()
        base = base_url()
        phrase = password()
    except Refused as refusal:
        complain(str(refusal))
        return refusal.code
    command, profile, precision = parsed
    jar_dir = Path(tempfile.mkdtemp(prefix="findling-probe-"))
    try:
        session = Session(base, jar_dir / "cookies.txt")
        session.login(os.environ.get("FINDLING_ADMIN_USER", DEFAULT_USER), phrase)
        if command == "pruefen":
            return command_pruefen(session, profile, precision)
        if command == "abwaerts":
            return command_abwaerts(session)
        return command_uebersicht(session)
    except Refused as refusal:
        complain(str(refusal))
        return refusal.code
    finally:
        shutil.rmtree(jar_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
