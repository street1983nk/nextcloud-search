"""The gate over the push triggers: no tag but a release tag starts a workflow.

GitHub evaluates the ``push`` filters of a workflow like this: a push block that
names neither ``branches`` nor ``tags`` runs for a push of either kind, and the
``paths`` filter is not evaluated for a tag at all. A push block that carries
only ``paths`` therefore starts on every tag that is pushed, whatever commit it
points at and whatever its name. Until plan 31-01 that was the shape of five
workflows, among them the two that hold a Nextcloud instance and an image
registry credential. Plan 31-01 publishes a source mirror as a pre-release under
the tag ``source-1.5-dev``; creating that release creates the tag, and with the
old triggers it would have started all five.

The rule this gate holds, for every workflow file with a push trigger:

1. The push block names ``branches`` or ``tags``. A block of ``paths`` alone is
   the shape that fires on every tag.
2. Every pattern under ``tags`` is exactly the release pattern
   ``v[0-9]+.[0-9]+.[0-9]+``, so a release tag still runs the gates and nothing
   else does.
3. The five workflows that carried ``paths`` alone carry ``branches: ['**']``
   and the release tag pattern, and their path lists are the lists they had
   before, so the change narrows the tag side and nothing else.

A small translation of the GitHub filter syntax (``*``, ``**``, ``+``, ``?``,
character classes, a literal dot) proves the pattern does what it says: it
matches ``v1.5.0`` and does not match ``source-1.5-dev``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

RELEASE_TAG_PATTERN = "v[0-9]+.[0-9]+.[0-9]+"

# The path lists of the five workflows as they stood before plan 31-01. The
# change adds a branch and a tag filter and must not move a single path.
PATHS_BEFORE: dict[str, list[str]] = {
    "deploy-harp.yml": [
        "backend/**",
        "php/**",
        ".github/workflows/deploy-harp.yml",
        ".github/actions/setup-test-nc/**",
        "scripts/release/**",
    ],
    "integration.yml": [
        "php/**",
        "backend/**",
        "testdata/corpus/**",
        "testdata/CORPUS.md",
        "scripts/dev/build_corpus.py",
        "scripts/ci/**",
        ".github/workflows/integration.yml",
        ".github/actions/setup-test-nc/**",
    ],
    "php.yml": [
        "php/**",
        "backend/appinfo/**",
        ".github/workflows/php.yml",
        ".github/workflows/release.yml",
        "scripts/dev/validate_info_xml.sh",
    ],
    "python.yml": [
        "backend/**",
        "scripts/**",
        ".github/workflows/python.yml",
        "docs/measurements/**",
        "php/l10n/**",
        "docs/l10n-*.md",
    ],
    "resilience.yml": [
        "backend/**",
        "php/**",
        ".github/workflows/resilience.yml",
        ".github/actions/setup-test-nc/**",
    ],
}


def _triggers(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), path.name
    # YAML 1.1 reads a bare ``on`` key as the boolean true.
    on = loaded.get("on", loaded.get(True))
    if isinstance(on, str):
        return {on: None}
    if isinstance(on, list):
        return {str(event): None for event in on}
    assert isinstance(on, dict), path.name
    return on


def _push_blocks() -> dict[str, Any]:
    blocks: dict[str, Any] = {}
    for path in sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml")):
        triggers = _triggers(path)
        if "push" in triggers:
            blocks[path.name] = triggers["push"]
    return blocks


def _filter_regex(pattern: str) -> re.Pattern[str]:
    """Translate one GitHub branch or tag filter into a regular expression."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        char = pattern[i]
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        if char == "*":
            out.append("[^/]*")
        elif char in "+?":
            out.append(char)
        elif char == "[":
            end = pattern.index("]", i)
            out.append(pattern[i : end + 1])
            i = end + 1
            continue
        else:
            out.append(re.escape(char))
        i += 1
    return re.compile("".join(out))


def _matches(patterns: list[str], ref: str) -> bool:
    return any(_filter_regex(pattern).fullmatch(ref) for pattern in patterns)


def test_the_scan_sees_the_workflows_it_judges() -> None:
    blocks = _push_blocks()
    # The five that carried paths alone plus the four with a branch or tag filter.
    assert set(PATHS_BEFORE) <= set(blocks)
    assert {"docker.yml", "release.yml", "scorecard.yml", "security.yml"} <= set(blocks)


@pytest.mark.parametrize("name", sorted(_push_blocks()))
def test_every_push_block_names_branches_or_tags(name: str) -> None:
    block = _push_blocks()[name]
    assert isinstance(block, dict), f"{name}: a bare push trigger fires on every tag"
    assert "branches" in block or "tags" in block, f"{name}: a push block without branches or tags fires on every tag"
    assert "branches-ignore" not in block, name
    assert "tags-ignore" not in block, name


@pytest.mark.parametrize("name", sorted(_push_blocks()))
def test_every_tag_filter_is_the_release_pattern(name: str) -> None:
    block = _push_blocks()[name]
    assert isinstance(block, dict), name
    assert block.get("tags", [RELEASE_TAG_PATTERN]) == [RELEASE_TAG_PATTERN], name


@pytest.mark.parametrize("name", sorted(PATHS_BEFORE))
def test_the_former_paths_only_workflows_carry_both_filters(name: str) -> None:
    block = _push_blocks()[name]
    assert isinstance(block, dict), name
    assert block.get("branches") == ["**"], name
    assert block.get("tags") == [RELEASE_TAG_PATTERN], name
    assert block.get("paths") == PATHS_BEFORE[name], name


def test_the_release_pattern_admits_release_tags_and_nothing_else() -> None:
    tags = [RELEASE_TAG_PATTERN]
    assert _matches(tags, "v1.5.0")
    assert _matches(tags, "v1.4.2")
    assert _matches(tags, "v10.20.30")
    assert not _matches(tags, "source-1.5-dev")
    assert not _matches(tags, "source-1.5-dev.2")
    assert not _matches(tags, "v1.5")
    assert not _matches(tags, "v1.5.0-rc1")
    assert not _matches(tags, "1.5.0")


def test_no_workflow_starts_on_the_source_mirror_tag() -> None:
    for name, block in _push_blocks().items():
        assert isinstance(block, dict), name
        if "tags" in block:
            # source-1.5-dev.2 is the mirror that carries the archives, after the
            # first tag became an immutable release without them (plan 31-01).
            for tag in ("source-1.5-dev", "source-1.5-dev.2"):
                assert not _matches(block["tags"], tag), (name, tag)
        else:
            # Without a tag filter only a branch filter is left, and a branch
            # filter alone means no tag starts this workflow.
            assert "branches" in block, name


def test_the_branch_filter_admits_every_branch() -> None:
    assert _matches(["**"], "main")
    assert _matches(["**"], "feature/x")
    assert not _matches(["main"], "feature/x")
