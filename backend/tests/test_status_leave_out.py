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

Since plan 41-02 (issue #25) the vector figure no longer stops at a hundred
thousand left out documents: up to LEFT_OUT_EMBEDDED_SYNC_CEILING it is counted
in the request, above it in a background thread of its own and answered from a
small cache. Single flight, a start that fails is tried again, the age runs from
the end of the count, at most four lists, and a replaced vector stock drops it.

The other half of the wire contract, that a call without the parameter carries
neither key, is held in test_status_endpoint.py next to the closed field set.
"""

import os
import threading
from collections.abc import Callable, Sequence
from pathlib import Path
from types import SimpleNamespace
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


def test_left_out_up_to_the_ceiling_is_counted_at_once(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Up to LEFT_OUT_EMBEDDED_SYNC_CEILING the figure is worked out inside the
    # request, as before plan 41-02: no thread, nothing cached. Lowered so that
    # the two documents of storage 2 sit exactly on it.
    _state(volume)
    _vectors(volume, [21, 22])
    monkeypatch.setattr(status, "LEFT_OUT_EMBEDDED_SYNC_CEILING", 2)

    answer = _status(client, sign("admin"), "2")

    assert (answer["indexedLeftOut"], answer["embeddedLeftOut"]) == (2, 2)
    assert status._LEFT_OUT_REFRESH is None
    assert not status._LEFT_OUT_CACHE


def test_left_out_above_the_ceiling_comes_from_the_background(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Issue #25 (D-41-11): an instance whose left out storages hold 113 851
    # documents got no embeddedLeftOut at all, and the deduplication of
    # AdminViewService::leftOutCounts() fell away without a word. The ceiling
    # is lowered here so that two documents are above it; the real numbers run
    # in test_phase40_audit.py. The first answer leaves the field out and starts
    # the count in the background, the answer after it carries the figure.
    _state(volume)
    _vectors(volume, [21, 22])
    monkeypatch.setattr(status, "LEFT_OUT_EMBEDDED_SYNC_CEILING", 1)

    first = _status(client, sign("admin"), "2")
    status.join_left_out_refresh()
    second = _status(client, sign("admin"), "2")

    assert first["indexedLeftOut"] == 2
    assert "embeddedLeftOut" not in first
    assert (second["indexedLeftOut"], second["embeddedLeftOut"]) == (2, 2)


def test_a_left_out_refresh_that_cannot_start_is_tried_again(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # The lesson of F-40N-03: a flag that points at a thread that never ran is
    # never cleared, and no later poll counts again until the container restarts.
    _state(volume)
    _vectors(volume, [21, 22])
    monkeypatch.setattr(status, "LEFT_OUT_EMBEDDED_SYNC_CEILING", 1)
    monkeypatch.setattr(status, "_LEFT_OUT_REFRESH", None)

    class _Unstartable(threading.Thread):
        """A thread whose start fails the way it fails without free threads.

        Only the name the status module sees is replaced: the test client and
        asyncio.to_thread start threads of their own while the request runs.
        """

        def start(self) -> None:
            raise RuntimeError("can't start new thread")

    seen_by_status = SimpleNamespace(Thread=_Unstartable, current_thread=threading.current_thread)
    with monkeypatch.context() as patch:
        patch.setattr(status, "threading", seen_by_status)
        with caplog.at_level("WARNING", logger="findling"):
            refused = _status(client, sign("admin"), "2")

    assert refused["indexedLeftOut"] == 2
    assert "embeddedLeftOut" not in refused
    assert status._LEFT_OUT_REFRESH is None
    lines = [record.getMessage() for record in caplog.records if "left out vector count" in record.getMessage()]
    assert lines == ["the left out vector count could not start, RuntimeError"]

    _status(client, sign("admin"), "2")
    status.join_left_out_refresh()
    after = _status(client, sign("admin"), "2")
    assert after["embeddedLeftOut"] == 2


class _Clock:
    """A monotonic clock the test moves by hand."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now


def test_the_left_out_cache_ages_from_the_end_of_the_count(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The lesson of F-40N-06: a count that took long must not come back stale
    # at once. The count here takes 1000 seconds of the clock, far more than
    # the 300 of LEFT_OUT_CACHE_SECONDS, so an age taken from its start would
    # expire the figure the moment it is written.
    _state(volume)
    _vectors(volume, [21, 22])
    monkeypatch.setattr(status, "LEFT_OUT_EMBEDDED_SYNC_CEILING", 1)
    clock = _Clock()
    monkeypatch.setattr(status, "time", SimpleNamespace(monotonic=clock.monotonic))
    real = status.embedded_in_storages
    counts: list[float] = []

    def _slow(state_db: Path, vectors_db: Path, storage_ids: Sequence[int]) -> int:
        counts.append(clock.now)
        clock.now += 1000
        return real(state_db, vectors_db, storage_ids)

    monkeypatch.setattr(status, "embedded_in_storages", _slow)

    _status(client, sign("admin"), "2")
    status.join_left_out_refresh()
    assert counts == [0.0]

    clock.now = 1000 + status.LEFT_OUT_CACHE_SECONDS - 1
    fresh = _status(client, sign("admin"), "2")
    status.join_left_out_refresh()
    assert fresh["embeddedLeftOut"] == 2
    assert len(counts) == 1

    clock.now = 1000 + status.LEFT_OUT_CACHE_SECONDS
    stale = _status(client, sign("admin"), "2")
    status.join_left_out_refresh()
    # The stale figure is answered while the next count runs, the way the fill
    # level of candidate F does it, so the page does not jump for one poll.
    assert stale["embeddedLeftOut"] == 2
    assert len(counts) == 2


def test_the_left_out_cache_holds_at_most_four_lists(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The list comes from the companion, and every new one would otherwise be
    # a new entry for the life of the process.
    _state(volume)
    _vectors(volume, [11, 21, 22, 31])
    monkeypatch.setattr(status, "LEFT_OUT_EMBEDDED_SYNC_CEILING", 1)

    for leave_out in ("1", "2", "1,2", "1,3", "2,3"):
        _status(client, sign("admin"), leave_out)
        status.join_left_out_refresh()

    assert status.LEFT_OUT_CACHE_KEYS == 4
    assert len(status._LEFT_OUT_CACHE) == 4
    assert frozenset({1}) not in status._LEFT_OUT_CACHE
    assert _status(client, sign("admin"), "2,3")["embeddedLeftOut"] == 3
    assert "embeddedLeftOut" not in _status(client, sign("admin"), "1")


def _replace_the_stock(volume: Path, file_ids: list[int]) -> None:
    """Put a new vector stock in place of the old one, the way a refill would."""
    fresh = volume / "fresh"
    fresh.mkdir(exist_ok=True)
    _vectors(fresh, file_ids)
    os.replace(fresh / "vectors.db", volume / "vectors.db")


def test_a_refilled_vector_stock_drops_the_cached_figure(
    client: TestClient,
    sign: Sign,
    volume: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The guard of _refresh_fill in another shape (T-41-11): a figure counted
    # on a vector stock that was replaced while the count ran is not cached,
    # and a cached figure of a stock that is gone is no figure.
    _state(volume)
    _vectors(volume, [21, 22])
    monkeypatch.setattr(status, "LEFT_OUT_EMBEDDED_SYNC_CEILING", 1)
    real = status.embedded_in_storages

    def _refilled_meanwhile(state_db: Path, vectors_db: Path, storage_ids: Sequence[int]) -> int:
        counted = real(state_db, vectors_db, storage_ids)
        _replace_the_stock(volume, [21])
        return counted

    with monkeypatch.context() as patch:
        patch.setattr(status, "embedded_in_storages", _refilled_meanwhile)
        _status(client, sign("admin"), "2")
        status.join_left_out_refresh()

    assert frozenset({2}) not in status._LEFT_OUT_CACHE
    assert "embeddedLeftOut" not in _status(client, sign("admin"), "2")
    status.join_left_out_refresh()
    assert _status(client, sign("admin"), "2")["embeddedLeftOut"] == 1

    _replace_the_stock(volume, [21, 22])
    assert "embeddedLeftOut" not in _status(client, sign("admin"), "2")
    status.join_left_out_refresh()
    assert _status(client, sign("admin"), "2")["embeddedLeftOut"] == 2


def test_the_ceiling_of_the_synchronous_count_is_a_hundred_thousand_documents() -> None:
    assert status.LEFT_OUT_EMBEDDED_SYNC_CEILING == 100_000
    assert not hasattr(status, "LEFT_OUT_EMBEDDED_CEILING")


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
