"""The 1.3.2 manifest fixes: the declared sandbox limit and the content routes off the list.

The declared routes are the surface a browser session or an app password can
reach through /exapps/. The companion never needs a declaration: HaRP skips
the route table for AppAPI signed requests ("We skip routes checking for
AppAPI signed requests", haproxy_agent.py), and so did ExAppProxyController
before it. A content route on that list is therefore reachable by every
logged in user, past the permission recheck that only the PHP side performs.

AppAPI hands an ExApp only the variables its info.xml declares
(ExAppEnvVarsHelper::normalizeAndValidate); an undeclared value is dropped
without a word, so the sandbox limit has to be declared to be raisable.
"""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

import pytest

from findling import config

BACKEND_INFO = Path(__file__).resolve().parents[2] / "backend" / "appinfo" / "info.xml"

CONTENT_ROUTES = ("/search", "/snippets")


def _info() -> ElementTree.Element:
    return ElementTree.fromstring(BACKEND_INFO.read_text(encoding="utf-8"))  # noqa: S314


def _declared_route_urls() -> list[str]:
    return [route.findtext("url") or "" for route in _info().iter("route")]


@pytest.mark.parametrize("path", CONTENT_ROUTES)
def test_a_content_route_is_not_on_the_browser_reachable_surface(path: str) -> None:
    assert not any(re.match(url, path) for url in _declared_route_urls()), (
        f"{path} is declared in info.xml and so reachable by any logged in user through /exapps/"
    )


def test_the_extraction_address_space_is_declared_with_the_config_default() -> None:
    declared = {variable.findtext("name"): variable.findtext("default") for variable in _info().iter("variable")}

    assert declared.get("FINDLING_EXTRACT_ADDRESS_SPACE_BYTES") == str(config.EXTRACT_ADDRESS_SPACE_BYTES)
