"""The store half of the storage sweep (plan 36-04, HART-06, M-32-02).

The reconcile learns which storages it still knows from the files table and
which of them Nextcloud no longer lists. Everything it decides on rests on the
six methods below, so each is pinned on its own: a living storage is one with a
row that is not a tombstone, the first sighting of a vanished storage is kept
and never overwritten, a storage that comes back loses its stamp, and a storage
that is forgotten leaves no bookmark behind that would hold the cadence open.

The last point is finding F4 of the phase 32 audit: a storage that disappeared
in the middle of a walk kept its reconcile row with after_file_id above zero,
and _is_due read that row as an interrupted walk in every tick for good.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from findling.store.repo import SCHEMA_VERSION, FileMeta, Store, open_store


@pytest.fixture
def store(tmp_path: Path) -> Iterator[Store]:
    opened = open_store(tmp_path / "state.db")
    yield opened
    opened.close()


def _record(store: Store, file_id: int, storage_id: int) -> None:
    meta = FileMeta(
        storage_id=storage_id,
        root_id=storage_id * 10,
        path=f"files/akte-{file_id}.pdf",
        title=f"akte-{file_id}.pdf",
        mime="application/pdf",
        size=1024,
        mtime=1_700_000_000,
    )
    store.record(file_id, meta, "indexed")


def test_living_storages_are_the_storages_with_a_row_that_is_no_tombstone(store: Store) -> None:
    _record(store, 1, 3)
    _record(store, 2, 3)
    _record(store, 3, 14)
    _record(store, 4, 21)
    store.tombstone(4, at=1_800_000_000)

    assert store.living_storages() == frozenset({3, 14})


def test_living_file_ids_are_the_living_rows_of_one_storage(store: Store) -> None:
    _record(store, 1, 3)
    _record(store, 2, 14)
    _record(store, 3, 14)
    _record(store, 4, 14)
    store.tombstone(4, at=1_800_000_000)

    assert store.living_file_ids(14) == [2, 3]
    assert store.living_file_ids(99) == []


def test_the_first_sighting_of_a_vanished_storage_is_kept(store: Store) -> None:
    first = store.mark_vanished(7, 1_800_000_000)
    again = store.mark_vanished(7, 1_800_086_400)

    assert first == 1_800_000_000
    assert again == 1_800_000_000


def test_a_listed_storage_loses_its_stamp_and_starts_over(store: Store) -> None:
    store.mark_vanished(7, 1_800_000_000)
    store.mark_vanished(8, 1_800_000_000)

    store.clear_vanished(frozenset({7}))

    # Back in the list, so the grace starts again from the next absence.
    assert store.mark_vanished(7, 1_801_000_000) == 1_801_000_000
    assert store.mark_vanished(8, 1_801_000_000) == 1_800_000_000


def test_clearing_many_stamps_is_banded(store: Store) -> None:
    for storage_id in range(1, 2501):
        store.mark_vanished(storage_id, 1_800_000_000)

    store.clear_vanished(frozenset(range(1, 2501)))

    assert store.mark_vanished(1234, 1_900_000_000) == 1_900_000_000


def _reconcile_rows(store: Store) -> list[int]:
    return [int(row[0]) for row in store._conn.execute("SELECT storage_id FROM reconcile ORDER BY storage_id")]


def _mount_rows(store: Store) -> list[int]:
    return [int(row[0]) for row in store._conn.execute("SELECT storage_id FROM mounts ORDER BY storage_id")]


def _vanished_rows(store: Store) -> list[int]:
    return [int(row[0]) for row in store._conn.execute("SELECT storage_id FROM vanished_storages ORDER BY storage_id")]


def test_forgetting_a_storage_drops_its_bookmark_its_mirror_and_its_stamp(store: Store) -> None:
    store.set_reconcile_cursor(14, 500, at=1_800_000_000)
    store.set_reconcile_cursor(3, 0, finished=True, at=1_800_000_000)
    store.record_mount(14, 140, 0, 5)
    store.record_mount(3, 30, 0, 5)
    store.mark_vanished(14, 1_800_000_000)

    store.forget_storage(14)

    assert _reconcile_rows(store) == [3]
    assert _mount_rows(store) == [3]
    assert _vanished_rows(store) == []


def test_an_orphan_bookmark_is_dropped_and_the_cadence_is_closed_again(store: Store) -> None:
    # F4: storage 9 vanished in the middle of a walk. Its bookmark stands above
    # zero, it has no living row and the list no longer carries it.
    _record(store, 1, 3)
    _record(store, 2, 5)
    store.set_reconcile_cursor(3, 0, finished=True, at=1_800_000_000)
    store.set_reconcile_cursor(9, 4711, at=1_800_000_000)
    store.set_reconcile_cursor(5, 12, at=1_800_000_000)
    store.record_mount(9, 90, 0, 5)
    assert store.reconcile_state().unfinished == 2

    store.drop_orphan_bookmarks(frozenset({3}))

    # 3 is listed, 5 still has a living row and is the sweep's business, 9 goes.
    assert _reconcile_rows(store) == [3, 5]
    assert _mount_rows(store) == []
    assert store.reconcile_state().unfinished == 1


def test_an_orphan_stamp_is_dropped_with_the_orphan_bookmarks(store: Store) -> None:
    # IN-04 of the phase 36 review: storage 9 was stamped, then lost its last
    # living row through the ordinary delete path and never came back to the
    # list. Nothing else would ever clear its stamp. Storage 3 is listed and
    # keeps its stamp until clear_vanished; storage 5 still has a living row
    # and its stamp is the sweep's grace, so it stays as well.
    _record(store, 1, 5)
    _record(store, 2, 9)
    store.mark_vanished(3, 1_800_000_000)
    store.mark_vanished(5, 1_800_000_000)
    store.mark_vanished(9, 1_800_000_000)
    store.tombstone(2, at=1_800_000_100)

    store.drop_orphan_bookmarks(frozenset({3}))

    assert _vanished_rows(store) == [3, 5]
    assert store.mark_vanished(5, 1_900_000_000) == 1_800_000_000
    store.clear_vanished(frozenset({3}))
    assert _vanished_rows(store) == [5]


def test_an_orphan_stamp_alone_is_dropped_without_any_bookmark(store: Store) -> None:
    # IN-04: the early return for "no orphan bookmark" must not skip the stamps.
    store.mark_vanished(9, 1_800_000_000)

    store.drop_orphan_bookmarks(frozenset())

    assert _vanished_rows(store) == []


def test_only_a_storage_mid_walk_that_vanished_leaves_nothing_unfinished(store: Store) -> None:
    store.set_reconcile_cursor(3, 0, finished=True, at=1_800_000_000)
    store.set_reconcile_cursor(9, 4711, at=1_800_000_000)

    store.drop_orphan_bookmarks(frozenset({3}))

    assert store.reconcile_state().unfinished == 0


def test_an_existing_database_gets_the_table_on_open_without_a_new_version(tmp_path: Path) -> None:
    path = tmp_path / "state.db"
    first = open_store(path)
    first.close()

    with sqlite3.connect(path) as conn:
        conn.execute("DROP TABLE vanished_storages")
    conn.close()

    reopened = open_store(path)
    try:
        assert reopened.mark_vanished(7, 1_800_000_000) == 1_800_000_000
    finally:
        reopened.close()

    assert SCHEMA_VERSION == "2"
