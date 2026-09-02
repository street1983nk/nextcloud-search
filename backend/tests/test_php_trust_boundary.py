"""Gate B: the ExApp trust boundary of every PHP route (security audit L4).

Every route this app exposes is reachable by *any* external app registered on
the instance, and that is the threat this gate exists for. An AI assistant an
admin installed last week is a registered ExApp, so it passes ``ExAppRequired``
without any trouble at all: that attribute answers "is this a registered
external app", never "is this *our* external app". The second question is
answered by ``rejectForeignCaller``, which compares the ``EX-APP-ID`` header
against the backend app id of this app, and only by that. A route that carries
the attribute and forgets the comparison hands the work stock, the file list of
the whole instance, or the content gateway to a foreign container.

The protection was written in phase 2 and it was complete then. What was
missing, and what this file adds, is the guarantee that it stays complete: the
security audit filed this as L4, "protection present, regression unsecured".
Phase 3 is the proof that the concern was justified. The four routes of the
audit have become eight, added by four different plans, and each of those plans
had to remember two attributes and one first statement by hand.

**Why this is a textual check and not a PHP test.** There is no PHP test
environment on the development machine and none in this repository; the PHP side
is checked with ``php -l`` in a container and nothing else. A textual gate that
pins the protection is worth more than the perfect test that does not exist, and
it is exactly the shape of Gate A in ``test_readonly_gate.py``: parse the
sources, judge every route, and fail closed when something cannot be read.

Two self tests against text samples belong to that shape and are not decoration.
A gate whose only assertion is "the current tree is clean" is green on the day
somebody deletes its body, so the two ways of breaking a route are staged here
deliberately and the gate has to report both of them.

**Two route classes since phase 4.** A route of this app is either an ExApp
route, spelled ``ApiRoute`` and reachable only by a registered container, or an
admin route, spelled ``FrontpageRoute`` and reachable only by the browser
session of an admin. The two are judged by opposite rules, and neither rule may
be applied to the other class. An ``ExAppRequired`` on an admin route points the
protection the wrong way round: the admin's own browser would no longer reach
the page, while every registered foreign container would (pitfall 7). And
``access_level ADMIN`` in ``backend/appinfo/info.xml`` does not close that gap,
because it is checked in ``ExAppProxyController`` on the way browser to AppAPI
proxy to ExApp, and ``PublicFunctions::exAppRequest`` never passes that check
(pitfall 10). The effective protection of the admin side is therefore the PHP
controller itself: a route without ``NoAdminRequired``, ``PublicPage`` and
``NoCSRFRequired`` makes ``SecurityMiddleware`` demand a logged in admin plus a
CSRF token, and with any of those three it does not. This gate is the regression
lock for that sentence, which is why the admin class is judged by what it must
*not* carry.

**What this gate does not claim.** It says nothing about whether AppAPI
authenticated the caller before the request arrived. That residual risk is
written down at every ``rejectForeignCaller`` in the PHP sources: whoever can
forge the header has broken the AppAPI trust model itself.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CONTROLLER_ROOT = Path(__file__).resolve().parents[2] / "php" / "lib" / "Controller"

# The two attributes that make a method a route. Everything else in this file
# hangs off finding one of them: a method without either is not reachable from
# the outside and needs no boundary. ApiRoute is the ExApp class, FrontpageRoute
# the admin class, and the attribute alone decides which set of rules applies.
ROUTE_ATTRIBUTE = "ApiRoute"
ADMIN_ROUTE_ATTRIBUTE = "FrontpageRoute"
ROUTE_ATTRIBUTES = (ROUTE_ATTRIBUTE, ADMIN_ROUTE_ATTRIBUTE)

# The attribute that keeps browsers and ordinary users out, and the call that
# keeps foreign ExApps out. Both are required on an ExApp route, because each of
# them answers a question the other one does not.
EXAPP_ATTRIBUTE = "ExAppRequired"
GUARD_CALL = "rejectForeignCaller"

# What an admin route may never carry. The first three each remove one half of
# what SecurityMiddleware would otherwise demand, and the fourth would hand the
# route to every registered container while locking the admin out of it. None of
# them is a weakening that can be argued for on a settings page, so the list is
# checked as a whole and every hit is named.
FORBIDDEN_ON_ADMIN_ROUTE = ("NoAdminRequired", "PublicPage", "NoCSRFRequired", EXAPP_ATTRIBUTE)

_FUNCTION = re.compile(r"^\s*(?:public|protected|private)\s+(?:static\s+)?function\s+(\w+)\s*\(")

# Lines that are not a statement: blank, and the three comment shapes PHP uses.
# ``#`` covers an attribute inside a body as well, which is the safe direction:
# an attribute is never the guard call, so skipping it can only make the gate
# look further, never make it pass earlier.
_NOT_A_STATEMENT = ("//", "/*", "*", "#")


@dataclass(frozen=True, slots=True)
class Route:
    """One method that is reachable over HTTP, with where it stands.

    ``kind`` is ``"exapp"`` or ``"admin"`` and decides which of the two rules
    below judges the method.
    """

    file: str
    method: str
    line: int
    kind: str


def _attributes_above(lines: list[str], function_index: int) -> list[str]:
    """The attribute lines directly above a method declaration.

    Walking upwards stops at the first line that is not an attribute, which is
    the docblock. That is deliberate: an attribute of the *previous* method must
    never be counted for this one, and the docblock is the wall between them.
    """
    collected: list[str] = []
    index = function_index - 1
    while index >= 0 and lines[index].strip().startswith("#["):
        collected.append(lines[index].strip())
        index -= 1
    return collected


def _body_start(lines: list[str], function_index: int) -> int:
    """The index of the first line inside the method body."""
    for index in range(function_index, len(lines)):
        if lines[index].rstrip().endswith("{"):
            return index + 1
    return len(lines)


def _first_statement(lines: list[str], start: int) -> str:
    """The first line of a body that is neither blank nor a comment."""
    for line in lines[start:]:
        stripped = line.strip()
        if not stripped or stripped.startswith(_NOT_A_STATEMENT):
            continue
        return stripped
    return ""


def routes_of(relative_path: str, source: str) -> list[Route]:
    """Every method of one controller that carries one of the route attributes.

    A method that carries both attribute names counts as ``admin``, which is the
    safe direction: the admin class is the stricter of the two, so a mixed
    method is reported rather than waved through.
    """
    lines = source.splitlines()
    routes: list[Route] = []
    for index, line in enumerate(lines):
        match = _FUNCTION.match(line)
        if match is None:
            continue
        attributes = _attributes_above(lines, index)
        if any(ADMIN_ROUTE_ATTRIBUTE in attribute for attribute in attributes):
            kind = "admin"
        elif any(ROUTE_ATTRIBUTE in attribute for attribute in attributes):
            kind = "exapp"
        else:
            continue
        routes.append(Route(file=relative_path, method=match.group(1), line=index + 1, kind=kind))
    return routes


def scan_source(relative_path: str, source: str) -> list[str]:
    """Return one message per unguarded route, empty list when clean.

    Every message names the file, the line and the method, because a gate that
    only says "something is wrong" costs the next reader the search this
    function already did.
    """
    lines = source.splitlines()
    violations: list[str] = []

    for route in routes_of(relative_path, source):
        attributes = _attributes_above(lines, route.line - 1)

        if route.kind == "admin":
            violations += [
                f"{route.file}:{route.line}: {route.method}() is an admin route carrying {forbidden}, "
                "so SecurityMiddleware no longer demands a logged in admin plus a CSRF token"
                for forbidden in FORBIDDEN_ON_ADMIN_ROUTE
                if any(forbidden in attribute for attribute in attributes)
            ]
            # No rejectForeignCaller here on purpose: there is no ExApp caller on
            # an admin route, so there is nothing for the comparison to reject.
            continue

        if not any(EXAPP_ATTRIBUTE in attribute for attribute in attributes):
            violations.append(
                f"{route.file}:{route.line}: {route.method}() is a route without {EXAPP_ATTRIBUTE}, "
                "so any browser session reaches it"
            )

        statement = _first_statement(lines, _body_start(lines, route.line - 1))
        if GUARD_CALL not in statement:
            violations.append(
                f"{route.file}:{route.line}: {route.method}() does not call {GUARD_CALL} as its first "
                "statement, so a foreign ExApp reaches it"
            )

    return violations


def _controller_sources() -> list[tuple[str, str]]:
    """Every controller of the PHP app, as (file name, source)."""
    return [(path.name, path.read_text(encoding="utf-8")) for path in sorted(CONTROLLER_ROOT.glob("*.php"))]


# -- the real tree ---------------------------------------------------------


def test_every_route_of_every_controller_is_guarded() -> None:
    violations = [message for name, source in _controller_sources() for message in scan_source(name, source)]

    assert violations == []


def test_the_gate_sees_every_route_the_sources_declare() -> None:
    # The count is the anti-vacuity clause of this gate. A parser that stopped
    # recognising methods would report zero violations over zero routes and look
    # perfectly healthy, so the number of judged methods is compared against the
    # number of route attributes in the sources. The two are only equal while the
    # attribute is spelled fully qualified in every controller, which is the
    # spelling the controllers themselves say they use for exactly this reason:
    # an import line would count as a mention without being a route.
    sources = _controller_sources()
    routes = [route for name, source in sources for route in routes_of(name, source)]
    mentions = sum(
        1
        for _, source in sources
        for line in source.splitlines()
        if any(attribute in line for attribute in ROUTE_ATTRIBUTES)
    )

    assert len(routes) == mentions
    # Nine today: eight ExApp routes, five on the queue, two on the reconcile
    # and one on the content gateway, plus the one admin route of the settings
    # page. A lower number means the parser lost something. Every plan that adds
    # a route raises this bound with it, admin routes included, otherwise the
    # clause stops being a ratchet.
    assert len(routes) >= 9


def test_every_controller_of_the_app_carries_at_least_one_route() -> None:
    # A controller without a route is either dead code or a class the gate is
    # silently ignoring, and both are worth knowing about.
    unrouted = [name for name, source in _controller_sources() if not routes_of(name, source)]

    assert unrouted == []


# -- self tests: the gate has to report both failures ----------------------

_GUARDED = """<?php

class ExampleController extends OCSController {
\t/**
\t * A docblock, so that the attribute walk has a wall to stop at.
\t */
\t#[\\OCP\\AppFramework\\Http\\Attribute\\ExAppRequired]
\t#[\\OCP\\AppFramework\\Http\\Attribute\\NoCSRFRequired]
\t#[\\OCP\\AppFramework\\Http\\Attribute\\ApiRoute(verb: 'GET', url: '/things')]
\tpublic function things(): DataResponse {
\t\t$foreign = $this->rejectForeignCaller();
\t\tif ($foreign !== null) {
\t\t\treturn $foreign;
\t\t}

\t\treturn new DataResponse([]);
\t}
}
"""


def test_a_fully_guarded_route_is_clean() -> None:
    # The counter sample of the two below. Without it a gate that reported every
    # route as broken would also pass both failure tests.
    assert scan_source("ExampleController.php", _GUARDED) == []
    assert len(routes_of("ExampleController.php", _GUARDED)) == 1


def test_missing_exapp_required_is_reported() -> None:
    source = _GUARDED.replace("\t#[\\OCP\\AppFramework\\Http\\Attribute\\ExAppRequired]\n", "")

    violations = scan_source("ExampleController.php", source)

    assert len(violations) == 1
    assert "ExAppRequired" in violations[0]
    assert "ExampleController.php" in violations[0]
    assert "things()" in violations[0]


def test_missing_reject_foreign_caller_is_reported() -> None:
    source = _GUARDED.replace("\t\t$foreign = $this->rejectForeignCaller();\n", "")

    violations = scan_source("ExampleController.php", source)

    assert len(violations) == 1
    assert "rejectForeignCaller" in violations[0]
    assert "ExampleController.php" in violations[0]
    assert "things()" in violations[0]


def test_the_guard_has_to_be_the_first_statement() -> None:
    # Second in the body is not good enough, and this is the shape in which the
    # protection realistically erodes: somebody adds "just one cheap line" in
    # front of it, and that line runs for a caller that has no business being
    # here at all.
    source = _GUARDED.replace(
        "\t\t$foreign = $this->rejectForeignCaller();\n",
        "\t\t$this->logger->info('a line in front of the guard');\n\t\t$foreign = $this->rejectForeignCaller();\n",
    )

    violations = scan_source("ExampleController.php", source)

    assert len(violations) == 1
    assert "first" in violations[0]


# -- self tests: the admin class has its own, stricter rule ----------------

_ADMIN = """<?php

class AdminSettingsController extends Controller {
\t/**
\t * A docblock, so that the attribute walk has a wall to stop at.
\t */
\t#[\\OCP\\AppFramework\\Http\\Attribute\\FrontpageRoute(verb: 'GET', url: '/settings/admin')]
\tpublic function index(): TemplateResponse {
\t\treturn new TemplateResponse(Application::APP_ID, 'admin');
\t}
}
"""


def _admin_route_carrying(attribute: str) -> str:
    """The clean admin sample with one more attribute above the same method."""
    marker = "\t#[\\OCP\\AppFramework\\Http\\Attribute\\FrontpageRoute"
    replacement = f"\t#[\\OCP\\AppFramework\\Http\\Attribute\\{attribute}]\n{marker}"
    return _ADMIN.replace(marker, replacement, 1)


def test_a_clean_admin_route_is_clean() -> None:
    # The counter sample of the four below, and at the same time the proof that
    # an admin controller is a controller as far as this gate is concerned: the
    # route is counted, so a class of nothing but FrontpageRoute methods can
    # satisfy test_every_controller_of_the_app_carries_at_least_one_route.
    routes = routes_of("AdminSettingsController.php", _ADMIN)

    assert scan_source("AdminSettingsController.php", _ADMIN) == []
    assert len(routes) == 1
    assert routes[0].kind == "admin"


def test_an_admin_route_needs_no_reject_foreign_caller() -> None:
    # The loosening of this plan, written down so that it cannot be undone by
    # accident. There is no ExApp caller on an admin route, so there is nothing
    # for the comparison to reject, and demanding it would force a meaningless
    # call into every settings page method.
    assert GUARD_CALL not in _ADMIN
    assert scan_source("AdminSettingsController.php", _ADMIN) == []


def test_no_admin_required_on_an_admin_route_is_reported() -> None:
    violations = scan_source("AdminSettingsController.php", _admin_route_carrying("NoAdminRequired"))

    assert len(violations) == 1
    assert "NoAdminRequired" in violations[0]
    assert "AdminSettingsController.php" in violations[0]
    assert "index()" in violations[0]


def test_public_page_on_an_admin_route_is_reported() -> None:
    violations = scan_source("AdminSettingsController.php", _admin_route_carrying("PublicPage"))

    assert len(violations) == 1
    assert "PublicPage" in violations[0]
    assert "index()" in violations[0]


def test_no_csrf_required_on_an_admin_route_is_reported() -> None:
    # Harmless on an ExApp route, where the credential is the signed AppAPI
    # header and no session is involved, and the opposite here: this route is
    # reached by a browser session, so the token is the only thing that keeps a
    # foreign page from acting as the logged in admin.
    violations = scan_source("AdminSettingsController.php", _admin_route_carrying("NoCSRFRequired"))

    assert len(violations) == 1
    assert "NoCSRFRequired" in violations[0]
    assert "index()" in violations[0]


def test_exapp_required_on_an_admin_route_is_reported() -> None:
    # Mixing the two classes is the mistake pitfall 7 and pitfall 10 describe
    # together, and it points the protection the wrong way round: the admin's
    # own browser would no longer reach the page, while every registered
    # foreign container would.
    violations = scan_source("AdminSettingsController.php", _admin_route_carrying("ExAppRequired"))

    assert len(violations) == 1
    assert "ExAppRequired" in violations[0]
    assert "index()" in violations[0]


def test_a_method_without_the_route_attribute_is_not_judged() -> None:
    # The private helpers of every controller are methods too, and they carry
    # neither attribute nor guard. Judging them would make the gate unusable and
    # therefore, in the end, deleted.
    source = """<?php

class ExampleController extends OCSController {
\tprivate function rejectForeignCaller(): ?DataResponse {
\t\treturn null;
\t}
}
"""

    assert routes_of("ExampleController.php", source) == []
    assert scan_source("ExampleController.php", source) == []
