"""The per document coverage counts of the store (plan 43-03, D-43-07, D-43-09, D-43-14).

Issue #25 was closed three times while the figure on the admin page was still
wrong, and every time the tests had checked a part and never the whole. This
module holds the whole against a truth that was counted by hand: the topology in
tests/fixtures/coverage_topology.json has share groups with a different view per
member, a document only the smallest member sees, a reshare that gives one file
two reader paths, two mount points of one share, the same file on two shares, a
storage that is no longer mounted, tombstones, a row of storage 0 and the
sentinel of plan 43-16. The expected numbers in that file are not output of the
code under test; a second, random topology is checked against a plain Python set
computation that shares nothing with the SQL.

The PHP half of the same file is checked by php/tests/Unit/CoverageTopologyParityTest.php
(plan 43-05).
"""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest

from findling.store import repo
from findling.store.repo import FileMeta, coverage_counts, open_store
from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

FIXTURE: Path = Path(__file__).parent / "fixtures" / "coverage_topology.json"


def _topology() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _key(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _build(root: Path, rows: Sequence[Mapping[str, Any]]) -> tuple[Path, Path]:
    """Write the rows into a real state.db and their chunks into a real vectors.db."""
    state_db = root / "state.db"
    vectors_db = root / "vectors.db"
    store = open_store(state_db)
    try:
        for row in rows:
            label = row["doc_key"]
            meta = FileMeta(
                storage_id=int(row["storage_id"]),
                root_id=max(1, int(row["storage_id"])),
                path=str(row["path"]),
                title=None,
                mime="text/plain",
                size=10,
                mtime=1_700_000_000,
                doc_key=_key(label) if label else None,
            )
            store.record(int(row["file_id"]), meta, str(row["state"]), row["reason"])
            if label == "":
                store.set_doc_keys({}, absent=[int(row["file_id"])])
            if row["deleted"]:
                store.tombstone(int(row["file_id"]))
    finally:
        store.close()
    stock = open_vectors(vectors_db)
    try:
        for row in rows:
            if int(row["chunks"]) > 0:
                stock.replace_chunks(
                    int(row["file_id"]),
                    [
                        Chunk(ordinal=ordinal, char_start=0, char_end=10, embedding=bytes(EMBEDDING_DIMENSIONS))
                        for ordinal in range(int(row["chunks"]))
                    ],
                )
    finally:
        stock.close()
    return state_db, vectors_db


def _by_storage(expected: Mapping[str, int]) -> dict[int, int]:
    return {int(storage_id): int(value) for storage_id, value in expected.items()}


@pytest.fixture
def topology(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    data = _topology()
    state_db, vectors_db = _build(tmp_path, data["rows"])
    return data, state_db, vectors_db


def test_the_fixture_matches_the_hand_derived_truth(topology: tuple[dict[str, Any], Path, Path]) -> None:
    data, state_db, vectors_db = topology
    expected = data["expected"]

    counts = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    assert counts.documents == expected["documents"]
    assert counts.embedded_documents == expected["embeddedDocuments"]
    assert counts.judged_documents == expected["judgedDocuments"]
    assert counts.doc_keys_missing == expected["docKeysMissing"]
    assert list(counts.documents_by_group) == expected["documentsByGroup"]
    assert list(counts.judged_by_group) == expected["judgedByGroup"]
    assert dict(counts.documents_by_storage) == _by_storage(expected["documentsByStorage"])
    assert dict(counts.judged_by_storage) == _by_storage(expected["judgedByStorage"])


def test_the_sums_are_the_sums_of_the_parts(topology: tuple[dict[str, Any], Path, Path]) -> None:
    data, state_db, vectors_db = topology

    counts = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    assert counts.documents == sum(counts.documents_by_group) + sum(counts.documents_by_storage.values())
    assert counts.judged_documents == sum(counts.judged_by_group) + sum(counts.judged_by_storage.values())


def test_no_group_and_no_single_storage_counts_more_documents_than_verdicts(
    topology: tuple[dict[str, Any], Path, Path],
) -> None:
    data, state_db, vectors_db = topology

    counts = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    for documents, judged in zip(counts.documents_by_group, counts.judged_by_group, strict=True):
        assert documents <= judged
    for storage_id, documents in counts.documents_by_storage.items():
        assert documents <= counts.judged_by_storage.get(storage_id, 0)
    assert counts.documents <= counts.judged_documents
    assert counts.embedded_documents <= counts.documents


def test_a_reshare_to_an_earlier_reader_counts_once(tmp_path: Path) -> None:
    # A1: anna reads the file under Daten/, aaron, who sorts before her and
    # received the folder as a Nextcloud share, became the reader of the second
    # member and reads it under Shared/. Two reader paths, one internal path.
    rows = [
        {"file_id": 1, "storage_id": 11, "path": "Daten/x/a.txt", "doc_key": "x/a.txt"},
        {"file_id": 2, "storage_id": 12, "path": "Shared/x/a.txt", "doc_key": "x/a.txt"},
    ]
    state_db, vectors_db = _build(tmp_path, [_indexed(row) for row in rows])

    counts = coverage_counts(state_db, vectors_db, [11, 12], [[11, 12]])

    assert counts.documents == 1
    assert list(counts.documents_by_group) == [1]


def test_two_mount_points_of_one_share_count_once(tmp_path: Path) -> None:
    rows = [
        {"file_id": 1, "storage_id": 11, "path": "Daten/y/a4.txt", "doc_key": "y/a4.txt"},
        {"file_id": 2, "storage_id": 12, "path": "Daten2/y/a4.txt", "doc_key": "y/a4.txt"},
    ]
    state_db, vectors_db = _build(tmp_path, [_indexed(row) for row in rows])

    counts = coverage_counts(state_db, vectors_db, [11, 12], [[11, 12]])

    assert counts.documents == 1
    assert counts.judged_documents == 1


def test_the_reader_path_is_not_the_key(tmp_path: Path) -> None:
    # The positive control of the two tests above: the same reader path with
    # two internal paths is two documents, so the count follows doc_key and
    # never files.path.
    rows = [
        {"file_id": 1, "storage_id": 11, "path": "Daten/same.txt", "doc_key": "one/same.txt"},
        {"file_id": 2, "storage_id": 12, "path": "Daten/same.txt", "doc_key": "two/same.txt"},
    ]
    state_db, vectors_db = _build(tmp_path, [_indexed(row) for row in rows])

    counts = coverage_counts(state_db, vectors_db, [11, 12], [[11, 12]])

    assert counts.documents == 2


def test_rows_without_a_key_in_a_group_are_named_and_never_guessed(tmp_path: Path) -> None:
    data = _topology()
    variant = next(item for item in data["variants"] if item["name"] == "backfill_open")
    state_db, vectors_db = _build(tmp_path, [*data["rows"], *variant["extraRows"]])

    counts = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    assert counts.doc_keys_missing == variant["expected"]["docKeysMissing"]
    assert counts.doc_keys_missing > 0
    assert counts.documents == variant["expected"]["documents"]
    assert counts.judged_documents == variant["expected"]["judgedDocuments"]


def _variant(name: str) -> dict[str, Any]:
    return next(item for item in _topology()["variants"] if item["name"] == name)


def test_a_gateway_422_counts_once_and_never_in_judged(tmp_path: Path) -> None:
    # D-43-16 with D-43-11 (plan 43-18): the container verdict skipped/unreadable
    # of a gateway 422 is counted by the PHP side out of oc_findling_file_state,
    # with N1, in the denominator and in notReadable. judged leaves it out, so
    # the document stands in the denominator exactly once and the share never
    # passes a hundred per cent.
    variant = _variant("gateway_unreadable")
    expected = variant["expected"]
    state_db, vectors_db = _build(tmp_path, variant["rows"])

    counts = coverage_counts(state_db, vectors_db, variant["mounted"], variant["groups"])

    assert counts.documents == expected["documents"]
    assert counts.embedded_documents == expected["embeddedDocuments"]
    assert counts.judged_documents == expected["judgedDocuments"]
    assert counts.doc_keys_missing == expected["docKeysMissing"]
    assert list(counts.documents_by_group) == expected["documentsByGroup"]
    assert list(counts.judged_by_group) == expected["judgedByGroup"]
    assert dict(counts.documents_by_storage) == _by_storage(expected["documentsByStorage"])
    assert dict(counts.judged_by_storage) == _by_storage(expected["judgedByStorage"])
    php = expected["php"]
    parts = php["denominatorParts"]
    for index, judged in enumerate(counts.judged_by_group):
        part = parts["groups"][index]
        assert part == max(php["groupParts"]["groups"][index], judged + php["phpOnly"]["byGroup"][index])
        assert counts.documents_by_group[index] <= part
    for storage_id, judged in counts.judged_by_storage.items():
        key = str(storage_id)
        part = parts["singles"][key]
        assert part == max(php["groupParts"]["singles"][key], judged + php["phpOnly"]["byStorage"][key])
        assert counts.documents_by_storage[storage_id] <= part
    assert php["denominator"] == sum(parts["groups"]) + sum(parts["singles"].values())
    assert php["counted"] == counts.documents
    assert php["counted"] * 100 // php["denominator"] == php["percent"] <= 100


def test_the_sentinel_counts_as_a_document_of_its_own_and_is_no_missing_key(tmp_path: Path) -> None:
    rows = [
        {"file_id": 1, "storage_id": 11, "path": "Daten/a.txt", "doc_key": ""},
        {"file_id": 2, "storage_id": 12, "path": "Daten/a.txt", "doc_key": ""},
        {"file_id": 3, "storage_id": 12, "path": "Daten/b.txt", "doc_key": "b.txt"},
    ]
    state_db, vectors_db = _build(tmp_path, [_indexed(row) for row in rows])

    counts = coverage_counts(state_db, vectors_db, [11, 12], [[11, 12]])

    # Two sentinel rows are two documents over (storage_id, file_id), never
    # one document under the shared key ''.
    assert counts.documents == 3
    assert counts.doc_keys_missing == 0


def test_an_empty_mount_list_counts_nothing(topology: tuple[dict[str, Any], Path, Path]) -> None:
    data, state_db, vectors_db = topology

    counts = coverage_counts(state_db, vectors_db, [], data["groups"])

    assert (counts.documents, counts.embedded_documents, counts.judged_documents) == (0, 0, 0)
    assert list(counts.documents_by_group) == [0, 0]
    assert dict(counts.documents_by_storage) == {}
    assert counts.doc_keys_missing == 0


def test_a_group_member_that_is_not_mounted_is_ignored(tmp_path: Path) -> None:
    rows = [
        {"file_id": 1, "storage_id": 11, "path": "Daten/a.txt", "doc_key": "a.txt"},
        {"file_id": 2, "storage_id": 12, "path": "Daten/b.txt", "doc_key": "b.txt"},
        {"file_id": 3, "storage_id": 12, "path": "Daten/c.txt", "doc_key": None},
    ]
    state_db, vectors_db = _build(tmp_path, [_indexed(row) for row in rows])

    counts = coverage_counts(state_db, vectors_db, [11], [[11, 12]])

    assert counts.documents == 1
    assert list(counts.documents_by_group) == [1]
    assert counts.doc_keys_missing == 0


def test_storage_zero_never_counts_even_when_it_is_named(topology: tuple[dict[str, Any], Path, Path]) -> None:
    data, state_db, vectors_db = topology

    counts = coverage_counts(state_db, vectors_db, [0, -1, *data["mounted"]], data["groups"])

    assert counts.documents == data["expected"]["documents"]
    assert 0 not in counts.documents_by_storage
    assert -1 not in counts.judged_by_storage


def test_a_storage_that_is_not_mounted_never_counts(topology: tuple[dict[str, Any], Path, Path]) -> None:
    data, state_db, vectors_db = topology

    counts = coverage_counts(state_db, vectors_db, [41], [])

    assert counts.documents == 1
    # And the control: without 41 in the list, its rows are gone from every figure.
    without = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])
    assert 41 not in without.documents_by_storage
    assert 41 not in without.judged_by_storage


def test_a_missing_vector_stock_costs_the_vector_figure_only(tmp_path: Path) -> None:
    data = _topology()
    state_db, vectors_db = _build(tmp_path, data["rows"])
    vectors_db.unlink()

    counts = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    assert counts.embedded_documents == 0
    assert counts.documents == data["expected"]["documents"]
    assert not vectors_db.exists()


def test_the_count_never_writes_the_state_database(topology: tuple[dict[str, Any], Path, Path]) -> None:
    data, state_db, vectors_db = topology
    before = state_db.stat().st_mtime_ns, state_db.read_bytes()

    coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    assert (state_db.stat().st_mtime_ns, state_db.read_bytes()) == before


def test_the_result_carries_numbers_and_storage_ids_only(topology: tuple[dict[str, Any], Path, Path]) -> None:
    data, state_db, vectors_db = topology

    counts = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    for value in (counts.documents, counts.embedded_documents, counts.judged_documents, counts.doc_keys_missing):
        assert type(value) is int
    for part in (counts.documents_by_group, counts.judged_by_group):
        assert all(type(value) is int for value in part)
    for mapping in (counts.documents_by_storage, counts.judged_by_storage):
        assert all(type(key) is int and type(value) is int and value > 0 for key, value in mapping.items())


def test_the_predicates_are_module_constants_and_the_lists_travel_bound() -> None:
    source = Path(repo.__file__).read_text(encoding="utf-8")

    assert "INDEXED BY files_storage" in source
    assert "json_each(?1)" in source
    assert "json_each(?2)" in source


# -- the random topology against a plain set computation -------------------


_STATES: tuple[tuple[str, str | None], ...] = (
    ("indexed", None),
    ("indexed", "truncated"),
    ("skipped", "too_large"),
    ("skipped", "mime_not_allowed"),
    ("skipped", "excluded"),
    ("skipped", "gone"),
    ("skipped", "encrypted"),
    ("failed", "corrupt"),
    ("skipped", "unreadable"),
)


def _random_rows(seed: int) -> list[dict[str, Any]]:
    chooser = random.Random(seed)  # noqa: S311, a fixed seed for a reproducible topology, no secret
    labels = [f"f{number}.txt" for number in range(40)]
    rows: list[dict[str, Any]] = []
    for file_id in range(1, 201):
        state, reason = chooser.choice(_STATES)
        roll = chooser.random()
        doc_key: str | None = chooser.choice(labels)
        if roll < 0.05:
            doc_key = None
        elif roll < 0.1:
            doc_key = ""
        rows.append(
            {
                "file_id": file_id,
                "storage_id": chooser.choice((0, 1, 2, 3, 4, 5, 6, 7, 8)),
                "path": f"p/{chooser.choice(labels)}",
                "doc_key": doc_key,
                "state": state,
                "reason": reason,
                "deleted": chooser.random() < 0.1,
                "chunks": chooser.choice((0, 0, 1)),
            }
        )
    return rows


def _truth(
    rows: Sequence[Mapping[str, Any]], mounted: Sequence[int], groups: Sequence[Sequence[int]]
) -> dict[str, Any]:
    """Count with Python sets only, by the rule of D-43-07 and D-43-14."""
    mounted_set = {storage_id for storage_id in mounted if storage_id > 0}
    group_of = {member: index for index, group in enumerate(groups) for member in group if member in mounted_set}
    documents: set[tuple[Any, ...]] = set()
    embedded: set[tuple[Any, ...]] = set()
    judged: set[tuple[Any, ...]] = set()
    missing = 0
    for row in rows:
        storage_id = row["storage_id"]
        if row["deleted"] or storage_id not in mounted_set:
            continue
        if storage_id in group_of:
            if row["doc_key"] is None:
                missing += 1
                continue
            label = row["doc_key"] if row["doc_key"] != "" else ("sentinel", row["file_id"])
            key: tuple[Any, ...] = ("group", group_of[storage_id], label)
        else:
            key = ("single", storage_id, row["file_id"])
        if row["state"] == "indexed":
            documents.add(key)
            if row["chunks"] > 0:
                embedded.add(key)
        if not (row["state"] == "skipped" and row["reason"] in {"mime_not_allowed", "excluded", "gone", "unreadable"}):
            judged.add(key)
    return {"documents": len(documents), "embedded": len(embedded), "judged": len(judged), "missing": missing}


@pytest.mark.parametrize("seed", [4303, 25, 1603])
def test_a_random_topology_matches_a_plain_set_computation(tmp_path: Path, seed: int) -> None:
    rows = _random_rows(seed)
    mounted = [1, 2, 3, 4, 5, 6, 7]
    groups = [[1, 2, 3], [4, 5]]
    state_db, vectors_db = _build(tmp_path, rows)
    truth = _truth(rows, mounted, groups)

    counts = coverage_counts(state_db, vectors_db, mounted, groups)

    assert counts.documents == truth["documents"]
    assert counts.embedded_documents == truth["embedded"]
    assert counts.judged_documents == truth["judged"]
    assert counts.doc_keys_missing == truth["missing"]
    assert counts.documents <= counts.judged_documents
    # The control that the truth is not trivially empty.
    assert truth["documents"] > 10


def _indexed(row: Mapping[str, Any]) -> dict[str, Any]:
    return {**row, "state": "indexed", "reason": None, "deleted": False, "chunks": 0}


# -- one share under several roots and spellings (plans 43-21 to 43-23) ------


def _roots() -> tuple[dict[str, Any], dict[str, Any]]:
    data = _topology()
    return data, next(item for item in data["variants"] if item["name"] == "roots")


def _format_two(share: str, share_path: str) -> str:
    return hashlib.sha256(b"2\x00" + share.encode("utf-8") + b"\x00" + share_path.encode("utf-8")).hexdigest()


def test_the_keys_of_the_roots_variant_are_format_two_over_the_share_path() -> None:
    # The fixture keys are recomputed from the identity and the internal path
    # by the rule of plan 43-22, never taken from the code under test.
    _, variant = _roots()
    identities = variant["identities"]
    for row in variant["extraRows"]:
        identity = identities[str(row["storage_id"])]
        root = identity["root"]
        share_path = row["internalPath"] if root == "" else root + "/" + row["internalPath"]
        assert share_path == row["sharePath"], row["file_id"]
        assert _format_two(identity["share"], share_path) == row["doc_key"], row["file_id"]
    for row in variant["expected"]["php"]["extraPhpOnlyRows"]:
        root = identities[str(row["storage_id"])]["root"]
        assert (row["internalPath"] if root == "" else root + "/" + row["internalPath"]) == row["sharePath"]
    for row in variant["expected"]["php"]["fileCacheWithoutVerdict"]:
        assert hashlib.md5(row["internalPath"].encode("utf-8"), usedforsecurity=False).hexdigest() == row["pathHash"]
    shares = {identity["share"] for key, identity in identities.items() if int(key) in variant["groups"][0]}
    assert shares == {"smb::fs.example//daten"}


def test_one_share_under_two_roots_and_two_spellings_counts_every_file_once(tmp_path: Path) -> None:
    # The container needs no change for the roots: equal keys are enough.
    data, variant = _roots()
    expected = variant["expected"]
    state_db, vectors_db = _build(tmp_path, [*data["rows"], *variant["extraRows"]])

    counts = coverage_counts(state_db, vectors_db, variant["mounted"], variant["groups"])

    assert counts.documents == expected["documents"]
    assert counts.embedded_documents == expected["embeddedDocuments"]
    assert counts.judged_documents == expected["judgedDocuments"]
    assert counts.doc_keys_missing == expected["docKeysMissing"]
    assert list(counts.documents_by_group) == expected["documentsByGroup"]
    assert list(counts.judged_by_group) == expected["judgedByGroup"]
    assert dict(counts.documents_by_storage) == _by_storage(expected["documentsByStorage"])
    assert dict(counts.judged_by_storage) == _by_storage(expected["judgedByStorage"])


def test_the_share_path_keeps_one_file_together_and_two_files_apart(tmp_path: Path) -> None:
    # The total of the variant is the same under the internal path by accident
    # (r1 twice, r3 merged), so this holds the two cases one by one.
    _, variant = _roots()
    rows = {row["file_id"]: row for row in variant["extraRows"]}
    together = [_indexed(rows[file_id]) for file_id in (1121, 1421, 1521)]
    apart = [_indexed(rows[file_id]) for file_id in (1123, 1423)]

    for chosen, documents in ((together, 1), (apart, 2)):
        root = tmp_path / str(documents)
        root.mkdir()
        state_db, vectors_db = _build(root, chosen)
        counts = coverage_counts(state_db, vectors_db, [11, 14, 15], [[11, 14, 15]])
        assert counts.documents == documents


def test_the_roots_variant_keeps_every_part_within_its_denominator() -> None:
    _, variant = _roots()
    expected = variant["expected"]
    php = expected["php"]
    parts = php["denominatorParts"]

    for index, judged in enumerate(expected["judgedByGroup"]):
        assert parts["groups"][index] == max(
            php["groupParts"]["groups"][index], judged + php["phpOnly"]["byGroup"][index]
        )
        assert expected["documentsByGroup"][index] <= parts["groups"][index]
    for key, judged in expected["judgedByStorage"].items():
        assert parts["singles"][key] == max(
            php["groupParts"]["singles"][key], judged + php["phpOnly"]["byStorage"][key]
        )
        assert expected["documentsByStorage"][key] <= parts["singles"][key]
    assert php["denominator"] == sum(parts["groups"]) + sum(parts["singles"].values())
    assert php["counted"] == expected["documents"]
    assert php["counted"] * 100 // php["denominator"] == php["percent"] <= 100
    assert php["embedded"] * 100 // php["denominator"] == php["embeddedPercent"]
    assert php["notReadable"] == sum(php["phpOnly"]["notReadableByGroup"]) + sum(
        php["phpOnly"]["notReadableByStorage"].values()
    )


def test_without_the_roots_variant_the_main_topology_is_unchanged(
    topology: tuple[dict[str, Any], Path, Path],
) -> None:
    data, state_db, vectors_db = topology
    _, variant = _roots()

    counts = coverage_counts(state_db, vectors_db, data["mounted"], data["groups"])

    assert list(counts.documents_by_group) == data["expected"]["documentsByGroup"]
    assert data["expected"]["php"]["phpOnly"]["byGroup"] == [3, 1]
    assert 14 not in data["mounted"]
    assert 15 not in data["mounted"]
    assert variant["mounted"] == sorted([*data["mounted"], 14, 15])
