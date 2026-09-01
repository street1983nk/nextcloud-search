"""Gate A: the static read-only invariant (IDX-07).

Findling never modifies user files. This gate exists before the first read path
does, because the documented data loss class in Nextcloud search apps came from a
write path that nobody reviewed. The gate parses every module under
``backend/src/findling`` and asserts three invariants:

1. Only ``findling/nc/client.py`` imports ``nc_py_api`` or ``httpx``.
2. No module contains a writing identifier of ``nc_py_api.files`` and none
   contains ``set_user``.
3. No call on any receiver outside a small local allowlist uses PUT, POST,
   PATCH or DELETE, or a method this gate cannot read, on a path outside an
   explicit allowlist. The path allowlist was empty throughout phase 1, holds
   the two queue paths of the return channel since plan 02-10 and the requeue
   path of the OCR track since plan 03-07, which is three in total;
   the reasoning sits at :data:`OCS_WRITE_ALLOWLIST`. Judged by default since
   the M2 inversion: a receiver name proves nothing about where the object
   points, so only :data:`LOCAL_RECEIVERS` is exempt.

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

# Reviewed exceptions to invariant 2, the extension the module docstring above
# anticipates. One entry is one (module, identifier) pair, and the pair is the
# whole point: waving "mkdir" through everywhere would hide a real
# nc_py_api.files.mkdir one file over, which is exactly the class of breach this
# gate exists for. Adding an entry is a review decision, and it is only
# defensible when invariant 1 already proves that the module cannot reach
# Nextcloud at all.
#
# index/wordlist.py creates the dictionary directory of the container's own
# persistent volume. That path is never a Nextcloud node: the container has no
# access to the Nextcloud storage at all, and invariant 1 keeps nc_py_api out of
# that module, so the only object a mkdir there can reach is a local one.
#
# store/repo.py creates the directory of the state database under
# APP_PERSISTENT_STORAGE. Same reasoning: the module may not import nc_py_api
# or httpx, so the collision with the writing entry point of nc_py_api.files
# is one of names only.
#
# index/open.py creates the index directory under APP_PERSISTENT_STORAGE. It is
# the only module that opens a tantivy index, tantivy refuses a directory that
# does not exist ("Directory does not exist"), and the standard library offers no
# way to create one without naming mkdir or makedirs. Invariant 1 keeps nc_py_api
# and httpx out of that module as well, so the only directory it can reach is a
# local one.
#
# worker/poller.py creates the scratch directory under APP_PERSISTENT_STORAGE, the
# place a file is streamed to before it is handed to the extraction child. Same
# reasoning again: invariant 1 keeps both restricted imports out of that module,
# so the only directory the call can reach is one in the container's own volume.
# The path itself comes from findling.config, never from a queue entry, so no
# value out of Nextcloud reaches this call.
INVARIANT_2_EXCEPTIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("index/wordlist.py", "mkdir"),
        ("store/repo.py", "mkdir"),
        ("index/open.py", "mkdir"),
        ("worker/poller.py", "mkdir"),
    }
)

WRITING_HTTP_METHODS = frozenset({"PUT", "POST", "PATCH", "DELETE"})

# Stands in for the HTTP method when the gate cannot read it, for instance because
# it arrives in a variable. Reported like a writing method, because a call that
# may be a write has to be treated as one.
UNREADABLE_METHOD = "a method this gate cannot read"

# Entry points that take an HTTP method as their first argument. stream is the
# httpx one: `client.stream("PUT", url)` is a request like any other, it merely
# hands the body over lazily.
OCS_ENTRY_POINTS = frozenset({"ocs", "request", "request_json", "stream"})

# Receiver names whose write-shaped methods are local registrations rather than
# network calls: `ROUTER.post(...)` mounts an endpoint, it does not send one.
#
# Inverted on 2026-09-01 (security audit M2). The gate used to keep an allowlist
# of REMOTE receivers ({nc, ocs, _session, ...}) and judged only those, so
# `client.put(...)` on a pooled gateway client, one name the list did not know,
# walked past invariant 3 unjudged. A gate that cannot judge something has to
# say no: every write-shaped call is treated as remote now, and a purely local
# object with such a method has to be added here, deliberately and with a
# reason, instead of being waved through by default.
LOCAL_RECEIVERS = frozenset({"ROUTER"})

# Paths the backend may write to over OCS. Empty throughout phase 1; extended on
# 2026-08-31 by plan 02-10 with exactly two entries, in a step of its own rather
# than as a side effect of the feature that needs them, so that the weakening of
# a security gate is one readable commit in the history instead of three lines in
# a large diff.
#
# Why these two, and only these two. The indexing worker pulls its work from a
# queue that Nextcloud owns, and it has to say what it did with a batch. That
# return channel is the whole reason a write exists at all:
#
#   DELETE .../queues/documents         acknowledges a batch and records the
#                                       reason for everything that could not be
#                                       processed
#   POST   .../queues/documents/unlock  hands rows back unprocessed on shutdown,
#                                       so a restart is productive at once
#
# Both land in OCA\Findling\Controller\QueueController, both write into the two
# database tables this app owns, and neither has a code path into the file system
# of Nextcloud. No user file is reachable from either of them, which is the
# property that makes the exception defensible: IDX-07 promises that Findling
# never modifies user data, not that it never speaks.
#
# The threat register of plan 02-10 carries this as T-02-101 (Tampering, "widening
# of the OCS write allowlist"), with the disposition mitigate and three
# mitigations: the list is exactly two literal paths, the widening is its own
# step, and two of the three self tests below exist to show that the list is
# narrow rather than merely present. T-02-102 covers the other half, that no user
# file sits in the write path of the worker, and gate B keeps proving that from
# the outside through checksums of the reference corpus.
#
# Every further entry carries the same duty: a named threat, a statement of which
# tables it can reach, and a negative test. An entry without those three is not a
# reviewed exception, it is the hole this gate was written to prevent.
#
# Extended on 2026-09-01 by plan 03-07 with the third entry, again in a step of
# its own and again for the reason above:
#
#   POST   .../queues/documents/requeue   puts a row of the work stock on another
#                                         kind of job, or creates one, and resets
#                                         its attempt counter
#
# Why it exists. A PDF without a text layer ends the text track as
# skipped(no_text_layer), and that verdict was prepared in phase 2 as the handover
# point to OCR. Without a way to turn the finding back into work, a scanned
# document would stay skipped for good, which is precisely the outcome D-07
# forbids. The same route carries the findings of the reconcile of plan 03-12,
# because a file the comparison discovers may have no queue row at all.
#
# What it can reach, which is the property that makes the exception defensible:
# findling_queue and nothing else. The endpoint takes file ids and a job kind, it
# writes the kind column, the attempt counter and the free mark of that one table,
# and it has no code path into the file system of Nextcloud. No user file is
# reachable from it. The kind is checked against QueueMapper::KINDS, a closed list
# of five strings, so the route cannot invent a job either.
#
# The threat register of plan 03-07 carries this as T-03-701 (Tampering, "widening
# of the OCS write allowlist"), disposition mitigate, with three mitigations that
# are the same three duties: exactly one additional literal path, the widening as
# its own step, and the two tests below that show the list is narrow rather than
# merely present. T-03-702 covers the second half, that no foreign ExApp may call
# the route, and rejectForeignCaller as the first statement of the controller
# method is what answers it.
#
# This is the third and, on today's understanding, the last write this container
# needs: take work, say what happened to it, hand it back, and move it to the
# other track. A fourth entry has to argue for itself against
# test_write_allowlist_has_exactly_three_entries, which is the point of that test.
OCS_WRITE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "/ocs/v2.php/apps/findling/queues/documents",
        "/ocs/v2.php/apps/findling/queues/documents/unlock",
        "/ocs/v2.php/apps/findling/queues/documents/requeue",
    }
)


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

    receiver_is_local = bool(_receiver_names(func.value) & LOCAL_RECEIVERS)
    if receiver_is_local:
        return None

    if func.attr in OCS_ENTRY_POINTS:
        path = _string_argument(call, 1, "path", "url", "path_and_query")
        method = _string_argument(call, 0, "method")
        if method is None:
            # The bypass this closes: the method used to be judged only when it
            # was a literal, so `nc.ocs(verb, path)` fell through as harmless.
            # A call the gate cannot read is reported like a write, because a
            # call that may be a write has to be treated as one.
            return (UNREADABLE_METHOD, path)
        if method.upper() not in WRITING_HTTP_METHODS:
            return None
        return method.upper(), path

    if func.attr.upper() in WRITING_HTTP_METHODS:
        # Write-shaped method on any receiver the local allowlist does not
        # name (security audit M2): `client.put(...)` on a pooled httpx client
        # used to fall through because the old REMOTE allowlist did not know
        # the name. Invariant 2 already restricts `delete` everywhere, so this
        # judges the three others plus every future receiver by default.
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
        if identifier in FORBIDDEN_IDENTIFIERS and (normalized, identifier) not in INVARIANT_2_EXCEPTIONS:
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


def test_the_reviewed_exception_covers_exactly_the_named_modules() -> None:
    # The volume layout of the container is created in these places, and only there.
    assert scan_source("index/wordlist.py", "target.mkdir(parents=True, exist_ok=True)\n") == []
    assert scan_source("store/repo.py", "database.parent.mkdir(parents=True, exist_ok=True)\n") == []
    assert scan_source("index/open.py", "path.mkdir(parents=True, exist_ok=True)\n") == []
    assert scan_source("worker/poller.py", "scratch.mkdir(parents=True, exist_ok=True)\n") == []


def test_the_reviewed_exception_does_not_leak_into_other_modules() -> None:
    # Same line, one file over. An exception that spreads by itself is not an
    # exception, it is a hole, and moving code must not launder it.
    for module in ("index/schema.py", "api/search.py"):
        violations = scan_source(module, "target.mkdir(parents=True, exist_ok=True)\n")

        assert len(violations) == 1
        assert "invariant 2" in violations[0]


def test_the_reviewed_exception_covers_only_the_identifier_it_names() -> None:
    # mkdir is allowed in that module, delete is not. Both invariants report
    # it since the M2 inversion: as a writing identifier and as a write-shaped
    # method on a receiver the local list does not name.
    violations = scan_source("index/wordlist.py", "target.delete()\n")

    assert violations != []
    assert any("invariant 2" in violation for violation in violations)


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


def test_a_method_the_gate_cannot_read_is_a_violation_on_any_receiver() -> None:
    # The old REMOTE allowlist waved this through because "parser" was not on
    # it. A receiver name proves nothing about where the object points, so an
    # unreadable method is judged the same on every receiver the LOCAL list
    # does not name (security audit M2).
    source = 'async def f(parser, verb):\n    parser.request(verb, "/foo")\n'

    violations = scan_source("nc/other.py", source)

    assert len(violations) == 1
    assert "invariant 3" in violations[0]


def test_bypass_a_write_on_a_pooled_client_is_a_violation() -> None:
    # The receiver "client" was on no list, so this used to pass unjudged.
    source = 'async def f(client):\n    await client.put("/foo")\n'

    violations = scan_source("worker/poller.py", source)

    assert len(violations) == 1
    assert "invariant 3" in violations[0]


def test_bypass_a_streamed_write_is_a_violation() -> None:
    # stream() takes the method as its first argument, exactly like ocs(), and
    # used to be no entry point at all.
    source = 'async def f(client):\n    async with client.stream("PUT", "/foo"):\n        pass\n'

    violations = scan_source(CLIENT_MODULE, source)

    assert len(violations) == 1
    assert "invariant 3" in violations[0]


def test_a_streamed_read_is_allowed() -> None:
    source = 'async def f(client):\n    async with client.stream("GET", "/foo"):\n        pass\n'

    assert scan_source(CLIENT_MODULE, source) == []


def test_mounting_a_route_is_not_a_write() -> None:
    # The one reviewed entry of the LOCAL list: a FastAPI router registers an
    # endpoint, it sends nothing anywhere.
    source = '@ROUTER.post("/search")\nasync def f():\n    pass\n'

    assert scan_source("api/search.py", source) == []


def test_reading_ocs_call_is_allowed() -> None:
    source = 'async def f(nc):\n    await nc._session.ocs("GET", "/foo")\n'

    assert scan_source("nc/other.py", source) == []


def test_writing_ocs_call_to_an_allowed_path_is_not_a_violation() -> None:
    # The two paths of the queue return channel, the only write the container has.
    acknowledge = (
        'async def f(nc):\n    await nc._session.ocs("DELETE", "/ocs/v2.php/apps/findling/queues/documents")\n'
    )
    unlock = (
        'async def f(nc):\n    await nc._session.ocs("POST", "/ocs/v2.php/apps/findling/queues/documents/unlock")\n'
    )

    assert scan_source(CLIENT_MODULE, acknowledge) == []
    assert scan_source(CLIENT_MODULE, unlock) == []


def test_writing_ocs_call_to_the_requeue_path_is_not_a_violation() -> None:
    # The third and last write of the return channel: the container turns a
    # skipped(no_text_layer) verdict back into work by putting the row on the
    # OCR track instead of letting it end there (plan 03-07, D-07).
    requeue = (
        'async def f(nc):\n    await nc._session.ocs("POST", "/ocs/v2.php/apps/findling/queues/documents/requeue")\n'
    )

    assert scan_source(CLIENT_MODULE, requeue) == []


def test_writing_ocs_call_to_another_path_beside_the_requeue_route_is_a_violation() -> None:
    # The negative half of the entry above, and the duty every entry of the
    # allowlist carries. A neighbour of the new path, a longer spelling of it and
    # the same path reached through a module constant all have to stay
    # violations, otherwise the list would be proven to exist but not to be
    # narrow.
    for path in (
        "/ocs/v2.php/apps/findling/queues/documents/requeue/all",
        "/ocs/v2.php/apps/findling/queues/documents/requeues",
        "/ocs/v2.php/apps/findling/queues/documents/requeue ",
    ):
        source = f'async def f(nc):\n    await nc._session.ocs("POST", "{path}")\n'

        violations = scan_source(CLIENT_MODULE, source)

        assert len(violations) == 1, path
        assert "invariant 3" in violations[0]

    hidden = (
        'REQUEUE = "/ocs/v2.php/apps/findling/queues/documents/requeue"\n'
        "\n"
        "async def f(nc):\n"
        '    await nc._session.ocs("POST", REQUEUE)\n'
    )

    violations = scan_source(CLIENT_MODULE, hidden)

    assert len(violations) == 1
    assert "an unknown path" in violations[0]


def test_write_allowlist_has_exactly_three_entries() -> None:
    # Not a tautology, a ratchet. Every entry of this list is a hole in IDX-07
    # that somebody argued for once, and the argument is in the comment block
    # above the list. A fourth entry that arrives as a side effect of a feature
    # fails here first, which is the moment at which the three duties (a named
    # threat, a statement of the reachable tables, a negative test) can still be
    # asked for.
    assert len(OCS_WRITE_ALLOWLIST) == 3
    assert {
        "/ocs/v2.php/apps/findling/queues/documents",
        "/ocs/v2.php/apps/findling/queues/documents/unlock",
        "/ocs/v2.php/apps/findling/queues/documents/requeue",
    } == OCS_WRITE_ALLOWLIST


def test_writing_ocs_call_to_another_path_is_still_a_violation() -> None:
    # Without this one the allowlist would be proven to exist but not to be
    # narrow. A neighbouring path, and a writing method on an allowed path's
    # parent, both have to stay violations.
    for path in (
        "/ocs/v2.php/apps/findling/queues/documents/other",
        "/ocs/v2.php/apps/findling/files/42",
        "/ocs/v2.php/apps/files/api/v1/files",
    ):
        source = f'async def f(nc):\n    await nc._session.ocs("DELETE", "{path}")\n'

        violations = scan_source(CLIENT_MODULE, source)

        assert len(violations) == 1, path
        assert "invariant 3" in violations[0]


def test_a_writing_call_whose_path_is_not_a_literal_is_a_violation() -> None:
    # The mechanics the allowlist rests on: the gate reads the path as a literal
    # at the call site. Tidying the two allowed calls into a module constant
    # would leave the gate with "an unknown path" and no way to judge it, so this
    # test pins the reason the calls in nc/client.py look the way they do.
    source = (
        'QUEUE = "/ocs/v2.php/apps/findling/queues/documents"\n'
        "\n"
        "async def f(nc):\n"
        '    await nc._session.ocs("DELETE", QUEUE)\n'
    )

    violations = scan_source(CLIENT_MODULE, source)

    assert len(violations) == 1
    assert "an unknown path" in violations[0]


def test_the_real_package_has_no_violations() -> None:
    violations: list[str] = []
    for relative, source in _package_modules():
        violations.extend(scan_source(relative, source))

    assert violations == [], "read-only invariant broken:\n" + "\n".join(violations)
