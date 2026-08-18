"""Gate A: the static read-only invariant (IDX-07).

Findling never modifies user files. This gate exists before the first read path
does, because the documented data loss class in Nextcloud search apps came from a
write path that nobody reviewed. The gate parses every module under
``backend/src/findling`` and asserts three invariants:

1. Only ``findling/nc/client.py`` imports ``nc_py_api`` or ``httpx``.
2. No module contains a writing identifier of ``nc_py_api.files`` and none
   contains ``set_user``.
3. No call on a receiver that goes out to Nextcloud uses PUT, POST, PATCH or
   DELETE, or a method this gate cannot read, on a path outside an explicit
   allowlist. The allowlist is empty in phase 1.

All three are worded fail closed, and the three self tests named "bypass" below
are the reason. The first version of this gate could be walked past in three
ways, each of them by accident rather than by malice:

* the HTTP method was only ever compared as a literal, so ``nc.ocs(verb, path)``
  with the verb in a variable read as "not a writing call",
* invariant 2 only looked at the client module, so the same forbidden call one
  file over was invisible,
* ``httpx`` is a direct dependency of this project, so a module could have built
  its own client and written to Nextcloud without ever naming ``nc_py_api``.

A gate that cannot judge something has to say no. Later phases that need a name
from :data:`FORBIDDEN_IDENTIFIERS` for a purely local object have to rename the
local object or extend the gate deliberately, which is the point.

The self test group below is also the reason this file has value while the
package is still small: a gate that only runs against a nearly empty package is
vacuously green and would not catch a later breach.
"""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "src" / "findling"

# Relative to the package root, posix separators. The single module that is
# allowed to talk to Nextcloud at all.
CLIENT_MODULE = "nc/client.py"

# Import roots that only the client module may name. nc_py_api is the obvious
# one. httpx is the less obvious one and just as load bearing: it is a direct
# dependency, so any module could otherwise build its own client, sign an AppAPI
# header and write, without a single line of this gate noticing. The documented
# fallback for the private nc_py_api call in the client module is exactly such an
# httpx client, which is why the client module may import it.
RESTRICTED_MODULES = frozenset({"nc_py_api", "httpx"})

# Writing methods of nc_py_api.files plus set_user, which would let the backend
# act as another user. Checked in every module, not only in the client one: a
# forbidden call is forbidden wherever it stands, and the module that hides it is
# the one nobody looks at. Later phases may extend this set, never shrink it.
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

# Stands in for the HTTP method when the gate cannot read it, for instance because
# it arrives in a variable. Reported like a writing method, because a call that
# may be a write has to be treated as one.
UNREADABLE_METHOD = "a method this gate cannot read"

# Entry points that take an HTTP method as their first argument.
OCS_ENTRY_POINTS = frozenset({"ocs", "request", "request_json"})

# Receiver names that mark a call as going out to Nextcloud rather than into a
# local data structure. Keeps `index_writer.delete(...)` out of invariant 3.
REMOTE_RECEIVERS = frozenset({"nc", "ocs", "_session", "session", "adapter"})

# Paths the backend may write to over OCS. Empty in phase 1: the container writes
# nothing back into Nextcloud. Every future entry needs a threat model note.
OCS_WRITE_ALLOWLIST: frozenset[str] = frozenset()


def _restricted_import(module: str | None) -> bool:
    """True when this import names one of the modules only the client may use."""
    if module is None:
        return False
    return module.split(".", maxsplit=1)[0] in RESTRICTED_MODULES


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
    """Return (http method, path) when the call may write to Nextcloud, else None."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None

    receiver_is_remote = bool(_receiver_names(func.value) & REMOTE_RECEIVERS)

    if func.attr in OCS_ENTRY_POINTS:
        path = _string_argument(call, 1, "path", "url", "path_and_query")
        method = _string_argument(call, 0, "method")
        if method is None:
            # The bypass this closes: the method used to be judged only when it
            # was a literal, so `nc.ocs(verb, path)` fell through as harmless.
            # A call the gate cannot read is reported when it goes out to
            # Nextcloud, and ignored when the receiver is a local object.
            return (UNREADABLE_METHOD, path) if receiver_is_remote else None
        if method.upper() not in WRITING_HTTP_METHODS:
            return None
        return method.upper(), path

    if func.attr.upper() in WRITING_HTTP_METHODS and receiver_is_remote:
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
                    if _restricted_import(alias.name)
                ]
            elif isinstance(node, ast.ImportFrom) and _restricted_import(node.module):
                violations.append(
                    f"{normalized}:{node.lineno}: invariant 1, {node.module} may only be imported by {CLIENT_MODULE}"
                )

        # Invariant 2 in every module, not only in the client one. The module that
        # gets away with a forbidden call is precisely the module nobody reviews.
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


def test_bypass_import_of_httpx_outside_the_client_is_a_violation() -> None:
    # httpx is a direct dependency, so a module could have built its own client,
    # signed an AppAPI header and written, without ever naming nc_py_api. That
    # walked past every invariant this gate had.
    violations = scan_source("api/search.py", "import httpx\n")

    assert len(violations) == 1
    assert "invariant 1" in violations[0]


def test_import_of_httpx_inside_the_client_is_allowed() -> None:
    # The documented fallback for the private nc_py_api download call is exactly
    # an own httpx stream, and it lives in the client module.
    assert scan_source(CLIENT_MODULE, "import httpx\n") == []


def test_bypass_writing_identifier_outside_the_client_is_a_violation() -> None:
    # Same call as the test above, one file over. Invariant 2 used to look at the
    # client module only, so this was invisible to the gate.
    violations = scan_source("api/search.py", 'nc.set_user("bob")\n')

    assert len(violations) == 1
    assert "invariant 2" in violations[0]


def test_set_user_is_a_violation() -> None:
    violations = scan_source(CLIENT_MODULE, 'nc.set_user("bob")\n')

    assert len(violations) == 1
    assert "invariant 2" in violations[0]


def test_writing_ocs_call_is_a_violation() -> None:
    source = 'async def f(nc):\n    await nc._session.ocs("PUT", "/foo")\n'

    violations = scan_source("nc/other.py", source)

    assert len(violations) == 1
    assert "invariant 3" in violations[0]


def test_bypass_a_method_the_gate_cannot_read_is_a_violation() -> None:
    # The method used to be compared as a literal or not at all, so a variable in
    # that position turned any write into a call this gate waved through.
    source = 'async def f(nc, verb):\n    await nc._session.ocs(verb, "/foo")\n'

    violations = scan_source("nc/other.py", source)

    assert len(violations) == 1
    assert "invariant 3" in violations[0]


def test_a_method_the_gate_cannot_read_on_a_local_object_is_allowed() -> None:
    # The same shape on a receiver that is not Nextcloud. Reporting this one would
    # make the gate noisy without making it stricter, and a noisy gate gets muted.
    source = 'async def f(parser, verb):\n    parser.request(verb, "/foo")\n'

    assert scan_source("nc/other.py", source) == []


def test_reading_ocs_call_is_allowed() -> None:
    source = 'async def f(nc):\n    await nc._session.ocs("GET", "/foo")\n'

    assert scan_source("nc/other.py", source) == []


def test_the_real_package_has_no_violations() -> None:
    violations: list[str] = []
    for relative, source in _package_modules():
        violations.extend(scan_source(relative, source))

    assert violations == [], "read-only invariant broken:\n" + "\n".join(violations)
