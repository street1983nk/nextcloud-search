#!/usr/bin/env python3
"""Record the admin page of the instance, one JSON line per reading.

This file is in the repository for the first time, and that is the point of it.
The semantic run of 05.09.2026 was watched by a statusbeobachter2.py that lives
on the box and nowhere else; the whole repository knows it only from the two
script lines that call it. Without it the watchman of the full run is blind,
because it reads the last line of these recordings instead of asking the instance
itself: the observer holds the session, and two ways to log in are two ways that
can break. Criterion 4 of this phase asks for a run that is repeatable from the
repository, so the observer arrives with it.

**The recording carries numbers and state words and NO NAME CARRIER.** No file
name, no path, no account name, not one of the example paths of the error list.
The reason is not tidiness: this file writes a raw file that is committed, and
the admin page answers with example paths out of the error list and the coverage
block, which are names of documents of a real instance (T-10-21). The way that is
kept is a projection onto a closed set of keys rather than a list of keys to
drop: a new field on the page cannot leak through a projection, and it would leak
through a filter that names what it removes.

The password is read from a file or from an environment variable and never from
an argument, because an argument stands in the process list of the box and in
every log that records the command (T-10-27).

The login is the cookie session of scripts/dev/probe_page_login.sh, including the
Origin header, and the header is not decoration: LoginController of Nextcloud 34
refuses a login whose origin is not a trusted domain before it looks at the
password at all, with the same redirect back to the form that a wrong password
produces. After the login one more page is fetched for a fresh data-requesttoken,
because the admin route is polled with that header exactly the way the page
script polls it; without it the route answers with a refusal and every recording
would be an error line.

A failed reading produces a recording with the key "fehler" instead of no
recording, so the gap is visible in the row: the watchman reads the last line,
and a line that is missing looks exactly like a line that was never due.

Standard library only, because it is copied onto the box and started there.

Call:

    export FINDLING_ADMIN_PASSWORD='...'
    ./96d-statusbeobachter.py <ziel.jsonl> <intervall-s> <passwortdatei> <adresse>
    ./96d-statusbeobachter.py status.jsonl 120 '' https://example.invalid --user admin

The password file may be the empty string, in which case the environment variable
is the only source. Whichever way it arrives, it never becomes an argument.
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

TOOL: Final = "96d-statusbeobachter"

# The route the page polls, declared in php/lib/Controller/SettingsController.php
# as a FrontpageRoute, so an admin route without an access attribute: the guard
# is a logged in administrator plus the request token of the session.
OVERVIEW_ROUTE: Final = "/apps/findling/admin/overview"
LOGIN_ROUTE: Final = "/login"

# The page the fresh request token is read from after the login. Any page of the
# instance carries it in its head; the admin settings page is the one this
# session is entitled to in any case.
TOKEN_ROUTE: Final = "/settings/admin"  # noqa: S105 - a route of the instance, not a credential
TOKEN_PATTERN: Final = re.compile(r'data-requesttoken="([^"]+)"')

# The name of the environment variable the password is read from unless the
# caller names another one. A name and never a value.
DEFAULT_PASSWORD_ENV: Final = "FINDLING_ADMIN_PASSWORD"  # noqa: S105 - a variable name, not a value
DEFAULT_USER: Final = "admin"

# The keys of one recording, and this tuple is the whole privacy guarantee of the
# file. Six counters, one state word, one flag, the nested pair, and the reading
# time of the observer itself.
COUNTER_KEYS: Final = (
    "indexed",
    "indexedPercent",
    "embedded",
    "embeddedPercent",
    "scheduled",
    "running",
)
BACKEND_KEYS: Final = ("indexed", "embedded")

# A state word is a short identifier such as "running" or "idle". The pattern is
# what keeps this one string field from becoming a way for a sentence, a path or
# a file name to travel: anything that does not match is dropped.
STATE_WORD: Final = re.compile(r"^[A-Za-z_]{1,32}$")

# Ceiling per request. Generous, because a reading that is late is a reading and a
# reading that timed out is a gap, and the interval of the observer is minutes.
REQUEST_TIMEOUT_SECONDS: Final = 30.0

# The error words of a reading that says the session is gone rather than that the
# instance is. They are the ones worth a second attempt, because over nineteen
# hours a session can end and an observer that then writes error lines until
# morning is an observer that stopped observing.
SESSION_LOST: Final = frozenset({"SessionGone", "HTTPError401", "HTTPError403", "HTTPError412"})

# The exit codes, so that a run that ends can be read from the outside: 3 the
# login was refused, 4 the password is nowhere to be found.
EXIT_LOGIN_REFUSED: Final = 3
EXIT_NO_PASSWORD: Final = 4


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _counter(value: object) -> int | None:
    """One counter as an int, or None for anything that is not a number."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return int(value)


def recording_of(answer: object) -> dict[str, object]:
    """One answer of the admin page, projected onto the keys of a recording.

    The projection is the privacy guarantee and the readability guarantee at the
    same time. Only the keys of COUNTER_KEYS, the state word, the flag and the
    two nested counters can appear, so no example path, no file name and no
    account name of the instance reaches the row; and the reader of the watchman
    finds the counters where it looks for them, which is under "backend".

    The reading time is the clock of the observer and not the "at" of the answer:
    what the row has to say is when the question was asked, and a value the answer
    chose is a second clock nobody compared.

    An answer that is not the shape of the overview becomes a recording with the
    error key. That is a line the watchman reads as three times unklar, and it is
    a great deal better than a line of zeroes.
    """
    if not isinstance(answer, dict):
        return {"at": _now(), "fehler": "MalformedAnswer"}
    if "error" in answer:
        # The route answers 500 with a static sentence rather than a half filled
        # structure. The sentence itself stays out of the row: what belongs in the
        # row is that this reading failed, not what the instance said about it.
        return {"at": _now(), "fehler": "OverviewError"}

    recording: dict[str, object] = {"at": _now()}
    for key in COUNTER_KEYS:
        recording[key] = _counter(answer.get(key))

    state = answer.get("runState")
    recording["runState"] = state if isinstance(state, str) and STATE_WORD.match(state) else None

    reachable = answer.get("backendReachable")
    recording["backendReachable"] = reachable if isinstance(reachable, bool) else None

    backend = answer.get("backend")
    nested = backend if isinstance(backend, dict) else {}
    recording["backend"] = {key: _counter(nested.get(key)) for key in BACKEND_KEYS}
    return recording


def _opener() -> urllib.request.OpenerDirector:
    """One opener with one cookie jar, which is the session for the whole run."""
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def _get(opener: urllib.request.OpenerDirector, url: str, token: str | None = None) -> tuple[str, str]:
    """One GET with the session, returning the body and the address it landed on.

    The landing address is half of the answer: a request without a valid session
    is redirected to the login form, and urllib follows that redirect, so the body
    alone would look like a page rather than like a refusal.
    """
    headers = {"Accept": "application/json"}
    if token:
        headers["requesttoken"] = token
    request = urllib.request.Request(url, headers=headers)  # noqa: S310 - the scheme is checked in _checked_base_url
    with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as answer:
        return answer.read().decode("utf-8", "replace"), answer.geturl()


def log_in(opener: urllib.request.OpenerDirector, base_url: str, user: str, password: str) -> str | None:
    """The cookie login, and the reason it failed, or None when it worked.

    A reason and not an exception, because this function is called twice: once
    before the run, where a refusal is the end of the observer, and once during
    it, where a refusal has to become a recording and the loop has to go on.
    """
    try:
        form, _ = _get(opener, f"{base_url}{LOGIN_ROUTE}")
    except (urllib.error.URLError, OSError) as error:
        return f"the login form could not be fetched ({type(error).__name__})"

    found = TOKEN_PATTERN.search(form)
    if not found:
        return "the login form carries no data-requesttoken, so the login cannot be signed"

    payload = urllib.parse.urlencode(
        {"user": user, "password": password, "requesttoken": found.group(1)},
    ).encode()
    request = urllib.request.Request(  # noqa: S310 - the scheme is checked in _checked_base_url
        f"{base_url}{LOGIN_ROUTE}",
        data=payload,
        headers={"Origin": base_url},
    )
    try:
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as answer:
            landed = urllib.parse.urlparse(answer.geturl()).path
    except (urllib.error.URLError, OSError) as error:
        return f"the login did not answer ({type(error).__name__})"

    if landed.rstrip("/").endswith(LOGIN_ROUTE):
        # The same redirect a wrong password produces, which is why the Origin
        # header above is a condition and not a nicety.
        return "the instance sent the account back to the login form"
    return None


def request_token(opener: urllib.request.OpenerDirector, base_url: str) -> str | None:
    """A fresh request token for this session, read out of the head of a page."""
    try:
        body, _ = _get(opener, f"{base_url}{TOKEN_ROUTE}")
    except (urllib.error.URLError, OSError):
        return None
    found = TOKEN_PATTERN.search(body)
    return found.group(1) if found else None


def read_overview(opener: urllib.request.OpenerDirector, base_url: str, token: str | None) -> dict[str, object]:
    """One reading, already projected, error recording included.

    Every failure ends up as a recording rather than as an exception: nineteen
    hours of readings must not end because one of them did.
    """
    try:
        body, landed = _get(opener, f"{base_url}{OVERVIEW_ROUTE}", token)
    except urllib.error.HTTPError as error:
        return {"at": _now(), "fehler": f"HTTPError{error.code}"}
    except (urllib.error.URLError, OSError) as error:
        return {"at": _now(), "fehler": type(error).__name__}

    if urllib.parse.urlparse(landed).path.rstrip("/").endswith(LOGIN_ROUTE):
        return {"at": _now(), "fehler": "SessionGone"}
    try:
        return recording_of(json.loads(body))
    except ValueError:
        return {"at": _now(), "fehler": "NotJson"}


def _password(arguments: argparse.Namespace) -> str:
    """The password, out of the file or out of the environment, never an argument."""
    if arguments.passwortdatei:
        candidate = Path(arguments.passwortdatei)
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8").strip()
    return os.environ.get(arguments.password_env, "")


def _checked_base_url(raw: str) -> str:
    """The address, once, with its scheme checked before anything is opened."""
    parsed = urllib.parse.urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise argparse.ArgumentTypeError("the address has to be an http or https address")
    return raw.rstrip("/")


def _positive(raw: str) -> int:
    number = int(raw)
    if number < 1:
        raise argparse.ArgumentTypeError("has to be at least one")
    return number


def _parse(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=f"{TOOL}.py",
        description=(
            "Record the admin page of the instance as one JSON line per reading. The recording "
            "carries counters and state words only, because the raw file it writes is committed."
        ),
    )
    parser.add_argument("ziel", help="The JSONL file the recordings are appended to")
    parser.add_argument("intervall", type=_positive, help="Seconds between two readings")
    parser.add_argument(
        "passwortdatei",
        help=(
            "Path of the file the password is read from, or the empty string to use the "
            "environment variable only. The value is never an argument."
        ),
    )
    parser.add_argument("adresse", type=_checked_base_url, help="Address of the instance, http or https")
    parser.add_argument("--user", default=DEFAULT_USER, help=f"Administrator account (default {DEFAULT_USER})")
    parser.add_argument(
        "--password-env",
        default=DEFAULT_PASSWORD_ENV,
        help=f"Name of the environment variable the password is read from (default {DEFAULT_PASSWORD_ENV})",
    )
    parser.add_argument(
        "--deckel",
        type=int,
        default=0,
        help=(
            "Stop after this many readings. The default 0 means no cap, because the watchman "
            "ends the observer; a cap is the insurance against an observer nobody ends."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _parse(argv)
    password = _password(arguments)
    if not password:
        where = arguments.passwortdatei or "(no file was named)"
        print(f"{TOOL}: no password in {where} and none in the environment", file=sys.stderr)
        return EXIT_NO_PASSWORD

    opener = _opener()
    refusal = log_in(opener, arguments.adresse, arguments.user, password)
    if refusal:
        print(f"{TOOL}: {refusal}", file=sys.stderr)
        return EXIT_LOGIN_REFUSED
    token = request_token(opener, arguments.adresse)

    target = Path(arguments.ziel)
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"{TOOL}: logged in as {arguments.user}, every {arguments.intervall} s into {target.name}")

    readings = 0
    with target.open("a", encoding="utf-8") as row:
        while arguments.deckel == 0 or readings < arguments.deckel:
            recording = read_overview(opener, arguments.adresse, token)
            # A lost session is the one failure worth repairing on the spot: over
            # nineteen hours a session can end, and an observer that then writes
            # error lines until morning is an observer that stopped observing.
            lost = recording.get("fehler") in SESSION_LOST
            if lost and log_in(opener, arguments.adresse, arguments.user, password) is None:
                token = request_token(opener, arguments.adresse)
                recording = read_overview(opener, arguments.adresse, token)
            row.write(json.dumps(recording, ensure_ascii=False) + "\n")
            row.flush()
            readings += 1
            time.sleep(arguments.intervall)
    return 0


if __name__ == "__main__":
    sys.exit(main())
