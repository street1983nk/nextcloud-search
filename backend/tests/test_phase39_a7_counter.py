"""Assumption A7 of 35-DEDUP-NOTIZ: the indexed counter counts file ids (plan 39-04).

A reporter read the indexed figure of the admin page as a number the index had
already deduplicated by content. The backend has no content deduplication, and
this test pins that down: two copies of one file, same path, same content hash,
on two storages (one share mounted once per user with user specific
credentials), are two living indexed rows, and the status route says 2.

Only a test, no product code. If this ever turns red, some deduplication has
crept in, and it has to be understood before any of Weg A or Weg B is built.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from findling.store.repo import FileMeta, open_store

pytestmark = pytest.mark.usefixtures("appapi_environment")

Sign = Callable[[str], dict[str, str]]

SAME_HASH = "sha256:" + "ab" * 32


def _copy(storage_id: int) -> FileMeta:
    """The same file as seen through one per user mount: only the storage differs."""
    return FileMeta(
        storage_id=storage_id,
        root_id=storage_id,
        path="/Freigabe/Vertrag.pdf",
        title="Vertrag.pdf",
        mime="application/pdf",
        size=4096,
        mtime=1_700_000_000,
    )


def _two_copies(root: Path) -> None:
    store = open_store(root / "state.db")
    try:
        store.record(101, _copy(1), "indexed", content_hash=SAME_HASH, text_chars=500)
        store.record(202, _copy(2), "indexed", content_hash=SAME_HASH, text_chars=500)
    finally:
        store.close()


def test_the_store_counts_two_copies_of_one_content_as_two(volume: Path) -> None:
    _two_copies(volume)

    store = open_store(volume / "state.db")
    try:
        counters = store.counts()
    finally:
        store.close()

    assert counters["indexed"] == 2


def test_the_status_route_reports_two_copies_as_two_indexed(
    client: TestClient,
    sign: Sign,
    volume: Path,
) -> None:
    _two_copies(volume)

    response = client.get("/status", headers=sign("admin"))

    assert response.status_code == 200, response.text
    assert response.json()["indexed"] == 2
