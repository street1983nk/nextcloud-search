"""The six type group names, held together across five places (D-32-03).

The type filter of the unified search (plan 32-01, USRCH-01) splits one decision
between two halves on purpose. The container refuses an unknown group with a 422,
because only the PHP companion calls it and an unknown name there is a defect.
The PHP side falls back silently: a value somebody typed into the address bar or
into the filter field of the unified search costs a chip and never an error.

That split only works while both halves know the very same six names. A name
PHP lets through and the container does not know is answered with a 422, and a
422 arrives in the unified search dialog as an empty result group: the user sees
"nothing found" for a filter the surface offered, which is exactly the outcome
ROADMAP success criterion 3 rules out. A name the container knows and PHP drops
is a group nobody can ever reach. Neither drift is an error anywhere at runtime,
so this gate is the only place that sees it.

The five places are the PHP constant ``SearchFilters::TYPES`` (read as text,
because a PHP constant cannot be imported), the ``Literal`` of ``types`` on the
two request bodies of /search and /snippets and on the query parameter of
/diagnose (read through ``typing.get_args`` from the models themselves, never by
pattern over the source), and the keys of ``TYPE_GROUPS``. The order is compared
too: it is the order of the chip row and the order PHP canonicalises into.
"""

from __future__ import annotations

import re
import typing
from pathlib import Path

from findling.api.diagnose import read_diagnosis
from findling.api.search import SearchRequest
from findling.api.snippets import SnippetsRequest
from findling.query.rewrite import TYPE_GROUPS

PHP_SEARCH_FILTERS = Path(__file__).resolve().parents[2] / "php" / "lib" / "Service" / "SearchFilters.php"

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"(?m)(?://|#).*$")
_TYPES_CONSTANT = re.compile(r"\bconst\s+TYPES\s*=\s*\[(?P<body>.*?)\]\s*;", re.DOTALL)
_QUOTED = re.compile(r"'([^']*)'")


def php_type_groups(source: str) -> list[str] | None:
    """The names of the TYPES constant in source order, or None without one.

    Comments are removed first: the class comment of SearchFilters talks about
    the group names in prose, and a name quoted there must never count.
    """
    code = _LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", source))
    block = _TYPES_CONSTANT.search(code)
    if block is None:
        return None
    return _QUOTED.findall(block.group("body"))


def _literal_names(annotation: object) -> tuple[str, ...]:
    """The names of the one Literal inside list[...] or tuple[..., ...]."""
    if typing.get_origin(annotation) is typing.Annotated:
        annotation = typing.get_args(annotation)[0]
    element = typing.get_args(annotation)[0]
    assert typing.get_origin(element) is typing.Literal, f"no Literal inside {annotation!r}"
    return tuple(str(name) for name in typing.get_args(element))


def _sources() -> dict[str, tuple[str, ...] | None]:
    php = php_type_groups(PHP_SEARCH_FILTERS.read_text(encoding="utf-8"))
    search_types = SearchRequest.model_fields["types"].annotation
    snippets_types = SnippetsRequest.model_fields["types"].annotation
    diagnose_types = typing.get_type_hints(read_diagnosis, include_extras=True)["types"]
    return {
        "php SearchFilters::TYPES": None if php is None else tuple(php),
        "/search SearchRequest.types": _literal_names(search_types),
        "/snippets SnippetsRequest.types": _literal_names(snippets_types),
        "/diagnose types": _literal_names(diagnose_types),
        "rewrite TYPE_GROUPS": tuple(TYPE_GROUPS),
    }


def parity_findings(sources: dict[str, tuple[str, ...] | None]) -> list[str]:
    """One line per place that differs from the first one, empty on agreement."""
    names = list(sources)
    reference_name = names[0]
    reference = sources[reference_name]
    findings: list[str] = []
    if reference is None:
        findings.append(f"{reference_name} was not found")
    for name in names[1:]:
        values = sources[name]
        if values is None:
            findings.append(f"{name} was not found")
        elif reference is not None and values != reference:
            findings.append(f"{name} is {list(values)}, {reference_name} is {list(reference)}")
    return findings


def test_the_six_group_names_are_the_same_in_all_five_places() -> None:
    sources = _sources()

    assert parity_findings(sources) == []
    assert len(sources["rewrite TYPE_GROUPS"] or ()) == 6


def test_the_reader_finds_the_constant_and_ignores_names_in_comments() -> None:
    # Positive control of the reader: a real constant is found, and a quoted
    # name in a comment above it is not mistaken for a member.
    source = (
        "<?php\n"
        "/** The group 'videos' is not offered. */\n"
        "final class SearchFilters {\n"
        "    // 'audio' neither\n"
        "    public const TYPES = ['pdf', 'images'];\n"
        "}\n"
    )

    assert php_type_groups(source) == ["pdf", "images"]


def test_a_swapped_order_is_a_finding() -> None:
    source = "<?php final class S { public const TYPES = ['documents', 'pdf', 'spreadsheets', "
    source += "'presentations', 'images', 'text']; }"
    sources = _sources() | {"php SearchFilters::TYPES": tuple(php_type_groups(source) or ())}

    findings = parity_findings(sources)

    assert len(findings) == 4
    assert all("php SearchFilters::TYPES is ['documents', 'pdf'" in line for line in findings)


def test_a_seventh_name_is_a_finding() -> None:
    source = "<?php final class S { public const TYPES = ['pdf', 'documents', 'spreadsheets', "
    source += "'presentations', 'images', 'text', 'videos']; }"
    sources = _sources() | {"php SearchFilters::TYPES": tuple(php_type_groups(source) or ())}

    findings = parity_findings(sources)

    assert len(findings) == 4
    assert all("'videos'" in line for line in findings)


def test_a_missing_constant_is_a_finding_and_never_agreement() -> None:
    source = "<?php final class S { public const SORTS = ['relevance']; }"
    assert php_type_groups(source) is None

    sources = _sources() | {"php SearchFilters::TYPES": None}

    assert parity_findings(sources) == ["php SearchFilters::TYPES was not found"]


def test_a_renamed_group_on_the_container_side_is_a_finding() -> None:
    renamed = tuple("pictures" if name == "images" else name for name in TYPE_GROUPS)
    sources = _sources() | {"rewrite TYPE_GROUPS": renamed}

    findings = parity_findings(sources)

    assert len(findings) == 1
    assert findings[0].startswith("rewrite TYPE_GROUPS is")
