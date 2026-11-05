"""Text bans over the PHP half, the companion manifest included (plan 42-09).

The route attribute gate in php/tests/Unit/RouteSecurityTest.php already holds
docblock annotations, the routes file, the router and the container, and the
registrations of the app, but it runs in php.yml, and php.yml starts only on
php/**. python.yml runs on backend/** and scripts/** and every Monday. This
file is the text side of the same bans, so they also hold on a commit that
touches only the backend and on the weekly run against a tree nobody touched:

- every annotation name stable34 reads, in any file under php/lib, at any
  position (class docblocks and methods without a route included), in any
  case, with file and line; the list is held in lockstep with
  RouteProfiles::SERVER_ANNOTATION_NAMES (vector 1)
- under php/lib the texts that reach the router or the container: IRouter,
  OC\\Route\\, getRouter(, actionInclude(, ->action(, registerService(,
  registerServiceAlias(, registerParameter(, registerMiddleware( and
  getContainer( (vectors 3, 6 and 11)
- in php/appinfo/routes.php: $this, ->create(, include, require and eval,
  because that file runs inside a method of the router (vector 3)
- in php/appinfo/info.xml: none of remote, public, sabre, collaboration,
  activity, two-factor-providers, fulltextsearch and dashboard, and settings
  with exactly the admin page and its section (vector 13). A remote entry is
  loaded with require_once by remote.php and, in stable34, by public.php,
  without any middleware.

**The limit.** This is text, not a parser: it is coarse on purpose and fails
closed, so a comment that names a banned text is a finding as well. The
parser side, which knows a comment from code, is the PHPUnit gate.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PHP_LIB = REPO_ROOT / "php" / "lib"
ROUTES_FILE = REPO_ROOT / "php" / "appinfo" / "routes.php"
PHP_INFO_XML = REPO_ROOT / "php" / "appinfo" / "info.xml"
PROFILES = REPO_ROOT / "php" / "tests" / "RouteSecurity" / "RouteProfiles.php"

# The annotation names stable34 reads anywhere (middlewares of lib/private,
# core and apps), lowercased, in the order of RouteProfiles.php.
SERVER_ANNOTATION_NAMES = (
    "anonratethrottle",
    "authorizedadminsetting",
    "bruteforceprotection",
    "cors",
    "exapprequired",
    "noadminrequired",
    "nocsrfrequired",
    "noincomingfederatedsharingrequired",
    "nooutgoingfederatedsharingrequired",
    "nosamesitecookierequired",
    "nosubadminrequired",
    "notwofactorrequired",
    "passwordconfirmationrequired",
    "publicpage",
    "strictcookierequired",
    "subadminrequired",
    "usesession",
    "userratethrottle",
)

MIN_LIB_FILES = 65  # files under php/lib on 2026-11-04

_ANNOTATION = re.compile(r"@(?P<name>[A-Za-z]\w*)")

# Compared case sensitively, like PHP identifiers; OC\Route\ in addition
# case insensitively, because PHP resolves namespaces that way.
LIB_BANS = (
    "IRouter",
    "OC\\Route\\",
    "getRouter(",
    "actionInclude(",
    "->action(",
    "registerService(",
    "registerServiceAlias(",
    "registerParameter(",
    "registerMiddleware(",
    "getContainer(",
)
_ROUTE_NAMESPACE = "oc\\route\\"

ROUTES_BANS = (
    ("$this", re.compile(r"\$this\b")),
    ("->create(", re.compile(r"->create\(")),
    ("include", re.compile(r"\binclude(?:_once)?\b")),
    ("require", re.compile(r"\brequire(?:_once)?\b")),
    ("eval", re.compile(r"\beval\b")),
)

FORBIDDEN_ELEMENTS = (
    "remote",
    "public",
    "sabre",
    "collaboration",
    "activity",
    "two-factor-providers",
    "fulltextsearch",
    "dashboard",
)
EXPECTED_SETTINGS = (
    ("admin", "OCA\\Findling\\Settings\\Admin"),
    ("admin-section", "OCA\\Findling\\Settings\\Section"),
)

_PROFILES_LIST = re.compile(r"public const SERVER_ANNOTATION_NAMES = \[(?P<body>.*?)\];", re.DOTALL)
_PROFILES_NAME = re.compile(r"^\s*'(?P<name>[a-z]+)',\s*$", re.MULTILINE)


def scan_annotations(path: str, source: str) -> list[str]:
    """Every server annotation name after an @, any case, as path:line."""
    findings: list[str] = []
    for number, line in enumerate(source.splitlines(), start=1):
        for match in _ANNOTATION.finditer(line):
            name = match.group("name").lower()
            if name in SERVER_ANNOTATION_NAMES:
                findings.append(f"{path}:{number}: docblock annotation @{name}")
    return findings


def scan_lib_bans(path: str, source: str) -> list[str]:
    """Every banned router or container text, as path:line."""
    findings: list[str] = []
    for number, line in enumerate(source.splitlines(), start=1):
        for ban in LIB_BANS:
            hit = ban in line
            if ban == "OC\\Route\\":
                hit = _ROUTE_NAMESPACE in line.lower()
            if hit:
                findings.append(f"{path}:{number}: {ban}")
    return findings


def scan_routes_file(source: str) -> list[str]:
    """Every banned text in appinfo/routes.php, as line: text."""
    findings: list[str] = []
    for number, line in enumerate(source.splitlines(), start=1):
        findings.extend(f"routes.php:{number}: {name}" for name, pattern in ROUTES_BANS if pattern.search(line))
    return findings


def profiles_annotation_list(source: str) -> tuple[str, ...]:
    """SERVER_ANNOTATION_NAMES as RouteProfiles.php writes it, empty if absent."""
    match = _PROFILES_LIST.search(source)
    if match is None:
        return ()
    return tuple(name.group("name") for name in _PROFILES_NAME.finditer(match.group("body")))


def scan_info_xml(text: str) -> list[str]:
    """Forbidden elements anywhere, and the exact children of settings."""
    root = ET.fromstring(text.encode("utf-8"))  # noqa: S314 - a file of this repository, not foreign input
    findings = [
        f"info.xml has the forbidden element <{element.tag}>"
        for element in root.iter()
        if element.tag in FORBIDDEN_ELEMENTS
    ]
    settings = root.findall("settings")
    children = tuple((child.tag, (child.text or "").strip()) for block in settings for child in block)
    if len(settings) != 1 or children != EXPECTED_SETTINGS:
        findings.append(f"info.xml settings are {children!r}, expected {EXPECTED_SETTINGS!r}")
    return findings


def _lib_files() -> list[Path]:
    return sorted(PHP_LIB.rglob("*.php"))


def _relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


# The real tree.


def test_no_file_under_php_lib_carries_a_server_annotation() -> None:
    files = _lib_files()
    assert len(files) >= MIN_LIB_FILES
    findings = [
        finding for path in files for finding in scan_annotations(_relative(path), path.read_text(encoding="utf-8"))
    ]
    assert findings == []


def test_no_file_under_php_lib_reaches_the_router_or_the_container() -> None:
    files = _lib_files()
    assert len(files) >= MIN_LIB_FILES
    findings = [
        finding for path in files for finding in scan_lib_bans(_relative(path), path.read_text(encoding="utf-8"))
    ]
    assert findings == []


def test_the_routes_file_is_clean() -> None:
    assert scan_routes_file(ROUTES_FILE.read_text(encoding="utf-8")) == []


def test_the_annotation_list_is_the_one_of_route_profiles() -> None:
    names = profiles_annotation_list(PROFILES.read_text(encoding="utf-8"))
    assert names == SERVER_ANNOTATION_NAMES
    assert len(names) == 18


def test_the_companion_info_xml_has_no_other_surface() -> None:
    assert scan_info_xml(PHP_INFO_XML.read_text(encoding="utf-8")) == []


# Probes: every finding is reported, and nothing else is.


@pytest.mark.parametrize(
    "line",
    [
        "\t * @PublicPage",
        "\t/** @NoCSRFRequired */",
        "\t * @publicpage",
        "\t * @UserRateThrottle(limit=5, period=60)",
        "\t * @StrictCookieRequired",
    ],
)
def test_an_annotation_in_any_form_is_reported(line: str) -> None:
    findings = scan_annotations("x.php", f"<?php\n/**\n{line}\n */\n")
    assert len(findings) == 1
    assert findings[0].startswith("x.php:3: docblock annotation @")


def test_an_annotation_in_a_class_docblock_or_without_a_route_is_reported() -> None:
    source = (
        "<?php\n/**\n * @PublicPage\n */\nfinal class A {\n"
        "\t/**\n\t * @NoAdminRequired\n\t */\n\tpublic function helper(): void {}\n}\n"
    )
    assert scan_annotations("x.php", source) == [
        "x.php:3: docblock annotation @publicpage",
        "x.php:7: docblock annotation @noadminrequired",
    ]


@pytest.mark.parametrize("name", SERVER_ANNOTATION_NAMES)
def test_every_server_annotation_name_is_reported(name: str) -> None:
    assert scan_annotations("x.php", f"\t * @{name}\n") == [f"x.php:1: docblock annotation @{name}"]


@pytest.mark.parametrize(
    "line",
    [
        "\t#[PublicPage]",
        "use OCP\\AppFramework\\Http\\Attribute\\PublicPage;",
        "\t * Opens the page to everybody, PublicPage in prose.",
        "\t * @PublicPageExtra",
        "\t * @param string $value",
        "\t * @return void",
        "\t * @since 1.0.0",
        "\t * mail admin@example.org",
    ],
)
def test_no_annotation_is_reported_where_there_is_none(line: str) -> None:
    assert scan_annotations("x.php", line + "\n") == []


@pytest.mark.parametrize("ban", LIB_BANS)
def test_every_lib_ban_is_reported(ban: str) -> None:
    source = f"<?php\n$x = {ban}\n"
    assert scan_lib_bans("x.php", source) == [f"x.php:2: {ban}"]


def test_a_lowercase_route_namespace_is_reported() -> None:
    assert scan_lib_bans("x.php", "$r = \\oc\\route\\Router::class;\n") == ["x.php:1: OC\\Route\\"]


def test_similar_texts_are_not_lib_bans() -> None:
    source = "use OCP\\IURLGenerator;\n$this->container;\n$this->registerServices;\n"
    assert scan_lib_bans("x.php", source) == []


@pytest.mark.parametrize(
    ("snippet", "name"),
    [
        ("$this->getRouter();", "$this"),
        ("$router->create('findling_x', '/x');", "->create("),
        ("include 'x.php';", "include"),
        ("require_once 'x.php';", "require"),
        ("eval('1;');", "eval"),
    ],
)
def test_every_routes_ban_is_reported(snippet: str, name: str) -> None:
    source = f"<?php\n{snippet}\nreturn ['routes' => [], 'ocs' => []];\n"
    assert f"routes.php:2: {name}" in scan_routes_file(source)


def test_a_clean_routes_file_is_clean() -> None:
    source = "<?php\n\ndeclare(strict_types=1);\n\nreturn [\n\t'routes' => [],\n\t'ocs' => [],\n];\n"
    assert scan_routes_file(source) == []


def test_a_source_without_the_constant_has_no_list() -> None:
    assert profiles_annotation_list("<?php\nfinal class RouteProfiles {}\n") == ()


_CLEAN_INFO = (
    "<?xml version='1.0'?>\n<info>\n\t<id>findling</id>\n"
    "\t<settings><admin>OCA\\Findling\\Settings\\Admin</admin>"
    "<admin-section>OCA\\Findling\\Settings\\Section</admin-section></settings>\n</info>\n"
)


def test_a_clean_info_xml_is_clean() -> None:
    assert scan_info_xml(_CLEAN_INFO) == []


@pytest.mark.parametrize(
    "addition",
    [
        "<remote><x>a.php</x></remote>",
        "<public><x>a.php</x></public>",
        "<sabre><plugins><plugin>A</plugin></plugins></sabre>",
        "<collaboration><plugins><plugin>A</plugin></plugins></collaboration>",
        "<activity><settings>A</settings></activity>",
        "<two-factor-providers><provider>A</provider></two-factor-providers>",
        "<fulltextsearch><provider>A</provider></fulltextsearch>",
        "<dashboard><widget>A</widget></dashboard>",
    ],
)
def test_a_forbidden_element_is_reported(addition: str) -> None:
    findings = scan_info_xml(_CLEAN_INFO.replace("</info>", addition + "\n</info>"))
    assert len(findings) == 1
    assert "forbidden element" in findings[0]


def test_a_third_settings_child_is_reported() -> None:
    text = _CLEAN_INFO.replace("</settings>", "<personal>OCA\\Findling\\Settings\\Personal</personal></settings>")
    findings = scan_info_xml(text)
    assert len(findings) == 1
    assert "settings are" in findings[0]


def test_a_changed_admin_class_is_reported() -> None:
    text = _CLEAN_INFO.replace("Settings\\Admin<", "Settings\\Other<")
    findings = scan_info_xml(text)
    assert len(findings) == 1
    assert "settings are" in findings[0]
