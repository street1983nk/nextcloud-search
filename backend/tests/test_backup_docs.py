"""The backup guide (issue #37) says the same facts in all three languages.

The guide only promises what CI proves on a real instance, so the facts the
deploy workflow checks (command names, container and volume names) must stay
in every language, and every README must point to its own language.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DOCS = REPO / "docs"

GUIDES = {
    "de": DOCS / "backup.md",
    "en": DOCS / "backup.en.md",
    "fr": DOCS / "backup.fr.md",
}

READMES = {
    "de": (REPO / "README.md", "docs/backup.md"),
    "en": (REPO / "README.en.md", "docs/backup.en.md"),
    "fr": (REPO / "README.fr.md", "docs/backup.fr.md"),
}

COMMON_FACTS = (
    "findling:pause",
    "findling:resume",
    "docker stop",
    "docker start",
    "nc_app_findling_backend",
    "nc_app_findling_backend_data",
    "appconfig",
    "state.db",
    "vectors.db",
)

# The clear-text warning (D-41-07) in the wording each language uses.
UNENCRYPTED = {"de": "unverschlüsselt", "en": "unencrypted", "fr": "non chiffré"}

# The promise from the issue, word for word (D-41-06).
PROMISE = "indexing stops and everything is flushed to disk while search keeps working"

DASHES = (chr(0x2013), chr(0x2014))

LINK = re.compile(r"\]\(([^)\s]+)\)")


def _text(language: str) -> str:
    return GUIDES[language].read_text(encoding="utf-8")


@pytest.mark.parametrize("language", sorted(GUIDES))
def test_each_language_has_a_guide(language: str) -> None:
    assert GUIDES[language].is_file()


@pytest.mark.parametrize("language", sorted(GUIDES))
@pytest.mark.parametrize("fact", COMMON_FACTS)
def test_each_guide_names_the_commands_and_names(language: str, fact: str) -> None:
    assert fact in _text(language)


@pytest.mark.parametrize("language", sorted(GUIDES))
def test_each_guide_warns_that_the_index_is_clear_text(language: str) -> None:
    assert UNENCRYPTED[language] in _text(language)


@pytest.mark.parametrize("language", sorted(GUIDES))
def test_each_guide_waits_for_the_paused_state(language: str) -> None:
    text = _text(language)
    assert "--wait" in text
    assert "30" in text


def test_the_english_guide_keeps_the_promise_from_the_issue() -> None:
    assert PROMISE in _text("en")


@pytest.mark.parametrize("language", sorted(GUIDES))
def test_no_guide_uses_a_dash(language: str) -> None:
    text = _text(language)
    assert not [dash for dash in DASHES if dash in text]


@pytest.mark.parametrize("language", sorted(READMES))
def test_each_readme_links_its_language(language: str) -> None:
    readme, target = READMES[language]
    assert f"]({target})" in readme.read_text(encoding="utf-8")


@pytest.mark.parametrize("language", sorted(GUIDES))
def test_every_relative_link_resolves(language: str) -> None:
    guide = GUIDES[language]
    targets = [t for t in LINK.findall(guide.read_text(encoding="utf-8")) if "://" not in t]
    assert targets
    missing = [t for t in targets if not (guide.parent / t.split("#", 1)[0]).is_file()]
    assert not missing
