"""GET /status?leaveOut=...: the two counters behind the deduplicated coverage (plan 39-01).

The admin page groups the storages of one share that is mounted once per user
(Weg C of 35-DEDUP-NOTIZ, owner decision D-37-03) and keeps one storage of each
group in its sums. The others it names in ``leaveOut``, and this route answers
with two numbers for them: ``indexedLeftOut``, the living indexed documents of
those storages, and ``embeddedLeftOut``, how many of exactly those documents
carry a vector. Nothing else about them crosses the boundary (T-04-06).

Four claims are held here. The counters count the right rows: living, indexed,
in the named storages and nowhere else. The vector count reads the real vector
stock, a file of its own without a storage column. A vector stock that is
missing or broken costs that one figure and never the answer. And the parameter
is refused with a 422 unless it is a short list of numbers (T-39-02).

The other half of the wire contract, that a call without the parameter carries
neither key, is held in test_status_endpoint.py next to the closed field set.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from findling.api import status
from findling.store.repo import FileMeta, open_store
from findling.store.vectors import EMBEDDING_DIMENSIONS, Chunk, open_vectors

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]


def _meta(storage_id: int, file_id: int) -> FileMeta:
    return FileMeta(
        storage_id=storage_id,
        root_id=storage_id,
        path=f"/Akten/Akte-{file_id}.pdf",
        title=f"Akte-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000 + file_id,
    )


def _state(root: Path) -> None:
    """Two storages with two living indexed documents each, plus three distractors.

    Storage 1 holds 11 and 12, storage 2 holds 21 and 22. Storage 2 also holds a
    skipped file (23) and a tombstoned indexed file (24), and storage 3 holds one
    indexed file (31): none of the three may count for leaveOut=2.
    """
    store = open_store(root / "state.db")
    try:
        for storage_id, file_id in ((1, 11), (1, 12), (2, 21), (2, 22), (2, 24), (3, 31)):
            store.record(file_id, _meta(storage_id, file_id), "indexed")
        store.record(23, _meta(2, 23), "skipped", "too_large")
        store.tombstone(24)
    finally:
        store.close()


def _vectors(root: Path, file_ids: list[int]) -> None:
    """Give the named documents two chunks each, in the real vector stock."""
    stock = open_vectors(root / "vectors.db")
    try:
        for file_id in file_ids:
            stock.replace_chunks(
                file_id,
                [
                    Chunk(ordinal=ordinal, char_start=0, char_end=10, embedding=bytes(EMBEDDING_DIMENSIONS))
                    for ordinal in range(2)
                ],
            )
    finally:
        stock.close()


def _status(client: TestClient, headers: dict[str, str], leave_out: str) -> dict[str, Any]:
    response = client.get("/status", params={"leaveOut": leave_out}, headers=headers)

    assert response.status_code == 200, response.text
    return response.json()


def test_the_counters_name_the_living_indexed_documents_of_the_named_storages(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    _state(volume)
    # Vectors only for the documents of storage 2, and for 24, which is
    # tombstoned and therefore never counted, and for 31 in another storage.
    _vectors(volume, [21, 22, 24, 31])

    two = _status(client, sign("admin"), "2")
    one = _status(client, sign("admin"), "1")
    both = _status(client, sign("admin"), "1,2")

    assert (two["indexedLeftOut"], two["embeddedLeftOut"]) == (2, 2)
    assert (one["indexedLeftOut"], one["embeddedLeftOut"]) == (2, 0)
    assert (both["indexedLeftOut"], both["embeddedLeftOut"]) == (4, 2)


def test_a_storage_the_container_does_not_know_counts_nought(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    _state(volume)
    _vectors(volume, [21])

    answer = _status(client, sign("admin"), "99,100")

    assert (answer["indexedLeftOut"], answer["embeddedLeftOut"]) == (0, 0)


def test_the_counters_are_contained_in_the_figures_they_are_subtracted_from(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    _state(volume)
    _vectors(volume, [11, 21, 22])

    answer = _status(client, sign("admin"), "2,3")

    assert answer["indexedLeftOut"] <= answer["indexed"]
    assert answer["embeddedLeftOut"] <= answer["embedded"]
    assert answer["embeddedLeftOut"] <= answer["indexedLeftOut"]


def test_without_a_vector_database_only_the_vector_figure_is_missing(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    _state(volume)

    answer = _status(client, sign("admin"), "2")

    assert answer["indexedLeftOut"] == 2
    assert "embeddedLeftOut" not in answer
    # The attach is read only: a missing vector stock stays missing.
    assert not (volume / "vectors.db").exists()


@pytest.mark.parametrize("content", [b"", b"this is not a sqlite database"])
def test_a_broken_vector_database_costs_the_vector_figure_and_never_the_answer(
    client: TestClient,
    sign: Sign,
    volume: Path,
    content: bytes,
) -> None:
    _state(volume)
    (volume / "vectors.db").write_bytes(content)

    answer = _status(client, sign("admin"), "2")

    assert answer["indexedLeftOut"] == 2
    assert "embeddedLeftOut" not in answer


def test_above_the_ceiling_the_vector_figure_is_not_worked_out(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The ceiling is 100000 documents; lowered here so that two documents are
    # above it instead of building a hundred thousand rows.
    _state(volume)
    _vectors(volume, [21, 22])
    monkeypatch.setattr(status, "LEFT_OUT_EMBEDDED_CEILING", 1)

    answer = _status(client, sign("admin"), "2")

    assert status.LEFT_OUT_EMBEDDED_CEILING == 1
    assert answer["indexedLeftOut"] == 2
    assert "embeddedLeftOut" not in answer


def test_the_ceiling_of_the_vector_figure_is_a_hundred_thousand_documents() -> None:
    assert status.LEFT_OUT_EMBEDDED_CEILING == 100_000


def test_without_a_state_database_neither_counter_is_answered(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    answer = _status(client, sign("admin"), "2")

    assert "indexedLeftOut" not in answer
    assert "embeddedLeftOut" not in answer


def test_a_thousand_storages_are_answered(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    # Three bands of the SQL side, one request.
    _state(volume)
    _vectors(volume, [21])

    answer = _status(client, sign("admin"), ",".join(str(storage_id) for storage_id in range(1, 1001)))

    assert (answer["indexedLeftOut"], answer["embeddedLeftOut"]) == (5, 1)


@pytest.mark.parametrize(
    "leave_out",
    [
        "a,1",
        "1,,2",
        ",1",
        "1,",
        "",
        "-1",
        "1;2",
        "1 2",
        ",".join(str(storage_id) for storage_id in range(1, 1002)),
        "1" * 8001,
        "9" * 19,
    ],
    ids=[
        "a letter",
        "an empty item",
        "a leading comma",
        "a trailing comma",
        "the empty string",
        "a negative id",
        "a semicolon",
        "a blank",
        "1001 ids",
        "over 8000 characters",
        "a number beyond the integer range of SQLite",
    ],
)
def test_anything_but_a_short_list_of_numbers_is_refused(
    client: TestClient,
    sign: Sign,
    volume: Path,
    leave_out: str,
) -> None:
    _state(volume)

    response = client.get("/status", params={"leaveOut": leave_out}, headers=sign("admin"))

    assert response.status_code == 422


def test_the_answer_with_the_parameter_carries_numbers_only(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    _state(volume)
    _vectors(volume, [21])

    answer = _status(client, sign("admin"), "2")

    assert type(answer["indexedLeftOut"]) is int
    assert type(answer["embeddedLeftOut"]) is int
    assert "Akte" not in str(answer)
