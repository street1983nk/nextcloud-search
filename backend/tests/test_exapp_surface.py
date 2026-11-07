"""The surface of the ExApp toward Nextcloud, pinned exactly (plan 42-09, vector 9).

ExAppRequired on a companion route only says "some ExApp", so what the
container itself offers and asks for has to be held on the Python side:

- The route table of backend/appinfo/info.xml is the only surface a browser
  session or an app password reaches through /exapps/. It is pinned here as a
  whole, six routes in this order (five until plan 43-04 added /coverage),
  each with url, verb, access_level, headers_to_exclude and
  bruteforce_protection. PUBLIC and a non empty
  headers_to_exclude are in addition reported by a rule of their own, because
  either would hand the route to somebody the table never meant.
- AppAPI lets an ExApp register surfaces at run time without any change of the
  manifest: UI entries, occ commands, providers, webhooks and event listeners.
  backend/src must not call those registration surfaces of nc_py_api, must not
  name a path under app_api/, and every OCS path it names belongs to the
  companion, /ocs/v2.php/apps/findling/.

The Python sources are read with ast, so a comment never counts and a
docstring (an expression made of one string as the first statement of a
module, class or function) is not checked; nc/client.py names "/ocs/" in one.
"""

from __future__ import annotations

import ast
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_INFO_XML = REPO_ROOT / "backend" / "appinfo" / "info.xml"
BACKEND_SRC = REPO_ROOT / "backend" / "src"

Route = tuple[str | None, str | None, str | None, str | None, str | None]

# Written by hand from backend/appinfo/info.xml on 2026-11-05: url, verb,
# access_level, headers_to_exclude, bruteforce_protection.
EXPECTED_ROUTES: tuple[Route, ...] = (
    ("^/status$", "GET", "ADMIN", "[]", "[401]"),
    ("^/rates$", "GET", "ADMIN", "[]", "[401]"),
    ("^/diagnose$", "GET", "ADMIN", "[]", "[401]"),
    ("^/probe$", "POST", "ADMIN", "[]", "[401]"),
    ("^/probe/state$", "GET", "ADMIN", "[]", "[401]"),
    # Plan 43-04 (issue #25): the per document coverage of the admin page.
    ("^/coverage$", "POST", "ADMIN", "[]", "[401]"),
)
_FIELDS = ("url", "verb", "access_level", "headers_to_exclude", "bruteforce_protection")

OCS_PREFIX = "/ocs/v2.php/apps/findling/"
BANNED_ATTRIBUTES = ("ui", "occ_commands", "providers", "webhooks", "events_listener")
MIN_OCS_PATHS = 9  # eleven OCS strings in nc/client.py on 2026-11-05

_HEADERS_EMPTY = re.compile(r"^\[\s*\]$")


def routes_of(text: str) -> tuple[Route, ...]:
    """The route table of an ExApp info.xml, in document order."""
    root = ET.fromstring(text.encode("utf-8"))  # noqa: S314 - a file of this repository, not foreign input
    routes: list[Route] = []
    for route in root.iter("route"):
        values: list[str | None] = []
        for field in _FIELDS:
            child = route.find(field)
            values.append(None if child is None else (child.text or "").strip())
        routes.append((values[0], values[1], values[2], values[3], values[4]))
    return tuple(routes)


def scan_routes(routes: tuple[Route, ...]) -> list[str]:
    """The table against EXPECTED_ROUTES, and the two rules of their own."""
    findings: list[str] = []
    if routes != EXPECTED_ROUTES:
        findings.append(f"the route table is {routes!r}, expected {EXPECTED_ROUTES!r}")
    for url, _verb, access_level, headers, _bruteforce in routes:
        if access_level == "PUBLIC":
            findings.append(f"the route {url} is PUBLIC")
        if headers is None or not _HEADERS_EMPTY.match(headers):
            findings.append(f"the route {url} excludes headers {headers!r}")
    return findings


def _docstrings(tree: ast.Module) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                ids.add(id(first.value))
    return ids


def scan_source(path: str, source: str) -> tuple[list[str], list[str]]:
    """Findings and the OCS paths of one Python source file."""
    tree = ast.parse(source)
    docstrings = _docstrings(tree)
    findings: list[str] = []
    ocs_paths: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in BANNED_ATTRIBUTES:
            findings.append(f"{path}:{node.lineno}: attribute .{node.attr}")
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str) or id(node) in docstrings:
            continue
        value = node.value
        if "app_api/" in value:
            findings.append(f"{path}:{node.lineno}: path under app_api/ {value!r}")
        if value.startswith("/ocs"):
            ocs_paths.append(value)
            if not value.startswith(OCS_PREFIX):
                findings.append(f"{path}:{node.lineno}: OCS path outside {OCS_PREFIX} {value!r}")
    return findings, ocs_paths


# The real tree.


def test_the_route_table_is_exactly_the_expected_one() -> None:
    routes = routes_of(BACKEND_INFO_XML.read_text(encoding="utf-8"))
    assert routes == EXPECTED_ROUTES
    assert scan_routes(routes) == []


def test_backend_src_registers_nothing_at_run_time() -> None:
    findings: list[str] = []
    ocs_paths: list[str] = []
    for path in sorted(BACKEND_SRC.rglob("*.py")):
        found, paths = scan_source(path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8"))
        findings.extend(found)
        ocs_paths.extend(paths)
    assert findings == []
    assert len(ocs_paths) >= MIN_OCS_PATHS


# Probes.


def _replace(routes: tuple[Route, ...], index: int, field: int, value: str | None) -> tuple[Route, ...]:
    changed = list(routes)
    values = list(changed[index])
    values[field] = value
    changed[index] = (values[0], values[1], values[2], values[3], values[4])
    return tuple(changed)


def test_a_sixth_route_is_reported() -> None:
    routes = (*EXPECTED_ROUTES, ("^/extra$", "GET", "ADMIN", "[]", "[401]"))
    assert len(scan_routes(routes)) >= 1


def test_a_public_route_is_reported_twice() -> None:
    findings = scan_routes(_replace(EXPECTED_ROUTES, 1, 2, "PUBLIC"))
    assert len(findings) == 2
    assert "the route ^/rates$ is PUBLIC" in findings


def test_a_user_route_is_reported() -> None:
    assert len(scan_routes(_replace(EXPECTED_ROUTES, 0, 2, "USER"))) == 1


def test_excluded_headers_are_reported_twice() -> None:
    findings = scan_routes(_replace(EXPECTED_ROUTES, 2, 3, '["X"]'))
    assert len(findings) == 2
    assert "the route ^/diagnose$ excludes headers '[\"X\"]'" in findings


def test_a_missing_bruteforce_protection_is_reported() -> None:
    assert len(scan_routes(_replace(EXPECTED_ROUTES, 3, 4, None))) >= 1


def test_a_swapped_order_is_reported() -> None:
    routes = (EXPECTED_ROUTES[1], EXPECTED_ROUTES[0], *EXPECTED_ROUTES[2:])
    assert len(scan_routes(routes)) == 1


def test_the_reader_sees_a_changed_access_level() -> None:
    text = BACKEND_INFO_XML.read_text(encoding="utf-8").replace(
        "<access_level>ADMIN</access_level>", "<access_level>USER</access_level>", 1
    )
    assert routes_of(text)[0][2] == "USER"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ('X = "/ocs/v2.php/apps/app_api/api/v1/ui/files-actions-menu"\n', 2),
        ('X = "/ocs/v2.php/cloud/users"\n', 1),
        ('X = f"/ocs/v1.php/apps/files_sharing/{1}"\n', 1),
        ('X = "/index.php/apps/app_api/x"\n', 1),
        ("def f(nc):\n    return nc.ui.resources\n", 1),
        ("def f(nc):\n    return nc.occ_commands.register\n", 1),
        ("def f(nc):\n    return nc.providers.speech_to_text\n", 1),
        ("def f(nc):\n    return nc.webhooks.register\n", 1),
        ("def f(nc):\n    return nc.events_listener.register\n", 1),
    ],
)
def test_every_runtime_surface_is_reported(source: str, expected: int) -> None:
    findings, _paths = scan_source("x.py", source)
    assert len(findings) == expected


def test_own_ocs_paths_and_docstrings_are_clean() -> None:
    source = (
        '"""Talks to /ocs/v2.php/apps/app_api/ never, see the docstring."""\n'
        'A = "/ocs/v2.php/apps/findling/profile"\n'
        'B = f"/ocs/v2.php/apps/findling/files/{1}"\n'
        "def f():\n"
        '    """The /ocs/ route of the companion."""\n'
        "    return A\n"
        "# nc.ui.resources in a comment\n"
    )
    findings, paths = scan_source("x.py", source)
    assert findings == []
    assert paths == ["/ocs/v2.php/apps/findling/profile", "/ocs/v2.php/apps/findling/files/"]
