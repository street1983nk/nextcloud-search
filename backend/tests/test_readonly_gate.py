"""Gate A: the static read-only invariant (IDX-07).

Findling never modifies user files. This gate exists before the first read path
does, because the documented data loss class in Nextcloud search apps came from a
write path that nobody reviewed. The gate parses every module under
``backend/src/findling`` and asserts three invariants:

1. Only ``findling/nc/client.py`` imports ``nc_py_api``.
2. ``findling/nc/client.py`` contains none of the writing identifiers of
   ``nc_py_api.files`` and no ``set_user``.
3. No call of ``nc.ocs`` or of the raw session adapter uses PUT, POST, PATCH or
   DELETE on a path outside an explicit allowlist. The allowlist is empty in
   phase 1.

The self test group below is the reason this file has value while the package is
still empty: a gate that only runs against an empty package is vacuously green
and would not catch a later breach.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# Relative to the package root, posix separators. The single module that is
# allowed to talk to nc_py_api at all.
CLIENT_MODULE = "nc/client.py"

NC_MODULE = "nc_py_api"

# Writing methods of nc_py_api.files plus set_user, which would let the backend
# act as another user. Later phases may extend this set, never shrink it.
FORBIDDEN_IDENTIFIERS = frozenset(
    {
        "set_user",
        "upload",
        "upload_stream",
        "delete",
        "move",
        "copy",
        "mkdir",
        "makedirs",
        "trash",
    }
)

WRITING_HTTP_METHODS = frozenset({"PUT", "POST", "PATCH", "DELETE"})

# Entry points that take an HTTP method as their first argument.
OCS_ENTRY_POINTS = frozenset({"ocs", "request", "request_json"})

# Receiver names that mark a call as going out to Nextcloud rather than into a
# local data structure. Keeps `index_writer.delete(...)` out of invariant 3.
REMOTE_RECEIVERS = frozenset({"nc", "ocs", "_session", "session", "adapter"})

# Paths the backend may write to over OCS. Empty in phase 1: the container writes
# nothing back into Nextcloud. Every future entry needs a threat model note.
OCS_WRITE_ALLOWLIST: frozenset[str] = frozenset()


def _imports_nc_py_api(module: str | None) -> bool:
    return module is not None and (module == NC_MODULE or module.startswith(f"{NC_MODULE}."))


def _string_argument(call: ast.Call, position: int, *keywords: str) -> str | None:
    """Return a literal string argument by position or by keyword name."""
    if len(call.args) > position:
        candidate = call.args[position]
        if isinstance(candidate, ast.Constant) and isinstance(candidate.value, str):
            return candidate.value
    for keyword in call.keywords:
        if keyword.arg in keywords and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            if isinstance(value, str):
                return value
    return None


def _receiver_names(node: ast.expr) -> set[str]:
    """Collect the identifiers of the receiver chain, e.g. nc._session -> {nc, _session}."""
    names: set[str] = set()
    current: ast.expr | None = node
    while current is not None:
        if isinstance(current, ast.Attribute):
            names.add(current.attr)
            current = current.value
        elif isinstance(current, ast.Name):
            names.add(current.id)
            current = None
        elif isinstance(current, ast.Call):
            current = current.func
        else:
            current = None
    return names


def _writing_request(call: ast.Call) -> tuple[str, str | None] | None:
    """Return (http method, path) when the call writes to Nextcloud, else None."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None

    if func.attr in OCS_ENTRY_POINTS:
        method = _string_argument(call, 0, "method")
        if method is None or method.upper() not in WRITING_HTTP_METHODS:
            return None
        return method.upper(), _string_argument(call, 1, "path", "url", "path_and_query")

    if func.attr.upper() in WRITING_HTTP_METHODS and _receiver_names(func.value) & REMOTE_RECEIVERS:
        return func.attr.upper(), _string_argument(call, 0, "path", "url")

    return None


def scan_source(relative_path: str, source: str) -> list[str]:
    """Return one message per violated invariant, empty list when clean."""
    normalized = relative_path.replace("\\", "/")
    is_client = normalized == CLIENT_MODULE or normalized.endswith(f"/{CLIENT_MODULE}")
    tree = ast.parse(source, filename=relative_path)
    violations: list[str] = []

    for node in ast.walk(tree):
        if not is_client:
            if isinstance(node, ast.Import):
                violations += [
                    f"{normalized}:{node.lineno}: invariant 1, {alias.name} may only be imported by {CLIENT_MODULE}"
                    for alias in node.names
                    if _imports_nc_py_api(alias.name)
                ]
            elif isinstance(node, ast.ImportFrom) and _imports_nc_py_api(node.module):
                violations.append(
                    f"{normalized}:{node.lineno}: invariant 1, {node.module} may only be imported by {CLIENT_MODULE}"
                )

        if is_client:
            identifier: str | None = None
            lineno = 0
            if isinstance(node, ast.Attribute):
                identifier, lineno = node.attr, node.lineno
            elif isinstance(node, ast.Name):
                identifier, lineno = node.id, node.lineno
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                identifier, lineno = node.name, node.lineno
            if identifier in FORBIDDEN_IDENTIFIERS:
                violations.append(f"{normalized}:{lineno}: invariant 2, writing identifier {identifier}")

        if isinstance(node, ast.Call):
            request = _writing_request(node)
            if request is not None:
                method, path = request
                if path is None or path not in OCS_WRITE_ALLOWLIST:
                    target = path if path is not None else "an unknown path"
                    violations.append(f"{normalized}:{node.lineno}: invariant 3, {method} on {target}")

    return violations


def _package_modules() -> list[tuple[str, str]]:
    """Return (relative posix path, source) for every module of the package."""
    modules: list[tuple[str, str]] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        relative = path.relative_to(PACKAGE_ROOT).as_posix()
        modules.append((relative, path.read_text(encoding="utf-8")))
    return modules


def test_import_of_nc_py_api_outside_the_client_is_a_violation() -> None:
    violations = scan_source("api/search.py", "import nc_py_api\n")

    assert len(violations) == 1
    assert "invariant 1" in violations[0]


def test_import_of_nc_py_api_inside_the_client_is_allowed() -> None:
    source = "from nc_py_api import AsyncNextcloudApp\n"

    assert scan_source(CLIENT_MODULE, source) == []


def test_set_user_is_a_violation() -> None:
    violations = scan_source(CLIENT_MODULE, 'nc.set_user("bob")\n')

    assert len(violations) == 1
    assert "invariant 2" in violations[0]


def test_writing_ocs_call_is_a_violation() -> None:
    source = 'async def f(nc):\n    await nc._session.ocs("PUT", "/foo")\n'

    violations = scan_source("nc/other.py", source)

    assert len(violations) == 1
    assert "invariant 3" in violations[0]


def test_reading_ocs_call_is_allowed() -> None:
    source = 'async def f(nc):\n    await nc._session.ocs("GET", "/foo")\n'

    assert scan_source("nc/other.py", source) == []


def test_the_real_package_has_no_violations() -> None:
    violations: list[str] = []
    for relative, source in _package_modules():
        violations.extend(scan_source(relative, source))

    assert violations == [], "read-only invariant broken:\n" + "\n".join(violations)
