"""The shared catalogue of the share identity and who may call it (plan 43-21).

The companion groups the storages of one share for the coverage figure only:
host and share name fold to ASCII lower case, the root stays apart and unfolded
(D-43-15, D-43-17, OE-1 a to OE-4 a). backend/tests/fixtures/
share_identity_cases.json holds the cases php/tests/Unit/StorageServiceTest.php
runs against StorageService. This module checks the catalogue itself, without
the code under test: its form, every md5 of a hashed id recomputed with hashlib,
the folded parts in ASCII lower case, the roots without edge slashes and in NFC,
and the counters it promises.

The document key catalogue backend/tests/fixtures/doc_key_cases.json is
recomputed here as well, both formats, from its fields and with hashlib only:
format 2 (plan 43-22) over the share and the share path, format 1 (plan 43-15)
over the path alone, kept as history.

It also holds where the identity and the document key may be used at all: only
in the counting services, never in search, path, permission, gateway or
listener code (T-43-63).
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, cast

import pytest

REPO = Path(__file__).resolve().parents[2]
CATALOGUE = Path(__file__).resolve().parent / "fixtures" / "share_identity_cases.json"
DOC_KEYS = Path(__file__).resolve().parent / "fixtures" / "doc_key_cases.json"
PHP_LIB = REPO / "php" / "lib"
PHP_TESTS = REPO / "php" / "tests" / "Unit"
DECISIONS = REPO / ".planning" / "phases" / "43-findling-1-6-3-sweep-und-zaehler" / "43-FREIGABEN.md"
HEX32 = re.compile(r"[0-9a-f]{32}")
HEX64 = re.compile(r"[0-9a-f]{64}")
OUTCOMES = {"verified", "ungrouped", "placeholder", "excluded"}
STAT_KEYS = ["parsed", "hashedVerified", "hashedUngrouped", "placeholder", "excluded"]

SHARE_IDENTITIES_ALLOWED = {
    "Service/StorageService.php",
    "Service/DocKeyService.php",
    "Service/AdminViewService.php",
}
DOC_KEY_ALLOWED = {
    "Service/DocKeyService.php",
    "Service/FileStateService.php",
    "Service/QueueService.php",
    "Controller/ReconcileController.php",
}
COUNTING_CALLS = ("shareIdentity(", "shareIdentities(", "shareIdentityStats(", "docKeyOf(", "docKeysFor(")


def _catalogue() -> dict[str, Any]:
    return cast("dict[str, Any]", json.loads(CATALOGUE.read_text(encoding="ascii")))


def _ascii_lower(text: str) -> str:
    """Lower case for A to Z only, which is what PHP 8 strtolower does."""
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in text)


def _users(root: Path, needle: str) -> set[str]:
    return {
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*.php")
        if needle in path.read_text(encoding="utf-8")
    }


def _forbidden(relative: str) -> bool:
    return relative in {
        "Service/SearchService.php",
        "Service/PathResolverService.php",
        "Controller/GatewayController.php",
    } or relative.startswith(("Search/", "Listener/"))


# -- form ------------------------------------------------------------------------


def test_the_catalogue_is_pure_ascii_and_has_every_part() -> None:
    CATALOGUE.read_bytes().decode("ascii")
    doc = _catalogue()

    assert set(doc) == {"_comment", "decisions", "cases", "hashed", "groups", "stats"}
    assert len(doc["cases"]) >= 30
    assert len(doc["hashed"]) >= 8
    assert sorted(doc["stats"]) == sorted(STAT_KEYS)


def test_the_decisions_of_the_catalogue_are_the_released_ones() -> None:
    released = DECISIONS.read_text(encoding="utf-8")
    for decision, choice in _catalogue()["decisions"].items():
        line = re.compile(rf"^Freigabe Entscheid 43-21 {decision}: .* Entscheid: {choice}$", re.MULTILINE)
        assert len(line.findall(released)) == 1, decision


def test_every_case_has_its_form() -> None:
    decisions = _catalogue()["decisions"]
    for case in _catalogue()["cases"]:
        assert set(case) <= {"id", "expected", "why", "decision"}, case
        assert isinstance(case["id"], str)
        assert isinstance(case["why"], str), case["id"]
        assert case["why"], case["id"]
        if "decision" in case:
            assert case["decision"] in decisions
        expected = case["expected"]
        if expected is not None:
            assert set(expected) == {"share", "root"}, case["id"]


# -- the identities typed by hand ------------------------------------------------


def _identities() -> list[tuple[str, dict[str, str]]]:
    doc = _catalogue()
    found = [(c["id"], c["expected"]) for c in doc["cases"] if c["expected"] is not None]
    found += [(h["actual"], h["expected"]) for h in doc["hashed"] if h["expected"] is not None]
    return found


@pytest.mark.parametrize(("storage_id", "identity"), _identities())
def test_folded_parts_are_ascii_lower_and_roots_have_no_edge_slash(storage_id: str, identity: dict[str, str]) -> None:
    share = identity["share"]
    root = identity["root"]

    if share.startswith("smb::"):
        # smb::<host>//<share name>, both folded
        host, _, name = share.removeprefix("smb::").partition("//")
        assert host, storage_id
        assert name, storage_id
        assert host == _ascii_lower(host), storage_id
        assert name == _ascii_lower(name), storage_id
        assert "/" not in name
        assert "\\" not in name
    else:
        # sftp::<login>@<host>[:port], only the host folded
        assert share.startswith("sftp::"), storage_id
        login, _, host = share.removeprefix("sftp::").rpartition("@")
        assert login, storage_id
        assert host, storage_id
        assert host == _ascii_lower(host), storage_id
        assert login in storage_id, "the login name is never folded"

    assert root == root.strip("/"), storage_id
    assert "//" not in root
    assert "\\" not in root
    assert ".." not in root.split("/")
    assert "." not in root.split("/")
    assert unicodedata.normalize("NFC", root) == root


def test_a_root_that_differs_only_in_case_is_another_root() -> None:
    by_id = {c["id"]: c["expected"] for c in _catalogue()["cases"]}
    upper = by_id["smb::a@fs.example//Daten//Projekte/"]
    lower = by_id["smb::a@fs.example//Daten//projekte/"]

    assert upper["share"] == lower["share"]
    assert upper["root"] != lower["root"]


def test_the_mbozem_spellings_are_one_share() -> None:
    by_id = {c["id"]: c["expected"] for c in _catalogue()["cases"]}
    shares = {
        by_id[storage_id]["share"]
        for storage_id in (
            "smb::a@192.168.98.246//Daten//",
            "smb::b@192.168.98.246//daten//",
            "smb::c@192.168.98.246//Daten//Projekte/",
            "smb::d@192.168.98.246//DATEN//Arbeitssicherheit/",
        )
    }
    assert shares == {"smb::192.168.98.246//daten"}


# -- the hashed ids ---------------------------------------------------------------


@pytest.mark.parametrize("entry", _catalogue()["hashed"], ids=lambda entry: entry["name"])
def test_every_stored_md5_is_recomputed_and_only_a_match_gives_an_identity(entry: dict[str, Any]) -> None:
    actual = entry["actual"]

    assert len(actual) > 64, "Nextcloud hashes only ids above 64 characters"
    assert HEX32.fullmatch(entry["stored"])
    assert hashlib.md5(actual.encode(), usedforsecurity=False).hexdigest() == entry["stored"]
    assert entry["derivation"] == f"printf '%s' '{actual}' | md5sum"
    assert entry["backend"] in {"smb", "sftp"}
    assert set(entry["config"]) <= {"host", "share", "root", "user", "port"}, "never a password"
    assert entry["outcome"] in OUTCOMES

    matched = entry["reconstructed"] == actual
    if entry["outcome"] in {"verified", "excluded"}:
        assert matched, entry["name"]
    else:
        assert not matched, entry["name"]
    if entry["outcome"] == "placeholder":
        assert entry["reconstructed"] is None
        assert any("$" in str(v).replace("$user", "").replace("$USER", "") for v in entry["config"].values())
    assert (entry["expected"] is not None) == (entry["outcome"] == "verified")


# -- groups and counters ----------------------------------------------------------


def test_the_mbozem_groups_are_one_share_of_47_and_a_pair() -> None:
    groups = _catalogue()["groups"]
    storages = {s["numeric_id"]: s["id"] for s in groups["storages"]}
    expected = groups["expected"]

    assert [len(group) for group in expected] == [47, 2]
    mbozem = [storages[n] for n in expected[0]]
    assert sum(1 for s in mbozem if s.endswith("//Daten//")) == 25
    assert sum(1 for s in mbozem if s.endswith("//daten//")) == 5
    assert len({s.split("//Daten//", 1)[1] for s in mbozem if "//Daten//" in s} - {""}) == 6
    assert sum(1 for s in mbozem if "//Daten//" in s and not s.endswith("//Daten//")) == 17
    grouped = {n for group in expected for n in group}
    assert grouped.isdisjoint({301, 401}), "a share alone and a home are no group"
    for group in expected:
        assert group == sorted(group)


def test_the_counters_follow_the_cases() -> None:
    doc = _catalogue()
    cases = doc["cases"]
    hashed = doc["hashed"]
    outcomes = [h["outcome"] for h in hashed]

    assert doc["stats"] == {
        "parsed": sum(1 for c in cases if c["expected"] is not None),
        "hashedVerified": outcomes.count("verified"),
        "hashedUngrouped": outcomes.count("ungrouped") + outcomes.count("placeholder"),
        "placeholder": outcomes.count("placeholder"),
        "excluded": sum(1 for c in cases if c["expected"] is None and c["id"].startswith(("smb::", "sftp::")))
        + outcomes.count("excluded"),
    }


# -- who may call it (T-43-63) ----------------------------------------------------


def test_the_search_for_callers_finds_a_known_caller() -> None:
    """Positive control: the same search finds the PHP test of the catalogue."""
    assert "StorageServiceTest.php" in _users(PHP_TESTS, "shareIdentities(")
    assert "Service/DocKeyService.php" in _users(PHP_LIB, "docKeyOf(")


def test_share_identities_are_asked_by_the_counting_services_only() -> None:
    assert _users(PHP_LIB, "shareIdentities(") <= SHARE_IDENTITIES_ALLOWED


@pytest.mark.parametrize("needle", ["docKeyOf(", "docKeysFor("])
def test_document_keys_are_asked_by_the_counting_services_only(needle: str) -> None:
    assert _users(PHP_LIB, needle) <= DOC_KEY_ALLOWED


@pytest.mark.parametrize("needle", COUNTING_CALLS)
def test_no_search_path_gateway_or_listener_code_touches_the_counting(needle: str) -> None:
    users = _users(PHP_LIB, needle)
    assert sorted(user for user in users if _forbidden(user)) == []


# -- the document key (plan 43-22) ----------------------------------------------


def _doc_key_cases(fmt: int) -> list[dict[str, Any]]:
    cases = cast("list[dict[str, Any]]", json.loads(DOC_KEYS.read_text(encoding="ascii"))["cases"])
    return [case for case in cases if case["format"] == fmt]


def _share_path(case: dict[str, Any]) -> str:
    """root '/' path, the path without leading slashes, an empty part left out, in NFC."""
    path = str(case["path"]).lstrip("/")
    root = str(case["root"])
    if root == "":
        joined = path
    elif path == "":
        joined = root
    else:
        joined = root + "/" + path
    return unicodedata.normalize("NFC", joined)


def test_the_document_key_catalogue_is_ascii_and_holds_both_formats() -> None:
    DOC_KEYS.read_bytes().decode("ascii")
    cases = cast("list[dict[str, Any]]", json.loads(DOC_KEYS.read_text(encoding="ascii"))["cases"])

    assert {case["format"] for case in cases} == {1, 2}
    assert len(_doc_key_cases(1)) == 13
    assert len(_doc_key_cases(2)) >= 11
    names = [case["name"] for case in cases]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("case", _doc_key_cases(2), ids=lambda case: case["name"])
def test_every_format_2_key_is_recomputed_over_share_and_share_path(case: dict[str, Any]) -> None:
    assert set(case) <= {"name", "format", "share", "root", "path", "expected", "derivation", "sameAs", "differsFrom"}
    share = case["share"]
    joined = _share_path(case)

    assert HEX64.fullmatch(case["expected"])
    assert "\x00" not in share + joined
    assert hashlib.sha256(b"2\x00" + share.encode() + b"\x00" + joined.encode()).hexdigest() == case["expected"]
    assert case["derivation"] == f"printf '2\\000%s\\000%s' '{share}' '{joined}' | sha256sum"
    if share == "":
        assert case["root"] == "", "a storage without identity has no root"


@pytest.mark.parametrize("case", _doc_key_cases(1), ids=lambda case: case["name"])
def test_every_format_1_key_is_still_the_hash_of_the_path_alone(case: dict[str, Any]) -> None:
    path = unicodedata.normalize("NFC", str(case["path"]).lstrip("/"))

    assert hashlib.sha256(path.encode()).hexdigest() == case["expected"]
    assert case["derivation"] == f"printf '%s' '{path}' | sha256sum"


def test_the_relations_of_format_2_hold() -> None:
    by_name = {case["name"]: case for case in _doc_key_cases(2)}
    same = differs = 0
    for case in by_name.values():
        if "sameAs" in case:
            assert case["expected"] == by_name[case["sameAs"]]["expected"], case["name"]
            same += 1
        if "differsFrom" in case:
            assert case["expected"] != by_name[case["differsFrom"]]["expected"], case["name"]
            differs += 1

    assert same >= 7
    assert differs >= 4


def test_format_2_keys_never_meet_format_1_keys() -> None:
    old = {case["expected"] for case in _doc_key_cases(1)}
    new = {case["expected"] for case in _doc_key_cases(2)}
    assert old.isdisjoint(new)


def test_the_named_cases_of_the_plan_are_there() -> None:
    by_name = {case["name"]: case for case in _doc_key_cases(2)}
    top = by_name["share at its top"]

    assert by_name["the same file under the root Projekte"]["expected"] == top["expected"]
    assert by_name["Unterweisung under the root Arbeitssicherheit"]["sameAs"] == "Unterweisung at the top of the share"
    assert by_name["bericht.txt is another file"]["differsFrom"] == "Bericht.txt"
    assert by_name["a storage without share identity"]["share"] == ""
    assert by_name["a storage without share identity"]["path"] == top["path"]
    assert by_name["a storage without share identity"]["expected"] != top["expected"]
    assert any(case["share"].startswith("sftp::") for case in by_name.values())
    assert by_name["a home storage keeps its files/ prefix"]["path"].startswith("files/")
